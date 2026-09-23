#!/usr/bin/env python3
"""Acilim yonu ve varyant testleri (DEV-016).

Kullanim:
    python scripts/openings/selftest.py
Cikis kodu: 0 basarili, 1 basarisiz.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from openings import (  # noqa: E402
    ARCS_PER_VARIANT,
    DOOR_SYMBOLS,
    DefaultPlanOpeningStyle,
    Opening,
    OpeningSchedule,
    swing_geometry,
)
from walls import Wall, WallCatalog  # noqa: E402

TOLERANCE = 1e-6


def _wall(start, end, thickness: float = 200.0) -> Wall:
    return Wall.from_context(
        {"id": "w", "start": list(start), "end": list(end),
         "thickness": thickness, "layer": "DUVARLAR"},
        WallCatalog())


def _opening(**overrides) -> Opening:
    data = {"id": "k1", "type": "door", "wall_id": "w",
            "position_from_start": 1000.0, "width": 900.0}
    data.update(overrides)
    return Opening.from_context(data)


def _close(a, b) -> bool:
    return abs(a - b) <= 1e-6


class FakeMsp:
    """ezdxf gerektirmeyen sayac: hangi varyant neyi ciziyor."""

    def __init__(self):
        self.lines: list[tuple] = []
        self.arcs: list[dict] = []

    def add_line(self, p1, p2, dxfattribs=None):
        self.lines.append((tuple(p1), tuple(p2)))

    def add_arc(self, center, radius, start_angle, end_angle, dxfattribs=None):
        self.arcs.append({"center": tuple(center), "radius": radius,
                          "start": start_angle, "end": end_angle})


def check_defaults() -> list[str]:
    """Varsayilanlar rev-12 davranisini BIREBIR korumali."""
    errors: list[str] = []
    opening = _opening()
    if (opening.variant, opening.swing, opening.host_side) != ("single", "left", "pos"):
        errors.append(f"Varsayilanlar ('single','left','pos') olmali, "
                      f"{(opening.variant, opening.swing, opening.host_side)} cikti.")

    # +X yonlu duvar: mentese g_start'ta, yay 0 -> 90 derece
    wall = _wall((0, 0), (6000, 0))
    swing = swing_geometry(wall, opening, 1000.0, 1900.0)
    if not (_close(swing.hinge[0], 1000.0) and _close(swing.hinge[1], 0.0)):
        errors.append(f"Mentese (1000,0) olmali, {swing.hinge} cikti.")
    if not _close(swing.radius, 900.0):
        errors.append(f"Yay yaricapi 900 olmali, {swing.radius} cikti.")
    if not (_close(swing.start_angle, 0.0) and _close(swing.end_angle, 90.0)):
        errors.append(f"Yay 0->90 olmali, {swing.start_angle}->{swing.end_angle} cikti.")
    return errors


def check_sweep_always_90() -> list[str]:
    """GIZLI HATA TESTI: yay her zaman 90 derece olmali.

    Onceki surum acilari `min(along, perp)` .. `max(along, perp)` veriyordu;
    duvar -X yonunde cizilmisse (`along=180`, `perp=-90`) bu 270 DERECELIK bir
    yay uretirdi. Mevcut projede her duvar +X/+Y yonundeydi, bu yuzden hata
    hic gorunmedi - bir duvarin ucu ters verildigi anda ortaya cikacakti.
    """
    errors: list[str] = []
    walls = {
        "+X": _wall((0, 0), (6000, 0)),
        "-X": _wall((6000, 0), (0, 0)),
        "+Y": _wall((0, 0), (0, 6000)),
        "-Y": _wall((0, 6000), (0, 0)),
        "egik": _wall((0, 0), (4000, 3000)),
    }
    for name, wall in walls.items():
        for swing_side in ("left", "right"):
            for host_side in ("pos", "neg"):
                opening = _opening(swing=swing_side, host_side=host_side)
                geometry = swing_geometry(wall, opening, 1000.0, 1900.0)
                if abs(geometry.sweep - 90.0) > 1e-6:
                    errors.append(
                        f"{name} duvar / swing={swing_side} / side={host_side}: "
                        f"yay {geometry.sweep:.1f} derece (90 olmaliydi).")
    return errors


def check_swing_sides() -> list[str]:
    """`swing` mentese ucunu, `host_side` acilim tarafini degistirmeli."""
    errors: list[str] = []
    wall = _wall((0, 0), (6000, 0))

    left = swing_geometry(wall, _opening(swing="left"), 1000.0, 1900.0)
    right = swing_geometry(wall, _opening(swing="right"), 1000.0, 1900.0)
    if not _close(left.hinge[0], 1000.0):
        errors.append(f"swing=left mentesesi x=1000 olmali, {left.hinge} cikti.")
    if not _close(right.hinge[0], 1900.0):
        errors.append(f"swing=right mentesesi x=1900 olmali, {right.hinge} cikti.")

    pos = swing_geometry(wall, _opening(host_side="pos"), 1000.0, 1900.0)
    neg = swing_geometry(wall, _opening(host_side="neg"), 1000.0, 1900.0)
    if pos.open_end[1] <= 0 or neg.open_end[1] >= 0:
        errors.append(
            f"host_side kanadi ters tarafa aciyor: pos={pos.open_end}, "
            f"neg={neg.open_end}")
    return errors


def check_validation() -> list[str]:
    """NEGATIF testler: gecersiz varyant/yon uretimi DURDURMALI."""
    errors: list[str] = []
    cases = {
        "varyant": {"variant": "revolving"},
        "swing": {"swing": "up"},
        "host_side": {"host_side": "kuzey"},
    }
    for name, override in cases.items():
        try:
            _opening(**override)
        except ValueError:
            continue
        errors.append(f"YAKALANMADI: gecersiz {name} degeri kabul edildi.")

    # Bilinmeyen varyant icin sembol sozlugu de patlamali
    style = DefaultPlanOpeningStyle(door_symbols={"single": DOOR_SYMBOLS["single"]})
    try:
        style.draw_opening(FakeMsp(), _wall((0, 0), (6000, 0)), 1000.0, 1900.0,
                           {"id": "k9", "type": "door", "variant": "double"})
    except KeyError:
        pass
    else:
        errors.append("YAKALANMADI: tanimsiz varyant sessizce atlandi.")
    return errors


def check_variants() -> list[str]:
    """Her varyant BEKLENEN sembolu cizmeli.

    Soye (jamb) cizgileri her varyantta 2 tanedir; uzerine varyanta ozgu
    geometri gelir."""
    errors: list[str] = []
    style = DefaultPlanOpeningStyle()
    wall = _wall((0, 0), (6000, 0))

    # (varyant, beklenen ek cizgi). Beklenen YAY sayisi tabloya gore
    # dogrulanir: `ARCS_PER_VARIANT` semantik golden kuralinin da kaynagidir,
    # bu yuzden cizicilerin tabloya uydugunu burada KANITLAMAK gerekir.
    cases = [
        ("single", 1),    # kanat + 1 yay
        ("double", 2),    # iki kanat + iki yay
        ("sliding", 2),   # panel + yon isareti, YAY YOK
        ("folding", 2),   # iki kirik kanat, yay yok
    ]
    for variant, extra_lines in cases:
        arcs = ARCS_PER_VARIANT[variant]
        msp = FakeMsp()
        style.draw_opening(msp, wall, 1000.0, 1900.0,
                           _opening(variant=variant).as_dict())
        if len(msp.lines) != 2 + extra_lines:
            errors.append(f"{variant}: {2 + extra_lines} cizgi beklendi, "
                          f"{len(msp.lines)} cizildi.")
        if len(msp.arcs) != arcs:
            errors.append(f"{variant}: {arcs} yay beklendi, "
                          f"{len(msp.arcs)} cizildi.")

    # Pencere: soye + iki paralel cizgi, yay YOK
    msp = FakeMsp()
    style.draw_opening(msp, wall, 1000.0, 1900.0,
                       _opening(type="window").as_dict())
    if len(msp.lines) != 4 or msp.arcs:
        errors.append(f"Pencere 4 cizgi ve 0 yay olmali, "
                      f"{len(msp.lines)} cizgi / {len(msp.arcs)} yay cikti.")
    return errors


def check_gap_convention() -> list[str]:
    """REGRESYON TESTI: `position_from_start` acikligin MERKEZIDIR.

    rev-13'te `openings/collision.py` bunu acikligin BASLANGICI saniyordu ve
    denetlenen sektor, cizilen yaydan yarim genislik (900'luk bir kapida
    450 mm) kayiyordu. Cizim ve denetim artik ikisi de `gaps_for_wall`dan
    okur; bu test o sozlesmeyi sabitler.
    """
    from walls import gaps_for_wall

    errors: list[str] = []
    wall = _wall((0, 0), (6000, 0))
    data = _opening().as_dict()
    gaps = gaps_for_wall(wall, [data])
    if len(gaps) != 1:
        return ["gaps_for_wall tek bosluk dondurmedi."]
    g_start, g_end, _ = gaps[0]
    # merkez 1000, genislik 900 -> 550 .. 1450
    if not (_close(g_start, 550.0) and _close(g_end, 1450.0)):
        errors.append(f"Bosluk araligi (550, 1450) olmali, "
                      f"({g_start}, {g_end}) cikti.")

    swing = swing_geometry(wall, data, g_start, g_end)
    if not _close(swing.hinge[0], 550.0):
        errors.append(f"Mentese x=550 olmali, {swing.hinge[0]} cikti "
                      f"(merkez 1000 ile karistirilmis olabilir).")
    return errors


def check_schedule() -> list[str]:
    """Cetvel varyant ve acilim yonunu tasimali (siparis verisidir)."""
    errors: list[str] = []
    rows = OpeningSchedule.from_openings([
        _opening(id="k2", variant="double", swing="right", host_side="neg"),
    ])
    row = rows[0]
    if (row.get("variant"), row.get("swing"), row.get("host_side")) != \
            ("double", "right", "neg"):
        errors.append(f"Cetvel satiri varyant/yon tasimiyor: {row}")
    return errors


def main() -> int:
    groups = (
        ("varsayilanlar (rev-12 davranisi)", check_defaults()),
        ("yay her zaman 90 derece (gizli hata)", check_sweep_always_90()),
        ("mentese ve acilim tarafi", check_swing_sides()),
        ("gecersiz deger (negatif test)", check_validation()),
        ("varyant sembolleri", check_variants()),
        ("bosluk araligi sozlesmesi (regresyon)", check_gap_convention()),
        ("cetvel", check_schedule()),
    )
    failed = False
    for name, errors in groups:
        if errors:
            failed = True
            print(f"[HATA] {name}:")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"[OK  ] {name}")
    if failed:
        print("\nACIKLIK SELF-TEST BASARISIZ.")
        return 1
    print("\nAciklik self-test BASARILI.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
