# shafts modülü (şaft / havalandırma / baca) — rev-27

Kullanıcı kararı (2026-10-05): şaft bir ODA DEĞİLDİR; `floors[].shafts[]` ile ayrı veri olarak
bildirilir ve komşu odalar poligonlarını şaftın etrafından OYAR. Üç tür: `tesisat`,
`havalandirma`, `baca` — hepsinin varsayılanı **net 500 mm kare**; ek talebe göre
değiştirilir (tür başına farklı ölçü UYDURULMAZ, yönetmelik verilmedi).

## Kurallar (kullanıcı)
- Şaft **daima kare veya 4:3** (`SHAFT_MAX_RATIO`); dikdörtgen değilse/oran aşılırsa UYARI.
- Varsayılan net kenar 500; poligon (duvar merkez çizgisi) kenarı = net + duvar (150) = **650**
  (`shaft_centerline_side`).
- Kat planında şaft boşluğu **minimum**; ıslak hacimler (banyo/WC) başka dairelerin ıslak hacmiyle
  **sırt sırta** verilir, olmuyorsa her banyo/WC çifti için **ikisinin arasına (ikisine de değen)** bir
  tesisat şaftı konur. Yerleşimi bu modül ÜRETMEZ, DOĞRULAR (`check_shafts`, UYARI).
- Şaft oda poligonlarıyla kesişemez (HATA); asansör/merdiven odasının içine/köşesine giremez (HATA).
- Şaft düşey bir boşluktur: aynı `id`, bulunduğu tüm katlarda aynı poligonda olmalı (UYARI,
  `check_shafts_across_floors`).

## Cizim (rev-27 duzeltmesi)
Saft poligonu duvar MERKEZ cizgisindedir (650); cizim ise duvar YUZLERI arasindaki NET bosluga (500x500)
oturur (`net_polygon`: `standards.measure.inset_polygon`). Kullanici: "resim tam bosluğun uzerine gelmeli".
Saft komsu odalardan degil, ilgili islak hacimler (WC/banyo) ile yapilan kollarla acilmali; yasam alani
(giyinme/salon) icinden gecirilmez (kullanici geri bildirimi rev-28).

## Public API
`Shaft`, `SHAFT_KINDS`, `DEFAULT_NET_SIDE_MM`, `shaft_centerline_side`, `shared_edge_length`,
`check_shafts(floor)` → (errors, warnings), `check_shafts_across_floors(floors)`,
`ensure_shaft_layer(doc)`, `draw_shafts_on_floor(msp, floor)`. Çizim: kapalı kare + çapraz, `SAFT`
katmanı (palette'den kod-sahipli turuncu).

## Çakışma
`collision/scene.py::COLLISION_EXEMPT` içinde gerekçesiyle muaf: şaft odalardan oyulan boşluktur,
tefriş/duvar çakışması `rooms.collision`dan doğal çıkar; şaft↔oda kesişimi bu modülde HATA.

## Bilinen sınırlamalar
- Yerleşimi otomatik ÖNERMEZ (etüt/yerleşim bağlantısı yok); bu proje için konumlar elle verildi.
- Baca/havalandırma için tür başına özel kural (yangın ayrımı, çatı çıkışı) YOK; yalnız tür etiketi.
- Şaftın etrafındaki duvar kalınlığı `walls` üretimine bağlıdır (aynı birim içi 150).

## Doğrulama
`python scripts/shafts/selftest.py` — elle hesaplanan ortak kenar/oran; temiz kat; kasıtlı bozma +
yanlış-pozitif; kat arası konum; çizim.

## Muhakeme katkısı (DEV-048)
**Rol:** ölçüm sağlayıcı (`reasoning.py`). **Ölçüm (`ventilation.py`, DEV-062; `validate.py` ÇAĞIRMAZ):** `check_wet_ventilation` — WC/banyonun dış cepheye açılan
penceresi YA DA `tesisat`/`havalandirma` şaftına ≥ `MIN_SHARED_EDGE_MM` (300 mm) ortak kenarı var mı (`check_shafts` ile AYNI tanım; `baca` sayılmaz).
**Katıldığı veçhe:** `isik_hava_yonelim.hava.islak_hacim_havalandirma` (`shadow`). **Bilinen boşluk:** şaft tanımsız (`floors[].shafts[]` yok) projede ıslak hacim
penceresizse veçhe öter (şaft verisi opt-in). **Bilgi mühendisi için not:** `check_shafts` ('şaft ıslak hacmi sunuyor mu') ile bu ('ıslak hacim havalandırılıyor mu')
FARKLI sorulardır; ortak tanım `MIN_SHARED_EDGE_MM`dedir, ikinci bir eşik yazma.
