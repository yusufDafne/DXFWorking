#!/usr/bin/env python3
"""architect modulu testleri (DEV-039).

Ortak disiplin (kok CLAUDE.md): beklenen degerler ELLE hesaplanabilir
tutulur, her kural hem bir IHLAL hem bir YANLIS-POZITIF senaryosuyla
sinanir - "temiz dondu" cikisi tek basina hicbir sey kanitlamaz.

Kullanim:
    python scripts/architect/selftest.py
Cikis kodu: 0 basarili, 1 basarisiz.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from architect import (  # noqa: E402
    check_bedroom_via_corridor,
    check_circulation_area_share,
    check_door_core_balance,
    check_entry_sightlines,
    check_fits,
    options_for_core_placement,
    place_unit_entry_doors,
    resolve_unit_zoning,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
REAL_CONTEXT_PATH = PROJECT_ROOT / "context.json"


# --------------------------------------------------------------------------
# 1) check_circulation_area_share
# --------------------------------------------------------------------------

def check_circulation_share_flags_oversized_hol() -> list[str]:
    """koridor=20, salon=80 -> toplam=100, pay=%20 > varsayilan ust sinir
    %15 -> TAM 1 uyari, elle hesaplanabilir."""
    rooms = [
        {"id": "hol", "unit_id": "u1", "room_type": "koridor", "area_m2": 20.0},
        {"id": "salon", "unit_id": "u1", "room_type": "salon", "area_m2": 80.0},
    ]
    warnings = check_circulation_area_share(rooms)
    errors = []
    if len(warnings) != 1:
        errors.append(f"1 uyari beklenirdi, {len(warnings)} geldi: {warnings}")
    elif "u1" not in warnings[0]:
        errors.append(f"uyari 'u1' birimini ADLANDIRMALIYDI: {warnings[0]}")
    return errors


def check_circulation_share_false_positive_within_limit() -> list[str]:
    """koridor=10, salon=90 -> pay %10 < %15, YANLIS-POZITIF olmamali."""
    rooms = [
        {"id": "hol", "unit_id": "u1", "room_type": "koridor", "area_m2": 10.0},
        {"id": "salon", "unit_id": "u1", "room_type": "salon", "area_m2": 90.0},
    ]
    warnings = check_circulation_area_share(rooms)
    return [f"esik ICINDEKI bir oran uyari URETMEMELIYDI: {warnings}"] if warnings else []


def check_circulation_share_ignores_rooms_without_unit_id() -> list[str]:
    """`unit_id` verilmeyen odalar opt-in geregi HIC hesaba katilmamali -
    ayni koridor/salon oraniyla ama unit_id YOKSA uyari OLMAMALI."""
    rooms = [
        {"id": "hol", "room_type": "koridor", "area_m2": 20.0},
        {"id": "salon", "room_type": "salon", "area_m2": 80.0},
    ]
    warnings = check_circulation_area_share(rooms)
    return [f"unit_id'siz odalar kontrole GIRMEMELIYDI: {warnings}"] if warnings else []


# --------------------------------------------------------------------------
# 2) check_bedroom_via_corridor
# --------------------------------------------------------------------------

def _bedroom_fixture(other_room_type: str) -> tuple[list[dict], list[dict], list[dict]]:
    walls = [{"id": "w1", "start": [1000.0, 0.0], "end": [1000.0, 3000.0],
              "thickness": 200.0, "layer": "DUVARLAR"}]
    rooms = [
        {"id": "oda", "unit_id": "u1", "room_type": "yatak_odasi", "area_m2": 15.0,
         "polygon": [[0, 0], [1000, 0], [1000, 3000], [0, 3000]]},
        {"id": "diger", "unit_id": "u1", "room_type": other_room_type, "area_m2": 20.0,
         "polygon": [[1000, 0], [3000, 0], [3000, 3000], [1000, 3000]]},
    ]
    openings = [{"id": "d1", "type": "door", "wall_id": "w1",
                 "position_from_start": 1500.0, "width": 900.0, "layer": "KAPI-PENCERE"}]
    return rooms, walls, openings


def check_bedroom_via_salon_flags() -> list[str]:
    rooms, walls, openings = _bedroom_fixture("salon")
    warnings = check_bedroom_via_corridor(rooms, walls, openings)
    if len(warnings) != 1:
        return [f"1 uyari beklenirdi (yatak odasi -> salon), {len(warnings)} geldi: {warnings}"]
    return []


def check_bedroom_via_corridor_false_positive() -> list[str]:
    """AYNI geometri ama komsu oda 'koridor' (hol) ise - GERCEK projenin
    uA_d_oda_hol baglantisiyla AYNI durum - uyari OLMAMALI."""
    rooms, walls, openings = _bedroom_fixture("koridor")
    warnings = check_bedroom_via_corridor(rooms, walls, openings)
    return [f"hol'e acilan bir kapi uyari URETMEMELIYDI: {warnings}"] if warnings else []


# --------------------------------------------------------------------------
# 3) check_entry_sightlines
# --------------------------------------------------------------------------

def _sightline_fixture(wc_position_from_start: float, extra_wall: dict | None = None):
    walls = [
        {"id": "w_entry", "start": [0.0, 0.0], "end": [3000.0, 0.0],
         "thickness": 200.0, "layer": "DUVARLAR"},
        {"id": "w_wc", "start": [0.0, 2000.0], "end": [3000.0, 2000.0],
         "thickness": 200.0, "layer": "DUVARLAR"},
    ]
    if extra_wall is not None:
        walls.append(extra_wall)
    rooms = [
        {"id": "band", "room_type": "koridor", "area_m2": 30.0,
         "polygon": [[0, -1000], [3000, -1000], [3000, 0], [0, 0]]},
        {"id": "hol", "unit_id": "u1", "room_type": "koridor", "area_m2": 60.0,
         "polygon": [[0, 0], [3000, 0], [3000, 2000], [0, 2000]]},
        {"id": "wc", "unit_id": "u1", "room_type": "wc", "area_m2": 30.0,
         "polygon": [[0, 2000], [3000, 2000], [3000, 3000], [0, 3000]]},
    ]
    openings = [
        {"id": "d_entry", "type": "door", "wall_id": "w_entry",
         "position_from_start": 500.0, "width": 900.0, "layer": "KAPI-PENCERE"},
        {"id": "d_wc", "type": "door", "wall_id": "w_wc",
         "position_from_start": wc_position_from_start, "width": 800.0,
         "layer": "KAPI-PENCERE"},
    ]
    return rooms, walls, openings


def check_entry_sightline_flags_facing_wc() -> list[str]:
    """WC kapisi girisin ONUNDE (600,2000), koni ICINDE (~3 derece sapma)
    VE araya giren bir duvar YOK -> UYARI."""
    rooms, walls, openings = _sightline_fixture(wc_position_from_start=600.0)
    warnings = check_entry_sightlines(rooms, walls, openings)
    if len(warnings) != 1:
        return [f"1 uyari beklenirdi, {len(warnings)} geldi: {warnings}"]
    return []


def check_entry_sightline_false_positive_out_of_cone() -> list[str]:
    """WC kapisi girisin COK yanina tasinirsa (2900,2000) sapma 45 derece
    koninin DISINA cikar -> uyari OLMAMALI."""
    rooms, walls, openings = _sightline_fixture(wc_position_from_start=2900.0)
    warnings = check_entry_sightlines(rooms, walls, openings)
    return [f"koni disindaki bir WC uyari URETMEMELIYDI: {warnings}"] if warnings else []


def check_entry_sightline_false_positive_blocked() -> list[str]:
    """WC kapisi koni ICINDE (600,2000) ama araya bir bolme duvari
    (y=1000) girerse goru hatti KESILIR -> uyari OLMAMALI."""
    partition = {"id": "w_partition", "start": [0.0, 1000.0], "end": [3000.0, 1000.0],
                 "thickness": 200.0, "layer": "DUVARLAR"}
    rooms, walls, openings = _sightline_fixture(
        wc_position_from_start=600.0, extra_wall=partition,
    )
    warnings = check_entry_sightlines(rooms, walls, openings)
    return [f"engellenen bir goru hatti uyari URETMEMELIYDI: {warnings}"] if warnings else []


# --------------------------------------------------------------------------
# 4) check_door_core_balance
# --------------------------------------------------------------------------

def _core_balance_fixture(u1_x: float, u2_x: float) -> tuple[list[dict], list[dict], list[dict]]:
    # Cekirdek: asansor [0,0]-[1000,1000] + merdiven [1000,0]-[3000,1000].
    # Merkez noktalarinin ortalamasi (elle): ((500,500)+(2000,500))/2 = (1250,500).
    rooms = [
        {"id": "elevator", "room_type": "asansor", "area_m2": 1.0,
         "polygon": [[0, 0], [1000, 0], [1000, 1000], [0, 1000]]},
        {"id": "stair", "room_type": "merdiven", "area_m2": 2.0,
         "polygon": [[1000, 0], [3000, 0], [3000, 1000], [1000, 1000]]},
        {"id": "band", "room_type": "koridor", "area_m2": 50.0,
         "polygon": [[0, 1000], [20000, 1000], [20000, 2000], [0, 2000]]},
        {"id": "u1_hol", "unit_id": "u1", "room_type": "koridor", "area_m2": 10.0,
         "polygon": [[u1_x - 500, 2000], [u1_x + 500, 2000], [u1_x + 500, 3000],
                     [u1_x - 500, 3000]]},
        {"id": "u2_hol", "unit_id": "u2", "room_type": "koridor", "area_m2": 10.0,
         "polygon": [[u2_x - 500, 2000], [u2_x + 500, 2000], [u2_x + 500, 3000],
                     [u2_x - 500, 3000]]},
    ]
    walls = [
        {"id": "w_u1", "start": [u1_x - 500, 2000], "end": [u1_x + 500, 2000],
         "thickness": 200.0, "layer": "DUVARLAR"},
        {"id": "w_u2", "start": [u2_x - 500, 2000], "end": [u2_x + 500, 2000],
         "thickness": 200.0, "layer": "DUVARLAR"},
    ]
    openings = [
        {"id": "d_u1", "type": "door", "wall_id": "w_u1", "position_from_start": 500.0,
         "width": 900.0, "layer": "KAPI-PENCERE"},
        {"id": "d_u2", "type": "door", "wall_id": "w_u2", "position_from_start": 500.0,
         "width": 900.0, "layer": "KAPI-PENCERE"},
    ]
    return rooms, walls, openings


def check_door_core_balance_flags_imbalance() -> list[str]:
    """Cekirdek merkezi (1250,500). u1 kapi noktasi (1300,2000) -> mesafe
    sqrt(50^2+1500^2)=~1500.8mm. u2 kapi noktasi (10000,2000) -> mesafe
    sqrt(8750^2+1500^2)=~8877.6mm. Oran ~5.91, varsayilan ust sinir 1.6'yi
    COK asiyor -> TAM 1 uyari."""
    rooms, walls, openings = _core_balance_fixture(u1_x=1300.0, u2_x=10000.0)
    warnings = check_door_core_balance(rooms, walls, openings)
    if len(warnings) != 1:
        return [f"1 uyari beklenirdi, {len(warnings)} geldi: {warnings}"]
    return []


def check_door_core_balance_false_positive_symmetric() -> list[str]:
    """Iki kapi cekirdege ESIT mesafede (simetrik) -> oran 1.0, uyari
    OLMAMALI."""
    rooms, walls, openings = _core_balance_fixture(u1_x=-750.0, u2_x=3250.0)
    warnings = check_door_core_balance(rooms, walls, openings)
    return [f"simetrik bir yerlesim uyari URETMEMELIYDI: {warnings}"] if warnings else []


# --------------------------------------------------------------------------
# 5) study.check_fits / resolve_unit_zoning
# --------------------------------------------------------------------------

def check_fits_matches_dev038_discovery() -> list[str]:
    """DEV-038'in kesfettigi GERCEK senaryo: salon (3000) + 2 yatak odasi
    (2700x2) = 8400mm asgari, 7700mm genislige SIGMAZ (elle: 8400-7700=700
    aciik)."""
    errors = []
    report = check_fits(7700.0, ["salon", "yatak_odasi", "yatak_odasi"])
    if report.fits:
        errors.append("7700mm'e 8400mm'lik bir program SIGMAMALIYDI")
    if abs(report.required_mm - 8400.0) > 1e-9:
        errors.append(f"required_mm=8400.0 beklenirdi, {report.required_mm} geldi")
    if abs(report.margin_mm - (-700.0)) > 1e-9:
        errors.append(f"margin_mm=-700.0 beklenirdi, {report.margin_mm} geldi")
    return errors


def check_fits_false_positive_with_margin() -> list[str]:
    """AYNI program 9000mm genislige (600mm pay birakarak) SIGAR."""
    errors = []
    report = check_fits(9000.0, ["salon", "yatak_odasi", "yatak_odasi"])
    if not report.fits:
        errors.append(f"9000mm'e sigan bir program FITS=False donmemeliydi: {report}")
    if abs(report.margin_mm - 600.0) > 1e-9:
        errors.append(f"margin_mm=600.0 beklenirdi, {report.margin_mm} geldi")
    return errors


def check_fits_reports_unknown_types() -> list[str]:
    report = check_fits(9000.0, ["yatak_odasi", "bilinmeyen_tip"])
    errors = []
    if report.fits:
        errors.append("bilinmeyen tip iceren bir program FITS=True DONMEMELIYDI")
    if report.unknown_types != ("bilinmeyen_tip",):
        errors.append(f"unknown_types=('bilinmeyen_tip',) beklenirdi, {report.unknown_types} geldi")
    return errors


def check_resolve_unit_zoning_allocates_slack_evenly() -> list[str]:
    """9000mm genislik, [yatak_odasi(2700), salon(3000)] -> toplam asgari
    5700, bosluk 3300, oda basina 1650 (elle): zone1=[0,4350],
    zone2=[4350,9000]."""
    errors = []
    plan = resolve_unit_zoning(9000.0, 5000.0, ["yatak_odasi", "salon"])
    if not plan.fits:
        errors.append(f"plan sigmaliydi: {plan.feasibility}")
        return errors
    if len(plan.zones) != 2:
        errors.append(f"2 zone beklenirdi, {len(plan.zones)} geldi")
        return errors
    z1, z2 = plan.zones
    expected = [(0.0, 4350.0), (4350.0, 9000.0)]
    for zone, (x0, x1) in zip((z1, z2), expected):
        if abs(zone.x0 - x0) > 1e-6 or abs(zone.x1 - x1) > 1e-6:
            errors.append(f"'{zone.room_type}' araligi beklenenden farkli: "
                          f"({zone.x0},{zone.x1}) != ({x0},{x1})")
        if abs(zone.y0 - 0.0) > 1e-9 or abs(zone.y1 - 5000.0) > 1e-9:
            errors.append(f"'{zone.room_type}' derinligi TUM available_depth OLMALIYDI")
    return errors


def check_resolve_unit_zoning_empty_when_infeasible() -> list[str]:
    plan = resolve_unit_zoning(7700.0, 5000.0, ["salon", "yatak_odasi", "yatak_odasi"])
    if plan.fits or plan.zones:
        return [f"sigmayan bir program BOS zone listesi DONMELIYDI: {plan}"]
    return []


# --------------------------------------------------------------------------
# 6) options.options_for_core_placement
# --------------------------------------------------------------------------

def check_options_for_core_placement_scores_entry_side_higher() -> list[str]:
    """floor 20000x17500, cekirdek 4000x4500, entry_side='alt' (guney) ->
    sol-alt/sag-alt kosesi (skor 1.0) sol-ust/sag-ust'tan (skor 0.4) ONCE
    gelmeli (elle: 'alt' iceren 2 kose ile baslar)."""
    errors = []
    options = options_for_core_placement(20000.0, 17500.0, entry_side="alt")
    if len(options) != 4:
        errors.append(f"4 secenek beklenirdi, {len(options)} geldi")
        return errors
    top_two = {options[0].id, options[1].id}
    if top_two != {"sol-alt", "sag-alt"}:
        errors.append(f"en yuksek puanli 2 kose {{'sol-alt','sag-alt'}} olmaliydi: {top_two}")
    if options[0].score != 1.0 or options[3].score != 0.4:
        errors.append(f"puan sirasi beklenmedik: {[o.score for o in options]}")
    sag_alt = next(o for o in options if o.id == "sag-alt")
    if (sag_alt.x, sag_alt.y) != (16000.0, 0.0):
        errors.append(f"'sag-alt' konumu (16000,0) olmaliydi: {(sag_alt.x, sag_alt.y)}")
    return errors


# --------------------------------------------------------------------------
# 7) design.place_unit_entry_doors
# --------------------------------------------------------------------------

def check_place_unit_entry_doors_centers_on_zones() -> list[str]:
    """Yukaridaki zonlama sonucunun (zone1=[0,4350], zone2=[4350,9000])
    MERKEZLERINE (2175 / 6675) birer kapi konmali (elle hesap)."""
    errors = []
    plan = resolve_unit_zoning(9000.0, 5000.0, ["yatak_odasi", "salon"])
    doors = place_unit_entry_doors(plan, "w_south", door_width=900.0)
    if len(doors) != 2:
        errors.append(f"2 kapi beklenirdi, {len(doors)} geldi")
        return errors
    expected = {"door_yatak_odasi": 2175.0, "door_salon": 6675.0}
    for door in doors:
        expected_pos = expected.get(door["id"])
        if expected_pos is None:
            errors.append(f"beklenmeyen kapi id'si: {door['id']}")
            continue
        if abs(door["position_from_start"] - expected_pos) > 1e-6:
            errors.append(
                f"'{door['id']}' konumu {expected_pos} olmaliydi, {door['position_from_start']} geldi"
            )
        if door["wall_id"] != "w_south" or door["width"] != 900.0:
            errors.append(f"'{door['id']}' wall_id/width beklenenden farkli: {door}")
    return errors


def check_place_unit_entry_doors_empty_when_infeasible() -> list[str]:
    plan = resolve_unit_zoning(7700.0, 5000.0, ["salon", "yatak_odasi", "yatak_odasi"])
    doors = place_unit_entry_doors(plan, "w_south")
    return [f"sigmayan bir plan icin kapi URETILMEMELIYDI: {doors}"] if doors else []


# --------------------------------------------------------------------------
# 8) Gercek proje kaniti: rev-20'nin hol-orani ihlali (rev-21'de unit_id
# gercek projeye EKLENDI - bkz. context.json rev_history, requests.jsonl).
# --------------------------------------------------------------------------

def check_circulation_share_catches_real_project_violation() -> list[str]:
    """GERCEK context.json'daki uA_* odalarinin `unit_id` ARTIK GERCEK
    proje verisidir (rev-21'de eklendi, id-onek konvansiyonundan BIREBIR
    TURETILDI). Elle hesap: hol=37.7, toplam=27.3+22.75+6.27+3.8+2.28+37.7
    =100.1, pay=%37.66 - varsayilan ust sinir %15'i ACIKCA asiyor. Gercek
    dosya yoksa test ATLANIR."""
    if not REAL_CONTEXT_PATH.exists():
        return []
    context = json.loads(REAL_CONTEXT_PATH.read_text(encoding="utf-8"))
    floor = next(f for f in context["floors"] if f["id"] == "normal1")
    unit_a_rooms = [r for r in floor["rooms"] if r["id"].startswith("uA_")]
    errors = []
    total = sum(r["area_m2"] for r in unit_a_rooms)
    if abs(total - 100.1) > 0.05:
        errors.append(f"beklenen toplam alan ~100.1 m2, gercek dosyada {total} bulundu "
                       f"(context.json degisti olabilir, bu test guncellenmeli)")
    if not all(r.get("unit_id") == "uA" for r in unit_a_rooms):
        errors.append("uA_* odalarinin TUMU unit_id='uA' TASIMALIYDI "
                       "(rev-21 kapsami degisti olabilir)")
    warnings = check_circulation_area_share(unit_a_rooms)
    if len(warnings) != 1:
        errors.append(f"GERCEK proje verisinde TAM 1 uyari beklenirdi, {len(warnings)} geldi: {warnings}")
    elif "uA" not in warnings[0]:
        errors.append(f"uyari 'uA' birimini ADLANDIRMALIYDI: {warnings[0]}")
    return errors


def check_opt_in_still_holds_when_unit_id_is_stripped() -> list[str]:
    """AYNI gercek GEOMETRI (uA_* odalari) ama `unit_id` alani bellek-ici
    olarak SOYULEREK - opt-in ilkesinin (unit_id yoksa kontrol atlanir)
    rev-21'den SONRA da (gercek projeye unit_id EKLENDIKTEN sonra) hala
    GECERLI oldugunu kanitlar - kontrol yalnizca `unit_id` ALANINA bakar,
    id-onek konvansiyonuna DEGIL."""
    if not REAL_CONTEXT_PATH.exists():
        return []
    context = json.loads(REAL_CONTEXT_PATH.read_text(encoding="utf-8"))
    floor = next(f for f in context["floors"] if f["id"] == "normal1")
    rooms_without_unit_id = [
        {k: v for k, v in r.items() if k != "unit_id"} for r in floor["rooms"]
    ]
    warnings = check_circulation_area_share(rooms_without_unit_id)
    return ([f"unit_id SOYULUNCE uyari OLMAMALIYDI: {warnings}"]
            if warnings else [])


def main() -> int:
    groups = (
        ("hol payi esigi asinca UYARI verir", check_circulation_share_flags_oversized_hol()),
        ("esik icindeki hol payi YANLIS-POZITIF uretmez", check_circulation_share_false_positive_within_limit()),
        ("unit_id verilmeyen odalar kontrole GIRMEZ", check_circulation_share_ignores_rooms_without_unit_id()),
        ("yatak odasi -> salon kapisi UYARI verir", check_bedroom_via_salon_flags()),
        ("yatak odasi -> hol kapisi YANLIS-POZITIF uretmez", check_bedroom_via_corridor_false_positive()),
        ("giris karsisindaki WC kapisi UYARI verir", check_entry_sightline_flags_facing_wc()),
        ("koni disindaki WC YANLIS-POZITIF uretmez", check_entry_sightline_false_positive_out_of_cone()),
        ("duvarla ENGELLENEN goru hatti YANLIS-POZITIF uretmez", check_entry_sightline_false_positive_blocked()),
        ("dengesiz kapi-cekirdek mesafesi UYARI verir", check_door_core_balance_flags_imbalance()),
        ("simetrik kapi-cekirdek mesafesi YANLIS-POZITIF uretmez", check_door_core_balance_false_positive_symmetric()),
        ("check_fits DEV-038'in GERCEK kesfini (7700mm sigmaz) dogrular", check_fits_matches_dev038_discovery()),
        ("check_fits payli bir programda FITS=True doner", check_fits_false_positive_with_margin()),
        ("check_fits bilinmeyen tipi ISARETLER", check_fits_reports_unknown_types()),
        ("resolve_unit_zoning boslugu ESIT dagitir", check_resolve_unit_zoning_allocates_slack_evenly()),
        ("resolve_unit_zoning sigmayinca BOS doner", check_resolve_unit_zoning_empty_when_infeasible()),
        ("options_for_core_placement giris kenarini YUKSEK puanlar", check_options_for_core_placement_scores_entry_side_higher()),
        ("place_unit_entry_doors zone MERKEZLERINE kapi koyar", check_place_unit_entry_doors_centers_on_zones()),
        ("place_unit_entry_doors sigmayan planda BOS doner", check_place_unit_entry_doors_empty_when_infeasible()),
        ("GERCEK proje uA verisi hol-orani ihlalini YAKALAR", check_circulation_share_catches_real_project_violation()),
        ("unit_id SOYULUNCE opt-in HALA GECERLI", check_opt_in_still_holds_when_unit_id_is_stripped()),
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
        print("\nARCHITECT SELF-TEST BASARISIZ.")
        return 1
    print("\nArchitect self-test BASARILI.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
