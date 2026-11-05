#!/usr/bin/env python3
"""Vaziyet paftasi / alternatif karsilastirma DXF'i (DEV-084) - ana plan.dxf'ten BAGIMSIZ cikti. context.json'a YAZMAZ.

    python scripts/site_export.py context.json --scale 1/500 [--out output/vaziyet.dxf]
        site.building (SECILMIS yerlesim) icin tek vaziyet paftasi
    python scripts/site_export.py context.json --scale 1/500 --study --step-mm 5000 --rotations 0,90 [--n 3] [--weights ad=deger,...]
                                 [--min-separation-mm X] [--taks 0.4] [--kaks 1.2] [--floors 5]
        etut alternatifleri yan yana (her biri bir pafta; olculmus nitelikler pafta altinda)

Olcek ZORUNLU (1/200 ya da 1/500). Dosya baska programda aciksa `<ad>_N.dxf` yedegine kaydedilir (generate_dxf.py ile ayni kural).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from generate_dxf import save_with_fallback  # noqa: E402
from vaziyet import SITE_SCALES, VaziyetError, render_site_views, study_from_context, view_from_building, views_from_study  # noqa: E402
from pafta import PaftaOverflowError  # noqa: E402


def _opt(args, name, cast=str):
    if name in args:
        i = args.index(name)
        val = cast(args[i + 1])
        del args[i:i + 2]
        return val
    return None


def main(argv=None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    study = "--study" in args
    if study:
        args.remove("--study")
    scale = _opt(args, "--scale")
    out = _opt(args, "--out")
    step = _opt(args, "--step-mm", float)
    rots = _opt(args, "--rotations", lambda s: [float(x) for x in s.split(",") if x != ""])
    n = _opt(args, "--n", int)
    wtxt = _opt(args, "--weights")
    sep = _opt(args, "--min-separation-mm", float)
    taks = _opt(args, "--taks", float)
    kaks = _opt(args, "--kaks", float)
    floors = _opt(args, "--floors", int)
    if not args or scale is None or (study and (step is None or not rots)):
        print(__doc__)
        return 2
    if scale not in SITE_SCALES:
        print(f"HATA: vaziyet olcegi {SITE_SCALES} icinden secilmeli (verilen: {scale!r}); varsayilan yok")
        return 2
    ctx_path = Path(args[0])
    ctx = json.loads(ctx_path.read_text(encoding="utf-8"))
    try:
        if study:
            weights = {k: float(v) for k, v in (kv.split("=") for kv in wtxt.split(","))} if wtxt else None
            result, notices, buildable = study_from_context(ctx, step_mm=step, rotations_deg=rots, n=n, weights=weights, min_separation_mm=sep,
                                                            taks=taks, kaks=kaks, floors=floors)
            if not result.alternatives:
                print("ALTERNATIF YOK:", "; ".join(result.notes))
                return 1
            views = views_from_study(ctx, result, buildable)
            for line in notices + result.notes:
                print("BILGI:", line)
        else:
            views = [view_from_building(ctx)]
        doc, sheets = render_site_views(views, scale, ctx.get("meta"))
    except (VaziyetError, PaftaOverflowError, ValueError, KeyError) as exc:
        print("VAZIYET CIKTISI URETILEMEDI:", exc)
        return 1
    out_path = Path(out) if out else ctx_path.parent / "output" / "vaziyet.dxf"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    final = save_with_fallback(lambda p: doc.saveas(p), out_path)
    print(f"{len(sheets)} pafta yazildi: {final}")
    for s in sheets:
        print(f"  {s['label']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
