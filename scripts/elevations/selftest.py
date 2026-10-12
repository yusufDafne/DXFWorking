#!/usr/bin/env python3
"""Seviye istifi ve zemin-alti kesikli linetype testleri (DEV-011).

Kullanim:
    python scripts/elevations/selftest.py
Cikis kodu: 0 basarili, 1 basarisiz.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import ezdxf  # noqa: E402

from elevations import (  # noqa: E402
    BELOW_GROUND_LINETYPE,
    ElevationSheet,
    LevelStack,
    elevation_vertical_extent,
)

TOLERANCE = 1e-6


class _NullAxisGrid:
    """`draw_on_elevation` cagrisini yutan test dublesi - bu self-test aks
    modulunu degil, ElevationSheet'in KENDI mantigini sinar."""

    def draw_on_elevation(self, msp, dx, axis_source, y_bottom, y_top) -> None:
        pass


ELEVATION = {
    "label": "TEST CEPHE",
    "width": 10000.0,
    "levels": [
        {"label": "2. BODRUM", "height": 3000.0, "below_ground": True},
        {"label": "1. BODRUM", "height": 3000.0, "below_ground": True},
        {"label": "ZEMIN", "height": 4000.0, "window_count": 2, "door": True},
        {"label": "1. NORMAL", "height": 3000.0, "window_count": 2},
        {"label": "CATI", "height": 1000.0, "machine_room": True},
    ],
}


def check_placements_hand_computable() -> list[str]:
    """Cursor, ELLE hesaplanabilir bir istifte dogru birikmelidir:
    -6000 (iki 3000'lik zemin-alti) -> 0 -> 4000 -> 7000 -> 8000."""
    errors: list[str] = []
    placements = LevelStack.from_context(ELEVATION).placements()
    expected = [
        ("2. BODRUM", -6000.0, -3000.0),
        ("1. BODRUM", -3000.0, 0.0),
        ("ZEMIN", 0.0, 4000.0),
        ("1. NORMAL", 4000.0, 7000.0),
        ("CATI", 7000.0, 8000.0),
    ]
    if len(placements) != len(expected):
        return [f"{len(expected)} seviye bekleniyordu, {len(placements)} bulundu."]
    for (level, y0, y1), (label, ey0, ey1) in zip(placements, expected):
        if level.label != label or abs(y0 - ey0) > TOLERANCE or abs(y1 - ey1) > TOLERANCE:
            errors.append(f"'{label}': beklenen ({ey0},{ey1}), bulunan ({level.label},{y0},{y1}).")
    return errors


def check_extent_includes_machine_room() -> list[str]:
    """extent() ustteki machine_room protruzyonunu (yukseklik*0.8) DAHIL
    etmelidir - pafta bu kadar yer ayirmazsa CATI KATI blogu tasar."""
    errors: list[str] = []
    y_bottom, y_top = elevation_vertical_extent(ELEVATION)
    if abs(y_bottom - (-6000.0)) > TOLERANCE:
        errors.append(f"y_bottom beklenen -6000, bulunan {y_bottom}.")
    # ust seviye 8000'de baslar, machine_room extra = 1000*0.8 = 800 -> 8000+800
    if abs(y_top - 8800.0) > TOLERANCE:
        errors.append(f"y_top beklenen 8800 (8000 stack_top + 800 extra), bulunan {y_top}.")
    return errors


def check_below_ground_gets_dashed_linetype() -> list[str]:
    """Zemin-alti seviyenin ANA HATTI DASHED linetype almalidir; ustteki
    seviyeler BYLAYER kalmalidir (yanlis-pozitif: hepsi kesikli olmamali)."""
    errors: list[str] = []
    doc = ezdxf.new()
    msp = doc.modelspace()
    ElevationSheet.draw(msp, ELEVATION, 0.0, 120.0, _NullAxisGrid(), 120.0)

    outlines = list(msp.query("LWPOLYLINE[layer=='DUVARLAR']"))
    # 5 seviye ana hat + 1 machine_room kutusu = 6 (window/door KAPI-PENCERE
    # layer'inda, bu sayima girmez).
    by_bottom_y = {}
    for entity in outlines:
        points = list(entity.get_points("xy"))
        y0 = min(p[1] for p in points)
        by_bottom_y[round(y0)] = entity

    dashed_expected = {-6000, -3000}  # iki zemin-alti seviyenin y0'lari
    for y0, entity in by_bottom_y.items():
        should_be_dashed = y0 in dashed_expected
        is_dashed = entity.dxf.linetype == BELOW_GROUND_LINETYPE
        if should_be_dashed and not is_dashed:
            errors.append(f"y0={y0} zemin-alti oldugu halde linetype={entity.dxf.linetype!r}.")
        if not should_be_dashed and is_dashed:
            errors.append(f"y0={y0} zemin-ustu oldugu halde YANLISLIKLA DASHED.")
    return errors


def check_window_and_door_counts() -> list[str]:
    """Pencere/kapi sayisi ve DASHED yayilimi (zemin-alti seviyede pencere
    olsaydi o da kesikli olmali; bu ornekte yok, sadece kapi/pencere sayisi
    dogru mu diye kontrol edilir)."""
    errors: list[str] = []
    doc = ezdxf.new()
    msp = doc.modelspace()
    ElevationSheet.draw(msp, ELEVATION, 0.0, 120.0, _NullAxisGrid(), 120.0)

    openings = list(msp.query("LWPOLYLINE[layer=='KAPI-PENCERE']"))
    # ZEMIN: 2 pencere + 1 kapi, 1. NORMAL: 2 pencere -> toplam 5
    if len(openings) != 5:
        errors.append(f"5 acikilik bekleniyordu, {len(openings)} bulundu.")
    return errors


def _plan_context() -> dict:
    """DEV-073: 6000x9000 bina, tek oda (merkez cizgisinde), ic duvar x=3000. Iki kat: ZEMIN (seviye 0, 3000) ve K1 (seviye 1, 3000)."""
    wall = lambda i, a, b: {"id": i, "start": list(a), "end": list(b), "thickness": 200.0, "layer": "D"}  # noqa: E731
    walls = [wall("w_alt", (0, 0), (6000, 0)), wall("w_sag", (6000, 0), (6000, 9000)), wall("w_ust", (6000, 9000), (0, 9000)),
             wall("w_sol", (0, 9000), (0, 0)), wall("w_orta", (3000, 0), (3000, 9000))]
    rooms = [{"id": "R", "polygon": [[0, 0], [6000, 0], [6000, 9000], [0, 9000]]}]
    op = lambda i, t, w, pos, wd, **kw: {"id": i, "type": t, "wall_id": w, "position_from_start": pos, "width": wd, **kw}  # noqa: E731
    f0 = {"id": "zemin", "rooms": rooms, "walls": walls, "openings": [
        op("pen", "window", "w_alt", 1500.0, 1200.0),                              # normal: 1200 / 900
        op("boy", "window", "w_alt", 4500.0, 1800.0, window_class="tall"),         # boy: 2000 / 40
        op("kapi", "door", "w_alt", 3000.5, 900.0),                                # DIS kapi: boy pencere varsayilani
        op("ic", "door", "w_orta", 4500.0, 900.0),                                 # IC kapi: cepheye GIRMEZ
        op("sag", "window", "w_sag", 4000.0, 1000.0),                              # yalniz SAG cephe
        op("ust", "window", "w_ust", 3000.0, 1000.0)]}                             # ne on ne sag
    f1 = {"id": "k1", "rooms": rooms, "walls": walls, "openings": [
        op("ozel", "window", "w_alt", 3000.0, 1000.0, height=1500.0, sill_height=700.0),   # kullanici degeri varsayilani ezer
        op("sag2", "window", "w_sag", 2000.0, 800.0)]}
    return {"meta": {}, "floors": [f0, f1], "elevations": [
        {"id": "on", "label": "ON", "width": 6000.0, "axis_source": "vertical", "openings_from": "plan",
         "levels": [{"label": "ZEMIN", "height": 3000.0}, {"label": "1. KAT", "height": 3000.0}]},
        {"id": "sag", "label": "SAG", "width": 9000.0, "axis_source": "horizontal", "openings_from": "plan",
         "levels": [{"label": "ZEMIN", "height": 3000.0}, {"label": "1. KAT", "height": 3000.0}]}]}


def check_plan_derived_dev073() -> list[str]:
    """DEV-073: plan acikliklarindan turetilen cephe. Beklenen dikdortgenler ELLE hesaplanir."""
    from elevations import derive_level_openings
    errors: list[str] = []
    ctx = _plan_context()

    def eq(label, got, want):
        if got != want:
            errors.append(f"{label}: {got!r} != {want!r}")

    r, notes = derive_level_openings(ctx, ctx["elevations"][0])
    key = lambda x: (x.opening_id, x.x0, x.x1, x.sill, x.height, x.kind, x.window_class)  # noqa: E731
    eq("on cephe zemin: x0 sirali, 3 aciklik (ic kapi/sag/ust YOK)", [key(x) for x in r[0]],
       [("pen", 900.0, 2100.0, 900.0, 1200.0, "window", "standard"),
        ("kapi", 2550.5, 3450.5, 40.0, 2000.0, "door", "tall"),
        ("boy", 3600.0, 5400.0, 40.0, 2000.0, "window", "tall")])
    eq("on cephe K1: kullanici degeri (1500/700) varsayilani ezer", [key(x) for x in r[1]],
       [("ozel", 2500.0, 3500.0, 700.0, 1500.0, "window", "standard")])
    eq("notlar bos (temiz)", notes, [])
    r2, _ = derive_level_openings(ctx, ctx["elevations"][1])
    eq("sag cephe zemin: yatay eksen = plandaki Y", [key(x) for x in r2[0]], [("sag", 3500.0, 4500.0, 900.0, 1200.0, "window", "standard")])
    eq("sag cephe K1", [key(x) for x in r2[1]], [("sag2", 1600.0, 2400.0, 900.0, 1200.0, "window", "standard")])
    # kaynaklar adiyla bildirilir
    door = r[0][1]
    eq("dis kapi kaynagi (boy pencere varsayilani) adiyla", ("boy pencere varsayilani" in door.height_source, "boy pencere varsayilani" in door.sill_source), (True, True))
    eq("kullanici yuksekligi 'verilen'", (r[1][0].height_source, r[1][0].sill_source), ("verilen", "verilen"))
    # DIS kapida kullanici `height` degeri varsayilani ezer (denizlik boy pencere varsayilani kalir)
    kh = _plan_context()
    kh["floors"][0]["openings"][2]["height"] = 2400.0
    rk, _ = derive_level_openings(kh, kh["elevations"][0])
    kapi = [x for x in rk[0] if x.opening_id == "kapi"][0]
    eq("dis kapi: verilen yukseklik gecer, denizlik varsayilan", (kapi.height, kapi.sill, kapi.height_source), (2400.0, 40.0, "verilen"))
    # opt-in: generic cephe -> hicbir sey turetilmez
    g = {**ctx["elevations"][0]}
    del g["openings_from"]
    eq("generic cephe turetmez", derive_level_openings(ctx, g), ({}, []))
    # notlar: seviye yuksekligini asan aciklik, cephe disina dusen aciklik (kirpilmaz)
    bad = _plan_context()
    bad["floors"][1]["openings"][0]["sill_height"] = 1600.0                      # 1600 + 1500 = 3100 > 3000
    bad["floors"][0]["openings"][0]["position_from_start"] = 5800.0               # x1 = 6400 > 6000
    _, n = derive_level_openings(bad, bad["elevations"][0])
    eq("iki not (asma + dis)", len(n), 2)
    eq("seviye asma notu", any("seviye yuksekligini" in x for x in n), True)
    eq("cephe disi notu", any("disina dusuyor" in x for x in n), True)
    # sozlesme hatalari
    for label, mut in (("kat/seviye sayisi", lambda c: c["elevations"][0]["levels"].pop()),
                       ("axis_source yok", lambda c: c["elevations"][0].pop("axis_source"))):
        c = _plan_context()
        mut(c)
        try:
            derive_level_openings(c, c["elevations"][0])
            errors.append(f"{label}: ValueError beklenirdi")
        except ValueError:
            pass
    # egik dis duvar atlanir ve soylenir
    c = _plan_context()
    c["floors"][0]["walls"].append({"id": "w_egik", "start": [0, 0], "end": [3000, 3000], "thickness": 200.0, "layer": "D"})
    c["floors"][0]["openings"].append({"id": "egik", "type": "window", "wall_id": "w_egik", "position_from_start": 2000.0, "width": 800.0})
    _, n = derive_level_openings(c, c["elevations"][0])
    eq("egik/ic aciklik cepheye girmez (notlar temiz ya da egik notu)", all(("egik" in x) for x in n), True)
    # CIZIM: dikdortgen sayisi = turetilen + zemin-alti DASHED; context'siz plan cephe reddedilir
    doc = ezdxf.new()
    msp = doc.modelspace()
    ElevationSheet.draw(msp, ctx["elevations"][0], 0.0, 120.0, _NullAxisGrid(), 120.0, context=ctx)
    rects = list(msp.query("LWPOLYLINE[layer=='KAPI-PENCERE']"))
    eq("DXF: 3 + 1 = 4 aciklik", len(rects), 4)
    ys = sorted(round(min(p[1] for p in e.get_points("xy"))) for e in rects)
    eq("DXF: dikdortgen alt kenarlari (ZEMIN: 40, 40, 900; K1: 3700)", ys, [40, 40, 900, 3700])
    try:
        ElevationSheet.draw(ezdxf.new().modelspace(), ctx["elevations"][0], 0.0, 120.0, _NullAxisGrid(), 120.0)
        errors.append("context'siz plan cephe reddedilmeli")
    except ValueError:
        pass
    # jenerik cephe cizimi DEGISMEDI (geriye uyumluluk)
    doc2 = ezdxf.new()
    ElevationSheet.draw(doc2.modelspace(), ELEVATION, 0.0, 120.0, _NullAxisGrid(), 120.0)
    eq("jenerik cephe hala 5 aciklik", len(list(doc2.modelspace().query("LWPOLYLINE[layer=='KAPI-PENCERE']"))), 5)
    return errors


def main() -> int:
    groups = (
        ("plan acikliklarindan turetilen cephe (DEV-073)", check_plan_derived_dev073()),
        ("seviye istifi (elle hesaplanabilir)", check_placements_hand_computable()),
        ("pafta araligi machine_room'u kapsiyor", check_extent_includes_machine_room()),
        ("zemin-alti -> DASHED (yanlis-pozitif)", check_below_ground_gets_dashed_linetype()),
        ("pencere/kapi sayisi", check_window_and_door_counts()),
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
        print("\nCEPHE SELF-TEST BASARISIZ.")
        return 1
    print("\nCephe self-test BASARILI.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
