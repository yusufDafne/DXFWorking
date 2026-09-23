# legend modülü — Opsiyonel gelecek faz

## Sorumluluk

`TitleBlockLegend`, `LayerSwatch` ve pafta sembol/layer açıklamalarının tekrarlanabilir çizimi.

## Faz planı

1. Pafta anteti ile lejant sorumluluğunu ayır; `Sheet` anteti değiştirilmez.
2. Kullanılan layer ve sembolleri merkezi bir registry'den deterministik al.
3. `LayerSwatch` ve sembol açıklamalarını ortak text-fit/overflow kurallarıyla
   çiz.
4. Birden fazla paftada tekrar kullanım ve tekilleştirilmiş içerik kontrolü
   ekle.

## Public API adayı

- `TitleBlockLegend(entries, style)`.
- `LayerSwatch.from_registry(layer_name)`.
- `LegendRenderer.draw(sheet, entries)`.

## Invariant'lar ve doğrulama

- Lejantta yalnızca projede kullanılan ve registry'de tanımlı öğeler görünür.
- Pafta çerçevesi/anteti `pafta` modülünde kalır.
- Metin ve semboller pafta içinde kalır; tekrarlı ad-hoc açıklama eklenmez.
- Lejant opsiyoneldir ve açık proje/sistem mimarı kararı olmadan etkinleşmez.

## Sınır

Pafta çerçevesi ve antet `pafta` modülünde kalır. Lejant opsiyoneldir; proje talebi veya sistem mimarı kararı olmadan eklenmez.

## Kabul

Lejant tüm sembol/layer açıklamalarını deterministik ve pafta içinde gösterir; tekrar eden ad-hoc açıklamalar bırakılmaz.
