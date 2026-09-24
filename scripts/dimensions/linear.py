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
        # `add_linear_dim` bir `DimStyleOverride` SARMALAYICISI dondurur,
        # gercek DXF `Dimension` varligi DEGIL - o `.dimension` altindadir
        # (ezdxf API'si). `.dxf` yalnizca gercek varlikta vardir.
        override = msp.add_linear_dim(
            base=self.base,
            p1=self.p1,
            p2=self.p2,
            angle=self.angle,
            dimstyle="Standard",
            override=self.style.override(),
            text=format_dimension_cm(self.length),
            dxfattribs={"layer": self.style.layer},
        )
        override.render()
        dimension = override.dimension
        _fix_geometry_block_layer(msp.doc, dimension, self.style.layer)
        return dimension


def _fix_geometry_block_layer(doc, dimension, layer: str) -> None:
    """ezdxf 1.4.4 (`render/dim_base.py::BaseDimensionRenderer.add_line`)
    hesapladigi katman-birlesmis `attribs` sozlugunu KULLANMAZ - geometri
    BLOK'una orijinal (katmansiz) `dxfattribs`'i gecirir, bu yuzden olcu ve
    uzatma cizgileri DIMENSION'in kendi katmanindan BAGIMSIZ olarak hep "0"
    katmaninda cizilir (ok/metin bu hatadan MUAFTIR, onlarin kod yolu
    birlesmis sozlugu dogru kullanir - gozlemle dogrulandi). Bu, kullanicinin
    'aks çizgileri ölçüleri aks çizgileri ile aynı layerda olmalı' talebini
    (rev-18) karsilamak icin render SONRASI bir duzeltmedir; kutuphane
    kaynagi degistirilemez (proje disi dizin)."""
    block = doc.blocks.get(dimension.dxf.geometry)
    for entity in block:
        if entity.dxf.layer != "Defpoints":
            entity.dxf.layer = layer
