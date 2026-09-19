# pafta modülü — izole çalışma dosyası

Bu proje ilk modülümüz olarak buradan başladı: her mimari çizim konusu
(pafta, aks, duvar/oda, kolon, ...) zamanla kendi modülüne ve kendi
`CLAUDE.md`'sine sahip olacak, böylece ileride bir ajan sadece bu klasörü
açıp, projenin geri kalanını bilmeye ihtiyaç duymadan bu modül üzerinde
derinlemesine/izole çalışabilir. Bu dosya o izolasyonu sağlamak içindir —
mümkün olduğunca **kendi kendine yeterli** olacak şekilde yazılmıştır.

## Bu modül ne yapar

`pafta/__init__.py` şunlardan sorumludur:
1. **`Sheet`** — bir paftanın (çizim sayfasının) çift çizgili çerçevesini
   (dış hat + iç hat) ve sağ-alt köşedeki standart iki satırlı başlık
   kutusunu (üst: ölçek, alt: pafta adı) çizer. **Tüm paftalar (kat planı +
   görünüş) AYNI MUTLAK dış-çerçeve Y-ARALIĞINI (`frame_y0`..`frame_y1`)
   paylaşır** — kurulumda verilen `content_ranges` (her paftanın kendi ham
   `(y_bottom, y_top)` çifti) listesinin EN GENİŞİNİ kapsayacak şekilde BİR
   KERE hesaplanır. **ÖNEMLİ:** bu, her paftayı kendi içeriğinin merkezine
   göre simetrik şişirmek DEĞİLDİR (öyle yapılsa, örn. bir kat planının
   yerel sıfırı ile bir görünüşün zemin kotu farklı olduğundan paftalar
   birbirine göre düşey KAYAR — bu gerçek bir hataydı, düzeltildi). Aynı
   mutlak aralık her paftaya birebir uygulanır. **Genişlik** ise her
   paftanın kendi içeriğine göre serbest/dinamiktir, sınır yoktur.
   Paftaya yerleştirilen her şey (aks baloncukları, dış çizimler) paftanın
   İÇ çizgisinden itibaren `CONTENT_PADDING` kadar içeri çekilir; başlık
   kutusu da İÇ çizginin köşesinde biter (dışına taşmaz, üzerinde de
   durmaz). **Paftalar ayrıca dış çizgilerinden BİTİŞİKTİR** — aralarında
   ekstra boşluk yoktur (`meta.sheet_gap` kaldırıldı); çağıran taraf ardışık
   paftaların X-ofsetini `width + 2*(CONTENT_PADDING+FRAME_GAP)` kadar
   ilerletir.
2. **`fit_text_height` / `fit_uniform_text_height`** — gerçek font
   metrikleriyle (kaba karakter-sayısı tahmini DEĞİL) bir metnin verilen
   genişliğe sığacağı en büyük yüksekliği hesaplar. `Sheet`, TÜM pafta
   adlarını + ölçek metnini alıp bunların HEPSİNİN sığacağı EN KÜÇÜK ortak
   boyutu bulur ve tüm paftalarda aynı boyutu kullanır.
3. **`verify_within_frame` / `PaftaOverflowError`** — bir paftaya ait DXF
   varlıklarının (`content_entities`) o paftanın çerçevesini AŞIP AŞMADIĞINI
   kontrol eder; aşarsa istisna fırlatıp DXF üretimini durdurur. **Bu,
   "bir proje asla pafta dışına taşmamalı" kuralının uygulamasıdır ve
   istisnasızdır.**
4. **`PaperSizePlanner`** — sabit bir ölçek (`meta.scale`) için, projenin en
   yüksek paftasının standart kağıt yüksekliklerinden (45/60/90cm) hangisine
   sığdığını hesaplar/raporlar. Ölçeği KENDİLİĞİNDEN değiştirmez.

## Bu modülün DIŞINDA kalanlar (sorumluluk sınırı)

- Duvar/oda/kapı-pencere çizimi (`Wall`/`WallNetwork`, `draw_wall_network`) —
  ayrı bir modül adayı, henüz `generate_dxf.py` içinde.
- Aks (grid) çizimi (`AxisGrid`) — ayrı bir modül adayı, henüz
  `generate_dxf.py` içinde. Pafta modülü akslardan HABERSİZDİR; sadece
  "bana bu paftaya ait tüm varlıkları ver, ben taşma kontrolü yapayım" der.
- context.json okuma/şema — `scripts/validate.py` ve
  `schema/design.schema.json`'da kalır.

## Genel sözleşme (API) — çağıran taraf (`generate_dxf.py`) ne bekler

```python
from pafta import Sheet, PaftaOverflowError, PaperSizePlanner, CONTENT_PADDING

# Kurulum: TUM pafta adlari + proje olcegi + temel metin yuksekligi + TUM
# paftalarin kendi HAM (y_bottom, y_top) araligi bir kere verilir. Ortak
# MUTLAK Y-araligi bunlarin en genisini kapsayacak sekilde hesaplanir
# (kat plani icin tipik olarak (0, floor_depth), gorunus icin
# elevation_vertical_extent(...) sonucu).
sheet = Sheet(
    scale="1:100", base_text_height=350.0,
    sheet_labels=[...tum pafta adlari...],
    content_ranges=[...her paftanin kendi (y_bottom, y_top) cifti...],
)

# Her pafta icin: o paftaya ait TUM DXF varliklarini (walls/rooms/aks/dim/vb.)
# cizdikten SONRA, cerceveyi cizerken bu varliklari da ver:
sheet.draw(msp, dx, width, y_bottom, y_top, label, content_entities=[...bu paftaya eklenen entity'ler...])
# content_entities tasarsa PaftaOverflowError firlar - generate() bunu
# yakalamaz, DXF uretimi BASARISIZ olarak sonlanir (kasitli).
# Kagit boyutu raporu icin: PaperSizePlanner(scale).select(sheet.outer_height)
# (outer_height TUM paftalarda ayni oldugu icin TEK bir deger yeterli).
```

`content_entities`'i toplamak için tipik desen: pafta içeriğini çizmeye
başlamadan önce `start = len(msp)`, bitirdikten sonra
`content_entities = list(msp)[start:]`.

## Test/doğrulama yaklaşımı

Bu modülde regresyon test dosyası yok (proje küçük ölçekli, elle görsel
doğrulama yapılıyor). Bu modülde değişiklik yapan bir ajan şunu
doğrulamalı:
1. `python scripts/generate_dxf.py` hatasız tamamlanmalı (özellikle
   `PaftaOverflowError` fırlamamalı).
2. Üretilen `output/plan.dxf`'te her paftanın başlık kutusundaki metinlerin
   (`OLCEK ...` ve pafta adı) kutunun dışına taşmadığını, `ezdxf` ile
   `TEXT` varlıklarının `dxf.height` değerini okuyup `fit_text_height` ile
   aynı hesaplamayı elle tekrarlayarak (veya görsel bir debug render ile)
   kontrol etmeli.
3. `ezdxf.bbox.extents()` ile her paftanın toplam varlık sınırlarının
   `Sheet.draw`'a geçirdiği çerçeve sınırları içinde kaldığını teyit etmeli.
4. Tüm paftaların dış çerçeve `CERCEVE` polyline'larının Y-aralığının
   (`min(ys)`, `max(ys)`) BİREBİR aynı olduğunu, ve ardışık paftaların dış
   çerçevelerinin X'te tam bitişik olduğunu (bir paftanın `max(xs)`'i bir
   sonrakinin `min(xs)`'ine eşit) doğrulamalı — bunlar geçmişte bozulmuş ve
   düzeltilmiş iki gerçek regresyon noktasıdır.

## Bilinen sınırlamalar / gelecek işler

- `PaperSizePlanner` şu an sadece SABİT bir ölçek için kağıt boyutu seçer;
  "1/50 favori, sığmazsa 1/100'e düş" kaskad mantığı (yeni/ölçeği henüz
  seçilmemiş bir proje için) henüz YOK — kullanıcı bu konuya ileride daha
  detaylı dönecek.
- Ortak yükseklik SADECE yükseklik içindir; genişlik kasıtlı olarak dinamik
  bırakıldı (kullanıcı talebi). İleride genişlik için de bir "uniform
  template" istenirse, aynı `content_ranges` deseni genişlik için de
  uygulanabilir.
- Aks sıkıştırma (kağıda sığmadığında `AXIS_EXTENSION`/`CONTENT_PADDING`'i
  otomatik küçültme) henüz yok, sadece fikir olarak not edildi.
