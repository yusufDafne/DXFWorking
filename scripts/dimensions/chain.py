"""Ardisik nokta ciftlerini gercek DXF olculerine ceviren zincir."""
from __future__ import annotations

from .linear import LinearDim
from .style import DimensionStyle

# Bu mesafeden daha yakin iki ordinat AYNI nokta sayilir. Olmazsa sifir
# uzunluklu bir olcu ("0" metni) uretilir; gercek cizimde bu, ust uste binmis
# iki duvar yuzu demektir ve olcu olarak gosterilmesi anlamsizdir.
ORDINATE_TOLERANCE = 1.0


def merge_ordinates(values, tolerance: float = ORDINATE_TOLERANCE) -> list[float]:
    """Sirali, tekillestirilmis ordinat listesi.

    Deterministiktir: ayni girdi her zaman ayni listeyi verir."""
    merged: list[float] = []
    for value in sorted(float(v) for v in values):
        if not merged or abs(value - merged[-1]) > tolerance:
            merged.append(value)
    return merged


class DimensionChain:
    """Render adjacent point pairs as real DXF linear dimensions."""

    def __init__(self, points: list[tuple[float, float]], base_offset: float,
                 angle: float, style: DimensionStyle | None = None,
                 label: str = ""):
        self.points = points
        self.base_offset = base_offset
        self.angle = angle
        self.style = style or DimensionStyle()
        # Yalnizca teshis/rapor icindir; cizime yazilmaz.
        self.label = label

    def __len__(self) -> int:
        return max(0, len(self.points) - 1)

    def render(self, msp, edge_coordinate: float | None = None) -> None:
        for p1, p2 in zip(self.points, self.points[1:]):
            if self.angle == 0:
                base = (p1[0], self.base_offset)
            else:
                base = (self.base_offset, p1[1])
            LinearDim(p1, p2, base, self.angle, self.style).render(msp)

    def with_offset(self, base_offset: float) -> "DimensionChain":
        return DimensionChain(self.points, base_offset, self.angle, self.style,
                              self.label)

    @classmethod
    def horizontal(cls, coordinates: list[float], edge_y: float, dim_y: float,
                   style=None, label: str = "") -> "DimensionChain":
        return cls([(x, edge_y) for x in merge_ordinates(coordinates)],
                   dim_y, 0, style, label)

    @classmethod
    def vertical(cls, coordinates: list[float], edge_x: float, dim_x: float,
                 style=None, label: str = "") -> "DimensionChain":
        return cls([(edge_x, y) for y in merge_ordinates(coordinates)],
                   dim_x, 90, style, label)
