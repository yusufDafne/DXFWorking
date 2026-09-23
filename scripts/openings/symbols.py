"""Aciklik sembolleri: tek kanat, cift kanat, surme, katlanir ve pencere.

Her varyant `(msp, wall, g_start, g_end, data)` alan bir fonksiyondur;
`style.DefaultPlanOpeningStyle` bunlari veri odakli bir sozlukten secer -
varyant eklemek icin alt sinif GEREKMEZ (`WallCatalog` / `FurnitureCatalog`
ile ayni desen).
"""
from __future__ import annotations

from .geometry import side_sign, swing_geometry
from .opening import (
    VARIANT_DOUBLE,
    VARIANT_FOLDING,
    VARIANT_SINGLE,
    VARIANT_SLIDING,
)


def _add(point, vector):
    return (point[0] + vector[0], point[1] + vector[1])


def _scale(vector, factor):
    return (vector[0] * factor, vector[1] * factor)


def draw_jambs(msp, wall, g_start: float, g_end: float) -> None:
    """Aciklik kenarlarindaki (soye) dik cizgiler - her varyantta ayni."""
    for position in (g_start, g_end):
        msp.add_line(wall.rail_point("pos", position),
                     wall.rail_point("neg", position),
                     dxfattribs={"layer": wall.layer})


def _leaf_and_arc(msp, wall, g_start: float, g_end: float, data: dict,
                  layer: str) -> None:
    swing = swing_geometry(wall, data, g_start, g_end)
    msp.add_line(swing.hinge, swing.open_end, dxfattribs={"layer": layer})
    msp.add_arc(center=swing.hinge, radius=swing.radius,
                start_angle=swing.start_angle, end_angle=swing.end_angle,
                dxfattribs={"layer": layer})


def draw_single_door(msp, wall, g_start: float, g_end: float, data: dict) -> None:
    """Tek kanat: kanat cizgisi + 90 derecelik acilim yayi."""
    _leaf_and_arc(msp, wall, g_start, g_end, data, data.get("layer", "KAPI-PENCERE"))


def draw_double_door(msp, wall, g_start: float, g_end: float, data: dict) -> None:
    """Cift kanat: iki ucundan da acilan, YARIM genislikte iki kanat."""
    layer = data.get("layer", "KAPI-PENCERE")
    middle = (g_start + g_end) / 2.0
    left = dict(data, swing="left")
    right = dict(data, swing="right")
    _leaf_and_arc(msp, wall, g_start, middle, left, layer)
    _leaf_and_arc(msp, wall, middle, g_end, right, layer)


def draw_sliding_door(msp, wall, g_start: float, g_end: float, data: dict) -> None:
    """Surme kapi: acilim YAYI YOKTUR - kanat duvara paralel kayar.

    Bu, surme kapinin cakisma acisindan da farkli oldugu anlamina gelir:
    onunde bos alan gerektirmez (bkz. `collision.py`)."""
    layer = data.get("layer", "KAPI-PENCERE")
    sign = side_sign(data.get("host_side", "pos"))
    offset = _scale(wall.normal, sign * wall.thickness / 3.0)
    panel_start = _add(wall.centerline_point(g_start), offset)
    panel_end = _add(wall.centerline_point(g_end), offset)
    msp.add_line(panel_start, panel_end, dxfattribs={"layer": layer})
    # Kanadin kaydigi yonu gosteren kisa isaret
    tick = _scale(wall.normal, sign * wall.thickness / 6.0)
    msp.add_line(panel_end, _add(panel_end, tick), dxfattribs={"layer": layer})


def draw_folding_door(msp, wall, g_start: float, g_end: float, data: dict) -> None:
    """Katlanir kapi: iki esit kanat, akordeon gibi ortada kirilir."""
    layer = data.get("layer", "KAPI-PENCERE")
    sign = side_sign(data.get("host_side", "pos"))
    width = g_end - g_start
    half = width / 2.0
    hinge = wall.centerline_point(g_start)
    far = wall.centerline_point(g_end)
    # Kirilma noktasi: aciklik ortasindan duvara dik yarim genislik kadar
    fold = _add(wall.centerline_point(g_start + half),
                _scale(wall.normal, sign * half))
    msp.add_line(hinge, fold, dxfattribs={"layer": layer})
    msp.add_line(fold, far, dxfattribs={"layer": layer})


def draw_window(msp, wall, g_start: float, g_end: float, data: dict) -> None:
    """Pencere: duvar boyunca iki paralel cizgi (cam + dograma)."""
    layer = data.get("layer", "KAPI-PENCERE")
    offset = wall.thickness / 4.0
    start = wall.centerline_point(g_start)
    end = wall.centerline_point(g_end)
    for sign in (-1, 1):
        vector = _scale(wall.normal, sign * offset)
        msp.add_line(_add(start, vector), _add(end, vector),
                     dxfattribs={"layer": layer})


DOOR_SYMBOLS = {
    VARIANT_SINGLE: draw_single_door,
    VARIANT_DOUBLE: draw_double_door,
    VARIANT_SLIDING: draw_sliding_door,
    VARIANT_FOLDING: draw_folding_door,
}

# Varyant basina uretilen ACILIM YAYI sayisi. Bu, semantik golden kuralinin
# (`golden_report.rule_opening_symbols`) tek dogruluk kaynagidir: kural
# rev-12'ye kadar "her kapi = 1 ARC" varsayiyordu ve varyantlar eklenince
# kirilacakti. Cizicilerin bu tabloya uydugu `selftest.py` ile dogrulanir -
# yani tablo ile cizim sessizce ayrisamaz.
ARCS_PER_VARIANT = {
    VARIANT_SINGLE: 1,
    VARIANT_DOUBLE: 2,
    VARIANT_SLIDING: 0,   # kanat duvara paralel kayar, yay yoktur
    VARIANT_FOLDING: 0,   # akordeon kirilma, yay yoktur
}
