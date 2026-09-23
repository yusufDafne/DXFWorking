"""Duvar tarama / topoloji: odalardan kenar cikarimi, paylasilan duvar, birlesim raporu."""
from __future__ import annotations

from dataclasses import dataclass

from .catalog import WallCatalog, WallTypeSpec
from .geometry import round_point, segment_key, vec_len, vec_sub


@dataclass
class ScannedEdge:
    """Oda poligonundan turetilmis yonsuz kenar."""

    start: tuple[float, float]
    end: tuple[float, float]
    room_ids: list[str]
    shared: bool
    length: float


@dataclass
class JunctionReport:
    point: tuple[float, float]
    wall_ids: list[str]
    endpoint_roles: list[str]


class RoomPolygonScanner:
    """Kapali oda poligonlarindan duvar adaylari uretir (taslak / dogrulama araci).

    Uretilen segmentler context.json'a otomatik yazilmaz; ajan veya kullanici
    onayindan sonra tasarim verisine eklenir.
    """

    def __init__(self, units: str = "mm", catalog: WallCatalog | None = None):
        self.units = units
        self.catalog = catalog or WallCatalog()

    def scan_edges(self, rooms: list[dict]) -> list[ScannedEdge]:
        edge_rooms: dict[tuple, list[str]] = {}
        edge_geom: dict[tuple, tuple] = {}

        for room in rooms:
            poly = room["polygon"]
            rid = room["id"]
            n = len(poly)
            for i in range(n):
                p1, p2 = poly[i], poly[(i + 1) % n]
                key = segment_key(p1, p2, self.units)
                edge_rooms.setdefault(key, []).append(rid)
                edge_geom[key] = (tuple(p1), tuple(p2))

        result: list[ScannedEdge] = []
        for key, room_ids in edge_rooms.items():
            p1, p2 = edge_geom[key]
            result.append(
                ScannedEdge(
                    start=p1,
                    end=p2,
                    room_ids=sorted(set(room_ids)),
                    shared=len(set(room_ids)) > 1,
                    length=vec_len(vec_sub(p2, p1)),
                )
            )
        return sorted(result, key=lambda e: (-e.length, e.start))

    def suggest_wall_dicts(
        self,
        rooms: list[dict],
        *,
        interior_kind: str = "bolme",
        exterior_kind: str = "dis_tasiyici",
        id_prefix: str = "scan",
    ) -> list[dict]:
        """Paylasilan kenar = ic bolme, tek oda = dis (basit sezgisel — kullanici duzeltir)."""
        interior = self.catalog.get(interior_kind) or WallTypeSpec(
            interior_kind, "Bolme", 100.0, "DUVAR"
        )
        exterior = self.catalog.get(exterior_kind) or WallTypeSpec(
            exterior_kind, "Dis", 250.0, "DUVAR"
        )
        walls = []
        for i, edge in enumerate(self.scan_edges(rooms)):
            spec = interior if edge.shared else exterior
            walls.append(
                {
                    "id": f"{id_prefix}_{i}",
                    "start": list(edge.start),
                    "end": list(edge.end),
                    "thickness": spec.default_thickness_mm,
                    "layer": spec.layer,
                    "kind": spec.id,
                }
            )
        return walls


class NetworkTopologyScanner:
    """Mevcut duvar listesinde birlesim noktalarini raporlar (validate destegi)."""

    def __init__(self, units: str = "mm"):
        self.units = units

    def junctions(self, wall_dicts: list[dict]) -> list[JunctionReport]:
        groups: dict[tuple[float, float], list[tuple[str, str]]] = {}
        for w in wall_dicts:
            for which, pt in (("start", w["start"]), ("end", w["end"])):
                key = round_point(pt, self.units)
                groups.setdefault(key, []).append((w["id"], which))

        reports = []
        for pt, entries in groups.items():
            if len(entries) < 2:
                continue
            reports.append(
                JunctionReport(
                    point=pt,
                    wall_ids=[e[0] for e in entries],
                    endpoint_roles=[e[1] for e in entries],
                )
            )
        return reports
