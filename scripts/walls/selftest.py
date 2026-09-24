#!/usr/bin/env python3
"""Rail cizim standardi testleri (DEV-014).

Kullanim:
    python scripts/walls/selftest.py
Cikis kodu: 0 basarili, 1 basarisiz.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import ezdxf  # noqa: E402

from walls import (  # noqa: E402
    GLASS_LINETYPE,
    CatalogRailStandard,
    Wall,
    WallCatalog,
    WallNetwork,
    draw_wall_network,
    wall_fill_spans,
)

TOLERANCE = 1e-6


def _wall(kind: str | None = None, thickness: float = 200.0) -> Wall:
    return Wall.from_context(
        {"id": "w1", "start": [0.0, 0.0], "end": [9000.0, 0.0],
         "thickness": thickness, "layer": "DUVARLAR", **({"kind": kind} if kind else {})},
        WallCatalog(),
    )


def _door(wall_id: str = "w1", position: float = 4500.0, width: float = 900.0) -> dict:
    return {"id": "k1", "type": "door", "wall_id": wall_id,
            "position_from_start": position, "width": width}


def check_fill_spans_hand_computable() -> list[str]:
    """9000 uzunlugunda bir duvarda, merkezi 4500'de 900 genislikte bir kapi
    -> bosluk [4050,4950]; dolgu araliklari ELLE hesaplanabilir: [0,4050] ve
    [4950,9000]."""
    errors: list[str] = []
    spans = wall_fill_spans(_wall(), [_door()])
    expected = [(0.0, 4050.0), (4950.0, 9000.0)]
    if len(spans) != len(expected):
        return [f"{len(expected)} aralik bekleniyordu, {len(spans)} bulundu: {spans}."]
    for (a, b), (ea, eb) in zip(spans, expected):
        if abs(a - ea) > TOLERANCE or abs(b - eb) > TOLERANCE:
            errors.append(f"Aralik farkli: beklenen ({ea},{eb}), bulunan ({a},{b}).")
    return errors


def check_no_opening_is_single_span() -> list[str]:
    """Aciklik yoksa dolgu TEK bir [0, length] araligidir (yanlis-pozitif:
    bos gap listesi 0 aralik degil, TAM araligin kendisini vermeli)."""
    spans = wall_fill_spans(_wall(), [])
    if spans != [(0.0, 9000.0)]:
        return [f"Tek aralik [0,9000] bekleniyordu, {spans} bulundu."]
    return []


def check_default_no_kind_is_plain() -> list[str]:
    """`kind` bildirilmemis bir duvar: sadece duz LINE, HATCH/ozel linetype
    YOK - mevcut projelerin davranisi DEGISMEMELIDIR."""
    errors: list[str] = []
    wall = _wall(kind=None)
    network = WallNetwork([wall], "mm")
    doc = ezdxf.new()
    msp = doc.modelspace()
    draw_wall_network(msp, network, [])

    hatches = list(msp.query("HATCH"))
    lines = list(msp.query("LINE"))
    if hatches:
        errors.append(f"HATCH olmamali, {len(hatches)} bulundu.")
    if len(lines) != 2:
        errors.append(f"2 duz LINE bekleniyordu, {len(lines)} bulundu.")
    for line in lines:
        if line.dxf.linetype != "BYLAYER":
            errors.append(f"linetype BYLAYER olmali, {line.dxf.linetype!r} bulundu.")
    return errors


def check_unknown_catalog_kind_falls_back() -> list[str]:
    """Katalogda TANIMLI ama ozel-islenmeyen bir kind (`bolme`) da
    DefaultRailStandard'a duser - sadece `tugla_bolme`/`cam_duvar` ozeldir."""
    wall = _wall(kind="bolme")
    network = WallNetwork([wall], "mm")
    doc = ezdxf.new()
    msp = doc.modelspace()
    draw_wall_network(msp, network, [])
    if msp.query("HATCH"):
        return ["'bolme' kind'i icin HATCH olmamali."]
    lines = list(msp.query("LINE"))
    if any(l.dxf.linetype != "BYLAYER" for l in lines):
        return ["'bolme' kind'i icin tum rail'ler BYLAYER olmali."]
    return []


def _rail_lines(msp):
    """DUVARLAR katmanindaki YATAY (sabit-y) cizgiler - rail segmentleri.
    Ayni katmandaki DUSEY soye/jamb cizgilerini (ayri bir rutin ciziyor,
    rail standardindan BAGIMSIZ) elemek icin gerekli."""
    return [line for line in msp.query('LINE[layer=="DUVARLAR"]')
            if abs(line.dxf.start[1] - line.dxf.end[1]) < 1e-6]


def check_brick_hatch_respects_gap() -> list[str]:
    """`tugla_bolme`: HATCH sayisi dolgu arligi sayisiyla (2) esit olmali -
    kapi acikligi taramaya girmemeli. Rail'ler HALA duz LINE'dir (hatch
    SADECE ic dolgu, kontur cizgisini degistirmez)."""
    errors: list[str] = []
    wall = _wall(kind="tugla_bolme")
    network = WallNetwork([wall], "mm")
    doc = ezdxf.new()
    msp = doc.modelspace()
    draw_wall_network(msp, network, [_door()])

    hatches = list(msp.query("HATCH"))
    if len(hatches) != 2:
        errors.append(f"2 HATCH bekleniyordu (kapi araligi haric), {len(hatches)} bulundu.")
    for hatch in hatches:
        if hatch.dxf.pattern_name != "ANSI31":
            errors.append(f"Desen ANSI31 olmali, {hatch.dxf.pattern_name!r} bulundu.")
    rails = _rail_lines(msp)
    if len(rails) != 4:
        errors.append(f"4 rail parcasi bekleniyordu (2 taraf x 2 parca), {len(rails)} bulundu.")
    return errors


def check_glass_linetype_respects_gap() -> list[str]:
    """`cam_duvar`: rail'ler `CAM` linetype'iyla cizilir ve kapi acikligina
    gore bolunur (4 parca: 2 taraf x 2 aralik). Soye/jamb cizgileri (ayri
    bir rutin) bundan MUAFTIR - onlar her zaman BYLAYER kalir."""
    errors: list[str] = []
    wall = _wall(kind="cam_duvar", thickness=100.0)
    network = WallNetwork([wall], "mm")
    doc = ezdxf.new()
    msp = doc.modelspace()
    draw_wall_network(msp, network, [_door()])

    rails = _rail_lines(msp)
    if len(rails) != 4:
        errors.append(f"4 rail parcasi bekleniyordu, {len(rails)} bulundu.")
    if any(line.dxf.linetype != GLASS_LINETYPE for line in rails):
        errors.append("Tum rail parcalari CAM linetype'inda olmali.")
    if msp.query("HATCH"):
        errors.append("Cam duvarda HATCH olmamali.")
    return errors


def check_catalog_standard_reused_across_walls() -> list[str]:
    """Bir `CatalogRailStandard` orneği birden fazla duvar icin yeniden
    kullanilabilir (durum tasimadigini dogrular - yanlis-pozitif testi)."""
    errors: list[str] = []
    brick = _wall(kind="tugla_bolme")
    glass = Wall.from_context(
        {"id": "w2", "start": [0.0, 2000.0], "end": [9000.0, 2000.0],
         "thickness": 100.0, "layer": "DUVARLAR", "kind": "cam_duvar"},
        WallCatalog())
    network = WallNetwork([brick, glass], "mm")
    doc = ezdxf.new()
    msp = doc.modelspace()
    standard = CatalogRailStandard()
    for wall in network.walls:
        standard.draw_rails(msp, wall, network, [])
    if len(list(msp.query("HATCH"))) != 1:
        errors.append("Tugla duvar icin 1 HATCH bekleniyordu.")
    if len([l for l in msp.query("LINE") if l.dxf.linetype == GLASS_LINETYPE]) != 2:
        errors.append("Cam duvar icin 2 CAM rail bekleniyordu.")
    return errors


def main() -> int:
    groups = (
        ("dolgu araligi (elle hesaplanabilir)", check_fill_spans_hand_computable()),
        ("aciklik yoksa tek aralik (yanlis-pozitif)", check_no_opening_is_single_span()),
        ("kind yok -> duz LINE (regresyon)", check_default_no_kind_is_plain()),
        ("bilinmeyen ozel-isleme -> fallback", check_unknown_catalog_kind_falls_back()),
        ("tugla_bolme hatch, kapi araligi haric", check_brick_hatch_respects_gap()),
        ("cam_duvar linetype, kapi araligi haric", check_glass_linetype_respects_gap()),
        ("standart birden fazla duvarda yeniden kullanilir", check_catalog_standard_reused_across_walls()),
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
        print("\nDUVAR SELF-TEST BASARISIZ.")
        return 1
    print("\nDuvar self-test BASARILI.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
