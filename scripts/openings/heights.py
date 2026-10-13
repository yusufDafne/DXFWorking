"""Pencere yuksekligi ve denizlik (DEV-072).

Kullanici karari (2026-10-12): varsayilan pencere yuksekligi 1200 mm ve zeminden 900 mm baslar (DEV-075; once "verilmedi" idi); BOY pencere
(ornegin balkon kapisi / dukkan vitrini) yuksekligi 2000 mm ve zeminden 40 mm baslar. Bunlar VARSAYILANDIR: kullanici
`openings[].height` / `openings[].sill_height` verirse o deger gecerlidir (olcu ve dusey konum dinamik).

Katalog sabitleri `context.json`a yazilmaz (cizim sabiti sizmaz); kaynaklari buradadir. Kullanilan her varsayilan ADIYLA bildirilir
(`defaults_used`, `scripts/defaults_report.py`) - sessiz varsayilan yoktur (DEV-069 ilkesi).
"""
from __future__ import annotations

from dataclasses import dataclass

from . import classes as _classes
from .classes import (DEFAULT_TALL_WINDOW_HEIGHT_MM, DEFAULT_TALL_WINDOW_SILL_MM, DEFAULT_WINDOW_HEIGHT_MM,  # noqa: F401
                      DEFAULT_WINDOW_SILL_MM, SOURCE as DEFAULT_SOURCE)

CLASS_STANDARD = "standard"
CLASS_TALL = "tall"
WINDOW_CLASSES = _classes.values_for("window")      # ('standard', 'tall', 'shopfront') - kayittan

SRC_GIVEN = "verilen"


@dataclass(frozen=True)
class ResolvedHeights:
    """`height` ve `sill` her zaman sayidir (verilen ya da katalog varsayilani). Kaynak etiketleri: 'verilen' | 'varsayilan:<SABIT_ADI>'."""
    window_class: str
    height: float
    sill: float
    height_source: str
    sill_source: str
    class_key: str = ""     # katalog anahtari ('window.tall', 'door.main_entry')


def window_class_of(opening: dict) -> str:
    return opening.get("window_class", CLASS_STANDARD)


def _resolve_with_spec(op: dict, spec) -> ResolvedHeights:
    """Sinif katalogundan yukseklik/denizlik; kullanici degeri (`height`, `sill_height`) varsayilani ezer."""
    _w, hname, sname = spec.names
    if "height" in op:
        height, hsrc = float(op["height"]), SRC_GIVEN
    else:
        height, hsrc = spec.height_mm, f"varsayilan:{hname}"
    if "sill_height" in op:
        sill, ssrc = float(op["sill_height"]), SRC_GIVEN
    else:
        sill, ssrc = spec.sill_mm, f"varsayilan:{sname}"
    return ResolvedHeights(spec.value, height, sill, hsrc, ssrc, spec.key)


def resolve_window_heights(opening: dict) -> ResolvedHeights:
    """Bir `type: window` acikligi icin yukseklik/denizligi cozer (sinif: `window_class`, varsayilan 'standard'). Kullanici degeri varsayilani ezer."""
    cls = window_class_of(opening)
    if cls not in WINDOW_CLASSES:
        raise ValueError(f"Aciklik '{opening.get('id')}': window_class {WINDOW_CLASSES} olmali, '{cls}' verildi.")
    return _resolve_with_spec(opening, _classes.OPENING_CLASSES[f"window.{cls}"])


def resolve_door_heights(opening: dict) -> ResolvedHeights | None:
    """SINIFLANDIRILMIS kapi (`door_class`) icin yukseklik/denizlik; siniflandirilmamis kapi icin None (kapi yuksekligi verisi yoktur)."""
    spec = _classes.class_of(opening) if opening.get("type") == "door" else None
    return None if spec is None else _resolve_with_spec(opening, spec)


def defaults_used(context: dict) -> dict[str, int]:
    """{varsayilan sabit adi: kac pencerede kullanildi}. Salt okunur."""
    out: dict[str, int] = {}
    for fl in context.get("floors", []):
        for op in fl.get("openings", []):
            if op.get("type") == "window":
                r = resolve_window_heights(op)
            elif op.get("type") == "door":
                r = resolve_door_heights(op)
                if r is None:
                    continue
            else:
                continue
            for src in (r.height_source, r.sill_source):
                if src.startswith("varsayilan:"):
                    name = src.split(":", 1)[1]
                    out[name] = out.get(name, 0) + 1
    return dict(sorted(out.items()))


def floor_height_of(floor: dict) -> float | None:
    """Katin kat-kat yuksekligi (mm): kat verisinde `stairs[].floor_to_floor_mm` varsa en kucugu; yoksa None (kontrol atlanir)."""
    vals = [float(s["floor_to_floor_mm"]) for s in floor.get("stairs", []) if s.get("floor_to_floor_mm")]
    return min(vals) if vals else None


def check_window_heights(floor: dict) -> list[str]:
    """validate.py UYARILARI: denizlik + yukseklik kat yuksekligini asarsa (kat yuksekligi verisi varsa). Kat yuksekligi verisi yoksa kontrol atlanir."""
    limit = floor_height_of(floor)
    out: list[str] = []
    for op in floor.get("openings", []):
        if op.get("type") not in ("window", "door"):
            continue
        try:
            r = resolve_window_heights(op) if op["type"] == "window" else resolve_door_heights(op)
        except ValueError as exc:
            out.append(str(exc))
            continue
        if r is None or limit is None:
            continue
        top = r.height + r.sill
        if top > limit:
            kind = "Pencere" if op["type"] == "window" else "Kapi"
            out.append(f"{kind} '{op['id']}': denizlik + yukseklik {top:.0f} mm kat yuksekligini ({limit:.0f} mm) asiyor.")
    return out


def check_window_class_errors(openings: list[dict]) -> list[str]:
    """validate.py HATALARI (veri kalitesi): `window_class` yalniz `type: window`, `door_class` yalniz `type: door` icin; gecersiz sinif; `sill_height` yalniz pencerede."""
    out: list[str] = []
    doors = _classes.values_for("door")
    for op in openings:
        if "window_class" in op:
            if op.get("type") != "window":
                out.append(f"Aciklik '{op['id']}': window_class yalniz type=window icin gecerlidir (type={op.get('type')!r}).")
            elif op["window_class"] not in WINDOW_CLASSES:
                out.append(f"Aciklik '{op['id']}': window_class {WINDOW_CLASSES} olmali, {op['window_class']!r} verildi.")
        if "door_class" in op:
            if op.get("type") != "door":
                out.append(f"Aciklik '{op['id']}': door_class yalniz type=door icin gecerlidir (type={op.get('type')!r}).")
            elif op["door_class"] not in doors:
                out.append(f"Aciklik '{op['id']}': door_class {doors} olmali, {op['door_class']!r} verildi.")
        if "sill_height" in op and op.get("type") != "window":
            out.append(f"Aciklik '{op['id']}': sill_height (denizlik) yalniz type=window icin gecerlidir.")
    return out
