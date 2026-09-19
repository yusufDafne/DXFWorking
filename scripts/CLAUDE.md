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
sorusu sorulur. Ad-hoc, tek kullanımlık çizim fonksiyonları (örn. eski
`draw_sheet_frame`) zamanla bir sınıfa terfi ettirilir.

## Modüler mimari (rev-4'te başladı)

Uzun vadede her çizim konusu (pafta, aks, duvar/oda, kolon, kapı/pencere
cetveli, ...) KENDİ modülüne VE kendi izole `CLAUDE.md`'sine sahip olmalı —
böylece ileride bir ajan sadece o modülün klasörünü açıp, projenin geri
kalanını bilmeye ihtiyaç duymadan o modül üzerinde derinlemesine/izole
çalışabilir (çok güçlü, uzman bir dil modeliyle tek bir modüle odaklanma).
**Bu motto TÜM gelecek modüller için geçerlidir.**

- ✅ **`scripts/pafta/`** — İLK modül (rev-4). Kendi `CLAUDE.md`'si var.
  Detay için oraya bakın; bu dosyada tekrar edilmez.
- ⏳ **Aks modülü** (henüz `generate_dxf.py` içinde, `AxisGrid` sınıfı) —
  sıradaki modül adayı.
- ⏳ **Duvar/oda modülü** (henüz `generate_dxf.py` içinde, `Wall`/
  `WallNetwork` sınıfları) — modül adayı.
- ⏳ Kolon, kapı/pencere cetveli, ölçü zinciri (`DimensionChain`) — henüz
  sınıf bile yok, sadece fikir.

## Kurulu sınıflar (durum: uygulandı, henüz kendi modülüne taşınmadı)

- **`Wall` / `WallNetwork`** (rev-1'de kuruldu, CLAUDE.md'deki "Duvar çizim
  standardı" bölümüyle eşleşir): Duvarları merkez çizgisi + kalınlıktan iki
  kenar çizgisine (rail) çevirir, komşu duvarlarla gönye (miter) birleşimi
  hesaplar. Girdi: wall_id/start/end/thickness/layer listesi. Çıktı: her
  duvar için çizilebilir rail segmentleri.
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
