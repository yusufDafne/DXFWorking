"""Kot (seviye/datum) modulu (DEV-029): plan, kesit VE gorunuste kullanilan
standart kot (spot elevation) isareti - bayrak (ucgen) + kot metni.

**Neden ayri bir modul (kullanici karari, 2026-09-25):** kullanici acikca
yeni, kucuk, bagimsiz bir modul istedi - `northarrow`/`sections` ile AYNI
motif. Gerekce: kot hem PLAN gorunumunde (rampa/teras kademe farki) hem
KESIT/GORUNUSTE (her kat sinirinda) kullanilir, yani `elevations/`nin
("SADECE cephe istifi") bugunku net kapsaminin DISINDADIR - kot format/
sembol standardi ile "seviye istifi hesabi" birbirinden AYRI iki karardir
(bkz. `docs/development/DEVELOPMENT_TASKS.md` DEV-029 "Mimari soru").

**Kat yuksekligi hesabini YENIDEN YAZMAZ:** bu modul `elevations::
LevelStack`in zaten hesapladigi (y0, y1) ciftlerini TUKETIR - kendi kat
yuksekligi/kumulatif toplam mantigi icat ETMEZ. Baglilik YONU tektir ve
DOLAYLIDIR: bu modul `elevations`i import ETMEZ, yalnizca cagiranin
(`generate_dxf.py`) verdigi DUZ (y0, y1) sayı ciftlerini isler (axis_grid'in
`draw_on_elevation(...)` sozlesmesiyle AYNI "duck typing" deseni - somut
sinif degil, SEKIL beklenir).

**Kot metni formati (kullanici karari, 2026-09-25):** isaret + 2 ondalikli
METRE - `"+3.00"`, `"-0.20"`, sifir seviyesi icin `"±0.00"`. Bu SADECE
gosterim formatidir; context.json'daki asil olcu birimi (mm) degismez -
"Olculendirme birimi" (kok CLAUDE.md) ile AYNI ilke.

**Plan tarafi (rampa/teras spot kotu):** `floors[].level_marks[]` ile
ACIKCA verilir (`id`, `position`, `value_mm`) - bu GERCEK proje verisidir
(bir rampanin/terasin kademe farki), asla turetilmez/uydurulmaz. Kesit/
gorunus tarafinin aksine plan'da "otomatik turetilecek" bir kaynak yoktur
(kat yuksekligi PLAN duzleminde bir kavram degildir), bu yuzden veri
ACIKCA VERILMEDIYSE hicbir isaret cizilmez (kuzey oku ile AYNI "veri yoksa
uydurma" deseni).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ezdxf.enums import TextEntityAlignment

try:
    from ..pafta import parse_scale_denominator, to_modelspace
    from ..palette import color_for
except ImportError:  # dogrudan scripts/ uzerinden calistirildiginda
    from pafta import parse_scale_denominator, to_modelspace
    from palette import color_for

LEVEL_LAYER = "KOT"
# Kod-seviyeli sabit renk (ensure_axis_layer deseni) - scripts/palette::
# PALETTE'in TEK kaynagindan gelir (DEV-030).
LEVEL_RGB = color_for(LEVEL_LAYER)

# Kagit-uzerinde (PRINTED) mm sabitleri - pafta::to_modelspace ile projenin
# OLCEGINE gore turetilir. Tasarim verisi DEGILDIR. Metin bosluk payi,
# NorthArrow'daki `label_gap_ratio` ile AYNI desenle, `DefaultLevelMarkStyle.
# text_gap_ratio` uzerinden ucgen boyunun bir ORANI olarak verilir (ayri bir
# mm sabiti GEREKMEZ).
PRINTED_FLAG_SIZE_MM = 3.0
PRINTED_TEXT_HEIGHT_MM = 2.5


def format_level(value_mm: float) -> str:
    """Kullanicinin onayladigi format: isaret + 2 ondalikli metre.
    Sifire YUVARLANAN (2 ondalikta) her deger "±0.00" yazilir - hem
    tam sifir hem de yuvarlamayla sifira dusen (orn. 1mm) degerler icin
    tutarli, "-0.00" gibi cirkin/yanlis bir gorunum onlenir."""
    meters = round(value_mm / 1000.0, 2)
    if meters == 0.0:
        return "±0.00"
    sign = "+" if meters > 0 else "-"
    return f"{sign}{abs(meters):.2f}"


def level_boundaries_from_placements(placements: list[tuple[object, float, float]]) -> list[float]:
    """`LevelStack.placements()`in DUZ ciktisindan (herhangi bir (etiket,
    y0, y1) uclu listesi - `elevations::Level` sinifi ithal EDILMEZ, sadece
    SEKIL beklenir) her kat SINIRINI (tum y0'lar + en ustteki y1) turetir.
    Kat yuksekligi hesabini TEKRARLAMAZ - yalnizca zaten hesaplanmis
    degerleri TOPLAR ve tekilleştirir."""
    if not placements:
        return []
    boundaries = {y0 for _, y0, _ in placements}
    boundaries.add(placements[-1][2])
    return sorted(boundaries)


class LevelMarkStyle(Protocol):
    def draw(self, msp, anchor: tuple[float, float], value_mm: float, size: float,
             text_height: float, layer: str, text_layer: str) -> None: ...


@dataclass(frozen=True)
class DefaultLevelMarkStyle:
    """Standart kot isareti: apeksi `anchor`a (kot cizgisi uzerindeki
    noktaya) DOKUNAN, SOLA dogru acilan kucuk bir ucgen (bayrak) + solunda,
    kucuk bir bosluk payiyla, kot metni. `anchor`in NEREDE oldugu (hangi
    kenar, ne kadar icerde/discarda) bu sinifin islevi DEGILDIR
    (`NorthArrow`/`RailDrawingStandard` ile AYNI ayrim, bkz.
    `LevelMark.draw`)."""

    text_gap_ratio: float = 0.5   # metin bosluk payi / ucgen boyu (size)

    def draw(self, msp, anchor, value_mm, size, text_height, layer, text_layer) -> None:
        ax, ay = anchor
        apex = (ax, ay)
        base_x = ax - size
        b1 = (base_x, ay - size * 0.4)
        b2 = (base_x, ay + size * 0.4)
        flag = msp.add_lwpolyline([apex, b1, b2], dxfattribs={"layer": layer})
        flag.closed = True

        text_x = base_x - size * self.text_gap_ratio
        text = msp.add_text(format_level(value_mm), dxfattribs={"layer": text_layer, "height": text_height})
        text.set_placement((text_x, ay), align=TextEntityAlignment.MIDDLE_RIGHT)


class LevelMark:
    """Olcege gore turetilmis boyutla kot isareti cizer. `style` enjekte
    edilebilir (`RailDrawingStandard`/`NorthArrowStyle` ile AYNI Protocol +
    degistirilebilir varsayilan implementasyon deseni) - varsayilan
    `DefaultLevelMarkStyle`."""

    def __init__(self, scale: str, style: LevelMarkStyle | None = None,
                 layer: str = LEVEL_LAYER, text_layer: str = LEVEL_LAYER):
        denominator = parse_scale_denominator(scale)
        self.style = style or DefaultLevelMarkStyle()
        self.layer = layer
        self.text_layer = text_layer
        self.size = to_modelspace(PRINTED_FLAG_SIZE_MM, denominator)
        self.text_height = to_modelspace(PRINTED_TEXT_HEIGHT_MM, denominator)

    def draw(self, msp, anchor: tuple[float, float], value_mm: float) -> None:
        self.style.draw(msp, anchor, value_mm, self.size, self.text_height,
                        self.layer, self.text_layer)


def draw_level_marks(msp, mark: LevelMark, boundaries: list[float], anchor_x: float) -> None:
    """Verilen HER kat sinirinda (bkz. `level_boundaries_from_placements`),
    `anchor_x`te (paftanin SOL kenari - cagiranin kararidir, bu fonksiyon
    NEREYE sorusunu cevaplamaz) bir kot isareti cizer. Kesit/gorunus
    paftalari icin kullanilir."""
    for height in boundaries:
        mark.draw(msp, (anchor_x, height), height)


def draw_plan_level_marks(msp, floor: dict, mark: LevelMark) -> None:
    """`floor['level_marks']`teki HER GIRDIYI (varsa) kendi `position`unda
    cizer - GERCEK proje verisidir (rampa/teras kademe farki), context'te
    ACIKCA verilmelidir; veri yoksa hicbir sey cizilmez (kuzey oku ile AYNI
    desen)."""
    for entry in floor.get("level_marks", []):
        mark.draw(msp, tuple(entry["position"]), float(entry["value_mm"]))


def ensure_level_layer(doc) -> None:
    """`KOT` katmanini idempotent kurar (`ensure_axis_layer` deseni)."""
    if LEVEL_LAYER in doc.layers:
        layer = doc.layers.get(LEVEL_LAYER)
    else:
        layer = doc.layers.add(name=LEVEL_LAYER)
    layer.rgb = LEVEL_RGB


# Bu modulun CONTEXT SOZLESMESI surumu (DEV-020). KOD surumu DEGILDIR.
# Bkz. scripts/version.py
CONTRACT_VERSION = "1.0"

__all__ = [
    "LEVEL_LAYER",
    "LEVEL_RGB",
    "PRINTED_FLAG_SIZE_MM",
    "PRINTED_TEXT_HEIGHT_MM",
    "format_level",
    "level_boundaries_from_placements",
    "LevelMarkStyle",
    "DefaultLevelMarkStyle",
    "LevelMark",
    "draw_level_marks",
    "draw_plan_level_marks",
    "ensure_level_layer",
    "CONTRACT_VERSION",
]
