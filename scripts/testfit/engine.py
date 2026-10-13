"""Deneme yerlestirme motoru (DEV-063): bir kumenin NET odaya SIGIP SIGMADIGINI sinar. Cozum onerisi DEGIL, SINAVDIR.

Sonuc TUREVDIR; context'e yazilmaz. Yerlestirme kararini kullanici verir. Kural sahibi `collision` motorudur: son dogrulama
`collision.CollisionEngine` ile yapilir (tefris <-> tefris, tefris <-> kapi acilim sektoru, oda disina tasma; temas toleransi
`CONTACT_TOLERANCE`). Katman A: gecis payi = 0 (yalniz katalog olcusu + collision kurali). Rahat sigma paylari (Katman B)
DEGERLERI mimar verene dek kodlanmaz.

Yontem (deterministik): parcalar buyukten kucuge; her parca icin eksen-hizali iki yon; aday konumlar odanin net sinir kutusuna,
daha once yerlestirilmis parcalarin kenarlarina ve kapi sektoru sinir kutusuna HIZALI koordinatlardir (duvara/parcaya dayali yerlesimler);
geri izlemeli arama. Sinirli dugum sayisi (`MAX_NODES`) asilirsa sonuc 'OLCULEMEDI' (None) olur - 'sigmaz' DENMEZ.
"""
from __future__ import annotations

from dataclasses import dataclass

from collision import (TAG_DOOR_SWING, TAG_FURNITURE, TAG_ROOM, CollisionEngine, CollisionShape, rect_shape)
from collision.geometry import polygon_area, polygon_clip

try:
    from ..furniture import FurnitureCatalog
    from ..standards.measure import edge_wall_thicknesses, inset_polygon
except ImportError:
    from furniture import FurnitureCatalog
    from standards.measure import edge_wall_thicknesses, inset_polygon

from .library import Cluster

MAX_NODES = 200_000   # arama butcesi (kaynak ayri; asilirsa 'olculemedi')
_EPS = 1e-6


@dataclass(frozen=True)
class Placement:
    type: str
    position: tuple[float, float]   # blok ekleme noktasi (sol-alt kose, furniture sozlesmesi)
    rotation: float                 # 0 ya da 90


@dataclass(frozen=True)
class FitResult:
    cluster_id: str
    fits: bool | None               # None = OLCULEMEDI (arama butcesi)
    placements: tuple[Placement, ...] = ()


def net_room_polygon(room: dict, walls: list[dict]) -> list[list[float]]:
    """Duvar merkez cizgisinde tanimli oda poligonundan duvar IC YUZLERI arasi NET poligon."""
    poly = [list(p) for p in room["polygon"]]
    return inset_polygon(poly, edge_wall_thicknesses(poly, walls))


def _bbox(poly):
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    return min(xs), min(ys), max(xs), max(ys)


def _is_axis_rect(poly) -> bool:
    if len(poly) != 4:
        return False
    x0, y0, x1, y1 = _bbox(poly)
    return all(abs(p[0] - x0) < _EPS or abs(p[0] - x1) < _EPS for p in poly) and \
        all(abs(p[1] - y0) < _EPS or abs(p[1] - y1) < _EPS for p in poly)


def _inside_net(rect, net, net_is_rect: bool, net_box) -> bool:
    x0, y0, x1, y1 = rect
    nx0, ny0, nx1, ny1 = net_box
    if x0 < nx0 - _EPS or y0 < ny0 - _EPS or x1 > nx1 + _EPS or y1 > ny1 + _EPS:
        return False
    if net_is_rect:
        return True
    clipped = polygon_clip(net, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
    return len(clipped) >= 3 and polygon_area(clipped) >= (x1 - x0) * (y1 - y0) - 1.0


def _overlap_depth_rect(a, b) -> float:
    dx = min(a[2], b[2]) - max(a[0], b[0])
    dy = min(a[3], b[3]) - max(a[1], b[1])
    return min(dx, dy) if dx > 0 and dy > 0 else 0.0


def _hits_sector(rect, sector: CollisionShape, tolerance: float) -> bool:
    sx0, sy0, sx1, sy1 = sector.bbox
    if rect[2] <= sx0 or rect[0] >= sx1 or rect[3] <= sy0 or rect[1] >= sy1:
        return False
    clipped = polygon_clip(list(sector.polygon), [(rect[0], rect[1]), (rect[2], rect[1]), (rect[2], rect[3]), (rect[0], rect[3])])
    if len(clipped) < 3:
        return False
    cx0, cy0, cx1, cy1 = _bbox(clipped)
    return min(cx1 - cx0, cy1 - cy0) > tolerance


def _placement_for(item_type: str, rect, rotated: bool) -> Placement:
    # rotation 90: sol-alt kose etrafinda saat yonu tersi -> alan x: [px - depth, px], y: [py, py + width]
    return Placement(item_type, (rect[2], rect[1]) if rotated else (rect[0], rect[1]), 90.0 if rotated else 0.0)


def try_fit(room: dict, walls: list[dict], sectors: list[CollisionShape], cluster: Cluster,
            catalog: FurnitureCatalog | None = None, engine: CollisionEngine | None = None) -> FitResult:
    catalog = catalog or FurnitureCatalog()
    engine = engine or CollisionEngine()
    tol = engine.policy.contact_tolerance
    net = net_room_polygon(room, walls)
    net_box = _bbox(net)
    net_is_rect = _is_axis_rect(net)
    near = [s for s in sectors if not (s.bbox[2] <= net_box[0] or s.bbox[0] >= net_box[2]
                                       or s.bbox[3] <= net_box[1] or s.bbox[1] >= net_box[3])]
    specs = [catalog.get(t) for t in cluster.items]
    nodes = 0
    budget_hit = False

    def candidates(w, d, placed):
        out = []
        for rotated, (ww, dd) in ((False, (w, d)), (True, (d, w))):
            xs = {net_box[0], net_box[2] - ww} | {p[0] for p in net} | {p[0] - ww for p in net}
            ys = {net_box[1], net_box[3] - dd} | {p[1] for p in net} | {p[1] - dd for p in net}
            for r, _rot in placed:
                xs |= {r[2], r[0], r[0] - ww, r[2] - ww}
                ys |= {r[3], r[1], r[1] - dd, r[3] - dd}
            for s in near:
                xs |= {s.bbox[2], s.bbox[0] - ww}
                ys |= {s.bbox[3], s.bbox[1] - dd}
            for y in sorted(ys):
                for x in sorted(xs):
                    out.append(((x, y, x + ww, y + dd), rotated))
        return out

    def search(idx, placed):
        nonlocal nodes, budget_hit
        if idx == len(specs):
            return list(placed)
        spec = specs[idx]
        for rect, rotated in candidates(spec.width, spec.depth, placed):
            nodes += 1
            if nodes > MAX_NODES:
                budget_hit = True
                return None
            if not _inside_net(rect, net, net_is_rect, net_box):
                continue
            if any(_overlap_depth_rect(rect, r) > tol for r, _rot in placed):
                continue
            if any(_hits_sector(rect, s, tol) for s in near):
                continue
            result = search(idx + 1, placed + [(rect, rotated)])
            if result is not None:
                return result
            if budget_hit:
                return None
        return None

    found = search(0, [])
    if found is None:
        return FitResult(cluster.id, None if budget_hit else False)
    placements = tuple(_placement_for(spec.key, rect, rot) for spec, (rect, rot) in zip(specs, found))
    # kural sahibi collision motorudur: son dogrulama ayni politika ile (celiski varsa 'sigdi' DENMEZ)
    if verify_with_collision(room, net, near, placements, catalog, engine):
        return FitResult(cluster.id, True, placements)
    return FitResult(cluster.id, None)


def verify_with_collision(room: dict, net: list[list[float]], sectors: list[CollisionShape], placements,
                          catalog: FurnitureCatalog, engine: CollisionEngine | None = None) -> bool:
    """Yerlesimi `collision` motoruna verir: bloklayan (HATA) cakisma YOKSA True."""
    engine = engine or CollisionEngine()
    shapes: list[CollisionShape] = [CollisionShape(TAG_ROOM, room.get("id", "oda"), tuple(map(tuple, net)), container=True)]
    shapes += list(sectors)
    for i, p in enumerate(placements):
        spec = catalog.get(p.type)
        shapes.append(rect_shape(TAG_FURNITURE, f"{p.type}_{i}", p.position, spec.width, spec.depth, p.rotation, label=spec.label))
    return not any(c.blocking for c in engine.detect(shapes))


def best_cluster(room: dict, walls: list[dict], sectors: list[CollisionShape], clusters: tuple[Cluster, ...],
                 catalog: FurnitureCatalog | None = None) -> tuple[Cluster | None, list[FitResult]]:
    """Merdivenden (K1 -> K4) SIGAN ilk kume ve denenen tum sonuclar. Hicbiri sigmazsa (None, ...); bir deneme
    'olculemedi' ise kapasite KESIN soylenemez: sonuclarda None kalir."""
    results = []
    for cluster in clusters:
        r = try_fit(room, walls, sectors, cluster, catalog)
        results.append(r)
        if r.fits:
            return cluster, results
    return None, results
