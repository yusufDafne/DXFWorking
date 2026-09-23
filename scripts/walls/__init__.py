"""Duvar modulu: cift-rail geometri, ag birlesimi, katalog, cizim ve tarama.

scripts/generate_dxf.py `WallNetwork`, `draw_wall_network` ve ilgili tipleri
buradan import eder. Detay: scripts/walls/CLAUDE.md
"""
from .catalog import DEFAULT_WALL_CATALOG, WallCatalog, WallTypeSpec
from .network import WallNetwork, gaps_for_wall
from .render import DefaultPlanOpeningStyle, OpeningSymbolStyle, draw_wall_network
from .scan import JunctionReport, NetworkTopologyScanner, RoomPolygonScanner, ScannedEdge
from .wall import Wall

__all__ = [
    "DEFAULT_WALL_CATALOG",
    "DefaultPlanOpeningStyle",
    "JunctionReport",
    "NetworkTopologyScanner",
    "OpeningSymbolStyle",
    "RoomPolygonScanner",
    "ScannedEdge",
    "Wall",
    "WallCatalog",
    "WallNetwork",
    "WallTypeSpec",
    "draw_wall_network",
    "gaps_for_wall",
]
