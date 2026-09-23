"""`columns` modulunun cakisma ayak izi saglayicisi (DEV-019).

Kolonun gercek ayak izini kesit ve rotasyondan TUREYEN bu modul bilir;
`Column.corners()` zaten cizimde kullanilan donmus kose noktalarini verir, bu
yuzden ayak izi ile cizilen kontur BIREBIR aynidir. Ikinci bir kopya
tutulmaz - cizim ile denetimin ayrismasi bu modulde en kolay kacirilacak
hata olurdu.
"""
from __future__ import annotations

from collision import TAG_COLUMN, CollisionShape, circle_shape, polygon_shape

from .column import Column
from .section import ColumnSectionCatalog


def footprints(floor: dict, context: dict) -> list[CollisionShape]:
    catalog = ColumnSectionCatalog()
    shapes: list[CollisionShape] = []
    for data in floor.get("columns", []):
        column = Column.from_context(data, catalog)
        label = column.name or column.section.key
        if column.section.shape == "circle":
            shapes.append(circle_shape(TAG_COLUMN, column.id, column.position,
                                       column.section.radius, label=label))
        else:
            shapes.append(polygon_shape(TAG_COLUMN, column.id,
                                        column.corners(), label=label))
    return shapes
