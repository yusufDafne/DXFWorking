"""Deterministic DXF dimension chains with millimetre input and cm labels."""
from __future__ import annotations

from dataclasses import dataclass


def format_dimension_cm(mm_value: float) -> str:
    return str(int(round(abs(mm_value) / 10.0)))


@dataclass(frozen=True)
class DimensionStyle:
    layer: str = "AKS"
    text_height: float = 120.0
    arrow_size: float = 84.0
    extension: float = 150.0
    gap: float = 80.0

    def override(self) -> dict:
        return {
            "dimtxt": self.text_height,
            "dimasz": self.arrow_size,
            "dimexo": self.extension,
            "dimexe": self.extension,
            "dimgap": self.gap,
        }


@dataclass(frozen=True)
class LinearDim:
    p1: tuple[float, float]
    p2: tuple[float, float]
    base: tuple[float, float]
    angle: float
    style: DimensionStyle = DimensionStyle()

    def render(self, msp):
        dimension = msp.add_linear_dim(
            base=self.base,
            p1=self.p1,
            p2=self.p2,
            angle=self.angle,
            dimstyle="Standard",
            override=self.style.override(),
            text=format_dimension_cm(
                ((self.p2[0] - self.p1[0]) ** 2 + (self.p2[1] - self.p1[1]) ** 2) ** 0.5
            ),
            dxfattribs={"layer": self.style.layer},
        )
        dimension.render()
        return dimension


class DimensionChain:
    """Render adjacent point pairs as real DXF linear dimensions."""

    def __init__(self, points: list[tuple[float, float]], base_offset: float, angle: float, style: DimensionStyle | None = None):
        self.points = points
        self.base_offset = base_offset
        self.angle = angle
        self.style = style or DimensionStyle()

    def render(self, msp, edge_coordinate: float) -> None:
        for p1, p2 in zip(self.points, self.points[1:]):
            if self.angle == 0:
                base = (p1[0], self.base_offset)
            else:
                base = (self.base_offset, p1[1])
            LinearDim(p1, p2, base, self.angle, self.style).render(msp)

    @classmethod
    def horizontal(cls, coordinates: list[float], edge_y: float, dim_y: float, style=None) -> "DimensionChain":
        return cls([(x, edge_y) for x in coordinates], dim_y, 0, style)

    @classmethod
    def vertical(cls, coordinates: list[float], edge_x: float, dim_x: float, style=None) -> "DimensionChain":
        return cls([(edge_x, y) for y in coordinates], dim_x, 90, style)


class ChainLayout:
    """Deterministic bounds check for dimension-chain placement."""

    @staticmethod
    def place(chains, bounds):
        min_x, min_y, max_x, max_y = bounds
        placed = list(chains)
        for chain in placed:
            if chain.angle == 0 and not min_y <= chain.base_offset <= max_y:
                raise ValueError("Horizontal dimension baseline is outside layout bounds")
            if chain.angle != 0 and not min_x <= chain.base_offset <= max_x:
                raise ValueError("Vertical dimension baseline is outside layout bounds")
            for point in chain.points:
                if not (min_x <= point[0] <= max_x and min_y <= point[1] <= max_y):
                    raise ValueError("Dimension chain point is outside layout bounds")
        return placed


__all__ = ["ChainLayout", "DimensionChain", "DimensionStyle", "LinearDim", "format_dimension_cm"]
