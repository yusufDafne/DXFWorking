"""Parsel/yapilasma alani geometrisi (DEV-082). Birim: mm. Cokgenler kapali KABUL edilir (son nokta ilkini TEKRARLAMAZ)."""
from __future__ import annotations

import math
from dataclasses import dataclass

try:
    from ..collision.geometry import point_in_polygon, polygon_area, signed_area
except ImportError:  # dogrudan scripts/ uzerinden
    from collision.geometry import point_in_polygon, polygon_area, signed_area

Point = tuple[float, float]
EPS = 1e-9                       # sayisal esitlik (olcum esigi degil)
OFFSET_VERIFY_TOLERANCE_MM = 1e-6   # offset dogrulama (kayan nokta payi); bir TASARIM esigi degildir


class VaziyetError(ValueError):
    """Gecersiz parsel/cekme/girdi - yapilasma alani uydurulmaz."""


def _pts(polygon) -> list[Point]:
    return [(float(p[0]), float(p[1])) for p in polygon]


def _orient(a: Point, b: Point, c: Point) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _on_segment(a: Point, b: Point, p: Point) -> bool:
    return min(a[0], b[0]) - EPS <= p[0] <= max(a[0], b[0]) + EPS and min(a[1], b[1]) - EPS <= p[1] <= max(a[1], b[1]) + EPS


def segments_touch_or_cross(a: Point, b: Point, c: Point, d: Point) -> bool:
    """Iki dogru parcasi kesisiyor mu (UCLARDA/ustte DEGMEK de kesisimdir)."""
    o1, o2, o3, o4 = _orient(a, b, c), _orient(a, b, d), _orient(c, d, a), _orient(c, d, b)
    if ((o1 > EPS and o2 < -EPS) or (o1 < -EPS and o2 > EPS)) and ((o3 > EPS and o4 < -EPS) or (o3 < -EPS and o4 > EPS)):
        return True
    return ((abs(o1) <= EPS and _on_segment(a, b, c)) or (abs(o2) <= EPS and _on_segment(a, b, d))
            or (abs(o3) <= EPS and _on_segment(c, d, a)) or (abs(o4) <= EPS and _on_segment(c, d, b)))


def validate_polygon(polygon) -> list[str]:
    """Hata listesi (bos = gecerli): >=3 farkli kose, sifir alan degil, KENDINI KESMEZ/DEGMEZ (komsu kenarlar yalniz ortak ucta bulusur)."""
    try:
        pts = _pts(polygon)
    except (TypeError, ValueError, IndexError):
        return ["koseler [x, y] sayi cifti olmali"]
    if len(pts) < 3:
        return ["en az 3 kose gerekir"]
    errors: list[str] = []
    n = len(pts)
    for i in range(n):
        if math.dist(pts[i], pts[(i + 1) % n]) <= EPS:
            errors.append(f"{i}. ve {(i + 1) % n}. kose ayni nokta (sifir uzunluklu kenar; son nokta ilkini tekrarlamamali)")
    if errors:
        return errors
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        for j in range(i + 1, n):
            c, d = pts[j], pts[(j + 1) % n]
            adjacent = (j == i + 1) or (i == 0 and j == n - 1)
            if adjacent:
                # komsu kenarlar yalniz ortak ucta bulusur; ayni dogru uzerinde GERI donus (ust uste binme) hatadir
                shared = b if j == i + 1 else a
                p_i = a if j == i + 1 else b
                p_j = d if j == i + 1 else c
                if abs(_orient(shared, p_i, p_j)) <= EPS and (p_i[0] - shared[0]) * (p_j[0] - shared[0]) + (p_i[1] - shared[1]) * (p_j[1] - shared[1]) > 0:
                    errors.append(f"{i}. ve {j}. kenar ust uste biniyor")
            elif segments_touch_or_cross(a, b, c, d):
                errors.append(f"{i}. ve {j}. kenar kesisiyor/degiyor (kendini kesen parsel)")
    if not errors and abs(signed_area(pts)) <= EPS:
        return ["alan sifir (kolinear koseler)"]
    return errors


def normalize_ccw(polygon) -> list[Point]:
    """Saat yonu tersi (CCW) siralama; gecersiz cokgen `VaziyetError`."""
    errs = validate_polygon(polygon)
    if errs:
        raise VaziyetError("; ".join(errs))
    pts = _pts(polygon)
    return pts if signed_area(pts) > 0 else pts[::-1]


@dataclass(frozen=True)
class Parcel:
    """Dogrulanmis parsel: CCW koseler. Kenar i = kose[i] -> kose[i+1]. Kenar indeksleri `normalize_ccw` SIRASINA gore sayilir."""
    polygon: tuple[Point, ...]

    @classmethod
    def from_polygon(cls, polygon) -> "Parcel":
        return cls(tuple(normalize_ccw(polygon)))

    @property
    def area_mm2(self) -> float:
        return polygon_area(list(self.polygon))

    def edges(self) -> list[tuple[Point, Point]]:
        n = len(self.polygon)
        return [(self.polygon[i], self.polygon[(i + 1) % n]) for i in range(n)]

    def contains(self, point: Point) -> bool:
        return point_in_polygon(point, list(self.polygon))

    def as_site_dict(self) -> dict:
        return {"polygon": [[x, y] for x, y in self.polygon]}


def _dist_point_segment(p: Point, a: Point, b: Point) -> float:
    dx, dy = b[0] - a[0], b[1] - a[1]
    l2 = dx * dx + dy * dy
    t = 0.0 if l2 <= EPS else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / l2))
    return math.hypot(p[0] - (a[0] + t * dx), p[1] - (a[1] + t * dy))


def inward_offset(polygon, distances: list[float]) -> list[Point]:
    """CCW cokgeni kenar basina `distances[i]` kadar ICERI offsetler (komsu offset dogrularinin kesisimi = gonye).
    Sonuc DOGRULANIR: basit cokgen, pozitif alan, kenar yonleri korunmus (cokme/ters donme YOK) ve her kosenin HER orijinal kenara mesafesi >= o kenarin cekmesi.
    Dogrulanamazsa `VaziyetError` (cekme yapilasma alanini yok ediyor / parsel offset icin cok girintili) - sessizce yanlis cokgen DONMEZ."""
    pts = normalize_ccw(polygon)
    n = len(pts)
    if len(distances) != n:
        raise VaziyetError(f"cekme sayisi ({len(distances)}) kenar sayisina ({n}) esit olmali")
    if any((not isinstance(d, (int, float))) or isinstance(d, bool) or d < 0 for d in distances):
        raise VaziyetError("cekme mesafeleri negatif olmayan sayi olmali")
    lines = []        # (nokta, birim yon, ic normal, mesafe)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        l = math.dist(a, b)
        u = ((b[0] - a[0]) / l, (b[1] - a[1]) / l)
        nrm = (-u[1], u[0])                      # CCW'de sol = ic
        lines.append(((a[0] + distances[i] * nrm[0], a[1] + distances[i] * nrm[1]), u, nrm, distances[i]))
    out: list[Point] = []
    for j in range(n):
        p0, u0, n0, d0 = lines[(j - 1) % n]
        p1, u1, n1, d1 = lines[j]
        cross = u0[0] * u1[1] - u0[1] * u1[0]
        if abs(cross) <= 1e-12:                 # esdogrusal komsu kenarlar
            if abs(d0 - d1) > EPS:
                raise VaziyetError(f"{(j - 1) % n}. ve {j}. kenar esdogrusal ama cekmeleri farkli - gonye tanimsiz")
            out.append((pts[j][0] + d0 * n0[0], pts[j][1] + d0 * n0[1]))
            continue
        t = ((p1[0] - p0[0]) * u1[1] - (p1[1] - p0[1]) * u1[0]) / cross
        out.append((p0[0] + t * u0[0], p0[1] + t * u0[1]))
    if validate_polygon(out) or signed_area(out) <= 0:
        raise VaziyetError("cekmeler yapilasma alanini yok ediyor ya da gecersiz bir cokgen uretiyor (cekmeleri azaltin ya da parseli kontrol edin)")
    for i in range(n):
        a, b = out[i], out[(i + 1) % n]
        if (b[0] - a[0]) * lines[i][1][0] + (b[1] - a[1]) * lines[i][1][1] <= 0:
            raise VaziyetError(f"{i}. kenar offsette ters dondu/coktu: cekmeler bu parsel icin fazla buyuk")
    scale = max(1.0, max(abs(c) for p in pts for c in p))
    tol = OFFSET_VERIFY_TOLERANCE_MM * scale
    for v in out:
        for i in range(n):
            if _dist_point_segment(v, pts[i], pts[(i + 1) % n]) < distances[i] - tol:
                raise VaziyetError("offset dogrulamasi basarisiz: yapilasma alani bir parsel kenarina cekmeden daha yakin (cok girintili parsel; v1 siniri)")
    return out
