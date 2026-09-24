# importer modülü — DEV-013 (Fikir 1) tamamlandı

## İsim notu (rev-15, `import` → `importer`)

Bu modül planlama sırasında `scripts/import/` olarak adlandırılmıştı. Kod
yazılırken görüldü ki **`import` bir Python ANAHTAR KELİMESİDİR** — `import
import` bir `SyntaxError`dur, bu isim hiçbir zaman geçerli bir Python paketi
olamazdı. Bu, `fixture` → `golden` yeniden adlandırmasıyla (rev-11) AYNI
kategoride bir hata: planlama sırasında seçilen bir ad, uygulamaya
geçilince teknik olarak kullanılamaz çıktı. Çözüm aynı desen: dizin ve tüm
doküman atıfları `importer/`e taşındı, `DEV-013` kimliği DEĞİŞMEDİ.

## Sorumluluk

Mevcut bir DXF dosyasından duvar ADAYLARI çıkaran, salt-okunur bir tarayıcı.
`walls.scan::RoomPolygonScanner` (context içindeki ODALARDAN duvar öner)
ile AYNI deseni, kaynak context DIŞINDAN (bir DXF dosyasından) uygular.

## Karar: Fikir 1 seçildi, Fikir 2 ertelendi

- **Fikir 1 — `DxfWallScanner` (SEÇİLDİ):** mevcut bir DXF'ten duvar
  adaylarını çıkarır, confidence ve provenance (kaynak dosya + hash) ile
  raporlar. Çıktı ASLA doğrudan context veya nihai DXF olmaz.
- **Fikir 2 — PDF/görüntü altlık ölçekleme (uygulanmadı):** temelde farklı
  bir yetenek (raster gömme/ölçekleme, geometri ÜRETMEZ) olduğu için açık
  fikir olarak duruyor.

## Kapsam kararları (DEV-013'ün açık kararları KAPANDI)

- **Desteklenen kaynak format:** yalnızca DXF (`ezdxf.readfile`, salt-okunur).
- **Entity kapsamı:** yalnızca `LINE`. `LWPOLYLINE` kenarları, `ARC`,
  `POLYLINE` (eski stil) bu sürümde TARANMAZ — bkz. "Bilinen sınırlamalar".
- **Layer kapsamı:** varsayılan TÜMÜ; `layers` parametresiyle filtrelenebilir
  (kaynak DXF'in katman adları bu projeninkilerle ÖRTÜŞMEK ZORUNDA DEĞİLDİR).
- **Onaylı import patch formatı:** AYRI bir `ImportPatch`/otomatik-birleştirme
  sınıfı YOK. `WallCandidate.as_wall_dict(id_prefix)`, `walls[]` şemasıyla
  BİREBİR aynı şekilde bir sözlük üretir (`RoomPolygonScanner.
  suggest_wall_dicts`nin ürettiği şekille AYNI) — insan/agent bunu
  gözden geçirip normal talep akışıyla (`requests.jsonl` → context patch →
  `validate.py`) context.json'a ekler. Otomatik birleştirme YOKTUR; bu
  kasıtlıdır (bkz. kök `CLAUDE.md` "Deterministik üretim ilkesi").

## Algoritma (elle hesaplanabilir)

İki `LINE` entity'si şu ÜÇ koşulu SIRAYLA geçerse bir duvar ADAYI oluşturur:

1. **Paralellik:** yön vektörleri arasındaki açı `MAX_ANGLE_DEG` (10°)
   içinde olmalı — değilse çift TAMAMEN elenir (skor değil, reddediliyor).
2. **Kalınlık aralığı:** aralarındaki dik mesafe `[MIN_THICKNESS,
   MAX_THICKNESS]` (40–400 mm) içinde olmalı — bu, `WallCatalog`daki
   gerçek kalınlık aralığından (50–250mm) biraz geniş tutulmuş bir güvenlik
   payıdır.
3. **Örtüşme:** ortak yön üzerindeki izdüşüm aralıkları en az
   `MIN_OVERLAP_RATIO` (0.5) oranında ÇAKIŞMALI — aksi halde iki çizgi
   "yaklaşık paralel ve yakın" ama alakasız birer çizgi olabilir.

Geçen bir çift için:

- **Confidence** = `parallel_score * overlap_score`, ikisi de `[0,1]`:
  `parallel_score = 1 - angle_deg/MAX_ANGLE_DEG`,
  `overlap_score = overlap_length / max(len1, len2)`.
- **Merkez çizgisi** SADECE örtüşen aralıkta hesaplanır (iki rail'in
  örtüşmeyen uçları ADAY GEOMETRİSİNE dahil edilmez) — iki rail'in
  karşılıklı noktalarının orta noktası alınır.
- **Kalınlık** = ölçülen dik mesafe (yuvarlanmadan, mm).

Bu formül `selftest.py`de elle kurulmuş DXF örnekleriyle (bilinen açı,
bilinen mesafe, bilinen örtüşme) `< 1e-6` toleransla doğrulanır.

## Public API

```python
from importer import DxfWallScanner, ImportReport, WallCandidate

report = DxfWallScanner().scan(Path("mevcut_proje.dxf"))
report.source_path        # taranan dosya
report.source_sha256      # provenance
report.candidates         # list[WallCandidate], confidence'a gore siralı
for candidate in report.candidates:
    if candidate.confidence >= 0.8:
        wall_dict = candidate.as_wall_dict(f"import_{candidate.index}")
        # -> insan/agent inceler, onaylarsa normal talep akisiyla eklenir
```

## Invariant'lar

- **Salt okunur:** bu modül hiçbir dosyaya YAZMAZ (kaynak DXF dahil);
  context.json'u hiç GÖRMEZ/import etmez.
- **Deterministik:** aynı kaynak DXF her zaman aynı adayları, aynı sırada
  (confidence azalan, eşitlikte kaynak handle'a göre) üretir.
- **Provenance korunur:** her raporda kaynak dosya yolu + SHA-256 hash
  bulunur (`golden_report.py`nin kendi DXF hash'leme yöntemiyle AYNI).
- **Tahmin doğrulanmış veri gibi SUNULMAZ:** `WallCandidate` asla context
  şemasına UYGUN bir "wall" değildir, `as_wall_dict()` ÇAĞRILMADAN önce.

## Doğrulama

`python scripts/importer/selftest.py` — elle kurulmuş DXF senaryoları:
mükemmel paralel çift (confidence 1.0'a yakın), hafif açılı çift (skoru
düşürür ama eler geçer), açı sınırını AŞAN çift (reddedilir), kalınlık
aralığı DIŞINDA çift (reddedilir), kısmi örtüşen çift (merkez çizgisi
sadece örtüşen kısımda), örtüşme eşiğinin ALTINDA çift (reddedilir).

## Sınır

Bu modül context'i hiç görmez, `ezdxf` yalnızca OKUMA için kullanılır
(`readfile`), hiçbir DXF/context dosyasına yazmaz. `WallCandidate.
as_wall_dict()` şema-uyumlu bir sözlük üretir ama bunu HİÇBİR YERE
otomatik EKLEMEZ.

## Bilinen sınırlamalar

- **Sadece `LINE`.** `LWPOLYLINE` kenarları (bu projenin KENDİ duvar
  çizimi dahi `LINE` kullanır, ama gerçek dünyadan gelen DXF'ler genelde
  `LWPOLYLINE` kullanır) taranmıyor — gerçek bir mevcut-proje DXF'inde
  bu ciddi bir kapsam boşluğudur, bilerek v1 dışı bırakıldı.
- **PDF/görüntü altlık (Fikir 2) uygulanmadı.**
- **Köşe/T-kesişimi algılamaz** — her duvar adayı BAĞIMSIZ bir çifttir;
  `walls.scan::NetworkTopologyScanner.junctions` üretilen adaylar
  ÜZERİNDE (context'e eklendikten SONRA) çalıştırılabilir.
- **Kesikli/noktalı linetype'lı rail'leri ayırt etmez** — yalnızca
  geometriye (paralellik/mesafe/örtüşme) bakar, linetype'a bakmaz; bu
  yüzden `axis` veya ölçü çizgileri de (yanlışlıkla) YAKIN VE PARALEL
  iseler aday üretebilir. Düşük confidence bunu kısmen telafi eder ama
  insan gözden geçirmesi HER ZAMAN gereklidir (bkz. "Invariant'lar").
