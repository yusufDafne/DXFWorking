# elevations modülü — Gelecek faz

## Sorumluluk

`ElevationSheet`, `LevelStack` ve `FacadeOpeningPlacer`; kullanıcı tarafından bildirilen basitleştirilmiş cephe seviyeleri ve açıklık yerleşimidir.

## Faz planı

1. Mevcut `elevation_vertical_extent` ve `draw_elevation` davranışını
   karakterize et.
2. `LevelStack` ile below-ground/above-ground seviyelerini bildirilen veriden
   hesapla; cepheyi plandan otomatik türetme.
3. `FacadeOpeningPlacer` ile bildirilen pencere/kapı sayısı ve boyutlarını
   deterministic yerleştir.
4. AxisGrid izdüşümünü tüket ve `axis_source` ailesini koru.
5. Gerçek renderer linetype davranışını test edip dokümante et; uygulanmayan
   bir standardı varsayım olarak ekleme.

## Public API adayı

- `LevelStack.from_context(levels)` ve `vertical_extent()`.
- `ElevationSheet(width, levels, axis_source)`.
- `FacadeOpeningPlacer.place(level, opening_spec)`.
- `draw_elevation(...)` yalnızca bu API üzerinden çağrılır.

## Invariant'lar ve doğrulama

- Seviye sırası, yükseklik ve below-ground işareti context'ten gelir.
- Pencere/kapı boyutu level yüksekliğini aşamaz; eksik boyut uydurulmaz.
- Ortak pafta mutlak Y aralığı ve overflow kontrolü korunur.
- Ön/arka ve sağ/sol aks ailesi doğru `axis_source` ile gösterilir.

## Sınır

Cepheler gerçek plan geometrisinden kendiliğinden türetilmez. Below-ground ve linetype davranışı renderer ile doğrulanmadan standart kabul edilmez.

## Kabul

Seviye istifi, aks izdüşümü, açıklıklar ve pafta sınırları deterministik ve doğrulanabilir olmalıdır.
