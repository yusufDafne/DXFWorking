# axis modülü (aks sistemi) — Faz 2 + DEV-015 tamamlandı

Kesikli aks çizgisi, teğetli baloncuk, cephelere izdüşüm, aks ölçü zinciri,
**kısmi/ara aks** ve **kolon rasteri kapsama raporu**.

## Sorumluluk

| Dosya | Görev |
|-------|-------|
| `standard.py` | `AxisDrawingStandard`, layer/linetype/RGB, `ensure_axis_layer` |
| `axis.py` | `Axis` — etiket, konum, `extent` (kısmi uzanım) |
| `naming.py` | `check_labels` — etiket kuralı (`1'` evet, `1A` hayır) |
| `grid.py` | `AxisGrid` — çizim ve ölçü zinciri |
| `report.py` | `AxisCoverageReport` — aks'sız kolon hizaları (salt okunur) |
| `selftest.py` | kısmi aks, zincir üyeliği, etiket kuralı, kapsama testleri |

## Veri ve standart

Aks konumları `context.json`daki `grid`ten okunur; **çizim sabitleri kod
seviyesindedir** ve context'ten alınmaz. Tek istisna, `generate_dxf.py`nin
ölçü yığınına göre hesaplayıp verdiği `extension` ve `dimension_offset`
değerleridir — onlar da projeden değil, `dimensions` modülünden gelir.

## Ara aks etiketi: `1'` — karar ve gerekçe (rev-13)

**`1A` YASAKTIR.** Gerekçe tercih değil, **çatışma**:

- Yatay aks ailesi zaten `A`, `B`, `C` ile etiketlenir → `1A` "1 ve A
  akslarının kesişimi" gibi okunur.
- `columns::ColumnGrid.on_axis_report` bir kolonu tam olarak bu biçimde (`B2`)
  adlandırır. İki gösterim aynı dizede çarpışırdı.
- Kesme işareti Türkiye/Avrupa pratiğinde de yaygın olandır.

Kural **mekaniktir**: `naming.check_labels` düşey aksların numerik, yatay
aksların alfabetik olmasını ve her ikisinin tek kesme işaretiyle ara aks
olabilmesini arar; aynı etiketin iki kez kullanılması da hatadır. `validate.py`
bunu üretimden önce çalıştırır.

## Kısmi aks (`extent`)

Bir aks artık yapının tamamını kat etmek zorunda değildir. `extent` verilirse:

- Aks yalnızca o aralıkta uzanır ve **tam uzama yerine** küçük bir
  `partial_extension` kadar taşar — tam uzama verilseydi yapının dışında bir
  yere işaret ediyormuş gibi okunurdu.
- Baloncuklar aksın **kendi uçlarına** gelir.
- **Ulaşmadığı kenarın ölçü zincirine GİRMEZ.** Aksi halde zincir, orada
  olmayan bir aksı ölçüyormuş gibi görünürdü.

Cephe izdüşümünde `extent` **uygulanmaz**: cephe o aksı yine de görür.

## Kolon rasteri kapsama raporu (salt okunur)

`AxisCoverageReport.from_columns(...)`, aks'sız kalan kolon hizalarını
bildirir ve `generate_dxf.py` bunu UYARI olarak basar. **Aks EKLEMEZ**,
context'e yazmaz — kök `CLAUDE.md` türetilmiş geometrinin context'e
yazılmasını yasaklar; karar kullanıcınındır.

`columns::on_axis_report` bunun tersidir ("hangi kolon hangi kesişimde");
ikisi birlikte kolon↔aks çapraz kontrolünü tamamlar.

## Ölçü zinciriyle ilişki (çapraz nokta)

Aks ölçü zinciri ile `dimensions` yığını **aynı kenarı paylaşır**. Mimari
sıra: içeride en ayrıntılı ölçü, dışarıda en kaba → **aks zinciri en dışta**,
baloncuklar ondan da dışarıda. Bu modül `dimensions`ı import etmez; ofset ve
uzama `generate_dxf.py` tarafından verilir.

## Aks ölçü zinciri: ardışık mesafe + en-uçtaki-toplam (rev-18)

Kullanıcı kararı: "akslar arası mesafeler ve ikinci olarak en uçtaki
aksların arasındaki mesafeyi vermeli." `_dim_chain_x`/`_dim_chain_y`, bir
kenarda **2'den FAZLA** aks varsa, ardışık-mesafe zincirinin (mevcut
davranış) YANINA `[min(xs), max(xs)]` noktalarından tek-segmentli bir
"toplam" zinciri EKLER; TAM 2 aks varsa bu iki zincir ZATEN aynı sayıyı
verir ve toplam zincir tekrar ÇİZİLMEZ (`_total_offset`). Toplam zincirin
baseline'ı, aksın KENDİ baloncuk/uzama bölgesinin (`extension +
bubble_radius`) `total_dimension_clearance` kadar ÖTESİNDE durur — aksi
halde (örn. varsayılan `dimension_offset`i basitçe 2 katına çıkarmak)
üçüncü/dördüncü aks varlığında toplam zincirin ucu bubble'ın İÇİNE
girebilirdi (elle doğrulandı: `extension+bubble_radius=1650`,
`total_dimension_clearance=300` ile toplam ofset 1950'dir).

**Katman düzeltmesi (rev-18):** `ezdxf` 1.4.4'ün `add_linear_dim` render
motoru (`BaseDimensionRenderer.add_line`, `render/dim_base.py`) katman
dahil BİRLEŞMİŞ `attribs` sözlüğünü hesaplayıp sonra KULLANMADAN atıyor;
geometri bloğuna orijinal (katmansız) `dxfattribs`i geçiriyor — sonuç, ölçü
ve uzatma çizgilerinin DIMENSION'ın kendi katmanından BAĞIMSIZ olarak hep
`"0"` katmanında çizilmesidir (ok/metin bu hatadan MUAFTIR, onların kod
yolu birleşmiş sözlüğü doğru kullanır). Kullanıcı şikayeti buydu: "aks
çizgileri ölçüleri aks çizgileri ile aynı layerda olmalı." Düzeltme
`scripts/dimensions/linear.py::LinearDim.render`dedir (render SONRASI,
geometri bloğundaki `Defpoints` DIŞINDAKİ her varlığın katmanı zorla
`style.layer`e çekilir) — kütüphane kaynağı değiştirilemediği için bu
modülün DEĞİL, `dimensions`ın sorumluluğundadır, ama etkisi burada da
görünür (AKS zinciri de `LinearDim` üzerinden render edilir).

## Public API

- `AxisGrid(vertical_axes, horizontal_axes, text_height, standard=None)`
- `AxisGrid.draw_on_floor(...)` / `draw_on_elevation(...)` — çağrı sözleşmesi
  korunmuştur.
- `Axis`, `axes_from_context`, `check_labels`, `AxisCoverageReport`
- `ensure_axis_layer(doc, standard=None)`

## Invariant'lar

- Aks konumları bildirilen grid verisinden gelir; sıralama pozisyona göre
  **deterministiktir**.
- Aks çizgisi baloncuk yarıçapı kadar önce biter, baloncuğun içine girmez
  (`golden_report` `axis_bubbles` kuralı bunu denetler).
- Aks layer'ı context'ten stil almaz; `AxisDrawingStandard` kod sahibidir.
- Aks ölçü metni gerçek DXF linear dimension'dır ve tam sayı cm gösterir.
- Floor ve elevation aynı grid verisini kullanır; elevation yalnızca bildirilen
  `axis_source` ailesini çizer.

## Doğrulama

`python scripts/axis/selftest.py` — kısmi aks uzanımı, ölçü zinciri üyeliği,
etiket kuralının beş negatif vakası, kapsama raporunun yanlış-pozitif testi
ve (rev-18) en-uçtaki-toplam zincirin DIMENSION sayısı + bubble-clearance
kontrolü.

## Bilinen sınırlamalar

- **Aks yalnızca eksen hizalıdır** (düşey veya yatay); eğik aks desteklenmez.
- Kısmi aks cephe izdüşümünde uygulanmaz.
- Aks sıklığı **otomatik belirlenmez**; kapsama raporu yalnızca eksik hizaları
  bildirir, aks önermez veya eklemez.
- Ara aksın `extent`i ile ana aksların kesişip kesişmediği kontrol edilmez.
