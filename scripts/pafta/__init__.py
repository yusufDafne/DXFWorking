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
# CONTENT_PADDING: paftanin IC cizgisinden itibaren gercek cizime (aks
# baloncugu dahil) birakilan bosluk. AxisGrid'in ulasabilecegi en uzak nokta
# (generate_dxf.py'deki AXIS_EXTENSION+AXIS_BUBBLE_RADIUS = 1200+450=1650)
# ILE baslik kutusunun olasi en buyuk yuksekligini (base_text_height*3.6)
# rahatça icine alacak kadar buyuk olmalidir (iki kaynagin - pafta modulu +
# aks modulu - sabitlerini bilerek secildi, bkz. scripts/pafta/CLAUDE.md).
CONTENT_PADDING = 1800.0
FRAME_GAP = 150.0                # cift cizgili cerceve (ic/dis hat) arasi mesafe
TITLE_BOX_WIDTH = 7000.0
DEFAULT_FONT = "txt"             # ezdxf 'Standard' text style'in varsayilan SHX fontu

# Kullanicinin ofis standardi: pafta yuksekligi bu degerlerden birine oturmali.
STANDARD_PAPER_HEIGHTS_CM = (45.0, 60.0, 90.0)


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
    """Kullanicinin ofis standardi: pafta yuksekligi 45/60/90cm standart
    boylarindan birine oturmalidir. Bu siniftaki `select(...)`, context.json'da
    ZATEN sabitlenmis olan `meta.scale` icin, projenin en yuksek paftasinin
    bu standartlardan hangisine sigdigini hesaplar/raporlar.

    NOT: Bu surum olcegi KENDILIGINDEN degistirmez (ornegin '1/50 favori,
    sigmazsa 1/100'e gec' kaskad mantigi, olcegin henuz SECILMEDIGI YENI bir
    proje icin dusunulmustur). Zaten sabit bir meta.scale olan bu proje icin
    planlayici SADECE o sabit olcekte hangi kagidin yeterli oldugunu bulur;
    STANDARD_PAPER_HEIGHTS_CM'nin en buyugu bile yetmiyorsa `fits=False`
    doner - bu durumda aks sikistirma veya olcek degisikligi KULLANICI
    KARARIYLA ele alinmalidir, planlayici kendiliginden mudahale etmez."""

    def __init__(self, scale: str):
        self.scale = scale
        self.scale_denominator = self._parse_scale(scale)

    @staticmethod
    def _parse_scale(scale: str) -> float:
        sep = ":" if ":" in scale else "/"
        parts = scale.split(sep)
        return float(parts[1])

    def required_paper_height_cm(self, max_sheet_height_mm: float) -> float:
        return max_sheet_height_mm / 10.0 / self.scale_denominator

    def select(self, max_sheet_height_mm: float) -> dict:
        required_cm = self.required_paper_height_cm(max_sheet_height_mm)
        for height_cm in STANDARD_PAPER_HEIGHTS_CM:
            if required_cm <= height_cm:
                return {
                    "fits": True, "paper_height_cm": height_cm,
                    "required_cm": required_cm, "scale": self.scale,
                }
        return {
            "fits": False, "paper_height_cm": None,
            "required_cm": required_cm, "scale": self.scale,
        }


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
                 frame_gap: float = FRAME_GAP, box_width: float = TITLE_BOX_WIDTH):
        self.scale = scale
        self.padding = padding
        self.frame_gap = frame_gap
        self.box_width = box_width
        candidates = [f"OLCEK {scale}"] + list(sheet_labels)
        self.label_text_height = fit_uniform_text_height(
            candidates, available_width=box_width - 300.0, max_height=base_text_height,
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
        # ustune binmez), oradan sola/yukari dogru cizilir.
        h = self.label_text_height
        box_h = h * 3.6
        bx1, by0 = inner_x1, inner_y0
        bx0, by1 = bx1 - self.box_width, by0 + box_h
        box = msp.add_lwpolyline([(bx0, by0), (bx1, by0), (bx1, by1), (bx0, by1)], dxfattribs={"layer": "CERCEVE"})
        box.closed = True
        mid_y = by0 + box_h * 0.5
        msp.add_line((bx0, mid_y), (bx1, mid_y), dxfattribs={"layer": "CERCEVE"})

        add_text(msp, f"OLCEK {self.scale}", (bx0 + 150, by1 - 150), h, "METIN", align=TextEntityAlignment.TOP_LEFT)
        add_text(msp, label, (bx0 + 150, mid_y - 150), h, "METIN", align=TextEntityAlignment.TOP_LEFT)

    def _draw_double_frame(self, msp, ox0: float, oy0: float, ox1: float, oy1: float,
                            ix0: float, iy0: float, ix1: float, iy1: float) -> None:
        """Pafta cercevesi: duvar rail mantigina benzer iki ayri dikdortgen
        (dis hat + ic hat; kose gonyesi gerekmez, zaten eksene paralel/kapali
        dikdortgenler)."""
        outer = msp.add_lwpolyline([(ox0, oy0), (ox1, oy0), (ox1, oy1), (ox0, oy1)], dxfattribs={"layer": "CERCEVE"})
        outer.closed = True
        inner = msp.add_lwpolyline([(ix0, iy0), (ix1, iy0), (ix1, iy1), (ix0, iy1)], dxfattribs={"layer": "CERCEVE"})
        inner.closed = True
