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
  3b) ACIKCA bildirilmis her kesit (sections[], DEV-021) icin: levels_from
      gecerli bir elevation'a isaret ediyor mu, o elevation'in seviye sayisi
      floors[] sayisiyla esit mi, position bina siniri icinde mi.
  3c) Her merdiven (stairs[], DEV-022) icin: room_id gecerli bir odaya isaret
      ediyor mu, scripts/stairs::resolve_stair (cizim koduyla AYNI TEK
      kaynak) HATA (sigmayan/gecersiz) uretiyor mu; esnetme UYARILARI
      bloklamaz, basilir.
  4) SURUM KAPISI (DEV-020): meta.schema_version ile sistemin SCHEMA_VERSION'u
     arasinda MAJOR fark varsa uretim DURUR. Bkz. scripts/version.py.
  5) CAKISMA DENETIMI (DEV-019): moduller arasi girisim - tefris odanin
     disinda mi, duvara/kolona/kapi acilim yayina giriyor mu. Cift ("iki
     FARKLI eleman ayni yeri mi isgal ediyor") kontroller scripts/collision/
     motorunda yasar; bu dosyadaki check_* fonksiyonlari ise TEKIL ("kendi
     verim gecerli mi") kontrollerdir. Ayrim ARITEDIR, bkz. DEV-019.

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
SCRIPTS_ROOT = Path(__file__).resolve().parent
SCHEMA_PATH = PROJECT_ROOT / "schema" / "design.schema.json"
DEFAULT_CONTEXT_PATH = PROJECT_ROOT / "context.json"

sys.path.insert(0, str(SCRIPTS_ROOT))
# Poligon matematiginin TEK sahibi collision.geometry'dir. rev-12'den once
# ayni Sutherland-Hodgman kirpmasinin bir KOPYASI burada duruyordu; iki kopya
# zamanla ayrisir ve "oda cakismasi" ile "tefris cakismasi" farkli cevaplar
# vermeye baslardi.
from axis import check_labels as check_axis_labels  # noqa: E402
from collision import check_context as check_collisions  # noqa: E402
from collision.geometry import (  # noqa: E402
    polygon_intersection_area,
    shoelace_area,
)
from version import (  # noqa: E402
    SCHEMA_VERSION,
    check_compatibility,
    project_schema_version,
)
from stairs import StairFitError, resolve_stair  # noqa: E402
from walls import WallCatalog  # noqa: E402

AREA_TOLERANCE_RATIO = 0.03  # oda alani vs poligon alani icin tolerans


def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_schema(context: dict, schema: dict) -> list[str]:
    validator = jsonschema.Draft7Validator(schema)
    errors = sorted(validator.iter_errors(context), key=lambda e: list(e.path))
    return [f"Schema hatasi at {'/'.join(str(p) for p in e.path) or '<root>'}: {e.message}" for e in errors]


def to_m2(raw_area: float, units: str) -> float:
    if units == "mm":
        return raw_area / 1_000_000.0
    if units == "m":
        return raw_area
    raise ValueError(f"Bilinmeyen birim: {units}")


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

    # Mahal no, kat icinde benzersiz olmali: kat kodu ile birleserek proje
    # genelinde tekil bir mahal kimligi olusturur (orn. 'ZK-04').
    seen_numbers: dict[str, str] = {}
    for room in rooms:
        number = str(room.get("no", "") or "").strip()
        if not number:
            continue
        if number in seen_numbers:
            errors.append(
                f"Mahal no '{number}' ayni katta iki kez kullanilmis: "
                f"'{seen_numbers[number]}' ve '{room['id']}'."
            )
        else:
            seen_numbers[number] = room["id"]

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

    # DEV-014: 'kind' bildirilmisse KATALOGDA TANIMLI olmali. Aksi halde
    # bir yazim hatasi (orn. 'tugla_blome') SESSIZCE duz duvar olarak
    # cizilirdi - CatalogRailStandard bilinmeyen kind'i fallback'e dusurur,
    # hata vermez. Bu, arite-1 (kendi verim gecerli mi) bir kontroldur.
    known_kinds = {spec.id for spec in WallCatalog().kinds()}
    for wall in walls:
        kind = wall.get("kind")
        if kind is not None and kind not in known_kinds:
            errors.append(
                f"Duvar '{wall['id']}': bilinmeyen kind '{kind}'. "
                f"Tanimli turler: {', '.join(sorted(known_kinds))}."
            )

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


def check_stairs(floor: dict) -> tuple[list[str], list[str]]:
    """Arity-1 (DEV-022): `stairs[].room_id` bu kattaki bir odaya isaret
    ediyor mu, ve `resolve_stair` (cizim koduyla AYNI TEK kaynak, bkz.
    scripts/stairs/CLAUDE.md) HATA/UYARI uretiyor mu. Ayri bir hesap
    YAZMAZ - `resolve_stair`i CAGIRIR, sonucunu yorumlar."""
    errors: list[str] = []
    warnings: list[str] = []
    rooms_by_id = {r["id"]: r for r in floor.get("rooms", [])}
    for spec in floor.get("stairs", []):
        room = rooms_by_id.get(spec["room_id"])
        if room is None:
            errors.append(
                f"Merdiven '{spec['id']}', bu kattaki gecersiz bir oda id'sine "
                f"referans veriyor: '{spec['room_id']}'."
            )
            continue
        try:
            resolution = resolve_stair(spec, room["polygon"])
        except StairFitError as exc:
            errors.append(str(exc))
            continue
        warnings.extend(resolution.warnings)
    return errors, warnings


def check_floor_codes(floors: list[dict]) -> list[str]:
    """Kat kodlari (floors[].code) birbirinden farkli olmali; ayni kod iki
    katta kullanilirsa mahal kimligi ('ZK-04') artik benzersiz olmaz."""
    errors: list[str] = []
    seen: dict[str, str] = {}
    for floor in floors:
        code = str(floor.get("code", "") or "").strip()
        if not code:
            continue
        if code in seen:
            errors.append(
                f"Kat kodu '{code}' iki katta kullanilmis: "
                f"'{seen[code]}' ve '{floor['id']}'."
            )
        else:
            seen[code] = floor["id"]
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


def check_sections(context: dict) -> list[str]:
    """DEV-021. `context['sections']` HIC verilmemisse (anahtar yok) kontrol
    ATLANIR - o durumda `resolve_sections` sistem varsayilanini uretir ve
    zaten gecerli oldugu GARANTIDIR (kullanici verisi degil). ACIKCA
    verilmis (bos dizi dahil) her kesit icin: (1) levels_from gecerli bir
    elevations[].id'ye isaret etmeli, (2) o elevation'in seviye SAYISI,
    floors[] SAYISIYLA birebir esit olmalidir - kat<->seviye eslesmesi
    SIRAYLA (asagidan yukariya) yapildigi icin (bkz. scripts/sections/
    CLAUDE.md), boy uyusmazligi kati YANLIS seviyeye baglar ve bu SESSIZ bir
    hata olurdu. (3) position, bildirilmisse ilgili kenarin [0, span]
    araligi ICINDE olmalidir - yapinin disinda bir kesit anlamsizdir."""
    errors: list[str] = []
    raw = context.get("sections")
    if raw is None:
        return errors

    elevations_by_id = {e["id"]: e for e in context["elevations"]}
    default_levels_from = context["elevations"][0]["id"] if context["elevations"] else None
    floor_width = context["meta"]["floor_width"]
    floor_depth = context["meta"]["floor_depth"]
    num_floors = len(context["floors"])

    seen_ids: set[str] = set()
    for data in raw:
        prefix = f"[{data['id']}] "
        if data["id"] in seen_ids:
            errors.append(prefix + "kesit id'si ayni context icinde tekrarlanmis.")
        seen_ids.add(data["id"])

        levels_from = data.get("levels_from") or default_levels_from
        if levels_from is None or levels_from not in elevations_by_id:
            errors.append(prefix + f"levels_from '{levels_from}' gecerli bir elevations[].id degil.")
            continue
        target_levels = elevations_by_id[levels_from]["levels"]
        if len(target_levels) != num_floors:
            errors.append(
                prefix + f"levels_from='{levels_from}' {len(target_levels)} seviye tasiyor "
                f"ama floors[] {num_floors} kat iceriyor - kat<->seviye eslesmesi SIRAYLA "
                f"yapildigi icin bu ikisi AYNI boyda olmalidir."
            )

        axis_source = data["axis_source"]
        span = floor_depth if axis_source == "vertical" else floor_width
        position = data.get("position")
        if position is not None and not (0.0 <= position <= span):
            errors.append(
                prefix + f"position {position}, gecerli aralik [0, {span}] disinda "
                f"(axis_source='{axis_source}')."
            )
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

    # --- Surum kapisi (DEV-020): schema gectikten SONRA, geometriden ONCE.
    version_errors, version_warnings = check_compatibility(context)
    for warning in version_warnings:
        print(f"UYARI (surum): {warning}")
    if version_errors:
        print("DOGRULAMA BASARISIZ (surum uyumu):")
        for e in version_errors:
            print(f"  - {e}")
        return False

    units = context["meta"]["units"]
    all_errors: list[str] = []

    all_errors += check_floor_codes(context["floors"])
    # Aks etiketleme kurali (DEV-015): dusey numerik, yatay alfabetik, ara aks
    # kesme isaretiyle. '1A' yasaktir - yatay aks ailesiyle ve kolon
    # adlandirmasiyla (B2) carpisir.
    all_errors += check_axis_labels(context["grid"]["vertical_axes"],
                                    context["grid"]["horizontal_axes"])

    stair_warnings: list[str] = []
    for floor in context["floors"]:
        all_errors += check_floor(units, floor)
        floor_stair_errors, floor_stair_warnings = check_stairs(floor)
        all_errors += [f"[{floor['id']}] " + e for e in floor_stair_errors]
        stair_warnings += [f"[{floor['id']}] " + w for w in floor_stair_warnings]

    for elevation in context["elevations"]:
        all_errors += check_elevation(elevation)

    all_errors += check_sections(context)

    for warning in stair_warnings:
        print(f"UYARI (merdiven): {warning}")

    if all_errors:
        print("DOGRULAMA BASARISIZ (geometri/mantik):")
        for e in all_errors:
            print(f"  - {e}")
        return False

    # --- Cakisma denetimi (DEV-019): moduller arasi girisim.
    # Bilincli olarak EN SONDA calisir: tekil geometri bozuksa (kapanmayan
    # duvar agi, gecersiz poligon) cakisma raporu zaten anlamsiz olurdu.
    clash_report = check_collisions(context)
    for line in clash_report.warning_lines():
        print(f"UYARI (cakisma): {line}")
    if not clash_report.ok:
        print("DOGRULAMA BASARISIZ (cakisma):")
        for line in clash_report.error_lines():
            print(f"  - {line}")
        return False

    declared, _ = project_schema_version(context)
    print(
        f"DOGRULAMA BASARILI: context.json semaya uygun (schema_version "
        f"{declared} / sistem {SCHEMA_VERSION}), "
        f"{len(context['floors'])} kat + {len(context['elevations'])} cephe saglik "
        f"kontrollerinden ve cakisma denetiminden gecti "
        f"({len(clash_report.warnings)} uyari)."
    )
    return True


def main() -> int:
    context_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CONTEXT_PATH
    ok = run_validation(context_path)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
