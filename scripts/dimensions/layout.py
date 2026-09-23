"""Zincir yerlesimi: sinir kontrolu (`ChainLayout`) ve kademelendirme
(`ChainStack`).

`ChainStack`, `DEV-017` Fikir 2'nin karsiligidir. rev-12'ye kadar `ChainLayout`
yalnizca "zincir sinirlarin icinde mi" diye bakiyordu; AYNI kenara birden fazla
zincir konuldugunda ikisi de ayni baseline'a oturup UST USTE biniyordu ve bunu
hicbir kontrol yakalamiyordu (tek tuketici aks modulu oldugu ve o da kenar
basina TEK zincir cizdigi icin sorun gorunmuyordu).
"""
from __future__ import annotations

from dataclasses import dataclass

from .chain import DimensionChain

# Iki baseline'in ayni sayilacagi mesafe.
BASELINE_TOLERANCE = 1.0


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
        ChainLayout.verify_no_overlap(placed)
        return placed

    @staticmethod
    def verify_no_overlap(chains) -> None:
        """Ayni yonde iki zincir AYNI baseline'a oturamaz.

        Ust uste binmis iki olcu zinciri sessizce okunamaz bir cizim uretir;
        bu yuzden hata firlatilir, uyarilmaz."""
        seen: dict[tuple[float, float], str] = {}
        for chain in chains:
            key = (chain.angle, round(chain.base_offset / BASELINE_TOLERANCE))
            if key in seen:
                raise ValueError(
                    f"Iki olcu zinciri ayni baseline'da: '{seen[key]}' ve "
                    f"'{chain.label or '?'}' (offset {chain.base_offset:.1f}, "
                    f"aci {chain.angle}). Kademelendirme icin ChainStack kullanin."
                )
            seen[key] = chain.label or "?"


@dataclass(frozen=True)
class ChainStack:
    """Bir kenardaki zincirleri deterministik olarak KADEMELENDIRIR.

    `origin` ilk zincirin baseline'i, `step` kademeler arasi mesafe,
    `direction` yapidan UZAKLASMA yonudur (guney/bati kenarinda -1).

    Zincirler verilme SIRASINA gore kademelenir: ilk zincir yapiya en yakin
    olandir. Mimari gelenek de budur - en ictekinde en ayrintili olcu (aciklik),
    disa dogru gidildikce daha kaba olcu (mahal, toplam) bulunur.
    """

    origin: float
    step: float
    direction: int = -1

    def offset_for(self, level: int) -> float:
        return self.origin + self.direction * self.step * level

    def place(self, chains: list[DimensionChain]) -> list[DimensionChain]:
        stacked = [chain.with_offset(self.offset_for(level))
                   for level, chain in enumerate(chains)]
        ChainLayout.verify_no_overlap(stacked)
        return stacked

    def extent(self, count: int) -> float:
        """`count` zincir yerlestirildiginde en distaki baseline."""
        return self.offset_for(max(0, count - 1))
