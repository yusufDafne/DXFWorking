"""Tek bir aks: etiket, konum ve (varsa) KISMI uzanim.

rev-13'e (DEV-015) kadar aks bir `dict`ti ve HER aks yapinin tamamini kat
ediyordu. Iki yetenek eklendi:

- **Kismi aks** (`extent`): aks yalnizca bildirilen aralikta uzanir. Gercek
  projelerde bir aks cogu zaman tum yapiyi kat etmez (orn. yalnizca cekirdek
  bolgesini tanimlayan bir aks).
- **Ara aks** (`1'`): iki ana aks arasina giren aks. Etiket bir SONEKLE
  ayirt edilir; asagiya bakiniz.
"""
from __future__ import annotations

from dataclasses import dataclass

# Ara aks soneki. **Karar (rev-13):** `1'` kullanilir, `1A` KULLANILMAZ.
# Gerekce somut: yatay aks ailesi zaten A, B, C ... ile etiketlenir, bu yuzden
# `1A` "1 ve A akslarinin kesisimi" gibi okunur ve kolon adlandirmasiyla
# (`on_axis_report` `B2` gibi uretir) dogrudan catisir. Kesme isareti
# Turkiye/Avrupa pratiginde de yaygin olandir.
INTERMEDIATE_SUFFIX = "'"


@dataclass(frozen=True)
class Axis:
    """Bir aks cizgisi. `position` sabit koordinat (dusey akslarda X)."""

    label: str
    position: float
    # (baslangic, bitis) - aks yalnizca bu aralikta uzanir. None ise yapinin
    # tamamini kat eder.
    extent: tuple[float, float] | None = None

    @classmethod
    def from_context(cls, data: dict) -> "Axis":
        raw = data.get("extent")
        extent = None
        if raw:
            low, high = float(raw[0]), float(raw[1])
            if low > high:
                low, high = high, low
            extent = (low, high)
        return cls(label=str(data["label"]), position=float(data["position"]),
                   extent=extent)

    @property
    def partial(self) -> bool:
        return self.extent is not None

    @property
    def intermediate(self) -> bool:
        return self.label.endswith(INTERMEDIATE_SUFFIX)

    def span(self, full_low: float, full_high: float,
             extension: float, partial_extension: float) -> tuple[float, float]:
        """Aksin cizilecegi aralik.

        Tam aks, yapinin disina `extension` kadar tasar (baloncuklar orada
        durur). Kismi aks kendi araliginin disina yalnizca `partial_extension`
        kadar tasar - tam uzama verilseydi yapinin disinda bir yere isaret
        ediyormus gibi okunurdu."""
        if self.extent is None:
            return full_low - extension, full_high + extension
        low, high = self.extent
        return low - partial_extension, high + partial_extension

    def covers(self, coordinate: float, tolerance: float = 1.0) -> bool:
        """Aks bu koordinata ULASIYOR mu?

        Kenar olcu zincirine yalnizca o kenara gercekten ulasan akslar girer;
        aksi halde zincir, orada olmayan bir aksi olculuyormus gibi gorunur."""
        if self.extent is None:
            return True
        low, high = self.extent
        return low - tolerance <= coordinate <= high + tolerance


def axes_from_context(entries: list[dict]) -> list[Axis]:
    """Konuma gore SIRALI aks listesi (deterministik)."""
    return sorted((Axis.from_context(entry) for entry in entries),
                  key=lambda axis: axis.position)
