#!/usr/bin/env python3
"""Vaziyet DXF'ini SALT OKUNUR tarar ve adaylari raporlar (DEV-082). Context'e YAZMAZ, aday SECMEZ.

    python scripts/site_scan.py vaziyet.dxf [--patch c0[,c1]]   --patch: secilen aday kimlikleriyle `site` PATCH taslagini basar (parsel[,yerlesim alani])
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from vaziyet import DxfInputError, VaziyetError, build_site_patch, scan_site_dxf  # noqa: E402


def main(argv=None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    patch = None
    if "--patch" in args:
        i = args.index("--patch")
        patch = args[i + 1].split(",")
        del args[i:i + 2]
    if not args:
        print(__doc__)
        return 2
    try:
        scan = scan_site_dxf(args[0])
    except DxfInputError as exc:
        print("HATA:", exc)
        return 1
    print(f"Dosya: {scan.path} (sha256 {scan.sha256[:12]}...) birim: {scan.units or 'BILINMIYOR'}")
    print(f"Kuzey isareti: {scan.north['status']}" + (f" ({scan.north['direction_deg']:.1f} derece)" if scan.north.get("direction_deg") is not None else ""))
    print(f"Adaylar ({len(scan.candidates)}):")
    for c in scan.candidates:
        area = "?" if c.area_mm2 is None else f"{c.area_mm2 / 1e6:.1f} m2"
        print(f"  - {c.id}: {c.source}, katman '{c.layer}', {len(c.points)} kose, alan {area}, ipucu: {c.layer_hint or '-'}, "
              + ("GECERLI" if c.valid else "GECERSIZ: " + "; ".join(c.problems)))
    for seg in scan.road_segments_mm[:3]:
        print(f"  yol cizgisi: {seg[0]} -> {seg[1]}")
    for t in scan.texts:
        print(f"  metin [{t['layer']}]: {t['text']!r}")
    for u in scan.unsupported:
        print("  desteklenmeyen:", u)
    for w in scan.warnings:
        print(w)
    if patch:
        try:
            print(json.dumps(build_site_patch(scan, patch[0], patch[1] if len(patch) > 1 else None), ensure_ascii=False, indent=2))
        except VaziyetError as exc:
            print("PATCH URETILEMEDI:", exc)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
