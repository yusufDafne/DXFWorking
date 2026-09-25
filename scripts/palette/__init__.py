"""Katman renk organizasyonu (DEV-030): TUM kod-seviyeli (context.json'dan
DEGIL, `ensure_*_layer` deseniyle koddan gelen) katman renklerinin TEK
kaynagi ve cakisma/ayrisma denetleyicisi.

**Neden ayri bir modul (kullanici karari, 2026-09-25):** kullanici, her
modulun kendi rengini kendi belirlemesi (merkezi olmayan Fikir 1) yerine
merkezi bir kontrolor modulu (Fikir 2) istedi - gerekcesi: "her modül kendi
rengini oluşturursa bazı modüller aynı rengi seçmiş olabilir ... ve bazı
modüllerin birbirlerine kontrast renkler ile bulunması ihtiyacı olabilir."
Bu MODULE TAM OLARAK bu iki riski hedefler (bkz. `validate_palette`).

**Somut bulgu (bu modulun kurulma nedeni):** `columns/standard.py::
COLUMN_RGB`, uc FARKLI katmana (`KOLON` kontur, `KOLON-TARAMA` tarama,
`KOLON-METIN` isim) TEK bir renk atiyordu - birinci risk GERCEKTEN
gerceklesmisti. Bu modul kurulurken KOLON ailesi 3 AYRI, birbirinden
`CONTRAST_MIN_DISTANCE` kadar uzak tona ayrildi (bkz. `PALETTE`).

**Kapsam (bilincli sinir):** yalnizca KOD-SAHIPLI katmanlari kapsar (AKS,
KOLON ailesi, KESIT, MERDIVEN, TEFRIS ailesi - `ensure_axis_layer` deseniyle
kurulan katmanlar). `context.json::layers[]` (proje verisi, ACI index) bu
kaydin DISINDADIR - o zaten kullanici/proje kararidir, kod bunu SECMEZ,
sadece `generate_dxf.py::setup_layers` ile uygular. Bu ayrim `DEV-030`
planinin acik kararlarindan biriydi; kullanici bu konuda ek yonlendirme
vermediginden, kod-seviyeli/proje-seviyeli ayrimi BOZULMADI (mevcut
"context.json'a asla cizim sabiti sizmamali" ilkesiyle tutarli).

**Nasil calisir:** her kod-seviyeli katman `PALETTE`de KAYITLIDIR (`name`,
`rgb`, opsiyonel `contrast_group`). Bir modul kendi rengini `color_for(name)`
ile ALIR - kendi sabitini uydurmaz. Iki kural denetlenir
(`validate_palette`, `selftest.py` ile sinanir):

1. **Hicbir iki katman AYNI rengi tasiyamaz** (tam esitlik yasagi).
2. **Ayni `contrast_group`taki katmanlar birbirinden EN AZ
   `CONTRAST_MIN_DISTANCE` (RGB Oklid mesafesi) kadar uzak olmalidir.**
   Tefris ailesi bilerek bu gruba GIRMEZ (`contrast_group=None`) - kullanici
   rev-10'da "zıt renk kullanılmaz" dedi, dusuk kontrast KASITLIDIR.

**Bilinen basitlestirme:** mesafe olcumu duz RGB Oklid uzaklamasidir, gercek
insan algisina gore agirliklandirilmis bir CIE76/CIEDE2000 DEGILDIR - bu,
`axis`in kesin RGB(67,77,88) zorunlulugu gibi basit/deterministik bir
kontrol tercih edildigi icindir (bkz. kok CLAUDE.md "Deterministik uretim
ilkesi": renk KARARI modelin degil, bu tablonun ve esik degerinin isidir).
"""
from __future__ import annotations

from dataclasses import dataclass

RGB = tuple[int, int, int]

# Ayni contrast_group icindeki iki katman arasinda kabul edilen EN KUCUK
# Oklid mesafesi. 40, mevcut renklerin (gri/kirmizi/mavi ailesi) hepsinin
# rahatca gectigi ama gercek bir yakinligi (orn. eski COLUMN_RGB uc-kez
# tekrari, mesafe=0) YAKALAYAN bir esik olarak elle secildi.
CONTRAST_MIN_DISTANCE = 40.0


@dataclass(frozen=True)
class LayerColor:
    """Bir kod-sahipli katmanin merkezi kayit girdisi.

    `contrast_group` verilmisse, bu katman AYNI gruptaki HER katmandan en
    az `CONTRAST_MIN_DISTANCE` kadar uzak olmak ZORUNDADIR
    (`validate_palette`). `None` ise yalnizca "hicbir katmanla AYNI renk
    olmama" kurali uygulanir (tam esitlik yasagi HER ZAMAN gecerlidir,
    gruptan bagimsiz).
    """

    name: str
    rgb: RGB
    contrast_group: str | None = None
    note: str = ""


# "primary": ayni pafta uzerinde AYNI ANDA gorulebilen, birbirinden
# AYRISTIRILMASI gereken yapisal/anotasyon katmanlari (aks, kolon ailesi,
# kesit isareti, merdiven). Tefris ailesi bu gruba BILEREK girmez.
PALETTE: dict[str, LayerColor] = {
    "AKS": LayerColor(
        "AKS", (67, 77, 88), "primary",
        "SABIT - kok CLAUDE.md tarafindan mandate edilir (\"Aks cizgileri "
        "... sabit RGB(67,77,88)\"), bu modul tarafindan DEGISTIRILEMEZ."),
    "KOLON": LayerColor(
        "KOLON", (150, 150, 150), "primary",
        "kontur - notr orta gri (tasiyici eleman konvansiyonu); AKS'den "
        "(67,77,88) yeterince uzak olacak sekilde SECILDI (DEV-030 "
        "oncesi 90,90,96 idi, AKS'ye COK yakindi)."),
    "KOLON-TARAMA": LayerColor(
        "KOLON-TARAMA", (190, 190, 190), "primary",
        "tarama - KOLON konturundan daha ACIK (ast/ikincil eleman "
        "okunur konvansiyonu). DEV-030 ONCESI KOLON ile AYNIYDI (somut "
        "bulgu, bkz. modul docstring'i)."),
    "KOLON-METIN": LayerColor(
        "KOLON-METIN", (45, 45, 50), "primary",
        "kolon adi (bugun kapali, meta.column_label.enabled ile acilir) - "
        "grup icinde EN KOYU (metin okunurlugu icin). DEV-030 ONCESI "
        "KOLON ile AYNIYDI."),
    "KESIT": LayerColor(
        "KESIT", (200, 30, 30), "primary",
        "kirmizimsi - kullanici talebi (rev-17): \"aks ile karistirilmasin, "
        "farkli renkte/desende olsun\"."),
    "MERDIVEN": LayerColor(
        "MERDIVEN", (60, 120, 150), "primary",
        "mavi-gri - DEV-022; diger \"primary\" tonlarindan bilerek farkli "
        "bir aile (mavi) secildi."),
    "KOT": LayerColor(
        "KOT", (50, 140, 70), "primary",
        "yesil - DEV-029; kot/datum isareti, diger \"primary\" "
        "tonlarindan (gri/kirmizi/mavi) bilerek farkli bir aile."),
    "TEFRIS-OTURMA": LayerColor(
        "TEFRIS-OTURMA", (139, 94, 60), None,
        "kahverengi ailesi (rev-10) - kullanici: \"zit renk kullanilmaz\", "
        "bilerek DUSUK kontrastli, contrast_group DISINDA."),
    "TEFRIS-YEMEK": LayerColor("TEFRIS-YEMEK", (161, 120, 79), None, "kahverengi ailesi"),
    "TEFRIS-YATAK": LayerColor("TEFRIS-YATAK", (120, 86, 66), None, "kahverengi ailesi"),
    "TEFRIS-MUTFAK": LayerColor("TEFRIS-MUTFAK", (150, 111, 94), None, "kahverengi ailesi"),
    "TEFRIS-ISLAK": LayerColor("TEFRIS-ISLAK", (131, 120, 106), None, "kahverengi ailesi"),
}


def _distance(a: RGB, b: RGB) -> float:
    return sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5


def color_for(name: str) -> RGB:
    """Bir katmanin kod-sahipli rengini merkezi kayittan doner.

    Kayitli olmayan bir isim HATA verir: yeni bir kod-seviyeli katman,
    `PALETTE`e KAYDEDILMEDEN renk ALAMAZ. Bu disiplin, merkezilestirmenin
    butun amacidir - aksi halde bir modul yine kendi ad-hoc rengini
    uydurabilir ve DEV-030'un cozdugu sorun geri gelir."""
    try:
        return PALETTE[name].rgb
    except KeyError as exc:
        raise KeyError(
            f"'{name}' scripts/palette::PALETTE icinde KAYITLI degil. Yeni "
            f"bir kod-seviyeli katman renk almadan once PALETTE'e "
            f"eklenmelidir (bkz. scripts/palette/CLAUDE.md)."
        ) from exc


def validate_palette() -> list[str]:
    """Iki kurali denetler (bkz. modul docstring'i):

    1) Hicbir iki katman AYNI rengi TASIYAMAZ.
    2) Ayni `contrast_group`taki katmanlar birbirinden EN AZ
       `CONTRAST_MIN_DISTANCE` kadar uzak olmalidir.

    Bos liste = ihlal yok. `selftest.py` bunu hem GERCEK PALETTE uzerinde
    (temiz donmeli) hem KASITLI BOZULMUS bir kopya uzerinde (ihlali
    YAKALAMALI) sinar."""
    errors: list[str] = []
    items = list(PALETTE.values())
    for i, a in enumerate(items):
        for b in items[i + 1:]:
            if a.rgb == b.rgb:
                errors.append(f"'{a.name}' ve '{b.name}' AYNI rengi tasiyor: {a.rgb}.")
            elif a.contrast_group is not None and a.contrast_group == b.contrast_group:
                distance = _distance(a.rgb, b.rgb)
                if distance < CONTRAST_MIN_DISTANCE:
                    errors.append(
                        f"'{a.name}' ve '{b.name}' (contrast_group="
                        f"'{a.contrast_group}') birbirine COK YAKIN: "
                        f"mesafe {distance:.1f} < {CONTRAST_MIN_DISTANCE:.0f}."
                    )
    return errors


# Bu modulun CONTEXT SOZLESMESI surumu (DEV-020). KOD surumu DEGILDIR.
# Bkz. scripts/version.py. Bu modul context.json'dan HICBIR SEY okumadigi
# icin (yalnizca kod-sabiti renkler), sozlesme surumu pratikte hic
# ARTMAYACAKTIR - yine de diger her modulle AYNI mekanik denetime tabidir.
CONTRACT_VERSION = "1.0"

__all__ = [
    "RGB",
    "LayerColor",
    "PALETTE",
    "CONTRAST_MIN_DISTANCE",
    "color_for",
    "validate_palette",
    "CONTRACT_VERSION",
]
