"""Aks izgarasinin cizimi: kesikli cizgi, tegetli baloncuk ve olcu zinciri."""
from __future__ import annotations

from ezdxf.enums import TextEntityAlignment

try:
    from ..dimensions import ChainLayout, DimensionChain, DimensionStyle
except ImportError:
    from dimensions import ChainLayout, DimensionChain, DimensionStyle

from .axis import Axis, axes_from_context
from .standard import (
    AxisDrawingStandard,
    add,
    add_text,
    length,
    normalize,
    scale,
    subtract,
)


class AxisGrid:
    """Draw the shared floor/elevation axis grid and its dimension chain."""

    def __init__(
        self,
        vertical_axes: list[dict],
        horizontal_axes: list[dict],
        text_height: float,
        standard: AxisDrawingStandard | None = None,
    ):
        self.vertical = axes_from_context(vertical_axes)
        self.horizontal = axes_from_context(horizontal_axes)
        self.text_height = text_height
        self.standard = standard or AxisDrawingStandard()

    # Eski sozlesme: `dict` listesi bekleyen cagri yerleri icin korunur.
    @property
    def vertical_axes(self) -> list[dict]:
        return [{"label": a.label, "position": a.position} for a in self.vertical]

    @property
    def horizontal_axes(self) -> list[dict]:
        return [{"label": a.label, "position": a.position} for a in self.horizontal]

    # ------------------------------------------------------------- cizim
    def _bubble(self, msp, point, label: str) -> None:
        msp.add_circle(point, self.standard.bubble_radius,
                       dxfattribs={"layer": self.standard.layer})
        add_text(msp, label, point, self.text_height, self.standard.layer,
                 align=TextEntityAlignment.MIDDLE_CENTER)

    def _line_with_bubbles(self, msp, p1, p2, label: str) -> None:
        total_len = length(subtract(p2, p1))
        if total_len > 2 * self.standard.bubble_radius:
            direction = normalize(subtract(p2, p1))
            line_p1 = add(p1, scale(direction, self.standard.bubble_radius))
            line_p2 = add(p2, scale(direction, -self.standard.bubble_radius))
        else:
            line_p1, line_p2 = p1, p2
        msp.add_line(line_p1, line_p2,
                     dxfattribs={"layer": self.standard.layer,
                                 "linetype": self.standard.linetype})
        self._bubble(msp, p1, label)
        self._bubble(msp, p2, label)

    def _dimension_style(self) -> DimensionStyle:
        return DimensionStyle(
            layer=self.standard.layer,
            text_height=self.standard.dimension_text_height,
            arrow_size=self.standard.dimension_arrow_size,
            extension=self.standard.dimension_extension,
            gap=self.standard.dimension_gap,
        )

    def _dim_chain_x(self, msp, xs: list[float], edge_y: float, dim_y: float) -> None:
        if len(xs) < 2:
            return
        chain = DimensionChain.horizontal(xs, edge_y, dim_y, self._dimension_style(),
                                          label="aks/x")
        ChainLayout.place(
            [chain],
            (min(xs) - self.standard.dimension_extension,
             min(dim_y, edge_y) - self.standard.dimension_extension,
             max(xs) + self.standard.dimension_extension,
             max(dim_y, edge_y) + self.standard.dimension_extension),
        )[0].render(msp, edge_y)

    def _dim_chain_y(self, msp, ys: list[float], edge_x: float, dim_x: float) -> None:
        if len(ys) < 2:
            return
        chain = DimensionChain.vertical(ys, edge_x, dim_x, self._dimension_style(),
                                        label="aks/y")
        ChainLayout.place(
            [chain],
            (min(dim_x, edge_x) - self.standard.dimension_extension,
             min(ys) - self.standard.dimension_extension,
             max(dim_x, edge_x) + self.standard.dimension_extension,
             max(ys) + self.standard.dimension_extension),
        )[0].render(msp, edge_x)

    def _draw_family(self, msp, axes: list[Axis], full_low: float, full_high: float,
                     to_point) -> None:
        for axis in axes:
            low, high = axis.span(full_low, full_high, self.standard.extension,
                                  self.standard.partial_extension)
            p1, p2 = to_point(axis.position, low), to_point(axis.position, high)
            self._line_with_bubbles(msp, p1, p2, axis.label)

    def draw_on_floor(self, msp, dx: float, floor_width: float, floor_depth: float) -> None:
        self._draw_family(msp, self.vertical, 0.0, floor_depth,
                          lambda position, along: (dx + position, along))
        self._draw_family(msp, self.horizontal, dx, dx + floor_width,
                          lambda position, along: (along, position))

        # Olcu zincirine YALNIZCA o kenara ulasan akslar girer; kismi bir aks
        # kenara varmiyorsa zincirde yeri yoktur (aksi halde zincir orada
        # olmayan bir aksi olculuyormus gibi gorunur).
        self._dim_chain_x(
            msp,
            [dx + axis.position for axis in self.vertical if axis.covers(0.0)],
            edge_y=0.0,
            dim_y=-self.standard.dimension_offset,
        )
        self._dim_chain_y(
            msp,
            [axis.position for axis in self.horizontal if axis.covers(dx)],
            edge_x=dx,
            dim_x=dx - self.standard.dimension_offset,
        )

    def draw_on_elevation(self, msp, dx: float, axis_source: str | None,
                          y_bottom: float, y_top: float) -> None:
        if axis_source == "vertical":
            axes = self.vertical
        elif axis_source == "horizontal":
            axes = self.horizontal
        else:
            return

        # Cephede aks bir IZDUSUMDUR: plandaki kismi uzanim cephede anlamsizdir
        # (cephe o aksi yine de gorur), bu yuzden `extent` UYGULANMAZ ve tum
        # akslar cephe yuksekligi boyunca cizilir.
        y0 = y_bottom - self.standard.extension
        y1 = y_top + self.standard.extension
        for axis in axes:
            x = dx + axis.position
            self._line_with_bubbles(msp, (x, y0), (x, y1), axis.label)

        self._dim_chain_x(
            msp,
            [dx + axis.position for axis in axes],
            edge_y=y_bottom,
            dim_y=y_bottom - self.standard.dimension_offset,
        )
