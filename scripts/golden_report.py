#!/usr/bin/env python3
"""Semantic DXF golden raporu: olcum, kural kontrolu ve fixture kosucusu.

DEV-006 ile genisletildi. Uc katman vardir:

1. **Olcum raporu** (`report`) - entity sayisi/turu, layer dagilimi,
   modelspace bounding box, SHA-256. `--compare` ile karsilastirilir.
2. **Semantik kurallar** (`check_rules`) - "kac tane var" degil "dogru yerde
   ve dogru bicimde mi". Olcum raporunun TAMAMEN kor oldugu hata sinifini
   yakalar: bir duvar kaysa, bir mahal etiketi odasindan tassa veya bir kapi
   sembolu kaybolsa entity sayilari degismeyebilir ama kural patlar.
3. **Fixture kosucusu** (`run_fixtures`) - kucuk, izole context'ler uzerinde
   ayni kontrolleri calistirir. Tum projeyi tek parca karsilastirmak yerine
   modul modul bakilir; fark ciktiginda HANGI modulun bozuldugu dogrudan
   gorunur.

Kullanim:
    python scripts/golden_report.py output/plan.dxf
    python scripts/golden_report.py output/plan.dxf --write <rapor.json>
    python scripts/golden_report.py output/plan.dxf --compare <rapor.json>
    python scripts/golden_report.py output/plan.dxf --rules context.json
    python scripts/golden_report.py --fixtures
    python scripts/golden_report.py --fixtures --update

ONEMLI - bounding box: `entity_bbox` artik ezdxf'in gercek extent
hesabini kullanir. Onceki surum `INSERT` icin yalnizca EKLEME NOKTASINI
donduruyordu, yani bir bloga sarilmis geometri bounding box'a hic girmiyordu;
tefris/kolon bloklarina gecildiginde rapor sessizce kuculecekti (olculerek
tespit edildi). `TEXT` icin de yalnizca ekleme noktasi aliniyordu.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
from collections import Counter
from pathlib import Path

import ezdxf
import ezdxf.bbox as bbox_mod

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_ROOT = PROJECT_ROOT / "docs" / "development" / "fixtures"

sys.path.insert(0, str(Path(__file__).resolve().parent))


def entity_bbox(entity):
    """Bir entity'nin GERCEK sinirlari. `INSERT` blok icerigini, `TEXT` ise
    metin genisligini kapsar (bkz. modul docstring'indeki uyari)."""
    try:
        box = bbox_mod.extents([entity], fast=True)
    except Exception:
        return None
    if not box.has_data:
        return None
    return [float(box.extmin[0]), float(box.extmin[1]),
            float(box.extmax[0]), float(box.extmax[1])]


def report(path: Path) -> dict:
    document = ezdxf.readfile(path)
    modelspace = document.modelspace()
    types = Counter(entity.dxftype() for entity in modelspace)
    layers = Counter(entity.dxf.layer for entity in modelspace)
    box = bbox_mod.extents(modelspace, fast=True)
    bbox = ([round(float(box.extmin[0]), 3), round(float(box.extmin[1]), 3),
             round(float(box.extmax[0]), 3), round(float(box.extmax[1]), 3)]
            if box.has_data else None)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    result = {
        "source": str(path),
        "sha256": digest,
        "entity_count": len(modelspace),
        "entity_types": dict(sorted(types.items())),
        "layers": dict(sorted(layers.items())),
        "modelspace_bbox": bbox,
    }
    blocks = sorted(b.name for b in document.blocks
                    if not b.name.startswith("*"))
    if blocks:
        result["blocks"] = blocks
        result["block_inserts"] = dict(sorted(
            Counter(e.dxf.name for e in modelspace.query("INSERT")).items()))
    return result


def compare(actual: dict, expected: dict) -> list[str]:
    differences = []
    keys = ("entity_count", "entity_types", "layers", "modelspace_bbox",
            "blocks", "block_inserts")
    for key in keys:
        if actual.get(key) != expected.get(key):
            differences.append(key)
    return differences


# --------------------------------------------------------------------------
# Semantik kurallar
# --------------------------------------------------------------------------

def _text_entities(msp):
    return list(msp.query("TEXT"))


def _sheet_offsets(context: dict) -> list[tuple[dict, float]]:
    """Her katin modelspace X ofsetini `generate_dxf.generate` ile AYNI
    formulle yeniden hesaplar. Bu yuzden pafta yerlesimi degisirse bu
    fonksiyon da guncellenmelidir - kasitli bir baglilik."""
    from pafta import CONTENT_PADDING, FRAME_GAP, CoverBlock

    scale = context["meta"].get("scale", "1:100")
    block = CoverBlock(scale)
    frame_half = CONTENT_PADDING + FRAME_GAP
    cursor = (block.width - block.frame_gap) + frame_half
    offsets = []
    for floor in context["floors"]:
        offsets.append((floor, cursor))
        cursor += context["meta"]["floor_width"] + 2 * frame_half
    return offsets


def rule_room_labels(doc, context: dict) -> list[str]:
    """Her mahal etiketi 3 satirdir ve TAMAMI kendi oda poligonunun icinde
    kalir. Olcum raporu bunu goremez: etiket yanlis odaya yazilsa veya
    odasindan tassa entity sayilari ayni kalir."""
    from rooms import PolygonOps, RoomLabeler

    errors: list[str] = []
    msp = doc.modelspace()
    texts = _text_entities(msp)
    for floor, dx in _sheet_offsets(context):
        code = floor.get("code", "")
        for room in floor["rooms"]:
            polygon = [[p[0] + dx, p[1]] for p in room["polygon"]]
            xs = [p[0] for p in polygon]
            ys = [p[1] for p in polygon]
            expected = [t for t, _ in RoomLabeler.lines(room, code) if t]
            cx, cy = PolygonOps.centroid(polygon)
            found = [e for e in texts
                     if e.dxf.text in expected
                     and abs(e.get_placement()[1][0] - cx) < 1.0
                     and abs(e.get_placement()[1][1] - cy) < 2000.0]
            ident = f"{code}-{room.get('no', room['id'])}"
            if len(found) != len(expected):
                errors.append(
                    f"Mahal '{ident}': {len(expected)} etiket satiri bekleniyordu, "
                    f"{len(found)} bulundu."
                )
                continue
            box = bbox_mod.extents(found, fast=True)
            if not box.has_data:
                continue
            if (box.extmin[0] < min(xs) - 1 or box.extmax[0] > max(xs) + 1
                    or box.extmin[1] < min(ys) - 1 or box.extmax[1] > max(ys) + 1):
                errors.append(
                    f"Mahal '{ident}' etiketi oda sinirlarini asiyor."
                )
    return errors


def rule_opening_symbols(doc, context: dict) -> list[str]:
    """Her kapi bir yay (ARC) sembolu uretir. Kapi sembolu kaybolsa veya
    pencere kapiya donsa entity TURU degisir ama toplam sayi sabit
    kalabilir - bu kural farki yakalar."""
    msp = doc.modelspace()
    arcs = len(msp.query("ARC"))
    doors = sum(1 for floor in context["floors"]
                for opening in floor["openings"] if opening["type"] == "door")
    if arcs != doors:
        return [f"Kapi sembolu sayisi tutmuyor: {doors} kapi bildirildi, "
                f"{arcs} ARC cizildi."]
    return []


def rule_axis_bubbles(doc, context: dict) -> list[str]:
    """Aks cizgisi baloncugun ICINE girmez (kullanici standardi: cizgi
    baloncuk kenarinda biter). Bu bir GEOMETRIK kuraldir; sayim raporu
    baloncugun icine giren bir cizgiyi asla fark etmez."""
    msp = doc.modelspace()
    circles = list(msp.query('CIRCLE[layer=="AKS"]'))
    lines = list(msp.query('LINE[layer=="AKS"]'))
    errors: list[str] = []
    for circle in circles:
        cx, cy, _ = circle.dxf.center
        radius = circle.dxf.radius
        for line in lines:
            for point in (line.dxf.start, line.dxf.end):
                distance = math.hypot(point[0] - cx, point[1] - cy)
                if distance < radius - 1.0:
                    errors.append(
                        f"Aks cizgisi baloncugun icine giriyor "
                        f"(merkez {cx:.0f},{cy:.0f}; uc mesafesi {distance:.0f} "
                        f"< yaricap {radius:.0f})."
                    )
                    return errors
    return errors


def rule_block_references(doc, context: dict) -> list[str]:
    """Her `INSERT` tanimli bir bloga isaret eder. Tanimsiz blok referansi
    AutoCAD'de bos gorunur; dosya yine de acilir, yani sessiz bir hatadir."""
    errors: list[str] = []
    names = {b.name for b in doc.blocks}
    for insert in doc.modelspace().query("INSERT"):
        if insert.dxf.name not in names:
            errors.append(f"Tanimsiz blok referansi: '{insert.dxf.name}'.")
    return errors


def _code_owned_layers() -> set[str]:
    """Context'te bildirilmeyen, KOD tarafindan zorunlu kilinan layer'lar
    (aks, tefris gruplari, kolon). Bunlarin rengi/adi modullerin sorumlulugudur."""
    from columns import COLUMN_HATCH_LAYER, COLUMN_LAYER, COLUMN_TEXT_LAYER
    from furniture import FURNITURE_GROUPS

    layers = {"AKS", "0", COLUMN_LAYER, COLUMN_HATCH_LAYER, COLUMN_TEXT_LAYER}
    layers |= {group.layer for group in FURNITURE_GROUPS.values()}
    return layers


def rule_declared_layers(doc, context: dict) -> list[str]:
    """Cizimde context'te BILDIRILMEMIS bir layer kullanilmaz. Kod tarafindan
    zorunlu kilinan layer'lar (AKS, TEFRIS-*, KOLON*) muaftir."""
    declared = {layer["name"] for layer in context["layers"]} | _code_owned_layers()
    used = {e.dxf.layer for e in doc.modelspace()}
    unknown = sorted(used - declared)
    if unknown:
        return [f"Bildirilmemis layer kullanilmis: {', '.join(unknown)}."]
    return []


RULES = {
    "room_labels": rule_room_labels,
    "opening_symbols": rule_opening_symbols,
    "axis_bubbles": rule_axis_bubbles,
    "block_references": rule_block_references,
    "declared_layers": rule_declared_layers,
}


def check_rules(dxf_path: Path, context_path: Path) -> dict[str, list[str]]:
    doc = ezdxf.readfile(dxf_path)
    context = json.loads(context_path.read_bytes().decode("utf-8"))
    return {name: rule(doc, context) for name, rule in RULES.items()}


def print_rule_results(results: dict[str, list[str]]) -> int:
    failed = 0
    for name, errors in results.items():
        if errors:
            failed += 1
            print(f"  [HATA] {name}: {len(errors)} sorun")
            for error in errors[:5]:
                print(f"         - {error}")
            if len(errors) > 5:
                print(f"         ... ve {len(errors) - 5} tane daha")
        else:
            print(f"  [OK  ] {name}")
    return failed


# --------------------------------------------------------------------------
# Fixture kosucusu
# --------------------------------------------------------------------------

def fixture_dirs() -> list[Path]:
    if not FIXTURE_ROOT.exists():
        return []
    return sorted(p for p in FIXTURE_ROOT.iterdir()
                  if p.is_dir() and (p / "context.json").exists())


def run_fixtures(update: bool = False) -> int:
    """Her fixture icin: validate -> generate -> olcum raporu + kurallar."""
    import tempfile

    import generate_dxf
    import validate as validator

    failures = 0
    fixtures = fixture_dirs()
    if not fixtures:
        print("Fixture bulunamadi.")
        return 1

    for fixture in fixtures:
        context_path = fixture / "context.json"
        golden_path = fixture / "golden.json"
        print(f"\n--- fixture: {fixture.name} ---")

        if not validator.run_validation(context_path):
            print("  [HATA] validate basarisiz")
            failures += 1
            continue

        with tempfile.TemporaryDirectory() as tmp:
            dxf_path = Path(tmp) / "fixture.dxf"
            try:
                generate_dxf.generate(context_path, dxf_path)
            except Exception as exc:
                print(f"  [HATA] generate: {type(exc).__name__}: {exc}")
                failures += 1
                continue

            actual = report(dxf_path)
            actual.pop("sha256", None)      # gecici yol/zaman bagimli degil
            actual["source"] = fixture.name

            if update or not golden_path.exists():
                golden_path.write_text(json.dumps(actual, indent=2) + "\n",
                                       encoding="utf-8")
                print("  [YAZILDI] golden.json")
            else:
                expected = json.loads(golden_path.read_text(encoding="utf-8"))
                differences = compare(actual, expected)
                if differences:
                    print(f"  [HATA] golden farki: {', '.join(differences)}")
                    failures += 1
                else:
                    print("  [OK  ] golden raporu eslesti")

            results = check_rules(dxf_path, context_path)
            failures += print_rule_results(results)

    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dxf", type=Path, nargs="?")
    parser.add_argument("--write", type=Path, help="Semantic golden raporu yaz")
    parser.add_argument("--compare", type=Path, help="Mevcut raporla karsilastir")
    parser.add_argument("--rules", type=Path, help="Semantik kurallari bu context ile kontrol et")
    parser.add_argument("--fixtures", action="store_true", help="Fixture katalogunu calistir")
    parser.add_argument("--update", action="store_true", help="--fixtures ile: golden dosyalarini yeniden yaz")
    args = parser.parse_args()

    if args.fixtures:
        failures = run_fixtures(update=args.update)
        print(f"\nFixture sonucu: {'BASARILI' if failures == 0 else f'{failures} BASARISIZ'}")
        return 1 if failures else 0

    if args.dxf is None:
        parser.error("dxf yolu gerekli (veya --fixtures kullanin)")

    exit_code = 0
    actual = report(args.dxf)
    if args.write:
        args.write.write_text(json.dumps(actual, indent=2) + "\n", encoding="utf-8")
    if args.compare:
        expected = json.loads(args.compare.read_text(encoding="utf-8"))
        differences = compare(actual, expected)
        if differences:
            print("Golden differences: " + ", ".join(differences))
            exit_code = 1
        else:
            print("Golden semantic report matches.")
    if args.rules:
        print("Semantik kurallar:")
        exit_code = 1 if print_rule_results(check_rules(args.dxf, args.rules)) else exit_code
    if not args.compare and not args.rules and not args.write:
        print(json.dumps(actual, indent=2))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
