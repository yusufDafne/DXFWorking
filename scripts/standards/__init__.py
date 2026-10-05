"""Sartname + oransal mahal kural kutuphanesi (DEV-036).

**Kullanici talebi (2026-09-28):** "turkiye mimari cizimlerde kullanilan
sartnameleri analiz edip hardcoded kendinde barindiran bir modul ...
sartnameler disindaki mantiksal oranlari da barindiracak verileri tutacak
... her mahal icin bir oran en boy oran limitleri alt ust limiti olacak,
default ayarlarda bunlar esnetilmeyecek, ... sistem uyari verecek ama
kullanici istemeye devam edersek isteği dogrultusunda bu oransal mahaller
gerceklestirilecek." Somut ornekler: asansor kuyusu 3 m2 ama piyasada
karsiligi olmayan bir en-boy oraninda; merdiven alani makul ama KARE (daha
dikdortgen olmali); "cubuk gibi ince uzun" bir banyo "hicbir endustri
standardi bu formati kabul etmez".

**Bu bir SARTNAME METNI DEGIL, bir MUHENDISLIK KUTUPHANESIDIR** - tefris/
duvar/kolon kataloguyla AYNI konumdadir (kok CLAUDE.md: "modul altinda
yalnizca kutuphane yasar", proje VERISI degil). `STANDARDS` sozlugundeki
degerler IKI kaynaktan gelebilir ve her girisin `source` alaniyla ACIKCA
ayristirilir:
  - gercek bir yonetmelik/TS atfi (kullanici onayiyla eklenir/degistirilir),
  - v1'deki COGU deger BUDUR: genel mimari PRATIK/MANTIKSAL makuliyet
    (kullanicinin kendi ornekleri). Bunlar resmi bir atif GIBI SUNULMAZ -
    `source` metni "v1 pratik varsayilan" ibaresini tasir. Bu, kok
    CLAUDE.md'nin "olcu/standart UYDURULMAZ" ilkesini DELMEZ: proje
    GEOMETRISI (bir odanin gercek koordinati) hic uydurulmuyor, yalnizca
    bu KUTUPHANENIN kendi makuliyet esikleri - tipki tefris katalogunun
    "ofis/katalog standardi (cizim sabiti)" olmasi gibi (bkz. kok
    CLAUDE.md "Tefris" bolumu) - v1 icin makul bir baslangic degeri.

**Politika (kullanici karari, AYNEN uygulanir):** ihlal HER ZAMAN UYARIdir,
asla HATA degildir - `collision`in WARN seviyesi / `stairs::auto_flex` ile
AYNI disiplin. Varsayilan esikler kendiliginden ESNETILMEZ (kullanici context
'e o geometriyi yine de yazarsa uretim ENGELLENMEZ, yalnizca raporlanir).

**Mahal tipi eslemesi ADDAN TAHMIN EDILMEZ.** `rooms[].name` serbest metindir
("Anne Banyosu" gibi bir ad string-eslesmeyi kirar ve sessizce hic
kontrol edilmeyen bir oda uretirdi). Bunun yerine opsiyonel bir
`rooms[].room_type` alani (schema'da SERBEST STRING, sabit enum DEGIL)
kullanilir; `STANDARDS`ta TANIMSIZ bir deger `check_room_types` tarafindan
HATA olarak yakalanir (typo guvenligi, `walls.kind` ile AYNI desen);
`room_type` hic verilmezse o oda kontrole hic GIRMEZ (ceiling/levels ile
AYNI "veri yoksa kontrol etme" opt-in deseni).

**Gelecek guncelleme sozlesmesi (kullanici talebi, 2026-09-28):** "ilerleyen
zamanlarda bu standart mantigini gelistirebilirim, dil modeline sartname ya
da baska evraklar yukleyerek bu standart verileri guncelledigimde diger
modullerin uyumunu mumkun oldugu kadar koruması gerekir." Bunun icin:
  - `STANDARDS` sozlugunun DEGERLERI (esikler, `source` metni) SERBESTCE
    degisir - bu `CONTRACT_VERSION`i ARTIRMAZ (tipki furniture katalog
    olculeri gibi, bkz. scripts/version.py "surumlenen sey kod degil
    sozlesmedir").
  - `RoomStandard`in ALAN SEKLI (hangi alanlar var, tipleri) SABIT
    kalmalidir; yeni bir alan EKLEMEK/MEVCUT birini KALDIRMAK
    `CONTRACT_VERSION`i artirir - cunku bu, `check_room_proportions`i
    cagiran `validate.py` gibi TUKETICILERIN varsayimini degistirir.
  - Yeni bir mahal TIPI eklemek/var olanin esigini degistirmek guvenlidir;
    bir TIPI SILMEK guvenli DEGILDIR (context'te o tipi kullanan eski bir
    proje `check_room_types`ten HATA alir) - silmek yerine esikleri
    genisletmek (etkin olarak devre disi birakmak) tercih edilmelidir.
"""
from __future__ import annotations

from dataclasses import dataclass

from .measure import NarrowPoint, edge_wall_thicknesses, inset_polygon, narrowest_point, net_area
from .nuances import check_door_corridor_nuances


@dataclass(frozen=True)
class RoomStandard:
    """Bir mahal TIPI icin en-boy oran + (opsiyonel) boyut siniri.

    `min_ratio`/`max_ratio` HER ZAMAN >= 1.0'dir (uzun kenar / kisa kenar,
    yani 1.0 = tam kare). `source`, degerin NEREDEN geldigini (resmi atif mi,
    v1 pratik varsayilan mi) ACIKCA belirtir - bkz. modul dokstring'i.
    """

    room_type: str
    label: str
    min_ratio: float
    max_ratio: float
    min_short_edge_mm: float | None = None
    min_area_m2: float | None = None
    source: str = ""


# v1 KATALOGU. Kullanicinin kendi ornekleriyle DOGRUDAN baglantili degerler
# (asansor, merdiven, banyo) daha ozenle secildi; digerleri makul genel
# varsayimlardir. HEPSI "v1 pratik varsayilan" - kullanicinin gercek
# sartname/TS atiflariyla GUNCELLEMESI beklenir (bkz. modul dokstring
# "Gelecek guncelleme sozlesmesi").
STANDARDS: dict[str, RoomStandard] = {
    "asansor": RoomStandard(
        "asansor", "Asansor kuyusu", min_ratio=1.0, max_ratio=1.5,
        min_short_edge_mm=1400.0,
        source="v1 pratik varsayilan - kullanicinin verdigi somut ornek "
               "('3 m2 ama piyasada karsiligi olmayan/kullanissiz bir "
               "oran'). Gercek TS EN 81 kuyu/kabin asgari ic olculeri "
               "kullanici onayiyla eklenip bu deger DEGISTIRILMELIDIR."),
    "merdiven": RoomStandard(
        "merdiven", "Merdiven (oda orani)", min_ratio=1.3,
        max_ratio=2.4,
        source="v1 pratik varsayilan - kullanicinin ornegi ('alani makul "
               "ama kare, biraz daha dikdortgen olmali'). min_ratio>1.0 "
               "BILEREK: asiri kare bir merdiven odasi da reddedilsin diye. "
               "DEV-046'da DEGERLENDIRILDI (cift kollu/dog_leg destegi "
               "eklenirken): bu sinirlar SAYISAL olarak DEGISTIRILMEDI - "
               "gercek projenin 4000x3000mm odasi (oran 1.333) zaten bu "
               "aralikta VE hem tek kollu HEM dog_leg icin gecerli bir "
               "oran (max_ratio=2.4, asiri uzun bir dog_leg'i de dogru "
               "sekilde reddeder). Etiket eskiden 'tek kollu' diyordu - "
               "artik iki turu de kapsadigi icin DUZELTILDI. "
               "scripts/stairs/ kendi riser/going varsayilanlarini "
               "(170/270mm) AYRI tasir; bu kayit yalnizca ODANIN oran "
               "sinirlari icindir, basamak geometrisi degil."),
    "banyo": RoomStandard(
        "banyo", "Banyo", min_ratio=1.0, max_ratio=2.2,
        min_short_edge_mm=1500.0,
        source="v1 pratik varsayilan - kullanicinin ornegi ('cubuk gibi "
               "ince uzun banyo olmaz, hicbir endustri standardi bu "
               "formati kabul etmez')."),
    "wc": RoomStandard(
        "wc", "WC", min_ratio=1.0, max_ratio=2.2, min_short_edge_mm=900.0,
        source="v1 pratik varsayilan - banyo ile AYNI ailede, daha kucuk "
               "asgari kisa kenar."),
    "mutfak": RoomStandard(
        "mutfak", "Mutfak", min_ratio=1.0, max_ratio=2.5,
        min_short_edge_mm=1800.0,
        source="v1 pratik varsayilan."),
    "yatak_odasi": RoomStandard(
        "yatak_odasi", "Yatak odasi", min_ratio=1.0, max_ratio=2.0,
        min_short_edge_mm=2700.0,
        source="v1 pratik varsayilan."),
    "salon": RoomStandard(
        "salon", "Salon", min_ratio=1.0, max_ratio=2.3,
        min_short_edge_mm=3000.0,
        source="v1 pratik varsayilan."),
    "dukkan": RoomStandard(
        "dukkan", "Dukkan (ticari)", min_ratio=1.0, max_ratio=5.0,
        source="v1 pratik varsayilan (DEV-051 ek karar, 2026-10-05: dukkanlar "
               "konut sayilmaz, ayri islenir). Yalnizca en-boy orani siniri; "
               "kisa kenar/alan esigi UYDURULMADI - yonetmelik gelince "
               "eklenecek."),
    "koridor": RoomStandard(
        "koridor", "Koridor / hol", min_ratio=1.0, max_ratio=8.0,
        min_short_edge_mm=1500.0,
        source="v1 pratik varsayilan (DEV-049: 1100 -> 1500mm, kullanici "
               "karari 2026-10-05: 'hol genisligi minimum 1,5 metre'; "
               "gercek yonetmelik gelince degisecek) - koridorlar DOGASI GEREGI uzun-ince "
               "olur; bu yuzden max_ratio digerlerinden COK daha genistir "
               "(bu tip icin bir UST sinirin bile anlami tartismalidir, "
               "ama tamamen sinirsiz birakmak yazim hatalarini - orn. "
               "1mm genislikli bir koridor - yakalamaz)."),
}


def _aabb_edges(polygon: list[list[float]]) -> tuple[float, float]:
    """(kisa_kenar, uzun_kenar) - EKSEN HIZALI sinirlayici kutu (AABB).

    **Bilinen sinirlama:** bu projedeki odalar dikdortgen/eksen-hizali
    oldugu icin AABB = gercek oda kenarlaridir; donuk veya L-sekilli bir oda
    icin bu YAKLASIK bir deger olur (gercek yonlendirilmis en kucuk kutu
    DEGIL) - bkz. CLAUDE.md "Bilinen sinirlamalar".
    """
    xs = [point[0] for point in polygon]
    ys = [point[1] for point in polygon]
    width = max(xs) - min(xs)
    depth = max(ys) - min(ys)
    return (min(width, depth), max(width, depth))


def room_aspect_ratio(polygon: list[list[float]]) -> float:
    """Uzun kenar / kisa kenar (>= 1.0). Kisa kenar sifirsa `inf` doner
    (dejenere bir poligon - baska bir kontrol zaten bunu YAKALAMALIDIR,
    bu fonksiyon sessizce bolme hatasi VERMEZ)."""
    short_edge, long_edge = _aabb_edges(polygon)
    if short_edge <= 0:
        return float("inf")
    return long_edge / short_edge


def validate_standards() -> list[str]:
    """`STANDARDS` katalogunun KENDI IC TUTARLILIGI (palette::validate_palette
    ile AYNI disiplin). Gelecekte bir guncelleme (kullanicinin kendisi ya da
    sartname okuyan bir agent) bozuk bir deger (orn. min_ratio > max_ratio)
    eklerse bunu SESSIZCE gecirmez."""
    errors: list[str] = []
    for key, standard in STANDARDS.items():
        if key != standard.room_type:
            errors.append(
                f"STANDARDS['{key}']: sozluk anahtari room_type "
                f"('{standard.room_type}') ile UYUSMUYOR."
            )
        if standard.min_ratio < 1.0:
            errors.append(f"STANDARDS['{key}']: min_ratio ({standard.min_ratio}) >= 1.0 olmali.")
        if standard.max_ratio < standard.min_ratio:
            errors.append(
                f"STANDARDS['{key}']: max_ratio ({standard.max_ratio}) < min_ratio "
                f"({standard.min_ratio})."
            )
        if standard.min_short_edge_mm is not None and standard.min_short_edge_mm <= 0:
            errors.append(f"STANDARDS['{key}']: min_short_edge_mm pozitif olmali.")
        if standard.min_area_m2 is not None and standard.min_area_m2 <= 0:
            errors.append(f"STANDARDS['{key}']: min_area_m2 pozitif olmali.")
        if not standard.source.strip():
            errors.append(f"STANDARDS['{key}']: source (kaynak notu) bos - degerin nereden geldigi belirsiz.")
    return errors


def check_room_types(rooms: list[dict]) -> list[str]:
    """ERROR sinifi (arity-1, `validate.py`den cagirilir): `room_type`
    VERILMIS ama `STANDARDS`ta TANIMSIZ bir deger bir YAZIM HATASINI
    sessizce GECIRMEZ (`scripts/validate.py::check_walls`teki `kind`
    kontroluyle AYNI desen). `room_type` hic verilmemis bir oda buraya
    HIC GIRMEZ (opt-in)."""
    errors: list[str] = []
    for room in rooms:
        room_type = room.get("room_type")
        if room_type is None:
            continue
        if room_type not in STANDARDS:
            errors.append(
                f"Oda '{room['id']}': bilinmeyen room_type '{room_type}'. "
                f"Tanimli turler: {', '.join(sorted(STANDARDS))}."
            )
    return errors


def check_room_proportions(
    rooms: list[dict], units: str, walls: list[dict] | None = None
) -> list[str]:
    """WARN sinifi (kullanici karari, 2026-09-28): esik disina cikan bir
    mahal uretimi DURDURMAZ, yalnizca UYARI verir - kullanici context.json'da
    o geometriyi BIRAKIRSA (isteğine devam ederse) uretim GERCEKLESIR.
    `walls` (opsiyonel, ayni kat) verilirse en-boy orani, asgari kisa kenar/
    yerel en dar nokta VE alan duvar IC YUZLERI arasi NET olculur (DEV-049/
    DEV-057: mimari gelenek; `STANDARDS` esikleri NET yorumlanir); verilmezse
    oda poligonu net kabul edilir (eski davranis).
    `room_type` verilmeyen VEYA `STANDARDS`ta tanimsiz (bu ikinci durum
    `check_room_types` icinde zaten HATA) bir oda kontrole HIC GIRMEZ."""
    warnings: list[str] = []
    unit_to_mm = 1.0 if units == "mm" else 1000.0
    for room in rooms:
        room_type = room.get("room_type")
        standard = STANDARDS.get(room_type) if room_type else None
        if standard is None:
            continue
        gross_short, _gross_long = _aabb_edges(room["polygon"])
        thick = edge_wall_thicknesses(room["polygon"], walls) if walls else None
        # DEV-057 (kullanici karari 2026-10-05): oran ve alan da duvar IC
        # YUZLERI arasi NET poligonla olculur; `STANDARDS` esikleri NET olarak
        # yorumlanir. `walls` verilmezse poligon net kabul edilir.
        net_poly = inset_polygon(room["polygon"], thick) if thick and any(thick) else room["polygon"]
        short_edge, long_edge = _aabb_edges(net_poly)
        net_tag = " (net)" if thick and any(thick) else ""
        ratio = long_edge / short_edge if short_edge > 0 else float("inf")
        if ratio < standard.min_ratio or ratio > standard.max_ratio:
            warnings.append(
                f"Oda '{room['id']}' ({standard.label}): en-boy orani{net_tag} "
                f"{ratio:.2f}, izin verilen aralik "
                f"[{standard.min_ratio:.2f}, {standard.max_ratio:.2f}] disinda."
            )
        if standard.min_short_edge_mm is not None:
            narrow = narrowest_point(room["polygon"], thick)
            if narrow is not None:
                net_mm = narrow.width * unit_to_mm
                if net_mm < standard.min_short_edge_mm - 1e-6:
                    if abs(narrow.gross - gross_short) < 1e-6:
                        warnings.append(
                            f"Oda '{room['id']}' ({standard.label}): kisa kenar "
                            f"{net_mm:.0f}mm"
                            + (" (duvar ic yuzleri arasi net)" if thick else "")
                            + f", asgari {standard.min_short_edge_mm:.0f}mm altinda."
                        )
                    else:
                        where = "x" if narrow.axis == "y" else "y"
                        warnings.append(
                            f"Oda '{room['id']}' ({standard.label}): yerel en dar "
                            f"nokta {net_mm:.0f}mm"
                            + (" (duvar ic yuzleri arasi net)" if thick else "")
                            + f" ({where}={narrow.at:g} kesitinde, "
                            f"{narrow.span[0]:g}-{narrow.span[1]:g} araliginda), "
                            f"asgari {standard.min_short_edge_mm:.0f}mm altinda "
                            f"(dis kutu kisa kenari {gross_short * unit_to_mm:.0f}mm "
                            f"bunu gizliyordu)."
                        )
        if standard.min_area_m2 is not None:
            area_m2 = room["area_m2"]
            if thick and any(thick):
                area_m2 = net_area(room["polygon"], thick) / (1e6 if units == "mm" else 1.0)
            if area_m2 < standard.min_area_m2:
                warnings.append(
                    f"Oda '{room['id']}' ({standard.label}): alan{net_tag} "
                    f"{area_m2:.1f} m2, asgari {standard.min_area_m2:.1f} m2 "
                    f"altinda."
                )
    return warnings


# Bu modulun CONTEXT SOZLESMESI surumu (DEV-020). KOD/KATALOG DEGER surumu
# DEGILDIR - yalnizca RoomStandard'in ALAN SEKLI veya check_* fonksiyonlarinin
# imzasi/donus formati degisirse artar (bkz. modul dokstring "Gelecek
# guncelleme sozlesmesi"). Bkz. scripts/version.py
CONTRACT_VERSION = "1.2"

__all__ = [
    "RoomStandard", "STANDARDS", "room_aspect_ratio", "validate_standards",
    "check_room_types", "check_room_proportions", "narrowest_point",
    "edge_wall_thicknesses", "net_area", "check_door_corridor_nuances", "NarrowPoint", "CONTRACT_VERSION",
]
