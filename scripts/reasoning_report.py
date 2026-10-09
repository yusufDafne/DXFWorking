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

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from reasoning import (build_coverage, diff_findings, group_across_floors, load_registry,  # noqa: E402
                       parse_validate_output)

DEFAULT_CONTEXT = HERE.parent / "context.json"


def run_validate(context: Path) -> tuple[str, bool]:
    proc = subprocess.run([sys.executable, str(HERE / "validate.py"), str(context)],
                          capture_output=True, text=True, timeout=600)
    return proc.stdout + proc.stderr, proc.returncode == 0


def describe_group(group_key: str, items: list) -> str:
    floors = sorted({f.floor_id for f in items if f.floor_id})
    where = f" ({len(floors)} katta: {', '.join(floors)})" if len(floors) > 1 else (f" [{floors[0]}]" if floors else "")
    return f"- {items[0].facet_id}: {items[0].message}{where}"


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
