# ceiling modülü (yansıtılmış tavan planı / RCP) — DEV-023

Kat planından AYRI bir pafta: her odanın duvar konturunu YENİDEN çizer
(aynı `WallNetwork`, aynı açıklıklar) ve üstüne tavan kotu + (varsa)
malzeme etiketini basar.

## Neden ayrı bir modül + ayrı pafta (kullanıcı kararı, 2026-09-28)

`DEV-023`ün Fikir 1/Fikir 2 analizinde iki seçenek sunuldu: yeni bağımsız
modül + AYRI RCP paftası, ya da mevcut kat planına bindirme. Kullanıcı
**Fikir 1**'i seçti — endüstri standardında RCP kat planından AYRI bir
pafta türüdür (`sections`/`elevations` ile AYNI "kendi paftası olan
modül" deseni); zemin planı mobilyası + tavan bilgisi aynı pafta üzerinde
üst üste binerse okunmaz hale gelir.

## Veri disiplini — hangi alan gerçek ölçü, hangisi format

| Alan | Kategori | Kaynak |
|---|---|---|
| `rooms[].ceiling_height_mm` | **GERÇEK proje verisi** | context.json, oda başına, **HİÇ türetilmez** (kat yüksekliğinden TAHMİN dahi edilmez — döşeme kalınlığı + olası asma tavan boşluğu bilinmeden bu bir varsayım olurdu) |
| `rooms[].ceiling_finish` | Serbest proje verisi | context.json, opsiyonel, **serbest metin** — sabit bir malzeme kod listesi UYDURULMAZ |
| Kot metni formatı (`"+2.50"`) | Ofis/sistem standardı | `scripts/levels::format_level` DOĞRUDAN yeniden kullanılır — kendi format mantığı İCAT EDİLMEZ |

**Kullanıcının 2026-09-28 direktifi:** "Oda başına (`rooms[]` içinde)" —
her oda kendi tavan yüksekliğini bildirir (asma tavan farkı olan
projelerde gerçekçi, örn. ıslak hacim tavanı düşük olabilir). Kat başına
tek bir varsayılan + override seçeneği (Fikir'in ikinci alternatifi)
kullanılmadı.

## Opt-in: veri yoksa hiçbir şey çizilmez

`resolve_room_ceilings(floor)` yalnızca `ceiling_height_mm` VERİLMİŞ
odaları döndürür — vermeyen odalar SONUCA hiç girmez (kuzey oku ile AYNI
"veri yoksa uydurma" deseni). `floor_has_ceiling_data(floor)` bir katın
RCP paftasının HİÇ ÜRETİLİP ÜRETİLMEYECEĞİNİN tek kaynağıdır: hiçbir
odada bu veri yoksa o kat için pafta AÇILMAZ (gerçek projenin bugünkü
`context.json`ında `ceiling_height_mm` verisi YOKTUR — bu yüzden gerçek
projede RCP paftası bugün hiç görünmez, bu KASITLIDIR, veri UYDURULMADI).

## v1 kapsam sınırı (kullanıcı kararı, 2026-09-28)

Aydınlatma armatür yerleşimi bu revizyonun KAPSAMI DIŞINDADIR —
`stairs`/`levels` ile AYNI disiplin: net bir v1 sınırı çizilir, armatür
ayrı bir gelecek geliştirme konusudur (bkz.
`docs/development/DEVELOPMENT_TASKS.md`ye eklenecek takip görevi).

## Public API

```python
from ceiling import (
    CeilingSheet, RoomCeilingData,
    resolve_room_ceilings, floor_has_ceiling_data,
    draw_ceiling_label, ensure_ceiling_layer,
)

if floor_has_ceiling_data(floor):
    CeilingSheet.draw(msp, floor, units, text_height)   # duvarlar + etiketler
```

`CeilingSheet.draw` aks ızgarasını ÇİZMEZ — `generate_dxf.py` her pafta
için (kat planı/kesit/görünüş ile AYNI şekilde) `axis_grid.draw_on_floor`
çağırır; bu ayrım `sections`/`elevations`in aks sorumluluğunu
`generate_dxf.py`ye bırakmasıyla AYNIDIR.

## Duvarlar neden YENİDEN çizilir (kopyalanmaz, aynı ağdan türetilir)

Aynı DXF entity iki paftada gösterilemez (her pafta kendi mutlak X
ofsetinde yaşar, `translate_floor` deseni). `CeilingSheet.draw`, kat
planının kullandığı AYNI `walls::WallNetwork.from_context` + `draw_
wall_network` çağrısını, AYNI `floor['walls']`/`floor['openings']`
verisiyle YENİDEN yapar — ikinci bir duvar geometrisi İCAT EDİLMEZ, tek
kaynak (context.json'daki duvar verisi) iki kez ÇİZİLİR.

## Etiket biçimi: iki satır, `RoomLabeler`den BİLEREK basit

`draw_ceiling_label`, kot satırı + (varsa) BÜYÜK HARFE çevrilmiş malzeme
satırını centroid'e ortalar. `rooms::RoomLabeler`in 3 satırlık BLOK+ATTRIB
mekanizması (`DEV-018`) BİLEREK kullanılmaz — farklı içerik (mahal adı/kat
kodu/alan değil, kot/malzeme), farklı bir basit metin sınıfıdır.

## Katman

`TAVAN` katmanı, `scripts/palette::PALETTE`den (DEV-030) gelen kod-sahipli
sabit bir renkle (mor/eflatun, diğer "primary" ailelerden — AKS/KOLON
grisi, KESİT kırmızısı, MERDİVEN mavisi, KOT yeşili — bilerek farklı)
`ensure_ceiling_layer` ile idempotent kurulur.

## Çakışma denetimi: EXEMPT

`collision/scene.py::COLLISION_EXEMPT` içinde. Gerekçe: duvarlar zaten
`walls.collision`in kapsadığı AYNI veriden yeniden çizilir (yeni bir ayak
izi DEĞİL); tavan etiketi bir ANOTASYONDUR (`dimensions`/`stairs`in
etiket kısmıyla AYNI gerekçe).

## Doğrulama

`python scripts/ceiling/selftest.py` — `resolve_room_ceilings`in elle
hesaplanabilir sonucu (+ veri taşımayan oda yanlış-pozitifi),
`floor_has_ceiling_data`in her iki yönü, `draw_ceiling_label`in malzeme
var/yok durumunda ürettiği varlık sayısı + metin içeriği (kot formatı +
BÜYÜK HARF malzeme), `CeilingSheet.draw`in duvar ağı entity sayısına
(bağımsız ölçüm: `draw_wall_network` doğrudan çağrılarak) etiket
sayısını EKLEDİĞİNİN doğrulanması, katman RGB'sinin kod-sahipli olduğu.

`validate.py`de özel bir kontrol YOK — `ceiling_height_mm`/
`ceiling_finish` şema tarafından zaten sayısal/serbest-metin olarak
kısıtlanıyor; ekstra bir geometrik/mantıksal invariant (stairs'teki
`StairFitError` gibi) bu v1 kapsamında yok.

## Bilinen sınırlamalar

- **Aydınlatma armatür yerleşimi YOK** (v1 kapsam sınırı, yukarı bakınız).
- **Malzeme kod listesi standartlaştırılmamış** — serbest metin, proje
  bazında tutarlılık kullanıcının sorumluluğundadır.
- **Kapı/pencere açıklıkları RCP'de de gösterilir** (kat planındaki AYNI
  `openings[]` verisi) — gerçek RCP pratiğinde bazı ofisler açıklıkları
  gizler, bazıları gösterir; bu proje GÖSTERME tarafını seçti (basitlik,
  tek kod yolu — `draw_wall_network` zaten açıklık gerektiriyor).
- **`validate.py`de seviye sırası/tutarlılık kontrolü yok** — herhangi bir
  pozitif `ceiling_height_mm` kabul edilir, örn. duvar yüksekliğinden
  büyük bir değer engellenmez (bu proje henüz duvar/kat yüksekliğini
  `rooms[]` seviyesinde bilmiyor, çapraz kontrol için veri yok).
