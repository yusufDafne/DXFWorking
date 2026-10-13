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


META_INPUTS = frozenset({"north_angle"})   # kat degil proje (`context.meta`) girdisi olan adaptor parametreleri


def _resolve(ref: str):
    module, _, name = ref.partition(":")
    return getattr(importlib.import_module(module), name)


def facet_check(facet, meta=None):
    """Veche adaptorunu `floor -> [Finding]` cagrilabilirine cevirir (kopru: cekirdek cizim modulu import etmez).
    Girdi adi katta yoksa `meta`da aranir (ornek `north_angle`); ikisinde de yoksa liste girdileri `[]`, digerleri `None`."""
    fn = _resolve(facet.adapter.ref)
    meta = meta or {}

    def arg(floor, name):
        if name in floor:
            return floor[name]
        if name in meta:
            return meta[name]
        return None if name in META_INPUTS else []

    return lambda floor: adapt_warnings(facet.id, floor.get("id"), fn(*[arg(floor, i) for i in facet.adapter.inputs]))


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
        check = facet_check(facet, context.get("meta"))
        out[facet.id] = [x for fid in ran.get(facet.id, []) for x in check(floors[fid])]
    return out


def measure_inputs(facet) -> tuple:
    """`measure_ref` fonksiyonu ile adaptor AYNI girdi adlarini alir (kapi #11 adaptor parametrelerini denetler)."""
    return facet.adapter.inputs if facet.adapter is not None else ("rooms", "walls", "openings")


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
            margs = [fl.get(n, context.get("meta", {}).get(n) if n in META_INPUTS else []) for n in measure_inputs(facet)]
            for subject, result in measure(*margs).items():
                prev = merged.get(subject)
                merged[subject] = result if prev is None else (prev or bool(result))
        reports.append(trigger_report(facet.id, merged))
    return reports


def case_roles_of(facet) -> set:
    from reasoning import load_case
    from reasoning.cases import CASES_ROOT
    roles = set()
    for name in facet.cases:
        if (CASES_ROOT / name / "case.json").exists():
            roles.add(load_case(CASES_ROOT / name)[0].get("role"))
    return roles


def promotion_report(registry, context, fp_budget=None, today=None) -> list[str]:
    """Terfi/ayirt edicilik raporu (DEV-066): KAPI DEGIL, rapor. Her `shadow` veche icin kontrol listesi + tetik orani (N yazilir, kanit
    zayifsa soylenir); terfi ACIK kullanici karari + HD kaydidir. Ayrica bayat gozden gecirme listesi ve (parametre verilirse) yanlis-pozitif butcesi."""
    import datetime
    from reasoning import per_unit_topic_counts, promotion_readiness, promotion_snippet, select_topics, stale_review_list
    import doc_check
    lines = ["Terfi / ayirt edicilik raporu (KAPI DEGIL; terfi acik kullanici karari + HD kaydidir):"]
    reports = {r.facet_id: r for r in shadow_triggers(registry, context)}
    for facet in registry.facets.values():
        if facet.status != "shadow":
            continue
        items = promotion_readiness(facet, reports.get(facet.id), case_roles_of(facet))
        blockers = [i for i in items if not i.ok and not i.pending_user]
        lines.append(f"- {facet.id}: " + ("terfi icin TEKNIK engel yok (karar kullanicinin)" if not blockers else f"{len(blockers)} engel"))
        for i in items:
            lines.append(f"    [{'x' if i.ok else ('?' if i.pending_user else ' ')}] {i.key}: {i.detail}")
        rep = reports.get(facet.id)
        if rep is not None and not blockers:
            lines.append("    kayit taslagi (karardan sonra):\n      " + promotion_snippet(facet.id, rep).replace("\n", "\n      "))
    stale = stale_review_list(list(registry.facets.values()), today or datetime.date.today(), doc_check.REVIEW_MAX_AGE_DAYS)
    lines.append(f"Gozden gecirme listesi ({len(stale)}; esik {doc_check.REVIEW_MAX_AGE_DAYS} gun bir POLITIKA parametresidir, onay bekler):")
    lines += [f"  - {fid}: {why}" for fid, why in stale]
    if fp_budget is not None:
        out = subprocess.run([sys.executable, str(HERE / "validate.py"), str(context.get("_path", DEFAULT_CONTEXT))], capture_output=True, text=True, timeout=600).stdout
        shown, rest = select_topics(parse_validate_output(out), registry.facets, limit=10**6)
        room_units = {r["id"]: r["unit_id"] for fl in context.get("floors", []) for r in fl.get("rooms", []) if r.get("unit_id")}
        room_units.update({u: u for u in set(room_units.values())})   # bulgu elemani birimin kendisi olabilir (ornek: 'uC')
        counts = per_unit_topic_counts(shown, room_units)
        lines.append(f"Yanlis-pozitif butcesi (kullanici parametresi: birim basina en cok {fp_budget} sunulan konu; varsayilan YOK):")
        for unit, n in sorted(counts.items()):
            lines.append(f"  - {unit}: {n} konu" + ("  ** BUTCE ASILDI **" if n > fp_budget else ""))
    return lines


def main(argv: list[str]) -> int:
    fp_budget = None
    if "--fp-budget" in argv:
        i = argv.index("--fp-budget")
        fp_budget = int(argv[i + 1])
        argv = argv[:i] + argv[i + 2:]
    args = [a for a in argv if not a.startswith("--")]
    before = None
    if "--before" in argv:
        i = argv.index("--before")
        before = Path(argv[i + 1])
        args = [a for a in args if a != argv[i + 1]]
    context_path = Path(args[0]) if args else DEFAULT_CONTEXT
    context = json.loads(context_path.read_text(encoding="utf-8"))
    context["_path"] = str(context_path)

    registry, load_errors = load_registry()
    if "--promotion" in argv:
        print("\n".join(promotion_report(registry, context, fp_budget)))
        return 0
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
        print("\nGolge vecheler (kullaniciya KONU olarak SUNULMAZ; brief yalniz tek satirlik dogrulanmamis-gozlem notu verir; validate.py ciktisina GIRMEZ):")
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
