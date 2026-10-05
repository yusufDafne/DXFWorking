# stairs modülü (merdiven) — DEV-022 + DEV-046 + DEV-047

Kat paftalarındaki merdiven odasının İÇİNE gerçek basamak/rıht geometrisi,
(yön biliniyorsa) bir yön oku ve bir kesme çizgisi çizer. Kök `CLAUDE.md`nin
eskiden "bilinen basitleştirme" saydığı ("asansör/merdiven kapı sembolü
çizilmez, sadece etiketli kapalı oda olarak gösterilir") boşluğu merdiven
tarafında kapatır. **(2026-10-05, DEV-055: bu "basitleştirme" asansör kapısı için de KALDIRILDI — bkz. `scripts/openings/CLAUDE.md`.)**

## Neden ayrı bir modül (kullanıcı kararı, 2026-09-25)

`DEV-022`nin Fikir 1/Fikir 2 analizinde iki seçenek sunuldu: yeni bağımsız
modül mü, yoksa `rooms/`nin genişletilmesi mi. Kullanıcı **Fikir 1**'i
seçti: proje motifiyle (her çizim konusu kendi modülü) tutarlı, `columns/`
ve `furniture/`nin "oda-içi ek eleman = kendi modülü" desenini izler.
`rooms/` bugünkü net kapsamını (poligon + 3 satırlı etiket) korur.

## Veri disiplini — hangi alan gerçek ölçü, hangisi ofis standardı

Bu ayrım kritik ve kasıtlı:

| Alan | Kategori | Kaynak |
|---|---|---|
| `floor_to_floor_mm` | **GERÇEK proje verisi** (kat yüksekliği) | context.json, **ZORUNLU**, asla türetilmez/uydurulmaz |
| `room_id` (→ oda poligonu) | **GERÇEK proje verisi** | context.json, **ZORUNLU** |
| `riser_height_mm` | **Ofis çizim standardı** | Verilmezse `DEFAULT_RISER_MM=170` (ANSI33 hatch ölçeği, Arial Narrow font seçimi ile AYNI kategoride) |
| `going_mm` | **Ofis çizim standardı** | Verilmezse `DEFAULT_GOING_MM=270` (makul bant 250-300mm) |
| `step_count` | Türetilebilir | Verilmezse `floor_to_floor_mm / riser` üzerinden hesaplanır |
| `up_towards` | Opsiyonel yön verisi | Verilmezse yön oku + kesme çizgisi HİÇ çizilmez (kuzey oku ile AYNI "veri yoksa uydurma" deseni) |
| `kind` | Opsiyonel tür (DEV-046) | Verilmezse `single_flight` (eski/tek davranış, `walls.kind` ile AYNI opt-in desen) |
| `landing_depth_mm` | **Ofis çizim standardı** (DEV-046) | YALNIZCA `kind='dog_leg'` için anlamlı; verilmezse `DEFAULT_LANDING_DEPTH_MM=1100` |
| `exit_door_id` | Opsiyonel çapraz-referans (DEV-047) | Verilirse `validate.py`, bu kapının merdivenin GERÇEK çıkış yönüyle hizalı olup olmadığını denetler (UYARI) |

**Kullanıcının 2026-09-25 direktifi:** "default olarak 17 cm [riht] belirle
... eğer çok komplike bir nokta olması durumunda bu default değerlerin
otomatik esnetilebilme olanağı da olmalı ... esnetilebilirlik default true
... basamak genişliği 25-30 arasında olması makul ama default 27." Bu,
`DEFAULT_RISER_MM=170.0`, `DEFAULT_GOING_MM=270.0`, `DEFAULT_AUTO_FLEX=True`
olarak BİREBİR uygulandı.

## `resolve_stair` — TEK kaynak (openings::swing_geometry ile AYNI desen)

`resolve_stair(spec, room_polygon) -> StairResolution` hem `validate.py`
hem çizim kodu (`draw_stairs_on_floor`) tarafından ÇAĞRILIR. İkisi ayrı
hesap yaparsa (rev-13'te kapı açılım sektöründe GERÇEKTEN olduğu gibi)
sessizce ayrışırlar — bu modül baştan tek kaynaklı kuruldu.

Hesap sırası:

1. **Basamak sayısı/rıht:** `step_count` açıkça verilmişse `riser =
   floor_to_floor_mm / step_count` (türetilir, doğrulanır). Verilmemişse
   `step_count = round(floor_to_floor_mm / riser_nominal)`; `auto_flex`
   açıksa (varsayılan) `riser` bu `step_count`e göre yeniden hesaplanır
   (kat yüksekliğine TAM oturur); kapalıysa `riser` nominal kalır ve toplam
   kat yüksekliğini tam karşılamıyorsa UYARI verilir (HATA değil — kullanıcı
   `auto_flex=False` ile bunu bilerek istemiştir).
2. **Basamak genişliği (going):** gerekli koşu uzunluğu
   `(binding_steps - 1) * going` MEVCUT koşu uzunluğundan fazlaysa: `auto_flex`
   açıkken going daraltılır (UYARI); `auto_flex` kapalıyken hiç sığmıyorsa
   direkt `StairFitError`. `kind='single_flight'` için `binding_steps =
   step_count` ve mevcut koşu = oda'nın TÜM uzun ekseni (DEV-022'deki
   ORİJİNAL davranış, DEĞİŞMEDİ); `kind='dog_leg'` için `binding_steps =
   flight1_steps` (her zaman `flight2_steps`e eşit veya ondan büyük) ve
   mevcut koşu = oda'nın uzun ekseni EKSİ sahanlık derinliği (bkz. aşağıda
   "Çift kollu merdiven geometrisi (DEV-046)") — AYNI narrowing/MIN/MAX
   kod yolu, yalnızca girdi farklı. **`MIN_GOING_MM=250`/`MAX_GOING_MM=300`
   kontrolü KOŞULSUZDUR** — daraltılmış OLSUN ya da OLMASIN, nihai `going`
   değeri her zaman bu bantla karşılaştırılır: altındaysa **`StairFitError`**
   (bağımsız reviewer geçişinde bulunan gerçek bir açık: ilk sürümde bu
   kontrol yalnızca daraltma dalının İÇİNDEYDİ, yani zaten sığan bir odada
   açıkça verilmiş güvensiz bir `going_mm` — örn. 100mm — sessizce
   geçiyordu), üstündeyse UYARI (güvensiz değil, sadece standart dışı).
3. **Yön:** `up_towards` (`N`/`S`/`E`/`W`), merdivenin uzun ekseniyle
   (`travel_axis`) TUTARLI olmalı (dx≥dy → yalnızca `E`/`W` geçerli, aksi
   `StairFitError`). Verilmezse geometri yine hesaplanır, sadece ok/kesme
   çizgisi atlanır.
4. **Tür (`kind`, DEV-046):** `single_flight` (varsayılan) veya `dog_leg`.
   Bilinmeyen bir `kind` **yazım hatası korumasıdır** — sessizce
   varsayılana DÜŞMEZ, `StairFitError` fırlatır (`walls.kind`/`check_walls`
   ile AYNI desen).

## Çift kollu merdiven geometrisi (DEV-046)

**Neden gerekti (kullanıcı, 2026-09-28):** *"merdiven için ayrılan alan
daha ince uzun olmalı ve merdiven modülü oraya merdiven çizmeli."*
Gerçek projenin `Merdiven` odası (4000×3000mm) `MIN_GOING_MM`'yi ihlal
ettiği için tek kollu merdiven `StairFitError` fırlatıyordu — oda
büyütülmeden/uzatılmadan çözümün tek yolu farklı bir merdiven TÜRÜDÜR.

**Geometri — "dog-leg" (180° dönüşlü, sahanlıklı çift kol):** oda kısa
ekseni (perpendicular) **ortadan ikiye** bölünür (`MIN_FLIGHT_WIDTH_MM=900`
altına düşerse `StairFitError`); her yarı bir KOL'dür. Basamak sayısı
kollara `flight1 = ceil(step_count/2)`, `flight2 = step_count - flight1`
olarak (deterministik, "min kol 1" kuralı — `_travel_coords`in "min ucu
keyfi olarak aşağı" kuralıyla AYNI aile) bölünür. Kol 1, giriş ucundan
`up_towards` yönünde bir **sahanlığa** (`landing_depth_mm`, varsayılan
`DEFAULT_LANDING_DEPTH_MM=1100`) kadar çıkar; sahanlık oda GENİŞLİĞİNİN
TAMAMINI kaplar (180° dönüş platformu); kol 2, sahanlıktan **TERS yönde**
(gerçek bir merdivende olduğu gibi) geri döner ve GİRİŞ ucuna YAKIN bir
noktada biter.

**DEV-047: çıkış noktası GİRİŞİN YANINDADIR, odanın "yukarı" köşesi
DEĞİL.** Bu, kullanıcının *"merdivenin sahanlıklarına göre çıkış
noktalarını belirlemeli ... her merdivenin kat sahanlığından dönerek
koridora çıkılır"* gözleminin TAM karşılığıdır — tek kollu merdivende
"çıkış" sezgisel olarak odanın "uzak" köşesiydi (`up_towards` ucu); çift
kollu merdivende bu YANLIŞ olurdu, çünkü 180° dönüş sonunda insan GİRİŞE
yakın bir yerden çıkar. `StairResolution.exit_point`/`exit_direction`
(HER İKİ tür için de dolu) bu gerçek geometriyi KODLAR:

- `single_flight`: `exit_point` = odanın "yukarı" ucu (eski örtük
  varsayımla BİREBİR AYNI — `_travel_points`in "yukarı" noktası),
  `exit_direction = up_towards`.
- `dog_leg`: `exit_point`, kol 2'nin bittiği GERÇEK nokta (giriş ucuna
  yakın, ama tam ÜZERİNDE DEĞİL — kol uzunlukları eşit olmayabilir, bkz.
  `_dog_leg_exit_and_landing`), `exit_direction` = `up_towards`in TAM
  TERSİ (`_OPPOSITE_DIRECTION`) — kol 2, kol 1'in ters yönünde yürür.

**`exit_door_id` (opt-in) → `validate.py::check_stairs`:** bir kapı bu
alanla işaretlenirse, kapının duvar-merkez-çizgisi konumu
(`walls::Wall.centerline_point` — bu modülün DIŞINDA, TEK kaynaktan
hesaplanır, `stairs/` `walls/`e bağımlı KALMAZ) oda sınırının HANGİ
kenarına EN YAKIN olduğuyla (`_nearest_bbox_side`) karşılaştırılır; bu
kenar `exit_direction`den FARKLIYSA **UYARI** (HATA DEĞİL — bu bir mimari
sağduyu kontrolüdür, `architect/`in HER ZAMAN UYARI politikasıyla AYNI).
Mm hassasiyetinde bir mesafe eşiği yerine "en yakın kenar" testi
seçildi — plan metninin kendi belirsizliğini ("90 derece dönüş mü, 180
derece mi, tek bir kurala indirgenemeyebilir") TÜRDEN BAĞIMSIZ, sağlam
bir geometrik testle çözer.

**Görsel:** `DefaultStairStandard.draw`, `kind='dog_leg'` için her iki
kolun rıht çizgilerini (kendi şeridinde), sahanlık dikdörtgenini (4
kenarlı kapalı `LWPOLYLINE`), kollar arası bir BÖLÜCÜ çizgiyi (sahanlık
bölgesine GİRMEZ) ve (yön biliniyorsa) yön okunu/kesme çizgisini —
`exit_point`e göre konumlanmış ve kesme çizgisi ARTIK yalnızca kol-2
ŞERİDİ genişliğinde (tam oda genişliği DEĞİL, aksi var OLMAYAN kol-1
şeridinin üzerine taşan yanlış bir çizgi üretirdi) — çizer. Yön oku/kesme
çizgisi kod yolu tek kollu ile PAYLAŞILIR (`down`/`up` capa noktaları tür
bazında farklı hesaplanır, gerisi tekrar YAZILMAZ).

**`standards::STANDARDS['merdiven']` SAYISAL olarak DEĞİŞMEDİ (plan
metninin "Fikir 2"si değerlendirildi, gerekmedi):** gerçek projenin
4000×3000mm odası (oran 1.333) zaten `[1.3, 2.4]` aralığında VE bu aralık
hem tek kollu HEM dog_leg için anlamlı kalıyor (`max_ratio=2.4` aşırı
uzun — dog_leg için GEREKSİZ/VERİMSİZ — bir oda şeklini de doğru şekilde
reddeder). Yalnızca etiket metni ("tek kollu" → "oda oranı") ve `source`
açıklaması DÜZELTİLDİ — sayısal bir KALİBRASYON DEĞİL, artık YANLIŞ olan
bir varsayımın metninin düzeltilmesi (bkz. `scripts/standards/
__init__.py`).

Her esnetme (riht VEYA going) `StairResolution.warnings`e yazılır;
`generate_dxf.py` bunları "UYARI (merdiven): ..." olarak basar —
`validate.py`deki sürüm/çakışma uyarılarıyla AYNI görünürlük ilkesi
(sessiz varsayım yapılmaz, bkz. kök CLAUDE.md "Deterministik üretim
ilkesi").

## rev-26 geri bildirim duzeltmeleri (kullanici, 2026-10-05)

- **Sahanlik HER ZAMAN merdiven boslugunun UCUNDA** (dog_leg: odanin uzak ucu, tum
  genislik; three_flight: ust bant). Eski surum kolun bittigi yerde sahanlik koyuyor
  ve kalan boyu bos birakiyordu (donulemeyen merdiven). Artik artan boy sahanliga katilir;
  sahanlik derinligi = oda boyu - (n1-1)*going (>= 1100 varsayilan asgari korunur).
  Kol 2 sahanligin YAKIN kenarindan baslar ve giris ucuna doner.
- **Yon oku "ust kata cikis" yoludur** (`StairResolution.arrow_path`): giris -> kol 1 ->
  sahanlikta don -> son kol -> cikis; ok basi cikista. Cok kollu turlerde kesme cizgisi
  cizilmez; yalniz tek kollu eski ok + kesme cizgisi davranisini korur.
- **Kesit:** `StairResolution.treads` ([{kind: tread|landing|floor, bbox, z_mm}]) ve
  `stair_section_profile(res, axis, coord)` merdivenin ICINDEN gecen bir kesit hatti icin
  basamak profilini verir (s araligi + ust yuzey kotu). `sections/` bununla cizer
  (baglanti AYRI is: `SectionFeatureHook`); stairs sections'i import ETMEZ.
- **three_flight algoritmasi:** kuyu en KARE olacak sekilde `n2` (orta kol basamagi) secilir;
  n1=n3=m; e=(A-(n2-1)g)/2, d=H-(m-1)g; w=min(A/3, e). Proje: 4000x4000, 3000 mm kat
  6/6/6 (kuyu 1350x1350), ZK 4000 mm 8/8/8 (kuyu 1890x1890), going 270.
- **Proje cekirdegi (rev-26):** asansor 2100x3000 + kare 4000x4000 merdiven; merdiven acikligi
  `passage` merdiven genisligi (4000) kadar ve duvar payisiz; saft odasi cekirdekte YOKTUR
  (asansor ustundeki 2100x1000 nis K katlarda uB `Depo`, diger katlarda komsu odaya katilir).

## Merdiven turleri (`kind`, rev-26)

| `kind` | Sekil | Notlar |
|---|---|---|
| `dog_leg` | U, TEK ara sahanlik | **VARSAYILAN** (rev-26; eskiden `single_flight`). |
| `single_flight` | sahanliksiz ince uzun tek kol | acikca `kind` ile istenir. |
| `three_flight` | kare/yaklasik kare boslukta U, IKI ara sahanlik, uc kol | `well='open'` (varsayilan) / `'filled'`; `flight_width_mm` (varsayilan oda enine/3, >= 900). |

`three_flight` kanonik cerceve: a = yukari eksenine dik, b = giris kenarindan
yukari. Kol 1 (a:0..w, b:0..H-w) yukari, sahanlik 1 (w x w, kuzey-bati), kol 2
(a:w..A-w, b:H-w..H) yan, sahanlik 2 (kuzey-dogu), kol 3 (a:A-w..A) geri iner;
giris ve cikis AYNI kenarda (giris ucu = `up_towards`in tersi). Basamaklar kol
boylariyla (H-w, A-2w, H-w) orantili dagitilir (en buyuk kalan), tek ortak going
en siki kola gore daraltilir (MIN/MAX kurallari ayni). `up_towards` N/S/E/W
serbesttir (kare odada uzun eksen yok); yoksa geometri N kabul edilir, ok cizilmez.
Merdiven oda oranina "daha dikdortgen olmali" kurali `three_flight` odasina
UYGULANMAZ (`validate.py`). `golden/merdiven_uc_kollu` + selftest elle hesaplar.

## Kisa kenar girisi ve kapisiz acikli (rev-25)

Kullanici karari: merdiven kisa kenardan baslar, ara sahanlikta doner; giris ve
cikis KAT HOLUNDEN, kisa kenardaki giris ucundan yapilir; uzun kenarin
ortasindan girilmez; merdiven alani icin KAPI yoktur, dogrudan duvar acikligi
(`openings[].type='passage'`) vardir. Uygulama:

- `stair_entry_side(resolution)` = giris ucunun yonu (`up_towards`in tersi;
  dog_leg'de `exit_direction` ile ayni). `up_towards` yoksa `None`.
- `stair_access_warnings(resolution, accesses)` (hepsi UYARI): giris kenari
  disindaki (uzun kenar) acikliga, `door` tipli acikliga ve giriste hic
  acikligi olmayan merdivene uyari. `validate.py::check_stairs`
  (`_stair_room_accesses`) merdiven odasi sinirindaki acikliklari bulup
  cagirir; `stairs/` `walls/`e bagimli degildir.
- Standartlar degismedi: riht 170, going 270 (250-300), auto_flex; sahanlik
  1100 ofis varsayilani. Bu projede 3000x4000 oda: 3000 mm katta 18 basamak 9+9
  (daralma yok), ZK 4000 mm'de 24 basamak 12+12, going 263.6'ya daralir (UYARI).
- Cekirdek yerlesimi `templates::generate_central_core(stair_entry='short_edge')`
  (varsayilan; `'long_edge'` eski yerlesim): merdiven 3000x4000, asansor 2100x3000,
  L-seklinde 1000 mm saft. Saft yalniz oda olarak ayrilir; saft/baca modulu ayri fikir.
- Sinirlama: sahanlik (1100) kol genisliginden (1500) dar; cati katinda merdiven cizilmez.

## Public API

```python
from stairs import (
    resolve_stair, StairResolution, StairFitError,
    StairDrawingStandard, DefaultStairStandard,
    ensure_stair_layer, stairs_for_floor, draw_stairs_on_floor,
    exit_door_alignment_warning,
    DEFAULT_RISER_MM, DEFAULT_GOING_MM, MIN_GOING_MM, MAX_GOING_MM,
    SINGLE_FLIGHT, DOG_LEG, STAIR_KINDS, DEFAULT_STAIR_KIND,
    DEFAULT_LANDING_DEPTH_MM, MIN_FLIGHT_WIDTH_MM,
)

warnings = draw_stairs_on_floor(msp, floor)   # her kat icin
```

`StairDrawingStandard` bir Protocol'dür (`RailDrawingStandard`/
`NorthArrowStyle` ile AYNI enjeksiyon deseni) — yarın ofis farklı bir
sembol (örn. dolu ok yerine çift çizgi ok) isterse yeni bir `draw(...)`
sağlayıcısı yazılır, `draw_stairs_on_floor(msp, floor, standard=...)`
çağrı sözleşmesi DEĞİŞMEZ.

## Katman

`MERDIVEN` katmanı, kod-seviyeli sabit `STAIR_RGB = (60, 120, 150)`
(mavi-gri) rengiyle `ensure_stair_layer` ile idempotent kurulur
(`ensure_axis_layer` deseni — context.json'dan renk ALINMAZ). Bu ton
BİLEREK projedeki diğer kod-seviyeli ailelerden (AKS/KOLON grisi, TEFRİS
kahverengi ailesi) farklı seçildi — bkz. `DEV-030` (katman renk
organizasyonu, henüz PLANNED; bu modül o planın "iyi örnek" listesine
eklenebilir).

## Çakışma denetimi: EXEMPT

`collision/scene.py::COLLISION_EXEMPT` içinde listelenir. Gerekçe: bu
modül YENİ bir mekansal ayak izi ÜRETMEZ — yalnızca zaten `rooms.collision`
tarafından kapsanan bir oda poligonunun İÇİNE anotasyon çizer (aynı oda,
aynı koordinat uzayı). `dimensions`/`axis` ile AYNI "anotasyon, madde
değil" gerekçesi.

## Bilinen sınırlamalar (v1 kapsamı)

- ~~Yalnızca tek düz kollu (sahanlıksız) merdiven.~~ **`DEV-046`/`DEV-047`'de
  KAPANDI:** `kind='dog_leg'` (sahanlıklı, 180° dönüşlü çift kol) artık
  desteklenir — bkz. yukarıdaki "Çift kollu merdiven geometrisi (DEV-046)".
  Örnek projenin 4000×3000mm `Merdiven` odası bu TÜRLE (narrowing bile
  gerekmeden, 3000mm kat yüksekliğinde) RAHATÇA sığıyor; 4000mm kat
  yüksekliğinde (zemin kat) hafif bir going-daraltmasıyla sığıyor — her
  ikisi de `scripts/stairs/selftest.py`de ELLE doğrulanır. **Gerçek
  `context.json`a `stairs[]` verisi HENÜZ EKLENMEDİ** — bu görevin
  kapsamı (DEV-041/DEV-044 ile AYNI disiplin) yalnızca MODÜL desteğini
  kurmaktı; 8 kattaki `Merdiven` odasına gerçek `stairs[]` girdilerini
  (+ `exit_door_id` bağlantılarını) eklemek AYRI, sonraki bir proje
  revizyonu konusudur. Dönel/üç-kollu merdiven HÂLÂ desteklenmiyor.
- **Kesit entegrasyonu bu revizyonun KAPSAMINDA DEĞİL.** `sections::
  SectionFeatureHook` genişletme noktası merdiven kırılma çizgisi için
  hazır tutuluyor (bkz. `scripts/sections/CLAUDE.md`) ama bu modül henüz
  ona bağlanmadı — ayrı bir takip konusu.
  `stairs` modülü `sections`ı import ETMEZ, ileride tersi yönde
  (`sections` → `stairs`) enjekte edilebilir.
- **Rıht/going tüm basamaklarda TEK bir sabit değerdir** — gerçek
  merdivenlerde ilk/son basamak farklı olabilir (ör. taşma payı); bu
  modül bunu modellemez.
- **Merdiven kolu tam oda genişliğinde (`single_flight`) veya tam yarısında
  (`dog_leg`, iki kol) çizilir** — korkuluk/duvar payı (margin) veya
  kollar arası GERÇEK bir boşluk/duvar modellenmez (yalnızca ince bir
  bölücü ÇİZGİ, bkz. yukarı).
- **`MIN_FLIGHT_WIDTH_MM=900`/`DEFAULT_LANDING_DEPTH_MM=1100` "v1 pratik
  varsayılan"dır** — `standards/`in kendi disipliniyle AYNI, resmi bir
  yönetmelik atfı DEĞİL.
- **Kol 1/kol 2 ataması ("hangi yarı önce çıkar") DETERMİNİSTİK ama
  KEYFİDİR** (`_travel_coords`in "min ucu aşağı" kuralıyla AYNI aile) —
  kullanıcı tercihine göre SEÇİLEBİLİR bir alan DEĞİLDİR.

## Doğrulama

`python scripts/stairs/selftest.py` — elle hesaplanabilir riht/going
türetme, `auto_flex` açık/kapalı davranış farkı, going daraltma + MIN
altında `StairFitError` (+ yanlış-pozitif: sığan oda hata VERMEMELİ),
**açıkça verilmiş güvensiz `going_mm`nin daraltma dalı hiç TETİKLENMESE
bile reddedilmesi** (+ yanlış-pozitif) ve MAX üstünde UYARI, riht çizgisi
koordinatlarının HEM X HEM Y seyahat ekseninde elle hesaplanabilir olması
(bağımsız review sırasında yakalanan bir x/y-takas hatasının regresyon
testi), `up_towards`/`travel_axis` tutarlılığı (+ yanlış-pozitif), çizilen
varlık sayıları (yönsüz/yönlü), bilinmeyen `room_id`nin çizim tarafında
sessizce atlanması, katman RGB'si.

**DEV-046 (`dog_leg`):** gerçek `Merdiven` odasında (4000×3000mm, bkz.
`ROOM_4000x3000`) 3000mm kat yüksekliğinde (narrowing GEREKMEDEN) VE
4000mm'de (narrowing İLE) elle hesaplanabilir `step_count`/`riser`/
`going`/`flight_step_counts`/`landing_bbox`/`exit_point`/`exit_direction`;
kol genişliği `MIN_FLIGHT_WIDTH_MM` altında `StairFitError` (+ yanlış-
pozitif: geniş oda hata VERMEMELİ); sahanlık oda uzun ekseninden büyükse
`StairFitError`; bilinmeyen `kind` `StairFitError` (yazım hatası
koruması); `kind` hiç verilmeyince `StairResolution`'ın YENİ alanlarının
(`landing_bbox=None`, `flight_step_counts=(step_count,)`, `exit_point`/
`exit_direction`) eski davranışı BİREBİR yansıttığı (regresyon testi);
çizilen varlık sayıları (yönlü/yönsüz, elle hesaplanmış: 2×(kol-1)
riht + 1 sahanlık + 2 bölücü [+ 4 yön/kesme]).

**DEV-047 (`exit_door_id`):** `scripts/validate_selftest.py`de — hizalı
kapı YANLIŞ-POZİTİF üretmez, hizasız kapı TAM 1 UYARI verir (HATA DEĞİL),
`exit_door_id` OPT-IN'dir (verilmezse kontrol SESSİZCE atlanır), geçersiz
`exit_door_id` HATA verir. Ayrıca `golden/merdiven_cift_kollu` — gerçek
`Merdiven` odasıyla AYNI boyutta, `exit_door_id` HİZALI bir kapıyla,
uçtan uca (schema+validate+generate+golden) SIFIR uyarı/hata ile geçer.

`validate.py::check_stairs` (arity-1: `room_id` geçerli mi, `resolve_stair`
hata/uyarı üretiyor mu) `resolve_stair`i ÇAĞIRIR — ayrı bir doğrulama
mantığı YAZMAZ.
