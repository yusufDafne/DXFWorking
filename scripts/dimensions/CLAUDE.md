# dimensions modülü (ölçülendirme) — DEV-003 + DEV-017 tamamlandı

Gerçek DXF ölçü varlıkları, kademelendirilmiş ölçü yığını ve kat
geometrisinden ölçü **türetme**.

## Sorumluluk

| Dosya | Görev |
|-------|-------|
| `style.py` | `DimensionStyle`, `format_dimension_cm` — metin **her zaman tam sayı cm** |
| `linear.py` | `LinearDim` — tek bir gerçek DXF `LINEAR DIMENSION` |
| `chain.py` | `DimensionChain`, `merge_ordinates` — ardışık nokta çiftleri |
| `layout.py` | `ChainLayout` (sınır + **üst üste binme yasağı**), `ChainStack` (kademelendirme) |
| `derive.py` | `FloorOrdinates` — kat geometrisinden ordinat türetme |
| `plan.py` | `DimensionSettings`, `FloorDimensionPlanner` — sunum ayarı ve çizim |
| `selftest.py` | elle hesaplanabilir değerler + negatif testler |

## Kararın özü: ölçü TÜRETİLİR, elle bildirilmez

Bir ölçü sayısı **tasarım verisi değildir, geometrinin ölçüsüdür.** Duvar
koordinatı zaten `context.json`dadır; ölçüyü ayrıca elle yazmak aynı bilgiyi
iki yerde tutmak olurdu ve kaçınılmaz olarak ayrışırdı — duvar taşınır, ölçü
metni eski kalır. Bu, projenin "bayat satır" sorununun geometri hâlidir.

Türetme, kök `CLAUDE.md`'deki **"ölçü uydurulmaz"** yasağını DELMEZ: sayı
uydurulmuyor, context geometrisinden ölçülüyor.

Buna karşılık **hangi kenarın hangi kademede ölçüleneceği bir SUNUM
kararıdır** ve `meta.dimensions` ile gelir. Varsayılan **KAPALIDIR**.

## Üç kademe (içten dışa kabalaşır)

| Kademe | Ne ölçülür |
|--------|------------|
| `aciklik` | cephedeki kapı/pencere kenarları |
| `mahal` | dik duvarların **YÜZLERİ** → net mahal ölçüsü + duvar kalınlığı |
| `toplam` | yapının **dıştan dışa** ölçüsü |

Üçü de **aynı ordinatlarda** başlayıp biter; mimari bir ölçü yığınının
görünümü budur. `toplam`, merkez çizgisi değil **dış yüz**tür: dış duvarın
merkez çizgisi 0'da ve kalınlığı 250 ise yapı −125'ten başlar. Merkezden
merkeze ölçü **aks zincirinin** işidir ve onu `axis` çizer.

## Çapraz nokta: ölçü yığını ↔ aks

İkisi **aynı kenarı** paylaşır. Mimari sıra: içeride en ayrıntılı ölçü,
dışarıda en kaba — yani **aks zinciri EN DIŞTA** durur ve baloncuklar ondan da
dışarıdadır.

İki modül birbirini **import etmez**. Yığının derinliğini yalnızca bu modül
bilir (`stack_depth`), baloncuğun yarıçapını yalnızca `axis` bilir; bu yüzden
yarıçap `required_axis_extension(minimum, bubble_radius)`a **parametre olarak
verilir** ve `generate_dxf.py` ikisini birleştirir.

rev-13'te bu ilk denemede yanlış yapıldı ve baloncuk en dıştaki zincirin
üzerine bindi; çizimde görüldü ve yarıçap hesaba katıldı.

## Tolerans: alan değil DERİNLİK / mesafe

- `merge_ordinates`: 1 mm içindeki iki ordinat **tek noktaya** iner. Olmazsa
  "0" metinli, sıfır uzunluklu ölçüler üretilirdi.
- `ChainLayout.verify_no_overlap`: aynı yönde iki zincir aynı baseline'a
  oturamaz. rev-13'ten önce `ChainLayout` yalnızca sınır kontrolü yapıyordu ve
  üst üste binen iki zincir **sessizce** okunamaz bir çizim üretirdi (tek
  tüketici aks modülü olduğu ve o da kenar başına tek zincir çizdiği için
  sorun görünmüyordu).

## Katman

Aks ölçü zinciri `AKS` katmanındadır (onu aks modülü sahiplenir); mahal/açıklık
zincirleri projenin bildirdiği `OLCU` katmanına yazılır.

**ezdxf katman hatası ve düzeltmesi (rev-18):** `ezdxf` 1.4.4'ün
`add_linear_dim` render motoru (`render/dim_base.py::BaseDimensionRenderer.
add_line`), katman dahil BİRLEŞMİŞ `attribs` sözlüğünü hesaplayıp
KULLANMADAN atıyor — geometri bloğuna (ölçü + uzatma çizgileri) orijinal
katmansız `dxfattribs`i geçiriyor, sonuç bu çizgilerin DIMENSION'ın kendi
katmanından BAĞIMSIZ olarak hep `"0"` katmanında çizilmesi (ok/metin bu
hatadan MUAFTIR). `LinearDim.render` (`linear.py`) render SONRASI bir
düzeltme uygular (`_fix_geometry_block_layer`): geometri bloğundaki
`Defpoints` DIŞINDAKİ her varlığın katmanı zorla `style.layer`e çekilir.
Kütüphane kaynağı değiştirilemediği için (proje dışı dizin) bu, kalıcı bir
workaround'dur — `ezdxf` güncellenirse yeniden test edilmelidir
(`scripts/dimensions/selftest.py::check_rendered_layer`).

## Public API

```python
from dimensions import DimensionSettings, FloorDimensionPlanner

settings = DimensionSettings.from_context(context)   # meta.dimensions
FloorDimensionPlanner(floor, settings).draw(msp, dx)
```

## Invariant'lar ve doğrulama

- Kaynak koordinatlar mm'dir; cm dönüşümü **yalnızca** ölçü metninde yapılır.
- Ölçü entity'si gerçek DXF `LINEAR DIMENSION`dır, doğru layer'dadır ve pafta
  çerçevesi içindedir.
- Aynı context her zaman aynı zinciri verir (sıralama ve birleştirme
  deterministiktir).
- `python scripts/dimensions/selftest.py`: ordinatlar elle hesaplanabilir bir
  kat üzerinde birebir sınanır; kademelendirme ve **aynı baseline yasağı**
  negatif testle doğrulanır; kapalı ayarda aks standardının değişmediği ayrıca
  kontrol edilir.

## Sınır

Bu modül aks çizmez, duvar/oda geometrisini sahiplenmez ve context'i
değiştirmez. Yalnızca okur ve ölçü üretir.

## Bilinen sınırlamalar

- **Eğik duvarlar ölçülendirmeye girmez.** Eksen hizalı bir zincire anlamlı
  ordinat veremezler; `FloorOrdinates` onları atlar.
- **Yığın yalnızca güney ve batı kenarında çizilir.** Dört kenar için ayrı bir
  karar (ve muhtemelen ayrı bir `ChainStack` yönü) gerekir.
- Ölçü metinleri birbirine çok yakın ordinatlarda (örn. 20 cm'lik duvar
  kalınlığı) sıkışabilir; DXF ölçü stili bunu kendi kurallarıyla yerleştirir,
  modül müdahale etmez.
- `counters[]` ve tefriş ölçülendirmeye girmez; yalnızca duvar/açıklık
  geometrisi ölçülür.
