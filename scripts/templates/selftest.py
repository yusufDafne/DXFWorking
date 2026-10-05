#!/usr/bin/env python3
"""Sirkulasyon cekirdegi sablon modulu testleri (DEV-037).

Kullanim:
    python scripts/templates/selftest.py
Cikis kodu: 0 basarili, 1 basarisiz.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from templates import (  # noqa: E402
    CirculationCoreTemplate,
    generate_circulation_core,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
REAL_CONTEXT_PATH = PROJECT_ROOT / "context.json"


def _real_normal_floor() -> dict:
    context = json.loads(REAL_CONTEXT_PATH.read_text(encoding="utf-8"))
    return next(f for f in context["floors"] if f["id"] == "normal1"), context["meta"]


def check_band_is_efficient_rectangle_not_wasteful_l_shape() -> list[str]:
    """DEV-045: `band`, cekirdegin (asansor+merdiven) DOGUSUNDA artik
    GEREKSIZ yere tam `band_depth` derinliginde degil - SADECE
    `corridor_leg_depth` derinliginde basit bir DIKDORTGENDIR (eski
    L-sekli DEGIL). Elle hesap (varsayilan sablon, floor_width=20000,
    floor_depth=17500): band_y0=17500-4500=13000, core_y0=13000+1500=
    14500 -> poligon TAM [[0,13000],[20000,13000],[20000,14500],
    [0,14500]], alan=20000*1500/1e6=30.0 m2 (eski L-sekli 71.7 m2'ydi -
    41.7 m2'lik 'olu alan' KALDIRILDI)."""
    errors: list[str] = []
    fragment = generate_circulation_core(20000.0, 17500.0)
    band = next(r for r in fragment["rooms"] if r["id"] == "band")
    expected_polygon = [[0.0, 13000.0], [20000.0, 13000.0],
                         [20000.0, 14500.0], [0.0, 14500.0]]
    if band["polygon"] != expected_polygon:
        errors.append(f"band poligonu {expected_polygon} bekleniyordu, {band['polygon']} bulundu")
    if abs(band["area_m2"] - 30.0) > 1e-6:
        errors.append(f"band alani 30.0 m2 bekleniyordu, {band['area_m2']} bulundu")
    return errors


def check_band_still_excludes_core_footprint() -> list[str]:
    """YANLIS-POZITIF: dikdortgene basitlestirme, cekirdegin (asansor+
    merdiven, y>=core_y0) footprint'iyle YENIDEN cakismaya baslamamali -
    band'in y-araligi [band_y0, core_y0]de KALMALI, core_y0'in USTUNE
    HIC CIKMAMALI (bu, L-sekli hic GEREKMEDEN cakismanin onlendigini
    kanitlar)."""
    fragment = generate_circulation_core(20000.0, 17500.0)
    band = next(r for r in fragment["rooms"] if r["id"] == "band")
    band_ys = [p[1] for p in band["polygon"]]
    core_y0 = 17500.0 - 4500.0 + 1500.0  # 14500.0, DEFAULT_TEMPLATE'ten
    if max(band_ys) > core_y0:
        return [f"band, cekirdegin y araligina ({core_y0}) TASIYOR: max_y={max(band_ys)}"]
    return []


def check_core_position_fixed_when_floor_width_changes() -> list[str]:
    """Cekirdek HER ZAMAN sol-alt kosede (x=0) sabittir; yalnizca koridorun/
    guney duvarinin DOGU ucu floor_width'e gore degisir (kok CLAUDE.md:
    'Bu konum tum katlarda sabit tutulmalidir')."""
    errors: list[str] = []
    narrow = generate_circulation_core(9000.0, 17500.0)
    wide = generate_circulation_core(25000.0, 17500.0)
    for fragment, label in ((narrow, "9000"), (wide, "25000")):
        elevator = next(r for r in fragment["rooms"] if r["id"] == "elevator")
        if elevator["polygon"][0] != [0.0, 14500.0]:
            errors.append(f"floor_width={label}: asansor sol-alt kosesi x=0'da DEGIL: {elevator['polygon'][0]}")
    narrow_band = next(r for r in narrow["rooms"] if r["id"] == "band")
    wide_band = next(r for r in wide["rooms"] if r["id"] == "band")
    if narrow_band["area_m2"] >= wide_band["area_m2"]:
        errors.append(
            f"genis kat DAR kattan daha BUYUK koridor alanina sahip olmaliydi: "
            f"dar={narrow_band['area_m2']} genis={wide_band['area_m2']}"
        )
    return errors


def check_include_band_south_toggle() -> list[str]:
    """Bodrum/cati gibi acik gecisli katlarda band_south duvari CIZILMEMELI
    (kok CLAUDE.md: 'bodrum/catida YOK - acik gecis') - cagiran taraf bunu
    ACIKCA kontrol edebilmeli."""
    errors: list[str] = []
    with_wall = generate_circulation_core(20000.0, 17500.0, include_band_south=True)
    without_wall = generate_circulation_core(20000.0, 17500.0, include_band_south=False)
    if not any(w["id"] == "band_south" for w in with_wall["walls"]):
        errors.append("include_band_south=True iken band_south duvari YOK")
    if any(w["id"] == "band_south" for w in without_wall["walls"]):
        errors.append("include_band_south=False iken band_south duvari YINE DE uretildi")
    # Baska hicbir sey ETKILENMEMELI (sadece bu bir duvar eklenir/cikarilir).
    if len(with_wall["walls"]) - len(without_wall["walls"]) != 1:
        errors.append("include_band_south yalnizca TEK bir duvari degistirmeliydi")
    return errors


def check_id_prefix_avoids_collisions() -> list[str]:
    """Birden fazla cekirdek (orn. iki ayri blok) AYNI floor'a eklenecekse
    id CAKISMASI onlenebilmeli."""
    errors: list[str] = []
    fragment = generate_circulation_core(20000.0, 17500.0, id_prefix="blokB_")
    ids = [r["id"] for r in fragment["rooms"]] + [w["id"] for w in fragment["walls"]] + [o["id"] for o in fragment["openings"]]
    if not all(i.startswith("blokB_") for i in ids):
        errors.append(f"tum id'ler prefix TASIMALIYDI: {ids}")
    return errors


def check_custom_template_scales_linearly() -> list[str]:
    """Ozel bir CirculationCoreTemplate (farkli asansor/merdiven olculeri)
    enjekte edilebilmeli - varsayilanlar SABIT KODLANMAMIS olmali."""
    errors: list[str] = []
    custom = CirculationCoreTemplate(elevator_width=1400.0, stair_width=3000.0,
                                     corridor_leg_depth=1500.0, band_depth=4500.0,
                                     wall_thickness=200.0, door_width=900.0)
    fragment = generate_circulation_core(15000.0, 17500.0, template=custom)
    stair = next(r for r in fragment["rooms"] if r["id"] == "stair")
    expected_width = custom.stair_width
    actual_width = stair["polygon"][1][0] - stair["polygon"][0][0]
    if abs(actual_width - expected_width) > 1e-9:
        errors.append(f"ozel merdiven genisligi uygulanmadi: {actual_width} != {expected_width}")
    return errors


def check_central_core_dev055() -> list[str]:
    """DEV-055: merkezi cekirdek + kat holu. Kat 20000x17500, 3:2 hol: blok
    x 6950..13050, hol y 5216.67..9283.33 (derinlik 4066.67), cekirdek satiri
    9283.33..12283.33 (3000). Asansor 2100x3000 = 6.3 m2, merdiven 4000x3000 =
    12.0 m2, hol 6100x4066.67 = 24.81 m2. Asansor kapisi 2100-2*250 = 1600."""
    from validate import check_openings, check_rooms, check_walls
    from walls import Wall, WallCatalog, gaps_for_wall
    from openings import Opening, check_elevator_door_insets, swing_geometry
    from collision.geometry import point_in_polygon
    from templates import generate_central_core
    errors: list[str] = []
    r = generate_central_core(20000.0, 17500.0)
    areas = {x["id"]: x["area_m2"] for x in r["rooms"]}
    if areas != {"elevator": 6.3, "stair": 12.0, "hall": 24.81}:
        errors.append(f"alanlar 6.3/12.0/24.81 olmali: {areas}")
    if r["zone"]["option_id"] != "dikdortgen_3_2" or not r["zone"]["surrounds"]:
        errors.append(f"varsayilan: dikdortgen_3_2 ve cevrelenebilir olmali: {r['zone']}")
    elev = next(o for o in r["openings"] if o["type"] == "elevator_door")
    if elev["width"] != 1600.0 or elev["variant"] != "sliding":
        errors.append(f"asansor kapisi 1600mm / sliding olmali: {elev}")
    if check_elevator_door_insets(r["rooms"], r["walls"], r["openings"]):
        errors.append("uretilen asansor kapisi kendi pay kuralindan gecmeli")
    for combo in ({}, {"core_side": "south"}, {"orientation": "y"}, {"core_side": "south", "orientation": "y"}):
        g = generate_central_core(20000.0, 17500.0, elevator_variant="single", **combo)
        bad = (check_rooms("mm", g["rooms"]) + check_walls("mm", g["walls"], g["openings"])
               + check_openings(g["openings"], g["walls"]))
        if bad:
            errors.append(f"{combo}: validate.check_* temiz olmali: {bad}")
        rooms = {x["id"]: x for x in g["rooms"]}
        walls = {w["id"]: Wall.from_context(w, WallCatalog()) for w in g["walls"]}
        for op, expect in (("door_elevator", "hall"), ("door_stair", "stair")):
            data = next(o for o in g["openings"] if o["id"] == op)
            wall = walls[data["wall_id"]]
            (g0, g1, d), = gaps_for_wall(wall, [data])
            tip = swing_geometry(wall, Opening.from_context(d), g0, g1).open_end
            if not point_in_polygon(tip, rooms[expect]["polygon"]):
                errors.append(f"{combo}: {op} kanadi '{expect}' odasina acilmali")
    # kasitli bozma: asansor kapisi kuyu genisligi kadar -> pay uyarisi
    g = generate_central_core(20000.0, 17500.0)
    for o in g["openings"]:
        if o["type"] == "elevator_door":
            o["width"] = 2100.0
    if not check_elevator_door_insets(g["rooms"], g["walls"], g["openings"]):
        errors.append("kuyu genisligi kadar kapi (0 pay) UYARI vermeli")
    # sigmayan kat
    try:
        generate_central_core(6000.0, 17500.0)
        errors.append("6000mm katta ValueError bekleniyordu")
    except ValueError:
        pass
    return errors


def main() -> int:
    groups = (
        ("merkezi cekirdek + kat holu + asansor kapisi (DEV-055)", check_central_core_dev055()),
        ("band artik verimli bir dikdortgen, israf eden L-sekli DEGIL (DEV-045)", check_band_is_efficient_rectangle_not_wasteful_l_shape()),
        ("band basitlestirilince de cekirdek footprint'iyle CAKISMAZ", check_band_still_excludes_core_footprint()),
        ("cekirdek konumu sabit, yalnizca dogu ucu floor_width'e gore degisir", check_core_position_fixed_when_floor_width_changes()),
        ("include_band_south acik/kapali (bodrum/cati vs zemin/normal)", check_include_band_south_toggle()),
        ("id_prefix tum uretilen id'lere uygulanir", check_id_prefix_avoids_collisions()),
        ("ozel CirculationCoreTemplate enjekte edilebilir", check_custom_template_scales_linearly()),
    )
    failed = False
    for name, errors in groups:
        if errors:
            failed = True
            print(f"[HATA] {name}:")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"[OK  ] {name}")
    if failed:
        print("\nTEMPLATES SELF-TEST BASARISIZ.")
        return 1
    print("\nTemplates self-test BASARILI.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
