"""Duvar turu / kalinlik katalogu — ofis veya yonetmelik standardina gore genisletilir.

context.json'daki duvar kaydi opsiyonel `kind` tasiyabilir; kalinlik ve katman
bu katalogdan cozulur veya acikca verilen degerlerle dogrulanir. Cizim
sabitleri context'e sizmaz (bkz. kok CLAUDE.md).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WallTypeSpec:
    """Tek bir duvar cinsinin parametreleri."""

    id: str
    label: str
    default_thickness_mm: float
    layer: str
    structural: bool = False
    # Ileride: linetype, hatch, yangin sinifi, TS/EN referansi


DEFAULT_WALL_CATALOG: dict[str, WallTypeSpec] = {
    "dis_tasiyici": WallTypeSpec(
        id="dis_tasiyici",
        label="Dis tasiyici duvar",
        default_thickness_mm=250.0,
        layer="DUVAR",
        structural=True,
    ),
    "ic_tasiyici": WallTypeSpec(
        id="ic_tasiyici",
        label="Ic tasiyici duvar",
        default_thickness_mm=200.0,
        layer="DUVAR",
        structural=True,
    ),
    "bolme": WallTypeSpec(
        id="bolme",
        label="Bolme duvari",
        default_thickness_mm=100.0,
        layer="DUVAR",
        structural=False,
    ),
    "tugla_bolme": WallTypeSpec(
        id="tugla_bolme",
        label="Tugla bolme",
        default_thickness_mm=125.0,
        layer="DUVAR",
        structural=False,
    ),
    "cam_duvar": WallTypeSpec(
        id="cam_duvar",
        label="Cam bolme (plan sembolu)",
        default_thickness_mm=50.0,
        layer="DUVAR",
        structural=False,
    ),
}


class WallCatalog:
    """Kayitli duvar turleri; alt sinif veya farkli sozluk ile baska standart."""

    def __init__(self, specs: dict[str, WallTypeSpec] | None = None):
        self._specs = dict(specs if specs is not None else DEFAULT_WALL_CATALOG)

    def register(self, spec: WallTypeSpec) -> None:
        self._specs[spec.id] = spec

    def get(self, kind_id: str) -> WallTypeSpec | None:
        return self._specs.get(kind_id)

    def resolve(self, wall_dict: dict) -> tuple[float, str, str | None]:
        """(thickness, layer, kind_id). Tasarim verisi (mm/katman) her zaman onceliklidir."""
        kind = wall_dict.get("kind")
        return float(wall_dict["thickness"]), wall_dict["layer"], kind

    def params_for_kind(self, kind_id: str) -> WallTypeSpec:
        spec = self._specs.get(kind_id)
        if spec is None:
            raise KeyError(f"Bilinmeyen duvar turu: {kind_id}")
        return spec

    def kinds(self) -> list[WallTypeSpec]:
        return list(self._specs.values())
