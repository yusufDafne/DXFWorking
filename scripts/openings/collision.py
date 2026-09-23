"""`openings` modulunun cakisma ayak izi saglayicisi (DEV-019).

Uretilen tek sekil KAPI ACILIM SEKTORUDUR. Pencere ayak izi uretmez: pencere
duvar duzlemindedir ve plan duzleminde bir hacim isgal etmez.

**Neden bu modul `walls`'u tuketiyor:** kapi acilim yayi HOST DUVARA
bagimlidir - mentese noktasi duvarin merkez cizgisi uzerindedir, yay yonu
duvarin normalidir. Bu zaten var olan ve endustri standardiyla uyumlu bir
bagimliliktir (IFC'de `IfcDoor` bir duvardaki `IfcOpeningElement`i doldurur).
Tersi gecerli DEGILDIR: `walls` kapiyi bilmez.

Yay, `walls.render.DefaultPlanOpeningStyle` ile AYNI aci hesabini kullanir;
boylece denetlenen alan cizilen yayin ta kendisidir. Cokgen yaklasimi
`collision.SECTOR_SEGMENTS` ile SABIT parca sayisindadir (olcege bagli
degildir) - deterministik uretim ilkesi geregi ayni context her zaman ayni
raporu vermelidir.
"""
from __future__ import annotations

import math

from collision import TAG_DOOR_SWING, CollisionShape, sector_shape


def footprints(floor: dict, context: dict) -> list[CollisionShape]:
    openings = [o for o in floor.get("openings", []) if o.get("type") == "door"]
    if not openings:
        return []

    from walls import Wall, WallCatalog  # host duvar bagimliligi (yukariya bkz.)

    catalog = WallCatalog()
    walls = {w["id"]: Wall.from_context(w, catalog) for w in floor.get("walls", [])}

    shapes: list[CollisionShape] = []
    for opening in openings:
        wall = walls.get(opening["wall_id"])
        if wall is None:
            # host duvar yoksa bu bir ACIKLIK hatasidir ve validate.py'nin
            # check_openings kontrolu zaten raporlar; burada sessiz gecilir.
            continue
        width = float(opening["width"])
        hinge = wall.centerline_point(float(opening["position_from_start"]))
        along = math.degrees(math.atan2(wall.direction[1], wall.direction[0]))
        perpendicular = math.degrees(math.atan2(wall.normal[1], wall.normal[0]))
        shapes.append(sector_shape(
            TAG_DOOR_SWING,
            opening["id"],
            hinge,
            width,
            min(along, perpendicular),
            max(along, perpendicular),
            label="kapi acilimi",
        ))
    return shapes
