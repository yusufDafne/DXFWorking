# Geliştirme Görev Kuyruğu

Bu dosya sistem geliştiricisinin sıradaki kontrollü işini gösterir. Aynı anda
tek bir görev `IN_PROGRESS` olabilir. Sistem mimarı `READY` görevi başlatır;
agent kendi başına sıra değiştirmez.

## READY

### DEV-006 — Golden fixture kataloğu

- **Durum:** COMPLETED (rev-10)
- **Sonuç:** `golden_report.py` üç katmanlı hale geldi: ölçüm raporu +
  **semantik kurallar** + **fixture koşucusu**. Kurallar: `room_labels`
  (3 satır ve oda içinde), `opening_symbols` (kapı başına ARC),
  `axis_bubbles` (çizgi baloncuğa girmez), `block_references` (tanımsız blok
  yok), `declared_layers`. Beş kuralın hepsi **negatif testle** doğrulandı
  (kasıtlı bozma → kural patladı). `entity_bbox` artık ezdxf'in gerçek extent
  hesabını kullanıyor; önceki sürüm `INSERT` için yalnızca ekleme noktasını
  döndürüyordu (blok körlüğü — `DEV-018`de tespit edilmişti) ve `TEXT` için
  de metin genişliğini görmüyordu. Fixture kataloğu
  `docs/development/fixtures/` altında: `minimal` ve `tefris_kolon`.
- **Fixture'ların ilk günde yakaladıkları (gerçek bulgular):**
  1. **Kapak paftası projeye asgari yükseklik dayatıyor.** 1:50'de A4 kapak
     14850 yüksek; içeriğin düşey açıklığı 8150'den küçükse üretim
     `PaftaOverflowError` ile durur. `minimal` fixture 4000 derinlikle
     yazıldığında hemen patladı. Bu sınır daha önce belgelenmemişti.
  2. **`draw_floor_sheet` içinde isim çakışması.** Mahal etiketi için
     kullanılan `label_style` yerel değişkeni, kolon `label_style`
     parametresini gölgeliyordu; `tefris_kolon` fixture'ı bunu yakaladı.
- **Kayıt:** `DEVELOPMENT_HISTORY.md` içindeki `HD-006`.
- **Önceki öncelik:** 1
- **Bu görev neden var (problem):** Bugünkü `scripts/golden_report.py`
  yalnızca **dört kaba ölçü** karşılaştırıyor: toplam entity sayısı, entity
  tür dağılımı, layer dağılımı ve modelspace bounding box. Bu, bir
  regresyonu yakalamak için **zayıftır** — örneğin bir duvar 2 metre kaysa,
  bir kapı ters yöne açılsa veya bir mahal etiketi yanlış odaya yazılsa
  entity sayısı ve türleri değişmediği için rapor **"eşleşiyor" der ve
  hatayı kaçırır**. Bounding box da yalnızca en dış sınırı gördüğü için iç
  geometrideki kaymaları fark etmez.
- **Amaç:** Golden kontrolünü "kaç tane var" seviyesinden "doğru yerde ve
  doğru biçimde mi" seviyesine çıkarmak; bunu tüm projeyi tek parça
  karşılaştırarak değil, modül bazlı fixture'larla yapmak.
- **Fikir 1 — Modül bazlı mini fixture'lar:** Her modül için küçük, elle
  doğrulanmış birer context parçası (tek oda + tek kapı; iki aks + bir ölçü;
  tek kapak paftası) ve her birinin beklenen çıktısı. Bütün projeyi
  karşılaştırmak yerine modül modül karşılaştırılır; böylece bir fark
  çıktığında **hangi modülün** bozulduğu doğrudan görünür. Bugün 2226
  entity'lik tek bir rapor var ve fark çıktığında nerede olduğu belli olmaz.
- **Fikir 2 — Kritik sembol/geometri beklentileri:** Sayı yerine kural
  doğrulamak. Örnek beklentiler: "her kapı açıklığı 1 ARC + 3 LINE üretir",
  "aks çizgisi baloncuğun içine girmez", "her mahal etiketi 3 TEXT'tir ve
  tamamı kendi oda poligonunun içinde kalır", "ölçü metni tam sayı cm'dir".
  Bunlar toleranslı geometrik karşılaştırmalardır ve bugünkü raporun tamamen
  kör olduğu hata sınıfını yakalar. (Mahal etiketi kuralı `DEV-008`de elle
  yazılan bir kontrol olarak zaten bir kez uygulandı — 125/125 oda doğrulandı;
  bu görev onu kalıcı hale getirir.)
- **Açık kararlar:** Fixture'lar `context.json`'dan bağımsız ayrı dosyalar mı
  olacak? Geometrik karşılaştırmada tolerans ne olacak? Beklenti tanımları
  veri (JSON) olarak mı, kod olarak mı yazılacak?

## COMPLETED

### DEV-001 — Openings modülünü oluştur

- **Durum:** COMPLETED
- **Sonuç:** Typed `Opening`, `Door`, `Window`, `OpeningSchedule` ve
  enjekte edilebilir `DefaultPlanOpeningStyle` `scripts/openings/` içine alındı;
  generator host-wall ve açıklık genişliği doğrulaması yapıyor.
- **Kayıt:** `DEVELOPMENT_HISTORY.md` içindeki `HD-003`.

### DEV-002 — Room modülü

- **Durum:** COMPLETED
- **Sonuç:** `Room`, `PolygonOps`, `RoomLabeler` ve scanner sınırı
  `scripts/rooms/` içinde; kapanış, alan, self-intersection ve units-aware
  alan doğrulaması aktif.
- **Kayıt:** `DEVELOPMENT_HISTORY.md` içindeki `HD-003`.

### DEV-003 — DimensionChain modülü

- **Durum:** COMPLETED
- **Sonuç:** `DimensionChain`, `LinearDim`, `DimensionStyle` ve `ChainLayout`
  `scripts/dimensions/` içinde; AxisGrid gerçek DXF ölçülerini bu API ile
  üretir ve baseline bounds kontrolünden geçirir.
- **Kayıt:** `DEVELOPMENT_HISTORY.md` içindeki `HD-003`.

### DEV-004 — Golden output anlamsal karşılaştırması

- **Durum:** COMPLETED
- **Sonuç:** `scripts/golden_report.py` entity count/type, layer dağılımı,
  modelspace bbox ve SHA-256 raporu üretir; `--compare` ile semantic kontrol
  yapar.
- **Kayıt:** `DEVELOPMENT_HISTORY.md` içindeki `HD-002`.

### DEV-005 — Agentic kontrol altyapısı

- **Durum:** COMPLETED
- **Sonuç:** `development_control.py` atomik görev kilidi,
  `AGENT_PERMISSIONS.json` rol izinleri ve `PROVENANCE_TEMPLATE.json` eklendi.
- **Kayıt:** `DEVELOPMENT_HISTORY.md` içindeki `HD-002`.

## PLANNED — modül bazlı plan maddeleri

Her modülün kendi plan maddesi vardır. Her maddede **iki fikir** önerilir; bunlar
uygulama izni DEĞİLDİR — sistem mimarı (kullanıcı) bir fikri seçer, kendi
yönlendirmesini ekler ve görevi açıkça başlatır. Fikirler ilgili
`scripts/<modül>/CLAUDE.md` sözleşmesinin mevcut durumundan türetilmiştir.

**Şartname ile fikir farkı:** Bir maddede "Şartname" başlığı varsa, o kısım
kullanıcı tarafından KESİN olarak verilmiştir ve fikir gibi değerlendirilmez.

### DEV-007 — `pafta/` — kapak verisi ve pafta altyapısı

- **Durum:** BLOCKED — çizim tarafında yapılacak iş kalmadı, yalnızca
  kullanıcıdan gelecek resmi veri bekleniyor.
- **rev-9 değerlendirmesi:** Kullanıcı "tekrar bir çalışma gerekiyorsa
  uygula" dedi; kod tarafı gözden geçirildi ve **ek iş gerekmedi**. Proje
  fontu Arial Narrow'a geçtiğinde kapak da otomatik olarak yeni fontu aldı
  (`Standard` text style üzerinden) ve pafta taşma kontrolünden sorunsuz
  geçti. Aşağıdaki iki fikir kullanıcı tarafından seçilmedi, bekliyor.
- **Mevcut durum:** Tip-A kapak çizimi/yerleşimi tamamlandı (`CoverBlock`,
  bkz. `HD-004`). Eksik olan yalnızca resmi veridir. Ayrıca `PaperSizePlanner`
  90'lık ruloya sığmayan bir proje için "pafta bölme + keyplan" gerektiğini
  raporluyor ama bu henüz uygulanmadı.
- **Fikir 1 — Pafta bölme + keyplan:** En büyük rulo yetmediğinde mevzuatın
  tek kabul ettiği çözüm. Yapı aks/dilatasyon hatlarından parçalara bölünür ve
  her parçaya, binanın şematik konturunu tarayarak vurgulayan 1:500/1:1000
  ölçekli bir keyplan eklenir. `PaperSizePlanner.select(...)` zaten
  `fits=False` döndürdüğü için tetikleme noktası hazır.
- **Fikir 2 — Uniform sheet template:** Paftayı içeriği saran serbest bir tuval
  yerine gerçek standart kağıt boyutuna oturtmak. Bu yapılırsa antetin
  `MAX_TITLE_BOX_WIDTH_MM` / `MAX_TITLE_BOX_HEIGHT_MM` kırpması kalkar ve
  DIN/ISO 5457 Tip-B ölçüsü tam uygulanabilir; sayfa marjları (sol 20mm,
  diğer 10mm) da gerçekten çizilebilir.
- **Açık kararlar:** `meta.cover.architect_name`, `meta.cover.date`, ayrılmış
  iki imza alanının unvanı, ruhsat/onay alanı gerekip gerekmediği. Kapak
  **tasarımı** için kullanıcı ayrı bir talep paylaşacak; o talepte geometri
  (A4, sağ-alt sabitleme, eşit offset, antetsiz pafta) değişmemelidir.

### DEV-008 — `rooms/` — 3 satırlı mahal etiketi (`RoomLabeler`)

- **Durum:** COMPLETED (rev-9)
- **Sonuç:** Şartname birebir uygulandı. `RoomLabeler` artık 3 satır üretiyor
  (mahal adı BLOK / kat kodu-mahal no / alan), sığdırma hem **genişliğe hem
  yüksekliğe** bakıyor, kat kodu `floors[].code`'dan ve mahal no
  `rooms[].no`'dan geliyor (türetilmiyor). Proje fontu Arial Narrow oldu;
  bunun sahibi yeni `scripts/typography/` modülüdür ve mahal etiketi için
  `meta.fonts.room_label` ile ayrı font seçilebilir.
- **Doğrulama:** 125/125 mahal etiketinin gerçek font metrikleriyle ölçülen
  bounding box'ı kendi oda poligonunun içinde kaldı; mahal no ve kat kodu
  benzersizlik kontrolleri `validate.py`ye eklendi ve negatif testle
  doğrulandı. Kayıt: `DEVELOPMENT_HISTORY.md` içindeki `HD-005`.
- **Uygulanmayan fikirler:** Aşağıdaki iki fikir kullanıcı tarafından
  seçilmedi; şartname doğrudan uygulandı. `RoomLabelStyle` Protocol'ü ve
  leader'lı yerleşim hâlâ açık birer geliştirme olarak durur.
- **İlgili:** Etiketin DXF `BLOCK` + `ATTRIB` olarak üretilmesi `DEV-018`de
  planlandı.
- **Önceki durum (kayıt):** `RoomLabeler.draw` tek satır, sabit biçim
  `"{ad} ({alan} m2)"` üretiyordu; yalnızca oda genişliğine bakıyordu.

**Şartname (kullanıcı tarafından verildi — varsayılan format):**

Etiket **3 satırdır**:

```
SALON        <- 1. satir: mahal adi, BLOK
ZK-04        <- 2. satir: kat kodu + mahal no
28.9 m2      <- 3. satir: alan
```

- Yazı tipi **Arial Narrow**.
- Mahal adı **blok** olarak işlenir.
- Mahal kodu, katı ifade eden bir önek taşır. Kullanıcının verdiği eşleşme:
  `B1` = 1. bodrum, `B2` = 2. bodrum, `ZK` = zemin kat, `K1`/`K2`/`K3`... =
  normal katlar.

- **Fikir 1 — `RoomLabelStyle` Protocol + hazır format seti:** Biçimi
  `openings::OpeningSymbolStyle` deseninde enjekte edilebilir yap; şartnamedeki
  3 satırlı biçim `DefaultRoomLabelStyle` olur, yanına dar odalar için tek
  satırlık kompakt bir biçim ve sunum çizimleri için mahal no'suz bir biçim
  konur. Hangi stilin kullanılacağı pafta/proje seviyesinde seçilir.
- **Fikir 2 — Yerleşim zekası:** Etiketi sadece küçültmek yerine, oda
  poligonunun içine sığan en geniş eksen-hizalı dikdörtgeni bulup bloğu oraya
  oturtmak; sığmıyorsa etiketi odanın dışına alıp **leader (kılavuz çizgi)**
  ile odaya bağlamak. Bu, içbükey (L şeklinde) odalarda etiketin dışarı
  düşmesi sorununu da çözer.
- **Açık kararlar:**
  - **Çatı katının kodu ne olacak?** Kullanıcı `B1/B2/ZK/K1..` verdi, çatı
    katı için kod belirtilmedi — uydurulmayacak.
  - **Mahal no nereden gelecek?** İki seçenek: (a) `floors[].rooms[].no`
    olarak schema'ya eklenip veriden gelir, (b) oda sırasından deterministik
    türetilir. Türetme, oda sırası değişince numaraların kaymasına yol açar.
  - **Kat kodu nereden gelecek?** `floors[].code` schema alanı mı, yoksa
    `floors[].label`'dan çıkarım mı? Etiketten çıkarım kırılgandır.
  - **Arial Narrow kapsamı:** yalnızca mahal etiketi mi, yoksa projedeki tüm
    metinler mi? Bu, `pafta.DEFAULT_FONT = "txt"` sabitini ve dolayısıyla TÜM
    `fit_text_height` ölçümlerini etkiler (antet, cephe etiketleri, aks).
    Ayrıca Arial Narrow bir TTF'tir; DXF text style tanımı ve alıcı
    bilgisayarda fontun bulunması ayrıca değerlendirilmeli.

### DEV-009 — `furniture/` — tefriş modülü

- **Durum:** COMPLETED (rev-10)
- **Sonuç:** `scripts/furniture/` kuruldu. 22 tipli konut tefriş kataloğu
  (koltuk 3'lü/2'li, berjer, sehpa, TV ünitesi, yemek masası 4/6, sandalye,
  tek/çift yatak, gardırop, komodin, mutfak tezgahı, ocak, evye, buzdolabı,
  bulaşık mak., lavabo, klozet, duş teknesi, küvet, çamaşır mak.). Tefriş
  **her zaman DXF `BLOCK`** olarak çizilir (tip başına bir tanım, yerleşim
  başına bir `INSERT`). Beş işlevsel grup ve her birine **kahverengi
  ailesinden düşük kontrastlı** bir layer rengi. `FurnitureSchedule`
  salt-okunur liste üretir.
- **Kapı kararı (kullanıcı sordu):** Kapı **tefriş değildir, duvar
  açıklığıdır** — `openings/` + `walls/` sahiplenir, ki bu projede zaten
  öyledir. Gerekçe endüstri standardıdır: IFC'de `IfcDoor` bir
  `IfcBuildingElement`tir (`IfcFurnishingElement` değil), AIA/NCS layer
  standardında kapı `A-DOOR`, tefriş `A-FURN`; ayrıca kapı geometrisi host
  duvara bağımlıdır. Ayrıntı: `scripts/furniture/CLAUDE.md` "Kapı kimin?".
- **Kayıt:** `DEVELOPMENT_HISTORY.md` içindeki `HD-006`.
- **Uygulanmayan:** `counters[]` (mutfak tezgahı) hâlâ `generate_dxf.py`
  içinde ad-hoc çiziliyor; bu modüle devri ayrı bir karardır. Tefriş/duvar/
  kapı-açılımı çakışma kontrolü YOK.
- **Fikir 1 — Parametrik tefriş kataloğu:** `FurnitureCatalog`, tip adından
  ölçülü bir çizime çözen bir sözlük olur (`WallCatalog` deseni). Context'te
  yalnızca **tip + konum + rotasyon** tutulur, geometri koddan gelir. Aday
  set: yatak (90/140/160), koltuk takımı, yemek masası (4/6 kişilik), mutfak
  tezgahı + ocak/evye, gardırop, lavabo/klozet/duş-küvet, araç (otopark).
  Böylece context şişmez ve ölçüler tek yerden yönetilir.
- **Fikir 2 — Oda tipine göre tefriş şablonu:** `name`/oda tipi bilinen bir
  mahale (örn. "Yatak Odası") şablon bir yerleşim önerilir; modül yalnızca
  **öneri** üretir, `RoomPolygonScanner` gibi context'e otomatik yazmaz.
  Validator sığma ve duvar/kapı çakışması kontrolü yapar; yerleşim kullanıcı
  onayından sonra context'e girer.
- **Açık kararlar:** Katalog ölçüleri hangi kaynaktan gelecek (ofis
  standardı / yönetmelik)? Kapı açılım alanıyla çakışma bloklayıcı hata mı,
  uyarı mı?
- **İlgili:** Tefrişin DXF `BLOCK` olarak tanımlanıp tanımlanmayacağı
  `DEV-018`de planlandı. Tefriş uygulanmadan ÖNCE o karar verilirse kod iki
  kez yazılmaz.

### DEV-010 — `columns/` — kolon modülü

- **Durum:** COMPLETED (rev-10)
- **Sonuç:** `scripts/columns/` kuruldu. Kolonlar **taralıdır**; tarama
  deseni/ölçeği dinamiktir (`meta.column_hatch`) ve varsayılanı kullanıcının
  verdiği değerlerdir: **`ANSI33`, ölçek `3.0`**. Kesit kataloğu
  (`S30x60`…`D50`) veya doğrudan `width`/`depth`. Kontur `KOLON`, tarama
  `KOLON-TARAMA` layer'ında (baskı ağırlıkları bağımsız ayarlanabilsin diye).
  Kolonlar tefrişten ÖNCE çizilir.
- **İsimlendirme (kullanıcı şimdilik istemedi):** `Column.name` alanı ve
  `ColumnLabelStyle` hazır, varsayılan **KAPALI**. `meta.column_label.enabled`
  ile **kod değişikliği olmadan** açılır (test edildi). Ayrıca
  `ColumnGrid.on_axis_report(...)` her kolonun hangi aks kesişimine oturduğunu
  (örn. `A1`) salt-okunur raporlar — kullanıcının tercih ettiği "aks
  kesişimiyle ifade etme" yaklaşımının veri karşılığı.
- **Kayıt:** `DEVELOPMENT_HISTORY.md` içindeki `HD-006`.
- **Uygulanmayan:** Katlar arası düşey hizalama ve kolon/duvar-tefriş çakışma
  kontrolü YOK; kesit küçültme otomatik değildir.
- **Fikir 1 — Aks kesişimine parametrik kolon:** `ColumnSectionCatalog` ile
  kare/dikdörtgen/dairesel kesitler; `ColumnGrid.from_axes(...)` bildirilen
  aks kesişimlerine kolon oturtur. Üst katlara çıkıldıkça kesit küçültme
  (örn. 60x60 → 50x50) **ancak açıkça bildirilirse** uygulanır, otomatik
  varsayılmaz.
- **Fikir 2 — Kolon aplikasyon/pozisyon listesi:** Kolonlara aks tabanlı ad
  (`S1`, `S2`...) verip her kolonun aks kesişimi, kesiti ve kotunu listeleyen
  bir tablo üretmek. `OpeningSchedule` deseninde salt-okunur veri; çizimi
  `legend/` üstlenir.
- **Açık kararlar:** Kolon verisi context'te hangi yolda yaşayacak? Aks dışı
  kolona izin var mı? Katlar arası düşey hizalama zorunlu mu?

### DEV-011 — `elevations/` — cephe modülü

- **Durum:** PLANNED
- **Mevcut durum:** `elevation_vertical_extent` ve `draw_elevation` hâlâ
  `generate_dxf.py` içinde. Cepheler plandan türetilmez; kullanıcının izin
  verdiği şekilde semantik seviye istifi + eşit aralıklı jenerik pencerelerdir.
  **Bilinen basitleştirme:** `below_ground: true` seviyeler için DXF'te ayrı
  kesikli linetype UYGULANMIYOR, sadece etiketle ayırt ediliyor.
- **Fikir 1 — Below-ground linetype'ı gerçekten uygulamak:** Bugünkü
  basitleştirmeyi kapatmak; zemin altı seviyeleri kesikli linetype ile çizmek
  ve davranışı gerçek renderer ile doğrulamak (sözleşme, doğrulanmamış bir
  standardı varsaymayı yasaklıyor).
- **Fikir 2 — Plandan cephe açıklığı türetme (opt-in):** Pencere sayısını elle
  vermek yerine, ilgili cepheye bakan duvarlardaki `openings[]`'i X konumuyla
  izdüşürmek. Varsayılan KAPALI olmalı ve türetilen açıklıklar kullanıcı
  onayına sunulmalı — aksi halde "cephe plandan türetilmez" ilkesi delinir.
- **Açık kararlar:** Cephe açıklıkları plan opening stilini mi tüketir, ayrı
  stil mi kullanır?

### DEV-012 — `legend/` — lejant ve cetveller

- **Durum:** PLANNED
- **Mevcut durum:** Yalnızca sözleşme var. İlgili veri üretimi KISMEN hazır:
  `openings::OpeningSchedule.from_openings(...)` deterministik satırlar
  üretiyor ama `generate_dxf.py` sonucu kullanmadan atıyor.
- **Fikir 1 — Kapı/pencere cetveli:** Zaten üretilen `OpeningSchedule`
  satırlarını bir tablo olarak çizmek. Veri hazır olduğu için en kısa yoldan
  görünür değer üreten iş budur.
- **Fikir 2 — Layer/sembol lejantı:** Projede gerçekten KULLANILAN layer ve
  sembollerin merkezi bir registry'den okunup açıklanması. Lejant opsiyonel
  kalır ve açık karar olmadan etkinleşmez.
- **Açık kararlar:** Cetvel kendi paftasında mı, yoksa mevcut paftanın boş
  alanında mı duracak? Kapak paftasının üstündeki boş alan bu iş için
  kullanılabilir mi?

### DEV-013 — `import/` — mevcut çizimden veri okuma

- **Durum:** PLANNED (ileri faz)
- **Mevcut durum:** Kod yok. İlgili bir parça zaten mevcut:
  `walls.scan::RoomPolygonScanner` salt-okunur öneri üretiyor ve context'e
  yazmıyor — import modülünün benimseyeceği desen budur.
- **Fikir 1 — `DxfWallScanner` salt-okunur rapor:** Mevcut bir DXF'ten duvar
  adaylarını çıkarıp confidence ve provenance (kaynak dosya + hash) ile
  raporlamak. Çıktı asla doğrudan context veya nihai DXF olmaz.
- **Fikir 2 — PDF/görüntü altlık ölçekleme:** Bir altlığı bilinen bir referans
  ölçüden ölçekleyip çizimin altına referans olarak yerleştirmek; geometri
  üretmez, yalnızca elle çizime altlık olur.
- **Açık kararlar:** Desteklenen kaynak formatları ve entity/layer kapsamı;
  onaylı import patch formatı.

### DEV-014 — `walls/` — duvar çizim standardı genişletmesi

- **Durum:** PLANNED
- **Mevcut durum:** Tamamlandı ve çalışıyor: çift rail, köşe/T miter, açıklık
  boşlukları, `WallCatalog`. Rail çizimi bugün **tek yöntem** (paralel LINE).
- **Fikir 1 — `RailDrawingStandard`:** Sözleşmede zaten öngörülen genişleme
  noktası. Hatch'li duvar (tuğla/betonarme ayrımı), cam duvar için farklı
  linetype, yalıtım katmanı gösterimi bu Protocol üzerinden eklenir; mevcut
  düz-rail davranışı varsayılan standart olarak kalır.
- **Fikir 2 — Kataloğu context'ten sürmek:** `WallCatalog` bugün kod
  seviyesinde. Yönetmelik/ofis standardı kalınlıklarının context.json'dan
  verilebilmesi, aynı sistemle farklı standartlara göre üretim yapmayı mümkün
  kılar (alt sınıf gerekmez, veri odaklı).
- **Açık kararlar:** Hatch deseni ölçekle nasıl ilişkilenecek (1:50 ve 1:100'de
  aynı desen okunaklı olmayabilir)?

### DEV-015 — `axis/` — aks sistemi genişletmesi

- **Durum:** PLANNED
- **Mevcut durum:** Tamamlandı: kesikli AKS layer'ı, sabit RGB, baloncuk
  teğetliği, cephelere `axis_source` ile izdüşüm, gerçek DXF ölçü zincirleri.
  Aks konumları context'ten geliyor ve tüm katlarda sabit.
- **Fikir 1 — Kolon rasterine göre otomatik aks:** Kök kurallar, kolon
  yerleşimi projeye girdiğinde aks sayısı/sıklığının kolon rasterine göre
  yeniden belirlenmesini öngörüyor. `DEV-010` ile birlikte ele alınmalı.
- **Fikir 2 — Ara aks ve kısmi aks:** `1'`, `2'` gibi ara akslar ve yalnızca
  belirli bir bölgede uzanan kısmi akslar. Bugün her aks tüm yapı boyunca
  uzanıyor.
- **Açık kararlar:** Ara aks etiketleme kuralı (`1'` mi `1A` mı)?

### DEV-016 — `openings/` — açıklık varyantları

- **Durum:** PLANNED
- **Mevcut durum:** `Opening`/`Door`/`Window` tipli, host-wall ve genişlik
  doğrulaması aktif, `OpeningSymbolStyle` Protocol'ü hazır. Ancak pratikte tek
  stil var (`DefaultPlanOpeningStyle`) ve schema'da varyant/swing alanı YOK —
  açıklıklar tek kanat, tek yönlü çiziliyor.
- **Fikir 1 — Varyant sembolleri:** Çift kanat, sürme, katlanır ve döner kapı
  sembolleri. Protocol zaten var, yeni stil eklemek mevcut mimariyle uyumlu.
- **Fikir 2 — Swing/menteşe yönü:** Kapının hangi tarafa ve hangi yöne
  açıldığını veriden almak. Bugün yön geometriden sabit türetiliyor; gerçek
  projede kaçış yönü ve mobilya çakışması için kritik (`DEV-009` ile ilişkili).
- **Açık kararlar:** `variant` ve `swing` schema alanları ne zaman eklenecek?
  Konum duvar başlangıcına göre mi, merkeze göre mi tanımlanacak?

### DEV-017 — `dimensions/` — ölçülendirme genişletmesi

- **Durum:** PLANNED
- **Mevcut durum:** `LinearDim`, `DimensionChain`, `ChainLayout` hazır ve
  `AxisGrid` bunları kullanarak gerçek DXF dimension üretiyor. Ölçü metni tam
  sayı cm. Bugün ölçü üreten TEK tüketici aks modülü.
- **Fikir 1 — Oda içi/net ölçü zinciri:** Duvar yüzünden duvar yüzüne net oda
  ölçüleri ve kapı/pencere konum ölçüleri. Uygulama projesinde (1:50) asıl
  beklenen ölçülendirme budur; altyapı hazır, eksik olan tüketici.
- **Fikir 2 — Zincir çakışma çözümü:** Birden fazla zincir aynı kenarda
  olduğunda otomatik kademelendirme (offset artırma). Bugün `ChainLayout`
  yalnızca bounds kontrolü yapıyor; çakışan iki zincir üst üste binebilir.
- **Açık kararlar:** Ölçü zinciri context'ten mi bildirilecek, yoksa duvar
  geometrisinden mi türetilecek? Türetilirse hangi kenarlar ölçülendirilecek?


### DEV-018 — DXF `BLOCK` entity kullanımı (modüller arası)

- **Durum:** PLANNED (kullanıcı 2026-09-23'te plan olarak eklenmesini istedi)
- **Kapsam notu:** Bu madde tek bir modüle ait değildir; `rooms`, `furniture`,
  `openings`, `axis` ve `legend` modüllerinin hepsini ilgilendiren bir DXF
  yetenek kararıdır.
- **Mevcut durum:** Çizimde **hiç `BLOCK` kullanılmıyor** — `output/plan.dxf`
  içindeki `INSERT` sayısı **0**, 2226 entity'nin tamamı düz geometri
  (`LINE`, `LWPOLYLINE`, `TEXT`, `ARC`, `CIRCLE`). Tekrarlayan öğeler her
  yerde yeniden çiziliyor: 125 mahal etiketi = 375 ayrı `TEXT`, her kapı =
  1 `ARC` + 3 `LINE`, her aks baloncuğu = 1 `CIRCLE` + 1 `TEXT`.
- **Neden değerli:** AutoCAD'de bir blok **tek seçilebilir nesnedir**; bir
  tanım, çok `INSERT`. Tekrarlayan öğenin biçimi tek yerden değişir, dosya
  küçülür ve kullanıcı etiketi/mobilyayı yanlışlıkla parçalayamaz.
- **Fikir 1 — Mahal etiketi bloğu + `ATTRIB`:** Mahal etiketini
  `MAHAL_ADI` / `MAHAL_NO` / `ALAN` öznitelikli bir blok tanımı yapmak ve her
  mahale bir `INSERT` koymak. Etiket AutoCAD'de tek nesne olur, öznitelikler
  CAD içinde düzenlenebilir ve tüm etiketlerin biçimi tek tanımdan güncellenir.
  (Kullanıcının "mahal ismi blok olarak işlensin" ifadesi rev-9'da **büyük
  harf** olarak yorumlandı; `BLOCK` entity kastedildiyse asıl karşılığı budur.)
- **Fikir 2 — Sembol/tefriş blok kütüphanesi:** Tefriş elemanları, kapı/pencere
  sembolleri ve aks baloncuklarını yeniden kullanılabilir blok tanımlarına
  taşımak; tanımların sahibi yeni bir `scripts/blocks/` modülü olur, diğer
  modüller yalnızca `INSERT` üretir. `DEV-009` (tefriş) ile doğrudan bağlantılı
  — tefriş uygulanmadan önce bu karar verilirse kod iki kez yazılmaz.
- **ÖNCE ÇÖZÜLMESİ GEREKEN (ölçülerek doğrulandı):**
  - **`golden_report.py` blokları GÖREMİYOR.** `entity_bbox`, `INSERT` için
    yalnızca **ekleme noktasını** döndürüyor; blok içeriği bounding box'a
    girmiyor (test edildi: 2000x1000 içerikli bir blok, (5000,5000) noktasına
    eklendiğinde bbox `[5000, 5000, 5000, 5000]` çıkıyor). Bloklara geçilirse
    golden raporunun modelspace bbox'ı **sessizce küçülür** ve regresyon
    yakalama gücü daha da azalır. `DEV-006` ile birlikte ele alınmalıdır.
  - **Pafta taşma koruması çalışmaya devam eder.** `verify_within_frame`,
    `ezdxf.bbox.extents(...)` kullanıyor ve bu fonksiyon `INSERT`i çözüp
    gerçek sınırları veriyor (aynı testte `(5000,5000)-(7000,6000)` döndü).
    Yani bu tarafta bir risk yok.
- **Açık kararlar:** Mevcut düz geometri bloklara **taşınacak mı**, yoksa
  bloklar yalnızca yeni öğelerde mi kullanılacak? Blok adlandırma kuralı ne
  olacak? Öznitelikler `ATTRIB` mi olacak yoksa düz `TEXT` mi (öznitelik
  kullanılırsa `validate.py`nin ve golden raporunun bunları okuması gerekir)?
  Ölçekli blokta metin yüksekliği nasıl korunacak?

## BACKLOG

Her modülün kendi plan maddesi artık yukarıdaki **PLANNED** bölümündedir
(`DEV-007` … `DEV-017`); bu bölüm yalnızca sıra önerisini tutar.

Kullanıcının verdiği öncelik (2026-09-23): `DEV-008` tamamlandı, `DEV-007`
kullanıcı verisi bekliyor, `DEV-006` hazır. `DEV-009` (tefriş) ve `DEV-018`
(DXF `BLOCK` kullanımı) kullanıcı talebiyle açılmıştır; `DEV-018` modüller
arası bir karardır ve `DEV-009`dan ÖNCE ele alınması işi tekrar etmeyi önler.
Kalan modüller için sıra önerisi:

`columns/` → `elevations/` → `legend/` → `import/`

Her görev uygulamaya alınmadan önce ilgili `scripts/<module>/CLAUDE.md` dosyası
ve `docs/phases/NEXT-MODULES-ROADMAP.md` okunur. Buradaki kayıtlar kod
uygulama izni değildir; yalnızca planlama ve devir bağlamıdır.

## Görev tamamlama kuralı

Bir görev için agent şunları yapmadan `COMPLETED` yazamaz:

1. Kabul ölçütlerini karşılayan kod/doküman değişikliğini tamamlamak.
2. Odaklı validation çalıştırmak.
3. Gerekli ise `validate.py` ve `generate_dxf.py` çalıştırmak.
4. Golden output etkisini kaydetmek.
5. Ayrı reviewer/validator çalışmasından kabul raporu almak.
6. `DEVELOPMENT_HISTORY.md`ye kayıt eklemek.
7. `DEVELOPER_NOTES.md`yi bir sonraki direktifle güncellemek.
8. `python scripts/development_control.py release ...` ile görev kilidini bırakmak.
