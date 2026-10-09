"""Isik/hava/yonelim olcumleri (DEV-062): `reasoning/lenses/isik_hava_yonelim.py` vechelerinin OLCUM sahibi.

`validate.py` BUNLARI CAGIRMAZ; yalniz muhakeme katmaninin (`scripts/reasoning_report.py`) `shadow` vechelerini besler.
Mekansal sorgular `spatial/`dandir (cephe tayini = prob noktasi, pencere -> oda). Her olcum `check_*` (UYARI metinleri) ve
`*_subjects` (ozne -> True|False|None; None = olculemedi) ikizi verir. Kume sabitleri lens-yereldir (`standards/` DEGISMEZ):
yasam mahalli = salon + yatak odasi (pencere sart); mutfak AYRI kayittir ve burada degerlendirilmez.
Hicbiri yonetmelik DEGILDIR; esik yok - yalniz varlik/yon sayimi. Yon uydurulmaz: `north_angle` yoksa yonelim olcumu bos doner.
"""
from __future__ import annotations

import math

try:
    from ..spatial import exterior_windows
except ImportError:
    from spatial import exterior_windows

LIVING_ROOM_TYPES = frozenset({"salon", "yatak_odasi"})
SALON_ROOM_TYPES = frozenset({"salon"})
NORMAL_ROUND = 2   # cephe yonu karsilastirmasi: birim vektor bilesenleri 0,01'e yuvarlanir (ayni dis yon = ayni anahtar)


def _windows_of(room: dict, ext: list[dict]) -> list[dict]:
    return [w for w in ext if any(r["id"] == room["id"] for r in w["rooms"])]


# ---------------------------------------------------------------- yasam mahalli penceresi
def _living_room_window(rooms, walls, openings, shafts):
    ext = exterior_windows(rooms, walls, openings, shafts)
    subjects: dict[str, bool | None] = {}
    warnings: list[str] = []
    for room in (r for r in rooms if r.get("room_type") in LIVING_ROOM_TYPES):
        has = bool(_windows_of(room, ext))
        subjects[room["id"]] = not has
        if not has:
            kind = "Salon" if room["room_type"] == "salon" else "Yatak odasi"
            warnings.append(f"{kind} '{room['id']}' icin dis cepheye acilan pencere yok - gunisigi ve dogal havalandirma saglanmiyor.")
    return subjects, warnings


def check_living_room_window(rooms: list[dict], walls: list[dict], openings: list[dict], shafts: list[dict]) -> list[str]:
    """[isik_hava_yonelim.isik.yasam_mahalli_penceresi - SHADOW] Salon/yatak odasinin dis cepheye acilan penceresi yoksa UYARI."""
    return _living_room_window(rooms, walls, openings, shafts)[1]


def living_room_window_subjects(rooms: list[dict], walls: list[dict], openings: list[dict], shafts: list[dict]) -> dict:
    """Ozne = yasam mahalli odasi; True = penceresiz (tetikledi)."""
    return _living_room_window(rooms, walls, openings, shafts)[0]


# ---------------------------------------------------------------- capraz havalandirma
def _cross_ventilation(rooms, walls, openings, shafts):
    ext = exterior_windows(rooms, walls, openings, shafts)
    subjects: dict[str, bool | None] = {}
    warnings: list[str] = []
    units = sorted({r["unit_id"] for r in rooms if r.get("unit_id") and r.get("room_type") in LIVING_ROOM_TYPES})
    for unit in units:
        unit_rooms = [r for r in rooms if r.get("unit_id") == unit]
        normals = {(round(w["normal"][0], NORMAL_ROUND), round(w["normal"][1], NORMAL_ROUND))
                   for w in ext if any(r["id"] == ur["id"] for r in w["rooms"] for ur in unit_rooms)}
        if not normals:
            subjects[unit] = None   # hic dis pencere tayin edilemedi: 'olculemedi' (yasam mahalli penceresi veçhesi yakalar)
            continue
        subjects[unit] = len(normals) < 2
        if len(normals) < 2:
            warnings.append(f"Birim '{unit}': pencereler yalniz tek bir dis cepheye aciliyor - capraz havalandirma icin "
                            f"birbirinden farkli en az iki cephede acilik tercih edilir.")
    return subjects, warnings


def check_cross_ventilation(rooms: list[dict], walls: list[dict], openings: list[dict], shafts: list[dict]) -> list[str]:
    """[isik_hava_yonelim.hava.capraz_havalandirma - SHADOW] Birimin dis pencereleri tek cepheye bakiyorsa UYARI."""
    return _cross_ventilation(rooms, walls, openings, shafts)[1]


def cross_ventilation_subjects(rooms: list[dict], walls: list[dict], openings: list[dict], shafts: list[dict]) -> dict:
    """Ozne = yasam mahalli olan birim; True = tek cephe; None = dis pencere tayin edilemedi."""
    return _cross_ventilation(rooms, walls, openings, shafts)[0]


# ---------------------------------------------------------------- yonelim (meta.north_angle ister)
def _north_vector(north_angle: float) -> tuple[float, float]:
    """`north_angle`: paftanin 'yukari' yonunden gercek kuzeye SAAT YONUNDE derece (kok CLAUDE.md 'Kuzey oku')."""
    a = math.radians(north_angle)
    return (math.sin(a), math.cos(a))


def _salon_orientation(rooms, walls, openings, shafts, north_angle):
    subjects: dict[str, bool | None] = {}
    warnings: list[str] = []
    if north_angle is None:
        return subjects, warnings   # yon uydurulmaz; kapsam raporu 'kosamadi' der
    north = _north_vector(north_angle)
    ext = exterior_windows(rooms, walls, openings, shafts)
    for room in (r for r in rooms if r.get("room_type") in SALON_ROOM_TYPES):
        wins = _windows_of(room, ext)
        if not wins:
            subjects[room["id"]] = None   # penceresiz: yonelim olculemez (penceresiz yasam mahalli ayri vechede)
            continue
        all_north = all(w["normal"][0] * north[0] + w["normal"][1] * north[1] > 0 for w in wins)
        subjects[room["id"]] = all_north
        if all_north:
            warnings.append(f"Salon '{room['id']}' pencereleri yalniz kuzey yarisina bakiyor - salonun guney yarisina bakan bir "
                            f"pencere tercih edilir (genel pratik; kaynak yok).")
    return subjects, warnings


def check_salon_orientation(rooms: list[dict], walls: list[dict], openings: list[dict], shafts: list[dict],
                            north_angle: float | None) -> list[str]:
    """[isik_hava_yonelim.yonelim.salon_kuzeye_bakiyor - SHADOW] Salonun tum pencereleri kuzey yarisina bakiyorsa UYARI.
    `north_angle` yoksa bos doner (kapsam raporu 'kuzey yonu verilmedi' der)."""
    return _salon_orientation(rooms, walls, openings, shafts, north_angle)[1]


def salon_orientation_subjects(rooms: list[dict], walls: list[dict], openings: list[dict], shafts: list[dict],
                               north_angle: float | None) -> dict:
    """Ozne = salon; True = tum pencereler kuzey yarisina bakiyor; None = penceresiz (olculemedi)."""
    return _salon_orientation(rooms, walls, openings, shafts, north_angle)[0]
