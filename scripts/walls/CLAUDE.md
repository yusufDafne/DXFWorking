# walls modülü — DEV-014 tamamlandı

Duvar geometrisi (çift rail), birleşim çözümü, tür/kalınlık kataloğu, rail
çizim standardı ve tarama araçları. Pafta modülü gibi kendi klasöründe yaşar;
`generate_dxf.py` sadece public API'yi import eder.

## Sorumluluk

| Bileşen | Dosya | Görev |
|---------|-------|--------|
| `Wall` | `wall.py` | Merkez çizgisi + kalınlık -> rail geometrisi |
| `WallNetwork` | `network.py` | Köşe/T miter, açıklık için rail boşlukları |
| `WallCatalog` | `catalog.py` | Duvar türü -> varsayılan kalınlık/katman (ofis std.) |
| `RailDrawingStandard` / `DefaultRailStandard` / `CatalogRailStandard` | `standard.py` | Rail çizim standardı Protocol'ü + kind-farkındalı varyantlar (DEV-014) |
| `draw_wall_network` | `render.py` | DXF rail + açıklık sembolleri, `rail_standard` enjekte edilebilir |
| `RoomPolygonScanner` | `scan.py` | Oda poligonundan kenar/taslak duvar |
| `NetworkTopologyScanner` | `scan.py` | Birleşim noktası raporu |

Kapı/pencere sembolleri artık `scripts/openings/` modülündedir (`DefaultPlanOpeningStyle`
sadece oradan import edilip burada kullanılır); açılım yönü/varyant bkz.
`scripts/openings/CLAUDE.md`.

## Rail çizim standardı (DEV-014, rev-15)

Sözleşmede zaten öngörülen genişleme noktasıydı ("rail çizimi bugün TEK
yöntem"). `WallCatalog` iki türü ÖNCEDEN de tanımlıyordu (`tugla_bolme`,
`cam_duvar`) ama render tarafı `wall.kind`i hiç OKUMUYORDU — her duvar
görsel olarak aynıydı.

- **`DefaultRailStandard`** — bugüne kadarki TEK yöntem: her iki rail düz
  `LINE`, duvar türünden BAĞIMSIZ. Davranış referansıdır.
- **`CatalogRailStandard`** (yeni sistem varsayılanı) — `wall.kind`e göre:
  - `tugla_bolme` → rail'ler AYNEN çizilir + araya `ANSI31` `HATCH` eklenir
    (kolonlardaki `ColumnHatchStyle` fikriyle aynı, ama SABİT kod
    sabitleridir — `meta.column_hatch` gibi context-configurable DEĞİLDİR,
    bu bilinçli bir kapsam kararıdır).
  - `cam_duvar` → rail'ler `CAM` linetype'ıyla çizilir (`DASHED`
    KULLANILMADI — aks/zemin-altıyla AYNI çizgi türü farklı anlamları
    karıştırırdı; `axis`/`elevations` ile aynı "kendi linetype'ını kendin
    yükle" deseni, import YOK).
  - Başka/eksik `kind` → `DefaultRailStandard`e düşer.
- **Geriye dönük uyumluluk ölçülerek doğrulandı:** hiçbir mevcut proje
  (`context.json` veya golden fixture) `kind` bildirmiyordu; bu yüzden
  `CatalogRailStandard`ı sistem varsayılanı yapmak SIFIR görsel etki
  yarattı (`--golden-set` `--update` GEREKMEDEN geçti).
- **Hatch açıklığı doğru dışlar:** `wall_fill_spans(wall, openings)`,
  `gaps_for_wall` ile AYNI mantığı (ama `wall.length` üzerinde, `network`
  miter trim'i olmadan) kullanır — bir kapı bir tuğla bölmenin ortasındaysa
  tarama İKİ parçaya bölünür, kapı boşluğuna GİRMEZ.
- **Bilinen basitleştirme:** `wall_fill_spans` köşe/T miter'ini dikkate
  ALMAZ, `wall.length` (merkez çizgisi) kullanır — `scripts/collision/
  CLAUDE.md`deki "duvar ayak izi merkez çizgi + kalınlıktır, gönyelenmiş
  rail çokgeni değil" ile AYNI gerekçe. Fark yalnızca duvar UÇLARINDADIR.
- **Tarama katmanı:** `wall.layer` ile AYNIDIR (kolonlardaki sabit
  `KOLON-TARAMA` gibi ayrı bir katman YOKTUR) — `wall.layer` context'ten
  gelen VERİDİR ve duvardan duvara değişebilir, sabit bir "<layer>-TARAMA"
  çifti tanımlamak yerine aynı katmanda ayrı (hâlâ tek tek seçilebilir) bir
  `HATCH` entity'si olarak kalır.
- **`kind` şemaya eklendi (DEV-014'te kapatılan gerçek boşluk):** kod
  (`Wall.from_context`, `WallCatalog.resolve`) `kind`i HER ZAMAN okuyordu
  ama `schema/design.schema.json`nin `additionalProperties: false` olan
  `wall` tanımında YOKTU — hiçbir context.json bunu gerçekten
  KULLANAMAZDI. `validate.py::check_walls` ayrıca bilinmeyen bir `kind`
  değerini (yazım hatası) HATA sayar; aksi halde `CatalogRailStandard`
  sessizce `DefaultRailStandard`e düşerdi.
- **`Fikir 2` (katalog context'ten sürülsün) UYGULANMADI** — açık fikir
  olarak duruyor, bkz. "Bilinen sınırlar".

## Genişletilebilirlik (pafta deseni)

1. **Katalog:** `WallCatalog(DEFAULT_WALL_CATALOG)` yerine farklı sözlük
   verilir (ör. yeni yönetmelik kalınlıkları). Alt sınıf gerekmez; veri
   odaklı.
2. **Açıklık sembolü:** `draw_wall_network(..., opening_style=MyStyle())` —
   `OpeningSymbolStyle` Protocol'ü (`scripts/openings/`).
3. **Rail standardı:** `draw_wall_network(..., rail_standard=MyStandard())`
   — `RailDrawingStandard` Protocol'ü (DEV-014).

## context.json

Zorunlu alanlar değişmedi: `id`, `start`, `end`, `thickness`, `layer`.
Opsiyonel `kind` (DEV-014'te şemaya eklendi) katalog etiketi + rail çizim
standardı seçimi için kullanılır; mm değerleri yine context'te kalır
(uydurma yok — `kind` kalınlığı OTOMATİK belirlemez, `thickness` her zaman
açıkça verilir).

## Tarama (`scan.py`)

- **`RoomPolygonScanner.scan_edges`:** Her oda kenarı, kaç odada paylaşıldığı.
- **`suggest_wall_dicts`:** Basit iç/dış sezgiseli taslak — kullanıcı/validate
  onayı olmadan context'e yazılmaz.
- **`NetworkTopologyScanner.junctions`:** Validate'e eklenebilecek birleşim listesi.

İleride: DXF'ten duvar okuma (bkz. `scripts/import/CLAUDE.md`, `DEV-013`),
oda-duvar tutarlılık kontrolü.

## Doğrulama

`python scripts/walls/selftest.py` — dolgu aralığı hesaplaması elle
doğrulanabilir bir örnekte, `kind` yoksa/bilinmeyen özel-işlemeyse davranışın
DEĞİŞMEDİĞİ (regresyon testi), tuğla/cam duvarların açıklığı doğru
dışladığı ve standardın birden fazla duvarda yeniden kullanılabildiği
(yanlış-pozitif) sınanır.

## Çakışma ayak izi (rev-12)

`walls/collision.py::footprints(floor, context)`, her duvar için MERKEZ ÇİZGİ
+ KALINLIK dikdörtgeni üretir - çizimdeki GÖNYELENMİŞ rail çokgeni değil.
Gerekçe: gönye birleşim yalnızca duvar UÇLARINI etkiler ve bir tefrişin
duvara girip girmediği açısından fark yaratmaz; buna karşılık `WallNetwork`
kurmak sağlayıcıyı duvar çizim SIRASINA bağımlı kılardı, oysa çakışma
denetimi DXF üretilmeden önce saf context üzerinde çalışır.

Politika: duvar ↔ tefriş 5 mm toleransla UYARI (dolap duvara DAYANIR),
duvar ↔ kolon MUAF, duvar ↔ duvar MUAF (gönye birleşim). `kind`e göre rail
çizim FARKI (hatch/linetype) bu motoru İLGİLENDİRMEZ — motor merkez çizgi +
kalınlığa bakar, görsel sunuma değil. Ayrıntı: `scripts/collision/CLAUDE.md`.

## Bilinen sınırlar

- Eğri/çok segmentli duvar yok (tek düz segment).
- Yangın/drenaj katmanı ayrımı yok.
- **Katalog kalınlıkları kod seviyesindedir** (`DEV-014` Fikir 2,
  uygulanmadı) — `context.json`dan farklı bir yönetmelik/ofis standardı
  seçilemez, yalnızca kod tarafında `WallCatalog(farklı_sozluk)` ile
  değiştirilebilir.
- **Tarama deseni/ölçeği context'ten AYARLANAMAZ** (kolonlardaki
  `meta.column_hatch` gibi) — sabit `ANSI31`/`1.5`. 1:50 ve 1:100'de aynı
  desen okunaklı olmayabilir (kolonlarınkiyle AYNI açık soru).
- `wall_fill_spans` köşe/T miter'ini dikkate almaz (bkz. yukarıdaki not).
