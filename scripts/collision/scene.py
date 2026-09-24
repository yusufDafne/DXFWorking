"""Ayak izlerini toplayan TEK yer.

Bu dosya, tum saglayicilari bilen tek dosyadir; motor (`engine.py`) hicbirini
bilmez. Liste ACIKTIR - import-time kayit sihri yoktur, cunku sessizce
kaybolan bir kayit sessizce DENETLENMEYEN bir modul demektir.

Yeni bir cizim modulu eklendiginde ya buraya bir satir eklenir ya da
`COLLISION_EXEMPT` icinde GEREKCESIYLE muaf tutulur. `scripts/doc_check.py`
bunu mekanik olarak denetler.
"""
from __future__ import annotations

import importlib
from dataclasses import dataclass, field

from .engine import Clash, CollisionEngine
from .matrix import CollisionPolicy
from .report import ClashReport
from .shapes import CollisionShape

# modul adi -> `footprints(floor, context)` fonksiyonunu tasiyan alt modul.
# Import LAZY yapilir (`Scene.collect` icinde): boylece `collision` paketi tek
# basina, hicbir cizim modulu yuklenmeden import edilebilir ve dairesel import
# olusmaz (`furniture.collision` -> `collision.shapes`).
FOOTPRINT_PROVIDERS: tuple[str, ...] = (
    "rooms.collision",
    "walls.collision",
    "columns.collision",
    "openings.collision",
    "furniture.collision",
)

# Geometri uretmeyen ya da plan duzleminde cakisma aranmayan moduller.
# Gerekce ZORUNLUDUR: "bu modul hangi modulle cakisabilir?" sorusunun yaziya
# dokulmus cevabi budur.
COLLISION_EXEMPT: dict[str, str] = {
    "pafta": "Pafta bir KAPSAYICIDIR, cizim elemani degil; tasma kontrolu "
             "Sheet.verify_within_frame ile DXF seviyesinde zaten yapilir.",
    "axis": "Aks bir referans cizgisidir, madde degildir - hicbir seyle "
            "cakismaz (politika matrisinde de IGNORE).",
    "dimensions": "Olcu zinciri anotasyondur; plan geometrisinde yer kaplamaz.",
    "typography": "Metin stili tanimlar; hic geometri uretmez.",
    "collision": "Motorun kendisi.",
    "elevations": "Cephe (elevation) semantik/basit bir seviye istifidir, "
                  "gercek plan geometrisinden turetilmez (kok CLAUDE.md "
                  "rev-2 karari). Bu motor sadece floors[] uzerinde calisir; "
                  "elevations[] ayri bir veri agacidir ve mekansal cakisma "
                  "kavraminin (oda/tefris/duvar) hicbiri orada yoktur.",
    "legend": "Kapi/pencere cetveli kapak paftasinin BOS alaninda duran bir "
              "OZET TABLODUR (metin+cizgi); plan geometrisinde yer kaplamaz "
              "ve hicbir mekansal elemanla aynı KOORDINAT UZAYINI paylasmaz "
              "(dimensions/typography ile ayni gerekce).",
    "importer": "context.json'u HIC OKUMAZ/gormez, salt-okunur bir DIS DXF "
                "tarayicisidir (DEV-013); bu projenin plan/kat geometrisiyle "
                "AYNI koordinat uzayinda YASAMAZ, cakisma kavraminin "
                "kapsami disindadir.",
    "sections": "Kesit (section), floors[] duzleminde YENI bir mekansal "
                "eleman EKLEMEZ - var olan duvarlarin DUSEY bir izdusumunu "
                "cizer (DEV-021). Bu motor SADECE plan (floors[]) duzleminde "
                "calisir; kesit sahnesi kendi dikey koordinat eksenindedir "
                "ve elevations/ ile AYNI gerekceyle kapsam disidir.",
    "northarrow": "Kuzey oku + olcek cubugu (DEV-025), meta.north_angle/"
                  "meta.scale'den TURETILEN sabit bir pafta SEMBOLUDUR "
                  "(basligi/aksi gibi) - proje geometrisiyle (oda/duvar/"
                  "tefris) hicbir mekansal iliskisi yoktur (axis/typography "
                  "ile AYNI gerekce, politika matrisinde IGNORE).",
}


@dataclass
class Scene:
    """Bir KATIN cakisma sahnesi.

    Cakisma yalnizca AYNI kat icinde aranir. Katlar arasi (dusey) hizalama
    ayri bir konudur ve bu motorun isi degildir - bkz.
    `scripts/columns/CLAUDE.md` "Bilinen sinirlamalar".
    """

    floor_code: str
    shapes: list[CollisionShape] = field(default_factory=list)

    @classmethod
    def from_floor(cls, floor: dict, context: dict) -> "Scene":
        scene = cls(floor_code=str(floor.get("code", "") or floor.get("id", "")))
        for provider_path in FOOTPRINT_PROVIDERS:
            module = importlib.import_module(provider_path)
            scene.shapes.extend(module.footprints(floor, context))
        return scene

    def detect(self, policy: CollisionPolicy | None = None) -> list[Clash]:
        return CollisionEngine(policy).detect(self.shapes, self.floor_code)


def check_context(context: dict, policy: CollisionPolicy | None = None) -> ClashReport:
    """Tum katlari tarar ve tek bir rapor dondurur."""
    report = ClashReport(units=context.get("meta", {}).get("units", "mm"))
    for floor in context.get("floors", []):
        report.extend(Scene.from_floor(floor, context).detect(policy))
    return report
