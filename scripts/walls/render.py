"""Duvar rail cizimi ve aciklik sembolleri — standart degistirilebilir."""
from __future__ import annotations

try:
	from ..openings import DefaultPlanOpeningStyle, OpeningSymbolStyle
except ImportError:
	from openings import DefaultPlanOpeningStyle, OpeningSymbolStyle
from .network import WallNetwork, gaps_for_wall
from .standard import CatalogRailStandard, RailDrawingStandard


def draw_wall_network(
	msp,
	network: WallNetwork,
	openings: list[dict],
	*,
	opening_style: OpeningSymbolStyle | None = None,
	rail_standard: RailDrawingStandard | None = None,
) -> None:
	style = opening_style or DefaultPlanOpeningStyle()
	rails = rail_standard or CatalogRailStandard()
	for wall in network.walls:
		rails.draw_rails(msp, wall, network, openings)

		for g_start, g_end, opening in gaps_for_wall(wall, openings):
			style.draw_opening(msp, wall, g_start, g_end, opening)
