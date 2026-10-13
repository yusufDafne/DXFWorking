"""validate.py kancasi (DEV-082): `context.json::site` denetimi. Opt-in: `site` yoksa bos doner (mevcut projeler DEGISMEZ)."""
from __future__ import annotations

try:
    from .parcel import Parcel, VaziyetError, validate_polygon
    from .setback import buildable_area, building_footprint
except ImportError:
    from parcel import Parcel, VaziyetError, validate_polygon  # type: ignore
    from setback import buildable_area, building_footprint  # type: ignore

try:
    from ..collision.geometry import point_in_polygon, point_inside_or_on
except ImportError:
    from collision.geometry import point_in_polygon, point_inside_or_on


def check_site(context: dict) -> tuple[list[str], list[str]]:
    """(hatalar, uyarilar). HATA: gecersiz parsel/yerlesim alani cokgeni, gecersiz road_edges/setbacks, cekmelerin yapilasma alanini yok etmesi,
    bina parsel DISINDA. UYARI: kuzey yukari onaylanmamis, yerlesim alani parsel disina tasiyor, cekme verilmemis, bina yapilasma alani DISINDA."""
    site = context.get("site")
    if not site:
        return [], []
    errors: list[str] = []
    warnings: list[str] = []
    parcel = None
    poly = site.get("parcel", {}).get("polygon")
    if poly is None:
        errors.append("site.parcel.polygon yok")
    else:
        bad = validate_polygon(poly)
        if bad:
            errors += [f"site.parcel.polygon: {b}" for b in bad]
        else:
            parcel = Parcel.from_polygon(poly)
    zone = site.get("placement_zone", {}).get("polygon")
    if zone is not None:
        bad = validate_polygon(zone)
        if bad:
            errors += [f"site.placement_zone.polygon: {b}" for b in bad]
        elif parcel is not None and not all(point_inside_or_on(tuple(v), list(parcel.polygon), 1e-6) for v in zone):
            warnings.append("site.placement_zone parsel disina tasiyor (yaklasik yerlesim alani parsel icinde olmali)")
    if parcel is not None:
        n = len(parcel.polygon)
        for idx in site.get("road_edges", []):
            if not isinstance(idx, int) or isinstance(idx, bool) or not 0 <= idx < n:
                errors.append(f"site.road_edges: {idx!r} gecersiz kenar indeksi (parselde {n} kenar var)")
    if not site.get("north_confirmed"):
        warnings.append("site.north_confirmed yok/false: vaziyet planinin KUZEY YUKARI oldugu kullanicidan onaylanmadi (DEV-081 sozlesmesi)")
    buildable = None
    if parcel is not None:
        if site.get("setbacks") is None:
            warnings.append("site.setbacks verilmemis: yapilasma alani hesaplanamadi (cekme mesafesi uydurulmaz; kullanici degeri ya da varsayilan katalog gerekir)")
        else:
            try:
                buildable = buildable_area(parcel, site["setbacks"])
            except VaziyetError as exc:
                errors.append(f"site.setbacks: {exc}")
    building = site.get("building")
    if building and parcel is not None:
        meta = context.get("meta", {})
        w, d = meta.get("floor_width"), meta.get("floor_depth")
        if not (w and d):
            errors.append("site.building icin meta.floor_width/floor_depth gerekir")
        else:
            foot = building_footprint(float(w), float(d), building["position"], float(building.get("rotation_deg", 0.0)))
            if not all(point_inside_or_on(v, list(parcel.polygon), 1e-6) for v in foot):
                errors.append("site.building ayak izi PARSEL disina tasiyor")
            elif buildable is not None and not all(point_inside_or_on(v, buildable, 1e-6) for v in foot):
                warnings.append("site.building ayak izi yapilasma alani (cekmeler) disina giriyor")
    return errors, warnings
