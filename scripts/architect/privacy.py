"""Mahremiyet olcumleri (DEV-061): `reasoning/lenses/mahremiyet.py` veches'lerinin OLCUM sahibi.

`rules.py`den farki: buradaki fonksiyonlar `validate.py` tarafindan CAGRILMAZ; yalnizca muhakeme
katmaninin (`scripts/reasoning_report.py`) `shadow` vechelerini besler - yani kullaniciya gorunur bir
bulgu uretmezler. Mekansal sorgular `spatial/`dan gelir (DEV-059); burada ikinci bir kopya YOKTUR.

Her olcum IKI bicimde sunulur (ayni cekirdekten):
  * `check_*(rooms, walls, openings)` -> UYARI metinleri (adaptor/vaka kosucusu bunu okur);
  * `*_subjects(rooms, walls, openings)` -> `{ozne: True|False|None}` (asgari terfi olceri icin:
    ozne = sayma birimi; None = olculemedi, paydadan cikar).

Esikler katalog sabitidir (context'e yazilmaz) ve her fonksiyon override parametresi tasir.
Hicbiri yonetmelik DEGILDIR (`tercih`/`yaygin`); kaynak yoksa vechenin `provenance`i bunu soyler.
"""
from __future__ import annotations

import math

try:
    from ..spatial import (
        clear_line_of_sight as _clear_line_of_sight,
        door_midpoint as _door_midpoint,
        rooms_touching_point as _rooms_touching_point,
        shared_edge_length as _shared_edge_length,
        vertex_mean as _centroid,
    )
    from .rules import (
        BEDROOM_ROOM_TYPES,
        DEFAULT_ENTRY_FRONT_MAX_DISTANCE_MM,
        DEFAULT_SIGHTLINE_CONE_DEGREES,
        WC_ROOM_TYPES,
    )
except ImportError:
    from spatial import (
        clear_line_of_sight as _clear_line_of_sight,
        door_midpoint as _door_midpoint,
        rooms_touching_point as _rooms_touching_point,
        shared_edge_length as _shared_edge_length,
        vertex_mean as _centroid,
    )
    from architect.rules import (
        BEDROOM_ROOM_TYPES,
        DEFAULT_ENTRY_FRONT_MAX_DISTANCE_MM,
        DEFAULT_SIGHTLINE_CONE_DEGREES,
        WC_ROOM_TYPES,
    )

# Komsu birim giris kapilari arasi (orta noktalar) tercih edilen en kucuk mesafe: `DEFAULT_ENTRY_FRONT_MAX_DISTANCE_MM`
# (hol derinligi) degerinden ODUNC - 'tercih / v1 pratik varsayilan', kaynak YOK (kullanici karari 2026-10-09).
DEFAULT_NEIGHBOR_ENTRY_MIN_DISTANCE_MM = DEFAULT_ENTRY_FRONT_MAX_DISTANCE_MM
LIVING_ROOM_TYPES = frozenset({"salon"})
PRIVATE_SIDE_ROOM_TYPES = frozenset({"yatak_odasi", "salon"})


def _wall_normal(wall: dict) -> tuple[float, float] | None:
    dx, dy = wall["end"][0] - wall["start"][0], wall["end"][1] - wall["start"][1]
    length = (dx * dx + dy * dy) ** 0.5
    return None if length == 0 else (-dy / length, dx / length)


def _entries(rooms: list[dict], walls: list[dict], openings: list[dict]) -> list[dict]:
    """Birim GIRIS kapilari (ortak alan <-> `unit_id`li oda gecisi): kapi, orta nokta, birime bakan normal, birim."""
    walls_by_id = {w["id"]: w for w in walls}
    out = []
    for door in (o for o in openings if o.get("type") == "door"):
        wall = walls_by_id.get(door.get("wall_id"))
        point = _door_midpoint(door, walls_by_id)
        normal = _wall_normal(wall) if wall else None
        if point is None or normal is None:
            continue
        touching = _rooms_touching_point(point, rooms)
        unit_side = [r for r in touching if r.get("unit_id")]
        if not unit_side or not any(not r.get("unit_id") for r in touching):
            continue
        centroid = _centroid(unit_side[0]["polygon"])
        if normal[0] * (centroid[0] - point[0]) + normal[1] * (centroid[1] - point[1]) < 0:
            normal = (-normal[0], -normal[1])
        out.append({"door": door, "point": point, "normal": normal, "unit": unit_side[0]["unit_id"]})
    return out


# ------------------------------------------------------------------ olcum #4: girisden yatak odasi kapisi
def _entry_bedroom_sightline(rooms, walls, openings, cone_degrees):
    walls_by_id = {w["id"]: w for w in walls}
    cos_threshold = math.cos(math.radians(cone_degrees))
    entries = _entries(rooms, walls, openings)
    units_with_bedroom = {r["unit_id"] for r in rooms
                          if r.get("unit_id") and r.get("room_type") in BEDROOM_ROOM_TYPES}
    entry_units = {e["unit"] for e in entries}
    subjects: dict[str, bool | None] = {u: (False if u in entry_units else None) for u in sorted(units_with_bedroom)}
    warnings: list[str] = []
    doors = [o for o in openings if o.get("type") == "door"]
    for e in entries:
        for other in doors:
            if other["id"] == e["door"]["id"]:
                continue
            other_point = _door_midpoint(other, walls_by_id)
            if other_point is None:
                continue
            if not any(r.get("room_type") in BEDROOM_ROOM_TYPES and r.get("unit_id") == e["unit"]
                       for r in _rooms_touching_point(other_point, rooms)):
                continue
            vx, vy = other_point[0] - e["point"][0], other_point[1] - e["point"][1]
            dist = (vx * vx + vy * vy) ** 0.5
            if dist == 0:
                continue
            cos_angle = (e["normal"][0] * vx + e["normal"][1] * vy) / dist
            if cos_angle < cos_threshold:
                continue
            if not _clear_line_of_sight(e["point"], other_point, walls, {e["door"]["wall_id"], other["wall_id"]}):
                continue
            angle = math.degrees(math.acos(max(-1.0, min(1.0, cos_angle))))
            subjects[e["unit"]] = True
            warnings.append(
                f"Giris kapisi '{e['door']['id']}' ile yatak odasi kapisi '{other['id']}' ayni goru "
                f"hattinda (sapma {angle:.0f} derece, sinir {cone_degrees:.0f}, mesafe {dist:.0f}mm) - "
                f"giristen girildiginde yatak odasi kapisi dogrudan gorunur."
            )
    return subjects, warnings


def check_entry_bedroom_sightline(rooms: list[dict], walls: list[dict], openings: list[dict], *,
                                  cone_degrees: float = DEFAULT_SIGHTLINE_CONE_DEGREES) -> list[str]:
    """[mahremiyet.gorsel.giristen_yatak_odasi_gorus - SHADOW] `check_entry_sightlines`in AYNI koni/gorus
    hatti mantigi, hedef WC/banyo yerine AYNI birimin YATAK ODASI kapisi."""
    return _entry_bedroom_sightline(rooms, walls, openings, cone_degrees)[1]


def entry_bedroom_sightline_subjects(rooms: list[dict], walls: list[dict], openings: list[dict], *,
                                     cone_degrees: float = DEFAULT_SIGHTLINE_CONE_DEGREES) -> dict:
    """Ozne = yatak odasi olan birim; giris kapisi bulunamayan birim None (olculemedi)."""
    return _entry_bedroom_sightline(rooms, walls, openings, cone_degrees)[0]


# ------------------------------------------------------------------ olcum #5: komsu birim giris kapilari
def _neighbor_entry_proximity(rooms, walls, openings, min_distance):
    entries = _entries(rooms, walls, openings)
    units = sorted({e["unit"] for e in entries})
    subjects: dict[str, bool | None] = {u: False for u in units} if len(units) >= 2 else {}
    warnings: list[str] = []
    for i, a in enumerate(entries):
        for b in entries[i + 1:]:
            if a["unit"] == b["unit"]:
                continue
            dist = math.hypot(a["point"][0] - b["point"][0], a["point"][1] - b["point"][1])
            if dist < min_distance - 1e-6:
                subjects[a["unit"]] = subjects[b["unit"]] = True
                warnings.append(
                    f"'{a['unit']}' ve '{b['unit']}' birimlerinin giris kapilari ('{a['door']['id']}', "
                    f"'{b['door']['id']}') birbirine {dist:.0f}mm, tercih edilen en az {min_distance:.0f}mm - "
                    f"komsu girisler birbirine yakin."
                )
    return subjects, warnings


def check_neighbor_entry_proximity(rooms: list[dict], walls: list[dict], openings: list[dict], *,
                                   min_distance: float = DEFAULT_NEIGHBOR_ENTRY_MIN_DISTANCE_MM) -> list[str]:
    """[mahremiyet.birimler_arasi.komsu_giris_yakinligi - SHADOW] Farkli birimlerin giris kapilari
    (orta noktalar, duz cizgi) `min_distance`tan yakinsa UYARI. Kapi genisligi/ortak sahanlik baglami v1'de YOK."""
    return _neighbor_entry_proximity(rooms, walls, openings, min_distance)[1]


def neighbor_entry_proximity_subjects(rooms: list[dict], walls: list[dict], openings: list[dict], *,
                                      min_distance: float = DEFAULT_NEIGHBOR_ENTRY_MIN_DISTANCE_MM) -> dict:
    """Ozne = giris kapisi olan birim; katta tek birim varsa ozne YOK (kiyaslanacak komsu yok)."""
    return _neighbor_entry_proximity(rooms, walls, openings, min_distance)[0]


# ------------------------------------------------------------------ olcum #6: islak hacim ortak duvari (ayni birim)
def _wet_shared_wall(rooms, walls, openings):
    del walls, openings  # ortak kenar yalniz oda poligonlarindan okunur
    by_unit_private: dict[str, list[dict]] = {}
    for r in rooms:
        if r.get("unit_id") and r.get("room_type") in PRIVATE_SIDE_ROOM_TYPES:
            by_unit_private.setdefault(r["unit_id"], []).append(r)
    subjects: dict[str, bool | None] = {}
    warnings: list[str] = []
    for wet in (r for r in rooms if r.get("unit_id") and r.get("room_type") in WC_ROOM_TYPES):
        others = by_unit_private.get(wet["unit_id"], [])
        if not others:
            continue  # yatak odasi/salonu olmayan birimde olculecek bir sey yok
        subjects[wet["id"]] = False
        for other in others:
            shared = _shared_edge_length(wet["polygon"], other["polygon"])
            if shared > 0.0:
                subjects[wet["id"]] = True
                kind = "yatak odasi" if other["room_type"] in BEDROOM_ROOM_TYPES else "salon"
                warnings.append(
                    f"Birim '{wet['unit_id']}': islak hacim '{wet['id']}' {kind} '{other['id']}' ile "
                    f"{shared:.0f}mm ortak duvar paylasiyor - ses/koku acisindan duvar ayirici dusunulmeli."
                )
    return subjects, warnings


def check_wet_shared_wall_same_unit(rooms: list[dict], walls: list[dict], openings: list[dict]) -> list[str]:
    """[mahremiyet.isitsel.islak_ortak_duvar_ayni_birim - SHADOW] AYNI birimde WC/banyo, yatak odasi veya
    salonla ortak duvar paylasiyorsa UYARI. Duvar turu (kutle) ayirici v1'de YOK (gercek projede duvar
    turu verisi yok); kucuk ortak uzunluk da sayilir (esik uydurulmadi)."""
    return _wet_shared_wall(rooms, walls, openings)[1]


def wet_shared_wall_same_unit_subjects(rooms: list[dict], walls: list[dict], openings: list[dict]) -> dict:
    """Ozne = yatak odasi/salonu olan birimdeki her WC/banyo."""
    return _wet_shared_wall(rooms, walls, openings)[0]


# ------------------------------------------------------------------ sandvic banyo bileseni: iki bolgeye kapili islak hacim
def _wet_double_zone(rooms, walls, openings):
    walls_by_id = {w["id"]: w for w in walls}
    doors = [o for o in openings if o.get("type") == "door"]
    subjects: dict[str, bool | None] = {}
    warnings: list[str] = []
    for wet in (r for r in rooms if r.get("unit_id") and r.get("room_type") in WC_ROOM_TYPES):
        reached: dict[str, set[str]] = {}
        for door in doors:
            mid = _door_midpoint(door, walls_by_id)
            if mid is None:
                continue
            touching = _rooms_touching_point(mid, rooms)
            if wet["id"] not in {r["id"] for r in touching}:
                continue
            for other in touching:
                if other["id"] != wet["id"] and other.get("unit_id") == wet["unit_id"]:
                    reached.setdefault(other.get("room_type"), set()).add(other["id"])
        has_bed, has_living = bool(reached.get("yatak_odasi")), bool(reached.get("salon"))
        # olculebilirlik: iki bolgeden en az biri birimde VAR olmali
        if not any(r.get("unit_id") == wet["unit_id"] and r.get("room_type") in PRIVATE_SIDE_ROOM_TYPES for r in rooms):
            continue
        subjects[wet["id"]] = has_bed and has_living
        if has_bed and has_living:
            warnings.append(
                f"Birim '{wet['unit_id']}': islak hacim '{wet['id']}' hem salona "
                f"('{sorted(reached['salon'])[0]}') hem yatak odasina ('{sorted(reached['yatak_odasi'])[0]}') "
                f"kapili - misafirin kullandigi hacim ayni zamanda yatak odasinin hacmi."
            )
    return subjects, warnings


def check_wet_double_zone_doors(rooms: list[dict], walls: list[dict], openings: list[dict]) -> list[str]:
    """[mahremiyet.gecis.islak_iki_bolgeye_kapili - SHADOW] 'sandvic_banyo' kokunun bileseni: ayni birimde
    bir WC/banyonun HEM salona HEM yatak odasina kapisi varsa UYARI (sentetik vaka; gercek geometri yok)."""
    return _wet_double_zone(rooms, walls, openings)[1]


def wet_double_zone_doors_subjects(rooms: list[dict], walls: list[dict], openings: list[dict]) -> dict:
    """Ozne = yatak odasi veya salonu olan birimdeki her WC/banyo."""
    return _wet_double_zone(rooms, walls, openings)[0]
