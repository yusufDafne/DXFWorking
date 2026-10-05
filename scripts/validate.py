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
       (kose VE T-kesisimi taniniyor); bir T-kesisim, kesistigi duvarin bir
       kapi/pencere BOSLUGUNA denk gelmiyor mu (DEV-041 - duvar kapinin
       ORTASINDA "havada" bitemez, walls.gaps_for_wall ile denetlenir)
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
  3d) SARTNAME/ORANSAL MAHAL KURALLARI (DEV-036, scripts/standards): bir
      odaya `room_type` VERILMISSE (opt-in) STANDARDS'ta TANIMLI olmali
      (aksi HATA - yazim hatasi korumasi); en-boy orani/asgari kisa kenar/
      asgari alan esik DISINDAYSA bu HER ZAMAN UYARIdir - kullanici karari
      geregi uretimi DURDURMAZ.
  3e) ILISKISEL/MIMARI MANTIK KURALLARI (DEV-039, scripts/architect):
      arity-2+ kontroller - kapi-cekirdek dengesizligi, giris-wc goru
      hatti, hol/sirkulasyon alan payi (birim-ici VE ortak/bina-seviyesi,
      DEV-045), yatak odasi-salon komsulugu, islak hacmin yatak
      odasindan GECMEDEN erisilebilir olmasi (DEV-042), islak hacim
      kapilarinin birbirine yakinligi (DEV-043).
      `rooms[].unit_id` OPT-IN'dir; hic verilmezse bu kontroller SESSIZCE
      atlanir. standards ile AYNI politika: HER ZAMAN UYARI, asla HATA.
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
from shafts import check_shafts, check_shafts_across_floors  # noqa: E402
from stairs import (  # noqa: E402
    StairFitError, exit_door_alignment_warning, resolve_stair, stair_access_warnings,
)
from standards import (  # noqa: E402
    check_door_corridor_nuances,
    check_room_proportions,
    check_core_rectangular,
    check_room_types,
    edge_wall_thicknesses,
    net_area,
)
from architect import (  # noqa: E402
    check_bedroom_via_corridor,
    check_circulation_area_share,
    check_common_circulation_share,
    check_door_core_balance,
    check_door_window_nuances,
    check_entry_sightlines,
    check_wet_area_door_proximity,
    check_wet_area_reachable_without_bedroom,
)
from openings import check_elevator_door_insets, check_opening_nuances  # noqa: E402
from walls import Wall, WallCatalog, check_wall_thickness, gaps_for_wall  # noqa: E402

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


def point_position_on_segment(pt, seg_a, seg_b, tol: float) -> float | None:
    """`point_on_segment`in AYNI testi ama BOOLEAN yerine, nokta segment
    UZERINDEYSE `seg_a`dan ITIBAREN mm cinsinden mesafeyi (s) doner;
    degilse None. DEV-041: bir T-kesisim NOKTASININ, kesistigi duvarin
    HANGI konumuna denk geldigini bulmak icin (sonra o konumun bir kapi/
    pencere BOSLUGUNA denk gelip gelmedigini kontrol edebilmek icin)
    kullanilir - `point_on_segment`in KENDISI DEGISTIRILMEDI (geriye
    donuk uyumluluk), bu YENI bir kardes fonksiyondur."""
    ax, ay = seg_a
    bx, by = seg_b
    px, py = pt
    abx, aby = bx - ax, by - ay
    seg_len = (abx ** 2 + aby ** 2) ** 0.5
    if seg_len == 0:
        return None
    apx, apy = px - ax, py - ay
    cross = abx * apy - aby * apx
    dist = abs(cross) / seg_len
    if dist > tol:
        return None
    t = (apx * abx + apy * aby) / (seg_len ** 2)
    if not (-1e-6 <= t <= 1 + 1e-6):
        return None
    return t * seg_len


def wall_gap_ranges(wall_dict: dict, openings: list[dict]) -> list[tuple[float, float]]:
    """Bir duvarin kapi/pencere ACIKLIK araliklarini (s cinsinden, [0,
    duvar_uzunlugu] icinde) dondurur - `walls.gaps_for_wall`in (duvar
    aciklik hesabinin TEK kaynagi, bkz. openings/CLAUDE.md) DOGRUDAN
    yeniden kullanimidir, ikinci bir aciklik-hesaplama YAZILMAZ (rev-13
    swing-geometri dersiyle AYNI disiplin)."""
    wall_obj = Wall.from_context(wall_dict, WallCatalog())
    return [(g_start, g_end) for g_start, g_end, _opening in gaps_for_wall(wall_obj, openings)]


def check_rooms(units: str, rooms: list[dict], walls: list[dict] | None = None) -> list[str]:
    """`area_m2`, oda poligonunun BRUT (merkez cizgisi) alanina VEYA - `walls`
    verilmisse - duvar IC YUZLERI arasi NET alanina esit olmalidir (+-%3).
    Kullanici karari (2026-10-05, rev-24): mahal alani NET yazilir."""
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
        net_m2 = None
        if walls:
            thickness = edge_wall_thicknesses(room["polygon"], walls)
            if any(thickness):
                net_m2 = to_m2(net_area(room["polygon"], thickness), units)
        net_ok = net_m2 is not None and abs(net_m2 - declared_m2) / declared_m2 <= AREA_TOLERANCE_RATIO
        if diff_ratio > AREA_TOLERANCE_RATIO and not net_ok:
            net_note = f" (duvar ic yuzleri arasi net {net_m2:.2f} m^2)" if net_m2 is not None else ""
            errors.append(
                f"Oda '{room['id']}': beyan edilen alan {declared_m2:.2f} m^2, "
                f"poligondan hesaplanan alan {computed_m2:.2f} m^2{net_note} ile tutarsiz "
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


def check_walls(units: str, walls: list[dict], openings: list[dict] | None = None) -> list[str]:
    errors: list[str] = []

    if not walls:
        return errors

    openings = openings or []
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
            supported = False
            blocked_by_gap = False
            for other in walls:
                if other["id"] == wall["id"]:
                    continue
                s = point_position_on_segment(pt, other["start"], other["end"], tol)
                if s is None:
                    continue
                # DEV-041: bir T-kesisim, kesistigi duvarin DOLU (malzeme)
                # kismina degil bir kapi/pencere BOSLUGUNA denk geliyorsa
                # bu GECERLI bir baglanti DEGILDIR - gorsel olarak duvar
                # kapinin ORTASINDA "havada" biter (rev-22'de GERCEKTEN
                # olan bir hata, bkz. scripts/walls/CLAUDE.md "Bilinen
                # sinirlar"). Boslugun TAM SINIRINA (jamb) denk gelmek
                # (esitlik) GECERLIDIR - yalnizca KESIN ICERIDE (s bir
                # aciklik araliginin ICINDE) ise BOSLUGA baglaniyor sayilir.
                if any(g_start < s < g_end for g_start, g_end in wall_gap_ranges(other, openings)):
                    blocked_by_gap = True
                    continue
                supported = True
                break
            if not supported:
                if blocked_by_gap:
                    errors.append(
                        f"Duvar '{wall['id']}' ucu ({pt[0]}, {pt[1]}) bir kapi/pencere "
                        f"BOSLUGUNA baglaniyor - bu gecerli bir baglanti degildir (duvar "
                        f"kapinin/pencerenin ORTASINDA 'havada' bitiyor)."
                    )
                else:
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


def _entry_edge_open(resolution, walls: list[dict]) -> bool:
    """Merdivenin giris kenarinda (oda bbox kenari) HIC duvar yoksa True: merdiven kat
    holune tam genislikte ACIKTIR (kullanici karari rev-27: merdiven duvarinda 10 cm
    cikinti/kapi mantigi olmasin, duvar 0 olabilir)."""
    from stairs import stair_entry_side
    side = stair_entry_side(resolution)
    if side is None:
        return False
    x0, y0, x1, y1 = resolution.bbox
    for w in walls:
        (sx, sy), (ex, ey) = w["start"], w["end"]
        tol = float(w["thickness"]) / 2.0 + 1.0
        if side in ("N", "S"):
            y = y1 if side == "N" else y0
            if abs(sy - y) <= tol and abs(ey - y) <= tol and min(max(sx, ex), x1) - max(min(sx, ex), x0) > 1.0:
                return False
        else:
            x = x1 if side == "E" else x0
            if abs(sx - x) <= tol and abs(ex - x) <= tol and min(max(sy, ey), y1) - max(min(sy, ey), y0) > 1.0:
                return False
    return True


def _stair_room_accesses(polygon: list, walls_by_id: dict, openings: list) -> list[dict]:
    """Merdiven odasi SINIRINDAKI (kapi/duvar acikligi) acikliklar: acikligin
    duvar-merkez-cizgisi konumu poligon kenarina duvar yarim kalinligi + 10mm
    icinde ise o odaya aittir. Pencere sayilmaz."""
    found: list[dict] = []
    for op in openings:
        if op.get("type") == "window":
            continue
        wall = walls_by_id.get(op.get("wall_id"))
        if wall is None:
            continue
        point = Wall.from_context(wall, WallCatalog()).centerline_point(op["position_from_start"])
        limit = float(wall["thickness"]) / 2.0 + 10.0
        n = len(polygon)
        for k in range(n):
            ax, ay = polygon[k]
            bx, by = polygon[(k + 1) % n]
            dx, dy = bx - ax, by - ay
            seg2 = dx * dx + dy * dy
            t = 0.0 if seg2 == 0 else max(0.0, min(1.0, ((point[0] - ax) * dx + (point[1] - ay) * dy) / seg2))
            if ((point[0] - ax - t * dx) ** 2 + (point[1] - ay - t * dy) ** 2) ** 0.5 <= limit:
                found.append({"id": op["id"], "type": op["type"], "point": (point[0], point[1])})
                break
    return found


def check_stairs(floor: dict) -> tuple[list[str], list[str]]:
    """Arity-1 (DEV-022): `stairs[].room_id` bu kattaki bir odaya isaret
    ediyor mu, ve `resolve_stair` (cizim koduyla AYNI TEK kaynak, bkz.
    scripts/stairs/CLAUDE.md) HATA/UYARI uretiyor mu. Ayri bir hesap
    YAZMAZ - `resolve_stair`i CAGIRIR, sonucunu yorumlar.

    DEV-047 (opt-in): `stairs[].exit_door_id` verilmisse, o kapinin
    merdivenin GERCEK hesaplanan cikis yonuyle (`resolution.exit_
    direction`) hizali olup olmadigi da denetlenir (UYARI - bu bir
    mimari sagduyu kontroludur, `architect/`in HER ZAMAN UYARI
    politikasiyla AYNI, HATA DEGIL). Kapinin duvar-merkez-cizgisi
    konumu `walls::Wall.centerline_point` ile (bu modulun TEK
    kaynagi) hesaplanir - ikinci bir kopya YAZILMAZ."""
    errors: list[str] = []
    warnings: list[str] = []
    rooms_by_id = {r["id"]: r for r in floor.get("rooms", [])}
    openings_by_id = {o["id"]: o for o in floor.get("openings", [])}
    walls_by_id = {w["id"]: w for w in floor.get("walls", [])}
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
        warnings.extend(stair_access_warnings(
            resolution, _stair_room_accesses(room["polygon"], walls_by_id, floor.get("openings", [])),
            entry_edge_open=_entry_edge_open(resolution, floor.get("walls", []))))

        exit_door_id = spec.get("exit_door_id")
        if exit_door_id is None:
            continue
        door = openings_by_id.get(exit_door_id)
        if door is None:
            errors.append(
                f"Merdiven '{spec['id']}', gecersiz bir exit_door_id'ye "
                f"referans veriyor: '{exit_door_id}'."
            )
            continue
        wall = walls_by_id.get(door.get("wall_id"))
        if wall is None:
            continue
        door_point = Wall.from_context(wall, WallCatalog()).centerline_point(
            door["position_from_start"]
        )
        alignment_warning = exit_door_alignment_warning(resolution, door_point)
        if alignment_warning:
            warnings.append(alignment_warning)
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
    errors += [prefix + e for e in check_rooms(units, floor["rooms"], floor["walls"])]
    errors += [prefix + e for e in check_walls(units, floor["walls"], floor["openings"])]
    errors += [prefix + e for e in check_openings(floor["openings"], floor["walls"])]
    # DEV-036: room_type VERILMIS ama standards.STANDARDS'ta TANIMSIZ bir
    # deger YAZIM HATASIDIR (arity-1, walls.kind ile AYNI desen) - HATA.
    errors += [prefix + e for e in check_room_types(floor["rooms"])]
    errors += [prefix + e for e in check_core_rectangular(floor["rooms"])]
    shaft_errors, _shaft_warnings = check_shafts(floor, units)
    errors += [prefix + e for e in shaft_errors]
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
    standards_warnings: list[str] = list(check_shafts_across_floors(context["floors"]))
    standards_warnings = [f"{w}" for w in standards_warnings]
    architect_warnings: list[str] = []
    for floor in context["floors"]:
        all_errors += check_floor(units, floor)
        floor_stair_errors, floor_stair_warnings = check_stairs(floor)
        all_errors += [f"[{floor['id']}] " + e for e in floor_stair_errors]
        stair_warnings += [f"[{floor['id']}] " + w for w in floor_stair_warnings]
        # DEV-036: oransal mahal kurallari - kullanici karari geregi HER
        # ZAMAN UYARIdir, uretimi DURDURMAZ.
        standards_warnings += [
            f"[{floor['id']}] " + w
            for w in check_room_proportions(
                # rev-26/27: U seklindeki (dog_leg/three_flight) merdiven odasi kareye yakin olabilir;
                # "merdiven odasi daha dikdortgen olmali" orani ona uygulanmaz.
                [r for r in floor["rooms"] if r["id"] not in {
                    st["room_id"] for st in floor.get("stairs", []) if st.get("kind", "dog_leg") != "single_flight"}],
                units, floor["walls"])
        ]
        standards_warnings += [
            f"[{floor['id']}] " + w for w in check_shafts(floor, units)[1]
        ]
        # DEV-039: iliskisel (arity-2+) mimari mantik kurallari - standards
        # ile AYNI politika (HER ZAMAN UYARI, asla HATA). Tumu rooms[].
        # unit_id OPT-IN'dir; alan verilmeyen bir projede (bugunku gercek
        # context.json dahil) bu liste SESSIZCE bos kalir.
        rooms, walls, openings = floor["rooms"], floor["walls"], floor["openings"]
        architect_warnings += [
            f"[{floor['id']}] " + w
            for w in (
                check_circulation_area_share(rooms)
                + check_common_circulation_share(rooms)
                + check_bedroom_via_corridor(rooms, walls, openings)
                + check_entry_sightlines(rooms, walls, openings)
                + check_door_core_balance(rooms, walls, openings)
                + check_wet_area_reachable_without_bedroom(rooms, walls, openings)
                + check_wet_area_door_proximity(rooms, walls, openings)
                # DEV-050: kapi/pencere iliskisel nuanslar (madde 4,12,13,14)
                + check_door_window_nuances(rooms, walls, openings)
            )
        ]
        # DEV-050: arity-1 nuanslar - acikligin kendi duvarina gore
        # (madde 1,2,3,5,6,11), mahal/koridor tipine gore (madde 7-10) ve
        # dis/ic duvar kalinligi hiyerarsisi (madde 16). HER ZAMAN UYARI.
        standards_warnings += [
            f"[{floor['id']}] " + w
            for w in (
                check_opening_nuances(walls, openings)
                + check_elevator_door_insets(rooms, walls, openings)
                + check_door_corridor_nuances(rooms, walls, openings)
                + check_wall_thickness(walls, rooms, units)
            )
        ]

    for elevation in context["elevations"]:
        all_errors += check_elevation(elevation)

    all_errors += check_sections(context)

    for warning in stair_warnings:
        print(f"UYARI (merdiven): {warning}")
    for warning in standards_warnings:
        print(f"UYARI (sartname): {warning}")
    for warning in architect_warnings:
        print(f"UYARI (mimari): {warning}")

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
