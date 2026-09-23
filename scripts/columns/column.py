"""Bir kolon yerlesimi - PROJE VERISIDIR, context.json'dan gelir.

`position` kolonun MERKEZIDIR (tefriste sol-alt kosedir; bilincli fark -
kolon simetrik bir tasiyicidir ve aks kesisimine merkezinden oturur).
"""
from __future__ import annotations

from dataclasses import dataclass, replace

from .section import ColumnSection, ColumnSectionCatalog

@dataclass(frozen=True)
class Column:
    """Bir kolon yerlesimi. `position` kolonun MERKEZIDIR.

    `name` opsiyoneldir ve bugun cizilmez (bkz. `ColumnLabelStyle`); kullanici
    kolonlari aks kesisimiyle ifade ediyor. Alan yine de tasinir ki
    isimlendirme istendiginde veri yolu hazir olsun."""

    id: str
    position: tuple[float, float]
    section: ColumnSection
    rotation: float = 0.0
    name: str = ""

    @classmethod
    def from_context(cls, data: dict, catalog: ColumnSectionCatalog) -> "Column":
        if "section" in data:
            section = catalog.get(data["section"])
        else:
            section = ColumnSection(
                key=f"{data['id']}_custom",
                width=float(data["width"]),
                depth=float(data["depth"]),
                shape=str(data.get("shape", "rect")),
            )
        column = cls(
            id=data["id"],
            position=(float(data["position"][0]), float(data["position"][1])),
            section=section,
            rotation=float(data.get("rotation", 0.0)),
            name=str(data.get("name", "") or ""),
        )
        if section.width <= 0 or section.depth <= 0:
            raise ValueError(f"Kolon '{column.id}' kesit olcusu pozitif olmali.")
        return column

    def translated(self, dx: float) -> "Column":
        return replace(self, position=(self.position[0] + dx, self.position[1]))

    def corners(self) -> list[tuple[float, float]]:
        """Donme uygulanmis kose noktalari (dikdortgen kesit icin)."""
        import math

        half_w, half_d = self.section.width / 2.0, self.section.depth / 2.0
        angle = math.radians(self.rotation)
        cos_a, sin_a = math.cos(angle), math.sin(angle)
        cx, cy = self.position
        points = []
        for dx, dy in ((-half_w, -half_d), (half_w, -half_d),
                       (half_w, half_d), (-half_w, half_d)):
            points.append((cx + dx * cos_a - dy * sin_a,
                           cy + dx * sin_a + dy * cos_a))
        return points
