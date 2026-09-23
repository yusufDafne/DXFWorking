"""Kapi acilim geometrisinin TEK SAHIBI.

**Neden ayri bir dosya:** Acilim yayini hem `symbols.py` (cizim) hem
`collision.py` (denetim) kullanir. Iki yerde ayri ayri hesaplansaydi
kacinilmaz olarak ayrisirdi ve cizilen yay ile denetlenen alan farkli olurdu -
projenin en sinsi hata sinifi tam olarak budur (bkz. "cizilen font <-> olculen
font" capraz noktasi). Ikisi de buradan okur.

**Duzeltilen gizli hata (rev-13):** Onceki surum yay acilarini
`min(along, perp)` .. `max(along, perp)` olarak veriyordu. Duvar -X yonunde
cizilmisse (`along = 180`, `perp = -90`) bu 270 DERECELIK bir yay uretirdi.
Mevcut projede her duvar +X/+Y yonunde ciziliydi, bu yuzden hata hic
gorunmedi; bir duvarin ucu ters verildigi anda ortaya cikacakti. Artik yon
CAPRAZ CARPIMLA belirlenir ve yay her zaman 90 derecedir.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from .opening import SIDE_POS, SWING_LEFT, Opening


@dataclass(frozen=True)
class SwingGeometry:
    """Bir kapi kanadinin acilim bilgisi (modelspace koordinatlarinda)."""

    hinge: tuple[float, float]
    radius: float
    # Kanadin KAPALI konumdaki ucu (duvar boyunca)
    leaf_end: tuple[float, float]
    # Kanadin ACIK konumdaki ucu (duvara dik)
    open_end: tuple[float, float]
    start_angle: float
    end_angle: float

    @property
    def sweep(self) -> float:
        span = (self.end_angle - self.start_angle) % 360.0
        return span if span else 360.0


def _add(point, vector):
    return (point[0] + vector[0], point[1] + vector[1])


def _scale(vector, factor):
    return (vector[0] * factor, vector[1] * factor)


def side_sign(host_side: str) -> float:
    return 1.0 if host_side == SIDE_POS else -1.0


def swing_geometry(wall, opening: Opening | dict, g_start: float,
                   g_end: float) -> SwingGeometry:
    """Kapinin mentese noktasi, kanat yonu ve 90 derecelik acilim yayi.

    `g_start`/`g_end` acikligin duvar boyunca baslangic/bitis mesafesidir
    (`WallNetwork.gaps_for_wall` ile ayni sozlesme).
    """
    data = opening.as_dict() if isinstance(opening, Opening) else opening
    swing = data.get("swing", SWING_LEFT)
    sign = side_sign(data.get("host_side", SIDE_POS))

    width = g_end - g_start
    if swing == SWING_LEFT:
        hinge = wall.centerline_point(g_start)
        along = wall.direction
    else:
        hinge = wall.centerline_point(g_end)
        along = (-wall.direction[0], -wall.direction[1])
    perpendicular = _scale(wall.normal, sign)

    along_angle = math.degrees(math.atan2(along[1], along[0]))
    perp_angle = math.degrees(math.atan2(perpendicular[1], perpendicular[0]))

    # ezdxf yayi start_angle'dan end_angle'a SAAT YONUNUN TERSINE cizer.
    # Capraz carpim pozitifse `perpendicular`, `along`in CCW tarafindadir.
    cross = along[0] * perpendicular[1] - along[1] * perpendicular[0]
    if cross >= 0:
        start_angle, end_angle = along_angle, perp_angle
    else:
        start_angle, end_angle = perp_angle, along_angle

    return SwingGeometry(
        hinge=hinge,
        radius=width,
        leaf_end=_add(hinge, _scale(along, width)),
        open_end=_add(hinge, _scale(perpendicular, width)),
        start_angle=start_angle,
        end_angle=end_angle,
    )
