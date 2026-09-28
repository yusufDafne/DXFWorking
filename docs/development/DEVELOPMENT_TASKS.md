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
| DEV-007 | `pafta/` | **BLOCKED** — yalnızca mimar adı / proje tarihi |
| DEV-014 | `walls/` | COMPLETED (rev-15) |
| DEV-015 | `axis/` | COMPLETED (rev-13) |
| DEV-016 | `openings/` | COMPLETED (rev-13) |
| DEV-017 | `dimensions/` | COMPLETED (rev-13) |
| DEV-018 | DXF `BLOCK` (modüller arası) | COMPLETED (rev-14) |
| DEV-019 | `collision/` (modüller arası) | COMPLETED (rev-12) |
| DEV-020 | sürüm + provenance | COMPLETED (rev-12) |
| DEV-021 | `sections/` — kesit modülü | COMPLETED (rev-17) |
| DEV-022 | `stairs/` — merdiven gerçek geometrisi | COMPLETED (2026-09-25) |
| DEV-023 | `ceiling/` — yansıtılmış tavan planı | COMPLETED (2026-09-28) |
| DEV-024 | `site/` — vaziyet planı | PLANNED |
| DEV-025 | Kuzey oku (+ grafik ölçek çubuğu, rev-18'de geri alındı) | COMPLETED (rev-17) |
| DEV-026 | `legend/` — alan hesap cetveli | PLANNED |
| DEV-027 | Kaçış (tahliye) planı | PLANNED |
| DEV-028 | `legend/` — malzeme/kaplama cetveli | PLANNED |
| DEV-029 | Kot (seviye/datum) yönetim mantığı — proje geneli | COMPLETED (2026-09-25) |
| DEV-030 | Katman renk organizasyonu (modüller arası) | COMPLETED (2026-09-25) |
| DEV-031 | `electrical/` — elektrik tesisatı planı | PLANNED |
| DEV-032 | `plumbing/` — sıhhi tesisat (ıslak hacim) planı | PLANNED |
| DEV-033 | `walls/` genişletmesi — duvar katman/yalıtım detay kesiti | PLANNED |
| DEV-034 | `columns/`+`walls/` genişletmesi — statik kalıp planı | PLANNED |
| DEV-035 | `roof/` — çatı planı | PLANNED |
| DEV-036 | `standards/` — şartname + oransal mahal kural kütüphanesi | COMPLETED (2026-09-28) |
| DEV-037 | Kat planı / daire yerleşimi şablon kütüphanesi + generator | COMPLETED (2026-09-28) |
| DEV-038 | Oda programı ↔ mevcut alan sığma (feasibility) kontrolü | COMPLETED (2026-09-28) — `DEV-039`e absorbe edildi |
| DEV-039 | `scripts/architect/` — mekansal ilişki/mimari mantık kuralları (adjacency & circulation logic) | COMPLETED (2026-09-28) |
| DEV-040 | `architect/` — 2. nesil mimari mantık motoru (genişleme yol haritası) | PLANNED |

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
2. **`DEV-023`…`DEV-028`** (2026-09-24), **`DEV-031`…`DEV-035`**
   (2026-09-28) — kullanıcı talebiyle eklenen, **endüstri standardı bir
   mimari çizim setinde bulunan ama bu projede henüz olmayan** modül/
   geliştirme fikirleri (`DEV-021`/`DEV-025` rev-17'de, `DEV-022`
   2026-09-25'te, `DEV-023`/`DEV-036`/`DEV-037`/`DEV-038`/`DEV-039`
   2026-09-28'de seçilip tamamlandı, bkz. `## COMPLETED`). Bunlar bir
   mimarın ufkunu açmak ve gerçekten gözden kaçan bir şey olup
   olmadığını değerlendirmek için yazılmıştır — **uygulama izni
   DEĞİLDİR**. Her biri `PLANNED` seviyesinde bir taslaktır; gerçek
   Fikir 1/Fikir 2/Açık kararlar analizi (mevcut modüllerdeki gibi) o
   madde açıkça seçildiğinde yapılır. Sistem mimarı bir maddeyi seçip
   kendi yönlendirmesini eklemeden agent kod yazmaz.

> `DEV-036`…`DEV-039` bu ikisinden AYRI bir üçüncü tür örneğidir:
> `DEV-039`, kullanıcının bizzat "modül adı ve mevcut modüllere sığıp
> sığmayacağı belli değil, sen planla, ben tartışayım" diyerek
> DOĞRUDAN istediği bir tartışmaydı, bir agent'ın kendi inisiyatifiyle
> yazdığı "ufuk notu" DEĞİLDİ — üç tur süren bir diyalogla (modül adı,
> iç yapı, v1 kural kataloğu, şema kararı, kural şiddeti kullanıcı
> tarafından TEK TEK onaylandı) nihaileşti, sonra "planı uygula" ile
> tamamlandı. Bkz. `## COMPLETED` `DEV-039`.

> **`DEV-040`** bir DÖRDÜNCÜ türdür: `DEV-039` TAMAMLANIP gerçek projeye
> uygulandıktan HEMEN sonra kullanıcının verdiği bir STRATEJİK yönelim
> notu ("bu programı gerçek bir mimar yapan en önemli yapı taşının
> temellerini atıyoruz") — tek bir modülün genişleme YOL HARİTASINI
> (fikir listesi + değişmez ilke) kayıt altına alır, `DEV-021`…`DEV-035`
> gibi bir agent inisiyatifi DEĞİLDİR ama `DEV-039` gibi kod da
> ÜRETMEZ — salt planlama. Ayrıntı `scripts/architect/CLAUDE.md`
> "Gelecek yönü" bölümünde.
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

### DEV-031 — `electrical/` — elektrik tesisatı planı

- **Durum:** PLANNED

**Neden endüstri standardı bir boşluk:** Elektrik tesisat planı (priz,
anahtar, aydınlatma armatürü, pano/tek hat şeması, kablo güzergahı) TS EN
60617/IEC sembol setiyle çizilen, ruhsat evrakının AYRILMAZ bir parçasıdır
(AIA/NCS katman standardında `E-` öneki, elektrik mimari kabuktan AYRI bir
disiplindir). Bugün sistemde bu bilgi katmanı hiç yok — kullanıcının
açıkça belirttiği "elektrik projeleri" boşluğu budur.

**Fikir 1 — YENİ, bağımsız `scripts/electrical/` modülü (önerilen).**
`furniture/`nin "katalog + yerleşim" deseniyle AYNI yapı: sembol kataloğu
(priz/anahtar/aydınlatma armatürü — TS/IEC sembolleri) + `floors[].
electrical[]` yerleşimi. Elektrik `furniture/`ye KARIŞTIRILMAZ (endüstri
standardı: `A-FURN` ile `E-*` ayrı katman ailesidir, `openings/`in
`furniture/`den ayrı tutulma gerekçesiyle AYNI).

**Fikir 2 — `furniture/`ye yeni bir grup olarak eklemek.** Daha ucuz ama
endüstri standardıyla ÇELİŞİR — elektrik sembolleri tefriş değildir,
ayrı bir disiplindir; kapı/pencerenin tefrişten ayrı tutulma gerekçesiyle
(bkz. kök `CLAUDE.md` "Tefriş") AYNI mantıkla ÖNERİLMEZ.

**Açık kararlar:**

- Fikir 1 mi Fikir 2 mi? (Fikir 1 önerilir.)
- Kapsam yalnızca NOKTA sembolleri mi (priz/anahtar/armatür), yoksa hat
  (kablo güzergahı, nokta-nokta bağlama) da mı çizilecek? Otomatik
  routing İSTENMEZ/UYDURULMAZ — güzergah proje verisi olarak AÇIKÇA
  verilmelidir.
- Pano/tek hat şeması (ayrı bir şema türü, elektrik odası/panosu) bu
  revizyonun kapsamında mı, yoksa ayrı bir takip görevi mi?
- Sembol seti standardı (TS mi, IEC mi) kullanıcı onayı gerektirir.

**İlişkili modüller:** `furniture/` (yerleşim deseni benzer, AYRI liste),
`legend/` (sembol lejantı), `collision/` (muhtemelen `dimensions`/`axis`
ile AYNI gerekçeyle EXEMPT — anotasyon, oda dışına taşma kontrolü hariç).

### DEV-032 — `plumbing/` — sıhhi tesisat (ıslak hacim) planı

- **Durum:** PLANNED

**Neden endüstri standardı bir boşluk:** Kullanıcının açıkça belirttiği
"ıslak hacimler" boşluğu: bugün `furniture/`nin `ISLAK` grubu lavabo/
klozet/duş gibi ELEMANLARI yerleştiriyor ama su/pis su HATTINI, gider
noktasını çizmiyor. Sıhhi tesisat planı (`A-PLMB`/`P-` katman ailesi),
mimari tefriş çiziminden AYRI, standart bir mühendislik paftasıdır.

**Fikir 1 — YENİ, bağımsız `scripts/plumbing/` modülü (önerilen).**
`furniture/`nin `ISLAK` grubu YERLEŞİMLERİNİ TÜKETİR (kopyalamaz,
`stairs`in `rooms/`i tüketmesiyle AYNI desen) ve bu noktalara gider/temiz
su sembolü + (verilirse) hat bağlantısı ekler.

**Fikir 2 — `furniture/`nin `ISLAK` grubuna otomatik sembol eklemek.**
Daha ucuz, ayrı modül gerektirmez, ama endüstri standardıyla (tesisat
mimari kabuktan ayrı disiplin) ÇELİŞİR; `DEV-031`deki Fikir 2'nin AYNI
sakıncası geçerlidir.

**Açık kararlar:**

- Fikir 1 mi Fikir 2 mi?
- Kapsam yalnızca gider/bağlantı NOKTA sembolleri mi, yoksa gerçek boru
  güzergahı (routing) da mı çizilecek? Routing deterministik olabilir
  AMA güzergah proje verisi olarak AÇIKÇA verilmelidir — sistem boru
  yolunu TAHMİN ETMEZ.
- `furniture::ISLAK` grubuyla veri akışı: her ıslak hacim elemanı
  otomatik bir tesisat noktası mı alır, yoksa ayrı bir `floors[].
  plumbing[]` listesi mi (elemanla eşleşmesi gerekir) tanımlanacak?

**İlişkili modüller:** `furniture/` (`ISLAK` grubu TÜKETİLİR), `collision/`
(tesisat hattının duvar/tefrişle çakışması yeni bir kural gerektirebilir).

### DEV-033 — `walls/` genişletmesi: duvar katman/yalıtım detay kesiti

- **Durum:** PLANNED

**Neden endüstri standardı bir boşluk:** `scripts/pafta::PaperSizePlanner`
zaten `DETAY` proje tipini (1:20/1:10/1:5/1:1 ölçek kısıtıyla) TANIYOR —
ama bu ölçekte gerçekten çizilen bir detay YOK (`DEV-024`ün `VAZIYET_
PLANI` durumuyla AYNI desen: proje tipi tanınıyor, yetkinlik yok). Duvar
katman detayı (sıva-tuğla/yalıtım-tuğla-sıva, katman kalınlıkları +
malzeme etiketleri), Türkiye enerji kimlik belgesi/yalıtım yönetmeliği
kapsamında standart bir mimari uygulama çizimidir.

**Tek fikir (mevcut `walls/` modülünün genişletilmesi, yeni modül
GEREKMEZ):** `walls::WallCatalog`a katman kompozisyonu (örn. `layers:
[{"malzeme": "siva", "kalinlik_mm": 20}, ...]`) eklenip, büyük ölçekte TEK
bir duvarın enine kesitini katmanlarıyla çizen yeni bir fonksiyon
(`WallDetailSheet` gibi) `walls/` modülüne eklenir — `RailDrawingStandard`
deseninin doğal bir uzantısı (rail'in NASIL çizildiği zaten `kind`e göre
değişiyor, bu onun "yakınlaştırılmış" hali).

**Açık kararlar:**

- Katman kompozisyonu verisi `WallCatalog`a (kütüphane/ofis standardı,
  `kind`e göre sabit) mı, yoksa `context.json`a (proje verisi, projeye
  özgü) mı ait olacak?
- Detay hangi duvarlar için çizilecek — TÜMÜ mü, kullanıcının seçtiği
  BİRİ mi (`meta.detail_walls` gibi bir liste)?
- Malzeme kod listesi ve gösterim standardı (tarama deseni/renk) kullanıcı
  onayı gerektirir — UYDURULMAZ.

**İlişkili modüller:** `walls/` (ana sahiplenici), `pafta/` (`DETAY`
proje tipi zaten tanınıyor, yeni pafta boyutu/ölçek planlaması
gerekebilir).

### DEV-034 — `columns/`+`walls/` genişletmesi: statik kalıp planı

- **Durum:** PLANNED

**Neden endüstri standardı bir boşluk:** `scripts/pafta::PaperSizePlanner`
zaten `STATIK_KALIP` proje tipini (yalnızca `1:50` ölçek kısıtıyla)
TANIYOR — ama sistemde HİÇBİR statik/strüktürel çizim YOK, yalnızca
mimari plan var. Kalıp planı (kolon-kiriş-döşeme sınırları + kalıp
ölçüleri), ruhsat evrakının statik projesinin temel paftasıdır.

**Tek fikir gerçek bir mimari sorudur, iki alt-seçenek var:** kolonlar
zaten `columns/`de modelleniyor, ama kiriş ve döşeme (kalıp planının asıl
konusu) bugün HİÇ yok — bunlar GERÇEK yeni geometri sınıflarıdır
(`schema`ya `beams[]`/`slabs[]` eklenmesi gerekir), yani bu görev
muhtemelen `DEV-023`/`DEV-024` gibi "mevcut modülü genişlet" değil,
**yeni bir `scripts/structural/` modülü** gerektirir.

- **Alt-seçenek A (küçük kapsam):** v1 yalnızca mevcut kolon+taşıyıcı
  duvar geometrisini `STATIK_KALIP` ölçeğinde YENİDEN çizer (kiriş/döşeme
  OLMADAN) — gerçek bir kalıp planı değildir ama mevzuat tanıma
  altyapısını (`PaperSizePlanner`) gerçek bir çıktıya bağlar.
- **Alt-seçenek B (tam kapsam):** yeni `scripts/structural/` modülü,
  `beams[]`/`slabs[]` şema alanları, kalıp ölçü etiketleri. Demir donatı
  (çubuk çapı/aralığı) KAPSAM DIŞI bırakılmalıdır — bu çok daha büyük,
  ayrı bir mühendislik konusudur.

**Açık kararlar:**

- Alt-seçenek A mı B mi? (B gerçek değeri taşır ama çok daha büyük iştir.)
- B seçilirse: kiriş/döşeme verisi nasıl modellenir (aks ızgarasına mı
  oturur, yoksa serbest mi)?
- Demir donatı kesinlikle kapsam DIŞI mı kalacak? (Öneri: evet.)

**İlişkili modüller:** `columns/` (kolonlar zaten var, yeniden kullanılır),
`walls/` (taşıyıcı duvarlar), `axis/` (kalıp planı aks ızgarasına oturur),
`pafta/` (`STATIK_KALIP` zaten tanınıyor).

### DEV-035 — `roof/` — çatı planı

- **Durum:** PLANNED

**Neden endüstri standardı bir boşluk:** Bugün "ÇATI/TERAS" kat tipi düz
bir teras olarak modelleniyor — kırma/beşik çatı eğimi, mahya çizgisi,
dere çizgisi, saçak genişliği hiç modellenmiyor. Kırma çatılı bir yapı
için çatı planı (eğim yönleri + mahya/dere hatları + saçak ofseti + çatı
malzemesi), ruhsat evrakının standart bir parçasıdır.

**Fikir 1 — YENİ, bağımsız `scripts/roof/` modülü (önerilen).** Çatı
geometrisi (eğim yönü okları, mahya/dere çizgileri, saçak ofseti) binanın
MEVCUT `floor_width`/`floor_depth` oturumundan TÜRETİLİR (bina oturumu
zaten var — yeni bir geometri UYDURULMAZ); kullanıcı yalnızca eğim
oranı/yönü ve malzeme gibi GERÇEK proje kararlarını verir.

**Fikir 2 — Düz teras davranışını DEĞİŞTİRMEDEN, çatı görünümünü SADECE
cephe/kesitte göstermek.** Ayrı bir çatı PLANI çizmez, kapsamı küçültür;
`elevations`/`sections`e opsiyonel bir "çatı silueti" ekler. Endüstri
standardının bir PLAN paftası da beklediği gerçeğiyle KISMEN çelişir ama
çok daha küçük bir iştir.

**Açık kararlar:**

- Fikir 1 mi Fikir 2 mi?
- Mevcut düz teras davranışı (bilinen basitleştirme, kök `CLAUDE.md`)
  VARSAYILAN olarak KORUNACAK mı — kırma çatı yalnızca opt-in (yeni veri
  verilirse) mi devreye girecek? (Öneri: evet, geriye dönük uyumluluk.)
- Eğim oranı/yönü ve çatı malzemesi kullanıcı onayı gerektirir —
  UYDURULMAZ.

**İlişkili modüller:** `elevations/`+`sections/` (çatı siluetinin cephe/
kesitte görünmesi), `pafta/` (yeni pafta türü, Fikir 1 seçilirse).

### DEV-040 — `architect/` — 2. nesil mimari mantık motoru (genişleme yol haritası)

- **Durum:** PLANNED — bu bir "seç ve başlat" maddesi DEĞİLDİR, kullanıcının
  2026-09-28'de (DEV-039 commit'inden ÖNCE) verdiği bir STRATEJİK
  yönelim notudur. Hiçbir alt-fikir onaylanmadı/uygulanmadı; bu madde
  sadece fikirlerin TEK bir yerden (bu görev + `scripts/architect/
  CLAUDE.md` "Gelecek yönü") izlenebilmesi için açıldı.

**Neden bu madde (kullanıcının kendi sözleriyle):** *"bu yaptığın
çalışmanın genel altyapı konusunda en önemli ve kritik nokta olduğunu
bilmeni istiyorum. bu programı gerçek bir mimar yapan en önemli yapı
taşının temellerini atıyoruz ... bu sistem aslında birçok mimari çizim
konusunda ciddi belirleyicilik ve kısıtlayıcılık oluşturacak, hatta
müşteri taleplerine göre bazı projelerin saçmalık seviyesi ya da
imkansızlığı gibi durumlar ortaya çıkacak gelecekte (imkansız diye bir
şey yok tabii, müşteri kapının önüne wc koy derse koyacağız 🙂 sadece
örnek verdim)."*

**Değişmez ilke (bu maddenin ANAYASASI):** modül ne kadar büyürse
büyüsün, hiçbir kural kullanıcının açık kararı olmadan `collision/`in
`FORBID` sınıfına ÇEKİLMEZ — `architect/`in konusu fiziksel imkânsızlık
değil mimari SAĞDUYUDUR, ve sağduyu müşterinin bilinçli tercihiyle HER
ZAMAN ezilebilir kalmalıdır. Büyüyen şey kuralların SAYISI/KAPSAMIdır,
ŞİDDET SINIFI (WARN) değil.

**Fikirler (ayrıntı `scripts/architect/CLAUDE.md` "Gelecek yönü — 2.
nesil mimari mantık motoru" bölümünde, TEK kaynak orada tutulur, burada
TEKRARLANMAZ):**

1. Uyarı şiddeti bir SAYI (0.0-1.0 severity) olsun — spektrum, hâlâ
   bloklamaz.
2. Bina tipi profilleri (`standards/`in "mahal tipi -> eşik" deseninde,
   bina tipi -> kural kümesi).
3. Katlar ARASI ilişkiler — bugün `architect/` (`collision/` ile AYNI
   bilinen sınırlama) yalnızca AYNI katta çalışıyor; ıslak hacim düşey
   istifi, kolon/taşıyıcı düşey hizası gibi konular YENİ bir arite
   boyutu gerektirir.
4. `options.py`nin (seçenek kataloğu) HER önemli tasarım karar noktasına
   (birim karışımı, ıslak hacim sütunu konumu, giriş cephesi seçimi)
   yaygınlaştırılması.
5. Proje bazlı kural profili/eşik override'ı (`meta.architect_profile`
   gibi) — kök `CLAUDE.md`nin "çizim sabiti context'e sızmamalı"
   ilkesiyle GERİLİM içerebilir, dikkatli değerlendirilmeli.
6. Bilinçli göz ardı etmenin (bir UYARI'nın gerekçeyle kabul edilmesi)
   yapılandırılmış bir izinin tutulması fikri — henüz net değil.

**Açık kararlar:** hangi fikrin/fikirlerin, hangi sırayla, ne zaman
`DEV-0XX` olarak somutlaştırılıp seçileceği TAMAMEN kullanıcı kararıdır.
Bu madde kendi başına hiçbir kodu TETİKLEMEZ.

**İlişkili modüller:** `scripts/architect/` (uygulanacağı yer),
`standards/` (bina tipi profili deseninin emsali), `collision/` (arite
ayrımının ve "yalnızca aynı kat" sınırlamasının emsali), `columns/`
(düşey hizalama sınırlamasının emsali), `DEV-027` (kaçış planı —
"acil çıkış mesafesi" gibi bir gelecek kural ile kavramsal KOMŞU).

## COMPLETED

> Ayrıntılı gerekçe, karar süreci, bulunan gerçek hatalar ve ölçülen etki
> için her maddenin işaret ettiği `DEVELOPMENT_HISTORY.md` kaydına bakınız.
> Buradaki özetler KASITLI olarak 1-2 cümledir.

> **2026-09-28'de kullanıcı talebiyle budandı:** en eski 12 COMPLETED
> madde (`DEV-001`…`DEV-006`, `DEV-008`…`DEV-013` — orijinal modül
> kataloğunun ilk kuruluşu) bu dosyadan TAMAMEN kaldırıldı; bu bir veri
> kaybı DEĞİLDİR, ayrıntıları zaten `DEVELOPMENT_HISTORY.md`de
> (`HD-002`, `HD-003`, `HD-005`, `HD-006`, `HD-009`, `HD-010`) eksiksiz
> duruyor. Bu dosyanın amacı "sıradaki iş" olduğu için en eski/en az
> güncel bağlamlı tamamlanmış işler burada TUTULMAZ.

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

### DEV-023 — `ceiling/` — yansıtılmış tavan planı (RCP)

- **Durum:** COMPLETED (2026-09-28)
- **Özet:** Yeni `scripts/ceiling/` modülü (Fikir 1, kullanıcı kararı: ayrı
  RCP paftası); tavan kotu/malzeme `rooms[]` başına GERÇEK veridir
  (kullanıcı kararı: oda bazlı), v1 aydınlatma armatürünü İÇERMEZ (kullanıcı
  kararı). `ceiling_height_mm` taşımayan bir katın RCP paftası HİÇ
  üretilmez — gerçek projenin bugünkü verisinde bu alan yok, bu yüzden
  `output/plan.dxf` DEĞİŞMEDİ (yalnızca zaman damgası/GUID farkı). RCP'nin
  açıklıkları (kapı yayı dahil) YENİDEN çizmesi gerçek bir golden-kural
  boşluğunu ortaya çıkardı: `golden_report.py::rule_opening_symbols` "ARC
  sayısı = kapı sayısı" varsayıyordu, RCP'li bir katta bu İKİYE katlanır —
  kural `ceiling.floor_has_ceiling_data`yı (paftayı açan AYNI tek kaynak)
  okuyacak şekilde düzeltildi. Yeni `golden/tavan_ornek` RCP'yi uçtan uca
  sınıyor. (`HD-016`)

### DEV-036 — `standards/` — şartname + oransal mahal kural kütüphanesi

- **Durum:** COMPLETED (2026-09-28)
- **Özet:** Yeni `scripts/standards/` modülü (Fikir 1, kullanıcı yönlendirmesi:
  "best practices bir yaklaşım ile gerçekleştir"); mahal tipi başına en-boy
  oranı (+ opsiyonel asgari kısa kenar/alan). İhlal kullanıcı kararı gereği
  HER ZAMAN UYARIdır, üretimi DURDURMAZ. `rooms[].room_type` (opt-in, addan
  TAHMİN EDİLMEZ) `STANDARDS`ta tanımsızsa `walls.kind` ile AYNI desende
  HATA verir. v1 kataloğu çoğunlukla "pratik varsayılan" — kullanıcının
  ileride gerçek şartname belgeleriyle güncellemesi beklenir; bu yüzden
  `CONTRACT_VERSION` disiplini "katalog DEĞERİ serbestçe değişir, `RoomStandard`
  ALAN ŞEKLİ değişirse sürüm artar" şeklinde tasarlandı (bkz.
  `scripts/standards/CLAUDE.md` "Gelecek güncelleme sözleşmesi"). Gerçek
  projeye `room_type` verisi eklenmedi (altyapı opt-in kuruldu, `ceiling`/
  `levels` emsali); yeni `golden/oran_ornek` (golden/minimal ile AYNI
  geometri, yalnızca `room_type` etiketleriyle) politikayı uçtan uca
  kanıtlıyor: aynı oran bir tipte (koridor) UYARISIZ geçiyor, aynı oranın
  başka bir tipte (banyo) TAM 1 UYARI üretip yine de ÇİZİLDİĞİni gösteriyor.
  (`HD-017`)

### DEV-037 — Kat planı / daire yerleşimi şablon kütüphanesi + generator

- **Durum:** COMPLETED (2026-09-28)
- **Özet:** Yeni `scripts/templates/` modülü (Fikir 1, kullanıcı
  yönlendirmesi: "best practices"); v1 kapsamı yalnızca **sirkülasyon
  çekirdeği** (asansör+merdiven+L-şekilli koridor+güney duvarı) ile
  SINIRLANDI — daire/birim içi oda bölüntüsü kapsam DIŞI bırakıldı (kendi
  başına büyük bir açık-karar seti gerektirir). **Kritik mimari not**
  (kullanıcı istemedi, deterministik ilkeyle çelişmemek için eklendi):
  "generator" dil modeline geometri ÜRETTİRMEZ, tamamen deterministik bir
  Python fonksiyonudur. Varsayılan ölçüler icat EDİLMEDİ — gerçek
  projenin ZATEN çalışan sirkülasyon çekirdeğinden (`normal1` katı)
  BİREBİR çıkarıldı; `selftest.py` `generate_circulation_core(20000,
  17500)`in gerçek proje verisiyle (poligon/alan/duvar/kapı konumu)
  BİREBİR eşleştiğini doğrudan kanıtlıyor. Çıktı bir `dict`tir,
  context.json'a OTOMATİK YAZILMAZ (açık karar). (`HD-018`)

### DEV-038 — Oda programı ↔ mevcut alan sığma (feasibility) kontrolü

- **Durum:** COMPLETED (2026-09-28) — `DEV-039`e ABSORBE edildi.
- **Özet:** Ayrı bir modül/görev olarak KALMADI; `scripts/architect/
  study.py::check_fits` olarak uygulandı (DEV-038'in kendi "Fikir 1"i —
  1D sığma testi — BİREBİR kod hâli). Ayrıntı için `DEV-039`e bakınız.

### DEV-039 — `scripts/architect/` — mekansal ilişki/mimari mantık kuralları

- **Durum:** COMPLETED (2026-09-28)
- **Özet:** Yeni `scripts/architect/` modülü, üç turluk kullanıcı
  diyaloğu sonucunda netleşen bir plandan uygulandı ("standartları büyük
  oranda belirlediğimize göre yeni bir plan oluşturmamızın vakti geldi
  ... bu modül, mimarın gerçek anlamda yaptığı işi yapacak"). Arity
  ayrımı `collision/`in `rooms/`den ayrılmasıyla AYNI gerekçeyi mimari
  SAĞDUYUya taşıdı: `standards/` bir odanın KENDİ oranını denetler
  (arity-1), bu modül iki/N elemanın BİRBİRİNE GÖRE mantıklı olup
  olmadığını denetler (arity-2+). TEK modül, dört dosya: `rules.py`
  (dört ilişkisel WARN kuralı — kapı-çekirdek dengesizliği, giriş-WC
  görüş hattı, hol/sirkülasyon alan payı, yatak odası-salon komşuluğu),
  `study.py` (etüt: `DEV-038`in absorbe edilen sığma testi + kaba 1D
  zonlama), `options.py` (seçenek kataloğu — dil modelinin "o anki
  duruma göre hangi seçenekler geçerli" diye SORABİLECEĞİ, ön-puanlanmış
  bir liste), `design.py` (mimari: zonlama planından kapı kararı,
  geometriyi KENDİSİ çizmez). Politika `standards/` ile AYNI: HER ZAMAN
  UYARI, asla HATA — kullanıcı mahremiyet kuralları için bile daha ciddi
  bir sınıf İSTEMEDİ. Yeni `rooms[].unit_id` (opsiyonel, opt-in) şema
  alanı eklendi — eskiden yalnızca `uA_`/`uB_`/`uC_` id-önek
  konvansiyonuyla ÖRTÜK olan "hangi oda hangi daireye ait" bilgisi artık
  AÇIK; kullanıcının gerekçesi bunu DEV-039'un ötesine taşıyor
  (gelecekteki "emsal" hesabı da aynı gruplamaya bağımlı olacak).
  **rev-21'de (aynı gün, kullanıcı talebiyle) gerçek projeye UYGULANDI**
  — 80 birim odasına `id`-önek konvansiyonundan BİREBİR türetilerek
  yazıldı; dört kural artık GERÇEKTEN çalışıyor ve 6 UYARI üretiyor
  (hol-oranı × 3 birim — uA/uB %37.7, uC %26.2, sınır %15 —, giriş-WC
  görüş hattı, kapı-çekirdek dengesizliği oran 4.38, yatak odası-salon
  komşuluğu), hiçbiri üretimi DURDURMUYOR. `selftest.py` hem bu GERÇEK
  ihlalin yakalandığını hem `unit_id` bellek-içi SOYULDUĞUNDA opt-in'in
  hâlâ geçerli kaldığını ayrı ayrı kanıtlıyor. Golden fixture BİLİNÇLİ
  olarak eklenmedi (`collision/`in kendi gerekçesiyle AYNI — bu modülün
  sorusu "tasarım mantıklı mı", golden'ınki "çıktı değişti mi"; hiçbir
  DXF entity'si üretilmediği için bir karşılaştırma bu mantığı sınamaz).
  (`HD-019`)

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
