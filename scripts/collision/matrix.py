"""Hangi ciftin cakismasi HATA, hangisi UYARI, hangisi NORMAL.

Bu dosya kararin kendisidir: motor "nasil kesisiyor"u hesaplar, matris
"kesismesi sorun mu"ya cevap verir. Ikisinin ayri tutulmasinin sebebi, yeni
bir kuralin geometri koduna dokunmadan eklenebilmesidir.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .shapes import (
    TAG_COLUMN,
    TAG_DOOR_SWING,
    TAG_FURNITURE,
    TAG_ROOM,
    TAG_WALL,
)


class Policy(Enum):
    """Uc seviye. Ikili bir 'hata/hata degil' yetmez: duvara DAYALI bir dolap
    normaldir ama duvarin ICINDEN gecen bir dolap degildir."""

    FORBID = "HATA"
    WARN = "UYARI"
    IGNORE = "NORMAL"


# Bu esigin ALTINDAKI girisim TEMAS sayilir, cakisma degil.
#
# Neden ALAN degil DERINLIK: 2100 mm'lik bir koltuk duvara 5 mm girse kesisim
# alani 10500 mm^2 olur; alan esigi bu yuzden eleman boyuyla olceklenir ve
# anlamsizdir. Bunun yerine kesisim cokgeninin KISA kenarina bakilir
# (`geometry.min_extent`) - bu, girisimin gercek derinligidir.
CONTACT_TOLERANCE = 5.0  # mm

# Oda icinde kalma testinde kenar toleransi: duvara tam dayali bir tefrisin
# kosesi oda poligonunun kenarina birebir oturur ve "disarida" sayilmamalidir.
CONTAINMENT_TOLERANCE = 5.0  # mm


@dataclass(frozen=True)
class CollisionPolicy:
    """Cift -> politika eslemesi.

    `unknown`, matriste TANIMSIZ bir cift icin uygulanan politikadir ve
    varsayilani `IGNORE`'dur: bilinmeyen bir cift yuzunden uretimin durmasi,
    yeni bir modulun eklenmesini cezalandirirdi. Sessiz kalma riskini
    `doc_check.py` kapatir - geometri ureten her modul ya bir saglayiciya ya
    da gerekcesi yazili bir muafiyete sahip olmak zorundadir.
    """

    pairs: dict[frozenset[str], Policy] = field(default_factory=dict)
    containment: dict[str, str] = field(default_factory=dict)
    contact_tolerance: float = CONTACT_TOLERANCE
    containment_tolerance: float = CONTAINMENT_TOLERANCE
    unknown: Policy = Policy.IGNORE

    def for_pair(self, tag_a: str, tag_b: str) -> Policy:
        return self.pairs.get(frozenset({tag_a, tag_b}), self.unknown)

    def container_for(self, tag: str) -> str | None:
        """`tag` etiketli sekillerin ICINDE kalmasi gereken kapsayici etiketi."""
        return self.containment.get(tag)


# --------------------------------------------------------- varsayilan matris
#
# Gerekceler `docs/development/DEVELOPMENT_TASKS.md::DEV-019` ile birebir
# aynidir; burasi o kararin CALISAN halidir.
DEFAULT_PAIRS: dict[frozenset[str], Policy] = {
    # iki mobilya ayni yerde duramaz
    frozenset({TAG_FURNITURE}): Policy.FORBID,
    # tasiyici gecilemez
    frozenset({TAG_FURNITURE, TAG_COLUMN}): Policy.FORBID,
    # kapi acilamaz hale gelir
    frozenset({TAG_FURNITURE, TAG_DOOR_SWING}): Policy.FORBID,
    # dolap duvara DAYANIR; mm olceginde temas normaldir, girisim degildir
    frozenset({TAG_FURNITURE, TAG_WALL}): Policy.WARN,
    # kolonun duvarin icinde olmasi TASARIMDIR
    frozenset({TAG_COLUMN, TAG_WALL}): Policy.IGNORE,
    # kolon bir odanin icinde durabilir (strukturel gercek)
    frozenset({TAG_COLUMN, TAG_ROOM}): Policy.IGNORE,
    frozenset({TAG_COLUMN}): Policy.FORBID,
    # kapi onunde kolon olmaz
    frozenset({TAG_COLUMN, TAG_DOOR_SWING}): Policy.FORBID,
    # duvarlar gonye birlesir; ayrica validate.py duvar agini zaten denetler
    frozenset({TAG_WALL}): Policy.IGNORE,
    # acilim yayi zaten duvardan baslar
    frozenset({TAG_WALL, TAG_DOOR_SWING}): Policy.IGNORE,
    # rev-13 (DEV-016): swing yonu artik SCHEMA'DA -> iki kapinin birbirine
    # acilmasi gercekten tespit edilebilir ve HATADIR. rev-12'de bu cift
    # IGNORE birakilmisti cunku yay sabit bir varsayilan tarafa ciziliyordu ve
    # kontrol yanlis-pozitif uretirdi.
    frozenset({TAG_DOOR_SWING}): Policy.FORBID,
}

# Tefris, katindaki odalardan EN AZ BIRININ icinde tamamen kalmalidir.
DEFAULT_CONTAINMENT: dict[str, str] = {TAG_FURNITURE: TAG_ROOM}

DEFAULT_POLICY = CollisionPolicy(
    pairs=DEFAULT_PAIRS,
    containment=DEFAULT_CONTAINMENT,
)
