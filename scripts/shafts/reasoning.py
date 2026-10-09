"""shafts/ muhakeme saglayicisi (DEV-062): yalniz ROL + OLCUM BEYANI. Veche KAYITLARI `reasoning/lenses/isik_hava_yonelim.py`dedir."""
from __future__ import annotations

ROLE = "olcum_saglayici"

MEASUREMENTS = {
    "isik_hava_yonelim": ("shafts.ventilation:check_wet_ventilation",),
}


def register(reg) -> None:
    """Veche kaydi lens paketindedir; burada yapilacak bir sey yok."""
