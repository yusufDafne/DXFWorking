# walls modülü — izole çalışma dosyası

Duvar geometrisi (cift rail), birlesim cozumu, tur/kalinlik katalogu, plan
cizimi ve tarama araclari. Pafta modulu gibi kendi klasorunde yasar;
`generate_dxf.py` sadece public API'yi import eder.

## Sorumluluk

| Bilesen | Dosya | Gorev |
|---------|-------|--------|
| `Wall` | `wall.py` | Merkez cizgisi + kalinlik -> rail geometrisi |
| `WallNetwork` | `network.py` | Kose/T miter, aciklik icin rail bosluklari |
| `WallCatalog` | `catalog.py` | Duvar turu -> varsayilan kalinlik/katman (ofis std.) |
| `draw_wall_network` | `render.py` | DXF rail + aciklik sembolleri |
| `RoomPolygonScanner` | `scan.py` | Oda poligonundan kenar/taslak duvar |
| `NetworkTopologyScanner` | `scan.py` | Birlesim noktasi raporu |

Kapı/pencere sembolleri simdilik `DefaultPlanOpeningStyle` icinde; ileride
`openings/` modulune tasinacak.

## Genisletilebilirlik (pafta deseni)

1. **Katalog:** `WallCatalog(DEFAULT_WALL_CATALOG)` yerine farkli sozluk verilir
   (or. yeni yonetmelik kalinliklari). Alt sinif gerekmez; veri odakli.
2. **Cizim standardi:** `draw_wall_network(..., opening_style=MyStyle())` —
   `OpeningSymbolStyle` protocol'u.
3. **Rail standardi:** Bugun tek yontem (paralel LINE). Ileride `RailDrawingStandard`
   ile hatch'li duvar, linetype'li cam vb. eklenebilir.

## context.json

Zorunlu alanlar degismedi: `id`, `start`, `end`, `thickness`, `layer`.
Opsiyonel `kind` semaya eklendiginde katalog etiketi/dogrulama icin kullanilir;
mm degerleri yine context'te kalir (uydurma yok).

## Tarama (`scan.py`)

- **`RoomPolygonScanner.scan_edges`:** Her oda kenari, kac odada paylasildigi.
- **`suggest_wall_dicts`:** Basit ic/dis sezgiseli taslak — kullanici/validate
  onayi olmadan context'e yazilmaz.
- **`NetworkTopologyScanner.junctions`:** Validate'e eklenebilecek birlesim listesi.

Ileride: DXF'ten duvar okuma (import), oda-duvar tutarlilik kontrolu.

## Test

1. `python scripts/generate_dxf.py` — regresyon yok.
2. Bir katta rail birlesimlerinin koselerde acik kalmadigini gorsel kontrol.

## Bilinen sinirlar

- Yayli/ cok segmentli duvar yok (tek duz segment).
- Yangin/drenaj katmani ayrimi yok.
- Aciklik sembolu tek plan stili; mentese yonu / surme kapi yok.
