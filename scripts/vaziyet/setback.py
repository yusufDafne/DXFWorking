"""Cekme (yapi yaklasma) mesafeleri ve yapilasma alani (DEV-082). Mesafeler GIRDIDIR: verilmediyse uretilmez (varsayilan katalog DEV-086)."""
from __future__ import annotations

import math

try:
    from .parcel import Parcel, Point, VaziyetError, inward_offset
except ImportError:
    from parcel import Parcel, Point, VaziyetError, inward_offset  # type: ignore


def resolve_setbacks(setbacks: dict | None, edge_count: int, defaults: dict | None = None) -> list[float]:
    """`{"uniform_mm": x}` ya da `{"edges_mm": [..]}` -> kenar basina liste. Hicbiri yoksa `defaults` (DEV-086 katalog cikisi, ayni bicim);
    o da yoksa `VaziyetError` (mesafe UYDURULMAZ)."""
    src = setbacks or defaults
    if not src:
        raise VaziyetError("cekme mesafesi verilmedi (site.setbacks) ve varsayilan katalog verilmedi - mesafe uydurulmaz")
    if "edges_mm" in src:
        vals = src["edges_mm"]
        if not isinstance(vals, list) or len(vals) != edge_count:
            raise VaziyetError(f"setbacks.edges_mm {edge_count} sayi icermeli")
        return [float(v) for v in vals]
    if "uniform_mm" in src:
        return [float(src["uniform_mm"])] * edge_count
    raise VaziyetError("setbacks 'uniform_mm' ya da 'edges_mm' icermeli")


def buildable_area(parcel: Parcel, setbacks: dict | None, defaults: dict | None = None) -> list[Point]:
    """Yapilasma alani (parselin cekmeler kadar iceri offsetlenmis hali). Bos/gecersiz sonuc `VaziyetError`."""
    return inward_offset(list(parcel.polygon), resolve_setbacks(setbacks, len(parcel.polygon), defaults))


def building_footprint(width: float, depth: float, position, rotation_deg: float = 0.0) -> list[Point]:
    """Bina plan dikdortgeni: `position` MERKEZDIR; yerel +X = plan X (genislik), yerel +Y = plan 'yukari' (derinlik); `rotation_deg` SAAT YONUNDE
    (kuzey yukari olan vaziyette binanin ust yuzunun dis normalinin kuzeyden acisi, `northarrow.rotate_point` konvansiyonu). Kose sirasi CCW."""
    th = math.radians(rotation_deg)
    s, c = math.sin(th), math.cos(th)
    cx, cy = float(position[0]), float(position[1])
    out: list[Point] = []
    for lx, ly in ((-width / 2, -depth / 2), (width / 2, -depth / 2), (width / 2, depth / 2), (-width / 2, depth / 2)):
        out.append((cx + lx * c + ly * s, cy - lx * s + ly * c))     # saat yonunde donme
    return out


def plan_north_angle(rotation_deg: float) -> float:
    """DEV-081 sozlesmesi: vaziyette bina kuzeyden B derece (saat yonu) donukse kat plani `meta.north_angle = -B` (30 -> -30)."""
    a = -float(rotation_deg)
    a = (a + 180.0) % 360.0 - 180.0
    return 180.0 if a == -180.0 else a
