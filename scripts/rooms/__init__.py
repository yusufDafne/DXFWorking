"""Validated room geometry views and deterministic room labels."""
from __future__ import annotations

from dataclasses import dataclass

from ezdxf.enums import TextEntityAlignment
try:
    from ..pafta import fit_text_height
    from ..walls.scan import RoomPolygonScanner
except ImportError:
    from pafta import fit_text_height
    from walls.scan import RoomPolygonScanner


class PolygonOps:
    @staticmethod
    def signed_area(polygon: list[list[float]]) -> float:
        return 0.5 * sum(
            polygon[i][0] * polygon[(i + 1) % len(polygon)][1]
            - polygon[(i + 1) % len(polygon)][0] * polygon[i][1]
            for i in range(len(polygon))
        )

    @staticmethod
    def area(polygon: list[list[float]]) -> float:
        return abs(PolygonOps.signed_area(polygon))

    @staticmethod
    def centroid(polygon: list[list[float]]) -> tuple[float, float]:
        signed_area = PolygonOps.signed_area(polygon)
        if abs(signed_area) < 1e-9:
            xs = [point[0] for point in polygon]
            ys = [point[1] for point in polygon]
            return sum(xs) / len(xs), sum(ys) / len(ys)
        factor = 1.0 / (6.0 * signed_area)
        cx = cy = 0.0
        for i, point in enumerate(polygon):
            next_point = polygon[(i + 1) % len(polygon)]
            cross = point[0] * next_point[1] - next_point[0] * point[1]
            cx += (point[0] + next_point[0]) * cross
            cy += (point[1] + next_point[1]) * cross
        return cx * factor, cy * factor

    @staticmethod
    def is_closed(polygon: list[list[float]]) -> bool:
        # Context polygons are implicitly closed by the renderer.
        return len(polygon) >= 3

    @staticmethod
    def has_self_intersection(polygon: list[list[float]]) -> bool:
        def orientation(a, b, c):
            value = (b[1] - a[1]) * (c[0] - b[0]) - (b[0] - a[0]) * (c[1] - b[1])
            return (value > 0) - (value < 0)

        def intersects(a, b, c, d):
            return orientation(a, b, c) != orientation(a, b, d) and orientation(c, d, a) != orientation(c, d, b)

        edges = list(zip(polygon, polygon[1:] + polygon[:1]))
        for index, (a, b) in enumerate(edges):
            for other_index, (c, d) in enumerate(edges):
                if other_index <= index or other_index in {index - 1, index + 1}:
                    continue
                if index == 0 and other_index == len(edges) - 1:
                    continue
                if intersects(a, b, c, d):
                    return True
        return False


@dataclass(frozen=True)
class Room:
    id: str
    name: str
    area_m2: float
    polygon: list[list[float]]
    layer: str = "METIN"

    @classmethod
    def from_context(cls, data: dict, units: str = "mm") -> "Room":
        room = cls(
            id=data["id"],
            name=data["name"],
            area_m2=float(data["area_m2"]),
            polygon=data["polygon"],
            layer=data.get("layer", "METIN"),
        )
        if not PolygonOps.is_closed(room.polygon) or PolygonOps.area(room.polygon) <= 0:
            raise ValueError(f"Invalid room polygon: {room.id}")
        if PolygonOps.has_self_intersection(room.polygon):
            raise ValueError(f"Self-intersecting room polygon: {room.id}")
        unit_factor = 1_000_000.0 if units == "mm" else 1.0
        calculated_area_m2 = PolygonOps.area(room.polygon) / unit_factor
        if round(calculated_area_m2, 1) != round(room.area_m2, 1):
            raise ValueError(f"Room area mismatch: {room.id}")
        return room

    def centroid(self) -> tuple[float, float]:
        return PolygonOps.centroid(self.polygon)


class RoomLabeler:
    @staticmethod
    def content(room: Room | dict) -> str:
        data = room if isinstance(room, dict) else room.__dict__
        return f"{data['name']} ({data['area_m2']:.1f} m2)"

    @staticmethod
    def draw(msp, room: Room | dict, max_text_height: float, units: str = "mm") -> None:
        data = room if isinstance(room, dict) else room.__dict__
        Room.from_context(data, units)
        polygon = data["polygon"]
        cx, cy = PolygonOps.centroid(polygon)
        content = RoomLabeler.content(room)
        xs = [point[0] for point in polygon]
        available_width = max(0.0, max(xs) - min(xs) - 200.0)
        height = fit_text_height(content, available_width, max_text_height, min_height=60.0)
        text = msp.add_text(content, dxfattribs={"layer": data.get("layer", "METIN"), "height": height})
        text.set_placement((cx, cy), align=TextEntityAlignment.MIDDLE_CENTER)


__all__ = ["PolygonOps", "Room", "RoomLabeler", "RoomPolygonScanner"]
