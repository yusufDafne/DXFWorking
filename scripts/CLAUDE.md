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

## Kurulu sınıflar (durum: uygulandı)

- **`Wall` / `WallNetwork`** (rev-1'de kuruldu, CLAUDE.md'deki "Duvar çizim
  standardı" bölümüyle eşleşir): Duvarları merkez çizgisi + kalınlıktan iki
  kenar çizgisine (rail) çevirir, komşu duvarlarla gönye (miter) birleşimi
  hesaplar. Girdi: wall_id/start/end/thickness/layer listesi. Çıktı: her
  duvar için çizilebilir rail segmentleri.
- **`Sheet`** (rev-3'te kuruldu, "Pafta standardı" bölümüyle eşleşir):
  Bir paftanın çerçevesini ve sağ-alt köşedeki standart başlık kutusunu
  (kat adı + "PAFTA n/N" + ölçek + not) çizer. Parametrik: `scale` ve
  `text_height` ile kurulur, herhangi bir pafta genişliği/yüksekliği için
  `draw(...)` çağrılır. Hem kat planı paftalarında hem cephe paftalarında
  aynı sınıf kullanılır.
- **`AxisGrid`** (rev-3'te kuruldu, "Aks (grid) sistemi" bölümüyle eşleşir):
  Düşey (nümerik) ve yatay (alfabetik) aks çizgilerini kesikli çizgi + uç
  baloncuklarıyla çizer. `draw_on_floor(...)` bir kat paftasına tüm aksları
  basar; `draw_on_elevation(...)` bir cepheye SADECE ilgili aks ailesini
  (düşey akslar ön/arka cephede, yatay akslar sağ/sol cephede) izdüşürür.

## Planlanan sınıflar (durum: henüz yok — fikir notu)

Kullanıcı (backend/CAD standartları sahibi) zamanla şu türde sınıflar
isteyecek; her biri kurulduğunda yukarıki listeye taşınıp burada silinmeli:

- **`DimensionChain`**: Bir dizi noktayı art arda ölçülendiren (ölçü
  çizgisi + oklar/tikler + ölçü metni) sınıf. Ölçü metni HER ZAMAN tam
  sayı cm olarak formatlanmalı (bkz. kök CLAUDE.md "Ölçülendirme birimi").
  Parametrik: ölçek + metin yüksekliği + ok/tik stili.
  DUYURULMADI, henüz elle "labels" ile ad-hoc yapılıyor.
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
