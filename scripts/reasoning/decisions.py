"""Tasarim karari kaydi (DEV-065): `context.json` ust seviye `design_decisions[]`, kanita bagli kabul.

Bir bulgunun "bilincli goz ardi" edilmesi bir KARAR'dir ve gerekcesiyle birlikte projede yasar (proje kopyalanirsa
kararlar da gider). Kabul KANITA baglidir: bulgunun olcumu sonradan DEGISIRSE (iyilesme dahil, v1) kabul duser, bulgu
yeniden sunulur ve operator 'once -> simdi' sayilarini soyler. Eski kabul, degisen bir sorunu ortmez.

Bu dosya SAF fonksiyonlardir (dosya yazmaz); yazim `scripts/reasoning_dialogue.py decide` uzerindendir, boylece bir dil modeli
kaydi ELLE yazmaz. Kayit `context.json`a girer ama bir cizim modulu degildir: reasoning cekirdegi yalnizca bu alani okur.
Bulgu anahtari rakamsizlastirilmis mesaj ozetini icerir (`findings.make_key`): mesaj TURU degisirse anahtar degisir ve
kabul sessizce DEGIL, bulgu yeniden gorunerek duser (guvenli yon).
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

from .explain import ExplainError, NUMBER_RE, _format_number
from .model import Finding

ID_RE = re.compile(r"^[A-Za-z0-9_.\-]+$")
HASH_LEN = 16


def evidence_snapshot(finding: Finding) -> dict:
    """Bulgunun OLCULEN sayilarinin anlik goruntusu: `Finding.evidence` sayilari + mesajdaki sayilar (m1, m2, ...)."""
    snap: dict = {}
    for k in sorted(finding.evidence):
        v = finding.evidence[k]
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            snap[k] = float(v)
    for i, tok in enumerate(NUMBER_RE.findall(finding.message), 1):
        snap[f"m{i}"] = float(tok.replace(",", "."))
    return snap


def evidence_hash(key: str, snapshot: dict) -> str:
    payload = json.dumps({"key": key, "snapshot": {k: round(v, 6) for k, v in sorted(snapshot.items())}},
                         sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:HASH_LEN]


def make_decision(decision_id: str, rev: int, ts: str, reason: str, findings: list[Finding], devredilmis: bool = False,
                  supersedes: str | None = None) -> dict:
    """Karar kaydi uretir. Bos gerekce ya da bulgusuz kayit REDDEDILIR."""
    if not str(reason).strip():
        raise ExplainError("gerekce bos olamaz (karar kaydi gerekce olmadan yazilmaz)")
    if not findings:
        raise ExplainError("kapsanan bulgu yok")
    if not ID_RE.match(decision_id):
        raise ExplainError(f"karar kimligi gecersiz: {decision_id!r}")
    covers = []
    for f in findings:
        snap = evidence_snapshot(f)
        covers.append({"finding_key": f.key, "evidence_hash": evidence_hash(f.key, snap), "evidence": snap})
    rec = {"id": decision_id, "rev": rev, "ts": ts, "reason": reason.strip(), "covers": covers, "devredilmis": bool(devredilmis)}
    if supersedes:
        rec["supersedes"] = supersedes
    return rec


def check_decisions(context: dict) -> list[str]:
    """validate.py HATALARI (veri kalitesi; bulgunun kendisi yine UYARI). Alan yoksa bos liste (opt-in)."""
    errors: list[str] = []
    seen: set[str] = set()
    for i, d in enumerate(context.get("design_decisions", [])):
        where = f"design_decisions[{i}]" + (f" ('{d.get('id')}')" if isinstance(d, dict) and d.get("id") else "")
        if not str(d.get("reason", "")).strip():
            errors.append(f"{where}: gerekce (reason) bos olamaz - bilincli goz ardi gerekcesiz kaydedilmez.")
        did = d.get("id")
        if did in seen:
            errors.append(f"{where}: karar kimligi yinelenmis.")
        seen.add(did)
        if did is not None and not ID_RE.match(str(did)):
            errors.append(f"{where}: karar kimligi gecersiz karakter iceriyor.")
        covers = d.get("covers") or []
        if not covers:
            errors.append(f"{where}: covers bos - karar en az bir bulgu kapsamali.")
        keys = [c.get("finding_key") for c in covers]
        if len(keys) != len(set(keys)):
            errors.append(f"{where}: ayni bulgu anahtari covers icinde birden fazla.")
        for c in covers:
            if not re.fullmatch(r"[0-9a-f]{%d}" % HASH_LEN, str(c.get("evidence_hash", ""))):
                errors.append(f"{where}: evidence_hash {HASH_LEN} haneli onaltilik olmali ({c.get('finding_key')!r}).")
    for d in context.get("design_decisions", []):
        sup = d.get("supersedes")
        if sup and sup not in seen:
            errors.append(f"design_decisions '{d.get('id')}': supersedes '{sup}' diye bir karar yok.")
    return errors


@dataclass(frozen=True)
class Reopened:
    """Kabul DUSMUS bulgu: kararin kimligi/gerekcesi + 'once -> simdi' sayilari."""
    decision_id: str
    reason: str
    changed: tuple[tuple[str, float, float | None], ...]   # (anahtar, once, simdi)


def evaluate(findings: list[Finding], decisions: list[dict]) -> dict:
    """{bulgu_anahtari: ('kabul', karar_id) | ('dustu', Reopened)}. Yalniz bir karar tarafindan kapsanan bulgular listelenir.
    Ayni anahtari kapsayan birden fazla kararda SON kayit gecerlidir (ekleme-yalnizlik: yeni kayit eskiyi ezer)."""
    latest: dict[str, tuple[dict, dict]] = {}
    for d in decisions:
        for c in d.get("covers", []):
            latest[c["finding_key"]] = (d, c)
    out: dict = {}
    for f in findings:
        if f.key not in latest:
            continue
        d, c = latest[f.key]
        snap = evidence_snapshot(f)
        if evidence_hash(f.key, snap) == c["evidence_hash"]:
            out[f.key] = ("kabul", d["id"])
        else:
            before = c.get("evidence", {})
            changed = tuple((k, before[k], snap.get(k)) for k in sorted(set(before) | set(snap))
                            if before.get(k) != snap.get(k) and k in before)
            out[f.key] = ("dustu", Reopened(d["id"], d["reason"], changed))
    return out


def decision_numbers(decisions: list[dict]) -> set[str]:
    """Kullanilabilir sayilar: kararlardaki anlik goruntu degerleri + kullanicinin kendi gerekce metnindeki sayilar."""
    out: set[str] = set()
    for d in decisions:
        out |= {t.replace(",", ".") for t in NUMBER_RE.findall(d.get("reason", ""))}
        for c in d.get("covers", []):
            for v in c.get("evidence", {}).values():
                out.add(_format_number(v))
                out.add(f"{v:.1f}")
    return out
