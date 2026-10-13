"""Pencere varsayilan konumu ve ic duvar birlesimi (DEV-075).

Kullanici karari (2026-10-12): bir pencerenin VARSAYILAN konumu, ait oldugu odanin dis duvar boyunca uzanan SERBEST araliginin
(ic duvarlarin dis duvara baglandigi yerler cikarildiktan sonra kalan aralik) ortasidir; duvarin dis cepheye carptigi yerde pencere
olmamalidir. `position_from_start` (aciklik MERKEZI) verilmisse o gecerlidir; bu modul onu degistirmez - yalniz (a) varsayilani
hesaplar, (b) birlesim bolgesine dusen pencereyi UYARIR, (c) mevcut pencereler icin ortalanmis konum ONERIR (salt okunur).

Birlesim = baska bir duvarin UCU bu duvarin uzerinde (T/L; `spatial.dist_point_segment <= SHARED_EDGE_TOLERANCE_MM`) ve duvarlar paralel
degil. Birlesim bolgesi = iki yana o duvarin kalinliginin yarisi. Yeni tolerans sayisi YOKTUR.
"""
from __future__ import annotations

import math


def _length(w: dict) -> float:
    return math.dist(w["start"], w["end"])


def _t(w: dict, p) -> float:
    l = _length(w)
    return 0.0 if l < 1e-9 else ((p[0] - w["start"][0]) * (w["end"][0] - w["start"][0])
                                 + (p[1] - w["start"][1]) * (w["end"][1] - w["start"][1])) / l


def host_junctions(host: dict, walls: list[dict]) -> list[tuple[float, float, str]]:
    """Bu duvara UC UCA baglanan (paralel olmayan) duvarlar: [(t, kalinlik, duvar_id)], t'ye gore sirali."""
    from spatial import SHARED_EDGE_TOLERANCE_MM as TOL, dist_point_segment
    hx, hy = host["end"][0] - host["start"][0], host["end"][1] - host["start"][1]
    hl = math.hypot(hx, hy)
    out: list[tuple[float, float, str]] = []
    for w in walls:
        if w["id"] == host["id"]:
            continue
        wx, wy = w["end"][0] - w["start"][0], w["end"][1] - w["start"][1]
        wl = math.hypot(wx, wy)
        if hl < 1e-9 or wl < 1e-9 or abs(hx * wy - hy * wx) / (hl * wl) < 1e-6:
            continue                       # paralel/es dogrusal: birlesim degil, devam
        for p in (w["start"], w["end"]):
            if dist_point_segment(tuple(p), tuple(host["start"]), tuple(host["end"])) <= TOL:
                out.append((_t(host, p), float(w["thickness"]), w["id"]))
    return sorted(set(out))


def junction_zones(host: dict, walls: list[dict]) -> list[tuple[float, float, str]]:
    return [(t - th / 2.0, t + th / 2.0, wid) for t, th, wid in host_junctions(host, walls)]


def free_spans(host: dict, walls: list[dict]) -> list[tuple[float, float]]:
    """Duvar boyunca birlesim bolgeleri DISINDA kalan araliklar [(lo, hi)] (0..uzunluk icinde, pozitif uzunluklu)."""
    length = _length(host)
    spans: list[tuple[float, float]] = []
    cursor = 0.0
    for lo, hi, _wid in sorted(junction_zones(host, walls)):
        if lo > cursor:
            spans.append((cursor, min(lo, length)))
        cursor = max(cursor, hi)
    if cursor < length:
        spans.append((cursor, length))
    return [(a, b) for a, b in spans if b - a > 1e-9]


def _room_interval(host: dict, room: dict) -> tuple[float, float] | None:
    """Oda poligonunun bu duvarla ortusen kenarlarinin duvar uzerindeki izdusumu (govde araligi)."""
    from spatial import SHARED_EDGE_TOLERANCE_MM as TOL, wall_edge_overlap
    poly, length = room["polygon"], _length(host)
    los, his = [], []
    for k in range(len(poly)):
        a, b = poly[k], poly[(k + 1) % len(poly)]
        if wall_edge_overlap(host["start"], host["end"], a, b) > TOL:
            ta, tb = _t(host, a), _t(host, b)
            los.append(max(0.0, min(ta, tb)))
            his.append(min(length, max(ta, tb)))
    return (min(los), max(his)) if los else None


def room_span(host: dict, room: dict, walls: list[dict]) -> tuple[float, float] | None:
    """Odanin bu duvar boyunca kullanabilecegi SERBEST aralik: odanin duvarla ortusen govdesi ile en cok kesisen serbest aralik, ODANIN KENDI
    SINIRINA kirpilmis. Iki oda arasinda duvar yoksa (acik plan, ornek salon|mutfak) serbest aralik iki odayi birden kapsar; pencere kendi
    odasinin sinirinda biter, komsu odaya tasmaz."""
    interval = _room_interval(host, room)
    if interval is None:
        return None
    best, best_overlap = None, 0.0
    for lo, hi in free_spans(host, walls):
        overlap = min(hi, interval[1]) - max(lo, interval[0])
        if overlap > best_overlap:
            best, best_overlap = (max(lo, interval[0]), min(hi, interval[1])), overlap
    return best


def occupied_gaps(host: dict, openings: list[dict], exclude_id: str | None = None) -> list[tuple[float, float, str]]:
    """Bu duvardaki penceresiz (kapi/gecis/asansor kapisi) aciklik bosluklari: [(lo, hi, id)] (`position_from_start` MERKEZDIR).
    Pencere ortalanirken bu bosluklar serbest aralikdan CIKARILIR; diger pencereler cikarilmaz (ayni odada birden fazla pencere
    icin ortalama anlamli degildir, bkz. `placement_suggestions` `shared`)."""
    out = []
    for o in openings:
        if o.get("wall_id") != host["id"] or o.get("type") == "window" or o.get("id") == exclude_id:
            continue
        c, w = float(o["position_from_start"]), float(o["width"])
        out.append((c - w / 2.0, c + w / 2.0, str(o["id"])))
    return sorted(out)


def subtract_gaps(span: tuple[float, float], gaps: list[tuple[float, float, str]]) -> list[tuple[float, float]]:
    """`span` icinden bosluklari cikarir; kalan pozitif uzunluklu parcalar sirali doner."""
    cursor, out = span[0], []
    for lo, hi, _i in sorted(gaps):
        if hi <= cursor or lo >= span[1]:
            continue
        if lo > cursor:
            out.append((cursor, lo))
        cursor = max(cursor, hi)
    if cursor < span[1]:
        out.append((cursor, span[1]))
    return [(a, b) for a, b in out if b - a > 1e-9]


def default_window_position(host: dict, room: dict, walls: list[dict], width: float, gaps=None, near: float | None = None) -> float | None:
    """Pencere merkezi (`position_from_start`): odanin serbest araliginin ortasi. Aralik pencereden dar ya da oda bu duvarla
    ortusmuyorsa None (sigmaz; uydurma konum YOK). `gaps` (bkz. `occupied_gaps`) verilirse serbest aralik once kapi/gecis bosluklarindan
    arindirilir; pencereyi alabilen parcalar arasindan `near` noktasini iceren (yoksa ona en yakin; `near` yoksa en genis) secilir
    ve ORTALANIR."""
    span = room_span(host, room, walls)
    if span is None:
        return None
    parts = [pt for pt in subtract_gaps(span, gaps or []) if pt[1] - pt[0] >= width]
    if not parts:
        return None
    if near is None:
        lo, hi = max(parts, key=lambda pt: pt[1] - pt[0])
    else:
        lo, hi = min(parts, key=lambda pt: 0.0 if pt[0] <= near <= pt[1] else min(abs(near - pt[0]), abs(near - pt[1])))
    return (lo + hi) / 2.0


def check_opening_overlaps(floor: dict) -> list[str]:
    """validate.py UYARILARI: AYNI duvardaki iki aciklik (pencere/kapi/gecis) birbirine 1 mm'den fazla giriyorsa. Temas uyari degildir."""
    from spatial import SHARED_EDGE_TOLERANCE_MM as TOL
    ops = [o for o in floor.get("openings", []) if o.get("wall_id") and "position_from_start" in o and "width" in o]
    out: list[str] = []
    for i, a in enumerate(ops):
        for b in ops[i + 1:]:
            if a["wall_id"] != b["wall_id"]:
                continue
            alo, ahi = float(a["position_from_start"]) - float(a["width"]) / 2.0, float(a["position_from_start"]) + float(a["width"]) / 2.0
            blo, bhi = float(b["position_from_start"]) - float(b["width"]) / 2.0, float(b["position_from_start"]) + float(b["width"]) / 2.0
            if min(ahi, bhi) - max(alo, blo) > TOL:
                out.append(f"Aciklik '{a['id']}' ({alo:.0f}-{ahi:.0f} mm) ile '{b['id']}' ({blo:.0f}-{bhi:.0f} mm) ayni duvarda ('{a['wall_id']}') ust uste biniyor.")
    return out


def check_window_junctions(floor: dict) -> list[str]:
    """validate.py UYARILARI: pencere boslugu bir ic duvarin bu duvara baglandigi bolgeye (yarim kalinlik) giriyorsa. Temas uyari degildir;
    1 mm'den fazla ortusme uyaridir."""
    from spatial import SHARED_EDGE_TOLERANCE_MM as TOL
    walls = floor.get("walls", [])
    by_id = {w["id"]: w for w in walls}
    out: list[str] = []
    for op in floor.get("openings", []):
        if op.get("type") != "window":
            continue
        host = by_id.get(op.get("wall_id"))
        if host is None:
            continue
        lo = float(op["position_from_start"]) - float(op["width"]) / 2.0
        hi = float(op["position_from_start"]) + float(op["width"]) / 2.0
        for zlo, zhi, wid in junction_zones(host, walls):
            if min(hi, zhi) - max(lo, zlo) > TOL:
                out.append(f"Pencere '{op['id']}' ({host['id']}, {lo:.0f}-{hi:.0f} mm): ic duvar '{wid}' dis duvara bu bolgede "
                           f"({zlo:.0f}-{zhi:.0f} mm) baglaniyor - duvarin dis cepheye carptigi yerde pencere olmamali; "
                           "pencere ic duvarlar arasinda ortalanmali.")
    return out


def placement_suggestions(floor: dict) -> list[dict]:
    """Salt okunur: her pencere icin ait oldugu odanin serbest araligina gore ORTALANMIS konum onerisi.
    {window, wall, room, current, suggested (None = sigmaz/oda yok), delta, span, shared (ayni odada ayni duvardaki pencere sayisi)}.
    `shared` > 1 ise oneri TEK pencere varsayar: birden fazla pencere icin ortalama anlamli degildir, oneri bilgi amaclidir."""
    from spatial import window_rooms
    walls = floor.get("walls", [])
    by_id = {w["id"]: w for w in walls}
    rooms = floor.get("rooms", [])
    out: list[dict] = []
    for op in floor.get("openings", []):
        if op.get("type") != "window":
            continue
        host = by_id.get(op.get("wall_id"))
        if host is None:
            continue
        cur = float(op["position_from_start"])
        best = None
        for r in window_rooms(op, by_id, rooms):
            sp = room_span(host, r, walls)
            if sp is not None and sp[0] - 1e-9 <= cur <= sp[1] + 1e-9:
                best = (r, sp)
                break
            if sp is not None and best is None:
                best = (r, sp)
        if best is None:
            out.append({"window": op["id"], "wall": host["id"], "room": None, "current": cur, "suggested": None, "delta": None,
                        "span": None, "shared": 0, "blocked_by": []})
            continue
        r, sp = best
        gaps = occupied_gaps(host, floor.get("openings", []), exclude_id=op["id"])
        sug = default_window_position(host, r, walls, float(op["width"]), gaps=gaps, near=cur)
        blocked = [i for lo, hi, i in gaps if min(hi, sp[1]) - max(lo, sp[0]) > 1e-9]
        out.append({"window": op["id"], "wall": host["id"], "room": r["id"], "current": cur, "suggested": sug,
                    "delta": None if sug is None else sug - cur, "span": sp, "shared": 0, "blocked_by": blocked})
    for row in out:        # ayni oda + ayni duvar uzerindeki pencere sayisi
        row["shared"] = sum(1 for o in out if o["room"] == row["room"] and o["wall"] == row["wall"]) if row["room"] else 0
    return out
