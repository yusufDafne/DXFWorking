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
"elevations" listesi soldan saga dizilir (her pafta kendi genisligi +
meta.sheet_gap kadar sagda baslar). Her pafta sag-alt kosesine bir cerceve
ve baslik (kat adi + pafta no) yazilir.

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

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONTEXT_PATH = PROJECT_ROOT / "context.json"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "output" / "plan.dxf"

# --- Cizim/sunum sabitleri (tasarim verisi degil) ---
DEFAULT_LAYER_COLOR = 7
GAP_EPSILON = 1e-6
PAFTA_MARGIN = 1500.0
DEFAULT_ELEVATION_WINDOW_SIZE = (1200.0, 1400.0)
ELEVATION_DOOR_SIZE = (1800.0, 2100.0)
AXIS_EXTENSION = 700.0
AXIS_BUBBLE_RADIUS = 450.0
AXIS_LINETYPE = "DASHED"
AXIS_LAYER = "AKS"


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
    return (-a[1], a[0])


def round_point(pt, units: str) -> tuple[float, float]:
    precision = 1 if units == "mm" else 4
    return (round(pt[0], precision), round(pt[1], precision))


def point_on_segment(pt, seg_a, seg_b, tol: float) -> bool:
    ax, ay = seg_a
    bx, by = seg_b
    px, py = pt
    abx, aby = bx - ax, by - ay
    seg_len = (abx ** 2 + aby ** 2) ** 0.5
    if seg_len == 0:
        return False
    apx, apy = px - ax, py - ay
    cross = abx * apy - aby * apx
    dist = abs(cross) / seg_len
    if dist > tol:
        return False
    t = (apx * abx + apy * aby) / (seg_len ** 2)
    return -1e-6 <= t <= 1 + 1e-6


def line_intersection(p1, d1, p2, d2):
    denom = d1[0] * d2[1] - d1[1] * d2[0]
    if abs(denom) < 1e-9:
        return None
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    t = (dx * d2[1] - dy * d2[0]) / denom
    return vec_add(p1, vec_scale(d1, t))


def project_s(point, origin, direction) -> float:
    return (point[0] - origin[0]) * direction[0] + (point[1] - origin[1]) * direction[1]


class Wall:
    """Tek bir duvar segmenti: merkez cizgisi + kalinlik (bkz. CLAUDE.md duvar standardi)."""

    def __init__(self, wall_id: str, start, end, thickness: float, layer: str):
        self.id = wall_id
        self.start = tuple(start)
        self.end = tuple(end)
        self.thickness = thickness
        self.layer = layer
        self.length = vec_len(vec_sub(self.end, self.start))
        self.direction = vec_norm(vec_sub(self.end, self.start))
        self.normal = vec_perp(self.direction)
        self.rail_trim = {"pos": [0.0, self.length], "neg": [0.0, self.length]}

    def rail_origin(self, side: str) -> tuple[float, float]:
        sign = 1.0 if side == "pos" else -1.0
        return vec_add(self.start, vec_scale(self.normal, sign * self.thickness / 2.0))

    def rail_point(self, side: str, s: float) -> tuple[float, float]:
        return vec_add(self.rail_origin(side), vec_scale(self.direction, s))

    def rail_line(self, side: str):
        return self.rail_origin(side), self.direction

    def endpoint_s(self, which: str) -> float:
        return 0.0 if which == "start" else self.length

    def set_trim(self, side: str, which: str, s: float) -> None:
        idx = 0 if which == "start" else 1
        self.rail_trim[side][idx] = s

    def centerline_point(self, s: float) -> tuple[float, float]:
        return vec_add(self.start, vec_scale(self.direction, s))


class WallNetwork:
    """Duvarlar arasi birlesim (kose / T-kesisimi) cozumlemesi (gonye/miter)."""

    def __init__(self, walls: list[Wall], units: str):
        self.walls = walls
        self.units = units
        self.tol = 1.0 if units == "mm" else 0.001
        self._resolve_joints()

    def _resolve_joints(self) -> None:
        endpoint_groups: dict[tuple[float, float], list[tuple[Wall, str]]] = {}
        for w in self.walls:
            for which, pt in (("start", w.start), ("end", w.end)):
                key = round_point(pt, self.units)
                endpoint_groups.setdefault(key, []).append((w, which))

        handled: set[tuple[str, str]] = set()

        for entries in endpoint_groups.values():
            if len(entries) < 2:
                continue
            for i in range(len(entries)):
                for j in range(i + 1, len(entries)):
                    wA, whichA = entries[i]
                    wB, whichB = entries[j]
                    self._miter_corner(wA, whichA, wB, whichB)
            for w, which in entries:
                handled.add((w.id, which))

        for w in self.walls:
            for which, pt in (("start", w.start), ("end", w.end)):
                if (w.id, which) in handled:
                    continue
                for other in self.walls:
                    if other.id == w.id:
                        continue
                    if point_on_segment(pt, other.start, other.end, self.tol):
                        self._trim_stub_at_through(w, which, other)
                        break

    def _miter_corner(self, wA: Wall, whichA: str, wB: Wall, whichB: str) -> None:
        for side in ("pos", "neg"):
            originA, dirA = wA.rail_line(side)
            originB, dirB = wB.rail_line(side)
            inter = line_intersection(originA, dirA, originB, dirB)
            if inter is None:
                continue
            wA.set_trim(side, whichA, project_s(inter, originA, dirA))
            wB.set_trim(side, whichB, project_s(inter, originB, dirB))

    def _trim_stub_at_through(self, stub: Wall, which: str, through: Wall) -> None:
        far_s = stub.endpoint_s("end" if which == "start" else "start")
        far_point = stub.centerline_point(far_s)
        for side in ("pos", "neg"):
            origin, direction = stub.rail_line(side)
            candidates = []
            for t_side in ("pos", "neg"):
                t_origin, t_dir = through.rail_line(t_side)
                inter = line_intersection(origin, direction, t_origin, t_dir)
                if inter is not None:
                    candidates.append(inter)
            if not candidates:
                continue
            best = min(candidates, key=lambda p: vec_len(vec_sub(p, far_point)))
            stub.set_trim(side, which, project_s(best, origin, direction))

    def drawable_rail_segments(self, wall: Wall, side: str, openings: list[dict]):
        s0, s1 = wall.rail_trim[side]
        if s0 > s1:
            s0, s1 = s1, s0

        gaps = []
        for op in openings:
            if op["wall_id"] != wall.id:
                continue
            half = op["width"] / 2.0
            g_start = max(s0, op["position_from_start"] - half)
            g_end = min(s1, op["position_from_start"] + half)
            if g_end > g_start:
                gaps.append((g_start, g_end))
        gaps.sort()

        cursor = s0
        segments = []
        for g_start, g_end in gaps:
            if g_start - cursor > GAP_EPSILON:
                segments.append((cursor, g_start))
            cursor = max(cursor, g_end)
        if s1 - cursor > GAP_EPSILON:
            segments.append((cursor, s1))
        if not gaps:
            segments = [(s0, s1)]

        return [
            (wall.rail_point(side, a), wall.rail_point(side, b))
            for a, b in segments
            if b - a > GAP_EPSILON
        ]


def gaps_for_wall(wall: Wall, openings: list[dict]):
    gaps = []
    for op in openings:
        if op["wall_id"] != wall.id:
            continue
        half = op["width"] / 2.0
        g_start = max(0.0, op["position_from_start"] - half)
        g_end = min(wall.length, op["position_from_start"] + half)
        if g_end > g_start:
            gaps.append((g_start, g_end, op))
    gaps.sort(key=lambda g: g[0])
    return gaps


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


def ensure_dashed_linetype(doc) -> None:
    if AXIS_LINETYPE not in doc.linetypes:
        # Pattern: [toplam_uzunluk, cizgi, -bosluk] - mm olcegine gore secildi.
        doc.linetypes.add(AXIS_LINETYPE, pattern=[750.0, 500.0, -250.0], description="Aks kesikli cizgi")


def add_text(msp, content: str, position, height: float, layer: str, align=TextEntityAlignment.LEFT):
    text = msp.add_text(content, dxfattribs={"layer": layer, "height": height})
    text.set_placement(position, align=align)
    return text


class Sheet:
    """Pafta cercevesi + standart sag-alt kose baslik kutusu (bkz. CLAUDE.md
    'Pafta basligi' standardi). Olcege ve metin yuksekligine gore parametrik;
    hem kat plani hem cephe paftalarinda ayni sekilde kullanilir."""

    def __init__(self, scale: str, text_height: float, margin: float = PAFTA_MARGIN):
        self.scale = scale
        self.text_height = text_height
        self.margin = margin

    def draw(self, msp, dx: float, width: float, y_bottom: float, y_top: float,
              label: str, sheet_note: str | None, sheet_number: int, total_sheets: int) -> None:
        x0, y0 = dx - self.margin, y_bottom - self.margin
        x1, y1 = dx + width + self.margin, y_top + self.margin
        frame = msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], dxfattribs={"layer": "CERCEVE"})
        frame.closed = True

        box_w = min(width * 0.4, 8000.0)
        box_h = self.text_height * 4.4
        bx0, by0, bx1, by1 = x1 - box_w, y0, x1, y0 + box_h
        box = msp.add_lwpolyline([(bx0, by0), (bx1, by0), (bx1, by1), (bx0, by1)], dxfattribs={"layer": "CERCEVE"})
        box.closed = True
        mid_y = by0 + box_h * 0.55
        msp.add_line((bx0, mid_y), (bx1, mid_y), dxfattribs={"layer": "CERCEVE"})

        add_text(msp, label, (bx0 + 150, by1 - 150), self.text_height * 1.2, "METIN", align=TextEntityAlignment.TOP_LEFT)
        sub = f"PAFTA {sheet_number}/{total_sheets} - OLCEK {self.scale}"
        if sheet_note:
            sub += f" - {sheet_note}"
        add_text(msp, sub, (bx0 + 150, mid_y - 150), self.text_height * 0.8, "METIN", align=TextEntityAlignment.TOP_LEFT)


class AxisGrid:
    """Duvar/oda cizimlerinden bagimsiz, binanin tum kat paftalarinda ayni
    konumda tekrarlanan aks (grid) izgarasi. Duesy akslar (sabit X, numerik
    etiketli) plan uzerinde dikey cizgi olarak, ayni sekilde on/arka cephede
    de dikey cizgi olarak izdusurulur; yatay akslar (sabit Y, alfabetik
    etiketli) planda yatay cizgi, sag/sol cephede ise dikey cizgi olarak
    izdusurulur (bkz. CLAUDE.md 'Aks (grid) sistemi')."""

    def __init__(self, vertical_axes: list[dict], horizontal_axes: list[dict], text_height: float):
        self.vertical_axes = vertical_axes
        self.horizontal_axes = horizontal_axes
        self.text_height = text_height

    def _bubble(self, msp, point, label: str) -> None:
        msp.add_circle(point, AXIS_BUBBLE_RADIUS, dxfattribs={"layer": AXIS_LAYER})
        add_text(msp, label, point, self.text_height, AXIS_LAYER, align=TextEntityAlignment.MIDDLE_CENTER)

    def _line_with_bubbles(self, msp, p1, p2, label: str) -> None:
        msp.add_line(p1, p2, dxfattribs={"layer": AXIS_LAYER, "linetype": AXIS_LINETYPE})
        self._bubble(msp, p1, label)
        self._bubble(msp, p2, label)

    def draw_on_floor(self, msp, dx: float, floor_width: float, floor_depth: float) -> None:
        y0, y1 = -AXIS_EXTENSION, floor_depth + AXIS_EXTENSION
        for axis in self.vertical_axes:
            x = dx + axis["position"]
            self._line_with_bubbles(msp, (x, y0), (x, y1), axis["label"])

        x0, x1 = dx - AXIS_EXTENSION, dx + floor_width + AXIS_EXTENSION
        for axis in self.horizontal_axes:
            y = axis["position"]
            self._line_with_bubbles(msp, (x0, y), (x1, y), axis["label"])

    def draw_on_elevation(self, msp, dx: float, axis_source: str | None, y_bottom: float, y_top: float) -> None:
        if axis_source == "vertical":
            axes = self.vertical_axes
        elif axis_source == "horizontal":
            axes = self.horizontal_axes
        else:
            return
        y0, y1 = y_bottom - AXIS_EXTENSION, y_top + AXIS_EXTENSION
        for axis in axes:
            x = dx + axis["position"]
            self._line_with_bubbles(msp, (x, y0), (x, y1), axis["label"])


def draw_wall_network(msp, network: WallNetwork, openings: list[dict]) -> None:
    for wall in network.walls:
        for side in ("pos", "neg"):
            for p1, p2 in network.drawable_rail_segments(wall, side, openings):
                msp.add_line(p1, p2, dxfattribs={"layer": wall.layer})

        perp = wall.normal
        for g_start, g_end, op in gaps_for_wall(wall, openings):
            op_layer = op.get("layer", "KAPI-PENCERE")

            for s in (g_start, g_end):
                msp.add_line(
                    wall.rail_point("pos", s),
                    wall.rail_point("neg", s),
                    dxfattribs={"layer": wall.layer},
                )

            hinge = wall.centerline_point(g_start)
            far = wall.centerline_point(g_end)
            width = g_end - g_start

            if op["type"] == "door":
                leaf_end = vec_add(hinge, vec_scale(perp, width))
                msp.add_line(hinge, leaf_end, dxfattribs={"layer": op_layer})
                start_angle = math.degrees(math.atan2(wall.direction[1], wall.direction[0]))
                end_angle = math.degrees(math.atan2(perp[1], perp[0]))
                msp.add_arc(
                    center=hinge,
                    radius=width,
                    start_angle=min(start_angle, end_angle),
                    end_angle=max(start_angle, end_angle),
                    dxfattribs={"layer": op_layer},
                )
            else:  # window
                offset = wall.thickness / 4.0
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
                      sheet_number: int, total_sheets: int, text_height: float,
                      sheet: Sheet, axis_grid: AxisGrid) -> None:
    tfloor = translate_floor(floor, dx)

    walls = [
        Wall(w["id"], w["start"], w["end"], w["thickness"], w["layer"])
        for w in tfloor["walls"]
    ]
    network = WallNetwork(walls, units)
    draw_wall_network(msp, network, tfloor["openings"])

    room_label_height = room_label_height_for_units(units)
    for room in tfloor["rooms"]:
        draw_room_label(msp, room, room_label_height)

    draw_labels(msp, tfloor["labels"], text_height)

    for counter in tfloor.get("counters", []):
        pl = msp.add_lwpolyline(counter["polygon"], dxfattribs={"layer": counter["layer"]})
        pl.closed = True

    for marking in tfloor.get("markings", []):
        msp.add_line(marking["start"], marking["end"], dxfattribs={"layer": marking["layer"]})

    axis_grid.draw_on_floor(msp, dx, floor_width, floor_depth)

    sheet.draw(
        msp, dx, floor_width, 0.0, floor_depth, floor["label"], floor.get("sheet_note"),
        sheet_number, total_sheets,
    )


def elevation_vertical_extent(elevation: dict) -> tuple[float, float]:
    levels = elevation["levels"]
    total_below = sum(l["height"] for l in levels if l.get("below_ground"))
    total_above = sum(l["height"] for l in levels if not l.get("below_ground"))
    extra = 0.0
    for l in levels:
        if l.get("machine_room"):
            extra = max(extra, l["height"] * 0.8)
    return -total_below, total_above + extra


def draw_elevation(msp, elevation: dict, dx: float, text_height: float, axis_grid: AxisGrid) -> None:
    width = elevation["width"]
    levels = elevation["levels"]

    total_below = sum(l["height"] for l in levels if l.get("below_ground"))
    cursor = -total_below

    for level in levels:
        y0 = cursor
        y1 = cursor + level["height"]
        cursor = y1

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
            msp, level["label"], (dx - 200, (y0 + y1) / 2.0), text_height, "METIN",
            align=TextEntityAlignment.MIDDLE_RIGHT,
        )

    msp.add_line((dx - 1000, 0), (dx + width + 1000, 0), dxfattribs={"layer": "OLCU"})
    add_text(
        msp, "+-0.00 ZEMIN", (dx - 200, 150.0), text_height * 0.8, "OLCU",
        align=TextEntityAlignment.MIDDLE_RIGHT,
    )

    y_bottom, y_top = -total_below, cursor
    axis_grid.draw_on_elevation(msp, dx, elevation.get("axis_source"), y_bottom, y_top)


def generate(context_path: Path = DEFAULT_CONTEXT_PATH, output_path: Path = DEFAULT_OUTPUT_PATH) -> Path:
    context = load_json(context_path)
    units = context["meta"]["units"]
    floor_width = context["meta"]["floor_width"]
    floor_depth = context["meta"]["floor_depth"]
    sheet_gap = context["meta"].get("sheet_gap", 3000.0)

    doc = ezdxf.new(dxfversion="R2010")
    doc.header["$INSUNITS"] = ezdxf.units.MM if units == "mm" else ezdxf.units.M
    setup_layers(doc, context["layers"])
    ensure_dashed_linetype(doc)
    msp = doc.modelspace()

    floors = context["floors"]
    elevations = context["elevations"]
    total_sheets = len(floors) + len(elevations)
    text_height = text_height_for_units(units)

    scale = context["meta"].get("scale", "1:100")
    sheet = Sheet(scale, text_height)
    grid = context["grid"]
    axis_grid = AxisGrid(grid["vertical_axes"], grid["horizontal_axes"], text_height)

    cursor = 0.0
    for i, floor in enumerate(floors, start=1):
        draw_floor_sheet(msp, floor, cursor, units, floor_width, floor_depth, i, total_sheets, text_height, sheet, axis_grid)
        cursor += floor_width + sheet_gap

    for j, elevation in enumerate(elevations, start=1):
        y_bottom, y_top = elevation_vertical_extent(elevation)
        draw_elevation(msp, elevation, cursor, text_height, axis_grid)
        sheet.draw(
            msp, cursor, elevation["width"], y_bottom, y_top, elevation["label"], None,
            len(floors) + j, total_sheets,
        )
        cursor += elevation["width"] + sheet_gap

    output_path.parent.mkdir(parents=True, exist_ok=True)
    return save_with_fallback(lambda p: doc.saveas(p), output_path)


def main() -> int:
    context_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CONTEXT_PATH
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_OUTPUT_PATH
    result = generate(context_path, output_path)
    print(f"DXF uretildi: {result}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
