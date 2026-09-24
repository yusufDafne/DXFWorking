#!/usr/bin/env python3
"""context.json'dan tum paftalarin (kat planlari + cepheler) basit bir
ustten-gorunum PNG onizlemesini uretir.

Kullanim:
    python scripts/preview.py [context.json yolu] [cikti .png yolu]

Bu script sadece gorsel bir onizleme icindir; output/plan.dxf uzerinde hicbir
etkisi yoktur ve DXF'nin yerini tutmaz.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as MplPolygon
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "matplotlib"])
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as MplPolygon

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pafta import (  # noqa: E402  (once sys.path ayarlanmali)
    CONTENT_PADDING,
    FRAME_GAP,
    CoverBlock,
    ScaleBar,
    Sheet,
    format_scale_value,
    parse_scale_denominator,
    to_modelspace,
)
from version import (  # noqa: E402
    SCHEMA_VERSION,
    format_timestamp,
    generation_timestamp,
)
from rooms import RoomLabeler  # noqa: E402
from elevations import LevelStack, elevation_vertical_extent  # noqa: E402
from legend import COLUMNS, COLUMN_WEIGHTS, OpeningLegend  # noqa: E402
from northarrow import NORTH_LABEL, NorthArrow, rotate_point  # noqa: E402
from sections import (  # noqa: E402
    SectionCutLine,
    crossing_walls,
    resolve_sections,
    section_vertical_extent,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONTEXT_PATH = PROJECT_ROOT / "context.json"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "output" / "preview.png"
FRAME_HALF_WIDTH = CONTENT_PADDING + FRAME_GAP  # generate_dxf.py ile ayni bitisik-pafta formulu


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


def _draw_legend_preview(ax, rows, x0: float, y_top: float, width: float,
                         row_h: float, title_row_h: float) -> None:
    """`legend.LegendRenderer.draw`nin onizleme (matplotlib) karsiligi - AYNI
    sutun agirliklarini (`COLUMN_WEIGHTS`) kullanir, boylece DXF ile onizleme
    ayni tabloyu gosterir (bkz. kok CLAUDE.md 'onizleme pafta DXF ile
    birebir')."""
    n_rows = 1 + len(rows)
    row_ys = [y_top - title_row_h - i * row_h for i in range(n_rows + 1)]
    col_ws = [width * w for w in COLUMN_WEIGHTS]
    col_xs = [x0]
    for w in col_ws:
        col_xs.append(col_xs[-1] + w)
    bottom_y = row_ys[-1]

    for y in [y_top] + row_ys:
        ax.plot([x0, x0 + width], [y, y], color="#6b7280", linewidth=0.5, zorder=4)
    for x in (col_xs[0], col_xs[-1]):
        ax.plot([x, x], [y_top, bottom_y], color="#6b7280", linewidth=0.5, zorder=4)
    for x in col_xs[1:-1]:
        ax.plot([x, x], [row_ys[0], bottom_y], color="#6b7280", linewidth=0.5, zorder=4)

    ax.text(x0 + width / 2.0, (y_top + row_ys[0]) / 2.0, "KAPI/PENCERE CETVELI",
            fontsize=2.6, color="#111827", ha="center", va="center", zorder=5)
    for label, cx0, cx1 in zip(COLUMNS, col_xs[:-1], col_xs[1:]):
        ax.text((cx0 + cx1) / 2.0, (row_ys[0] + row_ys[1]) / 2.0, label,
                fontsize=2.2, color="#111827", ha="center", va="center", zorder=5)
    for row_index, row in enumerate(rows, start=1):
        values = (row.mark, row.type_label, row.variant_label, str(row.width_cm), str(row.count))
        y_center = (row_ys[row_index] + row_ys[row_index + 1]) / 2.0
        for value, cx0, cx1 in zip(values, col_xs[:-1], col_xs[1:]):
            ax.text((cx0 + cx1) / 2.0, y_center, value, fontsize=2.0,
                    color="#374151", ha="center", va="center", zorder=5)


def draw_cover(ax, meta: dict, dx: float, sheet, floors: list[dict] | None = None) -> float:
    """generate_dxf.py::draw_cover_sheet'in onizleme karsiligi; paftanin DIS
    cercevesinin sag kenarini (mutlak X) dondurur.

    Kapak paftasinin DIS CERCEVE GENISLIGI kapak genisligine ESITTIR (padding
    yok), kapak blogu paftanin ALTINA oturur ve bu paftada antet kutusu
    yoktur."""
    block = CoverBlock(meta.get("scale", "1:100"))
    gap = block.frame_gap
    sheet_width = block.width - 2 * gap
    x0, y0 = dx - gap, sheet.frame_y0
    y1 = sheet.frame_y1

    # Pafta cift cercevesi (kapak blogunun dis hattiyla cakisir)
    ax.add_patch(plt.Rectangle((x0, y0), block.width, y1 - y0, facecolor="white",
                               edgecolor="#111827", linewidth=0.9, zorder=3))
    ax.add_patch(plt.Rectangle((dx, y0 + gap), sheet_width, (y1 - y0) - 2 * gap,
                               facecolor="none", edgecolor="#6b7280", linewidth=0.5, zorder=4))
    # A4 panelini yukaridan kapatan ust kenar
    ax.plot([x0, x0 + block.width], [y0 + block.height] * 2, color="#111827", lw=0.9, zorder=4)
    ax.plot([dx, dx + sheet_width], [y0 + block.height - gap] * 2, color="#6b7280", lw=0.5, zorder=4)

    inner_x0, inner_y0 = dx, y0 + gap
    inner_w = sheet_width
    ax.text(inner_x0 + inner_w / 2.0, inner_y0 + block.mm(247.0),
            meta.get("project_name", "MIMARI PROJE"),
            fontsize=6, color="#111827", ha="center", va="center", zorder=5)
    cover_meta = meta.get("cover", {})
    rows = [
        ("PROJE TIPI", meta.get("project_type", "")),
        ("OLCEK", meta.get("scale", "")),
        ("MIMAR", cover_meta.get("architect_name", "")),
        ("TARIH", cover_meta.get("date", "")),
    ]
    for index, (label, value) in enumerate(rows):
        row_y = inner_y0 + block.mm(214.0 - 15.0 * index)
        ax.text(inner_x0 + block.mm(4.0), row_y, f"{label} :", fontsize=4,
                color="#374151", ha="left", va="center", zorder=5)
        ax.text(inner_x0 + block.mm(55.0), row_y, value or "................",
                fontsize=4, color="#374151", ha="left", va="center", zorder=5)

    # Uretim damgasi (generate_dxf.py::draw_cover_sheet ile ayni yerde):
    # ciktinin uretildigi an + sistem sozlesme surumu. Onizleme DXF ile ayni
    # yerlesimi gostermek zorundadir, bu yuzden burada da cizilir.
    footer_y = inner_y0 + block.mm(10.0)
    ax.text(inner_x0 + block.mm(4.0), footer_y,
            f"URETIM: {format_timestamp(generation_timestamp())}",
            fontsize=3, color="#6b7280", ha="left", va="center", zorder=5)
    ax.text(inner_x0 + inner_w - block.mm(4.0), footer_y, f"SISTEM: {SCHEMA_VERSION}",
            fontsize=3, color="#6b7280", ha="right", va="center", zorder=5)

    signature_labels = cover_meta.get("signature_fields", [])
    if signature_labels:
        columns = 2
        sig_rows = -(-len(signature_labels) // columns)
        sig_gap = block.mm(10.0)
        band = block.mm(110.0)
        cell_w = (inner_w - sig_gap * (columns - 1)) / columns
        cell_h = (band - sig_gap * (sig_rows - 1)) / sig_rows
        for index, label in enumerate(signature_labels):
            column, row = index % columns, index // columns
            bx0 = inner_x0 + column * (cell_w + sig_gap)
            by0 = inner_y0 + block.mm(20.0) + (sig_rows - 1 - row) * (cell_h + sig_gap)
            ax.add_patch(plt.Rectangle((bx0, by0), cell_w, cell_h, facecolor="none",
                                       edgecolor="#6b7280", linewidth=0.5, zorder=4))
            ax.text(bx0 + block.mm(4.0), by0 + block.mm(5.0), label or "(UNVAN)",
                    fontsize=3.5, color="#6b7280", ha="left", va="center", zorder=5)

    if floors:
        legend_rows = OpeningLegend.rows(floors)
        if legend_rows:
            margin = gap
            _draw_legend_preview(
                ax, legend_rows, x0 + margin, y1 - gap - margin, block.width - 2 * margin,
                row_h=block.mm(9.0), title_row_h=block.mm(11.0),
            )

    ax.text(dx, -600, "KAPAK PAFTASI", fontsize=7, color="#111827", ha="left", va="top")
    return dx + sheet_width + gap


def draw_floor(ax, floor: dict, dx: float) -> None:
    for room in floor["rooms"]:
        polygon = [(p[0] + dx, p[1]) for p in room["polygon"]]
        patch = MplPolygon(polygon, closed=True, facecolor="#dbeafe", edgecolor="none", alpha=0.6, zorder=1)
        ax.add_patch(patch)
        xs = [p[0] for p in polygon]
        ys = [p[1] for p in polygon]
        cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
        # DXF ile AYNI 3 satirli mahal etiketi (bkz. rooms::RoomLabeler)
        ax.text(
            cx, cy, RoomLabeler.content(room, floor.get("code", "")),
            ha="center", va="center", fontsize=4.5, zorder=4, linespacing=1.4,
        )

    for wall in floor["walls"]:
        x1, y1 = wall["start"][0] + dx, wall["start"][1]
        x2, y2 = wall["end"][0] + dx, wall["end"][1]
        thickness = wall.get("thickness", 1)
        ax.plot([x1, x2], [y1, y2], color="black", linewidth=max(0.5, thickness / 80), zorder=2)

    walls_by_id = {w["id"]: w for w in floor["walls"]}
    for opening in floor["openings"]:
        wall = walls_by_id.get(opening["wall_id"])
        if wall is None:
            continue
        x1, y1 = wall["start"]
        x2, y2 = wall["end"]
        length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        if length == 0:
            continue
        ux, uy = (x2 - x1) / length, (y2 - y1) / length
        pos = opening["position_from_start"]
        half = opening["width"] / 2.0
        gx1, gy1 = x1 + ux * (pos - half) + dx, y1 + uy * (pos - half)
        gx2, gy2 = x1 + ux * (pos + half) + dx, y1 + uy * (pos + half)
        color = "#dc2626" if opening["type"] == "door" else "#2563eb"
        ax.plot([gx1, gx2], [gy1, gy2], color=color, linewidth=2, zorder=3)

    for counter in floor.get("counters", []):
        polygon = [(p[0] + dx, p[1]) for p in counter["polygon"]]
        ax.add_patch(MplPolygon(polygon, closed=True, facecolor="#d1d5db", edgecolor="#6b7280", linewidth=0.5, zorder=3))

    for marking in floor.get("markings", []):
        x1, y1 = marking["start"][0] + dx, marking["start"][1]
        x2, y2 = marking["end"][0] + dx, marking["end"][1]
        ax.plot([x1, x2], [y1, y2], color="#9ca3af", linewidth=0.6, zorder=2)

    for label in floor["labels"]:
        x, y = label["position"][0] + dx, label["position"][1]
        ax.text(x, y, label["text"], fontsize=5, color="#374151", zorder=4)

    ax.text(dx, -600, floor["label"], fontsize=7, color="#111827", ha="left", va="top")


def draw_axes_on_floor(ax, grid: dict, dx: float, floor_width: float, floor_depth: float) -> None:
    ext = 700.0
    for axis in grid["vertical_axes"]:
        x = dx + axis["position"]
        ax.plot([x, x], [-ext, floor_depth + ext], color="#dc2626", linewidth=0.6, linestyle="--", zorder=5)
        ax.text(x, -ext, axis["label"], fontsize=5, color="#dc2626", ha="center", va="top")
    for axis in grid["horizontal_axes"]:
        y = axis["position"]
        ax.plot([dx - ext, dx + floor_width + ext], [y, y], color="#dc2626", linewidth=0.6, linestyle="--", zorder=5)
        ax.text(dx - ext, y, axis["label"], fontsize=5, color="#dc2626", ha="right", va="center")


def draw_axes_on_elevation(ax, grid: dict, dx: float, axis_source: str | None, y_bottom: float, y_top: float) -> None:
    ext = 700.0
    if axis_source == "vertical":
        axes = grid["vertical_axes"]
    elif axis_source == "horizontal":
        axes = grid["horizontal_axes"]
    else:
        return
    for axis in axes:
        x = dx + axis["position"]
        ax.plot([x, x], [y_bottom - ext, y_top + ext], color="#dc2626", linewidth=0.6, linestyle="--", zorder=5)
        ax.text(x, y_top + ext, axis["label"], fontsize=5, color="#dc2626", ha="center", va="bottom")


def draw_elevation(ax, elevation: dict, dx: float) -> None:
    # DEV-011 (rev-14): cursor/extent hesabi artik scripts/elevations
    # modulunde TEK yerde (LevelStack) - burada tekrarlanmaz. below_ground
    # kesikli cizgisi bu onizlemede zaten VARDI (matplotlib linestyle="--");
    # gercek DXF cikisinda ise rev-14'ten once YOKTU (bkz. ElevationSheet).
    width = elevation["width"]
    for level, y0, y1 in LevelStack.from_context(elevation).placements():
        style = "--" if level.below_ground else "-"
        ax.plot([dx, dx + width, dx + width, dx, dx], [y0, y0, y1, y1, y0], color="black", linewidth=0.8, linestyle=style)
        ax.text(dx - 200, (y0 + y1) / 2, level.label, fontsize=5, ha="right", va="center")
        if level.window_count:
            win_w, win_h = level.window_size
            gap = width / (level.window_count + 1)
            sill = max(0.0, (level.height - win_h) / 2.0)
            for i in range(1, level.window_count + 1):
                cx = dx + gap * i
                ax.add_patch(plt.Rectangle((cx - win_w / 2, y0 + sill), win_w, win_h, facecolor="#bfdbfe", edgecolor="#2563eb", linewidth=0.4))
        if level.door:
            dw, dh = 1800, 2100
            ax.add_patch(plt.Rectangle((dx + width / 2 - dw / 2, y0), dw, dh, facecolor="#fecaca", edgecolor="#dc2626", linewidth=0.4))
    ax.plot([dx - 1000, dx + width + 1000], [0, 0], color="#9ca3af", linewidth=0.6)
    ax.text(dx, -600, elevation["label"], fontsize=7, color="#111827", ha="left", va="top")


def draw_scale_bar_preview(ax, scale_bar: ScaleBar, x0: float, y0: float) -> None:
    """`scripts/pafta::ScaleBar` ile AYNI olculeri kullanan basit onizleme -
    gercek DXF cizimini TEKRARLAMAZ, sadece ayni sayilari (segment_m,
    segment_length) matplotlib ile gosterir (DEV-025)."""
    ax.plot([x0, x0 + scale_bar.total_length], [y0, y0], color="black", linewidth=0.8, zorder=5)
    for i in range(scale_bar.SEGMENTS + 1):
        x = x0 + i * scale_bar.segment_length
        ax.plot([x, x], [y0, y0 + scale_bar.tick_height], color="black", linewidth=0.8, zorder=5)
        label = format_scale_value(i * scale_bar.segment_m)
        if i == scale_bar.SEGMENTS:
            label = f"{label} m"
        ax.text(x, y0 + scale_bar.tick_height * 1.6, label, fontsize=3.5, ha="center", va="bottom", zorder=5)


def draw_north_arrow_preview(ax, center: tuple[float, float], angle_deg: float, radius: float) -> None:
    """`scripts/northarrow::NorthArrow` ile AYNI donme yonunu (`rotate_point`)
    kullanan basit onizleme (DEV-025)."""
    cx, cy = center
    ax.add_patch(plt.Circle((cx, cy), radius, fill=False, edgecolor="black", linewidth=0.6, zorder=5))
    tip = rotate_point(center, radius, angle_deg)
    ax.plot([cx, tip[0]], [cy, tip[1]], color="black", linewidth=1.2, zorder=5)
    label_point = rotate_point(center, radius * 1.5, angle_deg)
    ax.text(label_point[0], label_point[1], NORTH_LABEL, fontsize=5, ha="center", va="center", zorder=5)


def draw_cut_marker_preview(ax, cut: SectionCutLine, dx: float, floor_width: float, floor_depth: float) -> None:
    """Kat plani uzerindeki kesit hatti + ucgen isaretlerin basit onizlemesi
    (DEV-021) - `scripts/sections::draw_cut_marker_on_floor` ile AYNI
    cut objesinden ('sections.resolve_sections') beslenir, kendi kopyasini
    UYDURMAZ."""
    ext = 400.0
    if cut.axis_source == "vertical":
        p1, p2 = (dx - ext, cut.position), (dx + floor_width + ext, cut.position)
    else:
        p1, p2 = (dx + cut.position, -ext), (dx + cut.position, floor_depth + ext)
    ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color="#b91c1c", linewidth=1.0,
           linestyle=(0, (6, 3, 1, 3)), zorder=5)
    for point in (p1, p2):
        ax.text(point[0], point[1], cut.letter, fontsize=5, color="#b91c1c", ha="center", va="center",
               zorder=6, bbox=dict(boxstyle="circle", fc="white", ec="#b91c1c", linewidth=0.5))


def draw_section_preview(ax, cut: SectionCutLine, floors: list[dict],
                         elevation_lookup: dict[str, dict], dx: float, width: float) -> None:
    """Bir kesidin basit onizlemesi (DEV-021): her katta KESILEN duvarlar
    dolu (siyah) dikdortgen, kat sinirlari duz cizgi. `draw_elevation` ile
    AYNI gorsel dilde (bkz. yukarisi)."""
    stack = LevelStack.from_context(elevation_lookup[cut.levels_from])
    placements = stack.placements()
    for floor, (level, y0, y1) in zip(floors, placements):
        ax.plot([dx, dx + width], [y0, y0], color="black", linewidth=0.8)
        for crossing in crossing_walls(floor["walls"], cut.axis_source, cut.position):
            half = crossing["thickness"] / 2.0
            local = crossing["at"]
            ax.add_patch(plt.Rectangle((dx + local - half, y0), crossing["thickness"], y1 - y0,
                                       facecolor="#374151", edgecolor="none", zorder=3))
        ax.text(dx - 200, (y0 + y1) / 2, level.label, fontsize=5, ha="right", va="center")
    stack_top = stack.stack_top()
    ax.plot([dx, dx + width], [stack_top, stack_top], color="black", linewidth=0.8)
    ax.plot([dx - 1000, dx + width + 1000], [0, 0], color="#9ca3af", linewidth=0.6)
    ax.text(dx, -600, f"{cut.label} KESITI", fontsize=7, color="#111827", ha="left", va="top")


def generate_preview(context_path: Path = DEFAULT_CONTEXT_PATH, output_path: Path = DEFAULT_OUTPUT_PATH) -> Path:
    context = load_json(context_path)
    meta = context["meta"]
    floor_width = meta.get("floor_width")

    fig, ax = plt.subplots(figsize=(28, 8))

    grid = context.get("grid")
    if floor_width is not None:
        floor_depth = meta.get("floor_depth")
        # Paftalar dis cizgilerinden bitisiktir (bkz. scripts/pafta/CLAUDE.md) -
        # generate_dxf.py ile ayni formul kullanilir, aralarinda ekstra bosluk yok.
        cursor = 0.0
        # Kapak paftasi, DXF'te oldugu gibi ilk paftadir (bkz. generate_dxf.py::generate).
        # Kapak blogunun dusey konumu paylasilan mutlak pafta araligina baglidir,
        # bu yuzden Sheet ayni content_ranges ile burada da kurulur.
        scale = meta.get("scale", "1:100")
        units = meta.get("units", "mm")
        sections = resolve_sections(context)
        elevation_lookup = {e["id"]: e for e in context["elevations"]}
        content_ranges = [(0.0, floor_depth) for _ in context["floors"]]
        for elevation in context["elevations"]:
            content_ranges.append(elevation_vertical_extent(elevation))
        for cut in sections:
            content_ranges.append(section_vertical_extent(cut, elevation_lookup))
        sheet = Sheet(scale, 350.0, [], content_ranges)
        scale_bar = ScaleBar(scale, units)
        sheet_margin = to_modelspace(10.0, parse_scale_denominator(scale))
        north_angle = meta.get("north_angle")
        # Kapak paftasinin dis cercevesi kapak genisligi kadardir (padding yok).
        cursor = draw_cover(ax, meta, cursor, sheet, context["floors"]) + FRAME_HALF_WIDTH
        for floor in context["floors"]:
            draw_floor(ax, floor, cursor)
            if grid:
                draw_axes_on_floor(ax, grid, cursor, floor_width, floor_depth)
            for cut in sections:
                draw_cut_marker_preview(ax, cut, cursor, floor_width, floor_depth)
            center_x = cursor + floor_width / 2.0
            bar_y0 = floor_depth + sheet_margin
            draw_scale_bar_preview(ax, scale_bar, center_x - scale_bar.total_length / 2.0, bar_y0)
            if north_angle is not None:
                north_arrow = NorthArrow(scale)
                arrow_center = (center_x, bar_y0 + scale_bar.total_height + sheet_margin + north_arrow.radius)
                draw_north_arrow_preview(ax, arrow_center, north_angle, north_arrow.radius)
            cursor += floor_width + 2 * FRAME_HALF_WIDTH
        for elevation in context["elevations"]:
            draw_elevation(ax, elevation, cursor)
            y_bottom, y_top = elevation_vertical_extent(elevation)
            if grid:
                draw_axes_on_elevation(ax, grid, cursor, elevation.get("axis_source"), y_bottom, y_top)
            draw_scale_bar_preview(
                ax, scale_bar, cursor + elevation["width"] / 2.0 - scale_bar.total_length / 2.0,
                y_top + sheet_margin)
            cursor += elevation["width"] + 2 * FRAME_HALF_WIDTH
        for cut in sections:
            width = cut.width_for(floor_width, floor_depth)
            draw_section_preview(ax, cut, context["floors"], elevation_lookup, cursor, width)
            y_bottom, y_top = section_vertical_extent(cut, elevation_lookup)
            if grid:
                draw_axes_on_elevation(ax, grid, cursor, cut.axis_source, y_bottom, y_top)
            draw_scale_bar_preview(
                ax, scale_bar, cursor + width / 2.0 - scale_bar.total_length / 2.0,
                y_top + sheet_margin)
            cursor += width + 2 * FRAME_HALF_WIDTH
    else:
        # eski tek-daire (duz) sema geriye-donuk uyumluluk
        draw_floor(ax, context, 0.0)

    ax.set_aspect("equal", adjustable="datalim")
    ax.autoscale_view()
    ax.set_title(context["meta"].get("project_name") or "Bina Plani Onizleme")
    ax.set_xlabel(f"birim: {context['meta']['units']}")
    ax.grid(True, linestyle="--", linewidth=0.3, alpha=0.4)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    saved_path = save_with_fallback(
        lambda p: fig.savefig(p, dpi=150, bbox_inches="tight"), output_path
    )
    plt.close(fig)
    return saved_path


def main() -> int:
    context_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CONTEXT_PATH
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_OUTPUT_PATH
    result = generate_preview(context_path, output_path)
    print(f"Onizleme uretildi: {result}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
