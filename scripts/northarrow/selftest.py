#!/usr/bin/env python3
"""Kuzey oku testleri (DEV-025).

rev-18: bu modulun ayni revizyonda tanittigi `pafta::ScaleBar` (grafik
olcek cubugu) kullanici geri bildirimiyle KALDIRILDI (bkz.
DEVELOPMENT_HISTORY.md HD-012); bu dosya artik SADECE kuzey okunu sinar.

Kullanim:
    python scripts/northarrow/selftest.py
Cikis kodu: 0 basarili, 1 basarisiz.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import ezdxf  # noqa: E402

from northarrow import DefaultNorthArrowStyle, NorthArrow, rotate_point  # noqa: E402

TOLERANCE = 1e-6


def check_rotate_point_hand_computable() -> list[str]:
    """Saat yonu konvansiyonu (0=yukari, 90=sag): elle dogrulanabilir 4
    kardinal nokta + bir ara aci (30 derece)."""
    errors: list[str] = []
    cases = [
        (0.0, (0.0, 10.0)),
        (90.0, (10.0, 0.0)),
        (180.0, (0.0, -10.0)),
        (270.0, (-10.0, 0.0)),
    ]
    for angle, expected in cases:
        got = rotate_point((0.0, 0.0), 10.0, angle)
        if abs(got[0] - expected[0]) > 1e-3 or abs(got[1] - expected[1]) > 1e-3:
            errors.append(f"angle={angle}: {expected} bekleniyordu, {got} bulundu.")
    return errors


def check_north_arrow_scales_with_denominator() -> list[str]:
    """Yaricap, `to_modelspace` ile OLCEGE dogrusal turer: 1:100'deki
    yaricap, 1:50'dekinin TAM 2 katı olmalidir (elle hesaplanabilir)."""
    errors: list[str] = []
    a50 = NorthArrow("1:50")
    a100 = NorthArrow("1:100")
    if abs(a100.radius - 2 * a50.radius) > TOLERANCE:
        errors.append(f"1:100 yaricapi 1:50'nin 2 katı olmali: {a50.radius} vs {a100.radius}.")
    return errors


def check_north_arrow_draws_expected_entities() -> list[str]:
    """Varsayilan stil: 1 daire + 1 ucgen (ibre) + 1 metin = 3 varlik."""
    errors: list[str] = []
    doc = ezdxf.new()
    doc.layers.add("CERCEVE")
    doc.layers.add("METIN")
    msp = doc.modelspace()
    arrow = NorthArrow("1:50")
    arrow.draw(msp, (0.0, 0.0), 45.0)
    if len(msp) != 3:
        errors.append(f"3 varlik (daire+ucgen+metin) bekleniyordu, {len(msp)} bulundu.")
    circles = list(msp.query("CIRCLE"))
    if len(circles) != 1 or abs(circles[0].dxf.radius - arrow.radius) > TOLERANCE:
        errors.append("daire yaricapi arrow.radius ile ESLESMIYOR.")
    return errors


def check_custom_style_is_injectable() -> list[str]:
    """`NorthArrowStyle` Protocol'u enjekte edilebilir olmali (kullanici
    talebi: 'entegrasyon zor olmasin') - sahte bir stil verilince NorthArrow
    KENDI cizim mantigini DEGIL, verilen stili cagirmalidir."""
    calls: list[tuple] = []

    class _FakeStyle:
        def draw(self, msp, center, radius, angle_deg, layer, text_layer, text_height) -> None:
            calls.append((center, radius, angle_deg))

    doc = ezdxf.new()
    msp = doc.modelspace()
    arrow = NorthArrow("1:50", style=_FakeStyle())
    arrow.draw(msp, (5.0, 5.0), 10.0)
    if calls != [((5.0, 5.0), arrow.radius, 10.0)]:
        return [f"enjekte edilen stil beklenen argumanlarla cagrilmadi: {calls}"]
    if len(msp) != 0:
        return ["sahte stil hicbir DXF varligi eklemedi ama modelspace BOS degil."]
    return []


def check_north_convention_dev074() -> list[str]:
    """DEV-074: |aci| <= 45 (esdeger acilar normalize); aralik disi HATA; veri yoksa sessiz (yon uydurulmaz)."""
    from northarrow import check_north_convention, normalize_north_angle
    errors: list[str] = []

    def eq(label, got, want):
        if got != want:
            errors.append(f"{label}: {got!r} != {want!r}")

    for a, want in ((0, 0), (45, 45), (-45, -45), (350, -10), (-350, 10), (360, 0), (405, 45), (180, 180), (-180, 180), (225, -135)):
        eq(f"normalize({a})", normalize_north_angle(a), float(want))
    eq("veri yok -> hata yok", check_north_convention({}), [])
    for ok in (0, 25, 45, -45, 350, 315, 359.99, 405):
        eq(f"gecerli {ok}", check_north_convention({"north_angle": ok}), [])
    for bad in (45.01, -45.01, 46, 90, -90, 135, 180, 190, 225, 270, 314.99):
        got = check_north_convention({"north_angle": bad})
        if len(got) != 1 or "sessizce dondurulmez" not in got[0]:
            errors.append(f"gecersiz {bad} tek hata vermeli: {got}")
    eq("hata ham degeri soyler", "meta.north_angle=190" in check_north_convention({"north_angle": 190})[0], True)
    return errors


def check_north_convention_dev081() -> list[str]:
    """DEV-081: uzun kenar yatay + kuzeye yakin uzun yuz ustte => dikdortgen binada |aci| <= 90; tam kare <= 45; olcu bilinmiyorsa muhafazakar 45."""
    from northarrow import check_north_convention, check_north_layout, north_half_range
    errors: list[str] = []

    def eq(label, got, want):
        if got != want:
            errors.append(f"{label}: {got!r} != {want!r}")

    rect = {"floor_width": 20000.0, "floor_depth": 17500.0}
    sq = {"floor_width": 9000.0, "floor_depth": 9000.0}
    eq("aralik dikdortgen", north_half_range(rect), 90.0)
    eq("aralik kare", north_half_range(sq), 45.0)
    eq("aralik olcu yok", north_half_range({}), 45.0)
    eq("aralik sifir olcu", north_half_range({"floor_width": 0, "floor_depth": 10}), 45.0)
    eq("aralik bool olcu", north_half_range({"floor_width": True, "floor_depth": 2}), 45.0)
    eq("aralik uzun dikey (depth>width) da dikdortgen", north_half_range({"floor_width": 10.0, "floor_depth": 20.0}), 90.0)
    for ok in (0, 30, -30, 60, 89.99, 90, -90, 270, 350, 450):
        eq(f"dikdortgen gecerli {ok}", check_north_convention({**rect, "north_angle": ok}), [])
    for bad in (90.01, -90.01, 91, 135, 180, 190, 269.99):
        got = check_north_convention({**rect, "north_angle": bad})
        if len(got) != 1 or "sessizce dondurulmez" not in got[0] or "-90..+90" not in got[0]:
            errors.append(f"dikdortgen gecersiz {bad} tek hata ve -90..+90 yazmali: {got}")
    for ok in (0, 45, -45):
        eq(f"kare gecerli {ok}", check_north_convention({**sq, "north_angle": ok}), [])
    for bad in (45.01, -45.01, 60, 90):
        got = check_north_convention({**sq, "north_angle": bad})
        if len(got) != 1 or "-45..+45" not in got[0]:
            errors.append(f"kare gecersiz {bad} tek hata ve -45..+45 yazmali: {got}")
    eq("olcu yokken 60 hata (muhafazakar)", len(check_north_convention({"north_angle": 60})), 1)
    # paftalama uyarisi (yalniz north_angle verilmisse)
    eq("north_angle yok -> uyari yok", check_north_layout({"floor_width": 10.0, "floor_depth": 20.0}), [])
    eq("uzun kenar yatay -> uyari yok", check_north_layout({**rect, "north_angle": 0}), [])
    eq("kare -> uyari yok", check_north_layout({**sq, "north_angle": 0}), [])
    got = check_north_layout({"floor_width": 10000.0, "floor_depth": 12000.0, "north_angle": 0})
    if len(got) != 1 or "sessizce dondurulmez" not in got[0]:
        errors.append(f"uzun kenar dikeyse tek uyari: {got}")
    eq("olcu yok -> uyari yok", check_north_layout({"north_angle": 0}), [])
    return errors


def check_corner_placement_dev081() -> list[str]:
    """DEV-081: ok pafta IC cizgisinin sag-ust kosesinde. Elle hesap + uretilen DXF'te bagimsiz dogrulama."""
    from pafta import Sheet, to_modelspace, parse_scale_denominator
    errors: list[str] = []

    def eq(label, got, want):
        if got != want:
            errors.append(f"{label}: {got!r} != {want!r}")

    sheet = Sheet("1:50", 350.0, [], [(0.0, 10000.0)])
    # pads = 4000 + 150; frame_y = -4150 .. 14150; ic cizgi = dis cizgiden 150 iceride
    eq("inner_bounds", sheet.inner_bounds(1000.0, 5000.0, 0.0, 10000.0), (-3000.0, -4000.0, 10000.0, 14000.0))
    eq("inner_bounds icerik daha yuksekse dis aralik buyur", sheet.inner_bounds(0.0, 100.0, 0.0, 20000.0)[3], 20000.0 + 4150.0 - 150.0)
    arrow = NorthArrow("1:50")
    eq("extent = r*(1+0.45) + etiket", round(arrow.extent, 6), round(300.0 * 1.45 + 150.0, 6))
    cx, cy = arrow.corner_center(10000.0, 14000.0, 500.0)
    eq("merkez (marj 500)", (round(cx, 6), round(cy, 6)), (round(10000.0 - 500.0 - arrow.extent, 6), round(14000.0 - 500.0 - arrow.extent, 6)))
    # uretilen DXF: kesit_ornek (north_angle=25) - her kat paftasinda ok, KENDI ic cizgisinin sag-ust kosesinde ve baska ogeye binmiyor
    import json
    import tempfile
    import generate_dxf
    from ezdxf import bbox as ezbbox
    root = Path(__file__).resolve().parent.parent.parent
    ctx_path = root / "golden" / "kesit_ornek" / "context.json"
    meta = json.loads(ctx_path.read_text(encoding="utf-8"))["meta"]
    scale = meta["scale"]
    margin = to_modelspace(10.0, parse_scale_denominator(scale))
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "k.dxf"
        generate_dxf.generate(ctx_path, out)
        msp = ezdxf.readfile(out).modelspace()
    frames = []
    for e in msp:
        if e.dxftype() == "LWPOLYLINE" and e.dxf.layer == "CERCEVE":
            xs = [p[0] for p in e.get_points("xy")]
            ys = [p[1] for p in e.get_points("xy")]
            if len(xs) == 4:                                                              # cerceveler (ibre ucgeni 3 noktali)
                frames.append((min(xs), min(ys), max(xs), max(ys)))
    arrows = [e for e in msp if e.dxftype() == "CIRCLE" and e.dxf.layer == "CERCEVE" and abs(e.dxf.radius - arrow.radius) < 1e-6]
    if not arrows:
        errors.append("uretilen DXF'te kuzey oku dairesi yok")
    for c in arrows:
        x, y = c.dxf.center.x, c.dxf.center.y
        inside = [f for f in frames if f[0] < x < f[2] and f[1] < y < f[3]]
        inner = min(inside, key=lambda f: (f[2] - f[0]) * (f[3] - f[1]))      # ok'u iceren EN KUCUK cerceve = ic cizgi
        want = (inner[2] - margin - arrow.extent, inner[3] - margin - arrow.extent)
        if abs(x - want[0]) > 1e-6 or abs(y - want[1]) > 1e-6:
            errors.append(f"ok sag-ust kosede degil: merkez ({x:.1f},{y:.1f}) != ({want[0]:.1f},{want[1]:.1f})")
        box = (x - arrow.extent, y - arrow.extent, x + arrow.extent, y + arrow.extent)
        if box[2] > inner[2] or box[3] > inner[3]:
            errors.append("ok ic cizgiden tasiyor")
        for e in msp:
            if e.dxftype() in ("CIRCLE", "LWPOLYLINE", "TEXT") and e.dxf.layer in ("CERCEVE", "METIN") and abs(getattr(e.dxf, "radius", 0) - arrow.radius) < 1e-6:
                continue
            if e.dxftype() == "LWPOLYLINE" and e.dxf.layer == "CERCEVE":
                continue                                                                  # cerceve/antet cizgileri
            ext = ezbbox.extents([e])
            if not ext.has_data:
                continue
            if ext.extmin.x < box[2] and ext.extmax.x > box[0] and ext.extmin.y < box[3] and ext.extmax.y > box[1]:
                if e.dxftype() == "TEXT" and e.dxf.text == "K":
                    continue
                if e.dxftype() == "LWPOLYLINE" and e.is_closed and len(e) == 3:           # ibre ucgeni
                    continue
                errors.append(f"ok baska bir ogeye biniyor: {e.dxftype()} {e.dxf.layer}")
                break
    return errors


def main() -> int:
    groups = (
        ("kuzey sozlesmesi [-45, +45] (DEV-074)", check_north_convention_dev074()),
        ("dikdortgen binada [-90, +90], kare [-45, +45], paftalama uyarisi (DEV-081)", check_north_convention_dev081()),
        ("ok pafta ic cizgisinin sag-ust kosesinde (DEV-081)", check_corner_placement_dev081()),
        ("rotate_point (saat yonu, 4 kardinal nokta)", check_rotate_point_hand_computable()),
        ("NorthArrow yaricapi olcekle dogrusal turer", check_north_arrow_scales_with_denominator()),
        ("NorthArrow varsayilan varlik sayisi", check_north_arrow_draws_expected_entities()),
        ("ozel stil enjekte edilebilir (Protocol)", check_custom_style_is_injectable()),
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
        print("\nKUZEY OKU SELF-TEST BASARISIZ.")
        return 1
    print("\nKuzey oku self-test BASARILI.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
