"""Kat geometrisinden olcu ordinatlarini TURETIR (DEV-017 Fikir 1).

**Karar (rev-13) — olcu TURETILIR, elle bildirilmez.** Bir olcu sayisi
tasarim verisi DEGILDIR, geometrinin OLCUSUDUR. Duvar koordinati zaten
`context.json`dadir; olcuyu ayrica elle yazmak ayni bilgiyi IKI yerde tutmak
olurdu ve kacinilmaz olarak ayrisirdi (duvar tasinir, olcu metni eski kalir -
bu, projenin "bayat satir" sorununun geometri halidir). Turetme, kok
CLAUDE.md'deki "olcu uydurulmaz" yasagini DELMEZ: sayi uydurulmuyor, context
geometrisinden OLCULUYOR.

Buna karsilik **hangi kenarin, hangi kademede olculenecegi bir SUNUM
kararidir** ve context'ten gelir (`meta.dimensions`).

Uc kademe (mimari gelenek: icten disa dogru kabalasir):

| Kademe    | Ne olculur                                   |
| --------- | -------------------------------------------- |
| `aciklik` | cephedeki kapi/pencere kenarlari             |
| `mahal`   | dik duvarlarin YUZLERI -> net mahal + kalinlik |
| `toplam`  | yapinin dis olcusu                           |
"""
from __future__ import annotations

from dataclasses import dataclass

try:
    from ..walls import Wall, WallCatalog
except ImportError:  # dogrudan `dimensions` olarak import edildiginde
    from walls import Wall, WallCatalog

from .chain import merge_ordinates

AXIS_X = "x"
AXIS_Y = "y"

LEVEL_OPENING = "aciklik"
LEVEL_ROOM = "mahal"
LEVEL_TOTAL = "toplam"

DEFAULT_LEVELS = (LEVEL_OPENING, LEVEL_ROOM, LEVEL_TOTAL)

GEOMETRY_TOLERANCE = 1.0


@dataclass(frozen=True)
class _Segment:
    """Bir duvarin olcu icin gereken sadelestirilmis hali."""

    wall: Wall
    horizontal: bool

    @property
    def constant(self) -> float:
        """Yatay duvarda y, dusey duvarda x."""
        return self.wall.start[1] if self.horizontal else self.wall.start[0]


class FloorOrdinates:
    """Bir katin olcu ordinatlari. Context'i DEGISTIRMEZ, yalnizca okur."""

    def __init__(self, floor: dict, tolerance: float = GEOMETRY_TOLERANCE):
        catalog = WallCatalog()
        self.tolerance = tolerance
        self.openings = floor.get("openings", [])
        self.segments: list[_Segment] = []
        for data in floor.get("walls", []):
            wall = Wall.from_context(data, catalog)
            dx = abs(wall.end[0] - wall.start[0])
            dy = abs(wall.end[1] - wall.start[1])
            if dx <= tolerance and dy <= tolerance:
                continue
            if dy <= tolerance:
                self.segments.append(_Segment(wall, horizontal=True))
            elif dx <= tolerance:
                self.segments.append(_Segment(wall, horizontal=False))
            # Egik duvarlar olculendirmeye GIRMEZ - eksen hizali bir zincire
            # anlamli bir ordinat veremezler (bkz. "Bilinen sinirlamalar").

    # ------------------------------------------------------------ yardimcilar
    def _perpendicular(self, axis: str) -> list[_Segment]:
        """X zinciri DUSEY duvarlarla, Y zinciri YATAY duvarlarla olculur."""
        return [s for s in self.segments if s.horizontal == (axis == AXIS_Y)]

    def _parallel(self, axis: str) -> list[_Segment]:
        return [s for s in self.segments if s.horizontal == (axis == AXIS_X)]

    def _coordinate(self, point, axis: str) -> float:
        return point[0] if axis == AXIS_X else point[1]

    def _facade(self, axis: str) -> list[_Segment]:
        """Olculenen kenardaki cephe duvarlari.

        X zinciri yapinin GUNEY kenarinda (en kucuk y), Y zinciri BATI
        kenarinda (en kucuk x) cizilir; cephe duvari da o kenardakidir."""
        parallel = self._parallel(axis)
        if not parallel:
            return []
        edge = min(s.constant for s in parallel)
        return [s for s in parallel if abs(s.constant - edge) <= self.tolerance]

    # -------------------------------------------------------------- kademeler
    def total(self, axis: str) -> list[float]:
        """Yapinin DIS YUZDEN DIS YUZE olcusu.

        Merkez cizgisi degil YUZ alinir: dis duvarin merkez cizgisi 0'da ve
        kalinligi 250 ise yapinin gercek dis olcusu -125'ten baslar. Boylece
        uc kademe de AYNI ordinatlarda baslayip biter - mimari bir olcu
        yigininin gorunusu budur. Merkezden merkeze olcu aks zincirinin isidir.
        """
        values: list[float] = []
        for segment in self.segments:
            half = segment.wall.thickness / 2.0
            if segment.horizontal == (axis == AXIS_X):
                # Duvar bu eksen boyunca UZANIYOR -> uc noktalari
                values.append(self._coordinate(segment.wall.start, axis))
                values.append(self._coordinate(segment.wall.end, axis))
            else:
                # Duvar bu ekseni DIK kesiyor -> iki yuzu
                center = self._coordinate(segment.wall.start, axis)
                values.extend((center - half, center + half))
        if not values:
            return []
        return [min(values), max(values)]

    def room(self, axis: str) -> list[float]:
        """Dik duvarlarin IKI YUZU -> net mahal olcusu + duvar kalinligi.

        Merkez cizgisi degil YUZLER alinir: mimari uygulamada beklenen olcu
        net (yuzden yuze) olcudur; merkezden merkeze olcu aks zincirinin
        isidir ve o zaten `axis` modulunde cizilir."""
        values: list[float] = []
        for segment in self._perpendicular(axis):
            center = self._coordinate(segment.wall.start, axis)
            half = segment.wall.thickness / 2.0
            values.extend((center - half, center + half))
        values.extend(self.total(axis))
        return merge_ordinates(values, self.tolerance)

    def opening(self, axis: str) -> list[float]:
        """Cephedeki kapi/pencere kenarlari."""
        facade = {s.wall.id: s.wall for s in self._facade(axis)}
        values: list[float] = []
        for opening in self.openings:
            wall = facade.get(opening.get("wall_id"))
            if wall is None:
                continue
            start = float(opening["position_from_start"])
            width = float(opening["width"])
            for distance in (start, start + width):
                point = wall.centerline_point(distance)
                values.append(self._coordinate(point, axis))
        if not values:
            return []
        values.extend(self.total(axis))
        return merge_ordinates(values, self.tolerance)

    def for_level(self, level: str, axis: str) -> list[float]:
        if level == LEVEL_OPENING:
            return self.opening(axis)
        if level == LEVEL_ROOM:
            return self.room(axis)
        if level == LEVEL_TOTAL:
            return self.total(axis)
        raise KeyError(
            f"Bilinmeyen olcu kademesi: '{level}'. Gecerli kademeler: "
            f"{', '.join(DEFAULT_LEVELS)}"
        )
