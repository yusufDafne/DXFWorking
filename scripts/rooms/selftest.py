#!/usr/bin/env python3
"""Mahal etiketi BLOK+ATTRIB testleri (DEV-018).

Kullanim:
    python scripts/rooms/selftest.py
Cikis kodu: 0 basarili, 1 basarisiz.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import ezdxf  # noqa: E402

from rooms import (  # noqa: E402
    ROOM_LABEL_ATTDEF_TAGS,
    ROOM_LABEL_BLOCK_NAME,
    ROOM_LABEL_LINE_GAP,
    RoomLabeler,
)

TOLERANCE = 1e-6


def _room(**overrides) -> dict:
    data = {
        "id": "r1", "name": "salon", "no": "04", "area_m2": 30.0,
        "polygon": [[0.0, 0.0], [6000.0, 0.0], [6000.0, 5000.0], [0.0, 5000.0]],
        "layer": "METIN",
    }
    data.update(overrides)
    return data


def check_block_matches_raw_formula() -> list[str]:
    """Blok+ATTRIB konumu, eski duz-TEXT formuluyle (elle hesaplanabilir)
    BIREBIR ortusmelidir. INSERT scale = height/NOMINAL_HEIGHT dogrusal
    oldugu icin bu bir onceki surumden davranis degisikligi DEGILDIR."""
    errors: list[str] = []
    room = _room()
    doc = ezdxf.new()
    msp = doc.modelspace()
    RoomLabeler.draw(msp, room, max_text_height=500.0, units="mm",
                      floor_code="ZK")

    inserts = list(msp.query("INSERT"))
    if len(inserts) != 1:
        errors.append(f"1 INSERT bekleniyordu, {len(inserts)} bulundu.")
        return errors
    insert = inserts[0]
    attribs = list(insert.attribs)
    if len(attribs) != 3:
        errors.append(f"3 ATTRIB bekleniyordu, {len(attribs)} bulundu.")
        return errors
    if insert.dxf.name != ROOM_LABEL_BLOCK_NAME:
        errors.append(f"Yanlis blok: {insert.dxf.name!r}.")

    lines = [(t, f) for t, f in RoomLabeler.lines(room, "ZK") if t]
    height = RoomLabeler._fit(lines, 6000.0 - 400.0, 5000.0 - 400.0, 500.0, None)
    center_x, center_y = 3000.0, 2500.0
    cursor = center_y + RoomLabeler._block_height(lines, height) / 2.0
    expected: dict[str, tuple[float, float, float]] = {}
    for text, factor in lines:
        line_height = factor * height
        expected[text] = (center_x, cursor - line_height / 2.0, line_height)
        cursor -= line_height + ROOM_LABEL_LINE_GAP * height

    by_text = {a.dxf.text: a for a in attribs}
    if set(by_text) != set(expected):
        errors.append(f"ATTRIB metinleri uyusmuyor: {sorted(by_text)} != {sorted(expected)}.")
        return errors
    for text, (ex, ey, eh) in expected.items():
        attrib = by_text[text]
        px, py = attrib.get_placement()[1][0], attrib.get_placement()[1][1]
        if abs(px - ex) > TOLERANCE or abs(py - ey) > TOLERANCE:
            errors.append(
                f"'{text}' konumu farkli: beklenen ({ex:.3f},{ey:.3f}), "
                f"bulunan ({px:.3f},{py:.3f})."
            )
        if abs(attrib.dxf.height - eh) > TOLERANCE:
            errors.append(
                f"'{text}' yuksekligi farkli: beklenen {eh:.3f}, "
                f"bulunan {attrib.dxf.height:.3f}."
            )
    return errors


def check_missing_code_falls_back_to_raw_text() -> list[str]:
    """Kat kodu VE mahal no'nun ikisi de eksikse (2 satir), blok 3 ATTDEF
    icin sabit yerlesimle tanimlandigindan RAW-TEXT'e dusulmelidir - aksi
    halde ortadaki bos satir gorsel bosluk birakirdi (negatif test: block
    path yanlislikla eksik satirla da tetiklenirse burada yakalanir)."""
    errors: list[str] = []
    room = _room(no="")
    doc = ezdxf.new()
    msp = doc.modelspace()
    RoomLabeler.draw(msp, room, max_text_height=500.0, units="mm", floor_code="")

    inserts = list(msp.query("INSERT"))
    texts = list(msp.query("TEXT"))
    if inserts:
        errors.append(f"Blok kullanilmamaliydi, {len(inserts)} INSERT bulundu.")
    if len(texts) != 2:
        errors.append(f"2 duz TEXT bekleniyordu, {len(texts)} bulundu.")
    return errors


def check_block_definition_reused() -> list[str]:
    """Ayni belgede ikinci oda cizildiginde blok TANIMI yeniden olusturulmaz
    (yanlis-pozitif testi: iki INSERT, ama TEK blok tanimi)."""
    errors: list[str] = []
    doc = ezdxf.new()
    msp = doc.modelspace()
    RoomLabeler.draw(msp, _room(id="r1", no="01"), 500.0, "mm", floor_code="ZK")
    RoomLabeler.draw(msp, _room(id="r2", no="02", polygon=[
        [7000.0, 0.0], [13000.0, 0.0], [13000.0, 5000.0], [7000.0, 5000.0]]),
        500.0, "mm", floor_code="ZK")

    block_defs = [b for b in doc.blocks if b.name == ROOM_LABEL_BLOCK_NAME]
    if len(block_defs) != 1:
        errors.append(f"Tek blok tanimi bekleniyordu, {len(block_defs)} bulundu.")
    inserts = list(msp.query("INSERT"))
    if len(inserts) != 2:
        errors.append(f"2 INSERT bekleniyordu, {len(inserts)} bulundu.")
    return errors


def check_attdef_tags_match_lines() -> list[str]:
    """Blok tanimindaki ATTDEF etiketleri, RoomLabeler.lines()'in ADI/KOD/ALAN
    sirasiyla birebir eslesmelidir - siralama karisirsa yanlis satir yanlis
    ATTDEF'e yazilir (sessiz veri hatasi)."""
    errors: list[str] = []
    doc = ezdxf.new()
    msp = doc.modelspace()
    RoomLabeler.draw(msp, _room(), 500.0, "mm", floor_code="ZK")
    block = doc.blocks.get(ROOM_LABEL_BLOCK_NAME)
    tags = [attdef.dxf.tag for attdef in block.attdefs()]
    if tags != list(ROOM_LABEL_ATTDEF_TAGS):
        errors.append(f"ATTDEF sirasi farkli: {tags} != {list(ROOM_LABEL_ATTDEF_TAGS)}.")
    return errors


def main() -> int:
    groups = (
        ("blok konumu eski duz-TEXT formuluyle ortusuyor", check_block_matches_raw_formula()),
        ("eksik kod -> raw-text fallback (kenar durum)", check_missing_code_falls_back_to_raw_text()),
        ("blok tanimi tek kez olusuyor (yanlis-pozitif)", check_block_definition_reused()),
        ("ATTDEF sirasi", check_attdef_tags_match_lines()),
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
        print("\nODA SELF-TEST BASARISIZ.")
        return 1
    print("\nOda self-test BASARILI.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
