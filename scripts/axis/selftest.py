#!/usr/bin/env python3
"""Kismi aks, etiket kurali ve kapsama raporu testleri (DEV-015).

Kullanim:
    python scripts/axis/selftest.py
Cikis kodu: 0 basarili, 1 basarisiz.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import ezdxf  # noqa: E402

from axis import (  # noqa: E402
    Axis,
    AxisCoverageReport,
    AxisDrawingStandard,
    AxisGrid,
    axes_from_context,
    check_labels,
)

TOLERANCE = 1e-6


def check_partial() -> list[str]:
    errors: list[str] = []
    standard = AxisDrawingStandard()

    full = Axis("1", 0.0)
    partial = Axis("2'", 5000.0, extent=(5000.0, 9000.0))

    if full.partial or not partial.partial:
        errors.append("`partial` ozelligi yanlis.")
    if full.intermediate or not partial.intermediate:
        errors.append("`intermediate` (kesme isareti) tespiti yanlis.")

    # Tam aks yapinin DISINA `extension` kadar tasar
    span = full.span(0.0, 17500.0, standard.extension, standard.partial_extension)
    if abs(span[0] + 1200.0) > TOLERANCE or abs(span[1] - 18700.0) > TOLERANCE:
        errors.append(f"Tam aks uzanimi (-1200, 18700) olmali, {span} cikti.")

    # Kismi aks yalnizca `partial_extension` kadar tasar
    span = partial.span(0.0, 17500.0, standard.extension, standard.partial_extension)
    if abs(span[0] - 4400.0) > TOLERANCE or abs(span[1] - 9600.0) > TOLERANCE:
        errors.append(f"Kismi aks uzanimi (4400, 9600) olmali, {span} cikti.")

    # Kenara ULASMA testi
    if not full.covers(0.0):
        errors.append("Tam aks kenari kapsamiyor sayildi.")
    if partial.covers(0.0):
        errors.append("Kismi aks, ulasmadigi kenari kapsiyor sayildi.")
    if not partial.covers(7000.0):
        errors.append("Kismi aks kendi araligindaki noktayi kapsamiyor sayildi.")

    # Ters verilen extent duzeltilmeli
    reversed_extent = Axis.from_context(
        {"label": "3", "position": 1.0, "extent": [9000, 5000]})
    if reversed_extent.extent != (5000.0, 9000.0):
        errors.append("Ters verilen extent siralanmadi.")

    # Siralama konuma gore deterministik olmali
    order = [a.label for a in axes_from_context([
        {"label": "3", "position": 5000}, {"label": "1", "position": 0},
        {"label": "2", "position": 1000},
    ])]
    if order != ["1", "2", "3"]:
        errors.append(f"Aks siralamasi ['1','2','3'] olmali, {order} cikti.")
    return errors


def check_chain_membership() -> list[str]:
    """Kismi aks, ULASMADIGI kenarin olcu zincirine girmemeli."""
    errors: list[str] = []
    grid = AxisGrid(
        [{"label": "1", "position": 0},
         {"label": "2'", "position": 3000, "extent": [5000, 9000]},
         {"label": "3", "position": 8000}],
        [{"label": "A", "position": 0}, {"label": "B", "position": 9000}],
        text_height=200.0,
    )
    reaching = [a.label for a in grid.vertical if a.covers(0.0)]
    if reaching != ["1", "3"]:
        errors.append(
            f"Guney kenar zincirine ['1','3'] girmeliydi, {reaching} cikti "
            f"(kismi aks 2' y=0'a ulasmiyor).")
    return errors


def check_naming() -> list[str]:
    """Etiket kurali (`1'` evet, `1A` hayir) - NEGATIF testler."""
    errors: list[str] = []

    clean = check_labels(
        [{"label": "1", "position": 0}, {"label": "2'", "position": 1000}],
        [{"label": "A", "position": 0}, {"label": "B'", "position": 1000}],
    )
    if clean:
        errors.append(f"YANLIS-POZITIF: gecerli etiketler reddedildi: {clean}")

    cases = {
        "1A": ([{"label": "1A", "position": 0}], []),
        "kucuk harf yatay": ([], [{"label": "a", "position": 0}]),
        "yatayda rakam": ([], [{"label": "1", "position": 0}]),
        "duseyde harf": ([{"label": "A", "position": 0}], []),
        "cift kesme": ([{"label": "1''", "position": 0}], []),
    }
    for why, (vertical, horizontal) in cases.items():
        if not check_labels(vertical, horizontal):
            errors.append(f"YAKALANMADI ({why}): kural ihlali bildirilmedi.")

    duplicate = check_labels(
        [{"label": "1", "position": 0}, {"label": "1", "position": 5000}], [])
    if not duplicate:
        errors.append("YAKALANMADI: ayni etiket iki aksta kullanilmis.")
    return errors


def check_coverage() -> list[str]:
    """Kolon rasteri kapsama raporu - SALT OKUNUR."""
    errors: list[str] = []
    vertical = [{"label": "1", "position": 0.0}, {"label": "2", "position": 6000.0}]
    horizontal = [{"label": "A", "position": 0.0}, {"label": "B", "position": 4000.0}]

    covered = AxisCoverageReport.from_columns(
        [{"id": "c1", "position": [0.0, 0.0]},
         {"id": "c2", "position": [6000.0, 4000.0]}],
        vertical, horizontal)
    if not covered.ok:
        errors.append(f"YANLIS-POZITIF: aks uzerindeki kolonlar eksik sayildi: "
                      f"{covered.lines()}")

    missing = AxisCoverageReport.from_columns(
        [{"id": "c3", "position": [3000.0, 2000.0]},
         {"id": "c4", "position": [3000.0, 2000.0]}],
        vertical, horizontal, floor_code="T1")
    if missing.ok:
        errors.append("YAKALANMADI: aks'siz kolon hizasi bildirilmedi.")
    if missing.missing_vertical != [3000.0]:
        errors.append(f"Aks'siz X [3000] olmali, {missing.missing_vertical} cikti "
                      f"(ayni hizadaki iki kolon TEK kez bildirilmeli).")
    if missing.missing_horizontal != [2000.0]:
        errors.append(f"Aks'siz Y [2000] olmali, {missing.missing_horizontal} cikti.")
    return errors


def check_total_span_dimension() -> list[str]:
    """rev-18 (kullanici karari: 'akslar arası mesafeler ve ikinci olarak
    en uçtaki aksların arasındaki mesafeyi vermeli'): 2'den FAZLA aks
    varsa ardisik-mesafe zincirinin YANINA bir de en-uctaki-aksa-aks TOPLAM
    zinciri eklenir; TAM 2 aks varsa bu ikisi ZATEN AYNI sayidir ve
    tekrar cizilmemelidir (elle sayilabilir DIMENSION adedi)."""
    errors: list[str] = []
    doc = ezdxf.new()
    msp = doc.modelspace()
    # Guney kenarda (y=0) 3 dusey aks (x=0,4000,9000) TAM (partial degil),
    # bati kenarda (x=0) TAM 2 yatay aks (y=0,9000).
    grid = AxisGrid(
        [{"label": "1", "position": 0}, {"label": "2", "position": 4000},
         {"label": "3", "position": 9000}],
        [{"label": "A", "position": 0}, {"label": "B", "position": 9000}],
        text_height=200.0,
    )
    grid.draw_on_floor(msp, dx=0.0, floor_width=9000.0, floor_depth=9000.0)
    dims = list(msp.query("DIMENSION"))
    # Guney (3 aks): ardisik 1-2 + 2-3 (2 varlik) + en-uctaki-toplam 1-3
    # (1 varlik daha) = 3. Bati (TAM 2 aks): ardisik 1 varlik, toplam AYNI
    # sayi oldugu icin TEKRARLANMAZ. Toplam: 3 + 1 = 4.
    if len(dims) != 4:
        errors.append(f"3 aks + 2 aks icin 3+1=4 DIMENSION bekleniyordu, {len(dims)} bulundu.")
    # En uctaki (3.) aksin toplam zinciri, aksin KENDI baloncuk/uzama
    # bolgesinin (extension+bubble_radius=1650) OTESINDE durmali.
    standard = AxisDrawingStandard()
    min_clearance = standard.extension + standard.bubble_radius
    texts = sorted((d.dxf.text, d.dxf.defpoint.y) for d in dims if d.dxf.layer == "AKS")
    farthest_y = min(y for _, y in texts)
    if abs(farthest_y) <= min_clearance:
        errors.append(f"Toplam zinciri aks baloncugunun ({min_clearance} disinda olmali) "
                      f"ICINDE kaldi: {farthest_y}")
    return errors


def main() -> int:
    groups = (
        ("kismi aks", check_partial()),
        ("olcu zinciri uyeligi", check_chain_membership()),
        ("etiket kurali (negatif test)", check_naming()),
        ("kolon rasteri kapsamasi", check_coverage()),
        ("en uctaki aks TOPLAM zinciri", check_total_span_dimension()),
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
        print("\nAKS SELF-TEST BASARISIZ.")
        return 1
    print("\nAks self-test BASARILI.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
