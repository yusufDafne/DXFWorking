"""Deterministik yerlesim etudu (DEV-083): aday uret -> ele (FORBID benzeri) -> olc -> alternatif sec. Rastgelelik YOK; ayni girdi -> ayni liste.

Dil modeli bu modulu cagirmaz; yalniz parametreleri ONERIR (adim, donusler, N, agirlik) ve kullanici onaylar. Motor sayi/koordinat UYDURMAZ."""
from __future__ import annotations

import math
from dataclasses import dataclass, field

try:
    from .candidates import REASON_OUTSIDE_BUILDABLE, REASON_OUTSIDE_PARCEL, build_candidates, classify
    from .metrics import Measurement, measure_candidate
    from .parcel import Parcel, VaziyetError
    from .setback import plan_north_angle
except ImportError:
    from candidates import REASON_OUTSIDE_BUILDABLE, REASON_OUTSIDE_PARCEL, build_candidates, classify  # type: ignore
    from metrics import Measurement, measure_candidate  # type: ignore
    from parcel import Parcel, VaziyetError  # type: ignore
    from setback import plan_north_angle  # type: ignore

try:
    from ..collision.geometry import polygon_area
except ImportError:
    from collision.geometry import polygon_area

DEFAULT_ALTERNATIVES = 3      # kullanici karari (Q6)
MAX_ALTERNATIVES = 10         # SUNUM siniri (okunabilirlik); olcum esigi degil
# Takas EKSENLERI: hepsi "buyuk = o eksende one cikar" yonunde. Kalite iddiasi DEGIL; farkli odunlesimleri temsil eder.
OBJECTIVES = ("road_proximity", "neighbor_clearance", "light_south", "zone_fit")
OBJECTIVE_LABEL = {
    "road_proximity": "yola yakinlik",
    "neighbor_clearance": "yol disindaki parsel sinirlarindan uzaklik",
    "light_south": "uzun cephelerin guneye yonelimi",
    "zone_fit": "istenen yerlesim bolgesine uyum",
}


@dataclass(frozen=True)
class Alternative:
    id: str
    position: tuple
    rotation_deg: float
    plan_north_angle: float
    footprint: tuple
    measurements: tuple            # Measurement'lar (kaynak fonksiyon adi + deger)
    objectives: dict               # eksen -> deger (buyuk = iyi)
    reason: str                    # 'best:<eksen>' | 'diversity' | 'weighted'
    score: float | None = None
    outside_zone: bool = False

    def m(self, name):
        for x in self.measurements:
            if x.name == name:
                return x.value
        return None


@dataclass
class StudyResult:
    parameters: dict
    generated: int
    eliminated: dict
    survivors: int
    alternatives: list
    ceilings: list
    notes: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "parameters": self.parameters, "generated": self.generated, "eliminated": dict(sorted(self.eliminated.items())), "survivors": self.survivors,
            "alternatives": [{
                "id": a.id, "position": list(a.position), "rotation_deg": a.rotation_deg, "plan_north_angle": a.plan_north_angle, "reason": a.reason,
                "score": a.score, "outside_zone": a.outside_zone, "objectives": a.objectives,
                "measurements": [{"name": x.name, "value": x.value, "unit": x.unit, "source": x.source} for x in a.measurements],
            } for a in self.alternatives],
            "ceilings": self.ceilings, "notes": list(self.notes),
        }


# ------------------------------------------------------------------ secim (saf fonksiyonlar, elle sinanabilir)
def pareto_front(vectors: list[tuple]) -> list[int]:
    """Hicbir baska vektorun BASKIN cikmadigi indeksler (buyuk = iyi; baskin: hepsinde >= ve en az birinde >)."""
    front = []
    for i, v in enumerate(vectors):
        dominated = any(all(w[k] >= v[k] for k in range(len(v))) and any(w[k] > v[k] for k in range(len(v))) for j, w in enumerate(vectors) if j != i)
        if not dominated:
            front.append(i)
    return front


def _normalize(vectors: list[tuple]) -> list[tuple]:
    dims = len(vectors[0])
    lo = [min(v[k] for v in vectors) for k in range(dims)]
    hi = [max(v[k] for v in vectors) for k in range(dims)]
    return [tuple(0.0 if hi[k] == lo[k] else (v[k] - lo[k]) / (hi[k] - lo[k]) for k in range(dims)) for v in vectors]


def select_unweighted(vectors: list[tuple], names: tuple, n: int) -> list[tuple[int, str]]:
    """Agirliksiz secim: Pareto cephesinden her ekseni en iyi yapan aday (eksen sirasiyla), sonra normalize uzayda en uzak aday (min-max, esitlikte kucuk indeks).
    Ayni vektorlu (esdeger) adaylar tekrar SECILMEZ -> `n`den az donebilir. Donus: [(indeks, neden)]."""
    if not vectors:
        return []
    front = pareto_front(vectors)
    norm = _normalize(vectors)
    chosen: list[tuple[int, str]] = []

    def distinct(i):
        return all(norm[i] != norm[j] for j, _ in chosen)

    for k, name in enumerate(names):
        if len(chosen) >= n:
            break
        best = max(front, key=lambda i: (vectors[i][k], -i))
        if all(best != j for j, _ in chosen) and distinct(best):
            chosen.append((best, f"best:{name}"))
    pools = (front, [i for i in range(len(vectors)) if i not in set(front)])
    for pool in pools:
        while len(chosen) < n:
            cands = [i for i in pool if all(i != j for j, _ in chosen) and distinct(i)]
            if not cands:
                break
            far = max(cands, key=lambda i: (min(math.dist(norm[i], norm[j]) for j, _ in chosen) if chosen else 0.0, -i))
            chosen.append((far, "diversity"))
    return chosen


def select_weighted(vectors: list[tuple], names: tuple, weights: dict, n: int, min_separation_mm: float | None = None, positions=None) -> list[tuple[int, float]]:
    """Agirlikli secim: min-max normalize eksenlerin agirlikli toplami; esitlikte kucuk indeks. `min_separation_mm` (KULLANICI parametresi, varsayilan yok)
    verilirse secilenler arasi merkez uzakligi en az o kadar olur. Donus: [(indeks, skor)]."""
    unknown = sorted(set(weights) - set(names))
    if unknown:
        raise VaziyetError(f"bilinmeyen agirlik anahtari: {unknown} (gecerli: {list(names)})")
    if any(isinstance(w, bool) or not isinstance(w, (int, float)) or w < 0 for w in weights.values()):
        raise VaziyetError("agirliklar negatif olmayan sayi olmali")
    if not any(w > 0 for w in weights.values()):
        raise VaziyetError("en az bir agirlik pozitif olmali")
    if not vectors:
        return []
    norm = _normalize(vectors)
    w = [float(weights.get(nm, 0.0)) for nm in names]
    scored = sorted(((sum(w[k] * norm[i][k] for k in range(len(names))), i) for i in range(len(vectors))), key=lambda t: (-t[0], t[1]))
    out: list[tuple[int, float]] = []
    for s, i in scored:
        if len(out) >= n:
            break
        if min_separation_mm is not None and positions is not None and any(math.dist(positions[i], positions[j]) < min_separation_mm for j, _ in out):
            continue
        out.append((i, s))
    return out


# ------------------------------------------------------------------ tavan (TAKS/KAKS) - konumdan bagimsiz
def ceiling_checks(parcel_area: float, footprint_area: float, taks: dict | None, kaks: dict | None, floor_count: int | None) -> list[dict]:
    """TAKS = ayak izi/parsel; KAKS = ayak izi x kat adedi / parsel (kat adedi VERILMEDIYSE olculemez - uydurulmaz). Limit `{value, source}`; kaynak ADIYLA bildirilir."""
    out = []
    if taks is not None:
        ratio = footprint_area / parcel_area
        out.append({"name": "TAKS", "value": ratio, "limit": taks["value"], "limit_source": taks["source"], "ok": ratio <= taks["value"] + 1e-12})
    if kaks is not None:
        if floor_count is None:
            out.append({"name": "KAKS", "value": None, "limit": kaks["value"], "limit_source": kaks["source"], "ok": None,
                        "reason": "kat adedi verilmedi: emsal olculemedi (uydurulmaz)"})
        else:
            ratio = footprint_area * floor_count / parcel_area
            out.append({"name": "KAKS", "value": ratio, "limit": kaks["value"], "limit_source": kaks["source"], "ok": ratio <= kaks["value"] + 1e-12})
    return out


# ------------------------------------------------------------------ etut
def run_study(parcel_polygon, buildable_polygon, width: float, depth: float, *, step_mm, rotations_deg, n: int = DEFAULT_ALTERNATIVES,
              weights: dict | None = None, road_edges=(), zone=None, north_confirmed: bool = True, min_separation_mm: float | None = None,
              taks: dict | None = None, kaks: dict | None = None, floor_count: int | None = None) -> StudyResult:
    if isinstance(n, bool) or not isinstance(n, int) or not 1 <= n <= MAX_ALTERNATIVES:
        raise VaziyetError(f"alternatif sayisi 1..{MAX_ALTERNATIVES} arasi tam sayi olmali (varsayilan {DEFAULT_ALTERNATIVES})")
    if not (isinstance(width, (int, float)) and isinstance(depth, (int, float)) and width > 0 and depth > 0):
        raise VaziyetError("bina genisligi/derinligi pozitif olmali")
    parcel = Parcel.from_polygon(parcel_polygon)
    ppoly = list(parcel.polygon)
    road_edges = tuple(sorted(set(road_edges)))
    cands = build_candidates(buildable_polygon, step_mm, rotations_deg)
    eliminated = {REASON_OUTSIDE_PARCEL: 0, REASON_OUTSIDE_BUILDABLE: 0}
    survivors = []
    for c in cands:
        fp, reason = classify(c, width, depth, ppoly, buildable_polygon)
        if reason is not None:
            eliminated[reason] += 1
            continue
        survivors.append((c, fp))
    notes: list[str] = []
    names = tuple(k for k in OBJECTIVES
                  if (k != "road_proximity" or road_edges) and (k != "neighbor_clearance" or len(road_edges) < len(ppoly))
                  and (k != "light_south" or north_confirmed) and (k != "zone_fit" or zone is not None))
    if not north_confirmed:
        notes.append("Vaziyetin kuzey-yukari oldugu onaylanmadi: isik (guney yonelimi) ekseni DISARIDA birakildi, yon tahmin edilmedi.")
    if not road_edges:
        notes.append("Yola bakan kenar bildirilmedi: yola yakinlik ekseni ve yola bakan yuz olcumu DISARIDA.")
    rows = []
    for c, fp in survivors:
        ms = measure_candidate(parcel, buildable_polygon, fp, c.rotation_deg, width, depth, road_edges, zone, north_confirmed)
        mv = {m.name: m.value for m in ms}
        obj = {}
        if "road_proximity" in names:
            obj["road_proximity"] = -mv["road_distance_mm"]
        if "neighbor_clearance" in names:
            obj["neighbor_clearance"] = mv["min_other_edge_distance_mm"]
        if "light_south" in names:
            obj["light_south"] = -mv["long_face_south_deviation_deg"]
        if "zone_fit" in names:
            obj["zone_fit"] = mv["zone_overlap_ratio"]
        rows.append((c, fp, ms, obj))
    alternatives: list[Alternative] = []
    if rows:
        vectors = [tuple(r[3][k] for k in names) for r in rows]
        if weights:
            picked = [(i, f"weighted", s) for i, s in select_weighted(vectors, names, weights, n, min_separation_mm, [r[0].position for r in rows])]
        else:
            if min_separation_mm is not None:
                notes.append("min_separation_mm yalniz agirlikli secimde kullanilir; agirliksiz secim cesitliligi zaten eksen farkindan gelir.")
            picked = [(i, why, None) for i, why in select_unweighted(vectors, names, n)]
        for k, (i, why, score) in enumerate(picked, start=1):
            c, fp, ms, obj = rows[i]
            zov = next((m.value for m in ms if m.name == "zone_overlap_ratio"), None)
            alternatives.append(Alternative(
                id=f"A{k}", position=(round(c.position[0], 6), round(c.position[1], 6)), rotation_deg=c.rotation_deg, plan_north_angle=plan_north_angle(c.rotation_deg),
                footprint=tuple((round(x, 6), round(y, 6)) for x, y in fp), measurements=tuple(ms), objectives={kk: obj[kk] for kk in names}, reason=why,
                score=None if score is None else round(score, 9), outside_zone=bool(zone is not None and zov is not None and zov < 1.0 - 1e-9)))
        if len(alternatives) < n:
            notes.append(f"Istenen {n} alternatiften {len(alternatives)} tanesi FARKLI bir odunlesimi temsil ediyor; kalanlar esdeger (ayni olcumler) oldugu icin eklenmedi.")
        if any(a.outside_zone for a in alternatives):
            notes.append("Bazi alternatifler istenen yerlesim bolgesinin DISINA tasiyor (bolge yaklasik bir istektir, eleme degildir).")
    else:
        notes.append("Hicbir aday elemeyi gecemedi: adimi kucultun, donus kumesini degistirin ya da cekmeleri/bina boyutunu gozden gecirin.")
    ceilings = ceiling_checks(polygon_area(ppoly), width * depth, taks, kaks, floor_count)
    for c in ceilings:
        if c["ok"] is False:
            notes.append(f"{c['name']} tavani ASILIYOR (olculen {c['value']:.4f} > {c['limit']:g}; tavan kaynagi: {c['limit_source']}): bu bina boyutu konumdan bagimsiz tavani asar.")
    params = {"step_mm": step_mm, "rotations_deg": sorted({float(r) % 360.0 for r in rotations_deg}), "n": n, "weights": dict(sorted((weights or {}).items())) or None,
              "axes": list(names), "min_separation_mm": min_separation_mm, "width_mm": width, "depth_mm": depth, "road_edges": list(road_edges),
              "has_zone": zone is not None, "north_confirmed": north_confirmed}
    return StudyResult(params, len(cands), eliminated, len(rows), alternatives, ceilings, notes)
