#!/usr/bin/env python3
"""context.json dogrulama scripti.

Kullanim:
    python scripts/validate.py [context.json yolu]

Yaptigi kontroller:
  1) JSON Schema dogrulamasi (schema/design.schema.json)
  2) Her kat (floors[]) icin geometrik / mantiksal saglik kontrolleri:
     - Her oda poligonu en az 3 nokta iceriyor mu
     - Beyan edilen oda alani (area_m2), poligondan hesaplanan alanla tutarli mi
     - Duvar agi sarkan (baglantisiz) uc icermeden kapali bir yapi olusturuyor mu
       (kose VE T-kesisimi taniniyor)
     - Her kapi/pencere, var olan bir duvara (wall_id) referans veriyor mu ve
       genisligi o duvarin uzunlugundan kucuk mu, duvar sinirlari icinde mi
     - Iki oda poligonu birbiriyle cakisiyor mu (convex/dikdortgen varsayimiyla)
  3) Her cephe gorunusu (elevations[]) icin hafif tutarlilik kontrolleri.

Cikis kodu: basarili -> 0, basarisiz -> 1.
Bu script FAIL ile bitiyorsa generate_dxf.py CALISTIRILMAMALIDIR.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "jsonschema"])
    import jsonschema

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = PROJECT_ROOT / "schema" / "design.schema.json"
DEFAULT_CONTEXT_PATH = PROJECT_ROOT / "context.json"

AREA_TOLERANCE_RATIO = 0.03  # oda alani vs poligon alani icin tolerans


def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_schema(context: dict, schema: dict) -> list[str]:
    validator = jsonschema.Draft7Validator(schema)
    errors = sorted(validator.iter_errors(context), key=lambda e: list(e.path))
    return [f"Schema hatasi at {'/'.join(str(p) for p in e.path) or '<root>'}: {e.message}" for e in errors]


def shoelace_area(polygon: list[list[float]]) -> float:
    n = len(polygon)
    if n < 3:
        return 0.0
    total = 0.0
    for i in range(n):
        x1, y1 = polygon[i]
        x2, y2 = polygon[(i + 1) % n]
        total += x1 * y2 - x2 * y1
    return abs(total) / 2.0


def to_m2(raw_area: float, units: str) -> float:
    if units == "mm":
        return raw_area / 1_000_000.0
    if units == "m":
        return raw_area
    raise ValueError(f"Bilinmeyen birim: {units}")


def polygon_intersection_area(subject: list[list[float]], clip: list[list[float]]) -> float:
    """Sutherland-Hodgman polygon clipping ile kesisim alani.

    NOT: `clip` poligonunun convex (disbukey) olmasi gerekir. Bu araçtaki
    odalar tipik olarak dikdortgen/convex kabul edilir; karmasik ic-bukey
    oda seklinde yanlis-negatif verebilir.
    """

    def inside(p, a, b):
        return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]) >= 0

    def intersect(p1, p2, a, b):
        a1 = (b[0] - a[0]) * (p1[1] - a[1]) - (b[1] - a[1]) * (p1[0] - a[0])
        a2 = (b[0] - a[0]) * (p2[1] - a[1]) - (b[1] - a[1]) * (p2[0] - a[0])
        t = a1 / (a1 - a2)
        return [p1[0] + t * (p2[0] - p1[0]), p1[1] + t * (p2[1] - p1[1])]

    output = list(subject)
    clip_area_signed = 0.0
    for i in range(len(clip)):
        x1, y1 = clip[i]
        x2, y2 = clip[(i + 1) % len(clip)]
        clip_area_signed += x1 * y2 - x2 * y1
    clip_pts = clip if clip_area_signed >= 0 else list(reversed(clip))

    for i in range(len(clip_pts)):
        if not output:
            break
        a = clip_pts[i]
        b = clip_pts[(i + 1) % len(clip_pts)]
        input_list = output
        output = []
        for j in range(len(input_list)):
            current = input_list[j]
            prev = input_list[j - 1]
            current_in = inside(current, a, b)
            prev_in = inside(prev, a, b)
            if current_in:
                if not prev_in:
                    output.append(intersect(prev, current, a, b))
                output.append(current)
            elif prev_in:
                output.append(intersect(prev, current, a, b))
    if len(output) < 3:
        return 0.0
    return shoelace_area(output)


def round_point(pt: list[float], units: str) -> tuple[float, float]:
    precision = 1 if units == "mm" else 4
    return (round(pt[0], precision), round(pt[1], precision))


def point_on_segment(pt, seg_a, seg_b, tol: float) -> bool:
    """pt, (seg_a -> seg_b) dogru parcasinin uzerinde mi (T-kesisimi dahil)?"""
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


def check_rooms(units: str, rooms: list[dict]) -> list[str]:
    errors: list[str] = []

    for room in rooms:
        if len(room["polygon"]) < 3:
            errors.append(f"Oda '{room['id']}' poligonu en az 3 nokta icermeli.")
            continue
        computed_m2 = to_m2(shoelace_area(room["polygon"]), units)
        declared_m2 = room["area_m2"]
        if declared_m2 <= 0:
            errors.append(f"Oda '{room['id']}' icin area_m2 pozitif olmali.")
            continue
        diff_ratio = abs(computed_m2 - declared_m2) / declared_m2
        if diff_ratio > AREA_TOLERANCE_RATIO:
            errors.append(
                f"Oda '{room['id']}': beyan edilen alan {declared_m2:.2f} m^2, "
                f"poligondan hesaplanan alan {computed_m2:.2f} m^2 ile tutarsiz "
                f"(fark %{diff_ratio*100:.1f}, tolerans %{AREA_TOLERANCE_RATIO*100:.0f})."
            )

    for i in range(len(rooms)):
        for j in range(i + 1, len(rooms)):
            r1, r2 = rooms[i], rooms[j]
            if len(r1["polygon"]) < 3 or len(r2["polygon"]) < 3:
                continue
            inter_m2 = to_m2(polygon_intersection_area(r1["polygon"], r2["polygon"]), units)
            if inter_m2 > 0.01:
                errors.append(
                    f"Oda '{r1['id']}' ile '{r2['id']}' cakisiyor "
                    f"(kesisim alani ~{inter_m2:.2f} m^2)."
                )

    return errors


def check_walls(units: str, walls: list[dict]) -> list[str]:
    errors: list[str] = []

    if not walls:
        return errors

    tol = 1.0 if units == "mm" else 0.001

    endpoint_count: dict[tuple[float, float], int] = {}
    for wall in walls:
        for pt in (wall["start"], wall["end"]):
            key = round_point(pt, units)
            endpoint_count[key] = endpoint_count.get(key, 0) + 1

    for wall in walls:
        for pt in (wall["start"], wall["end"]):
            key = round_point(pt, units)
            if endpoint_count[key] >= 2:
                continue
            supported = any(
                other["id"] != wall["id"] and point_on_segment(pt, other["start"], other["end"], tol)
                for other in walls
            )
            if not supported:
                errors.append(
                    f"Duvar '{wall['id']}' ucu ({pt[0]}, {pt[1]}) baska hicbir "
                    f"duvara (kose veya T-kesisimi olarak) baglanmiyor (sarkan uc)."
                )

    for wall in walls:
        length = ((wall["end"][0] - wall["start"][0]) ** 2 + (wall["end"][1] - wall["start"][1]) ** 2) ** 0.5
        if length <= 0:
            errors.append(f"Duvar '{wall['id']}' sifir uzunlukta.")

    return errors


def check_openings(openings: list[dict], walls: list[dict]) -> list[str]:
    errors: list[str] = []
    walls_by_id = {w["id"]: w for w in walls}

    for opening in openings:
        wall = walls_by_id.get(opening["wall_id"])
        if wall is None:
            errors.append(
                f"Kapi/pencere '{opening['id']}', var olmayan duvar id'sine "
                f"referans veriyor: '{opening['wall_id']}'."
            )
            continue
        wall_length = ((wall["end"][0] - wall["start"][0]) ** 2 + (wall["end"][1] - wall["start"][1]) ** 2) ** 0.5
        if opening["width"] >= wall_length:
            errors.append(
                f"Kapi/pencere '{opening['id']}' genisligi ({opening['width']}) "
                f"ait oldugu duvarin ('{wall['id']}') uzunlugundan "
                f"({wall_length:.1f}) buyuk veya esit olamaz."
            )
        half_width = opening["width"] / 2.0
        pos = opening["position_from_start"]
        if pos - half_width < 0 or pos + half_width > wall_length:
            errors.append(
                f"Kapi/pencere '{opening['id']}' duvar ('{wall['id']}') "
                f"sinirlarinin disina tasiyor (position_from_start={pos}, "
                f"width={opening['width']}, duvar uzunlugu={wall_length:.1f})."
            )

    return errors


def check_floor(units: str, floor: dict) -> list[str]:
    errors: list[str] = []
    prefix = f"[{floor['id']}] "
    errors += [prefix + e for e in check_rooms(units, floor["rooms"])]
    errors += [prefix + e for e in check_walls(units, floor["walls"])]
    errors += [prefix + e for e in check_openings(floor["openings"], floor["walls"])]
    return errors


def check_elevation(elevation: dict) -> list[str]:
    errors: list[str] = []
    prefix = f"[{elevation['id']}] "
    if not elevation["levels"]:
        errors.append(prefix + "en az bir seviye (levels) tanimlanmali.")
    for level in elevation["levels"]:
        if level["height"] <= 0:
            errors.append(prefix + f"seviye '{level['label']}' yuksekligi pozitif olmali.")
    return errors


def run_validation(context_path: Path = DEFAULT_CONTEXT_PATH) -> bool:
    context = load_json(context_path)
    schema = load_json(SCHEMA_PATH)

    schema_errors = validate_schema(context, schema)
    if schema_errors:
        print("DOGRULAMA BASARISIZ (schema):")
        for e in schema_errors:
            print(f"  - {e}")
        return False

    units = context["meta"]["units"]
    all_errors: list[str] = []

    for floor in context["floors"]:
        all_errors += check_floor(units, floor)

    for elevation in context["elevations"]:
        all_errors += check_elevation(elevation)

    if all_errors:
        print("DOGRULAMA BASARISIZ (geometri/mantik):")
        for e in all_errors:
            print(f"  - {e}")
        return False

    print(
        f"DOGRULAMA BASARILI: context.json semaya uygun, "
        f"{len(context['floors'])} kat + {len(context['elevations'])} cephe saglik kontrollerinden gecti."
    )
    return True


def main() -> int:
    context_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CONTEXT_PATH
    ok = run_validation(context_path)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
