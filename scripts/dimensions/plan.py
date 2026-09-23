"""Kat olcu zincirlerinin planlanmasi ve cizimi (DEV-017).

`FloorDimensionPlanner`, bir katin geometrisinden turetilen ordinatlari
(`derive.FloorOrdinates`) kademelendirilmis zincirlere (`layout.ChainStack`)
donusturur ve cizer. Aks olcu zinciri BU MODULE AIT DEGILDIR - onu `axis`
modulu kendi standardiyla cizer; buradaki zincirler `OLCU` katmanina yazilir.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .chain import DimensionChain
from .derive import AXIS_X, AXIS_Y, DEFAULT_LEVELS, FloorOrdinates
from .layout import ChainStack
from .style import DIMENSION_LAYER, DimensionStyle

# Yapi kenarindan ILK zincire ve kademeler arasina birakilan mesafe (mm,
# modelspace). Aks baloncuklarinin bu yiginin DISINDA kalmasi gerekir; bunu
# `required_axis_extension` bildirir ve `generate_dxf.py` aks standardini ona
# gore kurar (bkz. `scripts/axis/CLAUDE.md` capraz nokta notu).
DEFAULT_OFFSET = 700.0
DEFAULT_STEP = 550.0
# Detay zinciri metni aks zincirinden KUCUK olmalidir; 20 cm'lik bir duvar
# kalinligi metni aksi halde kendi olcu araligindan tasar.
DEFAULT_TEXT_SCALE = 0.7
# Baloncugun en distaki zincire degmemesi icin birakilan pay.
AXIS_CLEARANCE = 400.0


@dataclass(frozen=True)
class DimensionSettings:
    """`meta.dimensions` sunum ayari. VARSAYILAN KAPALIDIR.

    Olcu SAYISI geometriden turetilir (uydurulmaz), ama hangi kenarin hangi
    kademede olculenecegi bir sunum kararidir ve projeden gelir."""

    enabled: bool = False
    levels: tuple[str, ...] = DEFAULT_LEVELS
    offset: float = DEFAULT_OFFSET
    step: float = DEFAULT_STEP
    text_scale: float = DEFAULT_TEXT_SCALE
    layer: str = DIMENSION_LAYER

    @classmethod
    def from_context(cls, context: dict) -> "DimensionSettings":
        data = context.get("meta", {}).get("dimensions") or {}
        levels = tuple(data.get("levels", DEFAULT_LEVELS))
        if not levels:
            return cls(enabled=False)
        return cls(
            enabled=bool(data.get("enabled", False)),
            levels=levels,
            offset=float(data.get("offset", DEFAULT_OFFSET)),
            step=float(data.get("step", DEFAULT_STEP)),
            text_scale=float(data.get("text_scale", DEFAULT_TEXT_SCALE)),
            layer=str(data.get("layer", DIMENSION_LAYER)),
        )

    def stack_depth(self) -> float:
        """En distaki zincirin yapi kenarina uzakligi (kapali ise 0)."""
        if not self.enabled or not self.levels:
            return 0.0
        return self.offset + self.step * (len(self.levels) - 1)

    def axis_dimension_offset(self, minimum: float) -> float:
        """Aks olcu zincirinin yapi kenarina uzakligi.

        Mimari gelenek: en ictekinde EN AYRINTILI olcu (aciklik), disa dogru
        gidildikce kabalasir ve AKS zinciri EN DISTA durur. rev-13'ten once
        aks zinciri -400'de, yani en ictede duruyordu; detay zincirleri
        eklenince sira tersine donmus olurdu."""
        depth = self.stack_depth()
        if depth <= 0.0:
            return minimum
        return max(minimum, depth + self.step)

    def required_axis_extension(self, minimum: float,
                                bubble_radius: float = 0.0) -> float:
        """Aks baloncuklarinin olcu yiginini asmasi icin gereken uzama.

        Bu, `axis` ile `dimensions` arasindaki CAPRAZ NOKTADIR: iki modul
        birbirini BILMEZ ama ayni kenari paylasir. Yiginin derinligini
        yalnizca bu modul bilir, baloncugun yaricapini ise yalnizca `axis`
        bilir - bu yuzden yaricap PARAMETRE olarak verilir, import edilmez.

        Baloncugun YARICAPI hesaba katilmazsa daire, en distaki zincirin
        uzerine biner (rev-13'te once boyle oldu ve cizimde goruldu)."""
        depth = self.stack_depth()
        if depth <= 0.0:
            return minimum
        return max(minimum,
                   self.axis_dimension_offset(0.0) + bubble_radius + AXIS_CLEARANCE)


@dataclass
class FloorDimensionPlanner:
    """Bir katin olcu zincirlerini uretir. Context'i DEGISTIRMEZ."""

    floor: dict
    settings: DimensionSettings
    base_style: DimensionStyle = field(default_factory=DimensionStyle)

    def __post_init__(self) -> None:
        self.ordinates = FloorOrdinates(self.floor)

    @property
    def style(self) -> DimensionStyle:
        return (self.base_style
                .scaled(self.settings.text_scale)
                .on_layer(self.settings.layer))

    def chains(self, dx: float) -> list[DimensionChain]:
        """Yerlestirilmis (kademelendirilmis) zincirler.

        `dx` paftanin X ofsetidir; X ordinatlari ona tasinir, Y ordinatlari
        oldugu gibi kalir (kat paftalari yalnizca X'te kaydirilir)."""
        if not self.settings.enabled:
            return []

        south_edge = self._edge(AXIS_Y)
        west_edge = self._edge(AXIS_X)
        if south_edge is None or west_edge is None:
            return []

        style = self.style
        horizontal: list[DimensionChain] = []
        vertical: list[DimensionChain] = []
        for level in self.settings.levels:
            xs = self.ordinates.for_level(level, AXIS_X)
            if len(xs) >= 2:
                horizontal.append(DimensionChain.horizontal(
                    [x + dx for x in xs], south_edge, 0.0, style, label=f"x/{level}"))
            ys = self.ordinates.for_level(level, AXIS_Y)
            if len(ys) >= 2:
                vertical.append(DimensionChain.vertical(
                    ys, west_edge + dx, 0.0, style, label=f"y/{level}"))

        placed: list[DimensionChain] = []
        if horizontal:
            placed += ChainStack(south_edge - self.settings.offset,
                                 self.settings.step).place(horizontal)
        if vertical:
            placed += ChainStack(west_edge + dx - self.settings.offset,
                                 self.settings.step).place(vertical)
        return placed

    def _edge(self, axis: str) -> float | None:
        values = self.ordinates.total(axis)
        return values[0] if values else None

    def draw(self, msp, dx: float) -> int:
        chains = self.chains(dx)
        for chain in chains:
            chain.render(msp)
        return len(chains)
