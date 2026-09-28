"""Secenek katalogu (DEV-039): dil modelinin "o anki somut duruma gore
hangi secenekler GECERLI/MANTIKLI" diye SORABILECEGI bir arayuz.

Kullanicinin kendi sozleriyle (madde 4, "merdiven/asansor efektif
yerlesimi"): "efektif yerlesimi bir dil modelinden destek alarak
yapacagiz ama deterministik olabilmek icin modul altyapimizin, dil modeli
tarafindan yeteneklerinin algilanip ona gore calistirilabilmesi
gerekiyor." Sabit bir parametre (bugunku `templates.
CirculationCoreTemplate` enjeksiyon deseni) yerine, bu modul DURUMA gore
HESAPLANMIS, ON-PUANLANMIS birkac secenek dondurur - dil modeli bunlardan
BIRINI kimligiyle SECER. Geometriyi YINE `templates::
generate_circulation_core` (konum parametresi eklendiginde, bkz.
DEVELOPMENT_TASKS.md DEV-039 "Kalan kucuk teknik detaylar") uretir; bu
modulun KENDISI geometri URETMEZ.
"""
from __future__ import annotations

from dataclasses import dataclass

# Kose adlari, saat yonunun tersine SOL-ALT'tan baslar - templates::
# generate_circulation_core BUGUN yalnizca sol-alt kosede (x=0) calisir
# (DEV-037 "Bilinen sinirlamalar"); bu katalog GELECEKTEKI bir `position`
# parametresi icin secenek SIRALAR, henuz templates/'i CAGIRMAZ.
CORNERS: tuple[str, ...] = ("sol-alt", "sag-alt", "sol-ust", "sag-ust")


@dataclass(frozen=True)
class PlacementOption:
    id: str
    label: str
    x: float
    y: float
    score: float
    rationale: str


def _corner_point(corner: str, floor_width: float, floor_depth: float,
                   core_width: float, core_depth: float) -> tuple[float, float]:
    x = 0.0 if "sol" in corner else floor_width - core_width
    y = 0.0 if "alt" in corner else floor_depth - core_depth
    return (x, y)


def options_for_core_placement(
    floor_width: float, floor_depth: float, *, entry_side: str = "alt",
    core_width: float = 4000.0, core_depth: float = 4500.0,
) -> list[PlacementOption]:
    """`entry_side` ('alt'/'ust'/'sol'/'sag'), binaya girisin hangi
    kenardan oldugunu bildirir - VERILMEZSE 'alt' varsayilir (gercek
    projenin `band_south` giris duvariyla AYNI varsayilan). Cekirdek,
    giris kenarina BITISIK kosede EN YUKSEK puani alir (girenin cekirdegi
    hizlica gormesi mimari olarak tercih edilir); giris kenarindan UZAK
    kose daha DUSUK puan alir. Sonuc PUANA gore azalan sirada doner."""
    options: list[PlacementOption] = []
    for corner in CORNERS:
        x, y = _corner_point(corner, floor_width, floor_depth, core_width, core_depth)
        touches_entry = entry_side in corner
        score = 1.0 if touches_entry else 0.4
        rationale = (
            f"'{corner}' kosesi giris kenarina ('{entry_side}') "
            + ("BITISIK - cekirdek giristen hizlica gorunur."
               if touches_entry else
               "UZAK - cekirdege erisim dolayli olur.")
        )
        options.append(PlacementOption(
            id=corner, label=corner.replace("-", " ").upper(),
            x=x, y=y, score=score, rationale=rationale,
        ))
    options.sort(key=lambda option: option.score, reverse=True)
    return options


__all__ = ["PlacementOption", "options_for_core_placement", "CORNERS"]
