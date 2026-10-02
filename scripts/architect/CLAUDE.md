# architect modülü (mekansal ilişki/mimari mantık kuralları) — DEV-039 + DEV-042 + DEV-043

Bir mahalin geometrik olarak GEÇERLİ (`validate.py::check_rooms`) VE
oransal olarak MAKUL (`standards::check_room_proportions`) olabileceği,
ama iki/N farklı elemanın **birbirine göre** mimari açıdan SAÇMA
olabileceği boşluğu kapatır: bir dairenin kapısı doğrudan merdivene
açılırken diğerleri izole bir yere açılıyor olabilir; daire kapısından
girince karşıda WC kapısı görünebilir; hol büyütülüp diğer odalar
küçültülmüş olabilir.

## Neden bu modül (kullanıcı talebi, 2026-09-28)

> "bu modül, mimarın gerçek anlamda yaptığı işi yapacak aslında,
> planlama ... gerçek bir mimar gibi düşünüp oda, koridor, wc, mutfak
> vs. her şeyin planını endüstri standardına uygun biçimde yapacak.
> örneğin endüstri standardında yazılı olmayan ama büyük oranda kabul
> gören bazı şeyler vardır."

Üç somut örnek verdi (bkz. `docs/development/DEVELOPMENT_TASKS.md`
`DEV-039`): kapı-çekirdek dengesizliği, giriş-WC görüş hattı, hol'ün
optimum tutulup diğer odaların öncelikli büyütülmesi — ve dördüncü bir
gereksinim: merdiven/asansörün "efektif" yerleşiminin bir dil modelinden
destek alınarak, ama **deterministik kalarak** seçilebilmesi.

## Arity ayrımı: `standards/`dan farkı NE

`standards/` bir odanın **kendi** oranının makul olup olmadığını
denetler (arity-1). Bu modül iki/N **farklı** elemanın birbirine göre
mantıklı olup olmadığını denetler (arity-2+) — `collision/`in
`rooms/`den ayrılmasıyla BİREBİR AYNI gerekçedir, sadece konusu fiziksel
ÇAKIŞMA değil mimari SAĞDUYU:

| Arite | Soru | Sahip |
|---|---|---|
| 1 (tekil) | "Bu odanın KENDİ oranı makul mü?" | `standards/` |
| 2+ (ilişkisel) | "Bu iki/N eleman BİRBİRİNE GÖRE mantıklı mı?" | **bu modül** |

## İç yapı: TEK modül, dört dosya

Kullanıcının tarif ettiği **etüt → mimari** akışı sıralı bir boru
hattıdır (etüdün çıktısı mimarinin girdisidir) ve ikisi de AYNI kelime
dağarcığını paylaşır. `pafta/` (`Sheet`+`PaperSizePlanner`+`CoverBlock`)
ve `elevations/` (`LevelStack`+`FacadeOpeningPlacer`) ile AYNI desen:
sıkıca ardışık, aynı bağlamı paylaşan sınıflar ayrı modüllere
BÖLÜNMEZ.

- **`rules.py`** — ilişkisel (arity-2+) WARN kuralları. Tek çizim/tek
  kütüphane dosyası olmayan tek dosya; diğer üçü buna bağımlı DEĞİLDİR
  (`study.py`/`options.py`/`design.py` şu an `rules.py`yi ÇAĞIRMAZ —
  puanlama/karar mantığı `options.py`de kendi başınadır; ileride bir
  entegrasyon gerekirse `rules.py` tek kaynak olarak kalır).
- **`study.py`** — etüt aşaması: `check_fits` (DEV-038'in ABSORBE
  edilen 1D sığma testi) + `resolve_unit_zoning` (kaba, tek satırlık
  bölge/zone ataması).
- **`options.py`** — seçenek kataloğu: `options_for_core_placement`,
  durumun somut verisine göre ön-puanlanmış, dil modelinin kimlikle
  SEÇEBİLECEĞİ bir liste döndürür.
- **`design.py`** — mimari aşaması: `place_unit_entry_doors`, bir
  `ZoningPlan`den kapı SÖZLÜĞÜ üretir (gerçek geometriyi KENDİSİ ÇİZMEZ).

## Politika: `standards/` ile AYNI — HER ZAMAN UYARI, asla HATA

Kullanıcı kararı (2026-09-28, üçüncü tur, "hayır"): mahremiyet kuralları
(giriş-WC görüş hattı, yatak odası-salon komşuluğu) DAHİL, v1'deki
**hiçbir kural** daha ciddi/bloklayıcı bir sınıfa çekilmedi. Eşikler
context.json'a YAZILMAZ (kök `CLAUDE.md`: "çizim sabiti context'e
sızmamalı") — katalog sabiti olarak `rules.py` içinde tanımlanır VE her
`check_*` fonksiyonu bir OVERRIDE parametresi taşır (kullanıcı:
"default bir oran olsun ama ihtiyaca göre esnetilebilsin").

## `rooms[].unit_id`: yeni şema alanı, OPT-IN

Eskiden "hangi oda hangi daireye ait" bilgisi YALNIZCA `id` ön eki
konvansiyonuyla (`uA_`, `uB_`, `uC_`) ÖRTÜKTÜ. Artık `rooms[].unit_id`
(opsiyonel string) AÇIKÇA bildirilir. **Bu modülün TÜM ilişkisel
kuralları `unit_id` OPT-IN'dir** (`room_type` ile AYNI desen) — alan hiç
verilmeyen bir odayı taşıyan proje bu kurallardan SESSİZCE hiçbir uyarı
ALMAZ (`selftest.py::check_opt_in_still_holds_when_unit_id_is_stripped`
bunu gerçek geometriyle kanıtlar). Kullanıcının kendi gerekçesi: bu alan
DEV-039'un ötesinde bir ALTYAPI ihtiyacı — gelecekteki "emsal" (imar
alanı oranı) hesabı da AYNI güvenilir gruplamaya bağımlı olacaktır.

**Gerçek projeye `unit_id` rev-21'de EKLENDİ** (`standards::room_type`in
rev-19'da ayrı bir revizyon olarak eklenmesiyle AYNI desen, id-önek
konvansiyonundan BİREBİR TÜRETİLEREK — uydurulmadı). Bu, `architect/
rules.py`nin dört kuralının artık gerçek projede GERÇEKTEN çalıştığı
anlamına gelir; ortaya çıkan UYARIlar (hol-oranı, giriş-WC görüş hattı,
kapı-çekirdek dengesizliği, yatak odası-salon komşuluğu) bkz.
`context.json::rev_history` rev-21 ve `DEVELOPMENT_TASKS.md` `DEV-039`
"Uygulama sırası" adım 14 notu. Bu uyarıların GİDERİLMESİ (rev-20 birim
tasarımının yeniden gözden geçirilmesi) AYRI, sonraki bir revizyon
konusudur — kullanıcı açıkça talep ettiğinde ele alınır.

## Oda-kapı komşuluğu nasıl bulunur

Bir kapının duvar-merkez-çizgisi üzerindeki orta noktası hesaplanır
(`rules._door_midpoint`), sonra `collision.geometry.point_on_boundary`
ile HANGİ oda(lar)ın poligon KENARININ bu noktaya değdiği bulunur
(`rules._rooms_touching_point`). Bu, projedeki poligon matematiğinin TEK
sahibini (`collision/geometry.py`) YENİDEN kullanır — ikinci bir kopya
YAZILMADI (rev-13'ün swing-geometri dersiyle AYNI disiplin: iki yerde
ayrı hesaplanan bir geometri sessizce ayrışır).

**"Giriş kapısı" tanımı VERİDEN türetilir, ayrı bir şema alanı
GEREKTİRMEZ:** bir kapı, bir tarafında `unit_id`li bir oda VE diğer
tarafında `unit_id`SİZ (ortak/sirkülasyon) bir oda varsa "giriş kapısı"
sayılır. Bu, gerçek projenin `band` (ortak koridor, `unit_id` yok) ↔
`uA_hol` (birim, `unit_id` var) geçişiyle doğrudan örtüşür.

## Giriş-WC görüş hattı: v1 basitleştirmesi (bilerek, dürüstçe belgelenir)

`check_entry_sightlines`, gerçek bir mimarın gözüyle yapılan tam bir
görünürlük analizi DEĞİLDİR (oda içi mobilya, kapı açılım yayı vb. hesaba
katılmaz — `standards`'ın AABB basitleştirmesiyle AYNI kategoride bir
v1 sınırı). Kontrol iki adımdır:

1. **Koni testi:** WC/banyo kapısının, giriş kapısının duvar normali
   yönünden `cone_degrees` (varsayılan 45°) içinde kalıp kalmadığı.
2. **Görüş hattı testi:** iki kapı orta noktası arasındaki DÜZ çizginin,
   (kapıların kendi duvarları HARİÇ) başka bir duvarın MERKEZ çizgisini
   KESİP kesmediği (`rules._clear_line_of_sight`,
   `rules._segments_intersect` — standart çapraz-çarpım kesişim testi).

## Public API

```python
from architect import (
    check_circulation_area_share, check_bedroom_via_corridor,
    check_entry_sightlines, check_door_core_balance,
    check_wet_area_reachable_without_bedroom, check_wet_area_door_proximity,
    DEFAULT_CIRCULATION_SHARE_MAX, DEFAULT_DOOR_CORE_BALANCE_RATIO,
    DEFAULT_WET_AREA_DOOR_MAX_DISTANCE,
    FeasibilityReport, check_fits, ZoneAssignment, ZoningPlan,
    resolve_unit_zoning, PlacementOption, options_for_core_placement,
    place_unit_entry_doors,
)
```

## `DEV-038`nin absorbe edilmesi

`DEV-038`'in "oda programı mevcut alana sığıyor mu" sorusu, etüdün ZATEN
yapması gereken İLK adımdır — sığmayan bir programı zonlamaya ÇALIŞMAK
anlamsızdır. `study::check_fits`, DEV-038'in "Fikir 1"inin (1D sığma
testi: istenen oda tiplerinin `standards.STANDARDS[...].
min_short_edge_mm` toplamı ile mevcut genişliğin karşılaştırılması)
BİREBİR kod hâlidir. `DEV-038` artık ayrı bir görev/PLANNED satırı
DEĞİLDİR — bkz. `DEVELOPMENT_TASKS.md`.

## `check_fits`/`resolve_unit_zoning`: `validate.py` akışının PARÇASI DEĞİL

Bu iki fonksiyon, bir ajanın `templates::generate_circulation_core` gibi
bir üreticiyi ÇAĞIRMADAN ÖNCE sorabileceği bir ÖN-KONTROLDÜR. Odalar
ZATEN üretilmişse bu kontrolün bir anlamı kalmaz — `standards::
check_room_proportions` zaten üretilmiş odayı denetler. Bu yüzden
`validate.py`ye entegre EDİLMEDİ; yalnızca `rules.py`nin dört `check_*`
fonksiyonu (arity-2+, ZATEN üretilmiş bir yerleşimi denetleyen) oraya
bağlıdır.

## `options.py`/`design.py`: geometri ÜRETMEZ, `templates/` ile AYNI sınır

`options_for_core_placement` ve `place_unit_entry_doors` salt `dict`/
dataclass döndürür — context dosyasına DOKUNMAZ, DXF çizmez, `ezdxf`
içermez. `options_for_core_placement` BUGÜN `templates::
generate_circulation_core`yi ÇAĞIRMAZ (o fonksiyon henüz bir `position`
parametresi taşımıyor — DEV-037'nin "Bilinen sınırlamalar"ı, bkz.
`DEVELOPMENT_TASKS.md` `DEV-039` "Kalan küçük teknik detaylar"); yalnızca
kose ADAYLARINI puanlar.

## Çakışma denetimi: EXEMPT

`collision/scene.py::COLLISION_EXEMPT` içinde. Gerekçe: bu modül HİÇ
`ezdxf` kullanmaz ve YENİ bir FİZİKSEL ayak izi ÜRETMEZ — `rules.py`
yalnızca zaten `rooms.collision`/`walls.collision`/`openings.collision`in
kapsadığı AYNI oda/duvar/kapı verisini OKUYUP birbirine göre (mesafe/
görüş hattı/alan payı) YORUMLAR; bu fiziksel ÇAKIŞMA değil mimari
SAĞDUYUDUR (yukarıdaki arite tablosu). `study/options/design` ise
`templates/` ile AYNI "hesaplar, çizmez" sınırındadır.

## Neden `golden_report.py`ye bir referans EKLENMEDİ (bilinçli karar)

`collision/CLAUDE.md`deki AYNI gerekçe: golden'ın sorusu "çıktı
beklenmedik şekilde değişti mi", bu modülünki "tasarım MANTIKLI mı".
`rules.py`nin dört fonksiyonu HİÇ geometri üretmediği/değiştirmediği
için (yalnızca UYARI metni döndürür, DXF'e hiçbir entity eklemez/
çıkarmaz) bir entity/layer/bbox karşılaştırması bu modülün mantığını
SINAMAZ — `selftest.py`nin kasıtlı-bozma testleri tek gerçek kanıttır.

## DEV-042/DEV-043: ıslak hacim kuralları

İkisi de aynı "ıslak hacim" temasındaki KOMŞU ama FARKLI kontrol
sınıflarıdır: DEV-042 erişilebilirlik (bir yola GİRMEK zorunlu mu),
DEV-043 kümelenme (iki kapı birbirine YAKIN mı). Her ikisi de diğer dört
kuralla AYNI politikayı (HER ZAMAN UYARI) ve AYNI `unit_id`/`room_type`
opt-in desenini izler.

### `check_wet_area_reachable_without_bedroom` (DEV-042)

Kullanıcının somut örneği: *"koridor -> hol -> oda -> banyo şeklinde bir
yol var, bu bir konut projesi ya da herhangi bir otel projesinde asla
kabul edilebilir bir mimari yaklaşım değildir."* `check_bedroom_via_
corridor` (DEV-039) bunu KAÇIRIYORDU çünkü SADECE "yatak odası SALONA
doğrudan açılıyor mu" diye bakıyor; "yatak odası, BAŞKA bir odaya
ulaşmak için ZORUNLU bir GEÇİŞ odası mı" sorusunu hiç SORMUYORDU.

**Bu bir graf gezinme problemidir** (diğer dört kuralın "iki komşu oda"
tek-adım testinden FARKLI bir karmaşıklık seviyesi) — plan metninin
kendi "Açık kararlar"ı burada ÇÖZÜLDÜ:

- **`architect/rules.py`ye mi, ayrı bir `graph.py`ye mi?** `rules.py`ye
  EKLENDİ, ayrı dosya AÇILMADI — bu modülün "sıkıca ardışık, aynı
  bağlamı paylaşan sınıflar ayrı modüllere BÖLÜNMEZ" mottosunun AYNI
  gerekçesi: graf kurucu (`_build_unit_adjacency`) ve BFS (`_reachable_
  avoiding`) birlikte ~35 satır, zaten var olan `_door_midpoint`/
  `_rooms_touching_point`i YENİDEN kullanıyor, bağımsız bir modül
  gerektirecek kadar büyümedi.
- **"TEK yol" mu, "HİÇBİR yol" mu?** Plan metninin önerdiği gibi
  "HİÇBİR yol yatak-odasız değilse" UYARI — otel gibi çok erişimli
  birimlerde YANLIŞ-POZİTİF üretmemek için BİLEREK böyle. Bir yatak
  odası "engelli düğüm" (`blocked_ids`) sayılarak BFS ile test edilir:
  birimin KENDİ hol/koridor odalarından başlayıp, yatak odası
  düğümlerine HİÇ girmeden ıslak hacme ulaşılabiliyor mu.

**Graf BİLEREK yalnızca bu birimin kendi odalarıyla sınırlıdır**
(`_build_unit_adjacency`, `unit_id` filtresi) — ortak/sirkülasyon alanı
veya başka bir birim DAHİL EDİLMEZ, çünkü soru "bu birimin KENDİ
holünden ıslak hacme gidilebilir mi"dir, bina genelindeki erişim
DEĞİLDİR.

**Gerçek projede GERÇEK bir örnek yakaladı (beklenmedik, ama dürüstçe
belgelenir):** rev-22 `uC`'yi "salon-banyo-oda-hol" olarak yeniden
sıraladı ve "oda artık hol VE banyoya kapı açıyor, salona DOĞRUDAN kapı
YOK" diye düzeltildiği kaydedildi — ama bu, `uC_hol`ün TEK komşusunun
HÂLÂ `uC_oda` (yatak odası) olduğu, dolayısıyla `uC_banyo`ya `uC_hol`den
yatak odasından GEÇMEDEN ulaşan bir yolun OLMADIĞI gerçeğini
değiştirmedi — kullanıcının orijinal şikâyetinin (`koridor→hol→oda→
banyo`) KISMEN hayatta kalan somut bir örneği. `uA`/`uB`'nin T-şekilli
hol'ü ise banyo/wc'ye DOĞRUDAN açıldığı için TEMİZDİR.
`selftest.py::check_wet_area_real_project_catches_uC_chain` bunu
kanıtlar. **Bu görevin kapsamı yalnızca KONTROLÜ kurmaktı** (DEV-041 ile
AYNI disiplin) — `uC`nin GERÇEK düzeltilmesi (hol'ü banyoya da doğrudan
açmak, veya farklı bir bant sıralaması) AYRI, sonraki bir revizyon
konusudur.

### `check_wet_area_door_proximity` (DEV-043)

Kullanıcının somut örneği: *"banyo wc kapıları genelde yan yana olur,
kapıları birbirinden çok uzak yapma mümkünse."* Aynı zamanda yaygın
kabul gören bir tesisat ekonomisi pratiğidir (ıslak hacimler AYNI duvar
hattı/şaftı paylaşırsa daha ucuzdur).

**v1 basitleştirmesi (bilerek, `check_entry_sightlines`in görüş-hattı
basitleştirmesiyle AYNI kategoride):** yalnızca kapı-ORTA-NOKTASI
mesafesi ölçülür, iki oda arasında GERÇEK bir ortak duvar (adjacency)
olup olmadığı KONTROL EDİLMEZ — plan metninin kendi "Açık kararlar"ından
biri buydu, BİLİNÇLİ olarak basit tarafta bırakıldı: mesafece yakın ama
araya başka bir oda/duvar giren bir YANLIŞ-POZİTİF üretebilir. Bu, diğer
v1 basitleştirmeleriyle (AABB oranı, görüş-hattı koni testi) AYNI
"pratik yeterli, mükemmel değil" disiplinindedir.

**Eşik kalibrasyonu (`DEFAULT_WET_AREA_DOOR_MAX_DISTANCE = 5000.0`):**
gerçek projenin KENDİ uA/uB banyo-wc kapı mesafesi (4016mm, rev-22'den
beri değişmedi) bu sınırın ALTINDA kalacak şekilde seçildi — bir
"pratik varsayılan" (`standards/`in kataloğuyla AYNI disiplin), metre
hassasiyetinde bir ölçüm DEĞİL. `uC` bu kuralda hesaba KATILMAZ (yalnızca
`uC_banyo` var, eşleşecek bir `wc` yok — "ikisi de varsa" ön koşulu
plan metninde zaten vardı).

## Doğrulama

`python scripts/architect/selftest.py` — yirmi yedi kontrol grubu: altı
`rules.py` fonksiyonunun her biri hem bir İHLAL hem (giriş-WC görüş
hattı için İKİ farklı: koni-dışı VE duvarla-engellenmiş; ıslak hacim
yakınlığı için ayrıca bir `max_distance` OVERRIDE testi) bir
YANLIŞ-POZİTİF senaryosuyla; `check_fits`/`resolve_unit_zoning`in elle
hesaplanabilir sonuçları (DEV-038'in gerçek keşfettiği 7700mm/8400mm
senaryosu DAHİL); `options_for_core_placement`in giriş kenarını YÜKSEK
puanladığı; `place_unit_entry_doors`in zone merkezlerine kapı koyduğu;
VE gerçek `context.json`'daki (rev-21'den itibaren gerçek `unit_id`
taşıyan) oda verisiyle hol-oranı ihlalinin VE `uC`'nin yatak-odası
zincirinin GERÇEKTEN yakalandığı, `uA`/`uB`'nin bu iki YENİ kuralda
TEMİZ kaldığı (`unit_id` bellek-içi SOYULDUĞUNDA opt-in'in hâlâ geçerli
kaldığı da ayrıca kanıtlanır).

## Gelecek yönü — 2. nesil mimari mantık motoru (planlama notu, 2026-09-28)

**Kullanıcının kendi çerçevelemesi (DEV-039'un commit'inden ÖNCE, uyarı
sisteminin gerçek projede çalıştığı doğrulandıktan SONRA verildi):**
*"bu programı gerçek bir mimar yapan en önemli yapı taşının temellerini
atıyoruz ... bu sistem aslında birçok mimari çizim konusunda ciddi
belirleyicilik ve kısıtlayıcılık oluşturacak, hatta müşteri taleplerine
göre bazı projelerin saçmalık seviyesi ya da imkansızlığı gibi durumlar
ortaya çıkacak gelecekte (imkansız diye bir şey yok tabii, müşteri
kapının önüne wc koy derse koyacağız 🙂 sadece örnek verdim)."*

Bu, `architect/`i bugünkü 4 kural + 4 dosyalık bir v1 modülden **projenin
uzun vadeli mimari karar motoruna** taşıyan bir yönelim talimatıdır —
henüz bir uygulama izni DEĞİLDİR, kod DEĞİŞMEDİ; bu bölüm yalnızca
FİKİRLERİ kayıt altına alır (bkz. `DEVELOPMENT_TASKS.md` `DEV-040`, bu
bölümü referans veren PLANNED bir üst-görev).

### Değişmez ilke: kısıtlayıcılık büyüdükçe, override disiplini de büyümeli

Kullanıcının "imkansız diye bir şey yok, müşteri isterse yaparız" notu
**tek bir örnek DEĞİL, bu modülün TÜM gelecek genişlemesi için bir
ANAYASA maddesidir.** Kural kataloğu büyüdükçe (aşağıdaki fikirler
onaylanıp eklendikçe) `architect/`in HİÇBİR kuralı, açıkça ayrı bir
kullanıcı kararı olmadan `collision/`in `FORBID` sınıfına ÇEKİLMEZ —
`collision/`in FORBID'i FİZİKSEL imkânsızlık içindir (iki cisim aynı
yeri işgal edemez); bu modülün konusu mimari SAĞDUYUDUR ve sağduyu,
tanım gereği, müşterinin bilinçli tercihiyle her zaman EZİLEBİLİR.
Yani: **modül ne kadar "ciddi belirleyici" hale gelirse gelsin, WARN
sınıfı ve override edilebilirlik SABİT kalır** — büyüyen şey kuralların
SAYISI ve KAPSAMIdır, ŞİDDET SINIFI değil.

### Fikir 1 — Uyarı şiddeti bir SAYI olsun (spektrum, hâlâ bloklamaz)

Bugün her `check_*` fonksiyonu ikili çalışıyor (eşiği aştı/aşmadı ->
UYARI var/yok). Kullanıcının "saçmalık seviyesi" ifadesi bunun bir
SPEKTRUM olabileceğine işaret ediyor: eşiği %1 aşan bir hol oranıyla
%300 aşan bir hol oranı bugün AYNI ağırlıkta bir UYARI metni üretiyor.
**Fikir:** her uyarı, mesajın yanında yapılandırılmış bir `severity`
(0.0-1.0, eşikten sapma oranına göre HESAPLANAN, uydurulmayan bir sayı)
taşısın — dil modeli/agent bunu "bu ne kadar ciddi, müşteriye nasıl
anlatmalıyım" diye SORABİLSİN (`options.py`nin "yapılandırılmış karar
noktası" desenindeki AYNI felsefe: sabit metin yerine HESAPLANMIŞ,
yorumlanabilir bir veri). WARN sınıfı DEĞİŞMEZ, yalnızca WARN'ın
İÇİNDEKİ bilgi zenginleşir.

### Fikir 2 — Bina tipi profilleri (`standards/`in izinden)

Bugünkü 6 kural TAMAMEN konut varsayımlarıyla yazıldı (`salon`,
`yatak_odasi`, `wc` gibi tipler). Kullanıcı konut/işyeri/fabrika/spor
salonu dedi — bunların HER BİRİNİN kendi ilişkisel mantığı olacaktır
(bir fabrikada "giriş-WC görüş hattı" muhtemelen ANLAMSIZ, ama "üretim
hattı-acil çıkış mesafesi" ANLAMLI olur). **Fikir:** `standards::
STANDARDS`in "mahal tipi -> eşik" sözlüğüyle AYNI desende, bina tipi
başına bir kural KÜMESİ (`RULESET_BY_BUILDING_TYPE` gibi) — v1'in konut
kuralları bunun yalnızca BİR profili olur, silinmez.

### Fikir 3 — Katlar ARASI ilişkiler (yeni bir arite boyutu)

Bugün `architect/` (`collision/` ile AYNI bilinen sınırlama) yalnızca
AYNI kat içinde çalışıyor. Gerçek mimaride bazı ilişkiler DÜŞEYDİR: ıslak
hacimlerin (banyo/wc/mutfak) üst-alt katlarda ÜST ÜSTE gelmesi (tesisat
şaftı ekonomisi), kolonların/taşıyıcı duvarların düşey hizası (bkz.
`columns/CLAUDE.md`'nin ZATEN not düştüğü "bilinen sınırlama"), merdiven
izdüşümünün her katta AYNI konumda olması (bugün `templates/` bunu
KONVANSİYONLA sağlıyor, DENETLEMİYOR). **Fikir:** `architect/`e bir
"vertical.py" bileşeni — `Scene`in `collision/scene.py::check_context`de
TÜM katları AYRI AYRI taradığı desenden FARKLI olarak, katlar ARASI bir
karşılaştırma yapan yeni bir fonksiyon ailesi.

### Fikir 4 — Seçenek kataloğunun (`options.py`) yaygınlaştırılması

Bugün yalnızca `options_for_core_placement` var. Kullanıcının "dil
modeli yeteneklerinin algılanması" ilkesi, HER önemli tasarım karar
noktasına genellenebilir: birim karışımı (kaç 1+1/2+1 dairesi), ıslak
hacim sütununun konumu, giriş cephesi seçimi gibi noktalar için kendi
`options_for_*` fonksiyonları. Her biri AYNI deseni izler: durumun somut
verisinden HESAPLANMIŞ, ön-puanlanmış, sonlu bir seçenek listesi — dil
modeli asla ham koordinat İCAT ETMEZ.

### Fikir 5 — Proje bazlı kural profili/eşik override'ı

`rules.py`nin bugünkü `max_share=`/`max_ratio=` gibi parametreleri kod
seviyesinde override edilebiliyor ama context.json'dan DEĞİL (kök
`CLAUDE.md`: "çizim sabiti context'e sızmamalı" ilkesiyle bilinçli).
Kullanıcı ileride PROJE bazlı bir esneklik isteyebilir (örn. lüks bir
projede hol payı %20 kabul edilebilir olabilir). **Fikir (dikkatli
değerlendirilmeli, ilkeyle GERİLİM içerebilir):** `meta.architect_profile`
gibi opsiyonel bir üst-seviye proje ayarı, yalnızca ZATEN var olan
sabitlerin hangi DEĞERİ alacağını seçer (yeni bir çizim sabiti İCAT
ETMEZ) — `meta.column_hatch`in kolonun taramasını seçmesiyle AYNI
kategoride, sabitin KENDİSİNİ değil HANGİ profilin kullanılacağını.

### Fikir 6 — Bilinçli göz ardı etmenin izi

Kullanıcı bir UYARI'yı BİLEREK kabul edip geçtiğinde (rev-21'de henüz
olmadı ama olacaktır) bunun GEREKÇESİ nerede kayıt altında kalacak?
Bugün yalnızca `requests.jsonl`/`rev_history`nin serbest metni bunu
taşıyor (yeterli olabilir). **Fikir (henüz net değil, tartışmaya açık):**
`context.json`da yapılandırılmış bir "tasarım istisnası" kaydı (hangi
UYARI, hangi gerekçeyle, kim onayladı) — bir onay kutusu DEĞİL, gerekçe
metni gerektiren bir alan; `output/provenance.json`ın "KAYIT, karar
VERMEZ" felsefesiyle AYNI ailede olurdu.

**Bu altı fikrin HİÇBİRİ onaylanmadı/uygulanmadı** — hepsi kullanıcının
"bu geliştirme fikirlerini ayrıca planlayarak not et" talimatının
karşılığıdır. Bir sonraki adım, kullanıcının bunlardan hangisini/hangi
sırayla açacağına karar vermesidir (bkz. `DEVELOPMENT_TASKS.md`
`DEV-040`).

**rev-22'nin GERÇEK plan çıktısından çıkan SOMUT kural boşlukları
(`DEV-042`/`DEV-043`, TAMAMLANDI):** `DEV-040`'ın SPEKÜLATİF
fikirlerinden FARKLI olarak, bunlar kullanıcının BİZZAT üretilmiş DXF/
preview üzerinde bulduğu gerçek hatalardan çıkarıldı — o zamanki v1
kural kataloğu (4 kural) bunları YAKALAMIYORDU: (1) bir ıslak hacmin
(banyo/wc) TEK erişim yolunun bir yatak odasından geçmesi (`uC`'de
`hol→oda→banyo` zinciri, `check_bedroom_via_corridor`in kapsamı
DIŞINDA — o kural yalnızca "salon" komşuluğuna bakıyor), (2) banyo/wc
kapılarının birbirinden ÇOK uzak olması (tesisat kümelenmesi ilkesi,
önceden HİÇ kontrol edilmiyordu). İkisi de aşağıda "DEV-042/DEV-043:
ıslak hacim kuralları" bölümünde ayrıntılı anlatılır.

## Bilinen sınırlamalar

- **Giriş-WC görüş hattı bir v1 basitleştirmesidir** (yukarı bakınız) —
  mobilya/kapı açılım yayı hesaba katılmaz.
- **Oda-kapı komşuluğu 300mm sabit bir toleransla bulunur**
  (`rules._TOUCH_TOLERANCE_MM`) — bu proje ölçeğinde (duvar kalınlığı
  200mm) güvenlidir, ama farklı ölçekli bir projede yeniden
  değerlendirilmesi gerekebilir.
- **`resolve_unit_zoning` yalnızca TEK SATIRLIK (1D) bir yerleşimdir** —
  karmaşık 2D bin-packing/optimizasyon YAPILMAZ (DEV-038'in kendi v1
  sınırıyla AYNI disiplin).
- **`options_for_core_placement` bugün `templates/`i ÇAĞIRMAZ** —
  yalnızca köşe adaylarını puanlar (yukarı bakınız).
- **Rev-21'de gerçek projeye `unit_id` eklendikten sonra ortaya çıkan
  UYARIlar (hol-oranı, giriş-WC görüş hattı, kapı-çekirdek dengesizliği,
  yatak odası-salon komşuluğu) henüz GİDERİLMEDİ** — bunlar kullanıcı
  kararı gereği üretimi DURDURMUYOR, ama rev-20 birim tasarımının
  gözden geçirilmesi AYRI, sonraki bir revizyon konusudur (bkz.
  `context.json::rev_history` rev-21).
- **`DEV-042`'nin GERÇEK projede yakaladığı `uC_hol`→`uC_oda`→`uC_banyo`
  zinciri henüz GİDERİLMEDİ** (yukarı bakınız, "Gerçek projede GERÇEK
  bir örnek yakaladı") — bu da üretimi DURDURMUYOR, düzeltme AYRI bir
  revizyon konusudur.
- **`check_wet_area_door_proximity` (DEV-043) yalnızca kapı-orta-nokta
  mesafesi ölçer, gerçek adjacency (ortak duvar) KONTROL ETMEZ** (yukarı
  bakınız) — mesafece yakın ama araya başka bir oda/duvar giren bir
  YANLIŞ-POZİTİF teorik olarak mümkündür; plan metninin kendi "Açık
  kararlar"ında bilinçli bırakıldı.
- **`check_wet_area_reachable_without_bedroom` (DEV-042) yalnızca
  DOĞRUDAN kapı-komşuluğu graf kenarı kurar** — iki oda arasında kapı
  YOKSA (yalnızca duvarla komşularsa) bir kenar OLUŞMAZ; bu, modülün
  "oda-kapı komşuluğu" tanımıyla (yukarı bakınız) tutarlıdır ama bir
  odadan diğerine PENCEREDEN/açık plan geçişle (kapısız) geçilen —
  bugünkü şemada zaten desteklenmeyen — bir senaryoyu MODELLEMEZ.
- **Kural ağırlıkları/eşikleri "v1 pratik varsayılan"dır** —
  `standards/`in kendi "Gelecek güncelleme sözleşmesi" ile AYNI
  disiplin, kullanıcının gerçek şartname/deneyimle güncellemesi
  BEKLENİR.
