# standards modülü (şartname + oransal mahal kural kütüphanesi) — DEV-036

Bir mahalin geometrik olarak GEÇERLİ (kapalı poligon, `validate.py::
check_rooms`) ama mimari olarak SAÇMA (asansör kuyusu 1×3m gibi bir en-boy
oranında, banyo "çubuk gibi ince uzun") olabileceği boşluğu kapatır.

## Neden bu modül (kullanıcı talebi, 2026-09-28)

> "türkiye mimari çizimlerde kullanılan şartnameleri analiz edip hardcoded
> kendinde barındıran bir modül olacak. şartnameler dışındaki mantıksal
> oranları da barındıracak ... her mahal için bir oran en boy oran
> limitleri alt üst limiti olacak, default ayarlarda bunlar esnetilmeyecek,
> özel olarak kullanıcının talebi söz konusu olduğunda sistem uyarı
> verecek ama kullanıcı istemeye devam edersek isteği doğrultusunda bu
> oransal mahaller gerçekleştirilecek."

Somut örnekler kullanıcıdan geldi: asansör kuyusu 3 m² ama piyasada
karşılığı olmayan bir oranda; merdiven alanı makul ama KARE (daha
dikdörtgen olmalı); bir banyo "çubuk gibi ince uzun" olabilir.

## Bu bir şartname METNİ değil, bir mühendislik KÜTÜPHANESİDİR

Tefriş/duvar/kolon kataloğuyla AYNI konumdadır (kök `CLAUDE.md`: "modül
altında yalnızca kütüphane yaşar", proje VERİSİ değil). `STANDARDS`
sözlüğündeki değerler v1'de **çoğunlukla genel mimari pratik/mantıksal
makuliyettir**, resmi bir yönetmelik/TS atfı olarak SUNULMAZ — her girişin
`source` alanı bunu açıkça "v1 pratik varsayılan" diye işaretler. Bu, kök
`CLAUDE.md`'nin "ölçü/standart UYDURULMAZ" ilkesini DELMEZ: proje
GEOMETRİSİ (gerçek bir odanın koordinatı) hiç uydurulmuyor — bu kütüphane
tefriş kataloğunun "ofis/katalog standardı (çizim sabiti)" olmasıyla AYNI
kategoridedir.

## Politika: UYARI, asla HATA (kullanıcı kararı, AYNEN uygulandı)

Oran/kısa kenar/alan eşiği dışına çıkan bir mahal **üretimi DURDURMAZ** —
`collision`in WARN seviyesi / `stairs::auto_flex` ile AYNI disiplin.
Kullanıcı context.json'da o geometriyi BIRAKIRSA (ısrar ederse) üretim
GERÇEKLEŞİR. Varsayılan eşikler kendiliğinden ESNETİLMEZ.

## Mahal tipi eşlemesi: `room_type`, addan TAHMİN EDİLMEZ

`rooms[].name` serbest metindir ("Anne Banyosu" gibi bir ad string-eşlemeyi
kırar ve sessizce hiç kontrol edilmeyen bir oda üretirdi). Bunun yerine
opsiyonel `rooms[].room_type` alanı kullanılır:

- **Şemada SABİT bir enum DEĞİLDİR** (serbest string) — kod-sahipli
  `STANDARDS` kataloğu büyüdükçe/geliştikçe şema değişmesin diye.
- `STANDARDS`ta TANIMSIZ bir değer `check_room_types` tarafından **HATA**
  olarak yakalanır (`scripts/validate.py::check_walls`'daki `kind` kontrolü
  ile AYNI desen — bir yazım hatası "aasansor" sessizce hiç kontrol
  edilmeyen bir odaya dönüşmez).
- `room_type` hiç VERİLMEZSE o oda kontrole HİÇ GİRMEZ (`ceiling`/`levels`
  ile AYNI "veri yoksa kontrol etme" opt-in deseni) — eski context'ler
  KIRILMAZ.

## Gelecek güncelleme sözleşmesi (kullanıcı talebi, 2026-09-28)

> "ilerleyen zamanlarda bu standart mantığını geliştirebilirim, dil
> modeline şartname ya da başka evraklar yükleyerek bu standart verileri
> güncellediğimde diğer modüllerin uyumunu mümkün olduğu kadar koruması
> gerekir."

Bunun için `CONTRACT_VERSION` disiplini şöyle uygulanır:

| Değişiklik | `CONTRACT_VERSION` | Gerekçe |
|---|---|---|
| Bir mahal tipinin eşik değerini değiştirmek | ARTMAZ | katalog DEĞERİ, tefriş ölçüsü gibi (kod-seviyeli, proje etkilemez) |
| Yeni bir mahal tipi eklemek | ARTMAZ | var olan tüketicileri etkilemez |
| Bir mahal tipini SİLMEK | **DİKKAT** | o tipi kullanan eski context `check_room_types`ten HATA alır — silmek yerine eşikleri genişletmek (etkin olarak devre dışı bırakmak) tercih edilmelidir |
| `RoomStandard`'ın alan şeklini (yeni/silinen alan) değiştirmek | **ARTAR** | `check_room_proportions`/`check_room_types` imzasını veya `validate.py`nin varsayımını değiştirir |

Bir gelecek oturumda (kullanıcı bir şartname PDF'i verip kataloğu
güncellettiğinde) yalnızca `STANDARDS` sözlüğünün İÇERİĞİ (değerler,
`source` metni, yeni mahal tipleri) değiştirilmelidir; `RoomStandard`
dataclass'ının alanları veya `check_room_types`/`check_room_proportions`
imzaları DEĞİŞTİRİLMEMELİDİR — değiştirilirse `CONTRACT_VERSION` artırılır
VE bu modülü tüketen `validate.py` gözden geçirilir.

## Public API

```python
from standards import (
    RoomStandard, STANDARDS, room_aspect_ratio,
    validate_standards, check_room_types, check_room_proportions,
)

check_room_types(rooms)              # -> HATA listesi (arity-1)
check_room_proportions(rooms, units) # -> UYARI listesi (kullanici karari)
validate_standards()                 # -> katalogun KENDI ic tutarliligi
```

## Ölçüm: neden AABB (eksen hizali sınırlayıcı kutu)

`_aabb_edges` bir odanın kısa/uzun kenarını, poligonun x/y min-max'ından
hesaplar. Bu projedeki odalar dikdörtgen/eksen-hizalı olduğu için AABB =
gerçek oda kenarlarıdır. **Bilinen sınırlama:** döndürülmüş veya L-şekilli
bir oda için bu YAKLAŞIK bir değerdir (gerçek yönlendirilmiş en küçük kutu
DEĞİL) — `rooms/CLAUDE.md`'deki "bu projedeki odalar dikdörtgen olduğu için
bugün sorun çıkarmıyor" notuyla AYNI kategoride bir basitleştirme.

## Çakışma denetimi: EXEMPT

`collision/scene.py::COLLISION_EXEMPT` içinde. Gerekçe: bu modül HİÇ
geometri üretmez, `ezdxf` kullanmaz — yalnızca zaten `rooms.collision`in
kapsadığı AYNI oda poligonunu OKUYUP ölçer. `typography`/`palette` ile AYNI
"salt kütüphane, sıfır çizim" gerekçesi.

## Doğrulama

`python scripts/standards/selftest.py` — `room_aspect_ratio`in elle
hesaplanabilir sonucu (4000×2000 dikdörtgen → oran 2.0), `check_room_types`
(bilinmeyen tip HATA, `None`/eksik alan sessizce atlanır), `check_room_proportions`
(oran/kısa kenar/alan ihlalinin her biri ayrı ayrı UYARI üretir, sınırın
TAM İÇİNDEKİ bir oda yanlış-pozitif ÜRETMEZ), `validate_standards`
(gerçek katalog temiz döner + kasıtlı bozulmuş bir kopya HATA yakalanır).

## Bilinen sınırlamalar

- **v1 kataloğundaki eşiklerin çoğu resmi bir yönetmelik/TS atfı
  TAŞIMAZ** — "v1 pratik varsayılan" olarak işaretlidir, kullanıcının
  gerçek şartname belgeleriyle güncellemesi BEKLENİR (bkz. yukarı "Gelecek
  güncelleme sözleşmesi").
- **AABB yaklaşımı döndürülmüş/L-şekilli odalarda YANLIŞ olabilir**
  (yukarı bakınız).
- **Gerçek projeye bugün hiçbir `room_type` verisi EKLENMEDİ** — bu bir
  ayrı, açık karardır (bkz. `docs/development/DEVELOPMENT_TASKS.md`
  `DEV-036`); altyapı `golden/oran_ornek` ile sınanır.
- **`min_area_m2` v1 kataloğunda hiçbir girişte KULLANILMADI** (hepsi
  `None`) — alan sınırı özelliği KODda var ve test edilir, ama kullanıcı
  henüz bir alan eşiği istemedi; `min_short_edge_mm`/oran yeterli
  görüldü.
