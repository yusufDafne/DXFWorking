# daire-plani-ai — Proje Kuralları

Bu dosya, bu proje dizininde çalışırken her oturumda otomatik olarak okunacak
kalıcı kurallardır. Aşağıdaki kurallar istisnasız uygulanır.

## Kapsam
- Bu proje dışında hiçbir dizine okuma/yazma yapılmaz. Tüm işlemler
  `daire-plani-ai/` içinde kalır.

## DXF üretim disiplini
- `output/plan.dxf` **asla elle/serbestçe düzenlenmez veya elle yazılmaz**.
  Tek üretim yolu `scripts/generate_dxf.py` script'ini çalıştırmaktır.
- `context.json` içinde veya kullanıcının verdiği bilgide bulunmayan hiçbir
  ölçü, koordinat veya değer **uydurulmaz**. Eksik bilgi varsa varsayım
  yapmak yerine kullanıcıya sorulur.

## Çıktı dosyası kilitliyse (ör. AutoCAD'de açık)
- `scripts/generate_dxf.py` ve `scripts/preview.py`, `output/plan.dxf` /
  `output/preview.png` dosyasına yazarken `PermissionError` alırsa (dosya
  başka bir programda açık olduğu için) **akışı durdurmaz**: bunun yerine
  `plan_1.dxf`, `plan_2.dxf` gibi `<isim>_N<uzantı>` şeklinde bir yedek
  dosyaya kaydeder ve bunu kullanıcıya açıkça bildirir.
- Bir sonraki çalıştırmada normal isim (`plan.dxf`/`preview.png`) tekrar
  yazılabilir olduğunda, script önce oraya kaydeder, ardından geçmişte
  oluşmuş `_N` ekli yedek dosyaları otomatik siler — dosya kalabalığı
  oluşmaz.

## Talep işleme akışı (her talep için sırasıyla)
1. Talep, geldiği ham haliyle `requests.jsonl` dosyasına JSON Lines formatında
   satır olarak eklenir: `{"rev": n, "ts": "...", "request": "..."}`.
2. Talep, `context.json` üzerinde yapılandırılmış bir değişiklik (patch)
   olarak uygulanır.
3. Değişiklik uygulandıktan sonra `scripts/validate.py` ile:
   - JSON Schema (`schema/design.schema.json`) doğrulaması,
   - geometrik sağlık kontrolleri (kapalı poligon mu, çakışan oda var mı,
     kapı/pencere genişliği ait olduğu duvardan büyük mü, alanlar toplamı
     mantıklı mı)
   yapılır. **Doğrulama geçmeden DXF üretilmez.**
4. Doğrulama başarılıysa `scripts/generate_dxf.py` çalıştırılıp
   `output/plan.dxf` sıfırdan yeniden üretilir.
5. İsteğe bağlı olarak `scripts/preview.py` ile `output/preview.png` üretilip
   kullanıcıya görsel önizleme sunulabilir.

## Duvar çizim standardı (Türkiye standardı)
- Duvarlar AutoCAD'de **"tek merkez çizgisi + width (kalınlık) özniteliği"**
  yöntemiyle çizilmez — bu yöntem sektörde/Türkiye standartlarında
  kullanılmaz.
- Bunun yerine her duvar, kalınlığına karşılık gelen **iki paralel kenar
  çizgisi (rail)** ile temsil edilir; bu kenar çizgileri **LINE veya PLINE**
  (width=0, saf geometri) olarak çizilir.
- Duvar birleşim noktalarında (köşe veya T-kesişimi) bu kenar çizgileri,
  birleşen duvarların ilgili kenar çizgileriyle kesiştirilip (gönye/miter
  birleşim) o kesişim noktasına kadar uzatılır/kısaltılır. Sonuç: her dış
  köşe **dıştan tek bir noktada** temiz şekilde birleşir; çakışma veya boşluk
  oluşmaz.
- Uygulama: `scripts/generate_dxf.py` içinde bu mantık `Wall` ve
  `WallNetwork` sınıflarıyla kapsüllenir. Tüm duvar çizimleri bu sınıflardan
  türetilir/kullanılır — duvar çizen yeni kod tekilleştirilmiş bu sınıflar
  üzerinden yazılır, ayrı ayrı ad-hoc çizim mantığı eklenmez.

## Çok katli bina yapisi (rev-2'den itibaren)
- context.json semasi rev-2'de degisti: artik duz (tek daire) yapi degil,
  `meta.floor_width` / `meta.floor_depth` / `meta.sheet_gap` + `floors[]`
  (her biri kendi rooms/walls/openings/labels/counters/markings listesine
  sahip bir "pafta") + `elevations[]` (basitlestirilmis cephe seviye istifi)
  iceriyor. `schema/design.schema.json` bu yapiyi tanimlar.
- **Pafta duzeni:** `floors[]` sirayla, sonra `elevations[]` sirayla soldan
  saga dizilir; her paftanin X-ofseti kendi genisligi + `sheet_gap` kadar
  ilerler (bkz. `generate_dxf.py::generate`). Her paftanin sag-alt kosesine
  `CERCEVE` katmaninda bir cerceve ve METIN katmaninda kat adi + "PAFTA n/N"
  yazilir (`draw_sheet_frame`).
- **Ortak bina ayak izi:** Tum kat paftalari AYNI `floor_width x floor_depth`
  dikdortgenini kullanir (cikma yok). Derinlik iki banda ayrilir:
  - `y: 0 - 13000` "birim bandi": katin asil islevi (otopark / dukkan+lobi /
    3 daire / cati terasi) burada.
  - `y: 13000 - 17500` "sirkulasyon bandi": HER KATTA AYNI KONUMDA asansor
    (x:0-1000) + merdiven (x:1000-5000), bunlarin guney yuzu `y=14500`'de
    koridora acilir; L-seklinde koridor/rampa odasi tum genisligi kaplar.
    Bu konum tum katlarda sabit tutulmalidir (asansor/merdiven duseyde
    hizali olsun diye).
  - `y=13000` duvari ("band_south"): zemin/normal katlarda VAR (giris
    kapilariyla), bodrum/catida YOK (acik gecis - rampa/teras).
- **Mutfak tezgahi:** `floor.counters[]` icinde basit dikdortgen poligon
  olarak tanimlanir, `MOBILYA` katmaninda kapali polyline ciizilir.
- **Cephe gorunusleri (elevations):** Gercek plan geometrisinden TURETILMEZ;
  kullanicinin acikca izin verdigi sekilde (bkz. rev-2 talebi) semantik/basit
  bir seviye istifi + esit araliklarla yerlestirilmis jenerik pencere
  dikdortgenleri olarak cizilir (`draw_elevation`). `below_ground: true`
  seviyeler zemin cizgisinin (`y=0`) altinda cizilir; DXF'te ayri bir
  kesikli linetype UYGULANMAZ (sadece etiketle ayirt edilir) - bu bilinen
  bir basitlestirmedir.
- **Bilinen basitlestirmeler (rev-2):** Banyo/WC gibi servis odalari,
  "birim bandi"nin tam derinligini paylastigi icin gercekte olmasi
  gerekenden biraz dar-uzun orantili olabilir; otopark cizgileri
  (`markings[]`, `OTOPARK` katmani) salt gorsel/semantik olmayan
  isaretlemedir, validate.py bunlari kontrol etmez; asansor/merdiven kapi
  sembolu cizilmez (sadece etiketli kapali oda olarak gosterilir).

## Çizim standartları (ofis standardı, rev-3'ten itibaren)
Bunlar bir yönetmelik degil, kullanicinin kisisel/ofis standardidir; ileride
daha detayli yonetmelik-destekli standartlar gelebilir, o zaman bu bolum
guncellenir.

- **Ölçek:** Aksi açıkça belirtilmedikçe varsayılan ölçek **1/100**'dür
  (`meta.scale`). Farklı bir ölçek istenirse context.json'da açıkça
  belirtilir.
- **Ölçülendirme birimi:** Çizim üzerine bir ölçü (dimension) metni/etiketi
  eklenirken (örn. `labels[]` içindeki `type: "dimension"` girdileri veya
  ileride kurulacak `DimensionChain` sınıfı) metin **tam sayı cm** olarak
  yazılır — örn. gerçek ölçü 3750mm ise etiket metni `"375"` olur (mm veya
  ondalıklı m değil). Bu SADECE ölçü metninin gösterim formatıdır;
  context.json'daki asıl koordinat/ölçü birimi (`meta.units`) yine mm
  kalır, değişmez.
- **Pafta modülü (`scripts/pafta/`, rev-4'te ilk modül olarak kuruldu):**
  Pafta çerçevesi, başlık kutusu, tasma kontrolü ve kağıt boyutu planlaması
  ARTIK `scripts/generate_dxf.py`'de DEĞİL, kendi izole modülünde
  (`scripts/pafta/__init__.py` + kendi **`scripts/pafta/CLAUDE.md`**
  dosyası) yaşar. Bu, projenin "her çizim konusu kendi modülü + kendi
  izole CLAUDE.md'si olsun, böylece ileride bir ajan sadece o modülü açıp
  derinlemesine çalışabilsin" mottosunun İLK uygulamasıdır — sonraki
  modüller (aks, duvar/oda, kolon, ...) de aynı desenle ayrılacak (bkz.
  `scripts/CLAUDE.md`).
- **Pafta başlık kutusu:** Her pafta, sağ-alt köşesinde standart bir
  kutucuk içinde **iki satır** gösterilir: üstte "ÖLÇEK x", altta pafta adı.
  "PAFTA n/N" gösterimi KALDIRILDI. Kutunun metin boyutu, projedeki TÜM
  pafta adlarının (+ ölçek metninin) kutuya **gerçek font metrikleriyle**
  (kaba karakter-sayısı tahmini DEĞİL) sığacağı en küçük ortak boyut olacak
  şekilde bir kere hesaplanır ve tüm paftalarda AYNEN uygulanır. Uygulaması
  `scripts/pafta::Sheet` sınıfıdır — yeni pafta türleri de bu sınıf
  üzerinden çizilir, ayrı ad-hoc başlık kodu yazılmaz.
- **Pafta çerçevesi:** Duvar rail mantığına benzer şekilde **çift/ofsetli
  çizgi** (dış hat + iç hat) olarak çizilir (`Sheet._draw_double_frame`),
  tek çizgili basit dikdörtgen değildir.
- **Ortak yükseklik, dinamik genişlik, hizalı paftalar (rev-4'te
  tamamlandı):** Projedeki TÜM paftalar (kat planları + görünüşler) **aynı
  MUTLAK dış-çerçeve Y-ARALIĞINI** (`frame_y0`..`frame_y1`) paylaşır — bu,
  tüm paftaların ham `(y_bottom, y_top)` aralıklarının EN GENİŞİNİ kapsayacak
  şekilde bir kere hesaplanır. **Kritik nokta:** bu, her paftayı KENDİ
  içeriğinin merkezine göre simetrik olarak şişirmek DEĞİLDİR — öyle
  yapılırsa farklı "merkezli" paftalar (örn. bir kat planının yerel sıfırı
  ile bir görünüşün zemin kotu) birbirine göre DÜŞEY KAYAR (bu gerçekten
  yaşandı ve düzeltildi). Bunun yerine TEK bir mutlak aralık her paftaya
  aynen uygulanır, böylece hem yükseklik birebir aynı olur HEM DE paftalar
  arasında dikey kayma sıfırdır. **Genişlik** her paftanın kendi içeriğine
  göre serbestçe belirlenir, bir sınır yoktur. Uygulaması `Sheet.__init__`'e
  verilen `content_ranges` (her paftanın kendi `(y_bottom, y_top)` çifti)
  listesidir (`frame_y0`/`frame_y1`/`outer_height`).
- **Paftalar dış çizgilerinden bitişiktir (rev-4'te tamamlandı):** Paftalar
  arasında EKSTRA BOŞLUK YOKTUR — bir paftanın dış çerçevesinin sağ kenarı,
  bir sonrakinin dış çerçevesinin sol kenarına tam oturur. `meta.sheet_gap`
  alanı bu yüzden şemadan KALDIRILDI; ardışık paftaların X-ofseti
  `generate_dxf.py::generate` içinde `width + 2*(CONTENT_PADDING+FRAME_GAP)`
  kadar ilerletilir.
- **Pafta padding'i (rev-4'te tamamlandı):** Bir paftaya yerleştirilecek
  çizim (aks baloncukları, cephe kat etiketleri vb.), paftanın **İÇ
  çizgisinden itibaren** ölçülen bir boşluk (`CONTENT_PADDING`) kadar içeri
  çekilir — hiçbir öğe paftaya "sıfır hizalı"/bitişik yerleştirilmez.
  Başlık kutusu da bu iç çizgiye göre konumlanır: kutunun sağ-alt köşesi
  **iç çizgide BİTER** (dış çizgiye taşmaz, iç çizginin üzerinde de
  durmaz).
- **Pafta taşma koruması (istisnasız kural):** Bir projenin çizimi HİÇBİR
  ZAMAN kendi paftasının çerçevesini aşamaz. Bu, `scripts/pafta::Sheet.draw`'a
  o paftaya ait tüm DXF varlıkları (`content_entities`) verilerek,
  `verify_within_frame` ile gerçek bir bounding-box kontrolüyle
  uygulanır — aşan bir içerik varsa `PaftaOverflowError` fırlatılır ve DXF
  üretimi BAŞARISIZ olur (sessizce hatalı bir dosya üretilmez). Oda
  etiketleri gibi metinler de kendi oda genişliğine göre otomatik küçültülür
  (`fit_text_height`, gerçek font ölçümü) — bu kontrol rev-4'te tam da bu
  şekilde bir taşma hatasını (uzun oda adı) gerçekten yakalayıp
  düzeltilmesini sağladı.
- **Kağıt boyutu planlaması:** `scripts/pafta::PaperSizePlanner`, projenin
  SABİT `meta.scale`'i için en yüksek paftanın standart kağıt
  yüksekliklerinden (45/60/90cm) hangisine sığdığını hesaplar ve
  `generate_dxf.py` çalıştığında raporlar (örn. "45cm kağıda sığıyor").
  Ölçeği kendiliğinden DEĞİŞTİRMEZ; "1/50 favori, sığmazsa 1/100'e düş"
  gibi bir ölçek henüz seçilmemiş yeni bir proje için düşünülen kaskad
  mantığı henüz uygulanmadı (kullanıcı bu konuya ileride daha detaylı
  dönecek). Tüm paftaların FİZİKSEL boyutunun da birebir aynı olacağı bir
  "uniform sheet template" henüz YOK — bkz. `scripts/pafta/CLAUDE.md`
  "Bilinen sınırlamalar".
- **Aks (grid) sistemi:** Bina, `context.json`'ın üst seviye `grid` alanında
  tanımlanan bir aks ızgarasına oturur:
  - `grid.vertical_axes`: düşey aks çizgileri (sabit X, Y boyunca uzanır),
    **nümerik** etiketli (1, 2, 3, ...).
  - `grid.horizontal_axes`: yatay aks çizgileri (sabit Y, X boyunca
    uzanır), **alfabetik** etiketli (A, B, C, ...).
  - Aks çizgileri **kesikli** (`AKS` katmanı, `DASHED` linetype), **sabit
    RGB(67,77,88)** renginde (ACI index DEĞİL, context.json'da da
    tanımlanmaz — `generate_dxf.py::ensure_axis_layer` tarafından kod
    tarafında zorunlu kılınır), uçlarında etiketi taşıyan bir daire ("O"
    baloncuğu) ile gösterilir. Uygulaması `AxisGrid` sınıfıdır.
  - **Çizim sırası:** Aks izgarası HER paftada diğer her şeyden ÖNCE
    (dolayısıyla "en altta") çizilir.
  - **Baloncuk teğetliği:** Aks çizgisi, baloncuğun merkezine kadar değil,
    baloncuğun kenarına (yarıçapı kadar önce) kadar çizilir — çizgi
    baloncuğun içine girmez.
  - **Uzama mesafesi:** Aks, yapının kenarından itibaren **1200 birim**
    (mm) ileriye uzanır (`AXIS_EXTENSION`) ve bu uzama + baloncuk yarıçapı,
    pafta çerçevesini (`PAFTA_MARGIN`) KESİNLİKLE aşmayacak şekilde
    `PAFTA_MARGIN` bu mesafeye göre büyük tutulur. Komşu paftaların
    baloncukları/çerçeveleri çakışmasın diye `meta.sheet_gap` da buna göre
    yeterince büyük seçilmelidir.
  - **Aks arası mesafeler:** Ardışık akslar arasındaki mesafe, gerçek bir
    DXF `LINEAR DIMENSION` (ölçü) varlığıyla, **küçük punto** (`AKS`
    katmanı, ~120mm) ve **tam sayı cm** metniyle gösterilir
    (`AxisGrid._dim_chain_x/_dim_chain_y`). Bu, aks sınıfına ait bir
    fonksiyondur, ayrı bir "ölçülendirme" akışı değildir.
  - Aks konumları **tüm kat paftalarında aynıdır** (bina boyunca sabit) —
    farklı kat tiplerinin iç bölmeleri farklı olsa da (daire/dükkan/otopark)
    dış cephe ve çekirdek (asansör/merdiven) konumu her katta ortak
    olduğundan aks ızgarası bunlara oturtulur.
  - **Aks sıklığı optimum belirlenir**, her duvara aks konmaz — sadece ana
    strüktürel hatlar (dış cephe, çekirdek sınırları, ileride kolon
    hizaları) aks alır. Kolon yerleşimi projeye girdiğinde aks sayısı ve
    sıklığı kolon rastırına göre yeniden/dinamik belirlenir.
  - **Görünüşlerde izdüşüm:** Düşey (nümerik) akslar plandaki X konumunu
    korur ve **ön/arka cephede düşey çizgi** olarak aynı etiketle
    izdüşürülür. Yatay (alfabetik) akslar plandaki Y konumunu (derinlik)
    temsil eder ve **sağ/sol cephede düşey çizgi** olarak aynı etiketle
    izdüşürülür (bir cephe kendi ailesini gösterir, diğerini göstermez).
    Bu, `elevation.axis_source` alanıyla (`"vertical"` veya `"horizontal"`)
    kontrol edilir.
- **Genişletilebilir altyapı:** Bu ve gelecekteki çizim yetenekleri
  (kolonlar, ölçü zincirleri, kapı/pencere cetveli vb.) `Wall`/`WallNetwork`
  örneğindeki gibi parametrik, tek-sorumluluklu Python sınıflarıyla
  kurulur. Bu mimarinin planı ve durumu **`scripts/CLAUDE.md`** dosyasında
  tutulur — yeni bir sınıf fikri veya kararı oraya işlenir, buraya değil.

## Git (güncellendi)
1. Git komutları (`add`, `commit`, `log`, `diff`) SADECE bu proje dizini
   içinde çalıştırılır. Her git komutundan önce `git rev-parse
   --show-toplevel` ile bulunulan repo kökünün bu projenin dizini olduğu
   doğrulanır; eşleşmiyorsa işlem durdurulur ve kullanıcıya bildirilir. Bu
   dizin dışında hiçbir repoya dokunulmaz. Remote (`origin`) eklenmez veya
   `git push` yapılmaz — kullanıcı açıkça istemedikçe proje tamamen lokal
   kalır.
2. Bir revizyon işlendikten (context.json güncellenip validate + generate_dxf
   çalıştırıldıktan) SONRA, `git add`/`commit` yapmadan ÖNCE kullanıcıya
   şunlar gösterilip onay istenir:
   - Bu revizyonda context.json'da tam olarak neyin değiştiği (kısa özet)
   - Net bir soru: "Bu değişiklikleri commit'lemem için onaylıyor musun?"
   Kullanıcı açıkça onay vermeden (örn. "onaylıyorum", "evet", "commit'le")
   `git add` veya `git commit` çalıştırılmaz. Onay gelmeden başka bir talebe
   geçilmez.
3. Onay geldiğinde ilgili dosyalar (`context.json`, `output/plan.dxf`,
   `output/preview.png`, `requests.jsonl`) `git add` ile stage edilip
   commit'lenir. **Git config (local/global) hiçbir zaman değiştirilmez** —
   kullanıcı izin verse bile bu kural geçerlidir. Bunun yerine, `git log`'da
   yazar adının "Claude" görünmesi için her `git commit` komutu şu ortam
   değişkenleriyle çalıştırılır (sadece o komuta özel, kalıcı config
   değişikliği yapılmaz):
   `GIT_AUTHOR_NAME="Claude"`, `GIT_AUTHOR_EMAIL="noreply@anthropic.com"`,
   `GIT_COMMITTER_NAME="Claude"`, `GIT_COMMITTER_EMAIL="noreply@anthropic.com"`.
   Commit mesajı formatı sabittir (gelecekte `git log` ile geçmiş taranıp
   belirli bir revizyona hızlıca ulaşılabilsin diye):

   ```
   rev-<N> [<ISO 8601 tarih-saat>]: <tek satır kısa özet>

   Değişiklik: <hangi oda/duvar/kapı/pencere neyin değişti, somut şekilde>
   Kullanıcı talebi: <requests.jsonl'daki ilgili talebin kısa özeti>
   Etkilenen alanlar (context.json): <değişen key/path listesi, örn. rooms[2].area, walls[5]>
   ```

   `<N>` değeri `requests.jsonl`'daki revizyon sayacıyla birebir aynı olmalı.
4. Commit tamamlandığında kullanıcıya sadece commit hash'inin kısa hali ve
   tek satır özeti bildirilir, uzun log çıktısı gösterilmez.
5. **Git kimliği:** Bu proje için push işlemi (yalnızca kullanıcı açıkça
   isterse yapılır) `yusufakcakaya-sketch` hesabıyla yapılmalıdır — SSH host
   alias'ı `github-personal`, anahtar `~/.ssh/id_ed25519`. Bu makinedeki
   global git config şu an farklı bir kimlik kullanıyor (`YusufDafne` /
   `yusufakcakaya@dafneconstruction.com`, `~/.ssh/YusufDafne` anahtarı) —
   bu proje icin varsayilan olarak kullanilmamali. Global git config
   değiştirilmez; bir remote eklenmesi gerektiğinde kullanıcıyla birlikte
   `github-personal` host alias'ı üzerinden yapılandırılır.

## Belirsizlik durumunda
- Eksik/belirsiz bilgi varsa varsayım yapıp üretime devam etmek yerine
  kullanıcıya doğrudan soru sorulur.
