# Tamamlanan Geliştirmeler Geçmişi

Aktif geçmiş kapasitesi: **50 kayıt**. En eski tamamlanmış kayıt, 51. kayıt
alınırken silinir. Ayrıntılı teknik değişiklikler git geçmişi ve ilgili proje
provenance kayıtlarıyla ilişkilendirilir.

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
