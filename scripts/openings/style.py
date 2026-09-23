"""Aciklik sembol stili: enjekte edilebilir Protocol + varsayilan ofis stili."""
from __future__ import annotations

from typing import Protocol

from .opening import TYPE_DOOR, VARIANT_SINGLE
from .symbols import DOOR_SYMBOLS, draw_jambs, draw_window


class OpeningSymbolStyle(Protocol):
    def draw_opening(self, msp, wall, g_start: float, g_end: float, opening: dict) -> None: ...


class DefaultPlanOpeningStyle:
    """Ofis plan stili: soye cizgileri + tipe/varyanta gore sembol.

    Varyant secimi VERI ODAKLIDIR (`symbols.DOOR_SYMBOLS` sozlugu): yeni bir
    kapi tipi eklemek icin alt sinif yazmak gerekmez, sozluge bir fonksiyon
    eklenir. Bilinmeyen varyant SESSIZCE atlanmaz - `Opening.__post_init__`
    zaten uretimi durdurur.
    """

    def __init__(self, door_symbols: dict | None = None):
        self.door_symbols = dict(door_symbols if door_symbols is not None
                                 else DOOR_SYMBOLS)

    def draw_opening(self, msp, wall, g_start: float, g_end: float,
                     opening: dict) -> None:
        draw_jambs(msp, wall, g_start, g_end)
        if opening.get("type") == TYPE_DOOR:
            variant = opening.get("variant", VARIANT_SINGLE)
            symbol = self.door_symbols.get(variant)
            if symbol is None:
                raise KeyError(
                    f"Aciklik '{opening.get('id')}': '{variant}' varyanti icin "
                    f"sembol yok. Tanimli varyantlar: "
                    f"{', '.join(sorted(self.door_symbols))}")
            symbol(msp, wall, g_start, g_end, opening)
        else:
            draw_window(msp, wall, g_start, g_end, opening)
