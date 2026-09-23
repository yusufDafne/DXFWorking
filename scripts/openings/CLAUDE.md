# openings modülü — DEV-001 tamamlandı

## Sorumluluk

`Opening`, `Door`, `Window`, host wall ilişkisi, genişlik/konum, tek/çift/sürme varyantı, swing/menteşe ve sembol stillerini taşır.

## Faz planı

1. Mevcut `walls.render.DefaultPlanOpeningStyle` davranışını fixture olarak
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

## Kabul

Açıklık boşlukları duvar rails ile tutarlı, sembol stili enjekte edilebilir, schedule verisi deterministik ve mevcut plan çıktısı korunmuş olmalıdır.
