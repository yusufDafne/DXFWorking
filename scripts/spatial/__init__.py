"""spatial modulu (DEV-059): eleman-farkindali mekansal sorgularin TEK sahibi.

Neden var: kapi orta noktasi, bir noktaya deger odalar, iki poligonun ortak
kenari, dogru parcasi kesisimi / goru hatti gibi sorgular daha once
`architect/rules.py`, `standards/nuances.py`, `shafts/__init__.py` icinde ayri
ayri yazilmisti (rev-13'un "iki yerde ayri hesaplanan geometri sessizce
ayrisir" dersinin tekrari riski). Bu modul bunlari tek yerde toplar.

Bagimlilik yonu: `spatial -> collision.geometry` (TEK yonlu). Ham poligon
matematigi (`point_in_polygon`, `point_on_boundary`) `collision/geometry.py`de
KALIR ve buradan yeniden disa aktarilir; collision bu modulu ASLA import etmez.
Saf Python: ezdxf yok, cizim yok, context'e yazmaz.

**Davranis KORUNARAK tasindi** (kullanici kararlari 2026-10-09):
  - `door_midpoint`  : eski architect davranisi (sifir uzunluklu duvarda duvar
    baslangic noktasi); `door_frame`: eski standards davranisi (sifir uzunluk
    veya bilinmeyen duvar -> `(None, None)`). Ikisi BILINCLI ayri tutulur.
  - `shared_edge_length` TEK anlam = mimari surum (her yonde). Eski `shafts`
    surumunden DORT sinir farki vardir (OLCULDU, selftest'te SABITLENIR):
    0,5 mm ortusme: eski saft 0,5 / yeni 0 | tam 1,0 mm bosluk: eski saft 0 / yeni
    1000 | tam 1,0 mm ortusme: eski saft 1,0 / yeni 0 | 45 derece kenar: eski saft 0
    (yalniz eksen hizali sayardi) / yeni 1414,2. Tuketici esigi (saft >=300 mm) bu
    farklara duyarsizdir (gercek context'te tum oda ciftleri icin dogrulandi).
  - `touches_within` (standards'in sqrt karsilastirmasi) ile
    `rooms_touching_point` (collision.point_on_boundary'nin kare karsilastirmasi)
    tam tolerans sinirinda float duzeyinde AYRISIR; birlestirilmedi.
  - `vertex_mean` kose ortalamasidir; `rooms.PolygonOps.centroid` ALAN
    agirlikli olandir (144 odanin 37'sinde fark var) - adi bu yuzden `centroid`
    DEGILDIR.
Ayrinti: scripts/spatial/CLAUDE.md.
"""
from __future__ import annotations

import math

try:
    from ..collision.geometry import point_in_polygon, point_on_boundary
except ImportError:
    from collision.geometry import point_in_polygon, point_on_boundary

# Bu modulun CONTEXT SOZLESMESI surumu (DEV-020): context.json'dan hicbir alan
# okumaz; yalnizca eleman sozlukleri (door/wall/room) uzerinde calisir.
CONTRACT_VERSION = "1.0"

# Oda-kapi komsulugu toleransi (eskiden rules.py ve nuances.py'de AYRI AYRI 300.0).
TOUCH_TOLERANCE_MM = 300.0
# Ortak kenar: dik tolerans ve en az ortusme (eskiden rules.py'de sabit 1.0).
SHARED_EDGE_TOLERANCE_MM = 1.0


def door_midpoint(door: dict, walls_by_id: dict) -> tuple[float, float] | None:
    """Kapinin duvar-merkez-cizgisi uzerindeki orta noktasi; duvar bilinmiyorsa
    `None`, duvar uzunlugu sifirsa duvar BASLANGIC noktasi (eski architect davranisi)."""
    wall = walls_by_id.get(door.get("wall_id"))
    if wall is None:
        return None
    sx, sy = wall["start"]
    ex, ey = wall["end"]
    length = ((ex - sx) ** 2 + (ey - sy) ** 2) ** 0.5
    if length == 0:
        return (sx, sy)
    t = door["position_from_start"] / length
    return (sx + t * (ex - sx), sy + t * (ey - sy))


def door_frame(door: dict, walls_by_id: dict):
    """`(orta_nokta, duvar_birim_yonu)`; duvar bilinmiyorsa YA DA uzunluk sifirsa
    `(None, None)` (eski standards davranisi)."""
    wall = walls_by_id.get(door.get("wall_id"))
    if wall is None:
        return None, None
    sx, sy = wall["start"]
    ex, ey = wall["end"]
    length = ((ex - sx) ** 2 + (ey - sy) ** 2) ** 0.5
    if length == 0:
        return None, None
    t = door["position_from_start"] / length
    return (sx + t * (ex - sx), sy + t * (ey - sy)), ((ex - sx) / length, (ey - sy) / length)


def rooms_touching_point(point: tuple[float, float], rooms: list[dict],
                         tolerance: float = TOUCH_TOLERANCE_MM) -> list[dict]:
    """Poligon KENARI `point`a `tolerance` icinde olan odalar (collision.point_on_boundary)."""
    return [r for r in rooms if point_on_boundary(point, r["polygon"], tolerance)]


def dist_point_segment(p, a, b) -> float:
    """Nokta - dogru parcasi mesafesi (sqrt tabanli; eski standards davranisi)."""
    ax, ay = a
    dx, dy = b[0] - ax, b[1] - ay
    seg2 = dx * dx + dy * dy
    t = 0.0 if seg2 == 0 else max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / seg2))
    return ((p[0] - ax - t * dx) ** 2 + (p[1] - ay - t * dy) ** 2) ** 0.5


def touches_within(point, polygon, tol: float = TOUCH_TOLERANCE_MM) -> bool:
    """Poligonun herhangi bir kenari `point`a `tol` veya daha yakin mi (sqrt karsilastirma)."""
    n = len(polygon)
    return any(
        dist_point_segment(point, polygon[k], polygon[(k + 1) % n]) <= tol
        for k in range(n)
    )


def vertex_mean(polygon: list[list[float]]) -> tuple[float, float]:
    """KOSE ortalamasi (alan agirlikli centroid DEGIL)."""
    xs = [p[0] for p in polygon]
    ys = [p[1] for p in polygon]
    return (sum(xs) / len(xs), sum(ys) / len(ys))


def segments_intersect(p1, p2, p3, p4) -> bool:
    """Iki dogru parcasi GERCEKTEN (uc noktalarda DEGIL) kesisiyor mu - standart
    capraz-carpim testi. Uc noktada dokunma KASITLI olarak kesisim sayilmaz: goru
    hattinin kendi baslangic/bitis noktalari zaten bir duvarin uzerindedir."""
    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    d1 = cross(p3, p4, p1)
    d2 = cross(p3, p4, p2)
    d3 = cross(p1, p2, p3)
    d4 = cross(p1, p2, p4)
    return ((d1 > 0 > d2 or d1 < 0 < d2)
            and (d3 > 0 > d4 or d3 < 0 < d4))


def clear_line_of_sight(a: tuple[float, float], b: tuple[float, float],
                        walls: list[dict], exclude_wall_ids: set[str]) -> bool:
    """`a`-`b` parcasi, `exclude_wall_ids` disindaki hicbir duvarin MERKEZ cizgisini kesmiyor mu."""
    for wall in walls:
        if wall["id"] in exclude_wall_ids:
            continue
        if segments_intersect(a, b, tuple(wall["start"]), tuple(wall["end"])):
            return False
    return True


def shared_edge_length(poly_a, poly_b, tol: float = SHARED_EDGE_TOLERANCE_MM) -> float:
    """Iki poligonun ORTAK kenarinin (esdogrusal + ortusen, HER yonde) toplam uzunlugu.
    Kenar ciftleri arasi dik uzaklik `tol` dahil kabul edilir; yalnizca `tol`dan BUYUK
    ortusmeler sayilir. Kosede teget temas 0'dir."""
    total = 0.0
    na, nb = len(poly_a), len(poly_b)
    for i in range(na):
        a0, a1 = poly_a[i], poly_a[(i + 1) % na]
        ex, ey = a1[0] - a0[0], a1[1] - a0[1]
        elen = (ex * ex + ey * ey) ** 0.5
        if elen < 1e-9:
            continue
        for j in range(nb):
            b0, b1 = poly_b[j], poly_b[(j + 1) % nb]
            d0 = abs(ex * (b0[1] - a0[1]) - ey * (b0[0] - a0[0])) / elen
            d1 = abs(ex * (b1[1] - a0[1]) - ey * (b1[0] - a0[0])) / elen
            if d0 > tol or d1 > tol:
                continue
            t0 = ((b0[0] - a0[0]) * ex + (b0[1] - a0[1]) * ey) / elen
            t1 = ((b1[0] - a0[0]) * ex + (b1[1] - a0[1]) * ey) / elen
            overlap = min(max(t0, t1), elen) - max(min(t0, t1), 0.0)
            if overlap > tol:
                total += overlap
    return total


# DEV-062: cephe tayininde prob mesafesi = duvar kalinligi/2 + FACADE_PROBE_EXTRA_MM (duvarin iki yuzunun hemen otesi)
FACADE_PROBE_EXTRA_MM = 10.0


def _in_any(point, polygons) -> bool:
    return any(point_in_polygon(point, poly) for poly in polygons)


def facade_normal(point: tuple[float, float], wall: dict, rooms: list[dict], shafts: list[dict] | None = None):
    """Duvarin `point`indaki DIS yuz yonu (birim vektor) ya da `None` (ic duvar / belirsiz).

    Yontem: duvar merkezinden normal boyunca +/- (kalinlik/2 + 10 mm) iki prob; biri bir odanin ya da saftin ICINDE,
    digeri HICBIRININ icinde degilse dis taraf budur. Ikisi de iceride (ic duvar) ya da ikisi de disaridaysa `None`.
    Dis yon uydurulmaz: tayin edilemezse `None` doner ve cagiran 'olculemedi' der.
    """
    sx, sy = wall["start"]
    ex, ey = wall["end"]
    length = ((ex - sx) ** 2 + (ey - sy) ** 2) ** 0.5
    if length == 0:
        return None
    nx, ny = -(ey - sy) / length, (ex - sx) / length
    d = float(wall.get("thickness", 0.0)) / 2.0 + FACADE_PROBE_EXTRA_MM
    polys = [r["polygon"] for r in rooms] + [s["polygon"] for s in (shafts or [])]
    plus = (point[0] + nx * d, point[1] + ny * d)
    minus = (point[0] - nx * d, point[1] - ny * d)
    in_plus, in_minus = _in_any(plus, polys), _in_any(minus, polys)
    if in_plus == in_minus:
        return None
    return (-nx, -ny) if in_plus else (nx, ny)


def window_rooms(window: dict, walls_by_id: dict, rooms: list[dict]) -> list[dict]:
    """Pencere orta noktasina degen odalar (kapi-oda komsulugu ile ayni yontem ve tolerans)."""
    mid = door_midpoint(window, walls_by_id)
    return [] if mid is None else rooms_touching_point(mid, rooms)


def exterior_windows(rooms: list[dict], walls: list[dict], openings: list[dict], shafts: list[dict] | None = None) -> list[dict]:
    """Dis cepheye acilan pencereler: `{'window','mid','normal','rooms'}`. Dis yuzu tayin EDILEMEYEN pencere listeye girmez."""
    walls_by_id = {w["id"]: w for w in walls}
    out = []
    for o in openings:
        if o.get("type") != "window":
            continue
        wall = walls_by_id.get(o.get("wall_id"))
        mid = door_midpoint(o, walls_by_id)
        if wall is None or mid is None:
            continue
        normal = facade_normal(mid, wall, rooms, shafts)
        if normal is None:
            continue
        out.append({"window": o, "mid": mid, "normal": normal, "rooms": rooms_touching_point(mid, rooms)})
    return out


__all__ = [
    "CONTRACT_VERSION", "TOUCH_TOLERANCE_MM", "SHARED_EDGE_TOLERANCE_MM",
    "point_in_polygon", "point_on_boundary",
    "door_midpoint", "door_frame", "rooms_touching_point", "dist_point_segment",
    "touches_within", "vertex_mean", "segments_intersect", "clear_line_of_sight",
    "shared_edge_length", "FACADE_PROBE_EXTRA_MM", "facade_normal", "window_rooms", "exterior_windows",
]
