"""Tefris katalogu: tip -> olcu + cizim fonksiyonu.

Olculer OFIS/KATALOG STANDARDIDIR (cizim sabiti, `WallCatalog` gibi);
YERLESIM (konum/rotasyon) ise PROJE VERISIDIR ve context.json'dan gelir,
uydurulmaz. Katalog veri odaklidir: farkli bir set icin alt sinif degil,
farkli bir sozluk verilir.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from .groups import FURNITURE_GROUPS, FurnitureGroup
from .symbols import (
    _draw_appliance,
    _draw_bathtub,
    _draw_bed,
    _draw_cabinet,
    _draw_chair,
    _draw_cooker,
    _draw_fridge,
    _draw_shower,
    _draw_simple,
    _draw_sink,
    _draw_sofa,
    _draw_table,
    _draw_toilet,
    _draw_washbasin,
)

BLOCK_PREFIX = "TEFRIS_"

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
