"""Cephe (elevation) modulu: seviye istifi, jenerik pencere/kapi yerlesimi ve
zemin-alti kesikli linetype (DEV-011).

Cepheler GERCEK PLAN GEOMETRISINDEN TURETILMEZ; kullanicinin acikca izin
verdigi sekilde (kok CLAUDE.md rev-2 notu) semantik/basit bir seviye istifi +
esit araliklarla yerlestirilmis jenerik pencere/kapi dikdortgenleridir.
"""
from __future__ import annotations

from dataclasses import dataclass

from ezdxf.enums import TextEntityAlignment

ELEVATION_LAYER = "DUVARLAR"
OPENING_LAYER = "KAPI-PENCERE"
DIM_LAYER = "OLCU"
LABEL_LAYER = "METIN"

# `axis` modulu de AYNI isim+desenle bir DASHED linetype yukler
# (`ensure_axis_layer`). Iki modul birbirini import ETMEZ (kok CLAUDE.md
# "modüller bağımsız çalışır"); her biri kendi guvenli/idempotent kaydini
# yapar - ikisi de doc.linetypes.add'i SADECE isim yoksa cagirir, bu yuzden
# hangisi once calisirsa o kazanir, ikincisi no-op'tur.
BELOW_GROUND_LINETYPE = "DASHED"

DEFAULT_ELEVATION_WINDOW_SIZE = (1200.0, 1400.0)
ELEVATION_DOOR_SIZE = (1800.0, 2100.0)
ELEVATION_LABEL_OFFSET = 300.0


def ensure_below_ground_linetype(doc) -> None:
    if BELOW_GROUND_LINETYPE not in doc.linetypes:
        doc.linetypes.add(
            BELOW_GROUND_LINETYPE,
            pattern=[750.0, 500.0, -250.0],
            description="Zemin alti / aks kesikli cizgi",
        )


@dataclass(frozen=True)
class Level:
    height: float
    label: str
    below_ground: bool = False
    window_count: int = 0
    window_size: tuple[float, float] = DEFAULT_ELEVATION_WINDOW_SIZE
    door: bool = False
    machine_room: bool = False

    @classmethod
    def from_context(cls, data: dict) -> "Level":
        return cls(
            height=float(data["height"]),
            label=data["label"],
            below_ground=bool(data.get("below_ground", False)),
            window_count=int(data.get("window_count", 0)),
            window_size=tuple(data.get("window_size", DEFAULT_ELEVATION_WINDOW_SIZE)),
            door=bool(data.get("door", False)),
            machine_room=bool(data.get("machine_room", False)),
        )


@dataclass(frozen=True)
class LevelStack:
    """Seviyelerin dusey istifi. Sira ONEMLIDIR: zemin-alti seviyeler
    listede ONCE (asagidan yukariya) gelmelidir - cursor buna gore birikir."""

    levels: list[Level]

    @classmethod
    def from_context(cls, elevation: dict) -> "LevelStack":
        return cls([Level.from_context(level) for level in elevation["levels"]])

    def extent(self) -> tuple[float, float]:
        """Pafta Y-araligi icin (machine_room protruzyonu DAHIL)."""
        total_below = sum(l.height for l in self.levels if l.below_ground)
        total_above = sum(l.height for l in self.levels if not l.below_ground)
        extra = 0.0
        for level in self.levels:
            if level.machine_room:
                extra = max(extra, level.height * 0.8)
        return -total_below, total_above + extra

    def placements(self) -> list[tuple[Level, float, float]]:
        """Her seviye icin (level, y0, y1). machine_room protruzyonunu
        DAHIL ETMEZ - o sadece `extent()`in pafta sizdirmazligi icin."""
        total_below = sum(l.height for l in self.levels if l.below_ground)
        cursor = -total_below
        result = []
        for level in self.levels:
            y0 = cursor
            y1 = cursor + level.height
            result.append((level, y0, y1))
            cursor = y1
        return result

    def stack_top(self) -> float:
        placements = self.placements()
        return placements[-1][2] if placements else 0.0


class FacadeOpeningPlacer:
    """Jenerik pencere/kapi dikdortgenlerini bir seviyeye esit araliklarla
    yerlestirir. Gercek plan acikliklarindan TURETILMEZ (bkz. modul
    CLAUDE.md "acik karar": bu opt-in ozellik henuz uygulanmadi)."""

    @staticmethod
    def windows(msp, level: Level, dx: float, width: float, y0: float,
                linetype: str | None = None) -> None:
        if level.window_count <= 0:
            return
        win_w, win_h = level.window_size
        sill = max(0.0, (level.height - win_h) / 2.0)
        gap = width / (level.window_count + 1)
        attribs = {"layer": OPENING_LAYER}
        if linetype:
            attribs["linetype"] = linetype
        for i in range(1, level.window_count + 1):
            cx = dx + gap * i
            x0w = cx - win_w / 2.0
            entity = msp.add_lwpolyline(
                [(x0w, y0 + sill), (x0w + win_w, y0 + sill),
                 (x0w + win_w, y0 + sill + win_h), (x0w, y0 + sill + win_h)],
                dxfattribs=dict(attribs),
            )
            entity.closed = True

    @staticmethod
    def door(msp, level: Level, dx: float, width: float, y0: float,
             linetype: str | None = None) -> None:
        if not level.door:
            return
        door_w, door_h = ELEVATION_DOOR_SIZE
        cx = dx + width / 2.0
        x0d = cx - door_w / 2.0
        attribs = {"layer": OPENING_LAYER}
        if linetype:
            attribs["linetype"] = linetype
        entity = msp.add_lwpolyline(
            [(x0d, y0), (x0d + door_w, y0), (x0d + door_w, y0 + door_h), (x0d, y0 + door_h)],
            dxfattribs=attribs,
        )
        entity.closed = True


class ElevationSheet:
    """Bir cephenin tam cizimi: aks izdusumu + seviye istifi + acikliklar +
    zemin cizgisi. `generate_dxf.py`nin eski (rev-13 ve oncesi) yerlesik
    `draw_elevation` fonksiyonuyla AYNI cagri sozlesmesini korur."""

    @staticmethod
    def draw(msp, elevation: dict, dx: float, text_height: float, axis_grid,
              label_text_height: float) -> None:
        ensure_below_ground_linetype(msp.doc)
        width = elevation["width"]
        stack = LevelStack.from_context(elevation)
        placements = stack.placements()
        y_bottom = stack.extent()[0]
        stack_top = stack.stack_top()

        # Aks izgarasi HER ZAMAN en once (en altta) cizilir.
        axis_grid.draw_on_elevation(msp, dx, elevation.get("axis_source"), y_bottom, stack_top)

        for level, y0, y1 in placements:
            linetype = BELOW_GROUND_LINETYPE if level.below_ground else None
            attribs = {"layer": ELEVATION_LAYER}
            if linetype:
                attribs["linetype"] = linetype
            outline = msp.add_lwpolyline(
                [(dx, y0), (dx + width, y0), (dx + width, y1), (dx, y1)],
                dxfattribs=attribs,
            )
            outline.closed = True

            FacadeOpeningPlacer.windows(msp, level, dx, width, y0, linetype)
            FacadeOpeningPlacer.door(msp, level, dx, width, y0, linetype)

            if level.machine_room:
                mr_w, mr_h = width * 0.25, level.height * 0.8
                cx = dx + width * 0.2
                mr = msp.add_lwpolyline(
                    [(cx, y1), (cx + mr_w, y1), (cx + mr_w, y1 + mr_h), (cx, y1 + mr_h)],
                    dxfattribs={"layer": ELEVATION_LAYER},
                )
                mr.closed = True

            label_entity = msp.add_text(level.label, dxfattribs={
                "layer": LABEL_LAYER, "height": label_text_height})
            label_entity.set_placement(
                (dx - ELEVATION_LABEL_OFFSET, (y0 + y1) / 2.0),
                align=TextEntityAlignment.MIDDLE_RIGHT)

        msp.add_line((dx - 1000, 0), (dx + width + 1000, 0), dxfattribs={"layer": DIM_LAYER})
        ground = msp.add_text("+-0.00 ZEMIN", dxfattribs={
            "layer": DIM_LAYER, "height": label_text_height})
        ground.set_placement((dx - ELEVATION_LABEL_OFFSET, 150.0),
                              align=TextEntityAlignment.MIDDLE_RIGHT)


def elevation_vertical_extent(elevation: dict) -> tuple[float, float]:
    """Pafta Y-araligi hesaplarken kullanilir (`generate_dxf.py::generate`,
    `Sheet.content_ranges`, `preview.py`)."""
    return LevelStack.from_context(elevation).extent()


# Bu modulun CONTEXT SOZLESMESI surumu (DEV-020). KOD surumu DEGILDIR.
# Bkz. scripts/version.py
CONTRACT_VERSION = "1.0"

__all__ = [
    "Level", "LevelStack", "FacadeOpeningPlacer", "ElevationSheet",
    "ensure_below_ground_linetype", "elevation_vertical_extent",
    "BELOW_GROUND_LINETYPE", "DEFAULT_ELEVATION_WINDOW_SIZE", "ELEVATION_DOOR_SIZE",
    "ELEVATION_LABEL_OFFSET", "ELEVATION_LAYER", "OPENING_LAYER", "DIM_LAYER", "LABEL_LAYER",
]
