"""Islak hacim havalandirmasi olcumu (DEV-062): pencere **veya** saft. `reasoning/lenses/isik_hava_yonelim.py` vechesinin olcum sahibi.

`check_shafts` (saft <-> islak hacim SIRT SIRTA yerlesimi) ile AYNI tanimi kullanir (`MIN_SHARED_EDGE_MM`, `spatial.shared_edge_length`);
soru farklidir: orada 'saft islak hacmi sunuyor mu', burada 'islak hacim havalandiriliyor mu' (pencere de olur). Ikinci bir
esik/tanim YAZILMAZ. `tesisat` ve `havalandirma` turu saftler sayilir (kullanici karari 2026-10-09); `baca` sayilmaz.
`validate.py` cagirmaz; yalniz `shadow` vechesini besler.
"""
from __future__ import annotations

try:
    from ..spatial import exterior_windows, shared_edge_length
    from . import MIN_SHARED_EDGE_MM
except ImportError:
    from spatial import exterior_windows, shared_edge_length
    from shafts import MIN_SHARED_EDGE_MM

WET_ROOM_TYPES = frozenset({"wc", "banyo"})
VENTILATING_SHAFT_KINDS = frozenset({"tesisat", "havalandirma"})


def _wet_ventilation(rooms, walls, openings, shafts):
    ext = exterior_windows(rooms, walls, openings, shafts)
    vent_shafts = [s for s in shafts if s.get("kind") in VENTILATING_SHAFT_KINDS]
    subjects: dict[str, bool | None] = {}
    warnings: list[str] = []
    for room in (r for r in rooms if r.get("room_type") in WET_ROOM_TYPES):
        by_window = any(any(rr["id"] == room["id"] for rr in w["rooms"]) for w in ext)
        by_shaft = any(shared_edge_length(room["polygon"], s["polygon"]) >= MIN_SHARED_EDGE_MM for s in vent_shafts)
        subjects[room["id"]] = not (by_window or by_shaft)
        if not (by_window or by_shaft):
            warnings.append(f"Islak hacim '{room['id']}' icin ne dis cepheye acilan pencere ne de havalandirma/tesisat saftine "
                            f"bitisik duvar var - dogal ya da mekanik havalandirma yolu gorunmuyor.")
    return subjects, warnings


def check_wet_ventilation(rooms: list[dict], walls: list[dict], openings: list[dict], shafts: list[dict]) -> list[str]:
    """[isik_hava_yonelim.hava.islak_hacim_havalandirma - SHADOW] WC/banyonun penceresi de bitisik saftı da yoksa UYARI."""
    return _wet_ventilation(rooms, walls, openings, shafts)[1]


def wet_ventilation_subjects(rooms: list[dict], walls: list[dict], openings: list[dict], shafts: list[dict]) -> dict:
    """Ozne = WC/banyo; True = havalandirma yolu yok."""
    return _wet_ventilation(rooms, walls, openings, shafts)[0]
