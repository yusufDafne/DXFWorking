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

    # rev-25: passage (kapisiz duvar acikligi) = yalniz 2 soye cizgisi; kanat/yay/cam YOK
    msp = FakeMsp()
    style.draw_opening(msp, wall, 1000.0, 1900.0,
                       _opening(type="passage").as_dict())
    if len(msp.lines) != 2 or msp.arcs:
        errors.append(f"passage 2 soye cizgisi ve 0 yay olmali, "
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



def check_double_door_hinges_outside() -> list[str]:
    """DEV-051 (kullanici karari): cift kanatli kapinin mentesesi DISTA
    (aciklik kenarlarinda), kanatlar ortada bulusur."""
    import ezdxf
    from openings import DOOR_SYMBOLS
    errors: list[str] = []
    wall = Wall.from_context({"id": "w", "start": [0, 0], "end": [4000, 0], "thickness": 200, "layer": "D"}, WallCatalog())
    msp = ezdxf.new().modelspace()
    DOOR_SYMBOLS["double"](msp, wall, 1000.0, 2800.0, {"id": "dd", "type": "door", "wall_id": "w",
                                                        "position_from_start": 1900, "width": 1800})
    centers = sorted(round(a.dxf.center.x) for a in msp.query("ARC"))
    if centers != [1000, 2800]:
        errors.append(f"mentese merkezleri aciklik kenarlarinda (1000, 2800) olmali: {centers}")
    return errors


def check_leaf_clearance_along_dev057() -> list[str]:
    """DEV-057: kanat BOYUNCA yakinlik. Guney duvar y=0, kapi x=2050..2950 (merkez 2500, 900),
    swing left -> mentese x=2050, kanat x=2050 dogrusunda y=0..900. Kisa 'stub' duvar x=2100,
    y=400..500 (kalinlik 100): kanat ortasi (y=450) ile mesafe 50 - 50(yarim kalinlik) = 0mm
    (yalniz uc olcen eski kural bunu GORMEZDI: uc (2050,900) stub'a ~403mm)."""
    from openings import check_door_leaf_clearance
    errors: list[str] = []
    walls = [
        {"id": "s", "start": [0, 0], "end": [5000, 0], "thickness": 200, "layer": "D"},
        {"id": "stub", "start": [2100, 400], "end": [2100, 500], "thickness": 100, "layer": "D"},
    ]
    door = {"id": "d", "type": "door", "wall_id": "s", "position_from_start": 2500, "width": 900}
    got = check_door_leaf_clearance(walls, [door])
    if len(got) != 1 or "boyunca" not in got[0]:
        errors.append(f"kanat boyunca stub duvara 0mm: 'boyunca' UYARISI bekleniyordu: {got}")
    far = [walls[0], {**walls[1], "start": [2600, 400], "end": [2600, 500]}]
    if check_door_leaf_clearance(far, [door]):
        errors.append("stub 550mm uzaktayken UYARI olmamali (yanlis-pozitif)")
    return errors


def check_wall_nuances() -> list[str]:
    """DEV-050 madde 1,2,3,5,6,11 - ELLE hesaplanabilir degerlerle."""
    from openings import check_opening_nuances, check_opening_wall_nuances
    errors: list[str] = []
    def walls_rect():
        return [
            {"id": "s", "start": [0, 0], "end": [5000, 0], "thickness": 200, "layer": "D"},
            {"id": "e", "start": [5000, 0], "end": [5000, 4000], "thickness": 200, "layer": "D"},
            {"id": "n", "start": [5000, 4000], "end": [0, 4000], "thickness": 200, "layer": "D"},
            {"id": "w", "start": [0, 4000], "end": [0, 0], "thickness": 200, "layer": "D"},
        ]
    def door(i, pos, width, **kw):
        return {"id": i, "type": "door", "wall_id": "s", "position_from_start": pos, "width": width, **kw}
    # madde 1: duvar basinda 100mm (merkez) - 100 (w duvari yarim kalinligi) = 0 -> UYARI;
    # pos=700,w=900: baslangic 250, w yarim kalinlik 100 -> 150 kati duvar -> UYARI YOK
    if not any("basina" in w for w in check_opening_wall_nuances(walls_rect(), [door("d0", 550, 900)])):
        errors.append("550/900 kapi: 100-100=0mm kati duvar -> UYARI bekleniyordu")
    if any("basina" in w for w in check_opening_wall_nuances(walls_rect(), [door("d1", 700, 900)])):
        errors.append("700/900 kapi: 250-100=150mm -> UYARI OLMAMALI (yanlis-pozitif)")
    # madde 2: 1000-1450 ve 1600-... aralik 150 < 200
    two = [door("a", 1900, 900), door("b", 3050, 900)]  # a: 1450-2350, b: 2600-3500 -> 250 TAM esik (DEV-053: iki kapi)
    if any("arasi" in w for w in check_opening_wall_nuances(walls_rect(), two)):
        errors.append("iki kapi arasi 250mm tam esik UYARI vermemeli")
    two[1]["position_from_start"] = 2900  # 2450-3350: aralik 100 (<250)
    if not any("arasi" in w for w in check_opening_wall_nuances(walls_rect(), two)):
        errors.append("100mm aralik UYARI vermeli")
    # DEV-053: kapi-kapi 200mm artik YETERSIZ (250), ama kapi-pencere 200 yeterli
    dw = [door("a", 1900, 900), {"id": "pw", "type": "window", "wall_id": "s", "position_from_start": 3000, "width": 900}]  # aralik 200
    if any("arasi" in w for w in check_opening_wall_nuances(walls_rect(), dw)):
        errors.append("kapi-pencere 200mm UYARI vermemeli (yalniz iki kapi icin 250)")
    dd = [door("a", 1900, 900), door("b", 3000, 900)]  # aralik 200 (<250)
    if not any("asgari 250mm" in w for w in check_opening_wall_nuances(walls_rect(), dd)):
        errors.append("iki kapi arasi 200mm artik UYARI vermeli (asgari 250)")
    # madde 3: pencere dis koseye (0,0) yakin: pos=800,w=900 -> 350-100=250 < 350
    win = [{"id": "w1", "type": "window", "wall_id": "s", "position_from_start": 800, "width": 900}]
    if not any("dis kosenin" in w for w in check_opening_wall_nuances(walls_rect(), win)):
        errors.append("kosede pencere UYARI vermeli")
    win[0]["position_from_start"] = 1100  # 650-100=550
    if any("dis kosenin" in w for w in check_opening_wall_nuances(walls_rect(), win)):
        errors.append("kosedeki 550mm pencere UYARI vermemeli")
    # madde 5: cift kanat 900 genislik -> kanat 450 < 600; kenar payi 150
    dbl = [door("dd", 1500, 900, variant="double")]
    if not any("Cift kanatli" in w for w in check_opening_wall_nuances(walls_rect(), dbl)):
        errors.append("450mm kanat UYARI vermeli")
    dbl = [door("dd", 1500, 1200, variant="double")]
    if any("Cift kanatli" in w for w in check_opening_wall_nuances(walls_rect(), dbl)):
        errors.append("2x600 cift kanat UYARI vermemeli")
    # madde 6: surme kapi 1500 genislik 4000 uzunluk duvarda ortada: iki yanda ~1100 < 1500 -> UYARI
    from openings import check_sliding_door_parking
    slide = [{"id": "sl", "type": "door", "wall_id": "w", "position_from_start": 2000, "width": 1500, "variant": "sliding"}]
    if not any("duvar disina" in w for w in check_sliding_door_parking(walls_rect(), slide)):
        errors.append("kayacak yuzey yetersiz surme kapi UYARI vermeli")
    slide[0]["width"] = 900
    if check_sliding_door_parking(walls_rect(), slide):
        errors.append("yeterli yuzeyli surme kapi UYARI vermemeli")
    # DEV-051: baska aciklik alani + baska kapinin acilim sektoru (iki yan da bloke)
    def big():
        return [
            {"id": "s", "start": [0, 0], "end": [8000, 0], "thickness": 200, "layer": "D"},
            {"id": "e", "start": [8000, 0], "end": [8000, 4000], "thickness": 200, "layer": "D"},
            {"id": "n", "start": [8000, 4000], "end": [0, 4000], "thickness": 200, "layer": "D"},
            {"id": "w", "start": [0, 4000], "end": [0, 0], "thickness": 200, "layer": "D"},
        ]
    sl = {"id": "sl", "type": "door", "wall_id": "s", "position_from_start": 6200, "width": 900, "variant": "sliding"}
    left_block = {"id": "lb", "type": "door", "wall_id": "s", "position_from_start": 5000, "width": 900}
    side_door = {"id": "sd", "type": "door", "wall_id": "e", "position_from_start": 500, "width": 900}
    got = check_sliding_door_parking(big(), [sl, left_block, side_door])
    if not got or "aciklik alanina" not in got[0] or "acilim alanina" not in got[0]:
        errors.append(f"iki yan bloke (aciklik + sektor) UYARI vermeli: {got}")
    if check_sliding_door_parking(big(), [sl, left_block]):
        errors.append("bir yan serbestken (sektor yok) UYARI OLMAMALI (yanlis-pozitif)")
    # madde 11: kanat ucu karsi duvara yakin. 5000x4000 oda, kuzey duvari y=4000;
    # guney duvardaki kapi kanadi +Y'ye ac: 900'luk kanat ucu y=900 -> uzak, UYARI YOK;
    # oda 1000 derinlikte olsa ucu karsi duvar yuzune (1000-100=900) degecek
    if check_opening_nuances(walls_rect(), [door("far", 2500, 900)]) != []:
        errors.append("karsi duvar uzaktayken UYARI olmamali")
    shallow = walls_rect()
    shallow[1]["end"] = [5000, 1000]; shallow[2]["start"] = [5000, 1000]
    shallow[2]["end"] = [0, 1000]; shallow[3]["start"] = [0, 1000]
    got = [w for w in check_opening_nuances(shallow, [door("near", 2500, 900)]) if "kanat ucu" in w]
    if not got:
        errors.append("1000mm derinlikte 900mm kanat ucu karsi duvara dayanmali (UYARI)")
    return errors


def check_elevator_doors_dev055() -> list[str]:
    """DEV-055: asansor kapisi (3 tur, varsayilan surme, kuyudan 250mm daraltilmis)."""
    import ezdxf
    from openings import (DOOR_SYMBOLS, ELEVATOR_DEFAULT_VARIANT, Opening,
                          check_elevator_door_insets, elevator_door_width)
    errors: list[str] = []
    if ELEVATOR_DEFAULT_VARIANT != "sliding":
        errors.append("asansor kapisi varsayilani surme olmali")
    if Opening.from_context({"id": "e", "type": "elevator_door", "wall_id": "w",
                             "position_from_start": 1000, "width": 1600}).variant != "sliding":
        errors.append("varyanti verilmeyen asansor kapisi 'sliding' olmali")
    for v in ("single", "sliding", "sliding_double"):
        Opening.from_context({"id": "e", "type": "elevator_door", "wall_id": "w",
                              "position_from_start": 1000, "width": 1600, "variant": v})
    try:
        Opening.from_context({"id": "e", "type": "elevator_door", "wall_id": "w",
                              "position_from_start": 1000, "width": 1600, "variant": "folding"})
        errors.append("asansor kapisi icin 'folding' reddedilmeli")
    except ValueError:
        pass
    if elevator_door_width(2100.0) != 1600.0 or elevator_door_width(2100.0, 200.0) != 1700.0:
        errors.append("kuyu 2100 -> kapi 1600 (250 pay), 1700 (200 pay) olmali")
    # ikili surme: iki panel + iki isaret = 4 LINE, yay yok; aciklik kenarlari 1000..2800
    wall = Wall.from_context({"id": "w", "start": [0, 0], "end": [4000, 0], "thickness": 200, "layer": "D"}, WallCatalog())
    msp = ezdxf.new().modelspace()
    DOOR_SYMBOLS["sliding_double"](msp, wall, 1000.0, 2800.0, {"id": "e", "type": "elevator_door"})
    if len(msp.query("LINE")) != 4 or len(msp.query("ARC")) != 0:
        errors.append(f"ikili surme 4 LINE / 0 ARC cizmeli: {len(msp.query('LINE'))}/{len(msp.query('ARC'))}")
    # kuyu paylari: kuyu x 0..2100 (asansor odasi), kapi 1600 ortada -> 250/250 TEMIZ; 1900 genis -> 100 UYARI
    well = {"id": "a", "room_type": "asansor", "polygon": [[0, 0], [2100, 0], [2100, 3000], [0, 3000]]}
    walls = [{"id": "w", "start": [0, 0], "end": [4000, 0], "thickness": 200, "layer": "D"}]
    ok = {"id": "e", "type": "elevator_door", "wall_id": "w", "position_from_start": 1050, "width": 1600}
    if check_elevator_door_insets([well], walls, [ok]):
        errors.append("250/250 pay UYARI vermemeli (yanlis-pozitif)")
    wide = {**ok, "width": 1900}
    if len(check_elevator_door_insets([well], walls, [wide])) != 2:
        errors.append("100/100 pay: iki kenar icin UYARI bekleniyordu")
    return errors


def main() -> int:
    groups = (
        ("asansor kapisi: 3 tur, varsayilan surme, 250mm pay (DEV-055)", check_elevator_doors_dev055()),
        ("kanat boyunca duvar yakinligi (DEV-057 Grup A)", check_leaf_clearance_along_dev057()),
        ("cift kanat mentese DISTA (DEV-051)", check_double_door_hinges_outside()),
        ("aciklik duvar nuanslari (DEV-050 #1,2,3,5,6,11)", check_wall_nuances()),
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
