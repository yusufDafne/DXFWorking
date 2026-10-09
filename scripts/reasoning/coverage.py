"""Kapsam raporu (DEV-060): hangi veche KOSTU / KOSAMADI (neden) / UYGULANMAZ. 'Temiz' != 'bakilmadi'."""
from __future__ import annotations

import re
from dataclasses import dataclass

from .registry import Registry

STATE_RAN, STATE_BLOCKED, STATE_NA = "kostu", "kosamadi", "uygulanmaz"


@dataclass(frozen=True)
class CoverageEntry:
    facet_id: str
    floor_id: str | None
    state: str
    reason: str = ""


@dataclass(frozen=True)
class CoverageReport:
    entries: tuple[CoverageEntry, ...]
    lens_count: int
    facet_count: int

    def text(self) -> str:
        if self.lens_count == 0:
            return "Kapsam: HICBIR mercek kayitli degil - muhakeme degerlendirmesi YAPILMADI (bu 'temiz' demek degildir)."
        lines = [f"Kapsam: {self.lens_count} mercek, {self.facet_count} veche."]
        for e in self.entries:
            if e.state != STATE_RAN:
                lines.append(f"  - {e.facet_id} [{e.floor_id or '*'}]: {e.state.upper()} - {e.reason}")
        return "\n".join(lines)


def _count_path(path: str, floor: dict, context: dict) -> tuple[int, int]:
    """(var olan, toplam) - 'meta.x' tek deger; 'rooms[].f' kattaki eleman sayisi uzerinden."""
    if path.startswith("meta."):
        key = path.split(".", 1)[1]
        return (1 if context.get("meta", {}).get(key) is not None else 0), 1
    m = re.match(r"^(\w+)\[\]\.(\w+)$", path)
    if not m:
        return 0, 0
    items = floor.get(m.group(1), [])
    return sum(1 for it in items if it.get(m.group(2)) is not None), len(items)


def _applies(rule: str, floor: dict) -> bool:
    if not rule:
        return True
    kind, _, arg = rule.partition(":")
    if kind == "has_room_type":
        types = set(arg.split("|"))
        return any(r.get("room_type") in types for r in floor.get("rooms", []))
    return True  # bilinmeyen sozcuk: uygulanir sayilir (registry dogrulamasi ayri)


def build_coverage(registry: Registry, context: dict) -> CoverageReport:
    entries: list[CoverageEntry] = []
    for facet in registry.facets.values():
        for floor in context.get("floors", []):
            fid = floor.get("id")
            if not _applies(facet.applies_when, floor):
                entries.append(CoverageEntry(facet.id, fid, STATE_NA, "kat bu veche icin ilgisiz"))
                continue
            absent = []
            for need in facet.needs:
                have, total = _count_path(need, floor, context)
                if have == 0:
                    absent.append(f"{need} hicbir elemanda yok")
            if absent:
                entries.append(CoverageEntry(facet.id, fid, STATE_BLOCKED, "; ".join(absent)))
            else:
                partial = []
                for need in facet.needs:
                    have, total = _count_path(need, floor, context)
                    if total and have < total:
                        partial.append(f"{need} {have}/{total}")
                entries.append(CoverageEntry(facet.id, fid, STATE_RAN, "kismi: " + ", ".join(partial) if partial else ""))
    return CoverageReport(tuple(entries), len(registry.lenses), len(registry.facets))
