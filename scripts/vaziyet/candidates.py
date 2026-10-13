"""Aday uretimi ve eleme (DEV-083). Aday kumesi SIRALI bir izgaradir: adim ve donus kumesi KULLANICI parametresidir (varsayilan UYDURULMAZ)."""
from __future__ import annotations

import math
from dataclasses import dataclass

try:
    from .parcel import VaziyetError
    from .setback import building_footprint
except ImportError:
    from parcel import VaziyetError  # type: ignore
    from setback import building_footprint  # type: ignore

try:
    from ..collision.geometry import aabb, point_inside_or_on
except ImportError:
    from collision.geometry import aabb, point_inside_or_on

Point = tuple[float, float]
CONTAINMENT_TOLERANCE_MM = 1e-6     # sayisal (kayan nokta) payi; tasarim esigi DEGIL: sinirdaki aday elenmez, 1 mm iceri giren elenir
MAX_CANDIDATES = 200_000            # kaba korkuluk (bellek/sure); asilirsa adim buyutulmeli. Olcum esigi degil.
REASON_OUTSIDE_PARCEL = "parsel_disi"
REASON_OUTSIDE_BUILDABLE = "yapilasma_alani_disi"


@dataclass(frozen=True)
class Candidate:
    index: int
    position: Point              # bina MERKEZI
    rotation_deg: float          # saat yonunde (kuzey yukari vaziyette ust yuzun dis normalinin kuzeyden acisi)


def _signed_distance(a: Point, b: Point, p: Point) -> float:
    length = math.dist(a, b)
    return ((b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])) / length


def _properly_cross(a: Point, b: Point, c: Point, d: Point, tol: float) -> bool:
    """AB ve CD birbirini TAM KESIYOR mu (uclarda/ustte degmek kesisim sayilmaz; `tol` mesafe payi)."""
    s1, s2 = _signed_distance(a, b, c), _signed_distance(a, b, d)
    s3, s4 = _signed_distance(c, d, a), _signed_distance(c, d, b)
    return ((s1 > tol and s2 < -tol) or (s1 < -tol and s2 > tol)) and ((s3 > tol and s4 < -tol) or (s3 < -tol and s4 > tol))


def footprint_within(footprint, outer, tol: float = CONTAINMENT_TOLERANCE_MM) -> bool:
    """`footprint` (disbukey dikdortgen), `outer` (icbukey olabilir) cokgenin ICINDE mi (sinirda durmak iceridir)?
    (1) her kose icinde/uzerinde; (2) kenarlar birbirini kesmez (icbukey girintiyi kesen dis cizgi yakalanir; girintinin kosesi disbukey ayak izinin icinde kalamaz [kose iceride + girinti disarida zaten bir kenari keser])"""
    fp = [(float(x), float(y)) for x, y in footprint]
    out = [(float(x), float(y)) for x, y in outer]
    if not all(point_inside_or_on(v, out, tol) for v in fp):
        return False
    n, m = len(fp), len(out)
    for i in range(n):
        for j in range(m):
            if _properly_cross(fp[i], fp[(i + 1) % n], out[j], out[(j + 1) % m], tol):
                return False
    return True


def build_candidates(buildable, step_mm, rotations_deg) -> list[Candidate]:
    """Yapilasma alani sinir kutusu uzerinde `step_mm` adimli merkez izgarasi x `rotations_deg`. Sira: (donus, x, y) - determinist.
    Adim ve donus kumesi VERILMEK ZORUNDADIR (varsayilan yok)."""
    if isinstance(step_mm, bool) or not isinstance(step_mm, (int, float)) or step_mm <= 0:
        raise VaziyetError("step_mm pozitif sayi olmali (varsayilan yok; kullanici verir)")
    if not isinstance(rotations_deg, (list, tuple)) or not rotations_deg or any(isinstance(r, bool) or not isinstance(r, (int, float)) for r in rotations_deg):
        raise VaziyetError("rotations_deg bos olmayan sayi listesi olmali (varsayilan yok; kullanici verir)")
    rots = sorted({float(r) % 360.0 for r in rotations_deg})
    xmin, ymin, xmax, ymax = aabb([(float(x), float(y)) for x, y in buildable])
    nx = int(math.floor((xmax - xmin) / step_mm + 1e-9)) + 1
    ny = int(math.floor((ymax - ymin) / step_mm + 1e-9)) + 1
    if nx * ny * len(rots) > MAX_CANDIDATES:
        raise VaziyetError(f"aday sayisi {nx * ny * len(rots)} > {MAX_CANDIDATES}: adimi buyutun ya da donus sayisini azaltin")
    out: list[Candidate] = []
    for r in rots:
        for ix in range(nx):
            for iy in range(ny):
                out.append(Candidate(len(out), (xmin + ix * step_mm, ymin + iy * step_mm), r))
    return out


def classify(candidate: Candidate, width: float, depth: float, parcel_polygon, buildable_polygon) -> tuple[list[Point], str | None]:
    """(ayak izi, eleme nedeni | None). Once parsel disi, sonra yapilasma alani disi."""
    fp = building_footprint(width, depth, candidate.position, candidate.rotation_deg)
    if not footprint_within(fp, parcel_polygon):
        return fp, REASON_OUTSIDE_PARCEL
    if not footprint_within(fp, buildable_polygon):
        return fp, REASON_OUTSIDE_BUILDABLE
    return fp, None
