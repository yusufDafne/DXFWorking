#!/usr/bin/env python3
"""Katman renk organizasyonu testleri (DEV-030).

Ortak disiplin (kok CLAUDE.md): kurallar KASITLI BOZMAYLA sinanir - "temiz
dondu" cikisi tek basina hicbir sey kanitlamaz (kontrol hic calismasa da
temiz donerdi).

Kullanim:
    python scripts/palette/selftest.py
Cikis kodu: 0 basarili, 1 basarisiz.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from palette import (  # noqa: E402
    CONTRAST_MIN_DISTANCE,
    PALETTE,
    LayerColor,
    _distance,
    color_for,
    validate_palette,
)


def check_real_palette_is_clean() -> list[str]:
    """Gercek PALETTE, kendi kurallarini ihlal ETMEMELI - "temiz dondu"
    tek basina yeterli degil ama bu, sistemin GERCEKTEN kullandigi
    tabloyu da sinamak zorundadir."""
    return validate_palette()


def check_duplicate_color_is_caught() -> list[str]:
    """KASITLI BOZMA: iki FARKLI katmana AYNI rengi ata, hata YAKALANMALI.
    Bu, DEV-030'un kurulma nedeni olan somut bulgunun (eski COLUMN_RGB'nin
    3 katmana tek renk atamasi) dogrudan regresyon testidir."""
    errors: list[str] = []
    broken = dict(PALETTE)
    broken["_TEST_DUP_A"] = LayerColor("_TEST_DUP_A", (10, 20, 30))
    broken["_TEST_DUP_B"] = LayerColor("_TEST_DUP_B", (10, 20, 30))
    import palette as palette_module
    original = palette_module.PALETTE
    palette_module.PALETTE = broken
    try:
        violations = validate_palette()
    finally:
        palette_module.PALETTE = original
    if not any("_TEST_DUP_A" in v and "_TEST_DUP_B" in v for v in violations):
        errors.append(f"ayni-renk ihlali YAKALANMADI: {violations}")
    return errors


def check_close_contrast_group_is_caught() -> list[str]:
    """KASITLI BOZMA: ayni contrast_group'ta, esik mesafenin ALTINDA iki
    renk ata - hata YAKALANMALI. Yanlis-pozitif: esigin TAM USTUNDE iki
    renk hata VERMEMELI."""
    errors: list[str] = []
    import palette as palette_module
    original = palette_module.PALETTE

    too_close = dict(PALETTE)
    too_close["_TEST_A"] = LayerColor("_TEST_A", (100, 100, 100), "primary")
    too_close["_TEST_B"] = LayerColor("_TEST_B", (110, 100, 100), "primary")  # mesafe=10 < 40
    palette_module.PALETTE = too_close
    try:
        violations = validate_palette()
    finally:
        palette_module.PALETTE = original
    if not any("_TEST_A" in v and "_TEST_B" in v for v in violations):
        errors.append(f"yakin-kontrast ihlali YAKALANMADI: {violations}")

    far_enough = dict(PALETTE)
    far_enough["_TEST_C"] = LayerColor("_TEST_C", (0, 0, 0), "primary_test_isolated")
    far_enough["_TEST_D"] = LayerColor("_TEST_D", (40, 0, 0), "primary_test_isolated")  # mesafe=40 tam esik
    palette_module.PALETTE = far_enough
    try:
        violations = validate_palette()
    finally:
        palette_module.PALETTE = original
    if any("_TEST_C" in v or "_TEST_D" in v for v in violations):
        errors.append(f"esigin TAM UZERINDEKI mesafe (40.0) YANLIS-POZITIF uretti: {violations}")
    return errors


def check_different_contrast_group_is_exempt() -> list[str]:
    """Farkli contrast_group'taki (veya contrast_group=None olan, orn.
    tefris) katmanlar birbirine YAKIN olsa bile ihlal SAYILMAMALI - bu,
    tefris ailesinin BILEREK dusuk kontrastli tutulmasi kararinin (rev-10)
    korundugunu dogrular."""
    errors: list[str] = []
    import palette as palette_module
    original = palette_module.PALETTE
    close_but_exempt = dict(PALETTE)
    close_but_exempt["_TEST_E"] = LayerColor("_TEST_E", (5, 5, 5), None)
    close_but_exempt["_TEST_F"] = LayerColor("_TEST_F", (8, 5, 5), "other_group")
    palette_module.PALETTE = close_but_exempt
    try:
        violations = validate_palette()
    finally:
        palette_module.PALETTE = original
    if any("_TEST_E" in v or "_TEST_F" in v for v in violations):
        errors.append(f"farkli/None gruplar arasi yakinlik YANLIS-POZITIF uretti: {violations}")
    return errors


def check_color_for_known_and_unknown() -> list[str]:
    """Kayitli bir isim rengi dondurmeli; kayitsiz bir isim HATA vermeli
    (yeni katman PALETTE'e KAYDEDILMEDEN renk ALAMAZ disiplini)."""
    errors: list[str] = []
    if color_for("AKS") != (67, 77, 88):
        errors.append(f"AKS rengi (67,77,88) bekleniyordu, {color_for('AKS')} bulundu")
    try:
        color_for("_HICBIR_KATMAN_YOK_")
        errors.append("kayitsiz isim HATA vermeliydi, vermedi")
    except KeyError:
        pass
    return errors


def check_kolon_family_is_no_longer_identical() -> list[str]:
    """DEV-030'un kurulma nedeni olan somut bulgunun dogrudan regresyonu:
    KOLON / KOLON-TARAMA / KOLON-METIN ARTIK ayni renk OLMAMALI."""
    kolon = color_for("KOLON")
    tarama = color_for("KOLON-TARAMA")
    metin = color_for("KOLON-METIN")
    errors: list[str] = []
    if kolon == tarama or kolon == metin or tarama == metin:
        errors.append(f"KOLON ailesi hala ayni renk tasiyor: {kolon}, {tarama}, {metin}")
    return errors


def check_distance_hand_computable() -> list[str]:
    """_distance elle hesaplanabilir olmali: (0,0,0) ile (3,4,0) arasi TAM
    5.0 olmalidir (3-4-5 ucgeni)."""
    d = _distance((0, 0, 0), (3, 4, 0))
    if abs(d - 5.0) > 1e-9:
        return [f"mesafe 5.0 bekleniyordu, {d} bulundu"]
    return []


def main() -> int:
    groups = (
        ("gercek PALETTE kendi kurallarini ihlal etmiyor", check_real_palette_is_clean()),
        ("ayni-renk ihlali yakalanir (KOLON bulgusunun regresyonu)", check_duplicate_color_is_caught()),
        ("yakin-kontrast ihlali yakalanir (+ esik-siniri yanlis-pozitif)", check_close_contrast_group_is_caught()),
        ("farkli/None grup yakinligi muaf (tefris ailesi korunur)", check_different_contrast_group_is_exempt()),
        ("color_for: bilinen/bilinmeyen isim", check_color_for_known_and_unknown()),
        ("KOLON ailesi artik ayni renk degil", check_kolon_family_is_no_longer_identical()),
        ("_distance elle hesaplanabilir (3-4-5 ucgeni)", check_distance_hand_computable()),
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
        print("\nPALETTE SELF-TEST BASARISIZ.")
        return 1
    print("\nPalette self-test BASARILI.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
