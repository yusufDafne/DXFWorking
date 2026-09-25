"""Merdiven modulu (DEV-022): kat paftalarina GERCEK basamak/riht geometrisi,
yon oku ve kesme cizgisi cizer.

**Neden ayri bir modul (kullanici karari, 2026-09-25):** proje motifiyle
tutarli - kolonun `columns/` ve tefrisin `furniture/` ile iliskisine benzer
bir "oda-ici ek eleman = kendi modulu" deseni. `rooms/` bugunku net kapsamini
(poligon + 3 satirli etiket) korur; `stairs/` yalnizca merdiven olarak
isaretlenmis odanin ICINE ek geometri cizer.

**Tek kaynak ilkesi (openings::swing_geometry ile AYNI desen):** `resolve_stair`
hem `validate.py`nin hem cizim kodunun (`draw_stairs_on_floor`) OKUDUGU TEK
fonksiyondur. Ikisi ayri hesap yaparsa (rev-13'te kapi acilim sektorunde
gercekten oldugu gibi) sessizce ayrisirlar.

**Veri disiplini:** `floor_to_floor_mm` GERCEK proje verisidir (kat
yuksekligi) - hicbir zaman uydurulmaz, context'te acikca verilir.
`riser_height_mm`/`going_mm` ise OFIS CIZIM STANDARDIDIR (ANSI33 hatch
olcegi, Arial Narrow font secimi ile AYNI kategoride bir kod-seviyeli
varsayim) - verilmezse `DEFAULT_RISER_MM`/`DEFAULT_GOING_MM` kullanilir.
`auto_flex` (varsayilan ACIK) bu varsayilanlari kat yuksekligine ve oda
uzunluguna TAM oturacak sekilde ince ayarlar; her esnetme kullaniciya
UYARI olarak raporlanir (sessiz varsayim yapilmaz, bkz. kok CLAUDE.md
"Deterministik uretim ilkesi").

**Bilinen sinirlama (v1 kapsami, bkz. scripts/stairs/CLAUDE.md):** yalnizca
TEK DUZ KOL (sahanliksiz) merdiven desteklenir; kol, merdiven odasinin uzun
ekseni boyunca kosar. Bu, kucuk bir "sirkulasyon bandi" odasinda (orn. bu
projenin ornek 4000x3000mm Merdiven odasi) yuksek bir kat icin FIZIKSEL
OLARAK YETERSIZ olabilir - boyle bir durumda `resolve_stair` bir
`StairFitError` firlatir (sessizce gecersiz/guvensiz bir basamak genisligi
uretmez). Bu KASITLIDIR: cift kollu/sahanlikli merdiven gelecekte ayri bir
gelistirme konusudur.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Protocol

try:
    from ..palette import color_for
except ImportError:  # dogrudan scripts/ uzerinden calistirildiginda
    from palette import color_for

STAIR_LAYER = "MERDIVEN"
# Kod-seviyeli sabit renk (ensure_axis_layer deseni) - context.json'dan
# ALINMAZ. Renk artik scripts/palette::PALETTE'in TEK kaynagindan gelir
# (DEV-030, sonradan tamamlandi); DEGER AYNI (60,120,150) kalir - bilerek
# diger "primary" kod-seviyeli tonlarindan (AKS gri, KOLON ailesi, KESIT
# kirmizi) uzak bir mavi-gri ailesi.
STAIR_RGB = color_for(STAIR_LAYER)

DEFAULT_RISER_MM = 170.0     # ofis standardi (TS/mimari pratikte tipik 16-18cm)
DEFAULT_GOING_MM = 270.0     # ofis standardi (makul bant 250-300mm, orta deger)
MIN_GOING_MM = 250.0
MAX_GOING_MM = 300.0
DEFAULT_AUTO_FLEX = True
RISER_TOLERANCE_MM = 5.0     # bu tolerensin ustundeki esnetme UYARI uretir

PRINTED_ARROW_HEAD_MM = 3.0  # yon oku ucundaki ok basi boyu (kagit uzerinde)
BREAK_LINE_FRACTION = 0.65   # kesme cizgisinin asagi-uctan itibaren orani
BREAK_TICK_RATIO = 0.18      # kesme cizgisi zigzag genisligi / dik eksen uzunlugu


class StairFitError(ValueError):
    """Merdiven, verilen oda ICINE (veya verilen sabit degerlerle kat
    yuksekligine) GUVENLE sigmiyor - sessizce gecersiz bir tasarim uretmek
    yerine acikca durur."""


@dataclass(frozen=True)
class StairResolution:
    """`resolve_stair`in TEK ciktisi - hem validate.py hem cizim kodu bunu
    okur (bkz. modul docstring'i)."""

    stair_id: str
    room_id: str
    step_count: int
    riser_mm: float
    going_mm: float
    travel_axis: str          # 'x' veya 'y'
    up_towards: str | None    # 'N'/'S'/'E'/'W' veya None
    bbox: tuple[float, float, float, float]   # xmin, ymin, xmax, ymax
    warnings: list[str] = field(default_factory=list)


def _bbox(polygon: list[list[float]]) -> tuple[float, float, float, float]:
    xs = [p[0] for p in polygon]
    ys = [p[1] for p in polygon]
    return min(xs), min(ys), max(xs), max(ys)


def resolve_stair(spec: dict, room_polygon: list[list[float]]) -> StairResolution:
    """Bir `stairs[]` girdisini (context.json) + referans verdigi oda
    poligonunu, cizim/denetim icin gereken TUM turetilmis degerlere cozer.
    Hicbir sey uydurmaz: `floor_to_floor_mm` girdi olarak GELIR, riser/going
    yalnizca EKSIKSE ofis standardina duser."""
    stair_id = spec["id"]
    room_id = spec["room_id"]
    xmin, ymin, xmax, ymax = _bbox(room_polygon)
    dx, dy = xmax - xmin, ymax - ymin
    travel_axis = "x" if dx >= dy else "y"
    run_available = dx if travel_axis == "x" else dy

    up_towards = spec.get("up_towards")
    if up_towards is not None:
        expected = {"x": ("E", "W"), "y": ("N", "S")}[travel_axis]
        if up_towards not in expected:
            raise StairFitError(
                f"Merdiven '{stair_id}': up_towards='{up_towards}' merdivenin uzun "
                f"ekseniyle ({travel_axis}) tutarsiz; beklenen: {expected}."
            )

    floor_to_floor = float(spec["floor_to_floor_mm"])
    auto_flex = spec.get("auto_flex", DEFAULT_AUTO_FLEX)
    warnings: list[str] = []

    nominal_riser = float(spec.get("riser_height_mm", DEFAULT_RISER_MM))
    if spec.get("step_count"):
        step_count = int(spec["step_count"])
        riser = floor_to_floor / step_count
        if abs(riser - nominal_riser) > RISER_TOLERANCE_MM:
            warnings.append(
                f"Merdiven '{stair_id}': step_count={step_count} ile turetilen riht "
                f"{riser:.1f}mm, nominal riht {nominal_riser:.1f}mm'den farkli."
            )
    else:
        step_count = max(2, round(floor_to_floor / nominal_riser))
        if auto_flex:
            riser = floor_to_floor / step_count
            if abs(riser - nominal_riser) > RISER_TOLERANCE_MM:
                warnings.append(
                    f"Merdiven '{stair_id}': riht OTOMATIK esnetildi "
                    f"({nominal_riser:.1f}mm -> {riser:.1f}mm, {step_count} basamak) "
                    f"- kat yuksekligi {floor_to_floor:.0f}mm tam bolunsun diye."
                )
        else:
            riser = nominal_riser
            total = riser * step_count
            if abs(total - floor_to_floor) > RISER_TOLERANCE_MM:
                warnings.append(
                    f"Merdiven '{stair_id}': toplam riht yuksekligi ({total:.1f}mm) "
                    f"kat yuksekligini ({floor_to_floor:.0f}mm) TAM karsilamiyor "
                    f"(auto_flex kapali)."
                )

    nominal_going = float(spec.get("going_mm", DEFAULT_GOING_MM))
    required_run = (step_count - 1) * nominal_going
    going = nominal_going
    if required_run > run_available + 1e-6:
        if not auto_flex:
            raise StairFitError(
                f"Merdiven '{stair_id}': gerekli kosu uzunlugu ({required_run:.1f}mm) "
                f"oda uzunlugunu ({run_available:.1f}mm) asiyor (auto_flex kapali)."
            )
        going = run_available / (step_count - 1)
        warnings.append(
            f"Merdiven '{stair_id}': basamak genisligi OTOMATIK daraltildi "
            f"({nominal_going:.1f}mm -> {going:.1f}mm) - oda uzunluguna "
            f"({run_available:.1f}mm) sigdirmak icin."
        )

    # MIN_GOING_MM her zaman (esnetilmis VEYA acikca verilmis going_mm icin
    # AYNI SEKILDE) denetlenir - yalnizca daraltma dalinda kontrol etmek,
    # zaten sigan bir odaya acikca verilmis GUVENSIZ bir going_mm'in
    # sessizce gecmesine izin verirdi (bkz. scripts/stairs/CLAUDE.md
    # "sessizce gecersiz/guvensiz bir basamak genisligi uretmez").
    if going < MIN_GOING_MM:
        raise StairFitError(
            f"Merdiven '{stair_id}': basamak genisligi ({going:.1f}mm) minimum "
            f"konfor sinirinin ({MIN_GOING_MM:.0f}mm) altinda kalir - tek duz "
            f"kollu merdiven bu odaya SIGMIYOR (esnetildiyse) veya verilen "
            f"going_mm degeri gecersiz (esnetilmediyse). Oda buyutulmeli, "
            f"going_mm artirilmali veya sahanlikli/cift kollu merdiven (henuz "
            f"desteklenmiyor) gerekir."
        )
    if going > MAX_GOING_MM:
        warnings.append(
            f"Merdiven '{stair_id}': basamak genisligi ({going:.1f}mm) makul "
            f"bandin ({MAX_GOING_MM:.0f}mm) USTUNDE - standart disi, gozden "
            f"gecirilmeli."
        )

    return StairResolution(
        stair_id=stair_id, room_id=room_id, step_count=step_count,
        riser_mm=riser, going_mm=going, travel_axis=travel_axis,
        up_towards=up_towards, bbox=(xmin, ymin, xmax, ymax), warnings=warnings,
    )


def _travel_points(resolution: StairResolution) -> tuple[tuple[float, float], tuple[float, float]]:
    """(asagi-uc, yukari-uc) merkez noktalari. `up_towards` yoksa 'min' ucu
    keyfi olarak 'asagi' kabul edilir (yon anlami YOKTUR, sadece deterministik
    bir capa)."""
    down_c, up_c = _travel_coords(resolution)
    xmin, ymin, xmax, ymax = resolution.bbox
    mid_x, mid_y = (xmin + xmax) / 2.0, (ymin + ymax) / 2.0
    if resolution.travel_axis == "x":
        return (down_c, mid_y), (up_c, mid_y)
    return (mid_x, down_c), (mid_x, up_c)


def _travel_coords(resolution: StairResolution) -> tuple[float, float]:
    """(asagi-uc, yukari-uc) - YALNIZCA travel ekseni uzerindeki SKALER
    koordinat (x ekseni icin x, y ekseni icin y). `up_towards` yoksa 'min'
    ucu keyfi olarak 'asagi' kabul edilir (yon anlami YOKTUR, sadece
    deterministik bir capa)."""
    xmin, ymin, xmax, ymax = resolution.bbox
    up = resolution.up_towards
    if resolution.travel_axis == "x":
        if up == "W":
            return xmax, xmin
        return xmin, xmax   # up == 'E' veya None
    if up == "S":
        return ymax, ymin
    return ymin, ymax       # up == 'N' veya None


def _step_line_endpoints(resolution: StairResolution, distance_from_down: float) -> tuple[tuple[float, float], tuple[float, float]]:
    xmin, ymin, xmax, ymax = resolution.bbox
    down_c, up_c = _travel_coords(resolution)
    direction = 1.0 if up_c >= down_c else -1.0
    coord = down_c + direction * distance_from_down
    if resolution.travel_axis == "x":
        return (coord, ymin), (coord, ymax)
    return (xmin, coord), (xmax, coord)


class StairDrawingStandard(Protocol):
    def draw(self, msp, resolution: StairResolution, layer: str) -> None: ...


@dataclass(frozen=True)
class DefaultStairStandard:
    """Bugunku standart gorsel: esit araliklarla `step_count - 1` riht
    cizgisi (oda sinirlari zaten ilk/son basamagi temsil eder, tekrar
    cizilmez) + (yon biliniyorsa) bir yon oku + kesme cizgisi."""

    def draw(self, msp, resolution: StairResolution, layer: str) -> None:
        for i in range(1, resolution.step_count):
            distance = i * resolution.going_mm
            start, end = _step_line_endpoints(resolution, distance)
            msp.add_line(start, end, dxfattribs={"layer": layer})

        if resolution.up_towards is None:
            return

        down, up = _travel_points(resolution)
        arrow_start = down
        arrow_end = (
            down[0] + (up[0] - down[0]) * BREAK_LINE_FRACTION,
            down[1] + (up[1] - down[1]) * BREAK_LINE_FRACTION,
        )
        msp.add_line(arrow_start, arrow_end, dxfattribs={"layer": layer})
        self._draw_arrowhead(msp, arrow_start, arrow_end, layer)
        self._draw_break_line(msp, resolution, arrow_end, layer)

    @staticmethod
    def _draw_arrowhead(msp, start, end, layer: str) -> None:
        dx, dy = end[0] - start[0], end[1] - start[1]
        length = math.hypot(dx, dy)
        if length < 1e-6:
            return
        ux, uy = dx / length, dy / length
        head = PRINTED_ARROW_HEAD_MM * 40.0   # kaba modelspace olcegi; cizim sabiti
        px, py = -uy, ux
        tip = end
        b1 = (tip[0] - ux * head + px * head * 0.5, tip[1] - uy * head + py * head * 0.5)
        b2 = (tip[0] - ux * head - px * head * 0.5, tip[1] - uy * head - py * head * 0.5)
        triangle = msp.add_lwpolyline([tip, b1, b2], dxfattribs={"layer": layer})
        triangle.closed = True

    @staticmethod
    def _draw_break_line(msp, resolution: StairResolution, center, layer: str) -> None:
        xmin, ymin, xmax, ymax = resolution.bbox
        perp = (ymax - ymin) if resolution.travel_axis == "x" else (xmax - xmin)
        tick = perp * BREAK_TICK_RATIO
        if resolution.travel_axis == "x":
            p1 = (center[0] - tick * 0.3, center[1] - perp / 2.0)
            p2 = (center[0] + tick * 0.3, center[1] - perp / 2.0 + tick)
            p3 = (center[0] - tick * 0.3, center[1] + perp / 2.0 - tick)
            p4 = (center[0] + tick * 0.3, center[1] + perp / 2.0)
        else:
            p1 = (center[0] - perp / 2.0, center[1] - tick * 0.3)
            p2 = (center[0] - perp / 2.0 + tick, center[1] + tick * 0.3)
            p3 = (center[0] + perp / 2.0 - tick, center[1] - tick * 0.3)
            p4 = (center[0] + perp / 2.0, center[1] + tick * 0.3)
        msp.add_line(p1, p2, dxfattribs={"layer": layer})
        msp.add_line(p3, p4, dxfattribs={"layer": layer})


def ensure_stair_layer(doc) -> None:
    """`MERDIVEN` katmanini idempotent kurar (`ensure_axis_layer` deseni)."""
    if STAIR_LAYER in doc.layers:
        layer = doc.layers.get(STAIR_LAYER)
    else:
        layer = doc.layers.add(name=STAIR_LAYER)
    layer.rgb = STAIR_RGB


def stairs_for_floor(floor: dict) -> list[StairResolution]:
    """`floor['stairs']`teki HER girdiyi `resolve_stair` ile cozer. `room_id`
    gecersizse (validate.py zaten bunu HATA olarak yakalamis olmali) o
    girdi atlanir - bu fonksiyon validate.py DEGILDIR, sessizce dayanikli
    kalir."""
    rooms_by_id = {r["id"]: r for r in floor.get("rooms", [])}
    resolutions: list[StairResolution] = []
    for spec in floor.get("stairs", []):
        room = rooms_by_id.get(spec["room_id"])
        if room is None:
            continue
        resolutions.append(resolve_stair(spec, room["polygon"]))
    return resolutions


def draw_stairs_on_floor(msp, floor: dict, standard: StairDrawingStandard | None = None,
                         layer: str = STAIR_LAYER) -> list[str]:
    """Bir kat paftasindaki TUM merdivenleri cizer, toplanan UYARILARI
    dondurur (generate_dxf.py bunlari basar)."""
    standard = standard or DefaultStairStandard()
    warnings: list[str] = []
    for resolution in stairs_for_floor(floor):
        standard.draw(msp, resolution, layer)
        warnings.extend(resolution.warnings)
    return warnings


# Bu modulun CONTEXT SOZLESMESI surumu (DEV-020). KOD surumu DEGILDIR.
# Bkz. scripts/version.py
CONTRACT_VERSION = "1.0"

__all__ = [
    "STAIR_LAYER",
    "STAIR_RGB",
    "DEFAULT_RISER_MM",
    "DEFAULT_GOING_MM",
    "MIN_GOING_MM",
    "MAX_GOING_MM",
    "DEFAULT_AUTO_FLEX",
    "StairFitError",
    "StairResolution",
    "resolve_stair",
    "StairDrawingStandard",
    "DefaultStairStandard",
    "ensure_stair_layer",
    "stairs_for_floor",
    "draw_stairs_on_floor",
    "CONTRACT_VERSION",
]
