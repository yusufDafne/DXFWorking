"""reasoning modulu (DEV-060): mimari muhakeme CEKIRDEGI. Plan: docs/development/ARCHITECTURAL_REASONING_PLAN.md

Mercek (soru ailesi) -> veche (olculebilir alt orneklem) -> bulgu (kararli anahtar, siddet 0-1 ya da
'unscored', kanit). Cekirdek BILGI tasimaz ve hicbir cizim modulunu import etmez (collision/ ile ayni
ters bagimlilik); bilgi `reasoning/lenses/*.py` ve `<modul>/reasoning.py` dosyalarinda yasar ve DOSYA
YOLUYLA yuklenir. Import aninda dogrulama/yan etki YOKTUR. Politika: yalniz UYARI (FORBID yok).

DEV-060 kapsami: model, kayit, bulgu anahtari/farki/kumeleme, validate stdout adaptoru, kapsam raporu,
asgari terfi olcer, vaka kosucusu, doc_check kapilari #10-#12, #14, #15. DEGIL: aciklama motoru, rakam lint'i,
sunum kuyrugu (-> DEV-064); mercek paketleri (-> DEV-061+).
"""
from __future__ import annotations

from .adapters import adapt_warnings, parse_validate_output
from .cases import list_cases, load_case, run_case
from .coverage import CoverageEntry, CoverageReport, build_coverage
from .findings import (diff_findings, group_across_floors, make_key, message_signature, quoted_ids,
                       severity_band, severity_from_curve)
from .decisions import (Reopened, check_decisions, decision_numbers, evaluate, evidence_hash, evidence_snapshot,
                        make_decision)
from .explain import (ExplainError, allowed_numbers_for, Narrative, Topic, append_dialogue, coverage_sentence, effective_mode,
                      is_presentable, lint_template, match_smells, narrate, read_dialogue, render,
                      select_topics, validate_record, verify_numbers)
from .model import (CheckAdapter, Facet, Finding, Lens, Plain, Profile, Provenance, Remedy, Smell, Tension,
                    Thresholds, missing_for_status)
from .promotion import TriggerReport, trigger_report
from .registry import (REASONING_EXEMPT, REASONING_PENDING, REASONING_PROVIDERS, Registry,
                       load_registry, validate_registry)

# Bu paketin context sozlesmesi: kapsam raporu veche bildirimlerindeki yollara bakar; ayrica YALNIZ ust seviye
# `design_decisions[]` okunur (DEV-065); Finding/Facet DONUS SEKLI degisirse artar.
CONTRACT_VERSION = "1.1"  # 1.1 (DEV-065): context.json ust seviye `design_decisions[]` OKUR

__all__ = [
    "CONTRACT_VERSION", "CheckAdapter", "Facet", "Finding", "Lens", "Plain", "Profile", "Provenance",
    "Smell", "Tension", "Thresholds", "missing_for_status", "adapt_warnings", "parse_validate_output",
    "list_cases", "load_case", "run_case", "CoverageEntry", "CoverageReport", "build_coverage",
    "diff_findings", "group_across_floors", "make_key", "message_signature", "quoted_ids",
    "severity_band", "severity_from_curve", "TriggerReport", "trigger_report", "REASONING_EXEMPT",
    "REASONING_PENDING", "REASONING_PROVIDERS", "Registry", "load_registry", "validate_registry",
    "Reopened", "check_decisions", "decision_numbers", "evaluate", "evidence_hash", "evidence_snapshot", "make_decision",
    "ExplainError", "allowed_numbers_for", "Narrative", "Topic", "Remedy", "append_dialogue", "coverage_sentence", "effective_mode",
    "is_presentable", "lint_template", "match_smells", "narrate", "read_dialogue", "render", "select_topics",
    "validate_record", "verify_numbers",
]
