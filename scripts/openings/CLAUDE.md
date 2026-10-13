# openings modülü — DEV-001 tamamlandı

## Kapisiz duvar acikligi `passage` (rev-25)

`type='passage'`: duvarda bosluk + iki soye cizgisi; kanat/yay/cam YOK, kapi
kurallarina (acilim, giris/WC nuansi) girmez, yalniz genel aciklik araligi kurallari
gecerlidir. Kullanim: merdiven alaninin kat holune acilisi (stairs/CLAUDE.md).
Cetvelde `DUVAR ACIKLIGI` (G). rev-26: `passage` icin duvar basi/sonu 100 mm kasa payi kurali UYGULANMAZ (merdiven acikligi duvar boyunca tam genislikte olabilir; kullanici: "10 cm kapi cikintisi mantigi olmamali"). CONTRACT 1.3, schema 1.2.0 (additif).

## Sorumluluk

`Opening`, `Door`, `Window`, host wall ilişkisi, genişlik/konum, tek/çift/sürme varyantı, swing/menteşe ve sembol stillerini taşır.

## Faz planı

1. Mevcut `walls.render.DefaultPlanOpeningStyle` davranışını referans olarak
   kaydet.
2. Host wall referansı, açıklık merkezi/konumu ve genişlik doğrulamasını
   tanımla; schema alanları onaylanmadan context sözleşmesini genişletme.
3. `OpeningSymbolStyle` Protocol'ünü koruyarak plan kapısı, pencere, sürme ve
   çift kanat stillerini enjekte edilebilir yap.
4. Duvar rail boşluğu ile sembol çizimini ayır; `WallNetwork` yalnızca
   geometrik boşluğu sahiplenmeye devam etsin.
5. Schedule üretimini aynı açıklık verisinden deterministik olarak bağla.

## Veri ve public API adayı

- `Opening(host_wall_id, width, position, variant, swing=None)` yalnızca
  schema onayından sonra kullanılabilir.
- `Door` ve `Window`, ortak açıklık sözleşmesinin alt türleri olur.
- `OpeningSymbolStyle.draw_plan(...)` ve gerekirse `draw_elevation(...)` stil
  enjeksiyon noktalarıdır.
- `OpeningSchedule.from_openings(...)` çizimden bağımsız tablo verisi üretir.

## Invariant'lar ve doğrulama

- Her açıklık mevcut bir host wall'a bağlıdır; host yoksa üretim durur.
- Genişlik, ait olduğu duvarın kullanılabilir uzunluğunu aşamaz.
- Açıklık rail boşluğu ile sembol konumu aynı host geometriye göre hesaplanır.
- Menteşe/swing belirtilmemişse model varsayım yapmaz.
- `validate.py` öncesi DXF üretilmez; mevcut golden plan ile entity/layer ve
  açıklık boşluğu karşılaştırılır.

Uygulanan API `Opening.from_context`, `OpeningSchedule.from_openings` ve
`OpeningSymbolStyle.draw_opening` metodudur. `swing`, `variant` ve
`host_wall_id` mevcut schema'ya eklenmemiş; mevcut `wall_id` korunmuştur.

## Sınır

Duvar rail/network geometrisi `walls` içinde kalır. Geçici kaynak `walls.render.DefaultPlanOpeningStyle`dır. Yeni opening alanları schema kararı olmadan zorunlu değildir.

## Varyantlar ve açılım yönü (rev-13, DEV-016)

Üç alan eklendi ve **üçünün de varsayılanı rev-12 davranışıdır** — alan
verilmeyen projeler hiçbir şey değiştirmeden aynı çizimi üretir.

| Alan | Değerler | Varsayılan |
|------|----------|------------|
| `variant` | `single` / `double` / `sliding` / `folding` | `single` |
| `swing` | `left` (menteşe duvar başında) / `right` (sonunda) | `left` |
| `host_side` | `pos` / `neg` (duvar normalinin yönü) | `pos` |

Varyant seçimi **veri odaklıdır** (`symbols.DOOR_SYMBOLS`): yeni bir kapı tipi
için alt sınıf yazmak gerekmez, sözlüğe bir fonksiyon eklenir
(`WallCatalog` / `FurnitureCatalog` deseni). Geçersiz bir değer üretimi
**durdurur** (`Opening.__post_init__`), sessizce atlanmaz.

**Sürme kapı açılım alanı GEREKTİRMEZ** — kanat duvara paralel kayar. Bu hem
sembolde (yay çizilmez) hem çakışma denetiminde (sektör üretilmez) geçerlidir.

## Açılım yayının TEK sahibi: `geometry.swing_geometry`

Yayı hem çizim (`symbols.py`) hem çakışma denetimi (`collision.py`) kullanır.
İki yerde ayrı hesaplanması rev-13'te **gerçek bir hataya** yol açmıştı:

1. **Yay 270° olabiliyordu.** Açılar `min(along, perp)` .. `max(along, perp)`
   olarak veriliyordu; duvar −X yönünde çizilmişse (`along = 180`,
   `perp = −90`) bu 270°'lik bir yay üretirdi. Mevcut projede her duvar +X/+Y
   yönündeydi, bu yüzden hata hiç görünmedi — ama `golden/minimal`
   referansında ucu ters verilmiş **iki duvar zaten vardı** ve oraya bir kapı
   konduğu anda ortaya çıkacaktı. Yön artık çapraz çarpımla belirlenir.
2. **Sektör yarım genişlik kayıktı.** `collision.py`,
   `position_from_start`i açıklığın BAŞLANGICI sanıyordu; oysa MERKEZİDİR.
   900'lük bir kapıda menteşe 450 mm yanlış yerdeydi.

**Sözleşme:** duvar boyunca gerçek boşluk aralığı (`g_start`, `g_end`) HER
ZAMAN `walls.gaps_for_wall` ile alınır; bu hesap ikinci bir yerde
tekrarlanmaz.

## Golden kuralıyla ilişki

`golden_report.rule_opening_symbols` rev-12'ye kadar "her kapı = 1 ARC"
varsayıyordu. Çift kanat 2, sürme ve katlanır 0 yay üretir; kural artık
beklenen sayıyı `openings.ARCS_PER_VARIANT` tablosundan okur. Çizicilerin
tabloya uyduğunu `selftest.py` kanıtlar — tablo ile çizim sessizce ayrışamaz.

## Doğrulama

`python scripts/openings/selftest.py` — beş duvar yönü × iki swing × iki
host_side için yayın **her zaman 90°** olduğu, varyant başına çizilen
çizgi/yay sayısı, geçersiz değerlerin üretimi durdurması ve boşluk aralığı
sözleşmesinin regresyon testi.

## Çakışma ayak izi (rev-12, rev-13'te düzeltildi)

`openings/collision.py::footprints(floor, context)` yalnızca **kapı açılım
sektörünü** üretir. Pencere ayak izi üretmez: pencere duvar düzlemindedir ve
plan düzleminde hacim işgal etmez.

Bu sağlayıcı `walls`'u tüketir — açılım yayının menteşesi host duvarın merkez
çizgisi üzerinde, yönü duvarın normalindedir. Bu zaten var olan ve endüstri
standardıyla uyumlu bir bağımlılıktır (IFC'de `IfcDoor` bir duvardaki
`IfcOpeningElement`i doldurur); tersi geçerli DEĞİLDİR, `walls` kapıyı bilmez.

Açı hesabı `walls.render.DefaultPlanOpeningStyle` ile **aynıdır**, böylece
denetlenen alan çizilen yayın ta kendisidir. Çokgen yaklaşımı
`collision.SECTOR_SEGMENTS` ile SABİT parça sayısındadır (ölçeğe bağlı
değildir) — deterministik üretim ilkesi gereği aynı context her zaman aynı
raporu vermelidir.

**rev-13'te kapandı:** açılım yönü artık schema'dadır, bu yüzden "iki kapı
birbirine açılıyor" kontrolü **HATA** durumuna çekildi. Sürme kapı sektör
üretmediği için bu kontrolden doğal olarak muaftır.

## Açıklık nuans kuralları (DEV-050, `rules.py`)

Açıklığın KENDİ duvarına göre kuralları; hepsi UYARI, esikler kütüphane
varsayılanı (context'e yazılmaz): #1 duvar ucunda ≥100 mm katı duvar (uçtaki
dik duvarın yarım kalınlığı düşülür), #2 açıklıklar arası ≥200 (iki KAPI arası ≥250: 100 çerçeve + 150 priz, DEV-053), #3 pencere ↔
bina dış köşesi ≥350, #5 çift kanatta 150 kasa payı + kanat ≥600, #6 sürme
kapıda kayacağı duvar yüzeyi ≥ açıklık genişliği, #11 açık kanat ucu ile başka
duvar yüzü ≥50 (`swing_geometry` kullanılır; v1 yalnız kanat UCU). Public:
`check_opening_nuances`, `check_opening_wall_nuances`,
`check_door_leaf_clearance`. Sözleşme alanları DEĞİŞMEDİ (`CONTRACT_VERSION`
1.1). Test: `selftest.py::check_wall_nuances`. Ayrıntı: `DEV-050`.

## DEV-051: sürme kapı park alanı + çift kanat menteşe invariantı

`rules.py::check_sliding_door_parking` (DEV-050 #6'nın dinamik hali): sürme
kanat, açıklık genişliği kadar duvar yüzünde iki yandan birine park eder; iki
yan da denenir (yan UYDURULMAZ). Bir yan duvar katı ucunu aşarsa, başka bir
açıklık alanına girerse veya başka bir kapının açılım sektörüyle
(`collision.footprints` — çizilen yayla AYNI kaynak) kesişirse uygun
değildir; ikisi de uygun değilse UYARI. Çift kanat: menteşe açıklık
kenarlarındadır (kullanıcı kararı) — `selftest.py` bunu kilitler.

## DEV-055: asansör kapısı (`elevator.py`) — eski "çizilmez" kuralı KALDIRILDI

Kullanıcı kararı (2026-10-05): "asansörlerin kapısı olur; eski kuralı genel şablon
çıkarırken gereksiz token yemesin diye söylemiştim." `type='elevator_door'`
(oda kapısı kurallarına GİRMEZ): üç tür — `single` (kapı gibi açılan),
`sliding` (**varsayılan**), `sliding_double` (büyük kapılar için ikili sürgülü,
iki panel zıt yöne, yay yok, sektör üretmez). Kuyu genişliğinden her kenardan
200–300 mm (varsayılan 250) daraltılır: `elevator_door_width(2100)` = 1600.
`check_elevator_door_insets` (UYARI) pay [200,300] dışında ise. Şema: `type`
enum'una `elevator_door`, `variant` enum'una `sliding_double` eklendi
(additif); `CONTRACT_VERSION` 1.1 → 1.2; lejant `A…`/`-SD` işaretleri.

## DEV-057 Grup A: kanat boyunca yakınlık

`rules.py::check_door_leaf_clearance` artık yalnız kanat ucunu değil kanadı
menteşe→uç doğrusu üzerinde dört noktadan (1/4, 1/2, 3/4, uç) ölçer; en yakın
nokta 50 mm'den yakınsa UYARI ('ucu' veya 'boyunca').

## DEV-057 Grup C: golden referansı + şema sürümü

Asansör kapısının üç türü `golden/asansor_merkezi_cekirdek/` ile sınanır (varsayılan
sürgülü, ikili sürgülü, kapı gibi açılan; beklenen ARC = 4). Şema additif genişledi
ve `scripts/version.py::SCHEMA_VERSION` 1.1.0 oldu (kullanıcı kararı).

## DEV-072: pencere yüksekliği ve denizlik (`heights.py`, şema 1.5.0)

Kullanıcı kararı (2026-10-12): varsayılan pencere yüksekliği **1200 mm**; **boy pencere** (örn. balkon kapısı) varsayılan yüksekliği **2000 mm**, zeminden **40 mm**.
Bunlar VARSAYILANDIR: `openings[].height` / `openings[].sill_height` verilirse o değer geçer (ölçü ve düşey konum dinamiktir; yatay konum zaten `position_from_start`).
Normal pencerenin denizliği DEV-072'de "verilmedi" idi; **DEV-075'te kullanıcı 900 mm verdi** (`DEFAULT_WINDOW_SILL_MM`, "kullanıcı kararı 2026-10-12") — `ResolvedHeights.sill` artık her zaman bir sayıdır.
Boy pencere `type: window` üzerinde opsiyonel `window_class: "tall"` ile işaretlenir (yeni `type` AÇILMADI: `type == "window"` dallanan 6 yer var). Balkon KAPISI `type: door` olarak kalır (kapı yüksekliği bu maddenin konusu değil).
Sabitler katalogdadır (`DEFAULT_WINDOW_HEIGHT_MM`, `DEFAULT_TALL_WINDOW_HEIGHT_MM`, `DEFAULT_TALL_WINDOW_SILL_MM`), `context.json`a yazılmaz; kullanılan varsayılan ADIYLA bildirilir:
`python scripts/defaults_report.py` (`defaults_used`). `validate.py`: `check_window_class_errors` (HATA: `window_class`/`sill_height` yalnız pencerede, geçersiz sınıf) ve `check_window_heights`
(UYARI: denizlik + yükseklik kat yüksekliğini aşarsa; kat yüksekliği `stairs[].floor_to_floor_mm`den, yoksa kontrol ATLANIR). Cetvel (`legend/`): YÜKSEKLİK ve DENİZLİK sütunları
(`PB120` = boy pencere; normal pencere satırı yükseklik 120 / denizlik 90; aynı genişlikte farklı yükseklik/denizlik markaya eklenir, benzersizlik `ValueError` ile korunur). `CONTRACT_VERSION` 1.3 → 1.4. Test: `selftest.py::check_window_heights_dev072`
(elle değerler, 10 kasıtlı bozma yakalandı, biri `ValueError` koruması ile).

## DEV-075: pencere yerleşimi (`placement.py`)

Kullanıcı kararı (2026-10-12): **varsayılan konum = pencerenin odasının dış duvar boyunca serbest aralığının ortası**; duvarın dış cepheye çarptığı yerde pencere olmamalı.
**Birleşim** = başka bir duvarın UCU bu duvarın üzerinde ve duvarlar paralel değil (`spatial.dist_point_segment ≤ SHARED_EDGE_TOLERANCE_MM`; eş doğrusal devam duvarı birleşim DEĞİL).
**Birleşim bölgesi** = iç duvar kalınlığının yarısı iki yana. `free_spans` bölgeleri çıkarır (iç içe geçen bölgeler birleştirilir); `room_span` odanın duvarla örtüşen gövdesine kırpılır
(iki oda arasında duvar yoksa — açık plan salon|mutfak — pencere kendi odasının sınırında biter). `default_window_position(host, room, walls, width)` aralık pencereden darsa `None` verir
(konum UYDURULMAZ). `check_window_junctions(floor)` → `validate.py` UYARISI (temas ve 1 mm'ye kadar örtüşme uyarı değildir; yeni sayı yok). `placement_suggestions(floor)` ve
`python scripts/window_placement_report.py [--min-delta MM]` mevcut pencereler için ortalanmış konum ÖNERİR (salt okunur; uygulamak bir REVİZYONDUR; aynı odada/duvarda birden çok pencere varsa öneri tek pencere varsayar).
Rev-28'de 76 pencerenin 0'ı birleşime düşer (`validate` çıktısı değişmedi); önerilerde 10'a yakını 100 mm'den fazla sapar (örn. zemin kat dükkân vitrinleri ~3 m). `CONTRACT_VERSION` 1.4 → 1.5.
Test: `selftest.py::check_window_placement_dev075` (elle hesaplanan birleşim/aralık/orta değerleri, sınırlar, açık plan, iç içe bölgeler; 10 kasıtlı bozma yakalandı).

## DEV-076: açıklık sınıfları kataloğu (`classes.py`, şema 1.7.0)

Kullanıcı kararı (2026-10-12): ana giriş, dükkân kapısı, vitrin ve boy pencere **ayrı sınıflardır**; her birinin varsayılan ölçüleri vardır ve kullanıcı değeri (`width`/`height`/`sill_height`) her zaman varsayılanı ezer.
Taban **boy pencere 1600 × 2000 mm, denizlik 40 mm** (genişlik tabanı kullanıcı seçimi). Türevler: **vitrin** (`window.shopfront`) +400 mm genişlik / +200 mm yükseklik = **2000 × 2200**;
**ana giriş** (`door.main_entry`) +100 mm / +100 mm = **1700 × 2100**; **dükkân kapısı** (`door.shop`) ana giriş ölçüleriyle başlar (1700 × 2100) ama **AYRI sınıf ve AYRI sabitler**
(`DEFAULT_SHOP_DOOR_*`; biri değişince öteki değişmez — "gelecekte özelleştirilebilmeli"; test sabitlerin sayı olarak tanımlandığını ve ana girişe bağlanmadığını doğrular). Denizlik/eşik **40 mm** boy pencereden
devralındı (kullanıcı belirtmedi; varsayım olarak raporlanır). Normal pencerenin GENİŞLİĞİ varsayılansızdır (proje verisi); yükseklik 1200, denizlik 900.
Alanlar: pencere `window_class` (`standard`/`tall`/`shopfront`), kapı `door_class` (`main_entry`/`shop`, opsiyonel — verilmeyen kapı sınıfsızdır, yükseklik verisi yoktur). Kayıt AÇIKTIR (`OPENING_CLASSES`: yeni sınıf = bir sabit kümesi + bir kayıt).
**Genişlik `context.json`da her zaman açık yazılıdır** (duvar boşlukları ona dayanır): sınıf genişliği yalnız YENİ açıklık üretirken kullanılır — `new_opening(class_key, id, wall_id, position, width=None)`; pencere için `new_window(class_key, id, host, room, walls)` ayrıca
varsayılan KONUMU (`placement.default_window_position`, odanın serbest aralığının ortası) hesaplar ve sığmazsa `ValueError` verir (konum/genişlik uydurulmaz). Yükseklik/denizlik kullanım anında çözülür (`heights.resolve_window_heights`, `resolve_door_heights`).
`validate.py`: `door_class` yalnız kapıda, `window_class` yalnız pencerede, geçersiz sınıf HATA; sınıflı kapı da kat yüksekliği kontrolüne girer. Cetvel: `PB`/`PV`/`KG`/`KD` markaları ve sınıf etiketleri (BOY PENCERE, VITRIN, ANA GIRIS KAPISI, DUKKAN KAPISI);
sınıflı kapıda yükseklik/denizlik gösterilir. Katalog raporu: `python scripts/defaults_report.py --catalog`. `CONTRACT_VERSION` 1.5 → 1.6. Test: `selftest.py::check_opening_classes_dev076` (elle değerler, bağımsızlık, new_opening/new_window, doğrulama, cetvel; 14 kasıtlı bozma yakalandı).

## Kabul

Açıklık boşlukları duvar rails ile tutarlı, sembol stili enjekte edilebilir, schedule verisi deterministik ve mevcut plan çıktısı korunmuş olmalıdır.

## Muhakeme katkısı (DEV-048)
**Rol:** ölçüm sağlayıcı (`reasoning.py`: rol + ölçüm beyanı). **Ölçümler (`daylight.py`, DEV-062; `validate.py` ÇAĞIRMAZ):** `check_living_room_window`
(yaşam mahalli = salon + yatak odası, dış cepheye açılan pencere şart), `check_cross_ventilation` (birimin dış pencereleri ≥ 2 farklı dış normal yönünde mi),
`check_salon_orientation` (`meta.north_angle` ister; tüm pencereler kuzey yarısına bakıyorsa UYARI; yoksa BOŞ döner, yön uydurulmaz). Hepsinin `*_subjects`
ikizi vardır. **Katıldığı veçheler:** `isik_hava_yonelim.isik.yasam_mahalli_penceresi`, `…hava.capraz_havalandirma`, `…yonelim.salon_kuzeye_bakiyor`,
(`draft`) `…isik.pencere_alani_orani` — hepsi `shadow`. **Bilinen boşluk:** pencere/taban oranı için doğrulanmış oran eşiği yok (yükseklik artık DEV-072 ile bilinir); derinlik ölçümü yok. **Bilgi mühendisi için not:** cephe tayini `spatial.facade_normal`dır (kopya yazma); tolerans 300 mm'dir —
bölmeye çok yakın pencere iki odaya değebilir.
