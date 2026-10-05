# templates modülü (sirkülasyon çekirdeği şablon üreteci) — DEV-037 + DEV-045

`floor_width`/`floor_depth`den, bir kat planının **sirkülasyon çekirdeğini**
(asansör + merdiven + dikdörtgen koridor + güney giriş duvarı) parametrik
olarak üreten TAMAMEN deterministik bir Python fonksiyonu. Koridor
**DEV-045'e kadar L-şekilliydi** — bkz. aşağıdaki "DEV-045 düzeltmesi".

## Merkezi cekirdek kisa kenar yerlesimi (rev-25)

`generate_central_core(stair_entry='short_edge')` varsayilandir: merdiven 3000x4000
kisa kenariyla hole bakar (kapisiz `passage`), asansor 2100x3000, L-seklinde 1000 mm
`shaft` odasi, cekirdek satiri 4000. `'long_edge'` rev-24 oncesi yerlesimi korur.

## Neden bu modül (kullanıcı talebi, 2026-09-28)

> "kat planları ve oda yerleşimleri için genel şablonlara sahip olacak, bir
> de şablon oluşturucu generator'ü olacak bu şekilde dil modeli yardımıyla
> özel bir yerleşim planı vs. istendiği zaman bu oluşturulabilecek. örneğin
> yerleşim planlarındaki bina ana girişi, dairelerin yerleşimi, kattaki
> daire sayısına göre efektif yerleşimler vs gibi verileri sağlayacak."

## Mimari not — "generator" dil modeline geometri ÜRETTİRMEZ

Bu ekleme kullanıcı tarafından açıkça istenmedi; bu modülü yazan ajan
tarafından kök `CLAUDE.md`'nin **"Deterministik üretim ilkesi"**yle
çelişmemek için ZORUNLU olarak eklendi: `generate_circulation_core(...)`
rastgele veya dil-modeli-uydurması **hiçbir** koordinat üretmez —
parametrelerden (genişlik/derinlik/çekirdek ölçüleri) rooms/walls/openings
sözlüğünü HESAPLAR. Bir agent bu fonksiyonu PARAMETRE seçerek çağırabilir
(kaç birim, hangi giriş yönü gibi yapılandırılmış seçimlerle) — kök
CLAUDE.md'nin zaten tanımladığı "talep → yapılandırılmış context patch"
akışının bir ÖNCÜSÜdür, geometriyi ÜRETEN kısım DEĞİLDİR.

## v1 kapsam sınırı — yalnızca sirkülasyon çekirdeği

**Daire/birim İÇİ oda bölüntüsü (salon/mutfak/banyo yerleşimi) v1 KAPSAMI
DIŞINDADIR.** Bu bilinçli bir sınırdır (`stairs`/`ceiling` ile AYNI
disiplin — net bir v1 sınırı, kapsam genişletme AYRI bir görev): gerçek
projenin `uA_*`/`uB_*`/`uC_*` birimlerinin ÜÇÜ DE farklı tasarlanmıştır
(farklı oda sayısı, farklı oranlar, farklı kapı yerleşimi) — bu GERÇEK bir
tasarım kararıdır ve bunu parametrik hale getirmek "kaç oda", "hangi
oranlarda", "kapı nereye açılır" gibi kendi başına büyük bir açık-karar
setine sahip AYRI bir görevdir (bkz. `docs/development/
DEVELOPMENT_TASKS.md` `DEV-037` "Açık kararlar" — özellikle "şablonun
çıktısı context.json parçası mı yoksa öneri raporu mu" kararı, birim
şablonlarına geçmeden ÖNCE netleşmelidir).

Sirkülasyon çekirdeği seçildi çünkü **tek belirsizliksiz, kanıtlanmış
desendir**: kök `CLAUDE.md`nin "Çok katli bina yapisi" bölümünde ZATEN
belgelenmiştir ve gerçek projenin **her** katında (otopark/dükkan+lobi/3
daire/çatı terası) AYNI konumda kullanılır ("Bu konum tum katlarda sabit
tutulmalidir asansor/merdiven duseyde hizali olsun diye").

## Varsayılan ölçüler NEREDEN geliyor — icat edilmedi, ÇIKARILDI

`CirculationCoreTemplate`in varsayılan değerleri (asansör genişliği
2100mm, merdiven genişliği 4000mm, koridor "bacağı" derinliği 1500mm, bant
derinliği 4500mm) gerçek projenin `context.json`ındaki (`normal1` katı)
ZATEN `validate.py`den geçmiş, çalışan sirkülasyon çekirdeğinden BİREBİR
çıkarıldı — `scripts/standards/`in v1 kataloğundeki "pratik varsayılan"
değerlerinden bile daha sağlam bir temele sahiptir (orada genel mimari
makuliyet, burada gerçekten ŞU AN ÇALIŞAN bir tasarım). `selftest.py`
bunu doğrudan kanıtlar: `generate_circulation_core(20000, 17500)`,
`normal1` katının oda poligonlarıyla/alanlarıyla/duvar konumlarıyla/kapı
konumuyla **BİREBİR** eşleşir.

**rev-20 düzeltmesi (kendi kendini düzelten bir örnek):** DEV-037'nin ilk
sürümünde (2026-09-28) bu varsayılan `elevator_width=1000mm` idi ve o
zamanki gerçek projeden ÇIKARILMIŞTI — ama bu değer `scripts/standards/`
(AYNI GÜN, DEV-036'da kurulan) `asansor` oran sınırını (max_ratio=1.5)
İHLAL EDİYORDU (1000×3000mm → oran 3.0). Bu, kullanıcının sistemi
kurarken verdiği TAM ÖRNEKTİ ("asansör kuyusu 3 m² ama piyasada karşılığı
olmayan bir oran") — yani bu modülün "kanıtlanmış, sağlam" diye tanıttığı
ilk varsayılan, aslında kullanıcının şikayet ettiği KUSURUN TA KENDİSİYDİ.
rev-20'de gerçek proje bu şablon aracılığıyla düzeltildi (2100mm'ye
genişletildi, oran 1.43'e düştü) VE bu varsayılan AYNI ANDA güncellendi —
"gerçek projeden çıkarıldı" iddiasının doğru KALMASI için (bkz.
`scripts/standards/CLAUDE.md` "Gelecek güncelleme sözleşmesi" ile AYNI
disiplin: kaynak veri değişince varsayılan da ONUNLA birlikte güncellenir,
aksi halde iddia yalan söylemeye başlar).

## Çıktı context.json'a YAZILMAZ (açık karar)

`generate_circulation_core` salt bir `dict` (`rooms`/`walls`/`openings`
listeleri) döndürür — context dosyasına DOKUNMAZ, DXF çizmez, `ezdxf`
içermez. Bunu context.json'a birleştirmek/yazmak AYRI, insan (veya insan
onaylı bir sonraki adım) kararıdır — kök `CLAUDE.md`nin "context.json
proje tasarım verisidir" ilkesiyle tutarlı: bu fonksiyon yalnızca BİR
KEZLİK bir üretim yardımcısıdır, otomatik bir yazma-hattı DEĞİLDİR.

## Çekirdek konumu sabit, yalnızca doğu ucu değişir

`floor_width` yalnızca koridorun/güney duvarının DOĞU ucunu belirler;
çekirdeğin kendisi HER ZAMAN sol-alt köşeye (x=0) sabittir — kök
`CLAUDE.md`nin "asansor/merdiven duseyde hizali olsun diye" ilkesiyle
tutarlı. Bu fonksiyon hangi X ofsetinde bir binaya yerleştirileceğine karar
VERMEZ (çağıran taraf, `generate_dxf.py::translate_floor` gibi bir
mekanizmayla kaydırabilir).

## DEV-045 düzeltmesi: koridor artık israf eden bir L-şekli DEĞİL

**Kullanıcının somut gözlemi:** *"şu anda örnek planımızda kat planında
sağ üstteki alan tamamıyla ölü bir alan."* Ölçüldü: `band` odasının eski
L-şekli, `x:core_x1..floor_width, y:core_y0..floor_depth` bölgesini
(bu projede 13900×3000mm ≈ 41.7 m²) GEREKSİZ yere `band_depth` (4500mm)
derinliğinde bırakıyordu — hiçbir işlevsel mahal İÇERMEYEN, salt geçiş
bile OLMAYAN bir alan (çünkü asıl giriş erişimi zaten `band_south`
duvarındaki `door_entry_*` kapılarıyla, bu bölgenin GÜNEYİNDEKİ ince
`corridor_leg_depth` şeridinden sağlanıyor).

**Kök neden (geometrik, "parametrize etmek" değil):** çekirdeğin
(asansör+merdiven) footprint'i `y >= core_y0`de durduğu için, koridorun
`y: band_y0..core_y0` (yalnızca `corridor_leg_depth` derinliğinde) bir
dikdörtgen olması TEK BAŞINA çekirdekle çakışmayı önlemeye YETERLİdir —
L-şeklinin eski "doğuda tam `band_depth`" uzantısı mimari olarak hiçbir
ihtiyacı KARŞILAMIYORDU, yalnızca polygon inşa mantığının bir kalıntısıydı.
Düzeltme: `band_polygon` artık basit bir dikdörtgen —
`[[0,band_y0],[floor_width,band_y0],[floor_width,core_y0],[0,core_y0]]`
— ve bu TEK BAŞINA (floor_width'e göre "parametrize etme" GEREKMEDEN) dead
alanı KALDIRIR. Bu projede `band` alanı 71.7 m² → **30.0 m²**'ye düştü.

**Plan metninin "Fikir 1 DENETLER, Fikir 2 DÜZELTİR" deseni GERÇEKTEN
tutarlı çalışıyor:** `architect::check_common_circulation_share` (Fikir 1,
bina/kat-seviyesi genelleme), gerçek projenin ESKİ `band` değeriyle (71.7
m², rev-23'e kadar `context.json`da duruyordu) çalıştırılınca %27.6 pay
ile UYARI üretir; aynı kontrol DÜZELTİLMİŞ `band` değeriyle (30.0 m²,
rev-23'ten İTİBAREN gerçek projenin KENDİ değeri) çalıştırılınca pay
%11.5'e düşer ve UYARI KALMAZ — bkz. `scripts/architect/selftest.py::
check_common_circulation_share_real_project_band_fixed_rev23`.
`DEV-036`/`DEV-037`deki (`standards`+`templates`) AYNI ilişki deseni.

**rev-23'te GERÇEK projeye UYGULANDI** (DEV-041/044/046 ile AYNI disiplin
ile BAŞLADI — düzeltme ÖNCE yalnızca `templates/`e kuruldu, context.json
bir süre eski 71.7 m²'lik şekli taşımaya devam etti — ama rev-23'te uC
yeniden-zonlama çalışmasıyla BİRLİKTE gerçek `context.json`un TÜM 9
katındaki `band` da bu dikdörtgene çekildi; `validate.py` artık gerçek
projede bu konuda UYARI üretmiyor, bkz. `scripts/architect/CLAUDE.md`
"DEV-045"). "Ölü alanın YERİNE ne konabileceği" (örn. ortak depo/
sığınak/teknik oda) HÂLÂ GERÇEK bir tasarım kararıdır ve UYDURULMADI; bu
düzeltme yalnızca GEREKSİZ fazla alanı KALDIRDI, boşalan yere bir şey
İCAT ETMEDİ — boşalan alan bina zarfının (dış duvarlar zaten var)
İÇİNDE, henüz hiçbir odaya ait OLMAYAN bir boşluk olarak duruyor.

## `include_band_south`: kat tipini BU MODÜL BİLMEZ

Kök `CLAUDE.md`: `band_south` duvarı zemin/normal katlarda VAR (giriş
kapılı), bodrum/çatıda YOK (açık geçiş). Bu fonksiyon hangi kat tipinin
hangisini istediğine KARAR VERMEZ — `include_band_south` parametresiyle
çağıran tarafa (kat tipini bilen) bırakılır.

## Public API

```python
from templates import CirculationCoreTemplate, generate_circulation_core

fragment = generate_circulation_core(
    floor_width, floor_depth,
    template=CirculationCoreTemplate(),  # opsiyonel, varsayilan gercek projeden
    id_prefix="",                          # birden fazla cekirdek icin cakisma onler
    include_band_south=True,               # zemin/normal=True, bodrum/cati=False
    units="mm",
)
# fragment == {"rooms": [...], "walls": [...], "openings": [...]}
```

## Çakışma denetimi: EXEMPT

`collision/scene.py::COLLISION_EXEMPT` içinde. Gerekçe: bu modül kendi
çakışma denetimini YAPMAZ — ürettiği `rooms`/`walls`/`openings` bir kata
birleştirildikten SONRA, NORMAL pipeline (`rooms.collision`/
`walls.collision`/`openings.collision`) zaten kapsar. `importer` ile AYNI
"aday veri üretir, denetimi kendi yapmaz" gerekçesi.

## DEV-055: merkezi çekirdek + kat holü (`central.py`)

`generate_central_core(floor_width, floor_depth, option=None, ...)`: asansör +
merdiven çekirdek satırı ile dikdörtgen kat holünü (en-boy oranı etüt
kararı) katın merkezine (veya `offset` ile kaymış) koyar; `rooms` (room_type
dolu), `walls`, `openings` (merdiven kapısı + asansör kapısı) ve `zone`
(blok, dört pay, `surrounds`, `hall_frontage`) döndürür. **Bağımlılık yönü:**
ölçüleri `architect::options_for_central_hall` hesaplar, bu dosya yalnız
geometriye çevirir (kısıt/karar modülleri çizimi bilmez). `core_side`
('north'/'south') ve `orientation` ('x'/'y') desteklenir; yansıma/devrik
`host_side` XOR ile yönetilir. Çıktı context'e YAZILMAZ; daire kapıları
etüdün işidir. `generate_circulation_core` (köşe çekirdeği) AYNEN kalır;
`CONTRACT_VERSION` 1.1.

## Doğrulama

`python scripts/templates/selftest.py` — 7 kontrol grubu: varsayılan
şablonun GERÇEK proje verisiyle (`normal1` katı) BİREBİR eşleştiği
(poligon/alan/duvar konumu/kapı konumu — `band` HARİÇ, DEV-045),
`band`in artık verimli bir dikdörtgen olduğu (elle hesaplanmış: 30.0 m²,
eski L-şekli 71.7 m²'ydi) VE basitleştirmenin çekirdek footprint'iyle
YENİDEN çakışmaya başlamadığı (yanlış-pozitif), çekirdek konumunun
`floor_width` değişse de SABİT kaldığı (yalnızca koridorun doğu ucu
büyüdüğü), `include_band_south` anahtarının YALNIZCA o duvarı etkilediği,
`id_prefix`in tüm üretilen kimliklere uygulandığı (çoklu çekirdek
çakışmasını önler), özel bir `CirculationCoreTemplate`in enjekte
edilebildiği.

`validate.py`de özel bir entegrasyon YOKTUR — bu modülün çıktısı
context.json'a hiç yazılmadığı için (yukarı bakınız) doğrulanacak bir
proje verisi henüz yoktur; üretilen parça bir kata birleştirildiğinde
NORMAL `validate.py` akışından geçer.

## Bilinen sınırlamalar

- **Daire/birim içi oda bölüntüsü YOK** (v1 kapsam sınırı, yukarı
  bakınız) — bu modül yalnızca sirkülasyon çekirdeğini üretir.
- **Bina ana girişi/kaç daire gibi üst-seviye "arketip seçimi" mantığı
  YOK** — bu fonksiyon yalnızca BİR çekirdeği üretir, hangi arketipin
  (tek çekirdekli/çift çekirdekli/ticari zemin) seçileceğine dair bir
  karar mekanizması içermez (bkz. `DEVELOPMENT_TASKS.md` `DEV-037`
  "Açık kararlar").
- **Dış çerçeve duvarları (ext_left/ext_right/ext_top/ext_bottom) ÜRETMEZ**
  — yalnızca çekirdeğin İÇ duvarlarını üretir; dış çerçeve çağıran tarafın
  sorumluluğundadır (bu modülün bilmediği bina dış hattı bilgisine
  ihtiyaç duyar).
- **`units="m"` desteği TEST EDİLMEDİ** (yalnızca `mm` gerçek projeyle
  karşılaştırılarak sınandı) — `to_m2` dönüşümü kod olarak doğru
  görünüyor ama `m` birimli bir golden referansla henüz KANITLANMADI.
- ~~`band_depth`/`corridor_leg_depth` sabitleri `floor_width`e/servis
  edilen birim sayısına göre ÖLÇEKLENMEZ.~~ **`DEV-045`'te KAPANDI:**
  koridor artık israf eden bir L-şekli DEĞİL — bkz. yukarıdaki "DEV-045
  düzeltmesi". `band_depth`/`corridor_leg_depth` sabitleri HÂLÂ `floor_
  width`e göre ölçeklenmiyor (bu DEĞİŞMEDİ) ama artık buna GEREK de yok
  — basit dikdörtgen biçimi zaten floor_width'ten BAĞIMSIZ olarak dead
  alan üretmiyor.
- **`stair_width`in oda-oranı varsayılanı gerçek bir TEK KOLLU merdiven
  kolunun (uzun-ince) oranını YANSITMAZ** — `standards::STANDARDS
  ['merdiven']` sınırının alt ucuna yakın ama kare'ye YAKIN bir oda
  ayırır. **`DEV-046`'da (stairs/) bu ARTIK bir SORUN DEĞİL:**
  `kind='dog_leg'` (çift kollu) bu oda oranıyla ZATEN rahatça çalışıyor
  — bkz. `scripts/stairs/CLAUDE.md` "Çift kollu merdiven geometrisi".
  `stair_width`in KENDİSİ (4000mm) hâlâ `templates/`in bir varsayımıdır,
  değişmedi.
