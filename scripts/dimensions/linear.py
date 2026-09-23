"""Tek bir gercek DXF `LINEAR DIMENSION` varligi."""
from __future__ import annotations

from dataclasses import dataclass

from .style import DimensionStyle, format_dimension_cm


@dataclass(frozen=True)
class LinearDim:
    p1: tuple[float, float]
    p2: tuple[float, float]
    base: tuple[float, float]
    angle: float
    style: DimensionStyle = DimensionStyle()

    @property
    def length(self) -> float:
        return ((self.p2[0] - self.p1[0]) ** 2 + (self.p2[1] - self.p1[1]) ** 2) ** 0.5

    def render(self, msp):
        dimension = msp.add_linear_dim(
            base=self.base,
            p1=self.p1,
            p2=self.p2,
            angle=self.angle,
            dimstyle="Standard",
            override=self.style.override(),
            text=format_dimension_cm(self.length),
            dxfattribs={"layer": self.style.layer},
        )
        dimension.render()
        return dimension
