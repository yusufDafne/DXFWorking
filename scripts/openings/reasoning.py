"""openings/ muhakeme saglayicisi (DEV-062): yalniz ROL + OLCUM BEYANI. Veche KAYITLARI `reasoning/lenses/isik_hava_yonelim.py`dedir."""
from __future__ import annotations

ROLE = "olcum_saglayici"

MEASUREMENTS = {
    "isik_hava_yonelim": (
        "openings.daylight:check_living_room_window", "openings.daylight:check_cross_ventilation",
        "openings.daylight:check_salon_orientation",
    ),
}


def register(reg) -> None:
    """Veche kaydi lens paketindedir; burada yapilacak bir sey yok."""
