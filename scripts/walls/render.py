"""Duvar rail cizimi ve aciklik sembolleri — standart degistirilebilir."""
from __future__ import annotations

import math
from typing import Protocol

from .geometry import vec_add, vec_scale
from .network import WallNetwork, gaps_for_wall


class OpeningSymbolStyle(Protocol):
    """Kapı/pencere plan sembolu; farkli ofis standardi = farkli uygulama."""

    def draw_opening(self, msp, wall, g_start: float, g_end: float, opening: dict) -> None: ...


class DefaultPlanOpeningStyle:
    """Mevcut proje standardi: kapi kanat+kavis, pencere cift paralel cizgi."""

    def draw_opening(self, msp, wall, g_start: float, g_end: float, opening: dict) -> None:
        op_layer = opening.get("layer", "KAPI-PENCERE")
        perp = wall.normal

        for s in (g_start, g_end):
            msp.add_line(
                wall.rail_point("pos", s),
                wall.rail_point("neg", s),
                dxfattribs={"layer": wall.layer},
            )

        hinge = wall.centerline_point(g_start)
        far = wall.centerline_point(g_end)
        width = g_end - g_start

        if opening["type"] == "door":
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
        else:
            offset = wall.thickness / 4.0
            for sign in (-1, 1):
                off_vec = vec_scale(perp, sign * offset)
                msp.add_line(
                    vec_add(hinge, off_vec),
                    vec_add(far, off_vec),
                    dxfattribs={"layer": op_layer},
                )


def draw_wall_network(
    msp,
    network: WallNetwork,
    openings: list[dict],
    *,
    opening_style: OpeningSymbolStyle | None = None,
) -> None:
    style = opening_style or DefaultPlanOpeningStyle()
    for wall in network.walls:
        for side in ("pos", "neg"):
            for p1, p2 in network.drawable_rail_segments(wall, side, openings):
                msp.add_line(p1, p2, dxfattribs={"layer": wall.layer})

        for g_start, g_end, op in gaps_for_wall(wall, openings):
            style.draw_opening(msp, wall, g_start, g_end, op)
