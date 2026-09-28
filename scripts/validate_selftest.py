#!/usr/bin/env python3
"""`validate.py`nin KENDI (herhangi bir cizim modulune ait olmayan,
orkestrasyon seviyesindeki) arity-1 kontrollerinin testleri (DEV-041).

`check_walls` bugune kadar yalniz `golden_report.py --golden-set`
uzerinden DOLAYLI test ediliyordu (zaten GECERLI golden context'lerle);
HATA yollari hic dogrudan sinanmamisti. DEV-041'in kapi-bosluk kontrolu
GERCEK bir uretim hatasini yakaladigi icin (bkz. `scripts/walls/CLAUDE.md`
"Bilinen sinirlar") kendi odakli testini hak ediyor - kok CLAUDE.md'nin
"kasitli bozma + yanlis-pozitif" disiplini AYNEN uygulanir.

Kullanim:
    python scripts/validate_selftest.py
Cikis kodu: 0 basarili, 1 basarisiz.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from validate import check_walls  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REAL_CONTEXT_PATH = PROJECT_ROOT / "context.json"


def _fixture(door_position: float):
    """KAPALI bir dikdortgen (w_bottom/w_right/w_top/w_left, 10000x5000)
    + iceriye bolen bir T-duvari (w_mid, dusey, (5000,0)-(5000,5000)).
    Dikdortgenin DORT kosesi birbirine BAGLIDIR (sarkan uc YOK); w_mid'in
    (5000,0) UCU w_bottom UZERINDE bir T-kesisimidir - TEK degisken bu.
    w_bottom uzerindeki TEK kapi `door_position`de, genislik 900mm."""
    walls = [
        {"id": "w_bottom", "start": [0, 0], "end": [10000, 0], "thickness": 200.0, "layer": "DUVARLAR"},
        {"id": "w_right", "start": [10000, 0], "end": [10000, 5000], "thickness": 200.0, "layer": "DUVARLAR"},
        {"id": "w_top", "start": [10000, 5000], "end": [0, 5000], "thickness": 200.0, "layer": "DUVARLAR"},
        {"id": "w_left", "start": [0, 5000], "end": [0, 0], "thickness": 200.0, "layer": "DUVARLAR"},
        {"id": "w_mid", "start": [5000, 0], "end": [5000, 5000], "thickness": 200.0, "layer": "DUVARLAR"},
    ]
    openings = [
        {"id": "d1", "type": "door", "wall_id": "w_bottom",
         "position_from_start": door_position, "width": 900.0, "layer": "KAPI-PENCERE"},
    ]
    return walls, openings


def check_wall_ending_in_door_gap_flags() -> list[str]:
    """Kapi w1 uzerinde position=5000 (aralik [4550,5450]) - w2'nin
    (5000,0) ucu bu araligin TAM ICINDE. HATA beklenir, mesaj kapi/
    pencere BOSLUGUNU adlandirmali (genel 'sarkan uc' mesaji DEGIL)."""
    walls, openings = _fixture(door_position=5000.0)
    errors = check_walls("mm", walls, openings)
    if len(errors) != 1:
        return [f"TAM 1 hata beklenirdi, {len(errors)} geldi: {errors}"]
    if "BOSLUGUNA baglaniyor" not in errors[0]:
        return [f"hata mesaji kapi bosluğunu ADLANDIRMALIYDI: {errors[0]}"]
    return []


def check_wall_ending_outside_door_gap_false_positive() -> list[str]:
    """Kapi w1 uzerinde position=8000 (aralik [7550,8450]) - w2'nin
    (5000,0) ucu bu araliktan UZAK, NORMAL bir T-kesisimidir. HATA
    OLMAMALI."""
    walls, openings = _fixture(door_position=8000.0)
    errors = check_walls("mm", walls, openings)
    return [f"normal bir T-kesisimi HATA URETMEMELIYDI: {errors}"] if errors else []


def check_wall_ending_at_door_jamb_edge_is_valid() -> list[str]:
    """Kapi w1 uzerinde position=5450 (aralik [5000,5900]) - w2'nin
    (5000,0) ucu TAM boslugun SINIRINDA (jamb), KESIN ICERIDE degil.
    Bu GECERLI bir baglantidir (bir duvar tam kapi pervazinda bitebilir),
    HATA OLMAMALI - sinir esitligi de HATA sayilsaydi bu YANLIS-POZITIF
    olurdu."""
    walls, openings = _fixture(door_position=5450.0)
    errors = check_walls("mm", walls, openings)
    return [f"boslugun TAM SINIRINDAKI bir uc HATA URETMEMELIYDI: {errors}"] if errors else []


def check_genuinely_dangling_end_still_flagged() -> list[str]:
    """Kapi-bosluk kontrolu, ORIJINAL 'sarkan uc' (hicbir seye baglanmayan)
    testini BOZMAMALI - tek basina, hicbir seye degmeyen bir duvar HALA
    'sarkan uc' mesajiyla yakalanmali (kapi bosluk mesaji DEGIL)."""
    walls = [{"id": "w_lone", "start": [0, 0], "end": [3000, 0],
              "thickness": 200.0, "layer": "DUVARLAR"}]
    errors = check_walls("mm", walls, [])
    if len(errors) != 2:  # iki uc da sarkan
        return [f"2 sarkan uc hatasi beklenirdi, {len(errors)} geldi: {errors}"]
    if not all("sarkan uc" in e for e in errors):
        return [f"mesajlar 'sarkan uc' OLMALIYDI: {errors}"]
    return []


def check_real_project_bug_is_caught() -> list[str]:
    """GERCEK context.json'daki (rev-22) IKI bilinen hata (bkz.
    `scripts/walls/CLAUDE.md` 'Bilinen sinirlar') bu kontrolle
    GERCEKTEN yakalaniyor mu - `w_unit_A_B` ve `uA_w_hol_mutfak_v`,
    ikisi de `band_south` uzerindeki bir kapi bosluguna baglaniyor.
    Gercek dosya yoksa test ATLANIR."""
    if not REAL_CONTEXT_PATH.exists():
        return []
    context = json.loads(REAL_CONTEXT_PATH.read_text(encoding="utf-8"))
    floor = next(f for f in context["floors"] if f["id"] == "normal1")
    errors = check_walls(context["meta"]["units"], floor["walls"], floor["openings"])
    gap_errors = [e for e in errors if "BOSLUGUNA baglaniyor" in e]
    flagged_ids = {wid for wid in ("w_unit_A_B", "uA_w_hol_mutfak_v") if any(wid in e for e in gap_errors)}
    missing = {"w_unit_A_B", "uA_w_hol_mutfak_v"} - flagged_ids
    if missing:
        return [f"GERCEK projede beklenen duvarlar YAKALANMADI: {missing} "
                f"(context.json degisti/duzeltildi olabilir, bu test guncellenmeli): {gap_errors}"]
    return []


def main() -> int:
    groups = (
        ("kapi bosluguna baglanan duvar ucu UYARI/HATA verir", check_wall_ending_in_door_gap_flags()),
        ("kapidan UZAK bir T-kesisimi YANLIS-POZITIF uretmez", check_wall_ending_outside_door_gap_false_positive()),
        ("bosluk SINIRINDAKI (jamb) bir uc YANLIS-POZITIF uretmez", check_wall_ending_at_door_jamb_edge_is_valid()),
        ("GERCEK sarkan uc hala yakalaniyor (regresyon yok)", check_genuinely_dangling_end_still_flagged()),
        ("GERCEK projedeki rev-22 hatasi (2 duvar) YAKALANIYOR", check_real_project_bug_is_caught()),
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
        print("\nVALIDATE SELF-TEST BASARISIZ.")
        return 1
    print("\nValidate self-test BASARILI.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
