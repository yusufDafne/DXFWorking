"""Duvar modulu: cift-rail geometri, ag birlesimi, katalog, cizim ve tarama.

scripts/generate_dxf.py `WallNetwork`, `draw_wall_network` ve ilgili tipleri
buradan import eder. Detay: scripts/walls/CLAUDE.md
"""
from .catalog import DEFAULT_WALL_CATALOG, WallCatalog, WallTypeSpec
from .network import WallNetwork, gaps_for_wall
from .render import DefaultPlanOpeningStyle, OpeningSymbolStyle, draw_wall_network
from .scan import JunctionReport, NetworkTopologyScanner, RoomPolygonScanner, ScannedEdge
from .standard import (
    BRICK_HATCH_PATTERN,
    BRICK_KIND,
    GLASS_KIND,
    GLASS_LINETYPE,
    CatalogRailStandard,
    DefaultRailStandard,
    RailDrawingStandard,
    wall_fill_spans,
)
from .thickness import (
    CLASS_EXTERIOR,
    CLASS_INTERIOR,
    DEFAULT_EXTERIOR_THICKNESS_MM,
    INTERIOR_THICKNESS_DELTA_MM,
    check_wall_thickness,
    classify_walls,
    interior_thickness,
)
from .wall import Wall

# Bu modulun CONTEXT SOZLESMESI surumu (DEV-020). KOD surumu DEGILDIR:
# yalnizca bu modulun context.json'dan OKUDUGU alanlar degistiginde artar;
# refactor artirmaz. Bkz. scripts/version.py
CONTRACT_VERSION = "1.0"

__all__ = [
    "CLASS_EXTERIOR",
    "CLASS_INTERIOR",
    "DEFAULT_EXTERIOR_THICKNESS_MM",
    "INTERIOR_THICKNESS_DELTA_MM",
    "check_wall_thickness",
    "classify_walls",
    "interior_thickness",
    "BRICK_HATCH_PATTERN",
    "BRICK_KIND",
    "CatalogRailStandard",
    "DEFAULT_WALL_CATALOG",
    "DefaultPlanOpeningStyle",
    "DefaultRailStandard",
    "GLASS_KIND",
    "GLASS_LINETYPE",
    "JunctionReport",
    "NetworkTopologyScanner",
    "OpeningSymbolStyle",
    "RailDrawingStandard",
    "RoomPolygonScanner",
    "ScannedEdge",
    "Wall",
    "WallCatalog",
    "WallNetwork",
    "WallTypeSpec",
    "draw_wall_network",
    "gaps_for_wall",
    "wall_fill_spans",
]
