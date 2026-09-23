"""Tefris gruplari, layer adlari ve kahverengi ailesi renkleri.

Renkler bilerek DUSUK KONTRASTLIDIR (kullanici talebi: zit renk kullanilmaz) -
tefris, duvar/aks gibi okunmasi gereken katmanla yarismaz. Layer'lar kod
tarafinda zorunlu kilinir; renk context.json'dan ALINMAZ (`ensure_axis_layer`
deseni).
"""
from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True)
class FurnitureGroup:
    """Islevsel tefris grubu: kendi layer'i ve kahverengi ailesinden tonu."""

    key: str
    layer: str
    rgb: tuple[int, int, int]
    label: str


# Kahverengi ailesi - bilerek DUSUK kontrastli tonlar (kullanici talebi).
FURNITURE_GROUPS: dict[str, FurnitureGroup] = {
    "OTURMA": FurnitureGroup("OTURMA", "TEFRIS-OTURMA", (139, 94, 60), "Oturma grubu"),
    "YEMEK": FurnitureGroup("YEMEK", "TEFRIS-YEMEK", (161, 120, 79), "Yemek grubu"),
    "YATAK": FurnitureGroup("YATAK", "TEFRIS-YATAK", (120, 86, 66), "Yatak odasi"),
    "MUTFAK": FurnitureGroup("MUTFAK", "TEFRIS-MUTFAK", (150, 111, 94), "Mutfak"),
    "ISLAK": FurnitureGroup("ISLAK", "TEFRIS-ISLAK", (131, 120, 106), "Islak hacim"),
}


def ensure_furniture_layers(doc, groups: dict[str, FurnitureGroup] | None = None) -> None:
    """Tefris layer'larini sabit RGB tonlariyla hazirlar (`ensure_axis_layer`
    deseni). Renk context'ten alinmaz; kod sahibidir."""
    for group in (groups or FURNITURE_GROUPS).values():
        if group.layer in doc.layers:
            layer = doc.layers.get(group.layer)
        else:
            layer = doc.layers.add(name=group.layer)
        layer.rgb = group.rgb


# --------------------------------------------------------------------------
# Cizim yardimcilari - hepsi blok TANIMI icine, yerel koordinatta cizer.
# Yerel orijin (0,0) = elemanin SOL-ALT kosesi.
# --------------------------------------------------------------------------
