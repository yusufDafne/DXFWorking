#!/usr/bin/env python3
"""Kuzey oku testleri (DEV-025).

rev-18: bu modulun ayni revizyonda tanittigi `pafta::ScaleBar` (grafik
olcek cubugu) kullanici geri bildirimiyle KALDIRILDI (bkz.
DEVELOPMENT_HISTORY.md HD-012); bu dosya artik SADECE kuzey okunu sinar.

Kullanim:
    python scripts/northarrow/selftest.py
Cikis kodu: 0 basarili, 1 basarisiz.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import ezdxf  # noqa: E402

from northarrow import DefaultNorthArrowStyle, NorthArrow, rotate_point  # noqa: E402

TOLERANCE = 1e-6


def check_rotate_point_hand_computable() -> list[str]:
    """Saat yonu konvansiyonu (0=yukari, 90=sag): elle dogrulanabilir 4
    kardinal nokta + bir ara aci (30 derece)."""
    errors: list[str] = []
    cases = [
        (0.0, (0.0, 10.0)),
        (90.0, (10.0, 0.0)),
        (180.0, (0.0, -10.0)),
        (270.0, (-10.0, 0.0)),
    ]
    for angle, expected in cases:
        got = rotate_point((0.0, 0.0), 10.0, angle)
        if abs(got[0] - expected[0]) > 1e-3 or abs(got[1] - expected[1]) > 1e-3:
            errors.append(f"angle={angle}: {expected} bekleniyordu, {got} bulundu.")
    return errors


def check_north_arrow_scales_with_denominator() -> list[str]:
    """Yaricap, `to_modelspace` ile OLCEGE dogrusal turer: 1:100'deki
    yaricap, 1:50'dekinin TAM 2 katı olmalidir (elle hesaplanabilir)."""
    errors: list[str] = []
    a50 = NorthArrow("1:50")
    a100 = NorthArrow("1:100")
    if abs(a100.radius - 2 * a50.radius) > TOLERANCE:
        errors.append(f"1:100 yaricapi 1:50'nin 2 katı olmali: {a50.radius} vs {a100.radius}.")
    return errors


def check_north_arrow_draws_expected_entities() -> list[str]:
    """Varsayilan stil: 1 daire + 1 ucgen (ibre) + 1 metin = 3 varlik."""
    errors: list[str] = []
    doc = ezdxf.new()
    doc.layers.add("CERCEVE")
    doc.layers.add("METIN")
    msp = doc.modelspace()
    arrow = NorthArrow("1:50")
    arrow.draw(msp, (0.0, 0.0), 45.0)
    if len(msp) != 3:
        errors.append(f"3 varlik (daire+ucgen+metin) bekleniyordu, {len(msp)} bulundu.")
    circles = list(msp.query("CIRCLE"))
    if len(circles) != 1 or abs(circles[0].dxf.radius - arrow.radius) > TOLERANCE:
        errors.append("daire yaricapi arrow.radius ile ESLESMIYOR.")
    return errors


def check_custom_style_is_injectable() -> list[str]:
    """`NorthArrowStyle` Protocol'u enjekte edilebilir olmali (kullanici
    talebi: 'entegrasyon zor olmasin') - sahte bir stil verilince NorthArrow
    KENDI cizim mantigini DEGIL, verilen stili cagirmalidir."""
    calls: list[tuple] = []

    class _FakeStyle:
        def draw(self, msp, center, radius, angle_deg, layer, text_layer, text_height) -> None:
            calls.append((center, radius, angle_deg))

    doc = ezdxf.new()
    msp = doc.modelspace()
    arrow = NorthArrow("1:50", style=_FakeStyle())
    arrow.draw(msp, (5.0, 5.0), 10.0)
    if calls != [((5.0, 5.0), arrow.radius, 10.0)]:
        return [f"enjekte edilen stil beklenen argumanlarla cagrilmadi: {calls}"]
    if len(msp) != 0:
        return ["sahte stil hicbir DXF varligi eklemedi ama modelspace BOS degil."]
    return []


def main() -> int:
    groups = (
        ("rotate_point (saat yonu, 4 kardinal nokta)", check_rotate_point_hand_computable()),
        ("NorthArrow yaricapi olcekle dogrusal turer", check_north_arrow_scales_with_denominator()),
        ("NorthArrow varsayilan varlik sayisi", check_north_arrow_draws_expected_entities()),
        ("ozel stil enjekte edilebilir (Protocol)", check_custom_style_is_injectable()),
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
        print("\nKUZEY OKU SELF-TEST BASARISIZ.")
        return 1
    print("\nKuzey oku self-test BASARILI.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
