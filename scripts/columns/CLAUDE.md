# columns modülü — DEV-010 tamamlandı

Parametrik kolon kesiti, **tarama (hatch)** ve aks kesişimi ilişkisi. `axis`
modülünü TÜKETİR; aks/duvar/oda sorumluluğunu üstlenmez.

## Sorumluluk

| Bileşen | Görev |
|---------|-------|
| `ColumnSection` | Kesit: genişlik/derinlik, `rect` veya `circle` |
| `ColumnSectionCatalog` | Kesit adı → kesit; veri odaklı |
| `Column` | Bir kolon yerleşimi (merkez + kesit + dönme + opsiyonel ad) |
| `ColumnHatchStyle` | Tarama deseni/ölçeği — **dinamik**, varsayılanı var |
| `ColumnLabelStyle` | Kolon adı gösterimi — **varsayılan KAPALI** |
| `ColumnRenderer` | Kontur + tarama (+ istenirse ad) |
| `ColumnGrid` | Kat bazında kolon kümesi + aks kesişim raporu |

## Tarama — dinamik, ama varsayılanı var

Kullanıcı talebi: kolonlar taralı olacak, tarama oranı dinamik olacak ama bir
varsayılanı bulunacak.

```python
ColumnHatchStyle()            # ANSI33, olcek 3.0, aci 0
```

`context.json` ile değiştirilir (alt sınıf gerekmez):

```json
"meta": { "column_hatch": { "pattern": "ANSI31", "scale": 1.5, "angle": 45 } }
```

`enabled: false` taramayı tamamen kapatır. Tarama ayrı bir layer'dadır
(`KOLON-TARAMA`), böylece baskıda/görüntüde kontur ile taramanın ağırlığı
bağımsız ayarlanabilir.

## Kolon isimlendirme — bugün kapalı, altyapı hazır

Kullanıcı kolonları **aks birleşim noktalarıyla** ifade etmeyi tercih ediyor,
bu yüzden ad **çizilmez**. Yine de ileriye dönük olarak:

- `Column.name` alanı vardır ve context'ten (`columns[].name`) taşınır.
- `ColumnLabelStyle.enabled` varsayılan `False`.
- Açmak için **kod değişikliği gerekmez**:

```json
"meta": { "column_label": { "enabled": true, "height": 200 } }
```

Ayrıca `ColumnGrid.on_axis_report(...)` her kolonun hangi aks kesişimine
oturduğunu (örn. `A1`) **salt-okunur** olarak raporlar — kullanıcının tercih
ettiği "aks kesişimiyle ifade etme" yaklaşımının veri karşılığı budur. Bu
rapor kolon konumunu değiştirmez.

## Public API

```python
from columns import (ColumnGrid, ColumnHatchStyle, ColumnLabelStyle,
                     ColumnSectionCatalog, ensure_column_layers)

hatch = ColumnHatchStyle.from_context(meta.get("column_hatch"))
label = ColumnLabelStyle.from_context(meta.get("column_label"))
ensure_column_layers(doc, hatch, label)
ColumnGrid.from_context(floor["columns"], ColumnSectionCatalog(), hatch, label).draw(msp)
```

`context.json` — kesit ya katalogdan ya da doğrudan ölçüyle:

```json
"columns": [
  { "id": "s1", "position": [0, 0], "section": "S40x40" },
  { "id": "s2", "position": [6000, 0], "width": 350, "depth": 700, "rotation": 30 }
]
```

`position` kolonun **MERKEZİDİR** (tefrişte sol-alt köşedir — bilinçli fark:
kolon simetrik bir taşıyıcıdır, aks kesişimine merkezinden oturur).

Katalog: `S30x60`, `S40x40`, `S40x80`, `S50x50`, `S60x60`, `D40`, `D50`.

## Çizim sırası

Kolonlar tefrişten **ÖNCE** çizilir (`generate_dxf.py::draw_floor_sheet`) —
taşıyıcı eleman tefrişin altında kalmaz.

## Invariant'lar ve doğrulama

- **Konum ve kesit uydurulmaz**; ikisi de context'ten gelir.
- Bilinmeyen kesit adı üretimi durdurur (`KeyError`, katalogdaki kesitleri
  listeler). Kesit ölçüsü pozitif olmalıdır.
- Layer'lar (`KOLON`, `KOLON-TARAMA`, `KOLON-METIN`) kod tarafında sabit RGB
  ile oluşturulur (`ensure_axis_layer` deseni); renk context'ten alınmaz.
  **rev DEV-030'dan itibaren renk `scripts/palette::PALETTE`in TEK
  kaynağından gelir** (`COLUMN_RGB`/`COLUMN_HATCH_RGB`/`COLUMN_TEXT_RGB`,
  `columns/standard.py`) ve üçü artık BİRBİRİNDEN FARKLI tondadır — DEV-030
  ÖNCESİ üçü de AYNI `COLUMN_RGB`yi paylaşıyordu (kontur ile tarama
  ayrışmıyordu); bu somut bulgu `palette` modülünün kurulma nedenlerinden
  biriydi, bkz. `scripts/palette/CLAUDE.md`.
- `golden_report.py` bu layer'ları kod-sahipli sayar. **Ölçüm raporu renk
  değişikliğini YAKALAMAZ** (yalnızca entity/layer sayısı + bbox) — DEV-030
  bu üç layer'ın rengini değiştirdiği halde `--golden-set`/`--compare`
  "eşleşti" raporladı; ayrıntı `scripts/palette/CLAUDE.md` "Bilinen
  sınırlamalar".

## Sınır

Kolon aks üretmez, duvar/oda geometrisini değiştirmez. Aks kesişim eşlemesi
yalnızca **rapordur** — kolonu aksa otomatik oturtmaz.

## Çakışma ayak izi (rev-12)

`columns/collision.py::footprints(floor, context)`, her kolon için ayak izini
üretir. Dikdörtgen kesitte doğrudan `Column.corners()` kullanılır — yani
denetlenen çokgen, **çizilen konturun ta kendisidir**; ikinci bir kopya
tutulmaz ve çizim ile denetimin ayrışması (bu modülde en kolay kaçırılacak
hata) yapısal olarak engellenir. Dairesel kesit 16 parçalı çokgenle
yaklaşılır (gerçek daireden biraz küçüktür).

Politika: kolon ↔ tefriş, kolon ↔ kolon ve kolon ↔ kapı açılım sektörü
**HATA**; kolon ↔ duvar ve kolon ↔ oda **MUAF**. Ayrıntı:
`scripts/collision/CLAUDE.md`.

## Bilinen sınırlamalar

- **Kolon/tefriş ve kolon/kolon çakışması rev-12'de EKLENDİ** (bkz. "Çakışma
  ayak izi"); artık üretimi durdurur. Kolon ↔ duvar ve kolon ↔ oda bilinçli
  olarak **muaftır**: kolonun duvarın içinde ya da bir odanın ortasında
  durması TASARIMDIR, hata değildir.
- **Katlar arası düşey hizalama kontrol edilmez.** Üst katta kolon kayarsa
  veya kaybolursa hata verilmez; bu bilinçli bir boşluktur (karar alınmadı).
- Kesit küçültme (üst katta 60x60 → 50x50) **otomatik değildir**; her katın
  kolonu ayrı bildirilmelidir.
- Dairesel kolon taraması `add_arc` kenar yoluyla yapılır; çok küçük
  yarıçaplarda desen okunmayabilir.
- `validate.py` kolon verisini geometrik olarak denetlemez (yalnızca schema).
