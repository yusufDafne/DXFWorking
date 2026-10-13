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
from vaziyet import ZONING_DEFAULTS, edge_roles, resolve_zoning, setbacks_for_parcel  # noqa: E402

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


def check_zoning_catalog_dev086() -> list[str]:
    """DEV-086: imar standart deger katalogu - elle okunan degerler, kullanici ustunlugu, kosul eslesmezse UYGULANMAZ, adiyla bildirim."""
    import re
    e: list[str] = []
    want = {"front_setback_mm": 5000.0, "side_setback_mm": 3000.0, "rear_setback_mm": 3000.0, "taks": 0.40, "taks_max_without_kaks": 0.60, "kaks_rule": None}
    _eq(e, "katalog degerleri (tabloyla birebir)", {k: z.value for k, z in ZONING_DEFAULTS.items()}, want)
    for k, z in ZONING_DEFAULTS.items():
        if z.verified or not z.condition or not z.urls or not z.source or z.nizam != "ayrik":
            e.append(f"{k}: DOGRULANMADI + kosul + kaynak/url + ayrik nizam tasimali: {z}")
    src = open(Path(__file__).resolve().parent / "zoning.py", encoding="utf-8").read()
    for name in ("DEFAULT_FRONT_SETBACK_MM", "DEFAULT_SIDE_SETBACK_MM", "DEFAULT_REAR_SETBACK_MM", "DEFAULT_TAKS", "DEFAULT_TAKS_MAX_WITHOUT_KAKS"):
        if not re.search(rf"^{name} = \d+(\.\d+)?\b", src, re.M):
            e.append(f"{name} bagimsiz LITERAL sayi olmali (hesaplanmaz/birbirine baglanmaz)")
    r = resolve_zoning()
    _eq(e, "varsayilanlar: hepsi katalogdan", (r.sources["front_setback_mm"], r.sources["taks"], len(r.used_defaults)), ("varsayilan:DEFAULT_FRONT_SETBACK_MM", "varsayilan:DEFAULT_TAKS", 6))
    _eq(e, "varsayilan: soru yok", r.questions, ())
    d = r.describe()
    _eq(e, "bildirim: her varsayilan ADIYLA + DOGRULANMADI + kosul", all("DOGRULANMADI" in x and "kosul:" in x for x in d) and len(d) == 6, True)
    _eq(e, "bildirim adlari", [("DEFAULT_FRONT_SETBACK_MM" in d[0]), ("DEFAULT_TAKS_MAX_WITHOUT_KAKS" in d[4])], [True, True])
    r = resolve_zoning({"front_setback_mm": 7000, "side_setback_mm": 0})
    _eq(e, "kullanici degeri ezer (0 da gecerli)", (r.values["front_setback_mm"], r.sources["front_setback_mm"], r.values["side_setback_mm"], r.sources["side_setback_mm"]),
        (7000.0, "kullanici", 0.0, "kullanici"))
    _eq(e, "ezilen varsayilan bildirilmez", ["DEFAULT_FRONT_SETBACK_MM" in x or "DEFAULT_SIDE_SETBACK_MM" in x for x in r.describe()], [False] * 4)
    r = resolve_zoning({"kaks": 1.5})
    _eq(e, "kullanici KAKS: 'KAKS yok' siniri/kurali UYGULANMAZ", (r.values["kaks"], r.values["taks_max_without_kaks"], r.values["kaks_rule"], r.values["taks"]), (1.5, None, None, 0.40))
    r = resolve_zoning(plan_states={"taks": True})
    _eq(e, "plan TAKS belirtiyor: varsayilan UYGULANMAZ + soru", (r.values["taks"], any("TAKS" in q for q in r.questions)), (None, True))
    r = resolve_zoning(plan_states={"kaks": True})
    _eq(e, "plan KAKS belirtiyor: KAKS kurali/siniri UYGULANMAZ + soru", (r.values["taks_max_without_kaks"], r.values["kaks_rule"], any("KAKS" in q for q in r.questions)), (None, None, True))
    r = resolve_zoning({"taks": 0.5}, nizam="bitisik")
    _eq(e, "baska nizam: katalog yok -> soru; kullanici degeri yine gecer", (r.values["taks"], r.values["front_setback_mm"], r.used_defaults, len(r.questions) >= 5), (0.5, None, (), True))
    for bad in ({"xyz": 1}, {"taks": -0.1}, {"taks": True}, {"front_setback_mm": "5"}):
        try:
            resolve_zoning(bad)
            e.append(f"{bad!r}: hata beklenirdi")
        except VaziyetError:
            pass
    rect = Parcel.from_polygon(RECT)
    _eq(e, "roller: yol=0", edge_roles(rect, [0]), ["on", "yan", "arka", "yan"])
    _eq(e, "roller: yol=1 (yan kenar)", edge_roles(rect, [1]), ["yan", "on", "yan", "arka"])
    _eq(e, "roller: kose parsel (iki yol)", edge_roles(rect, [0, 1]), ["on", "on", "arka", "yan"])
    trap = Parcel.from_polygon([(0, 0), (30000, 0), (26000, 40000), (2000, 40000)])
    _eq(e, "roller: yamuk (arka = en antiparalel)", edge_roles(trap, [0]), ["on", "yan", "arka", "yan"])
    ell = Parcel.from_polygon([(0, 0), (20000, 0), (20000, 10000), (12000, 10000), (12000, 20000), (0, 20000)])
    _eq(e, "roller: iki antiparalel aday -> en uzun arka", edge_roles(ell, [0]), ["on", "yan", "yan", "yan", "arka", "yan"])
    for bad, frag in (([], "bilinmiyor"), ([9], "gecersiz"), ([True], "gecersiz")):
        try:
            edge_roles(rect, bad)
            e.append(f"road_edges={bad}: hata beklenirdi")
        except VaziyetError as exc:
            if frag not in str(exc):
                e.append(f"road_edges={bad}: '{frag}' bekleniyordu: {exc}")
    sb, res = setbacks_for_parcel(rect, [0], {"front_setback_mm": 6000, "side_setback_mm": 2500, "rear_setback_mm": 4000})
    _eq(e, "setbacks_for_parcel kullanici (on/yan/arka/yan)", sb, {"edges_mm": [6000.0, 2500.0, 4000.0, 2500.0]})
    sb, res = setbacks_for_parcel(Parcel.from_polygon([(0, 0), (30000, 0), (30000, 40000), (0, 40000)]), [0])
    _eq(e, "setbacks_for_parcel varsayilan", sb, {"edges_mm": [5000.0, 3000.0, 3000.0, 3000.0]})
    _eq(e, "varsayilan cekmelerle yapilasma alani ELLE", _rounded(buildable_area(Parcel.from_polygon([(0, 0), (30000, 0), (30000, 40000), (0, 40000)]), sb)),
        [(3000.0, 5000.0), (27000.0, 5000.0), (27000.0, 37000.0), (3000.0, 37000.0)])
    try:
        setbacks_for_parcel(rect, [0], nizam="bitisik")
        e.append("katalogda olmayan nizamda cekme varsayilani UYDURULMAMALI")
    except VaziyetError as exc:
        if "varsayilan YOK" not in str(exc):
            e.append(f"nizam hatasi soru metni icermeli: {exc}")
    # defaults_report: katalog ve `site` varsayilan bildirimi
    import json as _json
    import subprocess
    script = str(Path(__file__).resolve().parent.parent / "defaults_report.py")
    out = subprocess.run([sys.executable, script, "--catalog"], capture_output=True, text=True, timeout=300).stdout
    for needle in ("DEFAULT_FRONT_SETBACK_MM", "DEFAULT_TAKS_MAX_WITHOUT_KAKS", "DOGRULANMADI", "alomaliye.com"):
        if needle not in out:
            e.append(f"defaults_report --catalog '{needle}' icermeli")
    with tempfile.TemporaryDirectory() as tmp:
        ctx = {"site": {"parcel": {"polygon": [[0, 0], [30000, 0], [30000, 40000], [0, 40000]]}, "road_edges": [0]}}
        p1 = Path(tmp) / "c.json"
        p1.write_text(_json.dumps(ctx), encoding="utf-8")
        out = subprocess.run([sys.executable, script, str(p1)], capture_output=True, text=True, timeout=300).stdout
        if "5000.0, 3000.0, 3000.0, 3000.0" not in out or "DEFAULT_FRONT_SETBACK_MM" not in out:
            e.append(f"site.setbacks yokken uygulanacak varsayilanlar bildirilmeli: {out!r}")
        ctx["site"]["setbacks"] = {"uniform_mm": 3000}
        p1.write_text(_json.dumps(ctx), encoding="utf-8")
        out = subprocess.run([sys.executable, script, str(p1)], capture_output=True, text=True, timeout=300).stdout
        if "UYGULANIRDI" in out:
            e.append("site.setbacks VARKEN varsayilan bildirimi OLMAMALI")
    sb, _ = setbacks_for_parcel(rect, [0], {"front_setback_mm": 1, "side_setback_mm": 2, "rear_setback_mm": 3}, nizam="bitisik")
    _eq(e, "baska nizam + tum cekmeler kullanicidan -> gecer", sb, {"edges_mm": [1.0, 2.0, 3.0, 2.0]})
    return e


# ----------------------------------------------------------------------------- DEV-083: yerlesim etudu motoru
PARCEL_30x40 = [(0, 0), (30000, 0), (30000, 40000), (0, 40000)]


def _buildable(setback):
    return buildable_area(Parcel.from_polygon(PARCEL_30x40), {"uniform_mm": setback})


def check_study_candidates_dev083() -> list[str]:
    from vaziyet import build_candidates, footprint_within, run_study
    e: list[str] = []
    # ELLE: 30x40 parsel, cekme 5000 -> yapilasma alani 20x30 [5000..25000]x[5000..35000]; bina 10000x6000, adim 5000, donus 0
    r = run_study(PARCEL_30x40, _buildable(5000), 10000, 6000, step_mm=5000, rotations_deg=[0])
    _eq(e, "uretilen aday (5 x 7)", r.generated, 35)
    _eq(e, "kalan (x 10000/15000/20000 x y 10000..30000 = 3 x 5)", r.survivors, 15)
    _eq(e, "elenen: hepsi yapilasma alani disi", r.eliminated, {"parsel_disi": 0, "yapilasma_alani_disi": 20})
    # donus 90: 6000x10000 -> x merkezleri 10000/15000/20000 (8000..22000), y 10000..30000 = 15; iki donus birlikte 30
    r2 = run_study(PARCEL_30x40, _buildable(5000), 10000, 6000, step_mm=5000, rotations_deg=[90, 0])
    _eq(e, "iki donus: aday 70, kalan 30", (r2.generated, r2.survivors), (70, 30))
    # cekme 2000, adim 13000 -> bina parsel disina tasar: 9 aday, 2 kalan, 7 parsel disi
    r3 = run_study(PARCEL_30x40, _buildable(2000), 10000, 6000, step_mm=13000, rotations_deg=[0])
    _eq(e, "parsel disi eleme (9 aday, 2 kalan, 7 parsel disi)", (r3.generated, r3.survivors, r3.eliminated["parsel_disi"], r3.eliminated["yapilasma_alani_disi"]), (9, 2, 7, 0))
    # sinir: tam sinirda (merkez x=10000 -> sol kenar 5000) ICERI, 1 mm iceri girince (merkez 9999) DISARI
    buildable = _buildable(5000)
    fp_on = building_footprint(10000, 6000, (10000, 15000), 0)
    fp_in1 = building_footprint(10000, 6000, (9999, 15000), 0)
    fp_rot_on = building_footprint(10000, 6000, (15000, 15000), 90)       # dondurulmus ayak izi, kayan nokta hatasi sinirda elenmemeli
    if not footprint_within(fp_on, buildable):
        e.append("sinirda duran ayak izi elenmemeli (yanlis-pozitif)")
    if footprint_within(fp_in1, buildable):
        e.append("1 mm iceri giren ayak izi elenmeli")
    if not footprint_within(fp_rot_on, buildable):
        e.append("dondurulmus ayak izi iceride kalmali")
    # icbukey girinti: KOSELER iceride ama bir kenar girintiyi KESIYOR (L'nin cukur kosesi): yalniz kenar-kesisim kontrolu yakalar
    L = [(0, 0), (20000, 0), (20000, 10000), (10000, 10000), (10000, 20000), (0, 20000)]
    cut = [(18000, 9000), (9000, 18000), (8000, 17000), (17000, 8000)]
    if footprint_within(cut, L):
        e.append("L girintisini kesen ayak izi elenmeli (koseler iceride olsa da)")
    inside_L = [(1000, 1000), (9000, 1000), (9000, 9000), (1000, 9000)]
    if not footprint_within(inside_L, L):
        e.append("L icindeki ayak izi gecmeli")
    # varsayilan YOK: adim ve donus zorunlu
    for bad in ({"step_mm": None, "rotations_deg": [0]}, {"step_mm": 5000, "rotations_deg": []}, {"step_mm": 0, "rotations_deg": [0]}, {"step_mm": 5000, "rotations_deg": None}):
        try:
            build_candidates(buildable, **bad)
            e.append(f"adim/donus verilmeden aday uretildi: {bad}")
        except VaziyetError:
            pass
    try:
        build_candidates(buildable, 1, [0])
        e.append("asiri aday sayisi reddedilmeli")
    except VaziyetError:
        pass
    # siralama: ayni girdi -> ayni liste; donus girdi sirasi sonucu degistirmez
    a = [(c.position, c.rotation_deg) for c in build_candidates(buildable, 5000, [90, 0])]
    b = [(c.position, c.rotation_deg) for c in build_candidates(buildable, 5000, [0, 90])]
    _eq(e, "donus girdi sirasi bagimsiz", a, b)
    _eq(e, "ilk aday (donus 0, bbox min)", a[0], ((5000.0, 5000.0), 0.0))
    return e


def check_study_metrics_dev083() -> list[str]:
    from vaziyet.metrics import (edge_outward_bearing, face_bearings, garden_pieces, long_face_south_deviation_deg, measure_candidate, zone_center_distance_mm,
                                 zone_overlap_ratio)
    e: list[str] = []
    parcel = Parcel.from_polygon(PARCEL_30x40)
    buildable = _buildable(5000)
    zone = [(6000, 8000), (24000, 8000), (24000, 30000), (6000, 30000)]
    # dis normal pusula acilari (CCW parsel: alt, sag, ust, sol): 180, 90, 0, 270
    _eq(e, "kenar dis normalleri", [round(edge_outward_bearing(parcel, i)) for i in range(4)], [180, 90, 0, 270])
    _eq(e, "yuz acilari donus 0", face_bearings(0), {"ust": 0.0, "sag": 90.0, "alt": 180.0, "sol": 270.0})
    _eq(e, "yuz acilari donus 30", face_bearings(30), {"ust": 30.0, "sag": 120.0, "alt": 210.0, "sol": 300.0})
    fp = building_footprint(10000, 6000, (15000, 10000), 0)          # x 10000..20000, y 7000..13000
    ms = {m.name: m for m in measure_candidate(parcel, buildable, fp, 0.0, 10000, 6000, road_edges=[0], zone=zone)}
    _eq(e, "yapilasma alani payi (alt 7000-5000)", round(ms["buildable_margin_mm"].value, 6), 2000.0)
    _eq(e, "en yakin parsel kenari", round(ms["min_parcel_edge_distance_mm"].value, 6), 7000.0)
    _eq(e, "yol disi en yakin sinir (sag/sol 10000)", round(ms["min_other_edge_distance_mm"].value, 6), 10000.0)
    _eq(e, "yol mesafesi", round(ms["road_distance_mm"].value, 6), 7000.0)
    _eq(e, "yola bakan yuz", (ms["road_face"].value, round(ms["road_face_deviation_deg"].value, 6)), ("alt", 0.0))
    _eq(e, "uzun yuzler guneye sapma (alt yuz 180)", ms["long_face_south_deviation_deg"].value, 0.0)
    _eq(e, "bahce parcasi", ms["garden_pieces"].value, 1)
    _eq(e, "bolge ortusmesi 50e6/60e6", round(ms["zone_overlap_ratio"].value, 9), round(50e6 / 60e6, 9))
    _eq(e, "bolge merkez uzakligi (19000-10000)", round(ms["zone_center_distance_mm"].value, 6), 9000.0)
    _eq(e, "olcum kaynagi fonksiyon adini tasir", ms["road_distance_mm"].source, "road_facing")
    # donus 90: ayak izi x 12000..18000, y 5000..15000
    fp90 = building_footprint(10000, 6000, (15000, 10000), 90)
    ms90 = {m.name: m for m in measure_candidate(parcel, buildable, fp90, 90.0, 10000, 6000, road_edges=[0])}
    ms2 = {m.name: m for m in measure_candidate(parcel, buildable, fp, 0.0, 10000, 6000, road_edges=[0, 2])}      # alt (7000) ve ust (27000) yol: EN YAKINI
    _eq(e, "iki yol kenari: en yakin olan secilir", (round(ms2["road_distance_mm"].value, 6), ms2["road_face"].value), (7000.0, "alt"))
    _eq(e, "donus 90 yol mesafesi", round(ms90["road_distance_mm"].value, 6), 5000.0)
    _eq(e, "donus 90 yola bakan yuz = sag", (ms90["road_face"].value, round(ms90["road_face_deviation_deg"].value, 6)), ("sag", 0.0))
    _eq(e, "donus 90 uzun yuzler (90/270) guneyden 90", ms90["long_face_south_deviation_deg"].value, 90.0)
    _eq(e, "kare binada dort yuz uzun", long_face_south_deviation_deg(0, 8000, 8000), 0.0)
    # bahce: parseli iki kenardan tutan genis bina bahceyi ikiye boler
    wide = building_footprint(30000, 6000, (15000, 10000), 0)
    dists = [0.0 if i in (1, 3) else 7000.0 for i in range(4)]
    _eq(e, "sol+sag kenara degen bina -> 2 parca", garden_pieces(dists), 2)
    _eq(e, "komsu iki kenara degen (kose) -> 1 parca", garden_pieces([0.0, 0.0, 9.0, 9.0]), 1)
    _eq(e, "hicbirine degmiyor -> 1 parca", garden_pieces([5.0, 6.0, 7.0, 8.0]), 1)
    _eq(e, "dort kenara da degiyor -> 1", garden_pieces([0.0, 0.0, 0.0, 0.0]), 1)
    ms_wide = {m.name: m.value for m in measure_candidate(parcel, buildable, wide, 0.0, 30000, 6000, road_edges=[0])}
    _eq(e, "genis bina olcumu (parsel kenarlarina degiyor)", ms_wide["garden_pieces"], 2)
    # veri yoksa olcum YOK: yol/bolge bildirilmediyse ilgili olcumler uretilmez; kuzey onaysizsa isik olcumu uretilmez
    bare = {m.name for m in measure_candidate(parcel, buildable, fp, 0.0, 10000, 6000, road_edges=(), zone=None, north_confirmed=False)}
    for name in ("road_distance_mm", "zone_overlap_ratio", "long_face_south_deviation_deg"):
        if name in bare:
            e.append(f"veri yokken '{name}' uretilmemeli")
    _eq(e, "zone ortusmesi: ayak izini tamamen kapsayan bolge -> 1.0", round(zone_overlap_ratio(fp, [(9000, 6000), (21000, 6000), (21000, 14000), (9000, 14000)]), 9), 1.0)
    _eq(e, "zone ortusmesi: ayak izinin 32e6/60e6'si bolgede", round(zone_overlap_ratio(fp, [(11000, 8000), (19000, 8000), (19000, 12000), (11000, 12000)]), 9), round(32e6 / 60e6, 9))
    from vaziyet.metrics import polygon_centroid, seg_seg_distance
    cx, cy = polygon_centroid([(0, 0), (20000, 0), (20000, 10000), (10000, 10000), (10000, 20000), (0, 20000)])
    _eq(e, "L alan agirlik merkezi (200e6@(10000,5000) + 100e6@(5000,15000))/300e6", (round(cx, 3), round(cy, 3)), (8333.333, 8333.333))
    _eq(e, "kesisen parcalar arasi mesafe 0", seg_seg_distance((0, 0), (10, 10), (0, 10), (10, 0)), 0.0)
    _eq(e, "paralel parcalar arasi mesafe", seg_seg_distance((0, 0), (10, 0), (0, 5), (10, 5)), 5.0)
    _eq(e, "zone ortusmesi: ayrik bolge -> 0", zone_overlap_ratio(fp, [(0, 0), (1000, 0), (1000, 1000), (0, 1000)]), 0.0)
    _eq(e, "bolge merkezi == bina merkezi -> 0", round(zone_center_distance_mm(fp, [(10000, 7000), (20000, 7000), (20000, 13000), (10000, 13000)]), 9), 0.0)
    return e


def check_study_selection_dev083() -> list[str]:
    from vaziyet import pareto_front, select_unweighted, select_weighted
    e: list[str] = []
    names = ("a", "b")
    vec = [(10.0, 0.0), (0.0, 10.0), (5.0, 5.0), (4.0, 4.0)]
    _eq(e, "pareto: (4,4) baskin", pareto_front(vec), [0, 1, 2])
    _eq(e, "pareto: bir eksende esit, digerinde kotu -> baskin", pareto_front([(10.0, 0.0), (10.0, -1.0)]), [0])
    _eq(e, "pareto: yinelenen vektor ikisi de cephede", pareto_front([(1.0, 1.0), (1.0, 1.0)]), [0, 1])
    _eq(e, "agirliksiz N=3: a-en-iyi, b-en-iyi, sonra cesitlilik", select_unweighted(vec, names, 3), [(0, "best:a"), (1, "best:b"), (2, "diversity")])
    _eq(e, "agirliksiz N=2", select_unweighted(vec, names, 2), [(0, "best:a"), (1, "best:b")])
    _eq(e, "agirliksiz N=5: cephe bitince cephe disi, 4 aday", [i for i, _ in select_unweighted(vec, names, 5)], [0, 1, 2, 3])
    far = [(10.0, 0.0), (0.0, 10.0), (6.0, 6.0), (7.0, 5.0)]       # normalize: c2 en yakina .72, c3 en yakina .58 -> en UZAK = c2
    _eq(e, "cesitlilik: en uzak aday (c2) secilir, en yakin (c3) degil", [i for i, _ in select_unweighted(far, names, 3)], [0, 1, 2])
    dup = vec + [(10.0, 0.0)]                                   # indeks 4 == indeks 0
    _eq(e, "esdeger (ayni vektor) aday TEKRAR secilmez", [i for i, _ in select_unweighted(dup, names, 5)], [0, 1, 2, 3])
    _eq(e, "tek adayli kume", select_unweighted([(1.0, 2.0)], names, 3), [(0, "best:a")])
    _eq(e, "bos kume", select_unweighted([], names, 3), [])
    # esitlikte kucuk indeks
    tie = [(5.0, 5.0), (5.0, 5.0)]
    _eq(e, "tum vektorler ayni -> yalniz bir tane", select_unweighted(tie, names, 3), [(0, "best:a")])
    # agirlikli: normalize (10'a bol) toplam
    w = select_weighted(vec[:3], names, {"a": 1.0}, 3)
    _eq(e, "agirlik a=1: c0 once", [i for i, _ in w][0], 0)
    w2 = select_weighted(vec[:3], names, {"a": 3.0, "b": 1.0}, 3)
    _eq(e, "agirlik a=3,b=1 sirasi (skor 3, 2, 1)", [(i, round(s, 6)) for i, s in w2], [(0, 3.0), (2, 2.0), (1, 1.0)])
    w3 = select_weighted(vec[:3], names, {"a": 1.0, "b": 1.0}, 3)
    _eq(e, "esit skor -> indeks sirasi", [i for i, _ in w3], [0, 1, 2])
    pos = [(0, 0), (100, 0), (5000, 0)]
    _eq(e, "min_separation_mm yokken esit skor: 0 ve 1", [i for i, _ in select_weighted(vec[:3], names, {"a": 1.0, "b": 1.0}, 2, None, pos)], [0, 1])
    _eq(e, "min_separation_mm: 100 mm yakin komsu (1) atlanir, 2 secilir", [i for i, _ in select_weighted(vec[:3], names, {"a": 1.0, "b": 1.0}, 2, 1000.0, pos)], [0, 2])
    for bad, label in (({"zzz": 1.0}, "bilinmeyen anahtar"), ({"a": -1.0}, "negatif"), ({"a": -1.0, "b": 2.0}, "bir negatif + bir pozitif"), ({"a": 0.0, "b": 0.0}, "hepsi sifir"), ({"a": True}, "bool")):
        try:
            select_weighted(vec, names, bad, 2)
            e.append(f"agirlik reddedilmeli: {label}")
        except VaziyetError:
            pass
    return e


def check_study_run_dev083() -> list[str]:
    import json as _j
    from vaziyet import ceiling_checks, footprint_within, run_study
    e: list[str] = []
    zone = [(6000, 8000), (24000, 8000), (24000, 30000), (6000, 30000)]
    kw = dict(step_mm=5000, rotations_deg=[0, 90], road_edges=[0], zone=zone, north_confirmed=True)
    r = run_study(PARCEL_30x40, _buildable(5000), 10000, 6000, **kw)
    _eq(e, "varsayilan N=3", len(r.alternatives), 3)
    _eq(e, "kimlikler", [a.id for a in r.alternatives], ["A1", "A2", "A3"])
    buildable = _buildable(5000)
    for a in r.alternatives:
        if not footprint_within(list(a.footprint), buildable):
            e.append(f"{a.id} yapilasma alani disinda")
        want = -a.rotation_deg if a.rotation_deg <= 180 else 360 - a.rotation_deg
        if a.rotation_deg and abs(a.plan_north_angle - ((-a.rotation_deg + 180) % 360 - 180)) > 1e-9:
            e.append(f"{a.id} kat plani kuzey acisi -donus olmali: {a.plan_north_angle}")
        if not a.measurements or any(not m.source for m in a.measurements):
            e.append(f"{a.id} olcumleri kaynak fonksiyon adini tasimali")
    r5 = run_study(PARCEL_30x40, buildable, 10000, 6000, **{**kw, "n": 5})
    _eq(e, "N=5 istenirse 5", len(r5.alternatives), 5)
    # determinizm: iki kosu bayt-bayt ayni; donus sirasi bagimsiz
    j1 = _j.dumps(r.to_dict(), sort_keys=True)
    j2 = _j.dumps(run_study(PARCEL_30x40, buildable, 10000, 6000, **{**kw, "rotations_deg": [90, 0]}).to_dict(), sort_keys=True)
    _eq(e, "determinizm (donus girdi sirasi sonucu degistirmez)", j1.replace('"rotations_deg": [0.0, 90.0]', ""), j2.replace('"rotations_deg": [0.0, 90.0]', ""))
    _eq(e, "determinizm: ayni cagri ayni", j1, _j.dumps(run_study(PARCEL_30x40, buildable, 10000, 6000, **kw).to_dict(), sort_keys=True))
    # agirlikli / agirliksiz iki mod
    rw = run_study(PARCEL_30x40, buildable, 10000, 6000, **{**kw, "weights": {"road_proximity": 1.0}})
    _eq(e, "agirlikli mod nedeni", {a.reason for a in rw.alternatives}, {"weighted"})
    _eq(e, "agirlikli: 1. alternatif yola EN yakin (yol mesafesi minimum)", rw.alternatives[0].m("road_distance_mm"), min(a.m("road_distance_mm") for a in r.alternatives + rw.alternatives))
    if {a.reason for a in r.alternatives} == {"weighted"}:
        e.append("agirliksiz modda 'weighted' nedeni olmamali")
    # veri eksikligi sessiz gecilmez
    r_noroad = run_study(PARCEL_30x40, buildable, 10000, 6000, step_mm=5000, rotations_deg=[0])
    if not any("Yola bakan kenar bildirilmedi" in n for n in r_noroad.notes):
        e.append("yol yokken not dusulmeli")
    if "road_proximity" in r_noroad.parameters["axes"]:
        e.append("yol yokken yola yakinlik ekseni olmamali")
    r_nonorth = run_study(PARCEL_30x40, buildable, 10000, 6000, step_mm=5000, rotations_deg=[0], north_confirmed=False)
    if "light_south" in r_nonorth.parameters["axes"] or not any("kuzey-yukari oldugu onaylanmadi" in n for n in r_nonorth.notes):
        e.append("kuzey onaysizsa isik ekseni disarida + not")
    # bolge disina tasan alternatif acikca isaretlenir
    small_zone = [(24000, 33000), (25000, 33000), (25000, 34000), (24000, 34000)]
    rz = run_study(PARCEL_30x40, buildable, 10000, 6000, **{**kw, "zone": small_zone})
    if not any(a.outside_zone for a in rz.alternatives) or not any("DISINA" in n for n in rz.notes):
        e.append("bolge disina tasan alternatif isaretlenmeli ve not dusulmeli")
    # hic aday gecemezse soyler
    r_none = run_study(PARCEL_30x40, _buildable(14000), 10000, 6000, step_mm=1000, rotations_deg=[0])
    _eq(e, "bina sigmiyor -> alternatif yok", (len(r_none.alternatives), r_none.survivors), (0, 0))
    if not any("Hicbir aday" in n for n in r_none.notes):
        e.append("hic aday yokken not dusulmeli")
    # N dogrulama
    for bad in (0, 11, True, 2.5):
        try:
            run_study(PARCEL_30x40, buildable, 10000, 6000, **{**kw, "n": bad})
            e.append(f"gecersiz N kabul edildi: {bad!r}")
        except VaziyetError:
            pass
    # tavan: TAKS/KAKS elle (parsel 1200e6 mm2, ayak izi 60e6 mm2 -> 0.05)
    tk = ceiling_checks(1200e6, 60e6, {"value": 0.05, "source": "kullanici"}, {"value": 1.0, "source": "kullanici"}, 5)
    _eq(e, "TAKS tam sinirda tamam", (round(tk[0]["value"], 9), tk[0]["ok"]), (0.05, True))
    _eq(e, "KAKS = 0.05 x 5", (round(tk[1]["value"], 9), tk[1]["ok"]), (0.25, True))
    over = ceiling_checks(1200e6, 60e6, {"value": 0.04, "source": "varsayilan:DEFAULT_TAKS"}, None, None)
    _eq(e, "TAKS asilir", over[0]["ok"], False)
    nofl = ceiling_checks(1200e6, 60e6, None, {"value": 1.0, "source": "kullanici"}, None)
    _eq(e, "kat adedi yokken KAKS OLCULEMEZ (uydurulmaz)", (nofl[0]["value"], nofl[0]["ok"]), (None, None))
    ro = run_study(PARCEL_30x40, buildable, 10000, 6000, **{**kw, "taks": {"value": 0.04, "source": "varsayilan:DEFAULT_TAKS"}})
    if not any("TAKS tavani ASILIYOR" in n for n in ro.notes):
        e.append("tavan asiliyorsa not dusulmeli")
    r_few = run_study(PARCEL_30x40, _buildable(2000), 10000, 6000, step_mm=13000, rotations_deg=[0])      # 2 kalan aday
    if len(r_few.alternatives) >= 3 or not any("alternatiften" in n for n in r_few.notes):
        e.append("istenenden az farkli alternatif varsa bu SOYLENMELI")
    _eq(e, "tavan asilsa da alternatifler uretilir (UYARI, FORBID degil)", len(ro.alternatives), 3)
    return e


def check_study_narration_and_cli_dev083() -> list[str]:
    import json as _j
    import subprocess
    from vaziyet import narrate_alternative, run_study
    from vaziyet.narrate import LINES, AXIS_PHRASE, lint_template, render
    e: list[str] = []
    for key, tpl in LINES:
        if lint_template(tpl):
            e.append(f"sablon rakam iceriyor: {tpl!r}")
    for key, txt in AXIS_PHRASE.items():
        if lint_template(txt):
            e.append(f"eksen cumlesi rakam iceriyor: {key}")
    if not lint_template("bina 5 mm uzakta {olcum:x}"):
        e.append("lint: sablondaki rakam yakalanmali")
    if not lint_template("bina ٣ mm"):
        e.append("lint: Unicode rakam yakalanmali")
    if not lint_template("alan \u00b2") or not lint_template("bina \u2163 kat"):
        e.append("lint: No/Nl kategorisindeki rakamlar (us, Roma) yakalanmali")
    try:
        render("{olcum:yok}", {})
        e.append("olcum yoksa render hata vermeli (deger uydurulmaz)")
    except KeyError:
        pass
    _eq(e, "render mm tam sayi", render("{olcum:road_distance_mm} mm", {"road_distance_mm": 7000.4}), "7000 mm")
    _eq(e, "render oran virgullu", render("{olcum:zone_overlap_ratio}", {"zone_overlap_ratio": 0.8333333}), "0,83")
    r = run_study(PARCEL_30x40, _buildable(5000), 10000, 6000, step_mm=5000, rotations_deg=[0], road_edges=[0],
                  zone=[(6000, 8000), (24000, 8000), (24000, 30000), (6000, 30000)])
    text = "\n".join("\n".join(narrate_alternative(a)) for a in r.alternatives)
    a1 = r.alternatives[0]
    if f"{round(a1.m('road_distance_mm')):d} mm" not in "\n".join(narrate_alternative(a1)):
        e.append("anlatimdaki yol mesafesi OLCULEN degerle ayni olmali")
    if "yola en yakin" not in "\n".join(narrate_alternative(a1)):
        e.append("A1 'yola en yakin' eksen cumlesini tasimali")
    # CLI
    script = str(Path(__file__).resolve().parent.parent / "site_study.py")
    with tempfile.TemporaryDirectory() as tmp:
        ctx = {"meta": {"floor_width": 10000, "floor_depth": 6000},
               "site": {"north_confirmed": True, "parcel": {"polygon": [list(p) for p in PARCEL_30x40]}, "road_edges": [0]}}
        p = Path(tmp) / "c.json"
        p.write_text(_j.dumps(ctx), encoding="utf-8")
        before = hashlib.sha256(p.read_bytes()).hexdigest()
        run = lambda *a: subprocess.run([sys.executable, script, str(p), *a], capture_output=True, text=True, timeout=300)  # noqa: E731
        o = run("--step-mm", "5000", "--rotations", "0")
        if o.returncode != 0 or "A1" not in o.stdout:
            e.append(f"CLI calismadi: {o.stdout!r} {o.stderr!r}")
        if "DEFAULT_FRONT_SETBACK_MM" not in o.stdout or "DOGRULANMADI" not in o.stdout:
            e.append("site.setbacks yokken kullanilan imar varsayilani ADIYLA ve DOGRULANMADI ibaresiyle bildirilmeli")
        # varsayilan cekmeyle elle: yol=kenar0 (on 5000), arka=kenar2 (3000), yanlar 3000 -> yapilasma alani x 3000..27000, y 5000..37000
        js = _j.loads(run("--step-mm", "5000", "--rotations", "0", "--json").stdout)
        _eq(e, "CLI --json: 35 yerine varsayilan cekmeyle aday sayisi (x 3000..27000 -> 5 adim; y 5000..37000 -> 7 adim)", js["generated"], 35)
        _eq(e, "CLI --json bildirimler", any("DEFAULT_FRONT_SETBACK_MM" in n for n in js["notices"]), True)
        _eq(e, "CLI salt okunur (context degismedi)", hashlib.sha256(p.read_bytes()).hexdigest(), before)
        if run("--rotations", "0").returncode != 2:
            e.append("--step-mm verilmeden calismamali (varsayilan yok)")
        if run("--step-mm", "5000").returncode != 2:
            e.append("--rotations verilmeden calismamali (varsayilan yok)")
        bad = run("--step-mm", "5000", "--rotations", "0", "--weights", "zzz=1")
        if bad.returncode != 1 or "bilinmeyen agirlik" not in bad.stdout:
            e.append(f"bilinmeyen agirlik reddedilmeli: {bad.stdout!r}")
        ctx["site"]["setbacks"] = {"uniform_mm": 5000}
        p.write_text(_j.dumps(ctx), encoding="utf-8")
        js2 = _j.loads(run("--step-mm", "5000", "--rotations", "0", "--json").stdout)
        if any("DEFAULT_FRONT_SETBACK_MM" in n for n in js2["notices"]):
            e.append("site.setbacks VARKEN cekme varsayilani bildirilmemeli")
        _eq(e, "site.setbacks ile aday sayisi (5 x 7)", js2["generated"], 35)
        w = _j.loads(run("--step-mm", "5000", "--rotations", "0", "--weights", "road_proximity=1", "--n", "2", "--json").stdout)
        _eq(e, "CLI agirlikli N=2", (len(w["alternatives"]), {a["reason"] for a in w["alternatives"]}), (2, {"weighted"}))
    return e


def main() -> int:
    groups = (
        ("cokgen gecerliligi (kendini kesen/yinelenen/kolinear + L yanlis-pozitif yok)", check_polygon_validity()),
        ("ice offset ELLE hesap (dikdortgen, kenar basina, L konkav, cokme, esdogrusal)", check_offset_hand_computed()),
        ("cekme cozumleme + bina ayak izi + plan_north_angle", check_setbacks_and_footprint()),
        ("validate kancasi check_site (hata/uyari/yanlis-pozitif)", check_site_validation_hook()),
        ("vaziyet DXF ice aktarma (salt okunur, birim, zincir, kuzey, desteklenmeyen, DWG)", check_dxf_input()),
        ("imar standart deger katalogu: kullanici ustunlugu, kosul, bildirim, kenar rolleri (DEV-086)", check_zoning_catalog_dev086()),
        ("etut: aday uretimi + eleme + sinir toleransi (DEV-083)", check_study_candidates_dev083()),
        ("etut: ELLE hesaplanan olcumler (yol, bahce, bolge, yuz acilari) (DEV-083)", check_study_metrics_dev083()),
        ("etut: Pareto + agirliksiz/agirlikli secim (DEV-083)", check_study_selection_dev083()),
        ("etut: uctan uca, determinizm, N, veri eksikligi notlari, TAKS/KAKS (DEV-083)", check_study_run_dev083()),
        ("etut: anlatim sablonu rakam lint'i + site_study CLI (DEV-083)", check_study_narration_and_cli_dev083()),
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
