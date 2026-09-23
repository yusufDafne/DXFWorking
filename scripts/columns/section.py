"""Kolon kesiti ve kesit katalogu.

Katalog veri odaklidir: farkli bir kesit seti icin alt sinif degil, farkli bir
sozluk verilir (`WallCatalog` deseni).
"""
from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True)
class ColumnSection:
    """Kolon kesiti. `shape`: 'rect' veya 'circle'."""

    key: str
    width: float
    depth: float
    shape: str = "rect"

    @property
    def radius(self) -> float:
        return min(self.width, self.depth) / 2.0


DEFAULT_COLUMN_CATALOG: dict[str, ColumnSection] = {
    section.key: section for section in (
        ColumnSection("S30x60", 300.0, 600.0),
        ColumnSection("S40x40", 400.0, 400.0),
        ColumnSection("S40x80", 400.0, 800.0),
        ColumnSection("S50x50", 500.0, 500.0),
        ColumnSection("S60x60", 600.0, 600.0),
        ColumnSection("D40", 400.0, 400.0, "circle"),
        ColumnSection("D50", 500.0, 500.0, "circle"),
    )
}


class ColumnSectionCatalog:
    """Kesit adi -> `ColumnSection`. Veri odakli; alt sinif gerekmez."""

    def __init__(self, sections: dict[str, ColumnSection] | None = None):
        self.sections = dict(sections if sections is not None else DEFAULT_COLUMN_CATALOG)

    def __contains__(self, key: str) -> bool:
        return key in self.sections

    def get(self, key: str) -> ColumnSection:
        if key not in self.sections:
            raise KeyError(
                f"Bilinmeyen kolon kesiti: '{key}'. Katalogdaki kesitler: "
                f"{', '.join(sorted(self.sections))}"
            )
        return self.sections[key]

    def keys(self) -> list[str]:
        return sorted(self.sections)
