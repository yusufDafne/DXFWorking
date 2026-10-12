"""Acıklik SINIFLARI kataloğu (DEV-076): ana giris, dukkan kapisi, vitrin, boy pencere, normal pencere.

Kullanici karari (2026-10-12): her sinifin VARSAYILAN olculeri vardir; kullanici bir acikliga `height` / `sill_height` / `width` verirse o deger
gecerlidir. Siniflar BIRBIRINDEN BAGIMSIZDIR: her birinin kendi sabitleri vardir (dukkan kapisi ana giris olculeriyle BASLAR ama ayri sabittir;
biri degisince oteki degismez - "gelecekte ozellestirilebilmeli"). Kayit (`OPENING_CLASSES`) ACIKTIR: yeni sinif eklemek = bir sabit kumesi + bir kayit.

Taban (boy pencere) 1600 x 2000 mm, denizlik 40 mm. Turevler (kullanici bildirimi):
  * vitrin (`window.shopfront`)  = boy pencere +400 mm genislik ("ortalama 40 cm"), +200 mm yukseklik; denizlik boy pencereden devralinir (40 mm; kullanici belirtmedi).
  * ana giris (`door.main_entry`) = boy pencere +100 mm genislik, +100 mm yukseklik; denizlik 40 mm devralinir (esik payi; kullanici belirtmedi).
  * dukkan kapisi (`door.shop`)  = ana giris olculeri (1700 x 2100) ama AYRI sinif ve AYRI sabitler.
Normal pencerenin GENISLIGI varsayilansizdir (proje verisidir); yukseklik 1200, denizlik 900.

Genislik `context.json`da HER ZAMAN acik yazilidir (geometri, duvar bosluklari buna dayanir): sinif genisligi yalniz YENI acikligi olustururken
(`new_opening`, `new_window`) kullanilir; yukseklik/denizlik ise kullanim aninda cozulur (`openings.heights`). Kaynaklar ADIYLA bildirilir.
"""
from __future__ import annotations

from dataclasses import dataclass

from .placement import default_window_position

SOURCE = "kullanici karari 2026-10-12"

DEFAULT_WINDOW_HEIGHT_MM = 1200.0
DEFAULT_WINDOW_SILL_MM = 900.0

DEFAULT_TALL_WINDOW_WIDTH_MM = 1600.0
DEFAULT_TALL_WINDOW_HEIGHT_MM = 2000.0
DEFAULT_TALL_WINDOW_SILL_MM = 40.0

DEFAULT_SHOPFRONT_WIDTH_MM = 2000.0        # boy pencere + 400
DEFAULT_SHOPFRONT_HEIGHT_MM = 2200.0       # boy pencere + 200
DEFAULT_SHOPFRONT_SILL_MM = 40.0           # boy pencereden devralinir (kullanici belirtmedi)

DEFAULT_MAIN_ENTRY_WIDTH_MM = 1700.0       # boy pencere + 100
DEFAULT_MAIN_ENTRY_HEIGHT_MM = 2100.0      # boy pencere + 100
DEFAULT_MAIN_ENTRY_SILL_MM = 40.0          # esik payi, boy pencereden devralinir (kullanici belirtmedi)

DEFAULT_SHOP_DOOR_WIDTH_MM = 1700.0        # ana giris olculeriyle BASLAR; AYRI sabit
DEFAULT_SHOP_DOOR_HEIGHT_MM = 2100.0
DEFAULT_SHOP_DOOR_SILL_MM = 40.0


@dataclass(frozen=True)
class OpeningClassSpec:
    key: str                  # 'window.tall'
    type: str                 # 'window' | 'door'
    value: str                # context alan degeri ('tall')
    label_tr: str             # cetvel / rapor etiketi
    mark_prefix: str          # cetvel marka oneki
    width_mm: float | None    # None = varsayilan genislik YOK (proje verisi)
    height_mm: float
    sill_mm: float
    names: tuple[str | None, str, str]   # (genislik, yukseklik, denizlik) sabit adlari - kaynak bildirimi icin
    note: str = ""

    @property
    def field(self) -> str:
        return CLASS_FIELD[self.type]


CLASS_FIELD = {"window": "window_class", "door": "door_class"}

OPENING_CLASSES: dict[str, OpeningClassSpec] = {s.key: s for s in (
    OpeningClassSpec("window.standard", "window", "standard", "PENCERE", "P", None, DEFAULT_WINDOW_HEIGHT_MM, DEFAULT_WINDOW_SILL_MM,
                     (None, "DEFAULT_WINDOW_HEIGHT_MM", "DEFAULT_WINDOW_SILL_MM"), "normal pencere; genislik proje verisi"),
    OpeningClassSpec("window.tall", "window", "tall", "BOY PENCERE", "PB", DEFAULT_TALL_WINDOW_WIDTH_MM, DEFAULT_TALL_WINDOW_HEIGHT_MM,
                     DEFAULT_TALL_WINDOW_SILL_MM, ("DEFAULT_TALL_WINDOW_WIDTH_MM", "DEFAULT_TALL_WINDOW_HEIGHT_MM", "DEFAULT_TALL_WINDOW_SILL_MM"),
                     "boy pencere / balkon kapisi; vitrin ve ana giris icin TABAN"),
    OpeningClassSpec("window.shopfront", "window", "shopfront", "VITRIN", "PV", DEFAULT_SHOPFRONT_WIDTH_MM, DEFAULT_SHOPFRONT_HEIGHT_MM,
                     DEFAULT_SHOPFRONT_SILL_MM, ("DEFAULT_SHOPFRONT_WIDTH_MM", "DEFAULT_SHOPFRONT_HEIGHT_MM", "DEFAULT_SHOPFRONT_SILL_MM"),
                     "dukkan vitrini: boy pencere +400 mm genislik, +200 mm yukseklik"),
    OpeningClassSpec("door.main_entry", "door", "main_entry", "ANA GIRIS KAPISI", "KG", DEFAULT_MAIN_ENTRY_WIDTH_MM, DEFAULT_MAIN_ENTRY_HEIGHT_MM,
                     DEFAULT_MAIN_ENTRY_SILL_MM, ("DEFAULT_MAIN_ENTRY_WIDTH_MM", "DEFAULT_MAIN_ENTRY_HEIGHT_MM", "DEFAULT_MAIN_ENTRY_SILL_MM"),
                     "apartman ana girisi: boy pencere +100 mm genislik, +100 mm yukseklik"),
    OpeningClassSpec("door.shop", "door", "shop", "DUKKAN KAPISI", "KD", DEFAULT_SHOP_DOOR_WIDTH_MM, DEFAULT_SHOP_DOOR_HEIGHT_MM,
                     DEFAULT_SHOP_DOOR_SILL_MM, ("DEFAULT_SHOP_DOOR_WIDTH_MM", "DEFAULT_SHOP_DOOR_HEIGHT_MM", "DEFAULT_SHOP_DOOR_SILL_MM"),
                     "dukkan kapisi: ana giris olculeriyle baslar, AYRI sinif/sabit"),
)}


def values_for(type_: str) -> tuple[str, ...]:
    return tuple(s.value for s in OPENING_CLASSES.values() if s.type == type_)


def class_of(op: dict) -> OpeningClassSpec | None:
    """Aciklik verisinin sinifi. Pencere: `window_class` (varsayilan 'standard'); kapi: `door_class` (yoksa None = siniflandirilmamis)."""
    t = op.get("type")
    if t == "window":
        key = f"window.{op.get('window_class', 'standard')}"
    elif t == "door":
        if "door_class" not in op:
            return None
        key = f"door.{op['door_class']}"
    else:
        return None
    if key not in OPENING_CLASSES:
        raise ValueError(f"Aciklik '{op.get('id')}': gecersiz sinif {key!r}; gecerli: {', '.join(OPENING_CLASSES)}")
    return OPENING_CLASSES[key]


def new_opening(class_key: str, opening_id: str, wall_id: str, position_from_start: float, width: float | None = None,
                layer: str = "KAPI-PENCERE", **extra) -> dict:
    """Sinif varsayilanlariyla YENI bir acikliga ait context dict'i. Genislik verilmezse sinif varsayilani (yoksa ValueError: uydurulmaz).
    Sinif alani yazilir (`standard` pencere icin yazilmaz). `extra` (height, sill_height, variant ...) aynen eklenir."""
    spec = OPENING_CLASSES[class_key]
    w = float(width) if width is not None else spec.width_mm
    if w is None:
        raise ValueError(f"{class_key}: varsayilan genislik yok - genislik verilmeli.")
    op = {"id": opening_id, "type": spec.type, "wall_id": wall_id, "position_from_start": float(position_from_start), "width": w, "layer": layer}
    if not (spec.type == "window" and spec.value == "standard"):
        op[spec.field] = spec.value
    op.update(extra)
    return op


def new_window(class_key: str, opening_id: str, host: dict, room: dict, walls: list[dict], width: float | None = None,
               layer: str = "KAPI-PENCERE", **extra) -> dict:
    """Pencere + VARSAYILAN KONUM (odanin dis duvar boyunca serbest araliginin ortasi, `placement.default_window_position`).
    Pencere araliga sigmiyorsa ValueError (konum uydurulmaz)."""
    spec = OPENING_CLASSES[class_key]
    if spec.type != "window":
        raise ValueError(f"{class_key} bir pencere sinifi degil.")
    w = float(width) if width is not None else spec.width_mm
    if w is None:
        raise ValueError(f"{class_key}: varsayilan genislik yok - genislik verilmeli.")
    pos = default_window_position(host, room, walls, w)
    if pos is None:
        raise ValueError(f"{class_key} ({w:g} mm) '{room.get('id')}' odasinin '{host.get('id')}' duvarindaki serbest araligina sigmiyor.")
    return new_opening(class_key, opening_id, host["id"], pos, w, layer, **extra)
