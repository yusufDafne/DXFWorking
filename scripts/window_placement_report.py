"""Pencere yerlesim raporu (DEV-075, SALT OKUNUR): mevcut pencerelerin ait oldugu odanin dis duvar boyunca SERBEST araligina
(ic duvarlarin baglandigi yerler cikarilmis) gore ORTALANMIS konum onerisi + ic duvar birlesimine dusen pencereler.
`python scripts/window_placement_report.py [context.json] [--min-delta MM]` - context'e yazmaz; oneriyi uygulamak bir REVIZYONDUR."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import openings  # noqa: E402


def main(argv=None) -> int:
    args = list(argv or [])
    min_delta = 0.0
    if "--min-delta" in args:
        i = args.index("--min-delta")
        min_delta = float(args[i + 1])
        del args[i:i + 2]
    path = Path(args[0] if args else Path(__file__).resolve().parent.parent / "context.json")
    ctx = json.loads(path.read_text(encoding="utf-8"))
    groups: dict[tuple, list[str]] = {}
    junction_lines = []
    for fl in ctx["floors"]:
        for w in openings.check_window_junctions(fl):
            junction_lines.append(f"[{fl['id']}] {w}")
        for s in openings.placement_suggestions(fl):
            key = (s["window"], s["wall"], s["room"], s["current"], s["suggested"], s["shared"])
            groups.setdefault(key, []).append(fl["id"])
    print("Birlesime dusen pencereler: " + ("YOK" if not junction_lines else ""))
    for line in junction_lines:
        print("  -", line)
    print("Ortalanmis konum onerisi (merkez, mm; kat listesi ozdes katlari birlestirir):")
    shown = 0
    for (win, wall, room, cur, sug, shared), floors in groups.items():
        if room is None:
            print(f"  - {win} ({wall}): ait oldugu oda bulunamadi - oneri YOK [{', '.join(floors)}]")
            shown += 1
        elif sug is None:
            print(f"  - {win} ({wall}, {room}): pencere serbest araliga SIGMIYOR - oneri YOK [{', '.join(floors)}]")
            shown += 1
        elif abs(sug - cur) > min_delta:
            note = f"  (oda/duvarda {shared} pencere: oneri tek pencere varsayar)" if shared > 1 else ""
            print(f"  - {win} ({wall}, {room}): {cur:.0f} -> {sug:.0f} ({sug - cur:+.0f}){note} [{', '.join(floors)}]")
            shown += 1
    if not shown:
        print("  (esigin ustunde sapma yok)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
