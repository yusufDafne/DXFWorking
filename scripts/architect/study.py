"""Etut asamasi (DEV-039): oda programi <-> alan sigma + kaba bolge (zone)
atamasi.

`DEV-038`'in "oda programi mevcut alana sigiyor mu" sorusu buraya
ABSORBE EDILDI (kullanici onayi, 2026-09-28) - zonlama, sigmayan bir
programi zonlamaya CALISMAZ; bu yuzden sigma kontrolu zonlamanin ILK
adimidir. Bu dosya `validate.py` akisinin PARCASI DEGILDIR (odalar zaten
URETILMISSE bu kontrolun bir anlami kalmaz, `standards::
check_room_proportions` zaten uretilmis odayi denetler) - bu, bir ajanin
`generate_circulation_core` gibi bir ureticiyi CAGIRMADAN ONCE
sorabilecegi bir ON-KONTROLDUR.

v1 KASITLI OLARAK basit tutulur (DEV-038'in kendi "Fikir 1" siniriyla
AYNI disiplin): TEK SATIRLIK (1D) bir raf yerlesimi - odalar soldan saga,
her biri en az kendi `standards.STANDARDS[...].min_short_edge_mm` kadar
genislik alir, kalan bosluk odalar arasinda ESIT dagitilir. Karmasik 2D
bin-packing/optimizasyon YAPILMAZ - `stairs`/`ceiling` ile AYNI "net bir
v1 sinir" disiplini.
"""
from __future__ import annotations

from dataclasses import dataclass

try:
    from ..standards import STANDARDS
except ImportError:
    from standards import STANDARDS


@dataclass(frozen=True)
class FeasibilityReport:
    """`check_fits`in sonucu. `unknown_types`, `STANDARDS`ta tanimsiz VEYA
    `min_short_edge_mm` tasimayan bir tipi ISARETLER - bu tur bir tip sigma
    HESABINA KATILMAZ (check_room_types'in ERROR sinifiYLA KARISTIRILMAZ,
    bu fonksiyon salt-okunur bir on-kontroldur)."""

    fits: bool
    available_mm: float
    required_mm: float
    margin_mm: float
    unknown_types: tuple[str, ...] = ()


def check_fits(available_width_mm: float, room_types: list[str]) -> FeasibilityReport:
    """DEV-038'in 1D sigma testi: `room_types`teki HER tipin asgari kisa
    kenarini TOPLAYIP `available_width_mm` ile karsilastirir."""
    required = 0.0
    unknown: list[str] = []
    for room_type in room_types:
        standard = STANDARDS.get(room_type)
        if standard is None or standard.min_short_edge_mm is None:
            unknown.append(room_type)
            continue
        required += standard.min_short_edge_mm
    margin = available_width_mm - required
    return FeasibilityReport(
        fits=margin >= 0 and not unknown,
        available_mm=available_width_mm,
        required_mm=required,
        margin_mm=margin,
        unknown_types=tuple(unknown),
    )


@dataclass(frozen=True)
class ZoneAssignment:
    room_type: str
    x0: float
    x1: float
    y0: float
    y1: float

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def depth(self) -> float:
        return self.y1 - self.y0


@dataclass(frozen=True)
class ZoningPlan:
    """`fits=False` ise `zones` BOS bir demettir - architect kendisi bir
    istisna FIRLATMAZ (`stairs::StairFitError` deseninden FARKLI olarak
    bu bir ON-KONTROLDUR, cagiran taraf `fits` alanini yorumlar)."""

    fits: bool
    zones: tuple[ZoneAssignment, ...]
    feasibility: FeasibilityReport


def resolve_unit_zoning(
    available_width_mm: float, available_depth_mm: float,
    room_types: list[str], *, x0: float = 0.0, y0: float = 0.0,
) -> ZoningPlan:
    """Sigiyorsa her odaya SOLDAN SAGA, kendi asgari kisa kenari + esit
    dagitilan bosluk kadar bir X araligi verilir; derinlik (Y) TUM odalar
    icin `available_depth_mm`dir (tek satirlik yerlesim - bkz. modul
    dokstring). Sigmiyorsa (veya bilinmeyen bir tip varsa) `fits=False`,
    `zones=()` doner."""
    feasibility = check_fits(available_width_mm, room_types)
    if not feasibility.fits:
        return ZoningPlan(fits=False, zones=(), feasibility=feasibility)

    widths = [STANDARDS[rt].min_short_edge_mm for rt in room_types]
    slack = feasibility.margin_mm / len(room_types)
    zones: list[ZoneAssignment] = []
    cursor = x0
    for room_type, width in zip(room_types, widths):
        zone_width = width + slack
        zones.append(ZoneAssignment(
            room_type=room_type, x0=cursor, x1=cursor + zone_width,
            y0=y0, y1=y0 + available_depth_mm,
        ))
        cursor += zone_width
    return ZoningPlan(fits=True, zones=tuple(zones), feasibility=feasibility)


__all__ = [
    "FeasibilityReport", "check_fits", "ZoneAssignment", "ZoningPlan",
    "resolve_unit_zoning",
]
