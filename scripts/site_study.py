#!/usr/bin/env python3
"""Vaziyet yerlesim etudu (DEV-083) - SALT OKUNUR: context.json'a YAZMAZ, DXF cizmez.

    python scripts/site_study.py context.json --step-mm 5000 --rotations 0,90 [--n 3] [--weights road_proximity=2,light_south=1]
                                 [--min-separation-mm X] [--taks 0.4] [--kaks 1.2] [--floors 5] [--json]

Adim (`--step-mm`) ve donus kumesi (`--rotations`) ZORUNLUDUR: varsayilan uydurulmaz. Cekme `site.setbacks`ten; yoksa imar kataloguna dusulur
(KULLANILAN VARSAYILAN ADIYLA, 'DOGRULANMADI' ibaresiyle bildirilir). Alternatif sayisi varsayilan 3.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from vaziyet import DEFAULT_ALTERNATIVES, OBJECTIVE_LABEL, Parcel, VaziyetError, buildable_area, narrate_alternative, resolve_zoning, run_study, setbacks_for_parcel  # noqa: E402


def _opt(args, name, cast=str):
    if name in args:
        i = args.index(name)
        val = cast(args[i + 1])
        del args[i:i + 2]
        return val
    return None


def main(argv=None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    as_json = "--json" in args
    if as_json:
        args.remove("--json")
    step = _opt(args, "--step-mm", float)
    rots = _opt(args, "--rotations", lambda s: [float(x) for x in s.split(",") if x != ""])
    n = _opt(args, "--n", int)
    wtxt = _opt(args, "--weights")
    sep = _opt(args, "--min-separation-mm", float)
    taks_u = _opt(args, "--taks", float)
    kaks_u = _opt(args, "--kaks", float)
    floors = _opt(args, "--floors", int)
    if not args or step is None or not rots:
        print(__doc__)
        return 2
    ctx = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    site = ctx.get("site") or {}
    meta = ctx.get("meta", {})
    try:
        if not site.get("parcel"):
            raise VaziyetError("context.json'da site.parcel yok")
        if not meta.get("floor_width") or not meta.get("floor_depth"):
            raise VaziyetError("meta.floor_width/floor_depth yok: bina ayak izi bilinmiyor (uydurulmaz)")
        parcel = Parcel.from_polygon(site["parcel"]["polygon"])
        roads = list(site.get("road_edges", []))
        notices: list[str] = []
        user = {k: v for k, v in (("taks", taks_u), ("kaks", kaks_u)) if v is not None}
        res = resolve_zoning(user)
        if site.get("setbacks"):
            buildable = buildable_area(parcel, site["setbacks"])
        else:
            sb, sres = setbacks_for_parcel(parcel, roads, user)
            buildable = buildable_area(parcel, sb)
            notices += ["site.setbacks yok: imar katalogu varsayilani kullanildi."] + sres.describe()
        taks = {"value": res.values["taks"], "source": res.sources["taks"]} if res.values.get("taks") is not None else None
        kaks = {"value": res.values["kaks"], "source": res.sources["kaks"]} if res.values.get("kaks") is not None else None
        for z in res.used_defaults:
            if z.key == "taks":
                notices += [x for x in res.describe() if "TAKS" in x and x not in notices]
        weights = None
        if wtxt:
            weights = {k: float(v) for k, v in (kv.split("=") for kv in wtxt.split(","))}
        result = run_study(site["parcel"]["polygon"], buildable, float(meta["floor_width"]), float(meta["floor_depth"]), step_mm=step, rotations_deg=rots,
                           n=n or DEFAULT_ALTERNATIVES, weights=weights, road_edges=roads, zone=(site.get("placement_zone") or {}).get("polygon"),
                           north_confirmed=bool(site.get("north_confirmed")), min_separation_mm=sep, taks=taks, kaks=kaks, floor_count=floors)
    except (VaziyetError, ValueError, KeyError) as exc:
        print("ETUT YAPILAMADI:", exc)
        return 1
    if as_json:
        out = result.to_dict()
        out["notices"] = notices
        print(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    print(f"Aday: {result.generated}, elenen: {sum(result.eliminated.values())} {dict(sorted(result.eliminated.items()))}, kalan: {result.survivors}")
    print("Takas eksenleri:", ", ".join(OBJECTIVE_LABEL[a] for a in result.parameters["axes"]) or "-")
    for line in notices:
        print("BILGI:", line)
    for a in result.alternatives:
        print(f"\n{a.id} - konum {a.position[0]:.0f}, {a.position[1]:.0f} mm; donus {a.rotation_deg:g} derece; kat plani kuzey acisi {a.plan_north_angle:g} derece")
        for line in narrate_alternative(a):
            print(line)
    for c in result.ceilings:
        val = "olculemedi" if c["value"] is None else f"{c['value']:.3f}"
        print(f"\n{c['name']}: {val} (tavan {c['limit']:g}, kaynak {c['limit_source']}) -> {'TAMAM' if c['ok'] else ('ASILIYOR' if c['ok'] is False else 'olculemedi')}")
    for note in result.notes:
        print("NOT:", note)
    return 0


if __name__ == "__main__":
    sys.exit(main())
