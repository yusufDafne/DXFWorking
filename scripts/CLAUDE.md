# scripts/ — Çizim Altyapısı Geliştirme Notları

Bu dosya, `daire-plani-ai` pipeline'ının **kod mimarisi** ve gelecekteki
genişletme planı içindir. Kök dizindeki `CLAUDE.md` "ne zaman ne yapılır"
kurallarını (talep akışı, git, doğrulama) tutar; bu dosya ise "kod nasıl
yapılandırılır" sorusuna cevap verir — bir backend/CAD-altyapı yol haritası.

## Vizyon

`scripts/generate_dxf.py` tek bir dev script olarak büyümek yerine, her biri
**ölçek ve boyut parametreleriyle çalışan, tekrar kullanılabilir bir çizim
sınıfı** etrafında organize olmalı. Yeni bir çizim ihtiyacı doğduğunda önce
"bunun için bir sınıf mı gerekiyor, yoksa mevcut bir sınıfa mı ekleniyor?"
sorusu sorulur. Ad-hoc, tek kullanımlık çizim fonksiyonları zamanla ilgili
modülün parametrik sınıfına terfi ettirilir; pafta çizimi artık
`scripts/pafta/Sheet` içindedir.

## Modüler mimari (rev-4'te başladı)

Uzun vadede her çizim konusu (pafta, aks, duvar/oda, kolon, kapı/pencere
cetveli, ...) KENDİ modülüne VE kendi izole `CLAUDE.md`'sine sahip olmalı —
böylece ileride bir ajan sadece o modülün klasörünü açıp, projenin geri
kalanını bilmeye ihtiyaç duymadan o modül üzerinde derinlemesine/izole
çalışabilir (çok güçlü, uzman bir dil modeliyle tek bir modüle odaklanma).
**Bu motto TÜM gelecek modüller için geçerlidir.**

- ✅ **`scripts/pafta/`** — İLK modül (rev-4). Kendi `CLAUDE.md`'si var.
- ✅ **`scripts/walls/`** — Duvar modülü: `Wall`, `WallNetwork`, katalog,
  cizim, tarama (bkz. `scripts/walls/CLAUDE.md`).
- ✅ **`scripts/axis/`** — `AxisGrid`, `AxisDrawingStandard` ve
  `ensure_axis_layer` taşındı; tamamlanma kaydı
  `docs/development/DEVELOPMENT_HISTORY.md` içindedir.
- ✅ **`scripts/openings/`** — `Opening`/`Door`/`Window`,
  `OpeningSymbolStyle`, `OpeningSchedule` (bkz. `HD-003`).
- ✅ **`scripts/rooms/`** — `Room`, `PolygonOps`, `RoomLabeler` (3 satırlı
  mahal etiketi, bkz. `HD-005`).
- ✅ **`scripts/dimensions/`** — `DimensionChain`, `LinearDim`,
  `ChainLayout` (bkz. `HD-003`).
- ✅ **`scripts/typography/`** — Proje yazı tipi / DXF text style sahibi
  (bkz. `HD-005`). Çizilen font ile `fit_text_height`'in ölçtüğü font bu
  modül sayesinde tek kaynaktan gelir.
- ⏳ Kolon, tefriş, cephe, lejant, import — her biri için ayrı plan maddesi
  `docs/development/DEVELOPMENT_TASKS.md` içindedir (`DEV-009` … `DEV-017`).

## Kurulu sınıflar (durum: uygulandı)

- **`Wall` / `WallNetwork`** — `scripts/walls/` modulunde (rev-1 mantigi +
  `WallCatalog`, `RoomPolygonScanner`, `OpeningSymbolStyle` genislemesi).
- **`AxisGrid`** (rev-3'te kuruldu, rev-4'te genişletildi, "Aks (grid)
  sistemi" bölümüyle eşleşir): Düşey (nümerik) ve yatay (alfabetik) aks
  çizgilerini kesikli + sabit RGB(67,77,88) renkte, uç baloncuklu (çizgi
  baloncuğa TEĞET biter, içine girmez) çizer; `draw_on_floor(...)` bir kat
  paftasına tüm aksları + aralarındaki DXF linear dimension'ları
  (`_dim_chain_x/_dim_chain_y`, küçük punto, tam sayı cm) basar;
  `draw_on_elevation(...)` bir cepheye SADECE ilgili aks ailesini (düşey
  akslar ön/arka cephede, yatay akslar sağ/sol cephede) + kendi ölçü
  zincirini izdüşürür. Katman rengi context.json'dan DEĞİL,
  `ensure_axis_layer` ile kod tarafında zorunlu kılınır (kullanıcı bunu
  "context.json'a asla cizim sabiti sizmamali" ilkesiyle tutarlı kod-seviyeli
  bir ofis standardı olarak istedi).

## `scripts/pafta/` modülünde yaşayanlar (bkz. `scripts/pafta/CLAUDE.md`)

`Sheet`, `PaftaOverflowError`, `verify_within_frame`, `PaperSizePlanner`,
`fit_text_height`/`fit_uniform_text_height` — hepsi ARTIK bu modülde.
`generate_dxf.py` bunları import eder, kendi kopyasını TUTMAZ. Oda
etiketleri gibi genel-amaçlı metin sığdırma ihtiyaçları da bu modülün
`fit_text_height` fonksiyonunu yeniden kullanır (henüz ayrı bir "text"
modülüne çıkarılmadı — küçük bir bilinen tutarsızlık, ileride
düzeltilebilir).

## Yol haritasi (modul sirasi ve genisletilebilirlik)

Ortak desen (pafta + walls ile kanitlandi):

- **Veri** `context.json` + sema; **standart** kod icinde katalog/protocol;
  **cizim** parametrik sinif (`scale`, `units`, enjekte edilebilir stil).
- Yeni yonetmelik/ofis std. = yeni katalog/sozluk veya alt `DrawingStandard`,
  cekirdek geometri degismez.

| Oncelik | Modul         | Cekirdek siniflar                                          | Not                                                            |
| ------- | ------------- | ---------------------------------------------------------- | -------------------------------------------------------------- |
| 1       | `pafta/`      | `Sheet`, `PaperSizePlanner`                                | Tamam; uniform template + keyplan bekliyor                     |
| 2       | `walls/`      | `Wall`, `WallNetwork`, `WallCatalog`, scanner              | Tamam (ilk surum)                                              |
| 3       | `axis/`       | `AxisGrid`, `AxisDrawingStandard`                          | Tamamlandi; davranis korunarak tasindi                         |
| 4       | `openings/`   | `Opening`, `DoorSymbol`, `WindowSymbol`, `OpeningSchedule` | Siradaki faz; duvar host referansi, mentese, surme, cift kanat |
| 5       | `rooms/`      | `Room`, `RoomLabeler`, `PolygonOps`                        | Alan, etiket sigrdirma (pafta `fit_text_height`)               |
| 6       | `dimensions/` | `DimensionChain`, `LinearDim`, `ChainLayout`               | Tam sayi cm; AxisGrid devrani                                  |
| 7       | `columns/`    | `Column`, `ColumnGrid`                                     | Aks kesisimi; kesit sembolu                                    |
| 8       | `elevations/` | `ElevationSheet`, `LevelStack`, `FacadeOpeningPlacer`      | Plan-ten bagimsiz basitlestirme bilincli kalabilir             |
| 9       | `furniture/`  | `Counter`, `Fixture`                                       | Mutfak tezgahi vb.                                             |
| 10      | `legend/`     | `TitleBlockLegend`, `LayerSwatch`                          | Opsiyonel pafta lejanti                                        |
| 11      | `import/`     | `DxfWallScanner`, `PdfUnderlay`                            | Ters yon: mevcut cizimden veri (ileri faz)                     |
| -       | `typography/` | `TextStyles`                                               | Proje fontu (Arial Narrow) + rol bazli text style; rev-9       |

Semaya eklenecek opsiyonel alanlar (talep ile, deger uydurulmaz):

- `walls[].kind` -> `WallCatalog`
- `openings[].variant` / `swing` / `host_side`
- `meta.drawing_standard` -> hangi katalog paketinin yuklenecegi

rev-9'da semaya EKLENENLER (artik opsiyonel degil, kullanimda):

- `meta.fonts.default` / `meta.fonts.room_label` -> `typography.TextStyles`
- `floors[].code` -> kat kodu (B1/B2/ZK/K1../TR), mahal no oneki
- `rooms[].no` -> mahal no; kat koduyla birlesince benzersiz mahal kimligi

## Planlanan sınıflar (durum: henüz yok — fikir notu)

Kullanıcı (backend/CAD standartları sahibi) zamanla şu türde sınıflar
isteyecek; her biri kurulduğunda kendi modülüne + kendi `CLAUDE.md`'sine
taşınıp buradan silinmeli:

- **`DimensionChain`**: Bir dizi noktayı art arda ölçülendiren (ölçü
  çizgisi + oklar/tikler + ölçü metni) sınıf. Ölçü metni HER ZAMAN tam
  sayı cm olarak formatlanmalı (bkz. kök CLAUDE.md "Ölçülendirme birimi").
  Parametrik: ölçek + metin yüksekliği + ok/tik stili. `AxisGrid` zaten
  benzer bir mini-versiyonunu (`_dim_chain_x/_dim_chain_y`) kullanıyor;
  bu sınıf kurulduğunda `AxisGrid` ona devredebilir.
- **`ColumnGrid` / `Column`**: Kolonlar projeye girdiğinde, `AxisGrid` ile
  entegre çalışacak — kolonlar aks kesişimlerine oturur, aks sıklığı kolon
  yerleşimine göre dinamikleşir. Kolon kesiti (kare/dikdörtgen/dairesel)
  parametrik olmalı.
- **`DoorWindowSchedule`**: Kapı/pencere tipi başına tekrarlanan sembolü
  (kanat+kavis / çift çizgi) tek yerden üreten, `openings[]` verisinden
  besleneni bir sınıf — su an `draw_wall_network` icinde gomulu, ayri
  sinifa cikarilabilir.
- **`TitleBlockLegend`**: Birden fazla paftada tekrar eden katman/sembol
  lejantı (opsiyonel, kullanıcı isterse).
- **Pafta kaskad mantığı** (henüz `PaperSizePlanner`'a eklenmedi): "1/50
  favori, sığmazsa 60/90'lığa, o da yetmezse 1/100'e düş" — henüz ölçeği
  seçilmemiş YENİ bir proje için düşünülüyor. Şu anki `PaperSizePlanner`
  SABİT bir ölçek için sadece kağıt boyutu seçiyor, ölçeği değiştirmiyor.
- **Uniform sheet template**: Tüm paftaların FİZİKSEL boyutunun (genişlik
  dahil) birebir aynı olacağı, içerik daha küçükse boş alanla ortalanan bir
  şablon. Kullanıcı netleştirdiğinde `scripts/pafta/` içinde uygulanmalı.

## Tasarım ilkeleri

1. **Parametrik olceklenebilirlik:** Bir sinif "olcek" (ör. "1:100") ve/veya
   somut boyut alip, CLAUDE.md'deki standart oranlara (metin yuksekligi,
   cizgi kalinligi, bubble capi vb.) gore otomatik olcekli cizim uretmeli —
   sabit mm degerleri sinif disinda, sinifin kendi ic sabitleri olarak
   kalmali (context.json'a asla "cizim sabiti" sizmamali, bkz. kok
   CLAUDE.md'deki "DXF uretim disiplini").
2. **Tek sorumluluk:** Her sinif TEK bir katman/eleman turunu cizer (duvar,
   pafta cercevesi, aks, vs.). Cok isli "god function" yerine sinif
   kompozisyonu tercih edilir.
3. **Tum katlarda/cephede tekrar kullanim:** Bir sinif hem kat planlarinda
   hem cephelerde (hem ileride kesitlerde) calisabilmeli — ayni AxisGrid
   nesnesi hem `draw_on_floor` hem `draw_on_elevation` sunmasi gibi.
4. **context.json = veri, sinif = ciizim mantigi:** Yeni bir sinif eklerken
   ilk soru "bu sinifin ihtiyac duydugu veri context.json semasinda nerede
   duracak" olmali. Sinifin kendisi tasarim verisi uretmez/uydurmaz, sadece
   context.json'daki veriyi cizim kurallarina gore yorumlar.

## Sistem vizyonu ve teknik otorite

Bu sistem, dil modeli aracılığıyla mimari proje üreten, yöneten, revize eden,
bölen/parçalayan ve modüler uygulama çıktıları hazırlayan uzun soluklu bir
mimari araçtır. En uzak vizyon, aracın uzman mimarın bir numaralı çalışma
aracına ve zamanla mimari kararları güvenilir biçimde taşıyan bir sisteme
dönüşmesidir.

Dil modeli bu sistemde nihai teknik otorite değildir. Model; yapılandırılmış
talep, patch ve izinli seçenek önerileri üretir. Ölçü, koordinat, geometri,
standart veya eksik veri uyduramaz. Nihai kararları Python sınıfları,
kataloglar, Protocol'ler, schema ve `validate.py` verir. Eksik veya çelişkili
bilgi varsa akış durur ve karar istenir. Sistem mimarı açıkça sonlandırma
komutu vermedikçe planlama ve sistemi güçlendirme çalışmaları tamamlanmış
kabul edilmez.

## Generic Component Contract

Yeni her çizim bileşeni aşağıdaki sözleşmeyi karşılamadan sisteme alınmaz:

1. Sahip olduğu modül ve o modülün izole `CLAUDE.md` dosyası.
2. `context.json` veri yolu veya bileşenin yalnızca derived/read-only olduğu
   açık ifadesi; şema ve `additionalProperties` kararı.
3. Public API, bağımlılık yönü, units/scale davranışı ve veri ile çizim
   standardı arasındaki sınır.
4. Katalog, Protocol veya style enjeksiyon noktası; çizim sabitlerinin
   context'e sızmaması.
5. Layer ve çizim sırası; pafta yerleşimi, taşma ve geometri invariant'ları.
6. `validate.py` sorumluluğu, hata ve eksik veri davranışı.
7. Odaklı test/regresyon komutu, golden-output etkisi ve bilinen sınırlamalar.

Bir bileşen derived geometri üretse bile bunu kullanıcı tasarım verisi gibi
`context.json` içine yazamaz. Yeni context alanı, schema değişikliği ve yeni
standart ancak açık sistem mimarı/kullanıcı kararıyla eklenir.

## Agent rolleri ve çalışma yöntemi

Agent rolleri ayrıdır:

- `system-architect/developer`: sistem kodu, schema, kataloglar, modül
  sözleşmeleri ve merkezi geliştirme dokümanları üzerinde çalışır.
- `project-operator`: yalnızca onaylı public API ve proje dizini içinde
  yapılandırılmış proje üretir/revize eder; sistem koduna veya başka projeye
  yazamaz.
- `reviewer/validator`: validate sonuçlarını, golden output'u ve sözleşme
  uyumunu bağımsız denetler; tasarım verisi uydurmaz.

Her geliştirme agent'ı önce en yakın `CLAUDE.md`yi, public APIyi ve komşu
uygulamayı okur; tek bir falsifiable yerel hipotez ve ucuz bir ayrıştırıcı
kontrol kurar; en küçük değişikliği yapar; hemen focused validation çalıştırır.
Sonra gerekli ise `validate.py` ve `generate_dxf.py` çalıştırılır. Modül dışı
bir karar çıkarsa agent durur ve üst sözleşmeye geri döner.

## Sistem, proje ve çıktı sahipliği

Sistem kodu, schema, kataloglar ve genel geliştirme/kullanım dokümanları proje
verisinden ayrı tutulur. Her proje kendi dizininde taleplerini, context
revizyonlarını, doğrulama raporlarını, preview'larını, manifest/provenance
kayıtlarını ve nihai DXF çıktısını taşır. Projeler birbirlerinin verisine
yazamaz.

DXF dosyaları nihai çıktıdır; elle düzenlenmez ve yalnızca validate edilmiş
pipeline ile üretilir. Seçilmiş nihai DXF'ler golden output olarak sistemin
biçimsel referansıdır. Yeni renderer veya modül değişiklikleri golden
çıktılarla karşılaştırılır; yalnızca dosya hash'i değil, entity türleri,
katmanlar, geometrik sınırlar, pafta çerçeveleri, ölçüler ve kritik semboller
kontrol edilir.

Merkezi `docs/` dizini şu bilgi sınıflarını taşır: sistem geliştirme agent
talimatları, sistem kullanım/üretim agent talimatları, mimari karar kayıtları,
golden-output politikası, operasyon kılavuzu ve geliştirme geçmişi/görev
kayıtları. Proje
dizinlerine bu belgelerin kopyası yazılmaz; proje yalnızca kullanılan sistem
sürümü ve ilgili karar referansını kaydeder.

## Güncel modül sırası ve faz kapısı

Sabit geliştirme sırası şöyledir:

1. `pafta/` tamamlandı: `Sheet`, fit, overflow ve kağıt planlama.
2. `walls/` tamamlandı: rail, network, katalog, render ve scanner.
3. `axis/` tamamlandı: `AxisGrid` ve `AxisDrawingStandard`,
   `scripts/axis/` içine davranış korunarak taşındı.
4. `openings/` sonraki ilk modüldür: kapı/pencere tipleri, host wall, swing
   ve cetvel.
5. `rooms/`: oda poligonu, alan, etiket ve oda-duvar tutarlılığı.
6. `dimensions/`: `DimensionChain`; AxisGrid'in mini zincirlerini devralır.
7. `columns/`: kolon ve aks kesişimi.
8. `elevations/`: seviye istifi ve cephe açıklıkları.
9. `furniture/`: tezgah ve sabit mobilya.
10. `legend/`: isteğe bağlı lejant.
11. `import/`: ileri faz DXF/altlık okuma.

Her fazda önce agent sözleşmesi ve public API, sonra davranış korumalı taşıma,
sonra schema/validator/generator entegrasyonu ve focused validation yapılır.
Faz devri; mevcut durum, tamamlanan işler, açık kararlar, bilinen riskler ve
bir sonraki direktif önerisiyle `docs/development/` altındaki geliştirme
geçmişi ve geliştirici notlarında kayıt altına alınır. Eski tekil faz dosyaları
kalıcı çalışma kaydı olarak tutulmaz.
