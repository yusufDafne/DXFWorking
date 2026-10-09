"""architect/ muhakeme saglayicisi (DEV-061, plan §7.1): yalniz ROL + OLCUM BEYANI.

Veche KAYITLARI burada degil, lens paketinde yasar (`reasoning/lenses/*.py`); bu dosya 'bu modul hangi
mercege hangi olcum/kurali saglar?' sorusunu yanitlar ve `register` bilerek bostur.
"""
from __future__ import annotations

ROLE = "olcum_ve_kural_sahibi"

# mercek -> olcum/kural sembolleri (kural: architect/rules.py, yeni olcum: architect/privacy.py)
MEASUREMENTS = {
    "mahremiyet": (
        "architect.rules:check_entry_sightlines", "architect.rules:check_kitchen_wet_door_opposite",
        "architect.rules:check_wet_door_swing_inward", "architect.rules:check_bedroom_via_corridor",
        "architect.rules:check_wet_area_reachable_without_bedroom", "architect.rules:check_entry_wet_door_proximity",
        "architect.rules:check_wet_area_adjacency",
        "architect.privacy:check_entry_bedroom_sightline", "architect.privacy:check_neighbor_entry_proximity",
        "architect.privacy:check_wet_shared_wall_same_unit", "architect.privacy:check_wet_double_zone_doors",
    ),
}


def register(reg) -> None:
    """Veche kaydi lens paketindedir (`reasoning/lenses/mahremiyet.py`); burada yapilacak bir sey yok."""
