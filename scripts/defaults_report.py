"""Kullanilan KATALOG VARSAYILANLARINI adiyla bildirir (DEV-072; DEV-069 ilkesi: sessiz varsayilan yok). SALT OKUNUR.

`python scripts/defaults_report.py [context.json]` - su an: pencere yuksekligi/denizlik (openings.heights) + `site.setbacks` yoksa uygulanacak imar varsayilanlari (vaziyet.zoning, DEV-086); `--catalog`: sinif katalogu (openings.classes) + imar standart deger katalogu. Baska modullerin
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
import vaziyet  # noqa: E402

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


def zoning_catalog() -> None:
    """DEV-086: imar standart deger katalogu (cekme/TAKS/KAKS) - DOGRULANMAMIS, kullanici gercek yonetmelikle degistirecek."""
    print("Imar standart deger katalogu (vaziyet/zoning.py; DOGRULANMADI - kullanici gercek yonetmelikle belirleyecek; kullanici degeri her zaman ezer):")
    for z in vaziyet.ZONING_DEFAULTS.values():
        val = "kural metni (sayi yok)" if z.value is None else f"{z.value:g} {z.unit}"
        print(f"  - {z.name:32s} = {val:24s} {z.label}; kosul: {z.condition}; nizam: {z.nizam}; kaynak: {z.source} ({z.researched_on})")
        for u in z.urls:
            print(f"        {u}")


def site_defaults(ctx: dict) -> list[str]:
    """`site` var ama `site.setbacks` YOKSA: hangi varsayilanlarin UYGULANACAGINI soyler (UYGULAMAZ; patch kullanici onayiyla)."""
    site = ctx.get("site")
    if not site or site.get("setbacks") or "parcel" not in site:
        return []
    try:
        sb, res = vaziyet.setbacks_for_parcel(vaziyet.Parcel.from_polygon(site["parcel"]["polygon"]), site.get("road_edges", []))
    except vaziyet.VaziyetError as exc:
        return [f"site.setbacks verilmemis ve varsayilan uygulanamiyor: {exc}"]
    return [f"site.setbacks verilmemis; kullanici degeri gelmezse sunlar UYGULANIRDI (edges_mm = {sb['edges_mm']}):"] + [f"  {x}" for x in res.describe()]


def main(argv=None) -> int:
    if argv and "--catalog" in argv:
        catalog()
        print()
        zoning_catalog()
        return 0
    path = Path(argv[0] if argv else Path(__file__).resolve().parent.parent / "context.json")
    ctx = json.loads(path.read_text(encoding="utf-8"))
    used = openings.defaults_used(ctx)
    facade_used = elevations.derive.defaults_used_on_facades(ctx)
    site_lines = site_defaults(ctx)
    if not used and not facade_used:
        print("Kullanilan katalog varsayilani yok.")
        for line in site_lines:
            print(line)
        return 0
    print(f"Kullanilan katalog varsayilanlari ({openings.heights.DEFAULT_SOURCE}):")
    for name, n in used.items():
        v = getattr(openings.classes, name)
        print(f"  - {name} = {v:g}: {DESCRIPTIONS[name].format(v=f'{v:g}')} ({n} pencerede)")
    for label, n in facade_used.items():
        print(f"  - {label}: {n} kapi (DEV-073, kullanici karari: dukkan kapilari boy pencere)")
    for line in site_lines:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
