"""`furniture` modulunun cakisma ayak izi saglayicisi (DEV-019).

Tefrisin kapladigi alani KATALOG OLCUSU + YERLESIM ROTASYONU belirler; bu
ikisini bir arada bilen tek yer bu moduldur. Blok ekleme noktasi elemanin
SOL-ALT kosesidir ve donme o nokta etrafindadir - `rect_shape(..., anchor=
"corner")` bunu birebir tekrarlar, boylece ayak izi cizilen blokla ayni yerde
durur.

Bilinmeyen tip burada da uretimi DURDURUR (`FurnitureCatalog.get` KeyError
firlatir); denetimin sessizce atlamasi, cizimin patlamasindan daha kotudur.
"""
from __future__ import annotations

from collision import TAG_FURNITURE, CollisionShape, rect_shape

from .catalog import FurnitureCatalog
from .item import FurnitureItem


def footprints(floor: dict, context: dict) -> list[CollisionShape]:
    entries = floor.get("furniture", [])
    if not entries:
        return []
    catalog = FurnitureCatalog()
    shapes: list[CollisionShape] = []
    for data in entries:
        item = FurnitureItem.from_context(data)
        spec = catalog.get(item.type)
        shapes.append(rect_shape(
            TAG_FURNITURE,
            item.id,
            item.position,
            spec.width,
            spec.depth,
            item.rotation,
            label=spec.label,
            anchor="corner",
        ))
    return shapes
