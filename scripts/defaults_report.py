"""Kullanilan KATALOG VARSAYILANLARINI adiyla bildirir (DEV-072; DEV-069 ilkesi: sessiz varsayilan yok). SALT OKUNUR.

`python scripts/defaults_report.py [context.json]` - su an: pencere yuksekligi/denizlik (openings.heights); `--catalog`: sinif katalogu (openings.classes). Baska modullerin
varsayilanlari (merdiven, saft, cekirdek) kendi katalog sabitleridir ve soru katalogunda (PROJECT_OPERATOR_AGENT.md) listelidir;
bu rapor yalniz PROJE VERISINDE eksik oldugu icin KULLANILAN varsayilanlari sayar.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import elevations  # noqa: E402
import openings  # noqa: E402

DESCRIPTIONS = {
    "DEFAULT_WINDOW_HEIGHT_MM": "pencere yuksekligi (normal): {v} mm",
    "DEFAULT_WINDOW_SILL_MM": "pencere denizligi (normal): zeminden {v} mm",
    "DEFAULT_TALL_WINDOW_HEIGHT_MM": "boy pencere yuksekligi: {v} mm",
    "DEFAULT_TALL_WINDOW_SILL_MM": "boy pencere denizligi: {v} mm",
    "DEFAULT_SHOPFRONT_HEIGHT_MM": "vitrin yuksekligi: {v} mm",
    "DEFAULT_SHOPFRONT_SILL_MM": "vitrin denizligi: {v} mm",
    "DEFAULT_MAIN_ENTRY_HEIGHT_MM": "ana giris kapisi yuksekligi: {v} mm",
    "DEFAULT_MAIN_ENTRY_SILL_MM": "ana giris kapisi esigi (denizlik): {v} mm",
    "DEFAULT_SHOP_DOOR_HEIGHT_MM": "dukkan kapisi yuksekligi: {v} mm",
    "DEFAULT_SHOP_DOOR_SILL_MM": "dukkan kapisi esigi (denizlik): {v} mm",
}


def catalog() -> None:
    """DEV-076: acikliklarin SINIF katalogu (varsayilan olculer, kaynak sabit adlari, not)."""
    print(f"Aciklik siniflari katalogu ({openings.heights.DEFAULT_SOURCE}); kullanici degeri (width/height/sill_height) her zaman varsayilani ezer:")
    for spec in openings.OPENING_CLASSES.values():
        w = "proje verisi" if spec.width_mm is None else f"{spec.width_mm:g}"
        print(f"  - {spec.key:18s} [{spec.field}={spec.value}] genislik {w} / yukseklik {spec.height_mm:g} / denizlik {spec.sill_mm:g} mm"
              f"  ({', '.join(n for n in spec.names if n)})  - {spec.note}")


def main(argv=None) -> int:
    if argv and "--catalog" in argv:
        catalog()
        return 0
    path = Path(argv[0] if argv else Path(__file__).resolve().parent.parent / "context.json")
    ctx = json.loads(path.read_text(encoding="utf-8"))
    used = openings.defaults_used(ctx)
    facade_used = elevations.derive.defaults_used_on_facades(ctx)
    if not used and not facade_used:
        print("Kullanilan katalog varsayilani yok.")
        return 0
    print(f"Kullanilan katalog varsayilanlari ({openings.heights.DEFAULT_SOURCE}):")
    for name, n in used.items():
        v = getattr(openings.classes, name)
        print(f"  - {name} = {v:g}: {DESCRIPTIONS[name].format(v=f'{v:g}')} ({n} pencerede)")
    for label, n in facade_used.items():
        print(f"  - {label}: {n} kapi (DEV-073, kullanici karari: dukkan kapilari boy pencere)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
