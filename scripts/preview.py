#!/usr/bin/env python3
"""context.json'dan basit bir ustten-gorunum PNG onizlemesi uretir.

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


def generate_preview(context_path: Path = DEFAULT_CONTEXT_PATH, output_path: Path = DEFAULT_OUTPUT_PATH) -> Path:
    context = load_json(context_path)

    fig, ax = plt.subplots(figsize=(10, 10))

    for room in context["rooms"]:
        polygon = room["polygon"]
        patch = MplPolygon(polygon, closed=True, facecolor="#dbeafe", edgecolor="none", alpha=0.6, zorder=1)
        ax.add_patch(patch)
        xs = [p[0] for p in polygon]
        ys = [p[1] for p in polygon]
        cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
        ax.text(
            cx, cy, f"{room['name']}\n{room['area_m2']:.1f} m2",
            ha="center", va="center", fontsize=9, zorder=4,
        )

    for wall in context["walls"]:
        x1, y1 = wall["start"]
        x2, y2 = wall["end"]
        thickness = wall.get("thickness", 1)
        ax.plot([x1, x2], [y1, y2], color="black", linewidth=max(1.0, thickness / 50), zorder=2)

    walls_by_id = {w["id"]: w for w in context["walls"]}
    for opening in context["openings"]:
        wall = walls_by_id.get(opening["wall_id"])
        if wall is None:
            continue
        x1, y1 = wall["start"]
        x2, y2 = wall["end"]
        length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        if length == 0:
            continue
        dx, dy = (x2 - x1) / length, (y2 - y1) / length
        pos = opening["position_from_start"]
        half = opening["width"] / 2.0
        gx1, gy1 = x1 + dx * (pos - half), y1 + dy * (pos - half)
        gx2, gy2 = x1 + dx * (pos + half), y1 + dy * (pos + half)
        color = "#dc2626" if opening["type"] == "door" else "#2563eb"
        ax.plot([gx1, gx2], [gy1, gy2], color=color, linewidth=3, zorder=3)

    for label in context["labels"]:
        x, y = label["position"]
        ax.text(x, y, label["text"], fontsize=8, color="#374151", zorder=4)

    ax.set_aspect("equal", adjustable="datalim")
    ax.autoscale_view()
    ax.set_title(context["meta"].get("project_name") or "Daire Plani Onizleme")
    ax.set_xlabel(f"birim: {context['meta']['units']}")
    ax.grid(True, linestyle="--", linewidth=0.3, alpha=0.5)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return output_path


def main() -> int:
    context_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CONTEXT_PATH
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_OUTPUT_PATH
    result = generate_preview(context_path, output_path)
    print(f"Onizleme uretildi: {result}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
