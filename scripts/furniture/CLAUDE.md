# furniture modülü (tefriş) — DEV-009 ile planlandı

Kullanıcı 2026-09-23'te bu modülün kurulmasını ve **standart tefriş
elemanlarından oluşan bir set** oluşturulmasını talep etti. Plan maddesi ve
iki uygulama fikri için `docs/development/DEVELOPMENT_TASKS.md` içindeki
`DEV-009`a bakınız. Bu dosya bir uygulama izni değildir; sistem mimarı görevi
açıkça başlatmadan kod yazılmaz.

**İlk iş:** Bugün `floor.counters[]` (mutfak tezgahı) doğrudan
`generate_dxf.py::draw_floor_sheet` içinde ad-hoc kapalı polyline olarak
çiziliyor. Modülün ilk görevi bu davranışı davranış korunarak devralmaktır
(`axis/` modülünün `AxisGrid`i devralmasıyla aynı desen).

## Sorumluluk

`Counter`, `Fixture` ve bildirilen sabit mobilya elemanlarının parametrik çizimi.

## Faz planı

1. Mevcut `floor.counters[]` dikdörtgen çizimini fixture olarak tanımla.
2. `Counter` ve `Fixture` için context veri yollarını ve layer sözleşmesini
   schema kararıyla netleştir.
3. Eleman poligonlarını doğrula; oda/duvar çakışmalarını raporla.
4. Mobilya stillerini enjekte edilebilir katalog/Protocol olarak ayır.
5. Pafta overflow ve golden output kontrollerini entegre et.

## Public API adayı

- `Counter.from_context(data)`.
- `Fixture.from_context(data)`.
- `FurnitureRenderer.draw(element, style)`.
- `FurnitureCatalog` veya style Protocol'ü.

## Invariant'lar ve doğrulama

- Eleman yalnızca bildirilen polygon ve layer ile çizilir.
- Mobilya eksikse model yerleşim veya ölçü uydurmaz.
- Çakışma raporu üretim kararını sessizce değiştiremez.
- Tüm entity'ler Sheet sınırları içinde kalır.

## Sınır

Mobilya tasarım verisi context'te yoksa uydurulmaz. Oda geometrisini veya pafta kompozisyonunu sahiplenmez.

## Kabul

Elemanlar doğru layer'da, bildirilen koordinatlarda, çakışma/taşma kontrolleriyle ve golden output etkisi raporlanarak çizilir.
