"""Tefris blok tanimlari, `INSERT` cizimi ve salt-okunur tefris listesi.

Tefris HER ZAMAN DXF `BLOCK` olarak cizilir: tip basina bir tanim, yerlesim
basina bir `INSERT`.
"""
from __future__ import annotations

from .catalog import FurnitureCatalog
from .groups import ensure_furniture_layers
from .item import FurnitureItem

class FurnitureBlocks:
    """Tefris blok TANIMLARINI belgeye kaydeder. Ayni tip ikinci kez
    istendiginde yeniden tanimlanmaz."""

    @staticmethod
    def ensure(doc, catalog: FurnitureCatalog, keys) -> dict[str, str]:
        ensure_furniture_layers(doc, catalog.groups)
        names: dict[str, str] = {}
        for key in sorted(set(keys)):
            spec = catalog.get(key)
            names[key] = spec.block_name
            if spec.block_name in doc.blocks:
                continue
            block = doc.blocks.new(name=spec.block_name)
            spec.draw(block, spec)
            # Blok icindeki geometri BYLAYER kalir; INSERT'in layer'i rengi
            # belirler, boylece ayni tanim farkli grupta kullanilabilir.
            for entity in block:
                entity.dxf.layer = "0"
        return names


class FurnitureRenderer:
    """Yerlesimleri `INSERT` olarak cizer."""

    @staticmethod
    def draw(msp, items: list[FurnitureItem], catalog: FurnitureCatalog) -> list:
        inserts = []
        for item in items:
            spec = catalog.get(item.type)
            inserts.append(msp.add_blockref(
                spec.block_name, item.position,
                dxfattribs={"layer": catalog.layer_of(spec),
                            "rotation": item.rotation},
            ))
        return inserts


class FurnitureSchedule:
    """Deterministik, salt-okunur tefris listesi (`OpeningSchedule` deseni)."""

    @staticmethod
    def from_items(items: list[FurnitureItem], catalog: FurnitureCatalog) -> list[dict]:
        rows = []
        for item in items:
            spec = catalog.get(item.type)
            rows.append({
                "id": item.id,
                "type": item.type,
                "label": spec.label,
                "group": spec.group,
                "width": spec.width,
                "depth": spec.depth,
            })
        return sorted(rows, key=lambda row: (row["group"], row["type"], row["id"]))
