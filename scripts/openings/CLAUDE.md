# openings modülü — DEV-001 tamamlandı

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

## Kabul

Açıklık boşlukları duvar rails ile tutarlı, sembol stili enjekte edilebilir, schedule verisi deterministik ve mevcut plan çıktısı korunmuş olmalıdır.
