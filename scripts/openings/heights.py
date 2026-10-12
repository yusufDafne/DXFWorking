"""Pencere yuksekligi ve denizlik (DEV-072).

Kullanici karari (2026-10-12): varsayilan pencere yuksekligi 1200 mm; BOY pencere (ornegin balkon kapisi) yuksekligi 2000 mm ve
zeminden 40 mm baslar. Bunlar VARSAYILANDIR: kullanici `openings[].height` / `openings[].sill_height` verirse o deger gecerlidir
(olcu ve konum dinamik). Normal pencerenin denizligi VERILMEDI: hicbir yerde varsayilan/0 olarak kullanilmaz ("verilmedi").

Katalog sabitleri `context.json`a yazilmaz (cizim sabiti sizmaz); kaynaklari buradadir. Kullanilan her varsayilan ADIYLA bildirilir
(`defaults_used`, `scripts/defaults_report.py`) - sessiz varsayilan yoktur (DEV-069 ilkesi).
"""
from __future__ import annotations

from dataclasses import dataclass

DEFAULT_WINDOW_HEIGHT_MM = 1200.0          # kullanici karari 2026-10-12
DEFAULT_TALL_WINDOW_HEIGHT_MM = 2000.0     # kullanici karari 2026-10-12 (boy pencere / balkon kapisi)
DEFAULT_TALL_WINDOW_SILL_MM = 40.0         # kullanici karari 2026-10-12 (zeminden 4 cm)
DEFAULT_SOURCE = "kullanici karari 2026-10-12"

CLASS_STANDARD = "standard"
CLASS_TALL = "tall"
WINDOW_CLASSES = (CLASS_STANDARD, CLASS_TALL)

SRC_GIVEN = "verilen"
SRC_UNKNOWN = "verilmedi"


@dataclass(frozen=True)
class ResolvedHeights:
    """`height` her zaman bir sayidir (verilen ya da katalog varsayilani); `sill` verilmediyse None. Kaynak etiketleri:
    'verilen' | 'varsayilan:<SABIT_ADI>' | 'verilmedi'."""
    window_class: str
    height: float
    sill: float | None
    height_source: str
    sill_source: str


def window_class_of(opening: dict) -> str:
    return opening.get("window_class", CLASS_STANDARD)


def resolve_window_heights(opening: dict) -> ResolvedHeights:
    """Bir `type: window` acikligi icin yukseklik/denizligi cozer. Kullanici degeri varsayilani ezer."""
    cls = window_class_of(opening)
    if cls not in WINDOW_CLASSES:
        raise ValueError(f"Aciklik '{opening.get('id')}': window_class {WINDOW_CLASSES} olmali, '{cls}' verildi.")
    if "height" in opening:
        height, hsrc = float(opening["height"]), SRC_GIVEN
    elif cls == CLASS_TALL:
        height, hsrc = DEFAULT_TALL_WINDOW_HEIGHT_MM, "varsayilan:DEFAULT_TALL_WINDOW_HEIGHT_MM"
    else:
        height, hsrc = DEFAULT_WINDOW_HEIGHT_MM, "varsayilan:DEFAULT_WINDOW_HEIGHT_MM"
    if "sill_height" in opening:
        sill, ssrc = float(opening["sill_height"]), SRC_GIVEN
    elif cls == CLASS_TALL:
        sill, ssrc = DEFAULT_TALL_WINDOW_SILL_MM, "varsayilan:DEFAULT_TALL_WINDOW_SILL_MM"
    else:
        sill, ssrc = None, SRC_UNKNOWN          # kullanici normal pencere denizligini VERMEDI: uydurulmaz
    return ResolvedHeights(cls, height, sill, hsrc, ssrc)


def defaults_used(context: dict) -> dict[str, int]:
    """{varsayilan sabit adi: kac pencerede kullanildi} + 'denizlik verilmedi' sayaci (normal pencere). Salt okunur."""
    out: dict[str, int] = {}
    for fl in context.get("floors", []):
        for op in fl.get("openings", []):
            if op.get("type") != "window":
                continue
            r = resolve_window_heights(op)
            for src in (r.height_source, r.sill_source):
                if src.startswith("varsayilan:"):
                    name = src.split(":", 1)[1]
                elif src == SRC_UNKNOWN:
                    name = "(denizlik verilmedi)"
                else:
                    continue
                out[name] = out.get(name, 0) + 1
    return dict(sorted(out.items()))


def floor_height_of(floor: dict) -> float | None:
    """Katin kat-kat yuksekligi (mm): kat verisinde `stairs[].floor_to_floor_mm` varsa en kucugu; yoksa None (kontrol atlanir)."""
    vals = [float(s["floor_to_floor_mm"]) for s in floor.get("stairs", []) if s.get("floor_to_floor_mm")]
    return min(vals) if vals else None


def check_window_heights(floor: dict) -> list[str]:
    """validate.py UYARILARI: denizlik + yukseklik kat yuksekligini asarsa (kat yuksekligi verisi varsa). Denizligi bilinmeyen pencere
    icin denizlik 0 alinmaz: yalniz yukseklik kat yuksekligiyle karsilastirilir. Kat yuksekligi verisi yoksa kontrol atlanir."""
    limit = floor_height_of(floor)
    out: list[str] = []
    for op in floor.get("openings", []):
        if op.get("type") != "window":
            continue
        try:
            r = resolve_window_heights(op)
        except ValueError as exc:
            out.append(str(exc))
            continue
        if limit is None:
            continue
        top = r.height + (r.sill if r.sill is not None else 0.0)
        if top > limit:
            out.append(f"Pencere '{op['id']}': denizlik + yukseklik {top:.0f} mm kat yuksekligini ({limit:.0f} mm) asiyor.")
    return out


def check_window_class_errors(openings: list[dict]) -> list[str]:
    """validate.py HATALARI (veri kalitesi): `window_class` yalniz `type: window` icin anlamlidir; gecersiz sinif; sill_height < 0."""
    out: list[str] = []
    for op in openings:
        if "window_class" in op:
            if op.get("type") != "window":
                out.append(f"Aciklik '{op['id']}': window_class yalniz type=window icin gecerlidir (type={op.get('type')!r}).")
            elif op["window_class"] not in WINDOW_CLASSES:
                out.append(f"Aciklik '{op['id']}': window_class {WINDOW_CLASSES} olmali, {op['window_class']!r} verildi.")
        if "sill_height" in op and op.get("type") != "window":
            out.append(f"Aciklik '{op['id']}': sill_height (denizlik) yalniz type=window icin gecerlidir.")
    return out
