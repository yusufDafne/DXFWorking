#!/usr/bin/env python3
"""Saft/baca modulu self-test'i (rev-27). Beklenen degerler ELLE hesaplanir; her kural
KASITLI BOZMAYLA ve YANLIS-POZITIF tarafiyla sinanir.

Kullanim: python scripts/shafts/selftest.py   (cikis 0 basarili, 1 basarisiz)
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import ezdxf  # noqa: E402

from shafts import (  # noqa: E402
    SHAFT_LAYER, SHAFT_RGB, Shaft, check_shafts, check_shafts_across_floors,
    draw_shafts_on_floor, ensure_shaft_layer, shaft_centerline_side, shared_edge_length,
)


def rect(x0, y0, x1, y1):
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


def room(i, t, poly, unit=None):
    d = {"id": i, "room_type": t, "polygon": poly}
    if unit:
        d["unit_id"] = unit
    return d


def floor_of(rooms, shafts):
    return {"id": "k", "rooms": rooms, "shafts": shafts}


def good_floor():
    """WC (0..2000 x 0..1400) ve banyo (0..2000 x 1400..3400) ayni dairede bitisik;
    650x650 saft (2000..2650 x 1075..1725) ikisine de deger (elle: ortak kenar WC icin
    y 1075..1400 = 325, banyo icin 1400..1725 = 325 >= 300)."""
    rooms = [room("wc", "wc", rect(0, 0, 2000, 1400), "A"), room("banyo", "banyo", rect(0, 1400, 2000, 3400), "A")]
    shafts = [{"id": "s1", "kind": "tesisat", "polygon": rect(2000, 1075, 2650, 1725), "unit_id": "A"}]
    return rooms, shafts


def check_defaults_and_geometry() -> list[str]:
    errors: list[str] = []
    if shaft_centerline_side() != 650.0 or shaft_centerline_side(net_mm=600.0, wall_mm=100.0) != 700.0:
        errors.append("poligon kenari net+duvar: 500+150=650, 600+100=700 olmali")
    s = Shaft.from_context({"id": "s", "kind": "baca", "polygon": rect(0, 0, 600, 450)})
    if not s.is_rectangle or abs(s.aspect_ratio - 600 / 450) > 1e-9:
        errors.append(f"600x450 dikdortgen, oran 4/3: {s.is_rectangle} {s.aspect_ratio}")
    if shared_edge_length(rect(0, 0, 1000, 1000), rect(1000, 200, 2000, 700)) != 500.0:
        errors.append("ortak kenar 500 olmali")
    if shared_edge_length(rect(0, 0, 1000, 1000), rect(1001.5, 0, 2000, 1000)) != 0.0:
        errors.append("1.5 mm bosluklu poligonlar ortak kenar SAYILMAMALI (yanlis-pozitif)")
    return errors


def check_clean_floor() -> list[str]:
    rooms, shafts = good_floor()
    got = check_shafts(floor_of(rooms, shafts))
    return [] if got == ([], []) else [f"temiz kat: {got}"]


def check_deliberate_breaks() -> list[str]:
    errors: list[str] = []
    rooms, shafts = good_floor()
    # bilinmeyen tur
    bad = [dict(shafts[0], kind="yok")]
    if len(check_shafts(floor_of(rooms, bad))[0]) != 1:
        errors.append("bilinmeyen tur tam 1 HATA vermeli")
    # oran 2:1 -> UYARI (HATA degil)
    wide = [dict(shafts[0], polygon=rect(2000, 1075, 3000, 1575))]
    e, w = check_shafts(floor_of(rooms, wide))
    if e or not any("orani" in x for x in w):
        errors.append(f"2:1 saft oran UYARISI (hata degil) vermeli: {e} {w}")
    # 4:3 temiz
    ok43 = [dict(shafts[0], polygon=rect(2000, 1075, 2800, 1675))]
    if any("orani" in x for x in check_shafts(floor_of(rooms, ok43))[1]):
        errors.append("4:3 saft oran UYARISI VERMEMELI (yanlis-pozitif)")
    # odanin icine girme -> HATA
    inside = [dict(shafts[0], polygon=rect(1500, 1075, 2150, 1725))]
    if len(check_shafts(floor_of(rooms, inside))[0]) < 1:
        errors.append("oda icine giren saft HATA vermeli")
    # asansor kosesine girme -> HATA (mesaj asansor/merdiven demeli)
    core = [room("m", "merdiven", rect(5000, 0, 9000, 4000))]
    deep = [{"id": "s", "kind": "tesisat", "polygon": rect(8500, 3500, 9150, 4150)}]
    e, _ = check_shafts(floor_of(core, deep))
    if len(e) != 1 or "asansor/merdiven" not in e[0]:
        errors.append(f"merdiven kosesine giren saft tam 1 HATA: {e}")
    touching = [{"id": "s", "kind": "tesisat", "polygon": rect(9000, 0, 9650, 650)}]
    if check_shafts(floor_of(core, touching))[0]:
        errors.append("merdivene SADECE bitisen saft HATA vermemeli (yanlis-pozitif)")
    # saft yok -> WC+banyo bitisik ama ikisine de degen saft yok: 2 uyari (her islak oda + cift)
    none_floor = floor_of(rooms, [])
    e, w = check_shafts(none_floor)
    if e or len(w) != 3:
        errors.append(f"saftsiz bitisik WC+banyo: 2 'ne sirt sirta ne safta' + 1 'cift arasi saft yok' UYARI beklenir: {w}")
    # saft sadece WC'ye degiyor -> cift uyarisi kalir
    wc_only = [dict(shafts[0], polygon=rect(2000, 0, 2650, 650))]
    w = check_shafts(floor_of(rooms, wc_only))[1]
    if not any("ARASINDA" in x for x in w):
        errors.append(f"yalniz WC'ye degen saft: cift uyarisi kalmali: {w}")
    # baska dairenin islak hacmiyle SIRT SIRTA -> saft gerekmez
    back = [room("wcA", "wc", rect(0, 0, 2000, 1400), "A"), room("banyoB", "banyo", rect(0, 1400, 2000, 3400), "B")]
    if check_shafts(floor_of(back, []))[1]:
        errors.append("farkli dairelerin sirt sirta islak hacimleri UYARI VERMEMELI (yanlis-pozitif)")
    return errors


def check_across_floors() -> list[str]:
    errors: list[str] = []
    a = {"id": "k1", "shafts": [{"id": "s", "kind": "tesisat", "polygon": rect(0, 0, 650, 650)}]}
    b = {"id": "k2", "shafts": [{"id": "s", "kind": "tesisat", "polygon": rect(0, 0, 650, 650)}]}
    if check_shafts_across_floors([a, b]):
        errors.append("ayni konumdaki saft UYARI VERMEMELI")
    b2 = {"id": "k2", "shafts": [{"id": "s", "kind": "tesisat", "polygon": rect(100, 0, 750, 650)}]}
    if len(check_shafts_across_floors([a, b2])) != 1:
        errors.append("kaymis saft tam 1 UYARI vermeli")
    return errors


def check_drawing() -> list[str]:
    errors: list[str] = []
    doc = ezdxf.new()
    ensure_shaft_layer(doc); ensure_shaft_layer(doc)
    if tuple(doc.layers.get(SHAFT_LAYER).rgb) != SHAFT_RGB:
        errors.append("SAFT katman rengi palette ile ayni olmali")
    msp = doc.modelspace()
    _, shafts = good_floor()
    n = draw_shafts_on_floor(msp, floor_of([], shafts + [dict(shafts[0], id="s2", kind="baca")]))
    if n != 2 or len(msp.query("LWPOLYLINE")) != 2 or len(msp.query("LINE")) != 4:
        errors.append(f"2 saft = 2 kapali kare + 4 capraz cizgi: n={n}")
    if draw_shafts_on_floor(msp, floor_of([], [dict(shafts[0], kind="yok")])) != 0:
        errors.append("bilinmeyen turlu saft CIZILMEMELI")
    return errors


def check_drawn_over_net_void() -> list[str]:
    """Saft duvar BANDININ degil, duvar yuzleri arasindaki bosluga cizilir: 650x650 poligonun
    4 kenarinda 150 mm duvar -> cizilen kare 500x500 ve poligonun ORTASINDA (elle: 75 mm iceri)."""
    errors: list[str] = []
    poly = rect(1000, 1000, 1650, 1650)
    walls = [{"id": f"w{i}", "start": poly[i], "end": poly[(i + 1) % 4], "thickness": 150.0, "layer": "D"}
             for i in range(4)]
    doc = ezdxf.new(); ensure_shaft_layer(doc); msp = doc.modelspace()
    draw_shafts_on_floor(msp, {"shafts": [{"id": "s", "kind": "tesisat", "polygon": poly}], "walls": walls})
    pts = [tuple(round(c, 3) for c in p[:2]) for p in list(msp.query("LWPOLYLINE"))[0].get_points()]
    if sorted(set(pts)) != [(1075.0, 1075.0), (1075.0, 1575.0), (1575.0, 1075.0), (1575.0, 1575.0)]:
        errors.append(f"500x500 net kare (1075..1575) beklenirdi: {pts}")
    doc2 = ezdxf.new(); ensure_shaft_layer(doc2); msp2 = doc2.modelspace()
    draw_shafts_on_floor(msp2, {"shafts": [{"id": "s", "kind": "tesisat", "polygon": poly}], "walls": []})
    pts2 = sorted({tuple(round(c, 3) for c in p[:2]) for p in list(msp2.query("LWPOLYLINE"))[0].get_points()})
    if pts2 != [(1000.0, 1000.0), (1000.0, 1650.0), (1650.0, 1000.0), (1650.0, 1650.0)]:
        errors.append(f"duvarsiz durumda poligonun kendisi beklenirdi: {pts2}")
    return errors


def main() -> int:
    groups = (
        ("varsayilanlar ve geometri yardimcilari", check_defaults_and_geometry()),
        ("temiz kat HICBIR uyari/hata vermez", check_clean_floor()),
        ("kasitli bozma + yanlis-pozitif", check_deliberate_breaks()),
        ("saft tum katlarda ayni konumda", check_across_floors()),
        ("cizim: SAFT katmani, kare + capraz", check_drawing()),
        ("cizim duvar yuzleri arasindaki NET boslugun uzerine oturur (rev-27b)", check_drawn_over_net_void()),
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
        print("\nSAFT SELF-TEST BASARISIZ.")
        return 1
    print("\nSaft self-test BASARILI.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
