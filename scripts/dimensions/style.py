"""Olcu metni bicimi ve olcu stili.

**Metin HER ZAMAN tam sayi cm'dir** (bkz. kok CLAUDE.md "Olculendirme
birimi"): kaynak koordinat mm kalir, cm donusumu YALNIZCA gorunen metinde
yapilir. Bu, tasarim verisini degistirmeyen bir GOSTERIM kuralidir.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

# Aks olcu zinciri `AKS` katmanindadir (aks modulu sahiplenir); mahal/aciklik
# zincirleri ise projenin bildirdigi `OLCU` katmanina yazilir.
DIMENSION_LAYER = "OLCU"


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

    def on_layer(self, layer: str) -> "DimensionStyle":
        return replace(self, layer=layer)

    def scaled(self, factor: float) -> "DimensionStyle":
        """Ayni orana gore kuculmus/buyumus bir stil.

        Detay zincirlerinde (aciklik/mahal) metin, aks zincirinden kucuk
        olmalidir; aksi halde 20 cm'lik bir duvar kalinligi metni kendi olcu
        araligindan tasar."""
        return replace(
            self,
            text_height=self.text_height * factor,
            arrow_size=self.arrow_size * factor,
            extension=self.extension * factor,
            gap=self.gap * factor,
        )
