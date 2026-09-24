# legend modülü — DEV-012 tamamlandı (Fikir 1)

## Sorumluluk

Kapı/pencere cetveli: `openings::OpeningSchedule`nin ürettiği deterministik
satırları proje çapında (tip, varyant, genişlik) ile **GRUPLAYIP** gerçek
bir mimari cetvel (MARKA/TİP/VARYANT/GENİŞLİK/ADET) olarak çizer.

## Kararın özü: iki fikirden biri seçildi

`DEV-012`nin iki fikri vardı:

- **Fikir 1 (SEÇİLDİ):** kapı/pencere cetveli. Veri zaten HAZIRDI
  (`OpeningSchedule.from_openings`), sadece `generate_dxf.py` sonucu
  kullanmadan atıyordu — en kısa yoldan görünür değer üreten iş buydu.
- **Fikir 2 (uygulanmadı, açık fikir olarak duruyor):** layer/sembol
  lejantı (`TitleBlockLegend`, `LayerSwatch`). Bu modülün İLK taslak
  `CLAUDE.md`'si (rev-4 civarı) bu fikri anlatıyordu; DEV-012 gerçekten ele
  alındığında Fikir 1'in daha somut/hazır olduğu görüldü. `TitleBlockLegend`/
  `LayerSwatch` adları HENÜZ modülde tanımlı DEĞİLDİR — ileride bu fikir
  seçilirse buraya (ayrı sınıflar olarak, mevcut `OpeningLegend`/
  `LegendRenderer`'ı BOZMADAN) eklenir.

## Neden TEK TEK değil GRUPLANMIŞ

Gerçek bir kapı/pencere cetveli, projedeki HER açıklığı ayrı satır olarak
listelemez (bu projede 145 açıklık olurdu) — TİP bazında özetler (10 farklı
(tip, varyant, genişlik) grubu, her biri ADET ile). `OpeningLegend.rows`
bunu yapar; `mark` alanı (`K090`, `P120-D` gibi) context.json'dan gelen bir
veri DEĞİLDİR, **türetilmiş bir sunum kodudur** (`RoomLabeler.room_code`
deseniyle aynı: kat kodu + mahal no'yu birleştirip görünür bir kimlik
üretmek gibi) — context'e YAZILMAZ.

**Pencerede `VARYANT` sütunu `-`dir.** `variant` alanı şemada hem kapı hem
pencerede var olsa da `openings/style.py::DefaultPlanOpeningStyle` bunu
SADECE kapıda kullanır (pencere her zaman `draw_window` ile çizilir,
varyantı yok sayar). Pencere satırında "TEK KANAT" yazmak var olmayan bir
kanat ayrımını UYDURURDU.

## Nereye çizilir: kapak paftasının BOŞ üst alanı

`DEV-012`nin açık kararı ("cetvel kendi paftasında mı, mevcut paftanın boş
alanında mı?") ŞÖYLE yanıtlandı: **kapak paftasının kapak bloğunun ÜSTÜNDE
kalan boş alanda** (kök `CLAUDE.md`: "kapak bloğu paftanın ALTINA oturur,
üstte kalan bölüm BOŞTUR"). Bu alan A4 kapak bloğundan (297mm basılı) daha
uzun bir paftada (diğer tüm paftalarla PAYLAŞILAN ortak Y aralığı yüzünden)
HER ZAMAN vardı ve rev-14'e kadar hiçbir zaman kullanılmıyordu.

Ayrı bir pafta AÇILMADI çünkü: (1) veri küçük (proje çapında tek bir özet
tablo, ~10 satır), (2) mevcut boş alan zaten yeterli, (3) yeni bir pafta
ortak Y-aralığı hesabına girip `CONTENT_PADDING`/aks uzaması gibi başka
sabitleri yeniden tetikleyecekti (bkz. rev-13'teki `CONTENT_PADDING` artışı
— gereksiz karmaşıklık).

## Public API

```python
from legend import OpeningLegend, LegendRenderer, ScheduleRow, COLUMNS

rows = OpeningLegend.rows(context["floors"])   # proje capinda gruplu satirlar
bottom_y = LegendRenderer.draw(msp, rows, x0, y_top, width, ...)
```

`LegendRenderer.draw` modelspace **plain float** yükseklik/satır parametreleri
alır (`row_height`, `title_height`, vb.) — `pafta`yı import ETMEZ. Gerçek
üretimde `generate_dxf.py::draw_cover_sheet`, zaten oluşturduğu `CoverBlock`
örneğinin `block.mm(printed_mm)` fonksiyonuyla bu değerleri hesaplayıp verir
— böylece cetvel metni, kapak bloğunun metniyle AYNI yazı yoğunluğuna sahip
olur, ama `legend` modülü `pafta`nın ölçek/mm dönüşüm mantığını BİLMEZ (iki
modül birbirini import etmez, `axis`/`dimensions` ilişkisiyle aynı desen).

`preview.py::_draw_legend_preview`, AYNI `COLUMNS`/`COLUMN_WEIGHTS`
sabitlerini kullanarak matplotlib karşılığını çizer (kök CLAUDE.md
"önizleme pafta DXF ile birebir" kuralı) — kendi font boyutları
matplotlib'in nokta-tabanlı ölçeklemesine göre AYRICA ayarlanmıştır (DXF'in
gerçek mm yükseklikleriyle birebir eşleşmesi gerekmez, çünkü bu SADECE
görsel bir onay aracıdır).

## Invariant'lar

- `OpeningLegend.rows` deterministiktir: aynı context her zaman aynı
  gruplamayı ve sıralamayı (tip, varyant, genişlik) verir.
- `mark` context'e YAZILMAZ; salt sunum türetmesidir.
- Cetvel, kapak paftasının taşma korumasına (`Sheet.verify_within_frame`)
  TABİDİR — `draw_cover_sheet` içinde `content_entities` yakalanmadan ÖNCE
  çizildiği için ayrı bir kontrol gerekmez, mevcut mekanizma otomatik kapsar.

## Doğrulama

Ayrı bir `selftest.py` YOK — bu modülün mantığı (gruplama + sabit-genişlik
tablo düzeni) `scripts/golden_report.py --golden-set` ve ana proje üzerinde
`--rules` ile dolaylı doğrulanır (satır/hücre sayısı `entity_count`/
`entity_types` ölçümüne yansır; bir gruplama hatası TEXT/LINE sayısını
değiştirir). Elle hesaplanabilir bir gruplama örneği: ana `context.json`'da
145 açıklık → 6 kapı grubu (600/700/800/900/1500/1800mm) + 4 pencere grubu
(1200/1400/1600/1800mm) = **10 satır** (bkz. bu modülün geliştirilmesi
sırasında doğrulanan sayı).

## Sınır

Bu modül `openings`i import eder (salt-okunur, `OpeningSchedule` üzerinden)
ama context'i DEĞİŞTİRMEZ ve hiçbir çizim modülünü BİLMEZ (`pafta`, `axis`
vb. import ETMEZ). Yalnızca `msp` ve plain-float geometri parametreleri
alır.

## Bilinen sınırlamalar / açık kararlar

- **Fikir 2 (layer/sembol lejantı) uygulanmadı** — `TitleBlockLegend`/
  `LayerSwatch` henüz YOK. Seçilirse ayrı sınıflar olarak eklenir.
- **Sadece `door`/`window` tipleri gruplanır.** Şemada başka bir `opening`
  tipi eklenirse (bugün yok) `_TYPE_LABELS`/`_TYPE_PREFIX` güncellenmelidir;
  tanımsız tip `?` öneki ve büyük-harf tip adıyla düşer (sessizce atlanmaz).
- **Tefriş/kolon cetveli YOK** — `FurnitureSchedule` zaten var ama bu
  modülde ÇİZİLMEZ; ayrı bir karar gerekir (bkz. `scripts/furniture/CLAUDE.md`).
