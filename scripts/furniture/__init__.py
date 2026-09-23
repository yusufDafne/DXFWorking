"""Tefris (furniture) modulu: konut tefris katalogu, blok tanimlari ve cizim.

Tasarim kararlari (kullanici talebi, DEV-009):

- **Tefris HER ZAMAN DXF `BLOCK` olarak cizilir.** Her tefris tipi bir blok
  TANIMIDIR, her yerlesim bir `INSERT`'tir. Boylece AutoCAD'de tek nesne olur,
  bicimi tek tanimdan degisir ve dosya sismez.
- **Kendi layer'lari ve renkleri vardir.** Tefris, mimari cizimin "okunmasi
  gereken" katmani degildir; bu yuzden duvar/aks gibi ogelerle yarismaz.
  Renkler KAHVERENGI ailesinde secilmistir ve birbirine yakin tonlardir -
  gruplar ayirt edilebilir ama cizimde zit/dikkat cekici lekeler olusmaz.
- **Gruplar** islevseldir (oturma / yemek / yatak / mutfak / islak hacim) ve
  her grubun kendi layer'i + kendi tonu vardir.

**Kapilar bu modulde DEGILDIR** - bkz. `scripts/furniture/CLAUDE.md`
"Kapi kimin?" bolumu. Kapi/pencere bir duvar acikligidir (`openings/` +
`walls/`), tefris degildir; bu endustri standardidir (IFC'de `IfcDoor` bir
`IfcBuildingElement`tir, `IfcFurnishingElement` degil; AIA/NCS layer
standardinda kapi `A-DOOR`, tefris `A-FURN`).

Olculer ofis/katalog standardidir (tasarim verisi degil), `WallCatalog`
mantigiyla sozlukten gelir ve degistirilebilir. Yerlesim (konum/rotasyon)
ise PROJE VERISIDIR ve context.json'dan gelir - uydurulmaz.
"""

from __future__ import annotations

from .catalog import (
    BLOCK_PREFIX,
    DEFAULT_FURNITURE_CATALOG,
    FurnitureCatalog,
    FurnitureSpec,
)
from .groups import FURNITURE_GROUPS, FurnitureGroup, ensure_furniture_layers
from .item import FurnitureItem
from .render import FurnitureBlocks, FurnitureRenderer, FurnitureSchedule

__all__ = [
    "BLOCK_PREFIX",
    "DEFAULT_FURNITURE_CATALOG",
    "FURNITURE_GROUPS",
    "FurnitureBlocks",
    "FurnitureCatalog",
    "FurnitureGroup",
    "FurnitureItem",
    "FurnitureRenderer",
    "FurnitureSchedule",
    "FurnitureSpec",
    "ensure_furniture_layers",
]
