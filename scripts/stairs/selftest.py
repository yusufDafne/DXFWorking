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

from stairs import (  # noqa: E402
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


def check_explicit_step_count_derives_riser() -> list[str]:
    """3000mm / 18 basamak = elle: 166.667mm riht. Nominal (170) farki
    3.33mm < tolerans (5mm) -> UYARI olmamali."""
    errors: list[str] = []
    spec = {"id": "sA", "room_id": "r1", "floor_to_floor_mm": 3000, "step_count": 18}
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
    spec = {"id": "sB", "room_id": "r1", "floor_to_floor_mm": 900}
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
    spec = {"id": "sC", "room_id": "r1", "floor_to_floor_mm": 900, "auto_flex": False}
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
    spec = {"id": "sD", "room_id": "r1", "floor_to_floor_mm": 1000, "step_count": 6}
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
    spec = {"id": "sE", "room_id": "r1", "floor_to_floor_mm": 1000, "step_count": 6}
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
    bad = {"id": "sI", "room_id": "r1", "floor_to_floor_mm": 3000,
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
    spec = {"id": "sJ", "room_id": "r1", "floor_to_floor_mm": 3000,
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
    bad = {"id": "sF", "room_id": "r1", "floor_to_floor_mm": 3000, "step_count": 18, "up_towards": "N"}
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
        {"id": "sX", "room_id": "r1", "floor_to_floor_mm": 3000, "step_count": 18, "up_towards": "E"},
        ROOM_5000x3000,
    )
    start, end = _step_line_endpoints(x_axis, 270.0)
    expected = ((270.0, 0.0), (270.0, 3000.0))
    if (start, end) != expected:
        errors.append(f"X ekseni: {expected} bekleniyordu, {(start, end)} bulundu")

    y_room = [[100, 100], [1100, 100], [1100, 8100], [100, 8100]]
    y_axis = resolve_stair(
        {"id": "sY", "room_id": "r1", "floor_to_floor_mm": 3000, "step_count": 18, "up_towards": "N"},
        y_room,
    )
    if y_axis.travel_axis != "y":
        errors.append(f"travel_axis 'y' bekleniyordu, '{y_axis.travel_axis}' bulundu")
    start, end = _step_line_endpoints(y_axis, 270.0)
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
        {"id": "sG1", "room_id": "r1", "floor_to_floor_mm": 3000, "step_count": 18},
        ROOM_5000x3000,
    )
    standard.draw(msp, no_direction, "MERDIVEN")
    if len(msp) != 17:
        errors.append(f"yonsuz cizimde 17 varlik (18-1) bekleniyordu, {len(msp)} bulundu")

    doc2 = ezdxf.new()
    ensure_stair_layer(doc2)
    msp2 = doc2.modelspace()
    with_direction = resolve_stair(
        {"id": "sG2", "room_id": "r1", "floor_to_floor_mm": 1000, "step_count": 6, "up_towards": "E"},
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
        "stairs": [{"id": "sH", "room_id": "GECERSIZ", "floor_to_floor_mm": 3000, "step_count": 18}],
    }
    try:
        resolutions = stairs_for_floor(floor)
    except Exception as exc:  # noqa: BLE001
        return [f"bilinmeyen room_id crash etmemeliydi: {exc}"]
    if resolutions:
        errors.append(f"bos liste bekleniyordu, {resolutions} bulundu")
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
