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
| DEV-041 | `walls/`+`validate.py` — duvar ucu / kapı boşluğu çakışması denetimi | COMPLETED (2026-09-28) |
| DEV-042 | `architect/` — ıslak hacmin mahremiyet odası üzerinden erişilmemesi kuralı | COMPLETED (2026-10-02) |
| DEV-043 | `architect/` — banyo/wc kapı yakınlığı (ıslak hacim kümelenmesi) kuralı | COMPLETED (2026-10-02) |
| DEV-044 | `rooms/` — içbükey (L/T-şekilli) odalarda mahal etiketi konumlandırması | COMPLETED (2026-09-28) |
| DEV-045 | `templates/`+`architect/` — kat sirkülasyon bandının ölü alan analizi | COMPLETED (2026-10-02) |
| DEV-046 | `stairs/`+`templates/`+`standards/` — merdiven oda oranı + çok kollu merdiven desteği | COMPLETED (2026-10-02) |
| DEV-047 | `stairs/`+`architect/` — merdiven sahanlık çıkış noktası ↔ koridor kapısı hizalaması | COMPLETED (2026-10-02) |
| DEV-048 | Mimari muhakeme yetisinin sistemleştirilmesi (başlangıç planı) | PLANNED |
| DEV-049 | `standards/`+`architect/` — mahal/koridor standartları + yerel en dar nokta ölçümü | PLANNED |
| DEV-050 | `walls/`+`openings/`+`architect/` — kapı/duvar/koridor endüstri standardı nüans kataloğu (15 madde) | PLANNED |
| DEV-051 | `openings/`+`collision/` — kapı açılımı ↔ kalan net geçiş genişliği dinamik kontrolü | PLANNED |
| DEV-052 | `architect/` — DEV-043'ün (banyo/wc kapı yakınlığı) gerçek adjacency ile gözden geçirilmesi | PLANNED |
| DEV-053 | `architect/` — giriş kapısı ↔ WC/banyo kapısı mesafe-tabanlı asgari eşik | PLANNED |
| DEV-054 | `architect/`+`templates/` — hol topolojisi kütüphanesi (L şekli zorunluluğunun kaldırılması) | PLANNED |
| DEV-055 | `templates/`+`architect/`+`openings/` — sirkülasyon çekirdeğinin merkeze taşınması + asansör kapısı | PLANNED |
| DEV-056 | `architect/study.py` — etüt modülünün 2D yerleşim optimizasyonuna genişletilmesi | PLANNED |

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

> **`DEV-041`…`DEV-047`** BEŞİNCİ bir türdür: `DEV-039`'un gerçek projeye
> uygulanmasının (rev-21/rev-22) SOMUT SONUCUNDAN — kullanıcının bizzat
> üretilmiş plan üzerinde bulduğu gerçek hatalardan — çıkarılmış modül
> iyileştirme planlarıdır. Kullanıcının açık talimatı: *"tüm bu gerçek
> dünya yorumlarımı ayrı revize planları olarak kaydet, şu anda planda
> bir değişiklik değil ... önceliğimiz modül iyileştirilmesidir."* Yani
> bu maddeler `context.json`'a DOKUNMAZ — hiçbiri bir proje revizyonu
> DEĞİLDİR, hepsi `scripts/` altındaki İLGİLİ modülün YETENEĞİNİ
> genişletme/düzeltme planıdır. `DEV-041` KRİTİK işaretlidir (gerçek,
> kanıtlanmış bir üretim hatası); diğerleri gerçek plan çıktısından
> gözlemlenen tasarım kalitesi boşluklarıdır.

**Uygulama sırası (kullanıcı talebi, 2026-09-28: "bu planları en
efektif şekilde sırayla yapacağız, efektif sıralamayı belirle"):**

1. ~~**`DEV-041`** (KRİTİK, temel güvenlik ağı)~~ **TAMAMLANDI**
   (2026-09-28) — bkz. `## COMPLETED`. Geri kalan altı madde artık bu
   GÜVENCE altında ilerliyor.
2. ~~**`DEV-044`** — küçük, bağımsız, DIŞ KARAR gerektirmeyen bir modül
   düzeltmesi (`rooms/`, algoritma değişimi).~~ **TAMAMLANDI** (2026-09-28)
   — bkz. `## COMPLETED`.
3. ~~**`DEV-042`** → **`DEV-043`** (birlikte) — ikisi de `architect/
   rules.py`ye ekleniyor, ikisi de AYNI "ıslak hacim" temasında.~~
   **TAMAMLANDI** (2026-10-02) — bkz. `## COMPLETED`.
4. ~~**`DEV-046`** → **`DEV-047`** (sırayla, `DEV-047` `DEV-046`ya
   BAĞIMLI olduğu için başka türlü mümkün değil).~~ **TAMAMLANDI**
   (2026-10-02) — bkz. `## COMPLETED`.
5. ~~**`DEV-045`** — EN SONA bırakıldı.~~ **TAMAMLANDI** (2026-10-02) —
   bkz. `## COMPLETED`. "Ölü alanın YERİNE ne konacağı" kararı (plan
   metninin kendi "Açık karar"ı) UYDURULMADI — yalnızca KONTROL (Fikir 1)
   ve gereksiz alanı KALDIRAN geometri düzeltmesi (Fikir 2) uygulandı,
   boşalan alana ne konacağı AYRI bir kullanıcı kararı bekliyor.

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

### DEV-048 — Mimari muhakeme yetisinin sistemleştirilmesi (başlangıç planı)

- **Durum:** PLANNED — bu bir "seç ve başlat" maddesi DEĞİLDİR, `DEV-040`
  ile AYNI kategoride bir STRATEJİK yönelim notudur. Hiçbir teknoloji/
  modül kararı verilmedi; bu madde yalnızca fikrin TEK bir yerden
  izlenebilmesi için açıldı.

**Neden bu madde (kullanıcının kendi sözleriyle, 2026-10-02):** *"artık
altyapımızı oldukça geliştirdiğin için mimar gibi düşünmeye ve
konuşabilmeye başladın, bu en önemli kısımdır, bu özelliğinin de
geliştirilebilmesi ve proje bağlamında muhakeme yeteneğini daha best
practice, efektif ve genişletilebilir ve geliştirilebilir hale getirmek
için bir başlangıç planı tanımla."* Bu gözlem somut bir olayın HEMEN
ardından geldi: `uC` biriminin gerçek-dünya etüdü sırasında (kullanıcının
"banyo/wc yan yana", "mutfak kapısı karşısında wc olmaması" gibi
örneklerinden yola çıkarak) `architect/rules.py`nin ZATEN var olan
araçlarını (`_door_midpoint`, `_rooms_touching_point`,
`_clear_line_of_sight`) YENİDEN BİR ARAYA getirip yeni bir mahremiyet
sorununu (uC'de banyo, salon ile yatak odası arasına sıkışmış ve
ikisine de doğrudan kapısı var) tespit ettim — bu çıkarım KOD olarak
HİÇBİR YERDE yazılı değildi, o oturumun kendi muhakemesiydi.

**DEV-040'tan FARKI (ikisi de "strateji notu" ama konusu farklı):**
`DEV-040` `architect/`in KOD/KURAL kataloğunun (deterministik, Python,
arity-2+ WARN fonksiyonları) büyütülmesiyle ilgilidir. Bu madde ise
AJANIN KENDİ muhakeme/çıkarım SÜRECİYLE ilgilidir — hangi soruları hangi
sırayla sorduğu, hangi gözlemlerden hangi mimari ilkeye vardığı, ve bu
sürecin bir sonraki oturumda/bir sonraki ajanda AYNI kalitede tekrar
ÇAĞRILIP ÇAĞRILAMAYACAĞI. Biri KOD büyütür, diğeri KOD'u NE ZAMAN/NASIL
yazacağına karar veren SÜRECİ büyütür — ikisi birbirini BESLER (bu
maddeden çıkan yeni bir ilke genellikle `DEV-040`nın kural kataloğuna bir
`DEV-0XX` olarak düşer) ama KARIŞTIRILMAMALIDIR.

**Başlangıç planı (beş aşama, HENÜZ UYGULANMADI):**

1. **Envanter — bugüne kadar örtük kalan ilkeleri İSİMLENDİR.** Bu
   oturumda kullanılan muhakeme örnekleri (hub vs. doğrusal sirkülasyon
   tercihi, ıslak hacimlerin ortak duvar paylaşması/tesisat ekonomisi,
   sosyal-özel alan mahremiyet tamponu, giriş-WC görüş hattı, kapı-
   çekirdek dengesi, "hangi kontrolü hangi sırayla çalıştırıp hangi
   soruyu sorarım" metodolojisi) bir KONTROL LİSTESİ/metodoloji olarak
   yazıya dökülür — bugün yalnızca bu konuşmanın bağlamında yaşıyorlar.
2. **Bilgi tabanının NEREDE yaşayacağına karar — AÇIK, kullanıcıyla AYRI
   tartışılacak (bkz. "Açık karar").**
3. **Geri besleme döngüsü.** Her gerçek etüt/inceleme çalışmasından
   (bugünkü `uC` analizi gibi) çıkan YENİ bir ilke, Aşama 1'in
   kataloğuna EKLENİR — pratikte keşfedilen bir ilke bir dahaki sefere
   yeniden keşfedilmek yerine DOĞRUDAN çağrılabilir hale gelir.
   `standards/`in "kullanıcı gerçek şartname getirdiğinde katalog
   güncellenir" disipliniyle AYNI kategori.
4. **Kalibrasyon/doğrulama.** Bu ilkelerin GERÇEKTEN best-practice olup
   olmadığı nasıl sınanır — `standards/`in "Gelecek güncelleme
   sözleşmesi"yle AYNI yol: kullanıcı gerçek şartname/referans
   getirdikçe katalog KALİBRE edilir; resmi bir kaynağa atıf OLMADAN
   iddialar "v1 pratik varsayılan" diye İŞARETLENİR.
5. **Genişletilebilirlik/erişilebilirlik testi.** Bu yetenek yalnızca BU
   konuşmada mı kalıyor, yoksa GELECEKTEKİ bir oturumda (yeni bir agent/
   yeni bir context penceresi) AYNI seviyede ÇAĞRILABİLİYOR mu — planın
   "genişletilebilir ve geliştirilebilir" hedefinin ÖLÇÜTÜ budur. Seçilen
   teknoloji NE OLURSA OLSUN, kök `CLAUDE.md`nin "agentic dokümanlar
   birbirine bağlı tek bir bağlam sistemidir" ilkesiyle UYUMLU olmalı.

**Açık karar (kullanıcı AYRICA tartışacağını belirtti, BURADA
ÇÖZÜLMEDİ):** Aşama 2'nin uygulama biçimi/teknolojisi HENÜZ SEÇİLMEDİ —
somut alternatifler (hiçbiri onaylanmadı):
- **(a) Düz dokümantasyon** — `docs/development/` altında yeni bir
  "mimari ilkeler/sağduyu" dosyası; en düşük teknoloji, mevcut CLAUDE.md
  disipliniyle BİREBİR tutarlı.
- **(b) `scripts/` içinde veri-odaklı bir modül** — `standards::
  STANDARDS` ile AYNI desende, ama GEOMETRİ değil MUHAKEME SIRASI/
  önceliği kodlayan bir "heuristic katalog" (kullanıcının "script
  dışında ayrı bir düşünme yetisi modülü" ifadesiyle KISMEN örtüşür ama
  script İÇİNDE kalır).
- **(c) Proje/script DIŞINDA başka bir teknoloji** — kullanıcının
  kendi ifadesiyle "script dışında ayrı bir düşünme yetisi modülü ya da
  başka bir teknoloji" — somut biçimi (bir agent "skill" dosyası, bir
  bilgi tabanı, başka bir mekanizma) HENÜZ TANIMLANMADI.

Bu üç seçenek de BİRBİRİNİ DIŞLAMAZ (örn. (a) ile başlayıp zamanla (b)
veya (c)'ye evrilmek mümkündür) — karar kullanıcıyla AYRI bir turda
netleşecektir.

**İlişkili modüller/belgeler:** `scripts/architect/` (bugünkü pratik
muhakemenin KOD tarafı, `DEV-040` ile kavramsal KOMŞU ama FARKLI),
`scripts/standards/` (kalibrasyon/"v1 pratik varsayılan" disiplininin
emsali), kök `CLAUDE.md` + `scripts/CLAUDE.md` (agentic doküman sistemi
ilkesi — Aşama 5'in ölçütü).

> **`DEV-049`…`DEV-056`** ALTINCI bir türdür: kullanıcının kendi plan
> incelemesinden ("mimar modülün berbat bir iş çıkarmış ... 250mm
> genişliğinde hol olur mu hiç ... kat planında sol üst köşede merdiven/
> asansör var fakat sağ üst tarafta kocaman bir ölü bölge var") doğrudan
> çıkan, `DEVELOPMENT_IDEAS.md`de fikir olarak kaydedilip kullanıcının
> AÇIKÇA göreve aldığı sekiz maddedir. `DEV-041`…`DEV-047`den farkı:
> onlar rev-21/22'nin SOMUT üretim hatalarından çıktı, bunlar kullanıcının
> "efektif kat planı" + "15 endüstri standardı nüansı" talebinin
> SİSTEMATİK dökümüdür (bkz. `DEVELOPMENT_IDEAS.md` "Kat planı
> efektifliği ve endüstri standardı nüans fikirleri", 2026-10-05).
> **Hiçbiri henüz `READY` değildir** — kullanıcının kendi kararı:
> *"plan uygulandığı zaman bana bir sonraki geliştirme fikirleri için ana
> konuları bilgilendirme olarak sunacaksın ... ben de o açıklamalara
> istinaden ... geliştirme fikrini detaylı şekilde uygulayabilmen için
> açıklamalar yapacağım."* Yani agent her maddeyi kendi başına
> "başlatılmış" SAYMAZ; her madde yalnızca kullanıcının mini-detay
> talimatıyla açılır (`DEV-007`nin "agent bu madde için veri İSTEMEZ"
> disipliniyle AYNI aile, ters yönde: burada veri değil onay bekleniyor).

**Uygulama sırası (kullanıcı talebi, 2026-10-05: "sıralamayı sen
belirleyeceksin ... her birini sıralama olarak birbirine bağla"):**

**`DEV-049` → `DEV-050` → `DEV-051` → `DEV-052` → `DEV-053` → `DEV-054`
→ `DEV-055` → `DEV-056`**

1. `DEV-049` ölçüm altyapısını (yerel en dar nokta) kurar — ölçüm
   olmadan `DEV-050`nin eşik/kural yazması anlamsız kalırdı.
2. `DEV-050`nin kapı-geçiş ailesindeki statik maddeleri (#3/#8/#11)
   kodlanınca, `DEV-051` bunun DİNAMİK devamı olarak AYNI altyapıyı
   (`openings::swing_geometry`) derinleştirir.
3. `DEV-051` biterse, `DEV-052` (DEV-043 gözden geçirmesi) kapı-mesafe
   ailesinin üçüncü halkasıdır — net-geçiş ve nüans kuralları netleşmiş
   olur.
4. `DEV-052` ile `DEV-053` AYNI ıslak-hacim-mesafe temasında ama TERS
   yönlü eşikler taşır (biri "yakın OLSUN", öbürü "çok yakın OLMASIN");
   ardışık ele alınınca kalibrasyon çatışması baştan görülür.
5. `DEV-053` sabitlenince `DEV-054` (hol topolojisi kütüphanesi) bu
   kuralları aday topolojileri puanlarken girdi olarak kullanabilir.
6. `DEV-054` biterse `DEV-055` (merkezi çekirdek + dikdörtgen kat holü)
   kütüphaneden bir "merkezi-hub" adayı SEÇEREK yapılır — kütüphane
   yoksa rev-23'teki gibi yine EL İLE yapılırdı.
7. `DEV-056` (etüt 2D optimizasyonu) `DEV-055`in EL ile yapılan TEK-
   ÖRNEKLİ çözümünü GENELLEŞTİREN kapanış maddesidir.

### DEV-049 — `standards/`+`architect/` — mahal/koridor standartları + yerel en dar nokta ölçümü

- **Durum:** PLANNED — sıradaki madde (bkz. "Uygulama sırası"); kullanıcı
  mini-detay verdiğinde `READY`e çekilir.

**Neden bu madde (kullanıcının kendi sözleriyle, 2026-10-05):** *"örneğin
250mm genişliğinde hol olur mu hiç ... mimar modülü için proje
standartlarını şimdilik default ayarlar ile belirle. örneğin hol genişliği
minimum 1,5 metre olmalı gibi kurallar belirle."*

**Mevcut durum:** `standards::STANDARDS['koridor']` bugün
`min_short_edge_mm=1100.0` taşıyor (kullanıcının istediği 1500mm'den düşük)
ve `_aabb_edges` yalnızca odanın DIŞ sınırlayıcı kutusuna bakıyor — rev-23
sonrası tarak/L-şekilli bir hol poligonu dış kutusu geniş görünse bile
ARADA çok dar bir "bacak"/geçiş noktası taşıyabilir ve bugünkü AABB bunu
HİÇ yakalayamaz (kullanıcının bildirdiği daralmanın muhtemel kök nedeni —
hangi odanın ürettiği henüz doğrulanmadı, bu maddenin ilk adımı budur).

**Önerilen kapsam:**
- `STANDARDS['koridor'].min_short_edge_mm`: 1100 → 1500 güncellemesi
  (katalog DEĞERİ, `CONTRACT_VERSION` artmaz).
- Yeni bir arity-1 ölçüm fonksiyonu: poligonu bir eksen boyunca tarayıp
  HER kesitte gerçek serbest genişliği bulan "yerel en dar nokta" testi.
- Mevcut `context.json`'daki TÜM koridor/hol odalarının bu ölçümle
  taranıp "250mm" gözleminin gerçek kaynağının doğrulanması.

**Gelişmiş LLM fikirleri:** Kullanıcı gerçek bir TS/şartname belgesi
yüklediğinde LLM'in `STANDARDS` için yapılandırılmış bir güncelleme
önerisi (diff formatında, context'e otomatik YAZILMADAN) çıkarması; LLM'in
mevcut kataloğu tarayıp yeni bir mahal alt-tipi gerekip gerekmediğine dair
öneri üretmesi — nihai sayısal değer HER ZAMAN insan onayıyla girer.

**Açık kararlar:** yeni ölçüm fonksiyonu `standards/`e mi `architect/`e mi
eklenir (arity-1 olduğu için `standards/`e daha yakın durur, ama tarak/L
hol GEOMETRİSİ `architect/`in bugünkü konusu — kullanıcı kararı gerekir).

**İlişkili modüller:** `scripts/standards/`, `scripts/architect/`.

### DEV-050 — `walls/`+`openings/`+`architect/` — kapı/duvar/koridor endüstri standardı nüans kataloğu (15 madde)

- **Durum:** PLANNED

**Neden bu madde:** kullanıcının kendi talebi: *"bir kapı değer duvarın en
sonuna ya da başına gelecekse duvarın sonundan en az 10 cm duvar olmalı ki
kapı çerçevesini oturtacak mesafe kalsın. bunlar uygulama detaylarıdır ve
bunun gibi 15 tane endüstri standardı nüans belirlemeni istiyorum."*

**Önerilen kapsam (15 madde, HER BİRİ `standards`/`architect`in HER ZAMAN
UYARI politikasıyla):**

*`walls/`+`openings/` (arity-1, açıklığın KENDİ duvarına göre geçerliliği):*
1. Açıklık, duvarın başına/sonuna en az 100mm (10cm) kalmadan OLMAMALI
   (kasa/pervaz payı — kullanıcının kendi örneği).
2. Aynı duvardaki iki açıklık arasında en az 200mm düz duvar payı.
3. Pencere açıklığı bir dış köşeye çok yakınsa (<300-400mm) asgari köşe
   mesafesi.
4. Islak hacim kapısı ile yakınındaki pencere arasında asgari mesafe.
5. Çift kanatlı kapılarda asgari payanda/kasa derinliği.
6. Sürme kapılarda, kanadın kayacağı duvar yüzeyinde açıklık genişliği
   kadar boş yüzey gerekliliği.

*`openings/`+`standards/` (arity-1, mahal tipine göre asgari ölçü):*
7. Mahal tipine göre asgari kapı genişliği (WC/Banyo ≥700mm, yatak
   odası/salon ≥800-900mm, giriş ≥900-1000mm).
8. Koridor NET genişliği, üzerindeki kapı kanat genişliğinden en az
   100-150mm fazla olmalı.
9. Koridorun çıkmaz sonunda asgari dönüş payı (örn. 900×900mm).
10. Koridor T/L dönüşünde net genişliğin hiçbir kolda daralmaması.

*`architect/rules.py` (arity-2+, iki elemanın BİRBİRİNE göre ilişkisi):*
11. Kapı açıldığında kanat ile karşı yüzey arasında asgari boşluk
    ("kapılar açılırken karşı duvara çarpmamalı").
12. WC/Banyo kapısı varsayılan olarak KENDİ hacmine açılmalı, hole doğru
    AÇILMAMALI.
13. Daire giriş kapısı kendi birimine İÇE açılmalı, ortak hole doğru
    AÇILMAMALI.
14. Mutfak kapısı ile WC/Banyo kapısı aynı eksende karşı karşıya
    OLMAMALI (kullanıcının kendi örneği).
15. Giriş kapısı ile aynı birimdeki WC/banyo kapısı arasında asgari DÜZ
    MESAFE eşiği (bkz. `DEV-053`, ayrı bir madde olarak açılan AYNI
    nüans).

**Gelişmiş LLM fikirleri:** LLM'e `context.json` + üretilen preview/golden
rapor metni verilip "henüz kurala dönüşmemiş ama şüpheli duran noktaları
işaretle" diye serbest metin inceleme istenebilir (KOD DEĞİLDİR, yalnızca
önceliklendirme girdisi, `DEV-048` ailesiyle AYNI); LLM'den her nüans için
`rules.py` deseninde bir fonksiyon İSKELETİ (docstring+pseudocode)
üretmesi istenip insan geliştirici koda çevirebilir — eşik/ölçü asla
model tarafından UYDURULMAZ.

**Açık kararlar:** 15 madde TEK bir revizyonda mı, yoksa alt-gruplar
halinde (walls/openings arity-1 önce, architect arity-2 sonra) mı
uygulanacak — kullanıcı kararı gerekir.

**İlişkili modüller:** `scripts/walls/`, `scripts/openings/`,
`scripts/architect/`, `scripts/standards/`, `scripts/collision/`.

### DEV-051 — `openings/`+`collision/` — kapı açılımı ↔ kalan net geçiş genişliği dinamik kontrolü

- **Durum:** PLANNED

**Neden bu madde:** kullanıcının kendi örneği: *"daire içi kapıları
açılırken karşı duvara çarpmamalı, şu anda böyle sorunlar var (çoğu
koridor genişliğinin yetersiz olmasından kaynaklı)."*

**Mevcut durum:** `collision/` kapı açılım yayını (sector) bir ayak izi
olarak taşır ve SABİT bir elemanla (duvar/kolon/mobilya/başka kapı
sektörü) ÇAKIŞMAYI FORBID sınıfında yakalar — ama sektör hiçbir elemanla
çakışmasa bile, sektörün DIŞINDA kalan net geçiş genişliği insan geçişine
YETMEYEBİLİR (örn. 900mm'lik bir koridorda 800mm'lik bir kapı tam
açıldığında kalan boşluk pratikte kullanılamaz). `DEV-050`nin #3/#8/#11
maddeleriyle AYNI kapsamda, ama AYRI bir DİNAMİK ölçüm.

**Önerilen kapsam:** `openings::swing_geometry`nin ürettiği sektör ile
duvarın karşı yüzü arasındaki en dar mesafeyi hesaplayan, bir eşikle
(örn. 600-700mm) karşılaştıran yeni bir fonksiyon.

**Gelişmiş LLM fikirleri:** Ölçüm HER ZAMAN Python'da kalır; LLM'in rolü
`DEV-040` Fikir 1'in (severity-skoru) bu kurala da uygulanmasıyla "bu
ihlal ne kadar ciddi" açıklamasını üretmekle sınırlı — ham ölçüye
karışmaz.

**İlişkili modüller:** `scripts/openings/`, `scripts/collision/`,
`scripts/architect/`.

### DEV-052 — `architect/` — DEV-043'ün (banyo/wc kapı yakınlığı) gerçek adjacency ile gözden geçirilmesi

- **Durum:** PLANNED

**Neden bu madde:** kullanıcının kendi talebi: *"belirlenecek
standartlardan biri de banyo ve wc kapılarının mümkün olduğunda yan yana
olmasıydı bunu da gözden geçir."*

**Mevcut durum:** `DEV-043`/`check_wet_area_door_proximity` zaten VAR
(COMPLETED) ama kendi belgelenmiş bilinen sınırlaması gerçek ADJACENCY'yi
(ortak duvar paylaşımı) kontrol ETMİYOR, yalnızca kapı-orta-nokta mesafesi
ölçüyor; eşik (5000mm) gerçek projenin KENDİ verisinden türetilmiş bir
kalibrasyon, resmi bir atıf DEĞİL.

**Önerilen kapsam:**
- Gerçek ortak duvar/adjacency kontrolünün eklenmesi (mesafe yerine/ek
  olarak "ortak bir duvar paylaşıyorlar mı" testi).
- Eşiğin daha prensipli bir değere (tesisat şaftı genişliği + duvar
  kalınlığı) bağlanması.

**Gelişmiş LLM fikirleri:** Kullanıcı bir sıhhi tesisat şartnamesi
yüklediğinde LLM'in bu belgeden yapılandırılmış bir mesafe/adjacency kuralı
ÖNERİSİ çıkarması — nihai eşik HER ZAMAN `rules.py` sabiti olarak insan
onayıyla girer.

**İlişkili modüller:** `scripts/architect/` (`rules.py`, `DEV-043`).

### DEV-053 — `architect/` — giriş kapısı ↔ WC/banyo kapısı mesafe-tabanlı asgari eşik

- **Durum:** PLANNED

**Neden bu madde:** kullanıcının kendi talebi: *"daire giriş kapısının
çok yakınında wc kapısı olmaması gerektiği standardından bahsetmiştim bunu
da tekrar standartlar konusunda kontrol et."*

**Mevcut durum:** `architect/rules.py::check_entry_sightlines` yalnızca
AÇI (45° koni) + GÖRÜŞ HATTI (engelleyen duvar var mı) bakıyor — çok YAKIN
ama koninin dışında kalan bir WC kapısı bugün HİÇ yakalanmıyor, çünkü
mesafeye hiç bakılmıyor.

**Önerilen kapsam:** `architect/rules.py`ye yeni bir arity-2 fonksiyon,
`check_wet_area_door_proximity`in (DEV-043/DEV-052) AYNI "kapı orta nokta
mesafesi" ölçüm tekniğini yeniden kullanan, ama TERS yönlü bir eşik
(DEV-052/053 bilerek ARDIŞIK sıralandı — bkz. "Uygulama sırası" madde 4,
kalibrasyon çatışması riski baştan görülsün diye).

**Gelişmiş LLM fikirleri:** `DEV-040` Fikir 2 (bina tipi profilleri) ile
birleştirilip, konut DIŞI bina tiplerinde bu kuralın hiç anlamlı
olmayabileceğinin LLM'in profil-önerisi aşamasında işaretlenmesi.

**İlişkili modüller:** `scripts/architect/` (`rules.py`, `DEV-043`/
`DEV-052` ile AYNI aile).

### DEV-054 — `architect/`+`templates/` — hol topolojisi kütüphanesi (L şekli zorunluluğunun kaldırılması)

- **Durum:** PLANNED

**Neden bu madde:** kullanıcının kendi talebi: *"daire holleri L şeklinde
olmak zorunda değil, yerleşim planına göre değişiklik gösterebilir."*

**Mevcut durum:** rev-23'teki `uC_hol`un tarak (comb) şekli TAMAMEN EL
İLE `context.json`'a yazıldı — `templates/`/`architect/` bunu ÜRETMEDİ;
hol şekli seçimi bugün tamamen proje-operatör elinde, sistemsel bir "hol
topolojisi" kütüphanesi YOK.

**Önerilen kapsam:** `architect/` içinde (veya yeni bir alt modülde),
birim geometrisine göre uygun hol TOPOLOJİLERİNİ (düz/I, L, T, tarak/comb,
merkezi-hub) ÖNEREN (üretmeyen, yalnızca puanlanmış aday LİSTESİ
döndüren) bir fonksiyon — `options_for_core_placement` ile AYNI "hesapla,
puanla, model seçsin" deseni. rev-23'teki "comb" tasarımı bu kütüphanenin
bir aday topolojisi olarak GERİYE-kodlanabilir.

**Gelişmiş LLM fikirleri:** LLM yalnızca önceden hesaplanmış (alan/
sirkülasyon payı/sightline-uygunluk skoruyla etiketlenmiş) aday
topolojiler arasından SEÇER, yeni bir topoloji/koordinat İCAT ETMEZ.

**İlişkili modüller:** `scripts/architect/`, `scripts/templates/`.

### DEV-055 — `templates/`+`architect/`+`openings/` — sirkülasyon çekirdeğinin merkeze taşınması + asansör kapısı

- **Durum:** PLANNED

**Neden bu madde:** kullanıcının kendi talebi: *"kat planında sol üst
köşede merdiven ve asansör var fakat sağ üst tarafta kocaman bir ölü
bölge var, böyle olmamalı, istersen merdiven ve asansörü kat planının
ortasına yerleştirip, ortada dikdörtgen bir kat holü belirleyip 3 daireyi
ona uygun kata yayabilirsin ... asansör kapısını da çizmelisin."*

**Mevcut durum:** `templates::generate_circulation_core` çekirdeği HER
katta sabit güneybatı köşesine oturtur (`check_door_core_balance` bu
sabitliğin yarattığı dengesizliği ZATEN uyarı olarak yakalıyor — `DEV-040`
Fikir 4'ün bilinen sınırlaması). Kök `CLAUDE.md` bugün AÇIKÇA *"asansör
kapı sembolü çizilmez"* diyor — bu madde bu basitleştirmenin
KALDIRILMASINI gerektirir, dolayısıyla AYRICA bir kök-doküman kuralı
değişikliği + açık kullanıcı onayı gerektirir.

**Önerilen kapsam:**
- `templates::generate_circulation_core`'a bir yerleşim parametresi
  (`position: 'corner_sw' | 'center'`) eklenmesi.
- `architect/options.py::options_for_core_placement`'in GERÇEKTEN bu
  şablon fonksiyonunu çağırıp köşe/merkez adaylarını puanlaması (bugün
  çağırmıyor).
- `architect/study.py::resolve_unit_zoning`'in 1D sınırının, merkezi bir
  hol'ün ÇEVRESİNE 3 birimin dağıtılabileceği bir perimeter-tabanlı
  zonlamaya genişletilmesi (`DEV-054`'ün hol topolojisi kütüphanesinden
  bir "merkezi-hub" adayı SEÇİLEREK).
- Asansör kapısı: `openings/` şemasına gerçek bir açıklık girişi + basit
  bir sembol eklenmesi.

**Kabul ölçütü taslağı:** merkezi konumda `check_door_core_balance`
oranının düşmesi; yeni kat holünün `check_common_circulation_share`in
%15 sınırını AŞMAMASI.

**Gelişmiş LLM fikirleri:** Aday zon stratejileri (perimeter'i eşit açı/
eşit alan/cephe-önceliğine göre bölme) `options_for_core_placement` ile
AYNI "hesapla, puanla, model seçsin" deseninde üretilip LLM'e SEÇİM
yaptırılır; birim karışımı doğal dilden yapılandırılmış bir `UnitProgram`
listesine çevrilebilir; karmaşık 2D yerleşim için bir kısıt çözücü (örn.
OR-Tools CP-SAT) entegre edilip LLM yalnızca çözücünün ürettiği Pareto-
seçenekleri yorumlayan bir katman olabilir.

**Açık kararlar:** kök `CLAUDE.md`'nin "asansör kapı sembolü çizilmez"
kuralının kaldırılması AYRI bir kullanıcı onayı gerektirir.

**İlişkili modüller:** `scripts/templates/`, `scripts/architect/`,
`scripts/openings/`, `DEV-054` (ön koşul).

### DEV-056 — `architect/study.py` — etüt modülünün 2D yerleşim optimizasyonuna genişletilmesi

- **Durum:** PLANNED

**Neden bu madde:** kullanıcının kendi talebi: *"bina oturum alanını
efektif kullanmak en önemli konularımızdan biridir ve bundan sorumlu olan
temel birim etütleme işlemini yapan birimdir, o birim için özel tasarım
yaklaşımları planlayabilirsin."*

**Mevcut durum:** `resolve_unit_zoning` bugün yalnızca 1D (tek satırlık)
zonlama yapıyor (`architect/CLAUDE.md`'nin kendi bilinen sınırlaması). Bu
madde `DEV-040`'ı TEKRARLAMAZ, onun somut TETİKLEYİCİSİNİ ekler: `DEV-055`
(merkezi çekirdek) ve `DEV-054` (hol topolojisi) burada birleşir.

**Önerilen kapsam:** amaç fonksiyonu olarak "ölü alan minimizasyonu"
(`DEV-045`'in `check_common_circulation_share`i ile ölçülür) + "standart
uyumu maksimizasyonu" (`standards::check_room_proportions` + `architect/
rules.py`nin tüm arity-2+ kuralları) birleşik bir skor önerisi.

**Gelişmiş LLM fikirleri:** Çok-amaçlı optimizasyon için bir arama/ILP
çözücü (örn. OR-Tools CP-SAT) entegre edilip LLM'in yalnızca çözücüye
kısıt/ağırlık ÖNERİSİ (doğal dilden yapılandırılmış ağırlık vektörüne
çeviri) sunması; LLM'in geçmiş revizyonların (`context.json::rev_history`,
`requests.jsonl`) metnini okuyup kullanıcının tercih ettiği ödünleşim
türlerine dair bir profil çıkarması — yapılandırılmış veri olarak yalnızca
ÖNERİ aşamasında kullanılır, `context.json`'a otomatik YAZILMAZ.

**İlişkili modüller:** `scripts/architect/` (`study.py`), `DEV-054`,
`DEV-055` (ön koşullar), `DEV-040` (stratejik çerçeve).

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

### DEV-041 — `walls/`+`validate.py` — duvar ucu / kapı boşluğu çakışması denetimi

- **Durum:** COMPLETED (2026-09-28)
- **Özet:** Kullanıcının gerçek projede bizzat gördüğü "bir duvar kapının
  ortasında bitmiş" hatasını (`w_unit_A_B`, `uA_w_hol_mutfak_v`) yakalayan
  arity-1 kontrol `validate.py::check_walls`e eklendi — bu bir eleman
  sınıfları arası çakışma DEĞİL ("bir duvarın KENDİ bağlantısının geçerli
  olup olmadığı"), o yüzden `collision/`e değil buraya ait. İkinci bir
  açıklık-hesabı YAZILMADI: yeni `wall_gap_ranges` yardımcı fonksiyonu
  `walls.gaps_for_wall`i (bu modülün TEK açıklık kaynağı) DOĞRUDAN
  yeniden kullanır — rev-13'teki swing-geometry ikilemesi tekrarlanmadı.
  Yeni `point_position_on_segment` bir T-kesişim noktasının host duvarın
  hangi konumuna denk geldiğini (s-mesafesi) döner; bu konum bir kapı/
  pencere boşluğunun KESİN İÇİNDEYSE (sınıra/jamb'a denk gelmek GEÇERLİ)
  artık "sarkan uç" sayılır ve HATA verir. İlk kez `validate.py`nin
  kendi orkestrasyon kontrolüne odaklı bir selftest (`scripts/
  validate_selftest.py`) eklendi — önceden `check_walls` yalnızca zaten
  GEÇERLİ golden fixture'lar üzerinden dolaylı sınanıyordu, hata yolu
  hiç doğrudan test edilmemişti. Kasıtlı-bozma + yanlış-pozitif
  disiplini uygulandı: kapı boşluğuna giren uç HATA, boşluktan uzak
  normal bir T-kesişimi HATA DEĞİL, boşluğun tam sınırındaki (jamb) uç
  HATA DEĞİL (sınır eşitliği geçerli bir bağlantıdır), gerçek sarkan uç
  hâlâ eski mesajıyla yakalanıyor (regresyon yok), gerçek projedeki iki
  bilinen hata GERÇEKTEN yakalanıyor. **Bu görevin kapsamı o zaman
  yalnızca KONTROLÜ kurmaktı** — gerçek `context.json`daki iki hata
  **rev-23'te DÜZELTİLDİ** (`door_entry_1`/`door_entry_2`nin merkezleri
  kaydırıldı, bkz. `HD-025`); `python scripts/validate.py` artık gerçek
  projede BAŞARILI dönüyor. Ayrıntı: `scripts/walls/CLAUDE.md` "Bilinen
  sınırlar". (`HD-020`, düzeltme `HD-025`)

### DEV-044 — `rooms/` — içbükey (L/T-şekilli) odalarda mahal etiketi konumlandırması

- **Durum:** COMPLETED (2026-09-28)
- **Özet:** Fikir 1 (önerilen) uygulandı: `PolygonOps.pole_of_
  inaccessibility` — Mapbox'un `polylabel` algoritmasıyla AYNI
  deterministik izgara-arama yöntemi (üçüncü parti kütüphane YOK).
  `RoomLabeler.draw` artık centroid değil bu noktayı kullanıyor; sığdırma
  kutusu da (`PolygonOps.local_extent`) artık TAM AABB değil, capa
  noktasından dört eksen yönünde GERÇEK kenar kesişimine kadar ölçülen
  yerel açıklık. Convex/dikdörtgen bir odada davranış **BİREBİR AYNI
  KALDI** (arama her zaman centroid'i VE bbox-merkezini aday olarak
  dener; bir dikdörtgende bu ikisi zaten analitik maksimumdur) —
  `check_block_matches_raw_formula` (DEV-018'den, 1e-6 tolerans) TEK
  SATIR DEĞİŞMEDEN geçmeye devam etti. İçbükey `L_SHAPED_HOL` test
  fixture'ıyla (gerçek `uA_hol`/`uB_hol` ile AYNI kategori) kasıtlı bozma
  ile kanıtlandı: elle hesaplanan geometrik centroid (2165.93, 1515.93)
  poligonun DIŞINDA (çentikte) kalıyor, `pole_of_inaccessibility` HER
  ZAMAN içeride kalıyor. Yeni golden referans `golden/hol_l_sekli`
  eklendi; `golden_report.py::rule_room_labels` artık `PolygonOps.
  centroid` değil `RoomLabeler`in KENDİ kullandığı `pole_of_
  inaccessibility`i çağırıyor (DEV-041'deki `wall_gap_ranges` ile AYNI
  "tek kaynak" disiplini). `scripts/ceiling/`in RCP etiketi BİLİNÇLİ
  olarak kapsam DIŞINDA bırakıldı (`DEV-044`'ün "İlişkili modüller"i
  yalnızca `rooms/`/`architect/`/`pafta/`). Ayrıntı: `scripts/rooms/
  CLAUDE.md` "İçbükey oda etiket konumlandırması (DEV-044)". (`HD-021`)

### DEV-042 — `architect/` — ıslak hacmin mahremiyet odası üzerinden erişilmemesi kuralı

- **Durum:** COMPLETED (2026-10-02)
- **Özet:** Plan metninin kendi "Fikir 1"i uygulandı:
  `check_wet_area_reachable_without_bedroom` — birimin KENDİ hol/koridor
  odasından bir ıslak hacme (banyo/wc) bir yatak odasından GEÇMEDEN
  ulaşan EN AZ bir yol yoksa UYARI. "Açık kararlar"ın ikisi de çözüldü:
  graf, `rules.py`ye eklendi (ayrı `graph.py` açılmadı — kod küçük ve
  zaten var olan `_door_midpoint`/`_rooms_touching_point`i yeniden
  kullanıyor); test "HİÇBİR yol yatak-odasız değilse" semantiğiyle BFS
  (bir yatak odası "engelli düğüm") olarak yazıldı (otel gibi
  çok-erişimli birimlerde yanlış-pozitif üretmemek için). Graf BİLEREK
  yalnızca birimin kendi odalarıyla sınırlı. Kasıtlı bozma + yanlış-
  pozitif (doğrudan bypass) ile kanıtlandı; GERÇEK projede BEKLENMEDİK
  ama GERÇEK bir örnek yakaladı: rev-22 `uC`yi "salon-banyo-oda-hol"
  olarak yeniden sıraladı ama `uC_hol`ün TEK komşusu hâlâ `uC_oda`
  (yatak odası) — `uC_banyo`ya yatak odasından geçmeden ulaşan bir yol
  YOK, kullanıcının orijinal `koridor→hol→oda→banyo` şikâyetinin KISMEN
  hayatta kalan somut bir örneği (`uA`/`uB` TEMİZ). Bu görevin kapsamı o
  zaman yalnızca KONTROLÜ kurmaktı (DEV-041 ile AYNI disiplin) — `uC`nin
  GERÇEK düzeltilmesi **rev-23'te yapıldı** (kullanıcının "sen bir mimar
  olarak düşün, etüt yap, çalışmaya başlayabilirsin" talebiyle uC
  tamamen yeniden zonlandı, bkz. `HD-025`). Ayrıntı: `scripts/
  architect/CLAUDE.md` "DEV-042/DEV-043: ıslak hacim kuralları" ve "uC
  yeniden-zonlama (rev-23)". (`HD-022`, düzeltme `HD-025`)

### DEV-043 — `architect/` — banyo/wc kapı yakınlığı (ıslak hacim kümelenmesi) kuralı

- **Durum:** COMPLETED (2026-10-02)
- **Özet:** Plan metninin kendi "Fikir 1"i uygulandı:
  `check_wet_area_door_proximity` — aynı birimdeki ıslak hacim (banyo/wc)
  kapı-orta-nokta mesafesi `DEFAULT_WET_AREA_DOOR_MAX_DISTANCE`i
  (5000mm) aşarsa UYARI, `max_distance` override edilebilir. v1
  basitleştirmesi BİLİNÇLİ bırakıldı (yalnızca mesafe, gerçek adjacency
  kontrol edilmiyor — plan metninin kendi "Açık kararlar"ı). Eşik,
  gerçek projenin KENDİ uA/uB banyo-wc mesafesi (4016mm) sınırın ALTINDA
  kalacak şekilde kalibre edildi — `standards/`in kataloğuyla AYNI
  "pratik varsayılan" disiplini. Kasıtlı bozma + yanlış-pozitif + özel
  eşik testiyle kanıtlandı; gerçek projede (uA/uB) SIFIR uyarı
  (kalibrasyonun doğrudan kanıtı). Ayrıntı: `scripts/architect/
  CLAUDE.md` "DEV-042/DEV-043: ıslak hacim kuralları". (`HD-022`)

### DEV-046 — `stairs/`+`templates/`+`standards/` — merdiven oda oranı + çok kollu merdiven desteği

- **Durum:** COMPLETED (2026-10-02)
- **Özet:** Plan metninin "Fikir 1"i uygulandı: `stairs/`e `kind='dog_leg'`
  (sahanlıklı, 180° dönüşlü çift kol) desteği eklendi — oda kısa ekseni
  ortadan ikiye bölünür, basamaklar `ceil(step_count/2)`/kalan olarak iki
  kola dağıtılır, kol 1 girişten sahanlığa (`landing_depth_mm`, varsayılan
  1100mm) çıkar, kol 2 TERS yönde geri döner. `MIN_FLIGHT_WIDTH_MM=900`
  altında (yeni bir başarısızlık modu, tek kolda hiç yoktu) `StairFitError`.
  Gerçek `Merdiven` odası (4000×3000mm) bu türle 3000mm kat yüksekliğinde
  narrowing bile GEREKMEDEN, 4000mm'de hafif bir going-daraltmasıyla
  SIĞIYOR (elle hesaplandı, `selftest.py`de kanıtlandı) — tek kollu
  `StairFitError`in tam tersi. **"Fikir 2" (templates/standards
  kalibrasyonu) DEĞERLENDİRİLDİ, SAYISAL olarak GEREKMEDİ:**
  `standards::STANDARDS['merdiven']`in `[1.3, 2.4]` aralığı gerçek odanın
  oranıyla (1.333) ZATEN uyumluydu VE dog_leg için de anlamlı kaldı —
  yalnızca "tek kollu" diyen ESKİ etiket/açıklama metni düzeltildi,
  `templates::generate_circulation_core` DEĞİŞMEDİ. Convex/tek-kollu
  davranış 1e-6 değil TAM (bit-bit) korundu — `kind` verilmeyince eski
  kod yolu HİÇ DEĞİŞMEDEN çalışır (regresyon testi). Yeni golden referans
  `golden/merdiven_cift_kollu` eklendi; DXF çıktısı görsel olarak da
  doğrulandı (iki kol + sahanlık + bölücü + yön oku, mimari olarak
  doğru). `context.json`a gerçek `stairs[]` verisi BİLEREK EKLENMEDİ
  (DEV-041/044 ile AYNI disiplin — bu görevin kapsamı yalnızca MODÜL
  desteğiydi). Ayrıntı: `scripts/stairs/CLAUDE.md` "Çift kollu merdiven
  geometrisi (DEV-046)". (`HD-023`)

### DEV-047 — `stairs/`+`architect/` — merdiven sahanlık çıkış noktası ↔ koridor kapısı hizalaması

- **Durum:** COMPLETED (2026-10-02)
- **Özet:** Plan metninin "Açık kararlar"ı ÇÖZÜLEREK uygulandı:
  `StairResolution`a `exit_point`/`exit_direction` eklendi (HER İKİ
  `kind` için de dolu) — tek kollu için eski örtük varsayımla (odanın
  "yukarı" ucu) BİREBİR AYNI; çift kollu için merdiven GEOMETRİSİNDEN
  TÜRER ve kullanıcının öngördüğü gibi GİRİŞE yakın bir noktadır (odanın
  "yukarı" köşesi DEĞİL — 180° dönüş nedeniyle), yön `up_towards`in TAM
  TERSİDİR. "stairs/ mi architect/ mi" kararı: **`stairs/` HESAPLAR**
  (`exit_point`/`exit_direction`, arity-1), **`validate.py::check_stairs`
  DENETLER** (yeni opt-in `stairs[].exit_door_id` + `exit_door_
  alignment_warning` — UYARI, HATA DEĞİL, `architect/`in politikasıyla
  AYNI). "90 derece mi 180 derece mi" belirsizliği, mm hassasiyetli bir
  mesafe eşiği yerine TÜRDEN BAĞIMSIZ bir "en yakın oda kenarı" testiyle
  (`_nearest_bbox_side`) çözüldü — kapının duvar-merkez-çizgisi konumu
  `walls::Wall.centerline_point` (TEK kaynak) ile hesaplanır, `stairs/`
  `walls/`e bağımlı KALMAZ. `golden/merdiven_cift_kollu`, hizalı bir
  `exit_door_id` ile uçtan uca SIFIR uyarı ile geçer; `validate_
  selftest.py`de hizalı/hizasız/opt-in/geçersiz-id dört senaryo da
  kasıtlı bozma + yanlış-pozitifle kanıtlandı. Ayrıntı: `scripts/stairs/
  CLAUDE.md` "Çift kollu merdiven geometrisi (DEV-046)". (`HD-023`)

### DEV-045 — `templates/`+`architect/` — kat sirkülasyon bandının ölü alan analizi

- **Durum:** COMPLETED (2026-10-02)
- **Özet:** Plan metninin önerdiği GİBİ ikisi de uygulandı (Fikir 1
  DENETLER, Fikir 2 DÜZELTİR, `standards`+`templates`in DEV-036/037'deki
  ilişkisiyle AYNI desen). **Fikir 2 — kök neden düzeltmesi:**
  `templates::generate_circulation_core`nin `band_polygon`ı eski L-şekli
  yerine artık SADECE `corridor_leg_depth` derinliğinde bir dikdörtgen —
  çekirdeğin (asansör+merdiven) footprint'i zaten `y >= core_y0`de
  durduğu için bu TEK BAŞINA çakışmayı önlüyordu, L-şeklinin "doğuda tam
  `band_depth`" uzantısı hiçbir mimari ihtiyacı karşılamayan bir kalıntı
  idi. Bu projede `band` alanı 71.7 m² → 30.0 m²'ye düştü (41.7 m²'lik
  "ölü alan" KALDIRILDI) — `floor_width`e göre parametrize etmek
  GEREKMEDİ, basitleştirme TEK BAŞINA yeterliydi. **Fikir 1 — yeni
  denetim:** `architect::check_common_circulation_share`,
  `check_circulation_area_share`in (birim-içi) BİNA/KAT SEVİYESİNE
  genellenmesi — ORTAK (`unit_id`siz, `room_type='koridor'`) alan,
  kattaki TÜM birimlerin TOPLAM net alanına göre `DEFAULT_CIRCULATION_
  SHARE_MAX`i (%15, aynı sabit yeniden kullanıldı) aşarsa UYARI. İki
  fikrin GERÇEKTEN tutarlı olduğu kanıtlandı: gerçek projenin ESKİ
  `band`ıyla (71.7 m²) çalıştırılınca %27.6 pay ile UYARI üretiyor,
  DÜZELTİLMİŞ değerle (30.0 m²) çalıştırılınca pay %11.5'e düşüp UYARI
  KALKIYOR. Bu görevin kapsamı o zaman yalnızca KONTROLÜ kurmak VE
  `templates/`i düzeltmekti (DEV-041/044/046 ile AYNI disiplin) —
  gerçek `context.json`daki `band` verisi BİLEREK DEĞİŞTİRİLMEMİŞTİ.
  **rev-23'te GERÇEK projeye de UYGULANDI** (tüm 9 katta `band` 30.0
  m²'lik dikdörtgene çekildi, bkz. `HD-025`); "ölü alanın YERİNE ne
  konabileceği" (plan metninin kendi "Açık karar"ı) HÂLÂ GERÇEK bir
  tasarım kararıdır ve UYDURULMADI — boşalan alan hâlâ hiçbir odaya ait
  değil. Ayrıntı: `scripts/templates/CLAUDE.md` "DEV-045 düzeltmesi",
  `scripts/architect/CLAUDE.md` "DEV-045: ortak sirkülasyon payı".
  (`HD-024`, gerçek projeye uygulama `HD-025`)

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
