"""Hol topolojisi kutuphanesi (DEV-054): bir birimin hol (koridor) sekli icin
PUANLANMIS ADAY LISTESI.

**Kullanici kararlari (2026-10-05):**
  - Hol L olmak ZORUNDA DEGIL; aday sekiller: duz (I), L, T, merkezi kare hub,
    en-boy orani korunan merkezi DIKDORTGEN hub. **Tarak VARSAYILAN DEGIL**,
    yalniz kullanici isterse eklenir (kayitli degil -> `register_topology`).
  - Aday kumesi KULLANICI BILDIRIMiyle (`allowed`) daraltilabilir.
  - WC kapisinin gorunmemesi icin KATI kural YOK; puan yalniz yerlesimin
    dogrulugunu olcer (hol payi, kapi cephesi, oran).
  - Simdilik DIK ACILI poligonlar; yeni (egik/aci) topoloji gerekirse
    `register_topology(id, builder)` ile eklenir (genisletme noktasi) - yeni
    bir gelistirme fikri olarak, bu modulde degil.

**Hesaplar, CIZMEZ, context'e YAZMAZ** (`options.py` ile AYNI sinir). Cikti
birim-yerel koordinatlardadir (0..W x 0..D, merkez cizgisi); dil modeli aday
KIMLIGIYLE secer, koordinat/sekil ICAT ETMEZ.

Puan bileskenleri (agent varsayilani, sabitler asagida):
  - kapi cephesi: holun oda tarafina bakan kenar uzunlugu / `n_rooms` kapi
    icin gereken uzunluk (kapi + 2x250mm: DEV-053 kapi araligi);
  - hol payi: hol alani / birim alani, `DEFAULT_CIRCULATION_SHARE_MAX` (%15)
    ustu cezali (`options`/`rules` ile AYNI sabit);
  - oran: AABB uzun kenar / en dar kol <= `STANDARDS['koridor'].max_ratio`.
Hol genisligi varsayilani `STANDARDS['koridor'].min_short_edge_mm` (NET
1500) + duvar kalinligi (poligon merkez cizgisinde).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

try:
    from ..standards import STANDARDS
    from ..standards.measure import arm_widths
except ImportError:
    from standards import STANDARDS
    from standards.measure import arm_widths

from .rules import DEFAULT_CIRCULATION_SHARE_MAX

TOPOLOGY_STRAIGHT = "duz"
TOPOLOGY_L = "L"
TOPOLOGY_T = "T"
TOPOLOGY_HUB_SQUARE = "merkezi_kare"
TOPOLOGY_HUB_RECT = "merkezi_dikdortgen"

DEFAULT_HUB_ASPECT_RATIO = 1.5
DEFAULT_DOOR_SLOT_PAD_MM = 250.0   # DEV-053: kapi basina yanlarda 250mm
WEIGHT_FRONTAGE, WEIGHT_SHARE, WEIGHT_RATIO = 0.40, 0.35, 0.25
VERTEX_TIEBREAK = 0.001            # esit puanda DAHA SADE sekil once
_TOL = 1.0

Polygon = list[list[float]]


@dataclass(frozen=True)
class HallOption:
    id: str
    label: str
    polygon: Polygon          # birim-yerel, merkez cizgisi, entry_side'a gore yonlendirilmis
    feasible: bool
    score: float
    area_m2: float
    share: float              # hol alani / birim alani
    frontage_mm: float        # odalara bakan kenar uzunlugu
    rationale: str
    metrics: dict = field(default_factory=dict)


def _clean(poly: Polygon) -> Polygon:
    """Ardisik tekrar eden ve ayni dogru uzerindeki (gereksiz) koseleri temizler."""
    pts = [list(p) for p in poly]
    changed = True
    while changed and len(pts) > 3:
        changed = False
        for k in range(len(pts)):
            a, b, c = pts[k - 1], pts[k], pts[(k + 1) % len(pts)]
            same = abs(b[0] - a[0]) < 1e-6 and abs(b[1] - a[1]) < 1e-6
            cross = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
            if same or abs(cross) < 1e-6:
                del pts[k]
                changed = True
                break
    return pts


def _rect(x0, y0, x1, y1) -> Polygon:
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


# --- kanonik cerceve: giris ALT kenarda (y=0), hol +y yonunde ----------------

def _build_straight(cw: float, cd: float, h: float, ctx: dict) -> Polygon:
    x0 = (cw - h) / 2.0
    return _rect(x0, 0.0, x0 + h, cd)


def _build_l(cw: float, cd: float, h: float, ctx: dict) -> Polygon:
    # dusey kol sol duvar boyunca (giristen uzak kenara), yatay kol uzak duvar boyunca
    return [[0, 0], [h, 0], [h, cd - h], [cw, cd - h], [cw, cd], [0, cd]]


def _build_t(cw: float, cd: float, h: float, ctx: dict) -> Polygon:
    x0, x1 = (cw - h) / 2.0, (cw + h) / 2.0
    return [[x0, 0], [x1, 0], [x1, cd - h], [cw, cd - h], [cw, cd], [0, cd], [0, cd - h], [x0, cd - h]]


def _hub(cw: float, cd: float, h: float, a: float, b: float) -> Polygon:
    hx0, hx1 = (cw - a) / 2.0, (cw + a) / 2.0
    y0 = (cd - b) / 2.0
    sx0, sx1 = (cw - h) / 2.0, (cw + h) / 2.0
    if y0 <= _TOL:
        return _rect(hx0, 0.0, hx1, b)
    return [[sx0, 0], [sx1, 0], [sx1, y0], [hx1, y0], [hx1, y0 + b],
            [hx0, y0 + b], [hx0, y0], [sx0, y0]]


def _hub_dims(h: float, ctx: dict, ratio: float) -> tuple[float, float]:
    """Gereken kapi cephesi cevresine gore (a x b), a/b = ratio, her ikisi >= h."""
    # hubun KENDI cevresi (giris sapinin acikligi h dusulerek) gereken kapi
    # cephesini saglamali: 2(a+b) - h >= gereken, a = ratio*b
    needed = ctx["required_frontage"] + h
    b = max(h, needed / (2.0 * (ratio + 1.0)))
    a = max(h, ratio * b)
    return a, b


def _build_hub_square(cw, cd, h, ctx):
    a, b = _hub_dims(h, ctx, 1.0)
    side = max(a, b)
    return _hub(cw, cd, h, side, side)


def _build_hub_rect(cw, cd, h, ctx):
    a, b = _hub_dims(h, ctx, ctx["hub_aspect_ratio"])
    return _hub(cw, cd, h, a, b)


TOPOLOGY_BUILDERS: dict[str, tuple[str, Callable]] = {
    TOPOLOGY_STRAIGHT: ("Duz (I) hol", _build_straight),
    TOPOLOGY_L: ("L hol", _build_l),
    TOPOLOGY_T: ("T hol", _build_t),
    TOPOLOGY_HUB_SQUARE: ("Merkezi kare hub", _build_hub_square),
    TOPOLOGY_HUB_RECT: ("Merkezi dikdortgen hub (oran korunur)", _build_hub_rect),
}
# Tarak (comb) BILEREK kayitli DEGIL (kullanici karari) - istenirse
# `register_topology` ile veya yeni bir gelistirme fikriyle eklenir.
DEFAULT_TOPOLOGIES: tuple[str, ...] = tuple(TOPOLOGY_BUILDERS)


def register_topology(topology_id: str, label: str, builder: Callable) -> None:
    """Genisletme noktasi (tarak, aci/egik yapilar...): `builder(cw, cd, h, ctx)`
    kanonik cerceve (giris alt kenar) icinde poligon dondurur. Dik acili
    olmayan sekiller icin kol/oran olcumu atlanir (`metrics['rectilinear']`)."""
    TOPOLOGY_BUILDERS[topology_id] = (label, builder)


# --- yonlendirme ve olcum ----------------------------------------------------

def _orient(poly: Polygon, entry_side: str, w: float, d: float) -> Polygon:
    if entry_side == "alt":
        return poly
    if entry_side == "ust":
        return [[x, d - y] for x, y in poly]
    if entry_side == "sol":
        return [[y, x] for x, y in poly]
    if entry_side == "sag":
        return [[w - y, x] for x, y in poly]
    raise ValueError(f"entry_side 'alt'/'ust'/'sol'/'sag' olmali, '{entry_side}' verildi.")


def _area(poly: Polygon) -> float:
    n = len(poly)
    return abs(0.5 * sum(poly[k][0] * poly[(k + 1) % n][1] - poly[(k + 1) % n][0] * poly[k][1] for k in range(n)))


def _frontage(poly: Polygon, w: float, d: float) -> float:
    """Birim sinirinda OLMAYAN (yani odalara bakan) kenarlarin toplam uzunlugu."""
    total, n = 0.0, len(poly)
    for k in range(n):
        (x0, y0), (x1, y1) = poly[k], poly[(k + 1) % n]
        on_boundary = (
            (abs(x0) <= _TOL and abs(x1) <= _TOL) or (abs(x0 - w) <= _TOL and abs(x1 - w) <= _TOL)
            or (abs(y0) <= _TOL and abs(y1) <= _TOL) or (abs(y0 - d) <= _TOL and abs(y1 - d) <= _TOL)
        )
        if not on_boundary:
            total += ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
    return total


def options_for_hall_topology(
    unit_width: float, unit_depth: float, *, entry_side: str = "alt", n_rooms: int = 4,
    door_width: float = 900.0, wall_thickness: float = 100.0,
    hall_width: float | None = None, allowed: tuple[str, ...] | None = None,
    hub_aspect_ratio: float = DEFAULT_HUB_ASPECT_RATIO,
    max_share: float = DEFAULT_CIRCULATION_SHARE_MAX,
) -> list[HallOption]:
    """Aday hol topolojileri, PUANA gore azalan (once uygulanabilir olanlar).

    `allowed`: kullanici bildirimiyle aday kumesi (varsayilan: kayitli tum
    topolojiler, tarak HARIC). Bilinmeyen kimlik `ValueError`. `hall_width`
    merkez-cizgisi genisligidir; verilmezse NET asgari koridor genisligi +
    `wall_thickness`. Sigmayan topoloji `feasible=False` ve nedeniyle doner."""
    ids = DEFAULT_TOPOLOGIES if allowed is None else tuple(allowed)
    unknown = [t for t in ids if t not in TOPOLOGY_BUILDERS]
    if unknown:
        raise ValueError(
            f"Kayitli olmayan hol topolojisi: {', '.join(unknown)}. Kayitli: "
            f"{', '.join(TOPOLOGY_BUILDERS)} (tarak/aci yapilar yeni bir gelistirme fikri)."
        )
    if entry_side not in ("alt", "ust", "sol", "sag"):
        raise ValueError(f"entry_side 'alt'/'ust'/'sol'/'sag' olmali, '{entry_side}' verildi.")
    standard = STANDARDS["koridor"]
    h = hall_width if hall_width is not None else (standard.min_short_edge_mm or 1500.0) + wall_thickness
    horizontal_entry = entry_side in ("sol", "sag")
    cw, cd = (unit_depth, unit_width) if horizontal_entry else (unit_width, unit_depth)
    required = n_rooms * (door_width + 2.0 * DEFAULT_DOOR_SLOT_PAD_MM)
    ctx = {"required_frontage": required, "hub_aspect_ratio": hub_aspect_ratio}
    unit_area = unit_width * unit_depth
    options: list[HallOption] = []
    for topology_id in ids:
        label, builder = TOPOLOGY_BUILDERS[topology_id]
        canonical = _clean(builder(cw, cd, h, ctx))
        xs, ys = [p[0] for p in canonical], [p[1] for p in canonical]
        fits = min(xs) >= -_TOL and max(xs) <= cw + _TOL and min(ys) >= -_TOL and max(ys) <= cd + _TOL
        poly = _orient(canonical, entry_side, unit_width, unit_depth)
        area = _area(poly)
        share = area / unit_area if unit_area else 0.0
        frontage = _frontage(poly, unit_width, unit_depth)
        if not fits:
            options.append(HallOption(topology_id, label, poly, False, 0.0, area / 1e6, share, frontage,
                                      f"{h:.0f}mm hol genisligi birime SIGMIYOR.", {"rectilinear": True}))
            continue
        rectilinear = all(abs(a[0] - b[0]) < 1e-6 or abs(a[1] - b[1]) < 1e-6
                          for a, b in zip(poly, poly[1:] + poly[:1]))
        s_front = min(1.0, frontage / required) if required else 1.0
        s_share = 1.0 if share <= max_share else max(0.0, 1.0 - (share - max_share) / max_share)
        s_ratio = 1.0
        if rectilinear:
            arms = arm_widths(poly)
            if arms:
                long_edge = max(max(p[0] for p in poly) - min(p[0] for p in poly),
                                max(p[1] for p in poly) - min(p[1] for p in poly))
                ratio = long_edge / min(arms)
                s_ratio = 1.0 if ratio <= standard.max_ratio else max(0.0, standard.max_ratio / ratio)
        score = (WEIGHT_FRONTAGE * s_front + WEIGHT_SHARE * s_share + WEIGHT_RATIO * s_ratio
                 - VERTEX_TIEBREAK * len(poly))
        options.append(HallOption(
            topology_id, label, poly, True, round(score, 4), area / 1e6, share, frontage,
            f"hol payi %{share * 100:.1f} (sinir %{max_share * 100:.0f}), kapi cephesi "
            f"{frontage:.0f}mm / gereken {required:.0f}mm.",
            {"rectilinear": rectilinear, "frontage_score": s_front, "share_score": s_share,
             "ratio_score": s_ratio},
        ))
    options.sort(key=lambda o: (not o.feasible, -o.score))
    return options


__all__ = [
    "HallOption", "options_for_hall_topology", "register_topology",
    "TOPOLOGY_BUILDERS", "DEFAULT_TOPOLOGIES", "DEFAULT_HUB_ASPECT_RATIO",
    "TOPOLOGY_STRAIGHT", "TOPOLOGY_L", "TOPOLOGY_T", "TOPOLOGY_HUB_SQUARE",
    "TOPOLOGY_HUB_RECT",
]
