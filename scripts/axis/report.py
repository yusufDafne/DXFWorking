"""Kolon rasterine gore aks KAPSAMA raporu (DEV-015 Fikir 1).

**Salt okunurdur.** Kok CLAUDE.md, turetilmis geometrinin context'e
yazilmasini yasaklar; bu yuzden modul aks EKLEMEZ, yalnizca "su kolon
hizasinda aks yok" der. Kullanici raporu okur ve isterse context'e kendi
aksini ekler.

`columns.ColumnGrid.on_axis_report` bunun TERSIDIR: o, "hangi kolon hangi aks
kesisiminde" der. Ikisi birlikte kolon-aks capraz kontrolunu tamamlar
(bkz. `scripts/CLAUDE.md` capraz nokta tablosu).
"""
from __future__ import annotations

from dataclasses import dataclass, field

DEFAULT_TOLERANCE = 1.0


@dataclass
class AxisCoverageReport:
    """Aks'siz kolon hizalari. Bos ise raster tamamen akslanmistir."""

    missing_vertical: list[float] = field(default_factory=list)
    missing_horizontal: list[float] = field(default_factory=list)
    floor_code: str = ""

    @property
    def ok(self) -> bool:
        return not self.missing_vertical and not self.missing_horizontal

    @classmethod
    def from_columns(cls, columns: list[dict], vertical_axes: list[dict],
                     horizontal_axes: list[dict], floor_code: str = "",
                     tolerance: float = DEFAULT_TOLERANCE) -> "AxisCoverageReport":
        xs = [float(axis["position"]) for axis in vertical_axes]
        ys = [float(axis["position"]) for axis in horizontal_axes]

        def uncovered(values: list[float], axes: list[float]) -> list[float]:
            missing: list[float] = []
            for value in values:
                if any(abs(value - axis) <= tolerance for axis in axes):
                    continue
                if any(abs(value - other) <= tolerance for other in missing):
                    continue
                missing.append(value)
            return sorted(missing)

        column_xs = [float(c["position"][0]) for c in columns]
        column_ys = [float(c["position"][1]) for c in columns]
        return cls(
            missing_vertical=uncovered(column_xs, xs),
            missing_horizontal=uncovered(column_ys, ys),
            floor_code=floor_code,
        )

    def lines(self) -> list[str]:
        where = f"[{self.floor_code}] " if self.floor_code else ""
        messages: list[str] = []
        if self.missing_vertical:
            values = ", ".join(f"{v:.0f}" for v in self.missing_vertical)
            messages.append(
                f"{where}Kolon rasterinde aks'siz DUSEY hiza: x = {values}. "
                f"Aks eklenip eklenmeyecegi KULLANICI kararidir; sistem "
                f"context'e aks yazmaz."
            )
        if self.missing_horizontal:
            values = ", ".join(f"{v:.0f}" for v in self.missing_horizontal)
            messages.append(
                f"{where}Kolon rasterinde aks'siz YATAY hiza: y = {values}."
            )
        return messages
