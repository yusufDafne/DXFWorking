# templates modülü (sirkülasyon çekirdeği şablon üreteci) — DEV-037

`floor_width`/`floor_depth`den, bir kat planının **sirkülasyon çekirdeğini**
(asansör + merdiven + L-şekilli koridor + güney giriş duvarı) parametrik
olarak üreten TAMAMEN deterministik bir Python fonksiyonu.

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
1000mm, merdiven genişliği 4000mm, koridor "bacağı" derinliği 1500mm, bant
derinliği 4500mm) gerçek projenin `context.json`ındaki (`normal1` katı)
ZATEN `validate.py`den geçmiş, çalışan sirkülasyon çekirdeğinden BİREBİR
çıkarıldı — `scripts/standards/`in v1 kataloğundeki "pratik varsayılan"
değerlerinden bile daha sağlam bir temele sahiptir (orada genel mimari
makuliyet, burada gerçekten ŞU AN ÇALIŞAN bir tasarım). `selftest.py`
bunu doğrudan kanıtlar: `generate_circulation_core(20000, 17500)`,
`normal1` katının oda poligonlarıyla/alanlarıyla/duvar konumlarıyla/kapı
konumuyla **BİREBİR** eşleşir.

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

## Doğrulama

`python scripts/templates/selftest.py` — 5 kontrol grubu: varsayılan
şablonun GERÇEK proje verisiyle (`normal1` katı) BİREBİR eşleştiği
(poligon/alan/duvar konumu/kapı konumu), çekirdek konumunun `floor_width`
değişse de SABİT kaldığı (yalnızca koridorun doğu ucu büyüdüğü), `include_
band_south` anahtarının YALNIZCA o duvarı etkilediği, `id_prefix`in tüm
üretilen kimliklere uygulandığı (çoklu çekirdek çakışmasını önler), özel
bir `CirculationCoreTemplate`in enjekte edilebildiği.

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
