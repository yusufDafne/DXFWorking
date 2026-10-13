# northarrow modülü (kuzey oku) — DEV-025 tamamlandı

Kat paftalarına standart bir kuzey yön sembolü çizer. rev-17'de AYNI
DEV-025 talebinin ikinci parçası olarak `scripts/pafta::ScaleBar` (grafik
ölçek çubuğu) da eklenmişti; kullanıcı geri bildirimiyle rev-18'de
KALDIRILDI (bkz. `docs/development/DEVELOPMENT_HISTORY.md` HD-012 ve
`scripts/pafta/CLAUDE.md`). Bu modül ve kuzey oku bundan etkilenmedi.

## Neden ayrı bir modül (kullanıcı kararı)

Kullanıcı açıkça: *"kuzey oku için standart bir tasarım belirle, daha
sonra tasarım değişikliğine gidildiği zaman entegrasyon zor olmasın."*
Bu, projenin zaten kurulu `RailDrawingStandard` (bkz.
`scripts/walls/standard.py`) desenini DOĞRUDAN çağırır: **Protocol +
değiştirilebilir varsayılan implementasyon.** `NorthArrowStyle` tek bir
`draw(...)` sözleşmesi tanımlar; `DefaultNorthArrowStyle` bugünkü standart
görseldir. Yarın ofis farklı bir sembol isterse (örn. yıldızlı pusula), YENİ
bir `NorthArrowStyle` yazılır ve `NorthArrow(style=...)` ile enjekte edilir
— `NorthArrow.draw` çağrı sözleşmesi DEĞİŞMEZ, `generate_dxf.py` tek satır
değişir. Bu ölçüde küçük bir sembol için ayrı modül "aşırı mühendislik"
gibi görünebilir, ama kullanıcının AÇIKÇA istediği "kolay entegrasyon"
garantisi, `walls`/`elevations` ile AYNI izole-modül + Protocol disiplinini
gerektiriyordu.

## Sorumluluk

| Sınıf/fonksiyon | Görev |
|---|---|
| `rotate_point` | "Yukarı" (+Y) referansından SAAT YÖNÜNDE açı ile nokta döndürme (pusula/kerteriz konvansiyonu — normal matematik açısıyla KARIŞTIRILMAZ) |
| `NorthArrowStyle` | Protocol: `draw(msp, center, radius, angle_deg, layer, text_layer, text_height)` |
| `DefaultNorthArrowStyle` | Bugünkü standart görsel: daire + tek üçgen ibre + "K" etiketi |
| `NorthArrow` | Ölçeğe göre türetilmiş boyut (`to_modelspace`) + stil enjeksiyonu |

## Veri: `meta.north_angle` — verilmezse ok HİÇ çizilmez

Derece, **saat yönünde**, paftanın "+Y" ("yukarı") referansından GERÇEK
KUZEY'e ölçülür (`angle=0` → kuzey yukarıda, `angle=90` → kuzey sağda).
Bu proje verisidir (binanın gerçek yönü) ve context.json'da yoksa
UYDURULMAZ — `generate_dxf.py`, `north_angle is None` ise `NorthArrow`
nesnesini hiç OLUŞTURMAZ, hiçbir çizim yapılmaz (schema'da opsiyonel).

## Yerleşim (NEREYE çizileceği bu sınıfın işi DEĞİLDİR)

`NorthArrow.draw(msp, center, angle_deg)` sadece VERİLEN merkeze çizer;
konum kararı `generate_dxf.py`nindir. Bugünkü yerleşim: her kat paftasının
**KUZEY (üst) kenarındaki padding bölgesinde, katın TAM ORTASINDA**
(`dx + floor_width/2`) — aks baloncuklarından kasıtlı olarak uzak durmak
içindir: bu projede strüktürel akslar tipik olarak kenarlarda/uçlarda
bulunur (dış cephe, çekirdek sınırı), tam ortada NADİREN aks olur. Güney ve
batı kenarları zaten ölçü zinciri + aks baloncuklarıyla DOLU olduğu için
(bkz. `scripts/dimensions/CLAUDE.md`, `scripts/axis/CLAUDE.md`) kuzey/doğu
kenarları seçildi. **Bilinen sınırlama:** bu, aks konumlarıyla piksel-kesin
çakışmama GARANTİSİ değildir — tam ortada gerçekten bir aks olan bir
projede görsel çakışma olabilir; `pafta::CONTENT_PADDING`in kendisi de
benzer bir çakışmayı (rev-13, aks baloncuğu ↔ başlık kutusu) KABA bir
padding artışıyla çözmüştü, bu modül de aynı sınıf pragmatik yaklaşımı
izler (per-konum kaçınma yerine "güvenli bölge" seçimi).

## Public API

```python
from northarrow import NorthArrow, NorthArrowStyle, DefaultNorthArrowStyle, rotate_point

arrow = NorthArrow(scale)          # varsayilan stil
arrow.draw(msp, center, angle_deg)
```

## Çakışma denetimi

`COLLISION_EXEMPT` listesinde (`axis`/`typography` ile AYNI gerekçe): sabit
bir pafta sembolüdür, proje geometrisiyle (oda/duvar/tefriş) hiçbir mekansal
ilişkisi yoktur.

## Doğrulama

`python scripts/northarrow/selftest.py` — `rotate_point` elle hesaplanabilir
4 kardinal nokta, yarıçapın ölçekle DOĞRUSAL türediği (1:100 = 1:50'nin 2
katı), varsayılan stilin varlık sayısı, ÖZEL bir stilin enjekte
edilebildiği (sahte stil test çiftiyle).

## Bilinen sınırlamalar

- **Aks baloncuklarıyla piksel-kesin çakışmama garantisi yok** (bkz.
  "Yerleşim").
- **Elevations/sections'a kuzey oku çizilmez** (kullanıcı isteği örtük
  kaldı, ama mantık açık: kuzey bir PLAN/vaziyet kavramıdır, düşey bir
  görünüşte/kesitte yönü göstermenin standart bir karşılığı yoktur).

## Muhakeme katkısı (DEV-048)
**Rol:** gerekçeli muaf (`reasoning/registry.py::REASONING_EXEMPT`, DEV-067). **Gerekçe (düşünüldü, ölçüm/kural vermez):** yonelim merceginin girdisi meta.north_angle verisidir, bu modulun kodu degil (reasoning_report meta'dan okur); kuzey oku yalniz cizimdir.
**Sağlayıcıya geçiş:** bu modül için bir veçhe doğarsa modül `REASONING_EXEMPT`ten çıkar, `scripts/northarrow/reasoning.py` (rol + ölçüm beyanı;
veçhe kaydı lens paketinde) yazılır ve `REASONING_PROVIDERS`a girer — kural ve izinler: `docs/agents/KNOWLEDGE_ENGINEER_AGENT.md`.

## DEV-074: kuzey sözleşmesi
Vaziyet planında kuzey daima yukarı; proje planının **kuzeye en yakın cephesi** paftanın üst kenarına paraleldir ve plan paftasındaki ok vaziyet planına göre projenin yönünü gösterir. Dik açılı binada cepheler 90° arayla olduğundan `meta.north_angle` ∈ **[−45°, +45°]** (`NORTH_HALF_RANGE_DEG`, geometriden türer; ölçüm eşiği değildir). `normalize_north_angle`: eşdeğer açı (−180, +180] (350 → −10). `check_north_convention(meta)` aralık dışında `validate.py` HATASI verir ("proje sessizce döndürülmez, karar sizin"); alan yoksa sessiz kalır (ok çizilmez, yön uydurulmaz). Yerleşim planını analiz eden altyapı YOKTUR: yön yalnız açıyla bildirilir. Çizim (`NorthArrow`) ve yönelim veçhesinin hesabı DEĞİŞMEDİ (ham açı eşdeğer olduğundan kullanılmaya devam eder). `CONTRACT_VERSION` 1.0 → 1.1. Vaziyet paftası: `DEV-024` (arsa verisi gelince). Test: `selftest.py::check_north_convention_dev074` (sınır ±45 / ±45,01, normalize, 5 kasıtlı bozma).
