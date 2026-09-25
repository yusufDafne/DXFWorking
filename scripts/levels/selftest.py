#!/usr/bin/env python3
"""Kot (seviye/datum) modulu testleri (DEV-029).

Kullanim:
    python scripts/levels/selftest.py
Cikis kodu: 0 basarili, 1 basarisiz.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import ezdxf  # noqa: E402

from levels import (  # noqa: E402
    LevelMark,
    draw_level_marks,
    draw_plan_level_marks,
    ensure_level_layer,
    format_level,
    level_boundaries_from_placements,
)

TOLERANCE = 1e-6


def check_format_level_hand_computable() -> list[str]:
    """Kullanicinin onayladigi format: isaret + 2 ondalikli metre, sifir
    icin ±0.00. Elle hesaplanabilir 5 durum."""
    errors: list[str] = []
    cases = [
        (3000.0, "+3.00"),
        (-200.0, "-0.20"),
        (0.0, "±0.00"),
        (1.0, "±0.00"),        # 0.001m -> 2 ondalikta 0.00'a yuvarlanir
        (-1750.0, "-1.75"),
        (17500.0, "+17.50"),
    ]
    for value_mm, expected in cases:
        got = format_level(value_mm)
        if got != expected:
            errors.append(f"value_mm={value_mm}: '{expected}' bekleniyordu, '{got}' bulundu")
    return errors


def check_level_boundaries_hand_computable() -> list[str]:
    """Elle hesaplanabilir bir istif: (-3000,0), (0,4000), (4000,7000) ->
    sinirlar {-3000,0,4000,7000} (tekillestirilmis, siralanmis).
    Yanlis-pozitif: bos liste -> bos liste."""
    errors: list[str] = []
    placements = [("A", -3000.0, 0.0), ("B", 0.0, 4000.0), ("C", 4000.0, 7000.0)]
    got = level_boundaries_from_placements(placements)
    expected = [-3000.0, 0.0, 4000.0, 7000.0]
    if got != expected:
        errors.append(f"{expected} bekleniyordu, {got} bulundu")
    if level_boundaries_from_placements([]) != []:
        errors.append("bos placements listesi bos sinir listesi VERMELIYDI")
    return errors


def check_level_mark_draws_two_entities() -> list[str]:
    """Varsayilan stil: 1 LWPOLYLINE (bayrak) + 1 TEXT (kot metni) = 2 varlik."""
    errors: list[str] = []
    doc = ezdxf.new()
    ensure_level_layer(doc)
    msp = doc.modelspace()
    mark = LevelMark("1:50")
    mark.draw(msp, (0.0, 3000.0), 3000.0)
    if len(msp) != 2:
        errors.append(f"2 varlik (bayrak+metin) bekleniyordu, {len(msp)} bulundu")
    texts = list(msp.query("TEXT"))
    if len(texts) != 1 or texts[0].dxf.text != "+3.00":
        errors.append(f"TEXT '+3.00' bekleniyordu, bulunan: {[t.dxf.text for t in texts]}")
    return errors


def check_mark_size_scales_linearly() -> list[str]:
    """Yaricap/boy, `to_modelspace` ile OLCEGE dogrusal turer: 1:100'deki
    boyut, 1:50'dekinin TAM 2 katı olmalidir (elle hesaplanabilir,
    NorthArrow selftest'iyle AYNI desen)."""
    errors: list[str] = []
    m50 = LevelMark("1:50")
    m100 = LevelMark("1:100")
    if abs(m100.size - 2 * m50.size) > TOLERANCE:
        errors.append(f"1:100 boyu 1:50'nin 2 katı olmali: {m50.size} vs {m100.size}")
    if abs(m100.text_height - 2 * m50.text_height) > TOLERANCE:
        errors.append(f"1:100 metin yuksekligi 1:50'nin 2 katı olmali: {m50.text_height} vs {m100.text_height}")
    return errors


def check_draw_level_marks_entity_count() -> list[str]:
    """N sinir icin draw_level_marks TAM 2*N varlik eklemeli (elle
    hesaplanabilir)."""
    errors: list[str] = []
    doc = ezdxf.new()
    ensure_level_layer(doc)
    msp = doc.modelspace()
    mark = LevelMark("1:50")
    boundaries = [-3000.0, 0.0, 4000.0, 7000.0]
    draw_level_marks(msp, mark, boundaries, anchor_x=0.0)
    if len(msp) != 2 * len(boundaries):
        errors.append(f"{2 * len(boundaries)} varlik bekleniyordu, {len(msp)} bulundu")
    return errors


def check_plan_level_marks_opt_in() -> list[str]:
    """Veri VARSA cizilir, YOKSA HICBIR SEY cizilmez (kuzey oku ile AYNI
    'veri yoksa uydurma' deseni) - hem pozitif hem yanlis-pozitif tarafi."""
    errors: list[str] = []
    doc = ezdxf.new()
    ensure_level_layer(doc)
    msp = doc.modelspace()
    mark = LevelMark("1:50")

    empty_floor = {"level_marks": []}
    draw_plan_level_marks(msp, empty_floor, mark)
    if len(msp) != 0:
        errors.append(f"level_marks bos iken 0 varlik bekleniyordu, {len(msp)} bulundu")

    floor = {"level_marks": [
        {"id": "lm1", "position": [1000.0, 2000.0], "value_mm": -150.0},
        {"id": "lm2", "position": [3000.0, 2000.0], "value_mm": 300.0},
    ]}
    draw_plan_level_marks(msp, floor, mark)
    if len(msp) != 4:
        errors.append(f"2 kayit icin 4 varlik bekleniyordu, {len(msp)} bulundu")
    return errors


def check_custom_style_is_injectable() -> list[str]:
    """`LevelMarkStyle` Protocol'u enjekte edilebilir olmali - sahte bir
    stil verilince `LevelMark` KENDI cizim mantigini DEGIL, verilen stili
    cagirmalidir (`NorthArrow` selftest'iyle AYNI desen)."""
    calls: list[tuple] = []

    class _FakeStyle:
        def draw(self, msp, anchor, value_mm, size, text_height, layer, text_layer) -> None:
            calls.append((anchor, value_mm))

    doc = ezdxf.new()
    msp = doc.modelspace()
    mark = LevelMark("1:50", style=_FakeStyle())
    mark.draw(msp, (5.0, 10.0), 1234.0)
    if calls != [((5.0, 10.0), 1234.0)]:
        return [f"enjekte edilen stil beklenen argumanlarla cagrilmadi: {calls}"]
    if len(msp) != 0:
        return ["sahte stil hicbir DXF varligi eklemedi ama modelspace BOS degil"]
    return []


def check_ensure_level_layer_sets_rgb() -> list[str]:
    errors: list[str] = []
    doc = ezdxf.new()
    ensure_level_layer(doc)
    if "KOT" not in doc.layers:
        return ["KOT katmani olusturulmadi"]
    layer = doc.layers.get("KOT")
    from levels import LEVEL_RGB
    if tuple(layer.rgb) != LEVEL_RGB:
        errors.append(f"layer.rgb {LEVEL_RGB} bekleniyordu, {layer.rgb} bulundu")
    return errors


def main() -> int:
    groups = (
        ("format_level elle hesaplanabilir (6 durum)", check_format_level_hand_computable()),
        ("level_boundaries elle hesaplanabilir (+ bos liste)", check_level_boundaries_hand_computable()),
        ("LevelMark.draw 2 varlik (bayrak+metin)", check_level_mark_draws_two_entities()),
        ("boyut olcekle dogrusal turer (1:100 = 1:50 x2)", check_mark_size_scales_linearly()),
        ("draw_level_marks N sinir icin 2N varlik", check_draw_level_marks_entity_count()),
        ("plan kot isaretleri opt-in (veri yoksa cizilmez)", check_plan_level_marks_opt_in()),
        ("ozel stil enjekte edilebilir (Protocol)", check_custom_style_is_injectable()),
        ("KOT katmani RGB'si kod-sahipli", check_ensure_level_layer_sets_rgb()),
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
        print("\nKOT SELF-TEST BASARISIZ.")
        return 1
    print("\nKot self-test BASARILI.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
