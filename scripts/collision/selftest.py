#!/usr/bin/env python3
"""Cakisma motorunun NEGATIF testleri (DEV-019).

**Neden ayri bir self-test:** Bu motorun isi hata BULMAKTIR. "Temiz dondu"
cikti tek basina hicbir sey kanitlamaz - motor hic calismiyor olsa da temiz
donerdi. Bu yuzden projenin bes semantik kuralinda oldugu gibi burada da
kasitli olarak BOZULMUS bir kat kurulur ve motorun tam olarak beklenen
bulgulari (ne bir eksik, ne bir fazla) uretmesi aranir.

**Neden bir `golden/` referansi DEGIL:** golden kosucusu once `validate.py`
calistirir; cakismali bir context validate'ten gecemez ve referans daha
uretim asamasina gelmeden basarisiz olurdu. Golden'in sorusu "cikti degisti
mi", bu testin sorusu "motor hatayi goruyor mu" - farkli sorular, farkli
kosucular.

Kullanim:
    python scripts/collision/selftest.py
Cikis kodu: 0 basarili, 1 basarisiz.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from collision import (  # noqa: E402
    KIND_CONTAINMENT,
    KIND_OVERLAP,
    Policy,
    check_context,
    rect_shape,
    TAG_FURNITURE,
)
from collision.geometry import (  # noqa: E402
    is_convex,
    min_extent,
    point_in_polygon,
    polygon_area,
    polygon_intersection_area,
)

TOLERANCE = 1e-6


def _floor() -> dict:
    """Kasitli olarak BOZULMUS tek kat.

    Yerlesim elle hesaplanabilir tutulmustur; beklenen degerler asagida
    yorumlarda gosterilmistir.

        oda r1 : x 0..6000, y 0..4000
        duvar w1: (0,0)-(6000,0), t=200  -> dikdortgen y -100..100
        kapi d1 : w1 uzerinde s=1000, genislik 900 -> sektor merkez (1000,0),
                  0..90 derece (duvar yonu 0, normal +90)
    """
    return {
        "id": "kat_test",
        "code": "T1",
        "rooms": [
            {"id": "r1", "name": "TEST", "no": "01", "area_m2": 24.0,
             "polygon": [[0, 0], [6000, 0], [6000, 4000], [0, 4000]]},
        ],
        "walls": [
            {"id": "w1", "start": [0, 0], "end": [6000, 0],
             "thickness": 200, "layer": "DUVAR"},
        ],
        "openings": [
            {"id": "d1", "type": "door", "wall_id": "w1",
             "position_from_start": 1000, "width": 900},
        ],
        "columns": [
            # c1: odanin icinde duran kolon -> kolon/oda IGNORE, bulgu YOK
            {"id": "c1", "position": [5500, 3500], "section": "S40x40"},
            # c2: duvarin icinde duran kolon -> kolon/duvar IGNORE, bulgu YOK
            {"id": "c2", "position": [3000, 0], "section": "S40x40"},
        ],
        "furniture": [
            # f1 x200..2300  y1500..2350   (koltuk_3lu 2100x850)
            {"id": "f1", "type": "koltuk_3lu", "position": [200, 1500]},
            # f2 x1500..3100 y1600..2450   (koltuk_2li 1600x850)
            #   -> f1 ile kesisim 800 x 750 = 600000 mm2, derinlik 750  [HATA]
            {"id": "f2", "type": "koltuk_2li", "position": [1500, 1600]},
            # f3 odanin TAMAMEN disinda                                  [HATA]
            {"id": "f3", "type": "sandalye", "position": [7000, 1000]},
            # f4 x3500..4600 y50..650  -> duvara 50 mm girer             [UYARI]
            {"id": "f4", "type": "sehpa", "position": [3500, 50]},
            # f5 x5000..5450 y97..547  -> duvara 3 mm girer = TEMAS, bulgu YOK
            {"id": "f5", "type": "sandalye", "position": [5000, 97]},
            # f6 x1200..1650 y200..650 -> d1 acilim sektorunun icinde     [HATA]
            {"id": "f6", "type": "sandalye", "position": [1200, 200]},
        ],
    }


def _context() -> dict:
    return {"meta": {"units": "mm"}, "floors": [_floor()]}


def check_geometry() -> list[str]:
    """Saf geometri: elle hesaplanabilir degerler."""
    errors: list[str] = []

    square = [[0, 0], [1000, 0], [1000, 1000], [0, 1000]]
    if abs(polygon_area(square) - 1_000_000.0) > TOLERANCE:
        errors.append(f"polygon_area yanlis: {polygon_area(square)}")

    shifted = [[500, 0], [1500, 0], [1500, 1000], [500, 1000]]
    area = polygon_intersection_area(square, shifted)
    if abs(area - 500_000.0) > TOLERANCE:
        errors.append(f"kesisim alani 500000 olmali, {area} cikti.")

    apart = [[2000, 0], [3000, 0], [3000, 1000], [2000, 1000]]
    if polygon_intersection_area(square, apart) != 0.0:
        errors.append("ayrik iki kare icin kesisim alani 0 olmali.")

    sliver = [[0, 0], [1000, 0], [1000, 3], [0, 3]]
    if abs(min_extent(sliver) - 3.0) > TOLERANCE:
        errors.append(f"min_extent 3 olmali, {min_extent(sliver)} cikti.")

    if not point_in_polygon((500, 500), square):
        errors.append("point_in_polygon: ic nokta disarida sayildi.")
    if point_in_polygon((1500, 500), square):
        errors.append("point_in_polygon: dis nokta iceride sayildi.")

    # Icbukey L: kirpma degil, nokta testi kullanildigi icin dogru olmali
    ell = [[0, 0], [2000, 0], [2000, 1000], [1000, 1000], [1000, 2000], [0, 2000]]
    if is_convex(ell):
        errors.append("is_convex: L seklindeki poligon disbukey sayildi.")
    if not point_in_polygon((500, 1500), ell):
        errors.append("point_in_polygon: L'nin ic kolundaki nokta disarida sayildi.")
    if point_in_polygon((1500, 1500), ell):
        errors.append("point_in_polygon: L'nin bos kosesindeki nokta iceride sayildi.")

    # 45 derece donmus dikdortgenin ayak izi gercekten donmus mu
    rotated = rect_shape(TAG_FURNITURE, "x", (0, 0), 1000, 1000, 45.0)
    x0, y0, x1, y1 = rotated.bbox
    expected = 1000 * (2 ** 0.5)
    if abs((x1 - x0) - expected) > 1e-6 or abs((y1 - y0) - expected) > 1e-6:
        errors.append(f"45 derece donmus kare sinir kutusu {expected:.1f} olmali, "
                      f"{(x1 - x0):.1f}x{(y1 - y0):.1f} cikti.")

    return errors


def check_engine() -> list[str]:
    """Uctan uca: saglayicilar + motor + politika matrisi."""
    errors: list[str] = []
    report = check_context(_context())

    # Cift sirasi SAGLAYICI SIRASINA baglidir (rooms, walls, columns,
    # openings, furniture); test bu siraya bagimli olmamali diye kimlikler
    # sirasiz kumede aranir.
    found = {
        (c.kind, frozenset({c.a.id, c.b.id if c.b else ""})): c
        for c in report.clashes
    }

    expected_errors = {
        (KIND_OVERLAP, frozenset({"f1", "f2"})): "iki tefris ust uste",
        (KIND_CONTAINMENT, frozenset({"f3", ""})): "tefris odanin disinda",
        (KIND_OVERLAP, frozenset({"f6", "d1"})): "tefris kapi acilim sektorunde",
    }
    expected_warnings = {
        (KIND_OVERLAP, frozenset({"f4", "w1"})): "tefris duvara 50 mm giriyor",
    }

    for key, why in expected_errors.items():
        clash = found.get(key)
        if clash is None:
            errors.append(f"YAKALANMADI ({why}): {key}")
        elif clash.policy is not Policy.FORBID:
            errors.append(f"{key} HATA olmaliydi, {clash.policy.value} cikti.")

    for key, why in expected_warnings.items():
        clash = found.get(key)
        if clash is None:
            errors.append(f"YAKALANMADI ({why}): {key}")
        elif clash.policy is not Policy.WARN:
            errors.append(f"{key} UYARI olmaliydi, {clash.policy.value} cikti.")

    # Bulunmamasi gerekenler: yanlis-pozitif kontrolu
    silent = {
        ("f5", "w1"): "3 mm girisim TEMAS'tir, bildirilmemeliydi",
        ("c2", "w1"): "kolonun duvar icinde olmasi TASARIMDIR",
        ("c1", "r1"): "kolonun oda icinde olmasi normaldir",
    }
    for (a_id, b_id), why in silent.items():
        for clash in report.clashes:
            ids = {clash.a.id, clash.b.id if clash.b else ""}
            if ids == {a_id, b_id}:
                errors.append(f"YANLIS-POZITIF ({why}): {clash.message()}")

    # f1-f2 kesisiminin OLCUSU de dogru olmali (elle: 800 x 750)
    overlap = found.get((KIND_OVERLAP, frozenset({"f1", "f2"})))
    if overlap is not None:
        if abs(overlap.area - 600_000.0) > 1.0:
            errors.append(f"f1/f2 kesisim alani 600000 mm2 olmali, "
                          f"{overlap.area:.0f} cikti.")
        if abs(overlap.depth - 750.0) > 1.0:
            errors.append(f"f1/f2 girisim derinligi 750 mm olmali, "
                          f"{overlap.depth:.0f} cikti.")

    if len(report.errors) != len(expected_errors):
        errors.append(f"HATA sayisi {len(expected_errors)} olmali, "
                      f"{len(report.errors)} cikti: {report.error_lines()}")
    if len(report.warnings) != len(expected_warnings):
        errors.append(f"UYARI sayisi {len(expected_warnings)} olmali, "
                      f"{len(report.warnings)} cikti: {report.warning_lines()}")
    if report.ok:
        errors.append("Bozulmus kat icin report.ok True dondu.")

    return errors


def check_door_pair() -> list[str]:
    """Iki kapi birbirine aciliyorsa HATA (rev-13, DEV-016).

    rev-12'de bu cift MUAFTI cunku acilim yonu schema'da yoktu ve yay sabit
    bir varsayilan tarafa ciziliyordu; kontrol yanlis-pozitif uretirdi. Yon
    artik veriden geldigi icin kontrol anlamli.
    """
    context = {
        "meta": {"units": "mm"},
        "floors": [{
            "id": "k", "code": "T2", "rooms": [], "columns": [], "furniture": [],
            "walls": [{"id": "w1", "start": [0, 0], "end": [6000, 0],
                       "thickness": 200, "layer": "DUVAR"}],
            "openings": [
                # merkezler 600 mm arayla -> 900'luk iki yay ust uste biner
                {"id": "d1", "type": "door", "wall_id": "w1",
                 "position_from_start": 1000, "width": 900},
                {"id": "d2", "type": "door", "wall_id": "w1",
                 "position_from_start": 1600, "width": 900},
            ],
        }],
    }
    report = check_context(context)
    pair = {frozenset({c.a.id, c.b.id if c.b else ""}) for c in report.errors}
    errors: list[str] = []
    if frozenset({"d1", "d2"}) not in pair:
        errors.append(f"YAKALANMADI: birbirine acilan iki kapi bildirilmedi "
                      f"({report.error_lines()}).")

    # Ayni iki kapi SURME olsaydi sektor uretilmez, bulgu da olmazdi
    for opening in context["floors"][0]["openings"]:
        opening["variant"] = "sliding"
    if check_context(context).clashes:
        errors.append("YANLIS-POZITIF: surme kapilar icin acilim cakismasi "
                      "bildirildi (surme kapi onunde bos alan gerektirmez).")
    return errors


def check_clean() -> list[str]:
    """Bozuk yerlesimler cikarilinca motor SESSIZ kalmali (yanlis-pozitif yok)."""
    context = _context()
    floor = context["floors"][0]
    floor["furniture"] = [f for f in floor["furniture"]
                          if f["id"] in ("f1", "f5")]
    report = check_context(context)
    if not report.ok or report.clashes:
        return [f"Temiz kat icin bulgu uretildi: "
                f"{report.error_lines() + report.warning_lines()}"]
    return []


def main() -> int:
    groups = (
        ("geometri", check_geometry()),
        ("motor (negatif test)", check_engine()),
        ("kapi <-> kapi acilimi", check_door_pair()),
        ("temiz kat (yanlis-pozitif testi)", check_clean()),
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
        print("\nCAKISMA SELF-TEST BASARISIZ.")
        return 1
    print("\nCakisma self-test BASARILI.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
