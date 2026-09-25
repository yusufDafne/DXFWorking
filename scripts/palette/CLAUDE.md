# palette modülü (katman renk organizasyonu) — DEV-030

Tüm **kod-sahipli** (context.json'dan DEĞİL, `ensure_*_layer` deseniyle
koddan gelen) katman renklerinin TEK kaydı ve cakışma/ayrışma denetleyicisi.

## Neden ayrı bir modül (kullanıcı kararı, 2026-09-25)

`DEV-030`nin Fikir 1/Fikir 2 analizinde iki seçenek sunuldu: her modül kendi
rengini kendi belirlesin (merkezi olmayan), ya da merkezi bir kontrolör
modülü kursun. Kullanıcı **Fikir 2**'yi seçti, gerekçesi:

> "her modül kendi rengini oluşturursa bazı modüller aynı rengi seçmiş
> olabilir ... ve bazı modüllerin birbirlerine kontrast renkler ile
> bulunması ihtiyacı olabilir bundan dolayı ayrı bir modül olması uygun
> olabilir."

Bu iki cümle, modülün iki kuralına BİREBİR karşılık gelir (bkz. aşağı).

## Somut bulgu (bu modülün kurulma nedeni)

`scripts/columns/standard.py::COLUMN_RGB`, ÜÇ farklı katmana (`KOLON`
kontur, `KOLON-TARAMA` tarama, `KOLON-METIN` isim) TEK bir renk atıyordu —
kullanıcının birinci endişesi (aynı rengin paylaşılması) GERÇEKTEN
gerçekleşmişti. Bu modül kurulurken KOLON ailesi üçe ayrıldı (kontur orta
gri, tarama daha açık, metin en koyu) ve `AKS`in sabit rengine
(`(67,77,88)`) yeterince uzak tutuldu — eskiden `(90,90,96)` AKS'ye
tehlikeli derecede yakındı.

## İki kural

1. **Hiçbir iki katman AYNI rengi taşıyamaz** (tam eşitlik yasağı, HER ZAMAN
   geçerli — gruptan bağımsız).
2. **Aynı `contrast_group`taki katmanlar birbirinden en az
   `CONTRAST_MIN_DISTANCE` (40.0, RGB Öklid mesafesi) kadar uzak olmalıdır.**
   `"primary"` grubu, aynı pafta üzerinde AYNI ANDA görülebilen yapısal/
   anotasyon katmanlarını (AKS, KOLON ailesi, KESİT, MERDİVEN) kapsar.
   Tefriş ailesi bu gruba BİLEREK GİRMEZ (`contrast_group=None`) — kullanıcı
   rev-10'da "zıt renk kullanılmaz" dedi, düşük kontrast KASITLIDIR ve bu
   karar `DEV-030` ile BOZULMADI.

## Kapsam (bilinçli sınır — `DEV-030`nun açık kararlarından biri)

Yalnızca **kod-sahipli** katmanları kapsar. `context.json::layers[]`
(proje verisi, ACI index) bu kaydın DIŞINDADIR — o zaten kullanıcı/proje
kararıdır, kod bunu SEÇMEZ, `generate_dxf.py::setup_layers` sadece uygular.
Kullanıcı bu ayrımı genişletmeyi istemedi, bu yüzden ACI-index/RGB ikiliği
KORUNDU (proje verisi = ACI, sistem/kod standardı = RGB).

## Public API

```python
from palette import PALETTE, LayerColor, color_for, validate_palette, CONTRAST_MIN_DISTANCE

rgb = color_for("KOLON")          # kayıtlı bir isim -> RGB tuple
errors = validate_palette()        # boş liste = ihlal yok
```

`color_for` kayıtsız bir isim için **HATA verir** — yeni bir kod-seviyeli
katman `PALETTE`e KAYDEDİLMEDEN renk ALAMAZ. Bu disiplin merkezileştirmenin
BÜTÜN amacıdır: aksi halde bir modül yine kendi ad-hoc rengini uydurabilir
ve `DEV-030`un çözdüğü sorun geri gelir.

## Tüketen modüller (`PALETTE`den okur, kendi sabitini UYDURMAZ)

| Modül | Katman(lar) | Değişti mi (DEV-030) |
|---|---|---|
| `axis/standard.py` | `AKS` | HAYIR — sabit, `AXIS_RGB` artık `color_for("AKS")`e eşit ama DEĞER aynı |
| `columns/standard.py` | `KOLON`, `KOLON-TARAMA`, `KOLON-METIN` | **EVET** — üçü artık farklı ton (somut bulgu, yukarı bakınız) |
| `sections/__init__.py` | `KESIT` | HAYIR — değer aynı |
| `stairs/__init__.py` | `MERDIVEN` | HAYIR — değer aynı |
| `furniture/groups.py` | `TEFRIS-*` (5 grup) | HAYIR — değerler aynı |

Her tüketen modül kendi `_RGB`/`.rgb` sabitini KORUR (public API kırılmaz,
örn. `stairs.STAIR_RGB` hâlâ import edilebilir) ama artık DEĞERİ
`palette.color_for(...)`den gelir — tek kaynak burasıdır.

## Ölçüm yöntemi: bilinçli basitleştirme

Mesafe düz RGB Öklid uzaklığıdır, gerçek insan algısına göre ağırlıklandırılmış
bir CIE76/CIEDE2000 DEĞİLDİR. Bu, `axis`in kesin RGB zorunluluğu gibi basit/
deterministik bir kontrol tercihiyle tutarlıdır (kök `CLAUDE.md`
"Deterministik üretim ilkesi": renk KARARI modelin değil, bu tablonun ve eşik
değerinin işidir). İleride gerçek algısal mesafeye geçilmek istenirse
`_distance` tek değişecek yerdir.

## Çakışma denetimi: EXEMPT

`collision/scene.py::COLLISION_EXEMPT` içinde — `typography` ile AYNI
gerekçe: hiç geometri üretmez, yalnızca renk sabiti tanımlar.

## Doğrulama

`python scripts/palette/selftest.py` — gerçek `PALETTE`nin kendi kurallarını
ihlal etmediği, aynı-renk ihlalinin yakalandığı (KOLON bulgusunun
regresyonu), yakın-kontrast ihlalinin yakalandığı (+ eşiğin TAM ÜZERİNDEKİ
mesafenin yanlış-pozitif ÜRETMEDİĞİ), farklı/`None` gruplar arası yakınlığın
MUAF olduğu (tefriş ailesi korunur), `color_for`in bilinen/bilinmeyen isim
davranışı, KOLON ailesinin artık aynı renk OLMADIĞI, `_distance`in elle
hesaplanabilir olduğu (3-4-5 üçgeni).

## Bilinen sınırlamalar

- **`golden_report.py` renk DEĞİŞİKLİĞİNİ YAKALAMAZ.** Ölçüm raporu
  entity/layer SAYISINI ve `modelspace_bbox`i kaydeder, katman RGB'sini
  DEĞİL — `KOLON` ailesinin üç rengi bu modülle GERÇEKTEN değiştiği halde
  (yukarı bakınız) `--golden-set` ve `--compare` "eşleşti" raporladı. Renk
  regresyonu bugün yalnızca `palette/selftest.py` ve gözle önizleme
  kontrolüyle (`preview.py`) yakalanabilir; ileride `report()`e katman
  başına ÖRNEK bir RGB alanı eklenmesi düşünülebilir (henüz yapılmadı).
- **Yalnızca kod-sahipli katmanlar.** `context.json::layers[]` kapsam
  dışıdır (yukarı bakınız).
- **RGB Öklid mesafesi**, gerçek algısal kontrastın kaba bir yaklaşıklamasıdır
  (yukarı bakınız).
- **`CONTRAST_MIN_DISTANCE` tek bir global eşiktir** — gruba özel farklı
  eşikler (örn. bazı gruplar için daha sıkı) şu an desteklenmiyor; ihtiyaç
  doğarsa `LayerColor`a bir `min_distance_override` alanı eklenebilir.
