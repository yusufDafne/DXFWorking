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
DEFAULT_FONT = "txt"             # ezdxf 'Standard' text style'in varsayilan SHX fontu

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
              label: str, content_entities=None) -> None:
        # Bu paftanin kendi (y_bottom, y_top) icerigi, TUM projede paylasilan
        # mutlak frame_y0/frame_y1 araligina yerlesir - her paftanin kendi
        # merkezine gore simetrik padding YAPILMAZ (bu, farkli "merkezli"
        # paftalar - ornegin kat plani vs gorunus - arasinda dusey kaymaya
        # yol acardi). Sadece guvenlik icin, bu paftanin icerigi kurulumda
        # bildirilenden buyukse (olmamasi gerekir) araligi genislet.
        pads = self.padding + self.frame_gap
        outer_y0 = min(self.frame_y0, y_bottom - pads)
        outer_y1 = max(self.frame_y1, y_top + pads)

        inner_x0, inner_x1 = dx - self.padding, dx + width + self.padding
        outer_x0, outer_x1 = inner_x0 - self.frame_gap, inner_x1 + self.frame_gap
        inner_y0, inner_y1 = outer_y0 + self.frame_gap, outer_y1 - self.frame_gap

        if content_entities is not None:
            verify_within_frame(content_entities, outer_x0, outer_y0, outer_x1, outer_y1, label)

        self._draw_double_frame(msp, outer_x0, outer_y0, outer_x1, outer_y1, inner_x0, inner_y0, inner_x1, inner_y1)

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
