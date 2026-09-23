"""Olculendirme modulu: gercek DXF olcu varliklari, kademelendirme ve
geometriden olcu turetme.

rev-13'e (DEV-017) kadar bu modul yalnizca `AxisGrid`in tuketicisiydi ve tek
dosyadan ibaretti. Iki yetenek eklendi:

- **`ChainStack`** (Fikir 2): ayni kenardaki birden fazla zincir deterministik
  olarak KADEMELENDIRILIR. Once `ChainLayout` yalnizca sinir kontrolu
  yapiyordu; ayni baseline'a oturan iki zincir sessizce ust uste biniyordu.
  Artik bu bir HATADIR (`ChainLayout.verify_no_overlap`).
- **`FloorOrdinates` / `FloorDimensionPlanner`** (Fikir 1): kat geometrisinden
  aciklik / mahal / toplam kademelerinde olcu ordinatlari TURETILIR. Olcu
  sayisi uydurulmaz - context geometrisinden olculur; hangi kenarin
  olculenecegi ise `meta.dimensions` ile bildirilen bir SUNUM kararidir.

Detay: `scripts/dimensions/CLAUDE.md`.
"""
from __future__ import annotations

from .chain import ORDINATE_TOLERANCE, DimensionChain, merge_ordinates
from .derive import (
    AXIS_X,
    AXIS_Y,
    DEFAULT_LEVELS,
    LEVEL_OPENING,
    LEVEL_ROOM,
    LEVEL_TOTAL,
    FloorOrdinates,
)
from .layout import ChainLayout, ChainStack
from .linear import LinearDim
from .plan import DimensionSettings, FloorDimensionPlanner
from .style import DIMENSION_LAYER, DimensionStyle, format_dimension_cm

# Bu modulun CONTEXT SOZLESMESI surumu (DEV-020). KOD surumu DEGILDIR:
# yalnizca bu modulun context.json'dan OKUDUGU alanlar degistiginde artar;
# refactor artirmaz. rev-13'te `meta.dimensions` okunmaya baslandigi icin
# 1.0 -> 1.1 (geriye uyumlu: alan opsiyonel ve varsayilani KAPALI).
CONTRACT_VERSION = "1.1"

__all__ = [
    "AXIS_X",
    "AXIS_Y",
    "DEFAULT_LEVELS",
    "DIMENSION_LAYER",
    "LEVEL_OPENING",
    "LEVEL_ROOM",
    "LEVEL_TOTAL",
    "ORDINATE_TOLERANCE",
    "ChainLayout",
    "ChainStack",
    "DimensionChain",
    "DimensionSettings",
    "DimensionStyle",
    "FloorDimensionPlanner",
    "FloorOrdinates",
    "LinearDim",
    "format_dimension_cm",
    "merge_ordinates",
]
