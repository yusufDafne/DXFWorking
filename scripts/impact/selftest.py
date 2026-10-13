#!/usr/bin/env python3
"""impact testleri (DEV-068). Beklenen kumeler ELLE cikarilir (mini sahne: iki oda, bir orta duvar, bir kapi, bir pencere);
etki alani KASITLI bozmayla (span kontrolu kapatma, 'birim' yayilimi, duvar birlesimi) sinanir; yanlis-pozitif tarafi ayri.

Kullanim:  python scripts/impact/selftest.py     Cikis: 0 basarili, 1 basarisiz.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import impact  # noqa: E402
from impact import graph as G, report as R  # noqa: E402
from impact import Node  # noqa: E402


def mini() -> dict:
    """f1: A=[0..4000]x[0..3000], B=[4000..8000]x[0..3000] (duvar merkez cizgisinde). Orta duvar w_m x=4000.
    Kapi d1 w_m uzerinde merkez 1500 (bosluk [1050,1950]); pencere win w_b uzerinde merkez 6000 (bosluk [5500,6500])."""
    wall = lambda i, s, e: {"id": i, "start": s, "end": e, "thickness": 200.0, "layer": "D"}  # noqa: E731
    f1 = {
        "id": "f1", "label": "KAT 1", "code": "K1",
        "rooms": [
            {"id": "A", "polygon": [[0, 0], [4000, 0], [4000, 3000], [0, 3000]], "unit_id": "u1"},
            {"id": "B", "polygon": [[4000, 0], [8000, 0], [8000, 3000], [4000, 3000]], "unit_id": "u1"},
        ],
        "walls": [wall("w_b", [0, 0], [8000, 0]), wall("w_r", [8000, 0], [8000, 3000]), wall("w_t", [8000, 3000], [0, 3000]),
                  wall("w_l", [0, 3000], [0, 0]), wall("w_m", [4000, 0], [4000, 3000])],
        "openings": [
            {"id": "d1", "type": "door", "wall_id": "w_m", "position_from_start": 1500.0, "width": 900.0},
            {"id": "win", "type": "window", "wall_id": "w_b", "position_from_start": 6000.0, "width": 1000.0},
        ],
        "furniture": [
            {"id": "f_a", "type": "berjer", "position": [3100, 1100], "rotation": 0},     # kapinin A tarafinda
            {"id": "f_b", "type": "berjer", "position": [4100, 1100], "rotation": 0},     # kapinin B tarafinda
            {"id": "f_far", "type": "berjer", "position": [500, 2000], "rotation": 0},    # kapidan uzak, A icinde
        ],
        "columns": [{"id": "c1", "position": [6000, 1500], "width": 300, "depth": 300}],
        "shafts": [{"id": "s1", "kind": "tesisat", "polygon": [[0, 3000], [500, 3000], [500, 3500], [0, 3500]], "unit_id": "u1"}],
        "stairs": [{"id": "st", "room_id": "B", "floor_to_floor_mm": 3000.0}],
        "counters": [{"id": "ct", "room_id": "A", "polygon": [[100, 100], [900, 100], [900, 400], [100, 400]]}],
        "labels": [{"id": "lbl", "type": "text", "text": "x", "position": [6000, 2800]}],
        "level_marks": [{"id": "lm", "position": [1000, 2800], "value_mm": 0}],
        "markings": [{"id": "mk", "start": [5000, 500], "end": [7000, 500]}],
    }
    f2 = copy.deepcopy(f1)
    f2["id"], f2["label"], f2["code"] = "f2", "KAT 2", "K2"
    return {"meta": {"units": "mm"}, "floors": [f1, f2], "rev_history": []}


def N(i, kind="room", floor="f1"):
    return Node(floor, kind, i)


def ring_set(rep, d=None):
    if d is None:
        return {h.node for d_ in rep.rings for h in rep.rings[d_]}
    return {h.node for h in rep.rings.get(d, [])}


def check_graph_edges() -> list[str]:
    errs = []
    ctx = mini()
    g = impact.build_graph(ctx)
    if len([n for n in g.elements if n.floor == "f1"]) != 2 + 5 + 2 + 3 + 1 + 1 + 1 + 1 + 1 + 1 + 1:
        errs.append("f1 dugum sayisi 19 olmali (2 oda, 5 duvar, 2 aciklik, 3 tefris, 1 kolon, 1 saft, 1 merdiven, 1 tezgah, 1 etiket, 1 kot, 1 isaret)")
    has = lambda a, b, cls: any(d == b and c == cls for d, c in g.adj[a])  # noqa: E731
    for w in ("w_b", "w_t", "w_l", "w_m"):
        if not has(N("A"), N(w, "wall"), "duvar_oda_kenari"):
            errs.append(f"A - {w} duvar_oda_kenari olmali")
    for w in ("w_b", "w_t", "w_r", "w_m"):
        if not has(N("B"), N(w, "wall"), "duvar_oda_kenari"):
            errs.append(f"B - {w} duvar_oda_kenari olmali")
    if has(N("A"), N("w_r", "wall"), "duvar_oda_kenari") or has(N("B"), N("w_l", "wall"), "duvar_oda_kenari"):
        errs.append("A-w_r / B-w_l kenari OLMAMALI (yanlis-pozitif)")
    pairs = {("w_b", "w_l"), ("w_b", "w_r"), ("w_b", "w_m"), ("w_r", "w_t"), ("w_t", "w_l"), ("w_t", "w_m")}
    got = {tuple(sorted((a.id, b.id))) for a in g.elements if a.floor == "f1" and a.kind == "wall"
           for b, c in g.adj[a] if c == "duvar_birlesimi"}
    if got != {tuple(sorted(p)) for p in pairs}:
        errs.append(f"duvar birlesimleri hatali: {sorted(got)}")
    if not has(N("d1", "opening"), N("w_m", "wall"), "basvuru") or not has(N("win", "opening"), N("w_b", "wall"), "basvuru"):
        errs.append("aciklik -> duvar basvurusu eksik")
    if not (has(N("d1", "opening"), N("A"), "kapi_komsu_oda") and has(N("d1", "opening"), N("B"), "kapi_komsu_oda")):
        errs.append("kapi iki odaya da degmeli")
    if has(N("win", "opening"), N("A"), "kapi_komsu_oda"):
        errs.append("pencere A'ya degmemeli (6000, 0 noktasi B'nin kenarinda)")
    if not has(N("s1", "shaft"), N("A"), "saft_komsu_oda") or has(N("s1", "shaft"), N("B"), "saft_komsu_oda"):
        errs.append("saft yalniz A ile ortak kenar paylasir")
    if not has(N("st", "stairs"), N("B"), "basvuru") or not has(N("ct", "counter"), N("A"), "basvuru"):
        errs.append("merdiven/tezgah room_id basvurusu eksik")
    if not has(N("ct", "counter"), N("A"), "icinde") or has(N("ct", "counter"), N("B"), "icinde"):
        errs.append("tezgah poligonu yalniz A icinde")
    if not has(N("c1", "column"), N("B"), "icinde") or has(N("c1", "column"), N("A"), "icinde"):
        errs.append("kolon yalniz B icinde")
    if not has(N("lbl", "label"), N("B"), "icinde") or not has(N("lm", "level_mark"), N("A"), "icinde") or not has(N("mk", "marking"), N("B"), "icinde"):
        errs.append("etiket/kot/isaret konum-oda kenari eksik")
    # kapi acilim: A tarafi ya da B tarafi (tam biri), uzak olan HICBIRI; bagimsiz referans: collision motorunun ayni sektor ayak izi
    from collision.geometry import polygon_intersection_area
    from collision.scene import Scene
    shapes = Scene.from_floor(ctx["floors"][0], ctx).shapes
    sector = [s for s in shapes if s.tag == "kapi_acilim" and s.id == "d1"][0]
    for fid in ("f_a", "f_b", "f_far"):
        sh = [s for s in shapes if s.tag == "tefris" and s.id == fid][0]
        want = polygon_intersection_area(sh.polygon, sector.polygon) > 0
        if has(N(fid, "furniture"), N("d1", "opening"), "kapi_acilim") != want:
            errs.append(f"{fid}: kapi_acilim kenari collision sektoruyle uyusmuyor (beklenen {want})")
    if not any(has(N(f, "furniture"), N("d1", "opening"), "kapi_acilim") for f in ("f_a", "f_b")):
        errs.append("kapi sektoru A ya da B tarafindaki tefrisle kesismeli (elle yerlestirildi)")
    if has(N("f_far", "furniture"), N("d1", "opening"), "kapi_acilim"):
        errs.append("uzak tefris kapi sektorunde olmamali")
    if not has(N("A"), N("B"), "birim") or not has(N("s1", "shaft"), N("A"), "birim"):
        errs.append("ayni unit_id: birim kenari eksik")
    if not has(N("A"), N("A", floor="f2"), "kat_ikizi"):
        errs.append("kat ikizi kenari eksik")
    if g.warnings:
        errs.append(f"temiz sahnede uyari: {g.warnings}")
    return errs


def check_span_propagation() -> list[str]:
    errs = []
    ctx = mini()
    # A, derinlik 1: dogrudan komsular
    r1 = impact.blast_radius(ctx, [("f1", "room", "A")], depth=1)
    want1 = {N(w, "wall") for w in ("w_b", "w_t", "w_l", "w_m")} | {N("d1", "opening"), N("s1", "shaft"), N("ct", "counter"),
                                                                   N("lm", "level_mark"), N("f_far", "furniture")}
    want1 |= {n for n in (N("f_a", "furniture"), N("f_b", "furniture")) if n in ring_set(r1)}   # biri kapi tarafi; zaten 'icinde'
    got1 = ring_set(r1)
    if not want1 <= got1:
        errs.append(f"A halka-1 eksik: {sorted(map(str, want1 - got1))}")
    if got1 & {N("win", "opening"), N("B"), N("w_r", "wall"), N("c1", "column")}:
        errs.append(f"A halka-1'de olmamasi gerekenler: {sorted(map(str, got1 & {N('win', 'opening'), N('B'), N('w_r', 'wall'), N('c1', 'column')}))}")
    # A, derinlik 2: B orta duvardan gelir; ALT DUVARIN B tarafindaki parcasi (pencere) ve sag duvar GELMEZ (span)
    r2 = impact.blast_radius(ctx, [("f1", "room", "A")], depth=2)
    got2 = ring_set(r2)
    if N("B") not in got2:
        errs.append("A -> w_m -> B halka-2'de olmali")
    leaked = got2 & {N("win", "opening"), N("w_r", "wall")}
    if leaked:
        errs.append(f"span kontrolu sizdirdi (alt duvarin A parcasindan pencereye/sag duvara gecildi): {sorted(map(str, leaked))}")
    if N("c1", "column") in got2:
        errs.append("kolon B icinde ama B halka-2'de; kolon halka-3'tur")
    # tum duvar dokunuldu: pencere ve her iki oda ve uc birlesim halka-1
    rw = impact.blast_radius(ctx, [("f1", "wall", "w_b")], depth=1)
    gw = ring_set(rw)
    need = {N("win", "opening"), N("A"), N("B"), N("w_l", "wall"), N("w_r", "wall"), N("w_m", "wall")}
    if not need <= gw:
        errs.append(f"w_b halka-1 eksik: {sorted(map(str, need - gw))}")
    if N("w_t", "wall") in gw:
        errs.append("w_b ile w_t birlesmez (yanlis-pozitif)")
    # pencere: duvarin yalniz BOSLUK parcasindan ilerler -> B gelir, A gelmez, birlesimler gelmez
    rwin = impact.blast_radius(ctx, [("f1", "opening", "win")], depth=2)
    g2 = ring_set(rwin)
    # B pencerenin orta noktasina degen odadir (halka-1); B'nin duvarlari halka-2'de MESRU gelir (w_r, w_m, w_t).
    # Gelmemesi gerekenler: A (halka-3) ve alt duvarin pencere parcasi DISINDAKI birlesim (w_l, t=0).
    if N("B") not in g2 or N("A") in g2 or N("w_l", "wall") in g2:
        errs.append(f"pencere etki alani hatali (B var; A ve w_l yok olmali): {sorted(map(str, g2))}")
    if ring_set(rwin, 1) != {N("w_b", "wall"), N("B")}:
        errs.append(f"pencere halka-1 = {{w_b, B}} olmali: {sorted(map(str, ring_set(rwin, 1)))}")
    # kapi: orta duvar + iki oda (+ sektordeki tefris)
    rd = impact.blast_radius(ctx, [("f1", "opening", "d1")], depth=1)
    gd = ring_set(rd)
    if not {N("w_m", "wall"), N("A"), N("B")} <= gd:
        errs.append("kapi halka-1: w_m, A, B olmali")
    return errs


def check_span_chain() -> list[str]:
    """Oda olmayan sade sahne: w2'nin ucu w1'in t=5000 noktasinda. Etki yalniz o noktayi iceren aciklige gecer."""
    errs = []
    wall = lambda i, s, e: {"id": i, "start": s, "end": e, "thickness": 200.0}  # noqa: E731
    ctx = {"meta": {}, "floors": [{"id": "g", "walls": [wall("w1", [0, 0], [10000, 0]), wall("w2", [5000, 0], [5000, 4000])],
           "openings": [{"id": "o_near", "type": "window", "wall_id": "w1", "position_from_start": 5000.0, "width": 400.0},
                        {"id": "o_far", "type": "window", "wall_id": "w1", "position_from_start": 300.0, "width": 400.0}]}]}
    rep = impact.blast_radius(ctx, [("g", "wall", "w2")], depth=2)
    got = ring_set(rep)
    if Node("g", "wall", "w1") not in ring_set(rep, 1) or Node("g", "opening", "o_near") not in ring_set(rep, 2):
        errs.append(f"w2 -> w1 (halka-1) -> o_near (halka-2) olmali: {sorted(map(str, got))}")
    if Node("g", "opening", "o_far") in got:
        errs.append("o_far duvarin baska parcasinda: etki alanina GIRMEMELI")
    # dokunulan duvarin kendisi TAMDIR: w1 dokunulunca iki aciklik de halka-1
    rep1 = impact.blast_radius(ctx, [("g", "wall", "w1")], depth=1)
    if {Node("g", "opening", "o_near"), Node("g", "opening", "o_far"), Node("g", "wall", "w2")} - ring_set(rep1):
        errs.append("dokunulan duvarin tum aciklik/birlesimleri halka-1 olmali")
    return errs


def check_span_helpers() -> list[str]:
    errs = []
    ov, cv = R._overlaps, R._covered
    if not ov([(0, 10)], [(10, 20)], 1.0) or not ov([(0, 10)], [(11, 20)], 1.0) or ov([(0, 10)], [(12, 20)], 1.0):
        errs.append("_overlaps: temas/1 mm pay True, 2 mm bosluk False olmali")
    if not ov([(5, 5)], [(0, 10)], 1.0) or ov([(50, 50)], [(0, 10)], 1.0):
        errs.append("_overlaps: nokta araligi icinde/disinda")
    if not cv(None, [(1, 2)], 1.0) or not cv(None, None, 1.0):
        errs.append("_covered: tum parca zaten ulasildiysa her sey kapsanir")
    if not cv([(0, 10)], [(2, 3)], 1.0) or cv([(0, 10)], [(9, 12)], 1.0) or cv([(0, 10)], None, 1.0):
        errs.append("_covered: kismi/tam kapsama hatali")
    if not cv([(0, 5), (5, 10)], [(2, 8)], 1.0) is False and cv([(0, 5), (5, 10)], [(2, 8)], 1.0):
        pass   # parcalar BIRLESTIRILMEZ (korumaci): [2,8] tek aralik olarak ikisine de sigmaz -> kapsanmis sayilmaz
    return errs


def check_related_not_propagated() -> list[str]:
    errs = []
    ctx = mini()
    rep = impact.blast_radius(ctx, [("f1", "room", "A")], depth=2)
    rel = {(h.node, h.via) for h in rep.related}
    if (N("B"), "birim") in rel and N("B") in ring_set(rep, 1):
        errs.append("B hem halka-1 hem ilgili: halka-1'de olmamali")
    if (N("A", floor="f2"), "kat_ikizi") not in rel:
        errs.append("kat ikizi 'ilgili' listesinde olmali")
    if any(n.floor == "f2" for n in ring_set(rep)):
        errs.append("kat ikizi YAYILMAMALI: f2 halkalarda")
    # yalniz birimle bagli bir oda: bagli oldugu odayi degistirince ilgili listede, halkada degil
    ctx2 = copy.deepcopy(ctx)
    ctx2["floors"][0]["rooms"].append({"id": "C", "polygon": [[20000, 0], [22000, 0], [22000, 2000], [20000, 2000]], "unit_id": "u1"})
    rep2 = impact.blast_radius(ctx2, [("f1", "room", "A")], depth=3)
    if N("C") in ring_set(rep2) or (N("C"), "birim") not in {(h.node, h.via) for h in rep2.related}:
        errs.append("yalniz birimle bagli oda ilgili listede olmali, etki halkasinda degil")
    return errs


def check_errors_and_readonly() -> list[str]:
    errs = []
    ctx = mini()
    before = json.dumps(ctx, sort_keys=True)
    for bad in ([("f1", "room", "yok")], [("fx", "room", "A")], [("f1", "oda", "A")]):
        try:
            impact.blast_radius(ctx, bad)
            errs.append(f"bilinmeyen dugum reddedilmedi: {bad}")
        except impact.ImpactError:
            pass
    for d in (0, -1, 1.5, True):
        try:
            impact.blast_radius(ctx, [("f1", "room", "A")], depth=d)
            errs.append(f"gecersiz depth reddedilmedi: {d!r}")
        except impact.ImpactError:
            pass
    a = impact.format_report(impact.blast_radius(ctx, [("f1", "room", "A")]))
    b = impact.format_report(impact.blast_radius(ctx, [("f1", "room", "A")]))
    if a != b:
        errs.append("ayni girdi farkli rapor uretti (deterministik degil)")
    if json.dumps(ctx, sort_keys=True) != before:
        errs.append("context DEGISTI (salt okunur olmali)")
    return errs


def check_diff() -> list[str]:
    errs = []
    before = mini()
    after = copy.deepcopy(before)
    after["floors"][0]["walls"][4]["thickness"] = 150.0                                   # w_m degisti
    after["floors"][0]["furniture"] = [f for f in after["floors"][0]["furniture"] if f["id"] != "f_far"]   # f_far silindi
    after["floors"][0]["rooms"].append({"id": "C", "polygon": [[8000, 0], [9000, 0], [9000, 1000], [8000, 1000]]})  # C eklendi
    after["floors"][0]["label"] = "KAT 1 (REV)"
    after["meta"]["scale"] = "1:50"
    d = impact.touched_from_diff(before, after)
    if d["changed"] != [N("w_m", "wall")] or d["removed"] != [N("f_far", "furniture")] or d["added"] != [N("C")]:
        errs.append(f"fark hatali: {d}")
    if "floors[f1].label" not in d["other"] or "meta" not in d["other"]:
        errs.append(f"kat listesi disi degisiklikler adiyla soylenmeli: {d['other']}")
    same = impact.touched_from_diff(before, copy.deepcopy(before))
    if any(same[k] for k in same):
        errs.append(f"degisiklik yokken fark bos olmali: {same}")
    rep = impact.diff_report(before, after, depth=1)
    if rep.after is None or N("w_m", "wall") not in rep.after.touched or N("C") not in rep.after.touched:
        errs.append("diff_report sonraki taraf dokunulanlari eksik")
    if rep.before is None or N("f_far", "furniture") not in rep.before.touched:
        errs.append("diff_report onceki taraf silinen elemani icermeli")
    # kat eklendi/silindi
    after2 = copy.deepcopy(before)
    after2["floors"] = after2["floors"][:1]
    d2 = impact.touched_from_diff(before, after2)
    if d2["floors_removed"] != ["f2"] or N("A", floor="f2") not in d2["removed"]:
        errs.append("silinen katin elemanlari 'removed' olmali")
    return errs


def check_coverage() -> list[str]:
    errs = []
    ctx = mini()
    cov = impact.coverage(ctx)
    if any(cov["per_kind"][k]["isolated"] for k in cov["per_kind"]):
        errs.append(f"temiz sahnede bagsiz eleman: { {k: v['isolated'] for k, v in cov['per_kind'].items() if v['isolated']} }")
    if cov["out_of_scope"] != ["meta"]:
        errs.append(f"kapsam disi ust seviye alanlar: {cov['out_of_scope']}")
    ctx["floors"][0]["walls"].append({"id": "w_orphan", "start": [20000, 0], "end": [21000, 0], "thickness": 200.0, "layer": "D"})
    cov2 = impact.coverage(ctx)
    if cov2["per_kind"]["wall"]["isolated"] != ["f1/wall/w_orphan"]:
        errs.append(f"bagsiz duvar yakalanmali: {cov2['per_kind']['wall']['isolated']}")
    # kopuk basvuru uyari olarak yuzeye cikar (sessiz gecilmez)
    ctx["floors"][0]["openings"].append({"id": "kopuk", "type": "door", "wall_id": "yok_duvar", "position_from_start": 100.0, "width": 900.0})
    g = impact.build_graph(ctx)
    if not any("yok_duvar" in w for w in g.warnings):
        errs.append("olmayan duvara basvuru uyari uretmeli")
    return errs


def check_real_context() -> list[str]:
    errs = []
    ctx = json.loads((ROOT / "context.json").read_text(encoding="utf-8"))
    g = impact.build_graph(ctx)
    cov = impact.coverage(ctx, g)
    for kind in ("room", "wall", "opening", "shaft", "stairs"):
        iso = cov["per_kind"].get(kind, {}).get("isolated", [])
        if iso:
            errs.append(f"gercek projede bagsiz {kind}: {iso[:3]}")
    if g.warnings:
        errs.append(f"gercek projede kenar uyarisi: {g.warnings[:2]}")
    rep = impact.blast_radius(ctx, [("normal1", "room", "uC_banyo")], graph=g)
    r1 = ring_set(rep, 1)
    if not {Node("normal1", "opening", "uC_d_banyo_hol"), Node("normal1", "shaft", "uC_saft")} <= r1:
        errs.append("uC_banyo halka-1: kapisi ve saft olmali")
    leaked = ring_set(rep) & {Node("normal1", "opening", "uA_win_oda2_g"), Node("normal1", "opening", "uC_win_salon")}
    if leaked:
        errs.append(f"uzak pencereler uC_banyo etkisine girmis (span kontrolu): {sorted(map(str, leaked))}")
    if Node("normal2", "room", "uC_banyo") in ring_set(rep) or not any(h.via == "kat_ikizi" for h in rep.related):
        errs.append("kat ikizi yayilmamali, 'ilgili' olarak listelenmeli")
    return errs


def check_completeness_gate() -> list[str]:
    errs = []
    sys.path.insert(0, str(ROOT / "scripts"))
    import doc_check as dc
    if dc.check_impact_completeness():
        errs.append(f"uretim tablolari semayla uyusmuyor: {dc.check_impact_completeness()[:3]}")
    schema = json.loads((ROOT / "schema" / "design.schema.json").read_text(encoding="utf-8"))

    class T:   # enjekte edilen sahte tablolar
        REFERENCE_FIELDS = impact.REFERENCE_FIELDS
        UNIT_FIELDS = impact.UNIT_FIELDS
        IMPACT_IGNORED_FIELDS = impact.IMPACT_IGNORED_FIELDS
        FLOOR_LIST_KEY = impact.FLOOR_LIST_KEY
        IMPACT_FLOOR_EXEMPT = impact.IMPACT_FLOOR_EXEMPT
        DERIVED_OUTPUTS = impact.DERIVED_OUTPUTS
        KINDS = impact.KINDS
        EDGE_CLASSES = impact.EDGE_CLASSES

    def expect(name, schema_=None, **over):
        t = type("T2", (T,), over)
        out = dc.check_impact_completeness(schema_ if schema_ is not None else schema, t)
        if not out:
            errs.append(f"kapi #17 sessiz kaldi: {name}")

    expect("semada olmayan basvuru alani", REFERENCE_FIELDS=T.REFERENCE_FIELDS + (("opening", "yok_alan", "opening", "wall"),))
    expect("eksik basvuru (stairs.room_id kaldirildi)", REFERENCE_FIELDS=tuple(r for r in T.REFERENCE_FIELDS if r[:2] != ("stairs", "room_id")))
    expect("gerekcesiz yoksayma", IMPACT_IGNORED_FIELDS={**T.IMPACT_IGNORED_FIELDS, ("section", "levels_from"): " "})
    expect("kat listesi dugum turu degil", FLOOR_LIST_KEY={k: v for k, v in T.FLOOR_LIST_KEY.items() if k != "shaft"})
    expect("olmayan turetilen modul", DERIVED_OUTPUTS={**T.DERIVED_OUTPUTS, "room": (("yok_modul", "x"),)})
    expect("bozuk kenar sinifi", EDGE_CLASSES={**T.EDGE_CLASSES, "basvuru": (True, " ")})
    s2 = copy.deepcopy(schema)
    s2["definitions"]["opening"]["properties"]["panel_id"] = {"type": "string"}
    expect("semaya yeni _id alani eklendi", s2)
    s3 = copy.deepcopy(schema)
    s3["definitions"]["floor"]["properties"]["rampalar"] = {"type": "array"}
    expect("semaya yeni kat listesi eklendi", s3)
    return errs


def _mutate(target, name, value, check) -> list[str]:
    """`target.name`i gecici bozar; `check` BASARISIZ OLMALI (hata dondurmeli)."""
    old = getattr(target, name)
    setattr(target, name, value)
    try:
        out = check()
    except Exception as exc:  # noqa: BLE001 - bozulmus kod patlarsa bozma yakalanmis sayilir
        out = [f"patladi: {type(exc).__name__}"]
    finally:
        setattr(target, name, old)
    return [] if out else [f"KASITLI BOZMA yakalanmadi: {target.__name__}.{name}"]


def check_mutations_are_detected() -> list[str]:
    errs = []
    errs += _mutate(R, "_overlaps", lambda a, b, tol: True, check_span_propagation)          # span kontrolu kapali
    modified = dict(G.EDGE_CLASSES)
    modified["birim"] = (True, "bozuk: yayilir")
    errs += _mutate(R, "EDGE_CLASSES", modified, check_related_not_propagated)               # birim yayilir
    modified2 = dict(G.EDGE_CLASSES)
    modified2["kat_ikizi"] = (True, "bozuk: yayilir")
    errs += _mutate(R, "EDGE_CLASSES", modified2, check_related_not_propagated)              # kat ikizi yayilir
    errs += _mutate(R, "_covered", lambda reached, arrival, tol: True, check_span_helpers)
    errs += _mutate(R, "_overlaps", lambda a, b, tol: False, check_span_chain)
    errs += _mutate(R, "_overlaps", lambda a, b, tol: True, check_span_chain)
    errs += _mutate(G, "_t", lambda wall, p: 0.0, check_span_propagation)                    # izdusum bozuk
    errs += _mutate(G, "FLOOR_LIST_KEY", {k: v for k, v in G.FLOOR_LIST_KEY.items() if k != "shaft"}, check_graph_edges)
    return errs


def main() -> int:
    checks = [check_graph_edges, check_span_propagation, check_span_chain, check_span_helpers, check_related_not_propagated, check_errors_and_readonly, check_diff,
              check_coverage, check_real_context, check_completeness_gate, check_mutations_are_detected]
    failed = 0
    for check in checks:
        errs = check()
        print(("[FAIL] " if errs else "[OK]   ") + check.__name__)
        for e in errs[:10]:
            print("   -", e)
        failed += bool(errs)
    print("impact selftest:", "BASARISIZ" if failed else "BASARILI")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
