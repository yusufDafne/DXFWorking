# collision modülü (çakışma denetimi) — DEV-019 uygulandı (rev-12)

Modüller arası **girişim (clash) denetimi**. Bir koltuğun duvara, kolona,
başka bir koltuğa veya kapı açılım yayına girip girmediğini; bir tefrişin
bildirilen odaların dışına taşıp taşmadığını `context.json` üzerinde,
**DXF üretilmeden önce** denetler.

## Kararın özü: ayrım ARİTEDİR

Soru uzun süre "ayrı modül mü, her modül kendi mi" biçiminde duruyordu. İki
cevap da kısmen doğruydu, çünkü ortada **tek bir kontrol sınıfı yok, iki tane
var**:

| Arite | Soru | Sahibi |
|-------|------|--------|
| **1 (tekil)** | "Kendi verim geçerli mi?" — oda poligonu kapalı mı, açıklık host duvardan geniş mi, kolon kesiti katalogda var mı | **ilgili modül** (`validate.py::check_rooms` / `check_walls` / `check_openings`) |
| **2+ (çift)** | "İki FARKLI eleman sınıfı aynı yeri mi işgal ediyor?" | **bu modül** |

Endüstri karşılığı nettir: BIM'de modelleme aracı kendi disiplininin
tutarlılığını denetler, **disiplinler arası çakışma ayrı bir araçtır** —
Navisworks *Clash Detective*, Solibri *Model Checker*. Kural N modüle
dağıtılırsa hiçbiri bütünü göremez.

## Bağımsızlık nasıl korunuyor: bağımlılık TERSİNE çevrildi

**Bu paket hiçbir çizim modülünü import etmez.** Motor yalnızca anonim
`CollisionShape(tag, id, polygon)` tanır — koltuğun ne olduğunu bilmez.
Her çizim modülü kendi ayak izini kendisi üretir:

```
scripts/<modül>/collision.py::footprints(floor, context) -> list[CollisionShape]
```

Bir elemanın kapladığı alanı, onu **çizen** modül bilir: tefrişin katalog
ölçüsü + rotasyonunu `furniture/`, kapı açılım sektörünü `openings/`, kolon
kesitini `columns/`. Sonuç: **ayak izinin sahibi modül, çakışma kuralının
sahibi motordur.** Sahiplik bölünmez.

Benzetme: bir fizik motoru arabayı ve ağacı tanımaz, yalnızca collider tanır.

## Sorumluluk

| Dosya | Görev |
|-------|-------|
| `geometry.py` | Saf poligon matematiği — alan, AABB, Sutherland–Hodgman kırpma, nokta-içinde-çokgen, dışbükeylik. **Projedeki tek sahibi budur**; `validate.py` de buradan tüketir |
| `shapes.py` | `CollisionShape` + dikdörtgen / çokgen / yay-sektörü / daire üreticileri, etiket sabitleri |
| `matrix.py` | `CollisionPolicy`: hangi çift **FORBID / WARN / IGNORE**, temas toleransı |
| `engine.py` | `CollisionEngine`: kaba faz (AABB) → ince faz (kırpma) → `Clash` kayıtları + içerme kontrolü |
| `report.py` | `ClashReport`: hata/uyarı ayrımı, kabul kararı (`ok`), proje dilinde mesaj |
| `scene.py` | `Scene.from_floor` — sağlayıcıları çağıran **tek** yer; `FOOTPRINT_PROVIDERS`, `COLLISION_EXEMPT` |
| `selftest.py` | Negatif testler (aşağıya bakınız) |

## Politika matrisi (varsayılan)

| Çift | Politika | Gerekçe |
|------|----------|---------|
| tefriş ↔ tefriş | **FORBID** | iki mobilya aynı yerde duramaz |
| tefriş ↔ kolon | **FORBID** | taşıyıcı geçilemez |
| tefriş ↔ kapı açılım sektörü | **FORBID** | kapı açılamaz hale gelir |
| tefriş oda sınırının DIŞINDA | **FORBID** | yerleşim yanlış mahalde (içerme kuralı) |
| tefriş ↔ duvar | **WARN** (tolerans üstü) | dolap duvara DAYANIR; mm ölçeğinde temas normaldir |
| kolon ↔ duvar | **IGNORE** | kolonun duvar içinde olması TASARIMDIR |
| kolon ↔ oda | **IGNORE** | kolon bir odanın içinde durabilir |
| kolon ↔ kolon | **FORBID** | |
| kolon ↔ kapı açılımı | **FORBID** | kapı önünde kolon olmaz |
| duvar ↔ duvar, duvar ↔ kapı açılımı | **IGNORE** | gönye birleşim / yay zaten duvardan başlar |
| kapı ↔ kapı | **FORBID** (rev-13) | açılım yönü artık schema'da; iki kapının birbirine açılması gerçekten tespit edilebilir. Sürme kapı sektör üretmediği için doğal olarak muaftır |

Matriste **tanımsız** bir çift `IGNORE` alır — yeni bir modülün eklenmesi
üretimi durdurmasın diye. Sessiz kalma riskini `doc_check.py` kapatır.

## Tolerans: ALAN değil, DERİNLİK

2100 mm'lik bir koltuk duvara 5 mm girse kesişim **alanı** 10500 mm² olur;
alan eşiği eleman boyuyla ölçeklendiği için anlamsızdır. Bunun yerine kesişim
çokgeninin **kısa kenarına** bakılır (`geometry.min_extent`) — bu, girişimin
gerçek derinliğidir. `CONTACT_TOLERANCE = 5 mm` altındaki girişim **temas**
sayılır.

Ölçüm eksen hizalıdır; eğik bir dilim gerçek kalınlığından **kalın** görünür,
yani hata payı her zaman "daha çok bildir" yönündedir, sessiz kalma yönünde
değil.

## Nerede çalışır: `validate.py`, ÜRETİMDEN ÖNCE

Hata mesajı **proje dilinde** olmalıdır:

```
[K1] tefris 'f_koltuk3 (Koltuk (3'lu))' ile tefris 'f_koltuk2 (Koltuk (2'li))'
     cakisiyor (kesisim ~1.360 m2, girisim derinligi ~850 mm).
```

Bu doğrudan `context.json`'da düzeltilir. Denetim DXF üretildikten sonra
yapılsaydı mesaj `handle 2F4 ile handle 3A1` olurdu ve düzeltilemezdi.
Yalnızca **FORBID** üretimi durdurur; **WARN** raporlanır ama bloklamaz.

## Neden `golden_report.py`ye kural olarak eklenmedi

Golden'ın sorusu "çıktı beklenmedik şekilde değişti mi", çakışmanın sorusu
"tasarım doğru mu". Birleştirmenin somut bedeli: **bir golden referansı asla
kasıtlı çakışma içeremezdi**, çalıştığı anda patlardı. Oysa motorun kendisini
doğrulamanın tek yolu budur — bkz. `selftest.py`.

## Doğrulama

```
python scripts/collision/selftest.py
```

Kasıtlı olarak bozulmuş tek bir kat kurulur ve motorun **tam olarak** beklenen
bulguları (ne bir eksik, ne bir fazla) üretmesi aranır: iki tefriş üst üste,
tefriş odanın dışında, tefriş kapı sektöründe → **3 HATA**; tefriş duvara 50 mm
girmiş → **1 UYARI**. Yanlış-pozitif de sınanır: 3 mm girişim temastır, kolonun
duvarda/odada olması normaldir. Kesişim ölçüsü elle hesaplanabilir
(800 × 750 = 600000 mm², derinlik 750).

`doc_check.py` ayrıca şunu **mekanik** olarak denetler: geometri üreten her
modülün ya `collision.py`si vardır ya da `COLLISION_EXEMPT` içinde
**gerekçesiyle** listelenmiştir.

## Sınır

Bu modül çizim yapmaz, DXF'e dokunmaz, `ezdxf` kullanmaz ve context'i
değiştirmez. Yalnızca rapor üretir; kabul kararını `validate.py` verir.

## Bilinen sınırlamalar

- **Yalnızca AYNI kat içinde bakılır.** Katlar arası düşey hizalama (üst katta
  kolonun kayması) bu motorun işi değildir — bkz. `scripts/columns/CLAUDE.md`.
- **Kırpma, kırpan çokgenin dışbükey olmasını gerektirir.** Varsayılan
  matriste alan kesişimi hesaplanan her çift dışbükeydir. İçbükey olabilen tek
  şekil oda poligonudur ve o yalnızca içerme testinde (nokta-içinde-çokgen)
  kullanılır. İki içbükey şekil çifti oluşursa motor sınır kutusu kesişimine
  düşer — "daha çok bildir" yönünde bir hata.
- **Duvar ayak izi merkez çizgi + kalınlıktır**, gönyelenmiş rail çokgeni
  değil. Fark yalnızca duvar uçlarındadır.
- **Kapı açılım sektörü 8 doğru parçasıyla yaklaşılır** (`SECTOR_SEGMENTS`).
  Sabittir ve ölçeğe bağlı değildir; deterministik üretim ilkesi gereği aynı
  context her zaman aynı raporu vermelidir. Çokgen gerçek yaydan biraz
  KÜÇÜKTÜR, yani kenarda kalan bir tefriş kaçabilir.
- ~~Kapı açılım yönü schema'da yok.~~ **rev-13'te (DEV-016) kapandı:**
  `swing` ve `host_side` artık veriden gelir ve sektör, çizilen yayla **aynı
  kaynaktan** (`openings.geometry.swing_geometry`) hesaplanır. Bu düzeltme
  gerçek bir hatayı da kapattı: sektör, `position_from_start` açıklığın
  başlangıcı sanıldığı için çizilen yaydan **yarım genişlik** kayıktı.
- **`counters[]` denetlenmez.** Mutfak tezgahı hâlâ `generate_dxf.py` içinde
  ad-hoc çizilmektedir ve ayak izi üretmez (bkz. `scripts/furniture/CLAUDE.md`
  "çifte sorumluluk").
- **Pafta/aks/ölçü denetlenmez** (`COLLISION_EXEMPT`); pafta taşması `Sheet.
  verify_within_frame` ile DXF seviyesinde ayrıca kontrol edilir.
