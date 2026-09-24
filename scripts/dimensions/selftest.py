#!/usr/bin/env python3
"""Olcu turetme ve kademelendirme testleri (DEV-017).

`collision/selftest.py` ile ayni disiplin: beklenen degerler ELLE
hesaplanabilir tutulur ve kurallarin gercekten patladigi NEGATIF testlerle
dogrulanir. "Zincir cizildi" ciktisi tek basina hicbir sey kanitlamaz -
ordinatlar yanlis yerden turetilse de zincir cizilirdi.

Kullanim:
    python scripts/dimensions/selftest.py
Cikis kodu: 0 basarili, 1 basarisiz.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import ezdxf  # noqa: E402

from dimensions import (  # noqa: E402
    AXIS_X,
    AXIS_Y,
    ChainLayout,
    ChainStack,
    DimensionChain,
    DimensionSettings,
    DimensionStyle,
    FloorDimensionPlanner,
    FloorOrdinates,
    LinearDim,
    format_dimension_cm,
    merge_ordinates,
)

TOLERANCE = 1e-6


def _floor() -> dict:
    """Elle hesaplanabilir tek kat.

        oda      : 6000 x 4000 (aks-aks)
        dis duvar: t=200 -> yuzler +-100
        orta duvar (dusey, x=3000, t=100) -> yuzler 2950 / 3050
        kapi     : guney duvarda s=1000, genislik 900 -> X 1000 ve 1900
    """
    return {
        "id": "kat_olcu", "code": "T1",
        "rooms": [],
        "walls": [
            {"id": "guney", "start": [0, 0], "end": [6000, 0],
             "thickness": 200, "layer": "DUVARLAR"},
            {"id": "kuzey", "start": [0, 4000], "end": [6000, 4000],
             "thickness": 200, "layer": "DUVARLAR"},
            {"id": "bati", "start": [0, 0], "end": [0, 4000],
             "thickness": 200, "layer": "DUVARLAR"},
            {"id": "dogu", "start": [6000, 0], "end": [6000, 4000],
             "thickness": 200, "layer": "DUVARLAR"},
            {"id": "orta", "start": [3000, 0], "end": [3000, 4000],
             "thickness": 100, "layer": "DUVARLAR"},
        ],
        "openings": [
            {"id": "k1", "type": "door", "wall_id": "guney",
             "position_from_start": 1000, "width": 900},
        ],
    }


def _equal(actual, expected) -> bool:
    return (len(actual) == len(expected)
            and all(abs(a - b) <= TOLERANCE for a, b in zip(actual, expected)))


def check_ordinates() -> list[str]:
    errors: list[str] = []
    ordinates = FloorOrdinates(_floor())

    cases = {
        # dis yuzden dis yuze: -100 .. 6100 (merkez cizgisi 0..6000 DEGIL)
        ("total", AXIS_X): [-100.0, 6100.0],
        ("total", AXIS_Y): [-100.0, 4100.0],
        # dik duvarlarin IKI yuzu -> net mahal + kalinlik
        ("room", AXIS_X): [-100.0, 100.0, 2950.0, 3050.0, 5900.0, 6100.0],
        ("room", AXIS_Y): [-100.0, 100.0, 3900.0, 4100.0],
        # guney cephedeki kapi kenarlari + dis yuzler
        ("opening", AXIS_X): [-100.0, 1000.0, 1900.0, 6100.0],
        # bati cephede aciklik YOK -> bos liste (zincir de cizilmez)
        ("opening", AXIS_Y): [],
    }
    for (name, axis), expected in cases.items():
        actual = getattr(ordinates, name)(axis)
        if not _equal(actual, expected):
            errors.append(f"{name}({axis}) beklenen {expected}, cikan {actual}")

    # Metin tam sayi cm olmali
    if format_dimension_cm(2850.0) != "285":
        errors.append("format_dimension_cm(2850) '285' olmali.")
    if format_dimension_cm(-200.0) != "20":
        errors.append("format_dimension_cm negatif degeri mutlak almali.")

    # Tolerans icindeki iki ordinat TEK noktaya inmeli (sifir uzunluklu olcu
    # uretilmesin diye)
    if not _equal(merge_ordinates([0.0, 0.5, 1000.0]), [0.0, 1000.0]):
        errors.append("merge_ordinates 1 mm icindeki iki degeri birlestirmedi.")
    return errors


def check_stack() -> list[str]:
    """Kademelendirme (Fikir 2) ve ust uste binme YASAGI."""
    errors: list[str] = []
    style = None
    chains = [
        DimensionChain.horizontal([0.0, 1000.0], 0.0, 0.0, style, label="a"),
        DimensionChain.horizontal([0.0, 2000.0], 0.0, 0.0, style, label="b"),
        DimensionChain.horizontal([0.0, 3000.0], 0.0, 0.0, style, label="c"),
    ]
    stacked = ChainStack(-700.0, 550.0).place(chains)
    offsets = [chain.base_offset for chain in stacked]
    if not _equal(offsets, [-700.0, -1250.0, -1800.0]):
        errors.append(f"ChainStack ofsetleri [-700,-1250,-1800] olmali, {offsets} cikti.")

    # NEGATIF TEST: ayni baseline'daki iki zincir HATA vermeli
    same = [
        DimensionChain.horizontal([0.0, 1000.0], 0.0, -500.0, style, label="a"),
        DimensionChain.horizontal([0.0, 2000.0], 0.0, -500.0, style, label="b"),
    ]
    try:
        ChainLayout.verify_no_overlap(same)
    except ValueError:
        pass
    else:
        errors.append("YAKALANMADI: ayni baseline'daki iki zincir hata vermeliydi.")

    # Farkli YONdeki iki zincir ayni sayisal ofseti paylasabilir
    mixed = [
        DimensionChain.horizontal([0.0, 1000.0], 0.0, -500.0, style, label="yatay"),
        DimensionChain.vertical([0.0, 1000.0], 0.0, -500.0, style, label="dusey"),
    ]
    try:
        ChainLayout.verify_no_overlap(mixed)
    except ValueError as exc:
        errors.append(f"YANLIS-POZITIF: farkli yondeki zincirler catisti ({exc}).")
    return errors


def check_planner() -> list[str]:
    errors: list[str] = []
    floor = _floor()

    # Varsayilan KAPALI: hicbir sey cizilmemeli
    if FloorDimensionPlanner(floor, DimensionSettings()).chains(0.0):
        errors.append("Varsayilan ayarla (kapali) zincir uretildi.")

    settings = DimensionSettings(enabled=True)
    chains = FloorDimensionPlanner(floor, settings).chains(0.0)
    labels = [chain.label for chain in chains]
    expected = ["x/aciklik", "x/mahal", "x/toplam", "y/mahal", "y/toplam"]
    if labels != expected:
        errors.append(f"Zincir sirasi {expected} olmali, {labels} cikti.")

    # Bati cephede aciklik olmadigi icin y yigini 2 kademedir ve ILK kademeden
    # baslar (bos bir kademe atlanmaz).
    # Yiginin cikis noktasi yapinin DIS YUZUDUR (-100), merkez cizgisi degil:
    # -100 - 700 = -800, sonra -1350.
    y_offsets = [c.base_offset for c in chains if c.label.startswith("y/")]
    if not _equal(y_offsets, [-800.0, -1350.0]):
        errors.append(f"y yigini [-800,-1350] olmali, {y_offsets} cikti.")

    # dx otelemesi yalnizca X ordinatlarini tasimali
    shifted = FloorDimensionPlanner(floor, settings).chains(10000.0)
    x_chain = next(c for c in shifted if c.label == "x/toplam")
    if not _equal([p[0] for p in x_chain.points], [9900.0, 16100.0]):
        errors.append(f"dx otelemesi yanlis: {[p[0] for p in x_chain.points]}")

    # Capraz nokta: aks baloncugu olcu yigininin DISINDA kalmali
    depth = settings.stack_depth()
    axis_offset = settings.axis_dimension_offset(400.0)
    extension = settings.required_axis_extension(1200.0, 450.0)
    if axis_offset <= depth:
        errors.append("Aks olcu zinciri detay yigininin ICINDE kaldi.")
    if extension <= axis_offset + 450.0:
        errors.append("Aks baloncugu kendi olcu zincirinin uzerine biniyor.")

    # Kapali ayarda aks standardi DEGISMEMELI
    off = DimensionSettings()
    if off.required_axis_extension(1200.0, 450.0) != 1200.0:
        errors.append("Olcu kapaliyken aks uzamasi degistirildi.")
    if off.axis_dimension_offset(400.0) != 400.0:
        errors.append("Olcu kapaliyken aks olcu ofseti degistirildi.")
    return errors


def check_rendered_layer() -> list[str]:
    """rev-18: ezdxf 1.4.4'un `BaseDimensionRenderer.add_line`'i, katman
    dahil BIRLESMIS `attribs` sozlugunu hesaplayip ATAR ama geometri
    BLOK'una orijinal (katmansiz) `dxfattribs`'i gecirir - sonuc, olcu/
    uzatma cizgilerinin DIMENSION'in kendi katmanindan BAGIMSIZ olarak hep
    '0' katmaninda cizilmesidir (kullanici sikayeti: 'aks çizgileri
    ölçüleri aks çizgileri ile aynı layerda olmalı'). `LinearDim.render`
    render SONRASI bir duzeltme uygular; bu test o duzeltmeyi GERCEK bir
    ezdxf DIMENSION uzerinde dogrular - duzeltme kaldirilirsa bu test
    YAKALAR (elle: LINE/ARC/INSERT/MTEXT hepsi 'AKS_TEST' olmali,
    Defpoints ise KENDI ozel katmaninda kalmali)."""
    errors: list[str] = []
    doc = ezdxf.new()
    doc.layers.add("AKS_TEST")
    msp = doc.modelspace()
    style = DimensionStyle(layer="AKS_TEST")
    dimension = LinearDim((0.0, 0.0), (1000.0, 0.0), (0.0, -400.0), 0, style).render(msp)
    block = doc.blocks.get(dimension.dxf.geometry)
    stray = [e.dxftype() for e in block
             if e.dxf.layer not in ("AKS_TEST", "Defpoints")]
    if stray:
        errors.append(f"Geometri blogunda AKS_TEST/Defpoints DISINDA katmanli "
                      f"varlik bulundu: {stray}")
    if not any(e.dxf.layer == "Defpoints" for e in block):
        errors.append("Defpoints (tanim noktasi) katmani hic bulunamadi.")
    return errors


def main() -> int:
    groups = (
        ("ordinat turetme", check_ordinates()),
        ("kademelendirme (negatif test)", check_stack()),
        ("planlayici ve capraz nokta", check_planner()),
        ("render sonrasi katman duzeltmesi (ezdxf hatasi)", check_rendered_layer()),
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
        print("\nOLCU SELF-TEST BASARISIZ.")
        return 1
    print("\nOlcu self-test BASARILI.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
