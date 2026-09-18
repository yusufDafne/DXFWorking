#!/usr/bin/env python3
"""context.json dogrulama scripti.

Kullanim:
    python scripts/validate.py [context.json yolu]

Yaptigi kontroller:
  1) JSON Schema dogrulamasi (schema/design.schema.json)
  2) Geometrik / mantiksal saglik kontrolleri:
     - Her oda poligonu en az 3 nokta iceriyor mu
     - Beyan edilen oda alani (area_m2), poligondan hesaplanan alanla tutarli mi
     - Oda alanlari toplami, meta.target_total_area_m2 ile tutarli mi (varsa)
     - Duvar agi sarkan (baglantisiz) uc icermeden kapali bir yapi olusturuyor mu
     - Her kapi/pencere, var olan bir duvara (wall_id) referans veriyor mu ve
       genisligi o duvarin uzunlugundan kucuk mu
     - Iki oda poligonu birbiriyle cakisiyor mu (convex/dikdortgen varsayimiyla)

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

AREA_TOLERANCE_RATIO = 0.03       # oda alani vs poligon alani icin toleransi
TOTAL_AREA_TOLERANCE_RATIO = 0.05  # toplam alan vs hedef alan icin tolerans


class ValidationError(Exception):
    pass


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
    raise ValidationError(f"Bilinmeyen birim: {units}")


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
    # clip poligonunun yonunu (CCW) garanti et; degilse ters cevir
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


def check_rooms(context: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    units = context["meta"]["units"]
    rooms = context["rooms"]

    for room in rooms:
        if len(room["polygon"]) < 3:
            errors.append(f"Oda '{room['id']}' poligonu en az 3 nokta icermeli.")
            continue
        computed_raw = shoelace_area(room["polygon"])
        computed_m2 = to_m2(computed_raw, units)
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

    # Oda alanlari toplami vs hedef toplam alan
    target = context["meta"].get("target_total_area_m2")
    if target:
        total_declared = sum(r["area_m2"] for r in rooms)
        if total_declared > 0:
            diff_ratio = abs(total_declared - target) / target
            if diff_ratio > TOTAL_AREA_TOLERANCE_RATIO:
                errors.append(
                    f"Oda alanlari toplami {total_declared:.2f} m^2, hedef toplam alan "
                    f"{target:.2f} m^2 ile tutarsiz (fark %{diff_ratio*100:.1f}, "
                    f"tolerans %{TOTAL_AREA_TOLERANCE_RATIO*100:.0f})."
                )

    # Oda cakismalari (convex/dikdortgen varsayimiyla)
    for i in range(len(rooms)):
        for j in range(i + 1, len(rooms)):
            r1, r2 = rooms[i], rooms[j]
            if len(r1["polygon"]) < 3 or len(r2["polygon"]) < 3:
                continue
            inter_raw = polygon_intersection_area(r1["polygon"], r2["polygon"])
            inter_m2 = to_m2(inter_raw, units)
            if inter_m2 > 0.01:  # 0.01 m^2'den buyuk kesisimler cakisma sayilir
                errors.append(
                    f"Oda '{r1['id']}' ile '{r2['id']}' cakisiyor "
                    f"(kesisim alani ~{inter_m2:.2f} m^2)."
                )

    return errors, warnings


def check_walls(context: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    units = context["meta"]["units"]
    walls = context["walls"]

    if not walls:
        warnings.append("Hic duvar tanimlanmamis.")
        return errors, warnings

    # Sarkan uc (dangling endpoint) kontrolu: her duvar ucu en az bir baska
    # duvarla paylasilmali (derece >= 2), aksi halde poligon kapali degildir.
    endpoint_count: dict[tuple[float, float], int] = {}
    for wall in walls:
        for pt in (wall["start"], wall["end"]):
            key = round_point(pt, units)
            endpoint_count[key] = endpoint_count.get(key, 0) + 1

    dangling = [pt for pt, count in endpoint_count.items() if count < 2]
    if dangling:
        pts_str = ", ".join(f"({x}, {y})" for x, y in dangling)
        errors.append(
            f"Duvar agi kapali degil: su noktalarda baglantisiz (sarkan) duvar "
            f"ucu var: {pts_str}."
        )

    # Sifir uzunluklu duvar kontrolu
    for wall in walls:
        length = ((wall["end"][0] - wall["start"][0]) ** 2 + (wall["end"][1] - wall["start"][1]) ** 2) ** 0.5
        if length <= 0:
            errors.append(f"Duvar '{wall['id']}' sifir uzunlukta.")

    return errors, warnings


def check_openings(context: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    walls_by_id = {w["id"]: w for w in context["walls"]}

    for opening in context["openings"]:
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

    return errors, warnings


def run_validation(context_path: Path = DEFAULT_CONTEXT_PATH) -> bool:
    context = load_json(context_path)
    schema = load_json(SCHEMA_PATH)

    schema_errors = validate_schema(context, schema)
    if schema_errors:
        print("DOGRULAMA BASARISIZ (schema):")
        for e in schema_errors:
            print(f"  - {e}")
        return False

    all_errors: list[str] = []
    all_warnings: list[str] = []

    for check in (check_rooms, check_walls, check_openings):
        errors, warnings = check(context)
        all_errors.extend(errors)
        all_warnings.extend(warnings)

    if all_warnings:
        print("UYARILAR:")
        for w in all_warnings:
            print(f"  - {w}")

    if all_errors:
        print("DOGRULAMA BASARISIZ (geometri/mantik):")
        for e in all_errors:
            print(f"  - {e}")
        return False

    print("DOGRULAMA BASARILI: context.json semaya ve saglik kontrollerine uygun.")
    return True


def main() -> int:
    context_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CONTEXT_PATH
    ok = run_validation(context_path)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
