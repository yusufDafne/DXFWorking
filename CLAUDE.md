# daire-plani-ai — Proje Kuralları

Bu dosya, bu proje dizininde çalışırken her oturumda otomatik olarak okunacak
kalıcı kurallardır. Aşağıdaki kurallar istisnasız uygulanır.

## Kapsam

- Bu proje dışında hiçbir dizine okuma/yazma yapılmaz. Tüm işlemler
  `daire-plani-ai/` içinde kalır.

## Dokümantasyon ve veri sahipliği

- Bu kök dosya proje yönetişiminin otoritesidir: talep kaydı, context-only veri,
  doğrulama kapısı, çıktı üretimi, belirsizlikte durma, dosya kilidi ve git onayı.
- `scripts/CLAUDE.md` çizim mimarisi, modül sırası, public API ve modüller arası
  sözleşmelerin otoritesidir. Her `scripts/<modül>/CLAUDE.md` kendi modülünün
  sorumluluk, invariant, test ve bilinen sınırlamalarının otoritesidir.
- **Agentic dokümanlar birbirine bağlı tek bir bağlam sistemidir.** Kök
  `CLAUDE.md`, `scripts/CLAUDE.md`, her modülün `CLAUDE.md`'si ve
  `docs/development/*` kasıtlı olarak birbirine referans verir; amaç, bir
  agent'ın çalışmaya başlarken bağlamı eksiksiz kurabilmesi ve hiçbir yerde
  bayat satır kalmamasıdır. **Her çalışmanın sonunda bu dokümanlar
  güncellenir** — bu bir nezaket değil, sistemin çalışma koşuludur. Kontrolü
  `python scripts/doc_check.py` yapar; görev `COMPLETED` yazılmadan önce temiz
  dönmelidir.
- **Modüller bağımsız çalışır, kritik noktalarda çapraz kontrol edilir.** Her
  modül kendi klasöründe, kendi sözleşmesiyle ve diğer modülleri bilmeden
  geliştirilebilir olmalıdır — bir agent tek bir modüle odaklanabilsin diye.
  Ancak bağımsızlık **izolasyon değildir**: modüller arasında gerçek
  bağımlılıklar vardır (tefriş duvara/kapı açılımına, kolon aksa, mahal
  etiketi pafta sınırına). Bu kritik noktalarda **çapraz kontrol zorunludur**
  ve bugün `scripts/golden_report.py --rules` ile `--golden-set` üzerinden
  yürür. Yeni bir modül eklendiğinde "bu modül hangi modülle çakışabilir?"
  sorusu açıkça yanıtlanır ve gerekiyorsa bir kural eklenir.
  **Çakışma denetimi rev-12'de UYGULANDI:** tekil ("kendi verim geçerli mi")
  doğrulama ilgili modülde, çift ("iki farklı eleman aynı yeri mi işgal
  ediyor") denetim `scripts/collision/` motorunda yaşar. Motor hiçbir çizim
  modülünü import etmez; her modül kendi ayak izini
  `collision.py::footprints(floor, context)` ile verir, böylece bağımsızlık
  korunurken kural tek yerde toplanır. Kapı `validate.py`dedir ve **üretimi
  durdurur**. Bu gereklilik artık mekaniktir: `doc_check.py`, geometri üreten
  her modülün ya bir `collision.py`si olmasını ya da
  `collision/scene.py::COLLISION_EXEMPT` içinde **gerekçesiyle**
  listelenmesini arar. Ayrıntı: `scripts/collision/CLAUDE.md`.
- **Her proje diğerlerinden BAĞIMSIZDIR ve proje verisi proje dizininde
  kalır.** Tefriş yerleşimi, oda/duvar geometrisi, mahal numaraları gibi
  **proje bazlı adresler yalnızca o projenin `context.json`'ında** bulunur.
  Modül altında yalnızca **kütüphane** yaşar (tefriş kataloğu, duvar kataloğu,
  kolon kesitleri). Bu ayrım korunmazsa bir projenin verisi başka bir projeye
  sızar. `golden/` altındaki referanslar proje DEĞİLDİR; sistemi sınamak için
  uydurulmuş mini context'lerdir.
- **`docs/` YALNIZCA agentic yönetişim dokümanı tutar** (görev kuyruğu, geçmiş,
  fikirler, geliştirici notları, rol izinleri, provenance şablonu). Çalışan
  bileşenler oraya konmaz:
  - Bir modülün kodu, sözleşmesi ve **kendi golden referansı** `scripts/<modül>/`
    altında yaşar.
  - Proje geneli (entegrasyon) **golden referans projeleri** `golden/`
    altındadır — `schema/` ve `output/` gibi proje kökü seviyesinde bir VERİ
    dizinidir, doküman değildir. Bunlar tam bir context gerektirdiği için
    (schema `meta`, `layers`, `grid`, `floors`, `elevations` zorunlu kılar)
    tek bir modüle bağlanamazlar. Her referans dizini `context.json` (girdi) +
    `expected.json` (beklenen ölçüm raporu) tutar.
  `scripts/golden_report.py --golden-set` her iki kökü de tarar.

  **İsim notu (rev-11):** Bunlara rev-11'e kadar "fixture" deniyordu. Mimari
  bir projede *fixture* sözcüğü **sabit tesisat elemanı** (lavabo, klozet,
  vitrifiye) anlamına geldiği için yanıltıcıydı — bir kullanıcı haklı olarak
  bunu tefriş listesi sandı. Proje zaten "golden output" terimini kullandığı
  için ad `golden` oldu.
- Sistem kaynakları ile proje verileri ayrıdır. Her proje kendi proje dizininde
  context, talepler, revizyon kayıtları, doğrulama raporları, preview ve nihai
  DXF çıktısını tutar; bir projenin revizyonu başka projeye yazılmaz.
- DXF dosyaları nihai çıktıdır ve elle düzenlenmez. Yalnızca validate edilmiş
  pipeline çıktısı nihai kabul edilir; seçilmiş nihai DXF'ler sistem için
  golden-output referanslarıdır.
- Sistem geliştirme talimatları ile sistemi kullanarak proje üreten agent
  talimatları ayrı tutulur. Üretim agent'ı sistem koduna veya başka proje
  dizinine yazamaz; reviewer/validator agent teknik sonucu bağımsız denetler.

## Deterministik üretim ilkesi

- Dil modeli yalnızca yapılandırılmış talep, patch veya izinli seçenek önerir;
  ölçü, koordinat, geometri, standart veya eksik veri uyduramaz.
- Python sınıfları, kataloglar, Protocol'ler, schema ve `validate.py` nihai
  üretim kararını verir. Eksik veya çelişkili bilgi varsa süreç durur ve karar
  istenir; varsayım ile DXF üretilmez.
- Bir proje revizyonunun yaşam döngüsü şöyledir: talep → yapılandırılmış
  context patch → validate → DXF üretimi → preview/inceleme → kabul → final.
  Revizyon ve çıktı ilişkisi append-only/provenance kayıtlarıyla korunur.

## Mimari referans

Uzun vadeli sistem vizyonu, generic component contract, agent çalışma yöntemi
ve modül yol haritası için `scripts/CLAUDE.md`; sistem agent talimatları,
geliştirme görevleri, tamamlanmış geçmiş, fikirler ve geliştirici notları için
`docs/` dizini kullanılır.

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
   - **sürüm kapısı** (`meta.schema_version` ↔ `scripts/version.py`;
     MAJOR farkta üretim DURUR — bkz. "Sürüm uyumu"),
   - geometrik sağlık kontrolleri (kapalı poligon mu, çakışan oda var mı,
     kapı/pencere genişliği ait olduğu duvardan büyük mü, alanlar toplamı
     mantıklı mı),
   - **çakışma denetimi** (`scripts/collision/`; tefriş odanın dışında mı,
     duvara/kolona/kapı açılım yayına giriyor mu — bkz. "Çakışma denetimi")
     yapılır. **Doğrulama geçmeden DXF üretilmez.**
4. Doğrulama başarılıysa `scripts/generate_dxf.py` çalıştırılıp
   `output/plan.dxf` sıfırdan yeniden üretilir.
5. İsteğe bağlı olarak `scripts/preview.py` ile `output/preview.png` üretilip
   kullanıcıya görsel önizleme sunulabilir.
6. **Golden kontrol (rev-10'dan itibaren):** `scripts/golden_report.py`
   üç katmanlıdır ve üretimden sonra çalıştırılır:
   - `--compare <rapor>` — entity/layer/bbox ölçüm karşılaştırması,
   - `--rules context.json` — **semantik kurallar** (mahal etiketi 3 satır ve
     oda içinde mi, kapı başına yay var mı, aks çizgisi baloncuğa giriyor mu,
     tanımsız blok referansı var mı, bildirilmemiş layer kullanılmış mı),
   - `--golden-set` — `golden/` (proje geneli) ve `scripts/<modül>/golden/`
     (modüle özel) altındaki küçük, izole referans projelerini baştan üretip
     aynı kontrolleri uygular. Bir modül bozulduğunda hangi modül olduğu
     doğrudan görünür.
7. **Modül self-test'leri:** `collision`, `dimensions`, `axis`, `openings`,
   `rooms`, `elevations`, `walls`, `importer`, `sections` ve `northarrow`
   modüllerinin her birinde bir `selftest.py` vardır ve hepsi çalıştırılır:

   ```
   python scripts/collision/selftest.py
   python scripts/dimensions/selftest.py
   python scripts/axis/selftest.py
   python scripts/openings/selftest.py
   python scripts/rooms/selftest.py
   python scripts/elevations/selftest.py
   python scripts/walls/selftest.py
   python scripts/importer/selftest.py
   python scripts/sections/selftest.py
   python scripts/northarrow/selftest.py
   ```

   Ortak disiplin: beklenen değerler ELLE hesaplanabilir tutulur ve kurallar
   **kasıtlı bozmayla** sınanır. "Temiz döndü" çıktısı tek başına hiçbir şey
   kanıtlamaz — kontrol hiç çalışmasa da temiz dönerdi. Her test ayrıca
   **yanlış-pozitif** tarafını da sınar.
8. **Doküman tutarlılığı:** `python scripts/doc_check.py` çalıştırılır. Bu
   kontrol, "çalışma sonunda dokümanları güncelle" kuralını düzyazı olmaktan
   çıkarıp MEKANİK hale getirir: görev durumu ile bulunduğu bölüm, durum özeti
   tablosu, `HD-xxx` atıfları ve modül/golden yapısı örtüşmüyorsa hata verir.
   Ölçüm raporu tek başına yeterli DEĞİLDİR: bir duvar kaysa veya etiket
   yanlış odaya yazılsa entity sayıları değişmeyebilir.

## Çakışma denetimi (rev-12'den itibaren)

- Çizim artık yalnızca ÜRETİLMİYOR, **doğrulanıyor**. Bir tefrişin duvara,
  kolona, başka bir tefrişe veya **kapı açılım yayına** girmesi ve bildirilen
  odaların dışına taşması `validate.py` içinde, **DXF üretilmeden önce**
  denetlenir. Uygulaması `scripts/collision/`dur; ayrı ad-hoc çakışma kodu
  yazılmaz.
- **Ayrım aritedir.** "Kendi verim geçerli mi" (poligon kapalı mı, açıklık
  host duvardan geniş mi) **ilgili modülün** işidir ve `validate.py::check_*`
  içinde kalır. "İki FARKLI eleman aynı yeri mi işgal ediyor" ise çakışma
  motorunun işidir.
- **Motor çizim modüllerini bilmez.** Yalnızca anonim
  `CollisionShape(tag, id, polygon)` tanır; her modül kendi ayak izini
  `scripts/<modül>/collision.py::footprints(floor, context)` ile verir.
- Politika üç seviyelidir: **FORBID** üretimi durdurur, **WARN** raporlanır,
  **IGNORE** normaldir. Kolonun duvar veya oda içinde olması TASARIMDIR ve
  IGNORE'dur; tefrişin duvara 5 mm'den fazla girmesi UYARI, tefrişin tefrişe /
  kolona / kapı sektörüne girmesi ve oda dışına taşması HATADIR.
- Tolerans **alan değil derinliktir** (`CONTACT_TOLERANCE = 5 mm`): dolabın
  duvara dayanması normaldir, duvarın içinden geçmesi değildir.

## Sürüm uyumu ve provenance (rev-12'den itibaren)

- **Sürümlenen şey kod değil, SÖZLEŞMEDİR.** Bir modülün iç yapısının
  değişmesi hiçbir projeyi etkilemez; `context.json`'dan OKUDUĞU alanların
  değişmesi etkiler.
- Üç mekanizma amaca göre ayrılır:
  - `meta.schema_version` (tek semver) **KAPIDIR**: `scripts/version.py`
    içindeki `SCHEMA_VERSION` ile MAJOR farkı varsa üretim DURUR.
    Minor/patch farkı yalnızca uyarı verir. Bugün opsiyoneldir (yoksa
    `1.0.0` varsayılır + uyarı); tüm context'ler taşıdıktan sonra `required`
    yapılacaktır.
  - Her modülün `CONTRACT_VERSION`'u **TEŞHİSTİR** (bloklamaz), yalnızca o
    modülün context'ten okuduğu alanlar değiştiğinde artar.
  - `output/provenance.json` **KAYITTIR**: her üretimde schema sürümleri,
    modül sözleşmeleri, git commit ve zaman damgası yazılır.
    `context.json`'a YAZILMAZ — orası proje tasarım verisidir.
- **Otomatik migrasyon YOKTUR.** Major kırılımda eski proje sessizce
  dönüştürülmez; normal bir revizyon olarak (`requests.jsonl` + `rev_history`)
  güncellenir. Aksi halde provenance yalan söylemeye başlar.

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
- Uygulama: `scripts/walls/` modülündeki `Wall` ve `WallNetwork` sınıflarıyla
  kapsüllenir (`generate_dxf.py` yalnızca public API'yi çağırır). Tüm duvar
  çizimleri bu sınıflardan türetilir/kullanılır — duvar çizen yeni kod
  tekilleştirilmiş bu sınıflar üzerinden yazılır, ayrı ayrı ad-hoc çizim
  mantığı eklenmez.
- **Rail çizim standardı (rev-15'ten itibaren):** rail'lerin NASIL çizildiği
  (`RailDrawingStandard` Protocol'ü, `scripts/walls/standard.py`)
  duvarın türünden (`kind`, `WallCatalog`) ayrılmıştır. Varsayılan
  (`CatalogRailStandard`) `tugla_bolme` için araya taralı (`ANSI31`) bir
  `HATCH`, `cam_duvar` için farklı bir linetype (`CAM`) ekler; `kind`
  bildirilmeyen veya tanımsız bir duvar **eski düz-rail davranışını
  BİREBİR korur** (`DefaultRailStandard`). Ayrıntı:
  `scripts/walls/CLAUDE.md`.

## Kesit (building section) standardı (rev-17'den itibaren)

- Kesit hattı **HİÇBİR ZAMAN eğik veya kademeli (jogged) alınmaz** —
  kullanıcı kararı: bu yapılarda bir kesit çizgisi X ve Y eksenindeki
  akslardan birine **PARALELDİR**. `sections[]`teki `axis_source` alanı
  `elevations[]`deki alanla **BİREBİR AYNI ANLAMDADIR**: `'vertical'` →
  kesit hattı sabit Y'de (genişlik = `floor_width`, `on_cephe` ile aynı
  izdüşüm); `'horizontal'` → sabit X'te (genişlik = `floor_depth`,
  `sag_cephe` ile aynı izdüşüm). Kesit, binanın **TEK** gerçek düşey kat
  istifini (`elevations[].levels[]`) `levels_from` ile ödünç alır — kendi
  kat yüksekliği verisini UYDURMAZ.
- **Konum operatör tarafından bildirilir.** Bildirilmezse sistem yapının
  **TAM ORTASINDAN DEĞİL**, ilgili kenarın **1/3 noktasından** varsayılan
  bir kesit alır (kullanıcı: "amacımız default olarak projenin tam
  ortasından biraz sağ ya da solundan kesit almaktır"). `sections[]` alanı
  **HİÇ verilmezse** sistem X ve Y ekseninden **BİRER varsayılan kesit**
  üretir (`A-A`, `B-B`); boş dizi (`[]`) verilirse bu varsayılan devre
  dışı kalır ve hiçbir kesit çizilmez.
- **Plan üzerindeki işaret:** her kat paftasında (aks ızgarasıyla aynı
  konumda, tüm katlarda ortak) kesit hattı + uçlarında bakış yönünü
  gösteren birer **üçgen** + üçgenin **sırtına** yazılan kesit harfi
  bulunur. Bu işaret `AKS` katmanından **BİLEREK farklı** bir katman/
  linetype/renkte çizilir (`KESIT` katmanı, `KESIT_HATTI` linetype'ı,
  kırmızımsı) — aks ile karıştırılmaması içindir.
- **Ayrı bir paftada gösterilir** ve pafta adına kesit harfi verilir
  (örn. `"A-A KESITI"`), antetin sağ-alt köşesinde görünür.
- Uygulaması `scripts/sections/` modülündeki `SectionCutLine` ve
  `SectionSheet` sınıflarıyla kapsüllenir; kat yüksekliği/galeri boşluğu/
  merdiven kırılması gibi ileri düzey duyarlılıklar için genişletme noktası
  (`SectionFeatureHook` Protocol'ü) hazırdır ama bugün hiçbir proje verisi
  bunu tetiklemez. Ayrıntı: `scripts/sections/CLAUDE.md`.

## Kuzey oku (rev-17'den itibaren)

- Her kat paftasına, binanın gerçek kuzeye göre yönünü gösteren standart
  bir **kuzey oku** sembolü çizilir. Veri `meta.north_angle` (derece, saat
  yönünde, paftanın "yukarı" yönünden gerçek kuzeye) ile gelir; **verilmezse
  ok HİÇ çizilmez** — yön uydurulmaz.
- Kuzey okunun **NASIL çizildiği** (`NorthArrowStyle` Protocol'ü,
  `scripts/northarrow/`) standarttan ayrılmıştır — ileride farklı bir
  sembol tasarımına geçilmesi `NorthArrow(style=...)` ile enjekte edilir,
  çağıran taraf (`generate_dxf.py`) değişmez (`RailDrawingStandard` ile
  AYNI desen, kullanıcı kararı: "entegrasyon zor olmasın").
- **rev-18 düzeltmesi:** rev-17'de AYNI talebin parçası olarak eklenen
  grafik ölçek çubuğu (`pafta::ScaleBar`, her paftaya 0-5 arası basamaklı
  bir cetvel çizen özellik) kullanıcı geri bildirimiyle ("her pafta
  içerisinde ölçek gibi bir şey var ... onu istemiyorum, kaldır") TAMAMEN
  KALDIRILDI — bkz. `docs/development/DEVELOPMENT_HISTORY.md` HD-012. Kuzey
  oku bundan etkilenmedi. Ayrıntı: `scripts/northarrow/CLAUDE.md`.

## Kot (seviye/datum) standardı (rev-19'dan itibaren)

- Kullanıcı talebi (rev-17'de gündeme geldi, rev-19'da uygulandı): *"kot
  verme mantıklarını yöneten bir mantık istiyorum ... kot organizasyonu hem
  planda hem kesitte kullanılacaktır ... bu mantığın projenin geneline
  hakim olması gerekecektir."* Uygulaması `scripts/levels/` modülündeki
  `LevelMark` sınıfıyla kapsüllenir; ayrı ad-hoc kot çizim kodu YAZILMAZ.
- **Sembol:** bayrak (üçgen) + kot metni. Kot metni **işaret + 2 ondalıklı
  METRE** formatındadır (kullanıcı kararı): `"+3.00"`, `"-0.20"`, sıfır
  seviyesi `"±0.00"`. Bu SADECE gösterim formatıdır; `context.json`daki
  asıl ölçü birimi (mm) DEĞİŞMEZ.
- **Kesit/görünüş:** OTOMATİK çizilir, HİÇBİR yeni veri GEREKMEZ — her kat
  sınırında bir kot işareti, `elevations::LevelStack`in ZATEN hesapladığı
  `(y0, y1)` değerlerinden türetilir (`levels` modülü kat yüksekliği
  hesabını YENİDEN YAPMAZ, sadece formatlar/çizer). `sections/`teki kesit
  paftaları da AYNI mekanizmayı (`levels_from` üzerinden) kullanır.
- **Plan:** rampa/teras gibi bir kademe farkının kotu `floors[].
  level_marks[]` ile AÇIKÇA verilir (`id`, `position`, `value_mm`) — bu
  GERÇEK proje verisidir, plan düzleminde otomatik türetilecek bir kaynak
  YOKTUR. **Veri verilmezse hiçbir işaret çizilmez** — kuzey oku ile AYNI
  "veri yoksa uydurma" deseni.
- **Katman:** `KOT` katmanı, `scripts/palette::PALETTE`den (DEV-030) gelen
  kod-sahipli sabit bir renkle (yeşil, diğer "primary" ailelerden — AKS/
  KOLON grisi, KESİT kırmızısı, MERDİVEN mavisi — bilerek farklı) çizilir.
  Ayrıntı: `scripts/levels/CLAUDE.md`.

## Çok katli bina yapisi (rev-2 tarihsel notu; güncel pafta kuralları geçerlidir)

- context.json semasi rev-2'de degisti: artik duz (tek daire) yapi degil,
  `meta.floor_width` / `meta.floor_depth` + `floors[]`
  (her biri kendi rooms/walls/openings/labels/counters/markings listesine
  sahip bir "pafta") + `elevations[]` (basitlestirilmis cephe seviye istifi)
  iceriyor. `schema/design.schema.json` bu yapiyi tanimlar.
- **Pafta duzeni:** Güncel davranış `scripts/pafta/CLAUDE.md` ve
  `generate_dxf.py::generate` içindeki `Sheet` sözleşmesidir: tüm paftalar
  ortak mutlak Y aralığı kullanır, dış çerçeveler bitişiktir, içerik
  `CONTENT_PADDING + FRAME_GAP` ile ilerler ve antet iki satırlıdır.
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
  dikdortgenleri olarak cizilir. Uygulamasi rev-14'ten (`DEV-011`) itibaren
  kendi izole modulundedir: `scripts/elevations::ElevationSheet` /
  `LevelStack` / `FacadeOpeningPlacer` — ayrı ad-hoc cephe cizim kodu
  yazilmaz. `below_ground: true` seviyeler zemin cizgisinin (`y=0`) altinda
  **VE artik gercekten kesikli (`DASHED`) linetype'la** cizilir (rev-14'te
  kapatilan basitlestirme — onceden sadece etiketle ayirt ediliyordu, DXF'te
  cizgi turu ayni kaliyordu). Ayrıntı: `scripts/elevations/CLAUDE.md`.
- **Bilinen basitlestirmeler (rev-2):** Banyo/WC gibi servis odalari,
  "birim bandi"nin tam derinligini paylastigi icin gercekte olmasi
  gerekenden biraz dar-uzun orantili olabilir; otopark cizgileri
  (`markings[]`, `OTOPARK` katmani) salt gorsel/semantik olmayan
  isaretlemedir, validate.py bunlari kontrol etmez; asansor kapi sembolu
  cizilmez (sadece etiketli kapali oda olarak gosterilir). **Merdiven
  artik istisnadir (DEV-022, `scripts/stairs/`):** `floors[].stairs[]`
  ile ACIKCA bildirilirse gercek basamak/riht cizgileri + yon oku + kesme
  cizgisi cizilir (opsiyonel, opt-in - bildirilmezse eskisi gibi sadece
  etiketli kapali oda). **Bu ornek projenin `Merdiven` odasi (4000x3000mm)
  hala `stairs[]` VERISI TASIMIYOR:** modul yalnizca tek duz kollu merdiven
  destekliyor ve bu oda, ~3000mm kat yuksekligi icin tek duz kolla
  SIGMIYOR (`resolve_stair` bunu `StairFitError` ile dogru sekilde
  yakaliyor) - sahanlikli/cift kollu merdiven henuz ayri bir gelistirme
  konusudur, bkz. `scripts/stairs/CLAUDE.md` "Bilinen sinirlamalar".

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
- **Ölçü zinciri (rev-13'ten itibaren):** Kat paftalarında ölçü, kullanıcı
  tarafından yazılmaz — **geometriden TÜRETİLİR**. Bir ölçü sayısı tasarım
  verisi değil, geometrinin ölçüsüdür: duvar koordinatı zaten
  `context.json`dadır ve ölçüyü ayrıca elle yazmak aynı bilgiyi iki yerde
  tutmak olurdu (duvar taşınır, ölçü metni eski kalır). Bu, "ölçü uydurulmaz"
  kuralını DELMEZ — sayı uydurulmuyor, ölçülüyor.
  - **Hangi kenarın ölçüleneceği bir SUNUM kararıdır** ve `meta.dimensions`
    ile gelir. Varsayılan KAPALIDIR; bu proje rev-13—rev-17 arası açık
    tuttu, **rev-18'de kullanıcı talebiyle yeniden KAPALIYA çekildi**
    ("duvar ölçüleri sistem üzerinde şimdilik hiçbir yerde
    gösterilmeyecek" — bkz. "Aks (grid) sistemi" bölümündeki "Aks arası
    mesafeler" notu). Özellik KALDIRILMADI, sadece bu projenin sunum
    ayarı varsayılana döndü; `golden/aciklik_varyantlari` açık haliyle
    sınamaya devam eder.
  - Üç kademe, **içten dışa doğru kabalaşır**: `aciklik` (cephedeki
    kapı/pencere kenarları) → `mahal` (dik duvarların **yüzleri**: net mahal +
    duvar kalınlığı) → `toplam` (dıştan dışa). Üçü de aynı ordinatlarda
    başlayıp biter.
  - **Aks ölçü zinciri EN DIŞTA durur** (mimari gelenek). Aks baloncukları da
    yığının dışına itilir; gereken uzamayı `dimensions` hesaplar, `axis` ise
    baloncuk yarıçapını verir — iki modül birbirini import etmez.
  - Aynı kenarda iki zincirin aynı baseline'a oturması **hatadır**
    (`ChainLayout.verify_no_overlap`); kademelendirme `ChainStack` ile
    deterministiktir. Uygulaması `scripts/dimensions/`dır, ayrı ad-hoc ölçü
    kodu yazılmaz.
  - `pafta::CONTENT_PADDING` bu yüzden rev-13'te 3200 → 4000 oldu; artış
    tahminle değil, taşma korumasının verdiği ölçüyle yapıldı.
- **Açıklık varyantları ve açılım yönü (rev-13'ten itibaren):** Kapılar
  `variant` (`single`/`double`/`sliding`/`folding`), `swing` (menteşe duvarın
  başında mı sonunda mı) ve `host_side` (kanat hangi tarafa açılıyor)
  alanlarıyla sürülür. **Üçünün de varsayılanı rev-12 davranışıdır**, yani
  alan verilmeyen projeler aynı çizimi üretir. Sürme kapı açılım alanı
  GEREKTİRMEZ ve çakışma denetiminde sektör üretmez.
  - **Açılım yayının tek sahibi `openings::swing_geometry`dir**; çizim ve
    çakışma denetimi aynı kaynaktan okur. İkisinin ayrı hesaplanması rev-13'te
    gerçek bir hataya yol açtı (denetlenen sektör çizilen yaydan yarım
    genişlik kayıktı).
  - `position_from_start`, duvar başlangıcından açıklığın **MERKEZİNE** olan
    mesafedir; duvar boyunca gerçek boşluk aralığı her zaman
    `walls.gaps_for_wall` ile alınır.
- **Yazı tipi (rev-9'dan itibaren):** Projenin tüm metinleri **Arial
  Narrow**'dur. Uygulaması `scripts/typography::TextStyles`'tir: proje fontu
  `Standard` text style'ına yazılır, böylece stil verilmeyen HER metin
  (antet, aks baloncuğu, cephe etiketi, kapak bloğu, ölçü metni) otomatik
  olarak proje fontunu kullanır. **Kritik:** `pafta.fit_text_height`'in
  ölçtüğü font ile çizilen font AYNI olmak zorundadır; bu yüzden
  `pafta.DEFAULT_FONT` ikinci bir sabit tutmaz, `typography`den import eder.
  Font, **dosya adıyla** verilir (`arialn.ttf`) — `ArialNarrow` gibi bir aile
  adı ezdxf'te sessizce Arial'e düşer ve ölçüm yanlış çıkar. Mahal etiketi
  için `meta.fonts.room_label` ile ayrı bir font seçilebilir.
- **Mahal (oda) etiketi biçimi (rev-9'da uygulandı):**
  Varsayılan mahal etiketi **üç satırdır**:

  ```
  SALON        <- 1. satir: mahal adi, BLOK
  ZK-04        <- 2. satir: kat kodu + mahal no
  28.9 m2      <- 3. satir: alan
  ```

  - Mahal adı **blok** (büyük harf) olarak işlenir.
  - Kat kodu öneki `floors[].code`'dan gelir, etiketten TÜRETİLMEZ:
    `B1` = 1. bodrum, `B2` = 2. bodrum, `ZK` = zemin kat,
    `K1`/`K2`/`K3`… = normal katlar, **`TR` = çatı/teras**.
  - Mahal no `rooms[].no`'dan gelir. Kat kodu ile birleşince proje genelinde
    **benzersiz** bir mahal kimliği verir (`ZK-04`). `validate.py` hem kat
    içinde mahal no benzersizliğini hem de kat kodu benzersizliğini kontrol
    eder.
  - Etiket, oda poligonunun centroid'ine ortalanır ve oda kutusuna hem
    **genişlik hem yükseklik** bakımından sığacak şekilde ölçeklenir.
  - Uygulaması `scripts/rooms::RoomLabeler`dır — ayrı ad-hoc etiket kodu
    yazılmaz.
  - **BLOK+ATTRIB (rev-14, DEV-018):** standart 3 satırlı durumda etiket
    artık üç ayrı `TEXT` değil, tek bir `MAHAL_ETIKET` `INSERT`i + üç
    `ATTRIB` (`MAHAL_ADI`/`MAHAL_KOD`/`ALAN`) olarak çizilir. AutoCAD'de
    etiket **tek seçilebilir nesne** olur ve alanları CAD içinde
    düzenlenebilir. Konum/yükseklik matematiği eski düz-TEXT formülüyle
    **birebir örtüşür** (blok `NOMINAL_HEIGHT`e göre tanımlanır, `INSERT`
    ölçeği `fitted_height/NOMINAL_HEIGHT`tir — doğrusal olduğu için eşitlik
    kanıtlanabilir, bkz. `scripts/rooms/CLAUDE.md`). Kat kodu VEYA mahal no
    eksikse (2 satır) blok kullanılmaz, eski düz-TEXT çizimine düşülür.
- **Tefriş (rev-10'dan itibaren):** Tefriş **her zaman DXF `BLOCK`** olarak
  çizilir — tip başına bir blok tanımı, yerleşim başına bir `INSERT`.
  Uygulaması `scripts/furniture::FurnitureCatalog` / `FurnitureBlocks` /
  `FurnitureRenderer`dır; ayrı ad-hoc tefriş çizimi yazılmaz.
  - Tefrişin **kendi layer'ları ve renkleri** vardır; renkler **kahverengi
    ailesinde ve birbirine yakın tonlardadır** (zıt renk kullanılmaz), çünkü
    tefriş duvar/aks gibi okunması gereken katmanla yarışmamalıdır. Gruplar:
    `TEFRIS-OTURMA`, `TEFRIS-YEMEK`, `TEFRIS-YATAK`, `TEFRIS-MUTFAK`,
    `TEFRIS-ISLAK`. Layer'lar kod tarafında zorunlu kılınır (aks gibi),
    context.json'dan renk alınmaz.
  - Katalog ölçüleri ofis/katalog standardıdır (çizim sabiti); **yerleşim
    (konum/rotasyon) proje verisidir** ve `floors[].furniture[]` ile gelir,
    uydurulmaz. Blok ekleme noktası elemanın **sol-alt köşesidir**.
  - **Kapı tefriş DEĞİLDİR.** Kapı/pencere bir duvar açıklığıdır ve
    `openings/` + `walls/` modüllerine aittir (endüstri standardı: IFC'de
    `IfcDoor` bir `IfcBuildingElement`tir, AIA/NCS'te kapı `A-DOOR` /
    tefriş `A-FURN`). Ayrıntı: `scripts/furniture/CLAUDE.md`.
- **Kolonlar (rev-10'dan itibaren):** Kolonlar **taralıdır**. Tarama
  deseni ve ölçeği dinamiktir (`meta.column_hatch`), varsayılanı **`ANSI33`
  ve ölçek `3.0`**. Kontur `KOLON`, tarama `KOLON-TARAMA` layer'ındadır.
  Uygulaması `scripts/columns::ColumnGrid` / `ColumnRenderer`dır.
  `position` kolonun **merkezidir**. Kolonlar tefrişten ÖNCE çizilir.
  **Kolon adı bugün çizilmez** — kullanıcı kolonları aks birleşim
  noktalarıyla ifade ediyor; altyapı (`Column.name`, `ColumnLabelStyle`)
  hazırdır ve `meta.column_label.enabled` ile kod değişmeden açılır.
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
- **Kapak paftası (ISO 7200 Tip-A, rev-8'den itibaren):** Projenin İLK
  paftası bir kapak paftasıdır ve **özel bir paftadır** — aşağıdaki kurallar
  yalnızca bu paftaya uygulanır. Uygulaması `scripts/pafta::CoverBlock`
  sınıfıdır; ayrı ad-hoc kapak kodu yazılmaz.
  - **Ölçü:** Kapak bloğu **basılı kağıt üzerinde her zaman tam A4
    (210x297mm)** olur. Modelspace ölçüsü bu yüzden projenin ölçeğine göre
    türetilir (`to_modelspace`): 1:50'de 10500x14850mm, 1:100'de
    21000x29700mm çizilir ve **her iki durumda da çıktıda 210x297mm**
    basar. Çıktı daima ölçekli alındığı için doğru olan budur —
    modelspace'e birebir 210x297 yazmak ölçekli çıktıda kapağı
    4.2x5.9mm yapardı.
  - **Konum:** Kapak bloğu paftanın **SAĞ-ALTINA sabitlenir**. Pafta
    genişliği kapak genişliğine eşit olduğu için bu pratikte "en alta oturur"
    demektir. Sebep fizikseldir: proje çıktı alınıp katlandığında (DIN 824)
    bu bölge en üste gelir.
  - **Pafta genişliği:** Kapak paftasının **DIŞ ÇERÇEVE genişliği kapak
    genişliğine EŞİTTİR** — yani pafta dış hattı, kapak bloğunun dış hattıyla
    çakışır (1:50'de 10500mm = çıktıda 210mm). Bunun için bu paftada
    `CONTENT_PADDING` **uygulanmaz** (`padding=0`) ve çerçeve boşluğu kapağın
    kendi eşit offseti olur; aksi halde çerçeve iki yandan 3350'şer büyüyüp
    pafta 17200 (534mm) olurdu ve basılı pafta A4 genişliğinde katlanmazdı.
    Yüksekliği ise diğer tüm paftalarla ortak mutlak Y aralığını korur;
    kapak bloğu paftanın **altına** oturur, üstte kalan bölüm boştur ve A4
    panelinin üst kenarı çift çizgiyle kapatılır.
  - **Bitişiklik istisnası:** Kapak paftasında padding olmadığı için ardışık
    pafta X-ofseti genel `width + 2*(CONTENT_PADDING+FRAME_GAP)` formülüyle
    hesaplanmaz; bir sonraki paftanın dış hattı doğrudan kapak paftasının dış
    hattına oturtulur (`generate_dxf.py::generate`).
  - **Antet yok:** Bu paftada sağ-alt köşedeki iki satırlık Tip-B şerit
    anteti **çizilmez** (`Sheet.draw(..., title_box=False)`) — o köşeyi kapak
    bloğu kaplar ve kapağın kendisi antet işlevini görür.
  - **Çerçeve:** Kapağın kendi çerçevesi de `Sheet`in çift çizgili çerçevesi
    gibi **her kenardan EŞİT offsetlidir** (kağıt üzerinde 10mm). DIN/ISO
    sayfa marjı (sol 20 / diğer 10) burada KULLANILMAZ; eşit olmayan bir
    offset görünümü verdiği için kaldırıldı.
  - **İçerik:** Proje adı (başlık), `PROJE TIPI` / `OLCEK` / `MIMAR` /
    `TARIH` bilgi satırları ve imza alanları. **Mimar adı ve tarih gibi resmi
    veriler context.json'da yoksa UYDURULMAZ** — o satıra metin yazılmaz, elle
    doldurulacak bir çizgi bırakılır. Ayrıntılı kapak TASARIMI ayrı bir talep
    olarak gelecektir.
  - **İmza alanları (rev-12'de kullanıcı tarafından sabitlendi):** DÖRT alan
    vardır ve 2×2 yerleşir — **MIMAR, BELEDIYE, YETKILI 1, YETKILI 2**.
    `meta.cover.signature_fields` ile sürülür; başlığı boş bırakılan bir alan
    `(UNVAN)` olarak işaretlenir (artık bu projede kullanılmıyor).
  - **Üretim damgası (rev-12, kullanıcı talebi):** Kapağın eteğinde, imza
    bandının ALTINDAKI boş şeritte iki küçük satır bulunur: solda
    `URETIM: <tarih saat>`, sağda `SISTEM: <schema sürümü>`. Bu damga bilgi
    satırlarındaki `TARIH` ile **AYNI ŞEY DEĞİLDİR** — o proje/onay tarihidir,
    context.json'dan gelir ve uydurulmaz; damga ise çıktının NE ZAMAN ve
    NEYLE üretildiğinin kaydıdır ve sistem tarafından yazılır (bkz.
    `scripts/version.py`, `output/provenance.json`).
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
- **Ölçek mevzuatı ve kağıt boyutu planlaması (rev-4'te mevzuat-tabanlı
  hale getirildi):** `scripts/pafta::PaperSizePlanner`, TMMOB/imar
  yönetmeliği araştırmasına dayanır:
  - **Proje tipine göre ölçek KESİN KISITTIR** (`PROJECT_TYPES`,
    `meta.project_type` — opsiyonel, verilirse kontrol edilir):
    `MIMARI_UYGULAMA`→sadece 1:50; `MIMARI_RUHSAT_KUCUK`→oturum ≤300m²
    ise 1:100 veya 1:50; `STATIK_KALIP`→sadece 1:50; `VAZIYET_PLANI`→1:200
    veya 1:500; `DETAY`→1:20/1:10/1:5/1:1. `classify_violation(...)`,
    projenin BİLDİRİLEN tipiyle kullandığı ölçeğin çeliştiği durumları
    `generate_dxf.py` çalıştığında UYARI olarak raporlar (bloklamaz).
  - **Rulo kağıt NET yükseklikleri** (`ROLL_PAPER_NET_HEIGHT_MM`):
    45'lik→430mm net, 60'lık→580mm net, 90'lık→880mm net (üst/alt 10mm
    pay düşülmüş) — önceki sürümdeki "brüt = net" varsayımı YANLIŞTI,
    düzeltildi.
  - **KRİTİK KURAL — ölçek küçültülemez:** Pafta boyutuna sığdırmak için
    ölçek KÜÇÜLTÜLEMEZ (önceki "1/50 favori, sığmazsa 1/100'e düş" kaskad
    fikri bu yüzden YANLIŞTI ve KALDIRILDI). En büyük rulo (90'lık, net
    880mm) bile yetmiyorsa tek geçerli çözüm **pafta bölme + keyplan**
    eklemektir (aks/dilatasyon hatlarından bölünür, her parçaya 1:500 veya
    1:1000 ölçekli, binanın şematik konturunu tarayarak gösteren bir
    keyplan eklenir) — bu HENÜZ uygulanmadı, bkz.
    `scripts/pafta/CLAUDE.md`.
  - **Antet (başlık kutusu) boyutu artık ÖLÇEĞE göre türetilir**
    (DIN/ISO 5457 Tip-B: kağıt üzerinde 185×70mm), pratik bir üst sınırla
    (`MAX_TITLE_BOX_WIDTH_MM`/`MAX_TITLE_BOX_HEIGHT_MM`) sınırlanmış hâlde
    — tam ölçekli uygulanması, paftanın gerçekten standart bir kağıt
    boyutuna oturduğu bir "uniform sheet template" gerektirir (henüz YOK,
    bkz. `scripts/pafta/CLAUDE.md` "Bilinen sınırlamalar"). Tip-A (kapak
    paftası, ISO 7200) henüz hiç uygulanmadı, sadece fikir olarak not
    edildi.
  - **Bu örneğin mevzuat durumu (rev-8'de giderildi):** Örnek proje sistem
    geliştirmesi başlamadan önce üretildiği için uzun süre `1:100` ölçekte
    kaldı ve `MIMARI_UYGULAMA` sınıfıyla uyumsuz bir mevzuat uyarısı taşıdı.
    rev-8'de ölçek `1:50`'ye çekildi; `classify_violation(...)` artık uyarı
    üretmiyor ve en yüksek pafta (67.0 cm) 90'lık rulonun 88 cm net
    yüksekliğine sığıyor. Yeni projelerde mevzuat kontrolü yine validator ve
    `PaperSizePlanner` üzerinden uygulanır.
- **Aks (grid) sistemi:** Bina, `context.json`'ın üst seviye `grid` alanında
  tanımlanan bir aks ızgarasına oturur:
  - `grid.vertical_axes`: düşey aks çizgileri (sabit X, Y boyunca uzanır),
    **nümerik** etiketli (1, 2, 3, ...).
  - `grid.horizontal_axes`: yatay aks çizgileri (sabit Y, X boyunca
    uzanır), **alfabetik** etiketli (A, B, C, ...).
  - **Ara aks `1'` yazılır, `1A` YAZILMAZ (rev-13 kararı).** Gerekçe tercih
    değil çatışmadır: yatay aile zaten `A`, `B`, `C`'dir, dolayısıyla `1A`
    "1 ve A akslarının kesişimi" gibi okunur ve `columns::on_axis_report`un
    ürettiği kolon adıyla (`B2`) aynı dizede çarpışır. Kural
    `scripts/axis/naming.py` içinde yazılıdır ve `validate.py` tarafından
    **mekanik olarak** denetlenir; aynı etiketin iki kez kullanılması da
    hatadır.
  - **Kısmi aks (rev-13):** `extent` verilen bir aks yalnızca o aralıkta
    uzanır, uçlarına kendi baloncukları gelir ve **ulaşmadığı kenarın ölçü
    zincirine GİRMEZ** — aksi halde zincir, orada olmayan bir aksı ölçüyormuş
    gibi görünürdü.
  - **Kolon rasteri kapsama raporu (rev-13):** `AxisCoverageReport`, aks'sız
    kalan kolon hizalarını üretim sırasında UYARI olarak bildirir. **Salt
    okunurdur** — context'e aks yazmaz; karar kullanıcınındır.
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
    baloncukları/çerçeveleri çakışmamalıdır; ardışık pafta yerleşimi güncel
    `Sheet` ve `generate_dxf.py::generate` sözleşmesine göre yapılır.
  - **Aks arası mesafeler (rev-18'de netleştirildi):** Ardışık akslar
    arasındaki mesafe, gerçek bir DXF `LINEAR DIMENSION` (ölçü) varlığıyla,
    **küçük punto** (~120mm) ve **tam sayı cm** metniyle gösterilir
    (`AxisGrid._dim_chain_x/_dim_chain_y`). Bu, aks sınıfına ait bir
    fonksiyondur, ayrı bir "ölçülendirme" akışı değildir. **Kullanıcı
    kararı (rev-18):** bu ölçü zinciri, çizgileri/oku/metniyle **AKS ile
    AYNI katmandadır** (`ezdxf`'in `add_linear_dim` render'ının ölçü/uzatma
    çizgilerini DIMENSION'ın katmanından bağımsız olarak "0" katmanına
    çizdiği bir kütüphane hatası vardı — render sonrası düzeltilir, bkz.
    `scripts/dimensions/linear.py::_fix_geometry_block_layer`) ve **iki
    bilgiyi birlikte gösterir:** (1) ardışık aks-aks mesafeleri, (2) bir
    kenarda 2'den fazla aks varsa, ayrıca **en uçtaki iki aksın arasındaki
    TOPLAM mesafe** — bu ikinci zincir aksın kendi baloncuk/uzama
    bölgesinin ötesinde durur (`AxisDrawingStandard.total_dimension_
    clearance`). **Duvar/oda ölçüleri (`meta.dimensions` — aciklik/mahal/
    toplam kademeleri) aks ölçüsünün yanında GÖSTERİLMEZ:** kullanıcı,
    kademelerden birinin (mahal) ara sıra bir duvarın SADECE kalınlığı
    kadar bir segment ürettiğini ("duvarların kalınlıklarını ...
    göstermemeli, bu kafa karıştırır") ve bunun aks ölçüsüyle yan yana
    kafa karıştırıcı olduğunu bildirdi; bu yüzden bu proje `meta.
    dimensions.enabled`'ı **`false`ya çekti** (rev-18) — özellik
    `scripts/dimensions/` içinde hâlâ vardır ve `golden/aciklik_varyantlari`
    onu sınamaya devam eder, sadece bu projede şimdilik KAPALIDIR
    ("duvar ölçüleri sistem üzerinde şimdilik hiçbir yerde gösterilmeyecek").
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
   kullanıcı izin verse bile bu kural geçerlidir. Commit kimliği sabit bir
   kişi veya agent adına zorlanmaz: hangi agent çalışıyorsa kendi beyan ettiği
   ad ve e-posta ile imza atar. Agent commit öncesinde `GIT_AUTHOR_NAME`,
   `GIT_AUTHOR_EMAIL`, `GIT_COMMITTER_NAME` ve `GIT_COMMITTER_EMAIL`
   değerlerini yalnızca o commit komutuna özel sağlamalıdır. Agent kimliği
   açıkça mevcut değilse commit durdurulur ve kullanıcıdan kimlik istenir;
   başka bir agent'ın veya Claude'un kimliği taklit edilmez. Kalıcı Git config
   değişikliği yapılmaz.
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
5. **Git kimliği ve push hesabı (rev-8'de gerçeğe göre düzeltildi):** Push
   işlemi **yalnızca kullanıcı açıkça isterse** yapılır; aksi halde proje
   tamamen lokal kalır.
   - **Remote:** `origin` = `https://github.com/yusufDafne/DXFWorking.git`.
     Bu hedef rev-8'de kullanıcı onayıyla doğrulandı ve kullanıldı.
   - **ÖNCEKİ KURAL YANLIŞTI:** Bu madde eskiden push'un farklı bir GitHub
     hesabıyla ve belirli bir SSH alias'ı üzerinden yapılmasını söylüyordu;
     rev-8'de bunun bu makinedeki gerçek yapılandırmaya uymadığı görüldü ve
     kural mevcut remote'a çekildi.
   - **Agent, yerel SSH yapılandırmasını incelemez ve anahtar/hesap envanteri
     çıkarmaz.** Push hedefi `git remote -v` ile okunur; hedefin değişmesi
     gerekiyorsa kullanıcıya sorulur, agent remote'u kendi başına değiştirmez.
   - **Global git config hiçbir zaman değiştirilmez.** Commit kimliği, o
     komuta özel `GIT_AUTHOR_*` / `GIT_COMMITTER_*` değişkenleriyle verilir
     (bkz. madde 3).

## Belirsizlik durumunda

- Eksik/belirsiz bilgi varsa varsayım yapıp üretime devam etmek yerine
  kullanıcıya doğrudan soru sorulur.
