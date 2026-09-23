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
    Sheet,
    fit_text_height,
    fit_uniform_text_height,
)
from axis import AxisGrid, ensure_axis_layer  # noqa: E402
from walls import WallNetwork, draw_wall_network  # noqa: E402
from walls.geometry import vec_add, vec_len, vec_norm, vec_scale, vec_sub  # noqa: E402
from rooms import RoomLabeler  # noqa: E402
from typography import ROLE_ROOM_LABEL, TextStyles  # noqa: E402
from openings import Opening, OpeningSchedule  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONTEXT_PATH = PROJECT_ROOT / "context.json"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "output" / "plan.dxf"

# --- Cizim/sunum sabitleri (tasarim verisi degil) ---
DEFAULT_LAYER_COLOR = 7
DEFAULT_ELEVATION_WINDOW_SIZE = (1200.0, 1400.0)
ELEVATION_DOOR_SIZE = (1800.0, 2100.0)
ELEVATION_LABEL_OFFSET = 300.0   # icerik kenarindan itibaren bilerek birakilmis bosluk (sifir-hizali degil)

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


def draw_cover_sheet(msp, context: dict, dx: float, sheet: Sheet) -> float:
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
    return new_floor


def draw_floor_sheet(msp, floor: dict, dx: float, units: str, floor_width: float, floor_depth: float,
                      text_height: float, sheet: Sheet, axis_grid: AxisGrid,
                      text_styles: TextStyles) -> None:
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
    label_style = text_styles.style_of(ROLE_ROOM_LABEL)
    label_font = text_styles.font_of(ROLE_ROOM_LABEL)
    for room in tfloor["rooms"]:
        RoomLabeler.draw(msp, room, room_label_height, units,
                         floor_code=floor_code, style_name=label_style, font=label_font)

    draw_labels(msp, tfloor["labels"], text_height)

    for counter in tfloor.get("counters", []):
        pl = msp.add_lwpolyline(counter["polygon"], dxfattribs={"layer": counter["layer"]})
        pl.closed = True

    for marking in tfloor.get("markings", []):
        msp.add_line(marking["start"], marking["end"], dxfattribs={"layer": marking["layer"]})

    content_entities = list(msp)[content_start:]
    sheet.draw(msp, dx, floor_width, 0.0, floor_depth, floor["label"], content_entities=content_entities)


def elevation_vertical_extent(elevation: dict) -> tuple[float, float]:
    levels = elevation["levels"]
    total_below = sum(l["height"] for l in levels if l.get("below_ground"))
    total_above = sum(l["height"] for l in levels if not l.get("below_ground"))
    extra = 0.0
    for l in levels:
        if l.get("machine_room"):
            extra = max(extra, l["height"] * 0.8)
    return -total_below, total_above + extra


def draw_elevation(msp, elevation: dict, dx: float, text_height: float, axis_grid: AxisGrid,
                    label_text_height: float) -> None:
    width = elevation["width"]
    levels = elevation["levels"]

    total_below = sum(l["height"] for l in levels if l.get("below_ground"))
    cursor = -total_below
    computed = []
    for level in levels:
        y0 = cursor
        y1 = cursor + level["height"]
        computed.append((level, y0, y1))
        cursor = y1

    # Aks izgarasi HER ZAMAN en once (en altta) cizilir.
    axis_grid.draw_on_elevation(msp, dx, elevation.get("axis_source"), -total_below, cursor)

    for level, y0, y1 in computed:
        outline = msp.add_lwpolyline(
            [(dx, y0), (dx + width, y0), (dx + width, y1), (dx, y1)], dxfattribs={"layer": "DUVARLAR"}
        )
        outline.closed = True

        window_count = level.get("window_count", 0)
        if window_count > 0:
            win_w, win_h = level.get("window_size", list(DEFAULT_ELEVATION_WINDOW_SIZE))
            sill = max(0.0, (level["height"] - win_h) / 2.0)
            gap = width / (window_count + 1)
            for i in range(1, window_count + 1):
                cx = dx + gap * i
                x0w = cx - win_w / 2.0
                win = msp.add_lwpolyline(
                    [
                        (x0w, y0 + sill), (x0w + win_w, y0 + sill),
                        (x0w + win_w, y0 + sill + win_h), (x0w, y0 + sill + win_h),
                    ],
                    dxfattribs={"layer": "KAPI-PENCERE"},
                )
                win.closed = True

        if level.get("door"):
            door_w, door_h = ELEVATION_DOOR_SIZE
            cx = dx + width / 2.0
            x0d = cx - door_w / 2.0
            door = msp.add_lwpolyline(
                [(x0d, y0), (x0d + door_w, y0), (x0d + door_w, y0 + door_h), (x0d, y0 + door_h)],
                dxfattribs={"layer": "KAPI-PENCERE"},
            )
            door.closed = True

        if level.get("machine_room"):
            mr_w, mr_h = width * 0.25, level["height"] * 0.8
            cx = dx + width * 0.2
            mr = msp.add_lwpolyline(
                [(cx, y1), (cx + mr_w, y1), (cx + mr_w, y1 + mr_h), (cx, y1 + mr_h)],
                dxfattribs={"layer": "DUVARLAR"},
            )
            mr.closed = True

        add_text(
            msp, level["label"], (dx - ELEVATION_LABEL_OFFSET, (y0 + y1) / 2.0), label_text_height, "METIN",
            align=TextEntityAlignment.MIDDLE_RIGHT,
        )

    msp.add_line((dx - 1000, 0), (dx + width + 1000, 0), dxfattribs={"layer": "OLCU"})
    add_text(
        msp, "+-0.00 ZEMIN", (dx - ELEVATION_LABEL_OFFSET, 150.0), label_text_height, "OLCU",
        align=TextEntityAlignment.MIDDLE_RIGHT,
    )


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
    content_ranges = [(0.0, floor_depth) for _ in floors]
    for elevation in elevations:
        content_ranges.append(elevation_vertical_extent(elevation))

    sheet = Sheet(scale, text_height, all_labels, content_ranges)
    grid = context["grid"]
    axis_grid = AxisGrid(grid["vertical_axes"], grid["horizontal_axes"], text_height)

    # Cephe kat etiketleri (+ zemin notu), pafta IC cizgisinden itibaren
    # birakilan bosluga (CONTENT_PADDING) sigacak, sifir-hizali degil
    # gercekten padding'li konumlandirilir (bkz. scripts/pafta/CLAUDE.md -
    # onceki surumde bu metinler pafta kenarina bitisikti / komsu paftaya
    # tasiyordu).
    elevation_level_labels = [lvl["label"] for e in elevations for lvl in e["levels"]] + ["+-0.00 ZEMIN"]
    elevation_label_height = fit_uniform_text_height(
        elevation_level_labels, available_width=CONTENT_PADDING - 600.0, max_height=text_height,
    )

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
    cover_outer_x1 = draw_cover_sheet(msp, context, cursor, sheet)
    cursor = cover_outer_x1 + frame_half_width

    for floor in floors:
        draw_floor_sheet(msp, floor, cursor, units, floor_width, floor_depth, text_height,
                         sheet, axis_grid, text_styles)
        cursor += floor_width + 2 * frame_half_width

    for elevation in elevations:
        content_start = len(msp)
        draw_elevation(msp, elevation, cursor, text_height, axis_grid, elevation_label_height)
        content_entities = list(msp)[content_start:]
        y_bottom, y_top = elevation_vertical_extent(elevation)
        sheet.draw(msp, cursor, elevation["width"], y_bottom, y_top, elevation["label"], content_entities=content_entities)
        cursor += elevation["width"] + 2 * frame_half_width

    output_path.parent.mkdir(parents=True, exist_ok=True)
    return save_with_fallback(lambda p: doc.saveas(p), output_path)


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
