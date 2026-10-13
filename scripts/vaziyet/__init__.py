"""vaziyet modulu (DEV-082): vaziyet/parsel girdisi - parsel geometrisi, cekmeler, yapilasma alani, vaziyet DXF'i ice aktarma.

ISIM NOTU: plan `site/` adini kullaniyordu; `site` bir Python STDLIB modulu (baslangicta otomatik yuklenir) oldugundan `import site` paketimizi
DEGIL stdlib'i verirdi - `import`/`fixture` ile ayni sinifta bir ad duzeltmesi: dizin `vaziyet/`. Veri anahtari `context.json::site` KALDI (JSON anahtari, import degil).

Salt kutuphane + kontrol: context.json'a YAZMAZ, DXF CIZMEZ (vaziyet paftasi DEV-084), cekme degeri UYDURMAZ (varsayilan katalog DEV-086).
"""
from __future__ import annotations

# Bu modulun CONTEXT SOZLESMESI surumu (DEV-020). Bkz. scripts/version.py
CONTRACT_VERSION = "1.0"   # DEV-082: context.json::site (parcel, placement_zone, road_edges, setbacks, building, source, north_confirmed)

from .checks import check_site  # noqa: E402
from .dxf_in import (Candidate, DxfInputError, SiteScan, build_site_patch, layer_hint, scan_site_dxf)  # noqa: E402
from .parcel import Parcel, VaziyetError, inward_offset, normalize_ccw, validate_polygon  # noqa: E402
from .sample import write_sample  # noqa: E402
from .setback import buildable_area, building_footprint, plan_north_angle, resolve_setbacks  # noqa: E402

__all__ = [
    "CONTRACT_VERSION", "Parcel", "VaziyetError", "DxfInputError", "Candidate", "SiteScan", "validate_polygon", "normalize_ccw", "inward_offset",
    "resolve_setbacks", "buildable_area", "building_footprint", "plan_north_angle", "scan_site_dxf", "build_site_patch", "layer_hint",
    "write_sample", "check_site",
]
