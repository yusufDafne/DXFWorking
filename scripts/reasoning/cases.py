"""Vaka bicimi ve kosucusu (DEV-060). `golden/`den BILINCLI ayri: vaka = kat parcasi + beklenen bulgu anahtarlari.

Dizin: scripts/reasoning/cases/<ad>/case.json  {"id","facet","role":"ihlal|temiz","origin","floor":{rooms,walls,openings,...}}
                                     expected_findings.json {"expect_keys":[...],"expect_absent":[...]}
Test zamaninda git CAGRILMAZ; gecmisten alinan parcalar 'origin' alaniyla (git <hash>:context.json) donmus JSON'dur.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from .model import Finding

CASES_ROOT = Path(__file__).resolve().parent / "cases"
ROLES = ("ihlal", "temiz")


def list_cases(root: Path | None = None) -> list[Path]:
    base = root or CASES_ROOT
    return sorted(p for p in base.iterdir() if p.is_dir() and (p / "case.json").exists()) if base.is_dir() else []


def load_case(path: Path) -> tuple[dict, dict]:
    case = json.loads((path / "case.json").read_text(encoding="utf-8"))
    expected = json.loads((path / "expected_findings.json").read_text(encoding="utf-8"))
    return case, expected


def run_case(path: Path, check: Callable[[dict], list[Finding]]) -> list[str]:
    """Hata listesi: ihlal vakasi beklenen anahtari VERMELI, temiz kardesi VERMEMELI."""
    case, expected = load_case(path)
    if case.get("role") not in ROLES:
        return [f"{path.name}: role {case.get('role')!r} gecersiz"]
    keys = {f.key for f in check(case["floor"])}
    errors = [f"{path.name}: beklenen bulgu yok: {k}" for k in expected.get("expect_keys", []) if k not in keys]
    errors += [f"{path.name}: OLMAMASI gereken bulgu var: {k}" for k in expected.get("expect_absent", []) if k in keys]
    if case["role"] == "ihlal" and not expected.get("expect_keys"):
        errors.append(f"{path.name}: ihlal vakasi expect_keys bos")
    if case["role"] == "temiz" and keys:
        errors.append(f"{path.name}: temiz vaka bulgu uretti: {sorted(keys)}")
    return errors
