"""testfit/ muhakeme saglayicisi (DEV-063): yalniz ROL + OLCUM BEYANI. Veche KAYITLARI `reasoning/lenses/yasanabilirlik.py`dedir."""
from __future__ import annotations

ROLE = "olcum_saglayici"

MEASUREMENTS = {
    "yasanabilirlik": (
        "testfit.measure:check_bedroom_single_bed_fits",
        "testfit.measure:check_bedroom_double_bed_wardrobe_fits",
    ),
}


def register(reg) -> None:
    """Veche kaydi lens paketindedir; burada yapilacak bir sey yok."""
