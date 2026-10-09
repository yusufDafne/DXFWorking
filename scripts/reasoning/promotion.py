"""Asgari terfi olceri (DEV-060): bir vechenin 'her yerde otmesi' / 'hic otmemesi' bilgisi. KAPI DEGIL, rapor.

Sayma birimi: tekillestirilmis uygun OZNE (ozdes katlar BIR sayilir - cagiran tekillestirir).
Olculemeyen oznenin sonucu None'dir: paydadan CIKAR ve ayri raporlanir, %0 sayilmaz.
"""
from __future__ import annotations

from dataclasses import dataclass

WEAK_EVIDENCE_N = 10  # yalniz BILGI (v1 pratik varsayilan): bundan az ozne 'kanit zayif' diye yazilir, kapi degildir


@dataclass(frozen=True)
class TriggerReport:
    facet_id: str
    eligible: int
    fired: int
    unmeasurable: int
    rate: float | None
    degenerate: bool       # hep otuyor (rate==1) ya da hic otmuyor (rate==0) -> bilgi tasimaz
    weak_evidence: bool

    def text(self) -> str:
        if self.rate is None:
            return f"{self.facet_id}: olculebilir ozne yok ({self.unmeasurable} olculemedi)"
        tag = "DEJENERE (bilgi tasimiyor)" if self.degenerate else "dejenere degil"
        weak = f"; kanit zayif (N={self.eligible})" if self.weak_evidence else f"; N={self.eligible}"
        return (f"{self.facet_id}: {self.fired}/{self.eligible} ozne tetikledi, {tag}{weak}"
                f"{f', {self.unmeasurable} olculemedi' if self.unmeasurable else ''}")


def trigger_report(facet_id: str, results: dict) -> TriggerReport:
    """results: {ozne_kimligi: True|False|None}  (None = olculemedi)."""
    measured = [v for v in results.values() if v is not None]
    unmeasurable = len(results) - len(measured)
    if not measured:
        return TriggerReport(facet_id, 0, 0, unmeasurable, None, False, True)
    fired = sum(1 for v in measured if v)
    rate = fired / len(measured)
    return TriggerReport(facet_id, len(measured), fired, unmeasurable, rate,
                         rate in (0.0, 1.0), len(measured) < WEAK_EVIDENCE_N)
