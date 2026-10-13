"""Soguk baslangic sinavi (DEV-071) icin MUHURLU PAKET uretici/temizleyici. Sistem GELISTIRME aracidir (proje verisi yazmaz).

`python scripts/review_exam.py build [--out DIR]` : her vaka icin <DIR>/<vaka>/ altinda, sinanan ajanin gorecegi KOPYAYI kurar:
    kok CLAUDE.md, muhakeme plani, scripts/ (araclar kosabilsin diye; `reasoning/cases` = beklenen-bulgu cevap anahtari ve `golden/` HARIC),
    schema/, docs/agents/PROJECT_OPERATOR_AGENT.md ve vakanin context.json'i. Cevap anahtari (rubrik) pakette YOKTUR.
`python scripts/review_exam.py clean [--out DIR]` : paketi siler (sinav bitince).
`python scripts/review_exam.py recipe` : cikarma tarifini (commit + vaka + komut) yazar - COMMIT'LENEN TEK sey budur.

Vakalar (context kaynaklari): `eski_uC` = git `727405f`teki context.json (rev-22 oncesi uC: penceresiz uC_oda + sandvic banyo; bu commit gecmiste GERCEKTEN vardi),
`guncel` = calisma agacindaki context.json, `kuzey30` = guncel context + meta.north_angle=30 (yonelim veçhesi kosar).
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = ROOT / ".exam_sealed"
HISTORICAL_COMMIT = "727405f"
CASES = ("eski_uC", "guncel", "kuzey30")
EXCLUDE_DIRS = {"__pycache__", "cases", "golden", ".git"}      # cases = beklenen-bulgu cevap anahtari


def case_context(case: str) -> dict:
    if case == "eski_uC":
        out = subprocess.run(["git", "show", f"{HISTORICAL_COMMIT}:context.json"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
        return json.loads(out)
    ctx = json.loads((ROOT / "context.json").read_text(encoding="utf-8"))
    if case == "kuzey30":
        ctx["meta"]["north_angle"] = 30.0
    elif case != "guncel":
        raise SystemExit(f"bilinmeyen vaka: {case}")
    return ctx


def _copy_scripts(dst: Path) -> None:
    def ignore(_d, names):
        return [n for n in names if n in EXCLUDE_DIRS or n.endswith(".pyc")]
    shutil.copytree(ROOT / "scripts", dst / "scripts", ignore=ignore)


def build(out: Path) -> list[Path]:
    made = []
    for case in CASES:
        d = out / case
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True)
        shutil.copy(ROOT / "CLAUDE.md", d / "CLAUDE.md")
        (d / "docs" / "development").mkdir(parents=True)
        shutil.copy(ROOT / "docs" / "development" / "ARCHITECTURAL_REASONING_PLAN.md", d / "docs" / "development" / "ARCHITECTURAL_REASONING_PLAN.md")
        (d / "docs" / "agents").mkdir(parents=True)
        shutil.copy(ROOT / "docs" / "agents" / "PROJECT_OPERATOR_AGENT.md", d / "docs" / "agents" / "PROJECT_OPERATOR_AGENT.md")
        shutil.copytree(ROOT / "schema", d / "schema")
        _copy_scripts(d)
        (d / "context.json").write_text(json.dumps(case_context(case), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        made.append(d)
    return made


def recipe() -> str:
    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    return (f"belge commit'i: {head} (calisma agaci temiz olmali)\n"
            f"vakalar: eski_uC = git show {HISTORICAL_COMMIT}:context.json | guncel = context.json | kuzey30 = context.json + meta.north_angle=30\n"
            "komut: python scripts/review_exam.py build   (sonra: clean)")


def main(argv=None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    out = DEFAULT_OUT
    if "--out" in args:
        i = args.index("--out")
        out = Path(args[i + 1]).resolve()
        del args[i:i + 2]
    cmd = args[0] if args else "recipe"
    if cmd == "build":
        for d in build(out):
            print(f"paket: {d}")
        return 0
    if cmd == "clean":
        if out.exists():
            shutil.rmtree(out)
        print(f"silindi: {out}")
        return 0
    print(recipe())
    return 0


if __name__ == "__main__":
    sys.exit(main())
