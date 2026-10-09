#!/usr/bin/env python3
"""reasoning cekirdegi testleri (DEV-060).

Disiplin (kok CLAUDE.md): beklenen degerler ELLE hesaplanabilir, her kapi KASITLI bozmayla sinanir ve
her testin YANLIS-POZITIF tarafi vardir. NOT: uretim kaydinda bilgi YOKTUR, bu yuzden dogrulama kapilari
gercek kayitta bos kosar ve bu KANIT DEGILDIR - kapilar burada ENJEKTE EDILEN bozuk sahte kayitlarla sinanir.

Kullanim:  python scripts/reasoning/selftest.py     Cikis: 0 basarili, 1 basarisiz.
"""
from __future__ import annotations

import datetime
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import doc_check as dc  # noqa: E402
from reasoning import (CheckAdapter, Facet, Finding, Lens, Plain, Provenance, Registry, Thresholds,  # noqa: E402
                       adapt_warnings, build_coverage, diff_findings, group_across_floors, make_key,
                       message_signature, parse_validate_output, run_case, severity_band,
                       severity_from_curve, trigger_report, validate_registry)
from reasoning.registry import REASONING_EXEMPT, REASONING_PENDING, REASONING_PROVIDERS  # noqa: E402


def prov(conf="yaygin", src="mimari literatur"):
    return Provenance(kind="mimari_pratik", confidence=conf, source=src, reviewed="2026-10-09")


def idea(fid="mahremiyet.gorsel.deneme", **kw):
    base = dict(id=fid, lens=fid.split(".")[0], title_tr="t", principle_tr="p", why_tr="w")
    base.update(kw)
    return Facet(**base)


def reg_with(*facets, lens="mahremiyet"):
    r = Registry()
    r.register_lens(Lens(lens, "Mahremiyet", "felsefe"))
    for f in facets:
        r.register_facet(f)
    return r


def check_keys_and_signature() -> list[str]:
    e = []
    a = "Birim 'uC': hol payi %16.3 asildi (hol=10.1 m2)"
    b = "Birim 'uC': hol payi %14.9 asildi (hol=9.2 m2)"  # yalniz rakamlar farkli: AYNI kok neden
    c = "Birim 'uC': hol ucu cikmaz"                      # mesaj TURU farkli
    if message_signature(a) != message_signature(b):
        e.append("rakam degisikligi anahtari bozmamali (kismi cozum 'cozuldu' gorunmemeli)")
    if message_signature(a) == message_signature(c):
        e.append("farkli mesaj turu ayni imza almamali (yanlis-pozitif)")
    if message_signature("[normal1] " + a) != message_signature("[normal2] " + a):
        e.append("kat oneki imzaya girmemeli")
    k1 = make_key("legacy.mimari", "normal1", ("uC",), a)
    k2 = make_key("legacy.mimari", "normal2", ("uC",), a)
    f1 = Finding(k1, "legacy.mimari", "normal1", a, ("uC",))
    f2 = Finding(k2, "legacy.mimari", "normal2", a, ("uC",))
    if k1 == k2 or f1.group_key != f2.group_key:
        e.append("ozdes katlar: anahtar farkli, group_key AYNI olmali")
    if len(group_across_floors([f1, f2])) != 1:
        e.append("ozdes katlardaki ayni bulgu TEK konu olmali")
    f3 = Finding(make_key("legacy.mimari", "normal1", ("uA",), a), "legacy.mimari", "normal1", a, ("uA",))
    if len(group_across_floors([f1, f3])) != 2:
        e.append("farkli eleman = farkli konu (yanlis-pozitif)")
    return e


def check_severity_curve() -> list[str]:
    e = []
    th = Thresholds(warn_at=45.0, severe_at=15.0, unit="derece", source="x")  # dusuk deger daha kotu
    if severity_from_curve(45.0, th) != (0.0, "curve"):
        e.append("esikte siddet 0")
    s, _ = severity_from_curve(30.0, th)
    if abs(s - 0.5) > 1e-12:
        e.append(f"orta nokta siddeti 0.5 olmali, {s}")
    if severity_from_curve(0.0, th)[0] != 1.0 or severity_from_curve(90.0, th)[0] != 0.0:
        e.append("ramp 0..1'e kenetlenmeli")
    if severity_from_curve(30.0, Thresholds(warn_at=45.0)) != (None, "unscored"):
        e.append("severe_at yoksa siddet UYDURULMAMALI (None/unscored)")
    if severity_from_curve(30.0, None) != (None, "unscored"):
        e.append("esik yoksa siddet None")
    if [severity_band(x) for x in (None, 0.1, 0.25, 0.6, 0.61)] != ["olculmedi", "bilgi", "dikkat", "dikkat", "ciddi"]:
        e.append("anlatim bantlari: <0.25 bilgi, <=0.6 dikkat, >0.6 ciddi, None olculmedi")
    return e


def check_diff() -> list[str]:
    e = []
    a = Finding("k|*|x|1", "f", None, "m")
    b = Finding("k|*|y|2", "f", None, "m")
    c = Finding("k|*|z|3", "f", None, "m")
    d = diff_findings([a, b], [b, c])
    if [f.key for f in d["new"]] != [c.key] or [f.key for f in d["resolved"]] != [a.key] or [f.key for f in d["unchanged"]] != [b.key]:
        e.append("regresyon farki: yeni=c, cozulen=a, degismeyen=b olmali")
    same = diff_findings([a], [a])
    if same["new"] or same["resolved"]:
        e.append("ayni kume: yeni/cozulen bos olmali (yanlis-pozitif)")
    return e


SAMPLE = """UYARI (sartname): [normal1] Oda 'uB_salon' (Salon): yerel en dar nokta 2225mm asgari 3000mm altinda.
UYARI (sartname): [normal2] Oda 'uB_salon' (Salon): yerel en dar nokta 2225mm asgari 3000mm altinda.
UYARI (mimari): [normal1] Birim 'uC': hol payi %16.3 asildi.
UYARI (merdiven): Merdiven 'stair' icin uyari (etiketsiz)
DOGRULAMA BASARILI: 9 kat
bu satir UYARI degil
"""


def check_legacy_parse() -> list[str]:
    e = []
    fs = parse_validate_output(SAMPLE)
    if len(fs) != 4:
        e.append(f"4 UYARI satiri beklenirdi, {len(fs)}")
    if [f.facet_id for f in fs] != ["legacy.sartname", "legacy.sartname", "legacy.mimari", "legacy.merdiven"]:
        e.append("kategori -> legacy.<kategori>")
    if fs[3].floor_id is not None:
        e.append("etiketsiz satirda kat None olmali")
    if len(group_across_floors(fs)) != 3:
        e.append("4 satir -> 3 konu (iki ozdes kat tek konu) olmali")
    if fs[0].elements != ("uB_salon",):
        e.append("tirnak icindeki eleman adi cikarilmali")
    if adapt_warnings("x.y.z", "K1", ["Oda 'a' sorunlu", "Oda 'b' sorunlu"])[1].elements != ("b",):
        e.append("adapt_warnings eleman cikarimi")
    return e


def check_real_validate_parity() -> list[str]:
    """rev-28 gercek context: 15 satir -> 3 konu (validate stdout'u ile pariteyi yapi geregi saglar)."""
    out = subprocess.run([sys.executable, str(ROOT / "scripts" / "validate.py"), str(ROOT / "context.json")],
                         capture_output=True, text=True, timeout=600).stdout
    n_lines = sum(1 for l in out.splitlines() if l.startswith("UYARI"))
    fs = parse_validate_output(out)
    e = []
    if len(fs) != n_lines:
        e.append(f"adaptor {len(fs)} bulgu uretti, validate {n_lines} UYARI satiri bastı (parite bozuk)")
    if n_lines and len(group_across_floors(fs)) >= n_lines:
        e.append("ozdes katlar kumelenmedi")
    return e


def check_registry_validation() -> list[str]:
    e = []
    if validate_registry(Registry()):
        e.append("bos kayit gecerli olmali")
    good = reg_with(idea())
    if validate_registry(good):
        e.append(f"gecerli idea veche hata verdi: {validate_registry(good)}")
    bad = {
        "kimlik bicimi": idea("yanlis_kimlik"),
        "mercek farkli": idea("baska.gorsel.x", lens="mahremiyet"),
        "draft provenance yok": idea(status="draft"),
        "shadow check yok": idea(status="shadow", provenance=prov(), needs=("rooms[].unit_id",)),
        "active plain yok": idea(status="active", provenance=prov(), needs=("rooms[].unit_id",), check_ref="a:b"),
        "legacy ama shadow": idea(status="shadow", provenance=prov(), needs=("a.b",), check_ref="a:b", legacy=True),
        "gerilim dangling": idea(tensions=("yok.yok.yok",)),
    }
    for name, facet in bad.items():
        if not validate_registry(reg_with(facet)):
            e.append(f"bozuk kayit YAKALANMADI: {name}")
    r = reg_with(idea())
    r.register_facet(idea())
    if not any("yinelenen" in x for x in validate_registry(r)):
        e.append("yinelenen veche kimligi YAKALANMADI")
    full = idea(status="active", provenance=prov(), needs=("rooms[].unit_id",), check_ref="a:b",
                plain=Plain("p", "c"), thresholds=Thresholds(45.0, 15.0, "derece", "k"), remedies=("r1",))
    from reasoning import Remedy
    rf = reg_with(full)
    if not any("cozum basvurusu" in x for x in validate_registry(rf)):
        e.append("kayitsiz cozum basvurusu YAKALANMADI")
    rf.register_remedy(Remedy("r1", "Kapıyı kaydırmak.", ""))
    if validate_registry(rf):
        e.append(f"tam active veche hata verdi (yanlis-pozitif): {validate_registry(rf)}")
    return e


def check_gate10_three_state() -> list[str]:
    e = []
    names = ["a", "b", "c"]
    tmp = Path(tempfile.mkdtemp())
    for n in names:
        (tmp / n).mkdir()
    frozen = frozenset(names)
    ok = dc.check_reasoning_coverage(providers=(), exempt={"a": "dusunuldu"}, pending=frozenset({"b", "c"}),
                                     packages=names, scripts_root=tmp, frozen=frozen)
    if ok:
        e.append(f"gecerli uc durumlu kayit hata verdi: {ok}")
    cases = {
        "hicbir yerde yok": dict(exempt={"a": "x"}, pending=frozenset({"b"})),
        "iki yerde": dict(exempt={"a": "x", "b": "x"}, pending=frozenset({"b", "c"})),
        "bos gerekce": dict(exempt={"a": " ", "b": "x"}, pending=frozenset({"c"})),
        "donuk disi PENDING": dict(exempt={"a": "x", "b": "x"}, pending=frozenset({"c", "yeni"}), frozen=frozenset(names)),
        "bayat kayit": dict(exempt={"a": "x", "b": "x", "hayalet": "x"}, pending=frozenset({"c"})),
    }
    for name, kw in cases.items():
        kw.setdefault("frozen", frozen)
        errs = dc.check_reasoning_coverage(providers=(), packages=names, scripts_root=tmp, **kw)
        if not errs:
            e.append(f"kapi #10 YAKALAMADI: {name}")
    (tmp / "a" / "reasoning.py").write_text("def register(reg): pass\n")
    if not dc.check_reasoning_coverage(providers=(), exempt={"a": "x", "b": "x"}, pending=frozenset({"c"}),
                                       packages=names, scripts_root=tmp, frozen=frozen):
        e.append("reasoning.py var ama PROVIDERS'te yok -> HATA olmali")
    if dc.check_reasoning_coverage(providers=("a.reasoning",), exempt={"b": "x"}, pending=frozenset({"c"}),
                                   packages=names, scripts_root=tmp, frozen=frozen):
        e.append("gecerli saglayici hata verdi (yanlis-pozitif)")
    if not dc.check_reasoning_coverage(providers=("c.reasoning",), exempt={"a": "x", "b": "x"}, pending=frozenset(),
                                       packages=names, scripts_root=tmp, frozen=frozen):
        e.append("PROVIDERS'te listeli ama dosyasi olmayan paket HATA olmali")
    # uretim kaydi: bugun temiz olmali ve her paket tam bir yerde
    if dc.check_reasoning_coverage():
        e.append(f"URETIM kaydi kirmizi: {dc.check_reasoning_coverage()}")
    if set(REASONING_PENDING) - dc._PENDING_FROZEN:
        e.append("uretim PENDING kumesi donuk kumenin disina cikmis")
    if tuple(REASONING_PROVIDERS) != ("architect",):
        e.append(f"DEV-061 sonrasi tek saglayici 'architect' beklenir: {REASONING_PROVIDERS}")
    if "architect" in REASONING_PENDING or "architect" in dc._PENDING_FROZEN:
        e.append("architect saglayici oldu: PENDING ve donuk listeden CIKMALI (kume yalniz kuculur)")
    return e


def check_gate11_refs() -> list[str]:
    e = []
    tmp = Path(tempfile.mkdtemp())
    (tmp / "mod").mkdir()
    (tmp / "mod" / "rules.py").write_text("def check_x(rooms, walls, openings):\n    return []\nTHRESH = 1\n")
    base = dict(status="shadow", provenance=prov(), needs=("rooms[].unit_id",))
    good = reg_with(idea(check_ref="mod.rules:check_x", adapter=CheckAdapter("mod.rules:check_x", ("rooms", "walls")), **base))
    if dc.check_reasoning_refs(good, tmp):
        e.append(f"cozulen basvuru hata verdi: {dc.check_reasoning_refs(good, tmp)}")
    for name, facet in {
        "sembol yok": idea(check_ref="mod.rules:check_yok", **base),
        "dosya yok": idea(check_ref="mod.yokdosya:check_x", **base),
        "parametre uyusmuyor": idea(check_ref="mod.rules:check_x", adapter=CheckAdapter("mod.rules:check_x", ("walls", "rooms")), **base),
    }.items():
        if not dc.check_reasoning_refs(reg_with(facet), tmp):
            e.append(f"kapi #11 YAKALAMADI: {name}")
    draft_dangling = reg_with(idea(status="draft", provenance=prov(), needs=("x.y",), check_ref="mod.rules:yok"))
    if dc.check_reasoning_refs(draft_dangling, tmp):
        e.append("draft/idea veche icin cozulmeyen basvuru HATA OLMAMALI (yanlis-pozitif)")
    return e


def check_gate12_cases() -> list[str]:
    e = []
    tmp = Path(tempfile.mkdtemp())
    for name, role in (("v_ihlal", "ihlal"), ("v_temiz", "temiz")):
        d = tmp / name
        d.mkdir()
        (d / "case.json").write_text(json.dumps({"id": name, "facet": "x", "role": role, "origin": "elle", "floor": {}}))
        (d / "expected_findings.json").write_text(json.dumps({"expect_keys": ["k"] if role == "ihlal" else []}))
    base = dict(status="shadow", provenance=prov(), needs=("a.b",), check_ref="a:b")
    if dc.check_reasoning_cases(reg_with(idea(cases=("v_ihlal", "v_temiz"), **base)), tmp):
        e.append("iki rolde vaka olan veche hata verdi (yanlis-pozitif)")
    for name, cases in {"yalniz ihlal": ("v_ihlal",), "yalniz temiz": ("v_temiz",), "vaka yok": (), "diskte yok": ("v_ihlal", "hayalet")}.items():
        if not dc.check_reasoning_cases(reg_with(idea(cases=cases, **base)), tmp):
            e.append(f"kapi #12 YAKALAMADI: {name}")
    if dc.check_reasoning_cases(reg_with(idea(status="draft", provenance=prov(), needs=("a.b",))), tmp):
        e.append("draft veche vaka istememeli")
    return e


def check_case_runner() -> list[str]:
    e = []
    tmp = Path(tempfile.mkdtemp())

    def mk(name, role, keys, absent=()):
        d = tmp / name
        d.mkdir()
        (d / "case.json").write_text(json.dumps({"id": name, "facet": "x", "role": role, "origin": "elle",
                                                 "floor": {"rooms": [{"id": "r"}]}}))
        (d / "expected_findings.json").write_text(json.dumps({"expect_keys": keys, "expect_absent": list(absent)}))
        return d

    def check(floor):  # toy kural: oda 'r' varsa bulgu
        return [Finding("toy|*|r|0", "toy.x.y", None, "m", ("r",))] if floor.get("rooms") else []

    if run_case(mk("i", "ihlal", ["toy|*|r|0"]), check):
        e.append("dogru ihlal vakasi hata verdi")
    if not run_case(mk("i2", "ihlal", ["toy|*|YOK|0"]), check):
        e.append("beklenen anahtar yokken YAKALANMADI")
    if not run_case(mk("t", "temiz", []), check):
        e.append("temiz vaka bulgu uretince YAKALANMADI (toy kural r icin otuyor)")
    if not run_case(mk("a", "ihlal", ["toy|*|r|0"], absent=["toy|*|r|0"]), check):
        e.append("expect_absent ihlali YAKALANMADI")
    return e


def check_coverage() -> list[str]:
    e = []
    empty = build_coverage(Registry(), {"floors": []})
    if "HICBIR mercek" not in empty.text():
        e.append("bos kayitta kapsam raporu 'hicbir mercek kayitli degil' demeli")
    f_run = idea("mahremiyet.gecis.a", status="shadow", check_ref="a:b", provenance=prov(), needs=("rooms[].unit_id",), applies_when="has_room_type:salon|yatak_odasi")
    f_north = idea("isik.yonelim.b", lens="isik", status="shadow", check_ref="a:b", provenance=prov(), needs=("meta.north_angle",))
    r = Registry()
    r.register_lens(Lens("mahremiyet", "t", "p"))
    r.register_lens(Lens("isik", "t", "p"))
    r.register_facet(f_run)
    r.register_facet(f_north)
    ctx = {"meta": {}, "floors": [
        {"id": "K1", "rooms": [{"room_type": "salon", "unit_id": "uA"}, {"room_type": "yatak_odasi", "unit_id": None}]},
        {"id": "ZK", "rooms": [{"room_type": "dukkan"}]},
        {"id": "K2", "rooms": [{"room_type": "salon"}]},
    ]}
    rep = build_coverage(r, ctx)
    st = {(x.facet_id, x.floor_id): x for x in rep.entries}
    if st[("mahremiyet.gecis.a", "K1")].state != "kostu" or "1/2" not in st[("mahremiyet.gecis.a", "K1")].reason:
        e.append("K1: kostu ve kismi kapsam '1/2' yazmali")
    if st[("mahremiyet.gecis.a", "ZK")].state != "uygulanmaz":
        e.append("ZK: salon/yatak yok -> uygulanmaz")
    if st[("mahremiyet.gecis.a", "K2")].state != "kosamadi":
        e.append("K2: unit_id hicbir elemanda yok -> koSAMADI (uygulanmaz ile KARISMAMALI)")
    if st[("isik.yonelim.b", "K1")].state != "kosamadi" or "north_angle" not in st[("isik.yonelim.b", "K1")].reason:
        e.append("meta.north_angle yok -> kosamadi + neden")
    r.register_facet(idea("mahremiyet.gecis.taslak", status="draft", provenance=prov(), needs=("rooms[].unit_id",)))
    rep2 = build_coverage(r, ctx)
    if "mahremiyet.gecis.taslak" not in rep2.unmeasured or any(x.facet_id == "mahremiyet.gecis.taslak" for x in rep2.entries):
        e.append("draft veche 'kostu' sayilmamali: olcum kodu yok -> 'OLCULMEYEN' (temiz ile karismamali)")
    if "OLCULMEYEN" not in rep2.text().upper():
        e.append("kapsam metni olculmeyen vecheyi soylemeli")
    ctx["meta"]["north_angle"] = 30
    if {(x.facet_id, x.floor_id): x for x in build_coverage(r, ctx).entries}[("isik.yonelim.b", "K1")].state != "kostu":
        e.append("north_angle verilince kostu olmali (yanlis-pozitif)")
    return e


def check_provenance_gate_and_info() -> list[str]:
    e = []
    kesin_no_src = idea(status="draft", provenance=prov("kesin", ""), needs=("a.b",))
    kesin_placeholder = idea(status="draft", provenance=prov("kesin", "v1 pratik varsayılan"), needs=("a.b",))
    kesin_ok = idea(status="draft", provenance=prov("kesin", "TS 000 md.5"), needs=("a.b",))
    yaygin = idea(status="draft", provenance=prov("yaygin", ""), needs=("a.b",))
    if not dc.check_reasoning_provenance(reg_with(kesin_no_src)) or not dc.check_reasoning_provenance(reg_with(kesin_placeholder)):
        e.append("kaynaksiz 'kesin' YAKALANMADI (#14)")
    if dc.check_reasoning_provenance(reg_with(kesin_ok)) or dc.check_reasoning_provenance(reg_with(yaygin)):
        e.append("kaynakli kesin / kaynaksiz yaygin hata vermemeli (yanlis-pozitif)")
    old = idea(status="draft", provenance=Provenance("mimari_pratik", "yaygin", "k", "2024-01-01"), needs=("a.b",))
    fresh = idea("mahremiyet.gorsel.taze", status="draft", provenance=Provenance("mimari_pratik", "yaygin", "k", "2026-10-01"), needs=("a.b",))
    info = dc.run_info(today=datetime.date(2026, 10, 9), registry=reg_with(old, fresh))
    if not any("gun once" in x and "deneme" in x for x in info) or any("taze" in x for x in info):
        e.append("#15: eski reviewed BILGI satiri vermeli, taze vermemeli; bilgi satiri hata listesinde olmamali")
    return e


def check_promotion() -> list[str]:
    e = []
    allfire = trigger_report("f", {"u1": True, "u2": True, "u3": True})
    if not (allfire.degenerate and allfire.rate == 1.0 and allfire.weak_evidence):
        e.append("hep otuyor -> dejenere + kanit zayif")
    some = trigger_report("f", {"u1": True, "u2": False, "u3": None})
    if some.degenerate or some.eligible != 2 or some.unmeasurable != 1 or some.rate != 0.5:
        e.append("olculemedi paydadan CIKMALI ve %0 sayilmamali; 1/2 dejenere degil")
    if trigger_report("f", {"u": None}).rate is not None:
        e.append("hic olculebilir ozne yoksa oran None")
    if trigger_report("f", {"a": False, "b": False}).degenerate is not True:
        e.append("hic otmuyor -> dejenere")
    return e


def check_production_loading_is_side_effect_free() -> list[str]:
    from reasoning import load_registry
    reg, errs = load_registry()
    e = []
    if errs or set(reg.lenses) != {"mahremiyet"} or len(reg.facets) != 14:
        e.append(f"uretim kaydi: yalniz 'mahremiyet' merceginin 14 vechesi, hatasiz olmali: {errs} {sorted(reg.lenses)} {len(reg.facets)}")
    from reasoning import validate_registry as _vr
    if _vr(reg):
        e.append(f"uretim kaydi ic tutarlilik hatasi: {_vr(reg)}")
    # saglayici dosyasi cizim modulu import ederse REDDEDILMELI
    import reasoning.registry as rr
    tmp = Path(tempfile.mkdtemp())
    (tmp / "lenses").mkdir()
    bad = tmp / "m.py"
    bad.write_text("import ezdxf\nfrom reasoning.model import Facet\ndef register(reg): pass\n")
    if not rr._import_violations(bad):
        e.append("saglayicinin 'import ezdxf' yapmasi YAKALANMADI")
    ok = tmp / "ok.py"
    ok.write_text("from __future__ import annotations\nfrom reasoning.model import Facet\ndef register(reg): pass\n")
    if rr._import_violations(ok):
        e.append("yalniz reasoning.* import eden saglayici reddedildi (yanlis-pozitif)")
    return e


# ------------------------------------------------------------------ DEV-061: mahremiyet paketi
def _prod_registry():
    from reasoning import load_registry
    reg, errs = load_registry()
    return reg, errs


def _normal1():
    ctx = json.loads((ROOT / "context.json").read_text(encoding="utf-8"))
    return next(f for f in ctx["floors"] if f["id"] == "normal1")


def check_mahremiyet_statuses() -> list[str]:
    reg, errs = _prod_registry()
    e = list(errs)
    from collections import Counter
    got = Counter(f.status for f in reg.facets.values() if f.lens == "mahremiyet")
    if dict(got) != {"active": 5, "shadow": 6, "draft": 2, "idea": 1}:
        e.append(f"durum dagilimi 5 active / 6 shadow / 2 draft / 1 idea olmali: {dict(got)}")
    legacy = {f.id for f in reg.facets.values() if f.legacy}
    if len(legacy) != 5 or any(reg.facets[i].status != "active" for i in legacy):
        e.append("legacy bayragi tam beş active vecheye ait olmali")
    for f in reg.facets.values():
        if f.status == "active" and f.plain and any(ch.isdigit() for ch in f.plain.problem + f.plain.consequence):
            e.append(f"{f.id}: plain metninde rakam var (sayi yalniz olcumden gelir)")
    if {s.id for s in reg.smells.values()} != {"sandvic_banyo", "gecis_odasi_yatak", "dikizli_giris"}:
        e.append("uc koku kayitli olmali")
    return e


def check_mahremiyet_wiring_claim() -> list[str]:
    """'validate.py'nin cagirdigi bes = active+legacy, DEV-052/053 = shadow' iddiasi KODDAN sabitlenir:
    biri validate'e baglanirsa bu test kirilir ve durum guncellenir (sessiz sapma olmaz)."""
    import re
    reg, _ = _prod_registry()
    validate_src = (ROOT / "scripts" / "validate.py").read_text(encoding="utf-8")
    rules_src = (ROOT / "scripts" / "architect" / "rules.py").read_text(encoding="utf-8")
    nuances = rules_src[rules_src.index("def check_door_window_nuances"):]
    e = []
    for f in reg.facets.values():
        if f.adapter is None or not f.adapter.ref.startswith("architect.rules:"):
            continue
        name = f.adapter.ref.split(":")[1]
        called = bool(re.search(rf"\+?\s*{name}\(rooms, walls, openings\)", validate_src)) or f"{name}(rooms, walls, openings)" in nuances
        if f.legacy and not called:
            e.append(f"{f.id}: legacy ama validate.py {name}'i CAGIRMIYOR")
        if not f.legacy and called:
            e.append(f"{f.id}: shadow ama validate.py artik {name}'i cagiriyor - durumu active+legacy yap")
    return e


def check_mahremiyet_cases() -> list[str]:
    import reasoning_report as rr
    from reasoning import list_cases, load_case, run_case
    reg, _ = _prod_registry()
    e = []
    cases = list_cases()
    if len(cases) != 22:
        e.append(f"22 vaka beklenirdi (11 vechenin ihlal+temiz): {len(cases)}")
    for path in cases:
        case, _x = load_case(path)
        facet = reg.facets.get(case["facet"])
        if facet is None or facet.adapter is None:
            e.append(f"{path.name}: vechesi/adaptoru yok")
            continue
        e += run_case(path, rr.facet_check(facet))
    # kasitli bozma: ihlal sahnesini temizlersek de, temiz sahneyi bozarsak da kosucu YAKALAMALI
    tmp = Path(tempfile.mkdtemp())
    for name, door_pos in (("giristen_yatak_gorus_ihlal", 500), ("giristen_yatak_gorus_temiz", 2700)):
        src = next(p for p in cases if p.name == name)
        case, expected = load_case(src)
        for o in case["floor"]["openings"]:
            if o["id"] == "d_hedef":
                o["position_from_start"] = door_pos
        d = tmp / name
        d.mkdir()
        (d / "case.json").write_text(json.dumps(case), encoding="utf-8")
        (d / "expected_findings.json").write_text(json.dumps(expected), encoding="utf-8")
        if not run_case(d, rr.facet_check(reg.facets["mahremiyet.gorsel.giristen_yatak_odasi_gorus"])):
            e.append(f"kasitli bozma YAKALANMADI: {name}")
    return e


def check_mahremiyet_real_project() -> list[str]:
    """rev-28 normal1: plan §6.1 olcumleri. Degerler EL ile kontrol edildi: uC 16.1/1978, uB 20.2/2025, uB-uC 1485, 5/6."""
    from architect import privacy as pv
    fl = _normal1()
    a = (fl["rooms"], fl["walls"], fl["openings"])
    e = []
    msgs = pv.check_entry_bedroom_sightline(*a)
    if not (len(msgs) == 2 and any("uC_d_entry" in m and "sapma 16 " in m and "1978mm" in m for m in msgs)
            and any("uB_d_entry" in m and "sapma 20 " in m and "2025mm" in m for m in msgs)):
        e.append(f"olcum #4: uC 16/1978 ve uB 20/2025 beklenirdi: {msgs}")
    if pv.entry_bedroom_sightline_subjects(*a) != {"uA": False, "uB": True, "uC": True}:
        e.append(f"olcum #4 ozneleri: {pv.entry_bedroom_sightline_subjects(*a)}")
    msgs = pv.check_neighbor_entry_proximity(*a)
    if not (len(msgs) == 1 and "'uB'" in msgs[0] and "'uC'" in msgs[0] and "1485mm" in msgs[0]):
        e.append(f"olcum #5: uB-uC 1485 beklenirdi: {msgs}")
    subj = pv.wet_shared_wall_same_unit_subjects(*a)
    if (sum(1 for v in subj.values() if v), len(subj)) != (5, 6):
        e.append(f"olcum #6: ayni birimde 5/6 beklenirdi: {subj}")
    if any(pv.wet_double_zone_doors_subjects(*a).values()):
        e.append("gercek projede sandvic banyo YOK (sentetik vaka); tetiklememeli")
    # opt-in: unit_id soyulunca 4 olcum de SESSIZ
    bare = [{k: v for k, v in r.items() if k != "unit_id"} for r in fl["rooms"]]
    for fn in (pv.check_entry_bedroom_sightline, pv.check_neighbor_entry_proximity,
               pv.check_wet_shared_wall_same_unit, pv.check_wet_double_zone_doors):
        if fn(bare, fl["walls"], fl["openings"]):
            e.append(f"{fn.__name__}: unit_id yokken sessiz kalmali (opt-in)")
    # esik override: 1000 mm esikte komsu giris uyarisi KALKAR (yanlis-pozitif tarafi)
    if pv.check_neighbor_entry_proximity(*a, min_distance=1000.0):
        e.append("min_distance=1000 iken 1485mm uyari vermemeli")
    return e


def check_mahremiyet_report() -> list[str]:
    """reasoning_report: golge bolumu + asgari tetik orani; validate.py cikisi DEGISMEZ (15 satir)."""
    import reasoning_report as rr
    reg, _ = _prod_registry()
    ctx = json.loads((ROOT / "context.json").read_text(encoding="utf-8"))
    e = []
    sh = rr.shadow_findings(reg, ctx)
    got = {k: len(v) for k, v in sh.items()}
    want = {"mahremiyet.gorsel.giris_wc_kapi_yakin": 0, "mahremiyet.gorsel.islak_hacim_komsulugu": 0,
            "mahremiyet.gorsel.giristen_yatak_odasi_gorus": 10, "mahremiyet.birimler_arasi.komsu_giris_yakinligi": 5,
            "mahremiyet.isitsel.islak_ortak_duvar_ayni_birim": 30, "mahremiyet.gecis.islak_iki_bolgeye_kapili": 0}
    if got != want:
        e.append(f"golge bulgu sayilari (5 ozdes kat): {got}")
    rates = {r.facet_id: (r.fired, r.eligible, r.degenerate) for r in rr.shadow_triggers(reg, ctx)}
    if rates.get("mahremiyet.isitsel.islak_ortak_duvar_ayni_birim") != (5, 6, False):
        e.append(f"#6 tetik orani 5/6 olmali: {rates}")
    if rates.get("mahremiyet.gecis.islak_iki_bolgeye_kapili") != (0, 6, True):
        e.append("gercek projede hic otmeyen vechenin DEJENERE diye raporlanmasi gerekir")
    out = subprocess.run([sys.executable, str(ROOT / "scripts" / "reasoning_report.py")],
                         capture_output=True, text=True, timeout=600).stdout
    for needle in ("16 uyari satiri -> 4 tekil konu", "Golge vecheler", "5/6 ozne tetikledi", "OLCULMEYEN"):
        if needle not in out:
            e.append(f"rapor ciktisinda '{needle}' yok")
    return e


# ------------------------------------------------------------------ DEV-064: aciklama motoru, rakam lint'i, kuyruk, diyalog
def _salon_registry():
    """Plan §5.6 'salonu buyutelim' ornegi icin SENTETIK yasanabilirlik vechesi (uretim kaydinda yok)."""
    from reasoning import Remedy
    r = Registry()
    r.register_lens(Lens("yasanabilirlik", "Yasanabilirlik", "f"))
    r.register_remedy(Remedy("salonu_az_buyut", "Salonu daha az büyütmek; yatak odası rahat kalır, salon yine büyür.", "Salon beklenenden az büyür."))
    r.register_remedy(Remedy("tek_kisilik_dusun", "Büyütmeyi aynen yapıp yatak odasını tek kişilik düşünmek.", "Yatak odasında çift kişilik yatak olmaz."))
    f = Facet(id="yasanabilirlik.yatak.kume_sigmasi", lens="yasanabilirlik", title_tr="t", principle_tr="p", why_tr="w",
              status="active", provenance=prov(), needs=("rooms[].room_type",),
              plain=Plain(problem="Bitişik yatak odası {olcum:kuculme} küçüldüğü için çift kişilik yatak artık rahat yerleşmiyor ({ad:eleman}).",
                          consequence="Yatağın iki yanında geçiş kalmıyor.", numbers=("kuculme",)),
              thresholds=Thresholds(warn_at=0.0, severe_at=10.0, unit="m2", source="s"),
              remedies=("salonu_az_buyut", "tek_kisilik_dusun"))
    r.register_facet(f)
    return r, f


def check_lint_and_render() -> list[str]:
    from reasoning import ExplainError, lint_template, render, verify_numbers
    from reasoning.explain import allowed_numbers_for
    e = []
    if lint_template("Salon beş metrekare büyür."):
        e.append("rakamsiz sablon lint'e takildi (yanlis-pozitif)")
    for name, text in {"ASCII rakam": "Salon 5 m2 küçülür", "yer-tutucu disinda rakam": "Hol {olcum:a} ve 3 oda",
                       "Unicode Nd": "Salon ٣ oda", "ussu (No)": "Alan m²", "Roma (Nl)": "Ⅳ. kat",
                       "bilinmeyen sinif": "Salon {sayi:a} olur", "Plain.numbers disi": "Hol {olcum:b}"}.items():
        if not lint_template(text, ("a",)):
            e.append(f"rakam lint'i YAKALAMADI: {name}")
    if lint_template("1. Seçenek\n2. Seçenek\n{olcum:a} {ad:eleman} {sabit:warn_at}", ("a",)):
        e.append("numaralandirma istisnasi + gecerli yer-tutucular reddedildi (yanlis-pozitif)")
    if not lint_template("Üç seçenek var, 3 tane."):
        e.append("numaralandirma istisnasi satir basi disinda GECERLI olmamali")
    reg, facet = _salon_registry()
    f = Finding("k|*|x|1", facet.id, "K1", "m", ("uB_oda",), evidence={"kuculme": 2.5}, severity=0.3)
    if render(facet.plain.problem, f, facet) != "Bitişik yatak odası 2.5 küçüldüğü için çift kişilik yatak artık rahat yerleşmiyor (uB_oda).":
        e.append("render: yer-tutucular kanittan dogru dolmadi")
    for name, tpl, fnd, fct in (("olmayan olcum", "{olcum:yok}", f, facet),
                                ("esiksiz sabit", "{sabit:severe_at}", Finding("k|*|x|1", "y", None, "m"), None),
                                ("olmayan eleman", "{ad:eleman2}", f, facet),
                                ("olculmemis siddet", "{sabit:siddet}", Finding("k|*|x|1", "y", None, "m"), None)):
        try:
            render(tpl, fnd, fct)
            e.append(f"render: {name} icin HATA beklenirdi (uydurma yok)")
        except ExplainError:
            pass
    allowed = allowed_numbers_for([f], reg.facets)
    if verify_numbers("Yaklaşık 2.5 küçülüyor.", allowed):
        e.append("kaynakli sayi verify_numbers'tan gecmeli")
    if verify_numbers("Yaklaşık 3 küçülüyor.", allowed) != ["3"]:
        e.append("kaynaksiz sayi verify_numbers'ta YAKALANMALI")
    if verify_numbers("1. Seçenek A\n2. Seçenek B", allowed):
        e.append("satir basi numaralandirma kaynaksiz sayi sayilmamali")
    if verify_numbers("hol 25 m2, oda uC_oda2, K1 katı", {"25"}):
        e.append("birim/ad parcasi (m2, uC_oda2, K1) SAYI sayilmamali")
    return e


def check_narrative_example() -> list[str]:
    """Plan §5.6: bes parca, en cok uc secenek; sayi yalniz kanittan."""
    from reasoning import narrate, select_topics, verify_numbers
    from reasoning.explain import allowed_numbers_for
    reg, facet = _salon_registry()
    f = Finding("yasanabilirlik.yatak.kume_sigmasi|K1|uB_oda|1", facet.id, "K1", "m", ("uB_oda",), evidence={"kuculme": 2.5}, severity=0.3)
    shown, _rest = select_topics([f], reg.facets)
    nar = narrate(shown[0], reg.facets, reg.remedies, level="sade")
    text = nar.text()
    e = []
    if not (len(nar.options) == 3 and nar.options[-1].startswith("Olduğu gibi bırakmak")):
        e.append(f"secenekler: iki cozum + 'birak' olmali: {nar.options}")
    if "Önerim, ilk seçenek: Salonu daha az büyütmek" not in text:
        e.append("oneri ilk secenek olmali")
    i1, i2, i3, i4 = (text.index(x) for x in (nar.see, "Seçenekler:", nar.recommendation, "Karar sizin"))
    if not i1 < i2 < i3 < i4:
        e.append("bes parcali iskelet sirasi bozuk")
    bad = verify_numbers(text, allowed_numbers_for([f], reg.facets))
    if bad:
        e.append(f"anlatimda kaynaksiz sayi: {bad}")
    if "yapılamaz" in text.lower():
        e.append("'yapilamaz' denmemeli")
    return e


def check_queue_and_modes() -> list[str]:
    from reasoning import effective_mode, narrate, select_topics
    e = []
    extra = "UYARI (mimari): [normal1] Oda 'uZ' bir sey\nUYARI (mimari): [normal1] Oda 'uY' baska sey\n"
    shown, rest = select_topics(parse_validate_output(SAMPLE + extra), {}, limit=3)
    if (len(shown), len(rest)) != (3, 2):
        e.append(f"5 konu (SAMPLE 3 + 2): 3 ilk mesaj + 2 diger not: {(len(shown), len(rest))}")
    out = subprocess.run([sys.executable, str(ROOT / "scripts" / "validate.py"), str(ROOT / "context.json")],
                         capture_output=True, text=True, timeout=600).stdout
    real = parse_validate_output(out)
    sh, rs = select_topics(real, {})
    if (len(real), len(sh), len(rs)) != (16, 3, 0):
        e.append(f"rev-28: 16 satir (15 + surum notu) -> 3 konu beklenirdi: {(len(real), len(sh), len(rs))}")
    reg, _ = _prod_registry()  # golge gorunurluk degismezi
    shadow_f = Finding("mahremiyet.gorsel.giristen_yatak_odasi_gorus|K1|a|1", "mahremiyet.gorsel.giristen_yatak_odasi_gorus", "K1", "m", ("a",))
    active_f = Finding("mahremiyet.gorsel.giris_wc_gorus|K1|a|1", "mahremiyet.gorsel.giris_wc_gorus", "K1", "m", ("a",))
    sh, _ = select_topics([shadow_f, active_f], reg.facets)
    if [t.facet_id for t in sh] != ["mahremiyet.gorsel.giris_wc_gorus"]:
        e.append(f"shadow bulgu SUNULMAMALI (gorunurluk degismezi): {[t.facet_id for t in sh]}")
    a = Finding("legacy.mimari|K1|a|1", "legacy.mimari", "K1", "a", ("a",), severity=0.2)
    b = Finding("legacy.mimari|K1|b|2", "legacy.mimari", "K1", "b", ("b",), severity=0.9)
    c = Finding("legacy.mimari|K1|c|3", "legacy.mimari", "K1", "c", ("c",))
    d = Finding("legacy.mimari|K1|d|4", "legacy.mimari", "K1", "d", ("d",), severity=0.5)
    sh, _ = select_topics([a, b, c, d], {}, before=[a, b, c], limit=4)
    if [t.elements[0] for t in sh] != ["d", "b", "a", "c"]:
        e.append(f"siralama: yan etki(d) > siddet(b>a) > olculmeyen(c): {[t.elements[0] for t in sh]}")
    sh, _ = select_topics([a, b], {}, intent_elements=("a",), limit=2)
    if sh[0].elements[0] != "a":
        e.append("niyetle ilgili konu siddetten once gelmeli")
    if (effective_mode("devret", 0.2), effective_mode("devret", 0.7), effective_mode("sor", 0.9), effective_mode("devret", None)) != ("devret", "sor", "sor", "devret"):
        e.append("devret: ciddi (>0.6) bulguda SOR; digerlerinde devret")
    rr, facet = _salon_registry()
    f = Finding("k|K1|x|1", facet.id, "K1", "m", ("x",), evidence={"kuculme": 1.0}, severity=0.8)
    nar = narrate(select_topics([f], rr.facets)[0][0], rr.facets, rr.remedies, level="sade", mode="devret")
    if nar.mode != "sor" or "ciddi" not in nar.text():
        e.append("ciddi bulguda devir olsa bile sorulmali ve nedeni soylenmeli")
    f2 = Finding("k|K1|x|1", facet.id, "K1", "m", ("x",), evidence={"kuculme": 1.0}, severity=0.2)
    nar = narrate(select_topics([f2], rr.facets)[0][0], rr.facets, rr.remedies, level="sade", mode="devret")
    if nar.mode != "devret" or "devrettiğiniz" not in nar.text():
        e.append("hafif bulguda devir: oneri uygulanir, sonradan bildirilir")
    nar = narrate(select_topics(real, {})[0][0], {}, {}, level="sade", mode="devret")
    if nar.mode != "sor":
        e.append("uygulanacak cozum yokken devir gecersiz sayilmali")
    return e


def check_smells_and_coverage_sentence() -> list[str]:
    from reasoning import coverage_sentence, match_smells, select_topics
    reg, _ = _prod_registry()
    e = []

    def mk(fid, els):
        return Finding(f"{fid}|K1|{','.join(els)}|1", fid, "K1", "m", els)

    share = [mk("mahremiyet.gecis.islak_yatak_odasindan", ("oda", "ban")), mk("mahremiyet.gecis.yatak_salona_dogrudan", ("oda", "salon"))]
    if [s.id for s, _p in match_smells(select_topics(share, reg.facets)[0], reg.smells)] != ["gecis_odasi_yatak"]:
        e.append("ortak elemanli iki bilesen -> gecis_odasi_yatak kokusu")
    apart = [mk("mahremiyet.gecis.islak_yatak_odasindan", ("oda1",)), mk("mahremiyet.gecis.yatak_salona_dogrudan", ("oda2",))]
    if match_smells(select_topics(apart, reg.facets)[0], reg.smells):
        e.append("ortak eleman yokken koku birlestirmesi YAPILMAMALI (yanlis-pozitif)")
    s = coverage_sentence([("Yönelim", "meta.north_angle yok")], ["Kademelenme"])
    if "Yönelim" not in s or "north_angle" not in s or "Kademelenme" not in s or "değildir" not in s:
        e.append("bakilamayan ve olculmeyen bakis acilari ADIYLA soylenmeli")
    if coverage_sentence([], []):
        e.append("soylenecek bir sey yoksa bos donmeli")
    return e


def check_dialogue_log() -> list[str]:
    from reasoning import ExplainError, append_dialogue, read_dialogue, validate_record
    e = []
    tmp = Path(tempfile.mkdtemp()) / "dialogue.jsonl"
    rec = {"rev": 28, "ts": "2026-10-09T10:00:00+00:00", "context_sha256": "a" * 64, "finding_keys": ["k"],
           "text": "Oda yaklaşık 2025 mm.", "mode": "sor", "level": "mimar"}
    append_dialogue(tmp, rec, {"2025"})
    for name, bad in (("kaynaksiz sayi", {**rec, "text": "Oda yaklaşık 2026 mm."}), ("geri giden rev", {**rec, "rev": 27})):
        try:
            append_dialogue(tmp, bad, {"2025"})
            e.append(f"{name} REDDEDILMELI (ekleme-yalniz)")
        except ExplainError:
            pass
    append_dialogue(tmp, {**rec, "text": "Aynı revizyonda ikinci not."}, set())
    if len(read_dialogue(tmp)) != 2 or tmp.read_text(encoding="utf-8").count("\n") != 2:
        e.append("kayitlar satir satir EKLENMELI (reddedilenler yazilmamali)")
    for name, bad in {"alan eksik": {k: v for k, v in rec.items() if k != "level"}, "kotu sha": {**rec, "context_sha256": "x"},
                      "bos metin": {**rec, "text": " "}, "kotu mod": {**rec, "mode": "belki"}, "kotu seviye": {**rec, "level": "usta"}}.items():
        if not validate_record(bad):
            e.append(f"kayit bicimi {name} YAKALANMADI")
    return e


def check_digit_gate_13() -> list[str]:
    """#13: uretim kaydi temiz; enjekte edilen rakamli anlatim her alanda YAKALANMALI."""
    from reasoning import Remedy
    e = []
    if dc.check_reasoning_digits():
        e.append(f"uretim kaydinda rakamli anlatim: {dc.check_reasoning_digits()[:3]}")
    base = dict(id="mahremiyet.gorsel.deneme", lens="mahremiyet", title_tr="t", principle_tr="p", why_tr="w")
    for name, kw in {"title": dict(title_tr="3 oda"), "principle": dict(principle_tr="45 derece"), "why": dict(why_tr="1 sebep"),
                     "plain.problem": dict(plain=Plain(problem="5 oda", consequence="x")),
                     "plain.consequence": dict(plain=Plain(problem="x", consequence="2 kat")),
                     "numbers disi yer-tutucu": dict(plain=Plain(problem="{olcum:a}", consequence="x"))}.items():
        if not dc.check_reasoning_digits(reg_with(Facet(**{**base, **kw}))):
            e.append(f"kapi #13 YAKALAMADI: {name}")
    r = reg_with()
    r.register_remedy(Remedy("kotu", "iki kapıyı 2 metre kaydır", "x"))
    if not dc.check_reasoning_digits(r):
        e.append("kapi #13 YAKALAMADI: cozum metni")
    ok = Facet(**{**base, "plain": Plain(problem="{olcum:a} küçüldü", consequence="x", numbers=("a",))})
    if dc.check_reasoning_digits(reg_with(ok)):
        e.append("bildirilmis yer-tutucu hata verdi (yanlis-pozitif)")
    return e


def check_dialogue_cli() -> list[str]:
    import re as _re
    e = []
    script = str(ROOT / "scripts" / "reasoning_dialogue.py")

    def run(*a):
        return subprocess.run([sys.executable, script, *a], capture_output=True, text=True, timeout=600)

    r = run("brief")
    if r.returncode != 3 or "sade tutayım" not in r.stdout:
        e.append(f"seviye sorulmadan brief: cikis 3 ve soru beklenirdi: {r.returncode}")
    r = run("brief", "--level", "sade")
    if r.returncode != 0 or r.stdout.count("--- Konu") != 3 or "Diger notlar" in r.stdout:
        e.append("rev-28 brief: tam 3 konu, diger not yok beklenirdi")
    if "ölçülmüyor" not in r.stdout:
        e.append("brief henuz olculmeyen bakis acilarini adiyla soylemeli")
    body = _re.sub(r"(?m)^(\[Seviye.*|--- Konu .*|\d+\. .*)$", "", r.stdout.split("KAYIT ANAHTARLARI")[0])
    if any(ch.isdigit() for ch in body):
        e.append("sade seviyede serbest rakam olmamali")
    tmp = Path(tempfile.mkdtemp())
    d = tmp / "dialogue.jsonl"
    keys = json.loads(r.stdout.split("KAYIT ANAHTARLARI (append --key icin):")[1].strip().splitlines()[0])
    key = keys[0][0]
    base = ["append", "--level", "mimar", "--mode", "sor", "--rev", "28", "--dialogue", str(d), "--key", key]
    ok = run(*base, "--text", "uB salonunda en dar nokta 2225mm, 3000mm altında.")
    if ok.returncode != 0:
        e.append(f"kaynakli sayili kayit reddedildi: {ok.stdout}")
    bad = run(*base, "--text", "uB salonunda en dar nokta 2300mm.")
    if bad.returncode != 1 or "kaynaksiz" not in bad.stdout:
        e.append("kaynaksiz sayili kayit REDDEDILMELI (cikis 1)")
    if len(d.read_text(encoding="utf-8").splitlines()) != 1:
        e.append("reddedilen kayit dosyaya yazilmamali")
    v = run("verify", "--dialogue", str(d))
    if v.returncode != 0 or "tamam" not in v.stdout:
        e.append(f"verify temiz kaydi onaylamali: {v.stdout}")
    rec = json.loads(d.read_text(encoding="utf-8").splitlines()[0])
    rec["text"] = rec["text"].replace("2225", "2999")  # kasitli bozma: elle degistirilmis anlati
    d.write_text(json.dumps(rec, ensure_ascii=False) + "\n", encoding="utf-8")
    v = run("verify", "--dialogue", str(d))
    if v.returncode != 1 or "KAYNAKSIZ" not in v.stdout:
        e.append("elle bozulmus anlati verify tarafindan YAKALANMALI")
    rec["context_sha256"] = "b" * 64
    d.write_text(json.dumps(rec, ensure_ascii=False) + "\n", encoding="utf-8")
    v = run("verify", "--dialogue", str(d))
    if v.returncode != 0 or "DOGRULANAMADI" not in v.stdout:
        e.append("baglami degismis kayit 'dogrulanamadi' diye raporlanmali (sessiz gecilmemeli)")
    return e


# ------------------------------------------------------------------ DEV-065: tasarim karari kaydi, kanita bagli kabul
def _real_findings():
    out = subprocess.run([sys.executable, str(ROOT / "scripts" / "validate.py"), str(ROOT / "context.json")],
                         capture_output=True, text=True, timeout=600).stdout
    return parse_validate_output(out)


def _hol_topic(findings):
    return [f for f in findings if f.facet_id == "legacy.mimari"]


def check_decision_core() -> list[str]:
    from reasoning import ExplainError, evaluate, evidence_hash, evidence_snapshot, make_decision
    e = []
    fs = _real_findings()
    hol = _hol_topic(fs)
    if len(hol) != 5:
        return [f"rev-28 hol payi 5 katta beklenirdi: {len(hol)}"]
    snap = evidence_snapshot(hol[0])
    if snap != {"m1": 16.3, "m2": 15.0, "m3": 10.1, "m4": 62.0}:
        e.append(f"anlik goruntu mesajdaki olculen sayilari (m1..m4) tutmali: {snap}")
    if evidence_hash(hol[0].key, snap) == evidence_hash(hol[1].key, snap):
        e.append("hash bulgu anahtarina baglanmali")
    if evidence_hash(hol[0].key, snap) != evidence_hash(hol[0].key, dict(snap)):
        e.append("hash deterministik olmali")
    for name, kw in {"bos gerekce": dict(reason="   "), "bulgu yok": dict(findings=[]), "kotu kimlik": dict(decision_id="a b")}.items():
        args = dict(decision_id="dd-0001", rev=28, ts="t", reason="bilincli", findings=hol)
        args.update(kw)
        try:
            make_decision(**args)
            e.append(f"make_decision {name} icin REDDETMELI")
        except ExplainError:
            pass
    dec = make_decision("dd-0001", 28, "t", "Kullanıcı bilinçli kabul etti", hol)
    if len(dec["covers"]) != 5 or dec["devredilmis"] is not False:
        e.append("bir kayit bes katin bulgusunu kapsamali (covers[])")
    v = evaluate(fs, [dec])
    if {k for k, x in v.items() if x[0] == "kabul"} != {f.key for f in hol} or any(x[0] != "kabul" for x in v.values()):
        e.append("kaniti ayni bulgular 'kabul' olmali, kapsanmayanlar listede OLMAMALI")
    # kanit degisimi: KOTULESME ve IYILESME ikisi de kabulu dusurur (v1)
    for label, share, hol_m2 in (("kotulesme", "16.4", "10.2"), ("iyilesme", "16.1", "10.0")):
        changed = [Finding(f.key, f.facet_id, f.floor_id, f.message.replace("16.3", share).replace("10.1", hol_m2), f.elements) for f in hol]
        vv = evaluate(changed, [dec])
        if any(x[0] != "dustu" for x in vv.values()) or len(vv) != 5:
            e.append(f"{label}: kabul DUSMELI")
            continue
        ch = {k: (b, a) for k, b, a in vv[hol[0].key][1].changed}
        if ch.get("m1") != (16.3, float(share)) or "m2" in ch or "m4" in ch:
            e.append(f"{label}: 'once -> simdi' yalniz degisen sayilari vermeli: {ch}")
    # son kayit gecer (ekleme-yalnizlik: eski karar ezilir)
    newer = make_decision("dd-0002", 29, "t", "ikinci", hol[:1], supersedes="dd-0001")
    changed = [Finding(hol[0].key, hol[0].facet_id, hol[0].floor_id, hol[0].message.replace("16.3", "16.4"), hol[0].elements)]
    if evaluate(changed, [dec, newer])[hol[0].key][1].decision_id != "dd-0002":
        e.append("ayni bulguyu kapsayan son karar gecerli olmali")
    return e


def check_decision_schema_and_validate() -> list[str]:
    from reasoning import check_decisions, make_decision
    e = []
    fs = _real_findings()
    hol = _hol_topic(fs)
    ctx = json.loads((ROOT / "context.json").read_text(encoding="utf-8"))
    if check_decisions(ctx):
        e.append("alani olmayan eski context hata vermemeli (opt-in)")
    good = make_decision("dd-0001", 28, "2026-10-09T10:00:00+00:00", "Bilinçli", hol)
    ctx["design_decisions"] = [good]
    if check_decisions(ctx):
        e.append(f"gecerli kayit hata verdi: {check_decisions(ctx)}")

    def with_decisions(decisions):
        c = json.loads((ROOT / "context.json").read_text(encoding="utf-8"))
        c["design_decisions"] = decisions
        return c

    def mutated(fn):
        d = json.loads(json.dumps(good))
        fn(d)
        return d

    bad = {
        "bos gerekce (bosluk)": mutated(lambda d: d.update(reason="  \t ")),
        "yinelenen kimlik": None,
        "covers bos": mutated(lambda d: d.update(covers=[])),
        "kotu hash": mutated(lambda d: d["covers"][0].update(evidence_hash="xyz")),
        "yinelenen anahtar": mutated(lambda d: d["covers"].append(dict(d["covers"][0]))),
        "supersedes yok": mutated(lambda d: d.update(supersedes="dd-9999")),
    }
    for name, d in bad.items():
        decisions = [good, good] if d is None else [d]
        if not check_decisions(with_decisions(decisions)):
            e.append(f"check_decisions YAKALAMADI: {name}")
    tmp = Path(tempfile.mkdtemp())

    def run_validate(ctx_obj):
        p = tmp / "context.json"
        p.write_text(json.dumps(ctx_obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return subprocess.run([sys.executable, str(ROOT / "scripts" / "validate.py"), str(p)], capture_output=True, text=True, timeout=600)

    r = run_validate(with_decisions([good]))
    if r.returncode != 0:
        e.append(f"gecerli karar kaydiyla validate basarisiz: {r.stdout[-300:]}")
    r = run_validate(with_decisions([bad["bos gerekce (bosluk)"]]))
    if r.returncode == 0 or "gerekce (reason) bos olamaz" not in r.stdout:
        e.append("bosluktan olusan gerekce validate.py'de HATA olmali")
    r = run_validate(with_decisions([mutated(lambda d: d.pop("reason"))]))
    if r.returncode == 0:
        e.append("gerekcesiz kayit schema/validate tarafindan reddedilmeli")
    r = run_validate(with_decisions([mutated(lambda d: d.update(bilinmeyen=1))]))
    if r.returncode == 0:
        e.append("schema ek alanlari reddetmeli (additionalProperties)")
    base = subprocess.run([sys.executable, str(ROOT / "scripts" / "validate.py"), str(ROOT / "context.json")], capture_output=True, text=True, timeout=600)
    lines = [l for l in base.stdout.splitlines() if l.startswith("UYARI") and "(surum)" not in l]
    if len(lines) != 15 or sum(1 for l in base.stdout.splitlines() if "(surum)" in l) != 1:
        e.append("eski context: 15 mimari/sartname uyari + TEK surum notu (1.3.0 -> 1.4.0) beklenirdi")
    return e


def check_reopened_presentation() -> list[str]:
    from reasoning import make_decision, narrate, select_topics, verify_numbers
    from reasoning.explain import allowed_numbers_for
    e = []
    fs = _real_findings()
    hol = _hol_topic(fs)
    dec = make_decision("dd-0001", 28, "t", "Hol payı bilinçli", hol)
    shown, rest = select_topics(fs, {}, decisions=[dec])
    if len(shown) != 2 or rest:
        e.append(f"kabul edilen konu sessiz kalmali (3 -> 2 konu): {len(shown)}")
    if any(t.facet_id == "legacy.mimari" for t in shown):
        e.append("kaniti ayni kabul edilmis konu SUNULMAMALI")
    # yalniz normal5'te kanit degisir: konu geri gelir, yalniz o katla, 'once -> simdi' ile
    cur = [Finding(f.key, f.facet_id, f.floor_id, f.message.replace("16.3", "16.4").replace("10.1", "10.2"), f.elements)
           if f.floor_id == "normal5" and f.facet_id == "legacy.mimari" else f for f in fs]
    shown, _ = select_topics(cur, {}, decisions=[dec])
    topic = next((t for t in shown if t.facet_id == "legacy.mimari"), None)
    if topic is None or topic.floors != ("normal5",):
        e.append(f"degisen kat konu olarak GERI GELMELI (yalniz o kat): {topic and topic.floors}")
        return e
    if shown[0] is not topic:
        e.append("kabulu dusen konu siradaki ilk konu olmali (yan etki gibi)")
    nar = narrate(topic, {}, {}, level="sade")
    text = nar.text()
    if "Daha önce bilinçli olarak kabul etmiştiniz" not in text or "önce 16.3 → şimdi 16.4" not in text or "Hol payı bilinçli" not in text:
        e.append(f"'once -> simdi' ve gerekce soylenmeli: {text[-400:]}")
    if verify_numbers(text, allowed_numbers_for(list(topic.findings), {}, [dec])):
        e.append(f"anlatimdaki sayilar bulgudan/karardan gelmeli: {verify_numbers(text, allowed_numbers_for(list(topic.findings), {}, [dec]))}")
    if not verify_numbers(text, allowed_numbers_for(list(topic.findings), {})):
        e.append("karar kaydi olmadan 'once' sayisi kaynakli sayilmamali (kayit zinciri)")
    return e


def check_decide_cli_end_to_end() -> list[str]:
    e = []
    script = str(ROOT / "scripts" / "reasoning_dialogue.py")
    tmp = Path(tempfile.mkdtemp())
    shutil.copy(ROOT / "context.json", tmp / "context.json")
    shutil.copy(ROOT / "requests.jsonl", tmp / "requests.jsonl")

    def run(*a):
        return subprocess.run([sys.executable, script, *a, "--context", str(tmp / "context.json")], capture_output=True, text=True, timeout=600)

    keys = [f.key for f in _hol_topic(_real_findings())]
    args = [x for k in keys for x in ("--key", k)]
    r = run("decide", *args, "--reason", "   ")
    if r.returncode != 1 or "gerekce" not in r.stdout:
        e.append("bos gerekce decide tarafindan REDDEDILMELI")
    before = (tmp / "context.json").read_text(encoding="utf-8")
    if "design_decisions" in before:
        e.append("reddedilen karar context'e yazilmamali")
    r = run("decide", *args, "--reason", "Hol payı bu projede bilinçli olarak yüksek")
    if r.returncode != 0:
        return e + [f"decide basarisiz: {r.stdout}"]
    after = (tmp / "context.json").read_text(encoding="utf-8")
    import difflib
    changed = [l for l in difflib.unified_diff(before.splitlines(), after.splitlines(), lineterm="", n=0) if l[:1] in "+-" and l[:3] not in ("+++", "---")]
    removed = [l for l in changed if l.startswith("-")]
    if len(removed) > 1 or any(l.strip("- ") not in ("}", "]") for l in removed):
        e.append(f"decide yalniz EKLEMELI olmali (en cok son kapanis satiri degisir), silinen: {removed}")
    r = run("brief", "--level", "sade")
    if r.stdout.count("--- Konu") != 2 or "kabul edilmis" not in r.stdout:
        e.append("kabulden sonra brief 2 konu + sessiz kabul notu vermeli")
    # olcum degisir -> geri gelir
    ctx = json.loads(after)
    for f in ctx["floors"]:
        if f["id"] == "normal5":
            for room in f["rooms"]:
                if room["id"] == "uC_hol":
                    room["area_m2"] = 10.2
    (tmp / "context.json").write_text(json.dumps(ctx, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    r = run("brief", "--level", "mimar")
    if r.stdout.count("--- Konu") != 3 or "önce 16.3 → şimdi 16.4" not in r.stdout:
        e.append(f"olcum degisince konu 'once -> simdi' ile GERI GELMELI: {r.stdout[-600:]}")
    # kararin 'once' sayisi append'te kaynakli
    key = next(f.key for f in _real_findings() if False) if False else None
    return e


def check_knowledge_engineer_role() -> list[str]:
    """DEV-070: rol belgesi + izin girisi tutarli; yasak/yazma sinirlari mekanik sabitlenir."""
    perms = json.loads((ROOT / "docs" / "development" / "AGENT_PERMISSIONS.json").read_text(encoding="utf-8"))
    e = []
    ke = perms.get("knowledge_engineering")
    if not ke:
        return ["AGENT_PERMISSIONS.json: knowledge_engineering girisi yok"]
    for need in ("scripts/reasoning/lenses/", "scripts/reasoning/cases/", "scripts/<module>/reasoning.py"):
        if need not in ke["write"]:
            e.append(f"knowledge_engineering.write icinde yok: {need}")
    for need in ("schema/", "scripts/validate.py", "context.json", "scripts/reasoning/*.py", "CLAUDE.md"):
        if need not in ke["forbidden"]:
            e.append(f"knowledge_engineering.forbidden icinde yok: {need}")
    if any(w.startswith(("schema", "scripts/validate")) or w in ("scripts/", "context.json") for w in ke["write"]):
        e.append("knowledge_engineering.write yasak alana dokunuyor")
    if "docs/development/reviews/" in ke["write"] or "docs/development/reviews/" not in perms["review_validation"]["write"]:
        e.append("docs/development/reviews/ yalniz reviewer'in yazma alani olmali")
    if not any("never self-accepted" in r for r in ke["requires"]) or not any("active promotion" in r for r in ke["requires"]):
        e.append("kendi kendini kabul etmeme ve 'active' yalniz kullanici karariyla sartlari yazili olmali")
    doc = (ROOT / "docs" / "agents" / "KNOWLEDGE_ENGINEER_AGENT.md").read_text(encoding="utf-8")
    for needle in ("Vaka → İlke → Veçhe", "Yapmayacakların", "Terfi merdiveni", "Muhakeme katkısı (DEV-048)", "RAKAMSIZ", "kesin"):
        if needle not in doc:
            e.append(f"rol belgesinde bolum/ifade yok: {needle}")
    ref = (ROOT / "docs" / "agents" / "REVIEWER_VALIDATOR_AGENT.md").read_text(encoding="utf-8")
    if "Sistem sınavı" not in ref or "docs/development/reviews/" not in ref:
        e.append("REVIEWER_VALIDATOR_AGENT.md 'Sistem sinavi' bolumu ve reviews yolu eksik")
    return e


def main() -> int:
    checks = [check_keys_and_signature, check_severity_curve, check_diff, check_legacy_parse,
              check_real_validate_parity, check_registry_validation, check_gate10_three_state,
              check_gate11_refs, check_gate12_cases, check_case_runner, check_coverage,
              check_provenance_gate_and_info, check_promotion, check_production_loading_is_side_effect_free,
              check_mahremiyet_statuses, check_mahremiyet_wiring_claim, check_mahremiyet_cases,
              check_mahremiyet_real_project, check_mahremiyet_report,
              check_lint_and_render, check_narrative_example, check_queue_and_modes,
              check_smells_and_coverage_sentence, check_dialogue_log, check_digit_gate_13, check_dialogue_cli,
              check_decision_core, check_decision_schema_and_validate, check_reopened_presentation, check_decide_cli_end_to_end,
              check_knowledge_engineer_role]
    failed = 0
    for check in checks:
        try:
            errs = check()
        except Exception as exc:  # noqa: BLE001 - cokme de BASARISIZLIKTIR (temiz FAIL olarak raporlanir)
            errs = [f"kontrol coktu: {type(exc).__name__}: {exc}"]
        print(("[FAIL] " if errs else "[OK]   ") + check.__name__)
        for er in errs[:10]:
            print("   -", er)
        failed += bool(errs)
    print("reasoning selftest:", "BASARISIZ" if failed else "BASARILI")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
