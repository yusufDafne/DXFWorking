"""Acikligin KENDI duvarina gore nuans kurallari (DEV-050 madde 1,2,3,5,6,11).

HEPSI UYARI (asla HATA); esikler kutuphane varsayilanidir (`standards/` ile
AYNI "v1 pratik varsayilan" disiplini, context.json'a yazilmaz). Mesafeler
duvarin NET katı kısmı uzerinden olculur: duvar ucunda dik bir duvar varsa
onun yarim kalinligi (duvar govdesine giren kismi) dusulur.

  1. aciklik duvarin basina/sonuna >= 100mm kati duvar birakmali (kasa payi)
  2. ayni duvardaki iki aciklik arasi >= 200mm; iki KAPI arasi >= 250mm
     (DEV-053: 100 cerceve + 150 priz)
  3. pencere bina dis kosesine >= 350mm
  5. cift kanatli kapi: >= 150mm kasa payi ve kanat basina >= 600mm
  6. surme kapi (DEV-051'de dinamiklestirildi, `check_sliding_door_parking`):
     acik kanat (aciklik genisligi kadar, duvar yuzunde) en az BIR yanda
     duvar disina tasmamali, baska bir aciklik alanina ve baska bir kapinin
     acilim sektorune girmemeli
 11. acik kapi kanadi (mentese-uc dogrusu, 4 nokta) ile baska bir duvar yuzu
     arasinda >= 50mm (DEV-057: yalniz uc degil, kanat boyunca)

Madde 11, `swing_geometry`yi (kapi acilim yayinin TEK sahibi) kullanir; bu
yuzden `walls`i tembel import eder (`openings/collision.py` ile AYNI desen).
"""
from __future__ import annotations

from .opening import TYPE_DOOR, TYPE_WINDOW, VARIANT_DOUBLE, VARIANT_SLIDING

EDGE_MARGIN_MM = 100.0
DOUBLE_EDGE_MARGIN_MM = 150.0
DOUBLE_LEAF_MIN_WIDTH_MM = 600.0
OPENING_SPACING_MM = 200.0
# DEV-053 (kullanici karari): iki KAPI arasi 100mm cerceve + 150mm priz payi = 250.
DOOR_SPACING_MM = 250.0
WINDOW_CORNER_MARGIN_MM = 350.0
DOOR_LEAF_CLEARANCE_MM = 50.0


def _len(wall):
    return ((wall["end"][0] - wall["start"][0]) ** 2
            + (wall["end"][1] - wall["start"][1]) ** 2) ** 0.5


def _seg_dist(p, a, b) -> float:
    dx, dy = b[0] - a[0], b[1] - a[1]
    seg2 = dx * dx + dy * dy
    t = 0.0 if seg2 == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / seg2))
    return ((p[0] - a[0] - t * dx) ** 2 + (p[1] - a[1] - t * dy) ** 2) ** 0.5


def _end_overlap(point, wall_id, walls) -> float:
    """`point`te baska bir duvar varsa onun kalinliginin yarisi (govdeye
    giren kati kisim); yoksa 0."""
    best = 0.0
    for w in walls:
        if w["id"] == wall_id:
            continue
        if _seg_dist(point, w["start"], w["end"]) <= 1.0:
            best = max(best, float(w["thickness"]) / 2.0)
    return best


def _bbox_corners(walls):
    xs = [p[0] for w in walls for p in (w["start"], w["end"])]
    ys = [p[1] for w in walls for p in (w["start"], w["end"])]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def _spans(walls, openings):
    """{wall_id: [(start, end, opening), ...]} - duvar boyunca bosluk
    araliklari (`walls.gaps_for_wall` ile ayni sozlesme)."""
    out: dict[str, list] = {}
    for w in walls:
        gaps = []
        for op in openings:
            if op["wall_id"] != w["id"]:
                continue
            half = op["width"] / 2.0
            gaps.append((op["position_from_start"] - half, op["position_from_start"] + half, op))
        gaps.sort(key=lambda g: g[0])
        out[w["id"]] = gaps
    return out


def check_opening_wall_nuances(walls: list[dict], openings: list[dict]) -> list[str]:
    warnings: list[str] = []
    walls_by_id = {w["id"]: w for w in walls}
    corners = _bbox_corners(walls) if walls else []
    for wall_id, gaps in _spans(walls, openings).items():
        wall = walls_by_id[wall_id]
        length = _len(wall)
        if length == 0:
            continue
        ux = (wall["end"][0] - wall["start"][0]) / length
        uy = (wall["end"][1] - wall["start"][1]) / length
        solid_start = _end_overlap(tuple(wall["start"]), wall_id, walls)
        solid_end = _end_overlap(tuple(wall["end"]), wall_id, walls)
        for k, (g0, g1, op) in enumerate(gaps):
            double = op.get("variant") == VARIANT_DOUBLE
            need = DOUBLE_EDGE_MARGIN_MM if double else EDGE_MARGIN_MM
            for label, margin in (("basina", g0 - solid_start), ("sonuna", length - g1 - solid_end)):
                # rev-26 (kullanici karari): merdiven duvar acikligi (passage) icin 10cm
                # kapi cikintisi/kasa payi YOKTUR; acikligin duvar boyunca tam
                # genislikte (kati duvar payi 0) olmasi serbesttir.
                if op.get("type") == "passage":
                    continue
                if margin < need - 1e-6:
                    warnings.append(
                        f"Aciklik '{op['id']}' duvarin ('{wall_id}') {label} "
                        f"{margin:.0f}mm kati duvar birakiyor, asgari {need:.0f}mm "
                        f"(kasa payi)."
                    )
            if double and op["width"] / 2.0 < DOUBLE_LEAF_MIN_WIDTH_MM:
                warnings.append(
                    f"Cift kanatli kapi '{op['id']}': kanat basina "
                    f"{op['width'] / 2.0:.0f}mm, asgari {DOUBLE_LEAF_MIN_WIDTH_MM:.0f}mm."
                )
            if k + 1 < len(gaps):
                nxt = gaps[k + 1]
                gap = nxt[0] - g1
                need_gap = DOOR_SPACING_MM if (op.get("type") == TYPE_DOOR and nxt[2].get("type") == TYPE_DOOR) else OPENING_SPACING_MM
                if gap < need_gap - 1e-6:
                    warnings.append(
                        f"Aciklik '{op['id']}' ile '{nxt[2]['id']}' arasi {gap:.0f}mm "
                        f"duz duvar, asgari {need_gap:.0f}mm."
                    )
            if op.get("type") == TYPE_WINDOW:
                for end_name, s in (("baslangic", 0.0), ("bitis", length)):
                    pt = (wall["start"][0] + ux * s, wall["start"][1] + uy * s)
                    if not any(abs(pt[0] - c[0]) <= 1.0 and abs(pt[1] - c[1]) <= 1.0 for c in corners):
                        continue
                    margin = (g0 - solid_start) if s == 0.0 else (length - g1 - solid_end)
                    if margin < WINDOW_CORNER_MARGIN_MM - 1e-6:
                        warnings.append(
                            f"Pencere '{op['id']}' dis kosenin ({end_name}) "
                            f"{margin:.0f}mm yakininda, asgari {WINDOW_CORNER_MARGIN_MM:.0f}mm."
                        )
    return warnings


def check_door_leaf_clearance(walls: list[dict], openings: list[dict]) -> list[str]:
    """[madde 11, DEV-057: kanat BOYUNCA] Acik kapi kanadi, kendi duvari
    DISINDAKI bir duvar yuzune `DOOR_LEAF_CLEARANCE_MM`den yakinsa UYARI.
    Kanat; mentese -> uc dogrusu uzerinde 4 noktadan (1/4, 1/2, 3/4, uc)
    olculur; en yakin nokta raporlanir ('ucu' veya 'boyunca')."""
    from walls import Wall, WallCatalog, gaps_for_wall

    from .geometry import swing_geometry
    from .opening import Opening

    doors = [o for o in openings if o.get("type") == TYPE_DOOR]
    if not doors:
        return []
    catalog = WallCatalog()
    wall_objs = [Wall.from_context(w, catalog) for w in walls]
    warnings: list[str] = []
    for wall in wall_objs:
        for g_start, g_end, data in gaps_for_wall(wall, doors):
            opening = Opening.from_context(data)
            if opening.variant == VARIANT_SLIDING:
                continue
            swing = swing_geometry(wall, opening, g_start, g_end)
            samples = [
                (t, (swing.hinge[0] + (swing.open_end[0] - swing.hinge[0]) * t,
                     swing.hinge[1] + (swing.open_end[1] - swing.hinge[1]) * t))
                for t in (0.25, 0.5, 0.75, 1.0)
            ]
            for other in wall_objs:
                if other.id == wall.id:
                    continue
                t_min, clear = min(
                    ((t, _seg_dist(pt, other.start, other.end) - other.thickness / 2.0)
                     for t, pt in samples), key=lambda tc: tc[1])
                if clear < DOOR_LEAF_CLEARANCE_MM:
                    where = "ucu" if t_min == 1.0 else "boyunca"
                    warnings.append(
                        f"Kapi '{opening.id}' acikken kanat {where} duvara ('{other.id}') "
                        f"{max(clear, 0.0):.0f}mm yaklasiyor, asgari "
                        f"{DOOR_LEAF_CLEARANCE_MM:.0f}mm."
                    )
    return warnings


def check_sliding_door_parking(walls: list[dict], openings: list[dict]) -> list[str]:
    """[madde 6, DEV-051] Surme kapi acildiginda kanat duvar boyunca yana kayar
    ve aciklik genisligi kadar yer kaplar. Kullanici karari (2026-10-05):
    acik kanat DUVAR DISINA cikmamali ve baska bir KAPININ alanina girmemeli.

    Yan secimi UYDURULMAZ: iki yan (baslangica / bitise) da denenir; en az
    biri uygunsa UYARI yok. Bir yan su durumlarda uygun DEGILDIR: (a) duvarin
    katı ucunun otesine tasar, (b) baska bir acikligin duvar araligina girer,
    (c) baska bir kapinin acilim sektoru ile kesisir (sektor
    `openings.collision.footprints`den gelir - cizilen yay ile ayni kaynak).
    Kanat, host_side yuzunde duvar kalinligi derinliginde bir dikdortgen
    olarak modellenir (v1)."""
    from collision.geometry import polygon_intersection_area
    from walls import Wall, WallCatalog

    from .collision import footprints

    sliding = [o for o in openings if o.get("type") == TYPE_DOOR and o.get("variant") == VARIANT_SLIDING]
    if not sliding:
        return []
    catalog = WallCatalog()
    wall_objs = {w["id"]: Wall.from_context(w, catalog) for w in walls}
    sectors = footprints({"walls": walls, "openings": openings}, {})
    spans = _spans(walls, openings)
    warnings: list[str] = []
    for op in sliding:
        wall = wall_objs.get(op["wall_id"])
        if wall is None or wall.length == 0:
            continue
        raw = next(w for w in walls if w["id"] == wall.id)
        solid_start = _end_overlap(tuple(raw["start"]), wall.id, walls)
        solid_end = _end_overlap(tuple(raw["end"]), wall.id, walls)
        g0 = op["position_from_start"] - op["width"] / 2.0
        g1 = op["position_from_start"] + op["width"] / 2.0
        sign = 1.0 if op.get("host_side", "pos") == "pos" else -1.0
        reasons: list[str] = []
        ok = False
        for name, a, b in (("baslangic", g0 - op["width"], g0), ("bitis", g1, g1 + op["width"])):
            if a < solid_start - 1e-6 or b > wall.length - solid_end + 1e-6:
                reasons.append(f"{name} yani duvar disina tasar")
                continue
            other = next((o["id"] for (x0, x1, o) in spans[wall.id]
                          if o["id"] != op["id"] and x0 < b - 1e-6 and x1 > a + 1e-6), None)
            if other:
                reasons.append(f"{name} yani '{other}' aciklik alanina girer")
                continue
            near = wall.normal[0] * sign, wall.normal[1] * sign
            lo = wall.thickness / 2.0
            hi = lo + wall.thickness
            rect = [
                (wall.start[0] + wall.direction[0] * x + near[0] * d, wall.start[1] + wall.direction[1] * x + near[1] * d)
                for x, d in ((a, lo), (b, lo), (b, hi), (a, hi))
            ]
            hit = next((sh.id for sh in sectors
                        if sh.id != op["id"] and polygon_intersection_area(list(sh.polygon), rect) > 1.0), None)
            if hit:
                reasons.append(f"{name} yani '{hit}' kapisinin acilim alanina girer")
                continue
            ok = True
            break
        if not ok:
            warnings.append(f"Surme kapi '{op['id']}' acildiginda kanat yer bulamiyor: " + "; ".join(reasons) + ".")
    return warnings


def check_opening_nuances(walls: list[dict], openings: list[dict]) -> list[str]:
    return (check_opening_wall_nuances(walls, openings)
            + check_sliding_door_parking(walls, openings)
            + check_door_leaf_clearance(walls, openings))
