"""Kuzey oku modulu (DEV-025): kat paftalarina standart, degistirilebilir bir
kuzey yon sembolu cizer.

**Neden ayri bir modul (kullanici karari):** kullanici acikca "kuzey oku icin
standart bir tasarim belirle, daha sonra tasarim degisikligine gidildiginde
entegrasyon zor olmasin" istedi. `RailDrawingStandard` (bkz. scripts/walls/
standard.py) ile AYNI Protocol deseni burada da uygulanir: `NorthArrowStyle`
Protocol'u tek bir `draw(...)` sozlesmesi tanimlar, `DefaultNorthArrowStyle`
bugunku standart gorseldir (daire + ibre + 'K' etiketi). Yarin ofis farkli bir
sembol (orn. yildizli pusula) isterse, YENI bir `NorthArrowStyle` yazilir ve
`NorthArrow(style=...)` ile enjekte edilir - `NorthArrow.draw` cagri
sozlesmesi DEGISMEZ, cagiran taraf (generate_dxf.py) tek satir degisir.

Veri: `meta.north_angle` (derece, saat yonunde, +Y='yukari' referansindan
GERCEK KUZEY'e). Verilmezse ok HIC cizilmez - yon uydurulmaz (schema'da
opsiyonel).
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Protocol

from ezdxf.enums import TextEntityAlignment

try:
    from ..pafta import parse_scale_denominator, to_modelspace
except ImportError:  # dogrudan scripts/ uzerinden calistirildiginda
    from pafta import parse_scale_denominator, to_modelspace

NORTH_LABEL = "K"

# Kagit-uzerinde (PRINTED) mm sabitleri - pafta::to_modelspace ile projenin
# OLCEGINE gore turetilir (bkz. scripts/pafta/CLAUDE.md "parametrik
# olceklenebilirlik"). Tasarim verisi DEGILDIR.
PRINTED_RADIUS_MM = 6.0
PRINTED_LABEL_MM = 3.0


def rotate_point(center: tuple[float, float], distance: float, angle_deg: float) -> tuple[float, float]:
    """`center`den `distance` kadar, SAAT YONUNDE `angle_deg` acisiyla, 'yukari'
    (+Y) referansindan olculen bir nokta. angle=0 -> tam yukarida (cx,cy+d);
    angle=90 -> tam sagda (cx+d,cy). Elle dogrulanabilir: sin/cos'un standart
    (Y yukari, saat yonu tersi pozitif) matematiksel aciyla ORTUSMEDIGI icin
    (burada saat yonu pozitiftir - pusula/kerteriz konvansiyonu) isaretler
    normal trigonometriden FARKLIDIR, bu yuzden ayri bir yardimci fonksiyon
    olarak tutulur."""
    theta = math.radians(angle_deg)
    return (center[0] + distance * math.sin(theta), center[1] + distance * math.cos(theta))


class NorthArrowStyle(Protocol):
    def draw(self, msp, center: tuple[float, float], radius: float, angle_deg: float,
             layer: str, text_layer: str, text_height: float) -> None: ...


@dataclass(frozen=True)
class DefaultNorthArrowStyle:
    """Bugunku standart gorsel: daire + tek ucgen ibre (kuzeyi gosterir) +
    ibrenin ucunda 'K' etiketi. Kod-sahipli sabit oranlar (context.json'a
    SIZMAZ, bkz. kok CLAUDE.md 'DXF uretim disiplini')."""

    needle_base_ratio: float = 0.28   # ibre taban genisligi / radius
    label_gap_ratio: float = 0.45     # ibre ucundan etikete ek mesafe / radius

    def draw(self, msp, center, radius, angle_deg, layer, text_layer, text_height) -> None:
        msp.add_circle(center, radius, dxfattribs={"layer": layer})

        tip = rotate_point(center, radius, angle_deg)
        half_w = radius * self.needle_base_ratio
        b1 = rotate_point(center, half_w, angle_deg + 90.0)
        b2 = rotate_point(center, half_w, angle_deg - 90.0)
        needle = msp.add_lwpolyline([tip, b1, b2], dxfattribs={"layer": layer})
        needle.closed = True

        label_point = rotate_point(center, radius * (1.0 + self.label_gap_ratio), angle_deg)
        text = msp.add_text(NORTH_LABEL, dxfattribs={"layer": text_layer, "height": text_height})
        text.set_placement(label_point, align=TextEntityAlignment.MIDDLE_CENTER)


class NorthArrow:
    """Olcege gore turetilmis boyutlarla kuzey oku cizer. `style` enjekte
    edilebilir (bkz. modul docstring'i) - varsayilan `DefaultNorthArrowStyle`.

    Yerlesim (NEREYE cizilecegi) bu sinifin islevi DEGILDIR - o
    `generate_dxf.py`nin karari (pafta ic-cizgisinden itibaren birakilan
    padding icinde, aks baloncuklarindan uzak bir kose, bkz. modul
    CLAUDE.md 'Yerlesim')."""

    def __init__(self, scale: str, style: NorthArrowStyle | None = None,
                 layer: str = "CERCEVE", text_layer: str = "METIN"):
        scale_denominator = parse_scale_denominator(scale)
        self.style = style or DefaultNorthArrowStyle()
        self.layer = layer
        self.text_layer = text_layer
        self.radius = to_modelspace(PRINTED_RADIUS_MM, scale_denominator)
        self.label_height = to_modelspace(PRINTED_LABEL_MM, scale_denominator)

    def draw(self, msp, center: tuple[float, float], angle_deg: float) -> None:
        self.style.draw(msp, center, self.radius, angle_deg, self.layer,
                        self.text_layer, self.label_height)


# Bu modulun CONTEXT SOZLESMESI surumu (DEV-020). KOD surumu DEGILDIR.
# Bkz. scripts/version.py
CONTRACT_VERSION = "1.0"

__all__ = [
    "NORTH_LABEL",
    "PRINTED_RADIUS_MM",
    "PRINTED_LABEL_MM",
    "NorthArrow",
    "NorthArrowStyle",
    "DefaultNorthArrowStyle",
    "rotate_point",
]
