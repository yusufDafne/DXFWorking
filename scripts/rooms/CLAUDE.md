# rooms modülü — DEV-002 + DEV-018 + DEV-044 tamamlandı

## Sorumluluk

Kapalı oda poligonu, alan/komşuluk, `RoomLabeler`, alan etiketi sığdırma ve oda-duvar tutarlılığı.

## Faz planı

1. Mevcut `draw_room_label` ve `polygon_centroid` davranışını referans olarak
   çıkar.
2. `Room` veri modelinin mevcut `floors[].rooms[]` sözleşmesiyle ilişkisini
   belirle; schema değişikliğini ayrı karar olarak tut.
3. Kapalı poligon, self-intersection, alan ve komşu kenar kontrollerini
   validator sınırına taşı.
4. `RoomLabeler`ı pafta `fit_text_height` ile bağla; oda etiketi taşmasını
   gerçek entity bounding box ile kontrol et.
5. `RoomPolygonScanner`ı yalnızca rapor/taslak üreten read-only araç olarak
   koru.

## Public API adayı

- `Room.from_context(data)` doğrulanmış oda görünümü.
- `PolygonOps.area`, `centroid`, `is_closed`, `has_self_intersection`.
- `PolygonOps.pole_of_inaccessibility(polygon, precision)`, `local_extent(polygon, origin)`
  (DEV-044) — etiket konumu artık `centroid` DEĞİL bunlardır, bkz. aşağıda.
- `RoomLabeler.draw(msp, room, max_text_height, units)`.
- `RoomPolygonScanner.scan_edges(...)` ve `suggest_wall_dicts(...)`.
- `ensure_room_label_block(doc, layer, style_name)`, `ROOM_LABEL_BLOCK_NAME`,
  `ROOM_LABEL_ATTDEF_TAGS`, `ROOM_LABEL_NOMINAL_HEIGHT` (DEV-018).

## Invariant'lar ve doğrulama

- Oda poligonu en az üç noktalı, kapalı ve geçerli alana sahip olmalıdır.
- Alan değeri bildirilen veriyle çelişirse model alan uydurmaz; validator
  kararı gerekir.
- Etiket oda sınırları ve Sheet overflow sınırları içinde kalır.
- Scanner önerisi context'e otomatik yazılmaz.
- Golden output'ta oda label layer, metin ve konum farkları raporlanır.
- Blok+ATTRIB konumu, eski düz-TEXT formülüyle her zaman `< 1e-6` toleransla
  örtüşür (`python scripts/rooms/selftest.py`); blok tanımı belge başına
  BİR kez oluşur (yanlış-pozitif testi).

## Sınır

`RoomPolygonScanner` yalnızca öneri üretir; kullanıcı veya validator onayı olmadan context'e yazmaz. Pafta `fit_text_height` kullanılır, yeni ölçü/koordinat uydurulmaz.

## Mahal etiketi biçimi (kullanıcı şartnamesi — rev-9'da UYGULANDI)

Etiket **3 satırdır**:

```
SALON        <- 1. satir: mahal adi, BLOK
ZK-04        <- 2. satir: kat kodu + mahal no
28.9 m2      <- 3. satir: alan
```

- Mahal adı **blok** (büyük harf) olarak işlenir. Yazı tipi proje geneli
  fontudur (Arial Narrow); `meta.fonts.room_label` ile ayrı seçilebilir
  (bkz. `scripts/typography/CLAUDE.md`).
- Kat kodu `floors[].code`'dan, mahal no `rooms[].no`'dan gelir —
  **hiçbiri türetilmez.** `B1`/`B2` = bodrumlar, `ZK` = zemin,
  `K1`/`K2`/… = normal katlar, `TR` = çatı/teras.
- Kat kodu + mahal no, proje genelinde **benzersiz** bir mahal kimliğidir;
  `validate.py` bunu kontrol eder.

### Sığdırma

Etiket, oda poligonunun **"pole of inaccessibility"** noktasına ortalanır
(DEV-044'ten önce centroid'ti — bkz. aşağıdaki "İçbükey oda etiket
konumlandırması") ve oda kutusuna hem **genişlik hem yükseklik** bakımından
sığacak şekilde ölçeklenir. Genişlik için her satır KENDİ yükseklik
çarpanıyla ölçülür (ad 1.0, diğerleri 0.78). Tek satırlı önceki sürüm
yalnızca genişliğe bakıyordu; 3 satırda yükseklik kontrolü olmadan küçük
mahallerde (WC, hol) etiket odadan taşardı.

`ROOM_LABEL_MIN_HEIGHT` bir okunabilirlik tabanıdır. Taban devreye girerse
etiket teorik olarak odadan taşabilir; bu yüzden değişiklik sonrası
**tüm odalar için** kapsama kontrolü yapılmalıdır (rev-9'da 125/125 doğrulandı).

## BLOK+ATTRIB (rev-14, DEV-018)

`DEV-018` "çizimde hiç `BLOCK` kullanılmıyor" gözlemiyle açılmıştı; ama
tefriş (`DEV-010`) zaten `INSERT` kullanıyordu — asıl boşluk mahal etiketiydi
(kullanıcının "mahal ismi blok olarak işlensin" ifadesi rev-9'da büyük harf
olarak yorumlanmıştı; `BLOCK` entity kastedildiyse asıl karşılığı budur).

**Tasarım:** blok, `ROOM_LABEL_NOMINAL_HEIGHT` (100 birim) referans
yüksekliğine göre 3 ATTDEF (`MAHAL_ADI`/`MAHAL_KOD`/`ALAN`) ile TEK SEFER
tanımlanır (`ensure_room_label_block`, `FurnitureBlocks.ensure` deseniyle
idempotent). Her oda için `INSERT` ölçeği `fitted_height / NOMINAL_HEIGHT`
verilir ve `insert.add_auto_attribs(...)` ile ATTRIB'ler doldurulur.

**Neden eski çizimle birebir örtüşür:** eski düz-TEXT formülünün her terimi
(`satır yüksekliği`, `satırlar arası kayma`, `blok toplam yüksekliği`)
`height` değişkeninde DOĞRUSALDIR — hepsi `height * sabit` biçimindedir.
Bu yüzden blok NOMINAL_HEIGHT'ta tanımlanıp `scale = height/NOMINAL_HEIGHT`
ile eklendiğinde, `ezdxf`'in tekdüze (uniform) ölçekleme dönüşümü
(`Insert.add_auto_attribs` → `Attrib.transform`) konumu ve yüksekliği AYNI
`scale` ile çarpar — sonuç, eski formülün `height`i doğrudan kullanmasıyla
MATEMATİKSEL OLARAK AYNIDIR. Bu denklik `selftest.py`de elle hesaplanan
beklenen konumla `< 1e-6` toleransla kanıtlanır.

**Kenar durum:** kat kodu VE mahal no'nun ikisi de eksikse (nadir; 2 veya
daha az satır) blok kullanılmaz, eski düz-TEXT çizimine (`_draw_raw`)
düşülür — blok 3 ATTDEF için SABİT yerleşimle tanımlıdır, ortadaki satır boş
kalsaydı görsel bir boşluk bırakırdı.

**ezdxf tuzağı (ölçüm araçları için önemli):** bir `INSERT`e bağlı `ATTRIB`
entity'leri DXF dosyasında GERÇEKTEN ayrı, AutoCAD'de tek tek düzenlenebilir
kayıtlardır — ama ezdxf'in Python nesne modeli bunları genel layout
iterasyonuna/`query()`'e DAHİL ETMEZ (`insert.attribs` ile ayrıca okunur).
`scripts/golden_report.py::_iter_all` bu yüzden eklendi; onsuz ölçüm/kural
kontrolleri mahal etiketi ATTRIB'lerini SESSİZCE görmezdi.

## İçbükey oda etiket konumlandırması (DEV-044)

Kullanıcının gerçek dünya gözlemi: *"L şeklinde hol isimlendirmelerini
yaparken geometrik orta nokta değil, hol sınırları içerisinde yazmalısın
mahal ismini."* `architect/`in ürettiği L-şekilli hol'ler (`uA_hol`,
`uB_hol`) içbükeydir (concave) — böyle bir poligonun geometrik centroid'i
(ağırlık merkezi) poligonun "çentiğine" denk gelip odanın **DIŞINA**
düşebilir; bu artık VARSAYIMSAL değil, gerçek projede GERÇEKTEN oluyordu.

**Çözüm — "pole of inaccessibility":** `PolygonOps.pole_of_inaccessibility`,
Mapbox'un `polylabel` algoritmasıyla AYNI deterministik izgara-arama
yöntemidir (üçüncü parti kütüphane KULLANILMAZ — "deterministik üretim
ilkesi" gereği kendi implementasyonu; iteratif grid-arama bilinen bir
yöntemdir). Poligon sınırından bir noktanın imzalı mesafesini
(`_distance_to_boundary`, nokta-içindeyse pozitif/dışındaysa negatif) alıp
giderek daha küçük hücrelere bölerek bu mesafeyi MAKSİMİZE eden noktayı
bulur — yani sınıra en uzak, dolayısıyla HER ZAMAN poligonun gerçekten
İÇİNDE kalan bir nokta.

**Convex/dikdörtgen bir odada davranış DEĞİŞMEZ:** arama, adaylardan biri
olarak DAİMA `centroid`i VE bbox-merkezini de dener (`best_cell` başlangıcı).
Bir dikdörtgen için bu iki nokta zaten ANALİTİK OLARAK aynı ve maksimum
mesafeye sahip TEK noktadır — hiçbir izgara hücresi bunu KESİN OLARAK
(`>`, `>=` değil) geçemez, bu yüzden sonuç dikdörtgenlerde eski centroid
davranışıyla **1e-6 toleransla BİREBİR** örtüşür
(`scripts/rooms/selftest.py::check_pole_matches_centroid_for_rectangle`,
ayrıca `check_block_matches_raw_formula` DEĞİŞTİRİLMEDEN geçmeye devam
eder — regresyon YOK). İçbükey bir odada ise gerçekten farklı, İÇERİDE
kalan bir nokta döner (`check_pole_stays_inside_concave_l_shape`, kasıtlı
bozma: elle hesaplanan L-hol centroid'inin DIŞARIDA kaldığı ayrıca
kanıtlanır).

**Sığdırma kutusu da değişti:** eskiden `available_width`/`available_height`
odanın TAM AABB'inden (`max(xs)-min(xs)`) geliyordu — içbükey bir odada bu,
çentikteki BOŞ alanı da sayarak MEVCUT OLMAYAN bir genişlik/yükseklik
uydururdu (DEV-044'ün "Açık kararlar"ından biri buydu). `PolygonOps.
local_extent(polygon, origin)` bunun yerine capa noktasından dört eksen
yönünde (+x/-x/+y/-y) GERÇEK kenar kesişimine kadar ölçer. Dikdörtgende bu
AABB ile AYNI sonucu verir (`check_local_extent_matches_aabb_for_rectangle`);
kesişim bulunamazsa (beklenmeyen dejenere durum) eski AABB hesabına
DÜŞÜLÜR (güvenlik ağı, sessizce sıfır boyut üretmez).

**Golden referans:** `golden/hol_l_sekli` — `uA_hol`/`uB_hol` ile AYNI
kategoride L-şekilli tek odalı bir kat. `rule_room_labels`
(`golden_report.py`) artık `PolygonOps.centroid` DEĞİL, `RoomLabeler.draw`
ile AYNI `pole_of_inaccessibility`i çağırır — DEV-041'deki `wall_gap_ranges`
ile AYNI "tek kaynak" disiplini: kontrol, üretimin okuduğu FONKSİYONUN
KENDİSİNİ okur, geometrik bir varsayımı (centroid = etiket noktası)
YENİDEN YAZMAZ.

**Kapsam dışı bırakılan (bilinçli):** `scripts/ceiling/`in RCP etiketi HÂLÂ
`centroid` kullanır — DEV-044'ün "İlişkili modüller"i yalnızca `rooms/`,
`architect/`, `pafta/`dır; tavan planı etiketleri bu görevin kapsamı
DIŞINDA bırakıldı (bkz. `scripts/ceiling/CLAUDE.md`).

## Çakışma ayak izi (rev-12)

`rooms/collision.py::footprints(floor, context)`, her odayı `container=True`
bir `CollisionShape` olarak verir. Oda bir çizim elemanı DEĞİL, bir
**kapsayıcıdır**: çift-çift çakışma taramasına girmez, başka şekillerin
(bugün tefrişin) içinde kalması beklenen hacimdir.

İki odanın birbiriyle çakışması bu motorun işi değildir — o, modülün kendi
verisinin tutarlılığıdır ve `validate.py::check_rooms` içinde kalır (arite-1).

Oda poligonu **içbükey** olabilir (L şeklindeki koridor); bu yüzden içerme
testi nokta-içinde-çokgen ile yapılır, kırpma ile değil. Ayrıntı:
`scripts/collision/CLAUDE.md`.

## Bilinen sınırlamalar — `RoomLabeler`

- ~~İçbükey (L şeklinde) poligonlarda centroid oda dışına düşebilir;
  alternatif yerleşim veya leader çizgisi YOK.~~ **`DEV-044`'te KAPANDI:**
  etiket artık centroid değil `PolygonOps.pole_of_inaccessibility`e
  ortalanır — bkz. yukarıdaki "İçbükey oda etiket konumlandırması
  (DEV-044)". Leader çizgisi hâlâ YOK ama artık İHTİYAÇ da yok (nokta HER
  ZAMAN oda içinde).
- Etiket içeriği enjekte edilebilir bir stil/Protocol DEĞİL (karşılaştır:
  `openings::OpeningSymbolStyle`); farklı bir biçim istenirse kod değişir.
  `RoomLabelStyle` Protocol'ü `DEV-008`de fikir olarak duruyor, seçilmedi.
- Mahal adı büyük harfe `str.upper()` ile çevrilir. context.json bugün ASCII
  olduğu için güvenlidir; Türkçe karakterli ad eklenirse `i` → `I` sorunu
  için gözden geçirilmelidir.

## Kabul

Poligonlar kapalı, alanlar deterministik, etiketler pafta dışına taşmıyor ve mevcut oda çıktısı korunuyor olmalıdır.
