"""Asgari terfi olceri (DEV-060): bir vechenin 'her yerde otmesi' / 'hic otmemesi' bilgisi. KAPI DEGIL, rapor.

Sayma birimi: tekillestirilmis uygun OZNE (ozdes katlar BIR sayilir - cagiran tekillestirir).
Olculemeyen oznenin sonucu None'dir: paydadan CIKAR ve ayri raporlanir, %0 sayilmaz.
"""
from __future__ import annotations

from dataclasses import dataclass

from .model import PLACEHOLDER_SOURCES  # noqa: F401

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


# ---------------------------------------------------------------- terfi politikasi (DEV-066)
from dataclasses import dataclass as _dc  # noqa: E402


@_dc(frozen=True)
class ReadinessItem:
    key: str
    ok: bool
    detail: str
    pending_user: bool = False   # kullanici karari: arac TAMAMLAYAMAZ


def promotion_readiness(facet, report: TriggerReport | None, case_roles: set[str]) -> list[ReadinessItem]:
    """`shadow -> active` kontrol listesi. HICBIR madde otomatik terfi ETTIRMEZ: son madde (acik kullanici karari + HD kaydi) daima beklemededir.
    Sayisal bir ORNEKLEM KAPISI YOKTUR: arac N'yi yazar, kanit zayifsa SOYLER (kullanici karari 2026-10-09)."""
    items: list[ReadinessItem] = []
    items.append(ReadinessItem("vaka", {"ihlal", "temiz"} <= case_roles,
                               "ihlal + temiz vaka var" if {"ihlal", "temiz"} <= case_roles
                               else f"eksik vaka rolu: {sorted({'ihlal', 'temiz'} - case_roles)}"))
    if not facet.measure_ref:
        items.append(ReadinessItem("tetik_orani", False, "bu veche icin ozne olcumu (measure_ref) tanimli degil: tetik orani hesaplanamaz (ayirt edicilik KANITLANAMAZ)"))
    elif report is None or report.rate is None:
        items.append(ReadinessItem("tetik_orani", False, "olculebilir ozne yok (veri eksik ya da kat ilgisiz): tetik orani hesaplanamadi (ayirt edicilik KANITLANAMAZ)"))
    elif report.degenerate:
        items.append(ReadinessItem("tetik_orani", False, f"DEJENERE ({report.fired}/{report.eligible}): "
                                   + ("her ozne tetikliyor" if report.rate == 1.0 else "hic ozne tetiklemiyor")
                                   + " - bilgi tasimiyor, `shadow`da kalir; ayirici eklenmeli (ornek: duvar turu)"))
    else:
        weak = f"; kanit ZAYIF (N={report.eligible})" if report.weak_evidence else f"; N={report.eligible}"
        items.append(ReadinessItem("tetik_orani", True, f"{report.fired}/{report.eligible} ozne tetikledi, dejenere degil{weak}"
                                   + (f"; {report.unmeasurable} olculemedi (paydadan cikarildi)" if report.unmeasurable else "")))
    plain_ok = facet.plain is not None and bool(facet.plain.problem) and bool(facet.plain.consequence)
    items.append(ReadinessItem("anlatim", plain_ok, "plain.problem/consequence var" if plain_ok else "anlatim sablonu (plain) eksik"))
    items.append(ReadinessItem("cozum_yolu", bool(facet.remedies), "kayitli cozum yolu var" if facet.remedies else "kayitli cozum yolu (remedies) yok"))
    items.append(ReadinessItem("esik", facet.thresholds is not None,
                               "esik kaydi var" if facet.thresholds is not None else "esik (thresholds) kaydi yok"))
    src = (facet.provenance.source or "").strip() if facet.provenance else ""
    items.append(ReadinessItem("kaynak", bool(facet.provenance),
                               f"guven={facet.provenance.confidence}, kaynak={'var' if src and src.lower() not in PLACEHOLDER_SOURCES_LOWER else 'YOK (tercih/yaygin olarak sunulur, yonetmelik gibi degil)'}"
                               if facet.provenance else "provenance yok"))
    items.append(ReadinessItem("kullanici_karari", False, "ACIK kullanici karari + DEVELOPMENT_HISTORY kaydi gerekir (arac terfi ettiremez)", pending_user=True))
    return items


PLACEHOLDER_SOURCES_LOWER = ("", "v1 pratik varsayilan", "v1 pratik varsayılan", "mimari pratik; kaynak yok")


def promotion_snippet(facet_id: str, report: TriggerReport, hd_ref: str = "HD-0??", decided_on: str = "") -> str:
    """Kullanici karar verdikten SONRA lens paketine yapistirilacak kayit taslagi (arac KENDISI yazmaz)."""
    return (f"# {facet_id}: kullanici kararindan sonra, status='active' ile birlikte\n"
            f"promotion=Promotion(hd_ref=\"{hd_ref}\", decided_on=\"{decided_on or 'YYYY-AA-GG'}\", decided_by=\"kullanici\", "
            f"eligible={report.eligible}, fired={report.fired}, unmeasurable={report.unmeasurable})")


def stale_review_list(facets, today, max_age_days: int) -> list[tuple[str, str]]:
    """`provenance.reviewed` bayat / hic doldurulmamis veche listesi (idea haric). max_age_days bir POLITIKA parametresidir."""
    import datetime
    out = []
    for f in facets:
        if f.status == "idea" or f.provenance is None or f.legacy:
            continue
        if not f.provenance.reviewed:
            out.append((f.id, "hic gozden gecirilmemis (provenance.reviewed bos)"))
            continue
        try:
            age = (today - datetime.date.fromisoformat(f.provenance.reviewed)).days
        except ValueError:
            out.append((f.id, f"provenance.reviewed gecerli tarih degil: {f.provenance.reviewed!r}"))
            continue
        if age > max_age_days:
            out.append((f.id, f"{age} gun once gozden gecirilmis"))
    return out


def per_unit_topic_counts(topics, room_units: dict) -> dict:
    """Birim basina sunulan konu sayisi (yanlis-pozitif butcesi icin). Eleman -> birim `room_units`ten (rooms[].unit_id); bulunamazsa 'birimsiz'."""
    counts: dict = {}
    for t in topics:
        units = {room_units.get(e) for e in t.elements if e in room_units} or {None}
        for u in units:
            counts[u or "birimsiz"] = counts.get(u or "birimsiz", 0) + 1
    return counts
