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
    if validate_registry(reg_with(full)):
        e.append(f"tam active veche hata verdi (yanlis-pozitif): {validate_registry(reg_with(full))}")
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
    if REASONING_PROVIDERS:
        e.append("DEV-060 sonrasi uretimde saglayici beklenmiyordu (DEV-061 ekler; bu test o zaman guncellenir)")
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
    f_run = idea("mahremiyet.gecis.a", status="draft", provenance=prov(), needs=("rooms[].unit_id",), applies_when="has_room_type:salon|yatak_odasi")
    f_north = idea("isik.yonelim.b", lens="isik", status="draft", provenance=prov(), needs=("meta.north_angle",))
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
    if errs or reg.facets or reg.lenses:
        e.append(f"uretim kaydi bugun bos ve hatasiz olmali: {errs} {len(reg.facets)}")
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


def main() -> int:
    checks = [check_keys_and_signature, check_severity_curve, check_diff, check_legacy_parse,
              check_real_validate_parity, check_registry_validation, check_gate10_three_state,
              check_gate11_refs, check_gate12_cases, check_case_runner, check_coverage,
              check_provenance_gate_and_info, check_promotion, check_production_loading_is_side_effect_free]
    failed = 0
    for check in checks:
        errs = check()
        print(("[FAIL] " if errs else "[OK]   ") + check.__name__)
        for er in errs[:10]:
            print("   -", er)
        failed += bool(errs)
    print("reasoning selftest:", "BASARISIZ" if failed else "BASARILI")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
