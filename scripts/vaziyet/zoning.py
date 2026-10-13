"""Imar STANDART DEGER katalogu (DEV-086): cekme (yapi yaklasma), TAKS, KAKS varsayilanlari.

KULLANICI KARARI (2026-10-13): kullanici bu degerleri dil modeline ayrica verir; BILINMIYORSA standart degerler kullanilir. Bu katalog o standart
degerlerdir - kisa bir arastirmayla (2026-10-13) kaydedildi, kaynaklari IKINCILDIR ve `verified=False` (DOGRULANMADI). Kullanici gercek yonetmelik verisiyle
degistirecektir. Kullanici degeri HER ZAMAN varsayilani ezer; kullanilan her varsayilan ADIYLA bildirilir (`describe`); KOSUL eslesmiyorsa varsayilan
UYGULANMAZ (soru doner). v1 yalniz AYRIK nizam. Bu bir PROJE VERISI DEGILDIR (`context.json`a yazilmaz); `standards/` ile ayni kutuphane sozlesmesi.

Katalog degerleri BAGIMSIZ literal sayilardir (hesaplanmaz, birbirine baglanmaz): biri degisince digeri degismez.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

try:
    from .parcel import Parcel, VaziyetError
except ImportError:
    from parcel import Parcel, VaziyetError  # type: ignore

RESEARCHED_ON = "2026-10-13"

# --- cekme (asgari; uygulama imar planinda aksi hukum yoksa) ---
DEFAULT_FRONT_SETBACK_MM = 5000.0
DEFAULT_SIDE_SETBACK_MM = 3000.0
DEFAULT_REAR_SETBACK_MM = 3000.0
# --- TAKS (tavan) ---
DEFAULT_TAKS = 0.40                       # uygulama imar planinda TAKS belirtilmeyen ayrik/blok nizam
DEFAULT_TAKS_MAX_WITHOUT_KAKS = 0.60      # KAKS (emsal) belirtilmeyen parselde TAKS en cok (emsal siniri icinde kalmak kaydiyla)

_URL_ZONING = "https://alomaliye.com/2017/07/03/planli-alanlar-imar-yonetmeligi/"
_URL_IZMIR = "https://www.izmir.bel.tr:443/YuklenenDosyalar/Dokumanlar/13022024141408.pdf"
_URL_BURSA = "https://www.bursahakimiyet.com.tr/gundem/imar-yonetmeligi-nde-kapsamli-degisiklik-yapildi-1660706"
_URL_MUSAVIRLER = "https://musavirlerkulubu.com.tr/makale/planli-alanlar-imar-yonetmeligi-degisikligi-ve-emsal-asansor-hukumleri-2026"


@dataclass(frozen=True)
class ZoningValue:
    key: str                 # kullanici/patch anahtari
    name: str                # sabit adi (bildirimde gorunur)
    value: float | None      # None = SAYI YOK (kural metni)
    unit: str
    label: str
    condition: str           # varsayilanin gecerli oldugu KOSUL
    nizam: str
    source: str
    urls: tuple[str, ...]
    researched_on: str = RESEARCHED_ON
    verified: bool = False   # kullanici gercek yonetmelikle dogrulayana dek False


ZONING_DEFAULTS: dict[str, ZoningValue] = {
    "front_setback_mm": ZoningValue("front_setback_mm", "DEFAULT_FRONT_SETBACK_MM", DEFAULT_FRONT_SETBACK_MM, "mm", "on bahce / yol kenari cekmesi (asgari)",
                                    "uygulama imar planinda aksi hukum yoksa", "ayrik", "Planli Alanlar Imar Yonetmeligi md. 24 (ikincil alinti)",
                                    (_URL_IZMIR, _URL_ZONING)),
    "side_setback_mm": ZoningValue("side_setback_mm", "DEFAULT_SIDE_SETBACK_MM", DEFAULT_SIDE_SETBACK_MM, "mm", "yan bahce cekmesi (asgari)",
                                   "uygulama imar planinda aksi hukum yoksa", "ayrik", "Planli Alanlar Imar Yonetmeligi md. 24 (ikincil alinti)",
                                   (_URL_IZMIR, _URL_ZONING)),
    "rear_setback_mm": ZoningValue("rear_setback_mm", "DEFAULT_REAR_SETBACK_MM", DEFAULT_REAR_SETBACK_MM, "mm", "arka bahce cekmesi (asgari)",
                                   "uygulama imar planinda aksi hukum yoksa", "ayrik", "Planli Alanlar Imar Yonetmeligi md. 24 (ikincil alinti)",
                                   (_URL_IZMIR, _URL_ZONING)),
    "taks": ZoningValue("taks", "DEFAULT_TAKS", DEFAULT_TAKS, "oran", "TAKS (taban alani katsayisi, tavan)",
                        "uygulama imar planinda TAKS belirtilmeyen ayrik/blok nizam", "ayrik",
                        "1 Temmuz 2026 degisikligi (ikincil haber/makale; Resmi Gazete 33297 metni DOGRULANMADI)", (_URL_BURSA, _URL_MUSAVIRLER)),
    "taks_max_without_kaks": ZoningValue("taks_max_without_kaks", "DEFAULT_TAKS_MAX_WITHOUT_KAKS", DEFAULT_TAKS_MAX_WITHOUT_KAKS, "oran",
                                         "KAKS belirtilmeyen parselde TAKS en cok (emsal siniri icinde kalmak kaydiyla)", "KAKS (emsal) belirtilmemisse", "ayrik",
                                         "1 Temmuz 2026 degisikligi (ikincil haber/makale; DOGRULANMADI)", (_URL_BURSA, _URL_MUSAVIRLER)),
    "kaks_rule": ZoningValue("kaks_rule", "KAKS_FALLBACK_RULE", None, "kural", "KAKS (emsal): sayi YOK; belirtilmemisse yapi yaklasma mesafelerine gore bulunan taban alani x kat adedi",
                             "KAKS belirtilmemisse", "ayrik", "1 Temmuz 2026 degisikligi (ikincil haber/makale; DOGRULANMADI)", (_URL_MUSAVIRLER,)),
}

SUPPORTED_NIZAM = "ayrik"


@dataclass(frozen=True)
class ZoningResolution:
    values: dict                 # anahtar -> float | None
    sources: dict                # anahtar -> 'kullanici' | 'varsayilan:<SABIT_ADI>'
    used_defaults: tuple         # kullanilan ZoningValue'lar
    questions: tuple             # SORULMASI gereken seyler (kosul eslesmedi / veri yok)

    def describe(self) -> list[str]:
        """Kullanilan varsayilanlari ADIYLA bildirir (sessiz varsayilan yok)."""
        out = []
        for z in self.used_defaults:
            val = "kural metni (sayi yok)" if z.value is None else f"{z.value:g} {z.unit}"
            out.append(f"varsayilan: {z.label} = {val} [{z.name}; kosul: {z.condition}; nizam: {z.nizam}; kaynak: {z.source}, arastirma {z.researched_on}; "
                       f"{'DOGRULANDI' if z.verified else 'DOGRULANMADI - kullanici gercek yonetmelikle degistirecek'}]")
        return out


def resolve_zoning(user: dict | None = None, nizam: str = SUPPORTED_NIZAM, plan_states: dict | None = None) -> ZoningResolution:
    """Kullanici degeri > katalog varsayilani > SORU. `plan_states`: {'taks': bool, 'kaks': bool} - uygulama imar plani o degeri BELIRTIYOR mu
    (belirtiyorsa katalog varsayilani UYGULANMAZ; kullanicidan o deger istenir). Katalogda olmayan nizam icin varsayilan YOK (soru)."""
    user = dict(user or {})
    unknown = sorted(set(user) - set(ZONING_DEFAULTS) - {"kaks"})        # 'kaks' = kullanicinin verdigi emsal (katalogda varsayilani YOK)
    if unknown:
        raise VaziyetError(f"bilinmeyen imar anahtari: {unknown} (gecerli: {sorted(ZONING_DEFAULTS) + ['kaks']})")
    for k, v in user.items():
        if v is not None and (not isinstance(v, (int, float)) or isinstance(v, bool) or v < 0):
            raise VaziyetError(f"{k}: negatif olmayan sayi olmali")
    plan_states = plan_states or {}
    values: dict = {}
    sources: dict = {}
    used: list[ZoningValue] = []
    questions: list[str] = []
    if user.get("kaks") is not None:
        values["kaks"], sources["kaks"] = float(user["kaks"]), "kullanici"
    for key, z in ZONING_DEFAULTS.items():
        if user.get(key) is not None:
            values[key], sources[key] = float(user[key]), "kullanici"
            continue
        if nizam != SUPPORTED_NIZAM:
            values[key], sources[key] = None, "yok"
            questions.append(f"{z.label}: '{nizam}' nizami icin katalogda varsayilan YOK (v1 yalniz '{SUPPORTED_NIZAM}'); deger kullanicidan istenir")
            continue
        if key == "taks" and plan_states.get("taks"):
            values[key], sources[key] = None, "yok"
            questions.append("TAKS: uygulama imar plani TAKS belirtiyor - varsayilan UYGULANMAZ; plan notundaki degeri kullanicidan isteyin")
            continue
        if key in ("taks_max_without_kaks", "kaks_rule"):
            if plan_states.get("kaks"):
                values[key], sources[key] = None, "yok"
                if key == "kaks_rule":
                    questions.append("KAKS: uygulama imar plani KAKS (emsal) belirtiyor - varsayilan kural UYGULANMAZ; plan notundaki degeri kullanicidan isteyin")
                continue
            if user.get("kaks") is not None:      # kullanici KAKS verdi -> 'KAKS yok' kurali/siniri UYGULANMAZ
                values[key], sources[key] = None, "yok"
                continue
        values[key], sources[key] = z.value, f"varsayilan:{z.name}"
        used.append(z)
    return ZoningResolution(values, sources, tuple(used), tuple(questions))


def edge_roles(parcel: Parcel, road_edges: list[int]) -> list[str]:
    """Parsel kenarlarinin rolleri: yola bakan = 'on'; kalanlardan ILK yol kenarina EN TERS yonlu (en antiparalel; esitlikte en uzun) = 'arka'; digerleri 'yan'.
    Yola bakan kenar BILINMIYORSA rol UYDURULMAZ (`VaziyetError`: kullanicidan istenir)."""
    n = len(parcel.polygon)
    if not road_edges:
        raise VaziyetError("yola bakan kenar (road_edges) bilinmiyor: on/arka/yan ayrimi yapilamaz - kullanicidan istenir")
    for i in road_edges:
        if not isinstance(i, int) or isinstance(i, bool) or not 0 <= i < n:
            raise VaziyetError(f"road_edges: gecersiz kenar indeksi {i!r} (parselde {n} kenar var)")
    edges = parcel.edges()

    def unit(i):
        (ax, ay), (bx, by) = edges[i]
        l = math.hypot(bx - ax, by - ay)
        return ((bx - ax) / l, (by - ay) / l), l
    ref, _ = unit(road_edges[0])
    others = [i for i in range(n) if i not in road_edges]
    roles = ["yan"] * n
    for i in road_edges:
        roles[i] = "on"
    if others:
        def key(i):
            u, l = unit(i)
            return (u[0] * ref[0] + u[1] * ref[1], -l)       # en kucuk nokta carpimi (en antiparalel), sonra en uzun
        roles[min(others, key=key)] = "arka"
    return roles


def setbacks_for_parcel(parcel: Parcel, road_edges: list[int], user: dict | None = None, nizam: str = SUPPORTED_NIZAM,
                        plan_states: dict | None = None) -> tuple[dict, ZoningResolution]:
    """`site.setbacks` bicimi (`{"edges_mm": [...]}`) + cozumleme. Cekme degeri olmayan rol icin (kosul eslesmedi) `VaziyetError` (soru)."""
    res = resolve_zoning(user, nizam, plan_states)
    role_key = {"on": "front_setback_mm", "yan": "side_setback_mm", "arka": "rear_setback_mm"}
    roles = edge_roles(parcel, road_edges)
    vals = []
    for r in roles:
        v = res.values[role_key[r]]
        if v is None:
            raise VaziyetError("; ".join(res.questions) or f"{role_key[r]} bilinmiyor")
        vals.append(v)
    return {"edges_mm": vals}, res
