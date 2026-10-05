"""Merkezi sirkulasyon cekirdegi + kat holu uretici (DEV-055).

`generate_circulation_core` (kose cekirdegi, DEV-037) AYNEN KALIR; bu dosya
buna EK olarak cekirdegi kat holu ile birlikte kat planinin merkezine (veya
merkezden kaymis) yerlestiren ikinci bir deterministik uretici sunar.

**Bagimlilik yonu (kullanici karari, 2026-10-05):** kisit/karar modulleri
(`architect`, `standards`) cizim modullerini bilmez; cizim (`templates`,
`openings`) bunlara bagimlidir. Bu yuzden hol olculerini `architect::
options_for_central_hall` HESAPLAR, bu dosya yalniz o sayilari rooms/walls/
openings'e CEVIRIR. Cikti context.json'a YAZILMAZ (kok `CLAUDE.md`).

Blok yerlesimi (kanonik: `orientation='x'`, `core_side='north'`):

    y1  +-----------+--------------------+
        | Asansor   | Merdiven           |   cekirdek satiri (core_depth)
    yc  +-----+-----+--------------------+   <- core_bottom (asansor + merdiven kapisi)
        |            Kat holu             |   dikdortgen, en-boy orani etut karari
    y0  +---------------------------------+

Daireler blogu cevreler: dondurulen `zone` bloktan kat sinirina kalan dort
payi ve hol cephesi duvarlarini (`hall_frontage`) bildirir; daire kapilarini
yerlestirmek etut biriminin isidir (bu fonksiyon daire kapisi UYDURMAZ).

Asansor kapisi `type='elevator_door'`dir: kuyu genisliginden iki kenardan
`ELEVATOR_DOOR_INSET_MM` (250mm) daraltilir, varsayilan varyant `sliding`
(`single` = kapi gibi acilan, `sliding_double` = ikili surme).
"""
from __future__ import annotations

try:
    from ..architect import CentralHallOption, options_for_central_hall
    from ..collision.geometry import shoelace_area
    from ..openings import ELEVATOR_DOOR_INSET_MM, elevator_door_width
except ImportError:
    from architect import CentralHallOption, options_for_central_hall
    from collision.geometry import shoelace_area
    from openings import ELEVATOR_DOOR_INSET_MM, elevator_door_width

from . import CirculationCoreTemplate, DEFAULT_TEMPLATE

# rev-25 (kullanici karari): merdivenin KISA kenari kat holune bakar; giris/cikis
# kisa kenardan, KAPISIZ duvar acikligiyla. Merdiven 3000 x 4000, asansor 2100 x
# 3000, aralarinda ve asansorun ustunde L-seklinde 1000 mm saft; cekirdek satiri 4000.
STAIR_SHORT_MM = 3000.0
STAIR_LONG_MM = 4000.0
SHAFT_WIDTH_MM = 1000.0
ELEVATOR_DEPTH_MM = 3000.0
PASSAGE_JAMB_MM = 300.0   # acikligin iki yaninda birakilan kati duvar payi


def generate_central_core(
    floor_width: float, floor_depth: float, option: CentralHallOption | None = None,
    template: CirculationCoreTemplate = DEFAULT_TEMPLATE, *, id_prefix: str = "",
    units: str = "mm", elevator_variant: str = "sliding",
    elevator_inset: float = ELEVATOR_DOOR_INSET_MM, n_units: int = 3,
    offset: tuple[float, float] = (0.0, 0.0), core_side: str = "north", orientation: str = "x",
    stair_entry: str = "short_edge",
) -> dict:
    """Merkezi cekirdek + kat holu parcasini (`rooms`/`walls`/`openings`/`zone`)
    uretir. `option` verilmezse `options_for_central_hall`in EN YUKSEK puanli
    UYGULANABILIR secenegi kullanilir; etut birimi baska bir secenegi kimligiyle
    secip buraya verebilir.

    `stair_entry='short_edge'` (varsayilan, rev-25): merdiven kisa kenariyla kat
    holune bakar, giris kapisiz duvar acikligi (`passage`); `'long_edge'` eski
    yerlesim (merdiven uzun kenari holde, kapi ile)."""
    if stair_entry not in ("short_edge", "long_edge"):
        raise ValueError(f"stair_entry 'short_edge' veya 'long_edge' olmali: '{stair_entry}'")
    short = stair_entry == "short_edge"
    if option is None:
        candidates = [o for o in options_for_central_hall(
            floor_width, floor_depth, n_units=n_units, door_width=template.door_width,
            wall_thickness=template.wall_thickness, elevator_width=template.elevator_width,
            stair_width=(SHAFT_WIDTH_MM + STAIR_SHORT_MM) if short else template.stair_width,
            core_depth=STAIR_LONG_MM if short else _core_depth(template), offset=offset,
            core_side=core_side, orientation=orientation) if o.feasible]
        if not candidates:
            raise ValueError("Merkezi cekirdek bloku kata SIGMIYOR (hicbir alternatif uygulanabilir degil).")
        option = candidates[0]
    orient, side = option.orientation, option.core_side

    # --- kanonik cerceve (x yonu, cekirdek kuzeyde) -------------------------
    bx0, by0, bx1, by1 = option.block
    if orient == "y":
        bx0, by0, bx1, by1 = by0, bx0, by1, bx1
    ew = template.elevator_width
    sw = (SHAFT_WIDTH_MM + STAIR_SHORT_MM) if short else template.stair_width
    yc = by0 + option.hall_depth

    def xf(point):
        x, y = point
        if side == "south":
            y = by0 + by1 - y
        return [float(y), float(x)] if orient == "y" else [float(x), float(y)]

    def poly(*pts):
        return [xf(p) for p in pts]

    def pid(name):
        return f"{id_prefix}{name}"

    divisor = 1_000_000.0 if units == "mm" else 1.0
    def area(polygon):
        return round(shoelace_area(polygon) / divisor, 2)

    hall = poly((bx0, by0), (bx1, by0), (bx1, yc), (bx0, yc))
    if short:
        sx = bx0 + ew + SHAFT_WIDTH_MM          # merdiven bati kenari
        ey = yc + ELEVATOR_DEPTH_MM
        elev = poly((bx0, yc), (bx0 + ew, yc), (bx0 + ew, ey), (bx0, ey))
        stair = poly((sx, yc), (bx1, yc), (bx1, by1), (sx, by1))
        shaft = poly((bx0, ey), (bx0 + ew, ey), (bx0 + ew, yc), (sx, yc), (sx, by1), (bx0, by1))
    else:
        elev = poly((bx0, yc), (bx0 + ew, yc), (bx0 + ew, by1), (bx0, by1))
        stair = poly((bx0 + ew, yc), (bx1, yc), (bx1, by1), (bx0 + ew, by1))
        shaft = None
    rooms = [
        {"id": pid("elevator"), "name": "Asansor", "room_type": "asansor", "polygon": elev, "area_m2": area(elev)},
        {"id": pid("stair"), "name": "Merdiven", "room_type": "merdiven", "polygon": stair, "area_m2": area(stair)},
        {"id": pid("hall"), "name": "Kat Holu", "room_type": "koridor", "polygon": hall, "area_m2": area(hall)},
    ]
    if shaft is not None:
        rooms.append({"id": pid("shaft"), "name": "Saft", "polygon": shaft, "area_m2": area(shaft)})
    t = template.wall_thickness

    def wall(name, a, b):
        return {"id": pid(name), "start": xf(a), "end": xf(b), "thickness": t, "layer": "DUVARLAR"}

    walls = [
        wall("hall_south", (bx0, by0), (bx1, by0)),
        wall("hall_west", (bx0, by0), (bx0, yc)),
        wall("hall_east", (bx1, by0), (bx1, yc)),
        wall("core_west", (bx0, yc), (bx0, by1)),
        wall("core_east", (bx1, yc), (bx1, by1)),
        wall("core_north", (bx0, by1), (bx1, by1)),
        wall("core_bottom", (bx0, yc), (bx1, yc)),
    ]
    if short:
        walls += [
            wall("core_div", (sx, yc), (sx, by1)),               # saft | merdiven
            wall("core_elev_side", (bx0 + ew, yc), (bx0 + ew, ey)),  # asansor | saft
            wall("core_elev_top", (bx0, ey), (bx0 + ew, ey)),        # asansor ustu | saft
        ]
    else:
        walls.append(wall("core_div", (bx0 + ew, yc), (bx0 + ew, by1)))
    # core_bottom xf ile y yonune cevrilirse baslangic/bitis yer degistirmez;
    # position_from_start duvarin KENDI start'indan olculur (bx0'dan).
    # Yansima (south) ve devrik (orientation 'y') duvar normalinin YONUNU
    # cevirir; ikisi birden cevirmez -> host_side XOR ile secilir.
    flip = (side == "south") != (orient == "y")
    if short:
        stair_opening = {"id": pid("passage_stair"), "type": "passage", "wall_id": pid("core_bottom"),
                         "position_from_start": ew + SHAFT_WIDTH_MM + STAIR_SHORT_MM / 2.0,
                         "width": STAIR_SHORT_MM - 2.0 * PASSAGE_JAMB_MM, "layer": "KAPI-PENCERE"}
    else:
        stair_opening = {"id": pid("door_stair"), "type": "door", "wall_id": pid("core_bottom"),
                         "position_from_start": ew + sw / 2.0, "width": template.door_width,
                         "layer": "KAPI-PENCERE", "host_side": "neg" if flip else "pos"}
    openings = [
        stair_opening,
        {"id": pid("door_elevator"), "type": "elevator_door", "wall_id": pid("core_bottom"),
         "position_from_start": ew / 2.0, "width": elevator_door_width(ew, elevator_inset),
         "layer": "KAPI-PENCERE", "variant": elevator_variant,
         "host_side": "pos" if flip else "neg"},
    ]
    bx_final = option.block
    zone = {
        "block": bx_final,
        "margins": dict(option.margins),
        "surrounds": option.surrounds,
        "hall_frontage": [pid("hall_south"), pid("hall_west"), pid("hall_east")],
        "option_id": option.id,
        "hall_aspect_ratio": option.aspect_ratio,
    }
    return {"rooms": rooms, "walls": walls, "openings": openings, "zone": zone}


def _core_depth(template: CirculationCoreTemplate) -> float:
    # corridor_leg_depth/band_depth farki gercek projedeki cekirdek derinligidir
    # (DEV-037: core_y0 = floor_depth - band_depth + corridor_leg_depth).
    return template.band_depth - template.corridor_leg_depth


__all__ = ["generate_central_core"]
