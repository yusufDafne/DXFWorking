"""Aday olcumleri (DEV-083). Her olcum bir FONKSIYONUN ciktisidir ve `Measurement.source` o fonksiyonun adini tasir; esik/agirlik UYDURULMAZ."""
from __future__ import annotations

import math
from dataclasses import dataclass

try:
    from .parcel import Parcel
except ImportError:
    from parcel import Parcel  # type: ignore

try:
    from ..collision.geometry import point_in_polygon, polygon_area, polygon_intersection_area
except ImportError:
    from collision.geometry import point_in_polygon, polygon_area, polygon_intersection_area

Point = tuple[float, float]
CONTACT_MM = 1e-6        # "parsel kenarina degiyor" icin sayisal pay (tasarim esigi degil)
FACES = ("ust", "sag", "alt", "sol")      # yerel +Y, +X, -Y, -X yuzleri; dis normal pusula acisi = donus + 0/90/180/270


@dataclass(frozen=True)
class Measurement:
    name: str
    value: object          # float | int | str
    unit: str
    source: str            # olcumu ureten fonksiyonun adi


def _seg_point_dist(p: Point, a: Point, b: Point) -> float:
    dx, dy = b[0] - a[0], b[1] - a[1]
    l2 = dx * dx + dy * dy
    t = 0.0 if l2 == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / l2))
    return math.hypot(p[0] - (a[0] + t * dx), p[1] - (a[1] + t * dy))


def _orient(a, b, c) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _segments_cross(a, b, c, d) -> bool:
    o1, o2, o3, o4 = _orient(a, b, c), _orient(a, b, d), _orient(c, d, a), _orient(c, d, b)
    return (o1 * o2 < 0) and (o3 * o4 < 0)


def seg_seg_distance(a: Point, b: Point, c: Point, d: Point) -> float:
    """Iki dogru parcasi arasi en kisa mesafe (kesisiyorlarsa 0)."""
    if _segments_cross(a, b, c, d):
        return 0.0
    return min(_seg_point_dist(a, c, d), _seg_point_dist(b, c, d), _seg_point_dist(c, a, b), _seg_point_dist(d, a, b))


def footprint_edge_distances(footprint, segments) -> list[float]:
    """Ayak izinin her `segments[i]=(a,b)` parcaya en kisa mesafesi (kenar basina)."""
    n = len(footprint)
    out = []
    for a, b in segments:
        out.append(min(seg_seg_distance(footprint[i], footprint[(i + 1) % n], a, b) for i in range(n)))
    return out


def polygon_segments(poly) -> list[tuple[Point, Point]]:
    n = len(poly)
    return [(tuple(poly[i]), tuple(poly[(i + 1) % n])) for i in range(n)]


def buildable_margin_mm(footprint, buildable) -> float:
    """Ayak izi ile yapilasma alani siniri arasindaki EN KISA mesafe (cekmeye pay)."""
    return min(footprint_edge_distances(footprint, polygon_segments(buildable)))


def face_bearings(rotation_deg: float) -> dict[str, float]:
    """Dort yuzun dis normal pusula acisi (kuzeyden saat yonunde, [0, 360))."""
    return {f: (rotation_deg + 90.0 * i) % 360.0 for i, f in enumerate(FACES)}


def long_faces(width: float, depth: float) -> tuple[str, ...]:
    """Uzun yuzler: `ust`/`alt` yuzlerinin uzunlugu genislik, `sag`/`sol` yuzlerinin derinlik. Kare binada dortu de."""
    if math.isclose(width, depth):
        return FACES
    return ("ust", "alt") if width > depth else ("sag", "sol")


def angular_distance(a: float, b: float) -> float:
    d = abs(a - b) % 360.0
    return min(d, 360.0 - d)


def long_face_south_deviation_deg(rotation_deg: float, width: float, depth: float) -> float:
    """Uzun yuzlerin guney (180 derece) yonunden en kucuk sapmasi. Olcumdur; 'iyi' esigi YOK."""
    bearings = face_bearings(rotation_deg)
    return min(angular_distance(bearings[f], 180.0) for f in long_faces(width, depth))


def edge_outward_bearing(parcel: Parcel, index: int) -> float:
    """CCW parselde kenarin DIS normalinin pusula acisi (kenar yonunun sagi)."""
    a, b = parcel.edges()[index]
    ux, uy = b[0] - a[0], b[1] - a[1]
    nx, ny = uy, -ux                              # CCW'de sag = dis
    return math.degrees(math.atan2(nx, ny)) % 360.0


def road_facing(parcel: Parcel, road_edges, footprint, rotation_deg: float) -> tuple[float, str, float]:
    """(en yakin yol kenarina mesafe, o yola bakan yuz, yuz normali ile yol dis normali arasindaki aci farki)."""
    segs = parcel.edges()
    best = None
    for idx in road_edges:
        d = footprint_edge_distances(footprint, [segs[idx]])[0]
        if best is None or d < best[0]:
            best = (d, idx)
    dist, idx = best
    target = edge_outward_bearing(parcel, idx)
    bearings = face_bearings(rotation_deg)
    face = min(FACES, key=lambda f: (angular_distance(bearings[f], target), FACES.index(f)))
    return dist, face, angular_distance(bearings[face], target)


def parcel_edge_distances(parcel: Parcel, footprint) -> list[float]:
    return footprint_edge_distances(footprint, parcel.edges())


def garden_pieces(distances: list[float], tol: float = CONTACT_MM) -> int:
    """Ayak izi parsel sinirina degiyorsa bahce parcalara bolunur: degen ardisik kenar KOSULARI (dongusel) kadar parca (en az 1)."""
    touching = [d <= tol for d in distances]
    n = len(touching)
    if not any(touching):
        return 1
    if all(touching):
        return 1
    runs = sum(1 for i in range(n) if touching[i] and not touching[i - 1])
    return max(1, runs)


def polygon_centroid(poly) -> Point:
    a = 0.0
    cx = cy = 0.0
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        cr = x0 * y1 - x1 * y0
        a += cr
        cx += (x0 + x1) * cr
        cy += (y0 + y1) * cr
    a *= 0.5
    return (cx / (6 * a), cy / (6 * a))


def zone_overlap_ratio(footprint, zone) -> float:
    """Ayak izinin `YERLESIM_ALANI` ile ortusen payi (0..1). Ayak izi disbukey oldugundan kirpan odur."""
    area = polygon_area(footprint)
    return polygon_intersection_area(zone, footprint) / area if area else 0.0


def zone_center_distance_mm(footprint, zone) -> float:
    return math.dist(polygon_centroid(footprint), polygon_centroid(zone))


def measure_candidate(parcel: Parcel, buildable, footprint, rotation_deg: float, width: float, depth: float,
                      road_edges=(), zone=None, north_confirmed: bool = True) -> list[Measurement]:
    """Bir adayin TUM olcumleri (sirali, determinist). Veri yoksa ilgili olcum YOKTUR (uydurulmaz)."""
    out: list[Measurement] = []
    out.append(Measurement("buildable_margin_mm", buildable_margin_mm(footprint, buildable), "mm", "buildable_margin_mm"))
    dists = parcel_edge_distances(parcel, footprint)
    out.append(Measurement("min_parcel_edge_distance_mm", min(dists), "mm", "parcel_edge_distances"))
    others = [d for i, d in enumerate(dists) if i not in set(road_edges)]
    if others:
        out.append(Measurement("min_other_edge_distance_mm", min(others), "mm", "parcel_edge_distances"))
    if road_edges:
        rd, face, dev = road_facing(parcel, list(road_edges), footprint, rotation_deg)
        out.append(Measurement("road_distance_mm", rd, "mm", "road_facing"))
        out.append(Measurement("road_face", face, "yuz", "road_facing"))
        out.append(Measurement("road_face_deviation_deg", dev, "derece", "road_facing"))
    b = face_bearings(rotation_deg)
    for f in FACES:
        out.append(Measurement(f"bearing_{f}_deg", b[f], "derece", "face_bearings"))
    if north_confirmed:
        out.append(Measurement("long_face_south_deviation_deg", long_face_south_deviation_deg(rotation_deg, width, depth), "derece", "long_face_south_deviation_deg"))
    out.append(Measurement("garden_pieces", garden_pieces(dists), "adet", "garden_pieces"))
    if zone is not None:
        out.append(Measurement("zone_overlap_ratio", zone_overlap_ratio(footprint, zone), "oran", "zone_overlap_ratio"))
        out.append(Measurement("zone_center_distance_mm", zone_center_distance_mm(footprint, zone), "mm", "zone_center_distance_mm"))
    return out
