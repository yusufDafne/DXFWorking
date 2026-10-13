"""Cepheyi PLAN ACIKLIKLARINDAN turetme (DEV-073, kullanici karari 2026-10-12).

`elevations[].openings_from = "plan"` ise ilgili cephede kat basina jenerik `window_count/window_size/door` DEGIL, planin dis duvarlarindaki
GERCEK pencere/kapi acikliklari cizilir: ayni genislik, yukseklik, denizlik ve yatay konum. Opt-in'dir; verilmeyen cephe eski jenerik cizimi korur.

Kurallar (hicbiri uydurma degildir):
  * **Cephe secimi** `axis_source`tan: 'vertical' -> ON cephe (planin ALT kenari, y en kucuk duvar; yatay eksen = plandaki X, soldan saga);
    'horizontal' -> SAG cephe (planin x en buyuk duvari; yatay eksen = plandaki Y). Bu, mevcut `AxisGrid.draw_on_elevation` izdusumuyle AYNIDIR.
  * **Kat <-> seviye eslesmesi SIRAYLA** (`sections` ile ayni sozlesme; sayilar esit olmak zorunda, `validate.py` denetler).
  * Dis yuz `spatial.facade_normal` ile bulunur (ic acikliklar cepheye girmez). Normal cephe normaliyle ayni (nokta carpimi ~ 1) olmalidir;
    egik dis duvar ATLANIR ve `notes`ta soylenir.
  * Pencere yukseklik/denizligi `openings.heights.resolve_window_heights` (sinif: normal/boy/vitrin; verilen ya da adiyla bildirilen katalog varsayilani).
    DIS KAPI: yukseklik/denizlik verisi YOKTUR; kullanici karari geregi (dukkan kapilari "boy pencere") **boy pencere varsayilanlariyla**
    (2000 mm / 40 mm) cizilir, `height` verilmisse o gecer. DEV-076: kapida `door_class` (main_entry / shop) varsa kendi SINIF varsayilanlari gecer.
  * Denizlik + yukseklik seviye yuksekligini asiyorsa ya da aciklik cephe genisliginin disina dusuyorsa `notes`ta UYARI (kirpma YAPILMAZ).
Salt okunur: context'e yazmaz.
"""
from __future__ import annotations

from dataclasses import dataclass

FACADE_BY_AXIS = {"vertical": ("alt", (0.0, -1.0)), "horizontal": ("sag", (1.0, 0.0))}
ON_DOOR_SOURCE = "dis kapi: boy pencere varsayilani"


@dataclass(frozen=True)
class FacadeRect:
    opening_id: str
    floor_id: str
    kind: str            # 'window' | 'door'
    x0: float            # cephe sol kenarindan (dx'siz)
    x1: float
    sill: float
    height: float
    class_key: str       # katalog anahtari ('window.tall', 'door.main_entry'); siniflandirilmamis dis kapi: ''
    height_source: str
    sill_source: str


def _heights(op: dict):
    """(tur, sinif anahtari, yukseklik, denizlik, yukseklik kaynagi, denizlik kaynagi). Pencere ve SINIFLI kapi katalogdan/verilenden
    (`openings.heights`); SINIFSIZ dis kapi: yukseklik verisi yok -> boy pencere varsayilani (kullanici karari), `height` verilmisse o gecer."""
    try:
        from ..openings.heights import (DEFAULT_TALL_WINDOW_HEIGHT_MM, DEFAULT_TALL_WINDOW_SILL_MM, resolve_door_heights,
                                        resolve_window_heights)
    except ImportError:
        from openings.heights import (DEFAULT_TALL_WINDOW_HEIGHT_MM, DEFAULT_TALL_WINDOW_SILL_MM, resolve_door_heights,
                                      resolve_window_heights)
    if op.get("type") == "window":
        r = resolve_window_heights(op)
        return "window", r.class_key, r.height, r.sill, r.height_source, r.sill_source
    r = resolve_door_heights(op)
    if r is not None:
        return "door", r.class_key, r.height, r.sill, r.height_source, r.sill_source
    ssrc = "varsayilan:DEFAULT_TALL_WINDOW_SILL_MM (" + ON_DOOR_SOURCE + ")"
    if "height" in op:
        return "door", "", float(op["height"]), DEFAULT_TALL_WINDOW_SILL_MM, "verilen", ssrc
    return ("door", "", DEFAULT_TALL_WINDOW_HEIGHT_MM, DEFAULT_TALL_WINDOW_SILL_MM,
            "varsayilan:DEFAULT_TALL_WINDOW_HEIGHT_MM (" + ON_DOOR_SOURCE + ")", ssrc)


def derive_level_openings(context: dict, elevation: dict) -> tuple[dict[int, list[FacadeRect]], list[str]]:
    """{seviye_indeksi: [FacadeRect]} ve notlar (UYARI metinleri). Plan modunda olmayan cephe icin ({}, [])."""
    try:
        from ..spatial import exterior_openings
    except ImportError:
        from spatial import exterior_openings
    notes: list[str] = []
    if elevation.get("openings_from") != "plan":
        return {}, notes
    source = elevation.get("axis_source")
    if source not in FACADE_BY_AXIS:
        raise ValueError(f"Cephe '{elevation['id']}': openings_from='plan' icin axis_source 'vertical' (on cephe) ya da 'horizontal' (sag cephe) olmali.")
    facade, fnormal = FACADE_BY_AXIS[source]
    floors, levels = context["floors"], elevation["levels"]
    if len(floors) != len(levels):
        raise ValueError(f"Cephe '{elevation['id']}': kat sayisi ({len(floors)}) ile seviye sayisi ({len(levels)}) esit olmali - "
                         "kat<->seviye eslesmesi SIRAYLA yapilir (sections ile ayni sozlesme).")
    out: dict[int, list[FacadeRect]] = {}
    width = float(elevation["width"])
    oblique = False
    for i, (floor, level) in enumerate(zip(floors, levels)):
        rects: list[FacadeRect] = []
        for item in exterior_openings(floor.get("rooms", []), floor.get("walls", []), floor.get("openings", []),
                                      floor.get("shafts", []), ("window", "door")):
            nx, ny = item["normal"]
            dot = nx * fnormal[0] + ny * fnormal[1]
            if abs(nx) > 1e-6 and abs(ny) > 1e-6:
                oblique = True
                continue
            if dot < 1.0 - 1e-6:
                continue                                   # baska cephe
            op = item["window"]
            mx, my = item["mid"]
            cx = mx if facade == "alt" else my
            half = float(op["width"]) / 2.0
            kind, ckey, h, sill, hsrc, ssrc = _heights(op)
            rect = FacadeRect(op["id"], floor.get("id", str(i)), kind, cx - half, cx + half, sill, h, ckey, hsrc, ssrc)
            if rect.x0 < -1e-6 or rect.x1 > width + 1e-6:
                notes.append(f"[{elevation['id']}] {floor.get('id')}/{op['id']}: aciklik cephe genisliginin ({width:g} mm) disina dusuyor.")
            if sill + h > float(level["height"]) + 1e-6:
                notes.append(f"[{elevation['id']}] {floor.get('id')}/{op['id']}: denizlik + yukseklik {sill + h:g} mm seviye yuksekligini "
                             f"({float(level['height']):g} mm) asiyor (kirpilmadi).")
            rects.append(rect)
        out[i] = sorted(rects, key=lambda r: (r.x0, r.opening_id))
    if oblique:
        notes.append(f"[{elevation['id']}] egik dis duvardaki aciklik(lar) cepheye atanamadi ve ATLANDI (yalniz eksen hizali dis duvarlar desteklenir).")
    return out, notes


def defaults_used_on_facades(context: dict) -> dict[str, int]:
    """Plan modundaki cephelerde SINIFSIZ dis kapilar boy pencere varsayilaniyla cizilir (sinifli kapilar kendi sinif varsayilanlariyla)."""
    n = 0
    for el in context.get("elevations", []):
        if el.get("openings_from") != "plan":
            continue
        rects, _ = derive_level_openings(context, el)
        n += sum(1 for rs in rects.values() for r in rs if r.kind == "door" and not r.class_key and "varsayilan" in r.height_source)
    return {"dis kapi cephede boy pencere varsayilaniyla cizildi (kapi yuksekligi verisi yok)": n} if n else {}
