"""Deterministic architectural axis-grid drawing primitives."""
from __future__ import annotations

from dataclasses import dataclass
import math

import ezdxf
from ezdxf.enums import TextEntityAlignment

AXIS_LAYER = "AKS"
AXIS_LINETYPE = "DASHED"
AXIS_RGB = (67, 77, 88)


@dataclass(frozen=True)
class AxisDrawingStandard:
    """Code-owned drawing constants; never loaded from project context."""

    extension: float = 1200.0
    bubble_radius: float = 450.0
    dimension_offset: float = 400.0
    dimension_text_height: float = 120.0
    dimension_extension: float = 150.0
    dimension_gap: float = 80.0
    dimension_arrow_size: float = 84.0
    linetype: str = AXIS_LINETYPE
    layer: str = AXIS_LAYER
    rgb: tuple[int, int, int] = AXIS_RGB


def _subtract(p1, p2):
    return (p1[0] - p2[0], p1[1] - p2[1])


def _length(vector) -> float:
    return math.hypot(vector[0], vector[1])


def _normalize(vector):
    length = _length(vector)
    if length == 0:
        return (0.0, 0.0)
    return (vector[0] / length, vector[1] / length)


def _add(point, vector):
    return (point[0] + vector[0], point[1] + vector[1])


def _scale(vector, factor):
    return (vector[0] * factor, vector[1] * factor)


def _add_text(msp, content: str, position, height: float, layer: str, align=TextEntityAlignment.LEFT):
    text = msp.add_text(content, dxfattribs={"layer": layer, "height": height})
    text.set_placement(position, align=align)
    return text


def ensure_dashed_linetype(doc, standard: AxisDrawingStandard | None = None) -> None:
    standard = standard or AxisDrawingStandard()
    if standard.linetype not in doc.linetypes:
        doc.linetypes.add(
            standard.linetype,
            pattern=[750.0, 500.0, -250.0],
            description="Aks kesikli cizgi",
        )


def ensure_axis_layer(doc, standard: AxisDrawingStandard | None = None) -> None:
    """Create or normalize the code-owned axis layer and linetype."""
    standard = standard or AxisDrawingStandard()
    ensure_dashed_linetype(doc, standard)
    if standard.layer in doc.layers:
        layer = doc.layers.get(standard.layer)
    else:
        layer = doc.layers.add(standard.layer)
    layer.dxf.linetype = standard.linetype
    layer.dxf.color = 8
    layer.dxf.true_color = ezdxf.colors.rgb2int(standard.rgb)


class AxisGrid:
    """Draw the shared floor/elevation axis grid and temporary dimensions."""

    def __init__(
        self,
        vertical_axes: list[dict],
        horizontal_axes: list[dict],
        text_height: float,
        standard: AxisDrawingStandard | None = None,
    ):
        self.vertical_axes = sorted(vertical_axes, key=lambda axis: axis["position"])
        self.horizontal_axes = sorted(horizontal_axes, key=lambda axis: axis["position"])
        self.text_height = text_height
        self.standard = standard or AxisDrawingStandard()

    def _bubble(self, msp, point, label: str) -> None:
        msp.add_circle(
            point,
            self.standard.bubble_radius,
            dxfattribs={"layer": self.standard.layer},
        )
        _add_text(
            msp,
            label,
            point,
            self.text_height,
            self.standard.layer,
            align=TextEntityAlignment.MIDDLE_CENTER,
        )

    def _line_with_bubbles(self, msp, p1, p2, label: str) -> None:
        total_len = _length(_subtract(p2, p1))
        if total_len > 2 * self.standard.bubble_radius:
            direction = _normalize(_subtract(p2, p1))
            line_p1 = _add(p1, _scale(direction, self.standard.bubble_radius))
            line_p2 = _add(p2, _scale(direction, -self.standard.bubble_radius))
        else:
            line_p1, line_p2 = p1, p2
        msp.add_line(
            line_p1,
            line_p2,
            dxfattribs={"layer": self.standard.layer, "linetype": self.standard.linetype},
        )
        self._bubble(msp, p1, label)
        self._bubble(msp, p2, label)

    def _dim_override(self) -> dict:
        return {
            "dimtxt": self.standard.dimension_text_height,
            "dimasz": self.standard.dimension_arrow_size,
            "dimexo": self.standard.dimension_extension,
            "dimexe": self.standard.dimension_extension,
            "dimgap": self.standard.dimension_gap,
        }

    def _dim_chain_x(self, msp, xs: list[float], edge_y: float, dim_y: float) -> None:
        for x1, x2 in zip(xs, xs[1:]):
            dist_cm = round(abs(x2 - x1) / 10.0)
            dimension = msp.add_linear_dim(
                base=(x1, dim_y),
                p1=(x1, edge_y),
                p2=(x2, edge_y),
                angle=0,
                dimstyle="Standard",
                override=self._dim_override(),
                text=str(int(dist_cm)),
                dxfattribs={"layer": self.standard.layer},
            )
            dimension.render()

    def _dim_chain_y(self, msp, ys: list[float], edge_x: float, dim_x: float) -> None:
        for y1, y2 in zip(ys, ys[1:]):
            dist_cm = round(abs(y2 - y1) / 10.0)
            dimension = msp.add_linear_dim(
                base=(dim_x, y1),
                p1=(edge_x, y1),
                p2=(edge_x, y2),
                angle=90,
                dimstyle="Standard",
                override=self._dim_override(),
                text=str(int(dist_cm)),
                dxfattribs={"layer": self.standard.layer},
            )
            dimension.render()

    def draw_on_floor(self, msp, dx: float, floor_width: float, floor_depth: float) -> None:
        y0, y1 = -self.standard.extension, floor_depth + self.standard.extension
        for axis in self.vertical_axes:
            x = dx + axis["position"]
            self._line_with_bubbles(msp, (x, y0), (x, y1), axis["label"])

        x0, x1 = dx - self.standard.extension, dx + floor_width + self.standard.extension
        for axis in self.horizontal_axes:
            y = axis["position"]
            self._line_with_bubbles(msp, (x0, y), (x1, y), axis["label"])

        self._dim_chain_x(
            msp,
            [dx + axis["position"] for axis in self.vertical_axes],
            edge_y=0.0,
            dim_y=-self.standard.dimension_offset,
        )
        self._dim_chain_y(
            msp,
            [axis["position"] for axis in self.horizontal_axes],
            edge_x=dx,
            dim_x=dx - self.standard.dimension_offset,
        )

    def draw_on_elevation(
        self,
        msp,
        dx: float,
        axis_source: str | None,
        y_bottom: float,
        y_top: float,
    ) -> None:
        if axis_source == "vertical":
            axes = self.vertical_axes
        elif axis_source == "horizontal":
            axes = self.horizontal_axes
        else:
            return

        y0, y1 = y_bottom - self.standard.extension, y_top + self.standard.extension
        for axis in axes:
            x = dx + axis["position"]
            self._line_with_bubbles(msp, (x, y0), (x, y1), axis["label"])

        self._dim_chain_x(
            msp,
            [dx + axis["position"] for axis in axes],
            edge_y=y_bottom,
            dim_y=y_bottom - self.standard.dimension_offset,
        )


__all__ = [
    "AXIS_LAYER",
    "AXIS_LINETYPE",
    "AXIS_RGB",
    "AxisDrawingStandard",
    "AxisGrid",
    "ensure_axis_layer",
]
