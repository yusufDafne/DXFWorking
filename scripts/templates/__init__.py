"""Kat planı / sirkülasyon çekirdeği şablon kütüphanesi (DEV-037).

**Kullanıcı talebi (2026-09-28):** "kat planları ve oda yerleşimleri için
genel şablonlara sahip olacak, bir de şablon oluşturucu generator'ü olacak
... örneğin yerleşim planlarındaki bina ana girişi, dairelerin yerleşimi,
kattaki daire sayısına göre efektif yerleşimler vs gibi verileri
sağlayacak."

**Mimari not (bu modülü YAZAN ajanın eklediği, kullanıcı açıkça İSTEMEDİ
ama kök `CLAUDE.md`nin "Deterministik üretim ilkesi"yle ÇELİŞMEMESİ için
ZORUNLU):** "generator" kelimesi burada dil modeline GEOMETRİ ÜRETTİRMEZ.
Bu modüldeki tek "generator" `generate_circulation_core(...)`dur ve
TAMAMEN deterministik Python fonksiyonudur — parametrelerden (genişlik/
derinlik/çekirdek ölçüleri) rooms/walls/openings sözlüğünü HESAPLAR,
rastgele veya dil-modeli-uydurması HİÇBİR koordinat üretmez. Bir agent bu
fonksiyonu PARAMETRE seçerek çağırabilir (kaç birim, hangi giriş yönü gibi
yapılandırılmış seçimlerle) — kök CLAUDE.md'nin zaten tanımladığı
"talep → yapılandırılmış context patch" akışının bir ÖNCÜSÜ.

**v1 KAPSAM SINIRI (BİLEREK küçük tutuldu, `stairs`/`ceiling` ile AYNI
disiplin):** yalnızca **sirkülasyon çekirdeği** (asansör + merdiven +
L-şekilli koridor + güney giriş duvarı) parametrik olarak üretilir — bu,
kök `CLAUDE.md`'nin "Çok katli bina yapisi" bölümünde ZATEN belgelenen ve
gerçek projenin HER katında (otopark/dükkan+lobi/3 daire/çatı terası)
KULLANILAN, kanıtlanmış bir desendir; bu görev onu koda ÇIKARIR, İCAT
ETMEZ. **Daire/birim İÇİ oda bölüntüsü (salon/mutfak/banyo yerleşimi) v1
KAPSAMI DIŞINDADIR** — bu gerçek bir tasarım kararıdır (kaç oda, hangi
oranlarda, kapı nereye) ve context.json'daki her birim BUGÜN elle farklı
tasarlanmıştır (bkz. gerçek projenin `uA_*`/`uB_*`/`uC_*` odaları — üçü de
FARKLI); bunu parametrik hale getirmek AYRI, çok daha büyük bir karar
gerektirir (bkz. `docs/development/DEVELOPMENT_TASKS.md` `DEV-037` "Açık
kararlar").

**Varsayılan ölçüler NEREDEN geliyor:** icat edilmedi — gerçek projenin
`context.json`ındaki (`normal1` katı) ZATEN ÇALIŞAN, `validate.py`den
geçmiş sirkülasyon çekirdeğinden BİREBİR çıkarıldı (elevator genişliği
1000mm, merdiven genişliği 4000mm, koridor "bacağı" derinliği 1500mm, bant
derinliği 4500mm). `scripts/templates/selftest.py` bunu doğrudan sınar:
`generate_circulation_core(20000, 17500)` gerçek projenin (`normal1`)
oda/duvar verisiyle BİREBİR eşleşir.

**Çıktı context.json'a YAZILMAZ (açık karar, kök `CLAUDE.md`yle tutarlı):**
`generate_circulation_core` salt bir `dict` döndürür (`rooms`/`walls`/
`openings` listeleri) — bunu context.json'a birleştirmek/yazmak ayrı,
İNSAN (veya insan onaylı bir sonraki adım) kararıdır. Bu fonksiyon context
dosyasına DOKUNMAZ, DXF çizmez, `ezdxf` içermez.
"""
from __future__ import annotations

from dataclasses import dataclass

try:
    from ..collision.geometry import shoelace_area
except ImportError:
    from collision.geometry import shoelace_area


@dataclass(frozen=True)
class CirculationCoreTemplate:
    """Sirkülasyon çekirdeğinin PARAMETRİK ölçüleri.

    Varsayılanlar gerçek projeden ÇIKARILDI (yukarı bakınız, modül
    dokstring'i) - icat edilmiş sayı DEĞİLDİR.
    """

    elevator_width: float = 1000.0
    stair_width: float = 4000.0
    corridor_leg_depth: float = 1500.0
    band_depth: float = 4500.0
    wall_thickness: float = 200.0
    door_width: float = 900.0


DEFAULT_TEMPLATE = CirculationCoreTemplate()


def generate_circulation_core(
    floor_width: float,
    floor_depth: float,
    template: CirculationCoreTemplate = DEFAULT_TEMPLATE,
    *,
    id_prefix: str = "",
    include_band_south: bool = True,
    units: str = "mm",
) -> dict:
    """Sirkülasyon çekirdeğinin rooms/walls/openings PARÇASINI üretir.

    Çekirdek HER ZAMAN sol-alt köşeye (x=0) sabittir - kök `CLAUDE.md`nin
    "Bu konum tum katlarda sabit tutulmalidir (asansor/merdiven duseyde
    hizali olsun diye)" ilkesiyle tutarlı; `floor_width` yalnızca
    koridorun/güney duvarının DOĞU ucunu belirler.

    `include_band_south`: zemin/normal katlarda `True` (giriş kapılı güney
    duvarı VAR), bodrum/çatı gibi açık geçişli katlarda `False` verilmelidir
    (kök `CLAUDE.md`: "band_south ... bodrum/catida YOK - acik gecis").
    Bu fonksiyon hangi kat tipinin hangisini istediğine KARAR VERMEZ -
    çağıran taraf (kat tipini bilen) belirler.

    Döndürülen `dict` context.json'a YAZILMAZ - salt bir VERİ parçasıdır
    (bkz. modül dokstring'i).
    """
    core_y0 = floor_depth - template.band_depth + template.corridor_leg_depth
    band_y0 = floor_depth - template.band_depth
    core_x1 = template.elevator_width + template.stair_width
    unit_divisor = 1_000_000.0 if units == "mm" else 1.0

    def pid(name: str) -> str:
        return f"{id_prefix}{name}"

    def area_m2(polygon: list[list[float]]) -> float:
        return round(shoelace_area(polygon) / unit_divisor, 2)

    elevator_polygon = [
        [0.0, core_y0],
        [template.elevator_width, core_y0],
        [template.elevator_width, floor_depth],
        [0.0, floor_depth],
    ]
    stair_polygon = [
        [template.elevator_width, core_y0],
        [core_x1, core_y0],
        [core_x1, floor_depth],
        [template.elevator_width, floor_depth],
    ]
    # L-sekilli koridor: tam kat genisligini kaplar, cekirdegin kendisini
    # (asansor+merdiven dikdortgeni) DISLAR - gercek projenin 'band'
    # odasiyla AYNI sekil (bkz. modul dokstring).
    band_polygon = [
        [0.0, band_y0],
        [floor_width, band_y0],
        [floor_width, floor_depth],
        [core_x1, floor_depth],
        [core_x1, core_y0],
        [0.0, core_y0],
    ]

    rooms = [
        {"id": pid("elevator"), "name": "Asansor", "polygon": elevator_polygon,
         "area_m2": area_m2(elevator_polygon)},
        {"id": pid("stair"), "name": "Merdiven", "polygon": stair_polygon,
         "area_m2": area_m2(stair_polygon)},
        {"id": pid("band"), "name": "Koridor", "polygon": band_polygon,
         "area_m2": area_m2(band_polygon)},
    ]

    walls = [
        {
            "id": pid("core_bottom"),
            "start": [0.0, core_y0],
            "end": [core_x1, core_y0],
            "thickness": template.wall_thickness,
            "layer": "DUVARLAR",
        },
        {
            "id": pid("core_div"),
            "start": [template.elevator_width, core_y0],
            "end": [template.elevator_width, floor_depth],
            "thickness": template.wall_thickness,
            "layer": "DUVARLAR",
        },
        {
            "id": pid("core_right"),
            "start": [core_x1, core_y0],
            "end": [core_x1, floor_depth],
            "thickness": template.wall_thickness,
            "layer": "DUVARLAR",
        },
    ]

    openings = [
        {
            # Merdiven kapisi, merdiven boluminun (elevator_width..core_x1)
            # ORTASINA merkezlenir - gercek projenin door_stair'iyle AYNI
            # yerlesim kurali (position_from_start=3000, elevator=1000,
            # stair=4000 -> merkez 1000+4000/2=3000, BIREBIR ortusur).
            "id": pid("door_stair"),
            "type": "door",
            "wall_id": pid("core_bottom"),
            "position_from_start": template.elevator_width + template.stair_width / 2.0,
            "width": template.door_width,
            "layer": "KAPI-PENCERE",
        },
    ]

    if include_band_south:
        walls.append({
            "id": pid("band_south"),
            "start": [0.0, band_y0],
            "end": [floor_width, band_y0],
            "thickness": template.wall_thickness,
            "layer": "DUVARLAR",
        })

    return {"rooms": rooms, "walls": walls, "openings": openings}


# Bu modulun CONTEXT SOZLESMESI surumu (DEV-020). Yalnizca
# `generate_circulation_core`in DONDURDUGU dict'in SEKLI (anahtarlar,
# rooms/walls/openings alan adlari) degisirse artar - `CirculationCoreTemplate`
# varsayilan DEGERLERI (icat edilmemis, gercek projeden cikarildi) serbestce
# ayarlanabilir, surum ARTIRMAZ (standards.STANDARDS ile AYNI disiplin).
CONTRACT_VERSION = "1.0"

__all__ = [
    "CirculationCoreTemplate", "DEFAULT_TEMPLATE",
    "generate_circulation_core", "CONTRACT_VERSION",
]
