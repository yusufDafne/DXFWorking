"""Cakisma motorunun ANONIM geometri birimi.

Bu dosyanin tasarim amaci tek cumleyle sudur: **motor koltugun ne oldugunu
bilmez.** Bir `CollisionShape`, bir etiket (`tag`), bir kimlik ve bir cokgenden
ibarettir. Boylece `collision/` hicbir cizim modulunu import etmeden calisir;
her modul kendi ayak izini kendisi uretir (`scripts/<modul>/collision.py`).

Benzetme: bir fizik motoru arabayi ve agaci tanimaz, yalnizca collider tanir.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from .geometry import aabb, as_points

# --------------------------------------------------------------- etiketler
# Politika matrisi bu etiketler uzerinden kurulur (bkz. `matrix.py`).
TAG_FURNITURE = "tefris"
TAG_COLUMN = "kolon"
TAG_WALL = "duvar"
TAG_DOOR_SWING = "kapi_acilim"
TAG_ROOM = "mahal"

# Kapi acilim yayinin kac dogru parcasiyla yaklasildigi. SABITTIR ve olcege
# BAGLI DEGILDIR: deterministik uretim ilkesi geregi ayni context her zaman
# ayni cakisma raporunu vermelidir. Sektor icbukey olmasin diye yay acisi
# 180 dereceyi asmamalidir (kapi acilimi 90 derecedir).
SECTOR_SEGMENTS = 8


@dataclass(frozen=True)
class CollisionShape:
    """Bir elemanin PLAN DUZLEMINDEKI ayak izi.

    `container=True` olan sekiller cift-cift cakisma taramasina GIRMEZ; onlar
    baska sekilleri KAPSAMASI beklenen hacimlerdir (bugun yalnizca oda).
    """

    tag: str
    id: str
    polygon: tuple[tuple[float, float], ...]
    label: str = ""
    container: bool = False

    @property
    def bbox(self) -> tuple[float, float, float, float]:
        return aabb(self.polygon)

    @property
    def title(self) -> str:
        return f"{self.id} ({self.label})" if self.label else self.id


def polygon_shape(tag: str, shape_id: str, points, *, label: str = "",
                  container: bool = False) -> CollisionShape:
    return CollisionShape(tag, shape_id, tuple(as_points(points)),
                          label=label, container=container)


def rect_shape(tag: str, shape_id: str, origin, width: float, depth: float,
               rotation: float = 0.0, *, label: str = "",
               anchor: str = "corner") -> CollisionShape:
    """Donmus dikdortgen ayak izi.

    `anchor="corner"` -> `origin` SOL-ALT kose (tefris blok ekleme noktasi).
    `anchor="center"` -> `origin` MERKEZ (kolon yerlesimi).
    Donme her iki durumda da `origin` etrafindadir; bu, ilgili modullerin
    cizim davranisiyla birebir ayni olmalidir.
    """
    angle = math.radians(rotation)
    cos_a, sin_a = math.cos(angle), math.sin(angle)
    if anchor == "center":
        local = ((-width / 2.0, -depth / 2.0), (width / 2.0, -depth / 2.0),
                 (width / 2.0, depth / 2.0), (-width / 2.0, depth / 2.0))
    elif anchor == "corner":
        local = ((0.0, 0.0), (width, 0.0), (width, depth), (0.0, depth))
    else:
        raise ValueError(f"Bilinmeyen anchor: '{anchor}' (corner|center)")

    ox, oy = float(origin[0]), float(origin[1])
    points = tuple((ox + lx * cos_a - ly * sin_a, oy + lx * sin_a + ly * cos_a)
                   for lx, ly in local)
    return CollisionShape(tag, shape_id, points, label=label)


def segment_shape(tag: str, shape_id: str, start, end, thickness: float, *,
                  label: str = "") -> CollisionShape:
    """Kalinliga sahip bir dogru parcasinin dikdortgen ayak izi (duvar).

    Duvar ayak izi olarak MERKEZ CIZGI + KALINLIK kullanilir, cizimdeki
    gonyelenmis rail cokgeni degil. Gerekce: gonye birlesim yalnizca duvar
    UCLARINI etkiler ve tefris/kolon cakismasi acisindan fark yaratmaz; buna
    karsilik `WallNetwork` kurmak bu modulu duvar cizim sirasina bagimli
    kilardi. Bkz. `scripts/walls/CLAUDE.md`.
    """
    sx, sy = float(start[0]), float(start[1])
    ex, ey = float(end[0]), float(end[1])
    dx, dy = ex - sx, ey - sy
    length = math.hypot(dx, dy)
    if length == 0.0:
        raise ValueError(f"Sifir uzunluklu duvar: '{shape_id}'")
    ux, uy = dx / length, dy / length
    nx, ny = -uy * thickness / 2.0, ux * thickness / 2.0
    points = ((sx + nx, sy + ny), (ex + nx, ey + ny),
              (ex - nx, ey - ny), (sx - nx, sy - ny))
    return CollisionShape(tag, shape_id, points, label=label)


def sector_shape(tag: str, shape_id: str, center, radius: float,
                 start_deg: float, end_deg: float, *, label: str = "",
                 segments: int = SECTOR_SEGMENTS) -> CollisionShape:
    """Dairesel sektor (kapi acilim alani) cokgen yaklasimi.

    Merkez + yay noktalari. Yay acisi <= 180 derece oldugu surece sonuc
    DISBUKEYDIR, yani `polygon_clip` icin gecerli bir kirpan olabilir.
    """
    if segments < 2:
        raise ValueError("sector_shape en az 2 parca ister.")
    cx, cy = float(center[0]), float(center[1])
    span = end_deg - start_deg
    points = [(cx, cy)]
    for i in range(segments + 1):
        angle = math.radians(start_deg + span * i / segments)
        points.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
    return CollisionShape(tag, shape_id, tuple(points), label=label)


def circle_shape(tag: str, shape_id: str, center, radius: float, *,
                 label: str = "", segments: int = 16) -> CollisionShape:
    """Dairesel kesit (dairesel kolon) cokgen yaklasimi - ICTEN degil, DISTAN
    ornekler; yani gercek daireden biraz KUCUKTUR. Kolon icin bu kabul
    edilebilir: kolonun disbukey govdesi zaten kesit kutusuyla sinirlidir."""
    cx, cy = float(center[0]), float(center[1])
    points = tuple(
        (cx + radius * math.cos(2 * math.pi * i / segments),
         cy + radius * math.sin(2 * math.pi * i / segments))
        for i in range(segments)
    )
    return CollisionShape(tag, shape_id, points, label=label)
