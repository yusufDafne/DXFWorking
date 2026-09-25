# levels modülü (kot / datum) — DEV-029

Standart kot (spot elevation) işareti: bayrak (üçgen) + kot metni. Kat
paftalarında (rampa/teras kademe farkı) VE kesit/görünüşlerde (her kat
sınırında) kullanılır.

## Neden ayrı bir modül (kullanıcı kararı, 2026-09-25)

Kullanıcı `DEV-021`/`DEV-025` çalışması sırasında (rev-17) bu konuyu açtı:

> "kot verme mantıklarını yöneten bir mantık istiyorum ... kot organizasyonu
> hem planda hem kesitte kullanılacaktır ... bu mantığın projenin geneline
> hakim olması gerekecektir."

`DEVELOPMENT_TASKS.md::DEV-029` analizinde önerilen "yeni, küçük, bağımsız
modül" seçeneği (`elevations/`e eklemek yerine) kullanıcı tarafından
onaylandı: kot PLAN görünümünde de kullanılır (rampa/teras spot kotu) — bu,
`elevations/`nin bugünkü net kapsamının (SADECE cephe istifi) DIŞINDA bir
sorumluluktur. Kot format/sembol standardı ile "seviye istifi hesabı"
BİRBİRİNDEN AYRI iki karardır — `sections`/`northarrow`ın `elevations`/
`pafta`dan AYRI tutulma gerekçesiyle AYNI (bkz. `HD-011`).

## Kat yüksekliği hesabını YENİDEN YAZMAZ

Bu modülün EN KRİTİK invariant'ı: `elevations::LevelStack`in zaten
hesapladığı `(y0, y1)` çiftlerini TÜKETİR, kendi kümülatif toplam mantığı
İCAT ETMEZ. Bağımlılık YÖNÜ **tektir** ve **DOLAYLIDIR**:

- `levels` modülü `elevations`i import ETMEZ.
- `level_boundaries_from_placements(placements)`, `LevelStack.placements()`in
  DÜZ ÇIKTISINI (herhangi bir `(etiket, y0, y1)` üçlü listesi — SEKİL
  beklenir, SINIF değil) işler. `axis_grid`in `draw_on_elevation(...)`
  sözleşmesiyle AYNI "duck typing" deseni.
- `generate_dxf.py` (orkestratör) `LevelStack`i zaten kuruyor
  (`elevations`/`sections` için); `levels.level_boundaries_from_placements
  (stack.placements())` çağrısıyla köprüyü KENDİSİ kurar — iki modül
  birbirini BİLMEZ.

## Kot metni formatı (kullanıcının 2026-09-25 kararı)

`format_level(value_mm) -> str`: işaret + 2 ondalıklı METRE.

```python
format_level(3000.0)   # "+3.00"
format_level(-200.0)   # "-0.20"
format_level(0.0)      # "±0.00"
format_level(1.0)      # "±0.00" (2 ondalıkta sıfıra yuvarlanır)
```

Sıfıra YUVARLANAN (2 ondalıkta) her değer `"±0.00"` yazılır — hem tam sıfır
hem de yuvarlamayla sıfıra düşen değerler için tutarlı; `"-0.00"` gibi
çirkin/yanlış bir görünüm bilerek engellenir. Bu SADECE gösterim formatıdır;
context.json'daki asıl ölçü birimi (mm) DEĞİŞMEZ — kök `CLAUDE.md`
"Ölçülendirme birimi" ile AYNI ilke (sayı uydurulmuyor, formatlanıyor).

## İki tüketim yolu

### 1. Kesit/görünüş — OTOMATİK türetilir, veri EKLENMEZ

`draw_level_marks(msp, mark, boundaries, anchor_x)`: `boundaries`
(`level_boundaries_from_placements`in çıktısı) zaten `context.json::
elevations[].levels[].height`den (GERÇEK proje verisi) hesaplanmıştır — bu
modül SADECE var olan sayıyı FORMATLAR ve ÇİZER, yeni veri İSTEMEZ.
`anchor_x` çağıranın kararıdır (bu modülün işi DEĞİLDİR, `NorthArrow`
"Yerleşim" bölümüyle AYNI ayrım) — `generate_dxf.py` her elevation/section
paftasının SOL kenarının biraz dışına (`dx`nin biraz solu, zemin çizgisinin
zaten uzandığı `dx-1000` payının İÇİNDE) yerleştirir.

### 2. Plan — GERÇEK veri, verilmezse çizilmez

`draw_plan_level_marks(msp, floor, mark)`: `floor['level_marks']`teki HER
girdiyi kendi `position`unda çizer. Plan düzleminde "kat yüksekliği" diye
bir kavram YOKTUR (bir rampanın/terasın kademe farkı proje-özgü, gerçek bir
karardır) — bu yüzden OTOMATİK türetme YAPILAMAZ. Veri context'te AÇIKÇA
verilmelidir (`id`, `position`, `value_mm`); verilmezse HİÇBİR ŞEY çizilmez
— kuzey oku ile AYNI "veri yoksa uydurma" deseni.

## Public API

```python
from levels import (
    LevelMark, LevelMarkStyle, DefaultLevelMarkStyle,
    format_level, level_boundaries_from_placements,
    draw_level_marks, draw_plan_level_marks, ensure_level_layer,
)

mark = LevelMark(scale)                                   # varsayilan stil
boundaries = level_boundaries_from_placements(stack.placements())
draw_level_marks(msp, mark, boundaries, anchor_x=dx - 300.0)
draw_plan_level_marks(msp, floor, mark)                   # opsiyonel, veri varsa
```

`LevelMarkStyle` bir Protocol'dür (`RailDrawingStandard`/`NorthArrowStyle`/
`StairDrawingStandard` ile AYNI enjeksiyon deseni) — yarın ofis farklı bir
sembol isterse yeni bir `draw(...)` sağlayıcısı yazılır, çağrı sözleşmesi
DEĞİŞMEZ.

## Katman

`KOT` katmanı, kod-seviyeli sabit rengiyle (`scripts/palette::PALETTE`den,
DEV-030) `ensure_level_layer` ile idempotent kurulur — yeşil, diğer
"primary" kod-seviyeli ailelerden (AKS/KOLON grisi, KESİT kırmızısı,
MERDİVEN mavisi) bilerek farklı bir aile.

## Çakışma denetimi: EXEMPT

`collision/scene.py::COLLISION_EXEMPT` içinde — `dimensions`/`axis` ile AYNI
gerekçe: bir ANOTASYONDUR (bayrak+metin), plan geometrisinde anlamlı bir
alan kaplamaz.

## Doğrulama

`python scripts/levels/selftest.py` — `format_level`in elle hesaplanabilir
6 durumu, `level_boundaries_from_placements`in elle hesaplanabilir sonucu
(+ boş liste yanlış-pozitifi), `LevelMark.draw`in tam 2 varlık ürettiği
(bayrak+metin), boyutun ölçekle DOĞRUSAL türediği (1:100 = 1:50 × 2, elle
hesaplanabilir), `draw_level_marks`in N sınır için TAM 2N varlık ürettiği,
plan kot işaretlerinin OPT-IN olduğu (veri yoksa çizilmez + veri varsa
çizilir — her iki yön), özel bir stilin enjekte edilebildiği (sahte stil
test çiftiyle), katman RGB'sinin kod-sahipli olduğu.

## Bilinen sınırlamalar

- **`validate.py`de `level_marks[]` için özel bir kontrol YOK** —
  `position`/`value_mm` şema tarafından zaten sayısal/zorunlu kılınıyor;
  ekstra bir geometrik/mantıksal invariant (örn. plan sınırları içinde mi)
  henüz tanımlı değil.
- **Kesit/görünüşteki kot işaretlerinin `anchor_x` konumu piksel-kesin bir
  çakışmama garantisi vermez** — `NorthArrow` "Yerleşim" bölümündeki AYNI
  pragmatik yaklaşım (güvenli bölge seçimi, per-konum kaçınma değil).
  `generate_dxf.py`deki `anchor_x` ofseti (`to_modelspace(50, denom)`),
  ÖLÇEKLE BÜYÜYEN bir değerdir — bugünkü sabit `1:50` ölçeğinde
  `pafta::CONTENT_PADDING` (sabit 4000mm) içinde rahatça kalır (gerçek
  proje + 6 golden referansta elle doğrulandı), ama çok büyük ölçek
  paydalarında (`1:200`/`1:500`) bu payı AŞABİLİR — böyle bir durumda
  üretim SESSİZCE hatalı bir dosya ÜRETMEZ, `PaftaOverflowError` ile
  DURUR (bkz. `docs/development/DEVELOPMENT_HISTORY.md` HD-015
  "bağımsız reviewer düzeltmesi").
- **Tek bir dikey eksen (Y) varsayılır** — yatay bir kot (örn. X ekseninde
  bir kademe) bugün modellenmiyor, kapsamı dışında.
