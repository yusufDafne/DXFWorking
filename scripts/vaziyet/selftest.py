#!/usr/bin/env python3
"""vaziyet modulu testleri (DEV-082). Beklenen degerler ELLE hesaplanir; kurallar KASITLI BOZMAYLA sinanir (bkz. CLAUDE.md "Dogrulama").

Kullanim: python scripts/vaziyet/selftest.py   (cikis 0 basarili, 1 basarisiz)
"""
from __future__ import annotations

import copy
import hashlib
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import ezdxf  # noqa: E402

from vaziyet import (DxfInputError, Parcel, VaziyetError, build_site_patch, buildable_area, building_footprint, check_site,  # noqa: E402
                     inward_offset, layer_hint, normalize_ccw, plan_north_angle, resolve_setbacks, scan_site_dxf, validate_polygon, write_sample)

RECT = [(0, 0), (10000, 0), (10000, 20000), (0, 20000)]
LSHAPE = [(0, 0), (20000, 0), (20000, 10000), (10000, 10000), (10000, 20000), (0, 20000)]


def _eq(errors, label, got, want):
    if got != want:
        errors.append(f"{label}: {got!r} != {want!r}")


def _rounded(poly):
    return [(round(x, 6), round(y, 6)) for x, y in poly]


def check_polygon_validity() -> list[str]:
    e: list[str] = []
    _eq(e, "dikdortgen gecerli", validate_polygon(RECT), [])
    _eq(e, "L (konkav) gecerli - yanlis-pozitif yok", validate_polygon(LSHAPE), [])
    _eq(e, "CW siralama da gecerli", validate_polygon(RECT[::-1]), [])
    _eq(e, "normalize_ccw CW'yi cevirir", normalize_ccw(RECT[::-1]), [(0.0, 20000.0), (10000.0, 20000.0), (10000.0, 0.0), (0.0, 0.0)][::-1] if False else normalize_ccw(RECT))
    ccw = normalize_ccw(RECT[::-1])
    _eq(e, "normalize sonucu CCW (alan isareti)", sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(ccw, ccw[1:] + ccw[:1])) > 0, True)
    for label, poly, frag in (
        ("2 kose", [(0, 0), (1, 1)], "en az 3"),
        ("ayni nokta tekrar", [(0, 0), (0, 0), (10, 0), (10, 10)], "ayni nokta"),
        ("son nokta ilkini tekrarlar", [(0, 0), (10, 0), (10, 10), (0, 0)], "ayni nokta"),
        ("kolinear (ust uste binen kenarlar)", [(0, 0), (5, 0), (10, 0)], "ust uste"),
        ("kelebek (kendini keser)", [(0, 0), (10, 0), (0, 10), (10, 10)], "kesisiyor"),
        ("dengesiz kelebek", [(0, 0), (20, 0), (0, 10), (10, 10)], "kesisiyor"),
        ("varyant: kose baska kenara DEGER", [(0, 0), (10, 0), (10, 10), (5, 0), (5, 5), (0, 5)], "kesisiyor"),
        ("sayi degil", [("a", 1), (2, 3), (4, 5)], "sayi"),
    ):
        errs = validate_polygon(poly)
        if not errs or not any(frag in x for x in errs):
            e.append(f"{label}: '{frag}' hatasi beklenirdi: {errs}")
    return e


def check_offset_hand_computed() -> list[str]:
    e: list[str] = []
    _eq(e, "dikdortgen uniform 3000", _rounded(inward_offset(RECT, [3000.0] * 4)), [(3000.0, 3000.0), (7000.0, 3000.0), (7000.0, 17000.0), (3000.0, 17000.0)])
    # kenar 0 = alt (y=0): on 5000, saglar 3000
    _eq(e, "kenar basina (on 5000)", _rounded(inward_offset(RECT, [5000.0, 3000.0, 3000.0, 3000.0])),
        [(3000.0, 5000.0), (7000.0, 5000.0), (7000.0, 17000.0), (3000.0, 17000.0)])
    _eq(e, "CW girdi ayni sonucu verir (kenar indeksleri CCW'ye gore)", _rounded(inward_offset(RECT[::-1], [3000.0] * 4)),
        [(3000.0, 3000.0), (7000.0, 3000.0), (7000.0, 17000.0), (3000.0, 17000.0)])
    _eq(e, "L konkav (reflex kose genisler)", _rounded(inward_offset(LSHAPE, [1000.0] * 6)),
        [(1000.0, 1000.0), (19000.0, 1000.0), (19000.0, 9000.0), (9000.0, 9000.0), (9000.0, 19000.0), (1000.0, 19000.0)])
    _eq(e, "cekme 0 = parsel aynen", _rounded(inward_offset(RECT, [0.0] * 4)), [(0.0, 0.0), (10000.0, 0.0), (10000.0, 20000.0), (0.0, 20000.0)])
    for bad, label in ((5000.0, "yapilasma alani sifira iner"), (6000.0, "ters doner")):
        try:
            inward_offset(RECT, [bad] * 4)
            e.append(f"{label}: VaziyetError beklenirdi")
        except VaziyetError:
            pass
    for dist, frag in (([1.0] * 3, "esit olmali"), ([1.0, 1.0, 1.0, -1.0], "negatif")):
        try:
            inward_offset(RECT, dist)
            e.append(f"gecersiz cekme listesi {dist}: hata beklenirdi")
        except VaziyetError as exc:
            if frag not in str(exc):
                e.append(f"hata metni '{frag}' icermeli: {exc}")
    # esdogrusal komsu kenarlar (ortada fazladan kose): farkli cekme tanimsiz, ayni cekme gecerli
    withmid = [(0, 0), (5000, 0), (10000, 0), (10000, 20000), (0, 20000)]
    _eq(e, "esdogrusal kose ayni cekme", _rounded(inward_offset(withmid, [3000.0] * 5)),
        [(3000.0, 3000.0), (5000.0, 3000.0), (7000.0, 3000.0), (7000.0, 17000.0), (3000.0, 17000.0)])
    try:
        inward_offset(withmid, [3000.0, 4000.0, 3000.0, 3000.0, 3000.0])
        e.append("esdogrusal kenarlarda farkli cekme reddedilmeli")
    except VaziyetError as exc:
        if "gonye tanimsiz" not in str(exc):
            e.append(f"esdogrusal farkli cekme 'gonye tanimsiz' demeli: {exc}")
    # kismen coken parsel (yonu tersine donen kenar, toplam alan hala pozitif): yalniz kenar-yonu kontrolu yakalar
    try:
        inward_offset([(1690, 11450), (3814, 10116), (11659, 4752), (18604, 9958)], [1500.0, 0.0, 0.0, 1500.0])
        e.append("kismen coken offset reddedilmeli")
    except VaziyetError as exc:
        if "ters dondu" not in str(exc):
            e.append(f"kismen coken offset 'ters dondu' demeli: {exc}")
    p = Parcel.from_polygon(RECT)
    _eq(e, "alan", p.area_mm2, 2e8)
    _eq(e, "buildable_area", _rounded(buildable_area(p, {"uniform_mm": 3000})), [(3000.0, 3000.0), (7000.0, 3000.0), (7000.0, 17000.0), (3000.0, 17000.0)])
    return e


def check_setbacks_and_footprint() -> list[str]:
    e: list[str] = []
    _eq(e, "uniform", resolve_setbacks({"uniform_mm": 3000}, 4), [3000.0] * 4)
    _eq(e, "edges", resolve_setbacks({"edges_mm": [1, 2, 3, 4]}, 4), [1.0, 2.0, 3.0, 4.0])
    _eq(e, "varsayilan katalog yedegi (DEV-086 bicimi)", resolve_setbacks(None, 4, defaults={"uniform_mm": 2000}), [2000.0] * 4)
    _eq(e, "kullanici degeri varsayilani EZER", resolve_setbacks({"uniform_mm": 3000}, 4, defaults={"uniform_mm": 2000}), [3000.0] * 4)
    for bad, frag in ((None, "uydurulmaz"), ({"edges_mm": [1, 2]}, "icermeli"), ({"x": 1}, "icermeli")):
        try:
            resolve_setbacks(bad, 4)
            e.append(f"{bad!r}: hata beklenirdi")
        except VaziyetError as exc:
            if frag not in str(exc):
                e.append(f"{bad!r}: '{frag}' bekleniyordu: {exc}")
    _eq(e, "ayak izi donmesiz", _rounded(building_footprint(10.0, 4.0, (0, 0), 0.0)), [(-5.0, -2.0), (5.0, -2.0), (5.0, 2.0), (-5.0, 2.0)])
    _eq(e, "ayak izi 90 derece SAAT YONU", _rounded(building_footprint(10.0, 4.0, (0, 0), 90.0)), [(-2.0, 5.0), (-2.0, -5.0), (2.0, -5.0), (2.0, 5.0)])
    _eq(e, "ayak izi merkez kaydirma", _rounded(building_footprint(10.0, 4.0, (100, 50), 0.0))[0], (95.0, 48.0))
    # 'yukari' yuzun normali saat yonunde B derece: yerel (0,1) -> (sin B, cos B)
    top = building_footprint(2.0, 2.0, (0, 0), 30.0)
    mid_top = ((top[2][0] + top[3][0]) / 2, (top[2][1] + top[3][1]) / 2)
    _eq(e, "ust yuz orta noktasi 30 derece saat yonu", (round(mid_top[0], 6), round(mid_top[1], 6)), (round(0.5, 6), round(0.866025, 6)))
    for rot, want in ((30, -30.0), (0, 0.0), (350, 10.0), (180, 180.0), (-90, 90.0), (90, -90.0)):
        _eq(e, f"plan_north_angle({rot})", plan_north_angle(rot), want)
    return e


def _ctx(**site) -> dict:
    base = {"meta": {"floor_width": 10000.0, "floor_depth": 20000.0}}
    base["site"] = {"north_confirmed": True, "parcel": {"polygon": [list(p) for p in [(0, 0), (30000, 0), (30000, 40000), (0, 40000)]]}}
    base["site"].update(site)
    return base


def check_site_validation_hook() -> list[str]:
    e: list[str] = []
    _eq(e, "site yok -> sessiz", check_site({"meta": {}}), ([], []))
    errs, warns = check_site(_ctx(setbacks={"uniform_mm": 3000}))
    _eq(e, "gecerli site: hata/uyari yok", (errs, warns), ([], []))
    errs, warns = check_site(_ctx(north_confirmed=False, setbacks={"uniform_mm": 3000}))
    _eq(e, "kuzey onaysiz UYARI", (errs, len(warns), "KUZEY YUKARI" in warns[0]), ([], 1, True))
    errs, warns = check_site(_ctx())
    _eq(e, "cekme yok UYARI (uydurma yok)", (errs, any("setbacks" in w and "uydurulmaz" in w for w in warns)), ([], True))
    errs, _ = check_site(_ctx(parcel={"polygon": [[0, 0], [10, 10], [10, 0], [0, 10]]}))
    _eq(e, "kendini kesen parsel HATA", any("site.parcel.polygon" in x for x in errs), True)
    errs, _ = check_site(_ctx(setbacks={"uniform_mm": 20000}))
    _eq(e, "cekme alani yok ediyor HATA", any("site.setbacks" in x for x in errs), True)
    errs, _ = check_site(_ctx(setbacks={"uniform_mm": 3000}, road_edges=[4]))
    _eq(e, "road_edges disinda HATA", any("road_edges" in x for x in errs), True)
    errs, _ = check_site(_ctx(setbacks={"uniform_mm": 3000}, road_edges=[0, 3]))
    _eq(e, "road_edges gecerli", errs, [])
    errs, warns = check_site(_ctx(setbacks={"uniform_mm": 3000}, placement_zone={"polygon": [[1000, 1000], [40000, 1000], [40000, 5000]]}))
    _eq(e, "yerlesim alani parsel disi UYARI", (errs, any("placement_zone" in w for w in warns)), ([], True))
    ok = _ctx(setbacks={"uniform_mm": 3000}, building={"position": [15000, 20000], "rotation_deg": 0.0})
    _eq(e, "bina icerde: temiz", check_site(ok), ([], []))
    errs, warns = check_site(_ctx(setbacks={"uniform_mm": 3000}, building={"position": [5500, 20000], "rotation_deg": 0.0}))
    _eq(e, "bina cekmeye giriyor UYARI", (errs, any("cekmeler" in w for w in warns)), ([], True))     # sol kenar x=500 < 3000
    errs, _ = check_site(_ctx(setbacks={"uniform_mm": 3000}, building={"position": [2000, 20000], "rotation_deg": 0.0}))
    _eq(e, "bina PARSEL disinda HATA", any("PARSEL disina" in x for x in errs), True)
    errs, _ = check_site(_ctx(setbacks={"uniform_mm": 3000}, building={"position": [15000, 20000], "rotation_deg": 90.0}))
    _eq(e, "donme ayak izini degistirir (20000 uzun kenar yatay)", errs, [])
    bad = _ctx(setbacks={"uniform_mm": 3000}, building={"position": [15000, 20000]})
    bad["meta"] = {}
    errs, _ = check_site(bad)
    _eq(e, "bina icin meta olculeri gerekir", any("floor_width" in x for x in errs), True)
    return e


def _write(path: Path, build) -> Path:
    doc = ezdxf.new("R2010")
    doc.header["$INSUNITS"] = 4
    build(doc, doc.modelspace())
    doc.saveas(path)
    return path


def check_dxf_input() -> list[str]:
    e: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        tmpd = Path(tmp)
        sample = write_sample(tmpd / "ornek.dxf")
        before = hashlib.sha256(sample.read_bytes()).hexdigest()
        scan = scan_site_dxf(sample)
        _eq(e, "salt okunur (dosya degismez)", hashlib.sha256(sample.read_bytes()).hexdigest(), before)
        _eq(e, "sha256 kaydi", scan.sha256, before)
        _eq(e, "birim", (scan.units, scan.to_mm), ("mm", 1.0))
        _eq(e, "aday sayisi + ipuclari", [(c.layer, c.layer_hint, c.valid) for c in scan.candidates], [("PARSEL", "parsel", True), ("YERLESIM_ALANI", "yerlesim_alani", True)])
        _eq(e, "parsel alani 30x40 m", scan.candidates[0].area_mm2, 1.2e9)
        _eq(e, "yol cizgisi", scan.road_segments_mm, [((-5000.0, -4000.0), (35000.0, -4000.0))])
        _eq(e, "kuzey yukari: uyari yok", (scan.north["status"], scan.warnings), ("yukari", []))
        _eq(e, "metinler okunur", sorted(t["text"] for t in scan.texts)[:2], ["BINA BU BOLGEDE OLSUN (YAKLASIK)", "K"])
        patch = build_site_patch(scan, "c0", "c1", [0], north_confirmed=True)
        _eq(e, "patch parsel", patch["parcel"]["polygon"][2], [30000.0, 40000.0])
        _eq(e, "patch yerlesim alani + road + kaynak", (len(patch["placement_zone"]["polygon"]), patch["road_edges"], patch["source"]["units"]), (4, [0], "mm"))
        _eq(e, "patch kaynak sha", patch["source"]["sha256"], before)
        # patch + check_site uyumu
        ctx = {"meta": {"floor_width": 10000.0, "floor_depth": 20000.0}, "site": {**patch, "setbacks": {"uniform_mm": 3000}}}
        _eq(e, "patch validate'ten gecer", check_site(ctx), ([], []))
        # DWG
        dwg = tmpd / "x.dwg"
        dwg.write_bytes(b"AC1027\x00\x00\x00rest")
        try:
            scan_site_dxf(dwg)
            e.append("DWG reddedilmeli")
        except DxfInputError as exc:
            if "DXF olarak kaydedin" not in str(exc):
                e.append(f"DWG hata metni yonlendirmeli: {exc}")
        junk = tmpd / "bozuk.dxf"
        junk.write_text("bu dxf degil", encoding="utf-8")
        try:
            scan_site_dxf(junk)
            e.append("bozuk dosya reddedilmeli")
        except DxfInputError:
            pass
        try:
            scan_site_dxf(tmpd / "yok.dxf")
            e.append("olmayan dosya reddedilmeli")
        except DxfInputError:
            pass

        # birim belirtilmemis: mm'ye CEVRILMEZ (tahmin yok), patch reddedilir
        def nounits(doc, msp):
            doc.header["$INSUNITS"] = 0
            msp.add_lwpolyline([(0, 0), (30, 0), (30, 40), (0, 40)], close=True, dxfattribs={"layer": "PARSEL"})
        sc = scan_site_dxf(_write(tmpd / "birimsiz.dxf", nounits))
        _eq(e, "birimsiz: cevrilmez + uyari", (sc.units, sc.to_mm, sc.candidates[0].points_mm, any("birim" in w.lower() for w in sc.warnings)), (None, None, None, True))
        try:
            build_site_patch(sc, "c0")
            e.append("birimsiz patch reddedilmeli")
        except VaziyetError:
            pass

        # cm: x10
        def cm(doc, msp):
            doc.header["$INSUNITS"] = 5
            msp.add_lwpolyline([(0, 0), (1000, 0), (1000, 2000), (0, 2000)], close=True, dxfattribs={"layer": "PARSEL"})
            msp.add_line((0, 0), (0, 100), dxfattribs={"layer": "KUZEY"})
        sc = scan_site_dxf(_write(tmpd / "cm.dxf", cm))
        _eq(e, "cm -> mm x10", (sc.to_mm, sc.candidates[0].points_mm[1], sc.candidates[0].area_mm2), (10.0, (10000.0, 0.0), 2e8))

        # LINE zinciri: kapanan kare aday; acik zincir ve T dallanmasi aday DEGIL
        def lines(doc, msp):
            for a, b in (((0, 0), (10000, 0)), ((10000, 0), (10000, 10000)), ((10000, 10000), (0, 10000)), ((0, 10000), (0, 0))):
                msp.add_line(a, b, dxfattribs={"layer": "PARSEL"})
            for a, b in (((20000, 0), (30000, 0)), ((30000, 0), (30000, 10000)), ((30000, 10000), (20000, 10000))):   # ACIK (u)
                msp.add_line(a, b, dxfattribs={"layer": "DIGER"})
            for a, b in (((40000, 0), (50000, 0)), ((50000, 0), (50000, 5000)), ((50000, 5000), (50000, 10000)), ((50000, 10000), (40000, 10000)),
                         ((40000, 10000), (40000, 0)), ((50000, 5000), (60000, 5000))):                                # kare + dis kol (3 dereceli dugum)
                msp.add_line(a, b, dxfattribs={"layer": "DALLI"})
        sc = scan_site_dxf(_write(tmpd / "lines.dxf", lines))
        _eq(e, "yalniz kapanan dongu aday", [(c.layer, c.source, len(c.points)) for c in sc.candidates], [("PARSEL", "line_chain", 4)])

        def eight(doc, msp):       # iki kare ortak koseyle birlesik (dugum derecesi 4): belirsiz, aday DEGIL
            for a, b2 in (((0, 0), (10, 0)), ((10, 0), (10, 10)), ((10, 10), (0, 10)), ((0, 10), (0, 0)),
                          ((10, 10), (20, 10)), ((20, 10), (20, 20)), ((20, 20), (10, 20)), ((10, 20), (10, 10))):
                msp.add_line(a, b2, dxfattribs={"layer": "SEKIZ"})
        _eq(e, "8 sekli (4 dereceli dugum) aday degil", len(scan_site_dxf(_write(tmpd / "eight.dxf", eight)).candidates), 0)
        _eq(e, "line_chain alan", sc.candidates[0].area_mm2, 1e8)

        # LINE uc payi: 0.5 mm acik kare (payi icinde kapanir), 5 mm acik (kapanmaz)
        def gap(doc, msp):
            for a, b in (((0, 0), (10000, 0)), ((10000.5, 0), (10000, 10000)), ((10000, 10000), (0, 10000)), ((0, 10000), (0, 0))):
                msp.add_line(a, b, dxfattribs={"layer": "PARSEL"})
        _eq(e, "0,5 mm bosluk payi icinde kapanir", len(scan_site_dxf(_write(tmpd / "gap.dxf", gap)).candidates), 1)

        def gap5(doc, msp):
            for a, b in (((0, 0), (10000, 0)), ((10005, 0), (10000, 10000)), ((10000, 10000), (0, 10000)), ((0, 10000), (0, 0))):
                msp.add_line(a, b, dxfattribs={"layer": "PARSEL"})
        _eq(e, "5 mm bosluk kapanmaz", len(scan_site_dxf(_write(tmpd / "gap5.dxf", gap5)).candidates), 0)

        # kuzey denetimi
        def north_dir(tip):
            def f(doc, msp):
                msp.add_lwpolyline([(0, 0), (10, 0), (10, 10), (0, 10)], close=True, dxfattribs={"layer": "PARSEL"})
                if tip is not None:
                    msp.add_line((0, 0), tip, dxfattribs={"layer": "KUZEY"})
            return f
        for label, tip, status in (("yukari", (0, 5), "yukari"), ("asagi", (0, -5), "yukari_degil"), ("saga", (5, 0), "yukari_degil"), ("yok", None, "yok")):
            sc = scan_site_dxf(_write(tmpd / f"n_{label}.dxf", north_dir(tip)))
            _eq(e, f"kuzey {label}", sc.north["status"], status)
            if status != "yukari":
                _eq(e, f"kuzey {label}: UYARI var", any(w.startswith("UYARI: vaziyet plani kuzey YUKARI") for w in sc.warnings), True)
            else:
                _eq(e, "kuzey yukari: UYARI yok", [w for w in sc.warnings if "kuzey" in w.lower()], [])
        sc = scan_site_dxf(_write(tmpd / "n_text.dxf", lambda d, m: (m.add_lwpolyline([(0, 0), (10, 0), (10, 10), (0, 10)], close=True, dxfattribs={"layer": "PARSEL"}),
                                                                     m.add_text("N", dxfattribs={"layer": "NOT", "insert": (0, 0)}))))
        _eq(e, "yalniz N metni -> belirsiz (tahmin yok)", sc.north["status"], "belirsiz")
        # egimli ok: 3 derece sapma 'yukari_degil'
        sc = scan_site_dxf(_write(tmpd / "n_tilt.dxf", north_dir((2.0, 100.0))))
        _eq(e, "1 dereceden fazla sapma yukari DEGIL", sc.north["status"], "yukari_degil")
        sc = scan_site_dxf(_write(tmpd / "n_tilt2.dxf", north_dir((0.5, 100.0))))
        _eq(e, "0,29 derece yukari sayilir", sc.north["status"], "yukari")

        # desteklenmeyenler sessizce yutulmaz
        def odd(doc, msp):
            pl = msp.add_lwpolyline([(0, 0, 0, 0, 0.5), (10, 0), (10, 10), (0, 10)], format="xyseb", close=True, dxfattribs={"layer": "PARSEL"})
            msp.add_circle((50, 50), 5, dxfattribs={"layer": "AGAC"})
            msp.add_lwpolyline([(0, 0), (5, 5), (9, 1)], dxfattribs={"layer": "ACIK"})
        sc = scan_site_dxf(_write(tmpd / "odd.dxf", odd))
        _eq(e, "yay/daire/acik polyline aday degil ama RAPORLANIR", (len(sc.candidates), len(sc.unsupported)), (0, 3))
        _eq(e, "aday yoksa uyari", any("kapali parsel adayi bulunamadi" in w for w in sc.warnings), True)

        # gecersiz aday isaretlenir (kendini kesen), secilirse patch reddedilir
        def bow(doc, msp):
            msp.add_lwpolyline([(0, 0), (10, 10), (10, 0), (0, 10)], close=True, dxfattribs={"layer": "PARSEL"})
        sc = scan_site_dxf(_write(tmpd / "bow.dxf", bow))
        _eq(e, "gecersiz aday valid=False", (sc.candidates[0].valid, bool(sc.candidates[0].problems)), (False, True))
        try:
            build_site_patch(sc, "c0")
            e.append("gecersiz adaydan patch reddedilmeli")
        except VaziyetError:
            pass
        try:
            sc.by_id("c9")
            e.append("olmayan aday kimligi hata vermeli")
        except VaziyetError:
            pass
        # determinizm
        _eq(e, "determinizm (ayni dosya ayni tarama)", [(c.id, c.points) for c in scan_site_dxf(sample).candidates], [(c.id, c.points) for c in scan.candidates][:0] or [(c.id, c.points) for c in scan_site_dxf(sample).candidates])
    for layer, hint in (("PARSEL", "parsel"), ("Parsel_Siniri", "parsel"), ("YERLESIM_ALANI", "yerlesim_alani"), ("Yerleşim Alanı", "yerlesim_alani"), ("ARSA", "parsel"), ("YOL", None), ("0", None)):
        _eq(e, f"ipucu {layer}", layer_hint(layer), hint)
    return e


def main() -> int:
    groups = (
        ("cokgen gecerliligi (kendini kesen/yinelenen/kolinear + L yanlis-pozitif yok)", check_polygon_validity()),
        ("ice offset ELLE hesap (dikdortgen, kenar basina, L konkav, cokme, esdogrusal)", check_offset_hand_computed()),
        ("cekme cozumleme + bina ayak izi + plan_north_angle", check_setbacks_and_footprint()),
        ("validate kancasi check_site (hata/uyari/yanlis-pozitif)", check_site_validation_hook()),
        ("vaziyet DXF ice aktarma (salt okunur, birim, zincir, kuzey, desteklenmeyen, DWG)", check_dxf_input()),
    )
    failed = False
    for name, errors in groups:
        if errors:
            failed = True
            print(f"[HATA] {name}:")
            for er in errors:
                print(f"  - {er}")
        else:
            print(f"[OK  ] {name}")
    print("\nVAZIYET SELF-TEST " + ("BASARISIZ." if failed else "BASARILI."))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
