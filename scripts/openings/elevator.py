"""Asansor kapisi (DEV-055).

**Kullanici karari (2026-10-05):** kok `CLAUDE.md`deki eski "asansor kapi
sembolu cizilmez" kurali KALDIRILDI ("asansorlerin kapisi olur; genel bir
sablon cikarirken gereksiz token yemesin diye soylemistim"). Asansor kapisi
UC turdur: kapi gibi acilan (`single`), surme (`sliding`, **VARSAYILAN**) ve
buyuk kapilar icin ikili surme (`sliding_double`).

**Kuyu genisligi kadar OLMAZ:** kapi acikligi kuyunun iki kenarindan 200-300mm
(20-30cm) daraltilir - endustri standardi (kullanici). Varsayilan her kenardan
250mm (araligin ortasi): 2100mm kuyu -> 1600mm kapi.

Asansor kapisi `type='elevator_door'`dir; oda kapisi kurallari (asgari genislik,
odaya acilma, giris/WC nuanslari) ona UYGULANMAZ - kendi kurali burada.
Odalar duck-typed dict'tir (`rooms` modulu import edilmez).
"""
from __future__ import annotations

from .opening import TYPE_ELEVATOR_DOOR

ELEVATOR_DOOR_INSET_MM = 250.0        # her kenardan, varsayilan
ELEVATOR_INSET_MIN_MM = 200.0
ELEVATOR_INSET_MAX_MM = 300.0
_TOL = 1.0


def elevator_door_width(well_width_mm: float, inset_mm: float = ELEVATOR_DOOR_INSET_MM) -> float:
    """Kuyu genisliginden iki kenar payi dusulmus kapi genisligi (ELLE: 2100 -
    2*250 = 1600)."""
    width = well_width_mm - 2.0 * inset_mm
    if width <= 0:
        raise ValueError(f"Kuyu genisligi ({well_width_mm}) iki kenar payindan ({inset_mm}) kucuk.")
    return width


def check_elevator_door_insets(rooms: list[dict], walls: list[dict],
                               openings: list[dict]) -> list[str]:
    """UYARI: asansor kapisinin kuyu kenarlarina payi [200, 300]mm disindaysa
    (kuyu = kapinin bulundugu duvara oturan 'asansor' tipli oda kenari)."""
    warnings: list[str] = []
    walls_by_id = {w["id"]: w for w in walls}
    for op in openings:
        if op.get("type") != TYPE_ELEVATOR_DOOR:
            continue
        wall = walls_by_id.get(op["wall_id"])
        if wall is None:
            continue
        (sx, sy), (ex, ey) = wall["start"], wall["end"]
        length = ((ex - sx) ** 2 + (ey - sy) ** 2) ** 0.5
        if length == 0:
            continue
        ux, uy = (ex - sx) / length, (ey - sy) / length
        c0 = op["position_from_start"] - op["width"] / 2.0
        c1 = op["position_from_start"] + op["width"] / 2.0
        for room in rooms:
            if room.get("room_type") != "asansor":
                continue
            poly = room["polygon"]
            n = len(poly)
            for k in range(n):
                a, b = poly[k], poly[(k + 1) % n]
                d0 = abs(ux * (a[1] - sy) - uy * (a[0] - sx))
                d1 = abs(ux * (b[1] - sy) - uy * (b[0] - sx))
                if d0 > _TOL or d1 > _TOL:
                    continue  # kenar duvarla esdogrusal degil
                t0 = (a[0] - sx) * ux + (a[1] - sy) * uy
                t1 = (b[0] - sx) * ux + (b[1] - sy) * uy
                lo, hi = min(t0, t1), max(t0, t1)
                if not (lo - _TOL <= c0 and c1 <= hi + _TOL):
                    continue
                for side, inset in (("sol", c0 - lo), ("sag", hi - c1)):
                    if inset < ELEVATOR_INSET_MIN_MM - _TOL or inset > ELEVATOR_INSET_MAX_MM + _TOL:
                        warnings.append(
                            f"Asansor kapisi '{op['id']}' kuyu kenarindan ({side}) "
                            f"{inset:.0f}mm iceride; olmasi gereken "
                            f"{ELEVATOR_INSET_MIN_MM:.0f}-{ELEVATOR_INSET_MAX_MM:.0f}mm."
                        )
    return warnings
