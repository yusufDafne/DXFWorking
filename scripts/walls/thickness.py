"""Dis / ic duvar kalinligi hiyerarsisi (DEV-050 madde 16).

**Kullanici karari (2026-10-05):** dis ve ic duvar kalinligi FARKLIDIR;
varsayilan dis duvar 200 mm, ic duvar HER ZAMAN dis - 50 mm (150 mm). Hangi
dis kalinlik secilirse secilsin fark 50 mm kalir. **Daire (birim) ile kat
holu / ortak alan arasindaki duvar ve daire ile daire arasindaki ortak duvar
DIS duvar sayilir.**

Sinif DUVARA ELLE YAZILMAZ, oda komsulugundan TURETILIR:
  - bina dis cephesi (butun duvarlarin sinirlayici kutusunun bir kenari
    uzerindeki duvar) -> `dis`
  - duvarin iki yaninda farkli `unit_id` (veya biri `unit_id`siz ortak alan)
    varsa -> `dis`
  - duvara dokunan tum odalar AYNI (bos olmayan) `unit_id` ise -> `ic`
  - diger her durum (ortak alan <-> ortak alan, oda komsulugu yok) -> `None`
    (belirsiz: kural UYDURULMAZ, kontrol edilmez)

Politika: UYARI (kok `CLAUDE.md`/`standards/` ile ayni), asla HATA. Kutuphane
varsayilanidir (proje verisi DEGIL); proje `walls[].thickness` ile acikca
ezer, kontrol da yalnizca sapmayi RAPORLAR. Oda poligonlari merkez
cizgisinde kaldigi icin net mahal alani `standards.measure.net_area`
(duvar IC YUZLERI arasi) ile hesaplanir.

Bu dosya `rooms`i import ETMEZ: odalar duck-typed dict'lerdir.
"""
from __future__ import annotations

DEFAULT_EXTERIOR_THICKNESS_MM = 200.0
INTERIOR_THICKNESS_DELTA_MM = 50.0

CLASS_EXTERIOR = "dis"
CLASS_INTERIOR = "ic"

_TOL = 1.0


def interior_thickness(exterior_mm: float = DEFAULT_EXTERIOR_THICKNESS_MM) -> float:
    """Ic duvar = dis - 50 mm (hangi dis kalinlik secilirse secilsin)."""
    return exterior_mm - INTERIOR_THICKNESS_DELTA_MM


def _on_edge(wall: dict, polygon: list[list[float]]) -> bool:
    """Duvar, poligonun bir kenariyla esdogrusal VE >1mm ortusuyor mu."""
    n = len(polygon)
    ws, we = wall["start"], wall["end"]
    for k in range(n):
        a, b = polygon[k], polygon[(k + 1) % n]
        ex, ey = b[0] - a[0], b[1] - a[1]
        elen = (ex * ex + ey * ey) ** 0.5
        if elen < 1e-9:
            continue
        d0 = abs(ex * (ws[1] - a[1]) - ey * (ws[0] - a[0])) / elen
        d1 = abs(ex * (we[1] - a[1]) - ey * (we[0] - a[0])) / elen
        if d0 > _TOL or d1 > _TOL:
            continue
        t0 = ((ws[0] - a[0]) * ex + (ws[1] - a[1]) * ey) / elen
        t1 = ((we[0] - a[0]) * ex + (we[1] - a[1]) * ey) / elen
        if min(max(t0, t1), elen) - max(min(t0, t1), 0.0) > _TOL:
            return True
    return False


def _on_envelope(wall: dict, walls: list[dict]) -> bool:
    xs = [p[0] for w in walls for p in (w["start"], w["end"])]
    ys = [p[1] for w in walls for p in (w["start"], w["end"])]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    (sx, sy), (ex, ey) = wall["start"], wall["end"]
    return (
        (abs(sx - x0) <= _TOL and abs(ex - x0) <= _TOL)
        or (abs(sx - x1) <= _TOL and abs(ex - x1) <= _TOL)
        or (abs(sy - y0) <= _TOL and abs(ey - y0) <= _TOL)
        or (abs(sy - y1) <= _TOL and abs(ey - y1) <= _TOL)
    )


def classify_walls(walls: list[dict], rooms: list[dict]) -> dict[str, str | None]:
    """{wall_id: 'dis' | 'ic' | None} - bkz. modul dokstring."""
    result: dict[str, str | None] = {}
    for wall in walls:
        if _on_envelope(wall, walls):
            result[wall["id"]] = CLASS_EXTERIOR
            continue
        touching = [r for r in rooms if _on_edge(wall, r["polygon"])]
        if not touching:
            result[wall["id"]] = None
            continue
        units = {r.get("unit_id") or None for r in touching}
        if len(units) > 1:
            result[wall["id"]] = CLASS_EXTERIOR
        elif None not in units:
            result[wall["id"]] = CLASS_INTERIOR
        else:
            result[wall["id"]] = None
    return result


def check_wall_thickness(
    walls: list[dict], rooms: list[dict], units: str, *,
    exterior_mm: float = DEFAULT_EXTERIOR_THICKNESS_MM,
) -> list[str]:
    """WARN: bildirilen kalinlik sinifin varsayilanindan saparsa (kat basina
    TEK ozet uyari - yuzlerce satir uretmemek icin) ve ic duvar dis duvardan
    kalin/esitse."""
    to_mm = 1.0 if units == "mm" else 1000.0
    expected = {CLASS_EXTERIOR: exterior_mm, CLASS_INTERIOR: interior_thickness(exterior_mm)}
    classes = classify_walls(walls, rooms)
    warnings: list[str] = []
    for cls in (CLASS_EXTERIOR, CLASS_INTERIOR):
        off = [
            w for w in walls
            if classes[w["id"]] == cls
            and abs(float(w["thickness"]) * to_mm - expected[cls]) > _TOL
        ]
        if off:
            sample = ", ".join(w["id"] for w in off[:5]) + (" ..." if len(off) > 5 else "")
            warnings.append(
                f"{len(off)} {'dis' if cls == CLASS_EXTERIOR else 'ic'} duvar "
                f"kalinligi varsayilan {expected[cls]:.0f}mm'den farkli "
                f"(ornek: {sample})."
            )
    ext = [float(w["thickness"]) * to_mm for w in walls if classes[w["id"]] == CLASS_EXTERIOR]
    inn = [float(w["thickness"]) * to_mm for w in walls if classes[w["id"]] == CLASS_INTERIOR]
    if ext and inn and max(inn) >= min(ext):
        warnings.append(
            f"ic duvar ({max(inn):.0f}mm) dis duvardan ({min(ext):.0f}mm) "
            f"ince degil - hiyerarsi dis > ic olmali (varsayilan fark "
            f"{INTERIOR_THICKNESS_DELTA_MM:.0f}mm)."
        )
    return warnings
