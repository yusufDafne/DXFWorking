"""Vaziyet DXF'i IC AKTARMA (DEV-082): SALT OKUNUR tarama. Context'e YAZMAZ, hicbir adayi KENDISI SECMEZ (importer/ ile ayni ilke).

Cikti `SiteScan`: parsel/yerlesim-alani ADAYLARI (kapali LWPOLYLINE/POLYLINE + LINE zincirlerinden kapanan dongu), yol cizgileri, metinler, kuzey isareti
denetimi, birim bilgisi. Katman adlari yalniz IPUCUDUR (`layer_hint`); karar kullanicidadir (dil modeli YALNIZ onerir, DEV-085).
Tahmin YOK: birim bilinmiyorsa (`$INSUNITS` = 0) mm'ye cevrilmez ve bu soylenir; DWG okunmaz (DEV-087).
"""
from __future__ import annotations

import hashlib
import math
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

import ezdxf

try:
    from .parcel import VaziyetError, validate_polygon
except ImportError:
    from parcel import VaziyetError, validate_polygon  # type: ignore

# $INSUNITS -> mm carpani (yalniz DXF belirtimindeki birim kodlari; 0 = belirtilmemis -> BILINMIYOR)
UNIT_TO_MM = {1: ("inch", 25.4), 2: ("foot", 304.8), 4: ("mm", 1.0), 5: ("cm", 10.0), 6: ("m", 1000.0)}
JOIN_TOLERANCE_MM = 1.0                 # LINE uclarini 'ayni nokta' sayma payi: CIZIM HASSASIYETI, tasarim esigi degil (kullanici degistirebilir)
NORTH_UP_TOLERANCE_DEG = 1.0            # kuzey isareti 'yukari' sayma payi: CIZIM HASSASIYETI, tasarim esigi degil
NORTH_TEXTS = {"K", "N", "KUZEY", "NORTH"}


class DxfInputError(VaziyetError):
    """Okunamayan/desteklenmeyen girdi dosyasi."""


def _norm(text: str) -> str:
    t = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode("ascii")
    return t.casefold()


def layer_hint(layer: str) -> str | None:
    n = _norm(layer)
    if "yerlesim" in n or "zone" in n or "oturum" in n:
        return "yerlesim_alani"
    if "parsel" in n or "parcel" in n or "arsa" in n:
        return "parsel"
    return None


@dataclass
class Candidate:
    id: str
    source: str                         # lwpolyline | polyline | line_chain
    layer: str
    points: list[tuple[float, float]]   # DXF birimi
    points_mm: list[tuple[float, float]] | None
    area_mm2: float | None
    bbox_mm: tuple[float, float, float, float] | None
    layer_hint: str | None
    valid: bool
    problems: list[str]


@dataclass
class SiteScan:
    path: str
    sha256: str
    units: str | None
    to_mm: float | None
    candidates: list[Candidate] = field(default_factory=list)
    unsupported: list[str] = field(default_factory=list)
    road_segments_mm: list[tuple[tuple[float, float], tuple[float, float]]] = field(default_factory=list)
    texts: list[dict] = field(default_factory=list)
    north: dict = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def by_id(self, cid: str) -> Candidate:
        for c in self.candidates:
            if c.id == cid:
                return c
        raise VaziyetError(f"aday bulunamadi: {cid}")


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _convert(points, factor):
    return None if factor is None else [(x * factor, y * factor) for x, y in points]


def _bbox(points):
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    return (min(xs), min(ys), max(xs), max(ys))


def _area(points):
    s = 0.0
    for i in range(len(points)):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % len(points)]
        s += x1 * y2 - x2 * y1
    return abs(s) / 2.0


def _make_candidate(cid, source, layer, points, factor) -> Candidate:
    points = [(float(x), float(y)) for x, y in points]
    mm = _convert(points, factor)
    problems = validate_polygon(points)
    return Candidate(cid, source, layer, points, mm, None if mm is None else _area(mm), None if mm is None else _bbox(mm),
                     layer_hint(layer), not problems, problems)


def _chains(lines, tol):
    """LINE parcalarindan KAPANAN donguler: her dugum derecesi tam 2 olan bagli bilesenler. Dallanan/acik zincirler dongu SAYILMAZ."""
    def key(p):
        return (round(p[0] / tol), round(p[1] / tol)) if tol > 0 else p
    nodes: dict = {}
    for idx, (a, b, layer) in enumerate(lines):
        nodes.setdefault(key(a), []).append((idx, key(b), b, a))
        nodes.setdefault(key(b), []).append((idx, key(a), a, b))
    seen: set[int] = set()
    loops = []
    for idx, (a, b, layer) in enumerate(lines):
        if idx in seen:
            continue
        # bileseni topla
        comp, stack = set(), [idx]
        while stack:
            cur = stack.pop()
            if cur in comp:
                continue
            comp.add(cur)
            for end in (lines[cur][0], lines[cur][1]):
                for j, *_ in nodes[key(end)]:
                    if j not in comp:
                        stack.append(j)
        seen |= comp
        degrees = {}
        for j in comp:
            for end in (lines[j][0], lines[j][1]):
                degrees[key(end)] = degrees.get(key(end), 0) + 1
        if not all(d == 2 for d in degrees.values()) or len(comp) < 3:
            continue
        # sirali dolas
        start = lines[min(comp)]
        order = [start[0]]
        cur_key, used = key(start[1]), {min(comp)}
        order.append(start[1])
        while len(used) < len(comp):
            for j, other_key, other_pt, this_pt in nodes[cur_key]:
                if j not in used:
                    used.add(j)
                    order.append(other_pt)
                    cur_key = other_key
                    break
            else:
                break
        if len(used) == len(comp) and key(order[-1]) == key(order[0]):
            loops.append(([p for p in order[:-1]], lines[min(comp)][2]))
    return loops


def scan_site_dxf(path, join_tolerance_mm: float = JOIN_TOLERANCE_MM) -> SiteScan:
    p = Path(path)
    if not p.exists():
        raise DxfInputError(f"dosya yok: {p}")
    head = p.read_bytes()[:6]
    if head.startswith(b"AC10") or head.startswith(b"AC1"):
        raise DxfInputError("bu bir DWG dosyasi: sistem yalniz DXF okur. CAD'de 'DXF olarak kaydedin' (DWG dönüştürücü: DEV-087).")
    try:
        doc = ezdxf.readfile(p)
    except Exception as exc:  # noqa: BLE001
        raise DxfInputError(f"DXF okunamadi: {type(exc).__name__}: {exc}") from exc
    code = int(doc.header.get("$INSUNITS", 0) or 0)
    units, factor = UNIT_TO_MM.get(code, (None, None))
    scan = SiteScan(str(path), _file_sha256(p), units, factor)
    if factor is None:
        scan.warnings.append("DXF birimi belirtilmemis ($INSUNITS=0 ya da desteklenmeyen kod): mm'ye cevrilmedi, adaylar ham birimde. Birimi kullanicidan isteyin; tahmin edilmez.")
    tol_raw = join_tolerance_mm / (factor or 1.0)
    msp = doc.modelspace()
    lines, n_cand = [], 0
    roads = []
    north_dirs = []
    for e in msp:
        t = e.dxftype()
        layer = e.dxf.layer
        if t in ("LWPOLYLINE", "POLYLINE"):
            if t == "LWPOLYLINE":
                pts = [(float(pt[0]), float(pt[1])) for pt in e.get_points("xy")]
                bulges = any(abs(pt[4]) > 0 for pt in e.get_points("xyseb"))
                closed = bool(e.closed)
            else:
                if not e.is_2d_polyline:
                    scan.unsupported.append(f"{layer}: 3B POLYLINE desteklenmiyor")
                    continue
                pts = [(float(v.dxf.location.x), float(v.dxf.location.y)) for v in e.vertices]
                bulges = any(abs(v.dxf.bulge) > 0 for v in e.vertices)
                closed = bool(e.is_closed)
            if closed and len(pts) >= 2 and pts[0] == pts[-1]:
                pts = pts[:-1]
            if layer_hint(layer) is None and _norm(layer).find("yol") >= 0 and not closed:
                roads.append(pts)
                continue
            if _norm(layer).find("kuzey") >= 0 or _norm(layer).find("north") >= 0:
                if len(pts) >= 2:
                    north_dirs.append((pts[0], pts[-1]))
                continue
            if not closed:
                scan.unsupported.append(f"{layer}: acik polyline ({len(pts)} nokta) aday sayilmadi")
                continue
            if bulges:
                scan.unsupported.append(f"{layer}: yay (bulge) iceren polyline desteklenmiyor; duz kenarli cizin")
                continue
            scan.candidates.append(_make_candidate(f"c{n_cand}", "lwpolyline" if t == "LWPOLYLINE" else "polyline", layer, pts, factor))
            n_cand += 1
        elif t == "LINE":
            a = (float(e.dxf.start.x), float(e.dxf.start.y))
            b = (float(e.dxf.end.x), float(e.dxf.end.y))
            ln = _norm(layer)
            if "yol" in ln:
                roads.append([a, b])
            elif "kuzey" in ln or "north" in ln:
                north_dirs.append((a, b))
            else:
                lines.append((a, b, layer))
        elif t in ("TEXT", "MTEXT"):
            txt = e.dxf.text if t == "TEXT" else e.plain_text()
            pos = e.dxf.insert
            scan.texts.append({"text": str(txt).strip(), "layer": layer, "position": (float(pos.x), float(pos.y)),
                               "position_mm": None if factor is None else (float(pos.x) * factor, float(pos.y) * factor)})
        elif t in ("ARC", "CIRCLE", "SPLINE", "ELLIPSE"):
            scan.unsupported.append(f"{layer}: {t} desteklenmiyor")
    for loop, layer in _chains(lines, tol_raw):
        scan.candidates.append(_make_candidate(f"c{n_cand}", "line_chain", layer, loop, factor))
        n_cand += 1
    for seg in roads:
        for i in range(len(seg) - 1):
            a, b = seg[i], seg[i + 1]
            scan.road_segments_mm.append(((a[0] * (factor or 1.0), a[1] * (factor or 1.0)), (b[0] * (factor or 1.0), b[1] * (factor or 1.0))))
    # kuzey isareti denetimi
    text_found = any(t["text"].strip().upper() in NORTH_TEXTS for t in scan.texts)
    direction = None
    if north_dirs:
        a, b = north_dirs[0]
        direction = math.degrees(math.atan2(b[0] - a[0], b[1] - a[1]))        # +Y'den saat yonunde
    if direction is not None:
        status = "yukari" if abs(direction) <= NORTH_UP_TOLERANCE_DEG else "yukari_degil"
    elif text_found:
        status = "belirsiz"
    else:
        status = "yok"
    scan.north = {"status": status, "direction_deg": direction, "text_found": text_found}
    if status != "yukari":
        if status == "yukari_degil":
            reason = f"kuzey isareti yukariyi gostermiyor ({direction:.1f} derece)"
        elif status == "belirsiz":
            reason = "yalniz 'K/N' metni var, yon belirlenemedi"
        else:
            reason = "kuzey isareti bulunamadi"
        scan.warnings.append(f"UYARI: vaziyet plani kuzey YUKARI olmali ({reason}). Yon tahmin edilmez; kullaniciya sorun / planin kuzeyi yukari olan halini isteyin.")
    if not scan.candidates:
        scan.warnings.append("kapali parsel adayi bulunamadi (kapali polyline ya da kapanan LINE zinciri yok)")
    return scan


def build_site_patch(scan: SiteScan, parcel_id: str, zone_id: str | None = None, road_edges: list[int] | None = None,
                     north_confirmed: bool = False) -> dict:
    """ONAYLI aday secimlerinden `context.json::site` PATCH'i uretir (DOSYAYA YAZMAZ; otomatik birlestirme YOK: normal talep akisi). Birim bilinmiyorsa REDDEDER."""
    if scan.to_mm is None:
        raise VaziyetError("birim bilinmiyor: mm'ye cevrilemez (kullanicidan birimi isteyin)")
    parcel = scan.by_id(parcel_id)
    if not parcel.valid:
        raise VaziyetError(f"{parcel_id} gecersiz cokgen: {'; '.join(parcel.problems)}")
    site: dict = {"source": {"path": scan.path, "sha256": scan.sha256, "units": scan.units},
                  "north_confirmed": bool(north_confirmed),
                  "parcel": {"polygon": [[x, y] for x, y in parcel.points_mm]}}
    if zone_id:
        zone = scan.by_id(zone_id)
        if not zone.valid:
            raise VaziyetError(f"{zone_id} gecersiz cokgen: {'; '.join(zone.problems)}")
        site["placement_zone"] = {"polygon": [[x, y] for x, y in zone.points_mm]}
    if road_edges:
        site["road_edges"] = list(road_edges)
    return site
