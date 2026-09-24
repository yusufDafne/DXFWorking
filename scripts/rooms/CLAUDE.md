# rooms modülü — DEV-002 + DEV-018 tamamlandı

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

Etiket oda poligonunun centroid'ine ortalanır ve oda kutusuna hem **genişlik
hem yükseklik** bakımından sığacak şekilde ölçeklenir. Genişlik için her satır
KENDİ yükseklik çarpanıyla ölçülür (ad 1.0, diğerleri 0.78). Tek satırlı
önceki sürüm yalnızca genişliğe bakıyordu; 3 satırda yükseklik kontrolü
olmadan küçük mahallerde (WC, hol) etiket odadan taşardı.

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

- İçbükey (L şeklinde) poligonlarda centroid oda dışına düşebilir; alternatif
  yerleşim veya leader çizgisi YOK. Bu projedeki odalar dikdörtgen olduğu için
  bugün sorun çıkarmıyor.
- Etiket içeriği enjekte edilebilir bir stil/Protocol DEĞİL (karşılaştır:
  `openings::OpeningSymbolStyle`); farklı bir biçim istenirse kod değişir.
  `RoomLabelStyle` Protocol'ü `DEV-008`de fikir olarak duruyor, seçilmedi.
- Mahal adı büyük harfe `str.upper()` ile çevrilir. context.json bugün ASCII
  olduğu için güvenlidir; Türkçe karakterli ad eklenirse `i` → `I` sorunu
  için gözden geçirilmelidir.

## Kabul

Poligonlar kapalı, alanlar deterministik, etiketler pafta dışına taşmıyor ve mevcut oda çıktısı korunuyor olmalıdır.
