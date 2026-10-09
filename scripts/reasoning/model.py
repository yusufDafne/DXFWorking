"""Muhakeme bilgi modeli (DEV-060): saf veri tipleri. Bilgi ICERMEZ, cizim modulu import etmez."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

STATUSES = ("idea", "draft", "shadow", "active")
CONFIDENCES = ("kesin", "yaygin", "tercih")
KINDS = ("kullanici_karari", "yonetmelik", "mimari_pratik", "olcum")
SCOPES = ("floor", "building")
# kaynaksiz "kesin" iddiasini yakalamak icin (standards'in isaretiyle ayni)
PLACEHOLDER_SOURCES = ("", "v1 pratik varsayilan", "v1 pratik varsayılan")
FACET_ID_RE = re.compile(r"^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$")
LENS_ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")


@dataclass(frozen=True)
class Provenance:
    kind: str
    confidence: str
    source: str = ""
    reviewed: str = ""  # ISO tarih, bos olabilir


@dataclass(frozen=True)
class Thresholds:
    warn_at: float
    severe_at: float | None = None  # None: siddet HESAPLANAMAZ (uydurulmaz)
    unit: str = ""
    source: str = ""


@dataclass(frozen=True)
class Plain:
    problem: str = ""
    consequence: str = ""
    numbers: tuple[str, ...] = ()


@dataclass(frozen=True)
class CheckAdapter:
    """Mevcut bir check_* fonksiyonunu sarmak icin bildirim (v1: veche <-> check 1:1)."""
    ref: str                       # "architect.rules:check_entry_sightlines"
    inputs: tuple[str, ...] = ()   # fonksiyonun konumsal parametre adlari
    scope: str = "floor"
    channel: str = "warnings"      # YALNIZ uyari kanali; HATA kanali sarilmaz


@dataclass(frozen=True)
class Facet:
    id: str
    lens: str
    title_tr: str
    principle_tr: str
    why_tr: str
    status: str = "idea"
    provenance: Provenance | None = None
    measure_ref: str = ""
    check_ref: str = ""
    adapter: CheckAdapter | None = None
    thresholds: Thresholds | None = None
    needs: tuple[str, ...] = ()        # "rooms[].unit_id", "meta.north_angle"
    applies_when: str = ""             # kapali sozcuk: "", "has_room_type:salon|yatak_odasi"
    tensions: tuple[str, ...] = ()
    remedies: tuple[str, ...] = ()
    legit_overrides_tr: tuple[str, ...] = ()
    plain: Plain | None = None
    cases: tuple[str, ...] = ()
    legacy: bool = False               # validate.py'nin zaten cagirdigi kural (terfi kapisindan muaf)
    subject_kind: str = ""             # "unit" | "floor" | "building" (terfi olcerinin sayma birimi)
    needs_note_tr: tuple = ()          # ((need_yolu, "kosamadi nedeni"), ...): kapsam raporunda yol yerine duz dil neden


@dataclass(frozen=True)
class Lens:
    id: str
    title_tr: str
    philosophy_tr: str


@dataclass(frozen=True)
class Remedy:
    """Adli cozum yolu (DEV-064): metin RAKAMSIZDIR; bedel yalniz nitel soylenir (sayi olcumden gelir)."""
    id: str
    text_tr: str
    cost_tr: str = ""


@dataclass(frozen=True)
class Smell:
    id: str
    title_tr: str
    facet_ids: tuple[str, ...]
    root_cause_tr: str
    remedies: tuple[str, ...] = ()


@dataclass(frozen=True)
class Tension:
    a: str
    b: str
    note_tr: str


@dataclass(frozen=True)
class Profile:
    id: str
    title_tr: str
    weights: dict = field(default_factory=dict)
    disabled_facets: tuple[str, ...] = ()


@dataclass(frozen=True)
class Finding:
    key: str
    facet_id: str
    floor_id: str | None
    message: str
    elements: tuple[str, ...] = ()
    severity: float | None = None      # None = "unscored"; sayi uydurulmaz
    basis: str = "unscored"
    evidence: dict = field(default_factory=dict)

    @property
    def group_key(self) -> str:
        """Kat-bagimsiz kimlik (ozdes katlardaki ayni bulgu tek konu)."""
        parts = self.key.split("|")
        parts[1] = "*"
        return "|".join(parts)


def missing_for_status(facet: Facet) -> list[str]:
    """Durum basamagina gore eksik zorunlu alanlar (plan §7.3)."""
    miss: list[str] = []
    rank = STATUSES.index(facet.status)
    if rank >= 1:  # draft+
        if facet.provenance is None:
            miss.append("provenance")
        if not facet.needs and not facet.applies_when:
            miss.append("needs/applies_when")
    if rank >= 2:  # shadow+
        if not (facet.check_ref or facet.adapter):
            miss.append("check_ref/adapter")
    if rank >= 3:  # active
        if facet.plain is None or not facet.plain.problem or not facet.plain.consequence:
            miss.append("plain.problem/consequence")
        if facet.thresholds is None and not facet.legacy:
            miss.append("thresholds")
        if not facet.legacy and not facet.remedies:
            miss.append("remedies")
    return miss
