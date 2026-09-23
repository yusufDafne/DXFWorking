"""Structured opening data and injectable plan/elevation symbol styles."""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Protocol



def _add(point, vector):
    return point[0] + vector[0], point[1] + vector[1]


def _scale(vector, factor):
    return vector[0] * factor, vector[1] * factor


@dataclass(frozen=True)
class Opening:
    id: str
    type: str
    wall_id: str
    position_from_start: float
    width: float
    layer: str = "KAPI-PENCERE"

    @classmethod
    def from_context(cls, data: dict) -> "Opening":
        return cls(
            id=data["id"],
            type=data["type"],
            wall_id=data["wall_id"],
            position_from_start=float(data["position_from_start"]),
            width=float(data["width"]),
            layer=data.get("layer", "KAPI-PENCERE"),
        )

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "wall_id": self.wall_id,
            "position_from_start": self.position_from_start,
            "width": self.width,
            "layer": self.layer,
        }


class Door(Opening):
    """Door marker retaining the current schema-compatible opening shape."""


class Window(Opening):
    """Window marker retaining the current schema-compatible opening shape."""


class OpeningSymbolStyle(Protocol):
    def draw_opening(self, msp, wall, g_start: float, g_end: float, opening: dict) -> None: ...


class DefaultPlanOpeningStyle:
    """Current office plan style: door leaf/arc and paired window lines."""

    def draw_opening(self, msp, wall, g_start: float, g_end: float, opening: dict) -> None:
        op_layer = opening.get("layer", "KAPI-PENCERE")
        perp = wall.normal
        for position in (g_start, g_end):
            msp.add_line(
                wall.rail_point("pos", position),
                wall.rail_point("neg", position),
                dxfattribs={"layer": wall.layer},
            )

        hinge = wall.centerline_point(g_start)
        far = wall.centerline_point(g_end)
        width = g_end - g_start
        if opening["type"] == "door":
            leaf_end = _add(hinge, _scale(perp, width))
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
        else:
            offset = wall.thickness / 4.0
            for sign in (-1, 1):
                off_vec = _scale(perp, sign * offset)
                msp.add_line(
                    _add(hinge, off_vec),
                    _add(far, off_vec),
                    dxfattribs={"layer": op_layer},
                )


class OpeningSchedule:
    """Deterministic, read-only schedule rows derived from validated openings."""

    @staticmethod
    def from_openings(openings: list[dict | Opening]) -> list[dict]:
        rows = []
        for opening in openings:
            data = opening.as_dict() if isinstance(opening, Opening) else opening
            rows.append({
                "id": data["id"],
                "type": data["type"],
                "wall_id": data["wall_id"],
                "width": data["width"],
            })
        return sorted(rows, key=lambda row: (row["type"], row["id"]))


# Bu modulun CONTEXT SOZLESMESI surumu (DEV-020). KOD surumu DEGILDIR:
# yalnizca bu modulun context.json'dan OKUDUGU alanlar degistiginde artar;
# refactor artirmaz. Bkz. scripts/version.py
CONTRACT_VERSION = "1.0"

__all__ = [
    "Door",
    "DefaultPlanOpeningStyle",
    "Opening",
    "OpeningSchedule",
    "OpeningSymbolStyle",
    "Window",
]
