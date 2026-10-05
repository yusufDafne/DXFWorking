#!/usr/bin/env python3
"""Etut (kat zonlama) ornek cikti raporu - YALNIZ OKUR/YAZDIRIR (DEV-056).

Kullanici ornek ciktilari yorumlayip agirlik katsayilarinin zaman icinde
optimize edilmesi icindir. Hicbir dosyaya YAZMAZ, context.json'a DOKUNMAZ.

Kullanim:
    python scripts/architect/study_report.py <kat_genislik_mm> <kat_derinlik_mm> <tip> [<tip> ...] [tercihler]
    python scripts/architect/study_report.py 20000 17500 2+1 2+1 1+1
    python scripts/architect/study_report.py 20000 17500 2+1 2+1 1+1 --hall=koridor --area=uA:100
Birimler uA, uB, uC ... olarak adlandirilir. Tercihler (DEV-057 Grup B; dil modelinin
dogal dil talebinden cevirdigi yapi): --hall=<kare|dikdortgen|koridor|id>,
--centered | --shifted, --area=uA:95,uB:100, --side=uA:south,uB:north.
Sonda secim sonucu (tercihe en yakin aday ya da merkezi hol geri donusu) yazdirilir.
Cikis kodu 0.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from architect import (select_study_option, study_floor,  # noqa: E402
                       suggest_unit_mixes)


def main(argv: list[str]) -> int:
    if len(argv) < 4:
        print(__doc__)
        return 1
    width, depth = float(argv[1]), float(argv[2])
    flags = [a for a in argv[3:] if a.startswith("--")]
    program = tuple((f"u{chr(65 + i)}", t) for i, t in enumerate(a for a in argv[3:] if not a.startswith("--")))
    print(f"Kat {width:.0f} x {depth:.0f} mm ({width * depth / 1e6:.1f} m2), program: "
          f"{', '.join(t for _, t in program)}")
    top_mixes = suggest_unit_mixes(width, depth)[:3]
    if top_mixes:
        print("Hesaplanmis karisim onerileri (dil modeli geri bildirimi icin): "
              + "; ".join(f"[{', '.join(m['mix'])}] (doluluk {m['fill_ratio']:.2f})" for m in top_mixes))
    options = study_floor(width, depth, program, top=60)
    if not options:
        print("Uygulanabilir merkezi cekirdek blogu bulunamadi.")
        return 0
    shown = options[:5]
    for rank, option in enumerate(shown, 1):
        print(f"\n#{rank} {option.id}  puan={option.score:.4f}  uygulanabilir={option.feasible}")
        print(f"   hol: {option.hall_option}, desen: {option.pattern}, blok: {tuple(round(v) for v in option.block)}, "
              f"kayma: {tuple(round(v) for v in option.offset)}")
        print("   puan dokumu: " + ", ".join(f"{k}={v:.3f}" for k, v in option.breakdown.items()))
        for z in option.zones:
            rects = "; ".join(f"[{r[0]:.0f},{r[1]:.0f}-{r[2]:.0f},{r[3]:.0f}]" for r in z.rects)
            print(f"   {z.unit_id} {z.unit_type}: {z.area_m2:.1f} m2, hol temasi {z.access_mm:.0f}mm, "
                  f"cephe {z.facade_mm:.0f}mm, en dar {z.short_edge_mm:.0f}mm, hol onerisi={z.hall_topology}  {rects}")
        for problem in option.problems:
            print(f"   SORUN: {problem}")
    preference = _preference(flags)
    selection = select_study_option(options, preference, width, depth)
    print(f"\nSECIM: {selection.option.id} (hol {selection.option.hall_option}, kayma "
          f"{tuple(round(v) for v in selection.option.offset)}, geri donus={selection.fallback}) - {selection.reason}")
    return 0


def _preference(flags: list[str]):
    from architect import StudyPreference
    if not flags:
        return None
    kwargs: dict = {}
    for f in flags:
        key, _, value = f[2:].partition("=")
        if key == "hall":
            kwargs["hall"] = value
        elif key == "centered":
            kwargs["centered_hall"] = True
        elif key == "shifted":
            kwargs["centered_hall"] = False
        elif key == "area":
            kwargs["unit_area_m2"] = {u: float(v) for u, v in (p.split(":") for p in value.split(","))}
        elif key == "side":
            kwargs["unit_side"] = {u: v for u, v in (p.split(":") for p in value.split(","))}
    return StudyPreference(**kwargs)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
