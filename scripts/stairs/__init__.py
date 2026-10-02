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

# --- DEV-046: cift kollu (sahanlikli, "dog-leg"/U donuslu) merdiven ---
SINGLE_FLIGHT = "single_flight"
DOG_LEG = "dog_leg"
STAIR_KINDS = frozenset({SINGLE_FLIGHT, DOG_LEG})
DEFAULT_STAIR_KIND = SINGLE_FLIGHT

# "Pratik varsayilan" (bu modulun kendi riser/going varsayilanlariyla AYNI
# disiplin - resmi yonetmelik atfi DEGIL). Sahanlik derinligi tipik olarak
# bir kol genisligine yakin tutulur.
DEFAULT_LANDING_DEPTH_MM = 1100.0
# Tek kolda HICBIR zaman kontrol EDILMEYEN yeni bir basarisizlik modu: cift
# kollu merdivende oda kisa ekseni IKIYE bolunur, her kol bu asgarinin
# ALTINA duserse GUVENSIZ/KULLANILAMAZ (StairFitError, MIN_GOING_MM ile AYNI
# "sessizce gecersiz uretme" disiplini).
MIN_FLIGHT_WIDTH_MM = 900.0

# DEV-047: cikis YONU, giris yonunun (up_towards) TAM TERSIDIR (cift kollu
# merdiven 180 derece donup geri gelir).
_OPPOSITE_DIRECTION = {"N": "S", "S": "N", "E": "W", "W": "E"}


class StairFitError(ValueError):
    """Merdiven, verilen oda ICINE (veya verilen sabit degerlerle kat
    yuksekligine) GUVENLE sigmiyor - sessizce gecersiz bir tasarim uretmek
    yerine acikca durur."""


@dataclass(frozen=True)
class StairResolution:
    """`resolve_stair`in TEK ciktisi - hem validate.py hem cizim kodu bunu
    okur (bkz. modul docstring'i).

    DEV-046/DEV-047: `kind='dog_leg'` icin `landing_bbox`/`flight_step_
    counts` dolu, `kind='single_flight'` icin `landing_bbox=None` ve
    `flight_step_counts=(step_count,)` (eski davranis BIREBIR korunur).
    `exit_point`/`exit_direction`, merdivenin GERCEKTEN nereden/hangi
    yone ciktigini verir - tek kollu icin bu ODANIN GEOMETRIK kosesiyle
    CAKISIR (eski varsayimla AYNI), cift kollu icin merdiven GEOMETRISINDEN
    TURER (180 derece donus nedeniyle GIRIS ucuna YAKIN bir noktadir)."""

    stair_id: str
    room_id: str
    step_count: int
    riser_mm: float
    going_mm: float
    travel_axis: str          # 'x' veya 'y'
    up_towards: str | None    # 'N'/'S'/'E'/'W' veya None
    bbox: tuple[float, float, float, float]   # xmin, ymin, xmax, ymax
    exit_point: tuple[float, float]
    exit_direction: str | None
    kind: str = SINGLE_FLIGHT
    landing_depth_mm: float = 0.0
    landing_bbox: tuple[float, float, float, float] | None = None
    flight_step_counts: tuple[int, ...] = ()
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

    kind = spec.get("kind", DEFAULT_STAIR_KIND)
    if kind not in STAIR_KINDS:
        raise StairFitError(
            f"Merdiven '{stair_id}': bilinmeyen kind='{kind}'. Taninan "
            f"turler: {sorted(STAIR_KINDS)}."
        )

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

    landing_depth_mm = 0.0
    flight_step_counts: tuple[int, ...] = (step_count,)
    landing_bbox: tuple[float, float, float, float] | None = None
    if kind == DOG_LEG:
        # DEV-046: oda kisa eksende IKI koluna bolunur, her ikisi de AYNI
        # (uzun eksendeki) kosu araligini - sahanlik dusulmus halde - paylasir
        # (bkz. scripts/stairs/CLAUDE.md "cift kollu merdiven geometrisi").
        landing_depth_mm = float(spec.get("landing_depth_mm", DEFAULT_LANDING_DEPTH_MM))
        perpendicular = dy if travel_axis == "x" else dx
        half_width = perpendicular / 2.0
        if half_width < MIN_FLIGHT_WIDTH_MM:
            raise StairFitError(
                f"Merdiven '{stair_id}': cift kollu icin kol genisligi "
                f"({half_width:.1f}mm = oda kisa ekseni/2) minimum konfor "
                f"sinirinin ({MIN_FLIGHT_WIDTH_MM:.0f}mm) altinda kalir - "
                f"oda buyutulmeli veya tek kollu merdivene donulmeli."
            )
        flight1_steps = math.ceil(step_count / 2)
        flight2_steps = step_count - flight1_steps
        flight_step_counts = (flight1_steps, flight2_steps)
        run_available = run_available - landing_depth_mm
        if run_available <= 0:
            raise StairFitError(
                f"Merdiven '{stair_id}': sahanlik derinligi ({landing_depth_mm:.0f}mm) "
                f"odanin uzun ekseninden ({dx if travel_axis == 'x' else dy:.0f}mm) "
                f"buyuk/esit - kol icin hic yer kalmiyor."
            )
        binding_steps = flight1_steps   # her zaman >= flight2_steps
    else:
        binding_steps = step_count

    nominal_going = float(spec.get("going_mm", DEFAULT_GOING_MM))
    required_run = (binding_steps - 1) * nominal_going
    going = nominal_going
    if required_run > run_available + 1e-6:
        if not auto_flex:
            raise StairFitError(
                f"Merdiven '{stair_id}': gerekli kosu uzunlugu ({required_run:.1f}mm) "
                f"oda uzunlugunu ({run_available:.1f}mm) asiyor (auto_flex kapali)."
            )
        going = run_available / (binding_steps - 1)
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
            f"konfor sinirinin ({MIN_GOING_MM:.0f}mm) altinda kalir - bu merdiven "
            f"(kind='{kind}') bu odaya SIGMIYOR (esnetildiyse) veya verilen "
            f"going_mm degeri gecersiz (esnetilmediyse). Oda buyutulmeli veya "
            f"going_mm artirilmali."
        )
    if going > MAX_GOING_MM:
        warnings.append(
            f"Merdiven '{stair_id}': basamak genisligi ({going:.1f}mm) makul "
            f"bandin ({MAX_GOING_MM:.0f}mm) USTUNDE - standart disi, gozden "
            f"gecirilmeli."
        )

    bbox = (xmin, ymin, xmax, ymax)
    if kind == DOG_LEG:
        flight1_steps, flight2_steps = flight_step_counts
        exit_point, exit_direction, landing_bbox = _dog_leg_exit_and_landing(
            travel_axis, up_towards, bbox, landing_depth_mm, going,
            flight1_steps, flight2_steps,
        )
    else:
        down_point, up_point = _travel_points(travel_axis, up_towards, bbox)
        exit_point = up_point
        exit_direction = up_towards

    return StairResolution(
        stair_id=stair_id, room_id=room_id, step_count=step_count,
        riser_mm=riser, going_mm=going, travel_axis=travel_axis,
        up_towards=up_towards, bbox=bbox, exit_point=exit_point,
        exit_direction=exit_direction, kind=kind,
        landing_depth_mm=landing_depth_mm, landing_bbox=landing_bbox,
        flight_step_counts=flight_step_counts, warnings=warnings,
    )


def _travel_coords(travel_axis: str, up_towards: str | None,
                    bbox: tuple[float, float, float, float]) -> tuple[float, float]:
    """(asagi-uc, yukari-uc) - YALNIZCA travel ekseni uzerindeki SKALER
    koordinat (x ekseni icin x, y ekseni icin y). `up_towards` yoksa 'min'
    ucu keyfi olarak 'asagi' kabul edilir (yon anlami YOKTUR, sadece
    deterministik bir capa)."""
    xmin, ymin, xmax, ymax = bbox
    if travel_axis == "x":
        if up_towards == "W":
            return xmax, xmin
        return xmin, xmax   # up == 'E' veya None
    if up_towards == "S":
        return ymax, ymin
    return ymin, ymax       # up == 'N' veya None


def _travel_points(travel_axis: str, up_towards: str | None,
                    bbox: tuple[float, float, float, float]) -> tuple[tuple[float, float], tuple[float, float]]:
    """(asagi-uc, yukari-uc) merkez noktalari - bkz. `_travel_coords`."""
    down_c, up_c = _travel_coords(travel_axis, up_towards, bbox)
    xmin, ymin, xmax, ymax = bbox
    mid_x, mid_y = (xmin + xmax) / 2.0, (ymin + ymax) / 2.0
    if travel_axis == "x":
        return (down_c, mid_y), (up_c, mid_y)
    return (mid_x, down_c), (mid_x, up_c)


def _perp_line_endpoints(travel_axis: str, perp_range: tuple[float, float],
                          coord: float) -> tuple[tuple[float, float], tuple[float, float]]:
    """Travel eksenine DIK, `coord`de (travel skaleri) baslayan, `perp_range`
    boyunca uzanan bir cizginin iki ucu - riht cizgileri VE kol bolucusu
    AYNI bu fonksiyonu kullanir."""
    lo, hi = perp_range
    if travel_axis == "x":
        return (coord, lo), (coord, hi)
    return (lo, coord), (hi, coord)


def _travel_line(travel_axis: str, perp_coord: float,
                  c1: float, c2: float) -> tuple[tuple[float, float], tuple[float, float]]:
    """Travel ekseni boyunca, SABIT `perp_coord`de, `c1`den `c2`ye bir
    cizginin iki ucu - cift kollu kol BOLUCUSU icin kullanilir."""
    if travel_axis == "x":
        return (c1, perp_coord), (c2, perp_coord)
    return (perp_coord, c1), (perp_coord, c2)


def _step_line_endpoints(travel_axis: str, up_towards: str | None,
                          bbox: tuple[float, float, float, float],
                          distance_from_down: float) -> tuple[tuple[float, float], tuple[float, float]]:
    xmin, ymin, xmax, ymax = bbox
    down_c, up_c = _travel_coords(travel_axis, up_towards, bbox)
    direction = 1.0 if up_c >= down_c else -1.0
    coord = down_c + direction * distance_from_down
    perp_range = (ymin, ymax) if travel_axis == "x" else (xmin, xmax)
    return _perp_line_endpoints(travel_axis, perp_range, coord)


def _dog_leg_exit_and_landing(
    travel_axis: str, up_towards: str | None, bbox: tuple[float, float, float, float],
    landing_depth_mm: float, going_mm: float, flight1_steps: int, flight2_steps: int,
) -> tuple[tuple[float, float], str | None, tuple[float, float, float, float]]:
    """DEV-047: cift kollu merdivenin GERCEK cikis noktasi/yonu + sahanlik
    kutusu. Kol 1, giris ucundan sahanliga (`up_towards` yonunde) cikar;
    sahanlik 180 derece donusu temsil eder; kol 2 sahanliktan giris ucuna
    DOGRU (TERS yonde) geri doner - cikis bu yuzden ODANIN GEOMETRIK
    'yukari' kosesi DEGIL, GIRIS ucuna YAKIN bir noktadir (bkz. modul
    CLAUDE.md "cift kollu merdiven geometrisi")."""
    xmin, ymin, xmax, ymax = bbox
    down_c, up_c = _travel_coords(travel_axis, up_towards, bbox)
    direction = 1.0 if up_c >= down_c else -1.0
    perp_min, perp_max = (ymin, ymax) if travel_axis == "x" else (xmin, xmax)
    mid_perp = (perp_min + perp_max) / 2.0
    flight2_perp_mid = (mid_perp + perp_max) / 2.0

    flight1_run = (flight1_steps - 1) * going_mm
    flight2_run = (flight2_steps - 1) * going_mm
    landing_start = down_c + direction * flight1_run
    landing_end = landing_start + direction * landing_depth_mm
    exit_coord = landing_end - direction * flight2_run

    if travel_axis == "x":
        exit_point = (exit_coord, flight2_perp_mid)
        landing_bbox = (min(landing_start, landing_end), perp_min,
                         max(landing_start, landing_end), perp_max)
    else:
        exit_point = (flight2_perp_mid, exit_coord)
        landing_bbox = (perp_min, min(landing_start, landing_end),
                         perp_max, max(landing_start, landing_end))

    exit_direction = _OPPOSITE_DIRECTION.get(up_towards) if up_towards else None
    return exit_point, exit_direction, landing_bbox


class StairDrawingStandard(Protocol):
    def draw(self, msp, resolution: StairResolution, layer: str) -> None: ...


@dataclass(frozen=True)
class DefaultStairStandard:
    """Bugunku standart gorsel: esit araliklarla `step_count - 1` riht
    cizgisi (oda sinirlari zaten ilk/son basamagi temsil eder, tekrar
    cizilmez) + (yon biliniyorsa) bir yon oku + kesme cizgisi.

    DEV-046: `kind='dog_leg'` icin iki kol + sahanlik kutusu + kol
    bolucusu AYRICA cizilir; yon oku/kesme cizgisi HER IKI turde de AYNI
    ortak kod yolundan gecer (`down`/`up` capa noktalari tur bazinda
    farkli hesaplanir, gerisi PAYLASILIR - tekrar YAZILMAZ)."""

    def draw(self, msp, resolution: StairResolution, layer: str) -> None:
        if resolution.kind == DOG_LEG:
            down, up = self._draw_dog_leg(msp, resolution, layer)
        else:
            for i in range(1, resolution.step_count):
                distance = i * resolution.going_mm
                start, end = _step_line_endpoints(
                    resolution.travel_axis, resolution.up_towards, resolution.bbox, distance,
                )
                msp.add_line(start, end, dxfattribs={"layer": layer})
            down, up = _travel_points(resolution.travel_axis, resolution.up_towards, resolution.bbox)

        if resolution.up_towards is None:
            return

        arrow_start = down
        arrow_end = (
            down[0] + (up[0] - down[0]) * BREAK_LINE_FRACTION,
            down[1] + (up[1] - down[1]) * BREAK_LINE_FRACTION,
        )
        msp.add_line(arrow_start, arrow_end, dxfattribs={"layer": layer})
        self._draw_arrowhead(msp, arrow_start, arrow_end, layer)
        perp_span = self._break_line_perp_span(resolution)
        self._draw_break_line(msp, resolution.travel_axis, perp_span, arrow_end, layer)

    @staticmethod
    def _draw_dog_leg(msp, resolution: StairResolution, layer: str) -> tuple[tuple[float, float], tuple[float, float]]:
        """Iki kol + sahanlik + kol bolucusunu cizer; yon oku icin
        (kol-2-baslangici, cikis) capa ciftini dondurur - tek kollu
        `(down, up)`in dog-leg karsiligi."""
        xmin, ymin, xmax, ymax = resolution.bbox
        travel_axis = resolution.travel_axis
        perp_min, perp_max = (ymin, ymax) if travel_axis == "x" else (xmin, xmax)
        mid_perp = (perp_min + perp_max) / 2.0
        flight1_range = (perp_min, mid_perp)
        flight2_range = (mid_perp, perp_max)

        down_c, up_c = _travel_coords(travel_axis, resolution.up_towards, resolution.bbox)
        direction = 1.0 if up_c >= down_c else -1.0
        flight1_steps, flight2_steps = resolution.flight_step_counts

        for i in range(1, flight1_steps):
            coord = down_c + direction * i * resolution.going_mm
            start, end = _perp_line_endpoints(travel_axis, flight1_range, coord)
            msp.add_line(start, end, dxfattribs={"layer": layer})

        landing_start = down_c + direction * (flight1_steps - 1) * resolution.going_mm
        landing_end = landing_start + direction * resolution.landing_depth_mm
        for i in range(1, flight2_steps):
            coord = landing_end - direction * i * resolution.going_mm
            start, end = _perp_line_endpoints(travel_axis, flight2_range, coord)
            msp.add_line(start, end, dxfattribs={"layer": layer})

        lx0, ly0, lx1, ly1 = resolution.landing_bbox
        landing = msp.add_lwpolyline(
            [(lx0, ly0), (lx1, ly0), (lx1, ly1), (lx0, ly1)], dxfattribs={"layer": layer},
        )
        landing.closed = True

        exit_coord = resolution.exit_point[0] if travel_axis == "x" else resolution.exit_point[1]
        div1_start, div1_end = _travel_line(travel_axis, mid_perp, down_c, landing_start)
        div2_start, div2_end = _travel_line(travel_axis, mid_perp, landing_end, exit_coord)
        msp.add_line(div1_start, div1_end, dxfattribs={"layer": layer})
        msp.add_line(div2_start, div2_end, dxfattribs={"layer": layer})

        flight2_perp_mid = (mid_perp + perp_max) / 2.0
        flight2_start = ((landing_end, flight2_perp_mid) if travel_axis == "x"
                          else (flight2_perp_mid, landing_end))
        return flight2_start, resolution.exit_point

    @staticmethod
    def _break_line_perp_span(resolution: StairResolution) -> float:
        """Kesme cizgisi zigzaginin ENINI verir - tek kollu TAM oda
        genisligi (eski davranis), cift kollu yalnizca kol-2 SERIDININ
        genisligi (TAM oda genisligi kullanmak, var OLMAYAN kol-1
        serisinin uzerine tasan yanlis bir cizgi uretirdi)."""
        xmin, ymin, xmax, ymax = resolution.bbox
        full = (ymax - ymin) if resolution.travel_axis == "x" else (xmax - xmin)
        return full / 2.0 if resolution.kind == DOG_LEG else full

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
    def _draw_break_line(msp, travel_axis: str, perp: float, center, layer: str) -> None:
        tick = perp * BREAK_TICK_RATIO
        if travel_axis == "x":
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


def _nearest_bbox_side(point: tuple[float, float],
                        bbox: tuple[float, float, float, float]) -> str:
    """`point`e EN YAKIN oda-sinir kenari ('N'/'S'/'E'/'W'). Duvar
    merkez-cizgisi ile oda poligonu arasindaki yarim-kalinlik farkini
    (bkz. `architect/rules.py::_TOUCH_TOLERANCE_MM` ile AYNI gerekce)
    sabit bir tolerans yerine EN YAKIN kenari secerek GUVENLE asar."""
    x, y = point
    xmin, ymin, xmax, ymax = bbox
    distances = {"W": abs(x - xmin), "E": abs(x - xmax),
                 "S": abs(y - ymin), "N": abs(y - ymax)}
    return min(distances, key=distances.get)


def exit_door_alignment_warning(resolution: StairResolution,
                                 door_point: tuple[float, float]) -> str | None:
    """DEV-047: `stairs[].exit_door_id` ile isaretlenmis bir kapinin,
    merdivenin GERCEKTEN hesapladigi cikis yonunde (`exit_direction`)
    olup olmadigini denetler. `resolve_stair`in hesapladigi deger
    DISINDA ikinci bir geometri turetilMEZ - `door_point` (kapinin duvar
    merkez-cizgisi uzerindeki konumu) CAGIRAN tarafca (`validate.py`,
    `walls::Wall.centerline_point` ile) hesaplanip verilir; bu modul
    `walls/`e bagimli KALMAZ (tek yonlu bagimlilik korunur).

    `exit_direction` bilinmiyorsa (`up_towards` hic verilmediyse) kontrol
    SESSIZCE atlanir - yon zaten uydurulmuyor, bu kapi icin de
    uydurulmaz."""
    if resolution.exit_direction is None:
        return None
    actual_side = _nearest_bbox_side(door_point, resolution.bbox)
    if actual_side == resolution.exit_direction:
        return None
    return (
        f"Merdiven '{resolution.stair_id}': cikis kapisi oda sinirinin "
        f"'{actual_side}' tarafinda, ama merdivenin hesaplanan GERCEK "
        f"cikis yonu '{resolution.exit_direction}' - kapi merdivenin "
        f"cikisina HIZALI degil (bkz. scripts/stairs/CLAUDE.md "
        f"'cikis noktasi/yonu')."
    )


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
# 1.0 -> 1.1 (DEV-046/047): context.json'dan OKUNAN YENI opsiyonel alanlar
# (stairs[].kind/landing_depth_mm/exit_door_id) eklendi - eski alanlarin
# ANLAMI DEGISMEDI (geriye donuk uyumlu, MINOR artis). Bkz. scripts/version.py
CONTRACT_VERSION = "1.1"

__all__ = [
    "STAIR_LAYER",
    "STAIR_RGB",
    "DEFAULT_RISER_MM",
    "DEFAULT_GOING_MM",
    "MIN_GOING_MM",
    "MAX_GOING_MM",
    "DEFAULT_AUTO_FLEX",
    "SINGLE_FLIGHT",
    "DOG_LEG",
    "STAIR_KINDS",
    "DEFAULT_STAIR_KIND",
    "DEFAULT_LANDING_DEPTH_MM",
    "MIN_FLIGHT_WIDTH_MM",
    "StairFitError",
    "StairResolution",
    "resolve_stair",
    "exit_door_alignment_warning",
    "StairDrawingStandard",
    "DefaultStairStandard",
    "ensure_stair_layer",
    "stairs_for_floor",
    "draw_stairs_on_floor",
    "CONTRACT_VERSION",
]
