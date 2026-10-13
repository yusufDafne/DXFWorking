#!/usr/bin/env python3
"""testfit testleri (DEV-063). Beklenen degerler ELLE hesaplanir; her kural kasitli bozmayla (reasoning/selftest.py ve elle) sinanir.

Kullanim:  python scripts/testfit/selftest.py     Cikis: 0 basarili, 1 basarisiz.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import testfit as tf  # noqa: E402
from collision import check_context  # noqa: E402
from testfit import engine as eng  # noqa: E402
from testfit.library import BEDROOM_CLUSTERS  # noqa: E402

K = {c.id: c for c in BEDROOM_CLUSTERS}


def box_room(net_w, net_h, door=None, variant=None):
    """Duvar merkez cizgisinde poligon (4 duvar, 200 mm) -> NET = net_w x net_h. `door`: alt duvarda kapi genisligi."""
    w, h = net_w + 200, net_h + 200
    room = {"id": "oda", "room_type": "yatak_odasi", "polygon": [[0, 0], [w, 0], [w, h], [0, h]]}
    walls = [{"id": "w_alt", "start": [0, 0], "end": [w, 0], "thickness": 200.0, "layer": "D"},
             {"id": "w_sag", "start": [w, 0], "end": [w, h], "thickness": 200.0, "layer": "D"},
             {"id": "w_ust", "start": [w, h], "end": [0, h], "thickness": 200.0, "layer": "D"},
             {"id": "w_sol", "start": [0, h], "end": [0, 0], "thickness": 200.0, "layer": "D"}]
    openings = []
    if door:
        openings = [{"id": "kapi", "type": "door", "wall_id": "w_alt", "position_from_start": w / 2, "width": door,
                     **({"variant": variant} if variant else {})}]
    return room, walls, openings


def fits(cluster, net_w, net_h, door=None, variant=None):
    room, walls, openings = box_room(net_w, net_h, door, variant)
    sectors = tf.measure._sectors([room], walls, openings)
    return tf.try_fit(room, walls, sectors, K[cluster]).fits


def check_hand_computed_boundaries() -> list[str]:
    e = []
    # K4 tek yatak 900x2000: tam sigar / 1 mm eksik sigmaz (iki yon de)
    if fits("K4", 900, 2000) is not True or fits("K4", 2000, 900) is not True:
        e.append("K4: 900x2000 (iki yonde) net oda SIGMALI")
    if fits("K4", 900, 1990) is not False or fits("K4", 899, 2100) is not False or fits("K4", 1500, 1500) is not False:
        e.append("K4: 900x1990 / 899x2100 / 1500x1500 net oda SIGMAMALI")
    # K2 cift yatak 1600x2000 + gardirop 1800x600: yan yana (dikey gardirop 600x1800) 1600+600=2200 x 2000
    if fits("K2", 2200, 2000) is not True:
        e.append("K2: 2200x2000 net (yatak 1600 + dikey gardirop 600) SIGMALI")
    # collision temas toleransi 5 mm (CONTACT_TOLERANCE): <=5 mm girisim TEMASTIR -> 2195 sigar, 2194 sigmaz (collision ile ayni kural)
    if fits("K2", 2195, 2000) is not True or fits("K2", 2194, 2000) is not False or fits("K2", 2000, 2000) is not False:
        e.append("K2: 2195x2000 sigar (5 mm temas toleransi), 2194x2000 ve 2000x2000 SIGMAZ (yatak+gardirop 2200 genislik ya da 2600 yukseklik ister)")
    if fits("K2", 1800, 2600) is not True:
        e.append("K2: 1800x2600 net (alt alta: yatak 2000 + yatay gardirop 600) SIGMALI")
    # K1 = K2 + iki komodin 450x400: K2'nin sigdigi 2200x2000'e komodinler sigmaz (alan yok), genis odaya sigar
    if fits("K1", 2200, 2000) is not False:
        e.append("K1: 2200x2000 net odaya iki komodin ek olarak SIGMAMALI")
    if fits("K1", 3000, 3000) is not True:
        e.append("K1: 3000x3000 net oda SIGMALI")
    return e


def check_door_sector_is_respected() -> list[str]:
    """Kapi acilim sektoru engeldir (collision kapisi ile ayni kural); surme kapi sektor uretmez; yanlis-pozitif yok."""
    e = []
    if fits("K2", 2200, 2000) is not True:
        return ["on kosul: kapisiz 2200x2000 K2 sigmali"]
    if fits("K2", 2200, 2000, door=900) is not False:
        e.append("kapi acilim sektoru K2'yi engellemeli (2200x2000 odada bos alan yok)")
    if fits("K2", 2200, 2000, door=900, variant="sliding") is not True:
        e.append("surme kapi acilim alani GEREKTIRMEZ: K2 sigmali (yanlis-pozitif)")
    if fits("K4", 3000, 3000, door=900) is not True:
        e.append("genis odada kapi sektoru K4'u engellememeli (yanlis-pozitif)")
    return e


def check_non_rectangular_room() -> list[str]:
    e = []
    def l_room(arm):
        poly = [[0, 0], [2000, 0], [2000, 500], [arm, 500], [arm, 2000], [0, 2000]]
        return {"id": "L", "room_type": "yatak_odasi", "polygon": poly}
    if tf.try_fit(l_room(900), [], [], K["K4"]).fits is not True:
        e.append("L oda: 900x2000 kol tek yatagi alir")
    if tf.try_fit(l_room(850), [], [], K["K4"]).fits is not False:
        e.append("L oda: 850 genis kol + 500 yuksek bacak tek yatagi ALMAZ")
    return e


def check_budget_gives_unmeasured_not_no() -> list[str]:
    e = []
    old = eng.MAX_NODES
    try:
        eng.MAX_NODES = 1
        r = fits("K1", 3000, 3000)
    finally:
        eng.MAX_NODES = old
    if r is not None:
        e.append(f"arama butcesi asilinca sonuc 'olculemedi' (None) olmali, 'sigmaz' DENMEMELI: {r}")
    return e


def check_consistent_with_collision_on_real_project() -> list[str]:
    """Tefrissiz rev-28: her yatak odasi icin cevap uretilir; donen yerlesim gercek `collision.check_context` ile CELISMEZ
    (tefris VAR projede ayni kural: blok ekleme noktasi + rotasyon sozlesmesi); kasitli kaydirma yakalanir."""
    e = []
    ctx = json.loads((ROOT / "context.json").read_text(encoding="utf-8"))
    floor = next(f for f in ctx["floors"] if f["id"] == "normal1")
    cap = tf.bedroom_capacity(floor["rooms"], floor["walls"], floor["openings"])
    if set(cap) != {"uA_oda1", "uA_oda2", "uB_oda1", "uB_oda2", "uC_oda"} or any(v != "K1" for v in cap.values()):
        e.append(f"normal1: bes yatak odasinin hepsine K1 sigmali (elle: uC_oda net 2950x3175): {cap}")
    sectors = tf.measure._sectors(floor["rooms"], floor["walls"], floor["openings"])
    furniture = []
    for room in (r for r in floor["rooms"] if r.get("room_type") == "yatak_odasi"):
        res = tf.try_fit(room, floor["walls"], sectors, K["K1"])
        for i, p in enumerate(res.placements):
            furniture.append({"id": f"{room['id']}_{i}", "type": p.type, "position": list(p.position), "rotation": p.rotation})
    ctx2 = json.loads(json.dumps(ctx))
    ctx2["floors"] = [dict(floor, furniture=furniture)]
    ctx2["elevations"] = ctx["elevations"]
    blocking = [c for c in check_context(ctx2).clashes if c.blocking and ("tefris" in (c.a.tag, getattr(c.b, "tag", "")))]
    if blocking:
        e.append(f"deneme yerlesimi collision ile CELISIYOR: {[c.message() for c in blocking[:2]]}")
    if len(furniture) != 20:
        e.append(f"5 oda x K1 (4 parca) = 20 tefris beklenirdi: {len(furniture)}")
    # kasitli bozma: bir parcayi 300 mm kaydir -> collision YAKALAMALI (test gercekten bir sey olcuyor)
    shifted = json.loads(json.dumps(furniture))
    shifted[0]["position"][0] += 300.0
    shifted[0]["position"][1] += 300.0
    ctx3 = json.loads(json.dumps(ctx2))
    ctx3["floors"][0]["furniture"] = shifted
    bad = [c for c in check_context(ctx3).clashes if c.blocking and ("tefris" in (c.a.tag, getattr(c.b, "tag", "")))]
    if not bad:
        e.append("kasitli kaydirma collision tarafindan YAKALANMADI - tutarlilik testi anlamsiz")
    return e


def main() -> int:
    checks = [check_hand_computed_boundaries, check_door_sector_is_respected, check_non_rectangular_room,
              check_budget_gives_unmeasured_not_no, check_consistent_with_collision_on_real_project]
    failed = 0
    for check in checks:
        try:
            errs = check()
        except Exception as exc:  # noqa: BLE001
            errs = [f"kontrol coktu: {type(exc).__name__}: {exc}"]
        print(("[FAIL] " if errs else "[OK]   ") + check.__name__)
        for er in errs[:10]:
            print("   -", er)
        failed += bool(errs)
    print("testfit selftest:", "BASARISIZ" if failed else "BASARILI")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
