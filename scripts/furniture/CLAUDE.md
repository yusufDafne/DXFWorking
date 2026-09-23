# furniture modülü (tefriş) — DEV-009 tamamlandı

Konut tefriş kataloğu, DXF blok tanımları ve çizimi. `pafta` modülü gibi kendi
klasöründe yaşar; `generate_dxf.py` yalnızca public API'yi import eder.

## Sorumluluk

| Bileşen | Görev |
|---------|-------|
| `FurnitureSpec` | Bir tefriş tipinin katalog kaydı (ölçü + çizim fonksiyonu) |
| `FurnitureCatalog` | Tip → spec; veri odaklı, alt sınıf gerekmez |
| `FurnitureGroup` | İşlevsel grup: kendi layer'ı + kahverengi tonu |
| `FurnitureItem` | Bir YERLEŞİM (proje verisi: konum + rotasyon) |
| `FurnitureBlocks` | DXF `BLOCK` tanımlarını belgeye kaydeder |
| `FurnitureRenderer` | Yerleşimleri `INSERT` olarak çizer |
| `FurnitureSchedule` | Salt-okunur tefriş listesi (`OpeningSchedule` deseni) |

## Kapı kimin? — `openings/`, tefrişin DEĞİL

Kullanıcı bunu sordu; **endüstri standardı nettir: kapı bir duvar açıklığıdır,
tefriş değildir.**

- **IFC (buildingSMART):** `IfcDoor` ve `IfcWindow` birer `IfcBuildingElement`
  olup bir duvardaki `IfcOpeningElement`i doldurur. Mobilya ise tamamen ayrı
  bir daldır: `IfcFurnishingElement`.
- **CAD layer standartları (AIA / NCS / ISO 13567):** kapı `A-DOOR`, duvar
  `A-WALL`, mobilya `A-FURN`. Kapı mimari kabuk grubunda, tefriş ayrı bir
  grupta yer alır.
- **Pratik gerekçe:** Kapı geometrisi HOST DUVARA bağımlıdır — duvar
  kalınlığı, duvar üzerindeki konum ve rail boşluğu olmadan çizilemez. Tefriş
  ise oda içinde serbest duran bir nesnedir.

**Sonuç:** Bu projede kapı/pencere zaten doğru yerdedir — `openings/` açıklık
verisi ve sembol stilini, `walls/` ise rail boşluğunu sahiplenir. Tefriş
modülü kapı çizmez ve kapı verisine dokunmaz.

Tek bağlantı noktası şudur: **kapı açılım alanı (swing) tefriş yerleşimini
kısıtlar.** Bu bir *doğrulama* konusudur, sahiplik konusu değildir. rev-12'de
uygulandı: denetim `scripts/collision/` motoruna aittir; bu modülün tek
sorumluluğu **kendi ayak izini** üretmektir — bkz. "Çakışma ayak izi".

## Çakışma ayak izi (rev-12)

`furniture/collision.py::footprints(floor, context)`, her yerleşim için
dönmüş bir dikdörtgen `CollisionShape` üretir. Ölçü **katalogdan**, konum ve
rotasyon **context'ten** gelir; ekleme noktası sol-alt köşedir ve dönme o
nokta etrafındadır — yani ayak izi, çizilen blokla **birebir aynı yerdedir**.
İkinci bir geometri kopyası tutulmaz.

Motor bu modülü import ETMEZ; bağımlılık terstir (bkz.
`scripts/collision/CLAUDE.md`). Politika: tefriş ↔ tefriş / kolon / kapı
sektörü ve oda dışına taşma **HATA**, tefriş ↔ duvar 5 mm toleransla
**UYARI** (dolap duvara dayanır).

## Tefriş HER ZAMAN blok olarak çizilir

Her tefriş tipi bir `BLOCK` TANIMIDIR, her yerleşim bir `INSERT`tir
(kullanıcı talebi). Sonuçlar:

- AutoCAD'de tefriş **tek seçilebilir nesnedir**, yanlışlıkla parçalanmaz.
- Bir tipin biçimi **tek tanımdan** değişir; 4 sandalye tek tanımdan gelir.
- Dosya şişmez: `golden/tefris_kolon` referansında 19 tanım → 23 `INSERT`.

Blok adı `TEFRIS_<TIP>` (örn. `TEFRIS_KOLTUK_3LU`). Blok içindeki geometri
layer `0`da BYLAYER bırakılır; rengi **`INSERT`in layer'ı** belirler, böylece
aynı tanım farklı grupta da kullanılabilir.

**Yerel orijin:** Blok tanımı, elemanın **sol-alt köşesi** (0,0) olacak şekilde
çizilir. `position` bu noktadır ve `rotation` bu nokta etrafında döner.

## Gruplar ve renkler

Renkler **kahverengi ailesindedir ve birbirine yakın tonlardır** (kullanıcı
talebi: "çok zıt renkler kullanma"). Tefriş, duvar/aks gibi okunması gereken
katmanla yarışmaz.

| Grup | Layer | RGB | İçerik |
|------|-------|-----|--------|
| OTURMA | `TEFRIS-OTURMA` | 139,94,60 | koltuk 3'lü/2'li, berjer, sehpa, TV ünitesi |
| YEMEK | `TEFRIS-YEMEK` | 161,120,79 | yemek masası (4/6), sandalye |
| YATAK | `TEFRIS-YATAK` | 120,86,66 | tek/çift yatak, gardırop, komodin |
| MUTFAK | `TEFRIS-MUTFAK` | 150,111,94 | tezgah, ocak, evye, buzdolabı, bulaşık mak. |
| ISLAK | `TEFRIS-ISLAK` | 131,120,106 | lavabo, klozet, duş, küvet, çamaşır mak. |

Layer'lar `ensure_furniture_layers(doc)` ile **kod tarafında** oluşturulur —
renk context.json'dan alınmaz (`ensure_axis_layer` deseni).

## Public API

```python
from furniture import (FurnitureBlocks, FurnitureCatalog, FurnitureItem,
                       FurnitureRenderer, ensure_furniture_layers)

catalog = FurnitureCatalog()                       # varsayilan set
FurnitureBlocks.ensure(doc, catalog, used_types)   # BLOCK tanimlari + layer'lar
items = [FurnitureItem.from_context(d) for d in floor["furniture"]]
FurnitureRenderer.draw(msp, items, catalog)        # INSERT'ler
```

`context.json`:

```json
"furniture": [
  { "id": "f_koltuk3", "type": "koltuk_3lu", "position": [500, 7000], "rotation": 0 }
]
```

## Invariant'lar ve doğrulama

- **Ölçü katalogdan, yerleşim context'ten.** Katalog ölçüleri ofis/katalog
  standardıdır (çizim sabiti, `WallCatalog` gibi); konum/rotasyon ise PROJE
  VERİSİDİR ve uydurulmaz.
- **Bilinmeyen tip üretimi durdurur** — `FurnitureCatalog.get` katalogdaki
  tipleri listeleyen bir `KeyError` fırlatır, sessizce atlamaz.
- Her `INSERT` tanımlı bir bloğa işaret eder; `golden_report.py`nin
  `block_references` kuralı bunu doğrular.
- Tefriş layer'ları `golden_report.py`de kod-sahipli sayılır (`AKS` gibi),
  context'te bildirilmeleri gerekmez.

## Sınır

Tefriş **kapı/pencere çizmez** (yukarıya bakınız), oda geometrisini veya pafta
kompozisyonunu sahiplenmez. `counters[]` (mutfak tezgahı) hâlâ
`generate_dxf.py` içinde ad-hoc çizilmektedir — bu modüle devredilmesi ayrı
bir karardır.

## Bilinen sınırlamalar

- **Çakışma kontrolü rev-12'de EKLENDİ** (yukarıya bakınız); aşağıdaki iki
  boşluk kapandı: tefrişin duvara/kolona/başka tefrişe/kapı açılım alanına
  girmesi ve odanın dışına taşması artık `validate.py` içinde üretimi
  durdurur. Kalan sınırlama: kapı açılım **yönü** schema'da olmadığı için yay
  varsayılan tarafa çizilir (`DEV-016`).
- `counters[]` ile bu modül arasında **çifte sorumluluk** vardır: mutfak
  tezgahı hem `counters[]` poligonuyla hem `mutfak_tezgahi` tipiyle
  çizilebilir. Tek yol seçilmelidir.
- Katalog ölçüleri tek bir tipik set içindir; ölçü varyantı (örn. 160 yerine
  180 yatak) için katalog sözlüğü değiştirilmelidir, context'ten ölçü
  verilemez.
- Blok öznitelikleri (`ATTRIB`) kullanılmıyor; tefriş adı çizimde görünmez.
