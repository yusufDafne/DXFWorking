#!/usr/bin/env python3
"""context.json'dan output/plan.dxf uretir.

Kullanim:
    python scripts/generate_dxf.py [context.json yolu] [cikti .dxf yolu]

ONEMLI: Bu script, context.json'da (veya kullanicidan gelen talepte) mevcut
OLMAYAN hicbir olcuyu/koordinati uydurmaz. Asagida gorulen sabitler (metin
yuksekligi, kapi kolu/pervaz cizim detaylari gibi) SADECE cizim/sunum
kurallaridir; mimari tasarim verisi degildir ve context.json'daki gercek
geometriyi degistirmez.

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
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "ezdxf"])
    import ezdxf

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONTEXT_PATH = PROJECT_ROOT / "context.json"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "output" / "plan.dxf"

# --- Cizim/sunum sabitleri (tasarim verisi degil) ---
DEFAULT_LAYER_COLOR = 7
GAP_EPSILON = 1e-6  # duvar uzerinde kalan parca cok kisaysa cizmemek icin


def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def text_height_for_units(units: str) -> float:
    # Cizimde okunabilir metin yuksekligi icin standart bir CAD sunum degeri.
    return 250.0 if units == "mm" else 0.25


def vec_sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def vec_add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def vec_scale(a, s):
    return (a[0] * s, a[1] * s)


def vec_len(a):
    return math.hypot(a[0], a[1])


def vec_norm(a):
    length = vec_len(a)
    if length == 0:
        return (0.0, 0.0)
    return (a[0] / length, a[1] / length)


def vec_perp(a):
    # 90 derece saat yonu tersine (CCW) donduruleus vektor
    return (-a[1], a[0])


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


def gaps_for_wall(wall: dict, openings: list[dict]) -> list[tuple[float, float]]:
    start = wall["start"]
    end = wall["end"]
    length = vec_len(vec_sub(end, start))
    gaps = []
    for op in openings:
        if op["wall_id"] != wall["id"]:
            continue
        half = op["width"] / 2.0
        g_start = max(0.0, op["position_from_start"] - half)
        g_end = min(length, op["position_from_start"] + half)
        if g_end > g_start:
            gaps.append((g_start, g_end, op))
    gaps.sort(key=lambda g: g[0])
    return gaps


def draw_wall(msp, wall: dict, openings: list[dict]) -> None:
    start = tuple(wall["start"])
    end = tuple(wall["end"])
    length = vec_len(vec_sub(end, start))
    if length <= 0:
        return
    direction = vec_norm(vec_sub(end, start))
    thickness = wall["thickness"]
    layer = wall["layer"]

    gaps = gaps_for_wall(wall, openings)

    # Duvarin acikliklar disinda kalan dolu kisimlarini ciz
    cursor = 0.0
    solid_segments = []
    for g_start, g_end, _op in gaps:
        if g_start - cursor > GAP_EPSILON:
            solid_segments.append((cursor, g_start))
        cursor = max(cursor, g_end)
    if length - cursor > GAP_EPSILON:
        solid_segments.append((cursor, length))
    if not gaps:
        solid_segments = [(0.0, length)]

    for seg_start, seg_end in solid_segments:
        p1 = vec_add(start, vec_scale(direction, seg_start))
        p2 = vec_add(start, vec_scale(direction, seg_end))
        msp.add_lwpolyline(
            [p1, p2],
            dxfattribs={"layer": layer, "const_width": thickness},
        )

    # Aciklik sembollerini ciz (kapi: kanat + kavis; pencere: cift cizgi)
    perp = vec_perp(direction)
    for g_start, g_end, op in gaps:
        hinge = vec_add(start, vec_scale(direction, g_start))
        far = vec_add(start, vec_scale(direction, g_end))
        width = g_end - g_start
        op_layer = op.get("layer", "KAPI-PENCERE")

        if op["type"] == "door":
            leaf_end = vec_add(hinge, vec_scale(perp, width))
            msp.add_line(hinge, leaf_end, dxfattribs={"layer": op_layer})
            start_angle = math.degrees(math.atan2(direction[1], direction[0]))
            end_angle = math.degrees(math.atan2(perp[1], perp[0]))
            msp.add_arc(
                center=hinge,
                radius=width,
                start_angle=min(start_angle, end_angle),
                end_angle=max(start_angle, end_angle),
                dxfattribs={"layer": op_layer},
            )
        else:  # window
            offset = thickness / 4.0
            for sign in (-1, 1):
                off_vec = vec_scale(perp, sign * offset)
                msp.add_line(
                    vec_add(hinge, off_vec),
                    vec_add(far, off_vec),
                    dxfattribs={"layer": op_layer},
                )


def polygon_centroid(polygon: list[list[float]]) -> tuple[float, float]:
    area = 0.0
    cx = 0.0
    cy = 0.0
    n = len(polygon)
    for i in range(n):
        x1, y1 = polygon[i]
        x2, y2 = polygon[(i + 1) % n]
        cross = x1 * y2 - x2 * y1
        area += cross
        cx += (x1 + x2) * cross
        cy += (y1 + y2) * cross
    area *= 0.5
    if abs(area) < 1e-9:
        # dejenere poligon icin basit ortalama
        xs = [p[0] for p in polygon]
        ys = [p[1] for p in polygon]
        return (sum(xs) / len(xs), sum(ys) / len(ys))
    cx /= 6 * area
    cy /= 6 * area
    return (cx, cy)


def draw_room_label(msp, room: dict, text_height: float) -> None:
    cx, cy = polygon_centroid(room["polygon"])
    content = f"{room['name']} ({room['area_m2']:.1f} m2)"
    text = msp.add_text(content, dxfattribs={"layer": "METIN", "height": text_height})
    text.dxf.insert = (cx, cy)


def draw_labels(msp, labels: list[dict], default_height: float) -> None:
    for label in labels:
        height = label.get("height", default_height)
        layer = label.get("layer", "METIN")
        text = msp.add_text(label["text"], dxfattribs={"layer": layer, "height": height})
        text.dxf.insert = tuple(label["position"])


def generate(context_path: Path = DEFAULT_CONTEXT_PATH, output_path: Path = DEFAULT_OUTPUT_PATH) -> Path:
    context = load_json(context_path)
    units = context["meta"]["units"]

    doc = ezdxf.new(dxfversion="R2010")
    doc.header["$INSUNITS"] = ezdxf.units.MM if units == "mm" else ezdxf.units.M
    setup_layers(doc, context["layers"])
    msp = doc.modelspace()

    openings = context["openings"]
    for wall in context["walls"]:
        draw_wall(msp, wall, openings)

    text_height = text_height_for_units(units)
    for room in context["rooms"]:
        draw_room_label(msp, room, text_height)

    draw_labels(msp, context["labels"], text_height)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(output_path)
    return output_path


def main() -> int:
    context_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CONTEXT_PATH
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_OUTPUT_PATH
    result = generate(context_path, output_path)
    print(f"DXF uretildi: {result}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
