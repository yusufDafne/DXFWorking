# stairs modülü (merdiven) — DEV-022

Kat paftalarındaki merdiven odasının İÇİNE gerçek basamak/rıht geometrisi,
(yön biliniyorsa) bir yön oku ve bir kesme çizgisi çizer. Kök `CLAUDE.md`nin
eskiden "bilinen basitleştirme" saydığı ("asansör/merdiven kapı sembolü
çizilmez, sadece etiketli kapalı oda olarak gösterilir") boşluğu merdiven
tarafında kapatır.

## Neden ayrı bir modül (kullanıcı kararı, 2026-09-25)

`DEV-022`nin Fikir 1/Fikir 2 analizinde iki seçenek sunuldu: yeni bağımsız
modül mü, yoksa `rooms/`nin genişletilmesi mi. Kullanıcı **Fikir 1**'i
seçti: proje motifiyle (her çizim konusu kendi modülü) tutarlı, `columns/`
ve `furniture/`nin "oda-içi ek eleman = kendi modülü" desenini izler.
`rooms/` bugünkü net kapsamını (poligon + 3 satırlı etiket) korur.

## Veri disiplini — hangi alan gerçek ölçü, hangisi ofis standardı

Bu ayrım kritik ve kasıtlı:

| Alan | Kategori | Kaynak |
|---|---|---|
| `floor_to_floor_mm` | **GERÇEK proje verisi** (kat yüksekliği) | context.json, **ZORUNLU**, asla türetilmez/uydurulmaz |
| `room_id` (→ oda poligonu) | **GERÇEK proje verisi** | context.json, **ZORUNLU** |
| `riser_height_mm` | **Ofis çizim standardı** | Verilmezse `DEFAULT_RISER_MM=170` (ANSI33 hatch ölçeği, Arial Narrow font seçimi ile AYNI kategoride) |
| `going_mm` | **Ofis çizim standardı** | Verilmezse `DEFAULT_GOING_MM=270` (makul bant 250-300mm) |
| `step_count` | Türetilebilir | Verilmezse `floor_to_floor_mm / riser` üzerinden hesaplanır |
| `up_towards` | Opsiyonel yön verisi | Verilmezse yön oku + kesme çizgisi HİÇ çizilmez (kuzey oku ile AYNI "veri yoksa uydurma" deseni) |

**Kullanıcının 2026-09-25 direktifi:** "default olarak 17 cm [riht] belirle
... eğer çok komplike bir nokta olması durumunda bu default değerlerin
otomatik esnetilebilme olanağı da olmalı ... esnetilebilirlik default true
... basamak genişliği 25-30 arasında olması makul ama default 27." Bu,
`DEFAULT_RISER_MM=170.0`, `DEFAULT_GOING_MM=270.0`, `DEFAULT_AUTO_FLEX=True`
olarak BİREBİR uygulandı.

## `resolve_stair` — TEK kaynak (openings::swing_geometry ile AYNI desen)

`resolve_stair(spec, room_polygon) -> StairResolution` hem `validate.py`
hem çizim kodu (`draw_stairs_on_floor`) tarafından ÇAĞRILIR. İkisi ayrı
hesap yaparsa (rev-13'te kapı açılım sektöründe GERÇEKTEN olduğu gibi)
sessizce ayrışırlar — bu modül baştan tek kaynaklı kuruldu.

Hesap sırası:

1. **Basamak sayısı/rıht:** `step_count` açıkça verilmişse `riser =
   floor_to_floor_mm / step_count` (türetilir, doğrulanır). Verilmemişse
   `step_count = round(floor_to_floor_mm / riser_nominal)`; `auto_flex`
   açıksa (varsayılan) `riser` bu `step_count`e göre yeniden hesaplanır
   (kat yüksekliğine TAM oturur); kapalıysa `riser` nominal kalır ve toplam
   kat yüksekliğini tam karşılamıyorsa UYARI verilir (HATA değil — kullanıcı
   `auto_flex=False` ile bunu bilerek istemiştir).
2. **Basamak genişliği (going):** gerekli koşu uzunluğu
   `(step_count - 1) * going` oda'nın uzun ekseninden fazlaysa: `auto_flex`
   açıkken going daraltılır (UYARI); `auto_flex` kapalıyken hiç sığmıyorsa
   direkt `StairFitError`. **`MIN_GOING_MM=250`/`MAX_GOING_MM=300` kontrolü
   KOŞULSUZDUR** — daraltılmış OLSUN ya da OLMASIN, nihai `going` değeri
   her zaman bu bantla karşılaştırılır: altındaysa **`StairFitError`**
   (bağımsız reviewer geçişinde bulunan gerçek bir açık: ilk sürümde bu
   kontrol yalnızca daraltma dalının İÇİNDEYDİ, yani zaten sığan bir odada
   açıkça verilmiş güvensiz bir `going_mm` — örn. 100mm — sessizce
   geçiyordu), üstündeyse UYARI (güvensiz değil, sadece standart dışı).
3. **Yön:** `up_towards` (`N`/`S`/`E`/`W`), merdivenin uzun ekseniyle
   (`travel_axis`) TUTARLI olmalı (dx≥dy → yalnızca `E`/`W` geçerli, aksi
   `StairFitError`). Verilmezse geometri yine hesaplanır, sadece ok/kesme
   çizgisi atlanır.

Her esnetme (riht VEYA going) `StairResolution.warnings`e yazılır;
`generate_dxf.py` bunları "UYARI (merdiven): ..." olarak basar —
`validate.py`deki sürüm/çakışma uyarılarıyla AYNI görünürlük ilkesi
(sessiz varsayım yapılmaz, bkz. kök CLAUDE.md "Deterministik üretim
ilkesi").

## Public API

```python
from stairs import (
    resolve_stair, StairResolution, StairFitError,
    StairDrawingStandard, DefaultStairStandard,
    ensure_stair_layer, stairs_for_floor, draw_stairs_on_floor,
    DEFAULT_RISER_MM, DEFAULT_GOING_MM, MIN_GOING_MM, MAX_GOING_MM,
)

warnings = draw_stairs_on_floor(msp, floor)   # her kat icin
```

`StairDrawingStandard` bir Protocol'dür (`RailDrawingStandard`/
`NorthArrowStyle` ile AYNI enjeksiyon deseni) — yarın ofis farklı bir
sembol (örn. dolu ok yerine çift çizgi ok) isterse yeni bir `draw(...)`
sağlayıcısı yazılır, `draw_stairs_on_floor(msp, floor, standard=...)`
çağrı sözleşmesi DEĞİŞMEZ.

## Katman

`MERDIVEN` katmanı, kod-seviyeli sabit `STAIR_RGB = (60, 120, 150)`
(mavi-gri) rengiyle `ensure_stair_layer` ile idempotent kurulur
(`ensure_axis_layer` deseni — context.json'dan renk ALINMAZ). Bu ton
BİLEREK projedeki diğer kod-seviyeli ailelerden (AKS/KOLON grisi, TEFRİS
kahverengi ailesi) farklı seçildi — bkz. `DEV-030` (katman renk
organizasyonu, henüz PLANNED; bu modül o planın "iyi örnek" listesine
eklenebilir).

## Çakışma denetimi: EXEMPT

`collision/scene.py::COLLISION_EXEMPT` içinde listelenir. Gerekçe: bu
modül YENİ bir mekansal ayak izi ÜRETMEZ — yalnızca zaten `rooms.collision`
tarafından kapsanan bir oda poligonunun İÇİNE anotasyon çizer (aynı oda,
aynı koordinat uzayı). `dimensions`/`axis` ile AYNI "anotasyon, madde
değil" gerekçesi.

## Bilinen sınırlamalar (v1 kapsamı)

- **Yalnızca tek düz kollu (sahanlıksız) merdiven.** Kol, oda poligonunun
  bounding-box'ının UZUN ekseni boyunca koşar. Sahanlıklı/çift kollu/dönel
  merdiven desteklenmez — küçük bir sirkülasyon bandı odasında (örn. bu
  projenin örnek 4000×3000mm `Merdiven` odası, ~3000mm kat yüksekliğiyle)
  bu FİZİKSEL OLARAK yetersiz kalabilir; `resolve_stair` böyle bir durumda
  sessizce geçersiz bir basamak üretmek yerine `StairFitError` fırlatır
  (bkz. `DEVELOPMENT_HISTORY.md` ilgili HD kaydı — örnek projenin gerçek
  `Merdiven` odası bu sınırı BİREBİR karşılıyor, bu yüzden `context.json`a
  henüz `stairs[]` verisi EKLENMEDİ).
- **Kesit entegrasyonu bu revizyonun KAPSAMINDA DEĞİL.** `sections::
  SectionFeatureHook` genişletme noktası merdiven kırılma çizgisi için
  hazır tutuluyor (bkz. `scripts/sections/CLAUDE.md`) ama bu modül henüz
  ona bağlanmadı — ayrı bir takip konusu.
  `stairs` modülü `sections`ı import ETMEZ, ileride tersi yönde
  (`sections` → `stairs`) enjekte edilebilir.
- **Rıht/going tüm basamaklarda TEK bir sabit değerdir** — gerçek
  merdivenlerde ilk/son basamak farklı olabilir (ör. taşma payı); bu
  modül bunu modellemez.
- **Merdiven kolu tam oda genişliğinde çizilir** — korkuluk/duvar payı
  (margin) modellenmez.

## Doğrulama

`python scripts/stairs/selftest.py` — elle hesaplanabilir riht/going
türetme, `auto_flex` açık/kapalı davranış farkı, going daraltma + MIN
altında `StairFitError` (+ yanlış-pozitif: sığan oda hata VERMEMELİ),
**açıkça verilmiş güvensiz `going_mm`nin daraltma dalı hiç TETİKLENMESE
bile reddedilmesi** (+ yanlış-pozitif) ve MAX üstünde UYARI, riht çizgisi
koordinatlarının HEM X HEM Y seyahat ekseninde elle hesaplanabilir olması
(bağımsız review sırasında yakalanan bir x/y-takas hatasının regresyon
testi), `up_towards`/`travel_axis` tutarlılığı (+ yanlış-pozitif), çizilen
varlık sayıları (yönsüz/yönlü), bilinmeyen `room_id`nin çizim tarafında
sessizce atlanması, katman RGB'si.

`validate.py::check_stairs` (arity-1: `room_id` geçerli mi, `resolve_stair`
hata/uyarı üretiyor mu) `resolve_stair`i ÇAĞIRIR — ayrı bir doğrulama
mantığı YAZMAZ.
