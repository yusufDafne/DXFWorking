"""Kolon tarama ve isimlendirme stilleri.

`ColumnHatchStyle` - tarama deseni/olcegi DINAMIKTIR ama varsayilani vardir
(kullanici karari: `ANSI33`, olcek `3.0`). `ColumnLabelStyle` - kolon adi
gosterimi; kullanici kolonlari AKS KESISIMIYLE ifade ettigi icin varsayilan
KAPALI, ama altyapi ileriye donuk hazir birakildi.
"""
from __future__ import annotations

from dataclasses import dataclass

from .standard import (
    COLUMN_HATCH_LAYER,
    COLUMN_TEXT_LAYER,
    DEFAULT_HATCH_PATTERN,
    DEFAULT_HATCH_SCALE,
)

@dataclass(frozen=True)
class ColumnHatchStyle:
    """Kolon taramasi. Desen ve olcek dinamiktir; asagidakiler varsayilandir."""

    pattern: str = DEFAULT_HATCH_PATTERN
    scale: float = DEFAULT_HATCH_SCALE
    angle: float = 0.0
    layer: str = COLUMN_HATCH_LAYER
    enabled: bool = True

    @classmethod
    def from_context(cls, data: dict | None) -> "ColumnHatchStyle":
        """`meta.column_hatch` verilirse ondan, verilmezse varsayilandan."""
        if not data:
            return cls()
        return cls(
            pattern=str(data.get("pattern", DEFAULT_HATCH_PATTERN)),
            scale=float(data.get("scale", DEFAULT_HATCH_SCALE)),
            angle=float(data.get("angle", 0.0)),
            enabled=bool(data.get("enabled", True)),
        )


@dataclass(frozen=True)
class ColumnLabelStyle:
    """Kolon adi gosterimi. Kullanici su an istemedigi icin varsayilan KAPALI;
    altyapi hazir birakildi (ileriye donuk tasarim)."""

    enabled: bool = False
    height: float = 180.0
    layer: str = COLUMN_TEXT_LAYER

    @classmethod
    def from_context(cls, data: dict | None) -> "ColumnLabelStyle":
        if not data:
            return cls()
        return cls(
            enabled=bool(data.get("enabled", False)),
            height=float(data.get("height", 180.0)),
        )
