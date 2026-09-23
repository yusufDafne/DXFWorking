# dimensions modülü — Gelecek faz

## Sorumluluk

`DimensionChain`, `LinearDim` ve `ChainLayout`; gerçek DXF ölçü varlıkları, ölçekli stil ve tam sayı cm metni.

## Faz planı

1. AxisGrid'in `_dim_chain_x` ve `_dim_chain_y` davranışını karakterize et.
2. Ortak ölçü noktaları, yön, offset ve metin formatı için veri sözleşmesini
   belirle; context koordinatları mm olarak kalır.
3. Gerçek DXF `LINEAR DIMENSION` üretimini `LinearDim` ile kapsülle.
4. Aks ölçülerini devralırken mevcut DXF entity ve metin sonuçlarını koru.
5. Zincir çakışması ve Sheet overflow için layout doğrulaması ekle.

## Public API adayı

- `LinearDim(p1, p2, offset, style)`.
- `DimensionChain(points, orientation, style)`.
- `ChainLayout.place(chains, bounds)`.
- `format_dimension_cm(mm_value)` yalnızca görünür metni biçimlendirir.

## Invariant'lar ve doğrulama

- Kaynak koordinatlar mm'dir; cm dönüşümü yalnızca ölçü metninde yapılır.
- Ölçü metni tam sayı cm olur; sessiz yuvarlama tasarım verisini değiştirmez.
- Ölçü entity'si doğru layer'da, gerçek DXF dimension olarak ve pafta içinde
  üretilir.
- Aks fazından devralınan davranış golden output ile karşılaştırılır.

## Bağımlılıklar

`AxisGrid` içindeki `_dim_chain_x/_dim_chain_y` davranışını devralır. Koordinatlar mm olarak kalır; cm yalnızca çizim metninin gösterimidir.

## Kabul

Ölçü zincirleri deterministik, okunabilir, doğru layer'da ve pafta çerçevesi içinde olmalıdır.
