#!/usr/bin/env python3
"""context.json'dan output/plan.dxf uretir.

Kullanim:
    python scripts/generate_dxf.py [context.json yolu] [cikti .dxf yolu]

ONEMLI: Bu script, context.json'da (veya kullanicidan gelen talepte) mevcut
OLMAYAN hicbir olcuyu/koordinati uydurmaz. Asagida gorulen sabitler (metin
yuksekligi, kapi kolu/pervaz cizim detaylari gibi) SADECE cizim/sunum
kurallaridir; mimari tasarim verisi degildir ve context.json'daki gercek
geometriyi degistirmez.

Duvar cizim standardi (Turkiye standardi, bkz. CLAUDE.md):
Duvarlar "tek merkez cizgisi + width" yontemiyle DEGIL, kalinligina karsilik
gelen iki paralel kenar cizgisiyle (rail) - LINE olarak - cizilir. Birlesim
noktalarinda (kose / T-kesisimi) bu kenar cizgileri komsu duvarlarin
kenarlariyla kesistirilip (gonye/miter) uzatilir/kisaltilir; boylece her dis
kose disaridan tek bir noktada temiz birlesir. Bu mantik Wall/WallNetwork
siniflarinda kapsullenmistir - yeni duvar cizim kodu bu siniflar uzerinden
yazilmalidir.

Bu script calistirilmadan once mutlaka scripts/validate.py BASARILI donmus
olmalidir. output/plan.dxf elle duzenlenmez; her degisiklik icin bu script
yeniden calistirilir.
"""
from __future__ import annotations

import json
import math
import subprocess
import sys
from pathlib import Path

try:
    import ezdxf
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "ezdxf"])
    import ezdxf

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONTEXT_PATH = PROJECT_ROOT / "context.json"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "output" / "plan.dxf"

# --- Cizim/sunum sabitleri (tasarim verisi degil) ---
DEFAULT_LAYER_COLOR = 7
GAP_EPSILON = 1e-6  # duvar uzerinde kalan parca cok kisaysa cizmemek icin


def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def cleanup_fallback_files(output_path: Path) -> None:
    """output_path tekrar yazilabilir oldugunda, gecmiste kilit yuzunden
    olusturulmus '<isim>_N<uzanti>' yedek dosyalarini temizler."""
    pattern = f"{output_path.stem}_*{output_path.suffix}"
    for alt in output_path.parent.glob(pattern):
        try:
            alt.unlink()
        except OSError:
            pass  # kilitliyse veya silinemiyorsa sessizce gec


def save_with_fallback(save_fn, output_path: Path, max_attempts: int = 50) -> Path:
    """save_fn(path) ile kaydetmeyi dener; PermissionError alirsa (dosya baska
    bir programda acik, ör. AutoCAD) akisi kesmeden '<isim>_N<uzanti>' olarak
    kaydedip kullaniciyi bilgilendirir. output_path tekrar musaitse eski
    yedek dosyalari temizler ve normal isme kaydeder."""
    try:
        save_fn(output_path)
    except PermissionError as original_error:
        alt_path = output_path
        saved = False
        for n in range(1, max_attempts + 1):
            alt_path = output_path.with_name(f"{output_path.stem}_{n}{output_path.suffix}")
            try:
                save_fn(alt_path)
                saved = True
                break
            except PermissionError:
                continue
        if not saved:
            raise original_error
        print(
            f"UYARI: '{output_path.name}' su anda baska bir programda acik oldugu icin "
            f"uzerine yazilamadi. Bunun yerine '{alt_path.name}' olarak kaydedildi. "
            f"'{output_path.name}' dosyasini kapatip bir sonraki calistirmada bu yedek "
            f"dosya otomatik olarak temizlenecek."
        )
        return alt_path

    cleanup_fallback_files(output_path)
    return output_path


def text_height_for_units(units: str) -> float:
    # Cizimde okunabilir metin yuksekligi icin standart bir CAD sunum degeri.
    return 250.0 if units == "mm" else 0.25


def vec_sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def vec_add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def vec_scale(a, s):
    return (a[0] * s, a[1] * s)


def vec_len(a):
    return math.hypot(a[0], a[1])


def vec_norm(a):
    length = vec_len(a)
    if length == 0:
        return (0.0, 0.0)
    return (a[0] / length, a[1] / length)


def vec_perp(a):
    # 90 derece saat yonu tersine (CCW) donduruleus vektor
    return (-a[1], a[0])


def round_point(pt, units: str) -> tuple[float, float]:
    precision = 1 if units == "mm" else 4
    return (round(pt[0], precision), round(pt[1], precision))


def point_on_segment(pt, seg_a, seg_b, tol: float) -> bool:
    """pt, (seg_a -> seg_b) dogru parcasinin uzerinde mi (T-kesisimi dahil)?"""
    ax, ay = seg_a
    bx, by = seg_b
    px, py = pt
    abx, aby = bx - ax, by - ay
    seg_len = (abx ** 2 + aby ** 2) ** 0.5
    if seg_len == 0:
        return False
    apx, apy = px - ax, py - ay
    cross = abx * apy - aby * apx
    dist = abs(cross) / seg_len
    if dist > tol:
        return False
    t = (apx * abx + apy * aby) / (seg_len ** 2)
    return -1e-6 <= t <= 1 + 1e-6


def line_intersection(p1, d1, p2, d2):
    """Iki sonsuz dogrunun (p1+t*d1) ve (p2+s*d2) kesisim noktasi; paralelse None."""
    denom = d1[0] * d2[1] - d1[1] * d2[0]
    if abs(denom) < 1e-9:
        return None
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    t = (dx * d2[1] - dy * d2[0]) / denom
    return vec_add(p1, vec_scale(d1, t))


def project_s(point, origin, direction) -> float:
    """point'in origin'den direction yonunde (birim vektor) olculen s parametresi."""
    return (point[0] - origin[0]) * direction[0] + (point[1] - origin[1]) * direction[1]


class Wall:
    """Tek bir duvar segmenti: merkez cizgisi + kalinlik.

    Duvar, kalinligina karsilik gelen iki paralel kenar cizgisiyle (rail)
    temsil edilir: 'pos' (merkez cizginin +normal tarafi) ve 'neg' (-normal
    tarafi). Her rail'in cizilebilir [s_start, s_end] araligi (s=0 orijinal
    baslangic, s=length orijinal bitis), WallNetwork tarafindan komsu
    duvarlarla olan birlesim noktalarina gore (gonye/miter) guncellenir.
    """

    def __init__(self, wall_id: str, start, end, thickness: float, layer: str):
        self.id = wall_id
        self.start = tuple(start)
        self.end = tuple(end)
        self.thickness = thickness
        self.layer = layer
        self.length = vec_len(vec_sub(self.end, self.start))
        self.direction = vec_norm(vec_sub(self.end, self.start))
        self.normal = vec_perp(self.direction)
        self.rail_trim = {"pos": [0.0, self.length], "neg": [0.0, self.length]}

    def rail_origin(self, side: str) -> tuple[float, float]:
        sign = 1.0 if side == "pos" else -1.0
        return vec_add(self.start, vec_scale(self.normal, sign * self.thickness / 2.0))

    def rail_point(self, side: str, s: float) -> tuple[float, float]:
        return vec_add(self.rail_origin(side), vec_scale(self.direction, s))

    def rail_line(self, side: str):
        return self.rail_origin(side), self.direction

    def endpoint_s(self, which: str) -> float:
        return 0.0 if which == "start" else self.length

    def set_trim(self, side: str, which: str, s: float) -> None:
        idx = 0 if which == "start" else 1
        self.rail_trim[side][idx] = s

    def centerline_point(self, s: float) -> tuple[float, float]:
        return vec_add(self.start, vec_scale(self.direction, s))


class WallNetwork:
    """Duvarlar arasi birlesim (kose / T-kesisimi) cozumlemesini yapar.

    Her duvarin iki rail'ini komsu duvarlarin rail'leriyle kesistirip
    (gonye/miter birlesim) dogru uzunluga getirir; boylece disaridan
    bakildiginda her kose tek bir noktada temiz sekilde birlesir.
    """

    def __init__(self, walls: list[Wall], units: str):
        self.walls = walls
        self.units = units
        self.tol = 1.0 if units == "mm" else 0.001
        self._resolve_joints()

    def _resolve_joints(self) -> None:
        endpoint_groups: dict[tuple[float, float], list[tuple[Wall, str]]] = {}
        for w in self.walls:
            for which, pt in (("start", w.start), ("end", w.end)):
                key = round_point(pt, self.units)
                endpoint_groups.setdefault(key, []).append((w, which))

        handled: set[tuple[str, str]] = set()

        # 1) Kose birlesimleri: ayni noktada bulusan tum duvar uclarini
        #    ikili ikili gonyeleyerek kesistir.
        for entries in endpoint_groups.values():
            if len(entries) < 2:
                continue
            for i in range(len(entries)):
                for j in range(i + 1, len(entries)):
                    wA, whichA = entries[i]
                    wB, whichB = entries[j]
                    self._miter_corner(wA, whichA, wB, whichB)
            for w, which in entries:
                handled.add((w.id, which))

        # 2) T-kesisimleri: kose olarak islenmeyen her uc icin, baska bir
        #    duvarin uzerine denk gelip gelmedigine bak.
        for w in self.walls:
            for which, pt in (("start", w.start), ("end", w.end)):
                if (w.id, which) in handled:
                    continue
                for other in self.walls:
                    if other.id == w.id:
                        continue
                    if point_on_segment(pt, other.start, other.end, self.tol):
                        self._trim_stub_at_through(w, which, other)
                        break
            # Baglanti bulunamazsa (validate.py bunu zaten engeller) duvar
            # kendi orijinal ucunda birakilir.

    def _miter_corner(self, wA: Wall, whichA: str, wB: Wall, whichB: str) -> None:
        for side in ("pos", "neg"):
            originA, dirA = wA.rail_line(side)
            originB, dirB = wB.rail_line(side)
            inter = line_intersection(originA, dirA, originB, dirB)
            if inter is None:
                continue  # paralel duvarlar - gonye uygulanamaz, oldugu gibi birakilir
            wA.set_trim(side, whichA, project_s(inter, originA, dirA))
            wB.set_trim(side, whichB, project_s(inter, originB, dirB))

    def _trim_stub_at_through(self, stub: Wall, which: str, through: Wall) -> None:
        far_s = stub.endpoint_s("end" if which == "start" else "start")
        far_point = stub.centerline_point(far_s)
        for side in ("pos", "neg"):
            origin, direction = stub.rail_line(side)
            candidates = []
            for t_side in ("pos", "neg"):
                t_origin, t_dir = through.rail_line(t_side)
                inter = line_intersection(origin, direction, t_origin, t_dir)
                if inter is not None:
                    candidates.append(inter)
            if not candidates:
                continue
            # Uzak uctan bakildiginda ilk carpilan yuz = dogru kesim noktasi
            best = min(candidates, key=lambda p: vec_len(vec_sub(p, far_point)))
            stub.set_trim(side, which, project_s(best, origin, direction))

    def drawable_rail_segments(self, wall: Wall, side: str, openings: list[dict]):
        s0, s1 = wall.rail_trim[side]
        if s0 > s1:
            s0, s1 = s1, s0

        gaps = []
        for op in openings:
            if op["wall_id"] != wall.id:
                continue
            half = op["width"] / 2.0
            g_start = max(s0, op["position_from_start"] - half)
            g_end = min(s1, op["position_from_start"] + half)
            if g_end > g_start:
                gaps.append((g_start, g_end))
        gaps.sort()

        cursor = s0
        segments = []
        for g_start, g_end in gaps:
            if g_start - cursor > GAP_EPSILON:
                segments.append((cursor, g_start))
            cursor = max(cursor, g_end)
        if s1 - cursor > GAP_EPSILON:
            segments.append((cursor, s1))
        if not gaps:
            segments = [(s0, s1)]

        return [
            (wall.rail_point(side, a), wall.rail_point(side, b))
            for a, b in segments
            if b - a > GAP_EPSILON
        ]


def gaps_for_wall(wall: Wall, openings: list[dict]):
    gaps = []
    for op in openings:
        if op["wall_id"] != wall.id:
            continue
        half = op["width"] / 2.0
        g_start = max(0.0, op["position_from_start"] - half)
        g_end = min(wall.length, op["position_from_start"] + half)
        if g_end > g_start:
            gaps.append((g_start, g_end, op))
    gaps.sort(key=lambda g: g[0])
    return gaps


def setup_layers(doc, layers: list[dict]) -> None:
    for layer in layers:
        name = layer["name"]
        if name in doc.layers:
            continue
        attribs = {}
        if "color" in layer:
            attribs["color"] = layer["color"]
        if "linetype" in layer:
            attribs["linetype"] = layer["linetype"]
        doc.layers.add(name=name, dxfattribs=attribs or {"color": DEFAULT_LAYER_COLOR})


def draw_wall_network(msp, network: WallNetwork, openings: list[dict]) -> None:
    for wall in network.walls:
        for side in ("pos", "neg"):
            for p1, p2 in network.drawable_rail_segments(wall, side, openings):
                msp.add_line(p1, p2, dxfattribs={"layer": wall.layer})

        # Aciklik kenarlarina pervaz (jamb) cizgileri + kapi/pencere sembolleri
        perp = wall.normal
        for g_start, g_end, op in gaps_for_wall(wall, openings):
            op_layer = op.get("layer", "KAPI-PENCERE")

            for s in (g_start, g_end):
                msp.add_line(
                    wall.rail_point("pos", s),
                    wall.rail_point("neg", s),
                    dxfattribs={"layer": wall.layer},
                )

            hinge = wall.centerline_point(g_start)
            far = wall.centerline_point(g_end)
            width = g_end - g_start

            if op["type"] == "door":
                leaf_end = vec_add(hinge, vec_scale(perp, width))
                msp.add_line(hinge, leaf_end, dxfattribs={"layer": op_layer})
                start_angle = math.degrees(math.atan2(wall.direction[1], wall.direction[0]))
                end_angle = math.degrees(math.atan2(perp[1], perp[0]))
                msp.add_arc(
                    center=hinge,
                    radius=width,
                    start_angle=min(start_angle, end_angle),
                    end_angle=max(start_angle, end_angle),
                    dxfattribs={"layer": op_layer},
                )
            else:  # window
                offset = wall.thickness / 4.0
                for sign in (-1, 1):
                    off_vec = vec_scale(perp, sign * offset)
                    msp.add_line(
                        vec_add(hinge, off_vec),
                        vec_add(far, off_vec),
                        dxfattribs={"layer": op_layer},
                    )


def polygon_centroid(polygon: list[list[float]]) -> tuple[float, float]:
    area = 0.0
    cx = 0.0
    cy = 0.0
    n = len(polygon)
    for i in range(n):
        x1, y1 = polygon[i]
        x2, y2 = polygon[(i + 1) % n]
        cross = x1 * y2 - x2 * y1
        area += cross
        cx += (x1 + x2) * cross
        cy += (y1 + y2) * cross
    area *= 0.5
    if abs(area) < 1e-9:
        # dejenere poligon icin basit ortalama
        xs = [p[0] for p in polygon]
        ys = [p[1] for p in polygon]
        return (sum(xs) / len(xs), sum(ys) / len(ys))
    cx /= 6 * area
    cy /= 6 * area
    return (cx, cy)


def draw_room_label(msp, room: dict, text_height: float) -> None:
    cx, cy = polygon_centroid(room["polygon"])
    content = f"{room['name']} ({room['area_m2']:.1f} m2)"
    text = msp.add_text(content, dxfattribs={"layer": "METIN", "height": text_height})
    text.dxf.insert = (cx, cy)


def draw_labels(msp, labels: list[dict], default_height: float) -> None:
    for label in labels:
        height = label.get("height", default_height)
        layer = label.get("layer", "METIN")
        text = msp.add_text(label["text"], dxfattribs={"layer": layer, "height": height})
        text.dxf.insert = tuple(label["position"])


def generate(context_path: Path = DEFAULT_CONTEXT_PATH, output_path: Path = DEFAULT_OUTPUT_PATH) -> Path:
    context = load_json(context_path)
    units = context["meta"]["units"]

    doc = ezdxf.new(dxfversion="R2010")
    doc.header["$INSUNITS"] = ezdxf.units.MM if units == "mm" else ezdxf.units.M
    setup_layers(doc, context["layers"])
    msp = doc.modelspace()

    walls = [
        Wall(w["id"], w["start"], w["end"], w["thickness"], w["layer"])
        for w in context["walls"]
    ]
    network = WallNetwork(walls, units)

    openings = context["openings"]
    draw_wall_network(msp, network, openings)

    text_height = text_height_for_units(units)
    for room in context["rooms"]:
        draw_room_label(msp, room, text_height)

    draw_labels(msp, context["labels"], text_height)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    return save_with_fallback(lambda p: doc.saveas(p), output_path)


def main() -> int:
    context_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CONTEXT_PATH
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_OUTPUT_PATH
    result = generate(context_path, output_path)
    print(f"DXF uretildi: {result}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
