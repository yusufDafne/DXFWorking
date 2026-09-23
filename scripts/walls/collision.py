"""`walls` modulunun cakisma ayak izi saglayicisi (DEV-019).

Ayak izi olarak MERKEZ CIZGI + KALINLIK dikdortgeni verilir, cizimdeki
gonyelenmis rail cokgeni degil. Gerekce:

- Gonye birlesim yalnizca duvar UCLARINI etkiler; bir tefrisin duvara girip
  girmedigi acisindan fark yaratmaz.
- `WallNetwork` kurmak bu saglayiciyi duvar cizim SIRASINA bagimli kilardi;
  cakisma denetimi ise DXF uretilmeden once, saf context uzerinde calisir.

Kalinlik `WallCatalog.resolve` ile cozulur - tasarim verisi (context'teki mm)
her zaman onceliklidir.
"""
from __future__ import annotations

from collision import TAG_WALL, CollisionShape, segment_shape

from .catalog import WallCatalog


def footprints(floor: dict, context: dict) -> list[CollisionShape]:
    catalog = WallCatalog()
    shapes: list[CollisionShape] = []
    for wall in floor.get("walls", []):
        thickness, _layer, kind = catalog.resolve(wall)
        if thickness <= 0:
            continue
        if wall["start"] == wall["end"]:
            continue
        shapes.append(segment_shape(
            TAG_WALL,
            wall["id"],
            wall["start"],
            wall["end"],
            thickness,
            label=str(kind or ""),
        ))
    return shapes
