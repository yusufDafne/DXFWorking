"""Merkezi kat holu + sirkulasyon cekirdegi secenekleri (DEV-055).

**Kullanici karari (2026-10-05):** asansor+merdiven cekirdegi kosede olmak
ZORUNDA DEGIL; bir kat holu ile birlikte kat planinin MERKEZINE (veya
merkezden biraz kaymis) konabilir. Merkezde olursa daireler katin TAMAMINI
cevreleyebilir: hol bir kenara konursa her merdiven-cekirdek yuzu cepheye
bakmaz; merkezdeyse dort cephede de daire penceresi mumkun olur.

Kat holunun en-boy orani etut biriminin KARARIDIR; bu modul endustri/best
practice yaklasimlarindan **bes alternatif** sunar ve puanlar:

  kare            1:1      (genis fuaye; alan en buyuk)
  dikdortgen_3_2  1.5:1
  dikdortgen_2_1  2:1
  koridor_3_1     3:1      (cift yuklu koridor)
  koridor_min     ~en dar  (NET asgari koridor genisligi - STANDARDS['koridor'])

Blok = cekirdek satiri (asansor + merdiven yan yana, `core_depth` derinlik) +
kat holu (dikdortgen, cekirdek satiri ile ayni genislikte). Hol derinligi =
blok genisligi / oran, en az asgari koridor genisligi + duvar kalinligi.

**Bagimlilik yonu (kullanici):** kisit/karar modulleri (`standards`,
`architect`) cizim modullerini BILMEZ; cizim (`templates`) bunlara bagimlidir.
Bu dosya yalniz SAYI hesaplar; geometriyi `templates/central.py` uretir.
"""
from __future__ import annotations

from dataclasses import dataclass

try:
    from ..standards import STANDARDS
except ImportError:
    from standards import STANDARDS

from .rules import DEFAULT_CIRCULATION_SHARE_MAX

# Cekirdek varsayilanlari templates::CirculationCoreTemplate ile AYNI
# (gercek projeden cikarildi); templates bunlari BURADAN degil kendi
# sablonundan okur - degerler elle senkron tutulur, selftest karsilastirir.
DEFAULT_ELEVATOR_WIDTH = 2100.0
DEFAULT_STAIR_WIDTH = 4000.0
DEFAULT_CORE_DEPTH = 3000.0
DEFAULT_WALL_THICKNESS = 200.0
DEFAULT_DOOR_SLOT_PAD_MM = 250.0

HALL_ALTERNATIVES: tuple[tuple[str, str, float | None], ...] = (
    ("kare", "Kare kat holu (1:1)", 1.0),
    ("dikdortgen_3_2", "Dikdortgen kat holu (3:2)", 1.5),
    ("dikdortgen_2_1", "Dikdortgen kat holu (2:1)", 2.0),
    ("koridor_3_1", "Koridor tipi kat holu (3:1)", 3.0),
    ("koridor_min", "Asgari genislikli koridor tipi hol", None),
)
WEIGHT_SURROUND, WEIGHT_SHARE, WEIGHT_FRONTAGE, WEIGHT_CENTER = 0.35, 0.30, 0.20, 0.15
# Kat holunun kat alanina IDEAL payi (agent varsayilani, kucuk/orta kat icin
# makul bir fuaye): bu degerden uzaklastikca puan duser - hem cok buyuk hol
# (kayip alan, %15 siniri) hem cok kucuk hol (sikisik fuaye) cezalidir.
DEFAULT_IDEAL_HALL_SHARE = 0.07


@dataclass(frozen=True)
class CentralHallOption:
    id: str
    label: str
    hall_width: float
    hall_depth: float
    aspect_ratio: float                    # gercek hol en-boy orani (genislik/derinlik)
    hall_area_m2: float
    block: tuple[float, float, float, float]   # (x0, y0, x1, y1) kat yerel koordinati
    margins: dict                          # west/east/south/north: bloktan kat sinirina
    surrounds: bool                        # dort kenarda da daire derinligi kalir mi
    share: float                           # hol alani / kat alani
    frontage_mm: float                     # hol cephesi (daire kapilarina acilabilir)
    feasible: bool
    score: float
    rationale: str
    core_side: str
    orientation: str


def options_for_central_hall(
    floor_width: float, floor_depth: float, *, n_units: int = 3,
    door_width: float = 900.0, wall_thickness: float = DEFAULT_WALL_THICKNESS,
    elevator_width: float = DEFAULT_ELEVATOR_WIDTH, stair_width: float = DEFAULT_STAIR_WIDTH,
    core_depth: float = DEFAULT_CORE_DEPTH, offset: tuple[float, float] = (0.0, 0.0),
    core_side: str = "north", orientation: str = "x",
    min_unit_depth: float | None = None, max_share: float = DEFAULT_CIRCULATION_SHARE_MAX,
    ideal_share: float = DEFAULT_IDEAL_HALL_SHARE,
    allowed: tuple[str, ...] | None = None,
) -> list[CentralHallOption]:
    """Bes (veya `allowed` ile daraltilmis) merkezi hol alternatifi, puana gore
    azalan (once uygulanabilir olanlar). `offset` blogun kat merkezinden
    kaymasi (mm); `core_side` 'north'/'south' = cekirdek satirinin holun hangi
    tarafinda oldugu; `orientation` 'x' = blok uzun ekseni kat genisligi
    boyunca, 'y' = kat derinligi boyunca. Hesaplar, cizmez."""
    if core_side not in ("north", "south"):
        raise ValueError(f"core_side 'north'/'south' olmali, '{core_side}' verildi.")
    if orientation not in ("x", "y"):
        raise ValueError(f"orientation 'x'/'y' olmali, '{orientation}' verildi.")
    known = {a[0] for a in HALL_ALTERNATIVES}
    ids = tuple(a[0] for a in HALL_ALTERNATIVES) if allowed is None else tuple(allowed)
    unknown = [i for i in ids if i not in known]
    if unknown:
        raise ValueError(f"Bilinmeyen kat holu alternatifi: {', '.join(unknown)}. Tanimli: {', '.join(sorted(known))}.")
    if min_unit_depth is None:
        min_unit_depth = STANDARDS["salon"].min_short_edge_mm or 3000.0
    min_net = STANDARDS["koridor"].min_short_edge_mm or 1500.0
    min_gross = min_net + wall_thickness
    fw, fd = (floor_width, floor_depth) if orientation == "x" else (floor_depth, floor_width)
    dx, dy = offset if orientation == "x" else (offset[1], offset[0])
    block_w = elevator_width + stair_width
    floor_area = floor_width * floor_depth
    required_frontage = n_units * (door_width + 2.0 * DEFAULT_DOOR_SLOT_PAD_MM)
    options: list[CentralHallOption] = []
    for opt_id, label, ratio in HALL_ALTERNATIVES:
        if opt_id not in ids:
            continue
        hall_depth = max(min_gross, block_w / ratio) if ratio else min_gross
        block_d = hall_depth + core_depth
        x0 = (fw - block_w) / 2.0 + dx
        y0 = (fd - block_d) / 2.0 + dy
        x1, y1 = x0 + block_w, y0 + block_d
        west, east, south, north = x0, fw - x1, y0, fd - y1
        if orientation == "y":
            block = (y0, x0, y1, x1)
            margins = {"west": south, "east": north, "south": west, "north": east}
        else:
            block = (x0, y0, x1, y1)
            margins = {"west": west, "east": east, "south": south, "north": north}
        feasible = min(margins.values()) >= -1e-6
        smallest = min(margins.values())
        surrounds = feasible and smallest >= min_unit_depth
        area = block_w * hall_depth
        share = area / floor_area if floor_area else 0.0
        frontage = 2.0 * hall_depth + block_w
        s_surround = 1.0 if surrounds else max(0.0, min(1.0, smallest / min_unit_depth))
        s_share = max(0.0, 1.0 - abs(share - ideal_share) / max_share)
        s_front = min(1.0, frontage / required_frontage) if required_frontage else 1.0
        cx, cy = (x0 + x1) / 2.0 - fw / 2.0, (y0 + y1) / 2.0 - fd / 2.0
        shift = (cx * cx + cy * cy) ** 0.5
        s_center = max(0.0, 1.0 - shift / (0.25 * min(fw, fd)))
        score = (WEIGHT_SURROUND * s_surround + WEIGHT_SHARE * s_share
                 + WEIGHT_FRONTAGE * s_front + WEIGHT_CENTER * s_center) if feasible else 0.0
        options.append(CentralHallOption(
            id=opt_id, label=label, hall_width=block_w, hall_depth=hall_depth,
            aspect_ratio=block_w / hall_depth, hall_area_m2=area / 1e6, block=block,
            margins=margins, surrounds=surrounds, share=share, frontage_mm=frontage,
            feasible=feasible, score=round(score, 4),
            rationale=(
                f"hol {block_w:.0f}x{hall_depth:.0f}mm ({block_w / hall_depth:.2f}:1), "
                f"kat payi %{share * 100:.1f} (sinir %{max_share * 100:.0f}); "
                + ("daireler blogu dort kenardan cevreleyebilir "
                   f"(en dar pay {smallest:.0f}mm)." if surrounds else
                   (f"en dar pay {smallest:.0f}mm < {min_unit_depth:.0f}mm: daireler blogu "
                    f"tam cevreleyemez." if feasible else "blok kata SIGMIYOR."))
            ),
            core_side=core_side, orientation=orientation,
        ))
    options.sort(key=lambda o: (not o.feasible, -o.score))
    return options


__all__ = [
    "CentralHallOption", "options_for_central_hall", "HALL_ALTERNATIVES",
    "DEFAULT_IDEAL_HALL_SHARE", "DEFAULT_ELEVATOR_WIDTH", "DEFAULT_STAIR_WIDTH", "DEFAULT_CORE_DEPTH",
]
