#!/usr/bin/env python3
"""Sartname + oransal mahal kural kutuphanesi testleri (DEV-036).

Kullanim:
    python scripts/standards/selftest.py
Cikis kodu: 0 basarili, 1 basarisiz.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from standards import (  # noqa: E402
    RoomStandard,
    STANDARDS,
    check_room_proportions,
    check_room_types,
    room_aspect_ratio,
    validate_standards,
)

# 4000 x 2000 dikdortgen -> kisa kenar 2000, uzun kenar 4000 -> oran 2.0.
RECT_4000x2000 = [[0, 0], [4000, 0], [4000, 2000], [0, 2000]]
# 1400 x 1400 kare -> oran 1.0.
SQUARE_1400 = [[0, 0], [1400, 0], [1400, 1400], [0, 1400]]
# asansor sinirlari: min_ratio=1.0, max_ratio=1.5, min_short_edge_mm=1400.
# 2800 x 1400 -> kisa kenar TAM 1400 (siniri IHLAL ETMEZ), oran 2.0 (max 1.5'i
# ASAR) -> SADECE oran ihlali.
RATIO_ONLY_VIOLATION = [[0, 0], [2800, 0], [2800, 1400], [0, 1400]]
# 1400 x 1000 -> oran 1.4 (araligin ICINDE), kisa kenar 1000mm (asgari
# 1400mm'nin ALTINDA) -> SADECE kisa kenar ihlali.
SHORT_EDGE_ONLY_VIOLATION = [[0, 0], [1400, 0], [1400, 1000], [0, 1000]]


def check_room_aspect_ratio_hand_computable() -> list[str]:
    errors: list[str] = []
    ratio = room_aspect_ratio(RECT_4000x2000)
    if abs(ratio - 2.0) > 1e-9:
        errors.append(f"4000x2000 icin oran 2.0 bekleniyordu, {ratio} bulundu")
    square_ratio = room_aspect_ratio(SQUARE_1400)
    if abs(square_ratio - 1.0) > 1e-9:
        errors.append(f"1400x1400 icin oran 1.0 bekleniyordu, {square_ratio} bulundu")
    degenerate = room_aspect_ratio([[0, 0], [0, 0], [0, 0]])
    if degenerate != float("inf"):
        errors.append(f"kisa kenar 0 icin inf bekleniyordu, {degenerate} bulundu")
    return errors


def check_room_types_catches_typo_and_skips_missing() -> list[str]:
    errors: list[str] = []
    rooms = [
        {"id": "r1", "room_type": "asansor"},   # gecerli, hata YOK
        {"id": "r2"},                            # alan hic YOK, hata YOK (opt-in)
        {"id": "r3", "room_type": "aasansor"},  # yazim hatasi, HATA bekleniyor
    ]
    found = check_room_types(rooms)
    if len(found) != 1:
        errors.append(f"tam 1 hata bekleniyordu (r3), {len(found)} bulundu: {found}")
    elif "r3" not in found[0] or "aasansor" not in found[0]:
        errors.append(f"hata mesaji 'r3'/'aasansor' icermiyor: {found[0]!r}")
    return errors


def check_room_proportions_ratio_violation() -> list[str]:
    """RATIO_ONLY_VIOLATION: kisa kenar TAM sinirda (1400mm, ihlal YOK),
    oran 2.0 (max 1.5'i ASAR) -> TAM 1 uyari (yalnizca oran) beklenir."""
    errors: list[str] = []
    rooms = [{"id": "r1", "room_type": "asansor", "polygon": RATIO_ONLY_VIOLATION,
              "area_m2": 3.92}]
    warnings = check_room_proportions(rooms, "mm")
    if len(warnings) != 1:
        return [f"tam 1 uyari bekleniyordu (oran ihlali), {len(warnings)} bulundu: {warnings}"]
    if "en-boy orani" not in warnings[0] or "r1" not in warnings[0]:
        errors.append(f"beklenmedik uyari metni: {warnings[0]!r}")
    return errors


def check_room_proportions_short_edge_violation() -> list[str]:
    """SHORT_EDGE_ONLY_VIOLATION: oran 1.4 (araligin [1.0,1.5] ICINDE, ihlal
    YOK), kisa kenar 1000mm (asgari 1400mm'nin ALTINDA) -> TAM 1 uyari
    (yalnizca kisa kenar) beklenir."""
    rooms = [{"id": "r1", "room_type": "asansor", "polygon": SHORT_EDGE_ONLY_VIOLATION,
              "area_m2": 1.4}]
    warnings = check_room_proportions(rooms, "mm")
    if len(warnings) != 1:
        return [f"tam 1 uyari bekleniyordu (kisa kenar ihlali), {len(warnings)} bulundu: {warnings}"]
    if "kisa kenar" not in warnings[0]:
        return [f"kisa kenar uyarisi bekleniyordu: {warnings}"]
    return []


def check_room_proportions_within_limits_no_false_positive() -> list[str]:
    """1400x1400 kare, asansor sinirlarinin (oran [1.0,1.5], kisa kenar
    >=1400mm) TAM ICINDE - HICBIR uyari UretmeMELI (yanlis-pozitif testi)."""
    rooms = [{"id": "r1", "room_type": "asansor", "polygon": SQUARE_1400,
              "area_m2": 1.96}]
    warnings = check_room_proportions(rooms, "mm")
    if warnings:
        return [f"uyari beklenmiyordu, {len(warnings)} bulundu: {warnings}"]
    return []


def check_room_proportions_skips_untyped_and_meters() -> list[str]:
    """room_type verilmeyen oda kontrole HIC GIRMEZ. 'm' biriminde de
    kisa-kenar mm'ye DOGRU cevriliyor mu (1.0m -> 1000mm, asgarinin
    ALTINDA -> UYARI beklenir; 1.4m -> 1400mm, sinirda -> UYARI YOK)."""
    errors: list[str] = []
    untyped = [{"id": "r1", "polygon": SHORT_EDGE_ONLY_VIOLATION, "area_m2": 1.4}]
    if check_room_proportions(untyped, "mm"):
        errors.append("room_type verilmeyen oda icin uyari beklenmiyordu")

    meters_narrow = [{"id": "r2", "room_type": "asansor",
                       "polygon": [[0, 0], [1.0, 0], [1.0, 3.5], [0, 3.5]],
                       "area_m2": 3.5}]
    warnings = check_room_proportions(meters_narrow, "m")
    if not any("kisa kenar" in w for w in warnings):
        errors.append(f"'m' biriminde kisa kenar mm'ye cevrilip UYARI vermeliydi: {warnings}")
    return errors


def check_room_proportions_area_violation() -> list[str]:
    """min_area_m2 gercek katalogda HICBIR girişte kullanilmiyor - bu yuzden
    GECICI bir test standardi eklenip (try/finally ile geri alinip) alan
    kontrolunun CALISTIGI dogrudan sinanir."""
    errors: list[str] = []
    key = "__selftest_area__"
    STANDARDS[key] = RoomStandard(
        key, "Test odasi", min_ratio=1.0, max_ratio=10.0, min_area_m2=5.0,
        source="selftest gecici girdi")
    try:
        rooms = [{"id": "r1", "room_type": key, "polygon": SQUARE_1400, "area_m2": 1.96}]
        warnings = check_room_proportions(rooms, "mm")
        if not any("alan" in w for w in warnings):
            errors.append(f"alan ihlali icin UYARI bekleniyordu: {warnings}")
    finally:
        del STANDARDS[key]
    return errors


def check_validate_standards_catches_broken_catalog() -> list[str]:
    """Gercek katalog TEMIZ donmeli (yanlis-pozitif testi); GECICI olarak
    bozuk bir girdi (max_ratio < min_ratio) eklenince validate_standards
    bunu YAKALAMALI (kasitli bozma testi, try/finally ile geri alinir)."""
    errors: list[str] = []
    clean = validate_standards()
    if clean:
        return [f"gercek katalog TEMIZ donmeliydi, {len(clean)} hata bulundu: {clean}"]

    key = "__selftest_broken__"
    STANDARDS[key] = RoomStandard(
        key, "Bozuk test", min_ratio=2.0, max_ratio=1.0, source="")
    try:
        broken = validate_standards()
        if not broken:
            errors.append("max_ratio < min_ratio + bos source YAKALANMALIYDI")
        elif len(broken) < 2:
            errors.append(f"EN AZ 2 hata bekleniyordu (oran + bos source), {len(broken)} bulundu: {broken}")
    finally:
        del STANDARDS[key]
    return errors


def main() -> int:
    groups = (
        ("room_aspect_ratio elle hesaplanabilir (+ dejenere durum)", check_room_aspect_ratio_hand_computable()),
        ("check_room_types: yazim hatasi YAKALANIR, eksik alan atlanir", check_room_types_catches_typo_and_skips_missing()),
        ("check_room_proportions: oran ihlali UYARI", check_room_proportions_ratio_violation()),
        ("check_room_proportions: kisa kenar ihlali AYRI UYARI", check_room_proportions_short_edge_violation()),
        ("check_room_proportions: sinir icinde yanlis-pozitif YOK", check_room_proportions_within_limits_no_false_positive()),
        ("check_room_proportions: opt-in + 'm' birimi donusumu", check_room_proportions_skips_untyped_and_meters()),
        ("check_room_proportions: alan ihlali (gecici standart)", check_room_proportions_area_violation()),
        ("validate_standards: temiz katalog + kasitli bozma yakalanir", check_validate_standards_catches_broken_catalog()),
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
        print("\nSTANDARDS SELF-TEST BASARISIZ.")
        return 1
    print("\nStandards self-test BASARILI.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
