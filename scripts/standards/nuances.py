"""Kapi/koridor endustri nuanslari - mahal tipine bagli arity-1 kurallar
(DEV-050 madde 7-10). HEPSI UYARI (asla HATA), esikler kutuphane
varsayilanidir ("v1 pratik varsayilan", `STANDARDS` ile AYNI disiplin;
yonetmelik gelince BU DEGERLER guncellenir, fonksiyon imzalari degismez).

  7. mahal tipine gore asgari kapi genisligi (+ giris kapisi)
  8. koridor NET genisligi >= kapi KANAT genisligi + pay
  9. cikmaz koridor ucunda donus payi (900x900 serbest kare): kol uclarinin
     gercek geometrisi + uca kapi acilip acilmadigi (DEV-057)
 10. T/L koridorda kollar arasi net genislik daralmasi (rektilineer poligon)

Oda <-> kapi komsulugu `architect/rules.py` ile AYNI yontemle bulunur
(kapi merkez noktasinin oda kenarina <= 300mm yakinligi); `collision`/
`architect`i import etmez (modul bagimsizligi) - kucuk geometri yardimcisi
burada yeniden yazildi.
"""
from __future__ import annotations

from .measure import (
    arm_rects,
    arm_widths,
    chord_through,
    edge_wall_thicknesses,
    is_convex,
    is_rectilinear,
)

DOOR_MIN_WIDTH_MM: dict[str, float] = {
    "wc": 700.0,
    "banyo": 700.0,
    "yatak_odasi": 800.0,
    "salon": 800.0,
    "dukkan": 900.0,  # DEV-051 ek karar: dukkan konut degil, ayri islenir (v1 varsayilan)
}
ENTRY_DOOR_MIN_WIDTH_MM = 900.0
CORRIDOR_DOOR_MARGIN_MM = 100.0
DEAD_END_TURNING_SQUARE_MM = 900.0
ARM_NARROWING_TOLERANCE_MM = 100.0
# DEV-051: kapi tam acikken koridorda KALAN serbest gecis genisligi. v1 pratik
# varsayilan: 800mm (tek kisinin rahat gecisi; erisilebilirlik icin 900'e
# cikarilabilir). Yonetmelik gelince bu sabit guncellenir.
OPEN_DOOR_MIN_PASSAGE_MM = 800.0

_TOUCH_TOLERANCE_MM = 300.0


def _dist_point_segment(p, a, b) -> float:
    ax, ay = a
    dx, dy = b[0] - ax, b[1] - ay
    seg2 = dx * dx + dy * dy
    t = 0.0 if seg2 == 0 else max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / seg2))
    return ((p[0] - ax - t * dx) ** 2 + (p[1] - ay - t * dy) ** 2) ** 0.5


def _point_in_polygon(point, polygon) -> bool:
    x, y = point
    inside = False
    n = len(polygon)
    for k in range(n):
        (x0, y0), (x1, y1) = polygon[k], polygon[(k + 1) % n]
        if (y0 > y) != (y1 > y) and x < (x1 - x0) * (y - y0) / (y1 - y0) + x0:
            inside = not inside
    return inside


def _touches(point, polygon, tol=_TOUCH_TOLERANCE_MM) -> bool:
    n = len(polygon)
    return any(
        _dist_point_segment(point, polygon[k], polygon[(k + 1) % n]) <= tol
        for k in range(n)
    )


def _door_mid(door: dict, walls_by_id: dict):
    wall = walls_by_id.get(door.get("wall_id"))
    if wall is None:
        return None, None
    sx, sy = wall["start"]
    ex, ey = wall["end"]
    length = ((ex - sx) ** 2 + (ey - sy) ** 2) ** 0.5
    if length == 0:
        return None, None
    t = door["position_from_start"] / length
    return (sx + t * (ex - sx), sy + t * (ey - sy)), ((ex - sx) / length, (ey - sy) / length)


def _doors(openings):
    return [o for o in openings if o.get("type") == "door"]


def _leaf_width(door: dict) -> float | None:
    variant = door.get("variant", "single")
    if variant in ("sliding", "folding"):
        return None  # kanat kapi onunde donmez / koridoru daraltmaz
    return door["width"] / 2.0 if variant == "double" else door["width"]


def check_door_widths_by_room(rooms: list[dict], walls: list[dict],
                              openings: list[dict]) -> list[str]:
    """[madde 7] Kapi, dokundugu odalarin tipine gore asgari genislikten
    darsa UYARI; birim ile ortak alan arasindaki kapi GIRIS kapisidir
    (>= 900mm)."""
    warnings: list[str] = []
    walls_by_id = {w["id"]: w for w in walls}
    for door in _doors(openings):
        point, _ = _door_mid(door, walls_by_id)
        if point is None:
            continue
        touching = [r for r in rooms if _touches(point, r["polygon"])]
        need, why = 0.0, ""
        for room in touching:
            req = DOOR_MIN_WIDTH_MM.get(room.get("room_type") or "")
            if req and req > need:
                need, why = req, f"{room.get('room_type')} ('{room['id']}')"
        has_unit = any(r.get("unit_id") for r in touching)
        has_common = any(not r.get("unit_id") for r in touching)
        if has_unit and has_common and ENTRY_DOOR_MIN_WIDTH_MM > need:
            need, why = ENTRY_DOOR_MIN_WIDTH_MM, "giris kapisi"
        if need and door["width"] < need:
            warnings.append(
                f"Kapi '{door['id']}' genisligi {door['width']:.0f}mm, "
                f"{why} icin asgari {need:.0f}mm altinda."
            )
    return warnings


def check_corridor_door_clearance(rooms: list[dict], walls: list[dict],
                                  openings: list[dict]) -> list[str]:
    """[madde 8] Koridorun, kapinin onundeki NET genisligi kapi KANAT
    genisligi + `CORRIDOR_DOOR_MARGIN_MM`den az ise UYARI."""
    warnings: list[str] = []
    walls_by_id = {w["id"]: w for w in walls}
    for room in rooms:
        if room.get("room_type") != "koridor":
            continue
        thick = edge_wall_thicknesses(room["polygon"], walls)
        for door in _doors(openings):
            leaf = _leaf_width(door)
            point, direction = _door_mid(door, walls_by_id)
            if leaf is None or point is None or not _touches(point, room["polygon"], 1.0 + 100.0):
                continue
            normal = (-direction[1], direction[0])
            best = None
            for sgn in (1.0, -1.0):  # kapinin koridor tarafindaki kesit
                probe = (point[0] + normal[0] * sgn * 50.0, point[1] + normal[1] * sgn * 50.0)
                chord = chord_through(room["polygon"], probe, normal, thick)
                if chord is not None:
                    best = chord if best is None else min(best, chord)
            if best is not None and best < leaf + CORRIDOR_DOOR_MARGIN_MM:
                warnings.append(
                    f"Koridor '{room['id']}': '{door['id']}' kapisinin onunde net "
                    f"genislik {best:.0f}mm, kanat {leaf:.0f}mm + pay "
                    f"{CORRIDOR_DOOR_MARGIN_MM:.0f}mm = {leaf + CORRIDOR_DOOR_MARGIN_MM:.0f}mm gerekir."
                )
    return warnings


def check_dead_end_turning(rooms: list[dict], walls: list[dict],
                           openings: list[dict]) -> list[str]:
    """[madde 9, DEV-057: gercek uc geometrisi] Dik acili koridorun her KOLU icin
    kisa uclari (kol genisligi boyunca) incelenir: bir kisa uc poligon siniri
    (duvar) uzerindeyse VE o uca temas eden kapi YOKSA o uc CIKMAZDIR; cikmaz
    uctaki kolun NET genisligi `DEAD_END_TURNING_SQUARE_MM`den dar ise (donus
    payi icin 900x900mm serbest kare sigmaz) UYARI. Kol, baska bir kola
    baglanan (poligon icinde paylasilan) uctan CIKMAZ SAYILMAZ. Dik acili
    olmayan poligon olculemez -> atlanir."""
    warnings: list[str] = []
    walls_by_id = {w["id"]: w for w in walls}
    door_points = []
    for door in _doors(openings):
        point, _ = _door_mid(door, walls_by_id)
        if point is not None:
            door_points.append(point)
    for room in rooms:
        if room.get("room_type") != "koridor":
            continue
        poly = room["polygon"]
        for arm in arm_rects(poly, edge_wall_thicknesses(poly, walls)):
            x0, y0, x1, y1 = arm["rect"]
            w, h = x1 - x0, y1 - y0
            if abs(w - h) < 1e-6:
                continue  # kare bolum: kol degil, hol
            ends = ([((x0, y0), (x0, y1)), ((x1, y0), (x1, y1))] if w > h  # yatay kol: sol/sag uc
                    else [((x0, y0), (x1, y0)), ((x0, y1), (x1, y1))])      # dusey kol: alt/ust uc
            for a, b in ends:
                mid = ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)
                on_boundary = any(
                    _dist_point_segment(mid, poly[k], poly[(k + 1) % len(poly)]) <= 1.0
                    for k in range(len(poly)))
                if not on_boundary:
                    continue  # baska bir kola/hole baglanir
                # DONUS (bukey): ucun hemen yanindaki uzun kenarin DISINDA poligon
                # icindeyse kol orada baska bir kola baglanir -> cikmaz degil
                if w > h:
                    probes = [(a[0] + (1.0 if a[0] == x0 else -1.0), y0 - 1.0),
                              (a[0] + (1.0 if a[0] == x0 else -1.0), y1 + 1.0)]
                else:
                    probes = [(x0 - 1.0, a[1] + (1.0 if a[1] == y0 else -1.0)),
                              (x1 + 1.0, a[1] + (1.0 if a[1] == y0 else -1.0))]
                if any(_point_in_polygon(pr, poly) for pr in probes):
                    continue
                if any(_dist_point_segment(p, a, b) <= 150.0 for p in door_points):
                    continue  # uca kapi acilir: cikmaz degil
                if arm["width"] < DEAD_END_TURNING_SQUARE_MM - 1e-6:
                    warnings.append(
                        f"Koridor '{room['id']}' cikmaz ucu ({mid[0]:.0f},{mid[1]:.0f}): "
                        f"kol net genisligi {arm['width']:.0f}mm, "
                        f"{DEAD_END_TURNING_SQUARE_MM:.0f}x{DEAD_END_TURNING_SQUARE_MM:.0f}mm "
                        f"donus payi yok."
                    )
                    break  # kol basina tek uyari
    return warnings


def check_corridor_arm_narrowing(rooms: list[dict], walls: list[dict]) -> list[str]:
    """[madde 10] L/T (dis bukey) koridorda kollarin NET genisligi birbirinden
    `ARM_NARROWING_TOLERANCE_MM`den fazla ayriliyorsa (daralma) UYARI."""
    warnings: list[str] = []
    for room in rooms:
        if room.get("room_type") != "koridor":
            continue
        poly = room["polygon"]
        if is_convex(poly) or not is_rectilinear(poly):
            continue
        arms = arm_widths(poly, edge_wall_thicknesses(poly, walls))
        if len(arms) >= 2 and max(arms) - min(arms) > ARM_NARROWING_TOLERANCE_MM:
            warnings.append(
                f"Koridor '{room['id']}': kol net genislikleri {min(arms):.0f}-"
                f"{max(arms):.0f}mm - kollar arasinda daralma "
                f"(tolerans {ARM_NARROWING_TOLERANCE_MM:.0f}mm)."
            )
    return warnings


def check_open_door_net_passage(rooms: list[dict], walls: list[dict],
                                openings: list[dict]) -> list[str]:
    """[DEV-051] Bir kapi KORIDORA dogru aciliyorsa (host_side yuzunde koridor
    var), kanat tam acikken koridorda KALAN serbest gecis = koridor NET
    genisligi (kapinin onunde, duvara dik kesit) - kanat genisligi.
    `OPEN_DOOR_MIN_PASSAGE_MM`in altindaysa UYARI. Konutta kapilar odaya acilir
    (`architect.check_doors_open_into_rooms`); bu kontrol, istisnai olarak
    koridora acilan kapilar icin kalan gecisi OLCER."""
    warnings: list[str] = []
    walls_by_id = {w["id"]: w for w in walls}
    for door in _doors(openings):
        leaf = _leaf_width(door)
        point, direction = _door_mid(door, walls_by_id)
        if leaf is None or point is None:
            continue
        normal = (-direction[1], direction[0])
        sign = 1.0 if door.get("host_side", "pos") == "pos" else -1.0
        probe = (point[0] + normal[0] * sign * 50.0, point[1] + normal[1] * sign * 50.0)
        for room in rooms:
            if room.get("room_type") != "koridor":
                continue
            width = chord_through(room["polygon"], probe, normal,
                                  edge_wall_thicknesses(room["polygon"], walls))
            if width is None:
                continue
            passage = width - leaf
            if passage < OPEN_DOOR_MIN_PASSAGE_MM:
                warnings.append(
                    f"Kapi '{door['id']}' koridora ('{room['id']}') aciliyor: kanat "
                    f"acikken kalan gecis {passage:.0f}mm (net {width:.0f} - kanat "
                    f"{leaf:.0f}), asgari {OPEN_DOOR_MIN_PASSAGE_MM:.0f}mm."
                )
    return warnings


def check_door_corridor_nuances(rooms: list[dict], walls: list[dict],
                                openings: list[dict]) -> list[str]:
    return (
        check_door_widths_by_room(rooms, walls, openings)
        + check_corridor_door_clearance(rooms, walls, openings)
        + check_dead_end_turning(rooms, walls, openings)
        + check_open_door_net_passage(rooms, walls, openings)
        + check_corridor_arm_narrowing(rooms, walls)
    )
