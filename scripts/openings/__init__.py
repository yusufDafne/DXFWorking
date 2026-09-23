"""Aciklik (kapi/pencere) modulu: tipli veri, varyant sembolleri, acilim yonu
ve salt-okunur cetvel.

rev-13 (DEV-016) ile eklenenler - **hepsinin varsayilani rev-12 davranisidir**,
yani mevcut projeler hicbir sey degistirmeden ayni cizimi uretir:

- **Varyant sembolleri** (Fikir 1): `single`, `double`, `sliding`, `folding`.
  Secim veri odaklidir (`symbols.DOOR_SYMBOLS`); yeni varyant icin alt sinif
  gerekmez.
- **Acilim yonu** (Fikir 2): `swing` (mentese duvar basinda mi sonunda mi) ve
  `host_side` (kanat hangi tarafa aciliyor). Onceden yon geometriden SABIT
  turetiliyordu.
- **`geometry.swing_geometry`**: acilim yayinin TEK sahibi. Hem cizim
  (`symbols.py`) hem cakisma denetimi (`collision.py`) buradan okur; iki yerde
  ayri hesaplansaydi cizilen yay ile denetlenen alan ayrisirdi.

Detay: `scripts/openings/CLAUDE.md`.
"""
from __future__ import annotations

from .geometry import SwingGeometry, side_sign, swing_geometry
from .opening import (
    DOOR_VARIANTS,
    SIDE_NEG,
    SIDE_POS,
    SIDES,
    SWING_LEFT,
    SWING_RIGHT,
    SWINGS,
    TYPE_DOOR,
    TYPE_WINDOW,
    VARIANT_DOUBLE,
    VARIANT_FOLDING,
    VARIANT_SINGLE,
    VARIANT_SLIDING,
    Door,
    Opening,
    Window,
)
from .schedule import OpeningSchedule
from .style import DefaultPlanOpeningStyle, OpeningSymbolStyle
from .symbols import ARCS_PER_VARIANT, DOOR_SYMBOLS

# Bu modulun CONTEXT SOZLESMESI surumu (DEV-020). KOD surumu DEGILDIR:
# yalnizca bu modulun context.json'dan OKUDUGU alanlar degistiginde artar;
# refactor artirmaz. rev-13'te `variant` / `swing` / `host_side` okunmaya
# baslandigi icin 1.0 -> 1.1 (geriye uyumlu: hepsi opsiyonel ve varsayilanlari
# eski davranisi verir).
CONTRACT_VERSION = "1.1"

__all__ = [
    "ARCS_PER_VARIANT",
    "DOOR_SYMBOLS",
    "DOOR_VARIANTS",
    "SIDES",
    "SIDE_NEG",
    "SIDE_POS",
    "SWINGS",
    "SWING_LEFT",
    "SWING_RIGHT",
    "TYPE_DOOR",
    "TYPE_WINDOW",
    "VARIANT_DOUBLE",
    "VARIANT_FOLDING",
    "VARIANT_SINGLE",
    "VARIANT_SLIDING",
    "DefaultPlanOpeningStyle",
    "Door",
    "Opening",
    "OpeningSchedule",
    "OpeningSymbolStyle",
    "SwingGeometry",
    "Window",
    "side_sign",
    "swing_geometry",
]
