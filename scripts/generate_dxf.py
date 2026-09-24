#!/usr/bin/env python3
"""context.json'dan output/plan.dxf uretir (cok katli bina, cok pafta).

Kullanim:
    python scripts/generate_dxf.py [context.json yolu] [cikti .dxf yolu]

ONEMLI: Bu script, context.json'da (veya kullanicidan gelen talepte) mevcut
OLMAYAN hicbir olcuyu/koordinati uydurmaz. Asagida gorulen sabitler (metin
yuksekligi, pafta cercevesi, elevasyon pencere/kapi cizim boyutlari gibi)
SADECE cizim/sunum kurallaridir; mimari tasarim verisi degildir.

Duvar cizim standardi (Turkiye standardi, bkz. CLAUDE.md):
Duvarlar "tek merkez cizgisi + width" yontemiyle DEGIL, kalinligina karsilik
gelen iki paralel kenar cizgisiyle (rail) - LINE olarak - cizilir. Birlesim
noktalarinda (kose / T-kesisimi) bu kenar cizgileri komsu duvarlarin
kenarlariyla kesistirilip (gonye/miter) uzatilir/kisaltilir. Bu mantik
Wall/WallNetwork siniflarinda kapsullenmistir.

Pafta duzeni: context.json'daki "floors" listesi soldan saga, ardindan
"elevations" listesi soldan saga, DIS CIZGILERINDEN BITISIK olarak dizilir
(aralarinda ekstra bosluk yoktur). Her pafta cift-cizgili bir cerceve
(Sheet._draw_double_frame) ve sag-alt kosede iki satirlik standart baslik
kutusu (ust: olcek, alt: pafta adi) alir. Tum paftalar AYNI mutlak dis-
cerceve Y-araligini paylasir (bkz. scripts/pafta), genislik ise dinamiktir.

Aks (grid) sistemi: AxisGrid sinifi, context.json'daki "grid" alanindaki
sabit aks izgarasini (tum kat paftalarinda ayni konumda) kesikli çizgi +
uc baloncuklariyla cizer ve on/yan cephelere uygun aile ile izdusurur.
AKS katmani RGB(67,77,88) sabit renktedir ve HER paftada digerlerinden once
(en altta) cizilir.

Bu script calistirilmadan once mutlaka scripts/validate.py BASARILI donmus
olmalidir. output/plan.dxf elle duzenlenmez; her degisiklik icin bu script
yeniden calistirilir.
"""
from __future__ import annotations

import json
import math
import subprocess
import sys
from pathlib import Path

try:
    import ezdxf
    from ezdxf.enums import TextEntityAlignment
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "ezdxf"])
    import ezdxf
    from ezdxf.enums import TextEntityAlignment

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pafta import (  # noqa: E402  (once sys.path ayarlanmali)
    CONTENT_PADDING,
    CoverBlock,
    FRAME_GAP,
    PaftaOverflowError,
    PaperSizePlanner,
    ScaleBar,
    Sheet,
    fit_text_height,
    fit_uniform_text_height,
    parse_scale_denominator,
    to_modelspace,
)
from northarrow import NorthArrow  # noqa: E402
from axis import (  # noqa: E402
    AxisCoverageReport,
    AxisDrawingStandard,
    AxisGrid,
    ensure_axis_layer,
)
from dimensions import DimensionSettings, FloorDimensionPlanner  # noqa: E402
from walls import WallNetwork, draw_wall_network  # noqa: E402
from walls.geometry import vec_add, vec_len, vec_norm, vec_scale, vec_sub  # noqa: E402
from rooms import RoomLabeler  # noqa: E402
from typography import ROLE_ROOM_LABEL, TextStyles  # noqa: E402
from furniture import (  # noqa: E402
    FurnitureBlocks,
    FurnitureCatalog,
    FurnitureItem,
    FurnitureRenderer,
)
from columns import (  # noqa: E402
    ColumnGrid,
    ColumnHatchStyle,
    ColumnLabelStyle,
    ColumnSectionCatalog,
    ensure_column_layers,
)
from openings import Opening, OpeningSchedule  # noqa: E402
from elevations import elevation_vertical_extent, ElevationSheet  # noqa: E402
from legend import OpeningLegend, LegendRenderer  # noqa: E402
from sections import (  # noqa: E402
    SectionSheet,
    draw_cut_marker_on_floor,
    resolve_sections,
    section_vertical_extent,
)
from version import (  # noqa: E402
    SCHEMA_VERSION,
    format_timestamp,
    generation_timestamp,
    provenance,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONTEXT_PATH = PROJECT_ROOT / "context.json"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "output" / "plan.dxf"

# --- Cizim/sunum sabitleri (tasarim verisi degil) ---
DEFAULT_LAYER_COLOR = 7
# Cephe (elevation) cizim sabitleri artik scripts/elevations modulunde
# (DEV-011, rev-14) - bu script sadece cagirir, kendi kopyasini tutmaz.

# Pafta cercevesi/baslik/tasma-kontrolu/kagit-boyutu artik scripts/pafta
# modulunde (bkz. scripts/pafta/CLAUDE.md) - bu script sadece Sheet/
# CONTENT_PADDING'i yukarida import eder, kendi kopyasini tutmaz.


def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def cleanup_fallback_files(output_path: Path) -> None:
    pattern = f"{output_path.stem}_*{output_path.suffix}"
    for alt in output_path.parent.glob(pattern):
        try:
            alt.unlink()
        except OSError:
            pass


def save_with_fallback(save_fn, output_path: Path, max_attempts: int = 50) -> Path:
    try:
        save_fn(output_path)
    except PermissionError as original_error:
        alt_path = output_path
        saved = False
        for n in range(1, max_attempts + 1):
            alt_path = output_path.with_name(f"{output_path.stem}_{n}{output_path.suffix}")
            try:
                save_fn(alt_path)
                saved = True
                break
            except PermissionError:
                continue
        if not saved:
            raise original_error
        print(
            f"UYARI: '{output_path.name}' su anda baska bir programda acik oldugu icin "
            f"uzerine yazilamadi. Bunun yerine '{alt_path.name}' olarak kaydedildi. "
            f"'{output_path.name}' dosyasini kapatip bir sonraki calistirmada bu yedek "
            f"dosya otomatik olarak temizlenecek."
        )
        return alt_path

    cleanup_fallback_files(output_path)
    return output_path


def text_height_for_units(units: str) -> float:
    return 350.0 if units == "mm" else 0.35


def room_label_height_for_units(units: str) -> float:
    # Oda etiketleri kucuk odalara (WC, mutfak vb.) da sigmali - genel metinden kucuk.
    return 200.0 if units == "mm" else 0.2


def setup_layers(doc, layers: list[dict]) -> None:
    for layer in layers:
        name = layer["name"]
        if name in doc.layers:
            continue
        attribs = {}
        if "color" in layer:
            attribs["color"] = layer["color"]
        if "linetype" in layer:
            attribs["linetype"] = layer["linetype"]
        doc.layers.add(name=name, dxfattribs=attribs or {"color": DEFAULT_LAYER_COLOR})


def add_text(msp, content: str, position, height: float, layer: str, align=TextEntityAlignment.LEFT):
    text = msp.add_text(content, dxfattribs={"layer": layer, "height": height})
    text.set_placement(position, align=align)
    return text


def draw_labels(msp, labels: list[dict], default_height: float) -> None:
    for label in labels:
        height = label.get("height", default_height)
        layer = label.get("layer", "METIN")
        text = msp.add_text(label["text"], dxfattribs={"layer": layer, "height": height})
        text.dxf.insert = tuple(label["position"])


def draw_cover_sheet(msp, context: dict, dx: float, sheet: Sheet,
                     generated_at: str = "") -> float:
    """Kapak paftasi (OZEL pafta) - paftanin DIS cercevesinin sag kenarini
    (mutlak X) dondurur.

    Kurallar (bkz. kok CLAUDE.md 'Kapak paftasi'):
    - Kapak blogu kagit uzerinde tam A4'tur; modelspace olcusu projenin
      OLCEGINE gore turetilir (1:50 -> 10500x14850mm), boylece cikti HANGI
      olcekte alinirsa alinsin kagitta 210x297mm olur.
    - Paftanin DIS CERCEVE GENISLIGI kapak genisligine ESITTIR: pafta dis
      hatti, kapak blogunun dis hattiyla cakisir. Bu yuzden bu paftada
      CONTENT_PADDING uygulanmaz (padding=0) ve cerceve boslugu kapagin
      kendi esit offseti (`block.frame_gap`) olur - boylece basili pafta
      tam A4 genisliginde olur ve duzgun katlanir (DIN 824).
    - Kapak, paftanin ALTINA oturur; ustte kalan bolum bos birakilir.
    - Bu paftada Tip-B serit anteti CIZILMEZ - kapagin kendisi o islevi gorur.
    - Sayfa eteginde bir URETIM DAMGASI bulunur (kullanici talebi): ciktinin
      uretildigi tarih-saat ve uretildigi sistem sozlesme surumu. Bu, bilgi
      satirlarindaki `TARIH` ile AYNI SEY DEGILDIR - o proje/onay tarihidir,
      context.json'dan gelir ve uydurulmaz; damga ise uretimin kaydidir.
    """
    content_start = len(msp)
    meta = context["meta"]
    cover_meta = meta.get("cover", {})
    block = CoverBlock(meta.get("scale", "1:100"))
    gap = block.frame_gap

    # dx = paftanin IC cizgisinin sol kenari (padding=0 oldugu icin icerik
    # origini). Dis cerceve bunun `gap` kadar disindan gecer ve kapak blogu
    # tam o dis hattan baslar.
    sheet_width = block.width - 2 * gap
    block_x0 = dx - gap
    block_y0 = sheet.frame_y0

    info_rows = [
        ("PROJE TIPI", meta.get("project_type", "")),
        ("OLCEK", meta.get("scale", "")),
        ("MIMAR", cover_meta.get("architect_name", "")),
        ("TARIH", cover_meta.get("date", "")),
    ]
    block.draw(
        msp, block_x0, block_y0,
        title=meta.get("project_name", "MIMARI PROJE"),
        info_rows=info_rows,
        signature_labels=cover_meta.get("signature_fields", []),
        outer_frame=False,   # dis/ic hat paftanin kendi cercevesinden gelir
        footer_left=f"URETIM: {generated_at}" if generated_at else "",
        footer_right=f"SISTEM: {SCHEMA_VERSION}",
    )

    # Kapak blogunun USTUNDE kalan bos alana kapi/pencere cetveli (DEV-012).
    # Kapak paftasi digerlerinden daha kisa oldugu icin (A4 orantisi) bu alan
    # HER ZAMAN bosta kalirdi; kok CLAUDE.md'nin "kapak paftanin ALTINA
    # oturur, ustte kalan bolum BOS birakilir" notuyla tutarlidir.
    legend_rows = OpeningLegend.rows(context["floors"])
    if legend_rows:
        margin = gap
        LegendRenderer.draw(
            msp, legend_rows,
            block_x0 + margin, sheet.frame_y1 - gap - margin,
            block.width - 2 * margin,
            row_height=block.mm(7.0), title_row_height=block.mm(9.0),
            title_height=block.mm(4.0), header_height=block.mm(2.8),
            text_height=block.mm(2.6),
        )

    # Bu pafta, TUM paftalarla paylasilan mutlak Y araligini oldugu gibi
    # kullanir (kendi araligini bildirip ortak cerceveyi bozmaz).
    content_entities = list(msp)[content_start:]
    sheet.draw(msp, dx, sheet_width, sheet.frame_y0 + gap, sheet.frame_y1 - gap,
               "KAPAK PAFTASI", content_entities=content_entities,
               title_box=False, padding=0.0, frame_gap=gap)
    return dx + sheet_width + gap


def shift_point(pt, dx: float):
    return [pt[0] + dx, pt[1]]


def translate_floor(floor: dict, dx: float) -> dict:
    if dx == 0:
        return floor
    new_floor = dict(floor)
    new_floor["rooms"] = [
        {**r, "polygon": [shift_point(p, dx) for p in r["polygon"]]} for r in floor["rooms"]
    ]
    new_floor["walls"] = [
        {**w, "start": shift_point(w["start"], dx), "end": shift_point(w["end"], dx)} for w in floor["walls"]
    ]
    new_floor["openings"] = list(floor["openings"])
    new_floor["labels"] = [
        {**l, "position": shift_point(l["position"], dx)} for l in floor["labels"]
    ]
    new_floor["counters"] = [
        {**c, "polygon": [shift_point(p, dx) for p in c["polygon"]]} for c in floor.get("counters", [])
    ]
    new_floor["markings"] = [
        {**m, "start": shift_point(m["start"], dx), "end": shift_point(m["end"], dx)} for m in floor.get("markings", [])
    ]
    new_floor["furniture"] = [
        {**f, "position": shift_point(f["position"], dx)} for f in floor.get("furniture", [])
    ]
    new_floor["columns"] = [
        {**c, "position": shift_point(c["position"], dx)} for c in floor.get("columns", [])
    ]
    return new_floor


def draw_floor_sheet(msp, floor: dict, dx: float, units: str, floor_width: float, floor_depth: float,
                      text_height: float, sheet: Sheet, axis_grid: AxisGrid,
                      text_styles: TextStyles, furniture_catalog: FurnitureCatalog,
                      column_catalog: ColumnSectionCatalog,
                      column_hatch_style: ColumnHatchStyle,
                      column_label_style: ColumnLabelStyle,
                      dimension_settings: DimensionSettings,
                      scale: str, scale_bar: ScaleBar, sheet_margin: float,
                      north_arrow: NorthArrow | None, north_angle: float | None,
                      sections: list) -> None:
    content_start = len(msp)

    # Aks izgarasi HER ZAMAN en once (en altta) cizilir (bkz. kullanici standardi).
    axis_grid.draw_on_floor(msp, dx, floor_width, floor_depth)

    tfloor = translate_floor(floor, dx)

    network = WallNetwork.from_context(tfloor["walls"], units)
    wall_by_id = {wall.id: wall for wall in network.walls}
    openings = [Opening.from_context(data) for data in tfloor["openings"]]
    for opening in openings:
        host = wall_by_id.get(opening.wall_id)
        if host is None:
            raise ValueError(f"Opening {opening.id} references missing wall {opening.wall_id}")
        if opening.position_from_start - opening.width / 2.0 < 0 or opening.position_from_start + opening.width / 2.0 > host.length:
            raise ValueError(f"Opening {opening.id} exceeds host wall {opening.wall_id}")
    opening_dicts = [opening.as_dict() for opening in openings]
    OpeningSchedule.from_openings(openings)
    draw_wall_network(msp, network, opening_dicts)

    # Mahal etiketi: 3 satir (ad / kat kodu-mahal no / alan). Kat kodu
    # context'teki floors[].code'dan gelir (B1/B2/ZK/K1../TR) - turetilmez.
    room_label_height = room_label_height_for_units(units)
    floor_code = floor.get("code", "")
    room_label_style = text_styles.style_of(ROLE_ROOM_LABEL)
    room_label_font = text_styles.font_of(ROLE_ROOM_LABEL)
    for room in tfloor["rooms"]:
        RoomLabeler.draw(msp, room, room_label_height, units,
                         floor_code=floor_code, style_name=room_label_style,
                         font=room_label_font)

    draw_labels(msp, tfloor["labels"], text_height)

    for counter in tfloor.get("counters", []):
        pl = msp.add_lwpolyline(counter["polygon"], dxfattribs={"layer": counter["layer"]})
        pl.closed = True

    for marking in tfloor.get("markings", []):
        msp.add_line(marking["start"], marking["end"], dxfattribs={"layer": marking["layer"]})

    # Kolonlar: tarali kesit (bkz. scripts/columns). Tefristen ONCE cizilir -
    # tasiyici eleman, tefrisin altinda kalmaz.
    if tfloor.get("columns"):
        grid = ColumnGrid.from_context(tfloor["columns"], column_catalog,
                                       column_hatch_style, column_label_style)
        grid.draw(msp)

    # Tefris: HER ZAMAN blok olarak (bkz. scripts/furniture).
    if tfloor.get("furniture"):
        items = [FurnitureItem.from_context(data) for data in tfloor["furniture"]]
        FurnitureRenderer.draw(msp, items, furniture_catalog)

    # Olcu zincirleri (DEV-017): aciklik / mahal / toplam kademeleri, yapinin
    # guney ve bati kenarinda kademelendirilmis olarak. Olcu SAYISI buradaki
    # geometriden TURETILIR (uydurulmaz); hangi kademenin cizilecegi
    # `meta.dimensions` ile gelen bir SUNUM kararidir.
    FloorDimensionPlanner(floor, dimension_settings).draw(msp, dx)

    # Kesit hatti isaretleri (DEV-021): kesitin KENDISI ayri bir paftadadir,
    # ama NEREDEN kesildigi HER kat paftasinda (aks izgarasiyla ayni konumda,
    # tum katlarda ortak) bir cizgi + ucgen isaretle gosterilir.
    for cut in sections:
        draw_cut_marker_on_floor(msp, cut, dx, floor_width, floor_depth, scale,
                                 label_height=scale_bar.label_height)

    # Kuzey oku + grafik olcek cubugu (DEV-025): pafta IC cizgisinden itibaren
    # birakilan bosluga (CONTENT_PADDING), aks baloncuklarindan uzak durmak
    # icin kat GENISLIGININ ORTASINA (aks konumlari genelde kenar/uctedir,
    # bkz. scripts/northarrow/CLAUDE.md 'Yerlesim') yerlestirilir.
    center_x = dx + floor_width / 2.0
    bar_x0 = center_x - scale_bar.total_length / 2.0
    bar_y0 = floor_depth + sheet_margin
    scale_bar.draw(msp, bar_x0, bar_y0)
    if north_arrow is not None:
        arrow_center = (center_x, bar_y0 + scale_bar.total_height + sheet_margin + north_arrow.radius)
        north_arrow.draw(msp, arrow_center, north_angle)

    content_entities = list(msp)[content_start:]
    sheet.draw(msp, dx, floor_width, 0.0, floor_depth, floor["label"], content_entities=content_entities)


def generate(context_path: Path = DEFAULT_CONTEXT_PATH, output_path: Path = DEFAULT_OUTPUT_PATH) -> Path:
    context = load_json(context_path)
    units = context["meta"]["units"]
    floor_width = context["meta"]["floor_width"]
    floor_depth = context["meta"]["floor_depth"]

    doc = ezdxf.new(dxfversion="R2010")
    doc.header["$INSUNITS"] = ezdxf.units.MM if units == "mm" else ezdxf.units.M
    # Proje fontu (Arial Narrow) 'Standard' text style'ina yazilir; boylece
    # stil verilmeyen TUM metinler - antet, aks, cephe etiketi, olcu metni -
    # otomatik olarak proje fontunu kullanir (bkz. scripts/typography).
    # Herhangi bir metin cizilmeden ONCE calismalidir.
    text_styles = TextStyles.from_context(context["meta"])
    text_styles.ensure(doc)
    ensure_axis_layer(doc)
    setup_layers(doc, context["layers"])
    msp = doc.modelspace()

    floors = context["floors"]
    elevations = context["elevations"]
    text_height = text_height_for_units(units)

    # Tefris ve kolon altyapisi. Tefris blok TANIMLARI, kullanilan tipler
    # icin bir kere olusturulur; her yerlesim bir INSERT'tir.
    furniture_catalog = FurnitureCatalog()
    used_furniture = {item["type"] for floor in floors for item in floor.get("furniture", [])}
    if used_furniture:
        FurnitureBlocks.ensure(doc, furniture_catalog, used_furniture)
    column_catalog = ColumnSectionCatalog()
    column_hatch_style = ColumnHatchStyle.from_context(context["meta"].get("column_hatch"))
    column_label_style = ColumnLabelStyle.from_context(context["meta"].get("column_label"))
    if any(floor.get("columns") for floor in floors):
        ensure_column_layers(doc, column_hatch_style, column_label_style)

    scale = context["meta"].get("scale", "1:100")
    # Kapak paftasinda antet kutusu olmadigi icin adi bu listeye girmez.
    all_labels = [f["label"] for f in floors] + [e["label"] for e in elevations]

    # Tum paftalarin (kat plani + gorunus) AYNI MUTLAK dis-cerceve Y-araligini
    # paylasmasi (ve boylece birbirine gore DUSEY KAYMAMASI) icin, her
    # paftanin kendi HAM (y_bottom, y_top) araligi toplanir; Sheet bunlarin
    # en genisini kapsayan TEK bir mutlak aralik hesaplar (bkz.
    # scripts/pafta/CLAUDE.md - genislik ise her pafta icin serbesttir).
    # Kapak paftasi buraya KENDI araligini bildirmez: kapak blogu ortak
    # aralik hesaplandiktan SONRA paftanin sag-altina hizalanir (konumu
    # frame_y0'a, yani bu hesabin sonucuna baglidir). Blok ortak aralaga
    # sigmazsa Sheet.draw icindeki verify_within_frame hata firlatir.
    # Kesitler (DEV-021): context['sections'] HIC verilmezse sistem X ve Y
    # ekseninden BIRER varsayilan kesit uretir (kullanici karari, bkz.
    # scripts/sections/CLAUDE.md); bos dizi verilirse kesit HIC cizilmez.
    sections = resolve_sections(context)
    elevation_lookup = {e["id"]: e for e in elevations}
    section_labels = [f"{cut.label} KESITI" for cut in sections]
    all_labels += section_labels

    content_ranges = [(0.0, floor_depth) for _ in floors]
    for elevation in elevations:
        content_ranges.append(elevation_vertical_extent(elevation))
    for cut in sections:
        content_ranges.append(section_vertical_extent(cut, elevation_lookup))

    sheet = Sheet(scale, text_height, all_labels, content_ranges)

    # Kuzey oku + grafik olcek cubugu (DEV-025): olcek cubugu HER ZAMAN
    # cizilir (sadece meta.scale'den turetilir, veri uydurulmaz); kuzey oku
    # SADECE meta.north_angle bildirilmisse cizilir (yon uydurulmaz).
    scale_bar = ScaleBar(scale, units)
    sheet_margin = to_modelspace(10.0, parse_scale_denominator(scale))
    north_angle = context["meta"].get("north_angle")
    north_arrow = NorthArrow(scale) if north_angle is not None else None

    grid = context["grid"]
    # Olcu yigini ile aks baloncuklari AYNI kenari paylasir: baloncuk,
    # zincirlerin DISINDA kalmalidir. Gereken uzamayi yalnizca `dimensions`
    # bilir (yigin derinligi onun kararidir), bu yuzden aks standardi ona
    # sorularak kurulur - iki modul birbirini import etmez.
    dimension_settings = DimensionSettings.from_context(context)
    axis_defaults = AxisDrawingStandard()
    axis_standard = AxisDrawingStandard(
        extension=dimension_settings.required_axis_extension(
            axis_defaults.extension, axis_defaults.bubble_radius),
        dimension_offset=dimension_settings.axis_dimension_offset(
            axis_defaults.dimension_offset),
    )
    axis_grid = AxisGrid(grid["vertical_axes"], grid["horizontal_axes"], text_height,
                         standard=axis_standard)

    # Cephe kat etiketleri (+ zemin notu), pafta IC cizgisinden itibaren
    # birakilan bosluga (CONTENT_PADDING) sigacak, sifir-hizali degil
    # gercekten padding'li konumlandirilir (bkz. scripts/pafta/CLAUDE.md -
    # onceki surumde bu metinler pafta kenarina bitisikti / komsu paftaya
    # tasiyordu).
    elevation_level_labels = [lvl["label"] for e in elevations for lvl in e["levels"]] + ["+-0.00 ZEMIN"]
    elevation_label_height = fit_uniform_text_height(
        elevation_level_labels, available_width=CONTENT_PADDING - 600.0, max_height=text_height,
    )

    # Uretim ani TEK bir yerde uretilir: kapaktaki damga ile
    # provenance kaydinin ayni saniyeyi gostermesi gerekir.
    moment = generation_timestamp()

    planner = PaperSizePlanner(scale)
    paper_plan = planner.select(sheet.outer_height)
    if paper_plan["fits"]:
        print(
            f"Pafta boyutu: olcek {scale}, en yuksek pafta {paper_plan['required_cm']:.1f} cm "
            f"gerektiriyor -> {paper_plan['paper_height_cm']:.0f}'lik rulo kagida sigiyor "
            f"(net kullanilabilir {paper_plan['net_height_cm']:.1f} cm)."
        )
    else:
        print(
            f"UYARI: olcek {scale} icin en yuksek pafta {paper_plan['required_cm']:.1f} cm "
            f"gerektiriyor - en buyuk standart rulo (90'lik, net 88 cm) bile yetmiyor. "
            f"MEVZUAT GEREGI OLCEK KUCULTULEMEZ - tek gecerli cozum pafta bolme + keyplan "
            f"eklemektir (henuz uygulanmadi, bkz. scripts/pafta/CLAUDE.md)."
        )

    footprint_m2 = (floor_width * floor_depth) / 1_000_000.0
    project_type = context["meta"].get("project_type")
    violation = planner.classify_violation(project_type, footprint_m2)
    if violation:
        print(f"UYARI (olcek mevzuati): {violation}")

    # Paftalar DIS cizgilerinden BITISIKTIR (aralarinda ekstra bosluk yok):
    # bir paftanin dis cercevesinin sag kenari bir sonrakinin sol kenarina
    # tam oturur. Her paftanin kendi genisligine, dis cerceveye ulasmak icin
    # iki yaninda (padding+frame_gap) kadar pay eklenir.
    frame_half_width = CONTENT_PADDING + FRAME_GAP

    cursor = 0.0
    # Kapak paftasinin dis cercevesi kapak genisligi kadardir (padding yok),
    # bu yuzden ilerleme diger paftalardan farkli hesaplanir: bir sonraki
    # paftanin dis hatti, kapak paftasinin dis hattina TAM oturur.
    cover_outer_x1 = draw_cover_sheet(msp, context, cursor, sheet,
                                      generated_at=format_timestamp(moment))
    cursor = cover_outer_x1 + frame_half_width

    for floor in floors:
        # Kolon rasteri aks kapsama raporu (DEV-015 Fikir 1): SALT OKUNUR.
        # Sistem context'e aks YAZMAZ; yalnizca aks'siz kalan kolon hizalarini
        # bildirir ve karari kullaniciya birakir.
        coverage = AxisCoverageReport.from_columns(
            floor.get("columns", []), grid["vertical_axes"],
            grid["horizontal_axes"], floor.get("code", ""))
        for line in coverage.lines():
            print(f"UYARI (aks kapsami): {line}")

        draw_floor_sheet(msp, floor, cursor, units, floor_width, floor_depth, text_height,
                         sheet, axis_grid, text_styles, furniture_catalog,
                         column_catalog, column_hatch_style, column_label_style,
                         dimension_settings, scale, scale_bar, sheet_margin,
                         north_arrow, north_angle, sections)
        cursor += floor_width + 2 * frame_half_width

    for elevation in elevations:
        content_start = len(msp)
        ElevationSheet.draw(msp, elevation, cursor, text_height, axis_grid, elevation_label_height)
        # Grafik olcek cubugu (DEV-025): gorunusler de OLCEKLI cizimdir,
        # bu yuzden kat paftalariyla AYNI standart burada da uygulanir.
        y_bottom, y_top = elevation_vertical_extent(elevation)
        scale_bar.draw(msp, cursor + elevation["width"] / 2.0 - scale_bar.total_length / 2.0,
                      y_top + sheet_margin)
        content_entities = list(msp)[content_start:]
        sheet.draw(msp, cursor, elevation["width"], y_bottom, y_top, elevation["label"], content_entities=content_entities)
        cursor += elevation["width"] + 2 * frame_half_width

    for cut in sections:
        content_start = len(msp)
        width = cut.width_for(floor_width, floor_depth)
        SectionSheet.draw(msp, cut, floors, elevation_lookup, cursor, width,
                          elevation_label_height, axis_grid)
        y_bottom, y_top = section_vertical_extent(cut, elevation_lookup)
        scale_bar.draw(msp, cursor + width / 2.0 - scale_bar.total_length / 2.0,
                      y_top + sheet_margin)
        content_entities = list(msp)[content_start:]
        sheet.draw(msp, cursor, width, y_bottom, y_top, f"{cut.label} KESITI", content_entities=content_entities)
        cursor += width + 2 * frame_half_width

    output_path.parent.mkdir(parents=True, exist_ok=True)
    written = save_with_fallback(lambda p: doc.saveas(p), output_path)

    # Provenance KAYDI (DEV-020): bloklamaz, yalnizca "bu cikti neyle
    # uretildi" sorusunu yanitlar. context.json'a YAZILMAZ - orasi proje
    # TASARIM verisidir ve her uretimde kirletilmemelidir.
    write_provenance(context, written, moment)
    return written


def write_provenance(context: dict, output_path: Path, moment) -> Path:
    """`output/provenance.json` yazar (DEV-020).

    Nihai DXF'in yanina konur: hangi schema surumu, hangi modul
    sozlesmeleri ve hangi commit ile uretildigi buradan okunur. Bir proje
    eski bir sistem surumuyle uretilip moduller degistiginde,
    'entegrasyon koptu mu, koptuysa neyden' sorusu bu kayitla yanitlanir.
    """
    record = provenance(context, output_path=output_path.name, moment=moment)
    target = output_path.parent / "provenance.json"
    payload = json.dumps(record, ensure_ascii=False, indent=2) + "\n"
    return save_with_fallback(
        lambda p: Path(p).write_text(payload, encoding="utf-8"), target)


def main() -> int:
    context_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CONTEXT_PATH
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_OUTPUT_PATH
    try:
        result = generate(context_path, output_path)
    except PaftaOverflowError as exc:
        print(f"DXF URETILEMEDI (pafta tasmasi): {exc}")
        return 1
    print(f"DXF uretildi: {result}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
