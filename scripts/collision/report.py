"""Bulgularin sunumu ve kabul karari.

Rapor, hata mesajini PROJE DILINDE verir: "f_koltuk3 ile w12 cakisiyor" gibi.
Bu bilincli bir tercihtir - denetim DXF uretildikten sonra yapilsaydi mesaj
"handle 2F4 ile handle 3A1" olurdu ve kullanici bunu `context.json`da
duzeltemezdi.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .engine import Clash
from .matrix import Policy


@dataclass
class ClashReport:
    clashes: list[Clash] = field(default_factory=list)
    units: str = "mm"

    @property
    def errors(self) -> list[Clash]:
        return [c for c in self.clashes if c.policy is Policy.FORBID]

    @property
    def warnings(self) -> list[Clash]:
        return [c for c in self.clashes if c.policy is Policy.WARN]

    @property
    def ok(self) -> bool:
        """Yalnizca FORBID uretimi durdurur. UYARI raporlanir ama bloklamaz."""
        return not self.errors

    def error_lines(self) -> list[str]:
        return [c.message(self.units) for c in self.errors]

    def warning_lines(self) -> list[str]:
        return [c.message(self.units) for c in self.warnings]

    def summary(self) -> str:
        if not self.clashes:
            return "CAKISMA DENETIMI: temiz (hata yok, uyari yok)."
        return (f"CAKISMA DENETIMI: {len(self.errors)} hata, "
                f"{len(self.warnings)} uyari.")

    def extend(self, clashes: list[Clash]) -> None:
        self.clashes.extend(clashes)
