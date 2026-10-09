"""Muhakeme kayit defteri (DEV-060): saglayici/muaf/PENDING kaydi + tembel yukleyici + dogrulama.

Bagimlilik yonu `collision/` ile AYNI: cekirdek hicbir cizim modulunu import ETMEZ; bilgi
(`lenses/*.py`, `<modul>/reasoning.py`) DOSYA YOLUYLA yuklenir ve yalnizca `reasoning.*`
import edebilir (AST ile denetlenir). Import aninda dogrulama/yan etki YOKTUR.
"""
from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path

from .model import (CONFIDENCES, FACET_ID_RE, KINDS, LENS_ID_RE, PLACEHOLDER_SOURCES, SCOPES, STATUSES,
                    Facet, Lens, Profile, Remedy, Smell, Tension, missing_for_status)

ROOT_SCRIPTS = Path(__file__).resolve().parent.parent

# `<modul>/reasoning.py` saglayicilari (register(reg) fonksiyonu tasir). Veche kayitlari lens paketlerindedir.
REASONING_PROVIDERS: tuple[str, ...] = ("architect", "openings", "shafts")  # DEV-061, DEV-062

# Gerekceli muafiyet ("dusunuldu, bu modul olcum/kural vermez") - COLLISION_EXEMPT ile AYNI idiom.
REASONING_EXEMPT: dict[str, str] = {
    "reasoning": "Cekirdegin kendisi; bilgi tasimaz (bilgi lens paketlerinde ve saglayici modullerde yasar).",
    "spatial": "Salt sorgu kutuphanesi (DEV-059); muhakemeye olcum SAGLAYABILIR ama kendi veche/kurali yoktur, "
               "sorgulari tuketen modullerin reasoning.py'si kullanir.",
}

# "Henuz degerlendirilmedi" gecis kaydi (DEV-067 bosaltir). TEK YONLU: kume yalniz kuculur;
# doc_check'teki _PENDING_FROZEN disinda hicbir ad girilemez.
REASONING_PENDING: frozenset[str] = frozenset({
    "axis", "ceiling", "collision", "columns", "dimensions", "elevations", "furniture",
    "importer", "legend", "levels", "northarrow", "pafta", "palette", "rooms", "sections",
    "stairs", "standards", "templates", "typography", "walls",
})


class Registry:
    """Bellek ici kayit; selftest bozuk bir sahte kayit enjekte edebilsin diye parametre olarak gecer."""

    def __init__(self) -> None:
        self.lenses: dict[str, Lens] = {}
        self.facets: dict[str, Facet] = {}
        self.smells: dict[str, Smell] = {}
        self.tensions: list[Tension] = []
        self.profiles: dict[str, Profile] = {}
        self.remedies: dict[str, Remedy] = {}
        self.duplicates: list[str] = []

    def register_lens(self, lens: Lens) -> None:
        if lens.id in self.lenses:
            self.duplicates.append(f"mercek:{lens.id}")
        self.lenses[lens.id] = lens

    def register_facet(self, facet: Facet) -> None:
        if facet.id in self.facets:
            self.duplicates.append(f"veche:{facet.id}")
        self.facets[facet.id] = facet

    def register_smell(self, smell: Smell) -> None:
        self.smells[smell.id] = smell

    def register_tension(self, tension: Tension) -> None:
        self.tensions.append(tension)

    def register_remedy(self, remedy: Remedy) -> None:
        if remedy.id in self.remedies:
            self.duplicates.append(f"cozum:{remedy.id}")
        self.remedies[remedy.id] = remedy

    def register_profile(self, profile: Profile) -> None:
        self.profiles[profile.id] = profile


def validate_registry(reg: Registry) -> list[str]:
    """Kayit tutarliligi (HATA listesi). Bos kayit gecerlidir (hicbir mercek yok)."""
    errors = [f"yinelenen kimlik: {d}" for d in reg.duplicates]
    for lens in reg.lenses.values():
        if not LENS_ID_RE.match(lens.id):
            errors.append(f"mercek kimligi gecersiz: {lens.id!r}")
    for f in reg.facets.values():
        if not FACET_ID_RE.match(f.id):
            errors.append(f"{f.id}: kimlik <mercek>.<kategori>.<ad> bicimine uymuyor")
        elif f.id.split(".")[0] != f.lens:
            errors.append(f"{f.id}: kimligin ilk parcasi mercek ({f.lens!r}) ile ayni olmali")
        if f.lens not in reg.lenses:
            errors.append(f"{f.id}: mercek {f.lens!r} kayitli degil")
        if f.status not in STATUSES:
            errors.append(f"{f.id}: durum {f.status!r} gecersiz")
            continue
        for miss in missing_for_status(f):
            errors.append(f"{f.id}: durum {f.status!r} icin eksik alan: {miss}")
        if f.provenance is not None:
            if f.provenance.kind not in KINDS:
                errors.append(f"{f.id}: provenance.kind {f.provenance.kind!r} gecersiz")
            if f.provenance.confidence not in CONFIDENCES:
                errors.append(f"{f.id}: provenance.confidence {f.provenance.confidence!r} gecersiz")
        if f.adapter is not None and f.adapter.scope not in SCOPES:
            errors.append(f"{f.id}: adapter.scope {f.adapter.scope!r} gecersiz")
        if f.legacy and f.status != "active":
            errors.append(f"{f.id}: legacy bayragi yalniz 'active' veche icin (validate.py'nin zaten cagirdigi kural)")
        for r in f.remedies:
            if r not in reg.remedies:
                errors.append(f"{f.id}: cozum basvurusu {r!r} kayitli degil")
        for t in f.tensions:
            if t not in reg.facets:
                errors.append(f"{f.id}: gerilim basvurusu {t!r} kayitli degil")
    for s in reg.smells.values():
        for fid in s.facet_ids:
            if fid not in reg.facets:
                errors.append(f"koku {s.id}: bilesen veche {fid!r} kayitli degil")
        for r in s.remedies:
            if r not in reg.remedies:
                errors.append(f"koku {s.id}: cozum basvurusu {r!r} kayitli degil")
    for t in reg.tensions:
        for fid in (t.a, t.b):
            if fid not in reg.facets:
                errors.append(f"gerilim: {fid!r} kayitli degil")
    return errors


_ALLOWED_IMPORT_ROOTS = {"reasoning", "__future__", "dataclasses", "typing"}


def _import_violations(path: Path) -> list[str]:
    tree = ast.parse(path.read_bytes().decode("utf-8"))
    bad: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots = [a.name.split(".")[0] for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            roots = [] if node.level else [(node.module or "").split(".")[0]]
            if node.level:
                bad.append(f"{path.name}: goreli import yasak (satir {node.lineno})")
        else:
            continue
        bad += [f"{path.name}: {r!r} import edilemez (yalniz reasoning.*)" for r in roots if r not in _ALLOWED_IMPORT_ROOTS]
    return bad


def provider_files(scripts_root: Path | None = None) -> list[Path]:
    root = scripts_root or ROOT_SCRIPTS
    files = [root / m.split(".")[0] / "reasoning.py" for m in REASONING_PROVIDERS]
    lenses = root / "reasoning" / "lenses"
    if lenses.is_dir():
        files += sorted(p for p in lenses.glob("*.py") if not p.name.startswith("_"))
    return files


def load_registry(scripts_root: Path | None = None) -> tuple[Registry, list[str]]:
    """Saglayici/lens dosyalarini YOLLA yukler (paket __init__i calistirmadan); `register(reg)` cagirir.
    Donus: (kayit, yukleme hatalari)."""
    reg, errors = Registry(), []
    root = str(scripts_root or ROOT_SCRIPTS)
    if root not in sys.path:  # saglayicilar `reasoning.*` import eder
        sys.path.insert(0, root)
    for path in provider_files(scripts_root):
        if not path.exists():
            errors.append(f"saglayici dosyasi yok: {path}")
            continue
        violations = _import_violations(path)
        if violations:
            errors += violations
            continue
        spec = importlib.util.spec_from_file_location(f"_reasoning_provider_{path.parent.name}_{path.stem}", path)
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
            module.register(reg)
        except Exception as exc:  # noqa: BLE001 - yukleme hatasi RAPORLANIR
            errors.append(f"{path}: yuklenemedi: {exc}")
    return reg, errors
