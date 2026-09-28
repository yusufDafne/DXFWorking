#!/usr/bin/env python3
"""Yansitilmis tavan plani (RCP) modulu testleri (DEV-023).

Kullanim:
    python scripts/ceiling/selftest.py
Cikis kodu: 0 basarili, 1 basarisiz.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import ezdxf  # noqa: E402

from ceiling import (  # noqa: E402
    CeilingSheet,
    draw_ceiling_label,
    ensure_ceiling_layer,
    floor_has_ceiling_data,
    resolve_room_ceilings,
)
from walls import WallNetwork, draw_wall_network  # noqa: E402

ROOM_SQUARE = [[0, 0], [4000, 0], [4000, 3000], [0, 3000]]  # centroid = (2000, 1500)

SIMPLE_FLOOR = {
    "rooms": [
        {"id": "r1", "name": "Oda 1", "no": "01", "area_m2": 12.0,
         "polygon": ROOM_SQUARE, "ceiling_height_mm": 2500.0,
         "ceiling_finish": "alcipan asma tavan"},
        {"id": "r2", "name": "Oda 2", "no": "02", "area_m2": 12.0,
         "polygon": [[5000, 0], [9000, 0], [9000, 3000], [5000, 3000]]},
    ],
    "walls": [
        {"id": "w1", "start": [0, 0], "end": [9000, 0], "thickness": 200.0, "layer": "DUVARLAR"},
        {"id": "w2", "start": [9000, 0], "end": [9000, 3000], "thickness": 200.0, "layer": "DUVARLAR"},
        {"id": "w3", "start": [9000, 3000], "end": [0, 3000], "thickness": 200.0, "layer": "DUVARLAR"},
        {"id": "w4", "start": [0, 3000], "end": [0, 0], "thickness": 200.0, "layer": "DUVARLAR"},
    ],
    "openings": [],
}


def check_resolve_room_ceilings_hand_computable() -> list[str]:
    """r1 ceiling_height_mm TASIYOR (dahil edilmeli, centroid elle
    hesaplanabilir: 4000x3000 dikdortgen -> (2000,1500)); r2 TASIMIYOR
    (yanlis-pozitif: SONUCA DAHIL EDILMEMELI)."""
    errors: list[str] = []
    resolved = resolve_room_ceilings(SIMPLE_FLOOR)
    if len(resolved) != 1:
        errors.append(f"1 kayit bekleniyordu (r2 haric), {len(resolved)} bulundu")
        return errors
    data = resolved[0]
    if data.room_id != "r1":
        errors.append(f"room_id 'r1' bekleniyordu, '{data.room_id}' bulundu")
    if abs(data.height_mm - 2500.0) > 1e-6:
        errors.append(f"height_mm 2500.0 bekleniyordu, {data.height_mm} bulundu")
    if data.finish != "alcipan asma tavan":
        errors.append(f"finish beklenmedik: {data.finish!r}")
    if abs(data.centroid[0] - 2000.0) > 1e-6 or abs(data.centroid[1] - 1500.0) > 1e-6:
        errors.append(f"centroid (2000,1500) bekleniyordu, {data.centroid} bulundu")
    return errors


def check_floor_has_ceiling_data() -> list[str]:
    """En az bir oda ceiling_height_mm tasiyorsa True; HICBIR oda
    tasimiyorsa False (yanlis-pozitif)."""
    errors: list[str] = []
    if not floor_has_ceiling_data(SIMPLE_FLOOR):
        errors.append("SIMPLE_FLOOR icin True bekleniyordu (r1 veri tasiyor)")
    no_data_floor = {"rooms": [{"id": "r3", "polygon": ROOM_SQUARE}]}
    if floor_has_ceiling_data(no_data_floor):
        errors.append("veri yokken False bekleniyordu, True bulundu")
    return errors


def check_draw_ceiling_label_entity_counts() -> list[str]:
    """Malzeme YOKSA 1 TEXT (yalnizca kot); malzeme VARSA 2 TEXT (kot +
    malzeme, BUYUK harfe cevrilmis)."""
    errors: list[str] = []
    doc = ezdxf.new()
    ensure_ceiling_layer(doc)
    msp = doc.modelspace()

    from ceiling import RoomCeilingData
    only_height = RoomCeilingData("r1", 2500.0, None, (0.0, 0.0))
    draw_ceiling_label(msp, only_height, text_height=100.0)
    if len(msp) != 1:
        errors.append(f"malzeme yokken 1 TEXT bekleniyordu, {len(msp)} bulundu")
    texts = list(msp.query("TEXT"))
    if texts and texts[0].dxf.text != "+2.50":
        errors.append(f"kot metni '+2.50' bekleniyordu, '{texts[0].dxf.text}' bulundu")

    doc2 = ezdxf.new()
    ensure_ceiling_layer(doc2)
    msp2 = doc2.modelspace()
    with_finish = RoomCeilingData("r2", -200.0, "alcipan asma tavan", (0.0, 0.0))
    draw_ceiling_label(msp2, with_finish, text_height=100.0)
    if len(msp2) != 2:
        errors.append(f"malzeme varken 2 TEXT bekleniyordu, {len(msp2)} bulundu")
    texts2 = [t.dxf.text for t in msp2.query("TEXT")]
    if "-0.20" not in texts2:
        errors.append(f"kot metni '-0.20' beklenen listede yok: {texts2}")
    if "ALCIPAN ASMA TAVAN" not in texts2:
        errors.append(f"malzeme metni BUYUK HARFE cevrilmis olarak beklenen listede yok: {texts2}")
    return errors


def check_ceiling_sheet_draws_walls_plus_labels() -> list[str]:
    """CeilingSheet.draw, duvar aginin URETTIGI varlik sayisina (bagimsiz
    olcum: draw_wall_network dogrudan cagirilarak) + ceiling etiket
    varliklarini EKLER - iki ayri hesap AYRISMAMALI."""
    errors: list[str] = []

    baseline_doc = ezdxf.new()
    baseline_doc.layers.add("DUVARLAR")
    baseline_msp = baseline_doc.modelspace()
    network = WallNetwork.from_context(SIMPLE_FLOOR["walls"], "mm")
    draw_wall_network(baseline_msp, network, [])
    wall_entity_count = len(baseline_msp)

    doc = ezdxf.new()
    doc.layers.add("DUVARLAR")
    ensure_ceiling_layer(doc)
    msp = doc.modelspace()
    CeilingSheet.draw(msp, SIMPLE_FLOOR, units="mm", text_height=100.0)

    # r1 malzemeli (2 TEXT), r2 veri tasimiyor (0) -> +2 beklenir.
    expected = wall_entity_count + 2
    if len(msp) != expected:
        errors.append(f"{expected} varlik bekleniyordu (duvar={wall_entity_count}+etiket=2), {len(msp)} bulundu")
    return errors


def check_ensure_ceiling_layer_sets_rgb() -> list[str]:
    errors: list[str] = []
    doc = ezdxf.new()
    ensure_ceiling_layer(doc)
    if "TAVAN" not in doc.layers:
        return ["TAVAN katmani olusturulmadi"]
    layer = doc.layers.get("TAVAN")
    from ceiling import CEILING_RGB
    if tuple(layer.rgb) != CEILING_RGB:
        errors.append(f"layer.rgb {CEILING_RGB} bekleniyordu, {layer.rgb} bulundu")
    return errors


def main() -> int:
    groups = (
        ("resolve_room_ceilings elle hesaplanabilir (+ yanlis-pozitif)", check_resolve_room_ceilings_hand_computable()),
        ("floor_has_ceiling_data (+ yanlis-pozitif)", check_floor_has_ceiling_data()),
        ("draw_ceiling_label varlik sayilari + metin icerigi", check_draw_ceiling_label_entity_counts()),
        ("CeilingSheet.draw = duvar agi + etiketler", check_ceiling_sheet_draws_walls_plus_labels()),
        ("TAVAN katmani RGB'si kod-sahipli", check_ensure_ceiling_layer_sets_rgb()),
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
        print("\nTAVAN SELF-TEST BASARISIZ.")
        return 1
    print("\nTavan self-test BASARILI.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
