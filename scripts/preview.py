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

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONTEXT_PATH = PROJECT_ROOT / "context.json"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "output" / "preview.png"


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


def draw_floor(ax, floor: dict, dx: float) -> None:
    for room in floor["rooms"]:
        polygon = [(p[0] + dx, p[1]) for p in room["polygon"]]
        patch = MplPolygon(polygon, closed=True, facecolor="#dbeafe", edgecolor="none", alpha=0.6, zorder=1)
        ax.add_patch(patch)
        xs = [p[0] for p in polygon]
        ys = [p[1] for p in polygon]
        cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
        ax.text(
            cx, cy, f"{room['name']}\n{room['area_m2']:.1f} m2",
            ha="center", va="center", fontsize=5, zorder=4,
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


def elevation_vertical_extent(elevation: dict) -> tuple[float, float]:
    levels = elevation["levels"]
    total_below = sum(l["height"] for l in levels if l.get("below_ground"))
    total_above = sum(l["height"] for l in levels if not l.get("below_ground"))
    return -total_below, total_above


def draw_elevation(ax, elevation: dict, dx: float) -> None:
    width = elevation["width"]
    levels = elevation["levels"]
    total_below = sum(l["height"] for l in levels if l.get("below_ground"))
    cursor = -total_below
    for level in levels:
        y0, y1 = cursor, cursor + level["height"]
        cursor = y1
        style = "--" if level.get("below_ground") else "-"
        ax.plot([dx, dx + width, dx + width, dx, dx], [y0, y0, y1, y1, y0], color="black", linewidth=0.8, linestyle=style)
        ax.text(dx - 200, (y0 + y1) / 2, level["label"], fontsize=5, ha="right", va="center")
        wc = level.get("window_count", 0)
        if wc:
            win_w, win_h = level.get("window_size", [1200, 1400])
            gap = width / (wc + 1)
            sill = max(0.0, (level["height"] - win_h) / 2.0)
            for i in range(1, wc + 1):
                cx = dx + gap * i
                ax.add_patch(plt.Rectangle((cx - win_w / 2, y0 + sill), win_w, win_h, facecolor="#bfdbfe", edgecolor="#2563eb", linewidth=0.4))
        if level.get("door"):
            dw, dh = 1800, 2100
            ax.add_patch(plt.Rectangle((dx + width / 2 - dw / 2, y0), dw, dh, facecolor="#fecaca", edgecolor="#dc2626", linewidth=0.4))
    ax.plot([dx - 1000, dx + width + 1000], [0, 0], color="#9ca3af", linewidth=0.6)
    ax.text(dx, -600, elevation["label"], fontsize=7, color="#111827", ha="left", va="top")


def generate_preview(context_path: Path = DEFAULT_CONTEXT_PATH, output_path: Path = DEFAULT_OUTPUT_PATH) -> Path:
    context = load_json(context_path)
    meta = context["meta"]
    floor_width = meta.get("floor_width")
    sheet_gap = meta.get("sheet_gap", 3000.0)

    fig, ax = plt.subplots(figsize=(28, 8))

    grid = context.get("grid")
    if floor_width is not None:
        floor_depth = meta.get("floor_depth")
        cursor = 0.0
        for floor in context["floors"]:
            draw_floor(ax, floor, cursor)
            if grid:
                draw_axes_on_floor(ax, grid, cursor, floor_width, floor_depth)
            cursor += floor_width + sheet_gap
        for elevation in context["elevations"]:
            draw_elevation(ax, elevation, cursor)
            if grid:
                y_bottom, y_top = elevation_vertical_extent(elevation)
                draw_axes_on_elevation(ax, grid, cursor, elevation.get("axis_source"), y_bottom, y_top)
            cursor += elevation["width"] + sheet_gap
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
