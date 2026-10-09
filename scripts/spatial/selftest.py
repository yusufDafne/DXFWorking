#!/usr/bin/env python3
"""spatial modulu testleri (DEV-059).

Disiplin (kok CLAUDE.md): beklenen degerler ELLE hesaplanabilir; kurallar kasitli bozmayla
sinanir; her test yanlis-pozitif tarafini da sinar. NOT: `validate.py` cikisi 11 mekansal
yardimcinin 6'sina, `--golden-set` ise 9'una KORDUR (DEV-059 denetimi, mutasyon denemesi) -
bu yuzden tasimanin dogrulugu BURADAKI eski<->yeni diferansiyel testle kanitlanir.

Kullanim:  python scripts/spatial/selftest.py     Cikis: 0 basarili, 1 basarisiz.
"""
from __future__ import annotations

import itertools
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import spatial as sp  # noqa: E402
from collision.geometry import point_in_polygon, point_on_boundary  # noqa: E402

_TOUCH_TOLERANCE_MM = 300.0
_TOL = 1.0

# =====================================================================
# DONMUS ESKI UYGULAMALAR (DEV-059 oncesi, commit 9f97553'ten BIREBIR).
# Yalnizca diferansiyel test icin ORACLE'dir; uretim kodu DEGILDIR.
# =====================================================================
# --- architect/rules.py @ 9f97553 ---
def _door_midpoint(door: dict, walls_by_id: dict) -> tuple[float, float] | None:
    wall = walls_by_id.get(door.get("wall_id"))
    if wall is None:
        return None
    sx, sy = wall["start"]
    ex, ey = wall["end"]
    length = ((ex - sx) ** 2 + (ey - sy) ** 2) ** 0.5
    if length == 0:
        return (sx, sy)
    t = door["position_from_start"] / length
    return (sx + t * (ex - sx), sy + t * (ey - sy))

def _rooms_touching_point(point: tuple[float, float], rooms: list[dict],
                          tolerance: float = _TOUCH_TOLERANCE_MM) -> list[dict]:
    return [r for r in rooms if point_on_boundary(point, r["polygon"], tolerance)]

def _centroid(polygon: list[list[float]]) -> tuple[float, float]:
    xs = [p[0] for p in polygon]
    ys = [p[1] for p in polygon]
    return (sum(xs) / len(xs), sum(ys) / len(ys))

def _segments_intersect(p1, p2, p3, p4) -> bool:
    """Iki dogru parcasi GERCEKTEN (uc noktalarda DEGIL) kesisiyor mu -
    standart yon (cross-product) testi. Uc noktalarda dokunma KASITLI
    olarak KESISIM SAYILMAZ: goru hattinin kendi baslangic/bitis
    noktalari zaten bir duvarin UZERINDEDIR (kapinin oturdugu duvar),
    bu durum bir ENGEL degildir."""
    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    d1 = cross(p3, p4, p1)
    d2 = cross(p3, p4, p2)
    d3 = cross(p1, p2, p3)
    d4 = cross(p1, p2, p4)
    return ((d1 > 0 > d2 or d1 < 0 < d2)
            and (d3 > 0 > d4 or d3 < 0 < d4))

def _clear_line_of_sight(a: tuple[float, float], b: tuple[float, float],
                          walls: list[dict], exclude_wall_ids: set[str]) -> bool:
    """`a`-`b` dogru parcasi, `exclude_wall_ids` DISINDAKI herhangi bir
    duvarin MERKEZ CIZGISINI kesiyor mu? (duvar ayak izi merkez cizgidir -
    `collision/CLAUDE.md`deki AYNI bilinen basitlestirme)."""
    for wall in walls:
        if wall["id"] in exclude_wall_ids:
            continue
        if _segments_intersect(a, b, tuple(wall["start"]), tuple(wall["end"])):
            return False
    return True

def _shared_wall_length(poly_a: list[list[float]], poly_b: list[list[float]]) -> float:
    """Iki oda poligonunun ORTAK KENARININ (esdogrusal + ortusen) toplam
    uzunlugu. Koseden TEGET temas 0 sayilir; asgari ortak uzunluk sarti YOKTUR
    (kullanici karari) - herhangi bir gercek kenar paylasimi ortak duvardir."""
    total = 0.0
    na, nb = len(poly_a), len(poly_b)
    for i in range(na):
        a0, a1 = poly_a[i], poly_a[(i + 1) % na]
        ex, ey = a1[0] - a0[0], a1[1] - a0[1]
        elen = (ex * ex + ey * ey) ** 0.5
        if elen < 1e-9:
            continue
        for j in range(nb):
            b0, b1 = poly_b[j], poly_b[(j + 1) % nb]
            d0 = abs(ex * (b0[1] - a0[1]) - ey * (b0[0] - a0[0])) / elen
            d1 = abs(ex * (b1[1] - a0[1]) - ey * (b1[0] - a0[0])) / elen
            if d0 > 1.0 or d1 > 1.0:
                continue
            t0 = ((b0[0] - a0[0]) * ex + (b0[1] - a0[1]) * ey) / elen
            t1 = ((b1[0] - a0[0]) * ex + (b1[1] - a0[1]) * ey) / elen
            overlap = min(max(t0, t1), elen) - max(min(t0, t1), 0.0)
            if overlap > 1.0:
                total += overlap
    return total

# --- standards/nuances.py @ 9f97553 ---
def _n_dist_point_segment(p, a, b) -> float:
    ax, ay = a
    dx, dy = b[0] - ax, b[1] - ay
    seg2 = dx * dx + dy * dy
    t = 0.0 if seg2 == 0 else max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / seg2))
    return ((p[0] - ax - t * dx) ** 2 + (p[1] - ay - t * dy) ** 2) ** 0.5

def _n_point_in_polygon(point, polygon) -> bool:
    x, y = point
    inside = False
    n = len(polygon)
    for k in range(n):
        (x0, y0), (x1, y1) = polygon[k], polygon[(k + 1) % n]
        if (y0 > y) != (y1 > y) and x < (x1 - x0) * (y - y0) / (y1 - y0) + x0:
            inside = not inside
    return inside

def _n_touches(point, polygon, tol=_TOUCH_TOLERANCE_MM) -> bool:
    n = len(polygon)
    return any(
        _n_dist_point_segment(point, polygon[k], polygon[(k + 1) % n]) <= tol
        for k in range(n)
    )

def _n_door_mid(door: dict, walls_by_id: dict):
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

# --- shafts/__init__.py @ 9f97553 ---
def _s_shared_edge_length(poly_a, poly_b, tol: float = _TOL) -> float:
    """Iki poligonun (eksen-hizali kenarli) ORTAK kenar uzunlugu toplami (mm)."""
    def edges(poly):
        n = len(poly)
        for k in range(n):
            a, b = poly[k], poly[(k + 1) % n]
            yield a, b
    total = 0.0
    for a1, a2 in edges(poly_a):
        for b1, b2 in edges(poly_b):
            if abs(a1[0] - a2[0]) < tol and abs(b1[0] - b2[0]) < tol and abs(a1[0] - b1[0]) < tol:
                lo = max(min(a1[1], a2[1]), min(b1[1], b2[1])); hi = min(max(a1[1], a2[1]), max(b1[1], b2[1]))
                total += max(0.0, hi - lo)
            elif abs(a1[1] - a2[1]) < tol and abs(b1[1] - b2[1]) < tol and abs(a1[1] - b1[1]) < tol:
                lo = max(min(a1[0], a2[0]), min(b1[0], b2[0])); hi = min(max(a1[0], a2[0]), max(b1[0], b2[0]))
                total += max(0.0, hi - lo)
    return total


# nuances adlari: _n_* ; shafts: _s_*


# =====================================================================

def rect(x0, y0, x1, y1):
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


def _context():
    return json.load(open(ROOT / "context.json", encoding="utf-8"))


def check_hand_computed() -> list[str]:
    errors = []
    walls = {"w": {"id": "w", "start": [0.0, 0.0], "end": [4000.0, 0.0]}, "z": {"id": "z", "start": [5.0, 5.0], "end": [5.0, 5.0]}}
    if sp.door_midpoint({"wall_id": "w", "position_from_start": 1000.0}, walls) != (1000.0, 0.0):
        errors.append("door_midpoint 4000mm duvarda 1000mm -> (1000,0) olmali")
    if sp.door_midpoint({"wall_id": "yok", "position_from_start": 1.0}, walls) is not None:
        errors.append("bilinmeyen duvar -> None olmali")
    if sp.door_midpoint({"wall_id": "z", "position_from_start": 1.0}, walls) != (5.0, 5.0):
        errors.append("sifir uzunluklu duvar: door_midpoint duvar baslangici (5,5) olmali (eski architect davranisi)")
    if sp.door_frame({"wall_id": "z", "position_from_start": 1.0}, walls) != (None, None):
        errors.append("sifir uzunluklu duvar: door_frame (None, None) olmali (eski standards davranisi)")
    if sp.door_frame({"wall_id": "w", "position_from_start": 1000.0}, walls) != ((1000.0, 0.0), (1.0, 0.0)):
        errors.append("door_frame ((1000,0),(1,0)) olmali")
    if sp.vertex_mean(rect(0, 0, 4000, 2000)) != (2000.0, 1000.0):
        errors.append("vertex_mean dikdortgen merkezi (2000,1000) olmali")
    if not sp.segments_intersect((0, 0), (10, 10), (0, 10), (10, 0)):
        errors.append("X seklindeki iki parca kesismeli")
    if sp.segments_intersect((0, 0), (10, 0), (10, 0), (10, 10)):
        errors.append("uc noktada dokunma kesisim SAYILMAMALI (yanlis-pozitif)")
    wl = [{"id": "dik", "start": [5, -5], "end": [5, 5]}]
    if sp.clear_line_of_sight((0, 0), (10, 0), wl, set()):
        errors.append("duvar engel olmali")
    if not sp.clear_line_of_sight((0, 0), (10, 0), wl, {"dik"}):
        errors.append("haric tutulan duvar engel OLMAMALI (yanlis-pozitif)")
    if sp.shared_edge_length(rect(0, 0, 1000, 1000), rect(1000, 200, 2000, 700)) != 500.0:
        errors.append("ortak kenar elle hesap 500 olmali")
    if sp.shared_edge_length(rect(0, 0, 1000, 1000), rect(1500, 0, 2500, 1000)) != 0.0:
        errors.append("uzak poligonlar ortak kenar 0 (yanlis-pozitif)")
    if abs(sp.dist_point_segment((5, 5), (0, 0), (10, 0)) - 5.0) > 1e-12:
        errors.append("nokta-parca mesafesi 5 olmali")
    if not sp.touches_within((5, 3), rect(0, 0, 10, 10), 3.0) or sp.touches_within((5, 4), rect(0, 0, 10, 10), 3.0):
        errors.append("touches_within sinir: 3 icinde evet, 4'te hayir")
    return errors


def check_boundary_deltas_pinned() -> list[str]:
    """Kullanici karari (DEV-059 soru 2): tek anlam = mimari surum. Eski saft surumuyle DORT sinir
    farki burada SABITLENIR; tuketici esikleri (saft >=300 mm) bunlara duyarsizdir."""
    errors = []
    cases = {
        "0,5 mm ortusme": (rect(0, 0, 1000, 1000), rect(1000, 999.5, 2000, 2000), 0.0, 0.5),
        "tam 1,0 mm bosluk": (rect(0, 0, 1000, 1000), rect(1001, 0, 2000, 1000), 1000.0, 0.0),
        "tam 1,0 mm ortusme": (rect(0, 0, 1000, 1000), rect(1000, 999, 2000, 2000), 0.0, 1.0),
        "45 derece kenar": ([[0, 0], [1000, 1000], [0, 1000]], [[0, 0], [1000, 1000], [1000, 0]], 1000 * 2 ** 0.5, 0.0),
    }
    for name, (a, b, new_expected, old_shaft) in cases.items():
        new, old_arch, old_s = sp.shared_edge_length(a, b), _shared_wall_length(a, b), _s_shared_edge_length(a, b)
        if abs(new - new_expected) > 1e-9:
            errors.append(f"{name}: yeni {new} != {new_expected}")
        if abs(new - old_arch) > 1e-9:
            errors.append(f"{name}: yeni surum eski MIMARI surumden ayrisiyor ({new} vs {old_arch})")
        if abs(old_s - old_shaft) > 1e-9:
            errors.append(f"{name}: eski SAFT surumu beklenen {old_shaft} degil ({old_s}) - oracle bozuk")
    return errors


def check_differential_on_real_context() -> list[str]:
    """Gercek context.json (tum katlar): eski<->yeni AYNI cikti."""
    errors = []
    ctx = _context()
    n = {"door": 0, "touch": 0, "edge": 0, "los": 0}
    for fl in ctx["floors"]:
        walls_by_id = {w["id"]: w for w in fl["walls"]}
        rooms = fl["rooms"]
        for o in fl["openings"]:
            n["door"] += 1
            if sp.door_midpoint(o, walls_by_id) != _door_midpoint(o, walls_by_id):
                errors.append(f"door_midpoint ayrisiyor: {fl['id']}/{o['id']}")
            if sp.door_frame(o, walls_by_id) != _n_door_mid(o, walls_by_id):
                errors.append(f"door_frame ayrisiyor: {fl['id']}/{o['id']}")
            mid = _door_midpoint(o, walls_by_id)
            if mid is None:
                continue
            for r in rooms:
                n["touch"] += 1
                if (r in sp.rooms_touching_point(mid, rooms)) != (r in _rooms_touching_point(mid, rooms)):
                    errors.append(f"rooms_touching_point ayrisiyor: {fl['id']}/{o['id']}/{r['id']}")
                if sp.touches_within(mid, r["polygon"]) != _n_touches(mid, r["polygon"]):
                    errors.append(f"touches_within ayrisiyor: {fl['id']}/{o['id']}/{r['id']}")
        for ra, rb in itertools.combinations(rooms, 2):
            n["edge"] += 1
            if sp.shared_edge_length(ra["polygon"], rb["polygon"]) != _shared_wall_length(ra["polygon"], rb["polygon"]):
                errors.append(f"shared_edge_length ayrisiyor: {fl['id']}/{ra['id']}/{rb['id']}")
            # saft tuketicisinin esigi (>=300 mm): eski saft surumuyle AYNI karar
            if (sp.shared_edge_length(ra["polygon"], rb["polygon"]) >= 300.0) != (_s_shared_edge_length(ra["polygon"], rb["polygon"]) >= 300.0):
                errors.append(f"saft esigi (>=300) kararinda fark: {fl['id']}/{ra['id']}/{rb['id']}")
        for r in rooms:
            if sp.vertex_mean(r["polygon"]) != _centroid(r["polygon"]):
                errors.append(f"vertex_mean ayrisiyor: {r['id']}")
        pts = [(w["start"][0], w["start"][1]) for w in fl["walls"]][:8]
        for a, b in itertools.permutations(pts, 2):
            n["los"] += 1
            if sp.clear_line_of_sight(a, b, fl["walls"], set()) != _clear_line_of_sight(a, b, fl["walls"], set()):
                errors.append(f"clear_line_of_sight ayrisiyor: {fl['id']} {a}->{b}")
    if min(n.values()) == 0:
        errors.append(f"diferansiyel test bos calisti: {n}")
    return errors


def check_differential_synthetic() -> list[str]:
    """Deterministik tohumlu sentetik girdiler (nokta-poligon 3 uygulama, dogru parcasi, mesafe)."""
    errors = []
    state = [12345]

    def rnd():  # dogrusal kongruans: Math.random yok, tekrarlanabilir
        state[0] = (state[0] * 1103515245 + 12345) % (2 ** 31)
        return state[0] / 2 ** 31

    poly = [[0, 0], [6000, 0], [6000, 2400], [2400, 2400], [2400, 6000], [0, 6000]]
    for _ in range(4000):
        p = (rnd() * 7000 - 500, rnd() * 7000 - 500)
        if sp.point_in_polygon(p, poly) != _n_point_in_polygon(p, poly):
            errors.append(f"point_in_polygon (nuances) ayrisiyor {p}")
            break
        a, b = (rnd() * 100, rnd() * 100), (rnd() * 100, rnd() * 100)
        if sp.dist_point_segment(p, a, b) != _n_dist_point_segment(p, a, b):
            errors.append("dist_point_segment ayrisiyor")
            break
        c, d = (rnd() * 100, rnd() * 100), (rnd() * 100, rnd() * 100)
        if sp.segments_intersect(a, b, c, d) != _segments_intersect(a, b, c, d):
            errors.append("segments_intersect ayrisiyor")
            break
    return errors


def check_known_semantic_differences() -> list[str]:
    """BILINCLI ayri tutulan davranislar (kullanici karari 4 + denetim bulgusu) yine ayridir."""
    errors = []
    zero = {"z": {"id": "z", "start": [5.0, 5.0], "end": [5.0, 5.0]}}
    door = {"wall_id": "z", "position_from_start": 1.0}
    if sp.door_midpoint(door, zero) == sp.door_frame(door, zero)[0]:
        errors.append("sifir uzunluk: iki davranis ayri kalmali (birlestirmek ayri, acik degisiklik)")
    sq = rect(0, 0, 1000, 1000)
    # vertex_mean != alan agirlikli centroid: L-sekli
    L = [[0, 0], [6000, 0], [6000, 1000], [1000, 1000], [1000, 6000], [0, 6000]]
    # elle: x = (0+6000+6000+1000+1000+0)/6 = 14000/6; y ayni. Alan agirlikli centroid x =
    # (6e6*3000 + 5e6*500)/11e6 = 1954.5 -> ikisi FARKLIDIR.
    vm = sp.vertex_mean(L)
    if abs(vm[0] - 14000 / 6) > 1e-9 or abs(vm[1] - 14000 / 6) > 1e-9:
        errors.append(f"vertex_mean L-seklinde (14000/6, 14000/6) olmali, {vm}")
    if abs(vm[0] - 1954.5454545) < 1.0:
        errors.append("vertex_mean alan agirlikli centroid ile karismis")
    return errors


def check_mutation_is_detected() -> list[str]:
    """Kasitli bozma: bozuk bir door_midpoint diferansiyel testi GERCEKTEN kirmali."""
    ctx = _context()
    fl = ctx["floors"][3]
    walls_by_id = {w["id"]: w for w in fl["walls"]}
    broken = lambda door, w: (lambda m: None if m is None else (m[0] + 1.0, m[1]))(sp.door_midpoint(door, w))
    diffs = sum(1 for o in fl["openings"] if broken(o, walls_by_id) != _door_midpoint(o, walls_by_id))
    if diffs == 0:
        return ["diferansiyel test bozulmus door_midpoint'i YAKALAMIYOR - test anlamsiz"]
    return []


def main() -> int:
    checks = [check_hand_computed, check_boundary_deltas_pinned, check_differential_on_real_context,
              check_differential_synthetic, check_known_semantic_differences, check_mutation_is_detected]
    failed = 0
    for check in checks:
        errs = check()
        print(("[FAIL] " if errs else "[OK]   ") + check.__name__)
        for e in errs[:10]:
            print("   -", e)
        failed += bool(errs)
    print("spatial selftest:", "BASARISIZ" if failed else "BASARILI")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
