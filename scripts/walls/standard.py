"""Duvar rail cizim standardi: Protocol + kind-farkindali varyantlar (DEV-014).

Sozlesmede zaten ongorulen genisleme noktasi ("rail cizimi bugun TEK
yontem"). `DefaultRailStandard` bugune kadarki DAVRANISI (duz LINE, duvar
turunden BAGIMSIZ) degistirmeden bir Protocol'e tasir; `CatalogRailStandard`
`WallCatalog`daki `tugla_bolme` (tarali) ve `cam_duvar` (farkli linetype)
turlerini GERCEKTEN gorsel olarak ayirir. Baska bir `kind` (veya `kind` YOK)
icin `CatalogRailStandard`, `DefaultRailStandard` ile BIREBIR AYNI sonucu
uretir - mevcut projelerde davranis degismez (hicbir duvar henuz `kind`
bildirmiyor, olculerek dogrulandi).
"""
from __future__ import annotations

from typing import Protocol

from .network import WallNetwork
from .wall import Wall

BRICK_KIND = "tugla_bolme"
GLASS_KIND = "cam_duvar"
BRICK_HATCH_PATTERN = "ANSI31"
BRICK_HATCH_SCALE = 1.5
BRICK_HATCH_ANGLE = 0.0
GLASS_LINETYPE = "CAM"


def ensure_glass_linetype(doc) -> None:
    """`CAM` linetype'ini idempotent yukler. `axis`/`elevations` de KENDI
    `DASHED` linetype'larini ayni desenle yukler; hicbiri birbirini import
    ETMEZ (kok CLAUDE.md 'moduller bagimsiz calisir'). `DASHED`i yeniden
    KULLANMADIK cunku cam duvar aks/zemin-alti ile AYNI anlama gelmez -
    ayni cizgi turu farkli semantikleri karistirirdi."""
    if GLASS_LINETYPE not in doc.linetypes:
        doc.linetypes.add(
            GLASS_LINETYPE,
            pattern=[300.0, 200.0, -100.0],
            description="Cam bolme rail cizgisi",
        )


def wall_fill_spans(wall: Wall, openings: list[dict]) -> list[tuple[float, float]]:
    """Aciklarla kesilmis, duvarin TAM boyundaki (`[0, wall.length]`) dolgu
    araliklari - tarama SADECE bu araliklara girer, aciklik sektorune degil.

    **Bilinen basitlestirme:** kose/T miter'ini DIKKATE ALMAZ, `wall.length`
    (merkez cizgisi) kullanir - `scripts/collision/CLAUDE.md`deki "duvar ayak
    izi merkez cizgi + kalinliktir, gonyelenmis rail cokgeni degil" ile AYNI
    gerekce. Fark yalnizca duvar UCLARINDADIR (bkz. o dokumandaki not)."""
    gaps: list[tuple[float, float]] = []
    for opening in openings:
        if opening["wall_id"] != wall.id:
            continue
        half = opening["width"] / 2.0
        g_start = max(0.0, opening["position_from_start"] - half)
        g_end = min(wall.length, opening["position_from_start"] + half)
        if g_end > g_start:
            gaps.append((g_start, g_end))
    gaps.sort()

    cursor = 0.0
    spans: list[tuple[float, float]] = []
    for g_start, g_end in gaps:
        if g_start - cursor > 1e-6:
            spans.append((cursor, g_start))
        cursor = max(cursor, g_end)
    if wall.length - cursor > 1e-6:
        spans.append((cursor, wall.length))
    if not gaps:
        spans = [(0.0, wall.length)]
    return spans


class RailDrawingStandard(Protocol):
    def draw_rails(self, msp, wall: Wall, network: WallNetwork, openings: list[dict]) -> None: ...


class DefaultRailStandard:
    """Bugune kadarki TEK yontem: her iki rail duz `LINE`, duvar turunden
    BAGIMSIZ. Geriye donuk davranis referansidir - `CatalogRailStandard`
    bilinmeyen/eksik `kind` icin buna DUSER."""

    def draw_rails(self, msp, wall: Wall, network: WallNetwork, openings: list[dict]) -> None:
        for side in ("pos", "neg"):
            for p1, p2 in network.drawable_rail_segments(wall, side, openings):
                msp.add_line(p1, p2, dxfattribs={"layer": wall.layer})


class CatalogRailStandard:
    """`wall.kind`e gore FARKLI cizim. Tarama/linetype AYNI `wall.layer`
    uzerindedir (kolonlardaki sabit `KOLON-TARAMA` gibi ayri bir katman
    YOKTUR) - `wall.layer` DATA'dan gelir ve duvardan duvara degisebilir,
    bu yuzden sabit bir "<layer>-TARAMA" ciftine karar vermek yerine ayni
    katmanda ayri bir HATCH entity'si olarak kalir (hala tek tek secilebilir)."""

    def __init__(self, fallback: RailDrawingStandard | None = None):
        self._fallback = fallback or DefaultRailStandard()

    def draw_rails(self, msp, wall: Wall, network: WallNetwork, openings: list[dict]) -> None:
        if wall.kind == BRICK_KIND:
            self._fallback.draw_rails(msp, wall, network, openings)
            self._draw_hatch(msp, wall, openings)
        elif wall.kind == GLASS_KIND:
            ensure_glass_linetype(msp.doc)
            for side in ("pos", "neg"):
                for p1, p2 in network.drawable_rail_segments(wall, side, openings):
                    msp.add_line(p1, p2, dxfattribs={"layer": wall.layer, "linetype": GLASS_LINETYPE})
        else:
            self._fallback.draw_rails(msp, wall, network, openings)

    def _draw_hatch(self, msp, wall: Wall, openings: list[dict]) -> None:
        for a, b in wall_fill_spans(wall, openings):
            hatch = msp.add_hatch(dxfattribs={"layer": wall.layer})
            hatch.set_pattern_fill(BRICK_HATCH_PATTERN, scale=BRICK_HATCH_SCALE,
                                   angle=BRICK_HATCH_ANGLE)
            quad = [wall.rail_point("pos", a), wall.rail_point("pos", b),
                   wall.rail_point("neg", b), wall.rail_point("neg", a)]
            hatch.paths.add_polyline_path(quad, is_closed=True)
