# rooms modülü — DEV-002 tamamlandı

## Sorumluluk

Kapalı oda poligonu, alan/komşuluk, `RoomLabeler`, alan etiketi sığdırma ve oda-duvar tutarlılığı.

## Faz planı

1. Mevcut `draw_room_label` ve `polygon_centroid` davranışını fixture olarak
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

## Invariant'lar ve doğrulama

- Oda poligonu en az üç noktalı, kapalı ve geçerli alana sahip olmalıdır.
- Alan değeri bildirilen veriyle çelişirse model alan uydurmaz; validator
  kararı gerekir.
- Etiket oda sınırları ve Sheet overflow sınırları içinde kalır.
- Scanner önerisi context'e otomatik yazılmaz.
- Golden output'ta oda label layer, metin ve konum farkları raporlanır.

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
