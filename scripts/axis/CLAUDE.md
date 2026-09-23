# axis modülü — Faz 2 tamamlandı

## Sorumluluk

`AxisGrid` ve aks çizim standardını `generate_dxf.py`den davranış korunarak taşır. Floor/elevation izdüşümü, aks baloncukları, layer/linetype/rgb standardı ve mevcut mini ölçü zincirleri bu modülün sınırındadır.

## Veri ve standart

Aks konumları `context.json` grid verisinden okunur; çizim sabitleri kod seviyesinde kalır. Context'e standart veya türetilmiş geometri yazılmaz.

## Bağımlılıklar

`pafta` overflow sözleşmesini tüketir; `dimensions` gelene kadar mini zincirleri korur. Duvar ve oda geometrisini sahiplenmez.

## Public API

- `AxisGrid(vertical_axes, horizontal_axes, text_height, standard=None)`
- `AxisDrawingStandard`: kod seviyesinde aks çizim sabitleri.
- `ensure_axis_layer(doc, standard=None)`: `AKS`, `DASHED` ve sabit RGB
  standardını hazırlar.
- `AxisGrid.draw_on_floor(...)` ve `draw_on_elevation(...)` mevcut generator
  çağrı sözleşmesini korur.

## Invariant'lar

- Aks konumları bildirilen grid verisinden gelir; sıralama pozisyona göre
  deterministiktir.
- Aks çizgisi baloncuk yarıçapı kadar önce biter, baloncuğun içine girmez.
- Aks layer'ı context'ten stil almaz; `AxisDrawingStandard` kod sahibidir.
- Aks ölçü metni gerçek DXF linear dimension'dır ve tam sayı cm gösterir.
- Floor ve elevation aynı grid verisini kullanır; elevation yalnızca bildirilen
  `axis_source` ailesini çizer.

## Faz 2 doğrulaması

`py_compile`, `python scripts/validate.py` ve `python scripts/generate_dxf.py`
başarılıdır. Mevcut ölçek mevzuatı uyarısı üretim davranışının bilinen parçası
olarak sürmektedir.

## Kabul

Mevcut DXF ile aks entity/layer/linetype, izdüşüm, teğet baloncuk, ölçü ve taşma davranışı karşılaştırılır. `validate.py` ve `generate_dxf.py` çalıştırılır.
