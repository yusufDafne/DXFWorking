"""Pafta modulu: pafta (sheet) cercevesi, sag-alt kose baslik kutusu, pafta
tasma korumasi ve kagit/olcek boyutlandirma planlamasi.

Bu modul, projenin ILK izole cizim modulu'dur (bkz. scripts/pafta/CLAUDE.md).
scripts/generate_dxf.py bu moduldeki `Sheet`, `PaftaOverflowError`,
`PaperSizePlanner` ve `fit_text_height` isimlerini import eder; modulun kendi
ic detaylarina (ornegin tam olarak nasil olctugu) bagimli degildir.

SORUMLULUK SINIRI: Bu modul SADECE pafta cercevesi + baslik kutusu + tasma
kontrolu + kagit boyutu hesaplarindan sorumludur. Duvar/oda/aks cizim mantigi
buraya KARISMAZ (onlar kendi modullerinde/yerlerinde kalir).
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import ezdxf
import ezdxf.bbox as bbox_mod
from ezdxf.enums import TextEntityAlignment
from ezdxf.fonts import fonts

# --- Cizim/sunum sabitleri (tasarim verisi degil, bkz. CLAUDE.md) ---
# Baslik kutusunun PRATIK ust sinirlari (bkz. asagida PRINTED_TITLE_BOX_*) -
# tam bir "uniform sheet template" (standart kagit boyutuna oturan pafta)
# uygulanana kadar kutu bu degerleri ASMAZ.
MAX_TITLE_BOX_WIDTH_MM = 8000.0
MAX_TITLE_BOX_HEIGHT_MM = 1200.0

# CONTENT_PADDING: paftanin IC cizgisinden itibaren gercek cizime (aks
# baloncugu + baslik kutusu dahil) birakilan bosluk. Sag-alt kosede HEM aks
# baloncugu HEM baslik kutusu bulunabildiginden, (padding+frame_gap) su
# ikisinin toplamini + bir tampon payi rahatça icine alacak kadar buyuk
# olmalidir: AxisGrid'in ulasabilecegi en uzak nokta (generate_dxf.py'deki
# AXIS_EXTENSION+AXIS_BUBBLE_RADIUS = 1200+450=1650) + MAX_TITLE_BOX_HEIGHT_MM
# (1200) + tampon (~350) = ~3200 (iki kaynagin - pafta modulu + aks modulu -
# sabitlerini bilerek secildi, bkz. scripts/pafta/CLAUDE.md). Bu deger
# kucuk dusurulursa aks baloncugu ile baslik kutusu gorsel olarak cakisir -
# bu gercekten yasandi ve boylece duzeltildi.
CONTENT_PADDING = 3200.0
FRAME_GAP = 150.0                # cift cizgili cerceve (ic/dis hat) arasi mesafe
# Metin sigdirma olcumlerinde kullanilan font. CIZILEN fontla AYNI olmak
# zorundadir (bkz. scripts/typography/CLAUDE.md), bu yuzden burada ikinci bir
# sabit TUTULMAZ - proje fontu typography modulunden alinir.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
try:
    from ..typography import DEFAULT_FONT_FILE as DEFAULT_FONT
except ImportError:  # dogrudan scripts/ uzerinden calistirildiginda
    from typography import DEFAULT_FONT_FILE as DEFAULT_FONT

# --- Kagit-uzerinde (PRINTED) mm standartlari - DIN/ISO 5457 + TMMOB/imar
# mevzuati arastirmasindan alinmistir (bkz. scripts/pafta/CLAUDE.md). Bunlar
# BASILI kagitta olculen sabit degerlerdir; modelspace karsiligi
# `to_modelspace(printed_mm, scale_denominator)` ile PROJENIN OLCEGINE gore
# turetilir - yani ayni "185mm'lik antet" 1:50'de 9250mm, 1:100'de 18500mm
# modelspace genisligine karsilik gelir. Bu, scripts/CLAUDE.md'deki
# "parametrik olceklenebilirlik" ilkesinin ilk gercek uygulamasidir.
PRINTED_TITLE_BOX_WIDTH_MM = 185.0
PRINTED_TITLE_BOX_HEIGHT_MM = 70.0     # Tip-B (ozet/serit) anteti: 60-80mm araligi, orta deger
PRINTED_TITLE_TEXT_MM = 3.5
PRINTED_LABEL_TEXT_MM = 2.5
PRINTED_MARGIN_LEFT_MM = 20.0           # cilt/zimba payi (bilgi amacli, henuz cizilmiyor)
PRINTED_MARGIN_MM = 10.0                # sag/ust/alt (bilgi amacli, henuz cizilmiyor)

# --- ISO 7200 Tip-A (kapak / resmi onay) anteti - kagit uzerinde (PRINTED) mm.
# Kullanicinin mevzuat arastirmasi Tip-A icin 190x277mm veya 210x297mm (A4)
# verir; burada A4 kullanilir. Tip-B (serit antet, yukarida) her paftanin
# sag-alt kosesindeki kucuk kutudur - Tip-A ise SADECE kapak paftasinda,
# paftanin EN ALTINA yerlestirilen tam bir A4 kapak blogudur.
PRINTED_COVER_WIDTH_MM = 210.0
PRINTED_COVER_HEIGHT_MM = 297.0
# Kapak cercevesi, Sheet._draw_double_frame gibi HER KENARDAN ESIT offsetli
# cift cizgidir. (Onceki surumde DIN/ISO 5457 sayfa marjlari uygulaniyordu -
# sol 20mm, diger 10mm - bu ESIT OLMAYAN bir offset gorunumu veriyordu ve
# kullanici bunu duzelttirdi. Cilt payi, kapak blogunun kendi icinde degil,
# paftanin genelinde ele alinir.)
PRINTED_COVER_FRAME_GAP_MM = 10.0
PRINTED_COVER_TITLE_MM = 7.0
PRINTED_COVER_TEXT_MM = 3.5
PRINTED_COVER_LABEL_MM = 2.5

# Rulo kagit: BRUT (nominal) yukseklik -> NET kullanilabilir yukseklik (mm),
# ust/alt 10mm pay dusulmus haliyle. Kullanicinin "45/60/90'lik kagit"
# ifadesi nominal rulo genisligini belirtir; gercek cizilebilir alan bundan
# kucuktur.
ROLL_PAPER_NET_HEIGHT_MM = {45.0: 430.0, 60.0: 580.0, 90.0: 880.0}
ROLL_PAPER_LENGTH_RANGE_MM = (210.0, 2000.0)  # X ekseni (uzunluk) serbest araligi, bilgi amacli

# Proje tipine gore ZORUNLU/izin verilen olcekler (TMMOB / imar yonetmeligi).
# "footprint_limit_m2": None ise sinir yok (olcek her zaman sabit); bir sayi
# ise SADECE oturum bu deger ALTINDAYSA listedeki KUCUK olcek de gecerlidir.
PROJECT_TYPES: dict[str, dict] = {
    "MIMARI_UYGULAMA": {"scales": ["1:50"], "footprint_limit_m2": None,
                         "label": "Mimari Uygulama / Ruhsat Projesi"},
    "MIMARI_RUHSAT_KUCUK": {"scales": ["1:100", "1:50"], "footprint_limit_m2": 300.0,
                             "label": "Kucuk Olcekli Mimari Ruhsat Projesi"},
    "STATIK_KALIP": {"scales": ["1:50"], "footprint_limit_m2": None,
                      "label": "Statik Betonarme Kalip Plani"},
    "VAZIYET_PLANI": {"scales": ["1:200", "1:500"], "footprint_limit_m2": None,
                       "label": "Vaziyet / Yerlesim Plani"},
    "DETAY": {"scales": ["1:20", "1:10", "1:5", "1:1"], "footprint_limit_m2": None,
              "label": "Detay Cizimleri"},
}


def parse_scale_denominator(scale: str) -> float:
    sep = ":" if ":" in scale else "/"
    parts = scale.split(sep)
    return float(parts[1])


def to_modelspace(printed_mm: float, scale_denominator: float) -> float:
    """Kagit uzerinde olculen bir mm degerini, projenin olcegine gore
    modelspace (gercek dunya) karsiligina cevirir."""
    return printed_mm * scale_denominator


class PaftaOverflowError(Exception):
    """Bir paftanin icerigi kendi cercevesini astiginda firlatilir. Bu HATA,
    DXF uretimini durdurur - 'bir proje asla pafta disina tasmamali' kurali
    boylece kod seviyesinde zorunlu kilinir."""


def add_text(msp, content: str, position, height: float, layer: str, align=TextEntityAlignment.LEFT):
    text = msp.add_text(content, dxfattribs={"layer": layer, "height": height})
    text.set_placement(position, align=align)
    return text


def fit_text_height(text: str, available_width: float, max_height: float,
                     min_height: float = 60.0, font: str = DEFAULT_FONT) -> float:
    """Verilen metnin `available_width` icine sigacagi, `max_height`'i
    ASMAYAN en buyuk metin yuksekligini gercek font metrikleriyle hesaplar
    (kaba karakter-sayisi tahmini DEGIL - bu, onceki surumde pafta baslik
    kutusu ve cephe kat etiketlerinin tasmasina sebep olan hatanin duzeltilmis
    halidir)."""
    if not text or available_width <= 0:
        return max_height
    probe_height = 100.0
    probe_width = fonts.make_font(font, probe_height).text_width(text)
    if probe_width <= 0:
        return max_height
    fitted = probe_height * (available_width / probe_width)
    return max(min_height, min(max_height, fitted))


def fit_uniform_text_height(texts: list[str], available_width: float, max_height: float,
                             min_height: float = 60.0, font: str = DEFAULT_FONT) -> float:
    """`fit_text_height`'i bir metin listesinin EN UZUNUNA (en genisine) gore
    uygular ve tek bir ortak boyut dondurur - boylece cagiran taraf ayni
    boyutu TUM metinlere tek tip uygulayabilir."""
    height = max_height
    for text in texts:
        if not text:
            continue
        height = min(height, fit_text_height(text, available_width, max_height, min_height, font))
    return height


def verify_within_frame(entities, x0: float, y0: float, x1: float, y1: float,
                         label: str, tol: float = 5.0) -> None:
    """`entities` (bir paftaya ait DXF varliklari) tamamen [x0,y0]-[x1,y1]
    cercevesi icinde mi kontrol eder; degilse PaftaOverflowError firlatir."""
    if not entities:
        return
    box = bbox_mod.extents(entities, fast=True)
    if not box.has_data:
        return
    ex0, ey0, _ = box.extmin
    ex1, ey1, _ = box.extmax
    if ex0 < x0 - tol or ey0 < y0 - tol or ex1 > x1 + tol or ey1 > y1 + tol:
        raise PaftaOverflowError(
            f"Pafta '{label}' cercevesini asiyor: icerik sinirlari "
            f"({ex0:.0f},{ey0:.0f})-({ex1:.0f},{ey1:.0f}), cerceve sinirlari "
            f"({x0:.0f},{y0:.0f})-({x1:.0f},{y1:.0f}). Asan miktar: "
            f"sol={max(0.0, x0 - ex0):.0f} sag={max(0.0, ex1 - x1):.0f} "
            f"alt={max(0.0, y0 - ey0):.0f} ust={max(0.0, ey1 - y1):.0f} (birim: mm)."
        )


class PaperSizePlanner:
    """TMMOB/imar mevzuati arastirmasina dayanir (bkz. scripts/pafta/CLAUDE.md
    '#3 Rulo kagit ve marj standartlari'). `select(...)`, context.json'da
    ZATEN sabitlenmis olan `meta.scale` icin, projenin en yuksek paftasinin
    hangi NET rulo yuksekligine (`ROLL_PAPER_NET_HEIGHT_MM`) sigdigini
    hesaplar/raporlar.

    **KRITIK KURAL (mevzuat):** Pafta boyutuna sigdirmak icin OLCEK
    KUCULTULEMEZ - bu, eski surumdeki '1/50 favori, sigmazsa 1/100'e gec'
    kaskad fikrinin YANLIS oldugunu gosterdi ve DUZELTILDI. En buyuk rulo
    (90'lik, net 880mm) bile yetmiyorsa tek gecerli cozum PAFTA BOLME +
    KEYPLAN'dir (henuz uygulanmadi, bkz. scripts/pafta/CLAUDE.md), OLCEK
    DEGISTIRMEK DEGIL. Bu sinif olcegi hicbir zaman kendiliginden degistirmez
    veya kucultmez."""

    def __init__(self, scale: str):
        self.scale = scale
        self.scale_denominator = parse_scale_denominator(scale)

    def required_paper_height_cm(self, max_sheet_height_mm: float) -> float:
        return max_sheet_height_mm / 10.0 / self.scale_denominator

    def select(self, max_sheet_height_mm: float) -> dict:
        required_cm = self.required_paper_height_cm(max_sheet_height_mm)
        for nominal_cm, net_mm in sorted(ROLL_PAPER_NET_HEIGHT_MM.items()):
            if required_cm <= net_mm / 10.0:
                return {
                    "fits": True, "paper_height_cm": nominal_cm,
                    "net_height_cm": net_mm / 10.0,
                    "required_cm": required_cm, "scale": self.scale,
                }
        return {
            "fits": False, "paper_height_cm": None, "net_height_cm": None,
            "required_cm": required_cm, "scale": self.scale,
        }

    def classify_violation(self, project_type: str | None, footprint_m2: float | None) -> str | None:
        """`project_type` icin `self.scale` mevzuata uygun mu kontrol eder;
        degilse aciklayici bir uyari metni, uygunsa None doner. Bilinmeyen
        bir `project_type` icin de None doner (bu planlayici siniflandirma
        dayatmaz, sadece BILDIRILEN bir siniflandirmayi dogrular)."""
        if project_type is None or project_type not in PROJECT_TYPES:
            return None
        rule = PROJECT_TYPES[project_type]
        allowed_scales = rule["scales"]
        limit = rule["footprint_limit_m2"]
        if self.scale in allowed_scales:
            # 'MIMARI_RUHSAT_KUCUK' gibi kucuk-oturum istisnasi olan
            # tiplerde, istisna disi (daha kucuk detayli) olcek her zaman
            # serbesttir (ornegin 1:50, <300m2 bir projede de kullanilabilir);
            # sadece EN BUYUK (en izin verici) olcegin footprint sinirini
            # asip asmadigini kontrol etmek yeterlidir.
            if limit is not None and footprint_m2 is not None and footprint_m2 > limit:
                # sadece istisna olcegi (listenin ilki, orn. 1:100) sinirliysa uyar
                permissive_scale = allowed_scales[0]
                if self.scale == permissive_scale:
                    return (
                        f"'{project_type}' ({rule['label']}) sinifinda '{self.scale}' olcegi "
                        f"SADECE oturum <= {limit:.0f} m2 icin gecerlidir; bu projenin oturumu "
                        f"{footprint_m2:.0f} m2. Daha kucuk detayli bir olcek (orn. "
                        f"{allowed_scales[-1]}) gerekebilir."
                    )
            return None
        return (
            f"'{project_type}' ({rule['label']}) sinifinda izin verilen olcek(ler): "
            f"{', '.join(allowed_scales)} - ancak proje '{self.scale}' kullaniyor."
        )


class CoverBlock:
    """ISO 7200 **Tip-A kapak** blogu: kapak paftasinin EN ALTINA yerlestirilen,
    kagit uzerinde tam A4 (210x297mm) olculerinde bir kapak.

    Tip-B (`Sheet`in sag-alt kosedeki iki satirlik serit anteti) HER paftada
    bulunur; Tip-A ise SADECE kapak paftasinda, bir kere cizilir. Olculer
    kagit-uzerinde (PRINTED) mm cinsinden tanimlanir ve `to_modelspace(...)`
    ile projenin OLCEGINE gore turetilir - yani ayni A4 kapak 1:50'de
    10500x14850mm, 1:100'de 21000x29700mm modelspace alani kaplar.

    **Veri uydurulmaz:** `info_rows`'ta degeri bos gelen bir alan (orn. mimar
    adi veya tarih context.json'da yoksa) metin olarak UYDURULMAZ; yerine elle
    doldurulacak bir **doldurma cizgisi** cizilir. Imza alanlari da bos
    birakilir; basligi bos gelen bir imza alani `UNVAN_PLACEHOLDER` ile
    "sonra belirlenecek" olarak isaretlenir."""

    # Ic alana (marjlarin icine) gore, kagit uzerinde mm cinsinden yerlesim.
    TITLE_Y_MM = 247.0
    RULE_Y_MM = 234.0
    INFO_TOP_Y_MM = 214.0
    INFO_STEP_MM = 15.0
    INFO_VALUE_X_MM = 55.0
    SIGNATURE_HEAD_Y_MM = 145.0
    SIGNATURE_BAND_BOTTOM_MM = 20.0
    SIGNATURE_BAND_TOP_MM = 130.0
    SIGNATURE_COLUMNS = 2
    SIGNATURE_GAP_MM = 10.0
    TEXT_PAD_MM = 4.0          # ic marj hattina bitisik metin birakilmaz
    UNVAN_PLACEHOLDER = "(UNVAN)"

    def __init__(self, scale: str, frame_layer: str = "CERCEVE", text_layer: str = "METIN"):
        self.scale = scale
        self.scale_denominator = parse_scale_denominator(scale)
        self.frame_layer = frame_layer
        self.text_layer = text_layer
        self.width = self.mm(PRINTED_COVER_WIDTH_MM)
        self.height = self.mm(PRINTED_COVER_HEIGHT_MM)
        # Kapak paftasinin cerceve boslugu da budur: pafta DIS cercevesi kapak
        # blogunun dis hattiyla CAKISIR (bkz. draw(..., outer_frame=False)).
        self.frame_gap = self.mm(PRINTED_COVER_FRAME_GAP_MM)

    def mm(self, printed_mm: float) -> float:
        """Kagit-uzerinde mm -> modelspace birimi (projenin olcegine gore)."""
        return to_modelspace(printed_mm, self.scale_denominator)

    def _rect(self, msp, x0: float, y0: float, x1: float, y1: float):
        poly = msp.add_lwpolyline(
            [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], dxfattribs={"layer": self.frame_layer}
        )
        poly.closed = True
        return poly

    def draw(self, msp, x0: float, y0: float, title: str,
             info_rows: list[tuple[str, str]], signature_labels: list[str],
             outer_frame: bool = True) -> None:
        """A4 kapagi sol-alt kosesi (x0, y0) olacak sekilde cizer.

        `outer_frame=False`: kapak paftasinin DIS cercevesi zaten bu blogun
        dis hattiyla ayni yerde oldugundan (pafta genisligi = kapak genisligi)
        cift cizim yapilmaz; yalnizca A4 panelini yukaridan kapatan ust kenar
        cizgileri cizilir."""
        mm = self.mm
        # Dis A4 hatti + ic hat: Sheet._draw_double_frame ile ayni "cift/
        # ofsetli cizgi" yaklasimi, HER KENARDAN ESIT offsetle.
        gap = self.frame_gap
        ix0, iy0 = x0 + gap, y0 + gap
        ix1, iy1 = x0 + self.width - gap, y0 + self.height - gap
        if outer_frame:
            self._rect(msp, x0, y0, x0 + self.width, y0 + self.height)
            self._rect(msp, ix0, iy0, ix1, iy1)
        else:
            # Sol/sag/alt kenarlar paftanin cift cercevesinden geliyor; burada
            # sadece A4 panelinin UST kenari (ayni cift hat mantigiyla) eklenir.
            msp.add_line((x0, y0 + self.height), (x0 + self.width, y0 + self.height),
                         dxfattribs={"layer": self.frame_layer})
            msp.add_line((ix0, iy1), (ix1, iy1), dxfattribs={"layer": self.frame_layer})
        inner_width = ix1 - ix0

        title_height = fit_text_height(title, inner_width - mm(10.0), mm(PRINTED_COVER_TITLE_MM))
        add_text(msp, title, (ix0 + inner_width / 2.0, iy0 + mm(self.TITLE_Y_MM)),
                 title_height, self.text_layer, align=TextEntityAlignment.MIDDLE_CENTER)
        rule_y = iy0 + mm(self.RULE_Y_MM)
        msp.add_line((ix0, rule_y), (ix1, rule_y), dxfattribs={"layer": self.frame_layer})

        text_height = mm(PRINTED_COVER_TEXT_MM)
        text_pad = mm(self.TEXT_PAD_MM)
        label_x = ix0 + text_pad
        fill_x1 = ix1 - text_pad
        value_x = ix0 + mm(self.INFO_VALUE_X_MM)
        for index, (label, value) in enumerate(info_rows):
            row_y = iy0 + mm(self.INFO_TOP_Y_MM - self.INFO_STEP_MM * index)
            add_text(msp, f"{label} :", (label_x, row_y), text_height, self.text_layer,
                     align=TextEntityAlignment.MIDDLE_LEFT)
            if value:
                add_text(msp, value, (value_x, row_y),
                         fit_text_height(value, fill_x1 - value_x, text_height),
                         self.text_layer, align=TextEntityAlignment.MIDDLE_LEFT)
            else:
                # Deger context.json'da YOK - metin uydurulmaz, elle
                # doldurulacak bir cizgi birakilir (bkz. kok CLAUDE.md).
                fill_y = row_y - mm(2.0)
                msp.add_line((value_x, fill_y), (fill_x1, fill_y), dxfattribs={"layer": self.frame_layer})

        if not signature_labels:
            return
        add_text(msp, "IMZA ALANLARI", (label_x, iy0 + mm(self.SIGNATURE_HEAD_Y_MM)),
                 text_height, self.text_layer, align=TextEntityAlignment.MIDDLE_LEFT)

        columns = self.SIGNATURE_COLUMNS
        rows = math.ceil(len(signature_labels) / columns)
        gap = mm(self.SIGNATURE_GAP_MM)
        band_height = mm(self.SIGNATURE_BAND_TOP_MM - self.SIGNATURE_BAND_BOTTOM_MM)
        cell_width = (inner_width - gap * (columns - 1)) / columns
        cell_height = (band_height - gap * (rows - 1)) / rows
        label_height = mm(PRINTED_COVER_LABEL_MM)
        for index, label in enumerate(signature_labels):
            column = index % columns
            row = index // columns
            bx0 = ix0 + column * (cell_width + gap)
            # ilk satir EN USTTE dursun diye satir sirasi yukaridan asagiya
            by0 = iy0 + mm(self.SIGNATURE_BAND_BOTTOM_MM) + (rows - 1 - row) * (cell_height + gap)
            self._rect(msp, bx0, by0, bx0 + cell_width, by0 + cell_height)
            caption = label or self.UNVAN_PLACEHOLDER
            add_text(msp, caption,
                     (bx0 + mm(4.0), by0 + mm(5.0)),
                     fit_text_height(caption, cell_width - mm(8.0), label_height, min_height=label_height * 0.5),
                     self.text_layer, align=TextEntityAlignment.MIDDLE_LEFT)


class Sheet:
    """Pafta cercevesi + standart sag-alt kose baslik kutusu (bkz. kok
    CLAUDE.md 'Pafta başlık kutusu' standardi). Cerceve, duvar rail mantigina
    benzer sekilde iki ofsetli cizgi (dis + ic hat) olarak cizilir
    (`_draw_double_frame`). Baslik kutusu iki satirdir: ust olcek, alt pafta
    adi - pafta numarasi gosterilmez. Tum paftalarda AYNI metin boyutu
    kullanilir; bu boyut, en uzun pafta adinin/olcek metninin kutuya GERCEK
    FONT METRIKLERIYLE sigacagi en kucuk boyut olarak kurulumda bir kere
    hesaplanir.

    **Ortak yukseklik, dinamik genislik, hizali paftalar:** Projedeki TUM
    paftalar (kat planlari + gorunusler) AYNI MUTLAK dis-cerceve
    Y-ARALIGINI (`frame_y0`..`frame_y1`) paylasir - bu, kurulumda
    `content_ranges` (her paftanin kendi ham `(y_bottom, y_top)` araligi)
    listesinin en genisini kapsayacak sekilde BIR KERE hesaplanir. Boylece
    hem TUM paftalarin disaridan olculen YUKSEKLIGI birebir aynidir, HEM DE
    paftalar birbirine gore DUSEY olarak KAYMAZ (her paftanin ust/alt dis
    cizgisi ayni mutlak Y'de biter - ic icerigi farkli bir "merkeze" sahip
    olsa da, ornegin bir gorunusun zemin kotu ile bir kat planinin kendi
    yerel sifiri). Kisa icerikli paftalar (kat planlari), farki kendi
    icin ozel simetrik bir paylasimla degil, PAYLASILAN mutlak araligin
    neresine dustugu kadar bosluk alir - simetri aranmaz, hizalanma esastir.
    GENISLIK ise HER paftanin kendi icerigine gore serbestce (dinamik)
    belirlenir, bir sinir yoktur. Padding, DAIMA paftanin IC cizgisinden
    itibaren olculur (dis cizgiden degil) - `CONTENT_PADDING`.

    **Paftalar dis cizgilerinden bitisiktir:** Paftalar arasinda ekstra
    bosluk YOKTUR - bir paftanin dis cercevesinin sag kenari, bir sonrakinin
    dis cercevesinin sol kenarina TAM OTURUR (cagiran taraf, ardisik
    paftalarin X-ofsetini `width + 2*(padding+frame_gap)` kadar ilerleterek
    bunu saglar).

    `draw(...)`'a `content_entities` verilirse, cizilen DIS cerceve
    sinirlarini asip asmadigi `verify_within_frame` ile dogrulanir (asarsa
    PaftaOverflowError) - 'bir proje asla pafta disina tasmamali' kuralinin
    uygulamasi budur."""

    def __init__(self, scale: str, base_text_height: float, sheet_labels: list[str],
                 content_ranges: list[tuple[float, float]], padding: float = CONTENT_PADDING,
                 frame_gap: float = FRAME_GAP):
        self.scale = scale
        self.padding = padding
        self.frame_gap = frame_gap
        scale_denominator = parse_scale_denominator(scale)
        # Antet (baslik kutusu) boyutlari DIN/ISO 5457 Tip-B (ozet/serit
        # pafta anteti) standardindan, projenin OLCEGINE gore turetilir -
        # sabit bir modelspace mm degeri DEGIL (bkz. scripts/pafta/CLAUDE.md).
        # PRATIK SINIR: bu deger, paftamiz TAM BIR STANDART KAGIDA
        # oturtulmadigi (icerigi siki saran bir tuval oldugu) surece cok
        # buyuk cikabilir (orn. 1:100'de 18500mm) - "uniform sheet template"
        # (bkz. Bilinen sinirlamalar) uygulanana kadar makul bir ust sinirla
        # kirpilir; kucuk olcekli (DETAY vb.) paftalarda sinir devreye
        # girmez ve gercek deger kullanilir.
        self.box_width = min(to_modelspace(PRINTED_TITLE_BOX_WIDTH_MM, scale_denominator), MAX_TITLE_BOX_WIDTH_MM)
        self.box_height = min(to_modelspace(PRINTED_TITLE_BOX_HEIGHT_MM, scale_denominator), MAX_TITLE_BOX_HEIGHT_MM)
        self.text_padding = to_modelspace(2.0, scale_denominator)
        regulation_text_height = to_modelspace(PRINTED_TITLE_TEXT_MM, scale_denominator)
        candidates = [f"OLCEK {scale}"] + list(sheet_labels)
        self.label_text_height = fit_uniform_text_height(
            candidates, available_width=self.box_width - 300.0,
            max_height=min(base_text_height, regulation_text_height),
        )
        pads = padding + frame_gap
        if content_ranges:
            self.frame_y0 = min(y_bottom - pads for y_bottom, _ in content_ranges)
            self.frame_y1 = max(y_top + pads for _, y_top in content_ranges)
        else:
            self.frame_y0, self.frame_y1 = -pads, pads
        self.outer_height = self.frame_y1 - self.frame_y0

    def draw(self, msp, dx: float, width: float, y_bottom: float, y_top: float,
              label: str, content_entities=None, title_box: bool = True,
              padding: float | None = None, frame_gap: float | None = None) -> None:
        # Bu paftanin kendi (y_bottom, y_top) icerigi, TUM projede paylasilan
        # mutlak frame_y0/frame_y1 araligina yerlesir - her paftanin kendi
        # merkezine gore simetrik padding YAPILMAZ (bu, farkli "merkezli"
        # paftalar - ornegin kat plani vs gorunus - arasinda dusey kaymaya
        # yol acardi). Sadece guvenlik icin, bu paftanin icerigi kurulumda
        # bildirilenden buyukse (olmamasi gerekir) araligi genislet.
        # padding/frame_gap normalde sinif genelindedir; KAPAK PAFTASI gibi
        # ozel paftalar bunlari override edebilir (orada pafta dis cercevesi
        # kapak blogunun dis hattiyla cakistigi icin padding 0'dir).
        pad = self.padding if padding is None else padding
        gap = self.frame_gap if frame_gap is None else frame_gap
        pads = pad + gap
        outer_y0 = min(self.frame_y0, y_bottom - pads)
        outer_y1 = max(self.frame_y1, y_top + pads)

        inner_x0, inner_x1 = dx - pad, dx + width + pad
        outer_x0, outer_x1 = inner_x0 - gap, inner_x1 + gap
        inner_y0, inner_y1 = outer_y0 + gap, outer_y1 - gap

        if content_entities is not None:
            verify_within_frame(content_entities, outer_x0, outer_y0, outer_x1, outer_y1, label)

        self._draw_double_frame(msp, outer_x0, outer_y0, outer_x1, outer_y1, inner_x0, inner_y0, inner_x1, inner_y1)

        # KAPAK PAFTASI ozel bir paftadir: sag-alt kosesini Tip-A kapak blogu
        # kapladigi icin Tip-B serit anteti CIZILMEZ (title_box=False).
        if not title_box:
            return

        # Baslik kutusu: IC cizginin sag-alt kosesinde BITER (ona tasmaz/
        # ustune binmez), oradan sola/yukari dogru cizilir. Boyutlari
        # DIN/ISO Tip-B antet standardindan (olcege gore) turetilmistir.
        h = self.label_text_height
        box_h = self.box_height
        bx1, by0 = inner_x1, inner_y0
        bx0, by1 = bx1 - self.box_width, by0 + box_h
        box = msp.add_lwpolyline([(bx0, by0), (bx1, by0), (bx1, by1), (bx0, by1)], dxfattribs={"layer": "CERCEVE"})
        box.closed = True
        mid_y = by0 + box_h * 0.5
        msp.add_line((bx0, mid_y), (bx1, mid_y), dxfattribs={"layer": "CERCEVE"})

        pad = self.text_padding
        add_text(msp, f"OLCEK {self.scale}", (bx0 + pad, by1 - pad), h, "METIN", align=TextEntityAlignment.TOP_LEFT)
        add_text(msp, label, (bx0 + pad, mid_y - pad), h, "METIN", align=TextEntityAlignment.TOP_LEFT)

    def _draw_double_frame(self, msp, ox0: float, oy0: float, ox1: float, oy1: float,
                            ix0: float, iy0: float, ix1: float, iy1: float) -> None:
        """Pafta cercevesi: duvar rail mantigina benzer iki ayri dikdortgen
        (dis hat + ic hat; kose gonyesi gerekmez, zaten eksene paralel/kapali
        dikdortgenler)."""
        outer = msp.add_lwpolyline([(ox0, oy0), (ox1, oy0), (ox1, oy1), (ox0, oy1)], dxfattribs={"layer": "CERCEVE"})
        outer.closed = True
        inner = msp.add_lwpolyline([(ix0, iy0), (ix1, iy0), (ix1, iy1), (ix0, iy1)], dxfattribs={"layer": "CERCEVE"})
        inner.closed = True
