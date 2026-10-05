#!/usr/bin/env python3
"""Sartname + oransal mahal kural kutuphanesi testleri (DEV-036).

Kullanim:
    python scripts/standards/selftest.py
Cikis kodu: 0 basarili, 1 basarisiz.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from standards import (  # noqa: E402
    RoomStandard,
    STANDARDS,
    check_room_proportions,
    check_room_types,
    edge_wall_thicknesses,
    narrowest_point,
    room_aspect_ratio,
    validate_standards,
)

# 4000 x 2000 dikdortgen -> kisa kenar 2000, uzun kenar 4000 -> oran 2.0.
RECT_4000x2000 = [[0, 0], [4000, 0], [4000, 2000], [0, 2000]]
# 1400 x 1400 kare -> oran 1.0.
SQUARE_1400 = [[0, 0], [1400, 0], [1400, 1400], [0, 1400]]
# asansor sinirlari: min_ratio=1.0, max_ratio=1.5, min_short_edge_mm=1400.
# 2800 x 1400 -> kisa kenar TAM 1400 (siniri IHLAL ETMEZ), oran 2.0 (max 1.5'i
# ASAR) -> SADECE oran ihlali.
RATIO_ONLY_VIOLATION = [[0, 0], [2800, 0], [2800, 1400], [0, 1400]]
# 1400 x 1000 -> oran 1.4 (araligin ICINDE), kisa kenar 1000mm (asgari
# 1400mm'nin ALTINDA) -> SADECE kisa kenar ihlali.
SHORT_EDGE_ONLY_VIOLATION = [[0, 0], [1400, 0], [1400, 1000], [0, 1000]]


def check_room_aspect_ratio_hand_computable() -> list[str]:
    errors: list[str] = []
    ratio = room_aspect_ratio(RECT_4000x2000)
    if abs(ratio - 2.0) > 1e-9:
        errors.append(f"4000x2000 icin oran 2.0 bekleniyordu, {ratio} bulundu")
    square_ratio = room_aspect_ratio(SQUARE_1400)
    if abs(square_ratio - 1.0) > 1e-9:
        errors.append(f"1400x1400 icin oran 1.0 bekleniyordu, {square_ratio} bulundu")
    degenerate = room_aspect_ratio([[0, 0], [0, 0], [0, 0]])
    if degenerate != float("inf"):
        errors.append(f"kisa kenar 0 icin inf bekleniyordu, {degenerate} bulundu")
    return errors


def check_room_types_catches_typo_and_skips_missing() -> list[str]:
    errors: list[str] = []
    rooms = [
        {"id": "r1", "room_type": "asansor"},   # gecerli, hata YOK
        {"id": "r2"},                            # alan hic YOK, hata YOK (opt-in)
        {"id": "r3", "room_type": "aasansor"},  # yazim hatasi, HATA bekleniyor
    ]
    found = check_room_types(rooms)
    if len(found) != 1:
        errors.append(f"tam 1 hata bekleniyordu (r3), {len(found)} bulundu: {found}")
    elif "r3" not in found[0] or "aasansor" not in found[0]:
        errors.append(f"hata mesaji 'r3'/'aasansor' icermiyor: {found[0]!r}")
    return errors


def check_room_proportions_ratio_violation() -> list[str]:
    """RATIO_ONLY_VIOLATION: kisa kenar TAM sinirda (1400mm, ihlal YOK),
    oran 2.0 (max 1.5'i ASAR) -> TAM 1 uyari (yalnizca oran) beklenir."""
    errors: list[str] = []
    rooms = [{"id": "r1", "room_type": "asansor", "polygon": RATIO_ONLY_VIOLATION,
              "area_m2": 3.92}]
    warnings = check_room_proportions(rooms, "mm")
    if len(warnings) != 1:
        return [f"tam 1 uyari bekleniyordu (oran ihlali), {len(warnings)} bulundu: {warnings}"]
    if "en-boy orani" not in warnings[0] or "r1" not in warnings[0]:
        errors.append(f"beklenmedik uyari metni: {warnings[0]!r}")
    return errors


def check_room_proportions_short_edge_violation() -> list[str]:
    """SHORT_EDGE_ONLY_VIOLATION: oran 1.4 (araligin [1.0,1.5] ICINDE, ihlal
    YOK), kisa kenar 1000mm (asgari 1400mm'nin ALTINDA) -> TAM 1 uyari
    (yalnizca kisa kenar) beklenir."""
    rooms = [{"id": "r1", "room_type": "asansor", "polygon": SHORT_EDGE_ONLY_VIOLATION,
              "area_m2": 1.4}]
    warnings = check_room_proportions(rooms, "mm")
    if len(warnings) != 1:
        return [f"tam 1 uyari bekleniyordu (kisa kenar ihlali), {len(warnings)} bulundu: {warnings}"]
    if "kisa kenar" not in warnings[0]:
        return [f"kisa kenar uyarisi bekleniyordu: {warnings}"]
    return []


def check_room_proportions_within_limits_no_false_positive() -> list[str]:
    """1400x1400 kare, asansor sinirlarinin (oran [1.0,1.5], kisa kenar
    >=1400mm) TAM ICINDE - HICBIR uyari UretmeMELI (yanlis-pozitif testi)."""
    rooms = [{"id": "r1", "room_type": "asansor", "polygon": SQUARE_1400,
              "area_m2": 1.96}]
    warnings = check_room_proportions(rooms, "mm")
    if warnings:
        return [f"uyari beklenmiyordu, {len(warnings)} bulundu: {warnings}"]
    return []


def check_room_proportions_skips_untyped_and_meters() -> list[str]:
    """room_type verilmeyen oda kontrole HIC GIRMEZ. 'm' biriminde de
    kisa-kenar mm'ye DOGRU cevriliyor mu (1.0m -> 1000mm, asgarinin
    ALTINDA -> UYARI beklenir; 1.4m -> 1400mm, sinirda -> UYARI YOK)."""
    errors: list[str] = []
    untyped = [{"id": "r1", "polygon": SHORT_EDGE_ONLY_VIOLATION, "area_m2": 1.4}]
    if check_room_proportions(untyped, "mm"):
        errors.append("room_type verilmeyen oda icin uyari beklenmiyordu")

    meters_narrow = [{"id": "r2", "room_type": "asansor",
                       "polygon": [[0, 0], [1.0, 0], [1.0, 3.5], [0, 3.5]],
                       "area_m2": 3.5}]
    warnings = check_room_proportions(meters_narrow, "m")
    if not any("kisa kenar" in w for w in warnings):
        errors.append(f"'m' biriminde kisa kenar mm'ye cevrilip UYARI vermeliydi: {warnings}")
    return errors


def check_room_proportions_area_violation() -> list[str]:
    """min_area_m2 gercek katalogda HICBIR girişte kullanilmiyor - bu yuzden
    GECICI bir test standardi eklenip (try/finally ile geri alinip) alan
    kontrolunun CALISTIGI dogrudan sinanir."""
    errors: list[str] = []
    key = "__selftest_area__"
    STANDARDS[key] = RoomStandard(
        key, "Test odasi", min_ratio=1.0, max_ratio=10.0, min_area_m2=5.0,
        source="selftest gecici girdi")
    try:
        rooms = [{"id": "r1", "room_type": key, "polygon": SQUARE_1400, "area_m2": 1.96}]
        warnings = check_room_proportions(rooms, "mm")
        if not any("alan" in w for w in warnings):
            errors.append(f"alan ihlali icin UYARI bekleniyordu: {warnings}")
    finally:
        del STANDARDS[key]
    return errors


# L-sekilli hol: yatay kol 7700x900 (y 6950-7850), dusey bacak 1500 genislikli
# (x 1700-3200, y 7850-13000). AABB kisa kenari 6050 (cok genis gorunur) ama
# yatay kol 900mm -> yerel en dar nokta 900 (ELLE: 7850-6950).
L_HOL_900 = [[0, 6950], [7700, 6950], [7700, 7850], [3200, 7850],
             [3200, 13000], [1700, 13000], [1700, 7850], [0, 7850]]
# Ayni L ama her kol 1500 -> esigi TAM karsilar (yanlis-pozitif testi).
L_HOL_1500 = [[0, 0], [6000, 0], [6000, 1500], [1500, 1500], [1500, 6000],
              [0, 6000]]


def check_narrowest_point_hand_computable() -> list[str]:
    errors: list[str] = []
    rect = narrowest_point(RECT_4000x2000)
    if rect is None or abs(rect.width - 2000) > 1e-6:
        errors.append(f"4000x2000 dikdortgen icin 2000 bekleniyordu: {rect}")
    l_shape = narrowest_point(L_HOL_900)
    if l_shape is None or abs(l_shape.width - 900) > 1e-6:
        errors.append(f"L-hol icin 900 bekleniyordu: {l_shape}")
    l_ok = narrowest_point(L_HOL_1500)
    if l_ok is None or abs(l_ok.width - 1500) > 1e-6:
        errors.append(f"1500 kollu L icin 1500 bekleniyordu: {l_ok}")
    if narrowest_point([[0, 0], [1, 1]]) is not None:
        errors.append("<3 koseli poligon icin None bekleniyordu")
    return errors


def check_local_narrow_point_warning() -> list[str]:
    """DEV-049: AABB'nin KACIRDIGI daralma yerel olcumle yakalanir; esigi
    tam karsilayan L ve AABB zaten ihlalken ikinci uyari URETILMEZ."""
    errors: list[str] = []
    bad = [{"id": "h1", "room_type": "koridor", "polygon": L_HOL_900, "area_m2": 14.65}]
    warnings = check_room_proportions(bad, "mm")
    if not any("yerel en dar nokta 900mm" in w for w in warnings):
        errors.append(f"900mm daralma icin yerel UYARI bekleniyordu: {warnings}")
    ok = [{"id": "h2", "room_type": "koridor", "polygon": L_HOL_1500, "area_m2": 15.0}]
    if check_room_proportions(ok, "mm"):
        errors.append("1500mm kollu L icin UYARI olmamaliydi (yanlis-pozitif)")
    thin = [{"id": "h3", "room_type": "koridor", "polygon": [[0, 0], [5000, 0], [5000, 250], [0, 250]], "area_m2": 1.25}]
    warnings = check_room_proportions(thin, "mm")
    if any("yerel" in w for w in warnings) or not any("kisa kenar" in w for w in warnings):
        errors.append(f"250mm dikdortgen: yalniz kisa kenar uyarisi (yerel ikinci kez DEGIL) bekleniyordu: {warnings}")
    if STANDARDS["koridor"].min_short_edge_mm != 1500.0:
        errors.append("koridor min_short_edge_mm 1500 olmali (DEV-049)")
    return errors


def check_net_clear_width_between_wall_faces() -> list[str]:
    """DEV-049 (kullanici: 'mimari standartta oda/koridor aciklari duvar ic
    kenarlariyla olculur'): K1-31/K1-33 arasindaki gercek vaka. Merkez
    cizgileri 350mm arayla, iki duvar 100mm -> net 350-50-50 = 250 (ELLE)."""
    errors: list[str] = []
    hol = [[0, 0], [4600, 0], [4600, 350], [0, 350]]
    walls = [
        {"id": "w1", "start": [0, 0], "end": [4600, 0], "thickness": 100.0},
        {"id": "w2", "start": [0, 350], "end": [4600, 350], "thickness": 100.0},
    ]
    t = edge_wall_thicknesses(hol, walls)
    if t != [100.0, 0.0, 100.0, 0.0]:
        errors.append(f"kenar kalinliklari [100,0,100,0] bekleniyordu: {t}")
    n = narrowest_point(hol, t)
    if n is None or abs(n.width - 250) > 1e-6 or abs(n.gross - 350) > 1e-6:
        errors.append(f"net 250 / brut 350 bekleniyordu: {n}")
    rooms = [{"id": "h", "room_type": "koridor", "polygon": hol, "area_m2": 1.6}]
    if not any("250mm" in w and "net" in w for w in check_room_proportions(rooms, "mm", walls)):
        errors.append("net 250mm icin UYARI bekleniyordu")
    # yanlis-pozitif: 1600 merkez, 100mm duvarlar -> net 1500 TAM esik, uyari YOK
    ok = [[0, 0], [4600, 0], [4600, 1600], [0, 1600]]
    okw = [{"id": "a", "start": [0, 0], "end": [4600, 0], "thickness": 100.0},
           {"id": "b", "start": [0, 1600], "end": [4600, 1600], "thickness": 100.0}]
    if check_room_proportions([{"id": "o", "room_type": "koridor", "polygon": ok, "area_m2": 7}], "mm", okw):
        errors.append("net 1500mm (esik) icin UYARI olmamaliydi")
    # kasitli bozma: duvarlar verilmezse ayni 350 poligon BRUT 350 raporlanir
    if any("250mm" in w for w in check_room_proportions(rooms, "mm")):
        errors.append("walls verilmeden net 250 uretilmemeli (eski davranis)")
    return errors


def check_open_door_net_passage_dev051() -> list[str]:
    """DEV-051: koridora acilan kapida KALAN gecis. ELLE: 1500 koridor, 800
    kanat -> 700 kalir (<800 UYARI); 1700 koridor, 800 kanat -> 900 (temiz)."""
    from standards import check_door_corridor_nuances
    errors: list[str] = []
    def case(depth):
        hol = {"id": "hol", "room_type": "koridor", "polygon": [[0, 0], [5000, 0], [5000, depth], [0, depth]]}
        walls = [{"id": "w", "start": [0, 0], "end": [5000, 0], "thickness": 0.0, "layer": "D"}]
        door = {"id": "d", "type": "door", "wall_id": "w", "position_from_start": 2500, "width": 800, "host_side": "pos"}
        return check_door_corridor_nuances([hol], walls, [door])
    if not any("kalan gecis 700mm" in w for w in case(1500)):
        errors.append("1500 koridor/800 kanat -> 700mm kalan gecis UYARISI bekleniyordu")
    if any("kalan gecis" in w for w in case(1700)):
        errors.append("1700 koridor/800 kanat -> 900mm: UYARI olmamali (yanlis-pozitif)")
    # kapi koridorun TERS yuzune aciliyorsa (host_side neg) koridora donmez
    hol = {"id": "hol", "room_type": "koridor", "polygon": [[0, 0], [5000, 0], [5000, 1500], [0, 1500]]}
    walls = [{"id": "w", "start": [0, 0], "end": [5000, 0], "thickness": 0.0, "layer": "D"}]
    door = {"id": "d", "type": "door", "wall_id": "w", "position_from_start": 2500, "width": 800, "host_side": "neg"}
    if any("kalan gecis" in w for w in check_door_corridor_nuances([hol], walls, [door])):
        errors.append("kapi koridordan DISARI aciliyorsa kalan gecis UYARISI olmamali")
    return errors


def check_net_ratio_area_and_dead_end_dev057() -> list[str]:
    """DEV-057 Grup A: oran + alan NET; cikmaz kol gercek uc geometrisi."""
    from standards import check_door_corridor_nuances
    errors: list[str] = []
    room = [[0, 0], [4000, 0], [4000, 2000], [0, 2000]]
    walls = [
        {"id": "s", "start": [0, 0], "end": [4000, 0], "thickness": 100.0, "layer": "D"},
        {"id": "e", "start": [4000, 0], "end": [4000, 2000], "thickness": 100.0, "layer": "D"},
        {"id": "n", "start": [4000, 2000], "end": [0, 2000], "thickness": 100.0, "layer": "D"},
        {"id": "w", "start": [0, 2000], "end": [0, 0], "thickness": 100.0, "layer": "D"},
    ]
    # yatak odasi max_ratio 2.0: BRUT 4000/2000 = 2.0 (temiz), NET 3900/1900 = 2.0526 (> 2.0)
    r = [{"id": "r", "room_type": "yatak_odasi", "polygon": room, "area_m2": 8.0}]
    gross = [w for w in check_room_proportions(r, "mm") if "en-boy" in w]
    net = [w for w in check_room_proportions(r, "mm", walls) if "en-boy" in w]
    if gross:
        errors.append(f"duvarsiz (brut) 2.0 orani UYARI vermemeli: {gross}")
    if len(net) != 1 or "(net) 2.05" not in net[0]:
        errors.append(f"net oran 2.05 icin UYARI bekleniyordu: {net}")
    # alan: gecici standart min 7.5 m2; brut 8.0 temiz, NET 3900*1900 = 7.41 m2 uyari
    key = "__selftest_net_area__"
    STANDARDS[key] = RoomStandard(key, "Test", min_ratio=1.0, max_ratio=10.0, min_area_m2=7.5, source="selftest gecici")
    try:
        t = [{"id": "t", "room_type": key, "polygon": room, "area_m2": 8.0}]
        if check_room_proportions(t, "mm"):
            errors.append("brut 8.0 m2 >= 7.5: UYARI olmamali")
        got = [w for w in check_room_proportions(t, "mm", walls) if "alan" in w]
        if len(got) != 1 or "7.4 m2" not in got[0] or "(net)" not in got[0]:
            errors.append(f"net alan 7.4 m2 < 7.5 icin UYARI bekleniyordu: {got}")
    finally:
        del STANDARDS[key]
    # cikmaz uc: dusey koridor 0..W x 0..5000, kapi yalniz UZUN kenarda (y=500); iki kisa uc de kapali
    def corridor(width):
        poly = [[0, 0], [width, 0], [width, 5000], [0, 5000]]
        ws = [{"id": "L", "start": [0, 0], "end": [0, 5000], "thickness": 0.0, "layer": "D"},
              {"id": "B", "start": [0, 0], "end": [width, 0], "thickness": 0.0, "layer": "D"},
              {"id": "T", "start": [0, 5000], "end": [width, 5000], "thickness": 0.0, "layer": "D"}]
        return [{"id": "h", "room_type": "koridor", "polygon": poly}], ws
    rooms, ws = corridor(800.0)
    door_side = {"id": "d", "type": "door", "wall_id": "L", "position_from_start": 500, "width": 700}
    got = [w for w in check_door_corridor_nuances(rooms, ws, [door_side]) if "cikmaz" in w]
    if len(got) != 1:
        errors.append(f"800mm cikmaz kol icin TEK uyari bekleniyordu: {got}")
    rooms, ws = corridor(1000.0)
    if [w for w in check_door_corridor_nuances(rooms, ws, [door_side]) if "cikmaz" in w]:
        errors.append("1000mm cikmaz kol >= 900: UYARI olmamali (yanlis-pozitif)")
    # iki kisa uca da kapi -> gecis koridoru, 800mm bile cikmaz DEGIL
    rooms, ws = corridor(800.0)
    ends = [{"id": "d1", "type": "door", "wall_id": "B", "position_from_start": 400, "width": 700},
            {"id": "d2", "type": "door", "wall_id": "T", "position_from_start": 400, "width": 700}]
    if [w for w in check_door_corridor_nuances(rooms, ws, ends) if "cikmaz" in w]:
        errors.append("her iki ucu kapili gecis koridoru cikmaz SAYILMAMALI")
    # L bukeyi cikmaz degildir: L = dusey kol (0..800 x 0..5000) + yatay kol (800..3000 x 4200..5000),
    # kapi yalniz yatay kolun sag ucunda ve dusey kolun alt ucunda -> hicbir uc cikmaz degil
    L = [[0, 0], [800, 0], [800, 4200], [3000, 4200], [3000, 5000], [0, 5000]]
    lw = [{"id": "x", "start": [0, 0], "end": [800, 0], "thickness": 0.0, "layer": "D"},
          {"id": "y", "start": [3000, 4200], "end": [3000, 5000], "thickness": 0.0, "layer": "D"}]
    ld = [{"id": "da", "type": "door", "wall_id": "x", "position_from_start": 400, "width": 700},
          {"id": "db", "type": "door", "wall_id": "y", "position_from_start": 400, "width": 700}]
    if [w for w in check_door_corridor_nuances([{"id": "l", "room_type": "koridor", "polygon": L}], lw, ld) if "cikmaz" in w]:
        errors.append("L bukeyi ve kapili uclar cikmaz SAYILMAMALI")
    return errors


def check_validate_standards_catches_broken_catalog() -> list[str]:
    """Gercek katalog TEMIZ donmeli (yanlis-pozitif testi); GECICI olarak
    bozuk bir girdi (max_ratio < min_ratio) eklenince validate_standards
    bunu YAKALAMALI (kasitli bozma testi, try/finally ile geri alinir)."""
    errors: list[str] = []
    clean = validate_standards()
    if clean:
        return [f"gercek katalog TEMIZ donmeliydi, {len(clean)} hata bulundu: {clean}"]

    key = "__selftest_broken__"
    STANDARDS[key] = RoomStandard(
        key, "Bozuk test", min_ratio=2.0, max_ratio=1.0, source="")
    try:
        broken = validate_standards()
        if not broken:
            errors.append("max_ratio < min_ratio + bos source YAKALANMALIYDI")
        elif len(broken) < 2:
            errors.append(f"EN AZ 2 hata bekleniyordu (oran + bos source), {len(broken)} bulundu: {broken}")
    finally:
        del STANDARDS[key]
    return errors



def check_net_area_and_nuances() -> list[str]:
    """DEV-050: net alan (duvar IC yuzleri arasi) + kapi/koridor nuanslari."""
    from standards import check_door_corridor_nuances
    from standards.measure import arm_widths, net_area
    errors: list[str] = []
    rect = [[0, 0], [4000, 0], [4000, 3000], [0, 3000]]
    # ELLE: (4000-100)*(3000-100) = 11 310 000 mm2 = 11.31 m2
    if abs(net_area(rect, [100.0] * 4) - 11_310_000.0) > 1e-3:
        errors.append("100mm duvarli 4000x3000 net alan 11.31 m2 olmali")
    if abs(net_area(rect, [0.0] * 4) - 12_000_000.0) > 1e-3:
        errors.append("duvarsiz net alan = brut alan olmali")
    # L-hol kollari: 900 ve 1500 (duvarsiz) -> [900, 1500]
    if sorted(round(w) for w in arm_widths(L_HOL_900)) != [900, 1500]:
        errors.append(f"L-hol kol genislikleri [900,1500] olmali: {arm_widths(L_HOL_900)}")

    def wall(i, s, e, t=100.0):
        return {"id": i, "start": s, "end": e, "thickness": t, "layer": "D"}
    # madde 7: 3000x3000 WC, kapi 600 genis (asgari 700)
    wc = {"id": "wc", "room_type": "wc", "unit_id": "A",
          "polygon": [[0, 0], [3000, 0], [3000, 3000], [0, 3000]]}
    walls = [wall("w", [0, 0], [3000, 0])]
    door = {"id": "d", "type": "door", "wall_id": "w", "position_from_start": 1500, "width": 600}
    if not any("asgari 700" in w for w in check_door_corridor_nuances([wc], walls, [door])):
        errors.append("600mm WC kapisi UYARI vermeli")
    door["width"] = 700
    if any("asgari 700" in w for w in check_door_corridor_nuances([wc], walls, [door])):
        errors.append("700mm WC kapisi UYARI vermemeli (yanlis-pozitif)")
    # madde 8: koridor 1000 genis, kapi 900 + 100 pay = 1000 -> TAM esik, UYARI yok; 950 -> UYARI
    hol = {"id": "hol", "room_type": "koridor", "polygon": [[0, 0], [5000, 0], [5000, 1000], [0, 1000]]}
    hw = [wall("hw", [0, 0], [5000, 0], 0.0), wall("hn", [0, 1000], [5000, 1000], 0.0)]
    d9 = {"id": "d9", "type": "door", "wall_id": "hw", "position_from_start": 2500, "width": 900}
    if any("kapisinin onunde" in w for w in check_door_corridor_nuances([hol], hw, [d9, {**d9, "id": "x", "wall_id": "hn"}])):
        errors.append("1000mm koridor, 900mm kanat+100 pay TAM esik: UYARI olmamali")
    hol["polygon"] = [[0, 0], [5000, 0], [5000, 950], [0, 950]]
    hw[1] = wall("hn", [0, 950], [5000, 950], 0.0)
    if not any("kapisinin onunde" in w for w in check_door_corridor_nuances([hol], hw, [d9])):
        errors.append("950mm koridor icin UYARI bekleniyordu")
    # madde 10: L-hol kollari 900/1500 -> daralma UYARISI; esit kollu L temiz
    lh = {"id": "lh", "room_type": "koridor", "polygon": L_HOL_900}
    if not any("daralma" in w for w in check_door_corridor_nuances([lh], [], [])):
        errors.append("900/1500 kollu L icin daralma UYARISI bekleniyordu")
    eq = {"id": "eq", "room_type": "koridor", "polygon": L_HOL_1500}
    if any("daralma" in w for w in check_door_corridor_nuances([eq], [], [])):
        errors.append("esit kollu L icin daralma UYARISI OLMAMALI")
    return errors


def check_core_and_shafts_rev26() -> list[str]:
    """rev-26: asansor/merdiven DAIMA dikdortgen (L-seklinde asansor ERROR);
    saft asansor/merdivenin icine giremez (ERROR); kare 500x500 saft TEMIZ;
    4:3 (600x450) temiz, 2:1 (1000x500) saft oran UYARISI verir; saft poligonu
    dikdortgen degilse UYARI."""
    from standards import check_core_and_shafts, check_room_proportions
    errors: list[str] = []
    def rect(i, t, x0, y0, x1, y1):
        return {"id": i, "room_type": t, "polygon": [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]}
    clean = [rect("e", "asansor", 0, 0, 2100, 3000), rect("s", "saft", 3000, 0, 3500, 500)]
    if check_core_and_shafts(clean) != ([], []):
        errors.append(f"temiz durum: {check_core_and_shafts(clean)}")
    l_lift = {"id": "e", "room_type": "asansor",
              "polygon": [[0, 0], [2100, 0], [2100, 1000], [1000, 1000], [1000, 3000], [0, 3000]]}
    if len(check_core_and_shafts([l_lift])[0]) != 1:
        errors.append("L-seklinde asansor tam 1 ERROR vermeli")
    inside = [rect("m", "merdiven", 0, 0, 4000, 4000), rect("s", "saft", 3700, 3700, 4200, 4200)]
    if len(check_core_and_shafts(inside)[0]) != 1:
        errors.append("merdiven kosesine giren saft tam 1 ERROR vermeli")
    touching = [rect("m", "merdiven", 0, 0, 4000, 4000), rect("s", "saft", 4000, 0, 4500, 500)]
    if check_core_and_shafts(touching)[0]:
        errors.append("merdivene SADECE BITISEN saft ERROR vermemeli (yanlis-pozitif)")
    ratios = {"k": (500, 500, 0), "d": (600, 450, 0), "x": (1000, 500, 1)}
    for key, (w, h, bad) in ratios.items():
        warns = check_room_proportions([rect(key, "saft", 0, 0, w, h)], "mm")
        if bool(warns) != bool(bad):
            errors.append(f"saft {w}x{h}: oran uyarisi beklenen={bool(bad)} gelen={warns}")
    if not check_core_and_shafts([{"id": "s", "room_type": "saft",
                                   "polygon": [[0, 0], [500, 0], [500, 250], [250, 250], [250, 500], [0, 500]]}])[1]:
        errors.append("L-seklinde saft UYARI vermeli")
    return errors


def main() -> int:
    groups = (
        ("koridora acilan kapida kalan gecis (DEV-051)", check_open_door_net_passage_dev051()),
        ("net alan + kapi/koridor nuanslari (DEV-050 #7-10,16)", check_net_area_and_nuances()),
        ("room_aspect_ratio elle hesaplanabilir (+ dejenere durum)", check_room_aspect_ratio_hand_computable()),
        ("check_room_types: yazim hatasi YAKALANIR, eksik alan atlanir", check_room_types_catches_typo_and_skips_missing()),
        ("check_room_proportions: oran ihlali UYARI", check_room_proportions_ratio_violation()),
        ("check_room_proportions: kisa kenar ihlali AYRI UYARI", check_room_proportions_short_edge_violation()),
        ("check_room_proportions: sinir icinde yanlis-pozitif YOK", check_room_proportions_within_limits_no_false_positive()),
        ("check_room_proportions: opt-in + 'm' birimi donusumu", check_room_proportions_skips_untyped_and_meters()),
        ("check_room_proportions: alan ihlali (gecici standart)", check_room_proportions_area_violation()),
        ("narrowest_point elle hesaplanabilir (dikdortgen/L/dejenere)", check_narrowest_point_hand_computable()),
        ("check_room_proportions: yerel en dar nokta (AABB'nin kacirdigi)", check_local_narrow_point_warning()),
        ("net aciklik: duvar ic yuzleri arasi (K1-31/33 vakasi, 250mm)", check_net_clear_width_between_wall_faces()),
        ("net oran + net alan + gercek cikmaz uc (DEV-057 Grup A)", check_net_ratio_area_and_dead_end_dev057()),
        ("validate_standards: temiz katalog + kasitli bozma yakalanir", check_validate_standards_catches_broken_catalog()),
        ("asansor/merdiven dikdortgen + saft kare/4:3 + saft cekirdege girmez (rev-26)", check_core_and_shafts_rev26()),
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
        print("\nSTANDARDS SELF-TEST BASARISIZ.")
        return 1
    print("\nStandards self-test BASARILI.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
