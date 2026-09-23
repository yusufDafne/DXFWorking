"""Kolon layer adlari, sabit rengi ve tarama/isimlendirme varsayilanlari.

Renk ve layer adlari KOD sahipligindedir, context.json'dan alinmaz
(`ensure_axis_layer` deseni).
"""
from __future__ import annotations

COLUMN_LAYER = "KOLON"
COLUMN_HATCH_LAYER = "KOLON-TARAMA"
COLUMN_TEXT_LAYER = "KOLON-METIN"
COLUMN_RGB = (90, 90, 96)

DEFAULT_HATCH_PATTERN = "ANSI33"
DEFAULT_HATCH_SCALE = 3.0
