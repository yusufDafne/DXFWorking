"""Aciklik verisi: tip, varyant, acilim yonu ve host duvar konumu.

rev-13 (DEV-016) ile uc alan eklendi ve HEPSININ VARSAYILANI, rev-12'ye kadarki
davranistir - yani mevcut projeler hicbir sey degistirmeden ayni cizimi uretir:

| Alan        | Varsayilan | Anlami                                            |
| ----------- | ---------- | ------------------------------------------------- |
| `variant`   | `single`   | tek kanat / cift kanat / surme / katlanir          |
| `swing`     | `left`     | mentese duvar BASLANGICINDA mi, sonunda mi         |
| `host_side` | `pos`      | kanat duvarin hangi tarafina aciliyor              |

**Acik karar kapandi (rev-13):** `position_from_start`, duvarin
baslangicindan acikligin **MERKEZINE** olan mesafedir ve boyle KORUNDU
(kenardan olcmeye cevrilmedi). Gerekce: degisiklik geriye uyumsuz bir schema
kirilimi (MAJOR) olurdu ve karsiliginda hicbir yetenek kazandirmazdi - ayni
bilgi iki gosterimde de tam olarak ifade edilebiliyor. Duvar boyunca gercek
bosluk araligi (`g_start`, `g_end`) HER ZAMAN `walls.gaps_for_wall` ile
alinir; bu hesabi ikinci bir yerde tekrarlamak rev-13'te gercek bir hataya
yol acmisti (cakisma sektoru cizilen yaydan yarim genislik kaymisti).
"""
from __future__ import annotations

from dataclasses import dataclass

TYPE_DOOR = "door"
TYPE_WINDOW = "window"

VARIANT_SINGLE = "single"
VARIANT_DOUBLE = "double"
VARIANT_SLIDING = "sliding"
VARIANT_FOLDING = "folding"
DOOR_VARIANTS = (VARIANT_SINGLE, VARIANT_DOUBLE, VARIANT_SLIDING, VARIANT_FOLDING)

SWING_LEFT = "left"
SWING_RIGHT = "right"
SWINGS = (SWING_LEFT, SWING_RIGHT)

SIDE_POS = "pos"
SIDE_NEG = "neg"
SIDES = (SIDE_POS, SIDE_NEG)

DEFAULT_LAYER = "KAPI-PENCERE"


@dataclass(frozen=True)
class Opening:
    id: str
    type: str
    wall_id: str
    position_from_start: float
    width: float
    layer: str = DEFAULT_LAYER
    variant: str = VARIANT_SINGLE
    swing: str = SWING_LEFT
    host_side: str = SIDE_POS

    def __post_init__(self) -> None:
        if self.variant not in DOOR_VARIANTS:
            raise ValueError(
                f"Aciklik '{self.id}': bilinmeyen varyant '{self.variant}'. "
                f"Gecerli varyantlar: {', '.join(DOOR_VARIANTS)}")
        if self.swing not in SWINGS:
            raise ValueError(
                f"Aciklik '{self.id}': 'swing' {SWINGS} olmali, "
                f"'{self.swing}' verildi.")
        if self.host_side not in SIDES:
            raise ValueError(
                f"Aciklik '{self.id}': 'host_side' {SIDES} olmali, "
                f"'{self.host_side}' verildi.")

    @classmethod
    def from_context(cls, data: dict) -> "Opening":
        return cls(
            id=data["id"],
            type=data["type"],
            wall_id=data["wall_id"],
            position_from_start=float(data["position_from_start"]),
            width=float(data["width"]),
            layer=data.get("layer", DEFAULT_LAYER),
            variant=data.get("variant", VARIANT_SINGLE),
            swing=data.get("swing", SWING_LEFT),
            host_side=data.get("host_side", SIDE_POS),
        )

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "wall_id": self.wall_id,
            "position_from_start": self.position_from_start,
            "width": self.width,
            "layer": self.layer,
            "variant": self.variant,
            "swing": self.swing,
            "host_side": self.host_side,
        }


class Door(Opening):
    """Door marker retaining the current schema-compatible opening shape."""


class Window(Opening):
    """Window marker retaining the current schema-compatible opening shape."""
