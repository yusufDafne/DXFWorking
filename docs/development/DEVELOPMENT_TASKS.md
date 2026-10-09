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
| DEV-048 | Mimari muhakeme yetisinin sistemleştirilmesi (şemsiye plan; 2026-10-05'te genişletildi, uygulama `DEV-059`…`DEV-070`) | PLANNED |
| DEV-049 | `standards/`+`architect/` — mahal/koridor standartları + yerel en dar nokta ölçümü | COMPLETED (2026-10-05) |
| DEV-050 | `walls/`+`openings/`+`architect/` — kapı/duvar/koridor endüstri standardı nüans kataloğu (15 madde + 16. duvar kalınlığı hiyerarşisi) | COMPLETED (2026-10-05) |
| DEV-051 | `openings/`+`collision/` — kapı açılımı ↔ kalan net geçiş genişliği dinamik kontrolü | COMPLETED (2026-10-05) |
| DEV-052 | `architect/` — DEV-043'ün (banyo/wc kapı yakınlığı) gerçek adjacency ile gözden geçirilmesi | COMPLETED (2026-10-05) |
| DEV-053 | `architect/` — giriş kapısı ↔ WC/banyo kapısı mesafe-tabanlı asgari eşik | COMPLETED (2026-10-05) |
| DEV-054 | `architect/`+`templates/` — hol topolojisi kütüphanesi (L şekli zorunluluğunun kaldırılması) | COMPLETED (2026-10-05) |
| DEV-055 | `templates/`+`architect/`+`openings/` — sirkülasyon çekirdeğinin merkeze taşınması + asansör kapısı | COMPLETED (2026-10-05) |
| DEV-056 | `architect/study.py` — etüt modülünün 2D yerleşim optimizasyonuna genişletilmesi | COMPLETED (2026-10-05) |
| DEV-057 | Kümülatif mini düzeltmeler (DEV-049…056 sırasında çıkanlar; seansın KAPANIŞ maddesi) | COMPLETED (2026-10-05) |
| DEV-058 | `shafts/` — şaft / havalandırma / baca boşlukları modülü | COMPLETED (2026-10-05) |
| DEV-059 | `spatial/` — ortak mekânsal sorgu katmanı (5 kopyanın tek sahibe taşınması; `DEV-048` Faz 1a önkoşulu) | COMPLETED (2026-10-09) |
| DEV-060 | `reasoning/` — muhakeme çekirdeği (mercek/veçhe/bulgu modeli, kayıt, kapsam raporu, `doc_check` kapıları; `DEV-048` Faz 1b) | COMPLETED (2026-10-09) |
| DEV-061 | `reasoning/` — mahremiyet mercek paketi (mevcut kuralların kaydı + yeni veçheler; Faz 2) | COMPLETED (2026-10-09) |
| DEV-064 | `reasoning/`+operatör talimatı — diyalog sözleşmesi + açıklama motoru + kök-neden kümeleme (Faz 2) | COMPLETED (2026-10-09) |
| DEV-065 | Şema + `reasoning/` — tasarım kararı kaydı (`design_decisions[]`), kanıta bağlı kabul (Faz 4) | PLANNED (sıra 5/12) |
| DEV-070 | `docs/agents/` — bilgi mühendisi rolü + büyütme protokolü (Faz 2) | PLANNED (sıra 6/12) |
| DEV-062 | `reasoning/` — ışık-hava-yönelim mercek paketi (Faz 3) | PLANNED (sıra 7/12) |
| DEV-063 | `reasoning/`+`furniture/` — yaşanabilirlik mercek paketi + deneme yerleşimi (Faz 3) | PLANNED (sıra 8/12) |
| DEV-066 | `reasoning/` — kalibrasyon, ayırt edicilik ve terfi (shadow→active) protokolü (Faz 4) | PLANNED (sıra 9/12) |
| DEV-069 | `brief/` — kullanıcı ihtiyaç beyanı ve mimari program toplama (Faz 6) | PLANNED (sıra 10/12) |
| DEV-068 | `impact/` — revizyon etki analizi (minimal patch planlama; Faz 6) | PLANNED (sıra 11/12) |
| DEV-067 | Tüm modüller — her modülün muhakeme katkısı (`reasoning.py` veya gerekçeli muafiyet; Faz 5) | PLANNED (sıra 12/12) |

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

### DEV-048 — Mimari muhakeme yetisinin sistemleştirilmesi (şemsiye plan; 2026-10-05'te genişletildi)

- **Durum:** PLANNED — bu bir "seç ve başlat" maddesi DEĞİLDİR, `DEV-040`
  ile AYNI kategoride bir STRATEJİK şemsiye plandır. **2026-10-05'te
  genişletildi:** teknoloji kararı verildi (hibrit, aşağıya bakınız), uygulama
  `DEV-059`…`DEV-070`e bölündü; hiçbiri `READY` değildir ve her biri kullanıcının
  açık talimatıyla başlar. Bu madde kendi başına kod TETİKLEMEZ.
- **Ayrıntılı plan (TEK kaynak):** `docs/development/ARCHITECTURAL_REASONING_PLAN.md`
  — bilgi modeli, etüt protokolü, diyalog sözleşmesi, üç ana mercek, genişletilebilirlik
  mimarisi, her modülün rolü, fazlar ve açık kararlar orada tutulur, burada TEKRARLANMAZ.

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

#### 2026-10-05 genişletmesi — özet

Kullanıcı talimatı (2026-10-05): *"bu geliştirilecek şey bir modül ya da yaklaşım
metodu olup tüm modülleri kapsayabilir, best practices yaklaşımı sen belirleyeceksin ...
kullanıcı seninle bir konuyu tartışacağı zaman olası problemleri ona uygun biçimde
ifade edeceksin, çok fazla teknik altyapıya girmeden nihai ürün üzerinden durumu
açıklayacaksın ... kullanıcı bazı şeyleri gözünden kaçırabilir bu yüzden sen onun
kapsamlı düşünen motoru olacaksın ... kurallar artırılabilmeli, her kuralın alt
örneklemleri de zamanla geliştirilebilmeli ... gelecekte gelişmiş bir dil modeli bu
modül bağlamında özel olarak bu mantıkları geliştirebilmeli, her modül için bu mantığı
düşün, her modülümüz bağımsız olarak geliştirilebilir olmalıdır."*

- **Karar (Aşama 2'nin açık sorusu ÇÖZÜLDÜ):** *bilgi bildirimseldir, hüküm
  deterministiktir, anlatım dildir.* (a) düz doküman **şimdi etkindir** (Faz 0: plan
  belgesi + kök `CLAUDE.md` işaretçisi); (b) script içi veri-odaklı modül
  `scripts/reasoning/` olarak kurulacak (çekirdek bilgi içermez, çizim modülü import
  etmez; bilgi sahibi modülde yaşar — `collision/` ters bağımlılık deseni);
  (c) harici teknoloji (RAG/vektör DB) bilinçli olarak SEÇİLMEDİ (gerekçe: plan §2.1).
- **Kavramlar:** **mercek** (bakış açısı; kural değil kurallar için çerçeve) →
  **veçhe** (alt örneklem; ölçülebilir tek soru) → **bulgu** (şiddet 0–1, kanıt,
  kararlı anahtar) → **tasarım kokusu** (adlı örüntü, kök neden, standart çıkış) ·
  **gerilim** (veçheler arası ödünleşim) · **profil** · **vaka** · **karar**.
- **Anayasa (8 madde, plan §2.3):** yalnız UYARI (FORBID yok); sayı uydurulmaz (şablonda
  rakam yok, yalnız kanıttan); "yapılamaz" denmez; sessiz geçiş yok (kapsam raporu);
  karar kullanıcınındır ve devredilebilir; proje verisi↔kütüphane ayrımı; bilgi epistemik
  statü taşır (`kesin`/`yaygın`/`tercih`); modül bağımsızlığı.
- **Bu oturumun üç ana konusu (plan §6):** **`mahremiyet`** (toplumsal; görsel, işitsel,
  geçiş, kademelenme, birimler arası, yaşam tarzı), **`isik_hava_yonelim`** (fiziksel-iklimsel),
  **`yasanabilirlik`** (işlevsel; mobilya sığar mı). Ayrıca 11 aday mercek kataloğu (plan §6.4,
  fikir statüsünde).
- **Ölçülmüş boşluklar (plan §1.1, gerçek proje rev-28):** 15 `UYARI` satırı yalnız 3
  tekil konu · kuzey yönü ve pencere yüksekliği verisi yok (yönelim/ışık oranı koşamaz,
  sistem bunu söylemiyor) · girişten görünen yatak odası kapısı (`uC`, 16.1°) ve
  komşu giriş kapıları 1485 mm yakınlıkta — **hiçbir mevcut kural bunları görmüyor** ·
  tefriş yerleşimi 0/9 kat · mekânsal sorgu yardımcıları 5 ayrı kopya.
- **Genişletilebilirlik:** yeni veçhe = bildirimsel kayıt + sahibi modülde ölçüm/kural +
  ≥1 ihlal ve ≥1 yanlış-pozitif vakası; terfi merdiveni `idea→draft→shadow→active`;
  `doc_check`e mekanik kapılar (her modül `reasoning.py` **ya da** gerekçeli muafiyet).
- **Gelecekteki gelişmiş dil modeli = "bilgi mühendisi"** (`DEV-070`): yalnız mercek
  kayıtları, modül-yerel `reasoning.py` ve vakalara yazabilir; şema/eşik-kaynaksız/anayasa
  yazamaz; final kabulü reviewer verir; **soğuk başlangıç sınavı** (plan §8.5) Aşama 5'in ölçütüdür.

**Alt görevler ve sıra (plan §10.1, 2026-10-09 denetimi sonrası, doğrusal):** `DEV-059` → `DEV-060` →
`DEV-061` → `DEV-064` → `DEV-065` → `DEV-070` → `DEV-062` → `DEV-063` → `DEV-066` → `DEV-069` → `DEV-068` →
`DEV-067`. İlk görünür kazanç 4. adımdadır (15 uyarı satırı → 3 konu). Denetimde 12 görevin 9'u olduğu gibi
uygulanamaz bulundu; düzeltmeler ve kullanıcı kararları her maddenin "Netleştirme soruları"nda, çapraz
bulgular plan §10.4'te.

#### Orijinal başlangıç planı (2026-10-02; beş aşama — aşağıdaki "Güncel durum" tablosuyla birlikte okunur)

**Başlangıç planı (beş aşama, 2026-10-05'te Faz 0'a eşlendi):**

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

**Güncel durum (2026-10-05) — aşama ↔ plan eşlemesi:**

| Aşama | Güncel karşılık |
| ----- | --------------- |
| 1. Envanter / örtük ilkeleri isimlendirme | Faz 0 **yapıldı**: plan belgesi §3 (kavramlar), §4 (etüt protokolü = "hangi kontrolü hangi sırayla"), §6 (üç mercek), §4.2 (ilk koku kataloğu) |
| 2. Bilgi tabanının yeri | **ÇÖZÜLDÜ** — hibrit (aşağıdaki not ve plan §2.1) |
| 3. Geri besleme döngüsü | plan §8.1 "Vaka → İlke → Veçhe" akışı; `DEV-060` (vaka formatı) + `DEV-070` (rol) |
| 4. Kalibrasyon/doğrulama | plan §7.3 terfi merdiveni + §8.3 ayırt edicilik; `DEV-066` |
| 5. Genişletilebilirlik/erişilebilirlik testi | plan §8.5 **soğuk başlangıç sınavı**; `DEV-070` |

> **GÜNCELLEME (2026-10-05): aşağıdaki açık karar ÇÖZÜLDÜ.** Alternatiflerin hiçbiri
> tek başına seçilmedi: (a)+(b) birlikte, (c)'ye açık. Gerekçe ve karar için "2026-10-05
> genişletmesi — özet" ve `ARCHITECTURAL_REASONING_PLAN.md` §2.1. Aşağıdaki metin
> TARİHSEL kayıt olarak korunur.

**[Tarihsel, 2026-10-02] Açık karar (kullanıcı AYRICA tartışacağını belirtti, BURADA
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

**Genişleyen ilişkili belgeler (2026-10-05):** `ARCHITECTURAL_REASONING_PLAN.md`
(ayrıntılı plan, TEK kaynak), `scripts/collision/CLAUDE.md` (ters bağımlılık +
`COLLISION_EXEMPT` emsali — `reasoning/` aynı deseni izler), `scripts/axis/CLAUDE.md`
(`AxisCoverageReport` emsali — muhakeme kapsam raporu), `docs/agents/`
(operatör talimatı §5 diyalog sözleşmesinin yaşayacağı yer; `DEV-070` bilgi mühendisi
talimatı). **`DEV-040`ın altı fikri bu plana oturur** (plan §10.2): şiddet sayısı →
bulgu modeli, bina tipi profilleri → `Profile`, katlar arası ilişkiler → aday
`tesisat_hijyen` merceğine girdi, `options_for_*` → `remedies`, proje bazlı profil →
yalnız profil SEÇİMİ, bilinçli göz ardı → `DEV-065`. `DEV-040` kendi başına kalır.

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

> **`DEV-059`…`DEV-070`** YEDİNCİ bir türdür: `DEV-048`in (2026-10-05'te genişletilen)
> şemsiye planından çıkarılmış uygulama maddeleridir; ayrıntı ve gerekçenin TEK kaynağı
> `ARCHITECTURAL_REASONING_PLAN.md`dir, burada TEKRARLANMAZ. `DEV-049`…`DEV-056` ile AYNI
> disiplin: **hiçbiri `READY` değildir**, her biri yalnızca kullanıcının açık talimatıyla
> başlar. `DEV-059`, `DEV-068` ve `DEV-069` plan çalışılırken **keşfedilen** ek
> modül/geliştirme fikirleridir (kullanıcı: *"ilave bir modül ya da geliştirme fikri
> keşfedersen görevlere ekleyebilirsin, başka bir agentic oturumda detaylı çalışırız"*).
> **Uygulama sırası (2026-10-09, kod denetimiyle yeniden belirlendi; doğrusal — aynı anda tek `IN_PROGRESS`
> görev olabilir, eski 'paralel' gösterimler geçersizdir):** **`DEV-059` → `DEV-060` → `DEV-061` → `DEV-064` →
> `DEV-065` → `DEV-070` → `DEV-062` → `DEV-063` → `DEV-066` → `DEV-069` → `DEV-068` → `DEV-067`**. Gerekçe ve
> kritik yol: `ARCHITECTURAL_REASONING_PLAN.md` §10.1; çapraz bulgular §10.4. Her madde aşağıda bu sırayla
> durur ve "Geliştirici yorumu / Netleştirme soruları / Metin düzeltmeleri" taşır; **madde ancak kullanıcı
> soruları tek tek yanıtlayıp `READY`ye aldığında başlar.** Her maddenin kabul ölçütü deterministiktir ve
> **mevcut `validate.py` çıktısını ve golden referansları bozmamak** ortak kabul şartıdır (`DEV-065`in şema
> sürümü uyarısı satırı bilinen tek istisnadır). Bölünmesi önerilen maddelerde parçalar **sayısal** yeni DEV
> kimlikleri olur (`doc_check` `### DEV-\d+` ister; `DEV-063A` gibi kimlikler görünmez kalır).

### DEV-065 — Şema + `reasoning/` — tasarım kararı kaydı

- **Durum:** PLANNED
- **Kapsam (plan §5.5; `DEV-040` Fikir 6):** `design_decisions[]` (üst seviye, opt-in,
  ekleme-yalnız): `id`, `finding_key`, `reason` (**zorunlu, boş olamaz**), `evidence_hash`,
  `ts`, `devredilmis`. **Kanıta bağlı kabul:** `evidence_hash` değişirse kabul düşer ve bulgu
  yeniden sunulur. Şema MINOR artışı (1.4.0); `validate.py` boş gerekçeyi HATA sayar (veri kalitesi;
  bulgunun kendisi yine UYARI); `rev_history` ile ilişki.
- **Şema değişikliği = sistem mimarı kararı** (plan §11 #3). **Kabul ölçütü:** kabul sonrası
  kanıt kötüleşince bulgu geri gelir, aynıysa sessiz kalır; boş gerekçe reddedilir; alanı
  olmayan eski context'ler KIRILMAZ (opt-in).
- **Önkoşul:** `DEV-060`, `DEV-064`.
- **Sıra:** 5/12 — plan §10.1; geliştirici yorumu ve netleştirme soruları 2026-10-09 kod denetimine dayanır (iki bağımsız ajan; `DEV-070` yalnız bir denetim).
- **Geliştirici yorumu:** Fikir doğru ve şema tarafı güvenli: opt-in üst seviye dizi 14/14 bağlamı bozmuyor. Üç düzeltme: (1) tek `finding_key`+tek `evidence_hash` K1–K5'in beş özdeş bulgusunu beş kayda böler → bir kayıt `covers[]` taşımalı; (2) `evidence_hash` tek başına 'kötüleşti' diyemez ve 'ne değişti'yi anlatıcıya veremez → ölçülen sayıların anlık görüntüsü de yazılır (anayasa 2: sayı yalnız kanıttan) ve v1'de herhangi bir değişim (iyileşme dahil) kabulü düşürür, yeniden sorulur; (3) bir LLM bu kaydı elle yazmamalı → `scripts/reasoning/decisions.py` yazıcı/okuyucu. Şema MINOR (1.4.0) `validate` çıktısına bir sürüm-uyarısı satırı ekler (15→16), bu 'çıktı bire bir aynı' ortak şartıyla çelişir: şartın istisnası yazılmalı. Bugünkü üç canlı uyarı (uB salon, uC banyo, uC hol payı) için hemen işe yarar. 'MAJOR kırılım' ve 'ekleme-yalnız denetlenemez' iddiaları aşırıydı (konvansiyon + `supersedes` + reviewer git-diff yeter).
- **Netleştirme soruları** (her biri önerilen varsayılanla; kullanıcı tek tek onaylayınca madde `READY` olur):
  1. Karar kaydı nerede yaşar? Öneri: `context.json` üst seviye `design_decisions[]` (anayasa 6, proje kopyalanırsa kararlar da gider).
  2. Bir kayıt N bulguyu kapsasın mı (`covers[]`: her biri finding_key+evidence_hash+evidence, ortak gerekçe)? Öneri: evet.
  3. Kanıt düşme kuralı v1: herhangi bir değişimde düşsün ve operatör 'önce → şimdi' sayılarıyla yeniden sorsun (yön-duyarlı kural sonra, kalibrasyonla)? Öneri: evet.
  4. Kayda yalnız `Plain.numbers` ile adlandırılan ölçülen değerlerin anlık görüntüsü de yazılsın mı? Öneri: evet.
- **Kullanıcı kararları (2026-10-09, netleştirme tamam; başlamak için kullanıcı onayı bekleniyor):** (1) kayıt `context.json` üst seviye `design_decisions[]` — EVET; (2) bir kayıt `covers[]` ile N bulguyu kapsar — EVET; (3) v1 kanıt düşme: herhangi bir değişimde (iyileşme dahil) kabul düşer, operatör 'önce → şimdi' ile yeniden sorar — EVET; (4) `Plain.numbers` ile adlandırılan ölçülen değerlerin anlık görüntüsü kayda yazılır — EVET.
- **Uygulama sonucu (2026-10-09, kabul bekliyor):** şema 1.4.0 (`schema/design.schema.json` üst seviye opt-in `design_decisions[]`, `scripts/version.py`), `reasoning/decisions.py` (anlık görüntü + hash, `make_decision`, `check_decisions`, `evaluate`), `validate.py`ye YALNIZ `check_decisions` kancası (+3 satır; çıktı aynı), `select_topics(..., decisions=)` + `narrate` "önce → şimdi", `reasoning_dialogue.py decide` (ve brief/append/verify karar farkındalığı), `reasoning` `CONTRACT_VERSION` 1.1, operatör/reviewer talimatları, plan §5.5. **Kanıt:** kabulden sonra rev-28 hol payı konusu sessiz (3 → 2 konu, "5 bulgu kabul edilmiş" notu); yalnız normal5'te ölçüm değişince (kötüleşme VE iyileşme) konu yalnız o katla, ilk sırada, "önce 16.3 → şimdi 16.4" ve gerekçeyle GERİ GELİR, anlatımdaki sayılar karar kaydı + bulgudan kaynaklı (karar kaydı olmadan "önce" sayısı kaynaksız sayılır); boş/boşluktan oluşan gerekçe `make_decision`, `decide` ve `validate.py`de reddedilir; alanı olmayan context aynı çıktıyı verir; `decide` yalnız ekleme yapar (diff: en çok kapanış satırı). `reasoning/selftest.py` 30/30; 6 kasıtlı bozma (hash'i yok say, boş gerekçe, kabul edileni sun, validate kancası, validate gerekçe denetimi, boş anlık görüntü) yakalandı. **Mevcut davranış değişiklikleri (kabul şartı istisnası):** `validate` çıktısı "sürüm uyarısı satırı hariç aynı": proje 1.3.0 / sistem 1.4.0 → `UYARI (surum)` satırı (15 → 16); konu kümelemesi ve `brief` bunu sunmaz (`legacy.surum` dışlandı); `NUMBER_RE` artık harfe bitişik rakamı (m2, uC_oda2) sayı saymaz (doğrulama sıkılaşmadı, yanlış-pozitif azaldı); selftest bir kontrol çökerse temiz FAIL yazar. **Kullanıcıya:** gerçek projenin `meta.schema_version` değerini 1.4.0'a çekmek ayrı bir proje revizyonudur (sürüm notu o zaman kalkar); bugünkü üç canlı uyarı için `decide` hazır ama proje verisine karar YAZILMADI. Kilit bırakıldı.

### DEV-070 — `docs/agents/` — bilgi mühendisi rolü ve büyütme protokolü

- **Durum:** PLANNED
- **Kapsam (plan §8):** `docs/agents/KNOWLEDGE_ENGINEER_AGENT.md` (rol, izin sınırı, veçhe
  ekleme kontrol listesi, Vaka → İlke → Veçhe akışı, terfi merdiveni, "yapmayacakların"
  listesi); `AGENT_PERMISSIONS.json`a `knowledge_engineering` girişi (yazabilir:
  `scripts/reasoning/lenses/`, `scripts/<modül>/reasoning.py`, `scripts/reasoning/cases/`,
  modül `CLAUDE.md`sinin "Muhakeme katkısı" bölümü; yasak: şema, `validate.py`,
  kaynaksız eşik, kaynaksız `kesin`, `context.json`, anayasa); `SYSTEM_DEVELOPMENT_AGENT.md`
  ve kök `CLAUDE.md`ye işaretçi; **soğuk başlangıç sınavı** tanımı + sınav vaka seti.
- **Kabul ölçütü:** sınavı **reviewer** (geliştirici dışı) yürütür: yeni bir ajan yalnız kök
  `CLAUDE.md` + plan/çekirdek `CLAUDE.md` ile üç vakada doğru teşhisi koyar, sayı uydurmadan
  anlatır ve `uC` kokusunu adıyla bulur. Geçmezse **bilgi eksiktir**, belge düzeltilir.
- **Önkoşul:** `DEV-060` + `DEV-061` (gerçek bir paketten damıtılır; protokol soyut yazılmaz).
- **Sıra:** 6/12 — plan §10.1; geliştirici yorumu ve netleştirme soruları 2026-10-09 kod denetimine dayanır (iki bağımsız ajan; `DEV-070` yalnız bir denetim).
- **Geliştirici yorumu:** NOT: bu madde için ikinci (çürütücü) ajan koşamadı (kullanım limiti); yorum tek denetime dayanır. Önkoşul `060`+`061`dir; eski sıradaki 'paralel' gösterim yanlıştı. Sınav (soğuk başlangıç) önkoşulsuz ayrı bir iş olarak çıkarılabilir — bugünkü belgelerle bile bir taban koşusu yapılır (yeni sayısal kimlik, öneri `DEV-071`). Sınavın soğuk kalması için mühürlü paket proje kökü içinde (kök CLAUDE.md kapsam kuralı), cevap anahtarı pakette değil; kararlılık için vaka başına 3 bağımsız koşu, ≥2'si bütün rubrik maddelerini sağlarsa geçer. Reviewer'ın rapor yazma izni yalnız `assigned-project/review-reports/` olduğundan `docs/development/reviews/` (ekleme-yalnız) izni eklenmeli.
- **Netleştirme soruları** (her biri önerilen varsayılanla; kullanıcı tek tek onaylayınca madde `READY` olur):
  1. Sınav ayrı numaralı maddeye (öneri `DEV-071`, önkoşulsuz) çıkarılsın ve `DEV-070` rol belgesi + izin + protokol olarak kalsın mı?
  2. Soğukluk: proje kökü içinde silinen mühürlü paket; yalnız çıkarma tarifi (commit+kat+komut) commit'lenir. Öneri: evet.
  3. Geçme kuralı: vaka başına 3 koşu, ≥2/3 tüm rubrik maddeleri; rapor model kimliği + belge commit'ini taşır; MINOR çekirdek değişikliğinden sonra yeniden koşulur. Öneri: evet.
  4. Reviewer rapor yeri: `review_validation.write`a `docs/development/reviews/` (ekleme-yalnız) eklensin ve `REVIEWER_VALIDATOR_AGENT.md`ye 'Sistem sınavı' bölümü (`DEV-064` aynı dosyayı da düzenler — sıra önemli). Öneri: evet.
- **Kullanıcı kararları (2026-10-09, netleştirme tamam; başlamak için kullanıcı onayı bekleniyor):** (1) soğuk başlangıç sınavı ayrı maddeye çıkarılır (öneri `DEV-071`, önkoşulsuz; kayıt `DEV-070` onayında açılır), `DEV-070` rol belgesi + izin + protokol — EVET; (2) soğukluk: proje içi mühürlü paket, yalnız çıkarma tarifi commit'lenir, cevap anahtarı pakette yok — EVET; (3) geçme: vaka başına 3 koşu, ≥2/3 tüm rubrik; rapor model kimliği + belge commit'i taşır; çekirdekte MINOR değişiklikten sonra yeniden koşulur — EVET; (4) reviewer raporu `docs/development/reviews/` (ekleme-yalnız), `review_validation.write`a eklenir, `REVIEWER_VALIDATOR_AGENT.md`ye 'Sistem sınavı' bölümü (`DEV-064` ile aynı dosya, sıra önemli) — EVET.
- **Metin düzeltmeleri (onayla birlikte uygulanır):** Önkoşul satırı 'DEV-060 + DEV-061' korunur, 'paralel' gösterimi her yerde silinir; sınav tanımı ayrı madde olabilir.

### DEV-062 — `reasoning/` — ışık-hava-yönelim mercek paketi

- **Durum:** PLANNED
- **Kapsam (plan §6.2):** `lenses/isik_hava_yonelim.py` — yaşam mahalli penceresi/dış duvarı,
  cephe tayini + çapraz havalandırma, ıslak hacim havalandırması (pencere **veya** şaft),
  yönelim veçheleri (`meta.north_angle` yoksa **koşamadı** ve kullanıcıya sorulur; yön
  uydurulmaz), pencere/taban oranı (yükseklik verisi gelene dek `draft`). Yeni mekânsal
  sorgular (`facade_of_wall`, `window_rooms`) `spatial/`e eklenir.
- **Şema:** ilk yarı şemasız; pencere yüksekliği için veri alanı **ayrı karar** (plan §11 #4,
  öneri: opsiyonel, opt-in alan; katalog varsayılanıyla uydurma YOK). Güneş yolu
  (enlem/boylam) kapsam DIŞI.
- **Kabul ölçütü:** `727405f` K1 `uC_oda` (değen pencere sayısı 0, doğrulandı) yakalanır,
  `7d32a2d` (1 pencere) temiz; rev-28'de penceresiz yaşam mahalli 0; `north_angle` yokken
  kapsam raporu "yönelim koşamadı: kuzey yönü verilmedi" der; `north_angle` verilen bir
  deneme vakasında yönelim veçhesi koşar. Yönetmelik rakamı kullanıcı kaynağı getirmeden
  `kesin` OLMAZ.
- **Önkoşul:** `DEV-060`, `DEV-070` (protokole uyularak yazılır — genişletilebilirliğin ilk
  kanıtıdır).
- **Sıra:** 7/12 — plan §10.1; geliştirici yorumu ve netleştirme soruları 2026-10-09 kod denetimine dayanır (iki bağımsız ajan; `DEV-070` yalnız bir denetim).
- **Geliştirici yorumu:** Bölme önerisi: (A) mevcut veriyle çalışanlar (pencere varlığı, çapraz havalandırma, ıslak hacim havalandırması), (B) `meta.north_angle` ister (gerçek projede yok → kapsam raporu 'koşamadı' der), (C) pencere yüksekliği ister (şema kararı). Gerçek projede 76 pencerenin 76'sı tek odaya düşüyor, dış duvarlar şaft boşlukları hariç `ext_*` ile birebir çıkıyor, rev-28'de penceresiz yaşam mahalli 0. Eksik tanımlar: 'yaşam mahalli' ve 'ıslak hacim' kümeleri kodda yok (mutfak ayrı mı?); ıslak hacim havalandırma veçhesi mevcut `shafts.check_shafts` ile çakışıyor (aynı soruyu iki yerde sormayalım); 'room_type'sız oda için 'temiz' ne demek, sınırı yazılı değil (sessiz geçiş yasağı). Kabul cümlesi '`7d32a2d` temiz' yaşam mahalli tanımına bağlı — tanım yazılınca doğru olur.
- **Netleştirme soruları** (her biri önerilen varsayılanla; kullanıcı tek tek onaylayınca madde `READY` olur):
  1. 'Yaşam mahalli' (pencere şart) ve 'ıslak hacim' kümeleri: öneri lens-yerel sabitler (`standards/`e değil; `RoomStandard` sözleşmesi değişmesin), salon+yatak odası pencere şart, mutfak ayrı kayıt, `yaygın` statüsü.
  2. `tesisat` türü şaft, ıslak hacim için havalandırma sayılır mı (gerçek projede yalnız `tesisat` var)? Öneri: evet, ≥300 mm ortak kenar (`shafts.check_shafts` ile aynı tanım, `DEV-059` sahibinden).
  3. Dış duvar/cephe tespiti: duvarın bir tarafında oda ve şaft dışında kalan bir prob noktası (kalınlık/2+10 mm). Çapraz havalandırma = ≥2 farklı dış normal yönünde pencere. Öneri: evet.
  4. Pencere yüksekliği: opt-in veri alanı (şema 1.4.0'a `DEV-065` ile birlikte). Öneri: evet; katalog varsayılanıyla uydurma YOK.
- **Kullanıcı kararları (2026-10-09, netleştirme tamam; başlamak için kullanıcı onayı bekleniyor):** (1) yaşam mahalli/ıslak hacim kümeleri lens-yerel sabitler (`standards/`e değil), 'yaygın' statüsü — EVET; (2) `tesisat` türü şaft ıslak hacim havalandırması sayılır (≥300 mm ortak kenar, `DEV-059` tanımı) — EVET; (3) dış duvar/cephe tespiti prob noktasıyla, çapraz havalandırma ≥2 farklı dış normal yönünde pencere — EVET; (4) pencere yüksekliği opsiyonel opt-in alan (`DEV-065` ile aynı MINOR), katalog varsayılanıyla uydurma YOK — EVET.
- **Metin düzeltmeleri (onayla birlikte uygulanır):** Kabul cümleleri üç profile (A/B/C) ayrılır; yaşam mahalli/ıslak hacim kümeleri yazılır; ıslak hacim havalandırma veçhesi için kabul eklenir ve `shafts.check_shafts` ilişkisi netleşir; 'room_type'sız oda kapsam raporunda 'ölçülemedi'.

### DEV-063 — `reasoning/`+`furniture/` — yaşanabilirlik mercek paketi + deneme yerleşimi

- **Durum:** PLANNED
- **Kapsam (plan §6.3):** `lenses/yasanabilirlik.py` + **deneme yerleşimi motoru**: oda
  tipinin tipik tefriş kümesinin (katalog ölçüleri `furniture/`te hazır) kapı sektörü ve
  kullanılabilir duvar uzunluğuyla birlikte **sığıp sığmadığını** sınar. Sonuç
  **türetilmiştir, `context.json`a yazılmaz**; çözüm önerisi değil **sınavdır** ("sığdı /
  sığmadı, hangi kapasitede"). Yerleşim kararı kullanıcınındır.
- **Fikir 1 — motor `furniture/` içinde** (katalog yakın, yeni modül yok). **Fikir 2 — yeni
  küçük `furnish/` modülü** (`furniture/` çizim/katalog sorumluluğu temiz kalır). **Açık
  karar** (öneri Fikir 2, `collision` ayak izi disipliniyle aynı gerekçe: çizim ≠ muhakeme).
- **Pay değerleri** (yatak çevresi, dolap önü) `yaygın` statüsündedir; doğrulanmadan
  kodlanmaz, "v1 pratik varsayılan" işaretlenir.
- **Şema:** değişmez. **Kabul ölçütü:** tefrişsiz rev-28'de her yatak odası için "sığar/
  sığmaz" cevabı üretilir (yorumsuz rapor); kasıtlı küçültülmüş oda yakalanır; yeterli oda
  yanlış-pozitif VERMEZ; tefrişi VAR projede `collision` ile çelişmez.
- **Önkoşul:** `DEV-060` (+ `collision` kapı sektörünün yeniden kullanımı).
- **Sıra:** 8/12 — plan §10.1; geliştirici yorumu ve netleştirme soruları 2026-10-09 kod denetimine dayanır (iki bağımsız ajan; `DEV-070` yalnız bir denetim).
- **Geliştirici yorumu:** Tek parça olarak uygulanamaz: motorun merkezi girdisi 'tipik tefriş kümesi' `furniture/`te yok (yalnız tip ölçüleri); 'pay' aynı cümlede hem yasak hem şart; oda çokgenleri duvar merkez çizgisinde olduğundan net ölçü (uC_oda 2950×3175 mm) kullanılmalı; kabulün üçü deterministik değil. İyi haber: yatak grubu kataloğu eksiksiz (25 yatak odası, 5 tekil), `collision` kapı sektörü olduğu gibi yeniden kullanılabiliyor. Öneri: v1 yalnız yatak odası; Katman A (pay=0, yalnız katalog ölçüsü + collision kuralı) hemen `shadow`; Katman B (rahat sığma payları) mimar değer verene dek `draft`, kod yok. Modül adı `testfit/` (`furnish/` ile `furniture/` arasındaki üç harf yazım tuzağıdır). Bölme 'A/B' ise sayısal kimlikle olmalı.
- **Netleştirme soruları** (her biri önerilen varsayılanla; kullanıcı tek tek onaylayınca madde `READY` olur):
  1. Motor yeri/adı: öneri Fikir 2, yeni modül `testfit/` (yalnız tüketir; çizim≠muhakeme ayrımı).
  2. v1 yalnız `yatak_odasi` mı? Öneri: evet (mutfak `counters[]` çakışma sağlayıcısı yok; WC/banyo `DEV-049/050` net ölçümleriyle iç içe).
  3. Tipik küme ve kapasite merdiveni: K1 çift yatak+2 komodin+gardırop, K2 çift yatak+gardırop, K3 tek yatak+gardırop, K4 tek yatak — kütüphane verisi, context'e yazılmaz.
  4. Geçiş payı politikası: A katmanı (0) shadow, B katmanı değerlerini mimar verene dek draft. Öneri: evet.
- **Kullanıcı kararları (2026-10-09, netleştirme tamam; başlamak için kullanıcı onayı bekleniyor):** (1) motor yeni modül `testfit/` (yalnız tüketir) — EVET; (2) v1 yalnız `yatak_odasi` — EVET; (3) tipik küme K1–K4 kapasite merdiveni (kütüphane verisi, context'e yazılmaz) — EVET; (4) A katmanı (pay=0) `shadow`, B katmanı mimar değer verene dek `draft` ve kodlanmaz — EVET.
- **Metin düzeltmeleri (onayla birlikte uygulanır):** 'Katalog ölçüleri hazır' → 'tip ölçüleri hazır, küme yok'; pay cümlesi iki katmana bölünür; net/merkez çizgisi uyarısı eklenir; Önkoşul satırı preambulle uyumlu hale getirilir.

### DEV-066 — `reasoning/` — kalibrasyon, ayırt edicilik ve terfi protokolü

- **Durum:** PLANNED
- **Kapsam (plan §7.3, §8.3):** ayırt edicilik raporu (golden seti + gerçek proje tetik
  oranı), yanlış-pozitif bütçesi, `shadow→active` terfi kontrol listesi, eşik güncelleme
  sözleşmesi (`standards/` ile aynı: değer güncellemesi sürüm artırmaz, alan şekli artırır),
  `provenance.reviewed` bayatlama listesi, sunum kuyruğu ağırlıklarının kalibrasyonu.
- **Kabul ölçütü:** ölçüm #6 gibi "her yerde öten" veçhe `shadow`da kalır ve rapor nedenini
  yazar; ayırıcı eklenince oran düşer ve terfi edebilir; bu rapor olmadan terfi mümkün
  değildir (`doc_check` #12'ye bağlı).
- **Önkoşul:** **≥2 mercek paketi** (`DEV-061` + `DEV-062` veya `DEV-063`) — tek paketle
  ayırt edicilik karşılaştırılamaz.
- **Sıra:** 9/12 — plan §10.1; geliştirici yorumu ve netleştirme soruları 2026-10-09 kod denetimine dayanır (iki bağımsız ajan; `DEV-070` yalnız bir denetim).
- **Geliştirici yorumu:** Olduğu gibi uygulanamaz: `DEV-061`in kabulü bu maddenin üreteceği 'ayırt edicilik raporu'nu ister, bu madde de `DEV-061`i ister (döngü). Çözüm: asgari terfi makinesi (konu başına ölçüm sözleşmesi + tetik oranı raporu + imzalı terfi kaydı + `legacy` bayrağı) `060`/`061`e çekilir; bu madde politikayı (sınırlar, yanlış-pozitif bütçesi, sunum ağırlıkları) taşır. Kapı #12 maddede yanlış anılmış (yalnız vaka varlığına bakar, ayırt edicilik denetlemez). Korpus zayıf: golden setin 13 referansında yatak odası/salon/giriş kapısı yok → ayırt edicilik yalnız gerçek projede 3 bağımsız birimle ölçülür; bu yüzden otomatik sayısal kapı değil, rapor + açık kullanıcı kararı + `HD` kaydı. '≥2 paket' önkoşulu teknik dayanaktan yoksun; asgari makine öne çekilince 061 ile birlikte ilk terfi mümkün olur.
- **Netleştirme soruları** (her biri önerilen varsayılanla; kullanıcı tek tek onaylayınca madde `READY` olur):
  1. Asgari terfi makinesi `060`/`061`e çekilsin mi (~1 oturum maliyet)? Öneri: evet; aksi halde `061` kabulü doğrulanamaz ve #4/#5 kullanıcıya 8. adımda ulaşır.
  2. Sayma birimi: tekilleştirilmiş uygun özne (özdeş katlar bir sayılır; 'koşamadı' paydadan çıkar, 'ölçülemedi' diye raporlanır, %0 değildir). 'Her yerde öten' sınırı kullanıcı tercihi (kaynak yok).
  3. Asgari örneklem: otomatik sayısal kapı yok; araç N'yi yazar ('3 bağımsız birim, kanıt zayıf'), terfi açık kullanıcı kararı + `HD` kaydı. Öneri: evet.
  4. Mevcut 6 adaptör `active`+`legacy` ve #12/#16 kapılarından muaf (yalnız `validate.py`nin zaten çağırdıkları). Öneri: evet.
- **Kullanıcı kararları (2026-10-09, netleştirme tamam; başlamak için kullanıcı onayı bekleniyor):** (1) asgari terfi makinesi `060`/`061`e çekilir, bu madde politikayı taşır — EVET; (2) sayma birimi tekilleştirilmiş özne ('koşamadı' paydadan çıkar, 'ölçülemedi' raporlanır) — EVET; (3) sayısal örneklem kapısı yok, araç N'yi yazar, terfi açık kullanıcı kararı + `HD` kaydı — EVET; (4) mevcut eski adaptörler `active`+`legacy`, #12/#16 kapılarından muaf — EVET.
- **Metin düzeltmeleri (onayla birlikte uygulanır):** Önkoşul 'DEV-060 + DEV-061' → 'DEV-059 + DEV-060 + DEV-061'; 'doc_check #12 terfi kapısıdır' ifadesi düzeltilir (yalnız vaka varlığı); '≥2 paket' önkoşulu gerekçesiz olduğundan kaldırılır ya da 'tercih'e çekilir.

### DEV-069 — `brief/` — kullanıcı ihtiyaç beyanı ve mimari program toplama

- **Durum:** PLANNED
- **Neden (plan çalışılırken KEŞFEDİLEN ek modül):** kullanıcı: *"mimar olmayan ama
  hayalindeki çizimi ortaya koymak isteyen kullanıcılar"* ve *"anahtar teslim proje."* Sistem
  bugün **çözüm** talebini işler ("banyoyu şuraya koy"); **ihtiyaç** ("dört kişilik aile,
  evden çalışıyorum, misafir sık gelir") kayıtlı değildir → bir kararın NEDEN alındığı
  izlenemez ve `yasam_tarzi` profilini besleyecek veri yoktur.
- **Kapsam taslağı:** sade dille ihtiyaç toplama akışı (kişi sayısı, misafir sıklığı, ev ofisi,
  erişilebilirlik ihtiyacı, araç sayısı, evcil hayvan …) → yapılandırılmış **ihtiyaç beyanı**
  (opt-in üst seviye alan; kullanıcı beyanı = gerçek proje verisi, UYDURULMAZ) → mimari
  program (`study.py` girdisi) ve profil seçimi; ihtiyaç → karar izlenebilirliği (`DEV-065`
  ile ilişkili).
- **Şema değişikliği → sistem mimarı kararı.** **Açık kararlar:** alan adı/yapısı; profille
  ilişki; zorunlu/opsiyonel sorular; kültürel varsayım içermeyen soru dili.
- **Önkoşul:** `DEV-060`, `DEV-064` (diyalog dili); `DEV-056` (etüt) girdisi.
- **Sıra:** 10/12 — plan §10.1; geliştirici yorumu ve netleştirme soruları 2026-10-09 kod denetimine dayanır (iki bağımsız ajan; `DEV-070` yalnız bir denetim).
- **Geliştirici yorumu:** Önce v0, şemasız: yalnız diyalog/dokümantasyon. Gerekçe: tüketicisi olan tek yol program düzeyi (`study_floor`: birim karışımı, hedef alan, kat sayısı); hane ihtiyaçları (misafir, ev ofisi) bugün hiçbir şeye bağlanmıyor. Kayıt kuralı: ihtiyaç cümleleri **yeni `requests.jsonl` satırı açmadan**, onları işleyen ilk revizyonun request metnine olduğu gibi girer (rev sayacı commit ile 1:1, kök CLAUDE.md Git §3). Sorular hepsi opsiyonel, 'bilmiyorum' ve 'sen karar ver' geçerli yanıt, hiçbiri üretimi bloklamaz. v1 şema alanı (üst seviye opsiyonel `brief`) ancak v0 en az bir gerçek konuşmada koşulduktan sonra eklenir. Giriş kataloğu mevcut alanları (`meta.north_angle` — `DEV-062` yönelim veçhesinin girdisi) kapsamalı. Bölme (a docs/diyalog, b `brief/` + şema, c profil+izlenebilirlik) yapılacaksa sayısal kimlikle.
- **Netleştirme soruları** (her biri önerilen varsayılanla; kullanıcı tek tek onaylayınca madde `READY` olur):
  1. Kapsam/kişi: (c) diyalogda her ikisi, ama v1 yalnız **program düzeyini** yapılandırır. Öneri: evet.
  2. v0 kayıt kuralı: ihtiyaç cümleleri ilk işleyen revizyonun request metnine aynen girer. Öneri: evet.
  3. Soru politikası: hepsi opsiyonel, 'bilmiyorum'/'sen karar ver' geçerli; yalnız birim programı ve kat ölçüsü bloklayıcı veri (`DEV-056` kararı).
  4. v1 yeri: üst seviye opsiyonel `brief` (emsal: `sections`), v0 koştuktan sonra; plan §2.3-6 buna göre düzeltilir.
- **Kullanıcı kararları (2026-10-09, netleştirme tamam; başlamak için kullanıcı onayı bekleniyor):** (1) diyalog program + hane ihtiyaçlarını konuşur, v1 yalnız program düzeyini yapılandırır — EVET; (2) v0: ihtiyaç cümleleri ilk işleyen revizyonun request metnine aynen — EVET; (3) soru politikası **kullanıcı sözleriyle:** 'birçok modülün default değeri var, hepsini opsiyonel yapabiliriz; efektif seçim yapılabilir ya da default değerlerle devam edilebilir' → HİÇBİR soru zorunlu değil (öneriden farklı: `DEV-056`nın 'birim programı ve kat ölçüsü bloklayıcı' ayrımı da kalkar); **uygulama notu:** kullanılan her varsayılan sessiz geçilmez, 'şu varsayılanla devam ettim' diye adıyla bildirilir ve yalnız kaynaklı katalog/modül varsayılanı olabilir (anayasa 3/5: sayı uydurma yok); modül varsayılanı bulunmayan bir değer varsa o noktada üretim yine durup sorar (kök CLAUDE.md 'belirsizlikte durma') — başlamadan önce kullanıcıyla teyit edilecek; (4) v1 üst seviye opsiyonel `brief`, v0 koştuktan sonra — EVET.
- **Metin düzeltmeleri (onayla birlikte uygulanır):** Kabul ölçütü ve önkoşul satırı yazılır (sert önkoşul yok: `DEV-056` tamam; v1 şema alanı `DEV-065` ile aynı MINOR'da gruplanabilir); 'Program study.py girdisi' → iki program düzeyi (oda: `study.py`, birim: `layout.py`).

### DEV-068 — `impact/` — revizyon etki analizi (minimal patch planlama)

- **Durum:** PLANNED
- **Neden (plan çalışılırken KEŞFEDİLEN ek modül):** kullanıcı: *"revize gerektiği zaman
  sadece ilgili noktalara revize yapabilen bir makine."* Bugün bir talep gelince hangi
  elemanların etkilendiği ve hangi kuralların yeniden doğrulanacağı **ajanın tahminidir**;
  `validate.py` her şeyi yeniden koşar (doğru ama bilgisiz). "Banyoyu büyüttüm — hangi duvar,
  kapı, şaft, komşu oda oranı, mahal etiketi, ölçü zinciri, üst/alt kat şaftı etkilendi?"
  sorusunun deterministik bir cevabı yok.
- **Kapsam taslağı:** eleman bağımlılık grafı (duvar ↔ oda ↔ kapı/pencere ↔ şaft ↔ etiket ↔
  ölçü) ve bir patchin dokunduğu eleman kümesinden **etki alanı** + **minimal patch planı**;
  muhakemede §4 adım 3'ün (mercek seçimi) ve adım 5'in (kör nokta taraması) deterministik
  kaynağıdır. Hesaplar, yazmaz.
- **Açık kararlar:** bağımlılık bilgisi nerede yaşar — modül-yerel beyan (`collision` deseni,
  önerilen) mi, merkezi graf mı? Kat arası etki (şaft/merdiven düşey) `DEV-040` Fikir 3 ile
  kesişir.
- **Önkoşul:** `DEV-059` (eleman ilişki sorguları); `DEV-060` tercihen. Bağımsız büyük iş.
- **Sıra:** 11/12 — plan §10.1; geliştirici yorumu ve netleştirme soruları 2026-10-09 kod denetimine dayanır (iki bağımsız ajan; `DEV-070` yalnız bir denetim).
- **Geliştirici yorumu:** İki iş tek başlıkta: (1) salt-okunur, deterministik **etki alanı raporu**, (2) 'minimal patch planı' — ikincisinin girdi/çıktısı yok (sistemde patch dili yok). Öneri: bu madde yalnız (1); (2) ayrı madde, patch grameri tanımlanınca. Düğüm = (kat, tür, id); duvar-id düğümü etki alanını bina düzeyine patlatır → duvar-kenar parçası ve açıklık orta noktası üzerinden bağ. Eksik kenar sınıfları: duvar-duvar T-bağlantı ve duvar-ucu↔açıklık-boşluğu (gerçek vakaların nedeni), kapı açılım sektörü, aynı birim, kat ikizi. Mutasyon denemesi: 62 mutasyondan 5'i doğrulama çıktısını değiştirdi (3 yalnız uyarı, 1 yalnız hata, 1 ikisi) ve hepsi 'kapının değen odaları' ailesinden; yeni sayı eklenmeyecek (tolerans `spatial/`ten). Kapsam/tamlık raporu şart (sessiz geçiş yasağı). Sıra: 059 sonrası, 10. adım; değer 'düşük' çünkü patch dili olmadan kullanıcıya doğrudan yansımaz.
- **Netleştirme soruları** (her biri önerilen varsayılanla; kullanıcı tek tek onaylayınca madde `READY` olur):
  1. Madde bölünsün mü (v1 salt-okunur etki alanı raporu; patch planı ayrı, patch grameri tanımlanınca)? Öneri: evet.
  2. Bağımlılık bilgisi: v1'de modül-yerel `impact.py` YOK; küçük açık-referans tablosu + mevcut collision ayak izleri; tablo şema alan adlarıyla tamlık kapısından geçer. Öneri: evet.
  3. Girdi: `blast_radius(context, dokunulan=[(kat,tür,id)])` ve `touched_from_diff(onceki, sonraki)`; patch grameri v1'de yok. Öneri: evet.
  4. Düğüm ayrıntısı: duvar-kenar parçası (span) + açıklık orta noktası; yeni tolerans sayısı eklenmez. Öneri: evet.
- **Kullanıcı kararları (2026-10-09, netleştirme tamam; başlamak için kullanıcı onayı bekleniyor):** (1) madde bölünür: v1 yalnız salt-okunur etki alanı raporu, patch planı ayrı sayısal kimlikle (patch grameri tanımlanınca) — EVET; (2) bağımlılık: modül-yerel `impact.py` YOK, küçük açık-referans tablosu + mevcut collision ayak izleri, tablo şema alan adlarıyla tamlık kapısından geçer — EVET; (3) girdi `blast_radius(context, dokunulan=[(kat,tür,id)])` + `touched_from_diff(önceki, sonraki)`, patch grameri yok — EVET; (4) düğüm = duvar-kenar parçası (span) + açıklık orta noktası, yeni tolerans sayısı yok — EVET.
- **Metin düzeltmeleri (onayla birlikte uygulanır):** 'Minimal patch planı' kapsamdan çıkar; `DEV-059` kapsamına duvar/oda-kenarı çakışma ailesi (`walls/thickness._on_edge`, `standards/measure.edge_wall_thicknesses`, `architect/layout._collinear_overlap`) eklenir; tamlık raporu kabule girer.

### DEV-067 — Tüm modüller — modül başına muhakeme katkısı (yaygınlaştırma)

- **Durum:** PLANNED
- **Kapsam (plan §9):** her modül için `reasoning.py` (ölçümleri/veçheleri bildirir) **ya da**
  gerekçeli `REASONING_EXEMPT`; her modülün `CLAUDE.md`sine standart "Muhakeme katkısı"
  bölümü (plan §8.4). Modül başına küçük, bağımsız oturum; önerilen sıra (plan §9 "sonraki en
  değerli veçhe" sütunu): `openings`, `walls`, `furniture`, `rooms`, `columns`, `axis`,
  `stairs`, `shafts`, sonra kalanlar.
- **Kabul ölçütü:** `doc_check` #10 temiz; her modülün bölümü şablona uyar; muaf modüllerin
  gerekçesi "düşünüldü, ölçüm/kural vermez" biçiminde yazılı.
- **Önkoşul:** `DEV-060`; paketler biriktikçe ilerler (tek seferde bitmez, rolling).
- **Sıra:** 12/12 — plan §10.1; geliştirici yorumu ve netleştirme soruları 2026-10-09 kod denetimine dayanır (iki bağımsız ajan; `DEV-070` yalnız bir denetim).
- **Geliştirici yorumu:** XL ve olduğu gibi planlanamaz: 'rolling, tek seferde bitmez' ifadesi tek-`IN_PROGRESS` kuralı ve tamamlanma kuralıyla çelişir. Çözüm: birinci dalga paketlere gömülür (architect, walls, openings, spatial → `061`; shafts → `062`; furniture, standards → `063`); bu madde yalnız dalga 2–3'ü (axis, stairs, columns, pafta, collision; sonra toplu muafiyet kararı) yürütür, `PENDING` listesini boşaltır ve kapı #10'u bloklayıcı yapar. Bugün 23 paketin 5'i sağlayıcı (collision.py), 18'i muaf adayı; muaf kaydı merkezi sözlük (`REASONING_EXEMPT`, `collision/scene.py::COLLISION_EXEMPT` idiomu) ve bu dosya `knowledge_engineering` yazma kapsamına girer. `reasoning.py` sözleşmesi tek biçimli olmalı (rol + ölçüm beyanı). Sıra, plan §9'da yazılı değil — bu dosyadaki sıra geçerli. En sona konmasının nedeni: bloklayıcı kapı ancak tüm modüller bitince açılabilir.
- **Netleştirme soruları** (her biri önerilen varsayılanla; kullanıcı tek tek onaylayınca madde `READY` olur):
  1. Kapı #10: üç durumlu (sağlayıcı / `EXEMPT[modül]=(rol, gerekçe)` / `PENDING`); `DEV-060` mevcut tüm paketleri bir kez PENDING tohumlar, liste yalnız küçülür, yeni paket doğarken (a) veya (b) olmak zorunda. Öneri: evet.
  2. Veçhe kaydı yalnız lens paketlerinde, modül `reasoning.py`si yalnız ROL+ÖLÇÜM beyanı (bkz. `DEV-060` soru 3). Öneri: evet.
  3. Muaf sözlüğü merkezi (`scripts/reasoning/providers.py`) ve `knowledge_engineering` yazma izni yalnız bu dosya. Öneri: evet.
  4. Defter tutma: dalga 1'i `061`/`062`/`063` emer; `067` yalnız kalan dalgalar. Öneri: evet.
- **Kullanıcı kararları (2026-10-09, netleştirme tamam; başlamak için kullanıcı onayı bekleniyor):** (1) kapı #10 üç durumlu (sağlayıcı / `EXEMPT` / `PENDING`), liste yalnız küçülür — EVET; (2) veçhe kaydı yalnız lens paketlerinde, modül `reasoning.py`si ROL+ÖLÇÜM beyanı — EVET; (3) muaf sözlüğü merkezi `scripts/reasoning/providers.py`, `knowledge_engineering` yazma izni yalnız bu dosya — EVET; (4) dalga 1'i `061`/`062`/`063` üstlenir, `067` yalnız kalan dalgaları yürütür — EVET.
- **Metin düzeltmeleri (onayla birlikte uygulanır):** Önkoşul 'DEV-060' → 'DEV-059 + DEV-060'; 'rolling' ifadesi silinir; `northarrow` sırası `DEV-062` ile çakışır (northarrow önce); 'şablona uyar' ve 'gerekçe yazılı' kabulleri deterministik hale getirilir (başlık+alan varlığı, boş olmayan gerekçe).

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

### DEV-049 — `standards/`+`architect/` — mahal/koridor standartları + yerel en dar nokta ölçümü

- **Durum:** COMPLETED (2026-10-05) — kullanıcı kabul etti ("49 onaylıyorum"). Ayrıntılı kayıt: `HD-026`. `context.json`/output'a DOKUNULMADI.

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

**Önerilen kapsam (uygulandı, bkz. aşağıdaki "Uygulanan"):**
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

### DEV-050 — `walls/`+`openings/`+`architect/` — kapı/duvar/koridor endüstri standardı nüans kataloğu (15 madde + 16. duvar kalınlığı hiyerarşisi)

- **Durum:** COMPLETED (2026-10-05) — kullanıcı kabul etti ("dev 50 kabul edildi"). Ayrıntılı kayıt: `HD-027`. `context.json`/output'a DOKUNULMADI (proje güncellemesi sekiz plan bittikten SONRA — kullanıcı kararı).

**Kullanıcı kararları (2026-10-05):** dış duvar varsayılanı 200 mm; daire↔daire
ortak duvarı da DIŞ duvar; mahal NET alanı duvar İÇ YÜZLERİ arasında
hesaplanır; mevcut proje sekiz plan sonrası güncellenir.

**Uygulanan (hepsi UYARI, hepsi opt-in/veriye bağlı; kod → test eşlemesi):**
- `openings/rules.py` — #1 duvar ucu 100 mm kati duvar (uçtaki dik duvarın
  yarım kalınlığı düşülür), #2 açıklıklar arası 200, #3 pencere–dış köşe
  350 (köşe = tüm duvarların sınırlayıcı kutusu), #5 çift kanat: 150 kasa
  payı + kanat başına ≥600, #6 sürme: bir yanda ≥ açıklık genişliği
  duvar yüzeyi, #11 kanat ucu–başka duvar yüzü ≥50 (`swing_geometry`
  kullanır; v1: yalnız kanat UCU noktası).
- `standards/nuances.py` — #7 mahal tipine göre kapı genişliği (wc/banyo
  700, yatak/salon 800, birim↔ortak alan giriş 900), #8 koridor NET
  genişliği ≥ kanat + 100 (kapı önünde, duvara dik kesit), #9 çıkmaz
  (≤1 kapı) koridorda 900×900 dönüş payı (v1 basitleştirme), #10 L/T
  koridorda kollar arası net genişlik farkı ≤100 mm (dik açılı poligon;
  `measure.arm_widths`).
- `architect/rules.py` — #4 ıslak hacim kapısı–aynı duvardaki pencere
  ≥600, #12 WC/banyo kapısı kendi hacmine açılır, #13 giriş kapısı birime
  içe açılır, #14 mutfak kapısı ↔ WC/banyo kapısı aynı eksende karşı
  karşıya olmaz.
- **#15 (giriş ↔ WC/banyo düz mesafe) bu maddede UYGULANMADI** — `DEV-053`
  aynı nüansı mesafe-tabanlı eşikle ele alır; tekrarlanmaz.
- **#16** `walls/thickness.py` (`classify_walls`, `check_wall_thickness`,
  `interior_thickness`): sınıf oda komşuluğundan türetilir (cephe veya
  farklı `unit_id`/birim↔ortak alan → dış; aynı birim → iç; ortak↔ortak →
  belirsiz, kontrol edilmez). Dış 200, iç dış−50. `standards/measure.py`
  `inset_polygon`/`net_area`: net alan. Kat başına TEK özet uyarı.
- `validate.py` hepsini UYARI olarak bağlar. Selftest'ler: `walls`,
  `openings`, `standards`, `architect` (elle hesaplanabilir + yanlış-pozitif +
  kasıtlı bozma).
- **Düzeltme:** bu maddenin 16. madde eki "projedeki tüm duvarlar 100 mm"
  diyordu — YANLIŞ: gerçek projede dış cephe 250, birim sınırı/band 200,
  birim içi 100 mm. Kalınlık uyarıları bu gerçek değerlerle üretilir
  (21 iç duvar 150'den, 4 cephe duvarı 200'den farklı).
- **Gerçek proje bulguları (UYARI, düzeltme YOK):** kapı genişlikleri
  (giriş 700<900, salon 700<800), WC kapılarında 0 mm kati duvar, `uC_hol`
  net 250–650 mm kollar, giriş kapıları ortak alana açılıyor, `uB_wc`
  hole açılıyor — bunlar proje revizyonu/DEV-054–055 alanı.
- **Açık kalan (DEV-057 birikimine yazıldı):** #9 gerçek çıkmaz-uç tespiti;
  #11 kanat boyunca (yalnız uç değil) açıklık; net alanın mahal etiketine
  (`rooms[].area_m2`) yansıması (proje verisi — proje güncellemesiyle).

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

*`walls/`+`standards/` — duvar kalınlığı hiyerarşisi (kullanıcı eki, 2026-10-05):*
16. **Dış ve iç duvar kalınlığı farklıdır; varsayılan fark 50 mm (5 cm).**
    Kullanıcı: *"dış duvarlar 20cm kalınlığında ise iç duvarlar 15cm
    kalınlığında olabilir. ne seçilirse seçilsin default olarak iç ve dış
    duvarlar arasında 5 cm fark olsun. daire duvarları ile kat holü
    duvarları arası da dış duvar kabul edilir."*
    - **Sınıflandırma:** *dış duvar* = bina dış cephesi + **birim (daire)
      sınırı ile ortak alan (kat holü/koridor) arasındaki duvar**; *iç
      duvar* = bir birimin kendi içindeki bölme duvarı. Sınıf, mahal
      `unit_id`/`room_type` komşuluğundan TÜRETİLİR (duvara elle etiket
      yazılmaz); kural `walls/` kataloğunda (`WallCatalog`/`kind`
      yaklaşımı) yaşar.
    - **Varsayılan:** dış = D, iç = D − 50 mm. Önerilen başlangıç
      D = 200 mm / iç = 150 mm (kullanıcı örneği); D seçilirse iç HER ZAMAN
      D − 50 olur. İki değer de proje verisi DEĞİL, kütüphane varsayılanıdır
      (tefriş/duvar kataloğuyla aynı konum); proje `walls[].thickness`
      ile AÇIKÇA ezebilir.
    - **Kontrol (UYARI):** bir duvarın bildirilen kalınlığı sınıfının
      varsayılanıyla uyuşmuyorsa veya iç duvar dış duvardan kalın/eşitse
      uyarı.
    - **Bugünkü proje:** `context.json`da cephe 250, birim sınırı/band 200,
      birim içi 100 mm; varsayılan (200/150) uygulanırsa kalınlıklar
      değişir → mahal net alanları/açıklıkları (DEV-049 net ölçümü) ve
      kapı/pencere yerleşimi etkilenir. Bu bir PROJE revizyonudur ve
      kullanıcı talimatı olmadan yapılmaz.

**Gelişmiş LLM fikirleri:** LLM'e `context.json` + üretilen preview/golden
rapor metni verilip "henüz kurala dönüşmemiş ama şüpheli duran noktaları
işaretle" diye serbest metin inceleme istenebilir (KOD DEĞİLDİR, yalnızca
önceliklendirme girdisi, `DEV-048` ailesiyle AYNI); LLM'den her nüans için
`rules.py` deseninde bir fonksiyon İSKELETİ (docstring+pseudocode)
üretmesi istenip insan geliştirici koda çevirebilir — eşik/ölçü asla
model tarafından UYDURULMAZ.

**Açık kararlar (16. madde):** (a) D varsayılanı 200 mm mi kalsın? (b) daire
↔ daire ortak duvarı "dış" sayılır mı (kullanıcı yalnızca daire↔kat holü
dedi; öneri: evet, yangın/ses yalıtımı gereği — onay gerekir); (c) kalınlık
değişince oda poligonları merkez çizgisinde kaldığı için mahal net alanı
nasıl raporlanacak; (d) mevcut 100 mm projeye ne zaman uygulanacak.

**Açık kararlar:** 15 madde TEK bir revizyonda mı, yoksa alt-gruplar
halinde (walls/openings arity-1 önce, architect arity-2 sonra) mı
uygulanacak — kullanıcı kararı gerekir.

**İlişkili modüller:** `scripts/walls/`, `scripts/openings/`,
`scripts/architect/`, `scripts/standards/`, `scripts/collision/`.

### DEV-051 — `openings/`+`collision/` — kapı açılımı ↔ kalan net geçiş genişliği dinamik kontrolü

- **Durum:** COMPLETED (2026-10-05) — kullanıcı kabul etti ("51 kabul"). Ayrıntılı kayıt: `HD-028`. `context.json`/output'a DOKUNULMADI.

**Kullanıcı kararları (2026-10-05):** (1) KONUT için varsayılan: kapılar
ODALARA doğru açılır (hastane/otel gibi kaçış planlı yapılar ileride ayrıca
incelenecek). (2) Çift kanatlı kapıda menteşeler DIŞTA (açıklık kenarlarında),
kanatlar ortada buluşur. (3) Sürme kapı açıldığında başka bir kapının alanına
ya da duvar dışına ÇIKMAMALI. (4) İhlaller UYARI; modül yeri agent'a bırakıldı.
**"Eşik" açıklaması:** eşik, kapı tam açıkken koridorda KALAN serbest geçiş
genişliğinin asgarisidir (koridor net genişliği − kanat genişliği); v1
varsayılanı 800 mm (agent seçimi, `OPEN_DOOR_MIN_PASSAGE_MM`, tek sabit).

**Uygulanan (hepsi UYARI) ve modül yeri gerekçesi:**
- `architect/rules.py::check_doors_open_into_rooms` — kapı bir koridor ile bir
  oda arasındaysa ve koridora açılıyorsa uyarı. `swing_policy="into_room"`
  varsayılan; `"any"` kapatır (gelecekteki kaçış planı politikaları için
  genişletme noktası). Islak hacim (#12) ve giriş kapısı (#13) o kurallarda
  zaten denetlendiğinden tekrarlanmaz. Yer: iki ELEMANIN (kapı + oda)
  ilişkisi → arity-2 → `architect/`.
- `standards/nuances.py::check_open_door_net_passage` — koridora açılan
  kapıda kalan geçiş < 800 mm ise uyarı. Yer: koridor NET genişliği ölçümü
  `standards/measure`dadır.
- `openings/rules.py::check_sliding_door_parking` — sürme kapı kanadı (açıklık
  genişliği kadar) iki yandan en az birinde duvar dışına taşmamalı, başka
  açıklık alanına ve başka kapının açılım sektörüne (`openings.collision.
  footprints`, çizilen yayla aynı kaynak) girmemeli. Yan seçimi UYDURULMAZ:
  iki yan da denenir. DEV-050 #6'nın yerini alır (aynı kural, dinamikleşti).
  Yer: `swing_geometry`nin sahibi `openings/`.
- Çift kanat menteşe invariantı: çizim zaten menteşeyi açıklık kenarlarına
  koyuyor; `openings/selftest.py::check_double_door_hinges_outside` bunu
  KİLİTLER (veri tarafında ayrı bir kural gerekmedi).
- Selftest'ler: `openings`, `architect`, `standards` (elle hesaplanabilir +
  yanlış-pozitif + kasıtlı bozma).
- **Gerçek proje bulguları (UYARI, düzeltme YOK):** 7 daire/dükkan kapısı
  koridora/ortak alana açılıyor (`uA/uB/uC_d_*_hol`, `door_entry_1`);
  koridora açılan kapılarda kalan geçiş 0 – 650 mm (`uC_hol` −150 mm: kanat
  koridordan geniş); sürme kapı uyarısı yok (projede sürme kapı yok).
- **Ek karar (kabul öncesi, 2026-10-05): dükkânlar konut KABUL EDİLMEZ,
  ayrı işlenir.** `room_type='dukkan'` (yeni `STANDARDS` tipi: yalnız en-boy
  ≤5, eşik UYDURULMADI; kapı asgari 900 mm). Konut "odaya açılır" kuralı
  dükkân kapısına UYGULANMAZ; yerine `architect::check_commercial_door_swing`
  (varsayılan `shop_swing_policy="outward"`: dükkân↔ortak alan kapısı kaçış
  yönünde ortak alana açılır, içe açılırsa UYARI; `"any"` kapatır).
  Mevcut projede dükkân odalarında `room_type` YOK (addan tahmin edilmez), bu
  yüzden `door_entry_1` uyarısı proje güncellemesine (`DEV-057`) kadar kalır.
- **Bilinen sınır:** sürme kanadı v1'de duvar kalınlığı derinliğinde dikdörtgen;
  `door_entry_1` gibi dükkân kapıları "oda" sayılır (konut varsayılanı).

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

- **Durum:** COMPLETED (2026-10-05) — kullanıcı kabul etti ("52 kabul"). Ayrıntılı kayıt: `HD-029`. `context.json`/output'a DOKUNULMADI.

**Kullanıcı kararları (2026-10-05):** (1) WC ve banyo ORTAK DUVAR paylaşır
(varsayılan; geliştirici aksini isterse kapatılır). (2) Asgari ortak uzunluk
YOK; ancak ıslak hacimler odalarla yan yana ise ıslak hacim kapıları oda
kapılarından mümkün olduğunca UZAK, WC↔banyo kapıları birbirine YAKIN olmalı.
(3) WC/banyo kapıları AYNI HATTA ve yan yana olmalı; sırt sırta/karşılıklı
OLAMAZ; yalnız duvar komşuluğu yetmez. (4) Şaft/havalandırma boşluğu
(WC–banyo arasındaki duvardan kare alan) şimdi KODLANMADI — "son plana dahil
et" (DEV-057 + fikir kaydı `DEVELOPMENT_IDEAS.md`: ayrı modül, şaft +
havalandırma + baca).

**Uygulanan (UYARI):** `architect/rules.py::check_wet_area_adjacency`
(`require_shared_wall=True` varsayılan): (a) ortak kenar paylaşımı (kenar
örtüşmesi >1 mm; köşe teması SAYILMAZ; asgari uzunluk yok); (b) iki odanın en
yakın kapı çifti aynı doğru üzerindeki duvarlarda değilse uyarı; (c) bir ıslak
hacim kapısının en yakın diğer-oda kapısına (aynı birimin salon/yatak/mutfak
kapısı; hol/giriş hariç) uzaklığı, kendi WC/banyo çiftine uzaklığından küçükse
uyarı — GÖRELİ kural, sayı UYDURULMADI. `check_wet_area_door_proximity`
(DEV-043, 5000 mm üst sınır) KORUNDU; eşik, şaft genişliği tasarlanana dek
değişmedi (kararı 4'e bağlı). `check_door_window_nuances` toplayıcısına dahil.
Selftest: elle kurulu plan (ortak duvar/aynı hat/uzaklık + sırt sırta + köşe
teması + `require_shared_wall=False`).
- **Gerçek proje bulguları (UYARI, düzeltme YOK):** `uA`/`uB`: WC ve banyo
  kapıları aynı hatta değil; ıslak hacim kapısı salon kapısına 966–1460 mm
  (çiftine 4776); `uC`: banyo ve WC ortak duvar paylaşmıyor (aralarında
  koridor şeridi var) ve kapıları aynı hatta değil.

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

- **Durum:** COMPLETED (2026-10-05) — kullanıcı kabul etti ("53 kabul"). Ayrıntılı kayıt: `HD-030`. `context.json`/output'a DOKUNULMADI.

**Kullanıcı kararları (2026-10-05):** (1) Kapı aralığı asgarisi = 100 mm kapı
çerçevesi + 150 mm priz/tesisat payı = **250 mm** (temiz aralık). (2) Kural
YALNIZ giriş kapısı ↔ WC/banyo kapısı içindir (mutfak vb. değil): daire kapısı
açılınca hemen ÖNÜNDE veya ÇAPRAZINDA WC kapısı olmasın — "yerleşim planı ile
çözülecek konu". (3) Mesafe DÜZ ÇİZGİ. (4) DEV-050 #15 bu maddeyle BİRLEŞTİ.

**Uygulanan (UYARI):**
- `architect/rules.py::check_entry_wet_door_proximity` — (a) giriş ↔ WC/banyo
  kapısı kenarları arası temiz aralık < 250 mm; (b) giriş yönüne göre önde/
  çapraz (60°'ye kadar, 3000 mm içinde, arada duvar yok) WC/banyo kapısı.
  `check_entry_sightlines`in dar konisi (≤45°) TEKRARLANMAZ (çapraz bandı
  45–60°). 3000 mm ve 60° agent varsayılanıdır (parametre), 250 mm kullanıcı
  kararıdır (`DEFAULT_DOOR_GAP_MIN_MM`).
- `openings/rules.py` — iki KAPI arası asgari 200 → **250 mm**
  (`DOOR_SPACING_MM`); kapı–pencere ve pencere–pencere 200 mm kaldı.
- Selftest: elle hesaplanabilir sapma açıları/mesafeler, yanlış-pozitif,
  kasıtlı bozma (50 mm aralık).
- **Gerçek proje:** bu iki kuraldan UYARI ÇIKMADI (giriş kapıları WC
  kapılarından yeterince uzak/çapraz bandın dışında).

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

- **Durum:** COMPLETED (2026-10-05) — kullanıcı kabul etti ("54 kabul"). Ayrıntılı kayıt: `HD-031`. `context.json`/output'a DOKUNULMADI.

**Kullanıcı kararları (2026-10-05):** (1) Aday şekiller kullanıcı bildirimi
olabilir (`allowed`); düz (I), L, T, merkezi kare, en-boy oranı korunan
dikdörtgen hub; **tarak varsayılan DEĞİL** (kullanıcı isterse). (2) WC
kapısının görünmemesi için KATI kural yok — yalnız yerleşim doğru olsun.
(3) Modül yeri agent'a bırakıldı → `architect/topology.py` (`options.py`
deseniyle aynı: aday katalogları orada). (4) Şimdilik dik açılı; açılı yapı
istenirse yeni geliştirme fikri — genişletilebilir yapı kuruldu
(`register_topology`).

**Uygulanan:** `architect/topology.py::options_for_hall_topology(unit_width,
unit_depth, entry_side, n_rooms, door_width, wall_thickness, hall_width,
allowed, hub_aspect_ratio, max_share)` → puanlanmış `HallOption` listesi
(birim-yerel koordinat, merkez çizgisi; hesaplar, ÇİZMEZ, context'e YAZMAZ).
Hol genişliği varsayılanı `STANDARDS['koridor']` net 1500 mm + duvar kalınlığı.
Puan (agent varsayılanı, sabitler tek yerde): kapı cephesi 0.40, hol payı
(%15 sınırı, `rules.DEFAULT_CIRCULATION_SHARE_MAX`) 0.35, oran
(`STANDARDS['koridor'].max_ratio`) 0.25, eşitlikte sade şekil. Sığmayan aday
`feasible=False` + gerekçeyle döner. Tarak/açılı şekil `register_topology`
ile eklenir; dik açılı olmayan şekilde kol/oran ölçümü atlanır
(`metrics['rectilinear']=False`).
- Selftest: elle hesaplanabilir alanlar (duz 14.4 m², L 21.44 m²), hub
  boyutları (1800², 2400×1600 = oran 1.5), giriş yönü dönüşümleri,
  `allowed`/bilinmeyen/tarak, sığmayan birim, genişletme noktası.
- **Bilinen sınır / DEV-055/056 girdisi:** puan yalnız hol geometrisini
  ölçer; oda yerleşimi/WC görünürlüğü puanlamaya KATILMAZ (kullanıcı kararı).
  Aday geometriyi `templates/`e çevirmek (DEV-055) ve etüdle birleştirmek
  (DEV-056) sonraki maddelerdir; bu madde `templates/` koduna dokunmadı.

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

- **Durum:** COMPLETED (2026-10-05) — kullanıcı kabul etti ("55 kabul"). Ayrıntılı kayıt: `HD-032`. `context.json`/output'a DOKUNULMADI.

**Kullanıcı kararları (2026-10-05):** (1) Kök `CLAUDE.md`'deki "asansör kapı
sembolü çizilmez" kuralı KALDIRILDI (eski kural, genel şablon çıkarırken token
yemesin diye konmuştu). (2) Asansör kapısı üç tür: kapı gibi açılan, sürgülü
(VARSAYILAN), büyük kapılar için ikili sürgülü; kuyu genişliğinden kenarlardan
20–30 cm daraltılır. (3) Kat holü en-boy oranı etüt biriminin kararı; 4–5
endüstri/best-practice alternatifi, sistem hepsini çizebilmeli; merkezde olmak
zorunda değil (biraz kayabilir); merkezdeyse daireler katı çevreleyebilir
(cephe penceresi). (4) Proje denemesi YOK: etüt planlayınca tüm birimler onun
çevresinde şekillenecek, aks sistemi yeniden çizilecek; **kısıt modülleri çizim
modüllerine değil, çizim modülleri kısıt modüllerine bağlıdır** (templates →
architect/standards).

**Uygulanan:**
- `openings`: `type='elevator_door'` (3 varyant; varsayılan `sliding`),
  `sliding_double` varyantı (iki panel, yay yok), `elevator.py`
  (`elevator_door_width`, `check_elevator_door_insets`: pay 200–300 mm),
  şema additif genişledi, lejant/preview/golden kuralı güncellendi,
  `CONTRACT_VERSION` 1.2. Kök `CLAUDE.md` kuralı kaldırıldı/yeniden yazıldı.
- `architect/core_hall.py::options_for_central_hall` — beş alternatif (kare,
  3:2, 2:1, 3:1 koridor, asgari koridor), puan: dört cephede daire payı
  (`surrounds`), hol payı (ideal %7/sınır %15), hol cephesi, merkezîlik;
  `offset`/`core_side`/`orientation`. Yalnız sayı hesaplar.
- `templates/central.py::generate_central_core` — geometri üretici (rooms
  `room_type` dolu, walls, merdiven + asansör kapısı, `zone`); `core_side` ve
  `orientation` dört kombinasyonda kapı yönleri doğrulandı (host_side XOR).
  `generate_circulation_core` (köşe) AYNEN kaldı; `templates` sözleşmesi 1.1.
- Selftest: elle hesaplanabilir alanlar/paylar (hol 24.81 m², asansör kapısı
  1600), yanlış-pozitif, kasıtlı bozma (kuyu genişliği kadar kapı), `validate.
  check_*` üretilen parçaya temiz, kata sığmayan blok.
- **Bilinen sınırlar / DEV-056 girdisi:** hol genişliği çekirdek genişliğine
  (6100) eşit (alternatifler yalnız derinlikte değişir; çekirdeği daha geniş/dar
  hol için ayrı bir yerleşim gerekir); asansör kapısı `single` iken açılım
  sektörü çakışma motoruna girer, sürgülü türler sektör üretmez; daire kapıları/
  odaları bu madde ÜRETMEZ (etüt, DEV-056). Gerçek projeye uygulama sekiz plan
  sonrası (DEV-057): aks, daire sınırları, mevcut 8 kat yeniden çizilecek.

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

- **Durum:** COMPLETED (2026-10-05) — kullanıcı kabul etti ("56 kabul"). Ayrıntılı kayıt: `HD-033`. `context.json`/output'a DOKUNULMADI.

**Kullanıcı kararları (2026-10-05):** (1) Ağırlıkları agent "optimum" seçer;
kullanıcı örnek çıktılara bakıp yorum yapacak, agent katsayıları zamanla
optimize edecek. Oturum alanı makul (20000×17500); kat başına 3 daire kurgusu
(2 adet 2+1, 1 adet 1+1) şimdilik kalır — bu veriler kat planı çizilirken
KULLANICININ kesinlikle sağlaması gereken veridir; dil modeli yalnızca "bu kat
oturum alanına kaç daire/kaç odalı olabilir" geri bildirimi verir. (2)
Deterministik ilerlenir; dil modeli sistemin yeteneklerini bilir, ona göre adım
atar, gerekirse geliştiriciden seçimini düzeltmesini ister. (3) Etüt, mimari
planın oluşturulabilmesi için etüdü SUNAR; bugün son kullanıcıya sunumu yok,
gelecekte kullanıcı yalnızca etüt isteyip adaylar arasından seçim yapabilir.
(4) Ağırlıklar başlangıçta agent seçimidir; kullanıcı geri bildirimiyle
iyileştirilir. (5) Yalnız ZONLAMA; daire içi bölüntü ayrı geliştirme fikri
(`DEVELOPMENT_IDEAS.md`'ye yazıldı). (6) Projeye bir şey YAZMA.

**Uygulanan:** `architect/layout.py` — `study_floor(floor_width, floor_depth,
program, weights, ...)`: DEV-055'in beş merkezi çekirdek+hol seçeneği × 16 halka
bölme deseni (köşe bölgeleri komşu iki kenardan birine verilir; H-x/H-y/rüzgâr
gülü dahil) × komşu bölüm birleştirmeleri (N daire için N ardışık yay; N>4 için
en büyük bölüm eşit bölünür) × birim ataması (N≤4 tüm permütasyon, N>4 alan
sıralı açgözlü). **Sert kapı:** her bölge hol cephesine ≥ kapı+2×250 mm temas
etmeli, alan ≥ tip asgarisi. **Puan** (`StudyWeights`, toplam 1.0, agent
başlangıç seçimi): alan uyumu 0.35, cephe 0.20 (yaşanabilir oda başına 3000 mm),
oran 0.15, hol payı 0.15, hol seçeneği puanı 0.15; simetrik/yer değiştirmiş
eşdeğerler elenir. Dikdörtgen bölgelere DEV-054 hol topolojisi önerisi eklenir.
`UNIT_TYPES` (1+1/2+1/3+1 asgari/ideal brüt alan: 50/62, 80/95, 110/130 m² —
"v1 pratik varsayılan"), `suggest_unit_mixes` (dil modeli geri bildirimi için
hesaplanmış karışımlar), `CURRENT_PROJECT_PROGRAM` (örnek girdi, VARSAYILAN
DEĞİL; program verilmezse/geçersizse `ValueError`). `architect/study_report.py`:
örnek çıktıyı yazdıran (dosyaya yazmayan) araç —
`python scripts/architect/study_report.py 20000 17500 2+1 2+1 1+1`.
- Selftest: halka desenleri kat alanını tam kaplar (294.49 m² + blok = 350),
  birleşim poligonu (L), yay sayısı, determinizm, puan = ağırlıklı toplam,
  ağırlık değişince puan değişir, geçersiz program, 8000×8000 katta aday yok,
  N=5 çalışır, karışım önerileri alanı aşmaz.
- **Örnek sonuç (20000×17500, 2+1, 2+1, 1+1):** en iyi aday `dikdortgen_3_2`
  hol, desen `0110`: 121.6 / 117.2 / 68.1 m² (puan 0.928; alan uyumu 0.80 en
  zayıf bileşen — ideal 95/95/62 m²'nin üstü, çünkü halka 294 m², toplam ideal
  252 m²). Bölme çizgileri desene bağlı sabit; sürekli kaydırma ile alan
  uyumunu artırmak ağırlık geri bildirimi sonrası yapılacak bir iyileştirmedir.
- **Bilinen sınırlar:** zonlama yalnız sınırlar (oda/kapı/duvar üretmez);
  `core_side='north'`/`orientation='x'` varsayılanı; L şekilli bölgelerde hol
  topolojisi önerisi yok; yön/offset taraması `offsets` parametresiyle.

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

### DEV-057 — Kümülatif mini düzeltmeler (DEV-049…056 sırasında çıkanlar; seansın KAPANIŞ maddesi)

- **Durum:** COMPLETED (2026-10-05) — kullanıcı kabul etti (A, B ve C grupları). Ayrıntılı kayıt: `HD-034`. Bilerek EN SONA konuldu. **Gruplar (kullanıcı onaylı
  sıra A → B → C):** A (ölçüm/eşik tutarlılığı: kalem 1, 2, 3) = COMPLETED
  (kullanıcı kabul etti, 2026-10-05); B (etüt iyileştirme + seçim kuralı: kalem 7)
  = COMPLETED (kullanıcı kabul etti, 2026-10-05); C (golden referans + şema
  sürümü: kalem 6'nın golden kısmı) = COMPLETED (kullanıcı kabul etti, 2026-10-05). Proje
  güncellemesine bağlı kalemler (4, 6'nın proje kısmı, 3'ün etiket kısmı) ve
  şaft modülü bu maddenin DIŞINDA.

**Grup B — uygulananlar (2026-10-05; kullanıcı kararı: etüt adayını dil modeli
kullanıcının talebine en yakın olana göre seçer, hiçbiri seçilemezse hol
binanın merkezinde olan sürüm seçilir):**
- `architect/layout.py` — **blok kaydırma iyileştirmesi** (`study_floor(refine=True)`):
  en iyi 12 yapı (hol + desen + gruplama + atama) için blok kat merkezinden
  1000 sonra 250 mm adımlarla (|kayma| ≤ 4000 mm) kaydırılıp puan yükselten
  kayma aranır (bölme çizgileri blok kenarlarından geldiği için hepsi sürekli
  kayar); merkezi (kaymasız) en iyi aday geri dönüş olarak listede HER ZAMAN kalır.
  `StudyOption.offset`/`structure` eklendi. Bu kat için 0.9283 → 0.9295 (kazanç
  küçük: halka alanı 294 m² > toplam ideal 252 m², fazlalık atılamaz).
- **Tercih + seçim:** `StudyPreference` (dil modelinin doğal dilden çevirdiği
  yapı: `unit_area_m2`, `unit_side` south/north/east/west, `hall` kimlik/aile
  kare|dikdörtgen|koridor, `centered_hall`), `preference_closeness` (0–1,
  deterministik), `select_study_option` (en yakın aday; yakınlık < 0.5 ya da
  tercih yoksa → merkezi hol geri dönüşü), `study_and_select` (genel aday
  havuzu 60). Geçersiz birim/yön/hol → `ValueError`.
- `study_report.py` tercih bayrakları (`--hall=`, `--area=`, `--side=`,
  `--centered|--shifted`) + seçim sonucunu yazdırır.
- Selftest: kaydırma puanı düşürmez + 0.9295, kayma sınırı, bölgeler + blok = 350
  m², determinizm, geri dönüş listede, alan yakınlığı elle (1.0 / 0.5), tercihsiz
  → merkezi, koridor tercihi koridor tipi, imkânsız tercih (3 birim kuzey) →
  geri dönüş, `centered_hall=False`, geçersiz tercih.
- **Bekleyen (kullanıcı geri bildirimi):** `StudyWeights`/`UNIT_TYPES`
  kalibrasyonu örnek çıktı yorumlarınızı bekliyor.

**Grup C — uygulananlar (2026-10-05; kullanıcı kararları: golden referansı
oluştur; `SCHEMA_VERSION` artır — "zaten projeyi de güncelleyeceğiz"):**
- `scripts/version.py`: `SCHEMA_VERSION` 1.0.0 → **1.1.0** (additif: `elevator_door`
  tipi + `sliding_double` varyantı; sürüm geçmişi yorumu eklendi;
  `DEFAULT_SCHEMA_VERSION` 1.0.0 kaldı). Etki: `meta.schema_version` hâlâ 1.0.0
  olan gerçek proje ve eski golden'lar her doğrulamada "geriye uyumlu fark"
  minör UYARISI verir (üretim sürer); gerçek projede 1.1.0'a çekme proje
  güncellemesiyle (ayrıca talep edilecek). `context.json`a DOKUNULMADI.
- **Yeni golden:** `golden/asansor_merkezi_cekirdek/` (context.json + expected.json).
  İçerik `templates::generate_central_core` çıktısıdır (elle yazılmadı):
  12000×12000 kat, `dikdortgen_2_1` hol, üç kat — varsayılan sürgülü (varyant
  yazılmadı: varsayılanı kanıtlar), `sliding_double`, `single` asansör kapısı;
  `schema_version` 1.1.0. Elle doğrulanan beklenen değerler: ARC = 4 (3 merdiven
  kapısı + yalnız `single` asansör kapısı; sürgülü türler yay çizmez), INSERT
  `MAHAL_ETIKET` = 9 (3 kat × 3 mahal), ATTRIB = 27; `--golden-set`, kapı sembolü
  kuralı dahil tüm semantik kurallar geçti.
**Grup A — uygulananlar (2026-10-05, kullanıcı yanıtları: oran/alan net: evet;
`STANDARDS` eşikleri net yorumlanır; DEV-050 ince ayarlarının ikisi de):**
- `standards::check_room_proportions`: en-boy oranı VE alan artık duvar iç
  yüzleri arası NET poligonla ölçülür (`inset_polygon`/`net_area`); `STANDARDS`
  eşik değerleri DEĞİŞMEDİ, NET olarak yorumlanır (kaynak metinleri/CLAUDE.md
  güncellendi); `walls` verilmezse eski davranış. `CONTRACT_VERSION` 1.1 → 1.2.
- `standards::check_dead_end_turning`: gerçek uç geometrisi — dik açılı
  koridorun her kolunun kısa uçları; uç duvarda VE kapısız ise ÇIKMAZ; bükey
  (başka kola bağlanan uç) çıkmaz sayılmaz; çıkmaz kolun net genişliği < 900 ise
  uyarı. `measure.arm_rects` (kol dikdörtgenleri) eklendi.
- `openings::check_door_leaf_clearance`: kanat BOYUNCA (menteşe→uç, 4 nokta)
  başka duvar yüzüne ≥50 mm; 'ucu'/'boyunca' raporlanır.
- Selftest: net oran 2.05 (brüt 2.0 temiz), net alan 7.41 m² (< 7.5), 800 mm
  çıkmaz kol uyarısı / 1000 mm temiz / iki ucu kapılı geçiş koridoru temiz / L
  büküm temiz, kanat boyunca 0 mm stub (eski uç-ölçümü göremezdi).
- **Gerçek proje etkisi (UYARI, düzeltme YOK):** yatak odası `uA/uB_oda1` net
  oran 2.02 (>2.0), `band` net oran 14–15 (>8), çıkmaz uçlar: `uA/uB_hol` 800
  mm, `uC_hol` 250/300 mm (aynı kollar daha önce başka kurallarla da işaretliydi).

**Neden (kullanıcı kararı, 2026-10-05):** *"bu sekiz geliştirme fikrini
gerçekleştirirken karşılaştığımız mini düzeltmeleri o geliştirme fikrine
ekleyerek kümülatif ilerleyeceğiz, en sonunda da o geliştirmeyi yaparak
seansı sonlandıracağız."* Her maddenin kendi kapsamı dışında kalan küçük
tutarsızlıklar/düzeltmeler anında kodlanmaz; BURAYA eklenir ve en sonda
tek seferde uygulanır. (İstisna: kullanıcı bir düzeltmeyi açıkça "şimdi
uygula" derse ilgili madde içinde yapılır ve burada yalnızca not düşülür.)

**Birikim listesi:**
1. *(DEV-049'da uygulandı, kayıt için)* Mahal/koridor açıklıkları duvar
   iç yüzlerine göre ölçülür — oran/alan kontrolleri (`min_ratio`/
   `max_ratio`/`min_area_m2`) HÂLÂ merkez-çizgisi AABB'sine dayanır;
   bunların da net poligona taşınması burada değerlendirilecek.
2. `STANDARDS` tip eşikleri (banyo 1500, yatak odası 2700, ...) merkez
   çizgisi varsayımıyla yazılmıştı; net ölçüme geçildiği için yeniden
   kalibre edilmeli mi? (`uC_oda` 2550 net, `band` 1300/1400 net uyarıları
   bu soruyu gündeme getirdi.)
3. *(DEV-050'den)* #9 çıkmaz koridor tespiti gerçek uç geometrisiyle
   (v1 yalnız kapı sayısına bakıyor); #11 kanat BOYUNCA duvar yakınlığı
   (v1 yalnız kanat ucu); net mahal alanının `rooms[].area_m2` etiketine
   yansıması (proje verisi, proje güncellemesiyle).
4. *(DEV-051'den)* Proje güncellemesinde ZK dükkân odalarına
   `room_type='dukkan'` eklenmesi (şimdi yok → `door_entry_1` konut
   kuralıyla uyarılıyor); ticari birimde kapı yönü/asgari ölçü eşikleri
   gerçek yönetmelikle güncellenecek.
5. *(DEV-052'den — kullanıcı: "son plana dahil et")* **Şaft/havalandırma/
   baca boşlukları:** WC–banyo arasındaki duvardan kare bir alan olarak
   planlanacak; şaft, havalandırma boşluğu, baca vb. için AYRI bir modül
   gerekebilir (bkz. `DEVELOPMENT_IDEAS.md`). Tamamlanınca
   `check_wet_area_door_proximity` eşiği (5000 mm) şaft genişliği + duvar
   kalınlığına bağlanarak yeniden kalibre edilir.
6. *(DEV-055'ten)* Gerçek projeye merkezi çekirdek/kat holü + asansör kapısı
   uygulaması (aks, kolon, daire sınırları, 8 kat yeniden çizilir);
   `golden/` altına asansör kapısı + merkezi çekirdek içeren mini referans
   (`expected.json` ölçümüyle). Asansör kapısı `type`/`variant` şema
   değişikliği additif olduğundan `SCHEMA_VERSION` minör artışı kararı.
7. *(DEV-056'dan)* **Etüt ağırlık optimizasyonu:** kullanıcı örnek
   çıktıları (`study_report.py`) yorumladıkça `StudyWeights` ve `UNIT_TYPES`
   alanları kalibre edilir; bölme çizgilerinin sürekli kaydırılması (alan uyumu
   iyileştirme) ve daire içi bölüntü (ayrı fikir) bu birikimdedir.
8. *(sonraki maddeler sırasında eklenecek)*

**Kullanıcı kararları (2026-10-05, DEV-057 soruları):** (1) Sekiz kalem bağlam
açısından büyükse ayrı/grup grup planlanır — agent gruplama önerisi sunar.
(2) **Proje güncellemesi (kalem 6'nın proje kısmı, kalem 4, kalem 3'ün etiket
kısmı) bu planın İÇİNDE YAPILMAZ; ayrıca talep edilecek.** (3) Etüt adayını
dil modeli kullanıcının talebine en yakın olanı seçer; hiçbiri seçilemezse hol
binanın MERKEZİNDE olan sürüm seçilir. (4) Şaft/havalandırma/baca modülü YENİ
geliştirme fikri olarak `DEVELOPMENT_IDEAS.md`de ayrıca tutulur (kalem 5 bu
maddeden çıktı). (5) DXF üretimi/preview henüz YOK.
**Agent'ın bu maddeyi uygulamadan önce açıkladığı sorular:** bkz. oturum notu —
kullanıcı "planı uygula" diyene kadar KOD YAZILMAZ.

**İlişkili modüller:** DEV-049…056'nın dokunduğu modüller.

### DEV-058 — `shafts/` — şaft / havalandırma / baca boşlukları modülü

- **Durum:** COMPLETED (2026-10-05) — kullanıcı talebiyle başlatıldı (fikir kaydı
  `DEVELOPMENT_IDEAS.md`, "Şaft / havalandırma / baca boşlukları modülü"). Ayrıntılı kayıt: `HD-038`.
- **Kullanıcı kararları (2026-10-05):** kapsam = türler + yerleşim KURALI (otomatik yerleştirme yok);
  üç tür, hepsi varsayılan net 500 mm; şaft oda DEĞİL, ayrı `floors[].shafts[]` verisi.
- **Özet:** Yeni `scripts/shafts/`; şema 1.3.0 (additif); `SAFT` katmanı; `validate.py`/`generate_dxf.py`
  entegrasyonu; projede K1–K5 şaftları `rooms[]`den `shafts[]`e taşındı. Kurallar `scripts/shafts/CLAUDE.md`.

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

### DEV-059 — `spatial/` — ortak mekânsal sorgu katmanı

- **Durum:** COMPLETED (2026-10-09) — kullanıcı onayıyla (dört netleştirme kararı) uygulandı. Ayrıntılı kayıt: `HD-040`.
- **Özet:** `scripts/spatial/` kuruldu; `architect`/`standards`/`shafts`/`rooms` kopyaları davranış korunarak taşındı (`spatial → collision.geometry`); doğruluk eski↔yeni diferansiyel selftest'le kanıtlandı çünkü `validate.py`/`--golden-set` bu yardımcılara kördür.

### DEV-060 — `reasoning/` — muhakeme çekirdeği

- **Durum:** COMPLETED (2026-10-09) — kullanıcı onayıyla (dört netleştirme kararı) uygulandı. Ayrıntılı kayıt: `HD-041`.
- **Özet:** `scripts/reasoning/` çekirdeği + `scripts/reasoning_report.py` + `doc_check` kapıları #10–#12, #14, #15 kuruldu; `validate.py` çıktısı değişmedi; çekirdek bilgi taşımaz (mercek paketleri `DEV-061`+).

### DEV-061 — `reasoning/` — mahremiyet mercek paketi

- **Durum:** COMPLETED (2026-10-09) — kullanıcı onayıyla (dört netleştirme kararı) uygulandı. Ayrıntılı kayıt: `HD-042`.
- **Özet:** `reasoning/lenses/mahremiyet.py` (14 veçhe, 3 koku) + `architect/privacy.py` + `architect/reasoning.py` + 22 sentetik vaka; `validate.py` çıktısı değişmedi; rev-28'de ölçüm #4/#5/#6 gölge olarak raporlanır.

### DEV-064 — `reasoning/`+operatör talimatı — diyalog sözleşmesi, açıklama motoru, kümeleme

- **Durum:** COMPLETED (2026-10-09) — kullanıcı onayıyla (dört netleştirme kararı) uygulandı. Ayrıntılı kayıt: `HD-043`.
- **Özet:** `reasoning/explain.py` (rakam lint'i, sunum kuyruğu, anlatım, `dialogue.jsonl`) + `scripts/reasoning_dialogue.py` + `doc_check` #13 + operatör/reviewer talimatları; `validate.py` değişmedi; rev-28 15 satır → 3 konu.
