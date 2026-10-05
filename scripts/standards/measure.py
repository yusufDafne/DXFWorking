"""Yerel en dar nokta olcumu (DEV-049, arity-1).

`__init__._aabb_edges` bir odanin YALNIZCA dis sinirlayici kutusunu olcer;
L/tarak seklinde bir hol poligonunun ortasindaki dar bir "bacak" dis kutuda
gorunmez. Bu modul poligonu iki eksen boyunca TARAR ve her kesitte (ic
bolge boyunca) gercek serbest genisligi bulur.

Serbest genislik = bir kesit dogrusunun (yatay ya da dusey) poligonun ICINDE
kalan parcasinin (chord) uzunlugu. Dikdortgen icin bu kisa kenardir; L'nin
dar bacagi icin bacak genisligidir. Tum chord'larin minimumu "yerel en dar
nokta"dir.

Dogruluk: eksen-hizali (rektilineer) poligonlarda TAMDIR - chord uzunlugu
iki ardisik kose koordinati arasinda sabit oldugundan, aralarin ORTA
noktalarindan ornekleme yeterlidir. Egik kenarli poligonlarda yaklasiktir
(yalnizca kose koordinatlarindan ornekler). Hicbir ucuncu parti kutuphane
kullanmaz; geometri URETMEZ.
"""
from __future__ import annotations

from dataclasses import dataclass

EPS = 1e-9


@dataclass(frozen=True)
class NarrowPoint:
    """`width`: en dar chord uzunlugu (poligon birimiyle). `axis`: chord'un
    yonu ('x' = yatay chord, 'y' = dusey chord). `at`: chord'un sabit
    koordinati (axis='x' ise Y degeri; 'y' ise X degeri). `span`: chord'un
    degisen eksendeki (baslangic, bitis) araligi."""

    width: float  # NET: chord uzunlugu - uc duvarlarin yarim kalinliklari
    axis: str
    at: float
    span: tuple[float, float]
    gross: float = 0.0  # merkez cizgisi chord uzunlugu (duvar dusulmemis)


def _chords(polygon: list[list[float]], axis: str, at: float) -> list[tuple[float, float, int, int]]:
    """`axis='x'`: y=at yatay dogrusunun poligon icindeki [x0,x1] parcalari;
    her parca (c0, c1, kenar_idx_baslangic, kenar_idx_bitis) doner."""
    i, j = (1, 0) if axis == "x" else (0, 1)
    crossings: list[tuple[float, int]] = []
    n = len(polygon)
    for k in range(n):
        a, b = polygon[k], polygon[(k + 1) % n]
        a_fix, b_fix = a[i], b[i]
        if (a_fix <= at < b_fix) or (b_fix <= at < a_fix):
            t = (at - a_fix) / (b_fix - a_fix)
            crossings.append((a[j] + t * (b[j] - a[j]), k))
    crossings.sort()
    return [(crossings[m][0], crossings[m + 1][0], crossings[m][1], crossings[m + 1][1])
            for m in range(0, len(crossings) - 1, 2)]


def narrowest_point(
    polygon: list[list[float]], edge_thickness: list[float] | None = None
) -> NarrowPoint | None:
    """Poligonun yerel en dar noktasi (bkz. modul dokstring); dejenere
    (<3 kose veya sifir alan) ise `None`.

    `edge_thickness[k]` = k. kenarin (polygon[k] -> polygon[k+1]) uzerindeki
    duvarin KALINLIGI. Verilirse genislik NET (duvar IC YUZLERI arasi) olur:
    chord'un iki ucundaki kenarlarin yarim kalinliklari dusulur (mimari
    gelenek: oda/koridor aciklari duvar ic kenarlariyla olculur - DEV-049).
    Verilmezse (`None`) poligon zaten net kabul edilir."""
    if len(polygon) < 3:
        return None
    best: NarrowPoint | None = None
    for axis, fix_idx in (("x", 1), ("y", 0)):
        coords = sorted({round(p[fix_idx], 6) for p in polygon})
        for lo, hi in zip(coords, coords[1:]):
            if hi - lo <= EPS:
                continue
            mid = (lo + hi) / 2.0
            for c0, c1, e0, e1 in _chords(polygon, axis, mid):
                gross = c1 - c0
                half = 0.0
                if edge_thickness is not None:
                    half = (edge_thickness[e0] + edge_thickness[e1]) / 2.0
                width = gross - half
                if gross > EPS and (best is None or width < best.width - EPS):
                    best = NarrowPoint(width, axis, mid, (c0, c1), gross)
    return best


def edge_wall_thicknesses(polygon: list[list[float]], walls: list[dict]) -> list[float]:
    """Her poligon kenari icin, ustunde uzanan (eşdogrusal + ortusen) en kalin
    duvarin kalinligi; duvar yoksa 0. Duvarlar ve poligon AYNI birimdedir.
    Bir kenar farkli kalinlikta birden cok duvara bolunuyorsa EN KALINI
    alinir (korumaci: net aciklik daha dar cikar)."""
    result: list[float] = []
    n = len(polygon)
    for k in range(n):
        a, b = polygon[k], polygon[(k + 1) % n]
        ex, ey = b[0] - a[0], b[1] - a[1]
        elen = (ex * ex + ey * ey) ** 0.5
        best = 0.0
        if elen > EPS:
            for wall in walls:
                ws, we = wall["start"], wall["end"]
                # her iki duvar ucu kenar dogrusuna <=1mm yakin mi (esdogrusal)
                d0 = abs(ex * (ws[1] - a[1]) - ey * (ws[0] - a[0])) / elen
                d1 = abs(ex * (we[1] - a[1]) - ey * (we[0] - a[0])) / elen
                if d0 > 1.0 or d1 > 1.0:
                    continue
                t0 = ((ws[0] - a[0]) * ex + (ws[1] - a[1]) * ey) / elen
                t1 = ((we[0] - a[0]) * ex + (we[1] - a[1]) * ey) / elen
                overlap = min(max(t0, t1), elen) - max(min(t0, t1), 0.0)
                if overlap > 1.0:
                    best = max(best, float(wall["thickness"]))
        result.append(best)
    return result


# --- DEV-050: net alan (madde 16 / acik karar 3) ve kesit olcumu ------------

def _signed_area(polygon: list[list[float]]) -> float:
    n = len(polygon)
    return 0.5 * sum(
        polygon[k][0] * polygon[(k + 1) % n][1] - polygon[(k + 1) % n][0] * polygon[k][1]
        for k in range(n)
    )


def inset_polygon(polygon: list[list[float]], edge_thickness: list[float]) -> list[list[float]]:
    """Her kenari, ustundeki duvarin YARIM kalinligi kadar iceri ceker
    (komsu kenar dogrularinin kesisimi). Paralel komsu kenarlarda kose,
    kendi kenar normali boyunca kaydirilir. Duvarlari merkez cizgisinde
    tanimli oda poligonundan duvar IC YUZLERI arasi NET poligonu uretir."""
    n = len(polygon)
    sign = 1.0 if _signed_area(polygon) > 0 else -1.0
    lines = []  # (nokta, yon) - iceri ofsetlenmis dogru
    for k in range(n):
        a, b = polygon[k], polygon[(k + 1) % n]
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = (dx * dx + dy * dy) ** 0.5 or 1.0
        nx, ny = -dy / length * sign, dx / length * sign
        d = edge_thickness[k] / 2.0
        lines.append(((a[0] + nx * d, a[1] + ny * d), (dx / length, dy / length), (nx, ny, d)))
    out: list[list[float]] = []
    for k in range(n):
        p1, d1, _ = lines[k - 1]
        p2, d2, (nx, ny, d) = lines[k]
        denom = d1[0] * d2[1] - d1[1] * d2[0]
        if abs(denom) < 1e-9:
            out.append([polygon[k][0] + nx * d, polygon[k][1] + ny * d])
            continue
        t = ((p2[0] - p1[0]) * d2[1] - (p2[1] - p1[1]) * d2[0]) / denom
        out.append([p1[0] + d1[0] * t, p1[1] + d1[1] * t])
    return out


def net_area(polygon: list[list[float]], edge_thickness: list[float]) -> float:
    """Duvar IC YUZLERI arasi net alan (poligon biriminin karesi)."""
    return abs(_signed_area(inset_polygon(polygon, edge_thickness)))


def chord_through(
    polygon: list[list[float]], point: tuple[float, float], direction: tuple[float, float],
    edge_thickness: list[float] | None = None,
) -> float | None:
    """`point`i iceren, `direction` yonundeki dogrunun poligon icindeki
    parcasinin (chord) NET uzunlugu; nokta poligonun disindaysa `None`."""
    n = len(polygon)
    dl = (direction[0] ** 2 + direction[1] ** 2) ** 0.5
    if dl < EPS:
        return None
    ux, uy = direction[0] / dl, direction[1] / dl
    hits: list[tuple[float, int]] = []
    for k in range(n):
        a, b = polygon[k], polygon[(k + 1) % n]
        ex, ey = b[0] - a[0], b[1] - a[1]
        denom = ux * ey - uy * ex
        if abs(denom) < 1e-9:
            continue
        t = ((a[0] - point[0]) * ey - (a[1] - point[1]) * ex) / denom
        s = ((a[0] - point[0]) * uy - (a[1] - point[1]) * ux) / denom
        if 0.0 <= s < 1.0:
            hits.append((t, k))
    hits.sort()
    for m in range(0, len(hits) - 1, 2):
        (t0, e0), (t1, e1) = hits[m], hits[m + 1]
        if t0 - 1e-6 <= 0.0 <= t1 + 1e-6:
            half = 0.0 if edge_thickness is None else (edge_thickness[e0] + edge_thickness[e1]) / 2.0
            return (t1 - t0) - half
    return None


def is_rectilinear(polygon: list[list[float]]) -> bool:
    n = len(polygon)
    return all(
        abs(polygon[k][0] - polygon[(k + 1) % n][0]) < 1e-6
        or abs(polygon[k][1] - polygon[(k + 1) % n][1]) < 1e-6
        for k in range(n)
    )


def is_convex(polygon: list[list[float]]) -> bool:
    n = len(polygon)
    signs = set()
    for k in range(n):
        a, b, c = polygon[k], polygon[(k + 1) % n], polygon[(k + 2) % n]
        cross = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
        if abs(cross) > 1e-6:
            signs.add(cross > 0)
    return len(signs) <= 1


def arm_rects(polygon: list[list[float]], edge_thickness: list[float] | None = None) -> list[dict]:
    """Dik acili (rektilineer) poligonun KOL dikdortgenleri: poligon yatay
    seritlere bolunur, ayni x-araligindaki komsu seritler birlestirilir. Her
    kol `{"rect": (x0, y0, x1, y1), "width": NET kol genisligi}` (merkezden
    gecen yatay/dusey net chord'larin kucugu). Rektilineer degilse bos liste."""
    if len(polygon) < 4 or not is_rectilinear(polygon):
        return []
    ys = sorted({round(p[1], 6) for p in polygon})
    rects: list[list[float]] = []  # [x0, x1, y0, y1]
    for lo, hi in zip(ys, ys[1:]):
        mid = (lo + hi) / 2.0
        for c0, c1, _, _ in _chords(polygon, "x", mid):
            for r in rects:
                if abs(r[0] - c0) < 1e-6 and abs(r[1] - c1) < 1e-6 and abs(r[3] - lo) < 1e-6:
                    r[3] = hi
                    break
            else:
                rects.append([c0, c1, lo, hi])
    arms: list[dict] = []
    for x0, x1, y0, y1 in rects:
        center = ((x0 + x1) / 2.0, (y0 + y1) / 2.0)
        h = chord_through(polygon, center, (1.0, 0.0), edge_thickness)
        v = chord_through(polygon, center, (0.0, 1.0), edge_thickness)
        found = [w for w in (h, v) if w is not None]
        if found:
            arms.append({"rect": (x0, y0, x1, y1), "width": min(found)})
    return arms


def arm_widths(polygon: list[list[float]], edge_thickness: list[float] | None = None) -> list[float]:
    """Dik acili poligonun KOL genislikleri (NET) - `arm_rects`in genislikleri."""
    return [a["width"] for a in arm_rects(polygon, edge_thickness)]
