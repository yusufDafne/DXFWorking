# columns modülü — Gelecek faz

## Sorumluluk

`Column` ve `ColumnGrid`; parametrik kolon kesiti, aks kesişimi ve kolon/aks ilişkisinin çizimidir.

## Faz planı

1. Aks koordinatları ve kolon verisinin hangi context yolunda yaşayacağını
   sistem mimarı kararıyla belirle.
2. Kare, dikdörtgen ve dairesel kesitleri katalog/Protocol üzerinden tanımla.
3. `ColumnGrid` ile bildirilen aks kesişimlerini deterministik eşleştir.
4. Taşıyıcı eleman ile sembol çizimini ayır; pafta ve ölçü sorumluluğunu
   tüket, sahiplenme.
5. Olası çakışma, aks dışı kolon ve katlar arası hizalama kontrollerini
   validator sözleşmesine ekle.

## Public API adayı

- `Column(grid_intersection, section, rotation=0)`.
- `ColumnSectionCatalog` veya enjekte edilebilir kesit Protocol'ü.
- `ColumnGrid.from_axes(...)` ve `draw(...)`.

## Invariant'lar ve doğrulama

- Kolon yalnızca bildirilen aks kesişimlerine veya açıkça bildirilen konuma
  yerleşir; konum uydurulmaz.
- Kesit ölçüsü ve rotation doğrulanır.
- Düşey hizalama kararı yoksa katlar arasında otomatik varsayım yapılmaz.
- Golden output'ta kolon entity, kesit ve aks ilişkisi kontrol edilir.

## Sınır

Kolon konumu veya kesiti uydurulmaz. Aks modülünü tüketir; duvar, oda veya pafta sorumluluğunu almaz.

## Kabul

Kolonlar bildirilen akslara oturur, kesit geometrisi geçerli ve golden output farkları açıklanmış olur.
