"""Etki alani raporu (DEV-068, SALT OKUNUR): `python scripts/impact_report.py [context.json] --touch kat:tur:id [...] [--depth N]`
ya da `--before onceki.json` (iki context arasindaki farktan dokunulan elemanlar). `--coverage` kapsam/bagsiz eleman ozeti.
context.json'a hicbir sey yazmaz; patch uretmez; hukum vermez."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import impact  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("context", nargs="?", default=str(Path(__file__).resolve().parent.parent / "context.json"))
    ap.add_argument("--touch", action="append", default=[], help="kat:tur:id (tekrarlanabilir)")
    ap.add_argument("--before", help="onceki context.json; farktan dokunulanlar hesaplanir")
    ap.add_argument("--depth", type=int, default=2)
    ap.add_argument("--coverage", action="store_true")
    a = ap.parse_args(argv)
    ctx = json.loads(Path(a.context).read_text(encoding="utf-8"))
    try:
        if a.coverage:
            cov = impact.coverage(ctx)
            for kind, v in cov["per_kind"].items():
                print(f"{kind}: {v['count']} eleman, {len(v['isolated'])} bagsiz" + (f" ({', '.join(v['isolated'][:5])})" if v["isolated"] else ""))
            print("Kapsam disi ust seviye alanlar: " + ", ".join(cov["out_of_scope"]))
            for w in cov["warnings"]:
                print("UYARI:", w)
        if a.before:
            before = json.loads(Path(a.before).read_text(encoding="utf-8"))
            rep = impact.diff_report(before, ctx, a.depth)
            d = rep.diff
            print(f"Fark: eklenen {len(d['added'])}, degisen {len(d['changed'])}, silinen {len(d['removed'])}")
            if d["other"]:
                print("Etki alani HESAPLANMAYAN (kat listesi disi) degisiklikler: " + ", ".join(d["other"]))
            if rep.after:
                print("--- SONRAKI context'te etkilenen ---")
                print("\n".join(impact.format_report(rep.after)))
            if rep.before:
                print("--- ONCEKI context'te (silinen/degisen) komsuluklar ---")
                print("\n".join(impact.format_report(rep.before)))
        elif a.touch:
            nodes = []
            for t in a.touch:
                parts = t.split(":")
                if len(parts) != 3:
                    print(f"--touch kat:tur:id biciminde olmali: {t}", file=sys.stderr)
                    return 2
                nodes.append(tuple(parts))
            print("\n".join(impact.format_report(impact.blast_radius(ctx, nodes, a.depth))))
        elif not a.coverage:
            ap.print_usage()
            return 2
    except impact.ImpactError as exc:
        print(f"HATA: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
