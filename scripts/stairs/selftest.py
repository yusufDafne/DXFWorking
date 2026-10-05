#!/usr/bin/env python3
"""Merdiven modulu testleri (DEV-022).

Ortak disiplin (kok CLAUDE.md): beklenen degerler ELLE hesaplanabilir
tutulur, kurallar KASITLI BOZMAYLA sinanir, her kontrol ayrica bir
YANLIS-POZITIF tarafini da sinar ("temiz donmesi gereken durum gercekten
temiz donuyor mu").

Kullanim:
    python scripts/stairs/selftest.py
Cikis kodu: 0 basarili, 1 basarisiz.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import ezdxf  # noqa: E402

from stairs import (
    stair_section_profile,
    stair_access_warnings, stair_entry_side,  # noqa: E402
    DefaultStairStandard,
    StairFitError,
    _step_line_endpoints,  # ic yardimci - koordinat dogrulugu icin (bkz. asagi)
    ensure_stair_layer,
    resolve_stair,
    stairs_for_floor,
)

TOLERANCE = 1e-6

ROOM_5000x3000 = [[0, 0], [5000, 0], [5000, 3000], [0, 3000]]
ROOM_1300x800 = [[0, 0], [1300, 0], [1300, 800], [0, 800]]
ROOM_1500x800 = [[0, 0], [1500, 0], [1500, 800], [0, 800]]
ROOM_900x600 = [[0, 0], [900, 0], [900, 600], [0, 600]]
ROOM_10000x3000 = [[0, 0], [10000, 0], [10000, 3000], [0, 3000]]
# GERCEK projenin 'Merdiven' odasiyla BIREBIR AYNI (context.json, DEV-046) -
# tek kolun StairFitError ile reddettigi, dog_leg'in COZDUGU somut oda.
ROOM_4000x3000 = [[0, 0], [4000, 0], [4000, 3000], [0, 3000]]


def check_explicit_step_count_derives_riser() -> list[str]:
    """3000mm / 18 basamak = elle: 166.667mm riht. Nominal (170) farki
    3.33mm < tolerans (5mm) -> UYARI olmamali."""
    errors: list[str] = []
    spec = {"id": "sA", "room_id": "r1", "kind": "single_flight", "floor_to_floor_mm": 3000, "step_count": 18}
    res = resolve_stair(spec, ROOM_5000x3000)
    expected_riser = 3000 / 18
    if abs(res.riser_mm - expected_riser) > TOLERANCE:
        errors.append(f"riser {res.riser_mm} != elle hesap {expected_riser}")
    if res.going_mm != 270.0:
        errors.append(f"going varsayilani 270.0 olmali, {res.going_mm} bulundu")
    if res.warnings:
        errors.append(f"uyari beklenmiyordu: {res.warnings}")
    return errors


def check_auto_flex_true_adjusts_riser_with_warning() -> list[str]:
    """900mm / nominal 170 -> elle: round(900/170)=round(5.294)=5 basamak,
    riser=900/5=180.0mm. Fark 170 ile 10mm (>5mm tolerans) -> UYARI olmali."""
    errors: list[str] = []
    spec = {"id": "sB", "room_id": "r1", "kind": "single_flight", "floor_to_floor_mm": 900}
    res = resolve_stair(spec, ROOM_5000x3000)
    if res.step_count != 5:
        errors.append(f"step_count 5 bekleniyordu, {res.step_count} bulundu")
    if abs(res.riser_mm - 180.0) > TOLERANCE:
        errors.append(f"riser 180.0 bekleniyordu, {res.riser_mm} bulundu")
    if not any("esnetildi" in w for w in res.warnings):
        errors.append(f"riht esnetme UYARISI bekleniyordu, bulunan: {res.warnings}")
    return errors


def check_auto_flex_false_warns_without_adjusting() -> list[str]:
    """Ayni 900mm/5 basamak durumu ama auto_flex=False: riser NOMINAL
    (170) kalir, toplam 850mm kat yuksekligini (900mm) 50mm farkla
    KARSILAMAZ -> UYARI (riser DEGISMEZ, HATA da FIRLATILMAZ)."""
    errors: list[str] = []
    spec = {"id": "sC", "room_id": "r1", "kind": "single_flight", "floor_to_floor_mm": 900, "auto_flex": False}
    res = resolve_stair(spec, ROOM_5000x3000)
    if res.step_count != 5:
        errors.append(f"step_count 5 bekleniyordu, {res.step_count} bulundu")
    if abs(res.riser_mm - 170.0) > TOLERANCE:
        errors.append(f"auto_flex=False iken riser NOMINAL (170.0) kalmali, {res.riser_mm} bulundu")
    if not any("karsilamiyor" in w for w in res.warnings):
        errors.append(f"toplam-yukseklik UYUMSUZLUGU UYARISI bekleniyordu: {res.warnings}")
    return errors


def check_going_auto_shrinks_with_warning() -> list[str]:
    """1300mm oda, 6 basamak (5 bosluk) x varsayilan 270mm = 1350mm gerekli
    ama oda 1300mm -> elle: going=1300/5=260.0mm (>= MIN 250mm, HATA yok,
    UYARI var)."""
    errors: list[str] = []
    spec = {"id": "sD", "room_id": "r1", "kind": "single_flight", "floor_to_floor_mm": 1000, "step_count": 6}
    res = resolve_stair(spec, ROOM_1300x800)
    if abs(res.going_mm - 260.0) > TOLERANCE:
        errors.append(f"going 260.0 bekleniyordu, {res.going_mm} bulundu")
    if not any("daraltildi" in w for w in res.warnings):
        errors.append(f"going daraltma UYARISI bekleniyordu: {res.warnings}")
    return errors


def check_going_below_minimum_raises_fit_error() -> list[str]:
    """900mm oda, 6 basamak x 270mm = 1350mm gerekli; esnetilmis going
    900/5=180mm, MIN (250mm) altinda -> StairFitError FIRLATILMALI.
    Yanlis-pozitif: AYNI basamak sayisiyla daha genis (1500mm) bir odada
    going=300mm olur (MIN'in ustunde) -> HATA FIRLAMAMALI."""
    errors: list[str] = []
    spec = {"id": "sE", "room_id": "r1", "kind": "single_flight", "floor_to_floor_mm": 1000, "step_count": 6}
    try:
        resolve_stair(spec, ROOM_900x600)
        errors.append("900mm odada StairFitError bekleniyordu ama firlamadi")
    except StairFitError:
        pass

    try:
        res = resolve_stair(spec, ROOM_1500x800)
    except StairFitError as exc:
        errors.append(f"1500mm oda SIGMALIYDI ama StairFitError firladi: {exc}")
    else:
        # 1500mm >= gerekli 1350mm -> daraltma hic TETIKLENMEZ, going NOMINAL (270) kalir.
        if abs(res.going_mm - 270.0) > TOLERANCE:
            errors.append(f"going 270.0 (nominal, daraltmasiz) bekleniyordu, {res.going_mm} bulundu")
    return errors


def check_explicit_going_below_minimum_raises_even_without_shrink() -> list[str]:
    """Oda ZATEN sigiyor olsa bile (daraltma dalina hic GIRILMESE bile),
    acikca verilmis GUVENSIZ bir going_mm (MIN_GOING_MM altinda) sessizce
    GECMEMELI - StairFitError firlamali. Yanlis-pozitif: MIN_GOING_MM'in
    TAM UZERINDE acikca verilmis bir going_mm HATA VERMEMELI."""
    errors: list[str] = []
    bad = {"id": "sI", "room_id": "r1", "kind": "single_flight", "floor_to_floor_mm": 3000,
           "step_count": 18, "going_mm": 100.0}
    try:
        resolve_stair(bad, ROOM_5000x3000)
        errors.append("going_mm=100 (MIN altinda) HATA vermeliydi, ama gecti")
    except StairFitError:
        pass

    good = dict(bad, going_mm=260.0)
    try:
        res = resolve_stair(good, ROOM_5000x3000)
    except StairFitError as exc:
        errors.append(f"going_mm=260 (MIN ustunde) HATA vermemeliydi: {exc}")
    else:
        if abs(res.going_mm - 260.0) > TOLERANCE:
            errors.append(f"going 260.0 bekleniyordu, {res.going_mm} bulundu")
    return errors


def check_going_above_maximum_warns() -> list[str]:
    """MAX_GOING_MM'in UZERINDE acikca verilmis bir going_mm, oda ZATEN
    sigiyorsa (daraltma dalina hic GIRILMEDEN) HATA vermez (guvensiz degil,
    sadece standart disi) ama UYARI vermeli."""
    errors: list[str] = []
    spec = {"id": "sJ", "room_id": "r1", "kind": "single_flight", "floor_to_floor_mm": 3000,
            "step_count": 18, "going_mm": 320.0}
    res = resolve_stair(spec, ROOM_10000x3000)
    if abs(res.going_mm - 320.0) > TOLERANCE:
        errors.append(f"going 320.0 (daraltilmamis) bekleniyordu, {res.going_mm} bulundu")
    if not any("bandin" in w and "USTUNDE" in w for w in res.warnings):
        errors.append(f"MAX_GOING_MM ustunde UYARI bekleniyordu: {res.warnings}")
    return errors


def check_up_towards_must_match_travel_axis() -> list[str]:
    """ROOM_5000x3000 dx=5000 >= dy=3000 -> travel_axis='x', gecerli
    up_towards yalnizca 'E'/'W'. 'N' verilmesi HATA olmali (yanlis-pozitif:
    'E' verilmesi HATA OLMAMALI)."""
    errors: list[str] = []
    bad = {"id": "sF", "room_id": "r1", "kind": "single_flight", "floor_to_floor_mm": 3000, "step_count": 18, "up_towards": "N"}
    try:
        resolve_stair(bad, ROOM_5000x3000)
        errors.append("up_towards='N' (travel_axis='x' iken) HATA vermeliydi")
    except StairFitError:
        pass

    good = dict(bad, up_towards="E")
    try:
        resolve_stair(good, ROOM_5000x3000)
    except StairFitError as exc:
        errors.append(f"up_towards='E' gecerliydi ama HATA firladi: {exc}")
    return errors


def check_step_line_coordinates_hand_computable() -> list[str]:
    """Riht cizgisi UCLARI elle hesaplanabilir olmali - hem X hem Y
    seyahat ekseninde. Bu, bir onceki surumde X/Y'nin YANLISLIKLA yer
    degistirdigi (Y ekseninde nokta ciftlerinin (y, x) sirasinda donduruldugu)
    GERCEK bir hatayi yakalayan testtir: entity SAYISI dogru olsa bile
    KOORDINAT yanlis olabilir - sadece sayim yeterli degildir."""
    errors: list[str] = []

    x_axis = resolve_stair(
        {"id": "sX", "room_id": "r1", "kind": "single_flight", "floor_to_floor_mm": 3000, "step_count": 18, "up_towards": "E"},
        ROOM_5000x3000,
    )
    start, end = _step_line_endpoints(x_axis.travel_axis, x_axis.up_towards, x_axis.bbox, 270.0)
    expected = ((270.0, 0.0), (270.0, 3000.0))
    if (start, end) != expected:
        errors.append(f"X ekseni: {expected} bekleniyordu, {(start, end)} bulundu")

    y_room = [[100, 100], [1100, 100], [1100, 8100], [100, 8100]]
    y_axis = resolve_stair(
        {"id": "sY", "room_id": "r1", "kind": "single_flight", "floor_to_floor_mm": 3000, "step_count": 18, "up_towards": "N"},
        y_room,
    )
    if y_axis.travel_axis != "y":
        errors.append(f"travel_axis 'y' bekleniyordu, '{y_axis.travel_axis}' bulundu")
    start, end = _step_line_endpoints(y_axis.travel_axis, y_axis.up_towards, y_axis.bbox, 270.0)
    expected = ((100.0, 370.0), (1100.0, 370.0))
    if (start, end) != expected:
        errors.append(f"Y ekseni: {expected} bekleniyordu, {(start, end)} bulundu")
    return errors


def check_draw_entity_counts() -> list[str]:
    """Yon YOKKEN: yalnizca (step_count-1) riht cizgisi. Yon VARKEN: + 1 ok
    govdesi + 1 ok basi (LWPOLYLINE) + 2 kesme cizgisi parcasi = +4."""
    errors: list[str] = []
    doc = ezdxf.new()
    ensure_stair_layer(doc)
    msp = doc.modelspace()
    standard = DefaultStairStandard()

    no_direction = resolve_stair(
        {"id": "sG1", "room_id": "r1", "kind": "single_flight", "floor_to_floor_mm": 3000, "step_count": 18},
        ROOM_5000x3000,
    )
    standard.draw(msp, no_direction, "MERDIVEN")
    if len(msp) != 17:
        errors.append(f"yonsuz cizimde 17 varlik (18-1) bekleniyordu, {len(msp)} bulundu")

    doc2 = ezdxf.new()
    ensure_stair_layer(doc2)
    msp2 = doc2.modelspace()
    with_direction = resolve_stair(
        {"id": "sG2", "room_id": "r1", "kind": "single_flight", "floor_to_floor_mm": 1000, "step_count": 6, "up_towards": "E"},
        ROOM_1300x800,
    )
    standard.draw(msp2, with_direction, "MERDIVEN")
    expected = (6 - 1) + 4
    if len(msp2) != expected:
        errors.append(f"yonlu cizimde {expected} varlik bekleniyordu, {len(msp2)} bulundu")
    return errors


def check_stairs_for_floor_skips_unknown_room_gracefully() -> list[str]:
    """Bilinmeyen room_id -> validate.py bunu zaten HATA olarak yakalar;
    ama cizim tarafi (stairs_for_floor) KENDI BASINA sessizce dayanikli
    olmali (crash etmemeli)."""
    errors: list[str] = []
    floor = {
        "rooms": [{"id": "r1", "polygon": ROOM_5000x3000}],
        "stairs": [{"id": "sH", "room_id": "GECERSIZ", "kind": "single_flight", "floor_to_floor_mm": 3000, "step_count": 18}],
    }
    try:
        resolutions = stairs_for_floor(floor)
    except Exception as exc:  # noqa: BLE001
        return [f"bilinmeyen room_id crash etmemeliydi: {exc}"]
    if resolutions:
        errors.append(f"bos liste bekleniyordu, {resolutions} bulundu")
    return errors


# --------------------------------------------------------------------------
# DEV-046/DEV-047: cift kollu (dog_leg) merdiven
# --------------------------------------------------------------------------

def check_dog_leg_real_room_hand_computable() -> list[str]:
    """GERCEK projenin 4000x3000mm 'Merdiven' odasi, 3000mm kat yuksekligi
    (bodrum/normal katlarin TIPIK degeri) - tek kollun StairFitError ile
    REDDETTIGI, dog_leg'in TAM TERSINE narrowing bile GEREKMEDEN sigdigi
    somut senaryo. Tum degerler ELLE hesaplanabilir (bkz. yorum satirlari)."""
    errors: list[str] = []
    r = resolve_stair(
        {"id": "sDL", "room_id": "stair", "floor_to_floor_mm": 3000,
         "kind": "dog_leg", "up_towards": "E"},
        ROOM_4000x3000,
    )
    # step_count = round(3000/170) = 18; riser = 3000/18 = 166.67 (fark
    # 3.33 < 5mm tolerans -> UYARI YOK). flight1=ceil(18/2)=9, flight2=9.
    if r.step_count != 18:
        errors.append(f"step_count=18 bekleniyordu, {r.step_count} bulundu")
    if abs(r.riser_mm - 3000 / 18) > TOLERANCE:
        errors.append(f"riser={3000/18:.4f} bekleniyordu, {r.riser_mm} bulundu")
    if r.flight_step_counts != (9, 9):
        errors.append(f"flight_step_counts=(9,9) bekleniyordu, {r.flight_step_counts} bulundu")
    # run_available = 4000-1100(varsayilan sahanlik) = 2900; gerekli kosu
    # (9-1)*270 = 2160 <= 2900 -> DARALTMA YOK, going TAM 270.
    if abs(r.going_mm - 270.0) > TOLERANCE:
        errors.append(f"going=270.0 (daraltma OLMADAN) bekleniyordu, {r.going_mm} bulundu")
    if r.warnings:
        errors.append(f"UYARI OLMAMALIYDI (narrowing gerekmiyor): {r.warnings}")
    # rev-26: sahanlik odanin UZAK UCUNDA: flight1_run=(9-1)*270=2160 -> landing
    # [2160,4000]x[0,3000] (artan boy sahanliga katilir).
    expected_landing = (2160.0, 0.0, 4000.0, 3000.0)
    if tuple(round(v, 6) for v in r.landing_bbox) != expected_landing:
        errors.append(f"landing_bbox={expected_landing} bekleniyordu, {r.landing_bbox} bulundu")
    # exit: kol 2 sahanligin yakin kenarindan (2160) geri doner: 2160-8*270=0;
    # flight2_perp_mid=(1500+3000)/2=2250. up_towards='E' -> exit 'W'.
    if (round(r.exit_point[0], 6), round(r.exit_point[1], 6)) != (0.0, 2250.0):
        errors.append(f"exit_point=(0.0,2250.0) bekleniyordu, {r.exit_point} bulundu")
    prof = stair_section_profile(r, "y", 750.0)
    if len(prof) != 9 or abs(prof[0]["z_mm"] - 3000 / 18) > 1e-6 or prof[-1]["kind"] != "landing" \
            or abs(prof[-1]["z_mm"] - 1500.0) > 1e-6 or (prof[-1]["s_lo"], prof[-1]["s_hi"]) != (2160.0, 4000.0):
        errors.append(f"y=750 kesiti 8 basamak + sahanlik(z=1500, s 2160-4000) olmali: {prof}")
    if r.exit_direction != "W":
        errors.append(f"exit_direction='W' bekleniyordu, {r.exit_direction!r} bulundu")
    return errors


def check_dog_leg_4000mm_floor_narrows_going() -> list[str]:
    """AYNI gercek oda, ZEMIN katin 4000mm kat yuksekligiyle: step_count=24,
    flight=12+12, gerekli kosu (12-1)*270=2970mm > 2900mm mevcut -> going
    OTOMATIK daralir (2900/11=263.64mm), UYARI verir - narrowing yolunun
    dog_leg'de de CALISTIGININ kaniti (tek kollu yolla PAYLASILAN kod)."""
    errors: list[str] = []
    r = resolve_stair(
        {"id": "sDL2", "room_id": "stair", "floor_to_floor_mm": 4000,
         "kind": "dog_leg", "up_towards": "E"},
        ROOM_4000x3000,
    )
    expected_going = 2900.0 / 11.0
    if abs(r.going_mm - expected_going) > TOLERANCE:
        errors.append(f"going={expected_going:.4f} bekleniyordu, {r.going_mm} bulundu")
    if not any("daraltildi" in w for w in r.warnings):
        errors.append(f"'daraltildi' UYARISI bekleniyordu: {r.warnings}")
    return errors


def check_dog_leg_flight_width_below_minimum_raises() -> list[str]:
    """Oda kisa ekseni 1700mm -> kol basina 850mm < MIN_FLIGHT_WIDTH_MM
    (900mm) -> StairFitError (yanlis-pozitif: AYNI oranin genis hali asagida)."""
    narrow_room = [[0, 0], [6000, 0], [6000, 1700], [0, 1700]]
    try:
        resolve_stair(
            {"id": "sDL3", "room_id": "r1", "floor_to_floor_mm": 3000, "kind": "dog_leg"},
            narrow_room,
        )
        return ["850mm kol genisligi StairFitError FIRLATMALIYDI"]
    except StairFitError:
        pass
    wide_room = [[0, 0], [6000, 0], [6000, 2000], [0, 2000]]
    try:
        resolve_stair(
            {"id": "sDL3b", "room_id": "r1", "floor_to_floor_mm": 3000, "kind": "dog_leg"},
            wide_room,
        )
    except StairFitError as exc:
        return [f"1000mm kol genisligi (>MIN) StairFitError URETMEMELIYDI: {exc}"]
    return []


def check_dog_leg_landing_wont_fit_raises() -> list[str]:
    """Acikca BUYUK bir sahanlik derinligi (5000mm), odanin uzun ekseninden
    (4000mm) BUYUK - kol icin hic yer kalmaz -> StairFitError."""
    try:
        resolve_stair(
            {"id": "sDL4", "room_id": "stair", "floor_to_floor_mm": 3000,
             "kind": "dog_leg", "landing_depth_mm": 5000.0},
            ROOM_4000x3000,
        )
        return ["sahanlik > oda uzunlugu StairFitError FIRLATMALIYDI"]
    except StairFitError:
        return []


def check_unknown_kind_raises_fit_error() -> list[str]:
    """`walls.kind`/`check_walls` ile AYNI yazim-hatasi korumasi: bilinmeyen
    bir `kind` sessizce varsayilana DUSMEMELI, acikca HATA vermelidir."""
    try:
        resolve_stair(
            {"id": "sDL5", "room_id": "r1", "floor_to_floor_mm": 3000, "kind": "spiral"},
            ROOM_5000x3000,
        )
        return ["bilinmeyen kind StairFitError FIRLATMALIYDI"]
    except StairFitError as exc:
        return [] if "bilinmeyen kind" in str(exc) else [f"mesaj 'bilinmeyen kind' ICERMELIYDI: {exc}"]


def check_single_flight_fields_unaffected_by_dog_leg_additions() -> list[str]:
    """REGRESYON: `kind` hic verilmeyince (eski context'lerin TAMAMI)
    `StairResolution`in YENI alanlari eski davranisi birebir yansitmali -
    `landing_bbox=None`, `flight_step_counts=(step_count,)`, `exit_point`
    eski 'yukari uc' noktasiyla AYNI, `exit_direction=up_towards`."""
    errors: list[str] = []
    r = resolve_stair(
        {"id": "sSF", "room_id": "r1", "kind": "single_flight", "floor_to_floor_mm": 3000, "step_count": 18, "up_towards": "E"},
        ROOM_5000x3000,
    )
    if r.kind != "single_flight":
        errors.append(f"kind='single_flight' bekleniyordu, {r.kind!r} bulundu")
    if r.landing_bbox is not None:
        errors.append(f"landing_bbox=None bekleniyordu, {r.landing_bbox} bulundu")
    if r.flight_step_counts != (18,):
        errors.append(f"flight_step_counts=(18,) bekleniyordu, {r.flight_step_counts} bulundu")
    if r.exit_point != (5000.0, 1500.0):
        errors.append(f"exit_point=(5000.0,1500.0) (oda 'yukari' ucu) bekleniyordu, {r.exit_point} bulundu")
    if r.exit_direction != "E":
        errors.append(f"exit_direction='E' bekleniyordu, {r.exit_direction!r} bulundu")
    return errors


def check_dog_leg_draw_entity_counts() -> list[str]:
    """Yonlu: 8+8 riht (flight1+flight2) + 1 sahanlik LWPOLYLINE + 2 kol
    bolucusu + (1 ok govdesi + 1 ok basi + 2 kesme cizgisi) = 23. Yonsuz:
    ayni ama son 4'u YOK = 19 (yanlis-pozitif: yon olmadan ok/kesme cizgisi
    cizilMEMELI, tek kollu ile AYNI kural)."""
    errors: list[str] = []
    standard = DefaultStairStandard()

    r_dir = resolve_stair(
        {"id": "sDL6", "room_id": "stair", "floor_to_floor_mm": 3000,
         "kind": "dog_leg", "up_towards": "E"},
        ROOM_4000x3000,
    )
    doc = ezdxf.new(); ensure_stair_layer(doc); msp = doc.modelspace()
    standard.draw(msp, r_dir, "MERDIVEN")
    if len(msp) != 22:
        errors.append(f"yonlu dog_leg cizimde 22 varlik bekleniyordu, {len(msp)} bulundu")

    r_nodir = resolve_stair(
        {"id": "sDL7", "room_id": "stair", "floor_to_floor_mm": 3000, "kind": "dog_leg"},
        ROOM_4000x3000,
    )
    doc2 = ezdxf.new(); ensure_stair_layer(doc2); msp2 = doc2.modelspace()
    standard.draw(msp2, r_nodir, "MERDIVEN")
    if len(msp2) != 18:
        errors.append(f"yonsuz dog_leg cizimde 18 varlik bekleniyordu, {len(msp2)} bulundu")
    return errors


def check_ensure_stair_layer_sets_rgb() -> list[str]:
    errors: list[str] = []
    doc = ezdxf.new()
    ensure_stair_layer(doc)
    if "MERDIVEN" not in doc.layers:
        return ["MERDIVEN katmani olusturulmadi"]
    layer = doc.layers.get("MERDIVEN")
    from stairs import STAIR_RGB
    if tuple(layer.rgb) != STAIR_RGB:
        errors.append(f"layer.rgb {STAIR_RGB} bekleniyordu, {layer.rgb} bulundu")
    return errors


ROOM_3000x4000 = [[0, 0], [3000, 0], [3000, 4000], [0, 4000]]


def check_short_edge_entry_rev25() -> list[str]:
    """rev-25: 3000x4000 oda, dog_leg, up_towards='N' -> giris ucu GUNEY (kisa
    kenar). 3000mm katta 18 basamak 9+9, riht 166.67... (elle: 3000/18),
    going 270 (daralma yok: 8*270=2160 <= 4000-1100=2900). Giris 'S'te kapisiz
    acikliga UYARI yok; 'door' tipi, uzun kenar ('W') ve acikliksiz durum UYARI."""
    errors: list[str] = []
    spec = {"id": "s", "room_id": "r", "floor_to_floor_mm": 3000.0, "up_towards": "N",
            "kind": "dog_leg"}
    res = resolve_stair(spec, ROOM_3000x4000)
    if res.step_count != 18 or tuple(res.flight_step_counts) != (9, 9):
        errors.append(f"18 basamak 9+9 olmali: {res.step_count} {res.flight_step_counts}")
    if abs(res.going_mm - 270.0) > 1e-9 or res.warnings:
        errors.append(f"going 270, uyari yok olmali: {res.going_mm} {res.warnings}")
    if stair_entry_side(res) != "S":
        errors.append(f"giris kenari 'S' olmali: {stair_entry_side(res)}")
    ok = [{"id": "p", "type": "passage", "point": (1500.0, 0.0)}]
    if stair_access_warnings(res, ok):
        errors.append(f"kisa kenarda passage UYARI vermemeli: {stair_access_warnings(res, ok)}")
    if len(stair_access_warnings(res, [{"id": "d", "type": "door", "point": (1500.0, 0.0)}])) != 1:
        errors.append("kisa kenarda KAPI tam 1 uyari vermeli")
    if len(stair_access_warnings(res, [{"id": "w", "type": "passage", "point": (0.0, 2000.0)}])) != 1:
        errors.append("uzun kenardan (W) giris tam 1 uyari vermeli")
    if len(stair_access_warnings(res, [])) != 1:
        errors.append("hic acikligi olmayan merdiven tam 1 uyari vermeli")
    nodir = resolve_stair({k: v for k, v in spec.items() if k != "up_towards"}, ROOM_3000x4000)
    if stair_access_warnings(nodir, []):
        errors.append("up_towards yoksa kontrol SESSIZCE atlanmali (yon uydurulmaz)")
    zk = resolve_stair({**spec, "floor_to_floor_mm": 4000.0}, ROOM_3000x4000)
    if zk.step_count != 24 or abs(zk.going_mm - 2900.0 / 11.0) > 1e-6 or not zk.warnings:
        errors.append(f"4000mm: 24 basamak, going 2900/11, daralma UYARISI: {zk.step_count} {zk.going_mm} {zk.warnings}")
    return errors


def check_three_flight_rev26() -> list[str]:
    """rev-26: 3000x3000 kare oda, U seklinde uc kollu merdiven (iki sahanlik).
    ELLE: w=3000/3=1000; kol boylari 2000/1000/2000; 18 basamak orantili dagilir
    7.2/3.6/7.2 -> 7/4/7 (kalan 1 en buyuk kesre = kol 2); going 270 (en siki kol
    2000/6=333, 1000/3=333 > 270, daralma YOK). 6+3+6 = 15 riht cizgisi.
    Sahanliklar (0,2000,1000,3000) ve (2000,2000,3000,3000); kuyu (1000,0,2000,2000);
    cikis (2500,0) yonu 'S' (giris ucu). E icin 90 derece donmus: cikis (0,500), 'W'."""
    errors: list[str] = []
    room = [[0, 0], [3000, 0], [3000, 3000], [0, 3000]]
    spec = {"id": "s3", "room_id": "r", "floor_to_floor_mm": 3000.0, "kind": "three_flight",
            "up_towards": "N"}
    res = resolve_stair(spec, room)
    if res.step_count != 18 or tuple(res.flight_step_counts) != (7, 4, 7):
        errors.append(f"18 basamak 7/4/7 olmali: {res.step_count} {res.flight_step_counts}")
    if abs(res.going_mm - 270.0) > 1e-9 or res.warnings:
        errors.append(f"going 270, uyari yok olmali: {res.going_mm} {res.warnings}")
    g = res.three_flight
    if len(g["step_lines"]) != 15:
        errors.append(f"15 riht cizgisi olmali: {len(g['step_lines'])}")
    if g["landings"] != [(0.0, 1620.0, 1095.0, 3000.0), (1905.0, 1620.0, 3000.0, 3000.0)]:
        errors.append(f"sahanliklar yanlis: {g['landings']}")
    if g["well"] != (1000.0, 0.0, 2000.0, 1620.0):
        errors.append(f"kuyu yanlis: {g['well']}")
    if res.exit_point != (2500.0, 0.0) or res.exit_direction != "S" or stair_entry_side(res) != "S":
        errors.append(f"cikis (2500,0) 'S' olmali: {res.exit_point} {res.exit_direction}")
    east = resolve_stair({**spec, "up_towards": "E"}, room)
    if east.exit_point != (0.0, 500.0) or east.exit_direction != "W":
        errors.append(f"E icin cikis (0,500) 'W' olmali: {east.exit_point} {east.exit_direction}")
    for well, lines, polys in (("open", 21, 3), ("filled", 20, 4)):
        doc = ezdxf.new()
        msp = doc.modelspace()
        DefaultStairStandard().draw(msp, resolve_stair({**spec, "well": well}, room), "MERDIVEN")
        got = (len(msp.query("LINE")), len(msp.query("LWPOLYLINE")))
        if got != (lines, polys):
            errors.append(f"well={well}: {lines} LINE/{polys} LWPOLYLINE beklendi, {got}")
    try:
        resolve_stair(spec, [[0, 0], [2000, 0], [2000, 2000], [0, 2000]])
        errors.append("2000x2000'de (kol 667mm) StairFitError bekleniyordu")
    except StairFitError:
        pass
    try:
        resolve_stair({**spec, "well": "yok"}, room)
        errors.append("gecersiz well StairFitError vermeli")
    except StairFitError:
        pass
    if resolve_stair({"id": "d", "room_id": "r", "floor_to_floor_mm": 3000.0}, ROOM_3000x4000).kind != "dog_leg":
        errors.append("kind verilmeyince VARSAYILAN dog_leg olmali")
    return errors


def check_square_three_flight_project_rev26() -> list[str]:
    """Proje merdiveni: 4000x4000 kare oda, three_flight, up 'N'. ELLE: kat 3000
    -> N=18, g=270; n2 adaylari 2/4/6 (parite): n2=6 -> m=6, e=(4000-5*270)/2=1325,
    w=min(4000/3,1325)=1325, d=4000-5*270=2650, kuyu (4000-2650=1350) x (m-1)*g=1350
    = KARE; kuyu (1325,0,2675,1350); sahanlik 1 (0,1350,1325,4000). ZK 4000mm ->
    N=24 -> n2=8, m=8 -> kuyu 1890x1890 KARE, going 270 (daralma YOK)."""
    errors: list[str] = []
    room = [[0, 0], [4000, 0], [4000, 4000], [0, 4000]]
    base = {"id": "p", "room_id": "r", "kind": "three_flight", "up_towards": "N"}
    r = resolve_stair({**base, "floor_to_floor_mm": 3000.0}, room)
    if tuple(r.flight_step_counts) != (6, 6, 6) or r.three_flight["well"] != (1325.0, 0.0, 2675.0, 1350.0):
        errors.append(f"3000: 6/6/6 ve kuyu (1325,0,2675,1350): {r.flight_step_counts} {r.three_flight['well']}")
    if r.three_flight["landings"][0] != (0.0, 1350.0, 1325.0, 4000):
        errors.append(f"sahanlik 1 (0,1350,1325,4000): {r.three_flight['landings'][0]}")
    z = stair_section_profile(r, "x", 500.0)
    if len(z) != 5 + 1 or abs(z[-1]["z_mm"] - 6 * 3000 / 18) > 1e-6 or z[-1]["kind"] != "landing":
        errors.append(f"x=500 kesiti 5 basamak + sahanlik: {z}")
    zk = resolve_stair({**base, "floor_to_floor_mm": 4000.0}, room)
    wx0, wy0, wx1, wy1 = zk.three_flight["well"]
    if tuple(zk.flight_step_counts) != (8, 8, 8) or round(wx1 - wx0, 6) != 1890.0 or round(wy1 - wy0, 6) != 1890.0 or zk.warnings:
        errors.append(f"ZK: 8/8/8, kuyu 1890x1890, uyari yok: {zk.flight_step_counts} {zk.three_flight['well']} {zk.warnings}")
    # sahanliklar kutunun UCUNDA: ust kenar = oda ust kenari
    if zk.three_flight["landings"][0][3] != 4000 or zk.three_flight["landings"][1][2] != 4000:
        errors.append("sahanliklar oda ucuna (y=4000, x=4000) oturmali")
    return errors


def main() -> int:
    groups = (
        ("acik step_count'tan riht turetme (elle hesap)", check_explicit_step_count_derives_riser()),
        ("auto_flex=True riht esnetme + UYARI", check_auto_flex_true_adjusts_riser_with_warning()),
        ("auto_flex=False UYARI verir, degistirmez", check_auto_flex_false_warns_without_adjusting()),
        ("going otomatik daraltma + UYARI", check_going_auto_shrinks_with_warning()),
        ("MIN going altinda StairFitError (+ yanlis-pozitif)", check_going_below_minimum_raises_fit_error()),
        ("acikca verilen going MIN altinda (daraltma OLMADAN) + yanlis-pozitif", check_explicit_going_below_minimum_raises_even_without_shrink()),
        ("MAX going ustunde UYARI", check_going_above_maximum_warns()),
        ("up_towards eksen tutarliligi (+ yanlis-pozitif)", check_up_towards_must_match_travel_axis()),
        ("riht cizgisi koordinatlari elle hesaplanabilir (X ve Y ekseni)", check_step_line_coordinates_hand_computable()),
        ("cizim varlik sayilari (yonsuz/yonlu)", check_draw_entity_counts()),
        ("bilinmeyen room_id sessizce atlanir", check_stairs_for_floor_skips_unknown_room_gracefully()),
        ("MERDIVEN katmani RGB'si kod-sahipli", check_ensure_stair_layer_sets_rgb()),
        ("dog_leg GERCEK Merdiven odasinda elle hesaplanabilir (DEV-046)", check_dog_leg_real_room_hand_computable()),
        ("dog_leg 4000mm katta going OTOMATIK daralir", check_dog_leg_4000mm_floor_narrows_going()),
        ("dog_leg kol genisligi MIN altinda StairFitError (+ yanlis-pozitif)", check_dog_leg_flight_width_below_minimum_raises()),
        ("dog_leg sahanlik odaya sigmazsa StairFitError", check_dog_leg_landing_wont_fit_raises()),
        ("bilinmeyen kind StairFitError (yazim hatasi korumasi)", check_unknown_kind_raises_fit_error()),
        ("single_flight YENI alanlar eski davranisi birebir yansitir (regresyon)", check_single_flight_fields_unaffected_by_dog_leg_additions()),
        ("dog_leg cizim varlik sayilari (yonlu/yonsuz, DEV-047 cikis)", check_dog_leg_draw_entity_counts()),
        ("kisa kenar giris + kapisiz acikli (rev-25)", check_short_edge_entry_rev25()),
        ("uc kollu U merdiven + kuyu + varsayilan dog_leg (rev-26)", check_three_flight_rev26()),
        ("kare 4000x4000 uc kollu merdiven (proje) + kesit profili (rev-26)", check_square_three_flight_project_rev26()),
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
        print("\nMERDIVEN SELF-TEST BASARISIZ.")
        return 1
    print("\nMerdiven self-test BASARILI.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
