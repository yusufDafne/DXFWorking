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
4. **`PaperSizePlanner`** — TMMOB/imar yönetmeliği araştırmasına dayanır
   (bkz. "Mevzuat kaynağı" bölümü). Sabit bir ölçek (`meta.scale`) için,
   projenin en yüksek paftasının standart rulo kağıtların GERÇEK NET
   yüksekliklerinden (`ROLL_PAPER_NET_HEIGHT_MM`: 45'lik→43cm,
   60'lık→58cm, 90'lık→88cm) hangisine sığdığını hesaplar/raporlar
   (`select`). Ölçeği KENDİLİĞİNDEN değiştirmez/küçültmez — hiçbir rulo
   yetmiyorsa `fits=False` döner (çözüm pafta bölme+keyplan'dır, aşağıya
   bakın). Ayrıca `classify_violation(project_type, footprint_m2)` ile,
   `context.json`'da BİLDİRİLMİŞSE (`meta.project_type`), kullanılan
   ölçeğin o proje tipi için mevzuaten (`PROJECT_TYPES`) izinli olup
   olmadığını doğrular ve varsa ihlali açıklayan bir metin döner.

`CoverBlock` (rev-8) ise SADECE kapak paftasında kullanılan, kağıt
üzerinde tam A4 (ISO 7200 Tip-A) bir kapak bloğudur — `Sheet`in her paftada
çizdiği küçük Tip-B şerit antetiyle karıştırılmamalıdır. Ayrıntı için
aşağıdaki "Uygulanan / uygulanmayan kısımlar" bölümüne bakınız.

## Mevzuat kaynağı (rev-4, "PAFTA_MEVZUATI" araştırması)

Kullanıcı, başka bir ajandan aldığı detaylı bir TMMOB/imar yönetmeliği +
DIN/ISO 5457 araştırmasını paylaştı. Modül isimleri/terimleri BİZİM
mimarimize (Sheet/PaperSizePlanner/CONTENT_PADDING) göre uyarlandı, o
araştırmanın kendi isimlendirmesi (STATIK_KALIP vb. proje tipi adları hariç)
birebir kopyalanmadı. Uygulanan / uygulanmayan kısımlar:

- ✅ **Proje tipine göre zorunlu ölçek** (`PROJECT_TYPES`): uygulandı.
- ✅ **Rulo kağıt NET yükseklikleri** (430/580/880mm): uygulandı, eski
  yanlış "brüt=net" varsayımının yerini aldı.
- ✅ **"Ölçek küçültülemez" kuralı**: uygulandı — `PaperSizePlanner` artık
  asla ölçek düşürmeyi ÖNERMEZ bile, sadece "pafta bölme + keyplan gerekir"
  der.
- ✅ **Antet (Tip-B) boyutu ölçeğe göre türetilir** (185×70mm kağıt
  üzerinde): uygulandı, ama `MAX_TITLE_BOX_WIDTH_MM`/`MAX_TITLE_BOX_HEIGHT_MM`
  ile PRATİK bir tavana kırpılıyor — çünkü paftamız henüz TAM bir standart
  kağıda oturan bir tuval değil (bkz. "Bilinen sınırlamalar"). Tipik
  ölçeklerimizde (1:50, 1:100) bu tavan hep devreye girer; sadece çok küçük
  ölçekli (DETAY, 1:5 vb.) paftalarda gerçek değer kullanılabilir.
- ✅ **Tip-A kapak bloğu** (ISO 7200, A4): rev-8'de `CoverBlock` sınıfı olarak
  UYGULANDI. Kapak, basılı kağıt üzerinde **her zaman tam A4 (210x297mm)**
  olur; modelspace karşılığı `to_modelspace(...)` ile ölçeğe göre türetilir
  (1:50 → 10500x14850, 1:100 → 21000x29700 — ikisi de çıktıda 210x297mm
  basar). Çıktı daima ölçekli alındığı için doğru davranış budur.
  - **Konum:** paftanın **sağ-altına** sabitlenir — proje katlandığında
    (DIN 824) bu bölge en üste gelsin diye.
  - **Pafta:** kapak paftasının **DIŞ ÇERÇEVE genişliği kapak genişliğine
    EŞİTTİR** — pafta dış hattı kapak bloğunun dış hattıyla çakışır. Bu
    yüzden `Sheet.draw`'a `padding=0` ve `frame_gap=block.frame_gap` verilir;
    aksi halde çerçeve iki yandan `CONTENT_PADDING+FRAME_GAP` kadar büyür ve
    basılı pafta A4 genişliğinde olmaz. Tip-B şerit anteti de çizilmez
    (`title_box=False`); yükseklik ortak mutlak aralığı korur, kapak bloğu
    alta oturur ve A4 panelinin üst kenarı çift çizgiyle kapatılır.
  - **Çift çizim yok:** Pafta çerçevesi ile kapak bloğunun dış/iç hatları
    aynı yerde olduğundan `CoverBlock.draw(..., outer_frame=False)` ile blok
    kendi dikdörtgenlerini çizmez, yalnızca A4 panelinin üst kenarını ekler.
  - **Çerçeve:** `Sheet`in çift çizgili çerçevesi gibi **her kenardan EŞİT**
    offsetli (kağıt üzerinde 10mm, `PRINTED_COVER_FRAME_GAP_MM`). Önceki
    sürümdeki DIN/ISO sayfa marjı (sol 20 / diğer 10) eşit olmayan bir
    görünüm verdiği için KALDIRILDI.
  - **İçerik:** proje adı (başlık), `PROJE TIPI`/`OLCEK`/`MIMAR`/`TARIH`
    bilgi satırları ve `meta.cover.signature_fields` ile sürülen imza
    kutuları (2 sütunlu ızgara, başlığı boş gelen alan `(UNVAN)`).
  - **Veri uydurulmaz:** `architect_name`/`date` context.json'da yoksa metin
    yazılmaz, elle doldurulacak bir çizgi bırakılır. Ayrıntılı kapak
    TASARIMI ayrı bir talep olarak gelecektir.
- ❌ **Parçalı pafta + Keyplan** (bina aks/dilatasyon hatlarından bölünüp
  her parçaya 1:500/1:1000 taranmış bir konum planı eklenmesi): HENÜZ
  UYGULANMADI (büyük bir özellik) — şu anki projemiz zaten tek parça
  sığdığı için ihtiyaç doğmadı, ama mevzuata göre DOĞRU sonraki adım budur
  (ölçek küçültmek DEĞİL).
- ❌ **Sayfa marjları** (sol 20mm cilt payı, sağ/üst/alt 10mm): sabit
  olarak kaydedildi (`PRINTED_MARGIN_LEFT_MM`, `PRINTED_MARGIN_MM`) ama
  HENÜZ ÇİZİLMİYOR — bunlar gerçek bir kağıt/plot-alanı sınırı ima eder,
  bizim modelspace-only paftamızda henüz karşılığı yok (bkz. altta).

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
# Mevzuat uygunluk kontrolu icin (meta.project_type varsa):
# PaperSizePlanner(scale).classify_violation(project_type, footprint_m2)
```

`content_entities`'i toplamak için tipik desen: pafta içeriğini çizmeye
başlamadan önce `start = len(msp)`, bitirdikten sonra
`content_entities = list(msp)[start:]`.

**Kapak paftası (Tip-A, rev-8):**

```python
from pafta import CoverBlock

block = CoverBlock(scale)          # A4 olculeri olcege gore turetilir
gap = block.frame_gap
# Pafta DIS cercevesi = kapak genisligi. padding=0 oldugu icin dx, paftanin
# IC cizgisinin sol kenaridir; dis hat bunun `gap` kadar disindan gecer ve
# kapak blogu tam o dis hattan baslar.
sheet_width = block.width - 2 * gap
x0 = dx - gap
y0 = sheet.frame_y0
block.draw(
    msp, x0, y0,
    title=meta["project_name"],
    info_rows=[("PROJE TIPI", ...), ("OLCEK", ...), ("MIMAR", ...), ("TARIH", ...)],
    signature_labels=meta["cover"]["signature_fields"],
    outer_frame=False,     # dis/ic hat paftanin kendi cercevesinden gelir
)
# info_rows'ta degeri BOS gelen satir icin metin UYDURULMAZ: elle doldurulacak
# bir cizgi cizilir. signature_labels'ta basligi bos olan alan "(UNVAN)" olur.
```

Kapak paftası çizilirken `Sheet.draw`'a `width=sheet_width`,
`title_box=False`, `padding=0.0` ve `frame_gap=gap` verilir; `y_bottom`/
`y_top` olarak paylaşılan aralık (`frame_y0 + gap`, `frame_y1 - gap`)
geçilir ki bu pafta ortak yüksekliği bozmasın. Ardışık paftaya geçerken
genel `width + 2*(padding+frame_gap)` formülü bu pafta için GEÇERSİZDİR;
`draw_cover_sheet` dış çerçevenin sağ kenarını döndürür ve sonraki pafta
doğrudan oraya oturtulur. Kapak bloğu da diğer her içerik gibi `content_entities`'e dahil
edilir, yani `Sheet.draw`'ın taşma kontrolünden geçer.

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

- **Uniform sheet template (öncelikli):** Paftamız şu an içeriği SIKI SARAN
  bir tuval (content+padding), TAM bir standart kağıda (örn. gerçek 90'lık
  rulo eni) oturan bir şablon DEĞİL. Bu yüzden antet gibi kağıt-mm tabanlı
  standartlar (185×70mm) `MAX_TITLE_BOX_*` ile kırpılmak ZORUNDA kalıyor.
  Bu uygulanırsa (paftalar gerçek bir rulo genişliğine/uzunluğuna
  oturtulursa) kırpma kalkar, gerçek standart değerler dogrudan kullanılır.
- **Pafta bölme + Keyplan** (mevzuata göre "sığmazsa ölçek küçült" DEĞİL,
  bunun yerine yapılması gereken şey): büyük bir özellik, henüz yok. Bina
  aks/dilatasyon hatlarından bölünür, her parçaya küçük ölçekli
  (1:500/1:1000) taranmış bir konum (keyplan) eklenir.
- **Tip-A kapak VERİSİ** (ISO 7200): kapağın kendisi çizilir, ama müellif
  (`meta.cover.architect_name`), tarih (`meta.cover.date`) ve ayrılmış iki
  imza alanının unvanı henüz kullanıcı tarafından verilmedi; bu alanlar
  şimdilik boş doldurma çizgisi olarak çıkar (bkz. `DEV-007`). Ruhsat/onay
  alanlarının gerekip gerekmediği de ayrı bir karardır.
- **Kapak bloğunun ölçek/boyut sınırı:** `CoverBlock` A4'ü ölçeğe göre
  büyüttüğü için çok küçük ölçekli (büyük paydalı) projelerde blok, paftanın
  içerik alanından yüksek kalabilir; benzer şekilde `floor_width`, A4
  genişliğinden darsa blok yanlara taşar. Taşma `Sheet.draw` içindeki
  `verify_within_frame` ile yakalanır ve `PaftaOverflowError` fırlatılır —
  sessiz hatalı çıktı üretilmez (1:200 ile doğrulandı) — ancak otomatik bir
  küçültme/yeniden yerleşim stratejisi YOKTUR. Ayrıca bu kontrol DIŞ
  çerçeveye göre yapılır: blok `CONTENT_PADDING` alanına girse de, dış
  çerçeveyi aşmadığı sürece hata vermez.
- **Sayfa marjı çizimi** (20mm sol / 10mm sağ-üst-alt, gerçek kağıt
  sınırını modelspace'te göstermek): sabitler kayıtlı ama çizilmiyor.
- **`PaperSizePlanner`, proje tipi henüz SEÇİLMEMİŞ yeni bir proje için**
  "en uygun ölçeği kendi seç" modunda ÇALIŞMAZ — sadece BİLDİRİLEN
  `meta.scale`'i BİLDİRİLEN `meta.project_type`'a göre doğrular. Otomatik
  tip/ölçek ÖNERİSİ (örn. "bu oturum için MIMARI_UYGULAMA + 1:50 öneririm")
  henüz yok.
- Ortak yükseklik SADECE yükseklik içindir; genişlik kasıtlı olarak dinamik
  bırakıldı (kullanıcı talebi). İleride genişlik için de bir "uniform
  template" istenirse, aynı `content_ranges` deseni genişlik için de
  uygulanabilir.
- Aks sıkıştırma (kağıda sığmadığında `AXIS_EXTENSION`/`CONTENT_PADDING`'i
  otomatik küçültme) mevzuata göre zaten YANLIŞ bir cozum (ölçek/aks
  küçültülemez) - bu fikir kaldırıldı, yerine pafta bölme+keyplan kondu.
