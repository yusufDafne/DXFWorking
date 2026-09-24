# Sonraki Modüller Yol Haritası

Bu belge, Axis tamamlandıktan sonra yapılacak modül çalışmalarının sistem
mimarı tarafından tek tek direktiflendirilmesi için kullanılır. Aktif görev
durumu ve geliştirici bağlamı `docs/development/` altındadır. Her modül kendi
sözleşmesi okunmadan ve açık kapsam onayı verilmeden başlatılmaz.

## Ortak faz kapısı

Her modül için sıra değişmez:

1. Sistem mimarı fazı ve kapsamı açıkça başlatır.
2. İlgili `scripts/<module>/CLAUDE.md` okunur; mevcut implementasyon ve golden
   output etkisi belirlenir.
3. Veri/schema değişikliği gerekiyorsa ayrı karar alınır; varsayım yapılmaz.
4. Public API ve sorumluluk sınırı onaylanır.
5. Küçük taşıma/implementasyon yapılır.
6. Focused test veya compile çalıştırılır.
7. `python scripts/validate.py` ve gerekirse
   `python scripts/generate_dxf.py` çalıştırılır.
8. DXF entity, layer, geometri, pafta taşma ve golden-output farkları raporlanır.
9. Faz dosyasına durum, açık kararlar, riskler ve sonraki direktif önerisi yazılır.
10. Sistem mimarı kabul etmeden sonraki modüle geçilmez.

## Sıra

### Faz 3 — `openings/`

Kaynak: `scripts/walls/render.py::DefaultPlanOpeningStyle` ve
`WallNetwork` açıklık boşlukları.

Amaç: `Opening`, `Door`, `Window`, host wall, swing/menteşe, varyantlar,
style Protocol ve schedule davranışını ayırmak. Duvar rail geometrisi
`walls` içinde kalır.

Başlatma öncesi kararlar: schema alanları, host wall kimliği, açıklık konum
semantiği, plan/cephe stil kapsamı.

Kabul: mevcut kapı/pencere DXF davranışı korunur, açıklık genişliği/geometri
validate edilir, stil enjeksiyonu çalışır, golden farkları açıklanır.

### Faz 4 — `rooms/`

Kaynak: `scripts/generate_dxf.py::polygon_centroid`, `draw_room_label` ve
`scripts/walls/scan.py::RoomPolygonScanner`.

Amaç: oda poligonu, alan, komşuluk, etiketleme ve oda-duvar tutarlılığını
tek modüle almak.

Başlatma öncesi kararlar: bildirilen alan ile hesaplanan alan uyuşmazlığı,
validator'ın sahipliği, scanner önerisinin onay formatı.

Kabul: kapalı/self-intersection kontrolleri, fit edilmiş etiketler ve mevcut
oda çıktısı korunur.

### Faz 5 — `dimensions/`

Kaynak: `scripts/axis/__init__.py::AxisGrid._dim_chain_x/_dim_chain_y`.

Amaç: gerçek DXF ölçülerini `DimensionChain`, `LinearDim` ve `ChainLayout`
ile genelleştirmek.

Başlatma öncesi kararlar: ölçü stil Protocol'ü, zincir çakışma çözümü,
AxisGrid'den devralma API'si.

Kabul: cm metin kuralı, dimension entity türü, layer ve pafta sınırı korunur.

### Faz 6 — `columns/`

Kaynak: yeni bileşen; `axis/` public API tüketicisi.

Amaç: parametrik kolon kesitleri ve aks kesişimleri.

Başlatma öncesi kararlar: context veri yolu, kesit kataloğu, katlar arası
hizalama ve aks dışı kolonların izin modeli.

Kabul: bildirilen konum/kesit dışında geometri üretilmez, kolonlar akslarla
uyumlu ve golden output etkisi raporludur.

### Faz 7 — `elevations/`

Kaynak: `scripts/generate_dxf.py::elevation_vertical_extent` ve
`draw_elevation`.

Amaç: basitleştirilmiş seviye istifi, cephe açıklıkları ve aks izdüşümünü
izole etmek.

Başlatma öncesi kararlar: below-ground linetype, pencere yerleşim standardı,
plan bağımsızlığı ve `axis_source` sözleşmesi.

Kabul: bildirilen seviyeler doğru sırada, paftalarla hizalı, overflow kontrolü
altında ve renderer davranışıyla uyumludur.

### Faz 8 — `furniture/`

Kaynak: `scripts/generate_dxf.py` içindeki `counters` ve marking/furniture
çizimleri.

Amaç: tezgah ve sabit mobilya elemanlarını katalog/style ile ayırmak.

Başlatma öncesi kararlar: context veri yolları, oda/duvar çakışma kuralı,
fixture kapsamı.

Kabul: bildirilen geometri/layer korunur, mobilya paftadan taşmaz ve eksik veri
uydurulmaz.

### Faz 9 — `legend/` (opsiyonel)

Kaynak: pafta antetiyle karıştırılmaması gereken yeni legend bileşeni.

Amaç: kullanılan layer ve semboller için tekrar kullanılabilir lejant.

Başlatma öncesi kararlar: etkinleştirme kuralı, registry sahibi ve pafta
yerleşimi.

Kabul: yalnızca kullanılan/izinli öğeler açıklanır, `Sheet` sınırı korunur.

### Faz 10 — `importer/` (ileri faz — DXF tarama kısmı rev-15'te tamamlandı)

**Not (rev-15):** bu modül `import/` olarak planlanmıştı; `import` bir
Python anahtar kelimesi olduğu için geçerli bir paket adı DEĞİLDİR,
`importer/`e taşındı (bkz. `scripts/importer/CLAUDE.md` "İsim notu").
Aşağıdaki plan metni TARİHSEL olarak korunur; DXF tarama kısmı
(`DxfWallScanner`) tamamlandı, PDF/altlık kısmı hâlâ ileri fazdır.

Kaynak: yeni ters yönlü veri akışı.

Amaç: DXF/PDF/altlık kaynaklarından güven seviyesi ve provenance korunarak
aday yapılandırılmış veri üretmek.

Başlatma öncesi kararlar: desteklenen kaynaklar, confidence modeli, insan
onaylı import patch formatı ve context'e kabul kapısı.

Kabul: import sonucu otomatik olarak context veya nihai DXF olmaz; belirsiz
geometri raporlanır ve kaynak provenance'ı korunur.

## Mevcut durum

- `pafta/`: tamamlandı.
- `walls/`: tamamlandı.
- `axis/`: Faz 2 tamamlandı; validator ve generator başarılı.
- Sıradaki direktif: sistem mimarının onayıyla `openings/`.
- Bu yol haritası tek başına uygulama izni vermez.
