# Geliştirme Görev Kuyruğu

Bu dosya sistem geliştiricisinin sıradaki kontrollü işini gösterir. Aynı anda
tek bir görev `IN_PROGRESS` olabilir. Sistem mimarı `READY` görevi başlatır;
agent kendi başına sıra değiştirmez.

**Bu dosya BİRİNCİL OLARAK yapılacak (PLANNED/BLOCKED) görevleri barındırır.**
Tamamlanan işlerin ayrıntılı gerekçesi, karar süreci ve ölçülen etkisi
`DEVELOPMENT_HISTORY.md`dedir — buradaki `## COMPLETED` bölümü kasıtlı olarak
1-2 cümlelik bir özet + `HD-xxx` atfından ibarettir, tekrar anlatmaz.

## Durum özeti

| Görev | Modül | Durum |
| ----- | ----- | ----- |
| DEV-001 | `openings/` | COMPLETED |
| DEV-002 | `rooms/` | COMPLETED |
| DEV-003 | `dimensions/` | COMPLETED |
| DEV-004 | golden output | COMPLETED |
| DEV-005 | agentic kontrol | COMPLETED |
| DEV-006 | golden fixture kataloğu | COMPLETED (rev-10) |
| DEV-007 | `pafta/` | **BLOCKED** — yalnızca mimar adı / proje tarihi |
| DEV-008 | `rooms/` etiket | COMPLETED (rev-9) |
| DEV-009 | `furniture/` | COMPLETED (rev-10) |
| DEV-010 | `columns/` | COMPLETED (rev-10) |
| DEV-011 | `elevations/` | COMPLETED (rev-14) |
| DEV-012 | `legend/` | COMPLETED (rev-14) |
| DEV-013 | `importer/` | COMPLETED (rev-15) |
| DEV-014 | `walls/` | COMPLETED (rev-15) |
| DEV-015 | `axis/` | COMPLETED (rev-13) |
| DEV-016 | `openings/` | COMPLETED (rev-13) |
| DEV-017 | `dimensions/` | COMPLETED (rev-13) |
| DEV-018 | DXF `BLOCK` (modüller arası) | COMPLETED (rev-14) |
| DEV-019 | `collision/` (modüller arası) | COMPLETED (rev-12) |
| DEV-020 | sürüm + provenance | COMPLETED (rev-12) |
| DEV-021 | `sections/` — kesit modülü | COMPLETED (rev-17) |
| DEV-022 | `stairs/` — merdiven gerçek geometrisi | COMPLETED (2026-09-25) |
| DEV-023 | `ceiling/` — yansıtılmış tavan planı | PLANNED |
| DEV-024 | `site/` — vaziyet planı | PLANNED |
| DEV-025 | Kuzey oku (+ grafik ölçek çubuğu, rev-18'de geri alındı) | COMPLETED (rev-17) |
| DEV-026 | `legend/` — alan hesap cetveli | PLANNED |
| DEV-027 | Kaçış (tahliye) planı | PLANNED |
| DEV-028 | `legend/` — malzeme/kaplama cetveli | PLANNED |
| DEV-029 | Kot (seviye/datum) yönetim mantığı — proje geneli | COMPLETED (2026-09-25) |
| DEV-030 | Katman renk organizasyonu (modüller arası) | COMPLETED (2026-09-25) |

## READY

**Şu anda `READY` durumda görev YOKTUR.** Sistem mimarı aşağıdaki `##
PLANLANAN GÖREVLER` bölümünden bir maddeyi açıkça seçip başlatmalıdır; agent
kendi başına seçmez.

> `DEV-007` kullanıcı talimatıyla (rev-12) **konusu açılmadan** plan olarak
> bekleyecektir; agent bu madde için veri İSTEMEZ. İmza alanları rev-12'de
> çözüldü (MİMAR / BELEDİYE / YETKİLİ 1 / YETKİLİ 2); geriye yalnızca mimar
> adı ve proje tarihi kaldı ve bunları kullanıcı kendisi verecektir.

## PLANLANAN GÖREVLER

Planlanmış modül kataloğunun tamamı (`DEV-011`…`DEV-020`) tamamlandı. Bu
bölüm artık üç tür maddeyi tutar:

1. **`DEV-007`** — tek gerçek BLOCKED madde, yukarıya bakınız.
2. **`DEV-023`…`DEV-028`** — 2026-09-24'te (kullanıcı talebiyle) eklenen,
   **endüstri standardı bir mimari çizim setinde bulunan ama bu projede
   henüz olmayan** modül/geliştirme fikirleri (`DEV-021`/`DEV-025` rev-17'de,
   `DEV-022` 2026-09-25'te seçilip tamamlandı, bkz. `## COMPLETED`). Bunlar
   bir mimarın
   ufkunu açmak ve gerçekten gözden kaçan bir şey olup olmadığını
   değerlendirmek için yazılmıştır — **uygulama izni DEĞİLDİR**. Her biri
   `PLANNED` seviyesinde bir taslaktır; gerçek Fikir 1/Fikir 2/Açık kararlar
   analizi (mevcut modüllerdeki gibi) o madde açıkça seçildiğinde yapılır.
   Sistem mimarı bir maddeyi seçip kendi yönlendirmesini eklemeden agent
   kod yazmaz.
(`DEV-029` — kot/datum yönetim mantığı — ve `DEV-030` — katman renk
organizasyonu — 2026-09-25'te seçilip tamamlandı, bkz. `## COMPLETED`.)

**Şartname ile fikir farkı:** Bir maddede "Şartname" başlığı varsa, o kısım
kullanıcı tarafından KESİN olarak verilmiştir ve fikir gibi değerlendirilmez.

### DEV-007 — `pafta/` — kapak verisi ve pafta altyapısı

- **Durum:** BLOCKED — çizim tarafında yapılacak iş kalmadı, yalnızca
  kullanıcıdan gelecek resmi veri bekleniyor.
- **Mevcut durum:** Tip-A kapak çizimi/yerleşimi tamamlandı (`CoverBlock`,
  bkz. `HD-004`). Eksik olan yalnızca resmi veridir (`meta.cover.
  architect_name`, `meta.cover.date`). Ayrıca `PaperSizePlanner`, 90'lık
  ruloya sığmayan bir proje için "pafta bölme + keyplan" gerektiğini
  raporluyor ama bu henüz uygulanmadı (bkz. `DEV-024`ün vaziyet/keyplan
  notu).
- **Fikir 1 — Pafta bölme + keyplan:** En büyük rulo yetmediğinde mevzuatın
  tek kabul ettiği çözüm. `PaperSizePlanner.select(...)` zaten `fits=False`
  döndürdüğü için tetikleme noktası hazır.
- **Fikir 2 — Uniform sheet template:** Paftayı gerçek standart kağıt
  boyutuna oturtmak; DIN/ISO 5457 Tip-B ölçüsü ve sayfa marjları (sol 20mm,
  diğer 10mm) tam uygulanabilir hale gelir.
- **Açık kararlar:** Kapak **tasarımı** için kullanıcı ayrı bir talep
  paylaşacak; o talepte geometri (A4, sağ-alt sabitleme, eşit offset,
  antetsiz pafta) değişmemelidir.

### DEV-023 — `ceiling/` — yansıtılmış tavan planı (RCP)

- **Durum:** PLANNED

**Neden endüstri standardı bir boşluk:** Tavan planı (Reflected Ceiling
Plan), kat planından AYRI ve standart bir pafta türüdür — tavan kotu
farklılıkları (asma tavan, kot farkı), aydınlatma armatür yerleşimi ve
tavan malzemesi gösterir. Bugün sistemde `floors[]` yalnızca zemin
düzlemini (oda poligonu + duvar + tefriş) biliyor; tavan hiç modellenmiyor.

**Kapsam taslağı:** En basit sürüm, mevcut oda poligonlarını (`rooms[]`)
yeniden kullanıp üstüne tavan kotu + malzeme etiketi + (opsiyonel)
aydınlatma noktası yerleşimi ekler — `rooms/` ve `furniture/`nin
"katalog + yerleşim" deseniyle aynı yapıda olabilir (armatür bir tefriş
kataloğu gibi ele alınabilir).

**İlişkili modüller:** `rooms/` (poligon paylaşılır), `furniture/`
(armatür yerleşimi aynı desen), `legend/` (armatür lejantı).

### DEV-024 — `site/` — vaziyet planı

- **Durum:** PLANNED

**Neden endüstri standardı bir boşluk:** `scripts/pafta::PaperSizePlanner`
zaten `VAZIYET_PLANI` proje tipini (1:200/1:500 ölçek kısıtıyla) TANIYOR —
ama bu ölçekte gerçekten çizilen bir vaziyet planı YOK. Vaziyet planı
(parsel sınırı, yapı yaklaşma sınırları/çekme mesafeleri, bina oturumu,
kuzey oku, komşu parseller) Türkiye imar mevzuatında ruhsat evrakının
AYRILMAZ bir parçasıdır ve bugünkü kat planlarından farklı, daha küçük bir
ölçekte, farklı bir veri kümesiyle (parsel geometrisi, çekme mesafeleri)
çizilir.

**Kapsam taslağı:** `meta.parcel` gibi yeni bir üst-seviye alan (parsel
poligonu, çekme mesafeleri, kuzey açısı) + binanın mevcut `floor_width`/
`floor_depth` oturumunun bu parsel içine 1:200/1:500 ölçekte yerleştirilmesi.
`DEV-025` (tamamlandı) `scripts/northarrow::NorthArrow`i burada da
kullanır — `meta.north_angle` zaten var, yeni bir kuzey oku mantığı
YAZILMAZ.

**İlişkili modüller:** `pafta/` (yeni bir pafta türü — `PaperSizePlanner`
zaten ölçek kısıtını biliyor), `axis/` (bina oturumu aynı ızgara),
`northarrow/` (tamamlandı — kuzey oku doğrudan yeniden kullanılır).

### DEV-026 — `legend/` genişletmesi: alan hesap cetveli (brüt/net, emsal)

- **Durum:** PLANNED

**Neden endüstri standardı bir boşluk:** Türkiye imar mevzuatında (emsal/
KAKS hesabı) her katın ve toplam binanın brüt/net alan tablosu ruhsat
evrakının standart bir parçasıdır. `rooms[].area_m2` verisi PROJEDE ZATEN
VAR ve doğrulanıyor (`validate.py` alan-poligon tutarlılığını kontrol
ediyor) — sadece bir ÖZET TABLO olarak toplanıp çizilmiyor.

**Kapsam taslağı:** `legend/`nin zaten kurduğu desenin (`OpeningLegend` →
proje çapında gruplama + `LegendRenderer` → çizgi/metin tablosu) ÜÇÜNCÜ bir
tüketicisi: kat başına ve toplamda net alan (odaların toplamı) + brüt alan
(dış duvar dıştan-dışa alanı, `dimensions::FloorOrdinates`in `toplam`
kademesiyle aynı geometriden türetilebilir). Yeni bir modül GEREKMEZ —
`legend/`nin kendisi genişler.

**İlişkili modüller:** `rooms/` (alan verisi), `dimensions/` (dıştan-dışa
ölçü zaten türetiliyor), `legend/` (tablo çizim altyapısı hazır).

### DEV-027 — Kaçış (tahliye) planı / yangın güvenliği

- **Durum:** PLANNED

**Neden endüstri standardı bir boşluk:** Bu proje çok katlı + otopark +
ticari zemin kat içeren bir bina modelliyor — bu ölçekte bir binanın
Türkiye'de (Binaların Yangından Korunması Hakkında Yönetmelik) bir kaçış
(tahliye) planı bulundurması standarttır: kaçış yönü okları, yangın
merdiveni/asansör vurgusu, toplanma noktası. Bugün sistemde bu bilgi
KATMANI hiç yok.

**Kapsam taslağı:** Mevcut kat geometrisi (oda + koridor + merdiven
konumu, zaten `rooms`/`walls`te var) üzerine bir OVERLAY: kaçış yönü okları
+ zaten var olan merdiven/asansör odalarının vurgulanması. Yeni geometri
ÜRETMEZ, mevcut plan üzerine anotasyon ekler — `dimensions`/`legend`
katmanlarıyla aynı "anotasyon, geometri değil" sınıfında.

**İlişkili modüller:** `rooms/`+`walls/` (koridor/merdiven konumu zaten
biliniyor), `legend/` (sembol açıklaması).

### DEV-028 — `legend/` genişletmesi: malzeme/kaplama (finish) cetveli

- **Durum:** PLANNED

**Neden endüstri standardı bir boşluk:** Zemin/duvar/tavan kaplama cetveli
(hangi mahalde hangi malzeme — seramik, parke, sıva vb.), kapı/pencere
cetveliyle (`DEV-012`) AYNI ailede, mimari uygulama projesinin standart bir
parçasıdır. Bugün `rooms[]`in bir malzeme alanı yok.

**Kapsam taslağı:** `rooms[]`e opsiyonel `finish` alanı (zemin/duvar/tavan
malzeme kodu) eklenip, `legend/`nin AYNI gruplama+tablo deseniyle (bkz.
`DEV-012`, `DEV-026`) bir malzeme cetveli üretilmesi. Yeni modül GEREKMEZ.

**İlişkili modüller:** `rooms/` (şema genişlemesi), `legend/` (tablo
altyapısı hazır).

## COMPLETED

> Ayrıntılı gerekçe, karar süreci, bulunan gerçek hatalar ve ölçülen etki
> için her maddenin işaret ettiği `DEVELOPMENT_HISTORY.md` kaydına bakınız.
> Buradaki özetler KASITLI olarak 1-2 cümledir.

### DEV-001 — Openings modülünü oluştur

- **Durum:** COMPLETED
- **Özet:** Typed `Opening`/`Door`/`Window`/`OpeningSchedule` + enjekte
  edilebilir stil `scripts/openings/`e taşındı. (`HD-003`)

### DEV-002 — Room modülü

- **Durum:** COMPLETED
- **Özet:** `Room`, `PolygonOps`, `RoomLabeler` ve scanner
  `scripts/rooms/`e taşındı; kapanış/alan/self-intersection doğrulaması
  eklendi. (`HD-003`)

### DEV-003 — DimensionChain modülü

- **Durum:** COMPLETED
- **Özet:** `DimensionChain`/`LinearDim`/`ChainLayout` `scripts/dimensions/`e
  taşındı; `AxisGrid` gerçek DXF ölçülerini bu API ile üretir. (`HD-003`)

### DEV-004 — Golden output anlamsal karşılaştırması

- **Durum:** COMPLETED
- **Özet:** `scripts/golden_report.py` entity/layer/bbox/SHA-256 ölçüm
  raporu üretip `--compare` ile karşılaştırıyor. (`HD-002`)

### DEV-005 — Agentic kontrol altyapısı

- **Durum:** COMPLETED
- **Özet:** `development_control.py` atomik görev kilidi,
  `AGENT_PERMISSIONS.json` ve `PROVENANCE_TEMPLATE.json` eklendi. (`HD-002`)

### DEV-006 — Golden fixture kataloğu

- **Durum:** COMPLETED (rev-10)
- **Özet:** `golden_report.py` üç katmanlı oldu (ölçüm + semantik kural +
  fixture koşucusu); ilk fixture'lar bir pafta-yükseklik sınırını ve bir
  isim-çakışması hatasını gerçekten yakaladı. (`HD-006`)

### DEV-008 — `rooms/` — 3 satırlı mahal etiketi (`RoomLabeler`)

- **Durum:** COMPLETED (rev-9)
- **Özet:** Şartname birebir uygulandı (3 satır: ad/kat kodu-no/alan,
  Arial Narrow, genişlik+yükseklik sığdırma); 125/125 oda doğrulandı.
  (`HD-005`)

### DEV-009 — `furniture/` — tefriş modülü

- **Durum:** COMPLETED (rev-10)
- **Özet:** 22 tipli tefriş kataloğu, her tefriş DXF `BLOCK`/`INSERT`;
  kapı tefriş SAYILMADI (duvar açıklığı, endüstri standardı gerekçesiyle).
  (`HD-006`)

### DEV-010 — `columns/` — kolon modülü

- **Durum:** COMPLETED (rev-10)
- **Özet:** Taralı kolon (`ANSI33`/`3.0`), kesit kataloğu,
  `on_axis_report`; isimlendirme altyapısı hazır ama varsayılan kapalı.
  (`HD-006`)

### DEV-011 — `elevations/` — cephe modülü

- **Durum:** COMPLETED (rev-14)
- **Özet:** `draw_elevation` kendi modülüne taşındı; `below_ground`
  seviyeler artık gerçekten `DASHED` linetype ile çiziliyor. (`HD-009`)

### DEV-012 — `legend/` — lejant ve cetveller

- **Durum:** COMPLETED (rev-14)
- **Özet:** Kapı/pencere cetveli (`OpeningLegend`/`LegendRenderer`), kapak
  paftasının boş üst alanına çiziliyor. (`HD-009`)

### DEV-013 — `importer/` — mevcut çizimden veri okuma

- **Durum:** COMPLETED (rev-15)
- **Özet:** `DxfWallScanner`, mevcut bir DXF'ten confidence skorlu duvar
  adayı çıkarır (salt-okunur); `import/`den `importer/`e yeniden
  adlandırıldı (Python anahtar kelimesi çakışması). (`HD-010`)

### DEV-014 — `walls/` — duvar çizim standardı genişletmesi

- **Durum:** COMPLETED (rev-15)
- **Özet:** `CatalogRailStandard`, `tugla_bolme` için hatch, `cam_duvar`
  için farklı linetype ekliyor; şemaya eksik olan `wall.kind` alanı
  eklendi. (`HD-010`)

### DEV-015 — `axis/` — aks sistemi genişletmesi

- **Durum:** COMPLETED (rev-13)
- **Özet:** Kısmi/ara aks (`extent`, `1'` etiketi) ve kolon-rasteri
  kapsama raporu eklendi. (`HD-008`)

### DEV-016 — `openings/` — açıklık varyantları

- **Durum:** COMPLETED (rev-13)
- **Özet:** 4 kapı varyantı + `swing`/`host_side`; bu sırada iki gerçek
  çizim hatası (270° yay, yarım genişlik kayık çakışma sektörü) bulunup
  düzeltildi. (`HD-008`)

### DEV-017 — `dimensions/` — ölçülendirme genişletmesi

- **Durum:** COMPLETED (rev-13)
- **Özet:** Türetilmiş 3 kademeli ölçü zinciri (açıklık/mahal/toplam) +
  deterministik kademelendirme. (`HD-008`)

### DEV-018 — DXF `BLOCK` entity kullanımı (modüller arası)

- **Durum:** COMPLETED (rev-14)
- **Özet:** Mahal etiketi `MAHAL_ETIKET` bloğu + `ATTRIB` oldu; tefriş
  zaten `DEV-009`da bloktu. (`HD-009`)

### DEV-019 — Çakışma denetimi (`scripts/collision/`)

- **Durum:** COMPLETED (rev-12)
- **Özet:** Çakışma denetimi arite ile ayrıldı: tekil kontrol modülde,
  çift kontrol bağımsız `scripts/collision/` motorunda (hiçbir çizim
  modülünü import etmez). (`HD-007`)

### DEV-020 — Proje ↔ sistem sürüm uyumu

- **Durum:** COMPLETED (rev-12)
- **Özet:** `meta.schema_version` kapı, modül `CONTRACT_VERSION` teşhis,
  `output/provenance.json` kayıt olarak üçe ayrıldı. (`HD-007`)

### DEV-021 — `sections/` — bina kesiti

- **Durum:** COMPLETED (rev-17)
- **Özet:** Kesit hattı her zaman aks ailesine paralel; veri verilmezse
  X+Y'den birer varsayılan kesit (1/3 nokta) üretilir; plana kesit
  hattı+üçgen+harf işareti basılır. (`HD-011`)

### DEV-025 — Kuzey oku ve grafik ölçek çubuğu

- **Durum:** COMPLETED (rev-17)
- **Özet:** `northarrow::NorthArrow` (Protocol-tabanlı, `meta.north_angle`
  verilmezse çizilmez) eklendi. (`HD-011`) **rev-18 düzeltmesi:** aynı
  görevle eklenen `pafta::ScaleBar` (grafik ölçek cetveli) kullanıcı geri
  bildirimiyle ("her pafta içerisinde ölçek gibi bir şey var ... onu
  istemiyorum, kaldır") TAMAMEN KALDIRILDI; kuzey oku etkilenmedi. (`HD-012`)

### DEV-022 — `stairs/` — merdiven gerçek basamak geometrisi

- **Durum:** COMPLETED (2026-09-25)
- **Özet:** Yeni `scripts/stairs/` modülü (Fikir 1, kullanıcı kararı);
  `resolve_stair` tek kaynak (`openings::swing_geometry` deseni), rıht/going
  ofis standardı varsayılanları (170mm/270mm) `auto_flex` ile esnetilir
  (her esnetme UYARI). Yalnızca tek düz kollu merdiven desteklenir; sığmayan
  oda `StairFitError` ile REDDEDİLİR (gerçek projenin `Merdiven` odası bu
  sınıra girdiği için `context.json`a henüz veri eklenmedi). (`HD-013`)

### DEV-030 — Katman renk organizasyonu (modüller arası)

- **Durum:** COMPLETED (2026-09-25)
- **Özet:** Yeni `scripts/palette/` modülü (Fikir 2, kullanıcı kararı:
  "bazı modüller aynı rengi seçmiş olabilir" + "kontrast ihtiyacı"); tüm
  kod-sahipli katman renkleri TEK kayıtta (`PALETTE`), iki kural
  (aynı-renk yasağı + `contrast_group` içi minimum mesafe) denetleniyor.
  Somut bulgu düzeltildi: `KOLON`/`KOLON-TARAMA`/`KOLON-METIN` artık üç
  FARKLI ton (DEV-030 öncesi üçü aynıydı). `context.json::layers[]` (proje
  verisi, ACI index) kapsam DIŞINDA bırakıldı — kod-seviyeli/proje-seviyeli
  ayrım korundu. (`HD-014`)

### DEV-029 — Kot (seviye/datum) yönetim mantığı — proje geneline hakim

- **Durum:** COMPLETED (2026-09-25)
- **Özet:** Yeni `scripts/levels/` modülü (kullanıcının doğrudan önerdiği
  Fikir: bağımsız, küçük modül); kot metni `"+3.00"`/`"-0.20"`/`"±0.00"`
  formatında (kullanıcı kararı). Kesit/görünüşte OTOMATİK — kat yüksekliği
  hesabı `elevations::LevelStack`ten TÜKETİLİR, YENİDEN YAZILMAZ. Planda
  `floors[].level_marks[]` ile GERÇEK veri (rampa/teras kademesi), verilmezse
  çizilmez. Gerçek projenin `output/plan.dxf`ine otomatik olarak 80 yeni
  `KOT` varlığı eklendi (2 cephe + 2 kesit × 10 kat sınırı × 2 varlık).
  (`HD-015`)

## Görev tamamlama kuralı

Bir görev için agent şunları yapmadan `COMPLETED` yazamaz:

1. Kabul ölçütlerini karşılayan kod/doküman değişikliğini tamamlamak.
2. Odaklı validation çalıştırmak.
3. Gerekli ise `validate.py` ve `generate_dxf.py` çalıştırmak.
4. Golden output etkisini kaydetmek.
5. Ayrı reviewer/validator çalışmasından kabul raporu almak.
6. `DEVELOPMENT_HISTORY.md`ye kayıt eklemek.
7. `DEVELOPER_NOTES.md`yi bir sonraki direktifle güncellemek.
8. **Görevi doğru bölüme taşımak ve "Durum özeti" tablosunu güncellemek.**
9. **`python scripts/doc_check.py` çalıştırıp TEMİZ sonuç almak.** Bu adım
   zorunludur ve 1-8 arasındaki adımların gerçekten yapıldığını mekanik olarak
   doğrular.
10. `python scripts/development_control.py release ...` ile görev kilidini
    bırakmak.

> **Bu kural neden mekanik hale getirildi:** 6-7. maddeler uzun süre yalnızca
> düzyazıydı ve gerçekten kaçtı — rev-10'da `DEV-006`nın `Durum:` alanı
> COMPLETED yapıldı ama madde `## READY` başlığının altında kaldı; COMPLETED ve
> BLOCKED maddeler "PLANNED" başlığı altında birikti. Kullanıcı fark etti.
> Düzyazı hatırlatma bu hata sınıfını engellemiyor, bu yüzden `doc_check.py`
> yazıldı ve kontrolleri kasıtlı bozma testleriyle doğrulandı.
