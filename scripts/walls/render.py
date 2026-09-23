"""Duvar rail cizimi ve aciklik sembolleri — standart degistirilebilir."""
from __future__ import annotations

try:
	from ..openings import DefaultPlanOpeningStyle, OpeningSymbolStyle
except ImportError:
	from openings import DefaultPlanOpeningStyle, OpeningSymbolStyle
from .network import WallNetwork, gaps_for_wall


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

		for g_start, g_end, opening in gaps_for_wall(wall, openings):
			style.draw_opening(msp, wall, g_start, g_end, opening)

