"""Kullanilan KATALOG VARSAYILANLARINI adiyla bildirir (DEV-072; DEV-069 ilkesi: sessiz varsayilan yok). SALT OKUNUR.

`python scripts/defaults_report.py [context.json]` - su an: pencere yuksekligi/denizlik (openings.heights). Baska modullerin
varsayilanlari (merdiven, saft, cekirdek) kendi katalog sabitleridir ve soru katalogunda (PROJECT_OPERATOR_AGENT.md) listelidir;
bu rapor yalniz PROJE VERISINDE eksik oldugu icin KULLANILAN varsayilanlari sayar.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import openings  # noqa: E402

DESCRIPTIONS = {
    "DEFAULT_WINDOW_HEIGHT_MM": "pencere yuksekligi (normal): {v} mm",
    "DEFAULT_TALL_WINDOW_HEIGHT_MM": "boy pencere yuksekligi: {v} mm",
    "DEFAULT_TALL_WINDOW_SILL_MM": "boy pencere denizligi: {v} mm",
}


def main(argv=None) -> int:
    path = Path(argv[0] if argv else Path(__file__).resolve().parent.parent / "context.json")
    ctx = json.loads(path.read_text(encoding="utf-8"))
    used = openings.defaults_used(ctx)
    if not used:
        print("Kullanilan katalog varsayilani yok.")
        return 0
    print(f"Kullanilan katalog varsayilanlari ({openings.heights.DEFAULT_SOURCE}):")
    for name, n in used.items():
        if name == "(denizlik verilmedi)":
            print(f"  - {n} pencerede denizlik VERILMEDI (varsayilan yok, uydurulmaz; cephe/oran olcumu bu degere ihtiyac duyarsa durur ve sorar)")
        else:
            v = getattr(openings.heights, name)
            print(f"  - {name} = {v:g}: {DESCRIPTIONS[name].format(v=f'{v:g}')} ({n} pencerede)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
