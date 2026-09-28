# Tamamlanan Geliştirmeler Geçmişi

Aktif geçmiş kapasitesi: **50 kayıt**. En eski tamamlanmış kayıt, 51. kayıt
alınırken silinir. Ayrıntılı teknik değişiklikler git geçmişi ve ilgili proje
provenance kayıtlarıyla ilişkilendirilir.

## HD-021 — `rooms/`: içbükey (L/T-şekilli) odalarda mahal etiketi konumlandırması (DEV-044)

- **Durum:** COMPLETED
- **Tamamlanma:** 2026-09-28
- **Kökeni:** `HD-020` (`DEV-041`) ile AYNI kritik geri bildirim turunun
  bir başka maddesi: *"L şeklinde hol isimlendirmelerini yaparken
  geometrik orta nokta değil, hol sınırları içerisinde yazmalısın mahal
  ismini. sınırlara dikkat ederek mahal etiketlerini yerleştirmelisin."*
  Kullanıcının belirlediği "efektif sıralama"da (`DEVELOPMENT_TASKS.md`
  "Uygulama sırası") DEV-044 ikinci sıradaydı — "küçük, bağımsız, DIŞ
  KARAR gerektirmeyen bir modül düzeltmesi" olarak DEV-041'in hemen
  ardından, kullanıcının "sonraki geliştirme planını uygula" komutuyla
  uygulandı.

### Kök neden ve çözüm: "pole of inaccessibility"

`rooms::RoomLabeler` etiketi oda poligonunun geometrik centroid'ine
yerleştiriyordu. Bu, projedeki odaların neredeyse tamamen dikdörtgen
(convex) olması nedeniyle bugüne kadar sorun çıkarmıyordu — zaten
`rooms/CLAUDE.md`'de "bilinen sınırlama" olarak NOT edilmişti. `DEV-039`/
rev-22'de tanıtılan L-şekilli hol'ler (`uA_hol`, `uB_hol`) İÇBÜKEYDİR
(concave) ve bu varsayımı GERÇEKTEN kırdı: içbükey bir poligonun
centroid'i, poligonun "çentiğine" denk gelip odanın DIŞINA düşebilir.

Plan metninin kendi "Fikir 1 (önerilen)"i UYGULANDI: yeni
`PolygonOps.pole_of_inaccessibility`, Mapbox'un `polylabel` algoritmasıyla
AYNI deterministik izgara-arama yöntemidir (üçüncü parti kütüphane
KULLANILMADI — kök `CLAUDE.md`'nin "deterministik üretim ilkesi" gereği
kendi implementasyonu; iteratif grid-arama bilinen bir yöntemdir). Bir
noktanın poligon sınırına imzalı mesafesini (`_distance_to_boundary`,
içerideyse pozitif/dışarıdaysa negatif) giderek küçülen hücrelerle
maksimize eden noktayı bulur — sınıra en uzak, dolayısıyla HER ZAMAN
poligonun GERÇEKTEN içinde kalan nokta.

### Convex davranış BİREBİR korundu (bir kanıt tesadüf değil, tasarım)

Arama, adaylardan biri olarak HER ZAMAN `centroid`i VE bbox-merkezini
dener (`best_cell` başlangıcı); bir dikdörtgen için bu iki nokta zaten
ANALİTİK OLARAK aynı ve maksimum mesafeye sahip TEK noktadır — hiçbir
izgara hücresi bunu KESİN OLARAK (`>`, `>=` değil) geçemez. Sonuç:
dikdörtgen odalarda `pole_of_inaccessibility` == `centroid`, **1e-6
toleransla BİREBİR**. Bu, `DEV-018`in `check_block_matches_raw_formula`
testinin (hard-coded `center_x, center_y = 3000.0, 2500.0` bekleyen,
1e-6 toleranslı bir regresyon testi) TEK SATIR DEĞİŞMEDEN geçmeye devam
etmesiyle KANITLANDI — bu tesadüf değil, `bbox_cell`in bilinçli olarak
aday havuzuna eklenmesinin doğrudan sonucudur.

### Sığdırma kutusu da düzeltildi: TAM AABB değil, yerel açıklık

Plan metninin "Açık kararlar"ından biri buydu: etiketin sığacağı
genişlik/yükseklik eskiden odanın TAM AABB'inden geliyordu — içbükey bir
odada bu, çentikteki BOŞ alanı da sayarak MEVCUT OLMAYAN bir genişlik/
yükseklik uydururdu (taşma riski). Yeni `PolygonOps.local_extent(polygon,
origin)`, capa noktasından dört eksen yönünde (+x/-x/+y/-y) GERÇEK kenar
kesişimine kadar ölçer; dikdörtgende AABB ile AYNI sonucu verir, kesişim
bulunamazsa (dejenere durum) eski AABB hesabına DÜŞÜLÜR (güvenlik ağı).

### Kasıtlı bozma kanıtı + golden referans + tek kaynak disiplini

`scripts/rooms/selftest.py`ye 4 yeni grup eklendi (toplam 8): ikisi
regresyon (dikdörtgende pole==centroid, local_extent==AABB), ikisi
DEV-044'ün kendisi. `L_SHAPED_HOL` sabiti (`uA_hol`/`uB_hol` ile AYNI
kategoride, elle hesaplanmış L-şekil) ile: (1) geometrik centroid'in
(2165.93, 1515.93) GERÇEKTEN poligonun dışında (çentikte) kaldığı elle
kanıtlandı — bu, DEV-044 öncesi hatanın ta kendisidir; (2)
`pole_of_inaccessibility`in HER ZAMAN içeride kaldığı; (3) uçtan uca
`RoomLabeler.draw`in GERÇEKTEN çizdiği `INSERT` konumunun oda sınırları
içinde olduğu (yalnızca ham geometri fonksiyonu değil, fiili çizim çıktısı
sınandı).

Yeni proje-geneli golden referans `golden/hol_l_sekli` eklendi (`uA_hol`/
`uB_hol` ile AYNI L-şekil, tek odalı minimal bir kat) — `--golden-set`
üzerinden UÇTAN UCA (pipeline + `rule_room_labels`) doğrulandı.
`golden_report.py::rule_room_labels` bu vesileyle güncellendi:
artık `PolygonOps.centroid` DEĞİL, `RoomLabeler.draw`in KENDİ kullandığı
`pole_of_inaccessibility`i çağırıyor — `HD-020`deki (`DEV-041`)
`wall_gap_ranges` ile AYNI "tek kaynak" disiplini (kontrol, üretimin
okuduğu FONKSİYONUN KENDİSİNİ okur, geometrik bir varsayımı YENİDEN
YAZMAZ). Bu güncelleme olmasaydı, gelecekte eklenecek İÇBÜKEY bir golden
fixture'da kural YANLIŞLIKLA başarısız olurdu (centroid dışarıda kalırken
gerçek etiket doğru şekilde içeride olurdu).

### Kapsam BİLEREK dar tutuldu

`DEV-044`'ün "İlişkili modüller"i yalnızca `rooms/` (asıl uygulama),
`architect/` (concave hol üreten taraf) ve `pafta/` (`fit_text_height`
etkileşimi) idi. `scripts/ceiling/`in RCP (tavan) paftası etiketi de
`centroid` kullanıyor ama bu görevin kapsamı DIŞINDA BİLİNÇLİ olarak
bırakıldı — ayrı bir görev gerektirir.

- **Etkilenen dosyalar:** `scripts/rooms/__init__.py` (`PolygonOps.
  pole_of_inaccessibility`, `_distance_to_boundary`, `_point_in_polygon`,
  `_point_to_segment_distance`, `local_extent`, `_ray_hit_distance`;
  `RoomLabeler.draw` iç mantığı), `scripts/rooms/selftest.py` (4 yeni
  grup), `scripts/golden_report.py` (`rule_room_labels`), `scripts/
  rooms/CLAUDE.md`, `golden/hol_l_sekli/` (YENİ golden referans).
- **Golden etkisi:** mevcut TÜM fixture'lar (`--golden-set`)
  DEĞİŞMEDEN geçti (hepsi convex/dikdörtgen); YENİ bir fixture
  (`golden/hol_l_sekli`) eklendi.
- **Sonraki adım:** "Uygulama sırası"na göre `DEV-042`→`DEV-043` (aynı
  temalı `architect/` kuralları) — bkz. `docs/development/
  DEVELOPMENT_TASKS.md`.

## HD-020 — `walls/`+`validate.py`: duvar ucu / kapı boşluğu çakışması denetimi (DEV-041)

- **Durum:** COMPLETED
- **Tamamlanma:** 2026-09-28
- **Kökeni:** kullanıcının, `architect/` (DEV-039/rev-21/rev-22) çıktısını
  gerçek dünya mimar gözüyle incelediği kritik geri bildirim turu: *"bir
  tane duvar, kapının ortasında bitmiş, bu kritik bir hata ve kabul
  edilemez, bunun denetlenip bir daha olmaması gerekiyor. kontrol
  mekanizmalarını iyileştir ve bu problemi çöz."* Aynı mesajda gelen
  altı diğer gözlem (koridor→hol→oda→banyo sirkülasyonu, WC kapı
  yakınlığı, L-hol etiket konumu, ölü alan, merdiven oranı/sahanlık)
  PLANLAMA olarak `DEV-042`…`DEV-047`e ayrıldı; kullanıcı DEV-041'i
  "temel güvenlik ağı" olarak en öncelikli sıraya koydu ve doğrudan
  "dev 41 geliştirmesini gerçekleştir" komutuyla uygulanmasını istedi.

### Arite kararı: `collision/` değil, `validate.py::check_walls`

Soru DEV-019/DEV-039'daki AYNI arite ayrımıyla çözüldü: bu bir duvarın
KENDİ bağlantısının geçerli olup olmadığıdır (arity-1: "bir T-kesişim
NOKTASI, kesiştiği duvarın kapı/pencere boşluğuna mı denk geliyor"),
"iki FARKLI eleman sınıfı aynı yeri mi işgal ediyor" (arity-2+, örn.
tefriş↔duvar) DEĞİL. Bu yüzden `collision/`e değil, `walls`ın kendi
geçerliliğini zaten denetleyen `validate.py::check_walls`e eklendi.

### Tek kaynak: ikinci bir açıklık-hesabı YAZILMADI

`wall_gap_ranges` adlı yeni yardımcı, `walls.gaps_for_wall`i (host
duvarın kapı/pencere boşluk aralıklarının TEK hesaplandığı yer)
DOĞRUDAN çağırır. Bu, rev-13'te gerçekten yaşanan bir hatadan
(çizilen kapı yayı ile denetlenen sektörün AYRI hesaplanıp sessizce
ayrışması) bilinçli olarak kaçınma kararıdır — kök `CLAUDE.md`'nin
"tek kaynak" disiplini burada birebir uygulandı. Yeni
`point_position_on_segment`, mevcut boolean `point_on_segment`in bir
yan ürünüdür: nokta segment üzerindeyse `seg_a`dan itibaren s-mesafesini
(mm) döner. Bir T-kesişim ucu bir boşluğun KESİN İÇİNDEYSE (`g_start <
s < g_end`, sınır eşitliği HARİÇ — bir duvar tam kapı pervazında/jamb'da
bitmesi mimari olarak GEÇERLİDİR) artık "sarkan uç" sayılır ve mesaj
özel olarak boşluğu adlandırır (`"...BOSLUGUNA baglaniyor..."`),
genel "sarkan uç" mesajından AYRI tutulur.

### İlk kez: `validate.py`nin kendi kontrolüne odaklı selftest

`scripts/validate_selftest.py` (YENİ dosya) — `check_walls` bugüne
kadar yalnızca `golden_report.py --golden-set` üzerinden DOLAYLI test
ediliyordu (zaten GEÇERLİ golden context'lerle); hata yolu hiç
DOĞRUDAN sınanmamıştı. Kök `CLAUDE.md`'nin "kasıtlı bozma +
yanlış-pozitif" disiplini beş grupla uygulandı: (1) kapı boşluğuna
giren uç HATA verir, (2) boşluktan uzak normal bir T-kesişimi
YANLIŞ-POZİTİF üretmez, (3) boşluğun TAM SINIRINDAKİ (jamb) bir uç
YANLIŞ-POZİTİF üretmez (sınır eşitliği de HATA sayılsaydı bu gerçek
bir yanlış-pozitif olurdu — mimari olarak bir duvar kapı pervazında
bitebilir), (4) GERÇEK sarkan uç hâlâ eski mesajıyla yakalanır
(regresyon yok), (5) gerçek `context.json`daki İKİ bilinen hata
(`w_unit_A_B`, `uA_w_hol_mutfak_v`) GERÇEKTEN yakalanır. İlk fixture
denemesi (iki bağlantısız duvar) kendi kendine sarkan uçlar ürettiği
için kirli sayımlar verdi; kapalı bir dikdörtgen + tek bir T-duvarıyla
yeniden kurularak TEK değişken izole edildi.

### Kapsam BİLEREK dar tutuldu: kontrol kuruldu, gerçek hata DÜZELTİLMEDİ

Bu görevin kapsamı yalnızca KONTROLÜ kurmaktı, gerçek projedeki iki
somut hatayı düzeltmek DEĞİL — bu, kullanıcının kendi önceliklendirmesiyle
("önceliğimiz modül iyileştirilmesidir ... revizeleri kullanacaksın")
tutarlıdır: modül işi önce, veri düzeltmesi (bir proje revizyonu olarak)
sonra. Sonuç olarak `python scripts/validate.py` şu an gerçek `context.
json` üzerinde BAŞARISIZ dönüyor — bu bir regresyon DEĞİL, kontrolün
tam olarak beklendiği gibi çalıştığının kanıtıdır (önceden bu iki hata
sessizce üretiliyordu). Düzeltme ayrı bir gelecek proje revizyonu
bekliyor.

- **Etkilenen dosyalar:** `scripts/validate.py` (`point_position_on_segment`,
  `wall_gap_ranges`, `check_walls` imzası + iç mantığı), `scripts/
  validate_selftest.py` (YENİ), `scripts/walls/CLAUDE.md` ("Doğrulama" +
  "Bilinen sınırlar").
- **Golden etkisi:** yok (`--golden-set` zaten geçerli fixture'lar
  kullanır, hiçbiri bir kapı boşluğuna giren T-kesişimi İÇERMİYOR).
- **Sonraki adım:** `DEV-042`…`DEV-047` (kullanıcının aynı geri
  bildiriminden türeyen kalan altı plan), belirlenen "Uygulama sırası"na
  göre — bkz. `docs/development/DEVELOPMENT_TASKS.md`.

## HD-019 — `architect/` modülü: mekansal ilişki/mimari mantık kuralları (DEV-039)

- **Durum:** COMPLETED
- **Tamamlanma:** 2026-09-28
- **Kökeni:** kullanıcının, `standards/`+`templates/`in gerçek projeye
  uygulanmasından (rev-19/rev-20) HEMEN sonra gelen üçüncü büyük talebi:
  *"standartları büyük oranda belirlediğimize göre yeni bir plan
  oluşturmamızın vakti geldi ... bu modül, mimarın gerçek anlamda yaptığı
  işi yapacak aslında, planlama ... gerçek bir mimar gibi düşünüp oda,
  koridor, wc, mutfak vs. her şeyin planını endüstri standardına uygun
  biçimde yapacak."* Kullanıcı BİLEREK modül adını/kapsamını vermedi
  ("modülün adının ne olacağını ... ben bilmiyorum henüz ... sen plana
  detaylıca açıklayacaksın ben de onun üzerine seninle tartışıp planı
  geliştireceğim") — bu görev üç turluk bir DİYALOG sonucunda netleşti
  (modül adı, iç yapı, v1 kural kataloğunun tamamı, şema kararı, kural
  şiddeti kullanıcı tarafından TEK TEK onaylandı), sonra "planı uygula"
  ile implementasyon başladı.

### Arity ayrımının fiziksel çakışmadan mimari sağduyuya genişlemesi

`DEV-019`da (`collision/`) kurulan "arite ayrımı" ilkesi (arity-1 =
kendi verin geçerli mi, ilgili modülün işi; arity-2+ = iki farklı eleman
birbirine göre mantıklı mı, ayrı bir motorun işi) BİREBİR AYNI şekilde
buraya taşındı — sadece konu fiziksel ÇAKIŞMA değil mimari SAĞDUYU.
Kullanıcının verdiği üç somut örnek (kapı-çekirdek dengesizliği,
giriş-WC görüş hattı, hol'ün büyütülüp diğer odaların küçültülmesi)
HİÇBİRİ tek bir odanın kendi ölçüsüyle ilgili değildi — üçü de iki/N
elemanın birbirine göreliydi. Kullanıcının üçüncü örneği (hol optimum
olmalı) doğrudan bir öz-eleştiriydi: rev-20'de az önce kurulan `uA`/`uB`
birimlerinin hol alanları (%45-55 pay) tam olarak bu tuzağa düşmüştü —
bu bağlantı plan dokümanında AÇIKÇA belirtildi, gizlenmedi.

### Üç turluk plan diyaloğu: nihai kararlar

1. **Modül adı: `scripts/architect/`** — kullanıcının kendi gerekçesi:
   "en mimari fikirleri sunacak/planlayacak karar verici burası."
2. **İç yapı: TEK modül, dört dosya** (`rules.py`/`study.py`/
   `options.py`/`design.py`) — `pafta/`/`elevations/`in "sıkıca ardışık,
   aynı bağlamı paylaşan sınıflar ayrı modüllere BÖLÜNMEZ" deseniyle AYNI
   gerekçe. Kullanıcının "çok genişse ayrı modülde de olur" notu bir
   gelecek kaçış kapısı olarak dokümana yazıldı, ön koşul DEĞİL.
3. **v1 kapsamı TAMAMI baştan** (`stairs`/`ceiling`in kademeli-v1
   disiplini burada BİLEREK uygulanmadı, kullanıcı kararı).
4. **`rooms[].unit_id` yeni şema alanı** — eskiden `uA_`/`uB_`/`uC_`
   id-önek konvansiyonuyla ÖRTÜK olan "hangi oda hangi daireye ait"
   bilgisi artık AÇIK. Kullanıcının gerekçesi bunu DEV-039'un ötesine
   taşıyor: gelecekteki "emsal" (imar alanı oranı) hesabı da AYNI
   güvenilir gruplamaya bağımlı olacak.
5. **Kural şiddeti: `standards/` ile AYNI, HER ZAMAN UYARI** — kullanıcı
   mahremiyet kuralları (giriş-WC, yatak odası-salon) için bile daha
   ciddi bir sınıf İSTEMEDİ ("hayır").
6. **Hol payı eşiği: %12-15 varsayılan, ama esnetilebilir** — kod
   katalog sabiti (`DEFAULT_CIRCULATION_SHARE_MAX = 0.15`) + her
   `check_*` fonksiyonunun bir override parametresi.
7. **`DEV-038`in absorpsiyonu ONAYLANDI** — sığma kontrolü etüdün
   ZATEN yapması gereken ilk adım olduğu için ayrı bir görev olarak
   KALMADI, `study::check_fits` oldu.
8. **Ajanın önerdiği 2 ek kural (5, 6) ONAYLANDI** — yatak odasının
   salon üzerinden değil hol üzerinden erişilmesi, hol payının SAYISAL
   bir eşiğe bağlanması (madde 3'ü ÖLÇÜLEBİLİR hale getirir).

### Oda-kapı komşuluğu: `collision/geometry.py`nin YENİDEN kullanımı

Bir kapının duvar-merkez-çizgisi üzerindeki orta noktası, hangi
oda(lar)ın poligon KENARINA değdiğini bulmak için `collision.geometry.
point_on_boundary`yi (projedeki poligon matematiğinin TEK sahibi)
doğrudan kullanır — ikinci bir kopya YAZILMADI. Giriş-WC görüş hattı
kontrolü kendi çapraz-çarpım segment-kesişim testini (`rules.
_segments_intersect`) taşır; bu, `standards`ın AABB basitleştirmesiyle
AYNI kategoride, dürüstçe belgelenmiş bir v1 basitleştirmesidir (mobilya/
kapı açılım yayı hesaba katılmaz).

### `check_fits`/`resolve_unit_zoning`: `validate.py` akışının PARÇASI DEĞİL

DEV-038'in "sığma kontrolü" bir ÖN-KONTROLDÜR (bir ajan
`generate_circulation_core` gibi bir üreticiyi çağırmadan ÖNCE sorar);
odalar zaten üretilmişse anlamı kalmaz (`standards::
check_room_proportions` zaten üretilmiş odayı denetler). Bu yüzden
YALNIZCA `rules.py`nin dört ilişkisel `check_*` fonksiyonu
`validate.py`ye bağlandı (standards_warnings ile AYNI desende,
`UYARI (mimari): ...` olarak basılır, `all_errors`a HİÇ girmez).

### Golden output etkisi

- **Ana proje geometrik olarak DEĞİŞMEDİ** — `architect/` hiçbir yeni
  DXF entity üretmez/context.json'a yazmaz; `output/plan.dxf` diff'i
  yalnızca her üretimde değişen zaman damgası/GUID metadata'sıdır (kod
  seviyesinde doğrulandı: git diff yalnızca `$TDCREATE`/`$FINGERPRINTGUID`
  gibi alanları gösterdi, hiçbir entity/koordinat satırı DEĞİŞMEDİ).
- **8 golden referansın HİÇBİRİ değişmedi** (`--golden-set` temiz döndü).
- **Ayrı bir golden fixture EKLENMEDİ** (bilinçli karar) — `collision/`ın
  KENDİ gerekçesiyle AYNI: bu modülün sorusu "tasarım mantıklı mı" olduğu
  için (golden'ın sorusu "çıktı beklenmedik şekilde değişti mi" değil),
  bir entity/layer/bbox karşılaştırması `rules.py`nin dört fonksiyonunu
  SINAMAZ (hiçbiri DXF'e dokunmuyor) — tek gerçek kanıt `selftest.py`nin
  kasıtlı-bozma testleridir.

### Modül self-test'i

`python scripts/architect/selftest.py` — 20 kontrol grubu: dört
`rules.py` fonksiyonunun her biri hem bir İHLAL hem (giriş-WC görüş
hattı için İKİ farklı: koni-dışı VE duvarla-engellenmiş) bir
YANLIŞ-POZİTİF senaryosuyla; `check_fits`in DEV-038'in GERÇEK keşfettiği
7700mm/8400mm senaryosunu elle-hesaplanabilir biçimde doğrulaması;
`resolve_unit_zoning`in boşluğu eşit dağıtması; `options_for_core_
placement`in giriş kenarını yüksek puanlaması; `place_unit_entry_doors`in
zone merkezlerine kapı koyması; VE gerçek `context.json`'daki (rev-20)
`uA_*` oda verisine bellek-içi `unit_id` eklenerek hol-oranı ihlalinin
GERÇEKTEN yakalandığının (`unit_id` eklenmeden projenin SESSİZ kaldığı da
ayrıca kanıtlanarak) doğrulanması. Tüm 17 modül self-test'i,
`validate.py`, `generate_dxf.py`, `golden_report.py --golden-set` ve
`doc_check.py` ayrıca çalıştırılıp temiz döndü.

### Açık risk / bilinen sınırlama

- **Gerçek projeye bugün hiçbir `unit_id` verisi EKLENMEDİ** — bu bilinçli,
  ayrı bir sonraki revizyon konusudur (`standards::room_type`in rev-19'a
  kadar boş kalmasıyla AYNI desen); bu yüzden `architect/`in dört kuralı
  bugün gerçek projede SESSİZCE hiçbir uyarı ÜRETMEZ.
- **Giriş-WC görüş hattı bir v1 basitleştirmesidir** (yukarı bakınız).
- **`resolve_unit_zoning` yalnızca TEK SATIRLIK (1D) bir yerleşimdir** —
  karmaşık 2D bin-packing YAPILMAZ.
- **`options_for_core_placement` bugün `templates::
  generate_circulation_core`yi ÇAĞIRMAZ** — o fonksiyon henüz bir
  `position` parametresi taşımıyor (küçük, bloke etmeyen bir teknik
  detay olarak plana not düşüldü).

### Sonraki direktif

Rev-20'nin hol-oranı ihlalinin (ve varsa diğer `architect/` uyarılarının)
gerçek projeye UYGULANMASI (`unit_id` eklenmesi dahil) AYRI, sonraki bir
revizyon konusudur — sistem mimarı bunu açıkça talep ettiğinde ele
alınır. `DEVELOPMENT_TASKS.md::PLANLANAN GÖREVLER`de kalan maddeler:
`DEV-007` (BLOCKED), `DEV-024` (`site/`), `DEV-026`/`DEV-028`
(`legend/` genişletmeleri), `DEV-027` (kaçış planı), `DEV-031`…`DEV-035`.

### rev-21 notu (AYNI GÜN, kullanıcı talebiyle — "unit id planlamasını da
gerçekleştir")

Yukarıdaki "Açık risk" ve "Sonraki direktif" bu görev TAMAMLANDIĞI anda
doğruydu (`unit_id` henüz yoktu); birkaç saat içinde AYNI oturumda
kullanıcı bunu da istedi. `rooms[].unit_id`, `id`-önek konvansiyonundan
BİREBİR türetilerek 80 birim odasına (normal1-normal5, her katta 16'şar)
proje revizyonu olarak eklendi (`context.json::rev_history` rev-21,
`requests.jsonl`). Sonuç: `architect/rules.py`nin dört kuralı artık
GERÇEKTEN çalışıyor ve kat başına 6 UYARI üretiyor — hol-oranı üç birimde
de aşıyor (uA/uB %37.7, uC %26.2, sınır %15 — bu görevin "Neden boşluk"
bölümünde önceden işaret edilen rev-20 eleştirisinin AYNEN kanıtı),
`uC_oda`→`uC_salon` kapısı doğrudan salona açılıyor, `door_entry_3` ile
`uC_d_banyo_hol` aynı görüş hattında (36° sapma), uA/uC birimleri
cekirdeğe göre dengesiz (oran 4.38 — kullanıcının orijinal "bir dairenin
kapısı direkt merdivene açılıyor" örneğinin GERÇEK bir örneği). Tüm
UYARI sınıfında, üretimi DURDURMADI; `output/plan.dxf` GEOMETRİK olarak
DEĞİŞMEDİ (`unit_id` hiçbir çizimi etkilemez). Bu uyarıların GİDERİLMESİ
(rev-20 birim tasarımının yeniden gözden geçirilmesi) HÂLÂ AYRI, sonraki
bir revizyon konusudur.

## HD-018 — `templates/` modülü: sirkülasyon çekirdeği şablon üreteci (DEV-037)

- **Durum:** COMPLETED
- **Tamamlanma:** 2026-09-28
- **Kökeni:** `DEV-036`in AYNI oturumunda kullanıcının ikinci talebi:
  *"kat planları ve oda yerleşimleri için genel şablonlara sahip olacak,
  bir de şablon oluşturucu generator'ü olacak ... örneğin yerleşim
  planlarındaki bina ana girişi, dairelerin yerleşimi, kattaki daire
  sayısına göre efektif yerleşimler vs gibi verileri sağlayacak."*
  Kullanıcı yönlendirmesi (yine "best practices bir yaklaşım ile ...
  gerçekleştir") açık kararların çözümünü sisteme bıraktı.

### Kapsam BİLEREK küçültüldü: yalnızca sirkülasyon çekirdeği

`DEV-037` planı v1 için tek bir arketip önermişti; bu tek arketip bile
"bina ana girişi" + "daire yerleşimi" + "kaç daireye göre efektif
yerleşim" gibi birkaç farklı tasarım kararını içerebilirdi. Uygulama
sırasında kapsam DAHA DA daraltıldı: **yalnızca sirkülasyon çekirdeği**
(asansör + merdiven + L-şekilli koridor + güney giriş duvarı) üretildi;
**daire/birim İÇİ oda bölüntüsü (salon/mutfak/banyo yerleşimi) v1
KAPSAMI DIŞINDA bırakıldı.** Gerekçe: gerçek projenin üç birimi
(`uA_*`/`uB_*`/`uC_*`) ÜÇÜ DE farklı tasarlanmış (farklı oda sayısı,
farklı oranlar, farklı kapı yerleşimi) — bu GERÇEK bir tasarım kararıdır
ve parametrik hale getirmek kendi başına büyük bir açık-karar seti
(kaç oda, hangi oranlarda, şablonun çıktısı context parçası mı öneri
raporu mu) gerektirir. Sirkülasyon çekirdeği seçildi çünkü tek
BELİRSİZLİKSİZ, kanıtlanmış desendir — kök `CLAUDE.md`nin "Çok katli bina
yapisi" bölümünde ZATEN belgelenmiştir ve gerçek projenin HER katında
AYNI konumda kullanılır.

### Kritik mimari not: kendi eklenen bir kısıt, kullanıcı İSTEMEDİ

Kullanıcı "generator" kelimesini kullandı ama bunun dil modeline geometri
ürettirmek anlamına GELMEDİĞİ modülün dokstring'inde ve
`scripts/templates/CLAUDE.md`de AÇIKÇA yazıldı: `generate_circulation_core`
tamamen deterministik bir Python fonksiyonudur, parametrelerden koordinat
HESAPLAR; rastgele/LLM-uydurma HİÇBİR koordinat üretmez. Bu, kök
`CLAUDE.md`nin "Deterministik üretim ilkesi"yle çelişmemek için modülü
yazan ajan tarafından EKLENEN bir kısıttır — kullanıcı açıkça istemedi,
ama kullanıcının AYNI mesajda tekrar ettiği "dil modeli ile dxf oluşturmak
... mimari çalışmalarda kabul edilemez" ilkesiyle DOĞRUDAN bağlantılıdır.

### Varsayılan ölçüler: icat edilmedi, gerçek projeden ÇIKARILDI

`CirculationCoreTemplate`in varsayılan değerleri (asansör 1000mm, merdiven
4000mm, koridor bacağı 1500mm, bant derinliği 4500mm) gerçek projenin
`context.json`ındaki (`normal1` katı) ZATEN `validate.py`den geçmiş
sirkülasyon çekirdeğinden BİREBİR çıkarıldı — `standards/`in v1
kataloğundeki "pratik varsayılan" değerlerinden bile DAHA sağlam bir
temele sahiptir (orada genel mimari makuliyet, burada GERÇEKTEN ŞU AN
ÇALIŞAN bir tasarım). `selftest.py::check_matches_real_project_ground_truth`
bunu doğrudan kanıtlar: `generate_circulation_core(20000, 17500)`,
gerçek projenin `elevator`/`stair`/`band` odalarının poligonlarını VE
alanlarını (3.0/12.0/75.0 m²), `core_bottom`/`core_div`/`core_right`/
`band_south` duvarlarının konumlarını/kalınlığını, `door_stair` kapısının
konumunu/genişliğini **BİREBİR** üretir.

### Çıktı context.json'a YAZILMAZ (açık karar)

`DEV-036`daki AYNI kararla tutarlı: `generate_circulation_core` salt bir
`dict` (`rooms`/`walls`/`openings`) döndürür, context dosyasına DOKUNMAZ,
DXF çizmez. Bunu context.json'a birleştirmek AYRI, insan onaylı bir sonraki
adımdır — kök `CLAUDE.md`nin "context.json proje tasarım verisidir"
ilkesiyle tutarlı.

### Golden output etkisi

- **Ana proje DEĞİŞMEDİ** — bu modül context.json'a hiç yazmadığı, hiçbir
  entegrasyon noktası eklemediği için `output/plan.dxf` ZATEN etkilenmedi.
- **8 golden referansın HİÇBİRİ değişmedi** — bu görev yeni bir golden
  fixture EKLEMEDİ (çıktı context.json'a yazılmadığı için "uçtan uca"
  kanıt zaten `selftest.py`nin gerçek-proje-karşılaştırmasıyla sağlandı,
  ayrı bir golden fixture'a gerek kalmadı).

### Modül self-test'i

`python scripts/templates/selftest.py` — 5 kontrol grubu: varsayılan
şablonun gerçek proje verisiyle BİREBİR eşleşmesi (yukarı bakınız),
çekirdek konumunun `floor_width` değişse de SABİT kaldığı (yalnızca
koridorun doğu ucu büyüdüğü), `include_band_south` anahtarının YALNIZCA
o duvarı etkilediği (bodrum/çatı gibi açık geçişli katlar için), `id_prefix`in
tüm üretilen kimliklere uygulandığı (çoklu çekirdek çakışmasını önler),
özel bir `CirculationCoreTemplate`in enjekte edilebildiği. Tüm 16 modül
self-test'i ve `doc_check.py` ayrıca çalıştırılıp temiz döndü.

### Açık risk / bilinen sınırlama

- **Daire/birim içi oda bölüntüsü YOK** (v1 kapsam sınırı, yukarı
  bakınız).
- **Bina ana girişi/kaç daire gibi üst-seviye "arketip seçimi" mantığı
  YOK** — bu fonksiyon yalnızca BİR çekirdeği üretir.
- **Dış çerçeve duvarlarını ÜRETMEZ** — yalnızca çekirdeğin iç duvarları.
- **`units="m"` desteği gerçek veriyle KARŞILAŞTIRILARAK sınanmadı**
  (yalnızca `mm`, gerçek projeyle).

### Sonraki direktif

`DEVELOPMENT_TASKS.md::PLANLANAN GÖREVLER`de kalan maddeler: `DEV-007`
(BLOCKED), `DEV-024` (`site/`), `DEV-026`/`DEV-028` (`legend/`
genişletmeleri), `DEV-027` (kaçış planı), `DEV-031`…`DEV-035`. Daire/birim
içi oda bölüntüsü (bu görevin v1 kapsamı DIŞI bıraktığı kısım) henüz bir
`DEV-0XX` numarası ALMADI — sistem mimarı isterse bunu AYRI bir gelecek
görev olarak açabilir.

## HD-017 — `standards/` modülü: şartname + oransal mahal kural kütüphanesi (DEV-036)

- **Durum:** COMPLETED
- **Tamamlanma:** 2026-09-28
- **Kökeni:** Kullanıcı somut, kendi projesinden örneklerle bir boşluk tarif
  etti: *"her mahal için bir oran en boy oran limitleri alt üst limiti
  olacak, default ayarlarda bunlar esnetilmeyecek ... sistem uyarı verecek
  ama kullanıcı istemeye devam edersek isteği doğrultusunda bu oransal
  mahaller gerçekleştirilecek."* Örnekler: asansör kuyusu 3 m² ama piyasada
  karşılığı olmayan bir en-boy oranında; merdiven alanı makul ama KARE
  (dikdörtgen olmalı); "çubuk gibi ince uzun" bir banyo. Görev planı
  (Fikir1/Fikir2/açık kararlar) `DEV-036` olarak önce yazıldı, kullanıcı
  ardından *"bu oluşturduğumuz planları uygula ... best practices bir
  yaklaşım ile bu işlemi gerçekleştir"* diyerek açık kararların çözümünü
  (mimari seçim, `room_type` şeması, eşik kaynağı, gerçek projeye veri
  eklenip eklenmeyeceği) sisteme bıraktı.
- **Kapsam:** `scripts/standards/` (yeni modül: `__init__.py`, `CLAUDE.md`,
  `selftest.py`), `schema/design.schema.json` (`room.room_type`),
  `scripts/validate.py` (`check_room_types` HATA + `check_room_proportions`
  UYARI entegrasyonu), `scripts/collision/scene.py` (`COLLISION_EXEMPT`),
  `scripts/version.py` (`CONTRACT_MODULES`), yeni `golden/oran_ornek/`,
  `scripts/CLAUDE.md` (modül kaydı + roadmap satırı),
  `docs/development/{DEVELOPMENT_TASKS,DEVELOPER_NOTES}.md`.

### Açık kararların çözümü (kullanıcı yönlendirmesi "best practices" idi)

Üç açık karar, kullanıcının delege ettiği "best practices" ilkesiyle şöyle
çözüldü:
- **Fikir 1 seçildi** (yeni bağımsız modül, `rooms/`e genişletme değil) —
  kapsamın (çok sayıda mahal tipi + gelecekteki `DEV-037` şablon
  üreticisiyle ilişki) `rooms/`in bugünkü "etiketleme" sorumluluğunu
  aştığı gerekçesiyle.
- **`room_type` sabit bir şema enum'u YAPILMADI**, serbest string olarak
  bırakıldı ve geçerlilik `validate.py::check_room_types`te (çalışma
  zamanında, `walls.kind` ile AYNI desen) denetlendi. Bu, kullanıcının
  ayrıca belirttiği gelecek gereksinimle ("ilerleyen zamanlarda ...
  standart verilerini güncellediğimde diğer modüllerin uyumunu mümkün
  olduğu kadar koruması gerekir") doğrudan bağlantılı: yeni bir mahal
  tipi eklemek artık bir ŞEMA değişikliği DEĞİL, yalnızca `STANDARDS`
  sözlüğüne bir satır eklemektir.
- **Gerçek projeye `room_type` verisi EKLENMEDİ** — `ceiling`/`levels`
  emsali izlendi: altyapı opt-in kurulur, gerçek projeye veri eklemek AYRI
  bir karardır. `output/plan.dxf` bu yüzden GEOMETRİK olarak değişmedi
  (yalnızca zaman damgası/GUID farkı, `git diff` ile doğrulandı).

### Sayıların doğası: "v1 pratik varsayılan", resmi atıf İDDİASI DEĞİL

`STANDARDS` kataloğundaki eşiklerin (asansör min_ratio=1.0/max_ratio=1.5,
merdiven min_ratio=1.3 vb.) hiçbiri doğrulanmış bir TS/yönetmelik madde
numarasına dayanmıyor — bunlar kullanıcının kendi örneklerinden çıkarılan
MAKUL başlangıç değerleridir ve her `RoomStandard.source` alanı bunu
"v1 pratik varsayılan" diye AÇIKÇA işaretler. Bu, kök `CLAUDE.md`'nin
"ölçü/standart UYDURULMAZ" ilkesini DELMEZ: uydurulmayan şey PROJE
GEOMETRİSİdir (gerçek bir odanın koordinatı) — bu kütüphane, tefriş
kataloğunun "ofis/katalog standardı (çizim sabiti)" olmasıyla AYNI
kategoridedir. Kullanıcının ileride gerçek şartname belgeleri vermesi
BEKLENİYOR; bu yüzden `CONTRACT_VERSION` disiplini özellikle "katalog
DEĞERİ serbestçe değişir, `RoomStandard`'ın ALAN ŞEKLİ değişirse sürüm
artar" şeklinde tasarlandı (bkz. `scripts/standards/CLAUDE.md` "Gelecek
güncelleme sözleşmesi") — amaç, bir gelecek şartname-güncelleme
oturumunun `validate.py`yi KIRMADAN yalnızca `STANDARDS` sözlüğünü
değiştirebilmesidir.

### Politika: UYARI, asla HATA — golden fixture'la UÇTAN UCA kanıtlandı

Yeni `golden/oran_ornek`, `golden/minimal` ile TAMAMEN AYNI oda
geometrisini (2800×8800mm, oran 3.14) kullanır — tek fark iki odaya
`room_type` etiketi eklenmesidir: `oda_sol` → `koridor` (max_ratio=8.0,
AYNI oran sınırlar İÇİNDE → UYARI YOK), `oda_sag` → `banyo` (max_ratio=2.2,
AYNI oran sınırı AŞAR → TAM 1 UYARI). `validate.py` her iki durumda da
BAŞARILI döner (WARN asla FORBID değildir) ve DXF entity raporu
`golden/minimal`ınkiyle BİREBİR AYNIDIR (`room_type` hiçbir yeni DXF
varlığı üretmez, yalnızca `validate.py` çıktısında bir UYARI satırı
ekler) — bu, `diff` ile doğrulandı.

### Golden output etkisi

- **Ana proje DEĞİŞMEDİ** (yukarı bakınız). `--compare` YENİDEN üretilmeye
  gerek KALMADAN eşleşti.
- **7 mevcut golden referansın HİÇBİRİ değişmedi** (hiçbiri `room_type`
  taşımıyor).
- **Yeni `golden/oran_ornek`:** `--golden-set --update` sonrası ikinci
  (update'siz) çalıştırma birebir aynı raporu üretti (determinizm
  doğrulandı); entity raporu `golden/minimal`inkiyle (kaynak alanı hariç)
  BİREBİR eşleşiyor.

### Modül self-test'i

`python scripts/standards/selftest.py` — 8 kontrol grubu: `room_aspect_ratio`
elle hesaplanabilir (+ dejenere/sıfır-kenar durumu), `check_room_types`
(yazım hatası YAKALANIR, eksik alan sessizce atlanır), `check_room_proportions`
oran/kısa-kenar/alan ihlallerinin HER BİRİ İZOLE fixture'larla ayrı ayrı
sınandı (bir fixture'ın YALNIZCA bir sınırı ihlal etmesi elle kurgulandı,
aksi halde testler birbirine karışırdı), sınır İÇİNDEKİ bir oda için
yanlış-pozitif YOK, `room_type` verilmeyen oda opt-in olarak atlanıyor,
"m" biriminde kısa-kenar mm'ye doğru çevriliyor, `validate_standards`
gerçek kataloğun TEMİZ döndüğünü VE kasıtlı bozulmuş bir kopyanın
YAKALANDIĞINI (geçici `STANDARDS` girdisi eklenip `try/finally` ile geri
alınarak) doğruluyor. Tüm 15 modül self-test'i ve `doc_check.py` ayrıca
çalıştırılıp temiz döndü.

### Açık risk / bilinen sınırlama

- **v1 kataloğundaki eşiklerin çoğu resmi bir TS/yönetmelik atfı TAŞIMAZ**
  (yukarı bakınız) — kullanıcının gerçek belgelerle güncellemesi
  BEKLENİYOR.
- **AABB (eksen hizalı sınırlayıcı kutu) yaklaşımı** döndürülmüş veya
  L-şekilli bir oda için YANLIŞ olabilir; bu projedeki odalar dikdörtgen/
  eksen-hizalı olduğu için bugün sorun çıkarmıyor (`rooms/CLAUDE.md`deki
  AYNI sınırlama sınıfı).
- **Modüller arası tek-kaynak fırsatı** (`stairs::MIN_GOING_MM` gibi
  sabitlerin buraya taşınması) v1 KAPSAMINA DAHİL EDİLMEDİ — ayrı bir
  gelecek migrasyon konusu.

### Sonraki direktif

`DEVELOPMENT_TASKS.md::PLANLANAN GÖREVLER`de kalan maddeler: `DEV-007`
(BLOCKED), `DEV-024` (`site/`), `DEV-026`/`DEV-028` (`legend/`
genişletmeleri), `DEV-027` (kaçış planı), `DEV-031`…`DEV-035`, ve
**`DEV-037`** (kat planı/daire yerleşimi şablon kütüphanesi + generator —
kullanıcının AYNI oturumda "best practices ile uygula" dediği ikinci
madde; bu görevden HEMEN SONRA ele alınacak).

## HD-016 — `ceiling/` modülü: yansıtılmış tavan planı / RCP (DEV-023)

- **Durum:** COMPLETED
- **Tamamlanma:** 2026-09-28
- **Kökeni:** Kullanıcı `DEV-023`ü açıkça seçti ("DEV-023'ü (ceiling/) seçip
  başlat") ve sistemin sunduğu Fikir 1/Fikir 2/açık kararlar analizine üç
  net yönlendirme verdi: **Fikir 1** (ayrı, bağımsız `scripts/ceiling/`
  modülü + AYRI RCP paftası — kat planına bindirme REDDEDİLDİ), tavan
  yüksekliği verisi **oda başına** (`rooms[]` içinde, kat başına tek
  varsayılan DEĞİL), ve v1 kapsamı **aydınlatma armatürünü İÇERMEZ**
  (yalnızca tavan kotu + malzeme).
- **Kapsam:** `scripts/ceiling/` (yeni modül: `__init__.py`, `CLAUDE.md`,
  `selftest.py`), `schema/design.schema.json` (`room.ceiling_height_mm`/
  `room.ceiling_finish`), `scripts/generate_dxf.py` (import + `ceiling_floors`
  hesabı + `all_labels`/`content_ranges` genişletmesi + `draw_ceiling_sheet`
  döngüsü), `scripts/palette/__init__.py` (`TAVAN` girdisi, mor/eflatun),
  `scripts/collision/scene.py` (`COLLISION_EXEMPT`), `scripts/version.py`
  (`CONTRACT_MODULES`), `scripts/golden_report.py` (`_code_owned_layers`e
  `TAVAN` + `rule_opening_symbols` düzeltmesi, aşağı bakınız), yeni
  `golden/tavan_ornek/` (RCP'yi uçtan uca sınayan referans), kök `CLAUDE.md`
  (bu görev için ayrıca güncellenmedi — mimari ilke zaten mevcuttu) +
  `scripts/CLAUDE.md` (modül kaydı + roadmap tablosu satırı).

### Opt-in veri disiplini: gerçek proje HİÇ değişmedi

`floor_has_ceiling_data(floor)` bir katın RCP paftasının hiç üretilip
üretilmeyeceğinin TEK kaynağıdır — `resolve_room_ceilings` gibi o da
`rooms[].ceiling_height_mm` alanının context'te AÇIKÇA verilip
verilmediğine bakar, hiçbir varsayım/türetme yapmaz. Gerçek projenin
bugünkü `context.json`ında bu alan HİÇ yok — bu yüzden `output/plan.dxf`
üretiminde `ceiling_floors` boş liste döndü ve dosyada **`TAVAN` katmanı
hiç açılmadı, tek bir yeni entity eklenmedi**: `git diff -- output/plan.dxf`
yalnızca zaman damgası/GUID/`CLASS` blok sırası gibi üretimden üretime
DEĞİŞEN, geometri-dışı alanları gösterdi (elle doğrulandı). Kuzey oku/kot
ile AYNI "veri yoksa uydurma, veri yoksa çizme" deseni.

### Gerçek bir golden-kural boşluğu bulundu ve düzeltildi

`CeilingSheet.draw`, kat planının kullandığı AYNI `walls::draw_wall_network`
çağrısını AYNI `floor['openings']` verisiyle YENİDEN yapar — bu, kapı
sembolünün açılım yayını (ARC) da RCP paftasında YENİDEN çizdiği anlamına
gelir (bilerek; bkz. `scripts/ceiling/CLAUDE.md` "Bilinen sınırlamalar" —
RCP pratiğinde bazı ofisler açıklığı gizler, bu proje basitlik için
GÖSTERME'yi seçti). `golden/tavan_ornek`i ilk `--golden-set --update`
denemesinde `rule_opening_symbols` kuralı BAŞARISIZ oldu: kural "ARC sayısı
= kapı sayısı" varsayıyordu, oysa RCP'li bir katta kapı yayı katta 2 kez
(kat planı + RCP) çizilir. Kural, paftayı açan AYNI TEK kaynağı
(`ceiling.floor_has_ceiling_data`) okuyacak şekilde düzeltildi — katın RCP
paftası varsa beklenen ARC sayısı o kat için ×2'lenir. Bu, `MIN_GOING_MM`
(DEV-022) ve `PaftaOverflowError` (DEV-029) ile AYNI sınıf bir bulgu:
golden altyapısı gerçekten yeni bir modülün varsayımları BOZDUĞU bir kuralı
yakaladı, kör geçmedi.

### Golden output etkisi

- **Ana proje DEĞİŞMEDİ** (yukarı bakınız — `ceiling_floors` boş, geometrik
  fark sıfır). `docs/development/plan-golden-report.json`
  (`--compare`) YENİDEN üretilmeye gerek KALMADAN eşleşti.
- **6 mevcut golden referansın HİÇBİRİ değişmedi** (hiçbiri
  `ceiling_height_mm` taşımıyor — RCP'nin opt-in olduğunun ayrıca kanıtı).
- **Yeni `golden/tavan_ornek`:** `golden/minimal` ile AYNI küçük kat (2 oda,
  5 duvar, 1 kapı, 1 pencere) + iki odaya `ceiling_height_mm` (biri
  `ceiling_finish` ile, diğeri olmadan — `draw_ceiling_label`in her iki
  dalını da sınar). RCP paftası eklenince entity sayısı 222 → 282 (+60,
  yeni paftanın kendi aks ızgarası + duvar ağı + çerçeve + 3 `TAVAN` TEXT'i
  — 2 satır [kot+malzeme] + 1 satır [yalnız kot] = elle hesaplanabilir).
  `--golden-set --update` sonrası ikinci (update'siz) çalıştırma birebir
  aynı raporu üretti (determinizm doğrulandı). `PaftaOverflowError`
  TETİKLENMEDİ.

### Modül self-test'i

`python scripts/ceiling/selftest.py` — 5 kontrol grubu: `resolve_room_
ceilings`in elle hesaplanabilir sonucu (4000×3000 dikdörtgen → centroid
(2000,1500), veri taşımayan oda yanlış-pozitifi), `floor_has_ceiling_data`in
her iki yönü, `draw_ceiling_label`in malzeme var/yok durumunda ürettiği
TAM entity sayısı + metin içeriği (kot formatı `+2.50`/`-0.20` + BÜYÜK HARF
malzeme), `CeilingSheet.draw`in bağımsız ölçülen duvar-ağı entity sayısına
etiket sayısını EKLEDİĞİNİN doğrulanması, katman RGB'sinin kod-sahipli
olduğu. Tüm 14 modül self-test'i (`collision`…`stairs`) ve
`scripts/doc_check.py` ayrıca çalıştırılıp temiz döndü.

### Açık risk / bilinen sınırlama

- **Aydınlatma armatür yerleşimi YOK** (v1 kapsam sınırı, kullanıcı kararı
  — ayrı bir gelecek görev olarak `docs/development/DEVELOPER_NOTES.md`da
  not düşüldü).
- **Malzeme kod listesi standartlaştırılmamış** — serbest metin.
- **Kapı/pencere açıklıkları RCP'de de gösterilir** (bilerek; yukarıdaki
  golden-kural bulgusunun kökeni de budur).
- **`validate.py`de tavan kotu ↔ duvar/kat yüksekliği çapraz kontrolü YOK**
  — proje henüz `rooms[]` seviyesinde kat yüksekliği bilmiyor, çapraz
  kontrol için veri yok (bkz. `scripts/ceiling/CLAUDE.md`).

### Sonraki direktif

`DEVELOPMENT_TASKS.md::PLANLANAN GÖREVLER`de kalan maddeler: `DEV-007`
(BLOCKED), `DEV-024` (`site/`), `DEV-026`/`DEV-028` (`legend/`
genişletmeleri), `DEV-027` (kaçış planı), `DEV-031`…`DEV-035` (2026-09-28'de
eklenen 5 yeni aday: `electrical/`, `plumbing/`, `walls/` detay kesiti,
`columns/`+`walls/` statik kalıp, `roof/`). Sistem mimarı bir sonraki
maddeyi seçip yönlendirme verene kadar kod yazılmaz.

## HD-015 — `levels/` modülü: kot (seviye/datum) standardı (DEV-029)

- **Durum:** COMPLETED
- **Tamamlanma:** 2026-09-25
- **Kökeni:** rev-17'de (`DEV-021`/`DEV-025` çalışması sırasında)
  kullanıcının gündeme getirdiği çapraz-kesit konu: *"kot verme
  mantıklarını yöneten bir mantık istiyorum ... kot organizasyonu hem
  planda hem kesitte kullanılacaktır ... bu mantığın projenin geneline
  hakim olması gerekecektir."* `DEVELOPMENT_TASKS.md::DEV-029`de sistemin
  önceden yazdığı "Öneri" (yeni bağımsız modül) kullanıcı tarafından
  onaylandı; kullanıcı ayrıca kot metni formatını da onayladı: "+3.00"/
  "-0.20"/"±0.00" (işaret + 2 ondalıklı metre).
- **Kapsam:** `scripts/levels/` (yeni modül: `__init__.py`, `CLAUDE.md`,
  `selftest.py`), `schema/design.schema.json` (`level_mark` tanımı +
  `floor.properties.level_marks`), `scripts/generate_dxf.py` (kesit/
  görünüş/plan entegrasyonu), `scripts/palette/__init__.py` (`KOT` girdisi),
  `scripts/collision/scene.py` (`COLLISION_EXEMPT`), `scripts/version.py`
  (`CONTRACT_MODULES`), `scripts/golden_report.py` (`_code_owned_layers`e
  `KOT`), `golden/merdiven_ornek/` (plan kot işareti eklendi), kök
  `CLAUDE.md` + `scripts/CLAUDE.md` (modül kaydı).

### Kat yüksekliği hesabı YENİDEN YAZILMADI — dolaylı tüketim

Bu görevin en kritik invariant'ı: `levels` modülü `elevations::LevelStack`i
import ETMEZ. `level_boundaries_from_placements(placements)`,
`LevelStack.placements()`in DÜZ çıktısını (herhangi bir `(etiket, y0, y1)`
üçlü listesi — SEKİL beklenir, SINIF değil) işler; `generate_dxf.py`
(orkestratör) köprüyü KENDİSİ kurar (`LevelStack.from_context(elevation)`
zaten `sections`/`elevations` için kuruluyordu, `levels` sadece SONUCU
tüketir). Bu, `axis_grid`in `draw_on_elevation(...)` duck-typing
sözleşmesiyle AYNI desendir — iki modül birbirini BİLMEZ.

### İki tüketim yolu: otomatik (kesit/görünüş) vs. gerçek-veri (plan)

- **Kesit/görünüş:** HİÇBİR yeni proje verisi gerekmedi — her kat sınırının
  kotu zaten `context.json::elevations[].levels[].height`den (GERÇEK veri)
  hesaplanıyordu, `levels` SADECE bunu `"+3.00"` gibi FORMATLAR ve ÇİZER.
  Bu yüzden gerçek projenin `output/plan.dxf`ine **otomatik olarak** 80 yeni
  `KOT` varlığı eklendi (2 cephe × 10 sınır + 2 kesit × 10 sınır, her sınır
  1 bayrak + 1 metin = elle hesaplanabilir: `(2+2) × 10 × 2 = 80`).
- **Plan:** `floors[].level_marks[]` GERÇEK proje verisidir (rampa/teras
  kademe farkı) — plan düzleminde "kat yüksekliği" kavramı OLMADIĞI için
  otomatik türetme YAPILAMAZ. Veri verilmezse HİÇBİR ŞEY çizilmez (kuzey
  oku ile AYNI "veri yoksa uydurma" deseni). Gerçek projenin hiçbir katına
  bu veri EKLENMEDİ (rampa kademe değerleri elde yoktu, uydurulmadı);
  `golden/merdiven_ornek`e (üst sahanlık +3.00, `stairs[].
  floor_to_floor_mm` ile TUTARLI) tek bir örnek eklendi.

### Yerleşim kararı: sol kenarın biraz dışı, ölçekle türer

`anchor_x = cursor - to_modelspace(50.0, denominator)` — flag+metinle AYNI
oranda ölçeğe göre türeyen küçük bir pay. Gerçek proje + 6 golden
referansın TÜMÜNDE `PaftaOverflowError` TETİKLENMEDİ (elle doğrulandı,
`DEV-022`nin ilk denemesinde yaşanan taşma hatasının AKSİNE).

**Bağımsız reviewer düzeltmesi (aynı oturum):** İlk yazılan gerekçe
("`ElevationSheet.draw`daki zemin çizgisinin sabit `dx-1000` payının
İÇİNDE kalır") MATEMATİKSEL OLARAK YANLIŞTI — `to_modelspace(50, denom)`
ÖLÇEKLE BÜYÜYEN bir değerdir (1:50'de zaten `50×50=2500mm`, sabit
`1000mm`lik payı AŞAR), iki değer karşılaştırılamaz. Gerçek taşma
GÜVENCESİ bu karşılaştırma DEĞİL, `pafta::Sheet.verify_within_frame`in
(SABİT `CONTENT_PADDING=4000`, ölçekle türemez) üretim SIRASINDA yaptığı
gerçek bbox kontrolüdür — bugünkü `1:50` sabit ölçeğinde (bu proje
`MIMARI_UYGULAMA` sınıfı olduğu için ölçek zaten sabit) rahatça sığıyor,
ama ÇOK BÜYÜK ölçek paydalarında (örn. `1:200`/`1:500`, `VAZIYET_PLANI`
proje tipi) bu değer `CONTENT_PADDING`i AŞABİLİR — o durumda üretim
SESSİZCE değil, `PaftaOverflowError` ile DURUR (sessiz hata YOK, sadece
yanlış bir gerekçe yorumu vardı). Yorum düzeltildi
(`scripts/generate_dxf.py`), kod DEĞİŞMEDİ (davranış zaten güvenliydi).

### Golden output etkisi

- **Ana proje DEĞİŞTİ** (beklenen, otomatik kesit/görünüş kot işaretleri):
  `output/plan.dxf`e 80 yeni `KOT` entity'si eklendi;
  `docs/development/plan-golden-report.json` `--write` ile YENİDEN
  üretildi.
- **6 golden referansın TÜMÜ** aynı sebeple değişti (`--update`);
  `golden/merdiven_ornek` ayrıca `floors[0].level_marks[]` ile PLAN
  tarafını da (opt-in) sınıyor.
- `scripts/golden_report.py::_code_owned_layers` `KOT`u tanımadığı için ilk
  denemede `declared_layers` kuralı bunu "bildirilmemiş layer" olarak
  işaretledi — `MERDIVEN` ile AYNI unutkanlık sınıfı, `AKS`/`KOLON*`/
  `TEFRIS-*`/`KESIT`/`MERDIVEN` ile AYNI listeye eklenerek düzeltildi.

### Modül self-test'i

`python scripts/levels/selftest.py` — 8 kontrol grubu: `format_level`in
elle hesaplanabilir 6 durumu (dahil: `±0.00`ye yuvarlanan 1mm'lik değer),
`level_boundaries_from_placements`in elle hesaplanabilir sonucu (+ boş
liste), `LevelMark.draw`in TAM 2 varlık ürettiği, boyutun ölçekle
DOĞRUSAL türediği (1:100 = 1:50 × 2), `draw_level_marks`in N sınır için
TAM 2N varlık ürettiği, plan kot işaretlerinin OPT-IN olduğu (+ yanlış-
pozitif), özel bir stilin enjekte edilebildiği, katman RGB'sinin kod-
sahipli olduğu.

### Açık risk / bilinen sınırlama

- `validate.py`de `level_marks[]` için özel bir geometrik kontrol YOK
  (schema zaten sayısal/zorunlu kılıyor).
- Kesit/görünüşteki `anchor_x` konumu piksel-kesin çakışmama garantisi
  vermez (`NorthArrow` ile AYNI sınırlama sınıfı).

### Sonraki direktif

`DEVELOPMENT_TASKS.md::PLANLANAN GÖREVLER`de kalan maddeler: `DEV-007`
(BLOCKED), `DEV-023` (`ceiling/`), `DEV-024` (`site/`), `DEV-026`/
`DEV-028` (`legend/` genişletmeleri), `DEV-027` (kaçış planı). Sistem
mimarı bir sonraki maddeyi seçip yönlendirme verene kadar kod yazılmaz.

## HD-014 — `palette/` modülü: merkezi katman renk organizasyonu (DEV-030)

- **Durum:** COMPLETED
- **Tamamlanma:** 2026-09-25
- **Kökeni:** Kullanıcının kod incelemesi sırasında yaptığı gözlem
  ("modüllerin kendi layer'larında çalışırken renklerinin
  çeşitlendirilmediğini fark ettim") `DEV-030` olarak plana eklenmişti
  (bkz. bu oturumdaki önceki kayıt). Kullanıcı sonradan Fikir 1
  (merkezi olmayan) / Fikir 2 (merkezi kontrolör modülü) arasında **Fikir
  2**'yi seçti, gerekçesi:

  > "her modül kendi rengini oluşturursa bazı modüller aynı rengi seçmiş
  > olabilir ... ve bazı modüllerin birbirlerine kontrast renkler ile
  > bulunması ihtiyacı olabilir bundan dolayı ayrı bir modül olması uygun
  > olabilir."

- **Kapsam:** `scripts/palette/` (yeni modül: `__init__.py`, `CLAUDE.md`,
  `selftest.py`), `scripts/axis/standard.py`, `scripts/columns/standard.py`
  + `render.py` + `__init__.py`, `scripts/sections/__init__.py`,
  `scripts/stairs/__init__.py`, `scripts/furniture/groups.py` (hepsi
  `palette.color_for(...)`den okur), `scripts/collision/scene.py`
  (`COLLISION_EXEMPT`), `scripts/version.py` (`CONTRACT_MODULES`), kök
  `CLAUDE.md` + `scripts/CLAUDE.md` (modül kaydı).

### İki kural, kullanıcının iki cümlesine BİREBİR karşılık gelir

`palette::validate_palette`: (1) hiçbir iki katman AYNI rengi taşıyamaz
(tam eşitlik yasağı — "aynı rengi seçmiş olabilir" riski), (2) aynı
`contrast_group`taki katmanlar birbirinden en az `CONTRAST_MIN_DISTANCE`
(40.0, RGB Öklid mesafesi) kadar uzak olmalıdır ("kontrast ihtiyacı").
`"primary"` grubu AKS/KOLON ailesi/KESİT/MERDİVEN'i kapsar (aynı pafta
üzerinde aynı anda görülebilirler); tefriş ailesi bilerek bu gruba GİRMEZ
(rev-10 kararı: "zıt renk kullanılmaz" korunur).

### Somut bulgu düzeltildi: KOLON ailesi artık 3 farklı ton

`columns/standard.py::COLUMN_RGB`, üç farklı katmana (`KOLON` kontur,
`KOLON-TARAMA` tarama, `KOLON-METIN` isim) TEK renk atıyordu — kullanıcının
birinci endişesinin (aynı rengin paylaşılması) SOMUT bir örneğiydi.
`palette` kurulurken üçü ayrıştırıldı: kontur nötr orta gri `(150,150,150)`,
tarama daha açık `(190,190,190)` (ast eleman konvansiyonu), metin en koyu
`(45,45,50)` (okunurluk) — üçü de `AKS`in SABİT rengine `(67,77,88)`
(kök `CLAUDE.md` tarafından mandate edilir, DEĞİŞTİRİLEMEZ) yeterince uzak
tutuldu; eski `(90,90,96)` AKS'ye tehlikeli derecede yakındı (Öklid mesafesi
~27.6, yeni değerler ≥88).

### Kapsam kararı: yalnızca kod-sahipli katmanlar

`context.json::layers[]` (proje verisi, ACI index) merkezi kaydın DIŞINDA
bırakıldı — kullanıcı bu ayrımı genişletmeyi istemedi (soru açık kararlar
listesinde soruldu, ek yönlendirme gelmedi), bu yüzden "proje verisi = ACI,
sistem/kod standardı = RGB" ikiliği KORUNDU.

### `golden_report.py`nin bilinen bir kör noktası doğrulandı

DEV-030 gerçek projenin `KOLON` ailesinin rengini DEĞİŞTİRDİĞİ halde
`golden_report.py --golden-set` ve `--compare docs/development/
plan-golden-report.json` "eşleşti" raporladı — ölçüm raporu yalnızca
entity/layer SAYISINI ve `modelspace_bbox`i kaydeder, RGB'yi DEĞİL. Bu YENİ
bir hata değil (rapor formatı hep böyleydi) ama DEV-030 bunu İLK KEZ somut
olarak gösterdi; `scripts/palette/CLAUDE.md` ve `scripts/columns/CLAUDE.md`
"Bilinen sınırlamalar"a eklendi. Renk regresyonu bugün yalnızca
`palette/selftest.py` ve `preview.py` ile gözle kontrol edilebilir.

### Golden output etkisi

- **Ana proje GÖRSEL olarak değişti** (kolonların üç katmanı artık farklı
  gri tonlarında) ama **ölçüm raporu AYNI kaldı** (yukarı bakınız) —
  `docs/development/plan-golden-report.json` bu yüzden YENİDEN YAZILMADI
  (zaten hiçbir şeyi kaydetmiyordu).
- Mevcut 6 golden referansının TÜMÜ `--golden-set` ile yeniden koşuldu,
  hepsi (`golden/tefris_kolon` dahil) "eşleşti" — beklenen, çünkü ölçüm
  formatı renk taşımıyor.

### Modül self-test'i

`python scripts/palette/selftest.py` — 7 kontrol grubu: gerçek `PALETTE`nin
kendi kurallarını ihlal etmediği, aynı-renk ihlalinin yakalandığı (KOLON
bulgusunun regresyon testi), yakın-kontrast ihlalinin yakalandığı (+ eşiğin
TAM ÜZERİNDEKİ mesafenin yanlış-pozitif ÜRETMEDİĞİ, elle: (100,100,100) vs
(110,100,100) mesafe=10<40 HATA, (0,0,0) vs (40,0,0) mesafe=40 tam eşik
HATA VERMEZ), farklı/`None` gruplar arası yakınlığın MUAF olduğu (tefriş
ailesi korunur), `color_for`in bilinen/bilinmeyen isim davranışı, KOLON
ailesinin artık aynı renk OLMADIĞI, `_distance`in elle hesaplanabilir
olduğu (3-4-5 üçgeni, mesafe=5.0).

### Açık risk / bilinen sınırlama

- `golden_report.py` renk regresyonunu yakalamaz (yukarı bakınız) —
  ileride `report()`e katman başına örnek RGB eklenmesi düşünülebilir.
- `CONTRAST_MIN_DISTANCE` tek bir global eşiktir; gruba özel farklı eşikler
  desteklenmiyor.
- `context.json::layers[]` (ACI index) ile kod-seviyeli `PALETTE` (RGB)
  arasında bir çakışma kontrolü YOK — kullanıcı bunu istemedi, bilinçli
  sınır.

### Sonraki direktif

Sıradaki `PLANNED` madde `DEV-029` (kot/datum mantığı, `scripts/levels/`)
— aynı oturumda kullanıcı tarafından seçildi, ayrıca bkz. bu dosyadaki
sonraki kayıt.

## HD-013 — `stairs/` modülü: gerçek merdiven basamak geometrisi (DEV-022)

- **Durum:** COMPLETED
- **Tamamlanma:** 2026-09-25
- **Kökeni:** `DEVELOPMENT_TASKS.md::DEV-022`, 2026-09-24'te "endüstri
  standardı bir boşluk" olarak eklenmişti (kök `CLAUDE.md`nin "asansör/
  merdiven kapı sembolü çizilmez, sadece etiketli kapalı oda olarak
  gösterilir" bilinen basitleştirmesi). Kullanıcı 2026-09-25'te bu maddeyi
  açıkça seçti ve şu yönlendirmeyi verdi: **Fikir 1** (yeni bağımsız
  `scripts/stairs/` modülü — `columns/`/`furniture/` ile AYNI "oda-içi ek
  eleman = kendi modülü" deseni); rıht için varsayılan **17cm**, basamak
  genişliği için varsayılan **27cm** (makul bant 25-30cm); esnetilebilirlik
  (`auto_flex`) **varsayılan AÇIK**, esnetme her seferinde kullanıcıya
  bildirilir (UYARI).
- **Kapsam:** `scripts/stairs/` (yeni modül: `__init__.py`, `CLAUDE.md`,
  `selftest.py`), `schema/design.schema.json` (`stairs` tanımı +
  `floor.properties.stairs`), `scripts/validate.py` (`check_stairs`),
  `scripts/generate_dxf.py` (`ensure_stair_layer` + `draw_stairs_on_floor`
  çağrıları), `scripts/collision/scene.py` (`COLLISION_EXEMPT["stairs"]`),
  `scripts/version.py` (`CONTRACT_MODULES`), `scripts/golden_report.py`
  (`_code_owned_layers`e `MERDIVEN`), `golden/merdiven_ornek/` (yeni izole
  referans), kök `CLAUDE.md` + `scripts/CLAUDE.md` (modül kaydı).

### Tek kaynak: `resolve_stair`

`openings::swing_geometry` ile AYNI desen (kök `CLAUDE.md`, "Açıklık
varyantları" bölümü, rev-13'te bunun ihlalinin gerçek bir hataya yol açtığı
not edilir): `resolve_stair(spec, room_polygon)` hem `validate.py::
check_stairs` hem `draw_stairs_on_floor`in ÇAĞIRDIĞI TEK fonksiyondur. Basamak
sayısı `step_count` açıkça verilmemişse `floor_to_floor_mm / riser`den
(`round`) türetilir; `riser_height_mm`/`going_mm` verilmemişse ofis
standardı varsayılanlarına (170mm / 270mm) düşer; `auto_flex=True`
(varsayılan) bu değerleri kat yüksekliğine VE oda uzunluğuna TAM oturacak
şekilde ince ayarlar ve her esnetme `StairResolution.warnings`e yazılıp
hem `validate.py` hem `generate_dxf.py` tarafından "UYARI (merdiven): ..."
olarak basılır (sessiz varsayım YOK). Basamak genişliği esnetmesi
`MIN_GOING_MM=250`in altına düşerse (güvensiz/standart-dışı bir merdiven)
`StairFitError` fırlatılır — üretim durur, sessizce geçersiz geometri
üretilmez.

### Geliştirme sırasında bulunan gerçek hata: X/Y ekseni takası

İlk uygulamada `_travel_points` yardımcı fonksiyonu, seyahat ekseni `y`
olan bir merdiven için nokta çiftlerini `(y_koordinati, mid_x)` sırasıyla
döndürüyordu — DXF'in beklediği `(x, y)` sırası yerine KOORDINATLAR YER
DEĞİŞTİRİLMİŞTİ. Bu, `golden/merdiven_ornek` fixture'ı ilk kez üretilmeye
çalışılırken `PaftaOverflowError` olarak YAKALANDI (basamak/ok/kesme
çizgisi entity'leri pafta çerçevesinin çok dışına taştı — içerik sınırları
beklenenin binlerce mm dışındaydı). Kök neden bulunup `_travel_coords`
(yalnızca seyahat ekseni üzerindeki SKALER koordinatı döndüren, ayrı ve
daha az belirsiz bir yardımcı) ile düzeltildi. **Bu, `scripts/stairs/
selftest.py`ye eksik olan bir test sınıfını da ortaya çıkardı:**
`check_draw_entity_counts` yalnızca çizilen VARLIK SAYISINI doğruluyordu,
KOORDİNATLARINI değil — sayı doğru olsa bile koordinat yanlış olabilirdi.
Bunu kapatmak için `check_step_line_coordinates_hand_computable` eklendi
(hem X hem Y seyahat ekseninde elle hesaplanmış uç noktalarla karşılaştırma
— bu proje disiplininin "temiz döndü çıktısı tek başına hiçbir şey
kanıtlamaz" ilkesinin somut bir örneği).

### Bağımsız reviewer geçişinde bulunan ikinci gerçek hata: koşulsuz olmayan MIN_GOING_MM

Ayrı bir Agent çağrısıyla yapılan bağımsız reviewer/validator geçişi
(`scripts/CLAUDE.md`daki "reviewer/validator" rolü) `resolve_stair`i elle
izleyerek gerçek bir kapsam açığı buldu: `MIN_GOING_MM` kontrolü yalnızca
going'in OTOMATİK DARALTILDIĞI dalın İÇİNDEYDİ. Oda zaten sığıyorsa (daraltma
dalına hiç girilmiyorsa) açıkça verilmiş güvensiz bir `going_mm` (örn.
100mm) HİÇBİR kontrolden geçmeden sessizce kabul ediliyordu — modülün kendi
sözleşmesinin ("sessizce geçersiz/güvensiz bir basamak genişliği üretmez")
BİREBİR ihlaliydi. Düzeltme: `MIN_GOING_MM`/`MAX_GOING_MM` kontrolü
`resolve_stair`in SONUNDA, daraltılmış olsun ya da olmasın nihai `going`
değeri üzerinde KOŞULSUZ çalışacak şekilde taşındı (altında `StairFitError`,
üstünde UYARI — `MAX_GOING_MM` böylece ilk defa gerçekten KULLANILAN bir
sabit oldu, önceden tanımlı ama hiç okunmuyordu). İki yeni selftest eklendi
(`check_explicit_going_below_minimum_raises_even_without_shrink`,
`check_going_above_maximum_warns`) — toplam self-test grubu 10 → 12.
Reviewer ayrıca küçük bir kod kokusu (Python truthiness'e dayanan bir no-op
guard, `required_run and ...`) buldu; temiz bir bölmeyle değiştirildi.

### Gerçek projenin `Merdiven` odasına `stairs[]` verisi EKLENMEDİ

`context.json`daki mevcut `Merdiven` odası (4000×3000mm, tüm katlarda
sabit) için deneme amaçlı bir `stairs[]` girdisi (`floor_to_floor_mm=3000`)
`check_stairs` ile test edildi: sonuç `StairFitError` — tek düz kollu
merdiven için gereken kosu uzunluğu (~4590mm, 18 basamak × 270mm) odanın
uzun eksenine (4000mm) SIĞMIYOR, esnetilmiş basamak genişliği (~235mm)
minimum konfor sınırının (250mm) altında kalıyor. Bu SESSİZCE görmezden
gelinmedi: modül DOĞRU şekilde reddetti. Gerçek bir bina için bu odada
sahanlıklı/çift kollu bir merdiven gerekir (v1 kapsamı dışında, bkz.
`scripts/stairs/CLAUDE.md` "Bilinen sınırlamalar") — bu yüzden gerçek
projenin `context.json`ına HENÜZ `stairs[]` verisi eklenmedi; oda büyütülüp
tek kollu merdivene mi geçilecek yoksa çok kollu merdiven mi (ayrı bir
gelecek geliştirme konusu) eklenecek, sistem mimarının kararıdır.

### Golden output etkisi

- **Ana proje DEĞİŞMEDİ:** `context.json`a `stairs[]` verisi eklenmediği
  için `output/plan.dxf` entity/layer/bbox açısından AYNI kaldı
  (`golden_report.py --compare docs/development/plan-golden-report.json`
  ile doğrulandı, "Golden semantic report matches"); referans rapor
  YENİDEN YAZILMADI.
- **Yeni izole referans:** `golden/merdiven_ornek/` (tek oda, `stairs[]`
  ile `floor_to_floor_mm=3000` + `up_towards='N'`, TÜM basamak/riht/going
  değerleri varsayılanlardan türetilir, 0 UYARI) — 161 entity, `MERDIVEN`
  katmanında 21 entity (17 riht çizgisi + 1 ok gövdesi + 1 ok başı + 2
  kesme çizgisi parçası, elle sayılabilir: `step_count-1 + 4`).
- `scripts/golden_report.py::_code_owned_layers` `MERDIVEN`yi tanımadığı
  için ilk denemede `declared_layers` kuralı bunu "bildirilmemiş layer"
  olarak işaretlerdi — `AKS`/`KOLON*`/`TEFRIS-*`/`KESIT` ile AYNI listeye
  eklenerek düzeltildi.

### Modül self-test'i

`python scripts/stairs/selftest.py` — 12 kontrol grubu: step_count'tan
riht türetme (elle hesap), `auto_flex` açık/kapalı davranış farkı (+
UYARI), going daraltma (+ UYARI), MIN going altında `StairFitError` (+
yanlış-pozitif: sığan oda hata VERMEMELİ), **açıkça verilmiş güvensiz
`going_mm`nin daraltma dalı hiç tetiklenmese bile reddedilmesi** (+
yanlış-pozitif) ve MAX üstünde UYARI (bağımsız reviewer'ın bulduğu ikinci
kök neden hatasının regresyon testi, bkz. yukarısı), `up_towards`/
`travel_axis` tutarlılığı (+ yanlış-pozitif), riht çizgisi koordinatları
(X VE Y ekseni, elle hesaplanabilir — ilk kök neden hatasını yakalayan
test), çizilen varlık sayıları, bilinmeyen `room_id`nin çizim tarafında
sessizce atlanması, katman RGB'si.

### Açık risk / bilinen sınırlama

- Yalnızca TEK DÜZ KOLLU (sahanlıksız) merdiven desteklenir — bkz.
  `scripts/stairs/CLAUDE.md`.
- Kesit (`sections::SectionFeatureHook`) entegrasyonu bu revizyonun
  kapsamında DEĞİLDİR; ayrı bir takip konusu.
- `DEV-030` (katman renk organizasyonu, henüz PLANNED) tamamlandığında
  `STAIR_RGB` sabiti o merkezi karara göre yeniden gözden geçirilebilir.

### Sonraki direktif

Sistem mimarı şunlardan birine karar verebilir: (a) örnek projenin
`Merdiven` odasını büyütüp gerçek `stairs[]` verisiyle bağlamak, (b)
sahanlıklı/çift kollu merdiven desteğini ayrı bir görev olarak
`DEVELOPMENT_TASKS.md`ye eklemek, (c) `sections::SectionFeatureHook`
entegrasyonunu ayrı bir takip görevi yapmak, (d) sıradaki `PLANNED`
maddeye (`DEV-023` `ceiling/` veya kullanıcının seçtiği başka biri) geçmek.

## HD-012 — AutoCAD hatch uyarısı + aks ölçüsü düzeltmeleri, ScaleBar geri alındı

- **Durum:** COMPLETED
- **Tamamlanma:** 2026-09-24
- **Kökeni:** Kullanıcı gerçek projeyi AutoCAD'de açtığında "Hatch - Large,
  Dense Hatch Patterns" uyarısı aldığını bildirdi (ekran görüntüsüyle) ve
  ayrıca üç ayrı düzeltme istedi: (1) her paftadaki 0-5 arası basamaklı
  "ölçek gibi bir şey"in kaldırılması, (2) aks ölçü zincirinin AKS ile aynı
  katmanda olması ve sadece aks-aks + en-uçtaki-toplam mesafeyi göstermesi,
  (3) duvar kalınlığı gösteren ölçülerin aks ölçüsünün yanında (ve
  şimdilik sistemde hiçbir yerde) gösterilmemesi.
- **Kapsam:** `scripts/sections/__init__.py`, `scripts/dimensions/linear.py`,
  `scripts/dimensions/selftest.py`, `scripts/axis/standard.py`,
  `scripts/axis/grid.py`, `scripts/axis/selftest.py`,
  `scripts/pafta/__init__.py`, `scripts/generate_dxf.py`,
  `scripts/preview.py`, `scripts/northarrow/selftest.py`, `context.json`
  (`meta.dimensions.enabled` → `false`).

### Kök neden 1 — sahte "SOLID" hatch (AutoCAD uyarısının kaynağı)

`scripts/sections/__init__.py`'deki kesit-duvar kesişimi dolgusu
`hatch.set_pattern_fill("SOLID")` çağırıyordu — bu, GERÇEK bir solid-fill
API'si DEĞİLDİR (`ezdxf`de o `hatch.set_solid_fill()`dür); `"SOLID"` bir
PATTERN adı olarak arandı ve `pattern_scale=1.0`'da yaklaşık 0.125 birim
(mm) aralıklı bir çizgi deseni uygulandı. Gerçek projedeki 86 kesit-dolgusu
(250×4000mm'lik dikdörtgenler) bu yüzden HER BİRİ ~32.000 paralel çizgi
gerektiriyordu — AutoCAD'in "Large, Dense Hatch Patterns" uyarısının
BİREBİR kökeni buydu (elle doğrulanmış: `dxf.solid_fill=0`, `hatch.pattern`
içinde `(-0.088, 0.088)` ofsetli tek bir çizgi tanımı). Düzeltme:
`hatch.set_solid_fill()`. Regresyon testi:
`scripts/sections/selftest.py::check_section_sheet_entity_count`
(`dxf.solid_fill == 1` kontrolü).

### Kök neden 2 — `ezdxf` 1.4.4'ün katman hatası (aks ölçüsü "0" katmanında)

Kullanıcı "aks çizgileri ölçüleri aks çizgileri ile aynı layerda olmalı"
dedi; incelemede aks (AKS) DIMENSION'larının OK ve METİN'i doğru katmanda
ama ÖLÇÜ/UZATMA ÇİZGİLERİNİN hep `"0"` katmanında olduğu görüldü.
Kaynağı: `ezdxf`nin `render/dim_base.py::BaseDimensionRenderer.add_line`i
katman dahil BİRLEŞTİRİLMİŞ `attribs` sözlüğünü hesaplayıp sonra
KULLANMADAN, orijinal (katmansız) `dxfattribs`i geometri bloğuna geçiriyor
(ok/metin yolu birleşmiş sözlüğü doğru kullandığı için bu hatadan MUAF).
Kütüphane kaynağı değiştirilemediği için `scripts/dimensions/linear.py::
LinearDim.render` render SONRASI bir düzeltme uygular
(`_fix_geometry_block_layer`): geometri bloğundaki `Defpoints` DIŞINDAKİ
her varlığın katmanı `style.layer`e zorlanır. Regresyon testi:
`scripts/dimensions/selftest.py::check_rendered_layer`.

### Aks ölçüsü: en-uçtaki-toplam zinciri eklendi

Kullanıcı kararı: *"akslar arası mesafeler ve ikinci olarak en uçtaki
aksların arasındaki mesafeyi vermeli."* `AxisGrid._dim_chain_x/_dim_chain_y`
artık, bir kenarda 2'den FAZLA aks varsa, ardışık-mesafe zincirinin YANINA
`[min(xs), max(xs)]`ten tek-segmentli bir TOPLAM zinciri ekler; TAM 2 aks
varsa bu ikisi ZATEN aynı sayı olacağından toplam zincir TEKRARLANMAZ.
Toplam zincirin baseline'ı aksın kendi baloncuk/uzama bölgesinin
(`extension + bubble_radius`) `total_dimension_clearance` (300mm) kadar
ÖTESİNDE durur — aksi halde 3+ aks varlığında toplam zincirin ucu
bubble'ın İÇİNE girebilirdi (elle doğrulandı). Regresyon testi:
`scripts/axis/selftest.py::check_total_span_dimension` (3 aks + 2 aks →
3+1=4 DIMENSION; bubble-clearance kontrolü).

### Duvar/oda ölçüleri kaldırıldı (aks ölçüsünün yanında kafa karıştırıyordu)

Kullanıcı: *"duvarların kalınlıklarını vs. aks ölçülerinin yanında
göstermemeli bu kafa karıştırır, duvar ölçüleri sistem üzerinde şimdilik
hiçbir yerde gösterilmeyecek."* Kök neden: `meta.dimensions`in `mahal`
kademesi, bir bölme duvarının İKİ YÜZÜ arası (yani SADECE duvar kalınlığı)
kadar bir segment üretebiliyordu; bu, oda ölçüleri arasında aks ölçüsüne
yakın küçük ve şaşırtıcı bir sayı olarak görünüyordu. `dimensions` modülü
(ve `aciklik`/`mahal`/`toplam` kademeleri) KALDIRILMADI — hâlâ
`scripts/dimensions/` içinde vardır, `golden/aciklik_varyantlari` onu
sınamaya devam eder — sadece gerçek projenin `context.json::meta.
dimensions.enabled` alanı `true` → `false`ya çekildi (rev-13'ten beri
açıktı, şimdi belgelenmiş varsayılana döndü).

### ScaleBar tamamen kaldırıldı

Kullanıcı: *"ilave olarak her pafta içerisinde ölçek gibi bir şey var,
0-5 arası değerler ile birlikte, onu istemiyorum, kaldır."* Bu, rev-17'de
(HD-011, DEV-025) AYNI talebin ikinci parçası olarak eklenen
`pafta::ScaleBar` (+ `nice_scale_length_m`, `format_scale_value`) idi.
Sınıf, `generate_dxf.py`/`preview.py`'deki tüm çağrı yerleri,
`scripts/northarrow/selftest.py`'deki test grupları ve ilgili `CLAUDE.md`
bölümleri (`pafta`, `northarrow`, kök) TAMAMEN KALDIRILDI. Kuzey oku
(`NorthArrow`) etkilenmedi. `scripts/sections::draw_cut_marker_on_floor`,
etiket yüksekliğini artık `ScaleBar`dan ÖDÜNÇ ALMAK yerine kendi
`PRINTED_MARKER_LABEL_MM` sabitinden türetiyor (bağımsızlaştırma).

### Doğrulama

- `py_compile`, tüm 10 modül self-test'i (2 yeni test grubu: `dimensions::
  check_rendered_layer`, `axis::check_total_span_dimension`; 1 yeni
  assertion: `sections::check_section_sheet_entity_count`), `validate`,
  `generate` (`PaftaOverflowError` FIRLAMADI), `preview`, 5 semantik kural,
  5 golden referans (`--golden-set --update`), `doc_check` — hepsi temiz.
- Gerçek çıktıda doğrudan doğrulandı: 86 kesit-HATCH'i artık
  `dxf.solid_fill == 1`; 88 AKS DIMENSION'ının TAMAMI `AKS` katmanında
  (host + geometri bloğu); `meta.dimensions` kapalı olduğu için `OLCU`
  katmanlı DIMENSION SIFIRA düştü (önceden 402 idi).

### Golden output etkisi

- **Ana proje DEĞİŞTİ:** `output/plan.dxf`'te duvar/mahal/toplam ölçü
  zinciri (402 `OLCU` DIMENSION) ve ScaleBar entity'leri kayboldu, kesit
  HATCH'leri gerçek solid-fill oldu, aks ölçüsüne en-uçtaki-toplam satırı
  eklendi; `docs/development/plan-golden-report.json` `--write` ile
  YENİDEN üretildi.
- Mevcut 5 golden referansının TÜMÜ aynı sebeplerle değişti (`--update`).
  `golden/aciklik_varyantlari` kasıtlı olarak `meta.dimensions.enabled:
  true` BIRAKILDI — bu fixture'ın amacı zaten o özelliği sınamaktır.

## HD-011 — Kesit modülü ve kuzey oku/ölçek çubuğu standardı

- **Durum:** COMPLETED
- **Tamamlanma:** 2026-09-24
- **Görevler:** `DEV-021` ve `DEV-025` (kullanıcı: "dev 25, ve dev21 için
  çalışmaya başlayalım", ardından kesit hattı modeli ve kuzey oku/ölçek
  çubuğu için ayrıntılı yönlendirme).
- **Kapsam:** `scripts/sections/` (yeni modül), `scripts/northarrow/`
  (yeni modül), `scripts/pafta/` (`ScaleBar`, `nice_scale_length_m`,
  `format_scale_value` eklendi), `scripts/generate_dxf.py`,
  `scripts/preview.py`, `scripts/validate.py` (`check_sections`),
  `schema/design.schema.json` (`meta.north_angle`, `sections[]`,
  `definitions.section`), `scripts/golden_report.py`
  (`_code_owned_layers` → `KESIT`), `scripts/collision/scene.py`,
  `scripts/version.py`, `golden/kesit_ornek/` (yeni golden referans).

### DEV-021 — `sections/`: bina kesiti

Kullanıcının kesin kapsam kararı: *"bu yapılarda hiçbir zaman eğik kesit
ya da atlamalı kesit alınmaz. Bir kesit çizgisi X ve Y eksenindeki
akslardan birine paraleldir ve konumunu operatör bildirir."* Bu karar
`sections[].axis_source` alanını `elevations[].axis_source` ile BİREBİR
AYNI anlama getirdi (`'vertical'` → sabit Y, `'horizontal'` → sabit X) —
sayesinde `axis_grid.draw_on_elevation` VE `elevations::LevelStack`
DOĞRUDAN yeniden kullanıldı, ayrı bir "kesit aksı" kavramı icat edilmedi.

- **Varsayılan konum (kullanıcı kararı):** operatör bildirmezse kesit
  yapının TAM ORTASINDAN değil, ilgili kenarın **1/3 noktasından** alınır
  (`DEFAULT_POSITION_FRACTION`) — kullanıcı: *"amacımız default olarak
  projenin tam ortası değil de tam ortasından biraz sağ ya da solundan
  kesit almaktır."*
- **Varsayılan kesit sayısı (kullanıcı kararı):** `context['sections']`
  HİÇ verilmezse sistem X ve Y ekseninden BİRER varsayılan kesit üretir
  (`resolve_sections`, etiketler `A-A`/`B-B`); boş dizi (`[]`) verilirse bu
  varsayılan devre dışı kalır. Bu, **gerçek projeyi otomatik olarak
  değiştirdi**: ana `context.json`'da `sections[]` hiç yok, dolayısıyla
  `output/plan.dxf` artık 2 YENİ kesit paftası (`A-A KESITI`, `B-B KESITI`)
  içeriyor — bu FABRİKASYON değil, kullanıcının açıkça verdiği bir sistem
  standardının doğal sonucudur.
- **`crossing_walls`:** bir katın duvarlarından kesit hattını KESENLERİ
  (dik duran ve kesit konumunu Y/X aralığında kapsayan) bulur; kesit
  hattına PARALEL duran duvarlar (bilinen sınırlama) ve kesit konumuna
  ULAŞMAYAN kısa duvarlar (negatif test) dışlanır.
- **Genişletme noktası (kullanıcı talebi):** kesit alınırken kat
  yükseklikleri, galeri boşlukları veya merdivene denk gelen kısımların
  "zamanla güçlendirilebilir" olması istendi. Bugün bu senaryolar için
  PROJE VERİSİ yok; `SectionFeatureHook` Protocol'ü (`RailDrawingStandard`
  ile AYNI desen) tam olarak bu genişlemenin gireceği noktayı hazır tutar,
  çekirdek `SectionSheet.draw` değişmeden.
- **Plan işareti (kullanıcı talebi):** her kat paftasında kesit hattı +
  uçlarında bakış-yönü üçgeni + üçgenin SIRTINA yazılan kesit harfi
  (`draw_cut_marker_on_floor`). `AKS`ten BİLEREK farklı katman/linetype/
  renk (`KESIT`, `KESIT_HATTI`, kırmızımsı) — kullanıcı: *"farklı renkte ve
  desende çizgi."*
- **Pafta adı (kullanıcı talebi):** *"pafta ismine kesitin harfi verilir"*
  → `f"{cut.label} KESITI"` (örn. `"A-A KESITI"`).
- **`levels_from`:** kesit KENDİ kat yüksekliği istifini uydurmaz, bir
  `elevations[].id`den ödünç alır (verilmezse `elevations[0]`).
  **Invariant:** `floors[]` uzunluğu, hedef elevation'ın seviye sayısıyla
  BİREBİR eşit olmalı (kat↔seviye eşlemesi SIRAYLA yapılır) —
  `validate.py::check_sections` (açıkça bildirilen kesitler için) ve
  `SectionSheet.draw` (savunma amaçlı `ValueError`) bunu ikişer yerde
  denetler.

### DEV-025 — Kuzey oku + grafik ölçek çubuğu

- **Kuzey oku (`scripts/northarrow/`, YENİ modül):** kullanıcı açıkça
  *"kuzey oku için standart bir tasarım belirle, daha sonra tasarım
  değişikliğine gidildiğinde entegrasyon zor olmasın"* dedi — bu,
  `RailDrawingStandard` Protocol desenini DOĞRUDAN çağırdı:
  `NorthArrowStyle` Protocol'ü + `DefaultNorthArrowStyle` (daire + üçgen
  ibre + "K" etiketi). `meta.north_angle` (derece, saat yönünde, "yukarı"
  referansından) verilmezse ok HİÇ çizilmez — ana projede bu alan yok,
  dolayısıyla gerçek projede kuzey oku GÖRÜNMÜYOR (sıfır görsel etki);
  yalnızca yeni `golden/kesit_ornek` referansında (`north_angle=25`)
  sınandı.
- **Grafik ölçek çubuğu (`scripts/pafta::ScaleBar`, pafta'ya eklendi, YENİ
  modül GEREKMEDİ):** `meta.scale`den TÜRETİLEN, basılı çıktı küçültülüp/
  çoğaltılsa bile doğru ölçüyü koruyan standart bir öge. Segment uzunluğu
  (`nice_scale_length_m`) hedef ~20mm basılı genişliğe en yakın "nice"
  (1-2-5 serisi) gerçek-dünya metre değeridir (1:50→1m, 1:100→2m,
  1:200→5m, 1:500→10m, elle hesaplanabilir). **ScaleBar hiçbir opsiyonel
  veriye ihtiyaç duymadığı için** (sadece `meta.scale`) HER kat/görünüş/
  kesit paftasında OTOMATİK çizilir — bu da gerçek projeyi görsel olarak
  değiştirdi (her paftaya küçük bir ölçek cetveli eklendi).
- **Yerleşim:** her paftanın KUZEY (üst) kenarındaki padding bölgesinde,
  genişliğin TAM ORTASINDA — bu projede (ve `golden/duvar_standartlari`
  gibi mevcut fixture'larda) strüktürel akslar genelde kenarlarda olduğu
  için aks baloncuklarıyla çakışma riski düşüktür; piksel-kesin bir
  çakışmama GARANTİSİ yoktur (bilinen sınırlama, `pafta::CONTENT_PADDING`
  artışının çözdüğü rev-13 çakışmasıyla AYNI sınıf pragmatik yaklaşım).

### Doğrulama

- İki yeni self-test (`sections`, `northarrow` — ikincisi `pafta::
  ScaleBar`ı da sınar) — toplam ON modül self-test'i oldu.
- `py_compile`, `validate` (ana proje + `golden/kesit_ornek`), `generate`
  (`PaftaOverflowError` FIRLAMADI), `preview`, 5 semantik kural (`KESIT`
  katmanı `_code_owned_layers`e eklendi), 5 golden referans (4'ü
  `--update`, 1'i YENİ), `doc_check` — hepsi temiz.

### Golden output etkisi

- **Ana proje DEĞİŞTİ** (kullanıcının açık standardının doğal sonucu):
  `output/plan.dxf`e 2 yeni kesit paftası + her paftaya ölçek çubuğu
  eklendi; `docs/development/plan-golden-report.json` bu yüzden
  `--write` ile YENİDEN üretildi (rev-14/15'teki "sıfır görsel etki"
  emsalinin AKSİNE — bu değişiklik bilerek ve gözlemlenerek yapıldı).
- Mevcut 4 golden referansının TÜMÜ aynı sebeple değişti (`--update`).
- Yeni `golden/kesit_ornek`: 2 kat, FARKLI bölme duvarı x-konumuna sahip
  (4500 / 3000) — kesit hattının HER katta kendi duvarını doğru kestiğini
  (kat-başına bağımsız kesişim) hem elle hesaplanabilir hem entegrasyon
  seviyesinde kanıtlar; `meta.north_angle=25` ile kuzey oku de burada
  sınanır.

### Bilinen sınırlamalar

- `sections/`: eğik kesit yok (kullanıcı kararı); kesit hattına paralel
  duran duvar temsil edilemez; galeri boşluğu/merdiven kırılması için
  genişletme noktası hazır ama VERİ yok; seviye SIRASI doğrulanmaz (sadece
  SAYI eşitliği).
- `northarrow`/`ScaleBar`: aks baloncuklarıyla piksel-kesin çakışmama
  garantisi yok; elevations/sections'a kuzey oku çizilmez (kavramsal
  olarak anlamsız — bir düşey görünüşün/kesitin "kuzeyi" yoktur).

- **Sonraki direktif:** Kullanıcı ayrıca "kot (seviye/datum) verme
  mantığı"nın hem planda hem kesitte kullanılacağı için proje geneline
  hakim bir mantık olması gerektiğini, ayrı modül mü yoksa mevcut bir
  modül tarafından mı yönetilmesi gerektiğine karar verilemediğini
  belirtti. Bu, YENİ bir PLANNED görev olarak `DEV-029` altında
  `DEVELOPMENT_TASKS.md`ye eklendi (uygulama izni DEĞİLDİR — sistem
  mimarı açıkça seçmelidir).

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
