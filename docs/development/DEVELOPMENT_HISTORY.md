# Tamamlanan Geliştirmeler Geçmişi

Aktif geçmiş kapasitesi: **50 kayıt**. En eski tamamlanmış kayıt, 51. kayıt
alınırken silinir. Ayrıntılı teknik değişiklikler git geçmişi ve ilgili proje
provenance kayıtlarıyla ilişkilendirilir.

## HD-010 — DXF duvar tarayıcısı ve kind-farkındalı rail standardı

- **Durum:** COMPLETED
- **Tamamlanma:** 2026-09-24
- **Görevler:** `DEV-013` ve `DEV-014` (kullanıcı: "dev 13 ve 14'ü yap").
- **Kapsam:** `scripts/importer/` (yeni modül, `import/`den yeniden
  adlandırıldı), `scripts/walls/standard.py` (yeni), `scripts/walls/
  render.py`, `scripts/walls/__init__.py`, `scripts/validate.py`,
  `schema/design.schema.json`, `golden/duvar_standartlari/` (yeni).

### İsim düzeltmesi: `import/` → `importer/`

Planlama sırasında modül `scripts/import/` olarak adlandırılmıştı.
Uygulamaya geçilince görüldü ki **`import` bir Python ANAHTAR
KELİMESİDİR** — `import import` bir `SyntaxError`dır, bu isim hiçbir zaman
geçerli bir paket olamazdı. `fixture` → `golden` (rev-11) ile AYNI
kategoride bir hata: planlama sırasında seçilen ad, kod yazılınca teknik
olarak kullanılamaz çıktı. Aynı çözüm uygulandı: dizin + tüm doküman
atıfları `importer/`e taşındı (`git mv`), `DEV-013` kimliği değişmedi.

### DEV-013 — `importer/`: `DxfWallScanner`

- Mevcut bir DXF'ten `LINE` çiftlerini tarar; üç koşulu (paralellik ≤10°,
  kalınlık 40–400mm, örtüşme oranı ≥0.5) geçen çiftleri, ELLE hesaplanabilir
  bir confidence formülüyle (`parallel_score * overlap_score`) duvar adayı
  olarak raporlar. Merkez çizgisi SADECE örtüşen aralıkta hesaplanır.
- **Desen:** `walls.scan::RoomPolygonScanner.suggest_wall_dicts` İLE AYNI —
  salt-okunur, context'e YAZMAZ. `WallCandidate.as_wall_dict()` şema-uyumlu
  bir sözlük üretir ama hiçbir yere OTOMATİK eklenmez; insan/agent
  onayından sonra normal talep akışıyla eklenir.
- **Yan kazanç:** `RoomPolygonScanner.suggest_wall_dicts` rev-1'den beri
  çıktısına `"kind"` koyuyordu ama şema bu alanı TANIMIYORDU — o aracın
  çıktısı hiçbir zaman gerçekten context'e eklenemezdi. `DEV-014`nin şema
  düzeltmesi bunu da kapattı.

### DEV-014 — `walls/`: `RailDrawingStandard`

- `CatalogRailStandard` (yeni sistem varsayılanı), `wall.kind`e göre
  `tugla_bolme` için `ANSI31` `HATCH`, `cam_duvar` için `CAM` linetype
  ekler; bilinmeyen/eksik `kind` `DefaultRailStandard`e (eski TEK yöntem,
  düz `LINE`) düşer.
- **Gerçek boşluk bulundu:** `WallCatalog`/`Wall.from_context` `kind`i HER
  ZAMAN okuyordu ama `schema/design.schema.json`nin `additionalProperties:
  false` olan `wall` tanımında YOKTU — hiçbir context.json bunu
  KULLANAMAZDI. Şemaya eklendi; `validate.py::check_walls` artık bilinmeyen
  bir `kind` değerini (yazım hatası) HATA sayar.
- **Geriye dönük uyumluluk ölçülerek doğrulandı:** hiçbir mevcut proje
  `kind` bildirmiyordu; `CatalogRailStandard`ı varsayılan yapmak `--golden-
  set` `--update` GEREKMEDEN geçti (sıfır görsel etki).
- **Yeni golden referansı `golden/duvar_standartlari`:** üç duvar türünü
  (varsayılan, tuğla, cam) VE bir kapı açıklığının tarama/linetype'ı doğru
  DIŞLADIĞINI (hatch 2 parçaya bölünür, kapı boşluğuna girmez) birlikte
  sınar.

### Doğrulama

- İki yeni self-test (`importer`, `walls`) — toplam SEKİZ modül self-test'i
  oldu. Her ikisi de elle hesaplanabilir örnekler + negatif testlerle.
- `py_compile`, `validate`, `generate`, `preview`, 5 semantik kural,
  4 golden referans, `doc_check` — hepsi temiz.

### Golden output etkisi

- Ana proje ve mevcut 3 golden referansı DEĞİŞMEDİ (hiçbiri `kind`
  kullanmıyor) — `--update` gerekmedi.
- Yeni `golden/duvar_standartlari` referansı eklendi (2 `HATCH`, `CAM`
  linetype'lı 4 rail parçası).

### Bilinen sınırlamalar

- `importer/`: sadece `LINE` taranır (`LWPOLYLINE` YOK); PDF/altlık
  (Fikir 2) uygulanmadı; köşe/T-kesişimi algılamaz.
- `walls/`: tarama deseni/ölçeği context'ten AYARLANAMAZ (kolonlardaki
  `meta.column_hatch` gibi); katalog kalınlıkları hâlâ kod seviyesinde
  (Fikir 2 uygulanmadı).

- **Sonraki direktif:** Planlanan modül kataloğu (`DEV-011`…`DEV-018`)
  TAMAMLANDI. Sıradaki iş, mevcut modüllerin ertelenen "Fikir 2"lerinden
  biri veya yeni bir modül fikridir — sistem mimarı açıkça seçmelidir.

## HD-009 — Mahal etiketi BLOCK+ATTRIB, cephe modülü ve kapı/pencere cetveli

- **Durum:** COMPLETED
- **Tamamlanma:** 2026-09-23
- **Görevler:** `DEV-018` → `DEV-011` → `DEV-012` (bu sırayla; `DEV-018`
  blok yaygınlaştırmasının `DEV-011`den önce ele alınması iş tekrarını
  önledi — `DEVELOPER_NOTES.md`de rev-13 sonunda kayıtlı öneriydi).
- **Kapsam:** `scripts/rooms/` (BLOK+ATTRIB + `selftest.py` yeni),
  `scripts/elevations/` (yeni modül, `generate_dxf.py`den taşındı),
  `scripts/legend/` (yeni modül, ilk taslak `CLAUDE.md`nin fikri DEĞİL,
  Fikir 1 uygulandı), `scripts/golden_report.py` (`_iter_all` yeni),
  `scripts/preview.py` (elevations/legend'ı import eder, kendi kopyasını
  tutmaz), `scripts/collision/scene.py`, `scripts/version.py`,
  `generate_dxf.py`, golden referansları (3'ü de `--update`).

### DEV-018 — mahal etiketi BLOCK+ATTRIB

- **Ölçülerek görüldü:** görev açılırken "hiç BLOCK kullanılmıyor" denmişti
  ama bu ölçüm `furniture` (`DEV-010`) BLOCK/INSERT kullanmaya başlamadan
  ÖNCEki bir kayıttı ve bayatlamıştı — ana projede tefriş YOK, bu yüzden
  `INSERT` sayısı hâlâ 0 görünüyordu, furniture kodu blok kullanmadığı için
  değil.
- Asıl boşluk mahal etiketiydi. `MAHAL_ETIKET` bloğu üç `ATTDEF`
  (`MAHAL_ADI`/`MAHAL_KOD`/`ALAN`) ile bir kez tanımlanır; `INSERT` ölçeği
  `fitted_height / NOMINAL_HEIGHT`tir. Bu, eski düz-`TEXT` formülüyle
  **doğrusal ölçekleme kanıtıyla** birebir örtüşür (her terim `height *
  sabit` biçimindedir) — `selftest.py`de `< 1e-6` toleransla doğrulandı.
- **Gerçek bir ezdxf tuzağı bulundu:** bir `INSERT`e bağlı `ATTRIB`ler DXF
  dosyasında GERÇEKTEN ayrı entity'lerdir (AutoCAD'de tek tek düzenlenebilir)
  ama ezdxf bunları genel layout iterasyonuna/`query()`'e DAHİL ETMEZ. Bu,
  `golden_report.py`nin ölçüm raporunu ve `rule_room_labels`i SESSİZCE kör
  ederdi. `_iter_all` yardımcısı (`for e in modelspace: yield e; if INSERT:
  yield from e.attribs`) eklenerek kapatıldı.
- Kat kodu VE mahal no'nun ikisi de eksikse (2 satır) blok kullanılmaz, eski
  düz-TEXT'e düşülür — blok 3 ATTDEF için SABİT yerleşimlidir.

### DEV-011 — `elevations/` modülü + below-ground linetype

- `generate_dxf.py` içine gömülü `draw_elevation`/`elevation_vertical_extent`
  kendi modülüne taşındı (`ElevationSheet`, `LevelStack`,
  `FacadeOpeningPlacer`, `Level`) — diğer tüm modüllerle aynı desen.
- **Kapatılan basitleştirme:** `below_ground: true` seviyelerin DXF'teki
  çizgi türü artık gerçekten `DASHED`tir (önceden sadece etiketle ayırt
  ediliyordu). `axis` modülü AYNI isimle aynı deseni yükler; iki modül
  birbirini import ETMEZ, her biri kendi `if name not in doc.linetypes`
  korumalı kaydını yapar.
- **Taşıma sırasında bulunan tutarsızlık:** `preview.py`nin kendi
  `elevation_vertical_extent` KOPYASI `machine_room` protrüzyonunu pafta
  Y-aralığı hesabına KATMIYORDU (gerçek DXF versiyonu katıyordu). Ortak
  `LevelStack`e geçince bu sessizce düzeldi.

### DEV-012 — `legend/` modülü: kapı/pencere cetveli

- **İki fikirden Fikir 1 seçildi.** Veri zaten hazırdı
  (`OpeningSchedule.from_openings`); `OpeningLegend.rows` bunu proje çapında
  (tip, varyant, genişlik) ile GRUPLAYIP `LegendRenderer.draw` ile gerçek bir
  MARKA/TİP/VARYANT/GENİŞLİK/ADET cetveli çizer. Ana projede 145 açıklık →
  10 grup (6 kapı + 4 pencere).
- **Açık karar kapandı — nereye çizilir:** kapak paftasının kapak bloğunun
  ÜSTÜNDE kalan, HER ZAMAN boş kalan alana (A4 kapak, daha uzun paylaşılan
  pafta Y-aralığı içinde). Ayrı pafta açılmadı.
- **Pencerede `VARYANT` sütunu `-`dir** — `openings/style.py` varyantı
  SADECE kapıda kullanır; pencerede "TEK KANAT" yazmak var olmayan bir
  ayrımı uydururdu.
- `preview.py` da AYNI `COLUMNS`/`COLUMN_WEIGHTS` sabitleriyle matplotlib
  karşılığını çizer (kök CLAUDE.md "önizleme DXF ile birebir" kuralı).

### Doğrulama

- Beş self-test (`collision`, `dimensions`, `axis`, `openings`, `rooms`) +
  yeni altıncı (`elevations`) — hepsi negatif ve yanlış-pozitif testli.
- `py_compile`, `validate`, `generate`, `preview`, 5 semantik kural,
  3 golden referans, `doc_check` — hepsi temiz.
- `legend` için ayrı `selftest.py` yok; doğrulaması `--golden-set`/`--rules`
  üzerinden dolaylıdır (gruplama hatası TEXT/LINE sayısına yansır).

### Golden output etkisi

- Mahal etiketi `INSERT`+`ATTRIB` oldu: ana projede 125 `TEXT`→`INSERT`+375
  `ATTRIB` (+125 entity toplamda, `METIN` layer'i +125).
- Kapı/pencere cetveli her paftaya (kapak paftası) çizgi+metin ekledi.
- `output/plan.dxf` entity sayısı ve `docs/development/plan-golden-report.json`
  ile 3 golden `expected.json` bu yüzden `--update`/`--write` ile yenilendi;
  fark açıklanabilir (yeni içerik, regresyon değil).

### Bilinen sınırlamalar

- `legend` modülünün Fikir 2'si (layer/sembol lejantı, `TitleBlockLegend`/
  `LayerSwatch`) uygulanmadı, açık fikir olarak duruyor.
- `elevations`de plandan açıklık türetme (Fikir 2) uygulanmadı.
- `elevations`de seviye sırası (zemin-altı seviyelerin listede ÖNCE gelmesi
  gerektiği) doğrulanmaz — context yanlış sıralanırsa cursor sessizce yanlış
  konum üretir.

- **Sonraki direktif:** `DEV-013` (`import/`, ileri faz) veya `DEV-014`
  (`walls/` genişletmesi) görevlerinden birini sistem mimarı açıkça
  başlatmalıdır.

## HD-008 — Ölçü zinciri, kısmi aks ve açıklık varyantları

- **Durum:** COMPLETED
- **Tamamlanma:** 2026-09-23
- **Görevler:** `DEV-017` → `DEV-015` → `DEV-016` (bu sırayla).
- **Kapsam:** `scripts/dimensions/` (bölündü + genişletildi), `scripts/axis/`
  (bölündü + genişletildi), `scripts/openings/` (bölündü + genişletildi),
  `scripts/collision/matrix.py`, `scripts/collision/selftest.py`,
  `scripts/pafta/__init__.py`, `scripts/golden_report.py`, `validate.py`,
  `generate_dxf.py`, `preview.py`, `schema/design.schema.json`,
  `context.json`, `golden/aciklik_varyantlari/` (yeni).

### Sıra neden bu

`dimensions` ÜRETİCİ, `axis` onun tek tüketicisiydi. Üretici önce
genişletilince aks, gelişmiş API'yi bir kez devraldı; tersi sırada iki kez
dokunmak gerekirdi. `openings` üçüncü seçildi çünkü rev-12'de **kendi
yazdığım bilinen sınırlamayı** kapatıyor: çakışma motoru "iki kapı birbirine
açılıyor" kontrolünü, açılım yönü schema'da olmadığı için muaf bırakmıştı.

### DEV-017 — ölçü zinciri

- `FloorOrdinates` üç kademede ordinat türetir: `aciklik` (cephedeki kapı/
  pencere kenarları), `mahal` (dik duvarların YÜZLERİ → net mahal + kalınlık),
  `toplam` (dıştan dışa). Üçü aynı ordinatlarda başlayıp biter.
- **Karar: ölçü TÜRETİLİR.** Ölçü sayısı tasarım verisi değil, geometrinin
  ölçüsüdür; elle yazmak aynı bilgiyi iki yerde tutmak olur ve ayrışır.
  Hangi kenarın ölçüleneceği ise sunum kararıdır (`meta.dimensions`).
- `ChainStack` kademelendirme yapar; `ChainLayout.verify_no_overlap` aynı
  baseline'a oturan iki zinciri artık **hata** sayar (önceden sessizce üst
  üste binerlerdi).
- **Çapraz nokta:** ölçü yığını ile aks baloncukları aynı kenarı paylaşır.
  Aks ölçü zinciri yığının DIŞINA taşındı (mimari sıra: içeride ayrıntılı,
  dışarıda kaba). İki modül birbirini import etmez; baloncuk yarıçapı
  parametre olarak verilir.
- **`CONTENT_PADDING` 3200 → 4000, ölçülerek.** İlk denemede üretim
  `PaftaOverflowError` ile durdu (`sol=300 sag=300`); artış tahminle değil,
  taşma korumasının verdiği sayıyla yapıldı. Pafta 67.0 → 70.2 cm.

### DEV-015 — kısmi/ara aks

- `Axis` tipli nesne oldu ve `extent` taşıyor. Kısmi aks kendi aralığında
  uzanır, uçlarına kendi baloncukları gelir ve **ulaşmadığı kenarın ölçü
  zincirine girmez**.
- **Karar: ara aks `1'`, `1A` değil.** Gerekçe çatışma: yatay aile zaten
  `A, B, C`; `1A` "1 ve A kesişimi" gibi okunur ve `on_axis_report`un ürettiği
  kolon adıyla (`B2`) çarpışır. Kural `naming.py`de yazılıp `validate.py`ye
  bağlandı.
- `AxisCoverageReport` salt okunur: aks'sız kolon hizalarını bildirir, aks
  EKLEMEZ.

### DEV-016 — açıklık varyantları

- Dört varyant (`single`/`double`/`sliding`/`folding`) + `swing` +
  `host_side`. **Üçünün de varsayılanı rev-12 davranışıdır.**
- **İki gerçek hata bulundu:**
  1. Açılım yayı `min/max` ile hesaplandığı için −X yönlü bir duvarda **270°**
     olurdu. `golden/minimal`da ucu ters verilmiş iki duvar zaten vardı; oraya
     bir kapı konduğu anda ortaya çıkacaktı. Yön artık çapraz çarpımla
     belirleniyor.
  2. `openings/collision.py`, `position_from_start`i açıklığın BAŞLANGICI
     sanıyordu; oysa MERKEZİDİR. Denetlenen sektör çizilen yaydan **yarım
     genişlik** (900'lük kapıda 450 mm) kayıktı. Artık boşluk aralığı çizimle
     aynı fonksiyondan (`walls.gaps_for_wall`) alınıyor.
- `geometry.py::swing_geometry` açılım yayının **tek sahibi**; çizim ve
  denetim aynı kaynaktan okur.
- Çakışma matrisinde **kapı ↔ kapı artık HATA**; sürme kapı açılım alanı
  üretmez. `rule_opening_symbols` varyant farkındası oldu ve beklenen yay
  sayısını `ARCS_PER_VARIANT` tablosundan okuyor.

### Doğrulama

- Dört self-test: `collision`, `dimensions`, `axis`, `openings` — hepsi
  negatif testlerle (kasıtlı bozma) ve yanlış-pozitif testleriyle.
- `py_compile`, `validate`, `generate`, `preview`, 5 semantik kural,
  3 golden referans, `doc_check` — hepsi temiz.
- **Yeni golden referansı `golden/aciklik_varyantlari`**: dört kapı varyantı,
  ucu ters verilmiş duvarlar, kesme işaretli kısmi aks (`2'`) ve açık ölçü
  yığını tek bir referansta birlikte sınanır.

### Golden output etkisi

`CONTENT_PADDING` değişikliği tüm paftaların bbox'ını, ölçü zincirleri ise
`minimal` dışındaki entity sayılarını değiştirdi; fark açıklanabilir olduğu
için `expected.json` dosyaları `--update` ile yenilendi.
`output/plan.dxf` 2228 → 2630 entity (+402 `DIMENSION`, layer `OLCU`).

### Bilinen sınırlamalar

- Eğik duvarlar ölçülendirmeye girmez (eksen hizalı bir zincire anlamlı
  ordinat veremezler).
- Ölçü yığını yalnızca **güney ve batı** kenarında çizilir; dört kenar için
  ayrı bir karar gerekir.
- Kısmi aks cephe izdüşümünde uygulanmaz (cephe o aksı yine de görür).
- Katlanır kapı sembolü tek kırılma noktalıdır; gerçek akordeon panel sayısı
  modellenmez.

- **Sonraki direktif:** `DEV-018` (DXF `BLOCK` yaygınlaştırma) veya `DEV-011`
  (`elevations/`) görevlerinden birini sistem mimarı açıkça başlatmalıdır.

## HD-007 — Çakışma denetimi motoru, sürüm kapısı ve provenance

- **Durum:** COMPLETED
- **Tamamlanma:** 2026-09-23
- **Kapsam:** `scripts/collision/` (yeni), `scripts/version.py` (yeni),
  `scripts/<modül>/collision.py` (5 sağlayıcı), `validate.py`,
  `generate_dxf.py`, `preview.py`, `pafta::CoverBlock`, `doc_check.py`,
  `schema/design.schema.json`, `context.json`, `golden/*`.
- **Görevler:** `DEV-019` ve `DEV-020`.

### DEV-019 — çakışma denetimi

- **Karar:** "Ayrı modül mü, her modül kendi mi" sorusu **arite** ile
  ayrıldı. Arite-1 ("kendi verim geçerli mi") ilgili modülde kaldı; arite-2+
  ("iki FARKLI eleman aynı yeri mi işgal ediyor") `scripts/collision/`
  motoruna gitti. Endüstri karşılığı: BIM'de modelleme aracı kendi disiplinini
  denetler, disiplinler arası clash ayrı bir araçtır (Navisworks *Clash
  Detective*, Solibri *Model Checker*).
- **Kritik tasarım — bağımlılık tersine çevrildi:** Motor hiçbir çizim
  modülünü import etmez; yalnızca anonim `CollisionShape(tag, id, polygon)`
  tanır. Her modül kendi ayak izini `collision.py::footprints(floor, context)`
  ile verir. Böylece **ayak izinin sahibi modül, çakışma kuralının sahibi
  motor** oldu ve modül bağımsızlığı korunurken kural tek yerde toplandı.
- **Kapının yeri:** `validate.py`, üretimden ÖNCE. Sebep hata mesajının
  dilidir: context seviyesinde rapor `f_koltuk3 ile f_koltuk2 cakisiyor
  (~1.360 m2, derinlik 850 mm)` der ve `context.json`'da düzeltilir; DXF
  seviyesinde `handle 2F4` derdi ve düzeltilemezdi.
- **Tolerans ALAN değil DERİNLİK:** 2100 mm'lik bir koltuk duvara 5 mm girse
  kesişim alanı 10500 mm² olur — alan eşiği eleman boyuyla ölçeklendiği için
  anlamsızdır. Kesişim çokgeninin kısa kenarına bakılır (`min_extent`);
  `CONTACT_TOLERANCE = 5 mm` altındaki girişim **temas**tır.
- **`golden_report.py`ye EKLENMEDİ:** Golden "çıktı değişti mi", çakışma
  "tasarım doğru mu" sorar. Birleştirilseydi bir golden referansı asla kasıtlı
  çakışma içeremezdi ve motorun kendisi test edilemezdi.
- **Yan kazanç — kopya kaldırıldı:** Sutherland–Hodgman kırpmasının bir
  KOPYASI `validate.py` içinde duruyordu. `collision/geometry.py` poligon
  matematiğinin tek sahibi oldu; iki kopya ayrışsa "oda çakışması" ile "tefriş
  çakışması" farklı cevaplar vermeye başlardı.

### DEV-020 — sürüm uyumu

- **Karar:** Kullanıcı modül bazlı eğilimini bildirdi; ayrım **amaca göre**
  yapıldı. **Sürümlenecek şey kod değil SÖZLEŞMEDİR** — rev-11'de `furniture/`
  beş dosyaya bölündü, etkilenen proje sıfır; oysa `furniture[].position`
  yeniden adlandırılsa her proje kırılır. Modül bazlı semver bir **paket
  deposunun** modelidir (bağımsız yayın temposu gerekir); burada modüller tek
  commit'te birlikte gider.
- **Sonuç:** `meta.schema_version` **kapı** (MAJOR farkta üretim durur, modül
  sözleşmelerinin türevi), modül `CONTRACT_VERSION` **teşhis**,
  `output/provenance.json` **kayıt**. İstenen şey aslında teşhisti ("koptu mu,
  neden") ve onu provenance yanıtlar, versioning değil.
- **Migrasyon asla otomatik değil:** otomatik migrasyon
  `requests.jsonl`/`rev_history` zincirini kırar ve provenance yalan söylemeye
  başlar. Major kırılımda proje normal bir revizyon olarak güncellenir.
- **Kademeli giriş:** alan bugün opsiyonel (yoksa `1.0.0` + uyarı); tüm
  context'ler taşıdıktan sonra `required` yapılacaktır.

### Kapak (kullanıcı talebi, `DEV-007`in çözülen kısmı)

- İmza alanları dörde sabitlendi: **MİMAR / BELEDİYE / YETKİLİ 1 / YETKİLİ 2**
  (2×2 yerleşim). Daha önce ikisi boş (`(UNVAN)`) bırakılmıştı.
- Kapak eteğine **üretim damgası** eklendi: solda `URETIM: <tarih saat>`,
  sağda `SISTEM: <schema sürümü>`. Damga, bilgi satırlarındaki `TARIH` ile
  AYNI ŞEY DEĞİLDİR — o proje/onay tarihidir, context'ten gelir ve uydurulmaz.
  Damga imza bandının altındaki boş şeride (iç çerçeveden 10 mm) oturur;
  ölçülerek doğrulandı (imza bandı alt kenarı −7850, damga −8350, iç çerçeve
  −8850 → her iki yandan 10'ar mm).
- `preview.py` aynı yerleşimi birebir yansıtır.

### Doğrulama

- `python scripts/collision/selftest.py` — kasıtlı bozulmuş katta tam 3 HATA
  + 1 UYARI; yanlış-pozitif testi ayrıca geçti. Kesişim ölçüsü elle
  doğrulanabilir (800 × 750 = 600000 mm², derinlik 750).
- Boru hattı negatif testleri: çakışma → `exit 1`, oda dışı → `exit 1`,
  MAJOR sürüm farkı → `exit 1`, MINOR fark → `exit 0` + uyarı.
- `doc_check.py`ye üç yeni kontrol eklendi (çakışma kapsamı, bayat
  `COLLISION_EXEMPT`, sözleşme sürümü); **üçü de kasıtlı bozmayla** sınandı.
- `validate` + `generate` + 5 semantik kural + 2 golden referans temiz.

### Golden output etkisi

Kapak altbilgisi her paftaya değil yalnızca kapağa eklendiği için her golden
referansında **tam +2 `TEXT`** (layer `METIN`) farkı oluştu; `modelspace_bbox`
değişmedi. Fark birebir açıklanabildiği için `expected.json` dosyaları
`--update` ile yenilendi (`minimal` 111→113, `tefris_kolon` 176→178).

### Bilinen sınırlamalar

- Çakışma yalnızca AYNI kat içinde aranır; katlar arası düşey hizalama
  denetlenmez.
- Kapı açılım **yönü** schema'da yok; iki kapının birbirine açılması bu yüzden
  `IGNORE` bırakıldı ve `DEV-016` sonrası `FORBID`e çekilmelidir.
- `counters[]` ayak izi üretmez (hâlâ `generate_dxf.py` içinde ad-hoc).
- Kapı sektörü 8 doğru parçasıyla yaklaşılır; gerçek yaydan biraz küçüktür.

- **Sonraki direktif:** Sistem mimarı `DEV-018` (DXF `BLOCK` yaygınlaştırma)
  veya `DEV-011` (`elevations/`) görevlerinden birini açıkça başlatmalıdır.

## HD-006 — Golden fixture kataloğu, tefriş modülü ve taralı kolonlar

> **rev-11 terminoloji notu:** Bu kayıttaki "fixture" artık **golden referans
> projesi** olarak adlandırılır; dizin `fixtures/` → `golden/`, beklenti dosyası
> `golden.json` → `expected.json`, CLI `--fixtures` → `--golden-set` oldu. Kayıt
> tarihsel olduğu için metni yeniden yazılmadı.

- **Durum:** COMPLETED
- **Tamamlanma:** 2026-09-23
- **Kapsam:** `scripts/golden_report.py` (yeniden yazıldı), yeni
  `scripts/furniture/`, yeni `scripts/columns/`, `scripts/generate_dxf.py`,
  `schema/design.schema.json`, `fixtures/` (rev-11'de `docs/` altından
  proje köküne taşındı).
- **Sonuç — DEV-006:** Golden kontrolü üç katmanlı oldu: ölçüm raporu +
  semantik kurallar + fixture koşucusu. Beş kural eklendi ve hepsi negatif
  testle doğrulandı. `entity_bbox` gerçek extent hesabına geçti; önceki sürüm
  `INSERT` için yalnızca ekleme noktasını döndürdüğü için bloklara geçişte
  rapor sessizce körleşecekti. İki fixture: `minimal`, `tefris_kolon`.
- **Sonuç — DEV-009:** 22 tipli konut tefriş kataloğu; tefriş her zaman DXF
  `BLOCK`. Beş işlevsel grup, her birine kahverengi ailesinden düşük
  kontrastlı layer rengi. Kapı/pencere sahipliği araştırıldı ve
  `openings/`+`walls/`ta kalmasına karar verildi (IFC ve AIA/NCS layer
  standardı).
- **Sonuç — DEV-010:** Taralı kolon; desen/ölçek dinamik, varsayılan
  `ANSI33` + `3.0`. Kesit kataloğu, dairesel/dikdörtgen kesit, dönme.
  İsimlendirme altyapısı hazır ama varsayılan kapalı; `meta.column_label`
  ile kod değişmeden açılıyor. `on_axis_report` kolonu aks kesişimiyle
  eşleyen salt-okunur rapor üretiyor.
- **Doğrulama:** `py_compile`, `validate.py`, `generate_dxf.py`,
  `preview.py`, golden karşılaştırması ve her iki fixture başarılı. Beş
  semantik kural tek tek bozularak yakaladıkları teyit edildi. Tefriş
  bloklarının yeniden kullanımı ölçüldü: 19 tanım → 23 `INSERT`. Hatch
  parametreleri (`ANSI33`, ölçek 3.0) ve grup renkleri DXF'ten okunarak
  doğrulandı.
- **Fixture'ların ilk günde yakaladığı iki gerçek sorun:** (1) Kapak
  paftasının projeye dayattığı asgari yükseklik (1:50'de içeriğin düşey
  açıklığı ≥ 8150 olmalı) — belgelenmemişti; (2) `draw_floor_sheet` içinde
  mahal etiketi `label_style` yerelinin kolon `label_style` parametresini
  gölgelemesi.
- **Golden output etkisi:** Gerçek proje çıktısı DEĞİŞMEDİ — tefriş ve kolon
  verisi `context.json`a eklenmedi (yerleşim proje verisidir ve uydurulmaz).
  Yetenekler `tefris_kolon` fixture'ında doğrulanır.
- **Açık sınır:** Tefriş/kolon için çakışma ve oda-içinde-kalma kontrolü YOK;
  kapı açılım alanı ile tefriş çakışması denetlenmiyor. `counters[]` hâlâ
  `generate_dxf.py` içinde ad-hoc çiziliyor. Katlar arası kolon hizalaması
  kontrol edilmiyor.
- **Sonraki direktif:** `DEV-018` (DXF `BLOCK` yaygınlaştırma — mahal etiketi
  bloğu/`ATTRIB`) veya `DEV-011 elevations` sistem mimarı onayıyla
  başlatılabilir.

## HD-005 — 3 satırlı mahal etiketi ve `typography` modülü

- **Durum:** COMPLETED
- **Tamamlanma:** 2026-09-23
- **Kapsam:** yeni `scripts/typography/`, `scripts/rooms/`,
  `scripts/pafta/` (font kaynağı), `scripts/generate_dxf.py`,
  `scripts/validate.py`, `schema/design.schema.json`, `context.json`.
- **Sonuç:** Mahal etiketi kullanıcı şartnamesine göre **3 satır** oldu
  (mahal adı BLOK / kat kodu-mahal no / alan). Kat kodu `floors[].code`'dan,
  mahal no `rooms[].no`'dan gelir; ikisi de türetilmez. Sığdırma artık hem
  genişliğe hem **yüksekliğe** bakıyor. Proje fontu Arial Narrow'a geçti:
  yeni `typography` modülü fontu `Standard` text style'ına yazarak tek
  noktadan tüm metinlere uyguluyor, `pafta.DEFAULT_FONT` ise ikinci bir sabit
  tutmak yerine bu modülden import ediyor (çizilen font ile ölçülen fontun
  ayrışması engellendi). `meta.fonts.room_label` ile mahal etiketine ayrı
  font seçilebilir.
- **Doğrulama:** `py_compile`, `validate.py`, `generate_dxf.py`,
  `preview.py` ve semantic golden karşılaştırması başarılı. **125/125 mahal
  etiketinin** gerçek font metrikleriyle ölçülen bounding box'ı kendi oda
  poligonunun içinde kaldı. Mahal no ve kat kodu benzersizlik kontrolleri
  `validate.py`ye eklendi ve negatif testle (kasıtlı çakışma) doğrulandı.
  `arialn.ttf` ile `arial.ttf` ölçümlerinin farklı olduğu, `"ArialNarrow"`
  aile adının ise sessizce Arial'e düştüğü ölçülerek teyit edildi.
- **Golden output etkisi:** TEXT 339 → 589 (+250 = 125 oda × 2 ek satır),
  `METIN` layer 177 → 427, toplam entity 1976 → 2226. Geometri (duvar,
  açıklık, aks, çerçeve) değişmedi.
- **Açık sınır:** `RoomLabelStyle` Protocol'ü ve leader'lı yerleşim
  uygulanmadı (kullanıcı fikirlerden birini seçmedi, şartname doğrudan
  uygulandı). Arial Narrow bir TTF'tir; çizimi açan makinede font yoksa
  metin genişlikleri kayar — bu bilinen bir sınırdır.
- **Sonraki direktif:** `DEV-006 Golden fixture kataloğu` (amacı rev-9'da
  genişletildi) veya `DEV-009 tefriş modülü` sistem mimarı onayıyla
  başlatılabilir.

## HD-004 — Tip-A kapak paftası (`CoverBlock`) ve `Sheet` özel-pafta desteği

- **Durum:** COMPLETED
- **Tamamlanma:** 2026-09-23
- **Kapsam:** `scripts/pafta/` (`CoverBlock`, `Sheet.draw` genişletmesi),
  `scripts/generate_dxf.py`, `scripts/preview.py`, `schema/design.schema.json`.
- **Sonuç:** ISO 7200 Tip-A kapak bloğu `CoverBlock` olarak uygulandı; ölçüler
  `to_modelspace(...)` ile projenin ölçeğinden türetilir, böylece kapak ölçekli
  çıktıda her zaman tam A4 (210x297mm) basar. Kapak paftası **özel pafta**
  olarak tanımlandı: dış çerçeve genişliği kapak genişliğine eşittir
  (`padding=0`), blok paftanın sağ-altına sabitlenir, Tip-B şerit anteti
  çizilmez ve kapak çerçevesi her kenardan eşit offsetlidir. `Sheet.draw`
  bunun için `title_box`, `padding` ve `frame_gap` override'ları aldı;
  `CoverBlock.draw` ise `outer_frame` parametresiyle çift çizimi önler.
  `schema`ya `meta.cover` eklendi (`architect_name`, `date`,
  `signature_fields`).
- **Doğrulama:** `py_compile`, `python scripts/validate.py`,
  `python scripts/generate_dxf.py`, `python scripts/preview.py` ve semantic
  golden karşılaştırması başarılı. Ek olarak DXF geometrisi üzerinden 9
  otomatik kontrol (pafta genişliği = kapak genişliği, A4 panel ölçüsü, eşit
  offset, antet yokluğu, pafta bitişikliği, ortak yükseklik, çift çizim
  olmaması) ve 4 farklı ölçekte (1:20/1:50/1:100/1:200) "çıktıda 210x297mm"
  doğrulaması yapıldı. 1:200 ile kapak paftaya sığmadığında üretimin
  `PaftaOverflowError` ile durduğu, sessiz hatalı DXF üretilmediği test edildi.
- **Golden output etkisi:** `output/plan.dxf` yeniden üretildi ve semantic
  golden raporu güncellendi; mevcut kat planı/görünüş geometrisi korunmuştur.
- **Açık sınır:** Kapağın resmi verisi (`architect_name`, `date`, ayrılmış iki
  imza alanının unvanı) kullanıcıdan gelmedi; uydurulmadı, elle doldurulacak
  çizgi olarak bırakıldı (`DEV-007`). Kapak **tasarımı** için kullanıcı ayrı
  bir talep paylaşacak — o talepte geometri (A4, sağ-alt sabitleme, eşit
  offset, antetsiz pafta) değişmemelidir. Çok küçük ölçeklerde kapak bloğu
  için otomatik yeniden yerleşim stratejisi yoktur; yalnızca taşma hatası
  verilir.
- **Sonraki direktif:** `DEV-006 Golden fixture katalogu` görevini sistem
  mimarı onayıyla başlatmak; `DEV-008 RoomLabeler yapısı` PLANNED olarak
  beklemektedir.

## HD-002 — Agentic kontrol ve kabul altyapısı

- **Durum:** COMPLETED
- **Tamamlanma:** 2026-09-23
- **Kapsam:** görev kilidi, rol izinleri, reviewer ayrımı, provenance ve
  semantic golden-output raporu.
- **Sonuç:** `development_control.py` atomik görev kilidi sağlar;
  `AGENT_PERMISSIONS.json` rol alanlarını tanımlar; `PROVENANCE_TEMPLATE.json`
  revizyon izini standartlaştırır; `golden_report.py` entity türleri, layer,
  bounding box ve hash raporu üretir.
- **Doğrulama:** Python derlemesi ve kilit aracının `status` smoke testi
  başarılıdır. Proje validation/generation davranışı değiştirilmemiştir.
- **Golden output etkisi:** Mevcut `output/plan.dxf` için ilk semantic referans
  raporu oluşturulacaktır; byte hash tek kabul ölçütü değildir.
- **Bilinen durum:** OS seviyesinde klasör izinleri değil, proje içi agent
  protokolü ve görev kilidi uygulanır. Sistem dışı yetki mekanizması sonraki
  deployment kararıdır.
- **Sonraki direktif:** Sistem mimarı onayıyla `DEV-001 openings` görevini
  kilit alarak başlatmak.

## HD-003 — Openings, Rooms ve Dimensions modülleri

- **Durum:** COMPLETED
- **Tamamlanma:** 2026-09-23
- **Kapsam:** `scripts/openings/`, `scripts/rooms/`,
  `scripts/dimensions/` ve Axis/Wall/Generator entegrasyonları.
- **Sonuç:** Typed opening görünümü ve schedule, host-wall/açıklık genişliği
  doğrulaması, units-aware room alan/self-intersection doğrulaması,
  `RoomLabeler`, `DimensionChain`, `LinearDim`, `DimensionStyle` ve bounds
  kontrollü `ChainLayout` uygulandı.
- **Doğrulama:** package import, `py_compile`, `python scripts/validate.py`,
  `python scripts/generate_dxf.py` ve semantic golden karşılaştırması başarılı.
- **Golden output etkisi:** `output/plan.dxf` entity/layer/bbox semantic raporuyla
  eşleşti; mevcut örnek geometrisi korunmuştur.
- **Açık sınır:** Swing/variant/host_wall_id gibi yeni schema alanları
  eklenmedi; mevcut `wall_id` sözleşmesi korunmuştur.
- **Sonraki direktif:** `DEV-006 Golden fixture katalogu` görevini sistem
  mimarı onayıyla başlatmak.

## HD-001 — AxisGrid modül izolasyonu

- **Durum:** COMPLETED
- **Tamamlanma:** 2026-09-22
- **Kapsam:** `scripts/axis/` ve `scripts/generate_dxf.py`
- **Sonuç:** `AxisGrid`, `AxisDrawingStandard` ve `ensure_axis_layer`
  generator içinden izole modüle taşındı. Floor/elevation izdüşümü, baloncuk
  teğetliği, sabit AKS layer standardı ve geçici ölçü zincirleri korundu.
- **Doğrulama:** `py_compile` başarılı; `python scripts/validate.py` başarılı;
  `python scripts/generate_dxf.py` başarılı.
- **Golden output etkisi:** `output/plan.dxf` validate edilmiş pipeline ile
  yeniden üretildi. İlk anlamlı entity/geometri golden karşılaştırması sonraki
  kalite çalışmasında ayrıca otomatikleştirilecek.
- **Bilinen durum:** Örnek proje, sistem geliştirmesi öncesinde üretildiği için
  1:100 ölçek mevzuat uyarısı taşır. Bu tarihsel örnek durumudur ve sistem
  mimarisini bloke etmez.
- **Sonraki direktif:** `openings/` sözleşmesini sistem mimarı onayıyla
  uygulama fazına almak.
