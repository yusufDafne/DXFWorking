#!/usr/bin/env python3
"""Muhakeme raporu (DEV-060): validate SONRASI, ek, BLOKLAMAYAN adim. validate.py cikisi DEGISMEZ.

Kullanim:  python scripts/reasoning_report.py [context.json] [--before onceki_context.json]
- Kapsam: kayitli merceklerin hangisi kostu / kosamadi / uygulanmaz (bos kayitta bunu SOYLER).
- Bulgular: validate.py'nin UYARI satirlari kat-bagimsiz kimlige gore TEK konuya indirgenir
  (rev-28: 15 satir -> 3 konu). Fonksiyon duzeyi veche yok; 'legacy.<kategori>' (bkz. adapters.py).
- --before: iki context arasinda yeni / cozulen / degismeyen konular (yan etki taramasi).
Cikis kodu her zaman 0'dir (tavsiye niteliginde); validate basarisizsa bu yazilir.
"""
from __future__ import annotations

import importlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from reasoning import (adapt_warnings, build_coverage, diff_findings, group_across_floors,  # noqa: E402
                       load_registry, parse_validate_output, trigger_report)
from reasoning.coverage import STATE_RAN  # noqa: E402

DEFAULT_CONTEXT = HERE.parent / "context.json"


def run_validate(context: Path) -> tuple[str, bool]:
    proc = subprocess.run([sys.executable, str(HERE / "validate.py"), str(context)],
                          capture_output=True, text=True, timeout=600)
    return proc.stdout + proc.stderr, proc.returncode == 0


def describe_group(group_key: str, items: list) -> str:
    floors = sorted({f.floor_id for f in items if f.floor_id})
    where = f" ({len(floors)} katta: {', '.join(floors)})" if len(floors) > 1 else (f" [{floors[0]}]" if floors else "")
    return f"- {items[0].facet_id}: {items[0].message}{where}"


def _resolve(ref: str):
    module, _, name = ref.partition(":")
    return getattr(importlib.import_module(module), name)


def facet_check(facet):
    """Veche adaptorunu `floor -> [Finding]` cagrilabilirine cevirir (kopru: cekirdek cizim modulu import etmez)."""
    fn = _resolve(facet.adapter.ref)
    return lambda floor: adapt_warnings(facet.id, floor.get("id"), fn(*[floor.get(i, []) for i in facet.adapter.inputs]))


def ran_floors(registry, context) -> dict:
    """{veche_id: [kat, ...]} - yalniz kapsam raporunda KOSTU olan katlar."""
    ran: dict = {}
    for e in build_coverage(registry, context).entries:
        if e.state == STATE_RAN:
            ran.setdefault(e.facet_id, []).append(e.floor_id)
    return ran


def shadow_findings(registry, context) -> dict:
    """{veche_id: [Finding]} - `shadow` vecheler (kullaniciya SUNULMAZ; yalniz gozlem)."""
    ran, out = ran_floors(registry, context), {}
    floors = {f.get("id"): f for f in context.get("floors", [])}
    for facet in registry.facets.values():
        if facet.status != "shadow" or facet.adapter is None:
            continue
        check = facet_check(facet)
        out[facet.id] = [x for fid in ran.get(facet.id, []) for x in check(floors[fid])]
    return out


def shadow_triggers(registry, context) -> list:
    """Asgari terfi olcer: `measure_ref` tasiyan shadow veche icin tetik orani (ozne = tekillestirilmis, katlar birlesir)."""
    ran = ran_floors(registry, context)
    floors = {f.get("id"): f for f in context.get("floors", [])}
    reports = []
    for facet in registry.facets.values():
        if facet.status != "shadow" or not facet.measure_ref:
            continue
        measure, merged = _resolve(facet.measure_ref), {}
        for fid in ran.get(facet.id, []):
            fl = floors[fid]
            for subject, result in measure(fl.get("rooms", []), fl.get("walls", []), fl.get("openings", [])).items():
                prev = merged.get(subject)
                merged[subject] = result if prev is None else (prev or bool(result))
        reports.append(trigger_report(facet.id, merged))
    return reports


def main(argv: list[str]) -> int:
    args = [a for a in argv if not a.startswith("--")]
    before = None
    if "--before" in argv:
        i = argv.index("--before")
        before = Path(argv[i + 1])
        args = [a for a in args if a != argv[i + 1]]
    context_path = Path(args[0]) if args else DEFAULT_CONTEXT
    context = json.loads(context_path.read_text(encoding="utf-8"))

    registry, load_errors = load_registry()
    for err in load_errors:
        print("UYARI (kayit):", err)
    print(build_coverage(registry, context).text())

    out, ok = run_validate(context_path)
    if not ok:
        print("NOT: validate.py BASARISIZ - bulgular eksik olabilir.")
    findings = parse_validate_output(out)
    groups = group_across_floors(findings)
    print(f"\nBulgular: {len(findings)} uyari satiri -> {len(groups)} tekil konu")
    for key, items in groups:
        print(describe_group(key, items))

    shadows = shadow_findings(registry, context)
    if shadows:
        print("\nGolge vecheler (kullaniciya SUNULMAZ - yalniz gozlem; validate.py ciktisina GIRMEZ):")
        for facet_id, items in shadows.items():
            tops = group_across_floors(items)
            print(f"- {facet_id}: {len(items)} satir / {len(tops)} konu")
            for key, grp in tops:
                print("   ", describe_group(key, grp))
        print("\nAsgari tetik orani (shadow; kapi degil rapor):")
        for rep in shadow_triggers(registry, context):
            print("  ", rep.text())

    if before is not None:
        out_b, _ = run_validate(before)
        diff = diff_findings(parse_validate_output(out_b), findings)
        print(f"\nOnceki context'e gore ({before.name}):")
        for label, name in (("new", "YENI"), ("resolved", "COZULEN"), ("unchanged", "DEGISMEYEN")):
            tops = group_across_floors(diff[label])
            print(f"  {name}: {len(diff[label])} satir / {len(tops)} konu")
            if label != "unchanged":
                for key, items in tops:
                    print("   ", describe_group(key, items))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
