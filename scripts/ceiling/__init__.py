"""Yansitilmis tavan plani (RCP) modulu (DEV-023): kat plani duvarlarini
YENIDEN CIZEREK (ayni WallNetwork, ayri bir paftada), her odanin tavan
kotunu + malzeme etiketini gosteren AYRI bir pafta uretir.

**Neden ayri bir modul + ayri pafta (kullanici karari, 2026-09-28):**
endustri standardinda RCP kat planindan AYRI bir pafta turudur -
`sections`/`elevations` ile AYNI "kendi paftasi olan modul" deseni. Zemin
plani mobilyasi + tavan bilgisi ayni pafta uzerinde ust uste binerse
okunmaz hale gelir (bu yuzden mevcut kat planina bindirme - Fikir 2 -
kullanici tarafindan REDDEDILDI).

**Veri disiplini:** `rooms[].ceiling_height_mm` GERCEK proje verisidir
(asma tavan farki olabilir) - context'te ACIKCA verilir, HICBIR SEKILDE
turetilmez (orn. kat yuksekliginden TAHMIN EDILMEZ - bir dosemenin
kalinligi + olasi asma tavan boslugu bilinmeden bu bir varsayim olurdu).
Veri Oda BAZINDA tutulur (kullanici karari: "her oda kendi tavan
yuksekligini bildirir"). `ceiling_height_mm` verilmeyen bir oda RCP
paftasinda HIC gorunmez (kuzey oku ile AYNI "veri yoksa uydurma" deseni);
HICBIR odada bu veri yoksa o katin RCP paftasi HIC uretilmez
(`floor_has_ceiling_data`).

**Kot metni ayni format:** Tavan kotu, `stairs`in ust sahanlik kotuyla
AYNI kavramdir (zemin kotuna gore dusey mesafe) - bu yuzden
`scripts/levels::format_level` DOGRUDAN yeniden kullanilir ("+2.50" gibi),
kendi format mantigi ICAT EDILMEZ (DEV-029 ile AYNI "+X.XX" formati).

**v1 kapsam siniri (kullanici karari, 2026-09-28):** aydinlatma armatur
yerlesimi bu revizyonun KAPSAMI DISINDADIR - yalnizca tavan kotu + malzeme
etiketi cizilir. `stairs`/`levels` ile AYNI disiplin: net bir v1 siniri,
armatur ayri bir gelecek gelistirme konusudur.
"""
from __future__ import annotations

from dataclasses import dataclass

try:
    from ..openings import Opening
    from ..palette import color_for
    from ..levels import format_level
    from ..rooms import PolygonOps
    from ..walls import WallNetwork, draw_wall_network
except ImportError:  # dogrudan scripts/ uzerinden calistirildiginda
    from openings import Opening
    from palette import color_for
    from levels import format_level
    from rooms import PolygonOps
    from walls import WallNetwork, draw_wall_network

CEILING_LAYER = "TAVAN"
# Kod-seviyeli sabit renk (ensure_axis_layer deseni) - scripts/palette::
# PALETTE'in TEK kaynagindan gelir (DEV-030).
CEILING_RGB = color_for(CEILING_LAYER)

# Kagit-uzerinde (PRINTED) mm sabiti - pafta::to_modelspace ile projenin
# OLCEGINE gore turetilir. Tasarim verisi DEGILDIR. Etiket iki satirdir
# (kot / malzeme) - RoomLabeler'in 3 satirlik BLOK+ATTRIB mekanizmasi
# BILEREK kullanilmaz (farkli icerik, farkli sinif - kendi basit metni).
PRINTED_LABEL_HEIGHT_MM = 2.5
LABEL_LINE_GAP_RATIO = 1.4  # satirlar arasi bosluk / metin yuksekligi


@dataclass(frozen=True)
class RoomCeilingData:
    room_id: str
    height_mm: float
    finish: str | None
    centroid: tuple[float, float]


def resolve_room_ceilings(floor: dict) -> list[RoomCeilingData]:
    """`rooms[]` icinde `ceiling_height_mm` VERILMIS odalari cozer.
    Vermeyen odalar SONUCA DAHIL EDILMEZ (veri yoksa uydurulmaz)."""
    resolved: list[RoomCeilingData] = []
    for room in floor.get("rooms", []):
        if "ceiling_height_mm" not in room:
            continue
        centroid = PolygonOps.centroid(room["polygon"])
        resolved.append(RoomCeilingData(
            room_id=room["id"],
            height_mm=float(room["ceiling_height_mm"]),
            finish=room.get("ceiling_finish"),
            centroid=centroid,
        ))
    return resolved


def floor_has_ceiling_data(floor: dict) -> bool:
    """Bir katin RCP paftasi HIC uretilsin mi sorusunun tek kaynagi.
    HICBIR odada `ceiling_height_mm` yoksa o kat icin pafta ACILMAZ."""
    return any("ceiling_height_mm" in room for room in floor.get("rooms", []))


def draw_ceiling_label(msp, data: RoomCeilingData, text_height: float, layer: str = CEILING_LAYER) -> None:
    """Bir odanin RCP etiketini (kot satiri + varsa malzeme satiri)
    centroid'e ortalanmis iki satir olarak cizer."""
    from ezdxf.enums import TextEntityAlignment

    cx, cy = data.centroid
    line_gap = text_height * LABEL_LINE_GAP_RATIO
    lines = [format_level(data.height_mm)]
    if data.finish:
        lines.append(data.finish.upper())

    # Tek satirsa centroid'e ortalanir; iki satirsa centroid ARASINDA kalir
    # (RoomLabeler'daki merkezleme mantigiyla AYNI ilke, basitlestirilmis).
    top_y = cy + line_gap * (len(lines) - 1) / 2.0
    for i, line in enumerate(lines):
        text = msp.add_text(line, dxfattribs={"layer": layer, "height": text_height})
        text.set_placement((cx, top_y - i * line_gap), align=TextEntityAlignment.MIDDLE_CENTER)


class CeilingSheet:
    """Bir RCP paftasinin TAM icerigi: duvarlar (WallNetwork'ten YENIDEN
    cizilir, ayni acikliklarla) + her odanin tavan etiketi. Aks izgarasi
    BU sinifin islevi DEGILDIR (`generate_dxf.py` HER pafta icin ayni
    sekilde `axis_grid.draw_on_floor` cagirir, `sections`/`elevations` ile
    AYNI ayrim)."""

    @staticmethod
    def draw(msp, floor: dict, units: str, text_height: float, layer: str = CEILING_LAYER) -> None:
        network = WallNetwork.from_context(floor["walls"], units)
        openings = [Opening.from_context(data) for data in floor["openings"]]
        opening_dicts = [opening.as_dict() for opening in openings]
        draw_wall_network(msp, network, opening_dicts)

        for data in resolve_room_ceilings(floor):
            draw_ceiling_label(msp, data, text_height, layer)


def ensure_ceiling_layer(doc) -> None:
    """`TAVAN` katmanini idempotent kurar (`ensure_axis_layer` deseni)."""
    if CEILING_LAYER in doc.layers:
        layer = doc.layers.get(CEILING_LAYER)
    else:
        layer = doc.layers.add(name=CEILING_LAYER)
    layer.rgb = CEILING_RGB


# Bu modulun CONTEXT SOZLESMESI surumu (DEV-020). KOD surumu DEGILDIR.
# Bkz. scripts/version.py
CONTRACT_VERSION = "1.0"

__all__ = [
    "CEILING_LAYER",
    "CEILING_RGB",
    "PRINTED_LABEL_HEIGHT_MM",
    "RoomCeilingData",
    "resolve_room_ceilings",
    "floor_has_ceiling_data",
    "draw_ceiling_label",
    "CeilingSheet",
    "ensure_ceiling_layer",
    "CONTRACT_VERSION",
]
