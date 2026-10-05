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


def check_wet_area_real_project_uC_fixed_rev23() -> list[str]:
    """GERCEK projede (`normal1`), rev-22'de uC_hol'un TEK komsusu HALA
    uC_oda idi (uC_banyo'ya yatak odasindan GECMEDEN ulasan bir yol
    YOKTU - kullanicinin 'koridor->hol->oda->banyo' sikayetinin somut bir
    ornegi, bkz. DEV-042 COMPLETED ozeti). rev-23'te uC TAMAMEN yeniden
    zonlandi: Hol artik dar bir bacak + iki kisa tam-genislik "strip"ten
    olusan bir sekille Salon/Banyo/WC/Oda'nin HER BIRINE BAGIMSIZ acilir
    (bkz. scripts/architect/CLAUDE.md). Bu yuzden ne uC_banyo ne de
    (rev-23'te eklenen) uC_wc icin bir zincir uyarisi BEKLENMEMELI -
    ikisi de HER ZAMAN Hol'den, yatak odasindan (uC_oda) GECMEDEN
    erisilebilir. uA/uB zaten TEMIZDI, oyle kalmali. Gercek dosya yoksa
    test ATLANIR."""
    if not REAL_CONTEXT_PATH.exists():
        return []
    context = json.loads(REAL_CONTEXT_PATH.read_text(encoding="utf-8"))
    floor = next(f for f in context["floors"] if f["id"] == "normal1")
    rooms, walls, openings = floor["rooms"], floor["walls"], floor["openings"]
    warnings = check_wet_area_reachable_without_bedroom(rooms, walls, openings)
    if warnings:
        return [f"rev-23 sonrasi TUM islak hacimler TEMIZ olmaliydi: {warnings}"]
    return []


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


def check_real_project_is_clean_after_rev23_redesign() -> list[str]:
    """rev-22 uC'yi 'salon-banyo-oda-hol' olarak yeniden sıraladi ama
    uC_hol'un TEK komsusu HALA uC_oda idi (bu test o zaman BASARISIZDI -
    gercek duzeltme BILEREK rev-22'nin kapsami DISINDA birakilmisti, bkz.
    DEV-042 COMPLETED ozeti). rev-23'te uA/uB/uC'nin BACK BAND'i (hol/
    banyo/wc/oda) GERCEKTEN yeniden tasarlandi. GERCEK projede artik
    circulation-share/bedroom-via-corridor/entry-sightline UCU DA sifir
    uyari vermeli (check_door_core_balance HARIC - bu, templates::
    generate_circulation_core'un cekirdegi HER ZAMAN sol-alt kosede
    sabitlemesinden kaynaklanan YAPISAL bir sinirlamadir, DEV-040 Fikir
    4'un isaret ettigi gelecek calisma, bu revizyonun kapsami DISINDA).
    Gercek dosya yoksa test ATLANIR."""
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
        # rev-24: uC (1+1, 68.5 m2) hol payi %16.2 - giris kapisi savrulma
        # gecisi kurali (hol derinligi >=1900) yuzunden BILINEN, belgeli
        # uyari (docs HD-035); uC DISINDAKI birimlerde hala TEMIZ olmali.
        share_warnings = [w for w in share_warnings if "'uC'" not in w]
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



def _w(i, s, e, t=100.0):
    return {"id": i, "start": s, "end": e, "thickness": t, "layer": "D"}


def check_dev050_door_window_nuances() -> list[str]:
    """DEV-050 madde 4, 12, 13, 14 - elle kurulmus minik plan."""
    from architect import (check_entry_door_swing_inward, check_kitchen_wet_door_opposite,
                           check_wet_door_swing_inward, check_wet_door_window_gap)
    errors: list[str] = []
    hol = {"id": "hol", "room_type": "koridor", "unit_id": "A",
           "polygon": [[0, 0], [4000, 0], [4000, 1500], [0, 1500]]}
    wc = {"id": "wc", "room_type": "wc", "unit_id": "A",
          "polygon": [[0, -1500], [1500, -1500], [1500, 0], [0, 0]]}
    kitchen = {"id": "mut", "room_type": "mutfak", "unit_id": "A",
               "polygon": [[0, 1500], [1500, 1500], [1500, 3000], [0, 3000]]}
    walls = [_w("w_wc", [0, 0], [4000, 0]), _w("w_k", [0, 1500], [1500, 1500])]
    wc_door = {"id": "dwc", "type": "door", "wall_id": "w_wc", "position_from_start": 750,
               "width": 800, "host_side": "neg"}   # normal +y: 'neg' -> WC'ye (ice)
    rooms = [hol, wc, kitchen]
    # madde 12
    if check_wet_door_swing_inward(rooms, walls, [wc_door]):
        errors.append("WC'ye ice acilan kapi UYARI vermemeli (yanlis-pozitif)")
    out = {**wc_door, "host_side": "pos"}
    if not any("kendi hacmine degil" in w for w in check_wet_door_swing_inward(rooms, walls, [out])):
        errors.append("hole acilan WC kapisi UYARI vermeli")
    # madde 14: mutfak kapisi wc kapisiyla ayni eksende
    k_door = {"id": "dk", "type": "door", "wall_id": "w_k", "position_from_start": 750, "width": 800}
    if not any("karsi karsiya" in w for w in check_kitchen_wet_door_opposite(rooms, walls, [wc_door, k_door])):
        errors.append("eksenli mutfak/wc kapisi UYARI vermeli")
    far_k = {"id": "mut2", "room_type": "mutfak", "unit_id": "A",
             "polygon": [[2500, 1500], [4000, 1500], [4000, 3000], [2500, 3000]]}
    walls2 = walls + [_w("w_k2", [2500, 1500], [4000, 1500])]
    k2 = {"id": "dk2", "type": "door", "wall_id": "w_k2", "position_from_start": 750, "width": 800}
    if check_kitchen_wet_door_opposite([hol, wc, far_k], walls2, [wc_door, k2]):
        errors.append("2500mm kayik mutfak kapisi UYARI vermemeli (yanlis-pozitif)")
    # madde 4: ayni duvarda pencere cok yakin / uzak
    win_near = {"id": "win", "type": "window", "wall_id": "w_wc", "position_from_start": 1400, "width": 600}
    if not any("Islak hacim kapisi" in w for w in check_wet_door_window_gap(rooms, walls, [wc_door, win_near])):
        errors.append("yakin pencere UYARI vermeli")
    win_far = {**win_near, "id": "win2", "position_from_start": 3000}
    if check_wet_door_window_gap(rooms, walls, [wc_door, win_far]):
        errors.append("uzak pencere UYARI vermemeli")
    # madde 13
    unit_room = {"id": "U", "unit_id": "A", "room_type": "salon",
                 "polygon": [[0, 0], [3000, 0], [3000, 3000], [0, 3000]]}
    common = {"id": "C", "polygon": [[0, -2000], [3000, -2000], [3000, 0], [0, 0]]}
    ew = [_w("e", [0, 0], [3000, 0])]
    entry = {"id": "ent", "type": "door", "wall_id": "e", "position_from_start": 1500, "width": 1000, "host_side": "pos"}
    if check_entry_door_swing_inward([unit_room, common], ew, [entry]):
        errors.append("birime ice acilan giris kapisi UYARI vermemeli")
    if not any("ortak alana" in w for w in check_entry_door_swing_inward(
            [unit_room, common], ew, [{**entry, "host_side": "neg"}])):
        errors.append("ortak alana acilan giris kapisi UYARI vermeli")
    return errors


def check_dev051_doors_open_into_rooms() -> list[str]:
    from architect import check_doors_open_into_rooms
    errors: list[str] = []
    hol = {"id": "hol", "room_type": "koridor", "unit_id": "A",
           "polygon": [[0, 0], [4000, 0], [4000, 1500], [0, 1500]]}
    oda = {"id": "oda", "room_type": "yatak_odasi", "unit_id": "A",
           "polygon": [[0, 1500], [3000, 1500], [3000, 4000], [0, 4000]]}
    walls = [_w("w", [0, 1500], [3000, 1500])]
    # duvar +x yonlu: normal +y -> 'pos' ODAYA, 'neg' HOLE acilir
    door = {"id": "d", "type": "door", "wall_id": "w", "position_from_start": 1500, "width": 800, "host_side": "pos"}
    if check_doors_open_into_rooms([hol, oda], walls, [door]):
        errors.append("odaya acilan kapi UYARI vermemeli (yanlis-pozitif)")
    if not any("sirkulasyon alanina" in w for w in check_doors_open_into_rooms([hol, oda], walls, [{**door, "host_side": "neg"}])):
        errors.append("hole acilan oda kapisi UYARI vermeli")
    if check_doors_open_into_rooms([hol, oda], walls, [{**door, "host_side": "neg"}], swing_policy="any"):
        errors.append("swing_policy='any' kontrolu kapatmali")
    if check_doors_open_into_rooms([hol, oda], walls, [{**door, "host_side": "neg", "variant": "sliding"}]):
        errors.append("surme kapi odaya donmez: UYARI olmamali")
    return errors


def check_dev051_shops_not_residential() -> list[str]:
    from architect import check_commercial_door_swing, check_doors_open_into_rooms
    errors: list[str] = []
    band = {"id": "band", "room_type": "koridor",
            "polygon": [[0, 0], [4000, 0], [4000, 1500], [0, 1500]]}
    shop = {"id": "dk", "room_type": "dukkan",
            "polygon": [[0, 1500], [3000, 1500], [3000, 4000], [0, 4000]]}
    walls = [_w("w", [0, 1500], [3000, 1500])]
    inward = {"id": "d", "type": "door", "wall_id": "w", "position_from_start": 1500, "width": 1000, "host_side": "pos"}  # dukkana
    outward = {**inward, "host_side": "neg"}                                                                          # banda
    if check_doors_open_into_rooms([band, shop], walls, [outward]):
        errors.append("dukkan konut sayilmaz: konut kurali dukkan kapisina UYGULANMAMALI")
    if not any("kacis yonunde" in w for w in check_commercial_door_swing([band, shop], walls, [inward])):
        errors.append("dukkana ice acilan kapi UYARI vermeli")
    if check_commercial_door_swing([band, shop], walls, [outward]):
        errors.append("ortak alana acilan dukkan kapisi UYARI vermemeli (yanlis-pozitif)")
    if check_commercial_door_swing([band, shop], walls, [inward], shop_swing_policy="any"):
        errors.append("shop_swing_policy='any' kontrolu kapatmali")
    # kasitli bozma: ayni geometri 'yatak_odasi' ise KONUT kurali devreye girer
    shop2 = {**shop, "room_type": "yatak_odasi", "unit_id": "A"}
    band2 = {**band, "unit_id": "A"}
    if not check_doors_open_into_rooms([band2, shop2], walls, [outward]):
        errors.append("ayni geometri yatak odasiysa konut kurali UYARI vermeli")
    return errors


def check_dev052_wet_area_adjacency() -> list[str]:
    """DEV-052: ortak duvar + ayni hat + oda kapilarindan uzaklik. ELLE kurulu
    plan: hol y 0-1500; banyo x0-1500, WC x1500-2500, salon x2500-4000 (y 1500-3500)."""
    from architect import check_wet_area_adjacency
    errors: list[str] = []
    P = lambda x0, y0, x1, y1: [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]
    hol = {"id": "hol", "room_type": "koridor", "unit_id": "A", "polygon": P(0, 0, 4000, 1500)}
    banyo = {"id": "ban", "room_type": "banyo", "unit_id": "A", "polygon": P(0, 1500, 1500, 3500)}
    wc = {"id": "wc", "room_type": "wc", "unit_id": "A", "polygon": P(1500, 1500, 2500, 3500)}
    salon = {"id": "sal", "room_type": "salon", "unit_id": "A", "polygon": P(2500, 1500, 4000, 3500)}
    walls = [_w("w_b", [0, 1500], [1500, 1500]), _w("w_w", [1500, 1500], [2500, 1500]),
             _w("w_s", [2500, 1500], [4000, 1500])]
    def door(i, wid, pos): return {"id": i, "type": "door", "wall_id": wid, "position_from_start": pos, "width": 800}
    base = [door("db", "w_b", 750), door("dw", "w_w", 500), door("ds", "w_s", 1000)]  # banyo x750, wc x2000, salon x3500
    if check_wet_area_adjacency([hol, banyo, wc, salon], walls, base):
        errors.append(f"ortak duvar + ayni hat + salon kapisi uzak: UYARI olmamali (yanlis-pozitif): "
                      f"{check_wet_area_adjacency([hol, banyo, wc, salon], walls, base)}")
    # salon kapisi yakin (x3100: wc kapisina 1100 < cift 1250)
    near = [base[0], base[1], door("ds", "w_s", 600)]
    if not any("mumkun oldugunca uzak" in w for w in check_wet_area_adjacency([hol, banyo, wc, salon], walls, near)):
        errors.append("yakin salon kapisi UYARI vermeli")
    # sirt sirta: WC kapisi karsi duvarda (y=3500), banyo y=1500 -> farkli hat
    walls_b = walls + [_w("w_back", [1500, 3500], [2500, 3500])]
    back = [base[0], door("dw", "w_back", 500), base[2]]
    if not any("ayni hatta degil" in w for w in check_wet_area_adjacency([hol, banyo, wc, salon], walls_b, back)):
        errors.append("sirt sirta kapilar UYARI vermeli")
    # ortak duvar yok: WC 500mm saga kaydi (banyo x0-1500, wc x2000-3000)
    wc_far = {**wc, "polygon": P(2000, 1500, 3000, 3500)}
    got = check_wet_area_adjacency([hol, banyo, wc_far, salon], walls, base)
    if not any("ortak duvar" in w for w in got):
        errors.append("ortak duvarsiz WC/banyo UYARI vermeli")
    if any("ortak duvar" in w for w in check_wet_area_adjacency([hol, banyo, wc_far, salon], walls, base, require_shared_wall=False)):
        errors.append("require_shared_wall=False ortak duvar uyarisini kapatmali")
    # kose temasi ortak duvar SAYILMAZ
    wc_corner = {**wc, "polygon": P(1500, 3500, 2500, 5500)}
    if not any("ortak duvar" in w for w in check_wet_area_adjacency([hol, banyo, wc_corner, salon], walls, base)):
        errors.append("yalniz kose temasi ortak duvar sayilmamali")
    return errors


def check_dev053_entry_wet_door_proximity() -> list[str]:
    """DEV-053 (+DEV-050 #15): giris kapisi ile WC kapisi -> temiz aralik 250 ve
    capraz onde olmama. Birim: sal (y>=0), ortak band (y<0); giris kapisi y=0
    duvarinda x=1000 (900 genis), normal birime (+y)."""
    from architect import check_entry_wet_door_proximity
    errors: list[str] = []
    P = lambda x0, y0, x1, y1: [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]
    band = {"id": "band", "polygon": P(0, -2000, 6000, 0)}
    hol = {"id": "hol", "unit_id": "A", "room_type": "koridor", "polygon": P(0, 0, 6000, 1500)}
    wc = {"id": "wc", "unit_id": "A", "room_type": "wc", "polygon": P(0, 1500, 6000, 3000)}
    rooms = [band, hol, wc]
    walls = [_w("w_in", [0, 0], [6000, 0]), _w("w_wc", [0, 1500], [6000, 1500])]
    entry = {"id": "ent", "type": "door", "wall_id": "w_in", "position_from_start": 1000, "width": 900}
    def wc_door(x): return {"id": "dwc", "type": "door", "wall_id": "w_wc", "position_from_start": x, "width": 800}
    # capraz onde: WC kapisi x=2300 (y=1500): sapma atan(1300/1500)=41 -> dar koniye girer (sightlines);
    # x=2900: atan(1900/1500)=51.7 derece, mesafe 2420 -> capraz bandi -> UYARI
    if not any("capraz onunde" in w for w in check_entry_wet_door_proximity(rooms, walls, [entry, wc_door(2900)])):
        errors.append("52 derece capraz WC kapisi UYARI vermeli")
    # 70+ derece (x=5000: atan(4000/1500)=69) -> bant disi, mesafe 4272 > 3000 -> UYARI yok
    if check_entry_wet_door_proximity(rooms, walls, [entry, wc_door(5000)]):
        errors.append("uzak/yan WC kapisi UYARI vermemeli (yanlis-pozitif)")
    # dar koni (x=1100: ~3 derece) sightlines'in alani: burada TEKRARLANMAZ
    got = check_entry_wet_door_proximity(rooms, walls, [entry, wc_door(1100)])
    if any("capraz onunde" in w for w in got):
        errors.append("dar koni (<=45) bu kuralda tekrarlanmamali")
    # temiz aralik: giris x=1000 (550-1450 degil: 1000+-450), WC kapisi ayni duvarda degil;
    # merkez mesafe = sqrt((1100-1000)^2+1500^2)=1503 -> aralik 1503-850=653 (>=250, UYARI yok)
    if any("temiz aralik" in w for w in got):
        errors.append("653mm aralik UYARI vermemeli")
    # kasitli bozma: WC kapisi giris kapisina yapisik (ayni duvar, merkezler 900 -> aralik 50)
    walls2 = [_w("w_in", [0, 0], [6000, 0])]
    rooms2 = [band, {**hol, "room_type": "wc"}]
    close = {"id": "dwc2", "type": "door", "wall_id": "w_in", "position_from_start": 1900, "width": 800}
    got = check_entry_wet_door_proximity(rooms2, walls2, [entry, close])
    if not any("temiz aralik 50mm" in w for w in got):
        errors.append(f"50mm aralik UYARI vermeli: {got}")
    return errors


def check_dev054_hall_topology() -> list[str]:
    """DEV-054: hol topolojisi adaylari. Birim 6000x9000, giris alt, n_rooms=4,
    kapi 900, duvar 100 -> hol genisligi 1500+100=1600. ELLE hesaplar:
    duz: 1600x9000=14.4 m2, pay 14.4/54=%26.67; L: 14.4M+4400*1600=21.44 m2."""
    from architect import (DEFAULT_TOPOLOGIES, options_for_hall_topology, register_topology)
    from architect.topology import TOPOLOGY_BUILDERS
    errors: list[str] = []
    opts = {o.id: o for o in options_for_hall_topology(6000.0, 9000.0)}
    if set(opts) != set(DEFAULT_TOPOLOGIES) or "tarak" in opts:
        errors.append(f"varsayilan adaylar tarak HARIC bes topoloji olmali: {sorted(opts)}")
    if abs(opts["duz"].area_m2 - 14.4) > 1e-6 or abs(opts["duz"].share - 14.4 / 54.0) > 1e-9:
        errors.append(f"duz hol 14.4 m2 / pay 0.2667 olmali: {opts['duz'].area_m2}, {opts['duz'].share}")
    if abs(opts["L"].area_m2 - 21.44) > 1e-6:
        errors.append(f"L hol 21.44 m2 olmali: {opts['L'].area_m2}")
    # duz puan: 0.4*1 + 0.35*(1-(0.2667-0.15)/0.15) + 0.25*1 - 0.001*4 = 0.72378
    if abs(opts["duz"].score - 0.7238) > 1e-3:
        errors.append(f"duz puan ~0.7238 olmali: {opts['duz'].score}")
    # merkezi hub'lar: kare 1800x1800, dikdortgen 2400x1600 (oran 1.5 KORUNUR)
    def hub_dims(o):
        xs = sorted({p[0] for p in o.polygon}); ys = sorted({p[1] for p in o.polygon})
        return xs[-1] - xs[0], max(y2 - y1 for y1, y2 in zip(ys, ys[1:]))
    sq = opts["merkezi_kare"].polygon; rc = opts["merkezi_dikdortgen"].polygon
    wsq = max(p[0] for p in sq) - min(p[0] for p in sq)
    wrc = max(p[0] for p in rc) - min(p[0] for p in rc)
    if abs(wsq - 1800.0) > 1e-6 or abs(wrc - 2400.0) > 1e-6:
        errors.append(f"hub genislikleri 1800 / 2400 olmali: {wsq}, {wrc}")
    # en iyi aday merkezi hub (en dusuk hol payi + yeterli cephe); sirali dondu mu
    ordered = options_for_hall_topology(6000.0, 9000.0)
    if [o.score for o in ordered] != sorted((o.score for o in ordered), reverse=True):
        errors.append("adaylar puana gore azalan siralanmali")
    # giris yonu: 'sol' -> hol x boyunca, y merkezde (3700-5300); 'ust' -> y=9000'dan baslar
    left = options_for_hall_topology(6000.0, 9000.0, entry_side="sol", allowed=("duz",))[0].polygon
    if (min(p[0] for p in left), max(p[0] for p in left), min(p[1] for p in left), max(p[1] for p in left)) != (0.0, 6000.0, 3700.0, 5300.0):
        errors.append(f"sol girisli duz hol x:0-6000, y:3700-5300 olmali: {left}")
    top = options_for_hall_topology(6000.0, 9000.0, entry_side="ust", allowed=("duz",))[0].polygon
    if max(p[1] for p in top) != 9000.0 or min(p[1] for p in top) != 0.0:
        errors.append("ust girisli duz hol tum derinligi kaplamali")
    # kullanici bildirimi: yalniz L + T; bilinmeyen / kayitsiz (tarak) ValueError
    only = options_for_hall_topology(6000.0, 9000.0, allowed=("L", "T"))
    if sorted(o.id for o in only) != ["L", "T"]:
        errors.append("allowed yalniz bildirilen adaylari donmeli")
    for bad in ("tarak", "yok"):
        try:
            options_for_hall_topology(6000.0, 9000.0, allowed=(bad,))
            errors.append(f"kayitsiz '{bad}' ValueError vermeli")
        except ValueError:
            pass
    # sigmayan birim (1500 < 1600 hol genisligi): feasible=False + gerekce, puan 0
    narrow = options_for_hall_topology(1500.0, 9000.0)
    if any(o.feasible or o.score != 0.0 for o in narrow):
        errors.append("1500mm genislikte hicbir aday uygulanabilir OLMAMALI")
    # genisletme noktasi: acili (dik acili olmayan) topoloji kaydi
    register_topology("capraz_test", "Capraz", lambda cw, cd, h, ctx: [[0, 0], [h, 0], [cw, cd], [cw - h, cd]])
    try:
        got = options_for_hall_topology(6000.0, 9000.0, allowed=("capraz_test",))[0]
        if got.metrics.get("rectilinear") is not False:
            errors.append("dik acili olmayan topoloji metrics.rectilinear=False olmali")
    finally:
        del TOPOLOGY_BUILDERS["capraz_test"]
    return errors


def check_dev055_central_hall_options() -> list[str]:
    """DEV-055: bes merkezi hol alternatifi. Kat 20000x17500, cekirdek 2100+4000
    = 6100 genis, hol derinligi = 6100/oran (asgari 1500+200=1700). ELLE:
    kare 6100 -> 37.21 m2 (%10.6); 3:2 4066.7 -> 24.81 m2; 2:1 3050 -> 18.61;
    3:1 2033.3 -> 12.40; asgari 1700 -> 10.37 m2. Blok ortada: x 6950..13050."""
    from architect import HALL_ALTERNATIVES, options_for_central_hall
    errors: list[str] = []
    opts = {o.id: o for o in options_for_central_hall(20000.0, 17500.0)}
    if len(opts) != 5 or len(HALL_ALTERNATIVES) != 5:
        errors.append("bes alternatif bekleniyordu")
    want = {"kare": 37.21, "dikdortgen_3_2": 24.81, "dikdortgen_2_1": 18.61,
            "koridor_3_1": 12.40, "koridor_min": 10.37}
    for k, a in want.items():
        if abs(opts[k].hall_area_m2 - a) > 0.01:
            errors.append(f"{k} alani {a} m2 olmali: {opts[k].hall_area_m2:.2f}")
    if abs(opts["koridor_min"].hall_depth - 1700.0) > 1e-6:
        errors.append("asgari koridor hol derinligi 1700 (1500 net + 200 duvar) olmali")
    k = opts["kare"]
    if (k.block[0], k.block[2]) != (6950.0, 13050.0) or k.margins["west"] != 6950.0 or k.margins["south"] != 4200.0:
        errors.append(f"kare blok x 6950..13050 ve payi 4200 olmali: {k.block}, {k.margins}")
    if not all(o.surrounds for o in opts.values()):
        errors.append("merkezdeki blok bu katta daireler icin dort kenardan cevrilebilir olmali")
    ordered = options_for_central_hall(20000.0, 17500.0)
    if [o.score for o in ordered] != sorted((o.score for o in ordered), reverse=True):
        errors.append("secenekler puana gore azalan siralanmali")
    if ordered[0].id != "dikdortgen_3_2":
        errors.append(f"ideal pay %7'ye en yakin 3:2 en yuksek puani almali: {ordered[0].id}")
    # kayma: 5000mm doguya kayinca dogu payi 1950 < 3000 -> cevrelenemez (daireler sigmaz)
    shifted = options_for_central_hall(20000.0, 17500.0, offset=(5000.0, 0.0))
    if any(o.surrounds for o in shifted) or any(not o.feasible for o in shifted):
        errors.append("5000mm kayma: uygulanabilir ama cevrelenemez olmali")
    # kata sigmayan blok (kat 6000 genis < 6100 cekirdek)
    if any(o.feasible for o in options_for_central_hall(6000.0, 17500.0)):
        errors.append("6000mm katta 6100mm blok uygulanabilir OLMAMALI")
    # yon: 'y' yonu blogu transpoze eder
    oy = options_for_central_hall(20000.0, 17500.0, orientation="y", allowed=("kare",))[0]
    # kanonik cerceve 17500x20000: blok x' (17500-6100)/2=5700..11800 (-> final y),
    # kare derinligi 6100+3000=9100 -> y' (20000-9100)/2=5450..14550 (-> final x)
    if oy.block != (5450.0, 5700.0, 14550.0, 11800.0):
        errors.append(f"y yonunde blok (5450,5700,14550,11800) olmali: {oy.block}")
    try:
        options_for_central_hall(20000.0, 17500.0, allowed=("yok",))
        errors.append("bilinmeyen alternatif ValueError vermeli")
    except ValueError:
        pass
    return errors


def check_dev056_study_zoning() -> list[str]:
    """DEV-056: etut 2D zonlama. Kat 20000x17500 = 350 m2."""
    from architect import (CURRENT_PROJECT_PROGRAM, StudyWeights, UNIT_TYPES,
                           options_for_central_hall, study_floor, suggest_unit_mixes)
    from architect.layout import _patterns, _union_polygon, _arcs, _split_to
    errors: list[str] = []
    # halka deseni: kare blok x 6950..13050, y 4200..13300 -> H-x ('1111': koseler dusey kenarlara):
    # W = 6950 x 17500 = 121.625 m2; S = 6100 x 4200 = 25.62 m2; toplam = 350 - 55.51 (blok) = 294.49
    blok = (6950.0, 4200.0, 13050.0, 13300.0)
    pats = _patterns(20000.0, 17500.0, blok)
    if len(pats) != 16:
        errors.append("16 halka deseni bekleniyordu")
    for name, secs in pats.items():
        total = sum((r[2] - r[0]) * (r[3] - r[1]) for r in secs)
        if abs(total - (350e6 - 6100 * 9100)) > 1:
            errors.append(f"desen {name}: bolumler halkayi tam kaplamali (294.49 m2): {total / 1e6:.2f}")
    hx = pats["1111"]
    if abs((hx[3][2] - hx[3][0]) * (hx[3][3] - hx[3][1]) / 1e6 - 121.625) > 1e-6:
        errors.append("H-x bati bolumu 121.625 m2 olmali")
    # birlesim poligonu: iki komsu dikdortgen -> L (6 kose) ; alani toplam
    L = _union_polygon([(0, 0, 4000, 2000), (0, 2000, 2000, 5000)])
    if len(L) != 6:
        errors.append(f"L birlesimi 6 kose olmali: {L}")
    # yaylar: 4 bolumden 3 yay -> 4 secenek (hangi komsu cift birlesir)
    if len(_arcs(4, 3)) != 4:
        errors.append(f"4 bolumden 3 yay 4 olmali: {len(_arcs(4, 3))}")
    if len(_split_to([(0, 0, 4000, 2000)], 2)) != 2:
        errors.append("bolme iki parca vermeli")
    # esas etut: mevcut proje kurgusu
    res = study_floor(20000.0, 17500.0, CURRENT_PROJECT_PROGRAM)
    again = study_floor(20000.0, 17500.0, CURRENT_PROJECT_PROGRAM)
    if [(o.id, o.score) for o in res] != [(o.id, o.score) for o in again]:
        errors.append("etut DETERMINISTIK olmali (ayni girdi -> ayni siralama)")
    if not res or not res[0].feasible:
        errors.append("mevcut kurgu icin uygulanabilir aday bekleniyordu")
    else:
        best = res[0]
        block = best.block
        total = sum(z.area_m2 for z in best.zones) + (block[2] - block[0]) * (block[3] - block[1]) / 1e6
        if abs(total - 350.0) > 0.05:
            errors.append(f"bolgeler + blok kat alanini (350 m2) tam kaplamali: {total:.2f}")
        for z in best.zones:
            if z.access_mm < 900.0 + 500.0 - 1e-6:
                errors.append(f"{z.unit_id}: hol cephesine temas yetersiz ({z.access_mm})")
            if z.area_m2 < UNIT_TYPES[z.unit_type].min_area_m2:
                errors.append(f"{z.unit_id}: alan asgarinin altinda")
        w = StudyWeights()
        if abs(w.area_fit + w.facade + w.proportion + w.hall_share + w.hall_option - 1.0) > 1e-9:
            errors.append("agirliklar toplami 1.0 olmali")
        # puan = agirlikli toplam (elle)
        b = best.breakdown
        want = (w.area_fit * b["area_fit"] + w.facade * b["facade"] + w.proportion * b["proportion"]
                + w.hall_share * b["hall_share"] + w.hall_option * b["hall_option"])
        if abs(want - best.score) > 1e-3:
            errors.append(f"puan agirlikli toplama esit olmali: {want} / {best.score}")
        # simetrik tekrar elenmeli: ayni (tip, alan) kumesi iki kez gelmemeli
        keys = [(o.hall_option, o.offset, tuple(sorted((z.unit_type, z.area_m2) for z in o.zones))) for o in res]
        if len(keys) != len(set(keys)):
            errors.append("simetrik/yer degistirmis esdegerler elenmeli")
    # agirlik DEGISIKLIGI siralamayi etkiler (ayarlanabilirlik): alan uyumu 0 -> farkli puan
    alt = study_floor(20000.0, 17500.0, CURRENT_PROJECT_PROGRAM,
                      weights=StudyWeights(area_fit=0.0, facade=0.5, proportion=0.2, hall_share=0.15, hall_option=0.15))
    if alt[0].score == res[0].score:
        errors.append("agirliklar degisince puan degismeli")
    # kullanici verisi zorunlu
    for bad in ((), (("a", "9+9"),), (("a", "2+1"), ("a", "1+1"))):
        try:
            study_floor(20000.0, 17500.0, bad)
            errors.append(f"gecersiz program ValueError vermeli: {bad}")
        except ValueError:
            pass
    # kasitli bozma / yanlis-pozitif: kat cok kucukse uygulanabilir aday YOK
    if any(o.feasible for o in study_floor(8000.0, 8000.0, CURRENT_PROJECT_PROGRAM)):
        errors.append("8000x8000 katta 3 daire uygulanabilir OLMAMALI")
    # N>4: bes birim (alan sirali acgozlu) - cokmeden aday uretir
    five = study_floor(30000.0, 25000.0, (("a", "1+1"), ("b", "1+1"), ("c", "2+1"), ("d", "2+1"), ("e", "1+1")))
    if not five:
        errors.append("bes birimlik program aday uretmeli")
    # dil modeli geri bildirimi: hesaplanmis karisim onerileri
    mixes = suggest_unit_mixes(20000.0, 17500.0)
    if not mixes or any(m["min_total_m2"] > m["available_m2"] for m in mixes):
        errors.append("onerilen her karisimin asgari toplami kullanilabilir alani asmamali")
    if suggest_unit_mixes(6000.0, 6000.0):
        errors.append("6000x6000 katta hicbir karisim onerilmemeli")
    return errors


def check_dev057_group_b_selection_and_refinement() -> list[str]:
    """DEV-057 Grup B: blok kaydirma iyilestirmesi + tercihe gore secim + merkezi hol geri donusu."""
    from architect import (CURRENT_PROJECT_PROGRAM, StudyPreference, select_study_option,
                           study_and_select, study_floor)
    from architect.layout import preference_closeness
    errors: list[str] = []
    W, D = 20000.0, 17500.0
    base = study_floor(W, D, CURRENT_PROJECT_PROGRAM, refine=False)
    refined = study_floor(W, D, CURRENT_PROJECT_PROGRAM)
    if refined[0].score < base[0].score - 1e-9:
        errors.append("kaydirma iyilestirmesi puani DUSURMEMELI")
    if not (refined[0].score > base[0].score and refined[0].offset != (0.0, 0.0)):
        errors.append(f"bu katta kaydirma puani yukseltmeli (0.9283 -> ~0.9295): {refined[0].score} / {base[0].score}")
    if any(abs(o.offset[0]) > 4000.0 or abs(o.offset[1]) > 4000.0 for o in refined):
        errors.append("kayma 4000mm sinirini asmamali")
    for o in refined:
        bx0, by0, bx1, by1 = o.block
        total = sum(z.area_m2 for z in o.zones) + (bx1 - bx0) * (by1 - by0) / 1e6
        if abs(total - 350.0) > 0.05:
            errors.append(f"{o.id}: bolgeler + blok 350 m2 olmali: {total:.2f}")
    if not any(abs(o.offset[0]) < 1 and abs(o.offset[1]) < 1 for o in refined):
        errors.append("merkezi (kaymasiz) surum listede KALMALI (geri donus)")
    if [(o.id, o.score) for o in refined] != [(o.id, o.score) for o in study_floor(W, D, CURRENT_PROJECT_PROGRAM)]:
        errors.append("iyilestirme DETERMINISTIK olmali")
    # tercih yakinligi: ELLE - hedef = gercek alan -> 1.0 ; hedef = 2x alan -> 1 - |a-2a|/2a = 0.5
    opt = base[0]
    z = opt.zones[0]
    c1, _ = preference_closeness(opt, StudyPreference(unit_area_m2={z.unit_id: z.area_m2}), W, D)
    c2, _ = preference_closeness(opt, StudyPreference(unit_area_m2={z.unit_id: 2 * z.area_m2}), W, D)
    if abs(c1 - 1.0) > 1e-9 or abs(c2 - 0.5) > 1e-9:
        errors.append(f"alan yakinligi 1.0 / 0.5 olmali: {c1}, {c2}")
    pool = study_floor(W, D, CURRENT_PROJECT_PROGRAM, top=60)
    # tercih yoksa -> geri donus: hol merkezde, en yuksek puanli
    fb = select_study_option(pool, None, W, D)
    centered = [o for o in pool if o.feasible and abs(o.offset[0]) < 1 and abs(o.offset[1]) < 1]
    if not fb.fallback or fb.option.id != max(centered, key=lambda o: (o.score, o.id)).id:
        errors.append("tercihsiz secim merkezi holun en iyisi (geri donus) olmali")
    # hol ailesi tercihi: koridor -> secilen aday koridor ailesinden, geri donus DEGIL
    sel = select_study_option(pool, StudyPreference(hall="koridor"), W, D)
    if sel.fallback or sel.option.hall_option not in ("koridor_3_1", "koridor_min"):
        errors.append(f"koridor tercihi koridor tipi hol secmeli: {sel.option.hall_option}, fallback={sel.fallback}")
    # alan tercihi: yakinlik >= 0.5 -> tercih eslesir
    sel = select_study_option(pool, StudyPreference(unit_area_m2={"uA": 100.0, "uB": 100.0, "uC": 65.0}), W, D)
    if sel.fallback or sel.closeness is None or sel.closeness < 0.5:
        errors.append("makul alan tercihi eslesmeli")
    # imkansiz tercih: uc birim de 'north' -> yakinlik 1/3 < 0.5 -> merkezi hol geri donusu
    sel = select_study_option(pool, StudyPreference(unit_side={"uA": "north", "uB": "north", "uC": "north"}), W, D)
    if not sel.fallback or not (abs(sel.option.offset[0]) < 1 and abs(sel.option.offset[1]) < 1):
        errors.append("hicbir aday tercihe yetmezse merkezi hol surumu secilmeli")
    # merkez=False tercihi kayik surumu secer
    sel = select_study_option(pool, StudyPreference(centered_hall=False), W, D)
    if sel.fallback or (abs(sel.option.offset[0]) < 1 and abs(sel.option.offset[1]) < 1):
        errors.append("centered_hall=False kaymis bir aday secmeli")
    # gecersiz tercih
    for bad in (StudyPreference(unit_area_m2={"uZ": 50.0}), StudyPreference(unit_side={"uA": "up"}),
                StudyPreference(hall="yok")):
        try:
            select_study_option(pool, bad, W, D)
            errors.append(f"gecersiz tercih ValueError vermeli: {bad}")
        except ValueError:
            pass
    sel2 = study_and_select(W, D, CURRENT_PROJECT_PROGRAM, StudyPreference(hall="kare"))
    if sel2.option.hall_option != "kare":
        errors.append("study_and_select kare tercihini secmeli")
    return errors


def main() -> int:
    groups = (
        ("etut: blok kaydirma + tercihe gore secim + merkezi hol geri donusu (DEV-057 Grup B)", check_dev057_group_b_selection_and_refinement()),
        ("etut 2D zonlama (DEV-056)", check_dev056_study_zoning()),
        ("merkezi kat holu: bes alternatif (DEV-055)", check_dev055_central_hall_options()),
        ("hol topolojisi adaylari (DEV-054)", check_dev054_hall_topology()),
        ("giris kapisi <-> WC kapisi: aralik + capraz (DEV-053)", check_dev053_entry_wet_door_proximity()),
        ("WC/banyo komsulugu: ortak duvar + ayni hat + oda kapilarindan uzak (DEV-052)", check_dev052_wet_area_adjacency()),
        ("dukkan konut sayilmaz, ayri kural (DEV-051 ek)", check_dev051_shops_not_residential()),
        ("kapilar odalara acilir (DEV-051)", check_dev051_doors_open_into_rooms()),
        ("kapi/pencere nuanslari (DEV-050 #4,12,13,14)", check_dev050_door_window_nuances()),
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
        ("GERCEK projede uC rev-23'te DUZELTILDI (zincir yok)", check_wet_area_real_project_uC_fixed_rev23()),
        ("uzak islak hacim kapilari (DEV-043) UYARI verir", check_wet_area_door_proximity_flags_far_doors()),
        ("yakin islak hacim kapilari YANLIS-POZITIF uretmez", check_wet_area_door_proximity_false_positive_close()),
        ("max_distance OVERRIDE parametresi calisir", check_wet_area_door_proximity_custom_threshold()),
        ("GERCEK projede uA/uB banyo-wc mesafesi (4016mm) TEMIZ", check_wet_area_door_proximity_real_project_clean()),
        ("DEV-042/043 ikisi de unit_id OPT-IN'dir", check_wet_area_checks_are_opt_in()),
        ("ortak sirkulasyon payi esigi asinca UYARI verir (DEV-045)", check_common_circulation_share_flags_oversized_band()),
        ("esik icindeki ortak sirkulasyon payi YANLIS-POZITIF uretmez", check_common_circulation_share_false_positive_within_limit()),
        ("koridor OLMAYAN ortak oda payi SISIRMEZ", check_common_circulation_share_ignores_non_corridor_common_rooms()),
        ("birim-ici hol, ORTAK sirkulasyon ile KARISTIRILMAZ", check_common_circulation_share_differs_from_per_unit_check()),
        ("GERCEK proje rev-23 sonrasi TEMIZ (hol/yatak-salon/goru-hatti)", check_real_project_is_clean_after_rev23_redesign()),
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
