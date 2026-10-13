"""Kuzey oku modulu (DEV-025): kat paftalarina standart, degistirilebilir bir
kuzey yon sembolu cizer.

**Neden ayri bir modul (kullanici karari):** kullanici acikca "kuzey oku icin
standart bir tasarim belirle, daha sonra tasarim degisikligine gidildiginde
entegrasyon zor olmasin" istedi. `RailDrawingStandard` (bkz. scripts/walls/
standard.py) ile AYNI Protocol deseni burada da uygulanir: `NorthArrowStyle`
Protocol'u tek bir `draw(...)` sozlesmesi tanimlar, `DefaultNorthArrowStyle`
bugunku standart gorseldir (daire + ibre + 'K' etiketi). Yarin ofis farkli bir
sembol (orn. yildizli pusula) isterse, YENI bir `NorthArrowStyle` yazilir ve
`NorthArrow(style=...)` ile enjekte edilir - `NorthArrow.draw` cagri
sozlesmesi DEGISMEZ, cagiran taraf (generate_dxf.py) tek satir degisir.

Veri: `meta.north_angle` (derece, saat yonunde, +Y='yukari' referansindan
GERCEK KUZEY'e). Verilmezse ok HIC cizilmez - yon uydurulmaz (schema'da
opsiyonel).

**Kuzey sozlesmesi (DEV-074, kullanici karari 2026-10-12):** vaziyet planinda kuzey simgesi DAIMA yukaridir; proje plan paftalarinda ise
projenin KUZEYE EN YAKIN cephesi paftanin ust kenarina paraleldir ve ok, vaziyet planina gore projenin yonunu gosterir. Dik acili bir
binanin cepheleri 90 derece arayla durdugu icin kuzeye en yakin cephe en cok 45 derece uzaktadir: `north_angle` bu yuzden [-45, +45]
(esdeger acilar 360 modunda normalize edilir: 350 == -10). Aralik disi aci, projenin bu sozlesmeye gore yerlestirilmedigi anlamina gelir;
proje SESSIZCE dondurulmez (otomatik migrasyon yok) - `validate.py` HATA verir ve karar ister. Kullanicinin yerlesim plani verdigi
durumu ANALIZ edecek altyapi henuz yoktur: yon ancak aciyla bildirilir. Vaziyet paftasi ayri bir maddedir (`DEV-024`).
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Protocol

from ezdxf.enums import TextEntityAlignment

try:
    from ..pafta import parse_scale_denominator, to_modelspace
except ImportError:  # dogrudan scripts/ uzerinden calistirildiginda
    from pafta import parse_scale_denominator, to_modelspace

NORTH_LABEL = "K"

# Kagit-uzerinde (PRINTED) mm sabitleri - pafta::to_modelspace ile projenin
# OLCEGINE gore turetilir (bkz. scripts/pafta/CLAUDE.md "parametrik
# olceklenebilirlik"). Tasarim verisi DEGILDIR.
PRINTED_RADIUS_MM = 6.0
PRINTED_LABEL_MM = 3.0


def rotate_point(center: tuple[float, float], distance: float, angle_deg: float) -> tuple[float, float]:
    """`center`den `distance` kadar, SAAT YONUNDE `angle_deg` acisiyla, 'yukari'
    (+Y) referansindan olculen bir nokta. angle=0 -> tam yukarida (cx,cy+d);
    angle=90 -> tam sagda (cx+d,cy). Elle dogrulanabilir: sin/cos'un standart
    (Y yukari, saat yonu tersi pozitif) matematiksel aciyla ORTUSMEDIGI icin
    (burada saat yonu pozitiftir - pusula/kerteriz konvansiyonu) isaretler
    normal trigonometriden FARKLIDIR, bu yuzden ayri bir yardimci fonksiyon
    olarak tutulur."""
    theta = math.radians(angle_deg)
    return (center[0] + distance * math.sin(theta), center[1] + distance * math.cos(theta))


class NorthArrowStyle(Protocol):
    def draw(self, msp, center: tuple[float, float], radius: float, angle_deg: float,
             layer: str, text_layer: str, text_height: float) -> None: ...


@dataclass(frozen=True)
class DefaultNorthArrowStyle:
    """Bugunku standart gorsel: daire + tek ucgen ibre (kuzeyi gosterir) +
    ibrenin ucunda 'K' etiketi. Kod-sahipli sabit oranlar (context.json'a
    SIZMAZ, bkz. kok CLAUDE.md 'DXF uretim disiplini')."""

    needle_base_ratio: float = 0.28   # ibre taban genisligi / radius
    label_gap_ratio: float = 0.45     # ibre ucundan etikete ek mesafe / radius

    def draw(self, msp, center, radius, angle_deg, layer, text_layer, text_height) -> None:
        msp.add_circle(center, radius, dxfattribs={"layer": layer})

        tip = rotate_point(center, radius, angle_deg)
        half_w = radius * self.needle_base_ratio
        b1 = rotate_point(center, half_w, angle_deg + 90.0)
        b2 = rotate_point(center, half_w, angle_deg - 90.0)
        needle = msp.add_lwpolyline([tip, b1, b2], dxfattribs={"layer": layer})
        needle.closed = True

        label_point = rotate_point(center, radius * (1.0 + self.label_gap_ratio), angle_deg)
        text = msp.add_text(NORTH_LABEL, dxfattribs={"layer": text_layer, "height": text_height})
        text.set_placement(label_point, align=TextEntityAlignment.MIDDLE_CENTER)


class NorthArrow:
    """Olcege gore turetilmis boyutlarla kuzey oku cizer. `style` enjekte
    edilebilir (bkz. modul docstring'i) - varsayilan `DefaultNorthArrowStyle`.

    Yerlesim (NEREYE cizilecegi) bu sinifin islevi DEGILDIR - o
    `generate_dxf.py`nin karari (pafta ic-cizgisinden itibaren birakilan
    padding icinde, aks baloncuklarindan uzak bir kose, bkz. modul
    CLAUDE.md 'Yerlesim')."""

    def __init__(self, scale: str, style: NorthArrowStyle | None = None,
                 layer: str = "CERCEVE", text_layer: str = "METIN"):
        scale_denominator = parse_scale_denominator(scale)
        self.style = style or DefaultNorthArrowStyle()
        self.layer = layer
        self.text_layer = text_layer
        self.radius = to_modelspace(PRINTED_RADIUS_MM, scale_denominator)
        self.label_height = to_modelspace(PRINTED_LABEL_MM, scale_denominator)
        # Cizilen herhangi bir ogenin merkezden en uzak mesafesi (ibre ucundaki etiket dahil, MUHAFAZAKAR ust sinir):
        # etiket merkezi radius*(1+label_gap_ratio) uzakta, yarim metin yuksekligi kadar daha tasar.
        gap_ratio = getattr(self.style, "label_gap_ratio", 0.45)
        self.extent = self.radius * (1.0 + gap_ratio) + self.label_height

    def corner_center(self, inner_x1: float, inner_y1: float, margin: float) -> tuple[float, float]:
        """DEV-081: kat planinda ok pafta IC cizgisinin SAG-UST kosesine yerlesir: tum cizim (daire + ibre + etiket) ic cizgiye
        `margin` kadar pay birakarak kose icinde kalir. Konum karari cagirana aittir (`generate_dxf.py`/`preview.py` ayni yardimciyi kullanir)."""
        return (inner_x1 - margin - self.extent, inner_y1 - margin - self.extent)

    def draw(self, msp, center: tuple[float, float], angle_deg: float) -> None:
        self.style.draw(msp, center, self.radius, angle_deg, self.layer,
                        self.text_layer, self.label_height)


# Bu modulun CONTEXT SOZLESMESI surumu (DEV-020). KOD surumu DEGILDIR.
# Bkz. scripts/version.py
CONTRACT_VERSION = "1.2"   # DEV-081: dikdortgen binada [-90, +90] (uzun kenar yatay, kuzeye yakin uzun yuz ustte); kare [-45, +45]; 1.1: DEV-074 sozlesmesi

# Dik acili binanin cepheleri 90 derece arayla: kuzeye en yakin cephe en cok 90/2 = 45 derece uzaktadir (geometri, olcum esigi degil).
NORTH_HALF_RANGE_DEG = 45.0            # TAM KARE bina: dort cepheden kuzeye en yakini en cok 90/2 = 45 derece uzakta
# DEV-081 (kullanici karari 2026-10-13): proje paftaya UZUN KENARI YATAY, kuzeye yakin UZUN yuzu USTTE olacak sekilde konur. Iki karsit uzun yuzun
# disa bakan normalleri 180 derece arayla oldugundan kuzeye yakin olan en cok 90 derece uzaktadir (geometri, olcum esigi degil).
NORTH_LONG_SIDE_HALF_RANGE_DEG = 90.0


def north_half_range(meta: dict) -> float:
    """Izinli |north_angle| ust siniri: dikdortgen binada (floor_width != floor_depth) 90, tam karede 45; olculer bilinmiyorsa MUHAFAZAKAR 45."""
    w, d = meta.get("floor_width"), meta.get("floor_depth")
    if isinstance(w, (int, float)) and isinstance(d, (int, float)) and not isinstance(w, bool) and not isinstance(d, bool) and w > 0 and d > 0 and w != d:
        return NORTH_LONG_SIDE_HALF_RANGE_DEG
    return NORTH_HALF_RANGE_DEG


def normalize_north_angle(angle_deg: float) -> float:
    """Esdeger aciyi (-180, +180] araligina getirir (350 -> -10). Cizim/olcum ham degeri kullanmaya devam eder (esdegerdir)."""
    a = (float(angle_deg) + 180.0) % 360.0 - 180.0
    return 180.0 if a == -180.0 else a


def check_north_convention(meta: dict) -> list[str]:
    """validate.py HATALARI: `meta.north_angle` verilmisse kuzeye yakin uzun yuz ustte olmali (dikdortgen: |aci| <= 90; tam kare: <= 45).
    Verilmemisse bos (ok cizilmez, yon uydurulmaz; yonelim veçhesi 'kuzey yonu verilmedi' der)."""
    if "north_angle" not in meta:
        return []
    raw = meta["north_angle"]
    a = normalize_north_angle(raw)
    limit = north_half_range(meta)
    if abs(a) <= limit:
        return []
    shape = "dikdortgen binada uzun kenar yatay ve kuzeye yakin uzun yuz ustte" if limit == NORTH_LONG_SIDE_HALF_RANGE_DEG else "kare binada kuzeye en yakin cephe ustte"
    return [f"meta.north_angle={raw:g} (esdeger {a:g}): kuzey sozlesmesi {shape} olmasini ister (aci -{limit:g}..+{limit:g}). Bu aci icin proje farkli "
            "bir yonde yerlestirilmis; proje sessizce dondurulmez - projeyi vaziyete gore yeniden yerlestirmek mi yoksa aciyi duzeltmek mi istiyorsunuz?"]


def check_north_layout(meta: dict) -> list[str]:
    """validate.py UYARISI (yalniz `north_angle` verilmisse): paftalama uzun kenari YATAY ister; floor_width < floor_depth ise plan bu
    sozlesmeye gore yerlestirilmemistir. Otomatik dondurme YOK - karar sorulur (DEV-081)."""
    if "north_angle" not in meta:
        return []
    w, d = meta.get("floor_width"), meta.get("floor_depth")
    if isinstance(w, (int, float)) and isinstance(d, (int, float)) and w < d:
        return [f"meta.floor_width ({w:g}) < meta.floor_depth ({d:g}): kuzey sozlesmesi paftalamada binanin UZUN kenarinin yatay olmasini ister. "
                "Plan bu sozlesmeye gore yerlestirilmemis; proje sessizce dondurulmez - kuzey okunun yonu ve cephe yerlesimi icin karar sizin."]
    return []


__all__ = [
    "NORTH_HALF_RANGE_DEG",
    "NORTH_LONG_SIDE_HALF_RANGE_DEG",
    "north_half_range",
    "check_north_layout",
    "check_north_convention",
    "normalize_north_angle",
    "NORTH_LABEL",
    "PRINTED_RADIUS_MM",
    "PRINTED_LABEL_MM",
    "NorthArrow",
    "NorthArrowStyle",
    "DefaultNorthArrowStyle",
    "rotate_point",
]
