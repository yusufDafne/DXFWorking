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
| DEV-022 | `stairs/` — merdiven gerçek geometrisi | PLANNED |
| DEV-023 | `ceiling/` — yansıtılmış tavan planı | PLANNED |
| DEV-024 | `site/` — vaziyet planı | PLANNED |
| DEV-025 | Kuzey oku (+ grafik ölçek çubuğu, rev-18'de geri alındı) | COMPLETED (rev-17) |
| DEV-026 | `legend/` — alan hesap cetveli | PLANNED |
| DEV-027 | Kaçış (tahliye) planı | PLANNED |
| DEV-028 | `legend/` — malzeme/kaplama cetveli | PLANNED |
| DEV-029 | Kot (seviye/datum) yönetim mantığı — proje geneli | PLANNED |
| DEV-030 | Katman renk organizasyonu (modüller arası) | PLANNED |

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
2. **`DEV-022`…`DEV-028`** — 2026-09-24'te (kullanıcı talebiyle) eklenen,
   **endüstri standardı bir mimari çizim setinde bulunan ama bu projede
   henüz olmayan** modül/geliştirme fikirleri (`DEV-021` ve `DEV-025`
   rev-17'de seçilip tamamlandı, bkz. `## COMPLETED`). Bunlar bir mimarın
   ufkunu açmak ve gerçekten gözden kaçan bir şey olup olmadığını
   değerlendirmek için yazılmıştır — **uygulama izni DEĞİLDİR**. Her biri
   `PLANNED` seviyesinde bir taslaktır; gerçek Fikir 1/Fikir 2/Açık kararlar
   analizi (mevcut modüllerdeki gibi) o madde açıkça seçildiğinde yapılır.
   Sistem mimarı bir maddeyi seçip kendi yönlendirmesini eklemeden agent
   kod yazmaz.
3. **`DEV-029`** — rev-17'de `DEV-021`/`DEV-025` çalışması sırasında
   kullanıcının ayrıca gündeme getirdiği, proje geneline hakim olması
   gereken bir çapraz-kesit (cross-cutting) konu: kot (seviye/datum) verme
   mantığı. Aynı "uygulama izni değildir" kuralı geçerlidir.
4. **`DEV-030`** — 2026-09-25'te kullanıcının kod incelemesi sırasında fark
   ettiği bir gözlem: modüller kendi katmanlarında (layer) çalışıyor ama bu
   katmanların RENKLERİ tutarlı biçimde çeşitlendirilmiyor. Aynı "uygulama
   izni değildir" kuralı geçerlidir — kullanıcı mimari kararın (merkezi bir
   renk kontrolör modülü mü, yoksa her modülün kendi rengini belirlemesi mi)
   kendi ihtiyaca göre verileceğini belirtti.

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

### DEV-022 — `stairs/` — merdiven gerçek basamak geometrisi

- **Durum:** PLANNED

**Neden endüstri standardı bir boşluk:** Kök `CLAUDE.md` bunu zaten kendi
"bilinen basitleştirme" olarak kayıtlı tutuyor: "asansör/merdiven kapı
sembolü çizilmez, sadece etiketli kapalı oda olarak gösterilir." Gerçek bir
mimari planda merdiven basamak/rıht çizgileri, çıkış yönü oku ve kesme
çizgisiyle (üst kat basamakları görünmez olduğu için) gösterilir — bu,
"birim bandı" / "sirkülasyon bandı" ayrımı zaten var olan bu projede somut
bir eksiktir.

**Kapsam taslağı:** `floors[].rooms[]`de merdiven için ayrılmış poligon +
basamak sayısı/rıht yüksekliği (kat yüksekliğinden türetilebilir) verilirse,
eşit aralıklı basamak çizgileri + yön oku + kesme çizgisi üretilir. Kesitle
(`DEV-021`, tamamlandı) doğal bir bağlantısı vardır: `sections::
SectionFeatureHook` genişletme noktası tam olarak bu senaryo (merdivenin
kesitte kırılma çizgisiyle gösterilmesi) için hazır tutulmuştur (bkz.
`scripts/sections/CLAUDE.md` "Genişletme noktası").

**Fikir 1 — YENİ, bağımsız `scripts/stairs/` modülü.** Projenin kurulu
motifiyle (her çizim konusu kendi modülü + kendi `CLAUDE.md`'si) tutarlı:
`Staircase`/`StairFlight` sınıfı merdiven poligonunü + basamak sayısını
girdi alıp eşit aralıklı rıht çizgilerini, yön okunu ve kesme çizgisini
üretir. `rooms/`e YENİ bir sorumluluk yüklemez — `rooms/` bugünkü gibi
poligon+etiketten sorumlu kalır, `stairs/` yalnızca merdiven olarak
işaretlenmiş odanın İÇİNE ek geometri çizer (kolonun `columns/` ile
tefrişin `furniture/` ile ilişkisine benzer bir "oda içi ek çizim" deseni).
Kesitteki kırılma çizgisi `sections::SectionFeatureHook`e bu modülden
enjekte edilir; `sections` `stairs`i import ETMEZ (mevcut tek yönlü
bağımlılık deseni korunur).

**Fikir 2 — `rooms/` modülünün genişletilmesi.** Merdiven zaten bugün bir
`Room` poligonu olarak modelleniyor; yeni bir modül açmak yerine
`RoomLabeler`e (veya yakınına) bir `stair_kind`/`is_stair` bayrağıyla
tetiklenen ek bir çizim adımı eklenebilir. Daha küçük bir değişiklik ama
`rooms/`in bugünkü net kapsamını (poligon + 3 satırlı etiket) bulanıklaştırır
ve `columns/`/`furniture/` emsaliyle (oda-içi ek eleman = kendi modülü)
tutarsız düşer.

**Açık kararlar (kod yazılmadan önce kullanıcı yönlendirmesi gerekir):**

- Fikir 1 mi Fikir 2 mi? (Proje motifiyle Fikir 1 önerilir ama seçim
  kullanıcınındır.)
- Basamak sayısı/rıht yüksekliği **şema alanı olarak mı verilecek**
  (örn. `rooms[].stairs.step_count`, `riser_height_mm`), yoksa kat
  yüksekliğinden (varsayılan rıht ~180mm ile) **otomatik türetilecek** mi?
  İkinci seçenek bir "çizim sabiti" (varsayım) içerir — kullanıcı onayı
  gerektirir, uydurulmaz.
- Yön oku (çıkış yönü) hangi veri alanından gelecek — yeni bir alan mı
  eklenecek, yoksa `rooms[]`in mevcut geometrisinden mi (örn. kapıya en
  yakın uç) türetilecek?
- Bu görevin kapsamı SADECE plan görünümü mü, yoksa `SectionFeatureHook`
  entegrasyonu (kesitte kırılma çizgisi) da AYNI revizyonda mı yapılacak?
- Çakışma denetimi (`collision/`): merdiven basamak çizgileri bir ayak izi
  ÜRETİR Mİ (örn. tefriş merdiven alanına girerse hata), yoksa yalnızca
  görsel bir katman mı kalacak?
- Golden referansı `golden/` (proje-geneli) altında mı yoksa
  `scripts/stairs/golden/` (modül-özel) altında mı olacak?
- Schema değişikliğine (`schema/design.schema.json`) izin var mı,
  `additionalProperties: false` sözleşmesiyle hangi alan adları eklenecek?

**İlişkili modüller:** `rooms/` (merdiven poligonu bugün de var, sadece
etiketli), `sections/` (tamamlandı — `SectionFeatureHook`e merdiven
kırılma çizgisi eklenerek genişletilir, çekirdek `SectionSheet.draw`
değişmeden), `collision/` (yeni ayak izi sağlayıcısı gerekip gerekmediği
açık karar).

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

### DEV-029 — Kot (seviye/datum) yönetim mantığı — proje geneline hakim

- **Durum:** PLANNED

**Kökeni:** `DEV-021`/`DEV-025` çalışması sırasında kullanıcının ayrıca
gündeme getirdiği bir konu: *"kot verme mantıklarını yöneten bir mantık
istiyorum... kot organizasyonu hem planda hem kesitte kullanılacaktır...
bu mantığın projenin geneline hakim olması gerekecektir."*

**Neden endüstri standardı bir boşluk:** Kot (spot/seviye yüksekliği,
örn. `±0.00`, `+3.00`, `-0.20`) mimari çizimde SEMBOLLE (üçgen/bayrak +
liderle bağlı metin) gösterilen, gerçek dünya yüksekliğini bildiren
standart bir anotasyondur — hem KAT PLANINDA (rampa/teras/kademe farkı
noktalarında) hem GÖRÜNÜŞ/KESİTTE (her kat sınırında) kullanılır. Bugün
sistemde bu YOK: `elevations::LevelStack` her seviyenin y0/y1'ini zaten
HESAPLIYOR (kümülatif kat yüksekliği) ama bunu bir "kot" olarak
FORMATLAYIP çizen hiçbir şey yok; kat planında ise hiçbir seviye/kot
verisi hiç yok.

**Mimari soru ve öneri (kullanıcının açıkça sorduğu karar):** Ayrı bir
modül mü, yoksa mevcut bir modül tarafından mı yönetilmeli? Bu görev
açıkça seçilmeden TAM Fikir 1/Fikir 2 analizi yapılmaz (bkz. dosya başı
kural), ama kullanıcı doğrudan bir mimari görüş istediği için ön bir
değerlendirme:

- **Öneri — YENİ, küçük, bağımsız bir modül** (örn. `scripts/levels/` veya
  `scripts/datum/`), `typography/` ölçeğinde küçük bir kütüphane:
  - Kot **formatlama/gösterim standardını** (işaret, ondalık sayısı, bayrak/
    üçgen sembolü — Türkiye standardında tipik olarak `+3.00` gibi 2
    ondalıklı METRE) ve bir `LevelMark` çizim ilkesini (flag/leader/text,
    `NorthArrow`/`ScaleBar` gibi ölçeğe göre türeyen) sahiplenir.
  - **Kat yüksekliği hesabını YENİDEN YAZMAZ** — `elevations::LevelStack`in
    zaten hesapladığı `y0`/`y1`i TÜKETİR (tek yönlü bağımlılık, `sections`
    → `elevations` ile AYNI desen).
  - Neden `elevations/`nin kendisine eklenmesin (Fikir 2 yerine): kot
    PLAN görünümünde de kullanılır (rampa/teras spot kotu) — bu,
    `elevations/`nin bugünkü net kapsamının (SADECE cephe istifi) dışında
    bir sorumluluktur; kot format/sembol standardı ile "seviye istifi
    hesabı" birbirinden ayrı iki karardır (birini değiştirmek diğerini
    etkilememeli). Bu tam olarak `sections`/`northarrow`ın `elevations`/
    `pafta`dan AYRI tutulma gerekçesiyle aynıdır (rev-17, bkz. `HD-011`).
- **Kapsam taslağı (taslak, henüz onay değil):** `rooms[]`e opsiyonel spot
  kot alanı (plan için) + `LevelMark.draw(msp, point, value_mm, ...)` +
  `elevations`/`sections`in her seviye sınırında bunu otomatik çağırması.
  Kot metni formatı (işaret/ondalık/birim) kullanıcı onayı gerektirir —
  UYDURULMAZ.

**İlişkili modüller:** `elevations/` (`LevelStack`in y0/y1'i TÜKETİLİR,
DEĞİŞTİRİLMEZ), `sections/` (aynı istif, kesitte de kot gösterilir),
`rooms/`+`pafta` (plan tarafı spot kotu, henüz şema yok).

### DEV-030 — Katman renk organizasyonu (modüller arası)

- **Durum:** PLANNED

**Kökeni:** Kullanıcının kod incelemesi sırasında yaptığı gözlem: "modüllerin
kendi layer'larında çalışırken renklerinin çeşitlendirilmediğini fark ettim."
Bu bir "endüstri standardı boşluğu" değil, mevcut kodun kendi içindeki bir
TUTARLILIK sorunudur — bu yüzden diğer `PLANNED` maddelerden farklı olarak
"Neden bir boşluk" yerine doğrudan bulgu ile başlıyor.

**Bulgu (mevcut durumun envanteri, rev-25'te çıkarıldı):**

- Proje verisi (`context.json::layers`) zaten çeşitlendirilmiş durumda:
  `DUVARLAR`(7)/`KAPI-PENCERE`(5)/`MOBILYA`(3)/`OLCU`(4)/`METIN`(2)/
  `CERCEVE`(8)/`OTOPARK`(9) — hepsi farklı ACI index.
- `scripts/furniture/groups.py::FURNITURE_GROUPS` da çeşitlendirilmiş: 5
  tefriş grubu (`TEFRIS-OTURMA`/`YEMEK`/`YATAK`/`MUTFAK`/`ISLAK`), 5 FARKLI
  kahverengi-ailesi RGB tonu (`ensure_furniture_layers`). Bu, projenin
  kendi iyi örneği.
- **`scripts/columns/standard.py`de somut bir tutarsızlık var:** `KOLON`
  (kontur), `KOLON-TARAMA` (hatch) ve `KOLON-METIN` (isim, bugün kapalı) —
  ÜÇ farklı katman — `ensure_column_layers` içinde TEK bir `COLUMN_RGB =
  (90, 90, 96)` ile boyanıyor. Kontur ve tarama görsel olarak ayrışmıyor.
- `scripts/axis/standard.py::AXIS_RGB` ve `scripts/sections/__init__.py::
  CUT_RGB` tek birer katmana (`AKS`, `KESIT`) ait olduğu için bu haliyle
  sorun değil; ama her ikisi de KOD içinde ayrı ayrı sabitlenmiş, ortak bir
  kayıt/çakışma kontrolünden geçmiyor — `AXIS_RGB=(67,77,88)` ile
  `COLUMN_RGB=(90,90,96)` birbirine yakın gri tonlar, tesadüfen çakışmıyor
  ama bunu garanti eden bir mekanizma yok.
  `scripts/northarrow/` kendi katmanını/rengini açmıyor, `CERCEVE`/`METIN`i
  ödünç alıyor (bilinçli bir paylaşım, ayrı bir renk sorunu değil).
- Özet: renk kararı bugün HER modülde (varsa) `ensure_axis_layer` deseniyle
  ayrı ayrı kod-seviyesinde veriliyor (kullanıcı ilkesi: "context.json'a
  asla çizim sabiti sızmamalı"); ama modüller arası hiçbir yerde bu
  renklerin BİRBİRİYLE çakışmadığını veya modül İÇİNDE anlamlı biçimde
  ayrıştığını denetleyen tek bir nokta yok.

**Fikir 1 — Merkezi olmayan: her modül kendi rengini kendi belirler.**
Bugünkü `ensure_axis_layer`/`ensure_furniture_layers`/`ensure_column_layers`
deseni AYNEN korunur; sadece HER modülün kendi `standard.py`si kendi
katmanları için (varsa birden fazla) GERÇEKTEN farklı ton seçer (örn.
`columns/standard.py`ye `COLUMN_LAYER` için bir RGB, `COLUMN_HATCH_LAYER`
için ayrı (daha açık/taralı okunur) bir RGB tanımlanır). `doc_check.py`ye
mekanik bir kontrol eklenebilir: bir modülün `ensure_*_layer` fonksiyonu
BİRDEN FAZLA katman kuruyorsa, bunlara aynı RGB atanmış olması hataya
sayılır. Modül bağımsızlığı ilkesiyle (`scripts/CLAUDE.md`) en uyumlu
seçenek budur — yeni bir modül gerekmez, mevcut desen genişler.

**Fikir 2 — Merkezi bir renk kontrolör modülü.** `typography::TextStyles`in
font için yaptığını renk için yapan küçük bir kütüphane (örn.
`scripts/palette/` veya `scripts/drawing_standards/`): tüm kod-seviyesi
katman renklerini (AKS, KOLON ailesi, KESIT, TEFRIS ailesi, ileride
`levels`/`stairs`/`ceiling` gibi yeni modüllerin katmanları) TEK bir
kayıtta toplar, modüller bu kayıttan RGB ister
(`palette.assign("KOLON-TARAMA", family="structural")` gibi), kayıt
çakışma/ayrışma kuralını (örn. "aynı ailedeki katmanlar birbirine yakın
ama BİRBİRİNDEN FARKLI tonda olmalı", "farklı aileler birbirine yakın
olmamalı") merkezi olarak uygular ve denetler. `context.json::layers`
(proje verisi, ACI index) bu kaydın KAPSAMI DIŞINDA kalır — o zaten
kullanıcı/proje kararıdır, kod bunu SEÇMEZ, sadece `setup_layers` ile
uygular.

**Açık kararlar (kullanıcı kendi ihtiyacına göre karar verecek):**

- Fikir 1 mi Fikir 2 mi? Bugün yalnızca 3 kod-seviyesi "aile" (aks/kolon/
  kesit + tefriş) olduğu için Fikir 1 yeterli olabilir; ama `DEV-022`
  (`stairs/`), `DEV-023` (`ceiling/`), `DEV-024` (`site/`), `DEV-029`
  (`levels`/`datum`) gibi planlanan yeni modüller devreye girdikçe kod-
  seviyesi katman/renk sayısı artacağı için merkezi bir kayıt (Fikir 2)
  o noktada daha değerli hale gelebilir — kullanıcı bunu ŞİMDİ mi yoksa
  ihtiyaç gerçekten büyüyünce mi kurmak istediğine karar verecek.
- Kapsam yalnızca RENK mi, yoksa katman ADI/linetype çakışması (örn. iki
  modülün aynı katman adını farklı amaçla kullanması) de aynı kontrole mi
  girecek?
- `context.json::layers` (proje verisi) ile kod-seviyesi katmanlar arasında
  bir çakışma kontrolü (örn. proje bir `KOLON` adlı kendi katmanını
  tanımlarsa ne olur) isteniyor mu, yoksa bu iki alan kasıtlı ayrı mı
  kalacak?
- ACI index (`context.json::layers[].color`, tamsayı) ile true RGB (kod-
  seviyesi katmanlar) bugün İKİ farklı renk sistemi — bu proje için tek bir
  sisteme (örn. hepsi RGB) geçmek isteniyor mu, yoksa ayrım (proje verisi =
  ACI, sistem/kod standardı = RGB) bilinçli olarak mı korunacak?
- Seçilen Fikir'e göre `doc_check.py`ye eklenecek mekanik kontrolün tam
  şekli (bkz. Fikir 1'deki öneri) kullanıcı onayı gerektirir.

**İlişkili modüller:** `columns/` (bugünkü somut tutarsızlığın kaynağı),
`furniture/` (zaten iyi örnek, referans desen), `axis/` + `sections/` (tek
katmanlı, bugün risksiz ama kaydın dışında), `typography/` (Fikir 2
seçilirse aynı "merkezi kayıt" deseninin ikinci örneği olur).

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
