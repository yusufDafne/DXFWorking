"""Cakisma cekirdegi: kaba faz -> ince faz -> `Clash` kayitlari.

Motor yalnizca `CollisionShape` gorur. Hangi modulden geldigini, nasil
cizildigini veya hangi layer'a yazilacagini BILMEZ.
"""
from __future__ import annotations

from dataclasses import dataclass

from .geometry import (
    aabb_overlap,
    is_convex,
    min_extent,
    point_inside_or_on,
    polygon_area,
    polygon_clip,
)
from .matrix import DEFAULT_POLICY, CollisionPolicy, Policy
from .shapes import CollisionShape

KIND_OVERLAP = "cakisma"
KIND_CONTAINMENT = "kapsama"


@dataclass(frozen=True)
class Clash:
    """Tek bir bulgu. `b` yalnizca cift kontrolunde doludur."""

    kind: str
    policy: Policy
    floor_code: str
    a: CollisionShape
    b: CollisionShape | None = None
    area: float = 0.0
    depth: float = 0.0
    # containment kaydinda hangi kapsayicinin arandigini mesaja tasir
    a_container_tag: str = ""

    @property
    def blocking(self) -> bool:
        return self.policy is Policy.FORBID

    def message(self, units: str = "mm") -> str:
        area_m2 = self.area / 1_000_000.0 if units == "mm" else self.area
        where = f"[{self.floor_code}] " if self.floor_code else ""
        if self.kind == KIND_CONTAINMENT:
            return (f"{where}{self.a.tag} '{self.a.title}' hicbir "
                    f"{self.a_container_tag} icinde tamamen kalmiyor.")
        return (f"{where}{self.a.tag} '{self.a.title}' ile {self.b.tag} "
                f"'{self.b.title}' cakisiyor "
                f"(kesisim ~{area_m2:.3f} m2, girisim derinligi ~{self.depth:.0f} mm).")


class CollisionEngine:
    """Sekil listesini alir, politikaya gore bulgulari dondurur.

    Kaba faz (AABB) olmadan 23 tefris + 9 kolon + 6 duvar iceren kucuk bir
    kat bile ~700 poligon kirpmasi yapardi; gercek bir katta bu sayi hizla
    buyur. AABB elemesi bunu birkac ona indirir.
    """

    def __init__(self, policy: CollisionPolicy | None = None):
        self.policy = policy or DEFAULT_POLICY

    def detect(self, shapes: list[CollisionShape],
               floor_code: str = "") -> list[Clash]:
        clashes: list[Clash] = []
        clashes += self._detect_pairs(shapes, floor_code)
        clashes += self._detect_containment(shapes, floor_code)
        return clashes

    # ------------------------------------------------------------ cift kontrol
    def _detect_pairs(self, shapes: list[CollisionShape],
                      floor_code: str) -> list[Clash]:
        candidates = [s for s in shapes if not s.container]
        boxes = [s.bbox for s in candidates]
        found: list[Clash] = []

        for i in range(len(candidates)):
            for j in range(i + 1, len(candidates)):
                a, b = candidates[i], candidates[j]
                policy = self.policy.for_pair(a.tag, b.tag)
                if policy is Policy.IGNORE:
                    continue
                if not aabb_overlap(boxes[i], boxes[j]):
                    continue

                area, depth = self._overlap(a, b)
                if depth <= self.policy.contact_tolerance:
                    # ince bir dilim: TEMAS, girisim degil
                    continue
                found.append(Clash(KIND_OVERLAP, policy, floor_code, a, b,
                                   area=area, depth=depth))
        return found

    def _overlap(self, a: CollisionShape, b: CollisionShape) -> tuple[float, float]:
        """(kesisim alani, girisim derinligi).

        `polygon_clip` KIRPAN poligonun disbukey olmasini ister; bu yuzden
        cift icinde disbukey olani kirpan secilir. Ikisi de icbukeyse (bugun
        varsayilan matriste boyle bir cift YOK) kaba sinir kutusu kesisimi
        kullanilir - bu "daha cok bildir" yonunde bir hatadir, sessiz kalmaz.
        """
        if is_convex(b.polygon):
            subject, clip = a.polygon, b.polygon
        elif is_convex(a.polygon):
            subject, clip = b.polygon, a.polygon
        else:
            return self._bbox_overlap(a, b)

        result = polygon_clip(subject, clip)
        if len(result) < 3:
            return 0.0, 0.0
        return polygon_area(result), min_extent(result)

    @staticmethod
    def _bbox_overlap(a: CollisionShape, b: CollisionShape) -> tuple[float, float]:
        ax0, ay0, ax1, ay1 = a.bbox
        bx0, by0, bx1, by1 = b.bbox
        width = min(ax1, bx1) - max(ax0, bx0)
        height = min(ay1, by1) - max(ay0, by0)
        if width <= 0 or height <= 0:
            return 0.0, 0.0
        return width * height, min(width, height)

    # -------------------------------------------------------- icerme kontrolu
    def _detect_containment(self, shapes: list[CollisionShape],
                            floor_code: str) -> list[Clash]:
        found: list[Clash] = []
        tolerance = self.policy.containment_tolerance

        for shape in shapes:
            if shape.container:
                continue
            container_tag = self.policy.container_for(shape.tag)
            if not container_tag:
                continue
            containers = [s for s in shapes
                          if s.container and s.tag == container_tag]
            if not containers:
                # kapsayici hic bildirilmemisse kontrol edilecek bir sey yok
                continue
            if any(self._contains(container, shape, tolerance)
                   for container in containers):
                continue
            found.append(Clash(KIND_CONTAINMENT, Policy.FORBID, floor_code,
                               shape, None, a_container_tag=container_tag))
        return found

    @staticmethod
    def _contains(container: CollisionShape, shape: CollisionShape,
                  tolerance: float) -> bool:
        """Sekil, kapsayicinin ICINDE TAMAMEN kaliyor mu?

        Kose noktalari uzerinden bakilir. Bu, iki odanin sinirina BINEN bir
        tefrisi de yakalar (hicbir tek oda onu tam kapsamaz) - ki bu da
        gercek bir yerlesim hatasidir.
        """
        return all(point_inside_or_on(point, container.polygon, tolerance)
                   for point in shape.polygon)
