#!/usr/bin/env python3
"""Kesit (building section) testleri (DEV-021).

Kullanim:
    python scripts/sections/selftest.py
Cikis kodu: 0 basarili, 1 basarisiz.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import ezdxf  # noqa: E402

from sections import (  # noqa: E402
    SectionCutLine,
    SectionSheet,
    crossing_walls,
    default_label,
    default_position,
    draw_cut_marker_on_floor,
    resolve_sections,
)

TOLERANCE = 1e-6


class _NullAxisGrid:
    """`draw_on_elevation` cagrisini yutan test dublesi - bu self-test axis
    modulunu degil, SectionSheet'in KENDI mantigini sinar."""

    def draw_on_elevation(self, msp, dx, axis_source, y_bottom, y_top) -> None:
        pass


def check_default_position_is_one_third_not_center() -> list[str]:
    """Kullanici karari: operator konum BILDIRMEZSE kesit yapinin TAM
    ORTASINDAN degil, ilgili kenarin 1/3 noktasindan alinir. Elle
    hesaplanabilir: floor_depth=9000 -> vertical icin 3000; floor_width=6000
    -> horizontal icin 2000."""
    errors: list[str] = []
    pos_v = default_position("vertical", floor_width=12000.0, floor_depth=9000.0)
    if abs(pos_v - 3000.0) > TOLERANCE:
        errors.append(f"axis_source=vertical: 3000 bekleniyordu, {pos_v} bulundu.")
    pos_h = default_position("horizontal", floor_width=6000.0, floor_depth=9000.0)
    if abs(pos_h - 2000.0) > TOLERANCE:
        errors.append(f"axis_source=horizontal: 2000 bekleniyordu, {pos_h} bulundu.")
    center_v = 9000.0 / 2.0
    if abs(pos_v - center_v) < TOLERANCE:
        errors.append("varsayilan konum yanlislikla TAM MERKEZE denk geldi (kullanici bunu YASAKLADI).")
    return errors


def check_resolve_sections_defaults_to_one_per_axis() -> list[str]:
    """context['sections'] HIC verilmezse (anahtar yok), sistem X ve Y
    ekseninden BIRER varsayilan kesit uretmelidir (kullanici karari);
    bos dizi ([]) verilirse HICBIR kesit uretilmemelidir."""
    errors: list[str] = []
    context = {
        "meta": {"floor_width": 12000.0, "floor_depth": 9000.0},
        "elevations": [{"id": "on_cephe"}],
    }
    defaults = resolve_sections(context)
    if len(defaults) != 2:
        return [f"anahtar YOK durumunda 2 varsayilan kesit bekleniyordu, {len(defaults)} bulundu."]
    if {c.axis_source for c in defaults} != {"vertical", "horizontal"}:
        errors.append("varsayilan kesitler X VE Y ekseninden birer tane olmali.")
    if [c.label for c in defaults] != ["A-A", "B-B"]:
        errors.append(f"varsayilan etiketler ['A-A','B-B'] bekleniyordu, {[c.label for c in defaults]} bulundu.")
    if any(c.levels_from != "on_cephe" for c in defaults):
        errors.append("varsayilan levels_from ilk elevation'a (on_cephe) dusmedi.")

    context_empty = dict(context, sections=[])
    disabled = resolve_sections(context_empty)
    if disabled != []:
        errors.append(f"bos dizi ([]) verildiginde HICBIR kesit BEKLENMIYORDU, {disabled} bulundu.")
    return errors


def check_default_label_sequence() -> list[str]:
    if [default_label(i) for i in range(3)] != ["A-A", "B-B", "C-C"]:
        return ["default_label(0..2) 'A-A','B-B','C-C' vermeli."]
    return []


def check_crossing_walls_hand_computable() -> list[str]:
    """Elle hesaplanabilir bir kat: 2 dis duvar (x=0, x=9000) + Y=0..9000 TAM
    kapsayan bir bolme (x=4500) + Y=0..4000 kapsayan (cut=4500'e ULASMAYAN)
    bir bolme (x=2000). cut_position=4500 iken SADECE x=0,4500,9000 kesilir;
    x=2000 (0..4000) 4500'e ULASMADIGI icin ATLANMALIDIR (negatif test)."""
    errors: list[str] = []
    walls = [
        {"id": "disL", "start": [0, 0], "end": [0, 9000], "thickness": 200.0},
        {"id": "disR", "start": [9000, 0], "end": [9000, 9000], "thickness": 200.0},
        {"id": "tamBolme", "start": [4500, 0], "end": [4500, 9000], "thickness": 150.0},
        {"id": "kisaBolme", "start": [2000, 0], "end": [2000, 4000], "thickness": 150.0},
        {"id": "yatayDuvar", "start": [0, 4500], "end": [9000, 4500], "thickness": 200.0},
    ]
    crossings = crossing_walls(walls, "vertical", 4500.0)
    ids = [c["wall_id"] for c in crossings]
    if ids != ["disL", "tamBolme", "disR"]:
        errors.append(f"['disL','tamBolme','disR'] (x'e gore sirali) bekleniyordu, {ids} bulundu.")
    thicknesses = {c["wall_id"]: c["thickness"] for c in crossings}
    if thicknesses.get("tamBolme") != 150.0:
        errors.append(f"tamBolme kalinligi 150 bekleniyordu, {thicknesses.get('tamBolme')} bulundu.")
    # kisaBolme (0..4000) 4500'e ULASMIYOR -> kesinlikle listede OLMAMALI.
    if "kisaBolme" in ids:
        errors.append("kisaBolme (Y=0..4000) cut=4500'u KAPSAMIYOR ama YANLISLIKLA kesildi.")
    # yatayDuvar cut hattina PARALEL (constant Y) - dusey-duvar testinden gecemez, ATLANMALI.
    if "yatayDuvar" in ids:
        errors.append("yatayDuvar (cut hattina PARALEL) yanlislikla kesilen duvar sayildi.")
    return errors


def check_crossing_walls_horizontal_axis_symmetric() -> list[str]:
    """axis_source='horizontal' icin SIMETRIK davranis: sabit X'te bir kesit,
    YATAY duvarlari (start.y==end.y) arar, DUSEY duvarlari atlar."""
    errors: list[str] = []
    walls = [
        {"id": "yatay1", "start": [0, 0], "end": [9000, 0], "thickness": 200.0},
        {"id": "yatay2", "start": [0, 9000], "end": [9000, 9000], "thickness": 200.0},
        {"id": "dusey", "start": [3000, 0], "end": [3000, 9000], "thickness": 150.0},
    ]
    crossings = crossing_walls(walls, "horizontal", 3000.0)
    ids = [c["wall_id"] for c in crossings]
    if ids != ["yatay1", "yatay2"]:
        errors.append(f"['yatay1','yatay2'] bekleniyordu, {ids} bulundu.")
    return errors


ELEVATION_LOOKUP = {
    "on_cephe": {
        "id": "on_cephe", "label": "ON", "width": 9000.0,
        "levels": [{"label": "ZEMIN", "height": 3000.0}, {"label": "1. KAT", "height": 3000.0}],
    }
}

FLOORS = [
    {"id": "f0", "walls": [
        {"id": "w0", "start": [0, 0], "end": [0, 9000], "thickness": 200.0},
        {"id": "w1", "start": [9000, 0], "end": [9000, 9000], "thickness": 200.0},
    ]},
    {"id": "f1", "walls": [
        {"id": "w0", "start": [0, 0], "end": [0, 9000], "thickness": 200.0},
        {"id": "w1", "start": [9000, 0], "end": [9000, 9000], "thickness": 200.0},
    ]},
]

CUT = SectionCutLine(id="k1", label="A-A", axis_source="vertical", position=3000.0,
                     look_direction="positive", levels_from="on_cephe")


def check_section_sheet_entity_count() -> list[str]:
    """Elle hesaplanabilir cizim sayisi: 2 kat * (1 sinir cizgisi + 2 dis
    duvar HATCH'i + 1 etiket) + 1 tepe cizgisi + 1 zemin cizgisi + 1 zemin
    etiketi = 2*4 + 3 = 11."""
    errors: list[str] = []
    doc = ezdxf.new()
    msp = doc.modelspace()
    SectionSheet.draw(msp, CUT, FLOORS, ELEVATION_LOOKUP, dx=0.0, width=9000.0,
                      label_text_height=120.0, axis_grid=_NullAxisGrid())
    if len(msp) != 11:
        errors.append(f"11 varlik bekleniyordu, {len(msp)} bulundu.")
    hatches = list(msp.query("HATCH"))
    if len(hatches) != 4:
        errors.append(f"4 HATCH (2 kat * 2 dis duvar) bekleniyordu, {len(hatches)} bulundu.")
    # rev-18: `hatch.set_pattern_fill("SOLID")` GERCEK bir solid fill
    # DEGILDI - "SOLID" adiyla bir PATTERN aranip cok yogun (spacing~0.125)
    # bir cizgi deseni uygulaniyordu (AutoCAD'in actigi acilan proje icin
    # "Large, Dense Hatch Patterns" uyarisinin KOKENI). `set_solid_fill()`
    # dogru API'dir; `dxf.solid_fill` 1 OLMALIDIR.
    if any(h.dxf.solid_fill != 1 for h in hatches):
        errors.append("En az bir kesit HATCH'i GERCEK solid_fill DEGIL (yogun cizgi deseni riski).")
    return errors


def check_length_mismatch_raises() -> list[str]:
    """floors[] uzunlugu, hedef elevation'in seviye sayisiyla UYUSMUYORSA
    (kat<->seviye eslesmesi belirsizlesir) HATA firlatilmalidir - sessizce
    yanlis hizalanmis bir kesit CIZILMEMELIDIR."""
    doc = ezdxf.new()
    msp = doc.modelspace()
    try:
        SectionSheet.draw(msp, CUT, FLOORS[:1], ELEVATION_LOOKUP, dx=0.0, width=9000.0,
                          label_text_height=120.0, axis_grid=_NullAxisGrid())
    except ValueError:
        return []
    return ["floors[] (1) ile seviye sayisi (2) UYUSMAZKEN ValueError BEKLENIYORDU, firlatilmadi."]


def check_cut_marker_draws_expected_entities() -> list[str]:
    """Plandaki kesit isareti: 1 kesit hatti + 2 ucgen + 2 harf etiketi = 5."""
    errors: list[str] = []
    doc = ezdxf.new()
    for name in ("DUVARLAR", "METIN", "CERCEVE"):
        doc.layers.add(name)
    msp = doc.modelspace()
    draw_cut_marker_on_floor(msp, CUT, dx=0.0, floor_width=9000.0, floor_depth=9000.0,
                             scale="1:50")
    if len(msp) != 5:
        errors.append(f"5 varlik (1 cizgi + 2 ucgen + 2 metin) bekleniyordu, {len(msp)} bulundu.")
    texts = [e.dxf.text for e in msp.query("TEXT")]
    if texts != ["A", "A"]:
        errors.append(f"her iki ucta 'A' harfi bekleniyordu, {texts} bulundu.")
    return errors


def main() -> int:
    groups = (
        ("varsayilan konum 1/3 (asla tam merkez degil)", check_default_position_is_one_third_not_center()),
        ("resolve_sections varsayilani (X+Y, bos dizi = kapali)", check_resolve_sections_defaults_to_one_per_axis()),
        ("varsayilan etiket sirasi (A-A,B-B,C-C)", check_default_label_sequence()),
        ("crossing_walls elle hesaplanabilir (+ negatif test)", check_crossing_walls_hand_computable()),
        ("crossing_walls horizontal simetrisi", check_crossing_walls_horizontal_axis_symmetric()),
        ("SectionSheet.draw varlik sayisi", check_section_sheet_entity_count()),
        ("kat/seviye uzunluk uyumsuzlugu -> ValueError", check_length_mismatch_raises()),
        ("plan kesit isareti varlik sayisi + harf", check_cut_marker_draws_expected_entities()),
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
        print("\nKESIT SELF-TEST BASARISIZ.")
        return 1
    print("\nKesit self-test BASARILI.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
