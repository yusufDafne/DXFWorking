"""Kapı/pencere cetveli (opening schedule) modülü (DEV-012).

`DEV-012`nin "Fikir 1"i: `openings::OpeningSchedule` zaten deterministik
satırlar üretiyordu ama `generate_dxf.py` sonucu kullanmadan atıyordu (veri
HAZIRDI, çizim YOKTU). Bu modül o satırları proje çapında (tip, varyant,
genişlik) ile GRUPLAYIP gerçek bir mimari cetvel (MARKA/TİP/VARYANT/
GENİŞLİK/ADET) olarak çizer — 145 açıklığın HER BİRİNİ tek tek listelemek
yerine (gerçek kapı/pencere cetveli konvansiyonu budur).

"Fikir 2" (layer/sembol lejantı, `TitleBlockLegend`/`LayerSwatch`) henüz
UYGULANMADI — bkz. modül `CLAUDE.md` "Açık kararlar".
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from ezdxf.enums import TextEntityAlignment

try:
    from ..openings import Opening, OpeningSchedule
except ImportError:
    from openings import Opening, OpeningSchedule

LEGEND_FRAME_LAYER = "CERCEVE"
LEGEND_TEXT_LAYER = "METIN"

COLUMNS = ("MARKA", "TIP", "VARYANT", "GENISLIK (cm)", "YUKSEKLIK (cm)", "DENIZLIK (cm)", "ADET")
COLUMN_WEIGHTS = (0.14, 0.18, 0.20, 0.14, 0.14, 0.12, 0.08)   # toplam 1.00 (DEV-072: yukseklik + denizlik sutunlari)
NO_HEIGHT_TEXT = "-"              # kapi/asansor/gecit: yukseklik cetvelde yok

# Modelspace VARSAYILANLARI: modul tek basina/selftest icinde kullanildiginda
# gecerlidir. Gercek uretimde `generate_dxf.py`, kapak blogunun KENDI
# olcek-turevi `mm()` fonksiyonuyla hesapladigi degerleri verir - boylece
# cetvel metni, kapak blogunun metniyle AYNI yazi yogunluguna sahip olur
# (bu modul bunun icin `pafta`yi import ETMEZ; degerler disaridan gelir).
DEFAULT_TITLE_HEIGHT = 300.0
DEFAULT_HEADER_HEIGHT = 220.0
DEFAULT_TEXT_HEIGHT = 180.0
DEFAULT_ROW_HEIGHT = 400.0
DEFAULT_TITLE_ROW_HEIGHT = 500.0

_TYPE_LABELS = {"door": "KAPI", "window": "PENCERE", "elevator_door": "ASANSOR KAPISI", "passage": "DUVAR ACIKLIGI"}
_TYPE_PREFIX = {"door": "K", "window": "P", "elevator_door": "A", "passage": "G"}
_VARIANT_MARK_SUFFIX = {"single": "", "double": "-D", "sliding": "-S", "folding": "-F",
                        "sliding_double": "-SD"}
_VARIANT_LABELS = {
    "single": "TEK KANAT", "double": "CIFT KANAT",
    "sliding": "SURME", "folding": "KATLANIR", "sliding_double": "CIFT SURME",
}


@dataclass(frozen=True)
class ScheduleRow:
    """Bir cetvel satırı: proje çapında AYNI (tip, varyant, genişlik) olan
    tüm açıklıkların ÖZETİdir - tek bir kapı/pencere INSTANCE'ı değil."""

    mark: str
    type_label: str
    variant_label: str
    width_cm: int
    count: int
    height_text: str = NO_HEIGHT_TEXT      # DEV-072: pencere icin cm metni (varsayilan ya da verilen deger)
    sill_text: str = NO_HEIGHT_TEXT        # pencere: cm metni

    def values(self) -> tuple[str, ...]:
        """Cetvel hucre metinleri (COLUMNS sirasiyla) - DXF ve onizleme AYNI kaynaktan okur."""
        return (self.mark, self.type_label, self.variant_label, str(self.width_cm), self.height_text, self.sill_text,
                str(self.count))


class OpeningLegend:
    """`OpeningSchedule` satırlarını proje çapında GRUPLAYIP özet bir
    cetvele dönüştürür. Sıralama deterministiktir (tip, varyant, genişlik)."""

    @staticmethod
    def rows(floors: list[dict]) -> list[ScheduleRow]:
        gathered: list[tuple[dict, dict]] = []     # (cetvel satiri, ham veri) - yukseklik/denizlik ham veriden cozulur
        for floor in floors:
            for data in floor.get("openings", []):
                row = OpeningSchedule.from_openings([Opening.from_context(data)])[0]
                gathered.append((row, data))

        counts: Counter = Counter()
        for row, data in gathered:
            counts[(row["type"], row["variant"], row["width"]) + _height_key(data)] += 1

        base = []
        for key, count in sorted(counts.items()):
            type_, variant, width, cls, h_text, s_text = key
            width_cm = round(width / 10.0)
            # `variant` SADECE kapida anlamlidir (bkz. openings/style.py -
            # pencere HER ZAMAN draw_window ile cizilir, varyanti yok sayar).
            # Pencere satirinda "TEK KANAT" yazmak var olmayan bir kanat
            # ayrimini uydururdu; bu yuzden pencerede varyant sutunu "-"dir.
            is_door = type_ in ("door", "elevator_door")
            mark_suffix = _VARIANT_MARK_SUFFIX.get(variant, "") if is_door else ""
            prefix = _TYPE_PREFIX.get(type_, "?") + ("B" if cls == "tall" else "")      # boy pencere: PB120
            variant_label = _VARIANT_LABELS.get(variant, variant.upper()) if is_door else "-"
            base.append([f"{prefix}{width_cm:03d}{mark_suffix}", _TYPE_LABELS.get(type_, type_.upper()), variant_label,
                         width_cm, count, h_text, s_text])
        # marka benzersizligi: ayni marka birden cok satirda ise (ayni genislik, farkli yukseklik/denizlik) yukseklik/denizlik eklenir
        seen = Counter(r[0] for r in base)
        result = []
        for mark, tl, vl, w, c, h, sl in base:
            if seen[mark] > 1:
                mark = f"{mark}-{h}" + (f"-{sl}" if sl != NO_HEIGHT_TEXT else "")
            result.append(ScheduleRow(mark=mark, type_label=tl, variant_label=vl, width_cm=w, count=c, height_text=h, sill_text=sl))
        marks = [r.mark for r in result]
        if len(set(marks)) != len(marks):      # son savunma: sessizce ayni markayi iki satirda birakma
            raise ValueError(f"Cetvel markalari benzersiz degil: {sorted(m for m in set(marks) if marks.count(m) > 1)}")
        return result


def _cm_text(mm: float) -> str:
    cm = mm / 10.0
    return str(int(round(cm))) if abs(cm - round(cm)) < 1e-9 else f"{cm:.1f}"


def _height_key(data: dict) -> tuple[str, str, str]:
    """(pencere sinifi, yukseklik metni, denizlik metni). Pencere disi: ('', '-', '-'). Degerler `openings.heights`tan cozulur."""
    if data.get("type") != "window":
        return ("", NO_HEIGHT_TEXT, NO_HEIGHT_TEXT)
    try:
        from ..openings.heights import resolve_window_heights
    except ImportError:
        from openings.heights import resolve_window_heights
    r = resolve_window_heights(data)
    return (r.window_class, _cm_text(r.height), _cm_text(r.sill))


def _center_text(msp, text: str, cx: float, cy: float, height: float):
    entity = msp.add_text(text, dxfattribs={"layer": LEGEND_TEXT_LAYER, "height": height})
    entity.set_placement((cx, cy), align=TextEntityAlignment.MIDDLE_CENTER)
    return entity


class LegendRenderer:
    """`OpeningLegend.rows(...)`u başlık-birleşimli bir çizgi+metin
    tablosu olarak çizer (mahal etiketinden ayrı, çünkü bu bir ATTRIB
    kadar sık tekrarlanmaz - proje çapında TEK cetvel çizilir)."""

    @staticmethod
    def draw(msp, rows: list[ScheduleRow], x0: float, y_top: float, width: float,
              row_height: float = DEFAULT_ROW_HEIGHT,
              title_row_height: float = DEFAULT_TITLE_ROW_HEIGHT,
              title_height: float = DEFAULT_TITLE_HEIGHT,
              header_height: float = DEFAULT_HEADER_HEIGHT,
              text_height: float = DEFAULT_TEXT_HEIGHT,
              title: str = "KAPI / PENCERE CETVELI") -> float:
        """(x0, y_top) tablonun SOL-ÜST köşesidir; tablo AŞAĞIYA büyür.
        Döner deger: tablonun ALT kenarının Y konumu."""
        n_rows = 1 + len(rows)  # 1 baslik (header) satiri + veri satirlari
        row_ys = [y_top - title_row_height - i * row_height for i in range(n_rows + 1)]
        col_widths = [width * weight for weight in COLUMN_WEIGHTS]
        col_xs = [x0]
        for col_width in col_widths:
            col_xs.append(col_xs[-1] + col_width)

        _center_text(msp, title, x0 + width / 2.0,
                     (y_top + row_ys[0]) / 2.0, title_height)

        for label, cx0, cx1 in zip(COLUMNS, col_xs[:-1], col_xs[1:]):
            _center_text(msp, label, (cx0 + cx1) / 2.0,
                         (row_ys[0] + row_ys[1]) / 2.0, header_height)

        for row_index, row in enumerate(rows, start=1):
            values = row.values()
            y_center = (row_ys[row_index] + row_ys[row_index + 1]) / 2.0
            for value, cx0, cx1 in zip(values, col_xs[:-1], col_xs[1:]):
                _center_text(msp, value, (cx0 + cx1) / 2.0, y_center, text_height)

        bottom_y = row_ys[-1]
        for y in [y_top] + row_ys:
            msp.add_line((x0, y), (x0 + width, y), dxfattribs={"layer": LEGEND_FRAME_LAYER})
        msp.add_line((x0, y_top), (x0, bottom_y), dxfattribs={"layer": LEGEND_FRAME_LAYER})
        msp.add_line((x0 + width, y_top), (x0 + width, bottom_y), dxfattribs={"layer": LEGEND_FRAME_LAYER})
        for cx in col_xs[1:-1]:
            msp.add_line((cx, row_ys[0]), (cx, bottom_y), dxfattribs={"layer": LEGEND_FRAME_LAYER})

        return bottom_y


# Bu modulun CONTEXT SOZLESMESI surumu (DEV-020). KOD surumu DEGILDIR.
# Bkz. scripts/version.py
CONTRACT_VERSION = "1.1"   # DEV-072: openings[].height/sill_height/window_class cetvel sutunlari

__all__ = [
    "ScheduleRow", "OpeningLegend", "LegendRenderer", "COLUMNS", "COLUMN_WEIGHTS",
    "DEFAULT_ROW_HEIGHT", "DEFAULT_TITLE_ROW_HEIGHT", "DEFAULT_TITLE_HEIGHT",
    "DEFAULT_HEADER_HEIGHT", "DEFAULT_TEXT_HEIGHT",
    "LEGEND_FRAME_LAYER", "LEGEND_TEXT_LAYER",
]
