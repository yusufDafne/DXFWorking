"""Saft / havalandirma / baca bosluklari modulu (rev-27, kullanici karari).

Saft bir ODA DEGILDIR (kullanici karari 2026-10-05): `floors[].shafts[]` ile
ayri veri olarak bildirilir; komsu odalar poligonlarini saftin etrafindan
OYAR (saft odalarin icinde degil, onlarin disinda kalir). Uc tur vardir:
`tesisat`, `havalandirma`, `baca`.

Kullanici kurallari:
  - Saft DAIMA kare veya 4:3 dikdortgendir (`SHAFT_MAX_RATIO`).
  - Varsayilan kare saftin NET kenari 500 mm'dir (`DEFAULT_NET_SIDE_MM`);
    ek talebe gore degistirilebilir. Poligon (duvar merkez cizgisi) kenari =
    net + duvar kalinligi (`shaft_centerline_side`, varsayilan 650 mm).
  - Kat planinda saft bosluklari MINIMUM tutulur; WC/banyo diger dairelerle
    SIRT SIRTA verilir, olmuyorsa her banyo/WC cifti icin ikisinin ARASINA
    (ikisine de degen) bir saft konur (`check_wet_rooms_served`).
  - Saft asansor/merdiven odasinin icine veya kosesine GIRMEZ (HATA).

Bu modul YERLESIMI uretmez, DOGRULAR ve CIZER (`draw_shafts_on_floor`:
kapali kare + capraz, `SAFT` katmani). Proje verisi `context.json`dadir;
kutuphane (turler, varsayilan olculer) burada yasar. Ayrinti: CLAUDE.md.
"""
from __future__ import annotations

from dataclasses import dataclass

try:
    from ..collision.geometry import polygon_intersection_area, shoelace_area
    from ..palette import color_for
    from ..standards.measure import edge_wall_thicknesses, inset_polygon
except ImportError:
    from collision.geometry import polygon_intersection_area, shoelace_area
    from palette import color_for
    from standards.measure import edge_wall_thicknesses, inset_polygon

SHAFT_LAYER = "SAFT"
SHAFT_RGB = color_for(SHAFT_LAYER)

KIND_PLUMBING = "tesisat"
KIND_VENTILATION = "havalandirma"
KIND_CHIMNEY = "baca"
SHAFT_KINDS = (KIND_PLUMBING, KIND_VENTILATION, KIND_CHIMNEY)

# Kullanici karari (2026-10-05): kare saftin bir kenari ortalama 50 cm; ek
# talebe gore degisir. Tur basina farkli olcu UYDURULMAZ (yonetmelik verilmedi).
DEFAULT_NET_SIDE_MM = {kind: 500.0 for kind in SHAFT_KINDS}
DEFAULT_WALL_MM = 150.0
SHAFT_MAX_RATIO = 4.0 / 3.0
MIN_SHARED_EDGE_MM = 300.0   # "sirt sirta"/"degiyor" sayilmasi icin ortak kenar asgari uzunlugu
_TOL = 1.0
WET_TYPES = ("banyo", "wc")


def shaft_centerline_side(kind: str = KIND_PLUMBING, wall_mm: float = DEFAULT_WALL_MM,
                          net_mm: float | None = None) -> float:
    """Saftin NET kenari -> poligon (duvar merkez cizgisi) kenari: net + duvar
    kalinligi. Varsayilan: 500 + 150 = 650."""
    return (DEFAULT_NET_SIDE_MM[kind] if net_mm is None else net_mm) + wall_mm


@dataclass(frozen=True)
class Shaft:
    id: str
    kind: str
    polygon: tuple
    unit_id: str | None = None

    @classmethod
    def from_context(cls, data: dict) -> "Shaft":
        return cls(id=data["id"], kind=data["kind"],
                   polygon=tuple(tuple(map(float, p)) for p in data["polygon"]),
                   unit_id=data.get("unit_id"))

    @property
    def bbox(self) -> tuple[float, float, float, float]:
        xs = [p[0] for p in self.polygon]; ys = [p[1] for p in self.polygon]
        return min(xs), min(ys), max(xs), max(ys)

    @property
    def is_rectangle(self) -> bool:
        xs = {round(p[0], 3) for p in self.polygon}; ys = {round(p[1], 3) for p in self.polygon}
        return len(self.polygon) == 4 and len(xs) == 2 and len(ys) == 2

    @property
    def aspect_ratio(self) -> float:
        x0, y0, x1, y1 = self.bbox
        short, long_ = sorted((x1 - x0, y1 - y0))
        return float("inf") if short <= 0 else long_ / short


def shared_edge_length(poly_a, poly_b, tol: float = _TOL) -> float:
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


def check_shafts(floor: dict, units: str = "mm") -> tuple[list[str], list[str]]:
    """Arity-1 (bir kat): (errors, warnings). HATA: bilinmeyen tur, bir ODANIN icine
    girme (oda poligonuyla kesisim), asansor/merdiven odasinin icine/kosesine girme.
    UYARI: saft dikdortgen degil veya oran 4:3'ten buyuk; WC/banyo ne baska bir
    daireyle sirt sirta ne de bir safta degiyor; ayni daire WC+banyo cifti ikisine de
    degen bir saft icermiyor."""
    errors: list[str] = []
    warnings: list[str] = []
    rooms = floor.get("rooms", [])
    shafts = []
    for data in floor.get("shafts", []):
        if data.get("kind") not in SHAFT_KINDS:
            errors.append(f"Saft '{data.get('id')}': bilinmeyen tur '{data.get('kind')}'. Gecerli: {', '.join(SHAFT_KINDS)}.")
            continue
        shafts.append(Shaft.from_context(data))
    for shaft in shafts:
        if not shaft.is_rectangle:
            warnings.append(f"Saft '{shaft.id}' kare veya 4:3 DIKDORTGEN olmali (poligon dikdortgen degil).")
        elif shaft.aspect_ratio > SHAFT_MAX_RATIO + 1e-6:
            warnings.append(f"Saft '{shaft.id}' en-boy orani {shaft.aspect_ratio:.2f}; saft DAIMA kare veya 4:3 (<= {SHAFT_MAX_RATIO:.2f}) olmali.")
        for room in rooms:
            if len(room["polygon"]) < 3:
                continue
            inter = polygon_intersection_area([list(p) for p in shaft.polygon], room["polygon"])
            if inter > 1.0:   # 1 mm2'den fazla: komsu odalar saftin etrafindan OYULMUS olmali
                core = room.get("room_type") in ("asansor", "merdiven")
                where = "asansor/merdiven odasinin icine/kosesine giriyor" if core else "oda poligonuyla kesisiyor (oda saftin etrafindan oyulmali)"
                errors.append(f"Saft '{shaft.id}', '{room['id']}' {where}.")
    wet = [r for r in rooms if r.get("room_type") in WET_TYPES]
    plumbing = [s for s in shafts if s.kind == KIND_PLUMBING]
    for room in wet:
        poly = room["polygon"]
        back_to_back = any(
            o is not room and o.get("unit_id") != room.get("unit_id") and o.get("room_type") in WET_TYPES
            and shared_edge_length(poly, o["polygon"]) >= MIN_SHARED_EDGE_MM for o in wet)
        touches_shaft = any(shared_edge_length(poly, [list(p) for p in s.polygon]) >= MIN_SHARED_EDGE_MM for s in plumbing)
        if not back_to_back and not touches_shaft:
            warnings.append(
                f"Oda '{room['id']}' ({room['room_type']}): baska bir dairenin islak hacmiyle sirt sirta "
                f"degil ve bir tesisat saftina degmiyor - sirt sirta verilmeli veya yanina saft konmali.")
    by_unit: dict = {}
    for r in wet:
        if r.get("unit_id"):
            by_unit.setdefault(r["unit_id"], []).append(r)
    for unit, rs in sorted(by_unit.items()):
        for i, a in enumerate(rs):
            for b in rs[i + 1:]:
                if a["room_type"] == b["room_type"] or shared_edge_length(a["polygon"], b["polygon"]) < MIN_SHARED_EDGE_MM:
                    continue
                if not any(shared_edge_length(a["polygon"], [list(p) for p in s.polygon]) >= MIN_SHARED_EDGE_MM
                           and shared_edge_length(b["polygon"], [list(p) for p in s.polygon]) >= MIN_SHARED_EDGE_MM
                           for s in plumbing):
                    warnings.append(f"Birim '{unit}': '{a['id']}' ve '{b['id']}' bitisik ama ikisinin ARASINDA (ikisine de degen) tesisat safti yok.")
    return errors, warnings


def check_shafts_across_floors(floors: list[dict]) -> list[str]:
    """Saft dusey bir bosluktur: ayni `id` tasiyan saft, bulundugu TUM katlarda ayni
    poligonda olmali (UYARI)."""
    warnings: list[str] = []
    seen: dict[str, tuple] = {}
    for floor in floors:
        for data in floor.get("shafts", []):
            key = tuple(tuple(round(c, 3) for c in p) for p in data["polygon"])
            if data["id"] in seen and seen[data["id"]][0] != key:
                warnings.append(f"Saft '{data['id']}': '{floor['id']}' katinda '{seen[data['id']][1]}' katindakiyle AYNI konumda degil (saft dusey devam etmeli).")
            seen.setdefault(data["id"], (key, floor["id"]))
    return warnings


def ensure_shaft_layer(doc) -> None:
    """`SAFT` katmanini idempotent kurar (code-owned renk, `ensure_stair_layer` deseni)."""
    layer = doc.layers.get(SHAFT_LAYER) if SHAFT_LAYER in doc.layers else doc.layers.add(name=SHAFT_LAYER)
    layer.rgb = SHAFT_RGB


def net_polygon(shaft: Shaft, walls: list[dict] | None) -> list[list[float]]:
    """Saftin GERCEK BOSLUGU: poligon duvar merkez cizgisinde oldugu icin etrafindaki
    duvarlarin yarim kalinligi iceri alinir (500 net icin 650 poligon). Duvar yoksa
    poligonun kendisi."""
    poly = [list(p) for p in shaft.polygon]
    if not walls:
        return poly
    thickness = edge_wall_thicknesses(poly, walls)
    return inset_polygon(poly, thickness) if any(thickness) else poly


def draw_shafts_on_floor(msp, floor: dict) -> int:
    """Her saft icin kapali dikdortgen + iki capraz cizgi (`SAFT` katmani), DUVAR
    YUZLERI ARASINDAKI GERCEK BOSLUGUN (net) uzerine cizilir - duvar bandinin ustune degil.
    Cizilen saft sayisini doner."""
    n = 0
    for data in floor.get("shafts", []):
        if data.get("kind") not in SHAFT_KINDS:
            continue
        shaft = Shaft.from_context(data)
        poly = net_polygon(shaft, floor.get("walls"))
        xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
        x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
        msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], dxfattribs={"layer": SHAFT_LAYER}).closed = True
        msp.add_line((x0, y0), (x1, y1), dxfattribs={"layer": SHAFT_LAYER})
        msp.add_line((x1, y0), (x0, y1), dxfattribs={"layer": SHAFT_LAYER})
        n += 1
    return n


CONTRACT_VERSION = "1.1"  # rev-27b: cizim net (duvar yuzleri arasi) bosluga

__all__ = [
    "SHAFT_LAYER", "SHAFT_RGB", "SHAFT_KINDS", "KIND_PLUMBING", "KIND_VENTILATION", "KIND_CHIMNEY",
    "DEFAULT_NET_SIDE_MM", "DEFAULT_WALL_MM", "SHAFT_MAX_RATIO", "Shaft", "shaft_centerline_side",
    "shared_edge_length", "check_shafts", "check_shafts_across_floors", "ensure_shaft_layer",
    "draw_shafts_on_floor", "net_polygon", "CONTRACT_VERSION",
]
