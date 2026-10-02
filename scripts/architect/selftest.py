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
    check_common_circulation_share,
    check_door_core_balance,
    check_entry_sightlines,
    check_fits,
    check_wet_area_door_proximity,
    check_wet_area_reachable_without_bedroom,
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
# 8) Gercek proje kaniti: rev-21'de unit_id EKLENDI, rev-22'de rev-20'nin
# hol-orani/kapi-cekirdek/goru-hatti/yatak-odasi-salon ihlalleri GIDERILDI
# (bkz. context.json rev_history, requests.jsonl). Bu grup artik GERCEK
# projenin TEMIZ oldugunu kanitlar - "ihlali yakalar" kaniti SENTETIK
# fixture'larda (yukaridaki gruplar) kalici olarak durur, GERCEK proje
# verisine BAGLI DEGILDIR (proje revize edildikce bu test KIRILMAZ).
# --------------------------------------------------------------------------

# --------------------------------------------------------------------------
# 6) check_wet_area_reachable_without_bedroom (DEV-042)
# --------------------------------------------------------------------------

def _wet_area_chain_fixture(direct_bypass: bool) -> tuple[list[dict], list[dict], list[dict]]:
    """`hol` (koridor) - `oda` (yatak_odasi) HER ZAMAN komsu. `direct_
    bypass=False` ise `banyo` SADECE `oda` uzerinden erisilir (kullanicinin
    somut ornegi: 'koridor -> hol -> oda -> banyo'); `True` ise `banyo`
    `hol`e DOGRUDAN de acilir (oda HALA unit'te var ama tek yol DEGIL)."""
    hol = {"id": "hol", "unit_id": "u1", "room_type": "koridor", "area_m2": 4.0,
           "polygon": [[0, 0], [2000, 0], [2000, 2000], [0, 2000]]}
    oda = {"id": "oda", "unit_id": "u1", "room_type": "yatak_odasi", "area_m2": 4.0,
           "polygon": [[2000, 0], [4000, 0], [4000, 2000], [2000, 2000]]}
    walls = [{"id": "w_hol_oda", "start": [2000.0, 0.0], "end": [2000.0, 2000.0],
              "thickness": 200.0, "layer": "DUVARLAR"}]
    openings = [{"id": "d_hol_oda", "type": "door", "wall_id": "w_hol_oda",
                 "position_from_start": 1000.0, "width": 900.0, "layer": "KAPI-PENCERE"}]
    if direct_bypass:
        banyo = {"id": "banyo", "unit_id": "u1", "room_type": "banyo", "area_m2": 4.0,
                 "polygon": [[0, 2000], [2000, 2000], [2000, 4000], [0, 4000]]}
        walls.append({"id": "w_hol_banyo", "start": [0.0, 2000.0], "end": [2000.0, 2000.0],
                      "thickness": 200.0, "layer": "DUVARLAR"})
        openings.append({"id": "d_hol_banyo", "type": "door", "wall_id": "w_hol_banyo",
                         "position_from_start": 1000.0, "width": 900.0, "layer": "KAPI-PENCERE"})
    else:
        banyo = {"id": "banyo", "unit_id": "u1", "room_type": "banyo", "area_m2": 4.0,
                 "polygon": [[4000, 0], [6000, 0], [6000, 2000], [4000, 2000]]}
        walls.append({"id": "w_oda_banyo", "start": [4000.0, 0.0], "end": [4000.0, 2000.0],
                      "thickness": 200.0, "layer": "DUVARLAR"})
        openings.append({"id": "d_oda_banyo", "type": "door", "wall_id": "w_oda_banyo",
                         "position_from_start": 1000.0, "width": 900.0, "layer": "KAPI-PENCERE"})
    return [hol, oda, banyo], walls, openings


def check_wet_area_blocked_by_bedroom_flags() -> list[str]:
    """hol -> oda (yatak_odasi) -> banyo zincirinde, banyo'ya hol'den
    yatak odasindan GECMEDEN ulasan BASKA bir yol YOK -> TAM 1 uyari."""
    rooms, walls, openings = _wet_area_chain_fixture(direct_bypass=False)
    warnings = check_wet_area_reachable_without_bedroom(rooms, walls, openings)
    if len(warnings) != 1:
        return [f"1 uyari beklenirdi, {len(warnings)} geldi: {warnings}"]
    if "banyo" not in warnings[0]:
        return [f"uyari 'banyo' odasini ADLANDIRMALIYDI: {warnings[0]}"]
    return []


def check_wet_area_direct_bypass_false_positive() -> list[str]:
    """AYNI 3 oda (hol/oda/banyo) ama banyo'ya hol'den DOGRUDAN (yatak
    odasindan GECMEDEN) bir kapi da var - oda unit'te var olmaya devam
    etse de TEK yol DEGIL, EN AZ bir yol yatak-odasiz -> uyari OLMAMALI."""
    rooms, walls, openings = _wet_area_chain_fixture(direct_bypass=True)
    warnings = check_wet_area_reachable_without_bedroom(rooms, walls, openings)
    return ([f"dogrudan bypass'i olan bir islak hacim uyari URETMEMELIYDI: {warnings}"]
            if warnings else [])


def check_wet_area_real_project_catches_uC_chain() -> list[str]:
    """GERCEK projede (`normal1`), rev-22 uC'yi 'salon-banyo-oda-hol'
    olarak yeniden sıraladi ama `uC_hol`un TEK komsusu HALA `uC_oda`
    (yatak_odasi) - yani `uC_banyo`'ya `uC_hol`den yatak odasindan
    GECMEDEN ulasan bir yol YOK (kullanicinin 'koridor->hol->oda->banyo'
    sikayetinin rev-22'den SONRA da KISMEN hayatta kalan somut bir
    ornegi). uA/uB'nin T-sekilli hol'u ise banyo/wc'ye DOGRUDAN acildigi
    icin TEMIZ olmali. Gercek dosya yoksa test ATLANIR."""
    if not REAL_CONTEXT_PATH.exists():
        return []
    context = json.loads(REAL_CONTEXT_PATH.read_text(encoding="utf-8"))
    floor = next(f for f in context["floors"] if f["id"] == "normal1")
    rooms, walls, openings = floor["rooms"], floor["walls"], floor["openings"]
    warnings = check_wet_area_reachable_without_bedroom(rooms, walls, openings)
    errors = []
    if not any("uC_banyo" in w for w in warnings):
        errors.append(f"uC_banyo'nun yatak-odasi zinciri YAKALANMALIYDI: {warnings}")
    if any("uA_" in w or "uB_" in w for w in warnings):
        errors.append(f"uA/uB TEMIZ olmaliydi (T-sekilli hol dogrudan acilir): {warnings}")
    return errors


# --------------------------------------------------------------------------
# 7) check_wet_area_door_proximity (DEV-043)
# --------------------------------------------------------------------------

def _wet_area_proximity_fixture(distance: float) -> tuple[list[dict], list[dict], list[dict]]:
    """Iki islak hacim kapisinin orta noktalari TAM (0,0) ve (`distance`,0)
    olacak sekilde - mesafe ELLE dogrulanabilir (oklid mesafesi =
    `distance`, cunku ikisi de y=0'da)."""
    rooms = [
        {"id": "banyo", "unit_id": "u1", "room_type": "banyo", "area_m2": 4.0,
         "polygon": [[-500, 0], [500, 0], [500, 2000], [-500, 2000]]},
        {"id": "wc", "unit_id": "u1", "room_type": "wc", "area_m2": 4.0,
         "polygon": [[distance - 500, 0], [distance + 500, 0],
                     [distance + 500, 2000], [distance - 500, 2000]]},
    ]
    walls = [
        {"id": "w_banyo", "start": [-500.0, 0.0], "end": [500.0, 0.0],
         "thickness": 200.0, "layer": "DUVARLAR"},
        {"id": "w_wc", "start": [distance - 500.0, 0.0], "end": [distance + 500.0, 0.0],
         "thickness": 200.0, "layer": "DUVARLAR"},
    ]
    openings = [
        {"id": "d_banyo", "type": "door", "wall_id": "w_banyo",
         "position_from_start": 500.0, "width": 900.0, "layer": "KAPI-PENCERE"},
        {"id": "d_wc", "type": "door", "wall_id": "w_wc",
         "position_from_start": 500.0, "width": 900.0, "layer": "KAPI-PENCERE"},
    ]
    return rooms, walls, openings


def check_wet_area_door_proximity_flags_far_doors() -> list[str]:
    """Iki islak hacim kapisi TAM 6000mm uzakta (ELLE: (0,0)-(6000,0)
    oklid mesafesi = 6000), varsayilan ust sinir 5000mm'yi asiyor -> TAM
    1 uyari, mesafe metninde 6000 GECMELI."""
    rooms, walls, openings = _wet_area_proximity_fixture(distance=6000.0)
    warnings = check_wet_area_door_proximity(rooms, walls, openings)
    if len(warnings) != 1:
        return [f"1 uyari beklenirdi, {len(warnings)} geldi: {warnings}"]
    if "6000" not in warnings[0]:
        return [f"uyari mesafeyi (6000mm) ICERMELIYDI: {warnings[0]}"]
    return []


def check_wet_area_door_proximity_false_positive_close() -> list[str]:
    """AYNI kurulum ama mesafe 3000mm (varsayilan 5000mm sinirinin
    ALTINDA) -> uyari OLMAMALI."""
    rooms, walls, openings = _wet_area_proximity_fixture(distance=3000.0)
    warnings = check_wet_area_door_proximity(rooms, walls, openings)
    return [f"sinir altindaki bir mesafe uyari URETMEMELIYDI: {warnings}"] if warnings else []


def check_wet_area_door_proximity_custom_threshold() -> list[str]:
    """`max_distance` OVERRIDE parametresi gercekten calisiyor mu - AYNI
    3000mm mesafe, ama esik 2000mm'ye DUSURULUNCE artik UYARI VERMELI."""
    rooms, walls, openings = _wet_area_proximity_fixture(distance=3000.0)
    warnings = check_wet_area_door_proximity(rooms, walls, openings, max_distance=2000.0)
    if len(warnings) != 1:
        return [f"dusuk esikle 1 uyari beklenirdi, {len(warnings)} geldi: {warnings}"]
    return []


def check_wet_area_door_proximity_real_project_clean() -> list[str]:
    """GERCEK projede uA/uB banyo-wc kapi mesafesi 4016mm (elle olculmus,
    rev-22) - varsayilan 5000mm sinirinin ALTINDA, bu yuzden GERCEK
    projede SIFIR uyari beklenir (bu, `DEFAULT_WET_AREA_DOOR_MAX_DISTANCE`
    secilirken KASITLI bir kalibrasyon noktasiydi, bkz. rules.py). Gercek
    dosya yoksa test ATLANIR."""
    if not REAL_CONTEXT_PATH.exists():
        return []
    context = json.loads(REAL_CONTEXT_PATH.read_text(encoding="utf-8"))
    floor = next(f for f in context["floors"] if f["id"] == "normal1")
    rooms, walls, openings = floor["rooms"], floor["walls"], floor["openings"]
    warnings = check_wet_area_door_proximity(rooms, walls, openings)
    return [f"GERCEK proje TEMIZ olmaliydi: {warnings}"] if warnings else []


def check_wet_area_checks_are_opt_in() -> list[str]:
    """Her iki YENI kural da `unit_id` OPT-IN'dir (diger dort kuralla AYNI
    desen) - AYNI ihlal geometrileri ama `unit_id` bellek-ici SOYULUNCE
    HICBIR uyari URETMEMELI."""
    errors: list[str] = []
    rooms, walls, openings = _wet_area_chain_fixture(direct_bypass=False)
    stripped = [{k: v for k, v in r.items() if k != "unit_id"} for r in rooms]
    warnings = check_wet_area_reachable_without_bedroom(stripped, walls, openings)
    if warnings:
        errors.append(f"unit_id SOYULUNCE erisim kurali SESSIZ KALMALIYDI: {warnings}")

    rooms2, walls2, openings2 = _wet_area_proximity_fixture(distance=6000.0)
    stripped2 = [{k: v for k, v in r.items() if k != "unit_id"} for r in rooms2]
    warnings2 = check_wet_area_door_proximity(stripped2, walls2, openings2)
    if warnings2:
        errors.append(f"unit_id SOYULUNCE yakinlik kurali SESSIZ KALMALIYDI: {warnings2}")
    return errors


# --------------------------------------------------------------------------
# check_common_circulation_share (DEV-045)
# --------------------------------------------------------------------------

def check_common_circulation_share_flags_oversized_band() -> list[str]:
    """2 birim (u1=50, u2=50 -> toplam=100) + ORTAK (unit_id YOK) koridor
    20 m2 -> pay %20 > varsayilan ust sinir %15 -> TAM 1 uyari."""
    rooms = [
        {"id": "u1_salon", "unit_id": "u1", "room_type": "salon", "area_m2": 50.0},
        {"id": "u2_salon", "unit_id": "u2", "room_type": "salon", "area_m2": 50.0},
        {"id": "band", "room_type": "koridor", "area_m2": 20.0},
    ]
    warnings = check_common_circulation_share(rooms)
    if len(warnings) != 1:
        return [f"1 uyari beklenirdi, {len(warnings)} geldi: {warnings}"]
    return []


def check_common_circulation_share_false_positive_within_limit() -> list[str]:
    """AYNI birimler ama ortak koridor 10 m2 -> pay %10 < %15, uyari OLMAMALI."""
    rooms = [
        {"id": "u1_salon", "unit_id": "u1", "room_type": "salon", "area_m2": 50.0},
        {"id": "u2_salon", "unit_id": "u2", "room_type": "salon", "area_m2": 50.0},
        {"id": "band", "room_type": "koridor", "area_m2": 10.0},
    ]
    warnings = check_common_circulation_share(rooms)
    return [f"esik ICINDEKI bir oran uyari URETMEMELIYDI: {warnings}"] if warnings else []


def check_common_circulation_share_ignores_non_corridor_common_rooms() -> list[str]:
    """YANLIS-POZITIF: `unit_id`siz ama `room_type` 'koridor' OLMAYAN bir
    oda (orn. ortak depo) ORTAK SIRKULASYON sayilmamali - buyuk bir 'depo'
    odasi payi SISIRMEMELI."""
    rooms = [
        {"id": "u1_salon", "unit_id": "u1", "room_type": "salon", "area_m2": 50.0},
        {"id": "depo", "room_type": "depo", "area_m2": 30.0},
    ]
    warnings = check_common_circulation_share(rooms)
    return [f"koridor OLMAYAN ortak oda payi SISIRMEMELIYDI: {warnings}"] if warnings else []


def check_common_circulation_share_differs_from_per_unit_check() -> list[str]:
    """`check_circulation_area_share` (birim-ici) ile `check_common_
    circulation_share` (ortak/bina-seviyesi) BIRBIRININ YERINE GECMEZ -
    unit_id'Lİ bir hol (birim-ici) ORTAK sirkulasyon sayilmamali."""
    rooms = [
        {"id": "u1_hol", "unit_id": "u1", "room_type": "koridor", "area_m2": 20.0},
        {"id": "u1_salon", "unit_id": "u1", "room_type": "salon", "area_m2": 80.0},
    ]
    common_warnings = check_common_circulation_share(rooms)
    return ([f"unit_id'li bir hol ORTAK sirkulasyon SAYILMAMALIYDI: {common_warnings}"]
            if common_warnings else [])


def check_common_circulation_share_real_project_catches_old_band() -> list[str]:
    """GERCEK projede (normal1), 'band' (71.7 m2, unit_id YOK, koridor)
    hala eski ISRAFLI L-sekli ile - ortak sirkulasyon payi kattaki UC
    birimin TOPLAM net alaninin (260 m2) %27.6'si, varsayilan ust sinir
    %15'i ACIKCA asiyor -> TAM 1 uyari GERCEKTEN yakalanmali. Bu, DEV-045
    Fikir 2'nin (templates duzeltmesi) context.json'a HENUZ UYGULANMADIGINI
    da dogrudan kanitlar. Gercek dosya yoksa test ATLANIR."""
    if not REAL_CONTEXT_PATH.exists():
        return []
    context = json.loads(REAL_CONTEXT_PATH.read_text(encoding="utf-8"))
    floor = next(f for f in context["floors"] if f["id"] == "normal1")
    warnings = check_common_circulation_share(floor["rooms"])
    if len(warnings) != 1:
        return [f"GERCEK projede 1 uyari (eski israfli 'band') beklenirdi: {warnings}"]
    if "band" not in warnings[0] and "27.6" not in warnings[0]:
        return [f"uyari eski 'band' ihlalini YANSITMALIYDI: {warnings[0]}"]
    return []


def check_common_circulation_share_clean_with_templates_fix() -> list[str]:
    """DEV-045'in İKİ fikri BİRBİRİYLE TUTARLI: `templates::generate_
    circulation_core`nin duzelttigi 'band' alanini (30.0 m2, eski 71.7
    m2 yerine) GERCEK projenin unit alanlariyla (260 m2) birlikte
    kullanınca pay %11.5'e duser (< %15) -> uyari KALMAZ. Fikir 1
    (bu kural) DENETLER, Fikir 2 (template) DUZELTIR - ikisi birlikte
    sorunu GERCEKTEN cozer, cakisma YOK."""
    if not REAL_CONTEXT_PATH.exists():
        return []
    context = json.loads(REAL_CONTEXT_PATH.read_text(encoding="utf-8"))
    floor = next(f for f in context["floors"] if f["id"] == "normal1")
    rooms = [dict(r) for r in floor["rooms"]]
    for room in rooms:
        if room["id"] == "band":
            room["area_m2"] = 30.0  # templates::generate_circulation_core (DEV-045) degeri
    warnings = check_common_circulation_share(rooms)
    return [f"duzeltilmis 'band' ile uyari KALMAMALIYDI: {warnings}"] if warnings else []


def check_real_project_is_clean_after_rev22_redesign() -> list[str]:
    """rev-22'de uA/uB/uC'nin BACK BAND'i (hol/mutfak/banyo/wc/oda) yeniden
    tasarlandi. GERCEK projede artik circulation-share/bedroom-via-corridor/
    entry-sightline UCU DA sifir uyari vermeli (check_door_core_balance
    HARIC - bu, templates::generate_circulation_core'un cekirdegi HER ZAMAN
    sol-alt kosede sabitlemesinden kaynaklanan YAPISAL bir sinirlamadir,
    bkz. context.json rev-22 ozeti - bu revizyonun kapsami DISINDA
    birakildi, DEV-040 Fikir 4'un isaret ettigi gelecek calisma). Gercek
    dosya yoksa test ATLANIR."""
    if not REAL_CONTEXT_PATH.exists():
        return []
    context = json.loads(REAL_CONTEXT_PATH.read_text(encoding="utf-8"))
    errors: list[str] = []
    for floor in context["floors"]:
        if floor["id"] not in ("normal1", "normal2", "normal3", "normal4", "normal5"):
            continue
        rooms, walls, openings = floor["rooms"], floor["walls"], floor["openings"]
        share_warnings = check_circulation_area_share(rooms)
        bedroom_warnings = check_bedroom_via_corridor(rooms, walls, openings)
        sightline_warnings = check_entry_sightlines(rooms, walls, openings)
        if share_warnings:
            errors.append(f"[{floor['id']}] hol-orani ihlali HALA VAR: {share_warnings}")
        if bedroom_warnings:
            errors.append(f"[{floor['id']}] yatak odasi-salon komsulugu HALA VAR: {bedroom_warnings}")
        if sightline_warnings:
            errors.append(f"[{floor['id']}] giris-WC goru hatti HALA VAR: {sightline_warnings}")
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
        ("hol->oda->banyo zinciri (DEV-042) UYARI verir", check_wet_area_blocked_by_bedroom_flags()),
        ("hol->banyo DOGRUDAN bypass'i YANLIS-POZITIF uretmez", check_wet_area_direct_bypass_false_positive()),
        ("GERCEK projede uC_hol->uC_oda->uC_banyo zinciri YAKALANIR", check_wet_area_real_project_catches_uC_chain()),
        ("uzak islak hacim kapilari (DEV-043) UYARI verir", check_wet_area_door_proximity_flags_far_doors()),
        ("yakin islak hacim kapilari YANLIS-POZITIF uretmez", check_wet_area_door_proximity_false_positive_close()),
        ("max_distance OVERRIDE parametresi calisir", check_wet_area_door_proximity_custom_threshold()),
        ("GERCEK projede uA/uB banyo-wc mesafesi (4016mm) TEMIZ", check_wet_area_door_proximity_real_project_clean()),
        ("DEV-042/043 ikisi de unit_id OPT-IN'dir", check_wet_area_checks_are_opt_in()),
        ("ortak sirkulasyon payi esigi asinca UYARI verir (DEV-045)", check_common_circulation_share_flags_oversized_band()),
        ("esik icindeki ortak sirkulasyon payi YANLIS-POZITIF uretmez", check_common_circulation_share_false_positive_within_limit()),
        ("koridor OLMAYAN ortak oda payi SISIRMEZ", check_common_circulation_share_ignores_non_corridor_common_rooms()),
        ("birim-ici hol, ORTAK sirkulasyon ile KARISTIRILMAZ", check_common_circulation_share_differs_from_per_unit_check()),
        ("GERCEK projede eski israfli 'band' YAKALANIR", check_common_circulation_share_real_project_catches_old_band()),
        ("templates DEV-045 duzeltmesiyle pay TEMIZ olur (Fikir 1+2 tutarli)", check_common_circulation_share_clean_with_templates_fix()),
        ("GERCEK proje rev-22 sonrasi TEMIZ (hol/yatak-salon/goru-hatti)", check_real_project_is_clean_after_rev22_redesign()),
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
