"""Aks (grid) modulu: kesikli aks cizgisi, tegetli baloncuk, olcu zinciri,
KISMI aks ve kolon rasteri kapsama raporu.

rev-13 (DEV-015) ile eklenenler:

- **Kismi aks** (`grid.*_axes[].extent`): bir aks artik yapinin tamamini kat
  etmek zorunda degildir. Kismi bir aks kenar olcu zincirine GIRMEZ - o kenara
  ulasmayan bir aksi olculuyormus gibi gostermek yaniltici olurdu.
- **Ara aks etiketi** `1'` olarak KARARA BAGLANDI (`naming.py`); `1A`
  yasaktir cunku yatay aks ailesiyle (A, B, C) ve kolon adlandirmasiyla
  (`B2`) carpisir. Kural `validate.py` icinde mekanik olarak denetlenir.
- **`AxisCoverageReport`** (Fikir 1): kolon rasterinde aks'siz kalan hizalari
  SALT OKUNUR olarak bildirir; aks EKLEMEZ, context'e yazmaz.
- Aks olcu zinciri artik `dimensions` yiginin **DISINDA** durur; ofset ve
  uzama `generate_dxf.py` tarafindan `DimensionSettings`e sorularak verilir
  (iki modul birbirini import etmez).

Detay: `scripts/axis/CLAUDE.md`.
"""
from __future__ import annotations

from .axis import INTERMEDIATE_SUFFIX, Axis, axes_from_context
from .grid import AxisGrid
from .naming import check_labels
from .report import AxisCoverageReport
from .standard import (
    AXIS_LAYER,
    AXIS_LINETYPE,
    AXIS_RGB,
    AxisDrawingStandard,
    ensure_axis_layer,
    ensure_dashed_linetype,
)

# Bu modulun CONTEXT SOZLESMESI surumu (DEV-020). KOD surumu DEGILDIR:
# yalnizca bu modulun context.json'dan OKUDUGU alanlar degistiginde artar;
# refactor artirmaz. rev-13'te `grid.*_axes[].extent` okunmaya baslandigi icin
# 1.0 -> 1.1 (geriye uyumlu: alan opsiyonel).
CONTRACT_VERSION = "1.1"

__all__ = [
    "AXIS_LAYER",
    "AXIS_LINETYPE",
    "AXIS_RGB",
    "INTERMEDIATE_SUFFIX",
    "Axis",
    "AxisCoverageReport",
    "AxisDrawingStandard",
    "AxisGrid",
    "axes_from_context",
    "check_labels",
    "ensure_axis_layer",
    "ensure_dashed_linetype",
]
