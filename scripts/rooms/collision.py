"""`rooms` modulunun cakisma ayak izi saglayicisi (DEV-019).

Oda bir cizim elemani DEGIL, bir KAPSAYICIDIR (`container=True`): cift-cift
cakisma taramasina girmez, baska sekillerin ICINDE kalmasi beklenen hacimdir.
Iki odanin birbiriyle cakismasi ayri bir kontroldur ve `validate.py::check_rooms`
icinde kalir (arite-1'e yakin, modulun kendi verisinin tutarliligi).

Oda poligonu ICBUKEY olabilir (L seklindeki koridor); bu yuzden icerme testi
nokta-icinde-cokgen ile yapilir, kirpma ile degil (bkz. `collision/geometry.py`).
"""
from __future__ import annotations

from collision import TAG_ROOM, CollisionShape, polygon_shape


def footprints(floor: dict, context: dict) -> list[CollisionShape]:
    shapes: list[CollisionShape] = []
    for room in floor.get("rooms", []):
        polygon = room.get("polygon") or []
        if len(polygon) < 3:
            continue
        shapes.append(polygon_shape(
            TAG_ROOM,
            room["id"],
            polygon,
            label=str(room.get("name", "") or ""),
            container=True,
        ))
    return shapes
