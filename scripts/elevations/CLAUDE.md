# elevations modülü (cephe görünüşleri) — DEV-011 tamamlandı

Seviye istifi, jenerik pencere/kapı yerleşimi, zemin çizgisi ve zemin-altı
kesikli linetype. `generate_dxf.py`nin eskiden gömülü olan
`draw_elevation`/`elevation_vertical_extent` fonksiyonlarının rev-14'teki
izole modül karşılığıdır (`axis`/`dimensions`/`openings`/`rooms` ile aynı
"her çizim konusu kendi modülü" deseni, bkz. kök `CLAUDE.md`).

## Sorumluluk

| Sınıf/fonksiyon | Görev |
|---|---|
| `Level` | Tek seviyenin doğrulanmış görünümü (`from_context`) |
| `LevelStack` | Seviyelerin dikey istifi: `placements()` (cursor birikimi), `extent()` (pafta Y-aralığı), `stack_top()` |
| `FacadeOpeningPlacer` | Jenerik pencere/kapı dikdörtgenlerinin eşit aralıklı yerleşimi |
| `ElevationSheet` | Tam çizim: aks izdüşümü + istif + açıklıklar + zemin çizgisi |
| `ensure_below_ground_linetype` | `DASHED` linetype'ı idempotent yükler |
| `elevation_vertical_extent` | Geriye dönük yardımcı: `Sheet.content_ranges` ve `preview.py` bunu kullanır |

## Kararın özü: gerçek plan geometrisinden TÜRETİLMEZ

Bu, kök `CLAUDE.md`'nin rev-2'de kullanıcı onayıyla sabitlediği bir
karardır — cepheler semantik/basit bir seviye istifi + eşit aralıklı jenerik
pencere dikdörtgenleridir. `DEV-011`'in "Fikir 2"si (plandan açıklık
türetme, opt-in) bilerek uygulanmadı; açık karar olarak kalıyor (bkz. "Açık
kararlar").

## Zemin-altı kesikli linetype (rev-14, kapatılan basitleştirme)

Önceden `below_ground: true` bir seviye SADECE zemin çizgisinin altında
konumlanıyordu; DXF'te çizgi türü diğer seviyelerle AYNIYDI (yalnızca
etiketle ayırt ediliyordu — bu `matplotlib` tabanlı `preview.py`de zaten
`linestyle="--"` ile taklit ediliyordu, ama gerçek DXF çıktısında YOKTU).

**Uygulama:** zemin-altı bir seviyenin ana hattı (ve içindeki pencere/kapı
varsa onlar da) `DASHED` linetype ile çizilir (`ElevationSheet.draw`). Diğer
tüm seviyeler `BYLAYER` kalır.

**Çapraz nokta — `axis` ile AYNI linetype adı, import YOK:** `axis` modülü
de `"DASHED"` adıyla aynı deseni yükler (`ensure_axis_layer`). İki modül
birbirini import ETMEZ (kök `CLAUDE.md` "modüller bağımsız çalışır"); her
biri kendi `ensure_*_linetype`'ını `if name not in doc.linetypes` koruması
ile çağırır — hangisi önce çalışırsa o kazanır, ikincisi no-op'tur. Bu,
`dimensions`/`axis` arasındaki "iki modül birbirini import etmez" ilişkisiyle
aynı desendir.

## `LevelStack`: `placements()` vs `extent()` — neden ikisi de var

- `placements()` her seviyenin GERÇEK çizilen dikdörtgenini verir
  (`machine_room` protrüzyonu HARİÇ — o, kendi seviyesinin ÜSTÜNE ayrıca
  çizilen bir kutudur).
- `extent()` paftanın ne kadar yer AYIRACAĞINI verir (`machine_room`
  protrüzyonu DAHİL — aksi halde çatı katı bloğu pafta çerçevesini aşardı).

İkisi kasıtlı olarak AYRIDIR: `axis_grid.draw_on_elevation` çağrısı
`placements()`in son `y1`sini kullanır (aks çizgisi gerçek son seviyenin
tepesinde biter, protrüzyonun üstünde değil) — bu, orijinal
`generate_dxf.py::draw_elevation`nun davranışıyla birebir aynıdır.

## Sıra invariant'ı: zemin-altı seviyeler listede ÖNCE gelmelidir

`placements()`in cursor birikimi, `levels` listesindeki SIRAYA göre çalışır;
`extent()`in `total_below` hesabı ise sıradan BAĞIMSIZ, sadece `below_ground`
bayrağına bakar. İkisi yalnızca zemin-altı seviyeler listede (aşağıdan
yukarıya) ÖNCE geldiğinde tutarlıdır. Bu, orijinal koddan miras kalan bir
invariant'tır — bu modül onu değiştirmez, ama context.json'da seviye
sırası bozulursa (örn. bir bodrum seviyesi listenin sonuna eklenirse) cursor
YANLIŞ konum üretir ve bu SESSİZ bir hatadır (schema seviyeleri sıralı
zorunlu kılmaz). `validate.py`de bugün bunun için bir kontrol YOKTUR (bkz.
"Bilinen sınırlamalar").

## Public API

```python
from elevations import ElevationSheet, LevelStack, Level, FacadeOpeningPlacer
from elevations import elevation_vertical_extent, ensure_below_ground_linetype

ElevationSheet.draw(msp, elevation_dict, dx, text_height, axis_grid, label_text_height)
y_bottom, y_top = elevation_vertical_extent(elevation_dict)
```

`generate_dxf.py` ve `preview.py` (matematik kısmı için `LevelStack`,
çizim için kendi `matplotlib` rutini) bu modülü kullanır.

## Invariant'lar

- Cephe genişliği ve pencere/kapı boyutları çizim SABİTİDİR
  (`DEFAULT_ELEVATION_WINDOW_SIZE`, `ELEVATION_DOOR_SIZE`); tasarım verisi
  DEĞİLDİR — `context.json`dan gelen tek şey `elevation["width"]` ve
  seviye başına `window_count`/`window_size`/`door`/`machine_room`.
- Aks izgarası HER ZAMAN diğer her şeyden önce çizilir.
- Zemin çizgisi (`y=0`) ve `"+-0.00 ZEMIN"` etiketi her cephede sabittir.

## Doğrulama

`python scripts/elevations/selftest.py` — elle hesaplanabilir bir istifte
cursor birikimi, `extent()`in `machine_room` protrüzyonunu kapsadığı,
zemin-altı seviyelerin (ve SADECE onların — yanlış-pozitif testi) `DASHED`
linetype aldığı ve pencere/kapı sayısı regresyon testleri.

## Sınır

Bu modül `ezdxf` kullanır ama context'i değiştirmez; sadece okur ve çizer.
`axis_grid` parametresi olarak herhangi bir `draw_on_elevation(msp, dx,
axis_source, y_bottom, y_top)` metoduna sahip nesne kabul edilir (`axis`
modülünü import ETMEZ, sadece bu sözleşmeyi bekler — duck typing).

## Bilinen sınırlamalar

- **Plandan türetme YOK** (bkz. "Kararın özü") — `DEV-011` Fikir 2 açık
  karar olarak duruyor.
- **Seviye sırası doğrulanmaz.** Zemin-altı seviyelerin listede önce
  gelmesi gerektiği (bkz. yukarıdaki invariant) `validate.py` veya bu modül
  tarafından KONTROL EDİLMEZ; context yanlış sıralanırsa cursor sessizce
  yanlış konum üretir.
- **Çakışma denetimine (`collision/`) girmez** — cephe çizimi anonim
  `CollisionShape` üretmez; `COLLISION_EXEMPT` listesinde bu yüzden yer
  almaz (çakışma motoru zaten sadece KAT `floors[]` üzerinde çalışır, bkz.
  `scripts/collision/CLAUDE.md` "Bilinen sınırlamalar" — cepheler o
  motorun kapsamı dışındadır).
- **`below_ground` + `window_count`/`door` birlikte kullanılırsa** pencere/
  kapı de `DASHED` çizilir (tutarlılık için); bu proje verisinde bu
  kombinasyon HENÜZ yok, sadece `selftest.py`de sentetik olarak sınandı.
