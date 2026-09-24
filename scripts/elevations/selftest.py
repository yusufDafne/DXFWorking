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


def main() -> int:
    groups = (
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
