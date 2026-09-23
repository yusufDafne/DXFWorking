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

## Bilinen sınırlamalar — `RoomLabeler` (DEV-008 ile ele alınacak)

rev-8 kullanıcı talebiyle `RoomLabeler`ın yapısının geliştirilmesi planlandı.
Mevcut davranış: tek satır, sabit biçim `"{ad} ({alan} m2)"`, centroid'e
`MIDDLE_CENTER` yerleşim, yalnızca oda **genişliğine** göre `fit_text_height`.

- Çok satırlı etiket (ad / alan ayrı satır) yok; uzun mahal adları dar
  odalarda `min_height=60` tabanına kadar küçülüyor.
- Oda **yüksekliği** sığdırmada hiç kullanılmıyor.
- İçbükey (L şeklinde) poligonlarda centroid oda dışına düşebilir; alternatif
  yerleşim veya leader çizgisi yok.
- Etiket içeriği enjekte edilebilir bir stil/Protocol değil (karşılaştır:
  `openings::OpeningSymbolStyle`); mahal no / mahal tipi gibi alanlar
  eklenemiyor.

Ayrıntı ve başlatma öncesi kararlar: `docs/development/DEVELOPMENT_TASKS.md`
içindeki `DEV-008`. Bu bölüm bir uygulama izni değildir; sistem mimarı görevi
açıkça başlatmadan `RoomLabeler` davranışı değiştirilmez.

## Kabul

Poligonlar kapalı, alanlar deterministik, etiketler pafta dışına taşmıyor ve mevcut oda çıktısı korunuyor olmalıdır.
