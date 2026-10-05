"""Etut 2D yerlesim optimizasyonu - ZONLAMA (DEV-056).

**Kullanici karari (2026-10-05):** bina oturum alanini efektif kullanmak en
onemli konulardan biridir ve bundan sorumlu birim etuttur. Etut, mimari planin
olusturulabilmesi icin ETUDU sunar (bugun son kullaniciya sunumu yok; gelecekte
kullanici yalniz etut isteyip adaylar arasindan secim yapabilir). **Deterministik**
ilerler: ayni girdi -> ayni siralama. Dil modeli sistemin yeteneklerini bilir,
ona gore adim atar, gerekirse gelistiriciden secimini duzeltmesini ister; olcu/
koordinat/esik UYDURMAZ ve `context.json`a YAZMAZ.

**Kullanicinin KESINLIKLE saglamasi gereken veri:** kat olculeri ve **birim
programi** (kac daire, hangi tip: `1+1`, `2+1`...). Dil modeli yalnizca "bu kat
oturum alanina kac daire / kac odali olabilir" geri bildirimi verebilir
(`suggest_unit_mixes`). Mevcut projenin kurgusu `CURRENT_PROJECT_PROGRAM`
(2 adet 2+1, 1 adet 1+1) ornek/test girdisidir, varsayilan DEGILDIR.

**Kapsam:** yalniz ZONLAMA (daire SINIRLARI). Daire ici oda bolunturusu bu
maddenin disindadir (yeni gelistirme fikri, DEV-057 notu); kullanici detayli
etut isterse o cikti ayrica uretilir.

**Yontem (aciklanabilir, kural tabanli arama):**
  1. `core_hall.options_for_central_hall` (DEV-055) bes merkezi cekirdek+hol
     alternatifi verir (blok = cekirdek satiri + kat holu).
  2. Kat, blok disinda kalan HALKA, 4 dikdortgen "bolum"e ayrilir; 16 desen
     denenir (her kose bolgesi iki komsu kenardan birine verilir; H-x, H-y ve
     ruzgar gulleri bunlarin icindedir).
  3. Bolumler komsu gruplara birlestirilir (N daire icin N ardisik yay; N>4
     ise en buyuk bolum esit bolunur) ve birim tiplerine atanir (N<=4 icin tum
     permutasyonlar, daha fazlasi icin alan sirali acgozlu).
  4. SERT KAPI: her bolge hol cephesine (kapi + 2x250mm) temas etmeli
     (giris kapisi holden acilir); alan >= birim asgarisi.
  5. PUAN (varsayilan agirliklar `StudyWeights`, agent'in "optimum" secimi;
     kullanici ornek ciktilari yorumladikca ayarlanir): alan uyumu, cephe,
     oran, hol payi, hol secenegi puani.
Birim ici hol topolojisi onerisi (DEV-054) dikdortgen bolgeler icin eklenir.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass, field

try:
    from ..standards import STANDARDS
except ImportError:
    from standards import STANDARDS

from .core_hall import CentralHallOption, options_for_central_hall
from .rules import DEFAULT_CIRCULATION_SHARE_MAX
from .topology import options_for_hall_topology

# --- birim tipleri (kutuphane varsayilani, "v1 pratik varsayilan") ----------
@dataclass(frozen=True)
class UnitType:
    id: str
    label: str
    habitable_rooms: int      # salon + yatak odalari (cephe/pencere ihtiyaci)
    min_area_m2: float        # brut (duvar dahil) asgari
    ideal_area_m2: float      # brut ideal


UNIT_TYPES: dict[str, UnitType] = {
    "1+1": UnitType("1+1", "1+1 daire", 2, 50.0, 62.0),
    "2+1": UnitType("2+1", "2+1 daire", 3, 80.0, 95.0),
    "3+1": UnitType("3+1", "3+1 daire", 4, 110.0, 130.0),
}
FACADE_PER_ROOM_MM = 3000.0     # yasanabilir oda basina cephe uzunlugu (pencere)
DOOR_SLOT_MM = 900.0 + 2 * 250.0  # giris kapisi + kapi araligi payi

# Ornek/test girdisi (varsayilan DEGIL): mevcut projenin kurgusu.
CURRENT_PROJECT_PROGRAM: tuple[tuple[str, str], ...] = (("uA", "2+1"), ("uB", "2+1"), ("uC", "1+1"))


@dataclass(frozen=True)
class StudyWeights:
    """Etut puan agirliklari (toplam 1.0). Agent'in baslangic "optimum" secimi;
    kullanici ornek ciktilari yorumladikca zaman icinde optimize edilir."""
    area_fit: float = 0.35
    facade: float = 0.20
    proportion: float = 0.15
    hall_share: float = 0.15
    hall_option: float = 0.15


@dataclass(frozen=True)
class ZonePlan:
    unit_id: str
    unit_type: str
    rects: list                 # [(x0, y0, x1, y1), ...] kat yerel mm
    polygon: list               # birlesik dik acili poligon (merkez cizgisi)
    area_m2: float
    access_mm: float            # hol cephesine temas uzunlugu
    facade_mm: float            # kat sinirina bakan uzunluk
    short_edge_mm: float        # en dar kol
    hall_topology: str | None   # DEV-054 onerisi (yalniz dikdortgen bolgede)


@dataclass(frozen=True)
class StudyOption:
    id: str
    hall_option: str
    pattern: str
    zones: list
    feasible: bool
    score: float
    breakdown: dict
    rationale: str
    block: tuple = ()
    problems: list = field(default_factory=list)
    offset: tuple = (0.0, 0.0)       # blogun kat merkezinden kaymasi (mm)
    structure: tuple = ()            # (hol id, desen, gruplama indeksi, atama) - yeniden kurmak icin


# --- geometri yardimcilari ---------------------------------------------------

def _area(r) -> float:
    return (r[2] - r[0]) * (r[3] - r[1])


def _union_polygon(rects: list) -> list:
    """Dik acili dikdortgenlerin BIRLESIM poligonu (koordinat sikistirma +
    sinir izleme); tek bir baglantili bolge varsayar, dogrusal koseleri atar."""
    xs = sorted({v for r in rects for v in (r[0], r[2])})
    ys = sorted({v for r in rects for v in (r[1], r[3])})
    filled = {(i, j) for i in range(len(xs) - 1) for j in range(len(ys) - 1)
              if any(r[0] <= xs[i] and xs[i + 1] <= r[2] and r[1] <= ys[j] and ys[j + 1] <= r[3] for r in rects)}
    edges = {}
    for i, j in filled:
        if (i, j - 1) not in filled:
            edges[(xs[i], ys[j])] = (xs[i + 1], ys[j])          # alt kenar, saat yonu tersi
        if (i + 1, j) not in filled:
            edges[(xs[i + 1], ys[j])] = (xs[i + 1], ys[j + 1])  # sag
        if (i, j + 1) not in filled:
            edges[(xs[i + 1], ys[j + 1])] = (xs[i], ys[j + 1])  # ust
        if (i - 1, j) not in filled:
            edges[(xs[i], ys[j + 1])] = (xs[i], ys[j])          # sol
    start = min(edges)
    poly, cur = [start], edges[start]
    while cur != start:
        poly.append(cur)
        cur = edges[cur]
    out = []
    n = len(poly)
    for k in range(n):
        a, b, c = poly[k - 1], poly[k], poly[(k + 1) % n]
        if (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0]) != 0:
            out.append([float(b[0]), float(b[1])])
    return out


def _overlap_1d(a0, a1, b0, b1) -> float:
    return max(0.0, min(a1, b1) - max(a0, b0))


def _edge_overlap(rect, seg) -> float:
    """`rect` kenarlari ile `seg` (x0,y0,x1,y1; eksen hizali) ortusme uzunlugu."""
    sx0, sy0, sx1, sy1 = seg
    x0, y0, x1, y1 = rect
    total = 0.0
    if abs(sy0 - sy1) < 1e-6:        # yatay segment
        for y in (y0, y1):
            if abs(y - sy0) < 1e-6:
                total += _overlap_1d(x0, x1, min(sx0, sx1), max(sx0, sx1))
    else:                             # dusey segment
        for x in (x0, x1):
            if abs(x - sx0) < 1e-6:
                total += _overlap_1d(y0, y1, min(sy0, sy1), max(sy0, sy1))
    return total


def _facade_length(rect, w, d) -> float:
    x0, y0, x1, y1 = rect
    total = 0.0
    if abs(x0) < 1e-6: total += y1 - y0
    if abs(x1 - w) < 1e-6: total += y1 - y0
    if abs(y0) < 1e-6: total += x1 - x0
    if abs(y1 - d) < 1e-6: total += x1 - x0
    return total


def _hall_frontage(option: CentralHallOption) -> tuple[tuple, list]:
    """(hol dikdortgeni, hol cephe segmentleri) - kat yerel, son yonde."""
    bx0, by0, bx1, by1 = option.block
    horiz = option.orientation == "x"
    if horiz:
        hall = (bx0, by0, bx1, by0 + option.hall_depth) if option.core_side == "north" \
            else (bx0, by1 - option.hall_depth, bx1, by1)
    else:
        hall = (bx0, by0, bx0 + option.hall_depth, by1) if option.core_side == "north" \
            else (bx1 - option.hall_depth, by0, bx1, by1)
    hx0, hy0, hx1, hy1 = hall
    segs = [(hx0, hy0, hx1, hy0), (hx0, hy1, hx1, hy1), (hx0, hy0, hx0, hy1), (hx1, hy0, hx1, hy1)]
    # cekirdek satirina komsu kenar cephe DEGILDIR (bloga ait): blok siniri
    # disindaki kenarlar da zaten yalniz blogun dis yuzu olanlardir.
    core = (bx0, by0, bx1, by1)
    keep = []
    for s in segs:
        shared_with_core = _edge_overlap(core, s) > 0 and _is_interior_to_block(s, core, hall)
        if not shared_with_core:
            keep.append(s)
    return hall, keep


def _is_interior_to_block(seg, block, hall) -> bool:
    """Segment blogun ICINDE mi (hol-cekirdek ortak kenari)?"""
    bx0, by0, bx1, by1 = block
    sx0, sy0, sx1, sy1 = seg
    if abs(sy0 - sy1) < 1e-6:
        return by0 + 1e-6 < sy0 < by1 - 1e-6
    return bx0 + 1e-6 < sx0 < bx1 - 1e-6


def _patterns(w, d, block) -> dict:
    """16 halka bolme deseni: 4 kose bolgesinin her biri komsu iki kenar
    seridinden BIRINE verilir (2^4); her kenar = serit + atanan koseler (daima
    dikdortgen). H-x, H-y ve iki ruzgar gulu bunlarin icindedir. Her desen
    [S, E, N, W] cevrim sirasinda doner (komsu bolumler ardisiktir)."""
    bx0, by0, bx1, by1 = block
    out = {}
    for bits in itertools.product((0, 1), repeat=4):
        sw, se, ne, nw = bits  # 0: yatay kenara (S/N), 1: dusey kenara (W/E)
        south = (0 if sw == 0 else bx0, 0, w if se == 0 else bx1, by0)
        east = (bx1, 0 if se == 1 else by0, w, d if ne == 1 else by1)
        north = (0 if nw == 0 else bx0, by1, w if ne == 0 else bx1, d)
        west = (0, 0 if sw == 1 else by0, bx0, d if nw == 1 else by1)
        out["".join(map(str, bits))] = [south, east, north, west]
    return out


def _arcs(n_sections: int, n_zones: int) -> list:
    """Dairesel dizide `n_zones` ardisik yaya bolme (her yay = komsu bolum
    indeks listesi). Tum baslangic donusleri uretilir (tekrarlar elenir)."""
    seen, out = set(), []
    for start in range(n_sections):
        for cuts in itertools.combinations(range(1, n_sections), n_zones - 1):
            bounds = [0, *cuts, n_sections]
            arcs = tuple(tuple((start + k) % n_sections for k in range(bounds[i], bounds[i + 1]))
                         for i in range(n_zones))
            key = frozenset(frozenset(a) for a in arcs)
            if key not in seen:
                seen.add(key)
                out.append(arcs)
    return out


def _split_to(rects: list, n: int) -> list:
    """N>4 icin en buyuk dikdortgeni uzun kenari boyunca esit ikiye boler."""
    rects = list(rects)
    while len(rects) < n:
        i = max(range(len(rects)), key=lambda k: _area(rects[k]))
        x0, y0, x1, y1 = rects.pop(i)
        if (x1 - x0) >= (y1 - y0):
            m = (x0 + x1) / 2.0
            rects += [(x0, y0, m, y1), (m, y0, x1, y1)]
        else:
            m = (y0 + y1) / 2.0
            rects += [(x0, y0, x1, m), (x0, m, x1, y1)]
    return rects


# --- ana API -------------------------------------------------------------------

def suggest_unit_mixes(floor_width: float, floor_depth: float, *, max_units: int = 4,
                       wall_allowance: float = 0.08) -> list[dict]:
    """Dil modelinin "bu kat oturum alanina kac daire / kac odali olabilir"
    sorusuna deterministik, hesaplanmis geri bildirim: blok (en yuksek puanli
    merkezi hol alternatifinin) ve duvar payi dusulunce kalan alana sigan
    daire karisimlari (her birim >= asgari alan). Sonuc doluluk oranina gore
    (ideal toplam / kullanilabilir) 1'e yakin olandan siralanir."""
    hall = next((o for o in options_for_central_hall(floor_width, floor_depth) if o.feasible), None)
    block_area = hall.hall_area_m2 + hall.hall_width * 3000.0 / 1e6 if hall else 0.0
    available = floor_width * floor_depth / 1e6 * (1.0 - wall_allowance) - block_area
    mixes: list[dict] = []
    for n in range(1, max_units + 1):
        for combo in itertools.combinations_with_replacement(sorted(UNIT_TYPES), n):
            need_min = sum(UNIT_TYPES[t].min_area_m2 for t in combo)
            need_ideal = sum(UNIT_TYPES[t].ideal_area_m2 for t in combo)
            if need_min > available:
                continue
            mixes.append({"mix": combo, "units": n, "min_total_m2": need_min,
                          "ideal_total_m2": need_ideal, "available_m2": round(available, 1),
                          "fill_ratio": round(need_ideal / available, 3)})
    mixes.sort(key=lambda m: (abs(1.0 - m["fill_ratio"]), -m["units"], m["mix"]))
    return mixes


MAX_REFINE_OFFSET_MM = 4000.0
REFINE_STEPS_MM = (1000.0, 250.0)
REFINE_TOP = 12


def _groupings(ordered: list, n: int) -> list:
    if n <= len(ordered):
        return [[[ordered[i] for i in arc] for arc in arcs] for arcs in _arcs(len(ordered), n)]
    return [[[r] for r in _split_to(ordered, n)]]


def _perms(groups: list, program, n: int) -> list:
    if n <= 4:
        return list(itertools.permutations(range(n)))
    areas = [sum(_area(r) for r in g) / 1e6 for g in groups]  # alan sirali acgozlu
    units_desc = sorted(range(n), key=lambda i: -UNIT_TYPES[program[i][1]].ideal_area_m2)
    zones_desc = sorted(range(n), key=lambda i: -areas[i])
    greedy = {u: z for u, z in zip(units_desc, zones_desc)}
    return [tuple(greedy[u] for u in range(n))]


def _validate_program(program) -> None:
    if not program:
        raise ValueError("Birim programi bos: etut icin birim sayisi ve tipleri kullanici tarafindan verilmeli.")
    for unit_id, unit_type in program:
        if unit_type not in UNIT_TYPES:
            raise ValueError(f"Birim '{unit_id}': bilinmeyen tip '{unit_type}'. Tanimli: {', '.join(sorted(UNIT_TYPES))}.")
    if len({u for u, _ in program}) != len(program):
        raise ValueError("Birim kimlikleri benzersiz olmali.")


def _rebuild(structure: tuple, offset: tuple, program, w, d, weights, max_share, min_short_edge,
             opt_id: str) -> "StudyOption | None":
    """Bir etut YAPISINI (hol, desen, gruplama, atama) baska bir blok kaymasinda
    yeniden kurar; yapi o kaymada gecersizse (bolum sayisi degisti, blok sigmadi) None."""
    hall_id, pname, gidx, perm = structure
    n = len(program)
    hall_opt = next((o for o in options_for_central_hall(w, d, n_units=n, offset=offset)
                     if o.id == hall_id and o.feasible), None)
    if hall_opt is None:
        return None
    ordered = [r for r in _patterns(w, d, hall_opt.block)[pname] if _area(r) > 1e-6]
    groupings = _groupings(ordered, n) if ordered else []
    if gidx >= len(groupings):
        return None
    _hall_rect, frontage = _hall_frontage(hall_opt)
    option = _evaluate(opt_id, pname, hall_opt, _hall_rect, frontage, groupings[gidx], perm,
                       program, w, d, weights, max_share, min_short_edge)
    from dataclasses import replace
    return replace(option, offset=(float(offset[0]), float(offset[1])), structure=structure)


def study_floor(
    floor_width: float, floor_depth: float, program: tuple[tuple[str, str], ...], *,
    weights: StudyWeights = StudyWeights(), n_hall_candidates: int | None = None,
    top: int = 5, offsets: tuple[tuple[float, float], ...] = ((0.0, 0.0),),
    min_short_edge: float | None = None, max_share: float = DEFAULT_CIRCULATION_SHARE_MAX,
    refine: bool = True,
) -> list[StudyOption]:
    """Birim programina gore kat zonlama etudu - PUANA gore azalan `top` aday
    (once uygulanabilirler). `program`: ((unit_id, tip), ...) - KULLANICININ
    saglamasi gereken veri; bos/bilinmeyen tip `ValueError`.

    `refine=True` (DEV-057 Grup B): en iyi yapilarin blogunu kat merkezinden
    1000 sonra 250 mm adimlarla (|kayma| <= 4000mm) kaydirip puani yukselten
    kaymalari bulur - bolme cizgilerinin SUREKLI kaydirilmasi (bolme cizgileri
    blok kenarlarindan gelir). Merkezi (kaymasiz) en iyi aday, tercih hicbir
    adaya uymazsa secilecek GERI DONUS surumu olarak HER ZAMAN listede kalir."""
    _validate_program(program)
    if min_short_edge is None:
        min_short_edge = STANDARDS["salon"].min_short_edge_mm or 3000.0
    n = len(program)
    results: list[StudyOption] = []
    counter = 0
    from dataclasses import replace
    for offset in offsets:
        hall_options = [o for o in options_for_central_hall(
            floor_width, floor_depth, n_units=n, offset=offset) if o.feasible]
        if n_hall_candidates:
            hall_options = hall_options[:n_hall_candidates]
        for hall_opt in hall_options:
            hall_rect, frontage = _hall_frontage(hall_opt)
            for pname, secs in _patterns(floor_width, floor_depth, hall_opt.block).items():
                ordered = [r for r in secs if _area(r) > 1e-6]
                if not ordered:
                    continue
                for gidx, groups in enumerate(_groupings(ordered, n)):
                    for perm in _perms(groups, program, n):  # perm[unit_index] = grup_index
                        counter += 1
                        option = _evaluate(
                            f"E{counter:04d}", pname, hall_opt, hall_rect, frontage, groups, perm,
                            program, floor_width, floor_depth, weights, max_share, min_short_edge)
                        results.append(replace(option, offset=(float(offset[0]), float(offset[1])),
                                               structure=(hall_opt.id, pname, gidx, perm)))
    results.sort(key=lambda o: (not o.feasible, -o.score, o.id))
    if refine:
        seeds, seen_struct = [], set()
        for o in results:
            if o.feasible and o.structure not in seen_struct:
                seen_struct.add(o.structure)
                seeds.append(o)
            if len(seeds) >= REFINE_TOP:
                break
        for seed in seeds:
            current, cur_off = seed, seed.offset
            for step in REFINE_STEPS_MM:
                for _ in range(16):  # sonlu: her tur en iyi komsuya yurur
                    best = current
                    for ddx, ddy in ((step, 0), (-step, 0), (0, step), (0, -step),
                                     (step, step), (step, -step), (-step, step), (-step, -step)):
                        off = (cur_off[0] + ddx, cur_off[1] + ddy)
                        if abs(off[0]) > MAX_REFINE_OFFSET_MM or abs(off[1]) > MAX_REFINE_OFFSET_MM:
                            continue
                        cand = _rebuild(seed.structure, off, program, floor_width, floor_depth, weights,
                                        max_share, min_short_edge, f"{seed.id}r")
                        if cand is not None and cand.feasible and cand.score > best.score + 1e-9:
                            best, best_off = cand, off
                    if best is current:
                        break
                    current, cur_off = best, best_off
            if current is not seed:
                results.append(current)
        results.sort(key=lambda o: (not o.feasible, -o.score, o.id))
    # simetrik/yer degistirmis esdegerleri ele: ayni hol secenegi + ayni (tip, alan)
    # kumesi + ayni puan (ayni tipli iki birimin yer degistirmesi yeni aday degildir)
    unique, seen = [], set()
    for o in results:
        key = (o.hall_option, o.offset, round(o.score, 6), tuple(sorted((z.unit_type, z.area_m2) for z in o.zones)))
        if key in seen:
            continue
        seen.add(key)
        unique.append(o)
    chosen = unique[:top]
    if not any(_is_centered(o) for o in chosen):  # geri donus surumu her zaman listede
        centered = next((o for o in unique if o.feasible and _is_centered(o)), None)
        if centered is not None:
            chosen.append(centered)
    return chosen


def _is_centered(option: "StudyOption") -> bool:
    return abs(option.offset[0]) < 1.0 and abs(option.offset[1]) < 1.0


def _evaluate(opt_id, pname, hall_opt, hall_rect, frontage, groups, perm, program, w, d,
              weights, max_share, min_short_edge) -> StudyOption:
    zones, problems = [], []
    s_area = s_facade = s_prop = 0.0
    for ui, (unit_id, unit_type) in enumerate(program):
        ut = UNIT_TYPES[unit_type]
        rects = groups[perm[ui]]
        area = sum(_area(r) for r in rects) / 1e6
        access = sum(_edge_overlap(r, seg) for r in rects for seg in frontage)
        facade = sum(_facade_length(r, w, d) for r in rects)
        short = min(min(r[2] - r[0], r[3] - r[1]) for r in rects)
        if access < DOOR_SLOT_MM - 1e-6:
            problems.append(f"{unit_id}: hol cephesine temas {access:.0f}mm < {DOOR_SLOT_MM:.0f}mm (giris kapisi sigmaz)")
        if area < ut.min_area_m2 - 1e-6:
            problems.append(f"{unit_id}: alan {area:.1f} m2 < {ut.min_area_m2:.0f} m2 ({unit_type} asgarisi)")
        s_area += max(0.0, 1.0 - abs(area - ut.ideal_area_m2) / ut.ideal_area_m2)
        s_facade += min(1.0, facade / (ut.habitable_rooms * FACADE_PER_ROOM_MM))
        aspect_ok = all(max(r[2] - r[0], r[3] - r[1]) / max(1.0, min(r[2] - r[0], r[3] - r[1])) <= 3.0 for r in rects)
        s_prop += (0.5 if short >= min_short_edge - 1e-6 else 0.0) + (0.5 if aspect_ok else 0.0)
        topo = None
        if len(rects) == 1:
            r = rects[0]
            side = None
            # giris yonu: hol cephesine temas eden kenar
            for name, seg in (("alt", (r[0], r[1], r[2], r[1])), ("ust", (r[0], r[3], r[2], r[3])),
                              ("sol", (r[0], r[1], r[0], r[3])), ("sag", (r[2], r[1], r[2], r[3]))):
                if any(_collinear_overlap(seg, f) for f in frontage):
                    side = name
                    break
            if side:
                try:
                    cand = options_for_hall_topology(r[2] - r[0], r[3] - r[1], entry_side=side,
                                                     n_rooms=ut.habitable_rooms + 2)
                    topo = next((c.id for c in cand if c.feasible), None)
                except ValueError:
                    topo = None
        zones.append(ZonePlan(unit_id, unit_type, [tuple(r) for r in rects],
                              _union_polygon(rects), round(area, 2), access, facade, short, topo))
    n = len(program)
    s_area /= n; s_facade /= n; s_prop /= n
    share = hall_opt.share
    s_share = max(0.0, 1.0 - max(0.0, share - max_share) / max_share)
    breakdown = {"area_fit": s_area, "facade": s_facade, "proportion": s_prop,
                 "hall_share": s_share, "hall_option": hall_opt.score}
    score = (weights.area_fit * s_area + weights.facade * s_facade + weights.proportion * s_prop
             + weights.hall_share * s_share + weights.hall_option * hall_opt.score)
    feasible = not problems
    return StudyOption(
        opt_id, hall_opt.id, pname, zones, feasible, round(score if feasible else 0.0, 4),
        {k: round(v, 4) for k, v in breakdown.items()},
        (f"hol '{hall_opt.id}', desen '{pname}': " + ", ".join(
            f"{z.unit_id}({z.unit_type}) {z.area_m2:.1f} m2" for z in zones)
         + (" | SORUN: " + "; ".join(problems) if problems else "")),
        hall_opt.block, problems)


def _collinear_overlap(a, b) -> bool:
    if abs(a[1] - a[3]) < 1e-6 and abs(b[1] - b[3]) < 1e-6:
        return abs(a[1] - b[1]) < 1e-6 and _overlap_1d(min(a[0], a[2]), max(a[0], a[2]), min(b[0], b[2]), max(b[0], b[2])) > 0
    if abs(a[0] - a[2]) < 1e-6 and abs(b[0] - b[2]) < 1e-6:
        return abs(a[0] - b[0]) < 1e-6 and _overlap_1d(min(a[1], a[3]), max(a[1], a[3]), min(b[1], b[3]), max(b[1], b[3])) > 0
    return False



# --- Tercih ve secim (DEV-057 Grup B) -----------------------------------------
MIN_CLOSENESS = 0.5
SIDES = ("south", "north", "east", "west")
HALL_FAMILIES = {"kare": ("kare",), "dikdortgen": ("dikdortgen_3_2", "dikdortgen_2_1"),
                 "koridor": ("koridor_3_1", "koridor_min")}


@dataclass(frozen=True)
class StudyPreference:
    """Kullanicinin dogal dil talebinin YAPILANDIRILMIS hali - dil modeli talebi bu
    alanlara cevirir, sistem aday yakinligini DETERMINISTIK hesaplar (olcu/
    koordinat dil modelinden gelmez). Tum alanlar opsiyoneldir.
      unit_area_m2: {birim: hedef alan}            ("A dairesi buyuk olsun")
      unit_side:    {birim: south|north|east|west} (bolgenin kat merkezine gore yonu)
      hall:         hol alternatifi kimligi ya da ailesi (kare|dikdortgen|koridor)
      centered_hall: True -> blok kat merkezinde (kaymasiz)"""
    unit_area_m2: dict = field(default_factory=dict)
    unit_side: dict = field(default_factory=dict)
    hall: str | None = None
    centered_hall: bool | None = None


@dataclass(frozen=True)
class StudySelection:
    option: StudyOption
    closeness: float | None   # tercih yoksa None
    fallback: bool            # True: tercih hicbir adaya uymadi -> merkezi hol surumu
    reason: str


def _zone_side(zone: ZonePlan, w: float, d: float) -> str:
    xs = [p[0] for p in zone.polygon]
    ys = [p[1] for p in zone.polygon]
    dx, dy = (min(xs) + max(xs)) / 2.0 - w / 2.0, (min(ys) + max(ys)) / 2.0 - d / 2.0
    if abs(dy) >= abs(dx):
        return "north" if dy > 0 else "south"
    return "east" if dx > 0 else "west"


def preference_closeness(option: StudyOption, preference: StudyPreference, w: float, d: float) -> tuple[float, list]:
    """Tercihe yakinlik 0..1 (mevcut tercih bilesenlerinin ortalamasi) + ayrintilar."""
    parts: list[tuple[str, float]] = []
    zones = {z.unit_id: z for z in option.zones}
    if preference.unit_area_m2:
        vals = [max(0.0, 1.0 - abs(zones[u].area_m2 - t) / t) for u, t in preference.unit_area_m2.items()]
        parts.append(("alan", sum(vals) / len(vals)))
    if preference.unit_side:
        vals = [1.0 if _zone_side(zones[u], w, d) == side else 0.0 for u, side in preference.unit_side.items()]
        parts.append(("yon", sum(vals) / len(vals)))
    if preference.hall is not None:
        family = HALL_FAMILIES.get(preference.hall, (preference.hall,))
        parts.append(("hol", 1.0 if option.hall_option in family else 0.0))
    if preference.centered_hall is not None:
        parts.append(("merkez", 1.0 if _is_centered(option) == preference.centered_hall else 0.0))
    if not parts:
        return 0.0, []
    return sum(v for _, v in parts) / len(parts), parts


def select_study_option(options: list, preference: StudyPreference | None, floor_width: float,
                        floor_depth: float) -> StudySelection:
    """Etut adaylari arasindan KULLANICI TALEBINE EN YAKIN olani secer
    (kullanici karari 2026-10-05). Hicbiri `MIN_CLOSENESS`in uzerinde degilse
    (veya tercih bos/belirsizse) hol binanin MERKEZINDE olan (kaymasiz blok)
    en yuksek puanli uygulanabilir surum secilir. Esitlikte etut puani, sonra id."""
    feasible = [o for o in options if o.feasible]
    if not feasible:
        raise ValueError("Secilebilecek uygulanabilir etut adayi yok.")
    if preference is not None:
        ids = {z.unit_id for z in feasible[0].zones}
        for unit in set(preference.unit_area_m2) | set(preference.unit_side):
            if unit not in ids:
                raise ValueError(f"Tercihteki birim '{unit}' programda yok: {sorted(ids)}.")
        for side in preference.unit_side.values():
            if side not in SIDES:
                raise ValueError(f"Yon {SIDES} olmali, '{side}' verildi.")
        if preference.hall is not None and preference.hall not in HALL_FAMILIES and \
                preference.hall not in {o.hall_option for o in feasible}:
            raise ValueError(f"Bilinmeyen hol tercihi: '{preference.hall}'.")
    scored = []
    if preference is not None:
        for o in feasible:
            c, parts = preference_closeness(o, preference, floor_width, floor_depth)
            if parts:
                scored.append((c, o, parts))
    best = max(scored, key=lambda t: (round(t[0], 9), t[1].score, t[1].id), default=None)
    if best is not None and best[0] >= MIN_CLOSENESS:
        c, o, parts = best
        return StudySelection(o, round(c, 4), False,
                              "tercihe en yakin aday: " + ", ".join(f"{k}={v:.2f}" for k, v in parts))
    centered = [o for o in feasible if _is_centered(o)] or feasible
    pick = max(centered, key=lambda o: (o.score, o.id))
    why = "tercih belirtilmedi" if (preference is None or not scored) else \
        f"hicbir aday tercihe yeterince yakin degil (en iyi {best[0]:.2f} < {MIN_CLOSENESS:.2f})"
    return StudySelection(pick, None if not scored else round(best[0], 4), True,
                          f"{why} -> hol merkezde olan en yuksek puanli surum secildi")


def study_and_select(floor_width: float, floor_depth: float, program, preference: StudyPreference | None = None,
                     *, pool: int = 60, **study_kwargs) -> StudySelection:
    """Etudu calistirir (secim icin genis bir aday havuzu: `pool`) ve tercihe en
    yakin adayi - yoksa merkezi hol surumunu - dondurur."""
    options = study_floor(floor_width, floor_depth, program, top=pool, **study_kwargs)
    return select_study_option(options, preference, floor_width, floor_depth)


__all__ = [
    "UnitType", "UNIT_TYPES", "StudyWeights", "ZonePlan", "StudyOption",
    "CURRENT_PROJECT_PROGRAM", "study_floor", "suggest_unit_mixes",
    "StudyPreference", "StudySelection", "select_study_option", "preference_closeness",
    "study_and_select",
]
