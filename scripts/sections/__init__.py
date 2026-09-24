"""Kesit (building section) modulu (DEV-021).

**Kapsam karari (kullanici):** bu yapida kesit hatti HICBIR ZAMAN egik veya
kademeli (jogged) alinmaz - kesit hatti HER ZAMAN aks ailelerinden birine
PARALELDIR (sabit X veya sabit Y). Bu, `elevations/`in `axis_source` alaniyla
AYNI ikili secimle ifade edilir: 'vertical' -> kesit hatti sabit Y'dedir
(kesit boyunca X degisir, numerik/dusey akslar kesitte gorunur, genislik =
floor_width). 'horizontal' -> kesit hatti sabit X'tedir (genislik =
floor_depth). Bu esdegerlik sayesinde kesit, `elevations/`deki `LevelStack`i
VE `axis`in `draw_on_elevation` izdusum mantigini DOGRUDAN yeniden kullanir -
ayri bir "kesit akslari" kavrami icat edilmez.

**Varsayilan kesit konumu (kullanici karari):** operator konum bildirmezse
kesit ASLA yapinin tam ortasindan alinmaz; ilgili kenarin 1/3 noktasindan
alinir (`DEFAULT_POSITION_FRACTION`). Operator hicbir `sections` alani
vermezse sistem otomatik olarak X ve Y ekseninden BIRER varsayilan kesit
uretir (`resolve_sections`) - bu FABRIKASYON degildir, kullanicinin acikca
verdigi bir SISTEM STANDARDIDIR (bkz. modul CLAUDE.md).

**Genisletme noktasi (kullanici talebi):** kat yukseklikleri bugun tam
desteklenir (LevelStack). Galeri bosluğu / merdivene denk gelen kirilma
gibi ozel durumlar HENUZ VERİ OLARAK yok, ama `SectionFeatureHook` Protocol'u
(bkz. asagida) TAM OLARAK bu genislemenin gireceği noktadir - `RailDrawing
Standard` (scripts/walls/standard.py) ile AYNI desen.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ezdxf.enums import TextEntityAlignment

try:
    from ..elevations import DIM_LAYER, LABEL_LAYER, Level, LevelStack
    from ..pafta import parse_scale_denominator, to_modelspace
except ImportError:  # dogrudan scripts/ uzerinden calistirildiginda
    from elevations import DIM_LAYER, LABEL_LAYER, Level, LevelStack
    from pafta import parse_scale_denominator, to_modelspace

SECTION_LAYER = "DUVARLAR"          # kesit icindeki kesilen duvar dolgusu - elevations ile AYNI konvansiyon (mevcut katman yeniden kullanilir)
CUT_LAYER = "KESIT"                 # PLANDAKI kesit hatti + ucgen isaretler - AKS'ten (gri) BILEREK farkli
CUT_LINETYPE = "KESIT_HATTI"
CUT_RGB = (200, 30, 30)             # kirmizimsi - kullanici: "farkli renkte ve desende cizgi"

DEFAULT_POSITION_FRACTION = 1.0 / 3.0

PRINTED_MARKER_EXTENSION_MM = 8.0   # kesit hattinin bina kenarindan disari tasan stub uzunlugu
PRINTED_MARKER_SIZE_MM = 5.0        # ucgen isaretin boyu
PRINTED_MARKER_LABEL_MM = 3.0

EPS = 1e-6


def ensure_section_cut_layer(doc) -> None:
    """`KESIT` katmani + `KESIT_HATTI` linetype'ini idempotent kurar.
    `axis`/`elevations` KENDI `DASHED` desenini ayni yontemle yukler; bu
    modul BASKA bir isim (`KESIT_HATTI`) ve BASKA bir renk kullanir cunku
    kullanici acikca "aks ile karistirilmasin, farkli renkte/desende olsun"
    istedi - `DASHED`i yeniden kullanmak bu ayrimi gizlerdi."""
    if CUT_LINETYPE not in doc.linetypes:
        doc.linetypes.add(
            CUT_LINETYPE,
            pattern=[600.0, 300.0, -150.0, 150.0, -150.0],
            description="Kesit (section cut) hatti - dash-dot-dash",
        )
    import ezdxf
    if CUT_LAYER in doc.layers:
        layer = doc.layers.get(CUT_LAYER)
    else:
        layer = doc.layers.add(CUT_LAYER)
    layer.dxf.linetype = CUT_LINETYPE
    layer.dxf.color = 1
    layer.dxf.true_color = ezdxf.colors.rgb2int(CUT_RGB)


@dataclass(frozen=True)
class SectionCutLine:
    id: str
    label: str
    axis_source: str
    position: float
    look_direction: str
    levels_from: str

    @property
    def letter(self) -> str:
        """Plan uzerindeki ucgen isaretlerde gosterilen TEK harf ('A-A' -> 'A')."""
        return self.label.partition("-")[0]

    def width_for(self, floor_width: float, floor_depth: float) -> float:
        return floor_width if self.axis_source == "vertical" else floor_depth


def default_label(index: int) -> str:
    """Sirali varsayilan etiket: 0->'A-A', 1->'B-B', ... (kullanici:
    'kesit cizgisi icin A-Z isimlendirilmesi yapilir')."""
    letter = chr(ord("A") + index)
    return f"{letter}-{letter}"


def default_position(axis_source: str, floor_width: float, floor_depth: float) -> float:
    """Operator konum BILDIRMEZSE kullanilan varsayilan: ilgili kenarin TAM
    ORTASI DEGIL, 1/3 noktasi (kullanici karari - bkz. modul docstring'i)."""
    span = floor_depth if axis_source == "vertical" else floor_width
    return span * DEFAULT_POSITION_FRACTION


def resolve_sections(context: dict) -> list[SectionCutLine]:
    """`context['sections']` HIC verilmezse (anahtar yok), kullanicinin
    acikca istedigi sekilde X ve Y ekseninden BIRER varsayilan kesit uretir.
    Bos dizi ([]) verilirse bu varsayilan DEVRE DISI kalir - operator
    ACIKCA "kesit yok" demis olur. Her elemanin eksik alanlari (`label`,
    `position`, `look_direction`, `levels_from`) burada, TEK yerde
    doldurulur - `validate.py` ve `generate_dxf.py` AYNI fonksiyonu cagirir,
    boylece varsayilan mantigi iki yerde ayrisamaz."""
    meta = context["meta"]
    floor_width = meta["floor_width"]
    floor_depth = meta["floor_depth"]
    elevations = context.get("elevations", [])
    default_levels_from = elevations[0]["id"] if elevations else None

    raw = context.get("sections")
    if raw is None:
        if default_levels_from is None:
            return []
        raw = [
            {"id": "kesit_x_varsayilan", "axis_source": "vertical"},
            {"id": "kesit_y_varsayilan", "axis_source": "horizontal"},
        ]

    result: list[SectionCutLine] = []
    for index, data in enumerate(raw):
        axis_source = data["axis_source"]
        label = data.get("label") or default_label(index)
        position = data.get("position")
        if position is None:
            position = default_position(axis_source, floor_width, floor_depth)
        look_direction = data.get("look_direction", "positive")
        levels_from = data.get("levels_from") or default_levels_from
        if levels_from is None:
            raise ValueError(
                f"Kesit '{data['id']}' icin levels_from belirlenemedi "
                f"(context['elevations'] bos, varsayilan istif kaynagi yok)."
            )
        result.append(SectionCutLine(
            id=data["id"], label=label, axis_source=axis_source, position=position,
            look_direction=look_direction, levels_from=levels_from,
        ))
    return result


def crossing_walls(walls: list[dict], axis_source: str, cut_position: float,
                    eps: float = EPS) -> list[dict]:
    """Bu KATIN duvarlarindan, kesit hattini KESENLERI bulur.

    Kesit hatti axis_source='vertical' ise sabit Y'dedir (X boyunca uzanir);
    onu kesen duvarlar DUSEY duvarlardir (start.x == end.x), Y-araligi
    cut_position'i icermelidir. axis_source='horizontal' ise simetriktir
    (sabit X, onu kesen duvarlar YATAY duvarlardir).

    **Bilinen sinirlama:** kesit hattina PARALEL duran (onunla ayni
    dogrultuda) duvarlar bu fonksiyon tarafindan ATLANIR - onlar kesitin
    "sirtinda" gorunur, basit bir dikdortgen dolgu olarak temsil edilemezler
    (bkz. modul CLAUDE.md). Bu yapida duvarlar eksene hizali (rectilinear)
    oldugu icin diyagonal duvar HIC beklenmez; oyle bir duvar da bu
    fonksiyonun her iki testinden gecemeyip sessizce ATLANIR."""
    result: list[dict] = []
    for wall in walls:
        sx, sy = wall["start"]
        ex, ey = wall["end"]
        if axis_source == "vertical":
            if abs(sx - ex) > eps:
                continue  # dusey degil (yatay veya diyagonal) - atlanir
            lo, hi = (sy, ey) if sy <= ey else (ey, sy)
            if lo - eps <= cut_position <= hi + eps:
                result.append({"wall_id": wall["id"], "at": sx,
                               "thickness": wall["thickness"], "kind": wall.get("kind")})
        else:
            if abs(sy - ey) > eps:
                continue  # yatay degil - atlanir
            lo, hi = (sx, ex) if sx <= ex else (ex, sx)
            if lo - eps <= cut_position <= hi + eps:
                result.append({"wall_id": wall["id"], "at": sy,
                               "thickness": wall["thickness"], "kind": wall.get("kind")})
    result.sort(key=lambda c: c["at"])
    return result


class SectionFeatureHook(Protocol):
    def draw_level(self, msp, floor: dict, level: Level, dx: float, y0: float,
                   y1: float, width: float) -> None: ...


class DefaultSectionFeatureHook:
    """Bugunku TEK davranis: her seviye ALTINDA (doseme ustu) tam genislikte
    duz bir sinir cizgisi. Galeri bosluğu (kat araliginin bir bolgede
    ATLANMASI) veya merdiven kirilma cizgisi gibi ozel durumlar, bu sinifi
    override eden YENI bir `SectionFeatureHook` yazarak eklenir - cekirdek
    `SectionSheet.draw` DEGISMEZ (bkz. modul CLAUDE.md 'Genisletme
    noktasi'). Bugun bu ozellestirmeyi tetikleyecek proje verisi YOKTUR;
    hic veri uydurmadan hazir tutulan bir dikis noktasidir."""

    def draw_level(self, msp, floor, level, dx, y0, y1, width) -> None:
        msp.add_line((dx, y0), (dx + width, y0), dxfattribs={"layer": DIM_LAYER})


class SectionSheet:
    """Bir kesidin tam cizimi: aks izdusumu + kat-kat kesilen duvar dolgusu +
    seviye sinirlari + etiketler + zemin cizgisi. `ElevationSheet.draw` ile
    AYNI cagri ruhundadir (bkz. scripts/elevations)."""

    @staticmethod
    def draw(msp, cut: SectionCutLine, floors: list[dict], elevation_lookup: dict[str, dict],
             dx: float, width: float, label_text_height: float, axis_grid,
             feature_hook: SectionFeatureHook | None = None) -> None:
        stack = LevelStack.from_context(elevation_lookup[cut.levels_from])
        placements = stack.placements()
        if len(floors) != len(placements):
            raise ValueError(
                f"Kesit '{cut.id}': floors[] uzunlugu ({len(floors)}) "
                f"'{cut.levels_from}'in seviye sayisiyla ({len(placements)}) "
                f"UYUSMUYOR - kat <-> seviye eslesmesi SIRAYA (asagidan yukariya) "
                f"gore yapilir ve bu ikisi ayni boyda olmalidir."
            )
        hook = feature_hook or DefaultSectionFeatureHook()
        y_bottom, y_top = stack.extent()
        stack_top = stack.stack_top()

        # Aks izgarasi HER ZAMAN en once (en altta) cizilir - elevations ile AYNI kural.
        axis_grid.draw_on_elevation(msp, dx, cut.axis_source, y_bottom, stack_top)

        for floor, (level, y0, y1) in zip(floors, placements):
            hook.draw_level(msp, floor, level, dx, y0, y1, width)
            for crossing in crossing_walls(floor["walls"], cut.axis_source, cut.position):
                half = crossing["thickness"] / 2.0
                local = crossing["at"]
                hatch = msp.add_hatch(dxfattribs={"layer": SECTION_LAYER})
                hatch.set_solid_fill()
                quad = [(dx + local - half, y0), (dx + local + half, y0),
                        (dx + local + half, y1), (dx + local - half, y1)]
                hatch.paths.add_polyline_path(quad, is_closed=True)

            label_entity = msp.add_text(level.label, dxfattribs={
                "layer": LABEL_LAYER, "height": label_text_height})
            label_entity.set_placement((dx - 300.0, (y0 + y1) / 2.0),
                                       align=TextEntityAlignment.MIDDLE_RIGHT)

        msp.add_line((dx, stack_top), (dx + width, stack_top), dxfattribs={"layer": DIM_LAYER})
        msp.add_line((dx - 1000, 0), (dx + width + 1000, 0), dxfattribs={"layer": DIM_LAYER})
        ground = msp.add_text("+-0.00 ZEMIN", dxfattribs={
            "layer": DIM_LAYER, "height": label_text_height})
        ground.set_placement((dx - 300.0, 150.0), align=TextEntityAlignment.MIDDLE_RIGHT)


def section_vertical_extent(cut: SectionCutLine, elevation_lookup: dict[str, dict]) -> tuple[float, float]:
    """Pafta Y-araligi hesaplarken kullanilir (`generate_dxf.py::generate`) -
    `elevation_vertical_extent` ile AYNI rol."""
    return LevelStack.from_context(elevation_lookup[cut.levels_from]).extent()


def _triangle(msp, base_center: tuple[float, float], point_dir: tuple[float, float],
             along_dir: tuple[float, float], size: float, layer: str):
    tip = (base_center[0] + point_dir[0] * size, base_center[1] + point_dir[1] * size)
    half = size * 0.4
    b1 = (base_center[0] + along_dir[0] * half, base_center[1] + along_dir[1] * half)
    b2 = (base_center[0] - along_dir[0] * half, base_center[1] - along_dir[1] * half)
    tri = msp.add_lwpolyline([tip, b1, b2], dxfattribs={"layer": layer})
    tri.closed = True


def draw_cut_marker_on_floor(msp, cut: SectionCutLine, dx: float, floor_width: float,
                              floor_depth: float, scale: str) -> None:
    """HER kat paftasinda (aks izgarasiyla AYNI konumda, tum katlarda ortak)
    kesit hattini + bakis yonu ucgenlerini + kesit harfini cizer (kullanici
    talebi: 'kesit çizgilerinin uçlarına ok işaretler (üçgenler) eklenir ve
    üçgenlerin sırtına da kesitin harfi yazılır'). Ucgenler kesit hattinin
    bina kenarindan disari tasan kisa bir 'stub'unun UCUNDA durur ve bina
    icine dogru (bakis yonu) isaret eder; harf, ucgenin SIRTINA (uctan
    UZAK, disari bakan) yazilir. Etiket yuksekligi bu modulun KENDI olcek
    turevidir (`PRINTED_MARKER_LABEL_MM`) - baska bir modulden (ScaleBar
    vb.) ODUNC ALINMAZ, boylece bu fonksiyon tek basina cagrilabilir."""
    scale_denominator = parse_scale_denominator(scale)
    ext = to_modelspace(PRINTED_MARKER_EXTENSION_MM, scale_denominator)
    size = to_modelspace(PRINTED_MARKER_SIZE_MM, scale_denominator)
    label_height = to_modelspace(PRINTED_MARKER_LABEL_MM, scale_denominator)
    ensure_section_cut_layer(msp.doc)

    if cut.axis_source == "vertical":
        along = (1.0, 0.0)
        into_building = (0.0, 1.0) if cut.look_direction == "positive" else (0.0, -1.0)
        p_start = (dx - ext, cut.position)
        p_end = (dx + floor_width + ext, cut.position)
    else:
        along = (0.0, 1.0)
        into_building = (1.0, 0.0) if cut.look_direction == "positive" else (-1.0, 0.0)
        p_start = (dx + cut.position, -ext)
        p_end = (dx + cut.position, floor_depth + ext)

    msp.add_line(p_start, p_end, dxfattribs={"layer": CUT_LAYER, "linetype": CUT_LINETYPE})

    label_gap = size + label_height
    for stub_end in (p_start, p_end):
        _triangle(msp, stub_end, into_building, along, size, CUT_LAYER)
        back = (stub_end[0] - into_building[0] * label_gap,
                stub_end[1] - into_building[1] * label_gap)
        text = msp.add_text(cut.letter, dxfattribs={"layer": CUT_LAYER, "height": label_height})
        text.set_placement(back, align=TextEntityAlignment.MIDDLE_CENTER)


# Bu modulun CONTEXT SOZLESMESI surumu (DEV-020). KOD surumu DEGILDIR.
# Bkz. scripts/version.py
CONTRACT_VERSION = "1.0"

__all__ = [
    "SECTION_LAYER", "CUT_LAYER", "CUT_LINETYPE", "CUT_RGB",
    "DEFAULT_POSITION_FRACTION",
    "SectionCutLine", "SectionSheet", "SectionFeatureHook", "DefaultSectionFeatureHook",
    "resolve_sections", "default_label", "default_position",
    "crossing_walls", "section_vertical_extent",
    "draw_cut_marker_on_floor", "ensure_section_cut_layer",
]
