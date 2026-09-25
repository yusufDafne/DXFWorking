"""Aks cizim standardi: layer, linetype, sabit RGB ve olcu sabitleri.

Bu degerler KOD SAHIPLIDIR ve context.json'dan ALINMAZ (bkz. kok CLAUDE.md
"Aks (grid) sistemi"). Tek istisna, `generate_dxf.py`nin olcu yiginina gore
hesaplayip verdigi `extension` / `dimension_offset` degerleridir - onlar da
projeden degil, `dimensions` modulunden gelir.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import ezdxf
from ezdxf.enums import TextEntityAlignment

try:
    from ..palette import color_for
except ImportError:  # dogrudan scripts/ uzerinden calistirildiginda
    from palette import color_for

AXIS_LAYER = "AKS"
AXIS_LINETYPE = "DASHED"
# Renk artik scripts/palette::PALETTE'in TEK kaynagindan gelir (DEV-030);
# DEGER AYNI (67,77,88) kalir - bu sabit kok CLAUDE.md tarafindan mandate
# edilir, palette de bunu DEGISTIRMEZ, sadece merkezi kayda alir.
AXIS_RGB = color_for("AKS")


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
    # KISMI aks (rev-13, DEV-015): yapinin tamamini kat etmeyen bir aks, kendi
    # `extent` araliginin disina TAM uzama kadar tasmaz - tasarsa yapi disinda
    # bir yere isaret ediyormus gibi okunur. Yalnizca baloncugun geometrinin
    # uzerine binmemesi kadar bir pay birakilir.
    partial_extension: float = 600.0
    # En uctaki aksların arasindaki TOPLAM mesafe (rev-18, kullanici karari:
    # "akslar arası mesafeler ve ikinci olarak en uçtaki aksların arasındaki
    # mesafeyi vermeli"). Bu ikinci zincir, aksin KENDI baloncugunu/uzamasini
    # (extension + bubble_radius) asip bu kadar OTESINDE durur - aksi halde
    # bir kenarda uc aks varsa toplam zincirin uc ciziklerinin bubble'a
    # girmesi riski olurdu (elle dogrulandi: extension+bubble_radius=1650,
    # varsayilan dimension_offset*2=800 bunun ICINDE kalirdi).
    total_dimension_clearance: float = 300.0
    linetype: str = AXIS_LINETYPE
    layer: str = AXIS_LAYER
    rgb: tuple[int, int, int] = AXIS_RGB


def subtract(p1, p2):
    return (p1[0] - p2[0], p1[1] - p2[1])


def length(vector) -> float:
    return math.hypot(vector[0], vector[1])


def normalize(vector):
    magnitude = length(vector)
    if magnitude == 0:
        return (0.0, 0.0)
    return (vector[0] / magnitude, vector[1] / magnitude)


def add(point, vector):
    return (point[0] + vector[0], point[1] + vector[1])


def scale(vector, factor):
    return (vector[0] * factor, vector[1] * factor)


def add_text(msp, content: str, position, height: float, layer: str,
             align=TextEntityAlignment.LEFT):
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
