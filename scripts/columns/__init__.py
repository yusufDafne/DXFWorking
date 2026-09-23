"""Kolon modulu: parametrik kesit, TARAMA (hatch) ve aks kesisimine oturma.

Tasarim kararlari (kullanici talebi, DEV-010):

- **Kolonlar TARALIDIR.** Tarama deseni ve olcegi DINAMIKTIR
  (`ColumnHatchStyle`), ancak makul bir varsayilani vardir: `ANSI33`,
  olcek `3.0`. Farkli bir desen/olcek istendiginde alt sinif gerekmez,
  farkli bir stil nesnesi verilir.
- **Kolon isimlendirme SIMDILIK KAPALI ama desteklenir.** Kullanici kolonlari
  aks birlesim noktalariyla ifade etmeyi tercih ediyor; bu yuzden
  `ColumnLabelStyle.enabled` varsayilan olarak `False`. Ileride ad istendiginde
  `Column.name` doldurulur ve stil acilir - cizim kodu degismez.
- **Konum uydurulmaz.** Kolon konumu ve kesiti context.json'dan gelir. Bu
  modul aks verisini TUKETIR, aks/duvar/oda sorumlulugunu ustlenmez.
"""

from __future__ import annotations

from .column import Column
from .render import ColumnGrid, ColumnRenderer, ensure_column_layers
from .section import DEFAULT_COLUMN_CATALOG, ColumnSection, ColumnSectionCatalog
from .standard import (
    COLUMN_HATCH_LAYER,
    COLUMN_LAYER,
    COLUMN_RGB,
    COLUMN_TEXT_LAYER,
    DEFAULT_HATCH_PATTERN,
    DEFAULT_HATCH_SCALE,
)
from .style import ColumnHatchStyle, ColumnLabelStyle

# Bu modulun CONTEXT SOZLESMESI surumu (DEV-020). KOD surumu DEGILDIR:
# yalnizca bu modulun context.json'dan OKUDUGU alanlar degistiginde artar;
# refactor artirmaz. Bkz. scripts/version.py
CONTRACT_VERSION = "1.0"

__all__ = [
    "COLUMN_HATCH_LAYER",
    "COLUMN_LAYER",
    "COLUMN_RGB",
    "COLUMN_TEXT_LAYER",
    "DEFAULT_COLUMN_CATALOG",
    "DEFAULT_HATCH_PATTERN",
    "DEFAULT_HATCH_SCALE",
    "Column",
    "ColumnGrid",
    "ColumnHatchStyle",
    "ColumnLabelStyle",
    "ColumnRenderer",
    "ColumnSection",
    "ColumnSectionCatalog",
    "ensure_column_layers",
]
