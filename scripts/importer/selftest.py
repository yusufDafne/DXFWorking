#!/usr/bin/env python3
"""DXF duvar tarayicisi testleri (DEV-013).

Kullanim:
    python scripts/importer/selftest.py
Cikis kodu: 0 basarili, 1 basarisiz.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import ezdxf  # noqa: E402

from importer import DxfWallScanner, evaluate_pair  # noqa: E402

TOLERANCE = 1e-6


def check_perfect_parallel_pair() -> list[str]:
    """Tam paralel, tam ortusen, 200mm araliklu cift -> confidence TAM 1.0,
    kalinlik TAM 200, merkez cizgisi girdi cizgilerinin ORTASI (elle
    hesaplanabilir en basit durum)."""
    errors: list[str] = []
    candidate = evaluate_pair(
        (0.0, 0.0), (5000.0, 0.0), "0", "hA",
        (0.0, 200.0), (5000.0, 200.0), "0", "hB",
    )
    if candidate is None:
        return ["Aday bulunamadi (beklenmiyordu)."]
    if abs(candidate.confidence - 1.0) > TOLERANCE:
        errors.append(f"confidence 1.0 bekleniyordu, {candidate.confidence} bulundu.")
    if abs(candidate.thickness - 200.0) > TOLERANCE:
        errors.append(f"kalinlik 200 bekleniyordu, {candidate.thickness} bulundu.")
    if candidate.start != (0.0, 100.0) or candidate.end != (5000.0, 100.0):
        errors.append(f"merkez cizgisi farkli: {candidate.start}, {candidate.end}.")
    return errors


def check_partial_overlap_hand_computable() -> list[str]:
    """Kismi ortusen cift: A=(0,1000)-(5000,1000) (len 5000), B=(2000,1150)-
    (5000,1150) (len 3000). Ortusme [2000,5000]=3000, oran=3000/5000=0.6;
    aci=0 -> confidence=0.6. Merkez cizgisi SADECE ortusen bolgede
    (2000..5000), y=1075 (1000 ve 1150'nin ortasi)."""
    errors: list[str] = []
    candidate = evaluate_pair(
        (0.0, 1000.0), (5000.0, 1000.0), "1", "hA",
        (2000.0, 1150.0), (5000.0, 1150.0), "1", "hB",
    )
    if candidate is None:
        return ["Aday bulunamadi (beklenmiyordu)."]
    if abs(candidate.confidence - 0.6) > TOLERANCE:
        errors.append(f"confidence 0.6 bekleniyordu, {candidate.confidence} bulundu.")
    if abs(candidate.thickness - 150.0) > TOLERANCE:
        errors.append(f"kalinlik 150 bekleniyordu, {candidate.thickness} bulundu.")
    if candidate.start != (2000.0, 1075.0) or candidate.end != (5000.0, 1075.0):
        errors.append(f"merkez cizgisi farkli: {candidate.start}, {candidate.end}.")
    return errors


def check_low_overlap_rejected() -> list[str]:
    """Ortusme orani esigin (0.5) ALTINDAYSA aday reddedilir (negatif test).
    A=(0,0)-(5000,0), B=(4500,150)-(6000,150): ortusme [4500,5000]=500,
    oran=500/5000=0.1 < 0.5."""
    candidate = evaluate_pair(
        (0.0, 0.0), (5000.0, 0.0), "4", "hA",
        (4500.0, 150.0), (6000.0, 150.0), "4", "hB",
    )
    if candidate is not None:
        return [f"Reddedilmesi bekleniyordu, aday bulundu: {candidate}."]
    return []


def check_out_of_range_thickness_rejected() -> list[str]:
    """Kalinlik [40,400] araliginin DISINDAYSA (600mm) aday reddedilir."""
    candidate = evaluate_pair(
        (0.0, 0.0), (3000.0, 0.0), "2", "hA",
        (0.0, 600.0), (3000.0, 600.0), "2", "hB",
    )
    if candidate is not None:
        return [f"Reddedilmesi bekleniyordu, aday bulundu: {candidate}."]
    return []


def check_angle_beyond_limit_rejected() -> list[str]:
    """Aci sinirinin (10 derece) USTUNDEYSE aday reddedilir. B, A'ya gore
    ~20 derece dondurulmus (tan(20)*5000 ~= 1820 dusey kayma)."""
    candidate = evaluate_pair(
        (0.0, 0.0), (5000.0, 0.0), "5", "hA",
        (0.0, 200.0), (5000.0, 2020.0), "5", "hB",
    )
    if candidate is not None:
        return [f"Reddedilmesi bekleniyordu, aday bulundu: {candidate}."]
    return []


def check_different_layer_rejected() -> list[str]:
    """Farkli katmandaki iki cizgi ADAY OLAMAZ - gercek bir duvarin iki
    rail'i HER ZAMAN ayni katmandadir (yanlis-pozitif riskini azaltir)."""
    candidate = evaluate_pair(
        (0.0, 0.0), (3000.0, 0.0), "A", "hA",
        (0.0, 150.0), (3000.0, 150.0), "B", "hB",
    )
    if candidate is not None:
        return [f"Reddedilmesi bekleniyordu, aday bulundu: {candidate}."]
    return []


def check_end_to_end_scan_and_provenance() -> list[str]:
    """Gercek bir DXF dosyasi taranir: aday sayisi, siralama (confidence
    azalan) ve provenance (kaynak yol + sha256) dogrulanir."""
    errors: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "existing.dxf"
        doc = ezdxf.new()
        msp = doc.modelspace()
        msp.add_line((0, 0), (5000, 0), dxfattribs={"layer": "0"})
        msp.add_line((0, 200), (5000, 200), dxfattribs={"layer": "0"})
        msp.add_line((0, 1000), (5000, 1000), dxfattribs={"layer": "1"})
        msp.add_line((2000, 1150), (5000, 1150), dxfattribs={"layer": "1"})
        doc.saveas(path)

        report = DxfWallScanner().scan(path)
        if len(report.candidates) != 2:
            errors.append(f"2 aday bekleniyordu, {len(report.candidates)} bulundu.")
            return errors
        if report.candidates[0].confidence < report.candidates[1].confidence:
            errors.append("Adaylar confidence azalan sirada OLMALI.")
        if report.source_path != path:
            errors.append("source_path korunmadi.")
        if len(report.source_sha256) != 64:
            errors.append("sha256 64 hex karakter olmali.")
        wall_dict = report.candidates[0].as_wall_dict("test")
        for required in ("id", "start", "end", "thickness", "layer"):
            if required not in wall_dict:
                errors.append(f"as_wall_dict() '{required}' alanini icermiyor.")
    return errors


def main() -> int:
    groups = (
        ("tam paralel cift (elle hesaplanabilir)", check_perfect_parallel_pair()),
        ("kismi ortusen cift (elle hesaplanabilir)", check_partial_overlap_hand_computable()),
        ("dusuk ortusme -> reddedilir (negatif test)", check_low_overlap_rejected()),
        ("kalinlik araligi disi -> reddedilir (negatif test)", check_out_of_range_thickness_rejected()),
        ("aci siniri -> reddedilir (negatif test)", check_angle_beyond_limit_rejected()),
        ("farkli katman -> reddedilir (negatif test)", check_different_layer_rejected()),
        ("uctan uca tarama + provenance", check_end_to_end_scan_and_provenance()),
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
        print("\nIMPORTER SELF-TEST BASARISIZ.")
        return 1
    print("\nImporter self-test BASARILI.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
