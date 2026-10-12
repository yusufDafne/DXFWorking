"""Yasanabilirlik olcumleri (DEV-063): `reasoning/lenses/yasanabilirlik.py` vechelerinin OLCUM sahibi.

`validate.py` BUNLARI CAGIRMAZ; yalniz `shadow` vecheleri besler (kullaniciya gosterilmez). Katman A (gecis payi = 0):
net oda + katalog olcusu + collision kapi sektoru. Sonuc turevdir, context'e yazilmaz; 'sigmadi' bir yerlesim onerisi degil
SINAV sonucudur. Tefris verisi olmayan projede de calisir (deneme yerlesimi). v1 yalniz `yatak_odasi`.
"""
from __future__ import annotations

from collision import TAG_DOOR_SWING

try:
    from ..openings.collision import footprints as door_footprints
except ImportError:
    from openings.collision import footprints as door_footprints

from .engine import best_cluster, try_fit
from .library import BEDROOM_CLUSTERS

BEDROOM = "yatak_odasi"
CLUSTER = {c.id: c for c in BEDROOM_CLUSTERS}


def _sectors(rooms, walls, openings):
    return [s for s in door_footprints({"walls": walls, "openings": openings}, {}) if s.tag == TAG_DOOR_SWING]


def _capacity_text(room, walls, sectors):
    best, results = best_cluster(room, walls, sectors, BEDROOM_CLUSTERS)
    if best is not None:
        return best.label_tr
    return None if any(r.fits is None for r in results) else ""


def _threshold_fit(rooms, walls, openings, cluster_id: str, template: str):
    """Ozne = yatak odasi; True = `cluster_id` kumesi SIGMIYOR (tetikledi); None = olculemedi."""
    sectors = _sectors(rooms, walls, openings)
    subjects: dict[str, bool | None] = {}
    warnings: list[str] = []
    for room in (r for r in rooms if r.get("room_type") == BEDROOM):
        res = try_fit(room, walls, sectors, CLUSTER[cluster_id])
        if res.fits is None:
            subjects[room["id"]] = None
            continue
        subjects[room["id"]] = not res.fits
        if not res.fits:
            cap = _capacity_text(room, walls, sectors)
            tail = ("hiçbir tipik küme sığmıyor" if cap == "" else f"en çok '{cap}' kümesi sığıyor") if cap is not None \
                else "sığabilecek kümeyi ölçemedik"
            warnings.append(template.format(room=room["id"], cluster=CLUSTER[cluster_id].label_tr, tail=tail))
    return subjects, warnings


_SINGLE = "Yatak odasi '{room}': net olcude '{cluster}' kumesi kapi acilimiyla birlikte SIGMIYOR ({tail}) - deneme yerlesimi sonucu; yerlesim karari sizindir."
_DOUBLE = "Yatak odasi '{room}': net olcude '{cluster}' kumesi kapi acilimiyla birlikte SIGMIYOR ({tail}) - deneme yerlesimi sonucu; yerlesim karari sizindir."


def check_bedroom_single_bed_fits(rooms: list[dict], walls: list[dict], openings: list[dict]) -> list[str]:
    """[yasanabilirlik.mobilya.yatak_odasi_tek_yatak_sigar - SHADOW] K4 (tek kisilik yatak) net odaya + kapi sektorune sigmiyorsa UYARI."""
    return _threshold_fit(rooms, walls, openings, "K4", _SINGLE)[1]


def bedroom_single_bed_fits_subjects(rooms: list[dict], walls: list[dict], openings: list[dict]) -> dict:
    return _threshold_fit(rooms, walls, openings, "K4", _SINGLE)[0]


def check_bedroom_double_bed_wardrobe_fits(rooms: list[dict], walls: list[dict], openings: list[dict]) -> list[str]:
    """[yasanabilirlik.mobilya.yatak_odasi_cift_yatak_gardirop_sigar - SHADOW] K2 (cift yatak + gardirop) sigmiyorsa UYARI (tercih)."""
    return _threshold_fit(rooms, walls, openings, "K2", _DOUBLE)[1]


def bedroom_double_bed_wardrobe_fits_subjects(rooms: list[dict], walls: list[dict], openings: list[dict]) -> dict:
    return _threshold_fit(rooms, walls, openings, "K2", _DOUBLE)[0]


def bedroom_capacity(rooms: list[dict], walls: list[dict], openings: list[dict]) -> dict:
    """Rapor icin: {oda_id: kume kimligi | None (hicbiri sigmiyor) | 'olculemedi'}. Yorumsuz sinav cevabi."""
    sectors = _sectors(rooms, walls, openings)
    out = {}
    for room in (r for r in rooms if r.get("room_type") == BEDROOM):
        best, results = best_cluster(room, walls, sectors, BEDROOM_CLUSTERS)
        out[room["id"]] = best.id if best else ("olculemedi" if any(r.fits is None for r in results) else None)
    return out
