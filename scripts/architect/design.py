"""Mimari asamasi (DEV-039): `study.py`nin zonlama PLANINDAN kapi karari
uretir - gercek geometriyi KENDISI cizmez, `openings/`in schema seklinde
bir SOZLUK dondurur (`templates::generate_circulation_core` ile AYNI
"hesaplar, cizmez" sinirinda).
"""
from __future__ import annotations

try:
    from .study import ZoningPlan
except ImportError:
    from study import ZoningPlan


def place_unit_entry_doors(
    zoning_plan: ZoningPlan, wall_id: str, *,
    door_width: float = 900.0, id_prefix: str = "",
) -> list[dict]:
    """Her zone'un GENISLIGININ ORTASINA merkezlenen tek bir kapi sozlugu
    uretir - zonlama planinin bildirdigi X araliklarindan TURETILIR,
    uydurulmaz. `zoning_plan.fits` False ise BOS liste doner (sigmayan bir
    plan icin kapi uretmek anlamsizdir)."""
    if not zoning_plan.fits:
        return []
    doors: list[dict] = []
    for zone in zoning_plan.zones:
        center = (zone.x0 + zone.x1) / 2.0
        doors.append({
            "id": f"{id_prefix}door_{zone.room_type}",
            "type": "door",
            "wall_id": wall_id,
            "position_from_start": center,
            "width": door_width,
            "layer": "KAPI-PENCERE",
        })
    return doors


__all__ = ["place_unit_entry_doors"]
