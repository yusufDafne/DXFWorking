"""`openings` modulunun cakisma ayak izi saglayicisi (DEV-019).

Uretilen tek sekil KAPI ACILIM SEKTORUDUR. Pencere ayak izi uretmez: pencere
duvar duzlemindedir ve plan duzleminde bir hacim isgal etmez. **Surme kapi da
sektor uretmez** (rev-13): kanat duvara paralel kayar, onunde bos alan
gerektirmez - tam da bu yuzden dar koridorlarda tercih edilir.

**Neden bu modul `walls`'u tuketiyor:** kapi acilim yayi HOST DUVARA
bagimlidir - mentese noktasi duvarin merkez cizgisi uzerinde, yonu duvarin
normalindedir. Bu zaten var olan ve endustri standardiyla uyumlu bir
bagimliliktir (IFC'de `IfcDoor` bir duvardaki `IfcOpeningElement`i doldurur).
Tersi gecerli DEGILDIR: `walls` kapiyi bilmez.

**Cizilen yay ile denetlenen alan AYNIDIR:** ikisi de
`openings.geometry.swing_geometry`den okur. rev-13'ten once aci hesabi burada
ve `walls.render` icinde AYRI AYRI yapiliyordu; bu, projenin en sinsi hata
sinifiydi (cizim ile denetimin sessizce ayrismasi).

Cokgen yaklasimi `collision.SECTOR_SEGMENTS` ile SABIT parca sayisindadir
(olcege bagli degildir) - deterministik uretim ilkesi geregi ayni context her
zaman ayni raporu vermelidir.
"""
from __future__ import annotations

from collision import TAG_DOOR_SWING, CollisionShape, sector_shape

from .geometry import swing_geometry
from .opening import TYPE_DOOR, VARIANT_SLIDING, Opening


def footprints(floor: dict, context: dict) -> list[CollisionShape]:
    doors = [o for o in floor.get("openings", []) if o.get("type") == TYPE_DOOR]
    if not doors:
        return []

    from walls import Wall, WallCatalog, gaps_for_wall

    catalog = WallCatalog()
    walls = [Wall.from_context(w, catalog) for w in floor.get("walls", [])]

    shapes: list[CollisionShape] = []
    for wall in walls:
        # Bosluk araligi CIZIMDEKI ile AYNI fonksiyondan alinir. rev-13'ten
        # once burada `position_from_start` acikligin BASLANGICI saniliyordu;
        # oysa o, acikligin MERKEZIDIR (bkz. schema ve `gaps_for_wall`). Sonuc:
        # denetlenen sektor cizilen yaydan yarim genislik (900'luk bir kapida
        # 450 mm) KAYIKTI. Cizim ile denetimin ayri ayri hesaplanmasi tam
        # olarak bu hatayi uretir; artik ikisi de tek kaynaktan okur.
        for g_start, g_end, data in gaps_for_wall(wall, doors):
            opening = Opening.from_context(data)
            if opening.variant == VARIANT_SLIDING:
                continue
            swing = swing_geometry(wall, opening, g_start, g_end)
            shapes.append(sector_shape(
                TAG_DOOR_SWING,
                opening.id,
                swing.hinge,
                swing.radius,
                swing.start_angle,
                swing.end_angle,
                label=f"{opening.variant} kapi acilimi",
            ))
    return shapes
