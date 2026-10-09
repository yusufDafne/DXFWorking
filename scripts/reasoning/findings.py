"""Bulgu anahtari, siddet egrisi, regresyon farki ve kat-bagimsiz kumeleme (DEV-060)."""
from __future__ import annotations

import hashlib
import re

from .model import Finding, Thresholds

_NUM = re.compile(r"-?\d+(?:[.,]\d+)?")
_QUOTED = re.compile(r"'([^']+)'")
_FLOOR_PREFIX = re.compile(r"^\[[^\]]+\]\s*")


def message_signature(message: str) -> str:
    """Rakamlari '#' yapilmis, kat oneki atilmis mesajin kisa ozeti. Rakam degisikligi (kismi cozum,
    esik degisikligi) anahtari BOZMAZ; mesaj TURU degisirse ayrisir."""
    text = _NUM.sub("#", _FLOOR_PREFIX.sub("", message))
    text = re.sub(r"\s+", " ", text).strip().lower()
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:8]


def quoted_ids(message: str) -> tuple[str, ...]:
    """Mesajda tirnak icindeki eleman adlari (sirali, tekil)."""
    return tuple(sorted(set(_QUOTED.findall(message))))


def make_key(facet_id: str, floor_id: str | None, elements: tuple[str, ...], message: str) -> str:
    return f"{facet_id}|{floor_id or '*'}|{','.join(elements)}|{message_signature(message)}"


def severity_from_curve(measured: float, th: Thresholds | None) -> tuple[float | None, str]:
    """Esikten sapmanin warn_at->severe_at dogrusal rampasi (0..1). severe_at yoksa siddet HESAPLANAMAZ:
    (None, 'unscored') - sayi uydurulmaz."""
    if th is None or th.severe_at is None or th.severe_at == th.warn_at:
        return None, "unscored"
    t = (measured - th.warn_at) / (th.severe_at - th.warn_at)
    return max(0.0, min(1.0, t)), "curve"


def severity_band(severity: float | None) -> str:
    """Anlatim bandi (plan §3.2): <0.25 bilgi, <=0.6 dikkat, >0.6 ciddi; None -> 'olculmedi'."""
    if severity is None:
        return "olculmedi"
    return "bilgi" if severity < 0.25 else ("dikkat" if severity <= 0.6 else "ciddi")


def diff_findings(before: list[Finding], after: list[Finding]) -> dict[str, list[Finding]]:
    """Regresyon farki (anahtar bazli): yeni / cozulen / degismeyen."""
    b = {f.key: f for f in before}
    a = {f.key: f for f in after}
    return {
        "new": [a[k] for k in a if k not in b],
        "resolved": [b[k] for k in b if k not in a],
        "unchanged": [a[k] for k in a if k in b],
    }


def group_across_floors(findings: list[Finding]) -> list[tuple[str, list[Finding]]]:
    """Kat-bagimsiz kimlige gore gruplar (ozdes katlardaki ayni bulgu tek konu); ilk gorulme sirasi korunur."""
    groups: dict[str, list[Finding]] = {}
    for f in findings:
        groups.setdefault(f.group_key, []).append(f)
    return list(groups.items())
