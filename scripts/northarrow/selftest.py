#!/usr/bin/env python3
"""Kuzey oku + grafik olcek cubugu testleri (DEV-025).

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
from pafta import ScaleBar, format_scale_value, nice_scale_length_m  # noqa: E402

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


def check_nice_scale_length_hand_computable() -> list[str]:
    """`pafta.nice_scale_length_m`: 1:50/1:100/1:200/1:500 icin elle
    hesaplanabilir sonuclar (bkz. fonksiyon docstring'i)."""
    errors: list[str] = []
    cases = {50.0: 1.0, 100.0: 2.0, 200.0: 5.0, 500.0: 10.0}
    for denom, expected in cases.items():
        got = nice_scale_length_m(denom, target_printed_mm=20.0)
        if abs(got - expected) > TOLERANCE:
            errors.append(f"denom={denom}: {expected} bekleniyordu, {got} bulundu.")
    return errors


def check_scale_bar_printed_length_matches_target() -> list[str]:
    """1:50'de segment_m=1.0 -> segment_length=1000mm (units=mm) -> basili
    karsiligi 1000/50=20mm = HEDEFIN TAM KENDISI (elle hesaplanabilir)."""
    errors: list[str] = []
    bar = ScaleBar("1:50", units="mm")
    if abs(bar.segment_length - 1000.0) > TOLERANCE:
        errors.append(f"segment_length 1000 bekleniyordu, {bar.segment_length} bulundu.")
    printed_mm = bar.segment_length / 50.0
    if abs(printed_mm - 20.0) > TOLERANCE:
        errors.append(f"basili segment 20mm bekleniyordu, {printed_mm} bulundu.")
    if abs(bar.total_length - 5000.0) > TOLERANCE:
        errors.append(f"toplam uzunluk (5 segment) 5000 bekleniyordu, {bar.total_length} bulundu.")
    return errors


def check_scale_bar_draws_expected_entities() -> list[str]:
    """1 taban cizgisi + 6 tik (0..5 segment ucu) + 6 etiket = 13."""
    errors: list[str] = []
    doc = ezdxf.new()
    doc.layers.add("CERCEVE")
    doc.layers.add("METIN")
    msp = doc.modelspace()
    bar = ScaleBar("1:50", units="mm")
    bar.draw(msp, 0.0, 0.0)
    if len(msp) != 13:
        errors.append(f"13 varlik bekleniyordu, {len(msp)} bulundu.")
    texts = [e.dxf.text for e in msp.query("TEXT")]
    if texts[-1] != "5 m":
        errors.append(f"son etiket '5 m' bekleniyordu, {texts[-1]!r} bulundu.")
    if texts[0] != "0":
        errors.append(f"ilk etiket '0' bekleniyordu, {texts[0]!r} bulundu.")
    return errors


def check_format_scale_value() -> list[str]:
    errors: list[str] = []
    cases = {0.0: "0", 1.0: "1", 5.0: "5", 0.5: "0.5", 0.2: "0.2"}
    for value, expected in cases.items():
        got = format_scale_value(value)
        if got != expected:
            errors.append(f"{value}: '{expected}' bekleniyordu, '{got}' bulundu.")
    return errors


def main() -> int:
    groups = (
        ("rotate_point (saat yonu, 4 kardinal nokta)", check_rotate_point_hand_computable()),
        ("NorthArrow yaricapi olcekle dogrusal turer", check_north_arrow_scales_with_denominator()),
        ("NorthArrow varsayilan varlik sayisi", check_north_arrow_draws_expected_entities()),
        ("ozel stil enjekte edilebilir (Protocol)", check_custom_style_is_injectable()),
        ("nice_scale_length_m elle hesaplanabilir", check_nice_scale_length_hand_computable()),
        ("ScaleBar basili uzunlugu hedefle esler", check_scale_bar_printed_length_matches_target()),
        ("ScaleBar varlik sayisi + etiketler", check_scale_bar_draws_expected_entities()),
        ("format_scale_value", check_format_scale_value()),
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
        print("\nKUZEY OKU / OLCEK CUBUGU SELF-TEST BASARISIZ.")
        return 1
    print("\nKuzey oku / olcek cubugu self-test BASARILI.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
