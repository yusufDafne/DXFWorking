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

from dataclasses import dataclass, field
from typing import Callable

import ezdxf

BLOCK_PREFIX = "TEFRIS_"


@dataclass(frozen=True)
class FurnitureGroup:
    """Islevsel tefris grubu: kendi layer'i ve kahverengi ailesinden tonu."""

    key: str
    layer: str
    rgb: tuple[int, int, int]
    label: str


# Kahverengi ailesi - bilerek DUSUK kontrastli tonlar (kullanici talebi).
FURNITURE_GROUPS: dict[str, FurnitureGroup] = {
    "OTURMA": FurnitureGroup("OTURMA", "TEFRIS-OTURMA", (139, 94, 60), "Oturma grubu"),
    "YEMEK": FurnitureGroup("YEMEK", "TEFRIS-YEMEK", (161, 120, 79), "Yemek grubu"),
    "YATAK": FurnitureGroup("YATAK", "TEFRIS-YATAK", (120, 86, 66), "Yatak odasi"),
    "MUTFAK": FurnitureGroup("MUTFAK", "TEFRIS-MUTFAK", (150, 111, 94), "Mutfak"),
    "ISLAK": FurnitureGroup("ISLAK", "TEFRIS-ISLAK", (131, 120, 106), "Islak hacim"),
}


def ensure_furniture_layers(doc, groups: dict[str, FurnitureGroup] | None = None) -> None:
    """Tefris layer'larini sabit RGB tonlariyla hazirlar (`ensure_axis_layer`
    deseni). Renk context'ten alinmaz; kod sahibidir."""
    for group in (groups or FURNITURE_GROUPS).values():
        if group.layer in doc.layers:
            layer = doc.layers.get(group.layer)
        else:
            layer = doc.layers.add(name=group.layer)
        layer.rgb = group.rgb


# --------------------------------------------------------------------------
# Cizim yardimcilari - hepsi blok TANIMI icine, yerel koordinatta cizer.
# Yerel orijin (0,0) = elemanin SOL-ALT kosesi.
# --------------------------------------------------------------------------

def _rect(block, x0: float, y0: float, x1: float, y1: float) -> None:
    polyline = block.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
    polyline.closed = True


def _line(block, p1, p2) -> None:
    block.add_line(p1, p2)


def _draw_sofa(block, spec: "FurnitureSpec") -> None:
    width, depth = spec.width, spec.depth
    arm, back = 150.0, 180.0
    _rect(block, 0, 0, width, depth)
    _line(block, (arm, 0), (arm, depth))
    _line(block, (width - arm, 0), (width - arm, depth))
    _line(block, (arm, depth - back), (width - arm, depth - back))
    seats = max(1, spec.options.get("seats", 1))
    seat_width = (width - 2 * arm) / seats
    for index in range(1, seats):
        x = arm + index * seat_width
        _line(block, (x, 0), (x, depth - back))


def _draw_chair(block, spec: "FurnitureSpec") -> None:
    width, depth = spec.width, spec.depth
    _rect(block, 0, 0, width, depth)
    _line(block, (0, depth - 70), (width, depth - 70))


def _draw_table(block, spec: "FurnitureSpec") -> None:
    _rect(block, 0, 0, spec.width, spec.depth)
    inset = 60.0
    if spec.width > 2 * inset and spec.depth > 2 * inset:
        _rect(block, inset, inset, spec.width - inset, spec.depth - inset)


def _draw_bed(block, spec: "FurnitureSpec") -> None:
    width, depth = spec.width, spec.depth
    _rect(block, 0, 0, width, depth)
    pillows = max(1, spec.options.get("pillows", 1))
    margin = 90.0
    pillow_width = (width - margin * (pillows + 1)) / pillows
    for index in range(pillows):
        x0 = margin + index * (pillow_width + margin)
        _rect(block, x0, depth - 520, x0 + pillow_width, depth - 160)
    _line(block, (0, depth - 700), (width, depth - 700))


def _draw_cabinet(block, spec: "FurnitureSpec") -> None:
    """Gardirop / tezgah / dolap: govde + on hat + kapak bolumleri."""
    width, depth = spec.width, spec.depth
    _rect(block, 0, 0, width, depth)
    _line(block, (0, depth * 0.22), (width, depth * 0.22))
    doors = max(1, int(round(width / spec.options.get("door_width", 600.0))))
    for index in range(1, doors):
        x = width * index / doors
        _line(block, (x, depth * 0.22), (x, depth))


def _draw_cooker(block, spec: "FurnitureSpec") -> None:
    width, depth = spec.width, spec.depth
    _rect(block, 0, 0, width, depth)
    radius = min(width, depth) * 0.16
    for fx in (0.28, 0.72):
        for fy in (0.28, 0.72):
            block.add_circle((width * fx, depth * fy), radius)


def _draw_sink(block, spec: "FurnitureSpec") -> None:
    width, depth = spec.width, spec.depth
    _rect(block, 0, 0, width, depth)
    _rect(block, width * 0.08, depth * 0.15, width * 0.62, depth * 0.85)
    block.add_circle((width * 0.35, depth * 0.5), min(width, depth) * 0.06)


def _draw_fridge(block, spec: "FurnitureSpec") -> None:
    width, depth = spec.width, spec.depth
    _rect(block, 0, 0, width, depth)
    _line(block, (0, depth * 0.62), (width, depth * 0.62))
    _line(block, (width * 0.5, 0), (width * 0.5, depth * 0.62))


def _draw_washbasin(block, spec: "FurnitureSpec") -> None:
    width, depth = spec.width, spec.depth
    _rect(block, 0, 0, width, depth)
    block.add_ellipse((width * 0.5, depth * 0.52),
                      major_axis=(width * 0.36, 0), ratio=0.72)
    block.add_circle((width * 0.5, depth * 0.52), min(width, depth) * 0.05)


def _draw_toilet(block, spec: "FurnitureSpec") -> None:
    width, depth = spec.width, spec.depth
    _rect(block, 0, 0, width, depth * 0.28)          # rezervuar
    block.add_ellipse((width * 0.5, depth * 0.62),
                      major_axis=(0, depth * 0.34), ratio=0.62)


def _draw_shower(block, spec: "FurnitureSpec") -> None:
    width, depth = spec.width, spec.depth
    _rect(block, 0, 0, width, depth)
    _line(block, (0, 0), (width, depth))
    _line(block, (0, depth), (width, 0))
    block.add_circle((width * 0.5, depth * 0.5), min(width, depth) * 0.07)


def _draw_bathtub(block, spec: "FurnitureSpec") -> None:
    width, depth = spec.width, spec.depth
    _rect(block, 0, 0, width, depth)
    inset = min(width, depth) * 0.10
    _rect(block, inset, inset, width - inset, depth - inset)
    block.add_circle((width - inset * 3.0, depth * 0.5), min(width, depth) * 0.06)


def _draw_appliance(block, spec: "FurnitureSpec") -> None:
    """Camasir/bulasik makinesi: govde + tambur dairesi."""
    width, depth = spec.width, spec.depth
    _rect(block, 0, 0, width, depth)
    block.add_circle((width * 0.5, depth * 0.5), min(width, depth) * 0.30)


def _draw_simple(block, spec: "FurnitureSpec") -> None:
    _rect(block, 0, 0, spec.width, spec.depth)


@dataclass(frozen=True)
class FurnitureSpec:
    """Bir tefris tipinin katalog kaydi.

    `width`/`depth` yerel eksende, `INSERT` noktasi elemanin SOL-ALT
    kosesidir. Olculer ofis/katalog standardidir; proje verisi degildir."""

    key: str
    label: str
    group: str
    width: float
    depth: float
    draw: Callable[[object, "FurnitureSpec"], None] = _draw_simple
    options: dict = field(default_factory=dict)

    @property
    def block_name(self) -> str:
        return f"{BLOCK_PREFIX}{self.key.upper()}"


def _spec(key, label, group, width, depth, draw=_draw_simple, **options) -> FurnitureSpec:
    return FurnitureSpec(key, label, group, width, depth, draw, options)


# Bir konutta standart olarak bulunmasi beklenen tefris seti (kullanici
# talebi). Olculer yaygin mobilya/vitrifiye katalog degerleridir.
DEFAULT_FURNITURE_CATALOG: dict[str, FurnitureSpec] = {
    spec.key: spec for spec in (
        # --- oturma ---
        _spec("koltuk_3lu", "Koltuk (3'lu)", "OTURMA", 2100.0, 850.0, _draw_sofa, seats=3),
        _spec("koltuk_2li", "Koltuk (2'li)", "OTURMA", 1600.0, 850.0, _draw_sofa, seats=2),
        _spec("berjer", "Berjer", "OTURMA", 800.0, 850.0, _draw_sofa, seats=1),
        _spec("sehpa", "Sehpa", "OTURMA", 1100.0, 600.0, _draw_table),
        _spec("tv_unitesi", "TV unitesi", "OTURMA", 1800.0, 450.0, _draw_cabinet, door_width=600.0),
        # --- yemek ---
        _spec("yemek_masasi_4", "Yemek masasi (4 kisi)", "YEMEK", 1200.0, 800.0, _draw_table),
        _spec("yemek_masasi_6", "Yemek masasi (6 kisi)", "YEMEK", 1600.0, 900.0, _draw_table),
        _spec("sandalye", "Sandalye", "YEMEK", 450.0, 450.0, _draw_chair),
        # --- yatak odasi ---
        _spec("yatak_tek", "Tek kisilik yatak", "YATAK", 900.0, 2000.0, _draw_bed, pillows=1),
        _spec("yatak_cift", "Cift kisilik yatak", "YATAK", 1600.0, 2000.0, _draw_bed, pillows=2),
        _spec("gardirop", "Gardirop", "YATAK", 1800.0, 600.0, _draw_cabinet, door_width=600.0),
        _spec("komodin", "Komodin", "YATAK", 450.0, 400.0, _draw_cabinet, door_width=450.0),
        # --- mutfak ---
        _spec("mutfak_tezgahi", "Mutfak tezgahi", "MUTFAK", 2400.0, 600.0, _draw_cabinet, door_width=600.0),
        _spec("ocak", "Ocak", "MUTFAK", 600.0, 600.0, _draw_cooker),
        _spec("evye", "Evye", "MUTFAK", 800.0, 600.0, _draw_sink),
        _spec("buzdolabi", "Buzdolabi", "MUTFAK", 700.0, 700.0, _draw_fridge),
        _spec("bulasik_makinesi", "Bulasik makinesi", "MUTFAK", 600.0, 600.0, _draw_appliance),
        # --- islak hacim ---
        _spec("lavabo", "Lavabo", "ISLAK", 600.0, 450.0, _draw_washbasin),
        _spec("klozet", "Klozet", "ISLAK", 400.0, 700.0, _draw_toilet),
        _spec("dus_teknesi", "Dus teknesi", "ISLAK", 900.0, 900.0, _draw_shower),
        _spec("kuvet", "Kuvet", "ISLAK", 1700.0, 750.0, _draw_bathtub),
        _spec("camasir_makinesi", "Camasir makinesi", "ISLAK", 600.0, 600.0, _draw_appliance),
    )
}


class FurnitureCatalog:
    """Tefris tipi -> `FurnitureSpec`. `WallCatalog` gibi VERI ODAKLIDIR:
    farkli bir set icin alt sinif degil, farkli bir sozluk verilir."""

    def __init__(self, specs: dict[str, FurnitureSpec] | None = None,
                 groups: dict[str, FurnitureGroup] | None = None):
        self.specs = dict(specs if specs is not None else DEFAULT_FURNITURE_CATALOG)
        self.groups = dict(groups if groups is not None else FURNITURE_GROUPS)

    def __contains__(self, key: str) -> bool:
        return key in self.specs

    def get(self, key: str) -> FurnitureSpec:
        if key not in self.specs:
            raise KeyError(
                f"Bilinmeyen tefris tipi: '{key}'. Katalogdaki tipler: "
                f"{', '.join(sorted(self.specs))}"
            )
        return self.specs[key]

    def layer_of(self, spec: FurnitureSpec) -> str:
        return self.groups[spec.group].layer

    def keys(self) -> list[str]:
        return sorted(self.specs)


@dataclass(frozen=True)
class FurnitureItem:
    """Bir tefris YERLESIMI - proje verisidir, context.json'dan gelir."""

    id: str
    type: str
    position: tuple[float, float]
    rotation: float = 0.0

    @classmethod
    def from_context(cls, data: dict) -> "FurnitureItem":
        return cls(
            id=data["id"],
            type=data["type"],
            position=(float(data["position"][0]), float(data["position"][1])),
            rotation=float(data.get("rotation", 0.0)),
        )

    def translated(self, dx: float) -> "FurnitureItem":
        return FurnitureItem(self.id, self.type,
                             (self.position[0] + dx, self.position[1]), self.rotation)


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
