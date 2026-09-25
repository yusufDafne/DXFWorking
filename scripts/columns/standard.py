"""Kolon layer adlari, sabit rengi ve tarama/isimlendirme varsayilanlari.

Renk ve layer adlari KOD sahipligindedir, context.json'dan alinmaz
(`ensure_axis_layer` deseni). Renkler artik scripts/palette::PALETTE'in TEK
kaynagindan gelir (DEV-030) - kontur/tarama/metin ARTIK 3 FARKLI tondur
(DEV-030 ONCESI ucu de AYNI COLUMN_RGB'yi kullaniyordu, bu somut bulgu
DEV-030'un kurulma nedenlerinden biriydi, bkz. scripts/palette/CLAUDE.md).
"""
from __future__ import annotations

try:
    from ..palette import color_for
except ImportError:  # dogrudan scripts/ uzerinden calistirildiginda
    from palette import color_for

COLUMN_LAYER = "KOLON"
COLUMN_HATCH_LAYER = "KOLON-TARAMA"
COLUMN_TEXT_LAYER = "KOLON-METIN"
COLUMN_RGB = color_for(COLUMN_LAYER)
COLUMN_HATCH_RGB = color_for(COLUMN_HATCH_LAYER)
COLUMN_TEXT_RGB = color_for(COLUMN_TEXT_LAYER)

DEFAULT_HATCH_PATTERN = "ANSI33"
DEFAULT_HATCH_SCALE = 3.0
