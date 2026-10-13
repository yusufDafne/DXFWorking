#!/usr/bin/env python3
"""Basit ORNEK vaziyet DXF'i uretir (DEV-082). Kullaniciya 'vaziyet planinizi boyle sade bir DXF olarak gonderin' diye verilir.

    python scripts/site_sample.py [cikti.dxf]      (varsayilan: scripts/vaziyet/samples/ornek_vaziyet.dxf)
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from vaziyet import write_sample  # noqa: E402


def main(argv=None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    out = Path(args[0]) if args else HERE / "vaziyet" / "samples" / "ornek_vaziyet.dxf"
    print(f"Ornek vaziyet DXF'i uretildi: {write_sample(out)}")
    print("Katmanlar: PARSEL (kapali polyline), YERLESIM_ALANI (binanin yaklasik oturmasini istediginiz bolge, kapali polyline), YOL (cizgi), NOT (kisa metinler), KUZEY (yukari bakan ok + 'K').")
    return 0


if __name__ == "__main__":
    sys.exit(main())
