# Geliştirme Görev Kuyruğu

Bu dosya sistem geliştiricisinin sıradaki kontrollü işini gösterir. Aynı anda
tek bir görev `IN_PROGRESS` olabilir. Sistem mimarı `READY` görevi başlatır;
agent kendi başına sıra değiştirmez.

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

## READY

**Şu anda `READY` durumda görev YOKTUR.** Planlanan tüm modül maddeleri
(`DEV-011` … `DEV-018`) tamamlandı. Kalan iş, mevcut modüllerin "Bilinen
sınırlamalar" bölümlerinde açık fikir olarak duran ikinci fikirlerdir (ör.
`legend/` Fikir 2, `elevations/` Fikir 2, `walls/` Fikir 2,
`importer/` Fikir 2) — hiçbiri sistem mimarı açıkça seçmeden başlatılmaz.

> `DEV-007` kullanıcı talimatıyla (rev-12) **konusu açılmadan** plan olarak
> bekleyecektir; agent bu madde için veri İSTEMEZ. İmza alanları rev-12'de
> çözüldü (MİMAR / BELEDİYE / YETKİLİ 1 / YETKİLİ 2); geriye yalnızca mimar
> adı ve proje tarihi kaldı ve bunları kullanıcı kendisi verecektir.


## COMPLETED

### DEV-001 — Openings modülünü oluştur

- **Durum:** COMPLETED
- **Sonuç:** Typed `Opening`, `Door`, `Window`, `OpeningSchedule` ve
  enjekte edilebilir `DefaultPlanOpeningStyle` `scripts/openings/` içine alındı;
  generator host-wall ve açıklık genişliği doğrulaması yapıyor.
- **Kayıt:** `DEVELOPMENT_HISTORY.md` içindeki `HD-003`.

### DEV-002 — Room modülü

- **Durum:** COMPLETED
- **Sonuç:** `Room`, `PolygonOps`, `RoomLabeler` ve scanner sınırı
  `scripts/rooms/` içinde; kapanış, alan, self-intersection ve units-aware
  alan doğrulaması aktif.
- **Kayıt:** `DEVELOPMENT_HISTORY.md` içindeki `HD-003`.

### DEV-003 — DimensionChain modülü

- **Durum:** COMPLETED
- **Sonuç:** `DimensionChain`, `LinearDim`, `DimensionStyle` ve `ChainLayout`
  `scripts/dimensions/` içinde; AxisGrid gerçek DXF ölçülerini bu API ile
  üretir ve baseline bounds kontrolünden geçirir.
- **Kayıt:** `DEVELOPMENT_HISTORY.md` içindeki `HD-003`.

### DEV-004 — Golden output anlamsal karşılaştırması

- **Durum:** COMPLETED
- **Sonuç:** `scripts/golden_report.py` entity count/type, layer dağılımı,
  modelspace bbox ve SHA-256 raporu üretir; `--compare` ile semantic kontrol
  yapar.
- **Kayıt:** `DEVELOPMENT_HISTORY.md` içindeki `HD-002`.

### DEV-005 — Agentic kontrol altyapısı

- **Durum:** COMPLETED
- **Sonuç:** `development_control.py` atomik görev kilidi,
  `AGENT_PERMISSIONS.json` rol izinleri ve `PROVENANCE_TEMPLATE.json` eklendi.
- **Kayıt:** `DEVELOPMENT_HISTORY.md` içindeki `HD-002`.

### DEV-006 — Golden fixture kataloğu

- **Durum:** COMPLETED (rev-10)
- **Sonuç:** `golden_report.py` üç katmanlı hale geldi: ölçüm raporu +
  **semantik kurallar** + **fixture koşucusu**. Kurallar: `room_labels`
  (3 satır ve oda içinde), `opening_symbols` (kapı başına ARC),
  `axis_bubbles` (çizgi baloncuğa girmez), `block_references` (tanımsız blok
  yok), `declared_layers`. Beş kuralın hepsi **negatif testle** doğrulandı
  (kasıtlı bozma → kural patladı). `entity_bbox` artık ezdxf'in gerçek extent
  hesabını kullanıyor; önceki sürüm `INSERT` için yalnızca ekleme noktasını
  döndürüyordu (blok körlüğü — `DEV-018`de tespit edilmişti) ve `TEXT` için
  de metin genişliğini görmüyordu. Fixture kataloğu
  `fixtures/` altında: `fixtures/minimal` ve `fixtures/tefris_kolon`.
- **Fixture'ların ilk günde yakaladıkları (gerçek bulgular):**
  1. **Kapak paftası projeye asgari yükseklik dayatıyor.** 1:50'de A4 kapak
     14850 yüksek; içeriğin düşey açıklığı 8150'den küçükse üretim
     `PaftaOverflowError` ile durur. `minimal` fixture 4000 derinlikle
     yazıldığında hemen patladı. Bu sınır daha önce belgelenmemişti.
  2. **`draw_floor_sheet` içinde isim çakışması.** Mahal etiketi için
     kullanılan `label_style` yerel değişkeni, kolon `label_style`
     parametresini gölgeliyordu; `tefris_kolon` fixture'ı bunu yakaladı.
- **Kayıt:** `DEVELOPMENT_HISTORY.md` içindeki `HD-006`.
- **Önceki öncelik:** 1
- **Bu görev neden var (problem):** Bugünkü `scripts/golden_report.py`
  yalnızca **dört kaba ölçü** karşılaştırıyor: toplam entity sayısı, entity
  tür dağılımı, layer dağılımı ve modelspace bounding box. Bu, bir
  regresyonu yakalamak için **zayıftır** — örneğin bir duvar 2 metre kaysa,
  bir kapı ters yöne açılsa veya bir mahal etiketi yanlış odaya yazılsa
  entity sayısı ve türleri değişmediği için rapor **"eşleşiyor" der ve
  hatayı kaçırır**. Bounding box da yalnızca en dış sınırı gördüğü için iç
  geometrideki kaymaları fark etmez.
- **Amaç:** Golden kontrolünü "kaç tane var" seviyesinden "doğru yerde ve
  doğru biçimde mi" seviyesine çıkarmak; bunu tüm projeyi tek parça
  karşılaştırarak değil, modül bazlı fixture'larla yapmak.
- **Fikir 1 — Modül bazlı mini fixture'lar:** Her modül için küçük, elle
  doğrulanmış birer context parçası (tek oda + tek kapı; iki aks + bir ölçü;
  tek kapak paftası) ve her birinin beklenen çıktısı. Bütün projeyi
  karşılaştırmak yerine modül modül karşılaştırılır; böylece bir fark
  çıktığında **hangi modülün** bozulduğu doğrudan görünür. Bugün 2226
  entity'lik tek bir rapor var ve fark çıktığında nerede olduğu belli olmaz.
- **Fikir 2 — Kritik sembol/geometri beklentileri:** Sayı yerine kural
  doğrulamak. Örnek beklentiler: "her kapı açıklığı 1 ARC + 3 LINE üretir",
  "aks çizgisi baloncuğun içine girmez", "her mahal etiketi 3 TEXT'tir ve
  tamamı kendi oda poligonunun içinde kalır", "ölçü metni tam sayı cm'dir".
  Bunlar toleranslı geometrik karşılaştırmalardır ve bugünkü raporun tamamen
  kör olduğu hata sınıfını yakalar. (Mahal etiketi kuralı `DEV-008`de elle
  yazılan bir kontrol olarak zaten bir kez uygulandı — 125/125 oda doğrulandı;
  bu görev onu kalıcı hale getirir.)
- **Açık kararlar:** Fixture'lar `context.json`'dan bağımsız ayrı dosyalar mı
  olacak? Geometrik karşılaştırmada tolerans ne olacak? Beklenti tanımları
  veri (JSON) olarak mı, kod olarak mı yazılacak?

### DEV-019 — Çakışma denetimi (`scripts/collision/`)

- **Durum:** COMPLETED (rev-12)
- **Sonuç:** `scripts/collision/` kuruldu ve `validate.py` içine **bloklayıcı
  kapı** olarak bağlandı — üretimden ÖNCE, context seviyesinde çalışır.
  Modül bağımsızlığı **bağımlılık tersine çevrilerek** korundu: motor hiçbir
  çizim modülünü import etmez, her modül kendi ayak izini
  `scripts/<modül>/collision.py::footprints(floor, context)` ile verir
  (`rooms`, `walls`, `columns`, `openings`, `furniture`). `geometry.py`
  projedeki poligon matematiğinin tek sahibi oldu; `validate.py` içindeki
  Sutherland–Hodgman KOPYASI kaldırıldı.
- **Doğrulama (kasıtlı bozma):** `python scripts/collision/selftest.py` —
  bozulmuş bir katta tam 3 HATA (iki tefriş üst üste, tefriş oda dışında,
  tefriş kapı sektöründe) + 1 UYARI (tefriş duvara 50 mm girmiş) beklenir;
  yanlış-pozitif de sınanır (3 mm girişim TEMAS'tır, kolonun duvarda/odada
  olması normaldir). Kesişim ölçüsü elle doğrulanabilir: 800 × 750 = 600000
  mm², derinlik 750. Ayrıca boru hattı seviyesinde dört negatif test
  çalıştırıldı: çakışma → `exit 1`, oda dışı → `exit 1`, MAJOR sürüm farkı →
  `exit 1`, MINOR fark → `exit 0` + uyarı.
- **Mekanik hale getirilen kural:** "Yeni bir modül eklendiğinde 'bu modül
  hangi modülle çakışabilir?' sorusu açıkça yanıtlanır" kuralı artık düzyazı
  değil: `doc_check.py`, geometri üreten her modülün ya `collision.py`si
  olmasını ya da `COLLISION_EXEMPT` içinde **gerekçesiyle** listelenmesini
  arar. Üç yeni kontrolün hepsi kasıtlı bozma testinden geçti.
- **Kayıt:** `DEVELOPMENT_HISTORY.md` içindeki `HD-007`.
- **Problem:** Bugün çizim **doğrulanmıyor, sadece üretiliyor.** Bir koltuk
  duvarın içine, kapı açılım yayının üstüne veya odanın tamamen dışına
  konabilir; kolon bir odanın ortasında durabilir. Ne `validate.py` ne golden
  raporu bunu görür — golden'ın işi "çıktı beklenmedik şekilde değişti mi",
  "çizim doğru mu" değil. Bu ikisi farklı sorulardır ve karıştırılması
  kolaydır.

#### KARAR (rev-12): ayrı modül — ama modüllerin geometrisini BİLMEDEN

Soru "ayrı modül mü, her modül kendi mi" biçiminde sorulduğunda iki cevap da
kısmen doğrudur, çünkü ortada **tek bir kontrol sınıfı yoktur, iki tane
vardır.** Ayrım aritedir:

| Arite | Soru | Sahibi | Bugünkü durum |
| ----- | ---- | ------ | ------------- |
| 1 (tekil) | "Kendi verim geçerli mi?" — oda poligonu kapalı mı, açıklık host duvardan geniş mi, kolon kesiti katalogda var mı | **ilgili modül** | kısmen var (`validate.py::check_rooms` / `check_walls` / `check_openings`) |
| 2+ (çift) | "İki FARKLI eleman sınıfı aynı yeri mi işgal ediyor?" — tefriş ↔ duvar, tefriş ↔ kapı yayı, kolon ↔ tefriş | **`scripts/collision/`** | YOK |

**Endüstri karşılığı nettir.** BIM'de modelleme aracı kendi disiplininin
tutarlılığını denetler; **disiplinler arası çakışma denetimi ayrı bir
araçtır** — Navisworks *Clash Detective*, Solibri *Model Checker*. Hiçbir BIM
aracı "mimari model mekanik modeli de denetlesin" demez, çünkü o zaman kural N
modüle dağılır ve hiçbiri bütünü göremez. Aynı sebeple burada da tekil
doğrulama modülde, çift doğrulama ayrı motorda kalır.

**Modül bağımsızlığı nasıl korunuyor (kararın kritik noktası):**
`scripts/collision/` **hiçbir çizim modülünü import etmez.** Bağımlılık
TERSİNE çevrilir:

- `collision/` yalnızca **anonim şekil** tanır: `CollisionShape(tag, id,
  polygon)`. Koltuğun ne olduğunu bilmez, yalnızca bir çokgen ve bir etiket
  görür.
- Her çizim modülü **kendi ayak izini** üretir:
  `scripts/<modül>/collision.py::footprints(floor, context) -> list[CollisionShape]`.
  Bir elemanın kapladığı alanı, onu ÇİZEN modül bilir — tefrişin rotasyonunu
  ve katalog ölçüsünü `furniture/`, kapı açılım sektörünü `openings/`, kolon
  kesitini `columns/` bilir. Bu bilgi başka yere kopyalanmaz.
- Böylece "sahiplik belirsizleşir" itirazı ortadan kalkar: **ayak izinin
  sahibi modül, çakışma kuralının sahibi motordur.** İkisi çakışmaz.

Benzetme: bir fizik motoru arabayı ve ağacı tanımaz, yalnızca collider tanır.

**Dosya düzeni:**

```
scripts/collision/
  __init__.py   public API (walls/ ve furniture/ deseni — sadece dışa açılan)
  shapes.py     CollisionShape + dikdörtgen / çokgen / yay-sektörü üreticileri
  matrix.py     CollisionPolicy: (tag_a, tag_b) -> FORBID | WARN | IGNORE + tolerans
  engine.py     kaba faz (AABB) -> ince faz (çokgen kesişim alanı) -> Clash kayıtları
  report.py     ClashReport: önem sırası, metin çıktısı, çıkış kodu
  scene.py      Scene.from_context(context): ayak izi sağlayıcılarını çağırır
  CLAUDE.md
```

`scene.py`, tüm sağlayıcıları bilen TEK dosyadır ve bu liste **açıktır** —
import-time kayıt sihri yoktur, çünkü sessizce kaybolan bir kayıt sessizce
denetlenmeyen bir modül demektir. Yeni modül eklemek = bu listeye bir satır.

**Politika matrisi (varsayılan; `matrix.py`):**

| Çift | Politika | Gerekçe |
| ---- | -------- | ------- |
| tefriş ↔ tefriş | **FORBID** | iki mobilya aynı yerde duramaz |
| tefriş ↔ kolon | **FORBID** | taşıyıcı geçilemez |
| tefriş ↔ kapı açılım sektörü | **FORBID** | kapı açılamaz hale gelir |
| tefriş oda sınırının DIŞINDA | **FORBID** | yerleşim yanlış mahalde |
| tefriş ↔ duvar | **WARN**, tolerans üstünde FORBID | dolap duvara DAYANIR; mm ölçeğinde temas normaldir |
| kolon ↔ duvar | **IGNORE** | kolonun duvar içinde olması TASARIMDIR, hata değil |
| kolon ↔ oda | **IGNORE** | kolon bir odanın içinde durabilir |
| kolon ↔ kolon | **FORBID** | |
| her şey ↔ aks | **IGNORE** | aks bir referans çizgisidir, madde değildir |

`CONTACT_TOLERANCE = 5 mm`: bunun altındaki örtüşme **temas**tır, çakışma
değil. Katalog ölçüsü yuvarlaması ve duvara dayalı yerleşim bu bandın içinde
kalır; tolerans olmadan her normal yerleşim hata üretirdi.

**Nerede çalışır: `validate.py` içinde, ÜRETİMDEN ÖNCE.** Sebep, hata
mesajının hangi dilde olduğudur. Context seviyesinde rapor şunu der:
`K1 katinda f_koltuk3 (koltuk_3lu) w12 duvariyla 0.42 m2 cakisiyor` — bu
doğrudan `context.json`da düzeltilir. Aynı hata DXF seviyesinde
`handle 2F4 ile handle 3A1 kesisiyor` olurdu ve düzeltilemezdi. Kök
`CLAUDE.md` zaten "Doğrulama geçmeden DXF üretilmez" diyor; bloklayıcı kapı
oraya aittir.

**Neden `golden_report.py`ye kural olarak EKLENMEDİ (eski Fikir 2 reddedildi):**
Golden'ın sorusu "çıktı beklenmedik şekilde değişti mi", çakışma denetiminin
sorusu "tasarım doğru mu". Birleştirmenin somut bedeli şudur: birleştirilirse
**bir golden referansı asla kasıtlı çakışma içeremez**, çünkü çalıştığı anda
patlar. Oysa beklenen çıktısı BELİRLİ BİR ÇAKIŞMA LİSTESİ olan bir referans
(`cakisma_negatif` adında), çakışma motorunun kendisini doğrulamanın tek
yoludur — projenin beş semantik kuralı da tam olarak böyle, kasıtlı bozma
testiyle doğrulanmıştı. Ayrı tutulunca bu mümkün olur.

**Uygulama sırası:**

1. `shapes.py` + `engine.py` + negatif testler (elle kurulmuş iki dikdörtgen;
   kesişim alanı elle hesaplanabilir olmalı).
2. `furniture/collision.py` + `columns/collision.py` — en somut fayda burada.
3. `validate.py` entegrasyonu ve politika matrisi; bloklayıcı davranış.
4. `openings/collision.py` — kapı açılım sektörü.
5. `cakisma_negatif` golden referansı (beklenen çıktı = belirli çakışma listesi).
6. `doc_check.py` kuralı (aşağıda).

**`doc_check.py` bağı:** "Yeni bir modül eklendiğinde 'bu modül hangi modülle
çakışabilir?' sorusu açıkça yanıtlanır" kuralı bugün DÜZYAZIDIR, bu yüzden
kaçabilir. DEV-019 uygulandığında şu kontrol eklenir: geometri üreten her
modülün ya `collision.py` dosyası olmalı ya da `collision/scene.py` içindeki
`COLLISION_EXEMPT` sözlüğünde **gerekçesiyle** listelenmiş olmalıdır. rev-11'de
düzyazı kuralın mekanikleştirilmesiyle aynı desen.

- **Açık kararlar (uygulamada netleşecek):** Kapı açılım sektörü kaç doğru
  parçayla yaklaşılacak (deterministiklik için SABİT olmalı, ölçeğe bağlı
  değil)? Duvarın ayak izi rail çokgeni mi yoksa merkez çizgi + kalınlık mı
  olacak? Çakışma yalnızca AYNI kat içinde aranır (şimdilik evet; katlar arası
  düşey hizalama ayrı bir konudur, bkz. `scripts/columns/CLAUDE.md`).

### DEV-020 — Proje ↔ sistem sürüm uyumu

- **Durum:** COMPLETED (rev-12)
- **Sonuç:** `scripts/version.py` kuruldu. Üç mekanizma AMACA GÖRE ayrıldı:
  `meta.schema_version` **kapıdır** (tek semver; MAJOR farkta `validate.py`
  üretimi DURDURUR), modül `CONTRACT_VERSION` **teşhistir** (10 modülün
  hepsinde bildirildi, bloklamaz), `output/provenance.json` **kayıttır** (her
  üretimde yazılır: schema sürümleri + modül sözleşmeleri + git commit +
  zaman damgası). Alan bugün **opsiyoneldir** — yoksa `1.0.0` varsayılır ve
  UYARI basılır; `context.json` ile iki golden referansı alanı taşıyor.
- **Doğrulama:** MAJOR farkta `exit 1` ve net gerekçe; MINOR farkta uyarı +
  `exit 0` (ikisi de çalıştırıldı). `doc_check.py`, `CONTRACT_VERSION` taşıyan
  her modülün `version.py::CONTRACT_MODULES` ile birebir örtüşmesini denetler
  — bayat/eksik kayıt üretimi değil dokümanı bozar, ve bu kasıtlı bozmayla
  sınandı.
- **Görünür provenance:** Kapak paftasının eteğinde artık `URETIM: <tarih
  saat>` (sol) ve `SISTEM: <schema sürümü>` (sağ) yazar — çıktının ne zaman ve
  neyle üretildiği çizimin kendisinden okunur.
- **Kayıt:** `DEVELOPMENT_HISTORY.md` içindeki `HD-007`.
- **Kullanıcı gerekçesi:** Her proje diğerlerinden bağımsızdır ve proje verisi
  (tefriş yerleşimi dahil) kendi dizininde durur. Bir proje eski bir sistem
  sürümüyle üretildikten sonra modüllerde değişiklik yapılırsa, o projenin
  sistemle **entegrasyonunun kopup kopmadığı** analiz edilebilmelidir. Sistem
  olgunlaşınca revizyonlar geriye dönük desteği korur; yalnızca **major**
  güncellemede eski projelerin güncellenmesi gerekir.
- **Mevcut durum:** Sürüm bilgisi HİÇ tutulmuyor. `context.json` hangi sistem
  sürümüyle üretildiğini bilmiyor; `rev_history` yalnızca PROJE revizyonunu
  sayıyor, sistemin sürümünü değil. Bugün tek proje üzerinden ilerlendiği için
  sorun görünmüyor — ikinci proje açıldığında görünür olacak.

#### KARAR (rev-12): ikisi de — ama aynı iş için değil

Kullanıcı "sanırım modül bazlı daha iyi olabilir" dedi. Sezgi doğru, ancak
modül bazlı sürüm **teşhis** için doğrudur, **kapı** için değildir. Üç gerekçe:

**1) Sürümlenecek şey KOD DEĞİL, SÖZLEŞMEDİR.** rev-11'de `furniture/` tek
dosyadan beş dosyaya bölündü: kod tamamen değişti, etkilenen proje SIFIR. Buna
karşılık `floors[].furniture[].position` alanı `origin` olarak yeniden
adlandırılsa tek satır kod değişir ve HER proje kırılır. Modüle `__version__`
koyup her refactor'da artırmak, hiçbir projeyi ilgilendirmeyen bir sayıyı
büyütür — ve kısa sürede gürültüye dönüşen bir sayıya kimse bakmaz.

**2) Modül bazlı semver'in ait olduğu yer bir PAKET DEPOSUDUR** (npm, pip):
orada her paketin bağımsız bir yayın temposu vardır, bu yüzden uyum matrisi
gerekir. Burada modüller bağımsız yayınlanmaz — hepsi tek repoda, tek
commit'te, her zaman BİRLİKTE gider. Bağımsız tempo yokken N×N uyum matrisi,
arkasında gerçek bir karar olmayan bir bakım yüküdür.

**3) İstenen şey aslında bir TEŞHİStir:** "eski proje koptu mu, koptuysa
neyden?". Bu soruyu **provenance** (ne kullanıldı, kaydet) yanıtlar;
**versioning** (neyle uyumluyum, beyan et) değil. İkisi farklı mekanizmadır ve
karıştırılması bu konudaki asıl tuzaktır.

Bu yüzden ayrım **amaca göre** yapılır:

| Mekanizma | Rolü | Bloklar mı | Ne zaman artar |
| --------- | ---- | ---------- | -------------- |
| `meta.schema_version` — TEK, semver | **kapı** | MAJOR farkta EVET | `context.json`ın şekli geriye uyumsuz değiştiğinde |
| modül `CONTRACT_VERSION` | **teşhis** | hayır | o modülün context'ten OKUDUĞU alanlar değiştiğinde |
| `provenance` bloğu (git commit + modül sözleşme sürümleri + zaman damgası) | **kayıt** | hayır | her üretimde yazılır |

Kapı bağımsız bir sayı DEĞİLDİR: `SCHEMA_VERSION`ın MAJOR'ı, herhangi bir
modül sözleşmesi geriye uyumsuz değiştiğinde artar — yani modül sözleşmelerinin
türevidir. Böylece Fikir 1'in tek ve temiz karar noktası ile Fikir 2'nin
"hangi modül sorumlu" cevabı birlikte elde edilir, Fikir 2'nin uyum matrisi
maliyeti ödenmeden.

**Migrasyon asla otomatik değildir.** Major kırılımda eski proje sessizce
dönüştürülmez. Sebep kök `CLAUDE.md`nin kendi kuralıdır: proje verisi
uydurulmaz ve her değişiklik `requests.jsonl` + `rev_history` üzerinden geçer.
Otomatik migrasyon bu zinciri kırar ve provenance yalan söylemeye başlar.
Doğru yol: `scripts/migrate.py --from 1 --to 2 --dry-run` bir RAPOR üretir,
kullanıcı onaylar, dönüşüm normal bir revizyon olarak işlenir.

**Kademeli giriş (mevcut projeleri kırmadan):** `meta.schema_version` önce
**opsiyonel** eklenir; yoksa `1.0.0` varsayılır ve UYARI verilir. Mevcut
`context.json` ile `golden/` altındaki referanslar bir revizyonda alanla
doldurulur. ANCAK ondan sonra schema'da `required` yapılır — bugün doğrudan
required yapmak her context'i (iki golden referansı dahil) anında geçersiz
kılardı.

**`doc_check.py` bağı:** `scripts/version.py::SCHEMA_VERSION` ile
`schema/design.schema.json`da bildirilen sürüm birebir eşleşmeli;
`CONTRACT_VERSION` taşıyan her modül mimari tablosunda anılmalıdır. Yine
düzyazı yerine mekanik kontrol.

- **Açık kararlar:** `provenance` bloğu `context.json` içinde mi, yoksa
  `output/` yanında ayrı bir dosyada mı dursun (context şişer, ama "proje
  verisi proje dizininde" ilkesi context'i işaret eder)?
  `PROVENANCE_TEMPLATE.json` bu şemaya çekilecek mi? Modül sözleşme sürümü
  modül başına tek sayı mı olacak (şimdilik evet; okunan her alan için ayrı
  sürüm erken optimizasyon görünüyor)?

### DEV-015 — `axis/` — aks sistemi genişletmesi

- **Durum:** COMPLETED (rev-13)
- **Sonuç:**
  - *Fikir 2 — ara ve kısmi aks:* `Axis` artık bir `dict` değil tipli bir
    nesnedir ve `extent` taşır. Kısmi bir aks yalnızca bildirilen aralıkta
    uzanır, uçlarına kendi baloncukları gelir ve tam uzama yerine küçük bir
    `partial_extension` kadar taşar. **Ulaşmadığı kenarın ölçü zincirine
    GİRMEZ** — aksi halde zincir, orada olmayan bir aksı ölçüyormuş gibi
    görünürdü.
  - *Fikir 1 — kolon rasterine göre aks:* `AxisCoverageReport` **salt
    okunurdur**; aks'sız kalan kolon hizalarını bildirir, context'e aks
    YAZMAZ (türetilmiş geometriyi context'e yazma yasağı). `columns::
    on_axis_report` bunun tersidir; ikisi birlikte kolon↔aks çapraz kontrolünü
    tamamlar.
- **Açık karar kapandı — ara aks `1'` yazılır, `1A` YAZILMAZ.** Gerekçe tercih
  değil ÇATIŞMA: yatay aks ailesi zaten `A`, `B`, `C`'dir, dolayısıyla `1A`
  "1 ve A akslarının kesişimi" gibi okunur ve `on_axis_report`un ürettiği
  kolon adıyla (`B2`) aynı dizede çarpışır. Kural `scripts/axis/naming.py`
  içinde yazılıp `validate.py`ye bağlandı: düşey akslar numerik, yatay akslar
  alfabetik, ikisi de tek kesme işaretiyle ara aks olabilir; aynı etiketin iki
  kez kullanılması da hatadır.
- **Modül bölündü** (kullanıcı ilkesi: tek `__init__.py`de her şey olmaz):
  `standard` / `axis` / `naming` / `grid` / `report`.
- **Doğrulama:** `python scripts/axis/selftest.py` — kısmi aks uzanımı, ölçü
  zinciri üyeliği, etiket kuralının beş negatif vakası ve kapsama raporunun
  yanlış-pozitif testi.
- **Kayıt:** `DEVELOPMENT_HISTORY.md` içindeki `HD-008`.

<details><summary>Uygulama oncesi plan notu (tarihsel)</summary>

- **Mevcut durum:** Tamamlandı: kesikli AKS layer'ı, sabit RGB, baloncuk
  teğetliği, cephelere `axis_source` ile izdüşüm, gerçek DXF ölçü zincirleri.
  Aks konumları context'ten geliyor ve tüm katlarda sabit.
- **Fikir 1 — Kolon rasterine göre otomatik aks:** Kök kurallar, kolon
  yerleşimi projeye girdiğinde aks sayısı/sıklığının kolon rasterine göre
  yeniden belirlenmesini öngörüyor. `DEV-010` ile birlikte ele alınmalı.
- **Fikir 2 — Ara aks ve kısmi aks:** `1'`, `2'` gibi ara akslar ve yalnızca
  belirli bir bölgede uzanan kısmi akslar. Bugün her aks tüm yapı boyunca
  uzanıyor.
- **Açık kararlar:** Ara aks etiketleme kuralı (`1'` mi `1A` mı)?

</details>

### DEV-016 — `openings/` — açıklık varyantları

- **Durum:** COMPLETED (rev-13)
- **Sonuç (her iki fikir de uygulandı):**
  - *Fikir 1 — varyant sembolleri:* `single`, `double`, `sliding`, `folding`.
    Seçim VERİ ODAKLIDIR (`symbols.DOOR_SYMBOLS`); yeni varyant için alt sınıf
    gerekmez, sözlüğe bir fonksiyon eklenir.
  - *Fikir 2 — swing/menteşe yönü:* `swing` (menteşe duvarın başında mı
    sonunda mı) ve `host_side` (kanat hangi tarafa açılıyor) schema'ya
    eklendi. **Üç alanın da varsayılanı rev-12 davranışıdır**, yani mevcut
    projeler hiçbir şey değiştirmeden aynı çizimi üretir.
- **Açık karar kapandı — `position_from_start` KORUNDU.** Alan, duvar
  başlangıcından açıklığın **merkezine** olan mesafedir. Kenardan ölçmeye
  çevirmek geriye uyumsuz bir schema kırılımı (MAJOR) olurdu ve karşılığında
  hiçbir yetenek kazandırmazdı.
- **İki gerçek hata bulundu ve düzeltildi:**
  1. **Açılım yayı 270° olabiliyordu.** Açılar `min(along, perp)` ..
     `max(along, perp)` olarak veriliyordu; duvar −X yönünde çizilmişse
     (`along = 180`, `perp = −90`) bu 270°'lik bir yay üretirdi. Mevcut
     projede her duvar +X/+Y yönündeydi, bu yüzden hata hiç görünmedi — ama
     `golden/minimal` referansında ucu ters verilmiş iki duvar ZATEN VARDI ve
     oraya bir kapı konduğu anda ortaya çıkacaktı. Yön artık çapraz çarpımla
     belirleniyor; yay her zaman 90°.
  2. **Çakışma sektörü çizilen yaydan yarım genişlik kayıktı.**
     `openings/collision.py`, `position_from_start`i açıklığın BAŞLANGICI
     sanıyordu; oysa MERKEZİDİR. 900'lük bir kapıda menteşe 450 mm yanlış
     yerdeydi. Artık boşluk aralığı çizimle AYNI fonksiyondan
     (`walls.gaps_for_wall`) alınıyor.
- **Tek sahip:** `openings/geometry.py::swing_geometry` açılım yayının tek
  kaynağıdır; hem çizim (`symbols.py`) hem çakışma denetimi (`collision.py`)
  buradan okur. İki yerde ayrı hesaplanması yukarıdaki 2 numaralı hatayı
  üretmişti.
- **Bağlı değişiklikler:** Çakışma matrisinde **kapı ↔ kapı artık HATADIR**
  (rev-12'de yön bilinmediği için muaf bırakılmıştı); sürme kapı açılım alanı
  üretmez. Golden kuralı `rule_opening_symbols` varyant farkındası oldu ve
  beklenen yay sayısını `openings.ARCS_PER_VARIANT` tablosundan okuyor —
  kural ile çizim aynı kaynağa bakıyor.
- **Doğrulama:** `python scripts/openings/selftest.py` — beş duvar yönü × iki
  swing × iki host_side için yayın **her zaman 90°** olduğu, varyant başına
  çizilen çizgi/yay sayısı, geçersiz değerlerin üretimi durdurması ve boşluk
  aralığı sözleşmesinin regresyon testi.
- **Kayıt:** `DEVELOPMENT_HISTORY.md` içindeki `HD-008`.

<details><summary>Uygulama oncesi plan notu (tarihsel)</summary>

- **Mevcut durum:** `Opening`/`Door`/`Window` tipli, host-wall ve genişlik
  doğrulaması aktif, `OpeningSymbolStyle` Protocol'ü hazır. Ancak pratikte tek
  stil var (`DefaultPlanOpeningStyle`) ve schema'da varyant/swing alanı YOK —
  açıklıklar tek kanat, tek yönlü çiziliyor.
- **Fikir 1 — Varyant sembolleri:** Çift kanat, sürme, katlanır ve döner kapı
  sembolleri. Protocol zaten var, yeni stil eklemek mevcut mimariyle uyumlu.
- **Fikir 2 — Swing/menteşe yönü:** Kapının hangi tarafa ve hangi yöne
  açıldığını veriden almak. Bugün yön geometriden sabit türetiliyor; gerçek
  projede kaçış yönü ve mobilya çakışması için kritik (`DEV-009` ile ilişkili).
- **Açık kararlar:** `variant` ve `swing` schema alanları ne zaman eklenecek?
  Konum duvar başlangıcına göre mi, merkeze göre mi tanımlanacak?

</details>

### DEV-017 — `dimensions/` — ölçülendirme genişletmesi

- **Durum:** COMPLETED (rev-13)
- **Sonuç (her iki fikir de uygulandı):**
  - *Fikir 1 — türetilen ölçü zinciri:* `dimensions/derive.py::FloorOrdinates`
    kat geometrisinden üç kademede ordinat üretir — `aciklik` (cephedeki
    kapı/pencere kenarları), `mahal` (dik duvarların **yüzleri** → net mahal +
    duvar kalınlığı), `toplam` (dıştan dışa). Üçü de aynı ordinatlarda başlayıp
    biter; mimari bir ölçü yığınının görünümü budur.
  - *Fikir 2 — kademelendirme:* `layout.py::ChainStack` aynı kenardaki
    zincirleri deterministik olarak basamaklandırır ve
    `ChainLayout.verify_no_overlap` **aynı baseline'a oturan iki zinciri artık
    HATA sayar**. Önceden `ChainLayout` yalnızca sınır kontrolü yapıyordu;
    üst üste binen iki zincir sessizce okunamaz bir çizim üretirdi.
- **Açık karar kapandı — ölçü TÜRETİLİR, elle bildirilmez.** Bir ölçü sayısı
  tasarım verisi değildir, geometrinin ölçüsüdür. Duvar koordinatı zaten
  context'tedir; ölçüyü ayrıca yazmak aynı bilgiyi iki yerde tutmak olurdu ve
  kaçınılmaz olarak ayrışırdı (duvar taşınır, ölçü metni eski kalır — bu,
  projenin "bayat satır" sorununun geometri hâli). Türetme "ölçü uydurulmaz"
  yasağını DELMEZ: sayı uydurulmuyor, ölçülüyor. Buna karşılık **hangi
  kenarın hangi kademede ölçüleneceği bir SUNUM kararıdır** ve
  `meta.dimensions` ile gelir (varsayılan KAPALI; bu projede AÇIK).
- **Tolerans alan değil DERİNLİK:** 2100 mm'lik bir koltuk duvara 5 mm girse
  kesişim alanı 10500 mm² olur — alan eşiği eleman boyuyla ölçeklendiği için
  anlamsızdır. Aynı mantık ölçüde de geçerli: 1 mm içindeki iki ordinat
  birleştirilir (`merge_ordinates`), aksi halde "0" metinli sıfır uzunluklu
  ölçüler üretilirdi.
- **Çapraz nokta (yeni):** Ölçü yığını ile aks baloncukları AYNI kenarı
  paylaşır. `DimensionSettings.axis_dimension_offset` ve
  `required_axis_extension` aks standardını besler; iki modül birbirini
  **import etmez**, baloncuk yarıçapı parametre olarak verilir. Aks ölçü
  zinciri artık yığının **DIŞINDA** durur (mimari sıra: içeride en ayrıntılı,
  dışarıda en kaba).
- **Ölçülerek yapılan değişiklik:** `pafta::CONTENT_PADDING` 3200 → 4000.
  İçerik yatayda gerçekten genişledi ve 3200 ile üretim `PaftaOverflowError`
  ile DURDU — yani artış tahminle değil, taşma korumasının yakaladığı gerçek
  bir ölçüyle yapıldı. Pafta yüksekliği 67.0 → 70.2 cm, 90'lık rulonun 88 cm
  netine sığıyor.
- **Doğrulama:** `python scripts/dimensions/selftest.py` — ordinatlar elle
  hesaplanabilir bir kat üzerinde birebir sınanır (dış yüz −100/6100, net
  mahal 2950/3050, kapı kenarları 1000/1900); kademelendirme ve **aynı
  baseline yasağı** negatif testle doğrulanır.
- **Kayıt:** `DEVELOPMENT_HISTORY.md` içindeki `HD-008`.

<details><summary>Uygulama oncesi plan notu (tarihsel)</summary>

- **Mevcut durum:** `LinearDim`, `DimensionChain`, `ChainLayout` hazır ve
  `AxisGrid` bunları kullanarak gerçek DXF dimension üretiyor. Ölçü metni tam
  sayı cm. Bugün ölçü üreten TEK tüketici aks modülü.
- **Fikir 1 — Oda içi/net ölçü zinciri:** Duvar yüzünden duvar yüzüne net oda
  ölçüleri ve kapı/pencere konum ölçüleri. Uygulama projesinde (1:50) asıl
  beklenen ölçülendirme budur; altyapı hazır, eksik olan tüketici.
- **Fikir 2 — Zincir çakışma çözümü:** Birden fazla zincir aynı kenarda
  olduğunda otomatik kademelendirme (offset artırma). Bugün `ChainLayout`
  yalnızca bounds kontrolü yapıyor; çakışan iki zincir üst üste binebilir.
- **Açık kararlar:** Ölçü zinciri context'ten mi bildirilecek, yoksa duvar
  geometrisinden mi türetilecek? Türetilirse hangi kenarlar ölçülendirilecek?

</details>

## Modül kataloğu — her modülün plan maddesi

> **Bu bir durum kovası DEĞİLDİR.** Buradaki maddeler modül modül
> düzenlenmiştir; her maddenin durumu kendi `Durum:` satırındadır ve
> COMPLETED/BLOCKED/PLANNED olabilir. Tek bakışta durum için yukarıdaki
> "Durum özeti" tablosuna bakınız.


Her modülün kendi plan maddesi vardır. Her maddede **iki fikir** önerilir; bunlar
uygulama izni DEĞİLDİR — sistem mimarı (kullanıcı) bir fikri seçer, kendi
yönlendirmesini ekler ve görevi açıkça başlatır. Fikirler ilgili
`scripts/<modül>/CLAUDE.md` sözleşmesinin mevcut durumundan türetilmiştir.

**Şartname ile fikir farkı:** Bir maddede "Şartname" başlığı varsa, o kısım
kullanıcı tarafından KESİN olarak verilmiştir ve fikir gibi değerlendirilmez.

### DEV-007 — `pafta/` — kapak verisi ve pafta altyapısı

- **Durum:** BLOCKED — çizim tarafında yapılacak iş kalmadı, yalnızca
  kullanıcıdan gelecek resmi veri bekleniyor.
- **rev-9 değerlendirmesi:** Kullanıcı "tekrar bir çalışma gerekiyorsa
  uygula" dedi; kod tarafı gözden geçirildi ve **ek iş gerekmedi**. Proje
  fontu Arial Narrow'a geçtiğinde kapak da otomatik olarak yeni fontu aldı
  (`Standard` text style üzerinden) ve pafta taşma kontrolünden sorunsuz
  geçti. Aşağıdaki iki fikir kullanıcı tarafından seçilmedi, bekliyor.
- **Mevcut durum:** Tip-A kapak çizimi/yerleşimi tamamlandı (`CoverBlock`,
  bkz. `HD-004`). Eksik olan yalnızca resmi veridir. Ayrıca `PaperSizePlanner`
  90'lık ruloya sığmayan bir proje için "pafta bölme + keyplan" gerektiğini
  raporluyor ama bu henüz uygulanmadı.
- **Fikir 1 — Pafta bölme + keyplan:** En büyük rulo yetmediğinde mevzuatın
  tek kabul ettiği çözüm. Yapı aks/dilatasyon hatlarından parçalara bölünür ve
  her parçaya, binanın şematik konturunu tarayarak vurgulayan 1:500/1:1000
  ölçekli bir keyplan eklenir. `PaperSizePlanner.select(...)` zaten
  `fits=False` döndürdüğü için tetikleme noktası hazır.
- **Fikir 2 — Uniform sheet template:** Paftayı içeriği saran serbest bir tuval
  yerine gerçek standart kağıt boyutuna oturtmak. Bu yapılırsa antetin
  `MAX_TITLE_BOX_WIDTH_MM` / `MAX_TITLE_BOX_HEIGHT_MM` kırpması kalkar ve
  DIN/ISO 5457 Tip-B ölçüsü tam uygulanabilir; sayfa marjları (sol 20mm,
  diğer 10mm) da gerçekten çizilebilir.
- **Açık kararlar:** `meta.cover.architect_name`, `meta.cover.date`, ayrılmış
  iki imza alanının unvanı, ruhsat/onay alanı gerekip gerekmediği. Kapak
  **tasarımı** için kullanıcı ayrı bir talep paylaşacak; o talepte geometri
  (A4, sağ-alt sabitleme, eşit offset, antetsiz pafta) değişmemelidir.

### DEV-008 — `rooms/` — 3 satırlı mahal etiketi (`RoomLabeler`)

- **Durum:** COMPLETED (rev-9)
- **Sonuç:** Şartname birebir uygulandı. `RoomLabeler` artık 3 satır üretiyor
  (mahal adı BLOK / kat kodu-mahal no / alan), sığdırma hem **genişliğe hem
  yüksekliğe** bakıyor, kat kodu `floors[].code`'dan ve mahal no
  `rooms[].no`'dan geliyor (türetilmiyor). Proje fontu Arial Narrow oldu;
  bunun sahibi yeni `scripts/typography/` modülüdür ve mahal etiketi için
  `meta.fonts.room_label` ile ayrı font seçilebilir.
- **Doğrulama:** 125/125 mahal etiketinin gerçek font metrikleriyle ölçülen
  bounding box'ı kendi oda poligonunun içinde kaldı; mahal no ve kat kodu
  benzersizlik kontrolleri `validate.py`ye eklendi ve negatif testle
  doğrulandı. Kayıt: `DEVELOPMENT_HISTORY.md` içindeki `HD-005`.
- **Uygulanmayan fikirler:** Aşağıdaki iki fikir kullanıcı tarafından
  seçilmedi; şartname doğrudan uygulandı. `RoomLabelStyle` Protocol'ü ve
  leader'lı yerleşim hâlâ açık birer geliştirme olarak durur.
- **İlgili:** Etiketin DXF `BLOCK` + `ATTRIB` olarak üretilmesi `DEV-018`de
  (rev-14) tamamlandı.
- **Önceki durum (kayıt):** `RoomLabeler.draw` tek satır, sabit biçim
  `"{ad} ({alan} m2)"` üretiyordu; yalnızca oda genişliğine bakıyordu.

**Şartname (kullanıcı tarafından verildi — varsayılan format):**

Etiket **3 satırdır**:

```
SALON        <- 1. satir: mahal adi, BLOK
ZK-04        <- 2. satir: kat kodu + mahal no
28.9 m2      <- 3. satir: alan
```

- Yazı tipi **Arial Narrow**.
- Mahal adı **blok** olarak işlenir.
- Mahal kodu, katı ifade eden bir önek taşır. Kullanıcının verdiği eşleşme:
  `B1` = 1. bodrum, `B2` = 2. bodrum, `ZK` = zemin kat, `K1`/`K2`/`K3`... =
  normal katlar.

- **Fikir 1 — `RoomLabelStyle` Protocol + hazır format seti:** Biçimi
  `openings::OpeningSymbolStyle` deseninde enjekte edilebilir yap; şartnamedeki
  3 satırlı biçim `DefaultRoomLabelStyle` olur, yanına dar odalar için tek
  satırlık kompakt bir biçim ve sunum çizimleri için mahal no'suz bir biçim
  konur. Hangi stilin kullanılacağı pafta/proje seviyesinde seçilir.
- **Fikir 2 — Yerleşim zekası:** Etiketi sadece küçültmek yerine, oda
  poligonunun içine sığan en geniş eksen-hizalı dikdörtgeni bulup bloğu oraya
  oturtmak; sığmıyorsa etiketi odanın dışına alıp **leader (kılavuz çizgi)**
  ile odaya bağlamak. Bu, içbükey (L şeklinde) odalarda etiketin dışarı
  düşmesi sorununu da çözer.
- **Açık kararlar:**
  - **Çatı katının kodu ne olacak?** Kullanıcı `B1/B2/ZK/K1..` verdi, çatı
    katı için kod belirtilmedi — uydurulmayacak.
  - **Mahal no nereden gelecek?** İki seçenek: (a) `floors[].rooms[].no`
    olarak schema'ya eklenip veriden gelir, (b) oda sırasından deterministik
    türetilir. Türetme, oda sırası değişince numaraların kaymasına yol açar.
  - **Kat kodu nereden gelecek?** `floors[].code` schema alanı mı, yoksa
    `floors[].label`'dan çıkarım mı? Etiketten çıkarım kırılgandır.
  - **Arial Narrow kapsamı:** yalnızca mahal etiketi mi, yoksa projedeki tüm
    metinler mi? Bu, `pafta.DEFAULT_FONT = "txt"` sabitini ve dolayısıyla TÜM
    `fit_text_height` ölçümlerini etkiler (antet, cephe etiketleri, aks).
    Ayrıca Arial Narrow bir TTF'tir; DXF text style tanımı ve alıcı
    bilgisayarda fontun bulunması ayrıca değerlendirilmeli.

### DEV-009 — `furniture/` — tefriş modülü

- **Durum:** COMPLETED (rev-10)
- **Sonuç:** `scripts/furniture/` kuruldu. 22 tipli konut tefriş kataloğu
  (koltuk 3'lü/2'li, berjer, sehpa, TV ünitesi, yemek masası 4/6, sandalye,
  tek/çift yatak, gardırop, komodin, mutfak tezgahı, ocak, evye, buzdolabı,
  bulaşık mak., lavabo, klozet, duş teknesi, küvet, çamaşır mak.). Tefriş
  **her zaman DXF `BLOCK`** olarak çizilir (tip başına bir tanım, yerleşim
  başına bir `INSERT`). Beş işlevsel grup ve her birine **kahverengi
  ailesinden düşük kontrastlı** bir layer rengi. `FurnitureSchedule`
  salt-okunur liste üretir.
- **Kapı kararı (kullanıcı sordu):** Kapı **tefriş değildir, duvar
  açıklığıdır** — `openings/` + `walls/` sahiplenir, ki bu projede zaten
  öyledir. Gerekçe endüstri standardıdır: IFC'de `IfcDoor` bir
  `IfcBuildingElement`tir (`IfcFurnishingElement` değil), AIA/NCS layer
  standardında kapı `A-DOOR`, tefriş `A-FURN`; ayrıca kapı geometrisi host
  duvara bağımlıdır. Ayrıntı: `scripts/furniture/CLAUDE.md` "Kapı kimin?".
- **Kayıt:** `DEVELOPMENT_HISTORY.md` içindeki `HD-006`.
- **Uygulanmayan:** `counters[]` (mutfak tezgahı) hâlâ `generate_dxf.py`
  içinde ad-hoc çiziliyor; bu modüle devri ayrı bir karardır. Tefriş/duvar/
  kapı-açılımı çakışma kontrolü YOK.
- **Fikir 1 — Parametrik tefriş kataloğu:** `FurnitureCatalog`, tip adından
  ölçülü bir çizime çözen bir sözlük olur (`WallCatalog` deseni). Context'te
  yalnızca **tip + konum + rotasyon** tutulur, geometri koddan gelir. Aday
  set: yatak (90/140/160), koltuk takımı, yemek masası (4/6 kişilik), mutfak
  tezgahı + ocak/evye, gardırop, lavabo/klozet/duş-küvet, araç (otopark).
  Böylece context şişmez ve ölçüler tek yerden yönetilir.
- **Fikir 2 — Oda tipine göre tefriş şablonu:** `name`/oda tipi bilinen bir
  mahale (örn. "Yatak Odası") şablon bir yerleşim önerilir; modül yalnızca
  **öneri** üretir, `RoomPolygonScanner` gibi context'e otomatik yazmaz.
  Validator sığma ve duvar/kapı çakışması kontrolü yapar; yerleşim kullanıcı
  onayından sonra context'e girer.
- **Açık kararlar:** Katalog ölçüleri hangi kaynaktan gelecek (ofis
  standardı / yönetmelik)? Kapı açılım alanıyla çakışma bloklayıcı hata mı,
  uyarı mı?
- **İlgili:** Tefrişin DXF `BLOCK` olarak tanımlanması bu görevde (`DEV-009`)
  zaten uygulandı; `DEV-018` (rev-14) bunu ÖLÇEREK doğruladı ve asıl eksiğin
  mahal etiketi olduğunu ortaya çıkardı.

### DEV-010 — `columns/` — kolon modülü

- **Durum:** COMPLETED (rev-10)
- **Sonuç:** `scripts/columns/` kuruldu. Kolonlar **taralıdır**; tarama
  deseni/ölçeği dinamiktir (`meta.column_hatch`) ve varsayılanı kullanıcının
  verdiği değerlerdir: **`ANSI33`, ölçek `3.0`**. Kesit kataloğu
  (`S30x60`…`D50`) veya doğrudan `width`/`depth`. Kontur `KOLON`, tarama
  `KOLON-TARAMA` layer'ında (baskı ağırlıkları bağımsız ayarlanabilsin diye).
  Kolonlar tefrişten ÖNCE çizilir.
- **İsimlendirme (kullanıcı şimdilik istemedi):** `Column.name` alanı ve
  `ColumnLabelStyle` hazır, varsayılan **KAPALI**. `meta.column_label.enabled`
  ile **kod değişikliği olmadan** açılır (test edildi). Ayrıca
  `ColumnGrid.on_axis_report(...)` her kolonun hangi aks kesişimine oturduğunu
  (örn. `A1`) salt-okunur raporlar — kullanıcının tercih ettiği "aks
  kesişimiyle ifade etme" yaklaşımının veri karşılığı.
- **Kayıt:** `DEVELOPMENT_HISTORY.md` içindeki `HD-006`.
- **Uygulanmayan:** Katlar arası düşey hizalama ve kolon/duvar-tefriş çakışma
  kontrolü YOK; kesit küçültme otomatik değildir.
- **Fikir 1 — Aks kesişimine parametrik kolon:** `ColumnSectionCatalog` ile
  kare/dikdörtgen/dairesel kesitler; `ColumnGrid.from_axes(...)` bildirilen
  aks kesişimlerine kolon oturtur. Üst katlara çıkıldıkça kesit küçültme
  (örn. 60x60 → 50x50) **ancak açıkça bildirilirse** uygulanır, otomatik
  varsayılmaz.
- **Fikir 2 — Kolon aplikasyon/pozisyon listesi:** Kolonlara aks tabanlı ad
  (`S1`, `S2`...) verip her kolonun aks kesişimi, kesiti ve kotunu listeleyen
  bir tablo üretmek. `OpeningSchedule` deseninde salt-okunur veri; çizimi
  `legend/` üstlenir.
- **Açık kararlar:** Kolon verisi context'te hangi yolda yaşayacak? Aks dışı
  kolona izin var mı? Katlar arası düşey hizalama zorunlu mu?

### DEV-011 — `elevations/` — cephe modülü

- **Durum:** COMPLETED (rev-14)
- **Sonuç:**
  - *Fikir 1 — below-ground linetype (SEÇİLDİ):* `below_ground: true`
    seviyelerin ana hattı (ve içindeki pencere/kapı varsa onlar da) artık
    gerçekten `DASHED` linetype ile çizilir. Önceden sadece ETİKETLE ayırt
    ediliyordu; DXF'te çizgi türü diğer seviyelerle AYNIYDI. `preview.py`
    zaten `linestyle="--"` ile bunu TAKLİT EDİYORDU — gerçek DXF çıkışında
    yoktu, bu asimetri kapandı.
  - *Fikir 2 — plandan açıklık türetme (uygulanmadı):* açık karar olarak
    duruyor, bkz. `scripts/elevations/CLAUDE.md` "Bilinen sınırlamalar".
- **Modül izole edildi:** `generate_dxf.py` içine gömülü `draw_elevation`/
  `elevation_vertical_extent` `scripts/elevations/` modülüne taşındı
  (`ElevationSheet`, `LevelStack`, `FacadeOpeningPlacer`, `Level`) — diğer
  tüm modüllerle aynı "her çizim konusu kendi modülü" deseni. `preview.py`
  artık cursor/extent matematiğini bu modülden import eder (önceden kendi
  KOPYASINI tutuyordu ve `machine_room` protrüzyonunu pafta Y-aralığı
  hesabına KATMIYORDU — bu tutarsızlık da bu geçişte kapandı).
- **Doğrulama:** `python scripts/elevations/selftest.py` — elle hesaplanabilir
  bir istifte cursor birikimi, `extent()`in `machine_room` protrüzyonunu
  kapsadığı ve zemin-altı seviylerin (SADECE onların) `DASHED` aldığı
  yanlış-pozitif testi.
- **Kayıt:** `DEVELOPMENT_HISTORY.md` içindeki `HD-009`.

### DEV-012 — `legend/` — lejant ve cetveller

- **Durum:** COMPLETED (rev-14)
- **Sonuç:**
  - *Fikir 1 — kapı/pencere cetveli (SEÇİLDİ):* `OpeningLegend.rows` zaten
    üretilen `OpeningSchedule` satırlarını proje çapında (tip, varyant,
    genişlik) ile GRUPLAYIP `LegendRenderer.draw` ile gerçek bir MARKA/TİP/
    VARYANT/GENİŞLİK/ADET cetveli çizer (145 açıklık → 10 grup, ana proje
    üzerinde ölçülerek doğrulandı).
  - *Fikir 2 — layer/sembol lejantı (uygulanmadı):* açık fikir olarak
    duruyor, bkz. `scripts/legend/CLAUDE.md`.
- **Açık karar kapandı — cetvel NEREYE çizilir:** kapak paftasının kapak
  bloğunun ÜSTÜNDE kalan, HER ZAMAN boş kalan alana (kök `CLAUDE.md`:
  "kapak bloğu paftanın ALTINA oturur, üstte kalan bölüm BOŞTUR"). Ayrı bir
  pafta açılmadı — ortak Y-aralığı hesabına yeni bir katılımcı eklemek
  `CONTENT_PADDING` gibi başka sabitleri gereksiz yere tetikleyecekti.
- **Pencere satırında `VARYANT` sütunu `-`dir** — `variant` alanı şemada
  pencerede de var ama `openings/style.py` bunu SADECE kapıda kullanır;
  pencerede "TEK KANAT" yazmak var olmayan bir ayrımı uydururdu.
- **Doğrulama:** ayrı bir `selftest.py` yok; `--golden-set`/`--rules` dolaylı
  doğrular (bkz. `scripts/legend/CLAUDE.md` "Doğrulama").
- **Kayıt:** `DEVELOPMENT_HISTORY.md` içindeki `HD-009`.

### DEV-013 — `importer/` — mevcut çizimden veri okuma

- **Durum:** COMPLETED (rev-15)
- **İsim notu:** `import/` olarak planlanmıştı; `import` bir Python anahtar
  kelimesidir ve geçerli bir paket adı OLAMAZ — `fixture` → `golden`
  (rev-11) ile AYNI kategoride bir düzeltmeyle `importer/`e taşındı.
- **Sonuç:**
  - *Fikir 1 — `DxfWallScanner` salt-okunur rapor (SEÇİLDİ):* mevcut bir
    DXF'ten `LINE` çiftlerini tarar, paralellik + kalınlık aralığı +
    örtüşme oranı KOŞULLARINI geçen çiftleri confidence skoruyla (elle
    hesaplanabilir formül) duvar ADAYI olarak raporlar. Çıktı `walls.scan::
    RoomPolygonScanner.suggest_wall_dicts` İLE AYNI desen: salt-okunur,
    context'e YAZMAZ; `WallCandidate.as_wall_dict()` onaylandıktan SONRA
    normal talep akışıyla eklenir.
  - *Fikir 2 — PDF/görüntü altlık (uygulanmadı):* açık fikir olarak duruyor.
- **Açık kararlar kapandı:** kaynak format SADECE DXF; entity kapsamı SADECE
  `LINE` (bkz. "Bilinen sınırlamalar"); onaylı patch formatı = AYRI bir
  `ImportPatch` sınıfı DEĞİL, `WallCandidate.as_wall_dict()`in ürettiği
  şema-uyumlu sözlük (insan/agent inceler, otomatik birleştirme YOK).
- **Yan kazanç:** `RoomPolygonScanner.suggest_wall_dicts` ÇOK ÖNCEDEN
  (rev-1'den beri) çıktısına `"kind"` alanı koyuyordu, ama şema bu alanı
  `DEV-013`e kadar TANIMIYORDU — o taslak aracın çıktısı context.json'a
  hiçbir zaman gerçekten EKLENEMEZDİ. `DEV-014`nin şema düzeltmesi bunu da
  kapattı.
- **Doğrulama:** `python scripts/importer/selftest.py`.
- **Kayıt:** `DEVELOPMENT_HISTORY.md` içindeki `HD-010`.

### DEV-014 — `walls/` — duvar çizim standardı genişletmesi

- **Durum:** COMPLETED (rev-15)
- **Sonuç:**
  - *Fikir 1 — `RailDrawingStandard` (SEÇİLDİ):* `scripts/walls/standard.py`.
    `DefaultRailStandard` bugüne kadarki TEK yöntemi (düz `LINE`, `kind`den
    BAĞIMSIZ) korur; `CatalogRailStandard` (yeni sistem varsayılanı)
    `tugla_bolme` için `ANSI31` `HATCH`, `cam_duvar` için `CAM` linetype
    ekler, başka/eksik `kind` için `DefaultRailStandard`e düşer.
  - *Fikir 2 — Kataloğu context'ten sürmek (uygulanmadı):* açık fikir
    olarak duruyor.
- **Gerçek boşluk bulundu ve kapatıldı (bu maddede öngörülmemiş):** kod
  (`Wall.from_context`, `WallCatalog.resolve`, `WallCatalog` içindeki
  `tugla_bolme`/`cam_duvar` girdileri) `kind`i HER ZAMAN destekliyordu ama
  `schema/design.schema.json`nin `additionalProperties: false` olan `wall`
  tanımında `kind` YOKTU — hiçbir context.json bunu kullanamazdı. Şemaya
  eklendi; `validate.py::check_walls` artık bilinmeyen bir `kind` değerini
  (yazım hatası) de HATA sayar.
- **Geriye dönük uyumluluk ölçülerek doğrulandı:** hiçbir mevcut proje
  `kind` bildirmiyordu; `CatalogRailStandard`ı sistem varsayılanı yapmak
  SIFIR görsel etki yarattı (`--golden-set` `--update` GEREKMEDEN geçti).
- **Yeni golden referansı `golden/duvar_standartlari`:** üç duvar türünü
  (varsayılan, tuğla, cam) ve bir kapı açıklığının tarama/linetype'ı doğru
  DIŞLADIĞINI tek bir katta birlikte sınar.
- **Açık kararlar kapandı:** tarama deseni/ölçeği context'ten AYARLANAMAZ
  (sabit `ANSI31`/`1.5` — kolonlardaki `meta.column_hatch` gibi
  configurable değil, bilinçli kapsam kararı); tarama katmanı `wall.layer`
  ile AYNIDIR (kolonlardaki sabit `KOLON-TARAMA` gibi ayrı bir katman YOK,
  çünkü `wall.layer` VERİdir ve duvardan duvara değişebilir).
- **Doğrulama:** `python scripts/walls/selftest.py`.
- **Kayıt:** `DEVELOPMENT_HISTORY.md` içindeki `HD-010`.

### DEV-018 — DXF `BLOCK` entity kullanımı (modüller arası)

- **Durum:** COMPLETED (rev-14)
- **Kapsam notu:** Bu madde tek bir modüle ait değildi; `rooms`, `furniture`,
  `openings`, `axis` ve `legend` modüllerinin hepsini ilgilendiren bir DXF
  yetenek kararıydı. Ölçülerek görüldü ki **`furniture` (`DEV-010`) zaten
  `BLOCK`/`INSERT` kullanıyordu** — asıl boşluk mahal etiketiydi (proje bu
  görevi AÇARKEN yazılan "Mevcut durum" metni furniture'dan ÖNCEki bir
  ölçümdü ve bayatlamıştı).
- **Sonuç:**
  - *Fikir 1 — mahal etiketi bloğu + `ATTRIB` (SEÇİLDİ):** `MAHAL_ETIKET`
    bloğu üç `ATTDEF` (`MAHAL_ADI`/`MAHAL_KOD`/`ALAN`) ile bir kez tanımlanır;
    her mahal bir `INSERT` + üç `ATTRIB` olur (ana projede 125 `INSERT` +
    375 `ATTRIB`). Konum/yükseklik matematiği eski düz-`TEXT` formülüyle
    **doğrusal ölçekleme kanıtıyla** birebir örtüşür — bkz.
    `scripts/rooms/CLAUDE.md` "BLOK+ATTRIB".
  - *Fikir 2 — sembol/tefriş blok kütüphanesi:* tefriş kısmı zaten `DEV-010`
    ile tamamlanmıştı (yukarıdaki not). Kapı/pencere sembolleri ve aks
    baloncuklarının blok kütüphanesine taşınması **uygulanmadı** — açık fikir
    olarak duruyor (bugün bu semboller düz `ARC`/`LINE`/`CIRCLE`/`TEXT`'tir,
    yanlış değildir, sadece tek-nesne/`ATTRIB` avantajını taşımaz).
- **ÖNCE ÇÖZÜLMESİ GEREKEN maddeleri gerçekten sınandı:**
  - `golden_report.py::report`, `INSERT` blok içeriğini bounding box'a zaten
    KATIYORDU (`entity_bbox` docstring'i bunun `DEV-006`/tefriş ile
    düzeltildiğini not ediyor) — bu madde ölçülünce zaten KAPALI çıktı.
  - **Yeni bulunan gerçek engel (bu maddede öngörülmemiş):** ezdxf, bir
    `INSERT`e bağlı `ATTRIB`leri genel layout iterasyonuna/`query()`'e DAHİL
    ETMEZ (DXF dosyasında GERÇEKTEN ayrı entity'ler olsalar da). Bu,
    `golden_report.py::report`/`rule_room_labels`i SESSİZCE kör ederdi;
    `_iter_all` yardımcısı eklenerek kapatıldı (bkz.
    `scripts/rooms/CLAUDE.md` "ezdxf tuzağı").
- **Açık kararlar kapandı:** Mevcut düz geometri bloklara TAŞINMADI (sadece
  mahal etiketi, yeni bir öğe gibi ele alındı — geriye dönük veri taşıma
  gerekmedi çünkü davranış BİREBİR korundu). Öznitelikler `ATTRIB` seçildi
  (düz `TEXT` değil) — `validate.py` bunları okumaz (mahal etiketi zaten
  `validate.py`nin ilgilendiği bir kontrol değildi); golden raporu `_iter_all`
  ile okur. Ölçekli blokta metin yüksekliği `INSERT` `xscale`/`yscale` ile
  korunur (`Attrib.transform` uniform ölçeği doğru uygular).
- **Doğrulama:** `python scripts/rooms/selftest.py`.
- **Kayıt:** `DEVELOPMENT_HISTORY.md` içindeki `HD-009`.

## BACKLOG

Her modülün kendi plan maddesi artık yukarıdaki bölümdedir. `DEV-011` …
`DEV-014`, `DEV-018` (ve `DEV-019`/`DEV-020`) TAMAMLANDI — bu proje için
planlanmış modül kataloğunun TAMAMI uygulandı. Yeni bir modül fikri veya
mevcut modüllerin ertelenen "Fikir 2"leri (bkz. her modülün kendi
`CLAUDE.md`'si) sistem mimarı tarafından açıkça talep edilmeden
başlatılmaz.

Her görev uygulamaya alınmadan önce ilgili `scripts/<module>/CLAUDE.md` dosyası
ve `docs/phases/NEXT-MODULES-ROADMAP.md` okunur. Buradaki kayıtlar kod
uygulama izni değildir; yalnızca planlama ve devir bağlamıdır.

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
