# Tamamlanan Geliştirmeler Geçmişi

Aktif geçmiş kapasitesi: **50 kayıt**. En eski tamamlanmış kayıt, 51. kayıt
alınırken silinir. Ayrıntılı teknik değişiklikler git geçmişi ve ilgili proje
provenance kayıtlarıyla ilişkilendirilir.

## HD-014 — `palette/` modülü: merkezi katman renk organizasyonu (DEV-030)

- **Durum:** COMPLETED
- **Tamamlanma:** 2026-09-25
- **Kökeni:** Kullanıcının kod incelemesi sırasında yaptığı gözlem
  ("modüllerin kendi layer'larında çalışırken renklerinin
  çeşitlendirilmediğini fark ettim") `DEV-030` olarak plana eklenmişti
  (bkz. bu oturumdaki önceki kayıt). Kullanıcı sonradan Fikir 1
  (merkezi olmayan) / Fikir 2 (merkezi kontrolör modülü) arasında **Fikir
  2**'yi seçti, gerekçesi:

  > "her modül kendi rengini oluşturursa bazı modüller aynı rengi seçmiş
  > olabilir ... ve bazı modüllerin birbirlerine kontrast renkler ile
  > bulunması ihtiyacı olabilir bundan dolayı ayrı bir modül olması uygun
  > olabilir."

- **Kapsam:** `scripts/palette/` (yeni modül: `__init__.py`, `CLAUDE.md`,
  `selftest.py`), `scripts/axis/standard.py`, `scripts/columns/standard.py`
  + `render.py` + `__init__.py`, `scripts/sections/__init__.py`,
  `scripts/stairs/__init__.py`, `scripts/furniture/groups.py` (hepsi
  `palette.color_for(...)`den okur), `scripts/collision/scene.py`
  (`COLLISION_EXEMPT`), `scripts/version.py` (`CONTRACT_MODULES`), kök
  `CLAUDE.md` + `scripts/CLAUDE.md` (modül kaydı).

### İki kural, kullanıcının iki cümlesine BİREBİR karşılık gelir

`palette::validate_palette`: (1) hiçbir iki katman AYNI rengi taşıyamaz
(tam eşitlik yasağı — "aynı rengi seçmiş olabilir" riski), (2) aynı
`contrast_group`taki katmanlar birbirinden en az `CONTRAST_MIN_DISTANCE`
(40.0, RGB Öklid mesafesi) kadar uzak olmalıdır ("kontrast ihtiyacı").
`"primary"` grubu AKS/KOLON ailesi/KESİT/MERDİVEN'i kapsar (aynı pafta
üzerinde aynı anda görülebilirler); tefriş ailesi bilerek bu gruba GİRMEZ
(rev-10 kararı: "zıt renk kullanılmaz" korunur).

### Somut bulgu düzeltildi: KOLON ailesi artık 3 farklı ton

`columns/standard.py::COLUMN_RGB`, üç farklı katmana (`KOLON` kontur,
`KOLON-TARAMA` tarama, `KOLON-METIN` isim) TEK renk atıyordu — kullanıcının
birinci endişesinin (aynı rengin paylaşılması) SOMUT bir örneğiydi.
`palette` kurulurken üçü ayrıştırıldı: kontur nötr orta gri `(150,150,150)`,
tarama daha açık `(190,190,190)` (ast eleman konvansiyonu), metin en koyu
`(45,45,50)` (okunurluk) — üçü de `AKS`in SABİT rengine `(67,77,88)`
(kök `CLAUDE.md` tarafından mandate edilir, DEĞİŞTİRİLEMEZ) yeterince uzak
tutuldu; eski `(90,90,96)` AKS'ye tehlikeli derecede yakındı (Öklid mesafesi
~27.6, yeni değerler ≥88).

### Kapsam kararı: yalnızca kod-sahipli katmanlar

`context.json::layers[]` (proje verisi, ACI index) merkezi kaydın DIŞINDA
bırakıldı — kullanıcı bu ayrımı genişletmeyi istemedi (soru açık kararlar
listesinde soruldu, ek yönlendirme gelmedi), bu yüzden "proje verisi = ACI,
sistem/kod standardı = RGB" ikiliği KORUNDU.

### `golden_report.py`nin bilinen bir kör noktası doğrulandı

DEV-030 gerçek projenin `KOLON` ailesinin rengini DEĞİŞTİRDİĞİ halde
`golden_report.py --golden-set` ve `--compare docs/development/
plan-golden-report.json` "eşleşti" raporladı — ölçüm raporu yalnızca
entity/layer SAYISINI ve `modelspace_bbox`i kaydeder, RGB'yi DEĞİL. Bu YENİ
bir hata değil (rapor formatı hep böyleydi) ama DEV-030 bunu İLK KEZ somut
olarak gösterdi; `scripts/palette/CLAUDE.md` ve `scripts/columns/CLAUDE.md`
"Bilinen sınırlamalar"a eklendi. Renk regresyonu bugün yalnızca
`palette/selftest.py` ve `preview.py` ile gözle kontrol edilebilir.

### Golden output etkisi

- **Ana proje GÖRSEL olarak değişti** (kolonların üç katmanı artık farklı
  gri tonlarında) ama **ölçüm raporu AYNI kaldı** (yukarı bakınız) —
  `docs/development/plan-golden-report.json` bu yüzden YENİDEN YAZILMADI
  (zaten hiçbir şeyi kaydetmiyordu).
- Mevcut 6 golden referansının TÜMÜ `--golden-set` ile yeniden koşuldu,
  hepsi (`golden/tefris_kolon` dahil) "eşleşti" — beklenen, çünkü ölçüm
  formatı renk taşımıyor.

### Modül self-test'i

`python scripts/palette/selftest.py` — 7 kontrol grubu: gerçek `PALETTE`nin
kendi kurallarını ihlal etmediği, aynı-renk ihlalinin yakalandığı (KOLON
bulgusunun regresyon testi), yakın-kontrast ihlalinin yakalandığı (+ eşiğin
TAM ÜZERİNDEKİ mesafenin yanlış-pozitif ÜRETMEDİĞİ, elle: (100,100,100) vs
(110,100,100) mesafe=10<40 HATA, (0,0,0) vs (40,0,0) mesafe=40 tam eşik
HATA VERMEZ), farklı/`None` gruplar arası yakınlığın MUAF olduğu (tefriş
ailesi korunur), `color_for`in bilinen/bilinmeyen isim davranışı, KOLON
ailesinin artık aynı renk OLMADIĞI, `_distance`in elle hesaplanabilir
olduğu (3-4-5 üçgeni, mesafe=5.0).

### Açık risk / bilinen sınırlama

- `golden_report.py` renk regresyonunu yakalamaz (yukarı bakınız) —
  ileride `report()`e katman başına örnek RGB eklenmesi düşünülebilir.
- `CONTRAST_MIN_DISTANCE` tek bir global eşiktir; gruba özel farklı eşikler
  desteklenmiyor.
- `context.json::layers[]` (ACI index) ile kod-seviyeli `PALETTE` (RGB)
  arasında bir çakışma kontrolü YOK — kullanıcı bunu istemedi, bilinçli
  sınır.

### Sonraki direktif

Sıradaki `PLANNED` madde `DEV-029` (kot/datum mantığı, `scripts/levels/`)
— aynı oturumda kullanıcı tarafından seçildi, ayrıca bkz. bu dosyadaki
sonraki kayıt.

## HD-013 — `stairs/` modülü: gerçek merdiven basamak geometrisi (DEV-022)

- **Durum:** COMPLETED
- **Tamamlanma:** 2026-09-25
- **Kökeni:** `DEVELOPMENT_TASKS.md::DEV-022`, 2026-09-24'te "endüstri
  standardı bir boşluk" olarak eklenmişti (kök `CLAUDE.md`nin "asansör/
  merdiven kapı sembolü çizilmez, sadece etiketli kapalı oda olarak
  gösterilir" bilinen basitleştirmesi). Kullanıcı 2026-09-25'te bu maddeyi
  açıkça seçti ve şu yönlendirmeyi verdi: **Fikir 1** (yeni bağımsız
  `scripts/stairs/` modülü — `columns/`/`furniture/` ile AYNI "oda-içi ek
  eleman = kendi modülü" deseni); rıht için varsayılan **17cm**, basamak
  genişliği için varsayılan **27cm** (makul bant 25-30cm); esnetilebilirlik
  (`auto_flex`) **varsayılan AÇIK**, esnetme her seferinde kullanıcıya
  bildirilir (UYARI).
- **Kapsam:** `scripts/stairs/` (yeni modül: `__init__.py`, `CLAUDE.md`,
  `selftest.py`), `schema/design.schema.json` (`stairs` tanımı +
  `floor.properties.stairs`), `scripts/validate.py` (`check_stairs`),
  `scripts/generate_dxf.py` (`ensure_stair_layer` + `draw_stairs_on_floor`
  çağrıları), `scripts/collision/scene.py` (`COLLISION_EXEMPT["stairs"]`),
  `scripts/version.py` (`CONTRACT_MODULES`), `scripts/golden_report.py`
  (`_code_owned_layers`e `MERDIVEN`), `golden/merdiven_ornek/` (yeni izole
  referans), kök `CLAUDE.md` + `scripts/CLAUDE.md` (modül kaydı).

### Tek kaynak: `resolve_stair`

`openings::swing_geometry` ile AYNI desen (kök `CLAUDE.md`, "Açıklık
varyantları" bölümü, rev-13'te bunun ihlalinin gerçek bir hataya yol açtığı
not edilir): `resolve_stair(spec, room_polygon)` hem `validate.py::
check_stairs` hem `draw_stairs_on_floor`in ÇAĞIRDIĞI TEK fonksiyondur. Basamak
sayısı `step_count` açıkça verilmemişse `floor_to_floor_mm / riser`den
(`round`) türetilir; `riser_height_mm`/`going_mm` verilmemişse ofis
standardı varsayılanlarına (170mm / 270mm) düşer; `auto_flex=True`
(varsayılan) bu değerleri kat yüksekliğine VE oda uzunluğuna TAM oturacak
şekilde ince ayarlar ve her esnetme `StairResolution.warnings`e yazılıp
hem `validate.py` hem `generate_dxf.py` tarafından "UYARI (merdiven): ..."
olarak basılır (sessiz varsayım YOK). Basamak genişliği esnetmesi
`MIN_GOING_MM=250`in altına düşerse (güvensiz/standart-dışı bir merdiven)
`StairFitError` fırlatılır — üretim durur, sessizce geçersiz geometri
üretilmez.

### Geliştirme sırasında bulunan gerçek hata: X/Y ekseni takası

İlk uygulamada `_travel_points` yardımcı fonksiyonu, seyahat ekseni `y`
olan bir merdiven için nokta çiftlerini `(y_koordinati, mid_x)` sırasıyla
döndürüyordu — DXF'in beklediği `(x, y)` sırası yerine KOORDINATLAR YER
DEĞİŞTİRİLMİŞTİ. Bu, `golden/merdiven_ornek` fixture'ı ilk kez üretilmeye
çalışılırken `PaftaOverflowError` olarak YAKALANDI (basamak/ok/kesme
çizgisi entity'leri pafta çerçevesinin çok dışına taştı — içerik sınırları
beklenenin binlerce mm dışındaydı). Kök neden bulunup `_travel_coords`
(yalnızca seyahat ekseni üzerindeki SKALER koordinatı döndüren, ayrı ve
daha az belirsiz bir yardımcı) ile düzeltildi. **Bu, `scripts/stairs/
selftest.py`ye eksik olan bir test sınıfını da ortaya çıkardı:**
`check_draw_entity_counts` yalnızca çizilen VARLIK SAYISINI doğruluyordu,
KOORDİNATLARINI değil — sayı doğru olsa bile koordinat yanlış olabilirdi.
Bunu kapatmak için `check_step_line_coordinates_hand_computable` eklendi
(hem X hem Y seyahat ekseninde elle hesaplanmış uç noktalarla karşılaştırma
— bu proje disiplininin "temiz döndü çıktısı tek başına hiçbir şey
kanıtlamaz" ilkesinin somut bir örneği).

### Bağımsız reviewer geçişinde bulunan ikinci gerçek hata: koşulsuz olmayan MIN_GOING_MM

Ayrı bir Agent çağrısıyla yapılan bağımsız reviewer/validator geçişi
(`scripts/CLAUDE.md`daki "reviewer/validator" rolü) `resolve_stair`i elle
izleyerek gerçek bir kapsam açığı buldu: `MIN_GOING_MM` kontrolü yalnızca
going'in OTOMATİK DARALTILDIĞI dalın İÇİNDEYDİ. Oda zaten sığıyorsa (daraltma
dalına hiç girilmiyorsa) açıkça verilmiş güvensiz bir `going_mm` (örn.
100mm) HİÇBİR kontrolden geçmeden sessizce kabul ediliyordu — modülün kendi
sözleşmesinin ("sessizce geçersiz/güvensiz bir basamak genişliği üretmez")
BİREBİR ihlaliydi. Düzeltme: `MIN_GOING_MM`/`MAX_GOING_MM` kontrolü
`resolve_stair`in SONUNDA, daraltılmış olsun ya da olmasın nihai `going`
değeri üzerinde KOŞULSUZ çalışacak şekilde taşındı (altında `StairFitError`,
üstünde UYARI — `MAX_GOING_MM` böylece ilk defa gerçekten KULLANILAN bir
sabit oldu, önceden tanımlı ama hiç okunmuyordu). İki yeni selftest eklendi
(`check_explicit_going_below_minimum_raises_even_without_shrink`,
`check_going_above_maximum_warns`) — toplam self-test grubu 10 → 12.
Reviewer ayrıca küçük bir kod kokusu (Python truthiness'e dayanan bir no-op
guard, `required_run and ...`) buldu; temiz bir bölmeyle değiştirildi.

### Gerçek projenin `Merdiven` odasına `stairs[]` verisi EKLENMEDİ

`context.json`daki mevcut `Merdiven` odası (4000×3000mm, tüm katlarda
sabit) için deneme amaçlı bir `stairs[]` girdisi (`floor_to_floor_mm=3000`)
`check_stairs` ile test edildi: sonuç `StairFitError` — tek düz kollu
merdiven için gereken kosu uzunluğu (~4590mm, 18 basamak × 270mm) odanın
uzun eksenine (4000mm) SIĞMIYOR, esnetilmiş basamak genişliği (~235mm)
minimum konfor sınırının (250mm) altında kalıyor. Bu SESSİZCE görmezden
gelinmedi: modül DOĞRU şekilde reddetti. Gerçek bir bina için bu odada
sahanlıklı/çift kollu bir merdiven gerekir (v1 kapsamı dışında, bkz.
`scripts/stairs/CLAUDE.md` "Bilinen sınırlamalar") — bu yüzden gerçek
projenin `context.json`ına HENÜZ `stairs[]` verisi eklenmedi; oda büyütülüp
tek kollu merdivene mi geçilecek yoksa çok kollu merdiven mi (ayrı bir
gelecek geliştirme konusu) eklenecek, sistem mimarının kararıdır.

### Golden output etkisi

- **Ana proje DEĞİŞMEDİ:** `context.json`a `stairs[]` verisi eklenmediği
  için `output/plan.dxf` entity/layer/bbox açısından AYNI kaldı
  (`golden_report.py --compare docs/development/plan-golden-report.json`
  ile doğrulandı, "Golden semantic report matches"); referans rapor
  YENİDEN YAZILMADI.
- **Yeni izole referans:** `golden/merdiven_ornek/` (tek oda, `stairs[]`
  ile `floor_to_floor_mm=3000` + `up_towards='N'`, TÜM basamak/riht/going
  değerleri varsayılanlardan türetilir, 0 UYARI) — 161 entity, `MERDIVEN`
  katmanında 21 entity (17 riht çizgisi + 1 ok gövdesi + 1 ok başı + 2
  kesme çizgisi parçası, elle sayılabilir: `step_count-1 + 4`).
- `scripts/golden_report.py::_code_owned_layers` `MERDIVEN`yi tanımadığı
  için ilk denemede `declared_layers` kuralı bunu "bildirilmemiş layer"
  olarak işaretlerdi — `AKS`/`KOLON*`/`TEFRIS-*`/`KESIT` ile AYNI listeye
  eklenerek düzeltildi.

### Modül self-test'i

`python scripts/stairs/selftest.py` — 12 kontrol grubu: step_count'tan
riht türetme (elle hesap), `auto_flex` açık/kapalı davranış farkı (+
UYARI), going daraltma (+ UYARI), MIN going altında `StairFitError` (+
yanlış-pozitif: sığan oda hata VERMEMELİ), **açıkça verilmiş güvensiz
`going_mm`nin daraltma dalı hiç tetiklenmese bile reddedilmesi** (+
yanlış-pozitif) ve MAX üstünde UYARI (bağımsız reviewer'ın bulduğu ikinci
kök neden hatasının regresyon testi, bkz. yukarısı), `up_towards`/
`travel_axis` tutarlılığı (+ yanlış-pozitif), riht çizgisi koordinatları
(X VE Y ekseni, elle hesaplanabilir — ilk kök neden hatasını yakalayan
test), çizilen varlık sayıları, bilinmeyen `room_id`nin çizim tarafında
sessizce atlanması, katman RGB'si.

### Açık risk / bilinen sınırlama

- Yalnızca TEK DÜZ KOLLU (sahanlıksız) merdiven desteklenir — bkz.
  `scripts/stairs/CLAUDE.md`.
- Kesit (`sections::SectionFeatureHook`) entegrasyonu bu revizyonun
  kapsamında DEĞİLDİR; ayrı bir takip konusu.
- `DEV-030` (katman renk organizasyonu, henüz PLANNED) tamamlandığında
  `STAIR_RGB` sabiti o merkezi karara göre yeniden gözden geçirilebilir.

### Sonraki direktif

Sistem mimarı şunlardan birine karar verebilir: (a) örnek projenin
`Merdiven` odasını büyütüp gerçek `stairs[]` verisiyle bağlamak, (b)
sahanlıklı/çift kollu merdiven desteğini ayrı bir görev olarak
`DEVELOPMENT_TASKS.md`ye eklemek, (c) `sections::SectionFeatureHook`
entegrasyonunu ayrı bir takip görevi yapmak, (d) sıradaki `PLANNED`
maddeye (`DEV-023` `ceiling/` veya kullanıcının seçtiği başka biri) geçmek.

## HD-012 — AutoCAD hatch uyarısı + aks ölçüsü düzeltmeleri, ScaleBar geri alındı

- **Durum:** COMPLETED
- **Tamamlanma:** 2026-09-24
- **Kökeni:** Kullanıcı gerçek projeyi AutoCAD'de açtığında "Hatch - Large,
  Dense Hatch Patterns" uyarısı aldığını bildirdi (ekran görüntüsüyle) ve
  ayrıca üç ayrı düzeltme istedi: (1) her paftadaki 0-5 arası basamaklı
  "ölçek gibi bir şey"in kaldırılması, (2) aks ölçü zincirinin AKS ile aynı
  katmanda olması ve sadece aks-aks + en-uçtaki-toplam mesafeyi göstermesi,
  (3) duvar kalınlığı gösteren ölçülerin aks ölçüsünün yanında (ve
  şimdilik sistemde hiçbir yerde) gösterilmemesi.
- **Kapsam:** `scripts/sections/__init__.py`, `scripts/dimensions/linear.py`,
  `scripts/dimensions/selftest.py`, `scripts/axis/standard.py`,
  `scripts/axis/grid.py`, `scripts/axis/selftest.py`,
  `scripts/pafta/__init__.py`, `scripts/generate_dxf.py`,
  `scripts/preview.py`, `scripts/northarrow/selftest.py`, `context.json`
  (`meta.dimensions.enabled` → `false`).

### Kök neden 1 — sahte "SOLID" hatch (AutoCAD uyarısının kaynağı)

`scripts/sections/__init__.py`'deki kesit-duvar kesişimi dolgusu
`hatch.set_pattern_fill("SOLID")` çağırıyordu — bu, GERÇEK bir solid-fill
API'si DEĞİLDİR (`ezdxf`de o `hatch.set_solid_fill()`dür); `"SOLID"` bir
PATTERN adı olarak arandı ve `pattern_scale=1.0`'da yaklaşık 0.125 birim
(mm) aralıklı bir çizgi deseni uygulandı. Gerçek projedeki 86 kesit-dolgusu
(250×4000mm'lik dikdörtgenler) bu yüzden HER BİRİ ~32.000 paralel çizgi
gerektiriyordu — AutoCAD'in "Large, Dense Hatch Patterns" uyarısının
BİREBİR kökeni buydu (elle doğrulanmış: `dxf.solid_fill=0`, `hatch.pattern`
içinde `(-0.088, 0.088)` ofsetli tek bir çizgi tanımı). Düzeltme:
`hatch.set_solid_fill()`. Regresyon testi:
`scripts/sections/selftest.py::check_section_sheet_entity_count`
(`dxf.solid_fill == 1` kontrolü).

### Kök neden 2 — `ezdxf` 1.4.4'ün katman hatası (aks ölçüsü "0" katmanında)

Kullanıcı "aks çizgileri ölçüleri aks çizgileri ile aynı layerda olmalı"
dedi; incelemede aks (AKS) DIMENSION'larının OK ve METİN'i doğru katmanda
ama ÖLÇÜ/UZATMA ÇİZGİLERİNİN hep `"0"` katmanında olduğu görüldü.
Kaynağı: `ezdxf`nin `render/dim_base.py::BaseDimensionRenderer.add_line`i
katman dahil BİRLEŞTİRİLMİŞ `attribs` sözlüğünü hesaplayıp sonra
KULLANMADAN, orijinal (katmansız) `dxfattribs`i geometri bloğuna geçiriyor
(ok/metin yolu birleşmiş sözlüğü doğru kullandığı için bu hatadan MUAF).
Kütüphane kaynağı değiştirilemediği için `scripts/dimensions/linear.py::
LinearDim.render` render SONRASI bir düzeltme uygular
(`_fix_geometry_block_layer`): geometri bloğundaki `Defpoints` DIŞINDAKİ
her varlığın katmanı `style.layer`e zorlanır. Regresyon testi:
`scripts/dimensions/selftest.py::check_rendered_layer`.

### Aks ölçüsü: en-uçtaki-toplam zinciri eklendi

Kullanıcı kararı: *"akslar arası mesafeler ve ikinci olarak en uçtaki
aksların arasındaki mesafeyi vermeli."* `AxisGrid._dim_chain_x/_dim_chain_y`
artık, bir kenarda 2'den FAZLA aks varsa, ardışık-mesafe zincirinin YANINA
`[min(xs), max(xs)]`ten tek-segmentli bir TOPLAM zinciri ekler; TAM 2 aks
varsa bu ikisi ZATEN aynı sayı olacağından toplam zincir TEKRARLANMAZ.
Toplam zincirin baseline'ı aksın kendi baloncuk/uzama bölgesinin
(`extension + bubble_radius`) `total_dimension_clearance` (300mm) kadar
ÖTESİNDE durur — aksi halde 3+ aks varlığında toplam zincirin ucu
bubble'ın İÇİNE girebilirdi (elle doğrulandı). Regresyon testi:
`scripts/axis/selftest.py::check_total_span_dimension` (3 aks + 2 aks →
3+1=4 DIMENSION; bubble-clearance kontrolü).

### Duvar/oda ölçüleri kaldırıldı (aks ölçüsünün yanında kafa karıştırıyordu)

Kullanıcı: *"duvarların kalınlıklarını vs. aks ölçülerinin yanında
göstermemeli bu kafa karıştırır, duvar ölçüleri sistem üzerinde şimdilik
hiçbir yerde gösterilmeyecek."* Kök neden: `meta.dimensions`in `mahal`
kademesi, bir bölme duvarının İKİ YÜZÜ arası (yani SADECE duvar kalınlığı)
kadar bir segment üretebiliyordu; bu, oda ölçüleri arasında aks ölçüsüne
yakın küçük ve şaşırtıcı bir sayı olarak görünüyordu. `dimensions` modülü
(ve `aciklik`/`mahal`/`toplam` kademeleri) KALDIRILMADI — hâlâ
`scripts/dimensions/` içinde vardır, `golden/aciklik_varyantlari` onu
sınamaya devam eder — sadece gerçek projenin `context.json::meta.
dimensions.enabled` alanı `true` → `false`ya çekildi (rev-13'ten beri
açıktı, şimdi belgelenmiş varsayılana döndü).

### ScaleBar tamamen kaldırıldı

Kullanıcı: *"ilave olarak her pafta içerisinde ölçek gibi bir şey var,
0-5 arası değerler ile birlikte, onu istemiyorum, kaldır."* Bu, rev-17'de
(HD-011, DEV-025) AYNI talebin ikinci parçası olarak eklenen
`pafta::ScaleBar` (+ `nice_scale_length_m`, `format_scale_value`) idi.
Sınıf, `generate_dxf.py`/`preview.py`'deki tüm çağrı yerleri,
`scripts/northarrow/selftest.py`'deki test grupları ve ilgili `CLAUDE.md`
bölümleri (`pafta`, `northarrow`, kök) TAMAMEN KALDIRILDI. Kuzey oku
(`NorthArrow`) etkilenmedi. `scripts/sections::draw_cut_marker_on_floor`,
etiket yüksekliğini artık `ScaleBar`dan ÖDÜNÇ ALMAK yerine kendi
`PRINTED_MARKER_LABEL_MM` sabitinden türetiyor (bağımsızlaştırma).

### Doğrulama

- `py_compile`, tüm 10 modül self-test'i (2 yeni test grubu: `dimensions::
  check_rendered_layer`, `axis::check_total_span_dimension`; 1 yeni
  assertion: `sections::check_section_sheet_entity_count`), `validate`,
  `generate` (`PaftaOverflowError` FIRLAMADI), `preview`, 5 semantik kural,
  5 golden referans (`--golden-set --update`), `doc_check` — hepsi temiz.
- Gerçek çıktıda doğrudan doğrulandı: 86 kesit-HATCH'i artık
  `dxf.solid_fill == 1`; 88 AKS DIMENSION'ının TAMAMI `AKS` katmanında
  (host + geometri bloğu); `meta.dimensions` kapalı olduğu için `OLCU`
  katmanlı DIMENSION SIFIRA düştü (önceden 402 idi).

### Golden output etkisi

- **Ana proje DEĞİŞTİ:** `output/plan.dxf`'te duvar/mahal/toplam ölçü
  zinciri (402 `OLCU` DIMENSION) ve ScaleBar entity'leri kayboldu, kesit
  HATCH'leri gerçek solid-fill oldu, aks ölçüsüne en-uçtaki-toplam satırı
  eklendi; `docs/development/plan-golden-report.json` `--write` ile
  YENİDEN üretildi.
- Mevcut 5 golden referansının TÜMÜ aynı sebeplerle değişti (`--update`).
  `golden/aciklik_varyantlari` kasıtlı olarak `meta.dimensions.enabled:
  true` BIRAKILDI — bu fixture'ın amacı zaten o özelliği sınamaktır.

## HD-011 — Kesit modülü ve kuzey oku/ölçek çubuğu standardı

- **Durum:** COMPLETED
- **Tamamlanma:** 2026-09-24
- **Görevler:** `DEV-021` ve `DEV-025` (kullanıcı: "dev 25, ve dev21 için
  çalışmaya başlayalım", ardından kesit hattı modeli ve kuzey oku/ölçek
  çubuğu için ayrıntılı yönlendirme).
- **Kapsam:** `scripts/sections/` (yeni modül), `scripts/northarrow/`
  (yeni modül), `scripts/pafta/` (`ScaleBar`, `nice_scale_length_m`,
  `format_scale_value` eklendi), `scripts/generate_dxf.py`,
  `scripts/preview.py`, `scripts/validate.py` (`check_sections`),
  `schema/design.schema.json` (`meta.north_angle`, `sections[]`,
  `definitions.section`), `scripts/golden_report.py`
  (`_code_owned_layers` → `KESIT`), `scripts/collision/scene.py`,
  `scripts/version.py`, `golden/kesit_ornek/` (yeni golden referans).

### DEV-021 — `sections/`: bina kesiti

Kullanıcının kesin kapsam kararı: *"bu yapılarda hiçbir zaman eğik kesit
ya da atlamalı kesit alınmaz. Bir kesit çizgisi X ve Y eksenindeki
akslardan birine paraleldir ve konumunu operatör bildirir."* Bu karar
`sections[].axis_source` alanını `elevations[].axis_source` ile BİREBİR
AYNI anlama getirdi (`'vertical'` → sabit Y, `'horizontal'` → sabit X) —
sayesinde `axis_grid.draw_on_elevation` VE `elevations::LevelStack`
DOĞRUDAN yeniden kullanıldı, ayrı bir "kesit aksı" kavramı icat edilmedi.

- **Varsayılan konum (kullanıcı kararı):** operatör bildirmezse kesit
  yapının TAM ORTASINDAN değil, ilgili kenarın **1/3 noktasından** alınır
  (`DEFAULT_POSITION_FRACTION`) — kullanıcı: *"amacımız default olarak
  projenin tam ortası değil de tam ortasından biraz sağ ya da solundan
  kesit almaktır."*
- **Varsayılan kesit sayısı (kullanıcı kararı):** `context['sections']`
  HİÇ verilmezse sistem X ve Y ekseninden BİRER varsayılan kesit üretir
  (`resolve_sections`, etiketler `A-A`/`B-B`); boş dizi (`[]`) verilirse bu
  varsayılan devre dışı kalır. Bu, **gerçek projeyi otomatik olarak
  değiştirdi**: ana `context.json`'da `sections[]` hiç yok, dolayısıyla
  `output/plan.dxf` artık 2 YENİ kesit paftası (`A-A KESITI`, `B-B KESITI`)
  içeriyor — bu FABRİKASYON değil, kullanıcının açıkça verdiği bir sistem
  standardının doğal sonucudur.
- **`crossing_walls`:** bir katın duvarlarından kesit hattını KESENLERİ
  (dik duran ve kesit konumunu Y/X aralığında kapsayan) bulur; kesit
  hattına PARALEL duran duvarlar (bilinen sınırlama) ve kesit konumuna
  ULAŞMAYAN kısa duvarlar (negatif test) dışlanır.
- **Genişletme noktası (kullanıcı talebi):** kesit alınırken kat
  yükseklikleri, galeri boşlukları veya merdivene denk gelen kısımların
  "zamanla güçlendirilebilir" olması istendi. Bugün bu senaryolar için
  PROJE VERİSİ yok; `SectionFeatureHook` Protocol'ü (`RailDrawingStandard`
  ile AYNI desen) tam olarak bu genişlemenin gireceği noktayı hazır tutar,
  çekirdek `SectionSheet.draw` değişmeden.
- **Plan işareti (kullanıcı talebi):** her kat paftasında kesit hattı +
  uçlarında bakış-yönü üçgeni + üçgenin SIRTINA yazılan kesit harfi
  (`draw_cut_marker_on_floor`). `AKS`ten BİLEREK farklı katman/linetype/
  renk (`KESIT`, `KESIT_HATTI`, kırmızımsı) — kullanıcı: *"farklı renkte ve
  desende çizgi."*
- **Pafta adı (kullanıcı talebi):** *"pafta ismine kesitin harfi verilir"*
  → `f"{cut.label} KESITI"` (örn. `"A-A KESITI"`).
- **`levels_from`:** kesit KENDİ kat yüksekliği istifini uydurmaz, bir
  `elevations[].id`den ödünç alır (verilmezse `elevations[0]`).
  **Invariant:** `floors[]` uzunluğu, hedef elevation'ın seviye sayısıyla
  BİREBİR eşit olmalı (kat↔seviye eşlemesi SIRAYLA yapılır) —
  `validate.py::check_sections` (açıkça bildirilen kesitler için) ve
  `SectionSheet.draw` (savunma amaçlı `ValueError`) bunu ikişer yerde
  denetler.

### DEV-025 — Kuzey oku + grafik ölçek çubuğu

- **Kuzey oku (`scripts/northarrow/`, YENİ modül):** kullanıcı açıkça
  *"kuzey oku için standart bir tasarım belirle, daha sonra tasarım
  değişikliğine gidildiğinde entegrasyon zor olmasın"* dedi — bu,
  `RailDrawingStandard` Protocol desenini DOĞRUDAN çağırdı:
  `NorthArrowStyle` Protocol'ü + `DefaultNorthArrowStyle` (daire + üçgen
  ibre + "K" etiketi). `meta.north_angle` (derece, saat yönünde, "yukarı"
  referansından) verilmezse ok HİÇ çizilmez — ana projede bu alan yok,
  dolayısıyla gerçek projede kuzey oku GÖRÜNMÜYOR (sıfır görsel etki);
  yalnızca yeni `golden/kesit_ornek` referansında (`north_angle=25`)
  sınandı.
- **Grafik ölçek çubuğu (`scripts/pafta::ScaleBar`, pafta'ya eklendi, YENİ
  modül GEREKMEDİ):** `meta.scale`den TÜRETİLEN, basılı çıktı küçültülüp/
  çoğaltılsa bile doğru ölçüyü koruyan standart bir öge. Segment uzunluğu
  (`nice_scale_length_m`) hedef ~20mm basılı genişliğe en yakın "nice"
  (1-2-5 serisi) gerçek-dünya metre değeridir (1:50→1m, 1:100→2m,
  1:200→5m, 1:500→10m, elle hesaplanabilir). **ScaleBar hiçbir opsiyonel
  veriye ihtiyaç duymadığı için** (sadece `meta.scale`) HER kat/görünüş/
  kesit paftasında OTOMATİK çizilir — bu da gerçek projeyi görsel olarak
  değiştirdi (her paftaya küçük bir ölçek cetveli eklendi).
- **Yerleşim:** her paftanın KUZEY (üst) kenarındaki padding bölgesinde,
  genişliğin TAM ORTASINDA — bu projede (ve `golden/duvar_standartlari`
  gibi mevcut fixture'larda) strüktürel akslar genelde kenarlarda olduğu
  için aks baloncuklarıyla çakışma riski düşüktür; piksel-kesin bir
  çakışmama GARANTİSİ yoktur (bilinen sınırlama, `pafta::CONTENT_PADDING`
  artışının çözdüğü rev-13 çakışmasıyla AYNI sınıf pragmatik yaklaşım).

### Doğrulama

- İki yeni self-test (`sections`, `northarrow` — ikincisi `pafta::
  ScaleBar`ı da sınar) — toplam ON modül self-test'i oldu.
- `py_compile`, `validate` (ana proje + `golden/kesit_ornek`), `generate`
  (`PaftaOverflowError` FIRLAMADI), `preview`, 5 semantik kural (`KESIT`
  katmanı `_code_owned_layers`e eklendi), 5 golden referans (4'ü
  `--update`, 1'i YENİ), `doc_check` — hepsi temiz.

### Golden output etkisi

- **Ana proje DEĞİŞTİ** (kullanıcının açık standardının doğal sonucu):
  `output/plan.dxf`e 2 yeni kesit paftası + her paftaya ölçek çubuğu
  eklendi; `docs/development/plan-golden-report.json` bu yüzden
  `--write` ile YENİDEN üretildi (rev-14/15'teki "sıfır görsel etki"
  emsalinin AKSİNE — bu değişiklik bilerek ve gözlemlenerek yapıldı).
- Mevcut 4 golden referansının TÜMÜ aynı sebeple değişti (`--update`).
- Yeni `golden/kesit_ornek`: 2 kat, FARKLI bölme duvarı x-konumuna sahip
  (4500 / 3000) — kesit hattının HER katta kendi duvarını doğru kestiğini
  (kat-başına bağımsız kesişim) hem elle hesaplanabilir hem entegrasyon
  seviyesinde kanıtlar; `meta.north_angle=25` ile kuzey oku de burada
  sınanır.

### Bilinen sınırlamalar

- `sections/`: eğik kesit yok (kullanıcı kararı); kesit hattına paralel
  duran duvar temsil edilemez; galeri boşluğu/merdiven kırılması için
  genişletme noktası hazır ama VERİ yok; seviye SIRASI doğrulanmaz (sadece
  SAYI eşitliği).
- `northarrow`/`ScaleBar`: aks baloncuklarıyla piksel-kesin çakışmama
  garantisi yok; elevations/sections'a kuzey oku çizilmez (kavramsal
  olarak anlamsız — bir düşey görünüşün/kesitin "kuzeyi" yoktur).

- **Sonraki direktif:** Kullanıcı ayrıca "kot (seviye/datum) verme
  mantığı"nın hem planda hem kesitte kullanılacağı için proje geneline
  hakim bir mantık olması gerektiğini, ayrı modül mü yoksa mevcut bir
  modül tarafından mı yönetilmesi gerektiğine karar verilemediğini
  belirtti. Bu, YENİ bir PLANNED görev olarak `DEV-029` altında
  `DEVELOPMENT_TASKS.md`ye eklendi (uygulama izni DEĞİLDİR — sistem
  mimarı açıkça seçmelidir).

## HD-010 — DXF duvar tarayıcısı ve kind-farkındalı rail standardı

- **Durum:** COMPLETED
- **Tamamlanma:** 2026-09-24
- **Görevler:** `DEV-013` ve `DEV-014` (kullanıcı: "dev 13 ve 14'ü yap").
- **Kapsam:** `scripts/importer/` (yeni modül, `import/`den yeniden
  adlandırıldı), `scripts/walls/standard.py` (yeni), `scripts/walls/
  render.py`, `scripts/walls/__init__.py`, `scripts/validate.py`,
  `schema/design.schema.json`, `golden/duvar_standartlari/` (yeni).

### İsim düzeltmesi: `import/` → `importer/`

Planlama sırasında modül `scripts/import/` olarak adlandırılmıştı.
Uygulamaya geçilince görüldü ki **`import` bir Python ANAHTAR
KELİMESİDİR** — `import import` bir `SyntaxError`dır, bu isim hiçbir zaman
geçerli bir paket olamazdı. `fixture` → `golden` (rev-11) ile AYNI
kategoride bir hata: planlama sırasında seçilen ad, kod yazılınca teknik
olarak kullanılamaz çıktı. Aynı çözüm uygulandı: dizin + tüm doküman
atıfları `importer/`e taşındı (`git mv`), `DEV-013` kimliği değişmedi.

### DEV-013 — `importer/`: `DxfWallScanner`

- Mevcut bir DXF'ten `LINE` çiftlerini tarar; üç koşulu (paralellik ≤10°,
  kalınlık 40–400mm, örtüşme oranı ≥0.5) geçen çiftleri, ELLE hesaplanabilir
  bir confidence formülüyle (`parallel_score * overlap_score`) duvar adayı
  olarak raporlar. Merkez çizgisi SADECE örtüşen aralıkta hesaplanır.
- **Desen:** `walls.scan::RoomPolygonScanner.suggest_wall_dicts` İLE AYNI —
  salt-okunur, context'e YAZMAZ. `WallCandidate.as_wall_dict()` şema-uyumlu
  bir sözlük üretir ama hiçbir yere OTOMATİK eklenmez; insan/agent
  onayından sonra normal talep akışıyla eklenir.
- **Yan kazanç:** `RoomPolygonScanner.suggest_wall_dicts` rev-1'den beri
  çıktısına `"kind"` koyuyordu ama şema bu alanı TANIMIYORDU — o aracın
  çıktısı hiçbir zaman gerçekten context'e eklenemezdi. `DEV-014`nin şema
  düzeltmesi bunu da kapattı.

### DEV-014 — `walls/`: `RailDrawingStandard`

- `CatalogRailStandard` (yeni sistem varsayılanı), `wall.kind`e göre
  `tugla_bolme` için `ANSI31` `HATCH`, `cam_duvar` için `CAM` linetype
  ekler; bilinmeyen/eksik `kind` `DefaultRailStandard`e (eski TEK yöntem,
  düz `LINE`) düşer.
- **Gerçek boşluk bulundu:** `WallCatalog`/`Wall.from_context` `kind`i HER
  ZAMAN okuyordu ama `schema/design.schema.json`nin `additionalProperties:
  false` olan `wall` tanımında YOKTU — hiçbir context.json bunu
  KULLANAMAZDI. Şemaya eklendi; `validate.py::check_walls` artık bilinmeyen
  bir `kind` değerini (yazım hatası) HATA sayar.
- **Geriye dönük uyumluluk ölçülerek doğrulandı:** hiçbir mevcut proje
  `kind` bildirmiyordu; `CatalogRailStandard`ı varsayılan yapmak `--golden-
  set` `--update` GEREKMEDEN geçti (sıfır görsel etki).
- **Yeni golden referansı `golden/duvar_standartlari`:** üç duvar türünü
  (varsayılan, tuğla, cam) VE bir kapı açıklığının tarama/linetype'ı doğru
  DIŞLADIĞINI (hatch 2 parçaya bölünür, kapı boşluğuna girmez) birlikte
  sınar.

### Doğrulama

- İki yeni self-test (`importer`, `walls`) — toplam SEKİZ modül self-test'i
  oldu. Her ikisi de elle hesaplanabilir örnekler + negatif testlerle.
- `py_compile`, `validate`, `generate`, `preview`, 5 semantik kural,
  4 golden referans, `doc_check` — hepsi temiz.

### Golden output etkisi

- Ana proje ve mevcut 3 golden referansı DEĞİŞMEDİ (hiçbiri `kind`
  kullanmıyor) — `--update` gerekmedi.
- Yeni `golden/duvar_standartlari` referansı eklendi (2 `HATCH`, `CAM`
  linetype'lı 4 rail parçası).

### Bilinen sınırlamalar

- `importer/`: sadece `LINE` taranır (`LWPOLYLINE` YOK); PDF/altlık
  (Fikir 2) uygulanmadı; köşe/T-kesişimi algılamaz.
- `walls/`: tarama deseni/ölçeği context'ten AYARLANAMAZ (kolonlardaki
  `meta.column_hatch` gibi); katalog kalınlıkları hâlâ kod seviyesinde
  (Fikir 2 uygulanmadı).

- **Sonraki direktif:** Planlanan modül kataloğu (`DEV-011`…`DEV-018`)
  TAMAMLANDI. Sıradaki iş, mevcut modüllerin ertelenen "Fikir 2"lerinden
  biri veya yeni bir modül fikridir — sistem mimarı açıkça seçmelidir.

## HD-009 — Mahal etiketi BLOCK+ATTRIB, cephe modülü ve kapı/pencere cetveli

- **Durum:** COMPLETED
- **Tamamlanma:** 2026-09-23
- **Görevler:** `DEV-018` → `DEV-011` → `DEV-012` (bu sırayla; `DEV-018`
  blok yaygınlaştırmasının `DEV-011`den önce ele alınması iş tekrarını
  önledi — `DEVELOPER_NOTES.md`de rev-13 sonunda kayıtlı öneriydi).
- **Kapsam:** `scripts/rooms/` (BLOK+ATTRIB + `selftest.py` yeni),
  `scripts/elevations/` (yeni modül, `generate_dxf.py`den taşındı),
  `scripts/legend/` (yeni modül, ilk taslak `CLAUDE.md`nin fikri DEĞİL,
  Fikir 1 uygulandı), `scripts/golden_report.py` (`_iter_all` yeni),
  `scripts/preview.py` (elevations/legend'ı import eder, kendi kopyasını
  tutmaz), `scripts/collision/scene.py`, `scripts/version.py`,
  `generate_dxf.py`, golden referansları (3'ü de `--update`).

### DEV-018 — mahal etiketi BLOCK+ATTRIB

- **Ölçülerek görüldü:** görev açılırken "hiç BLOCK kullanılmıyor" denmişti
  ama bu ölçüm `furniture` (`DEV-010`) BLOCK/INSERT kullanmaya başlamadan
  ÖNCEki bir kayıttı ve bayatlamıştı — ana projede tefriş YOK, bu yüzden
  `INSERT` sayısı hâlâ 0 görünüyordu, furniture kodu blok kullanmadığı için
  değil.
- Asıl boşluk mahal etiketiydi. `MAHAL_ETIKET` bloğu üç `ATTDEF`
  (`MAHAL_ADI`/`MAHAL_KOD`/`ALAN`) ile bir kez tanımlanır; `INSERT` ölçeği
  `fitted_height / NOMINAL_HEIGHT`tir. Bu, eski düz-`TEXT` formülüyle
  **doğrusal ölçekleme kanıtıyla** birebir örtüşür (her terim `height *
  sabit` biçimindedir) — `selftest.py`de `< 1e-6` toleransla doğrulandı.
- **Gerçek bir ezdxf tuzağı bulundu:** bir `INSERT`e bağlı `ATTRIB`ler DXF
  dosyasında GERÇEKTEN ayrı entity'lerdir (AutoCAD'de tek tek düzenlenebilir)
  ama ezdxf bunları genel layout iterasyonuna/`query()`'e DAHİL ETMEZ. Bu,
  `golden_report.py`nin ölçüm raporunu ve `rule_room_labels`i SESSİZCE kör
  ederdi. `_iter_all` yardımcısı (`for e in modelspace: yield e; if INSERT:
  yield from e.attribs`) eklenerek kapatıldı.
- Kat kodu VE mahal no'nun ikisi de eksikse (2 satır) blok kullanılmaz, eski
  düz-TEXT'e düşülür — blok 3 ATTDEF için SABİT yerleşimlidir.

### DEV-011 — `elevations/` modülü + below-ground linetype

- `generate_dxf.py` içine gömülü `draw_elevation`/`elevation_vertical_extent`
  kendi modülüne taşındı (`ElevationSheet`, `LevelStack`,
  `FacadeOpeningPlacer`, `Level`) — diğer tüm modüllerle aynı desen.
- **Kapatılan basitleştirme:** `below_ground: true` seviyelerin DXF'teki
  çizgi türü artık gerçekten `DASHED`tir (önceden sadece etiketle ayırt
  ediliyordu). `axis` modülü AYNI isimle aynı deseni yükler; iki modül
  birbirini import ETMEZ, her biri kendi `if name not in doc.linetypes`
  korumalı kaydını yapar.
- **Taşıma sırasında bulunan tutarsızlık:** `preview.py`nin kendi
  `elevation_vertical_extent` KOPYASI `machine_room` protrüzyonunu pafta
  Y-aralığı hesabına KATMIYORDU (gerçek DXF versiyonu katıyordu). Ortak
  `LevelStack`e geçince bu sessizce düzeldi.

### DEV-012 — `legend/` modülü: kapı/pencere cetveli

- **İki fikirden Fikir 1 seçildi.** Veri zaten hazırdı
  (`OpeningSchedule.from_openings`); `OpeningLegend.rows` bunu proje çapında
  (tip, varyant, genişlik) ile GRUPLAYIP `LegendRenderer.draw` ile gerçek bir
  MARKA/TİP/VARYANT/GENİŞLİK/ADET cetveli çizer. Ana projede 145 açıklık →
  10 grup (6 kapı + 4 pencere).
- **Açık karar kapandı — nereye çizilir:** kapak paftasının kapak bloğunun
  ÜSTÜNDE kalan, HER ZAMAN boş kalan alana (A4 kapak, daha uzun paylaşılan
  pafta Y-aralığı içinde). Ayrı pafta açılmadı.
- **Pencerede `VARYANT` sütunu `-`dir** — `openings/style.py` varyantı
  SADECE kapıda kullanır; pencerede "TEK KANAT" yazmak var olmayan bir
  ayrımı uydururdu.
- `preview.py` da AYNI `COLUMNS`/`COLUMN_WEIGHTS` sabitleriyle matplotlib
  karşılığını çizer (kök CLAUDE.md "önizleme DXF ile birebir" kuralı).

### Doğrulama

- Beş self-test (`collision`, `dimensions`, `axis`, `openings`, `rooms`) +
  yeni altıncı (`elevations`) — hepsi negatif ve yanlış-pozitif testli.
- `py_compile`, `validate`, `generate`, `preview`, 5 semantik kural,
  3 golden referans, `doc_check` — hepsi temiz.
- `legend` için ayrı `selftest.py` yok; doğrulaması `--golden-set`/`--rules`
  üzerinden dolaylıdır (gruplama hatası TEXT/LINE sayısına yansır).

### Golden output etkisi

- Mahal etiketi `INSERT`+`ATTRIB` oldu: ana projede 125 `TEXT`→`INSERT`+375
  `ATTRIB` (+125 entity toplamda, `METIN` layer'i +125).
- Kapı/pencere cetveli her paftaya (kapak paftası) çizgi+metin ekledi.
- `output/plan.dxf` entity sayısı ve `docs/development/plan-golden-report.json`
  ile 3 golden `expected.json` bu yüzden `--update`/`--write` ile yenilendi;
  fark açıklanabilir (yeni içerik, regresyon değil).

### Bilinen sınırlamalar

- `legend` modülünün Fikir 2'si (layer/sembol lejantı, `TitleBlockLegend`/
  `LayerSwatch`) uygulanmadı, açık fikir olarak duruyor.
- `elevations`de plandan açıklık türetme (Fikir 2) uygulanmadı.
- `elevations`de seviye sırası (zemin-altı seviyelerin listede ÖNCE gelmesi
  gerektiği) doğrulanmaz — context yanlış sıralanırsa cursor sessizce yanlış
  konum üretir.

- **Sonraki direktif:** `DEV-013` (`import/`, ileri faz) veya `DEV-014`
  (`walls/` genişletmesi) görevlerinden birini sistem mimarı açıkça
  başlatmalıdır.

## HD-008 — Ölçü zinciri, kısmi aks ve açıklık varyantları

- **Durum:** COMPLETED
- **Tamamlanma:** 2026-09-23
- **Görevler:** `DEV-017` → `DEV-015` → `DEV-016` (bu sırayla).
- **Kapsam:** `scripts/dimensions/` (bölündü + genişletildi), `scripts/axis/`
  (bölündü + genişletildi), `scripts/openings/` (bölündü + genişletildi),
  `scripts/collision/matrix.py`, `scripts/collision/selftest.py`,
  `scripts/pafta/__init__.py`, `scripts/golden_report.py`, `validate.py`,
  `generate_dxf.py`, `preview.py`, `schema/design.schema.json`,
  `context.json`, `golden/aciklik_varyantlari/` (yeni).

### Sıra neden bu

`dimensions` ÜRETİCİ, `axis` onun tek tüketicisiydi. Üretici önce
genişletilince aks, gelişmiş API'yi bir kez devraldı; tersi sırada iki kez
dokunmak gerekirdi. `openings` üçüncü seçildi çünkü rev-12'de **kendi
yazdığım bilinen sınırlamayı** kapatıyor: çakışma motoru "iki kapı birbirine
açılıyor" kontrolünü, açılım yönü schema'da olmadığı için muaf bırakmıştı.

### DEV-017 — ölçü zinciri

- `FloorOrdinates` üç kademede ordinat türetir: `aciklik` (cephedeki kapı/
  pencere kenarları), `mahal` (dik duvarların YÜZLERİ → net mahal + kalınlık),
  `toplam` (dıştan dışa). Üçü aynı ordinatlarda başlayıp biter.
- **Karar: ölçü TÜRETİLİR.** Ölçü sayısı tasarım verisi değil, geometrinin
  ölçüsüdür; elle yazmak aynı bilgiyi iki yerde tutmak olur ve ayrışır.
  Hangi kenarın ölçüleneceği ise sunum kararıdır (`meta.dimensions`).
- `ChainStack` kademelendirme yapar; `ChainLayout.verify_no_overlap` aynı
  baseline'a oturan iki zinciri artık **hata** sayar (önceden sessizce üst
  üste binerlerdi).
- **Çapraz nokta:** ölçü yığını ile aks baloncukları aynı kenarı paylaşır.
  Aks ölçü zinciri yığının DIŞINA taşındı (mimari sıra: içeride ayrıntılı,
  dışarıda kaba). İki modül birbirini import etmez; baloncuk yarıçapı
  parametre olarak verilir.
- **`CONTENT_PADDING` 3200 → 4000, ölçülerek.** İlk denemede üretim
  `PaftaOverflowError` ile durdu (`sol=300 sag=300`); artış tahminle değil,
  taşma korumasının verdiği sayıyla yapıldı. Pafta 67.0 → 70.2 cm.

### DEV-015 — kısmi/ara aks

- `Axis` tipli nesne oldu ve `extent` taşıyor. Kısmi aks kendi aralığında
  uzanır, uçlarına kendi baloncukları gelir ve **ulaşmadığı kenarın ölçü
  zincirine girmez**.
- **Karar: ara aks `1'`, `1A` değil.** Gerekçe çatışma: yatay aile zaten
  `A, B, C`; `1A` "1 ve A kesişimi" gibi okunur ve `on_axis_report`un ürettiği
  kolon adıyla (`B2`) çarpışır. Kural `naming.py`de yazılıp `validate.py`ye
  bağlandı.
- `AxisCoverageReport` salt okunur: aks'sız kolon hizalarını bildirir, aks
  EKLEMEZ.

### DEV-016 — açıklık varyantları

- Dört varyant (`single`/`double`/`sliding`/`folding`) + `swing` +
  `host_side`. **Üçünün de varsayılanı rev-12 davranışıdır.**
- **İki gerçek hata bulundu:**
  1. Açılım yayı `min/max` ile hesaplandığı için −X yönlü bir duvarda **270°**
     olurdu. `golden/minimal`da ucu ters verilmiş iki duvar zaten vardı; oraya
     bir kapı konduğu anda ortaya çıkacaktı. Yön artık çapraz çarpımla
     belirleniyor.
  2. `openings/collision.py`, `position_from_start`i açıklığın BAŞLANGICI
     sanıyordu; oysa MERKEZİDİR. Denetlenen sektör çizilen yaydan **yarım
     genişlik** (900'lük kapıda 450 mm) kayıktı. Artık boşluk aralığı çizimle
     aynı fonksiyondan (`walls.gaps_for_wall`) alınıyor.
- `geometry.py::swing_geometry` açılım yayının **tek sahibi**; çizim ve
  denetim aynı kaynaktan okur.
- Çakışma matrisinde **kapı ↔ kapı artık HATA**; sürme kapı açılım alanı
  üretmez. `rule_opening_symbols` varyant farkındası oldu ve beklenen yay
  sayısını `ARCS_PER_VARIANT` tablosundan okuyor.

### Doğrulama

- Dört self-test: `collision`, `dimensions`, `axis`, `openings` — hepsi
  negatif testlerle (kasıtlı bozma) ve yanlış-pozitif testleriyle.
- `py_compile`, `validate`, `generate`, `preview`, 5 semantik kural,
  3 golden referans, `doc_check` — hepsi temiz.
- **Yeni golden referansı `golden/aciklik_varyantlari`**: dört kapı varyantı,
  ucu ters verilmiş duvarlar, kesme işaretli kısmi aks (`2'`) ve açık ölçü
  yığını tek bir referansta birlikte sınanır.

### Golden output etkisi

`CONTENT_PADDING` değişikliği tüm paftaların bbox'ını, ölçü zincirleri ise
`minimal` dışındaki entity sayılarını değiştirdi; fark açıklanabilir olduğu
için `expected.json` dosyaları `--update` ile yenilendi.
`output/plan.dxf` 2228 → 2630 entity (+402 `DIMENSION`, layer `OLCU`).

### Bilinen sınırlamalar

- Eğik duvarlar ölçülendirmeye girmez (eksen hizalı bir zincire anlamlı
  ordinat veremezler).
- Ölçü yığını yalnızca **güney ve batı** kenarında çizilir; dört kenar için
  ayrı bir karar gerekir.
- Kısmi aks cephe izdüşümünde uygulanmaz (cephe o aksı yine de görür).
- Katlanır kapı sembolü tek kırılma noktalıdır; gerçek akordeon panel sayısı
  modellenmez.

- **Sonraki direktif:** `DEV-018` (DXF `BLOCK` yaygınlaştırma) veya `DEV-011`
  (`elevations/`) görevlerinden birini sistem mimarı açıkça başlatmalıdır.

## HD-007 — Çakışma denetimi motoru, sürüm kapısı ve provenance

- **Durum:** COMPLETED
- **Tamamlanma:** 2026-09-23
- **Kapsam:** `scripts/collision/` (yeni), `scripts/version.py` (yeni),
  `scripts/<modül>/collision.py` (5 sağlayıcı), `validate.py`,
  `generate_dxf.py`, `preview.py`, `pafta::CoverBlock`, `doc_check.py`,
  `schema/design.schema.json`, `context.json`, `golden/*`.
- **Görevler:** `DEV-019` ve `DEV-020`.

### DEV-019 — çakışma denetimi

- **Karar:** "Ayrı modül mü, her modül kendi mi" sorusu **arite** ile
  ayrıldı. Arite-1 ("kendi verim geçerli mi") ilgili modülde kaldı; arite-2+
  ("iki FARKLI eleman aynı yeri mi işgal ediyor") `scripts/collision/`
  motoruna gitti. Endüstri karşılığı: BIM'de modelleme aracı kendi disiplinini
  denetler, disiplinler arası clash ayrı bir araçtır (Navisworks *Clash
  Detective*, Solibri *Model Checker*).
- **Kritik tasarım — bağımlılık tersine çevrildi:** Motor hiçbir çizim
  modülünü import etmez; yalnızca anonim `CollisionShape(tag, id, polygon)`
  tanır. Her modül kendi ayak izini `collision.py::footprints(floor, context)`
  ile verir. Böylece **ayak izinin sahibi modül, çakışma kuralının sahibi
  motor** oldu ve modül bağımsızlığı korunurken kural tek yerde toplandı.
- **Kapının yeri:** `validate.py`, üretimden ÖNCE. Sebep hata mesajının
  dilidir: context seviyesinde rapor `f_koltuk3 ile f_koltuk2 cakisiyor
  (~1.360 m2, derinlik 850 mm)` der ve `context.json`'da düzeltilir; DXF
  seviyesinde `handle 2F4` derdi ve düzeltilemezdi.
- **Tolerans ALAN değil DERİNLİK:** 2100 mm'lik bir koltuk duvara 5 mm girse
  kesişim alanı 10500 mm² olur — alan eşiği eleman boyuyla ölçeklendiği için
  anlamsızdır. Kesişim çokgeninin kısa kenarına bakılır (`min_extent`);
  `CONTACT_TOLERANCE = 5 mm` altındaki girişim **temas**tır.
- **`golden_report.py`ye EKLENMEDİ:** Golden "çıktı değişti mi", çakışma
  "tasarım doğru mu" sorar. Birleştirilseydi bir golden referansı asla kasıtlı
  çakışma içeremezdi ve motorun kendisi test edilemezdi.
- **Yan kazanç — kopya kaldırıldı:** Sutherland–Hodgman kırpmasının bir
  KOPYASI `validate.py` içinde duruyordu. `collision/geometry.py` poligon
  matematiğinin tek sahibi oldu; iki kopya ayrışsa "oda çakışması" ile "tefriş
  çakışması" farklı cevaplar vermeye başlardı.

### DEV-020 — sürüm uyumu

- **Karar:** Kullanıcı modül bazlı eğilimini bildirdi; ayrım **amaca göre**
  yapıldı. **Sürümlenecek şey kod değil SÖZLEŞMEDİR** — rev-11'de `furniture/`
  beş dosyaya bölündü, etkilenen proje sıfır; oysa `furniture[].position`
  yeniden adlandırılsa her proje kırılır. Modül bazlı semver bir **paket
  deposunun** modelidir (bağımsız yayın temposu gerekir); burada modüller tek
  commit'te birlikte gider.
- **Sonuç:** `meta.schema_version` **kapı** (MAJOR farkta üretim durur, modül
  sözleşmelerinin türevi), modül `CONTRACT_VERSION` **teşhis**,
  `output/provenance.json` **kayıt**. İstenen şey aslında teşhisti ("koptu mu,
  neden") ve onu provenance yanıtlar, versioning değil.
- **Migrasyon asla otomatik değil:** otomatik migrasyon
  `requests.jsonl`/`rev_history` zincirini kırar ve provenance yalan söylemeye
  başlar. Major kırılımda proje normal bir revizyon olarak güncellenir.
- **Kademeli giriş:** alan bugün opsiyonel (yoksa `1.0.0` + uyarı); tüm
  context'ler taşıdıktan sonra `required` yapılacaktır.

### Kapak (kullanıcı talebi, `DEV-007`in çözülen kısmı)

- İmza alanları dörde sabitlendi: **MİMAR / BELEDİYE / YETKİLİ 1 / YETKİLİ 2**
  (2×2 yerleşim). Daha önce ikisi boş (`(UNVAN)`) bırakılmıştı.
- Kapak eteğine **üretim damgası** eklendi: solda `URETIM: <tarih saat>`,
  sağda `SISTEM: <schema sürümü>`. Damga, bilgi satırlarındaki `TARIH` ile
  AYNI ŞEY DEĞİLDİR — o proje/onay tarihidir, context'ten gelir ve uydurulmaz.
  Damga imza bandının altındaki boş şeride (iç çerçeveden 10 mm) oturur;
  ölçülerek doğrulandı (imza bandı alt kenarı −7850, damga −8350, iç çerçeve
  −8850 → her iki yandan 10'ar mm).
- `preview.py` aynı yerleşimi birebir yansıtır.

### Doğrulama

- `python scripts/collision/selftest.py` — kasıtlı bozulmuş katta tam 3 HATA
  + 1 UYARI; yanlış-pozitif testi ayrıca geçti. Kesişim ölçüsü elle
  doğrulanabilir (800 × 750 = 600000 mm², derinlik 750).
- Boru hattı negatif testleri: çakışma → `exit 1`, oda dışı → `exit 1`,
  MAJOR sürüm farkı → `exit 1`, MINOR fark → `exit 0` + uyarı.
- `doc_check.py`ye üç yeni kontrol eklendi (çakışma kapsamı, bayat
  `COLLISION_EXEMPT`, sözleşme sürümü); **üçü de kasıtlı bozmayla** sınandı.
- `validate` + `generate` + 5 semantik kural + 2 golden referans temiz.

### Golden output etkisi

Kapak altbilgisi her paftaya değil yalnızca kapağa eklendiği için her golden
referansında **tam +2 `TEXT`** (layer `METIN`) farkı oluştu; `modelspace_bbox`
değişmedi. Fark birebir açıklanabildiği için `expected.json` dosyaları
`--update` ile yenilendi (`minimal` 111→113, `tefris_kolon` 176→178).

### Bilinen sınırlamalar

- Çakışma yalnızca AYNI kat içinde aranır; katlar arası düşey hizalama
  denetlenmez.
- Kapı açılım **yönü** schema'da yok; iki kapının birbirine açılması bu yüzden
  `IGNORE` bırakıldı ve `DEV-016` sonrası `FORBID`e çekilmelidir.
- `counters[]` ayak izi üretmez (hâlâ `generate_dxf.py` içinde ad-hoc).
- Kapı sektörü 8 doğru parçasıyla yaklaşılır; gerçek yaydan biraz küçüktür.

- **Sonraki direktif:** Sistem mimarı `DEV-018` (DXF `BLOCK` yaygınlaştırma)
  veya `DEV-011` (`elevations/`) görevlerinden birini açıkça başlatmalıdır.

## HD-006 — Golden fixture kataloğu, tefriş modülü ve taralı kolonlar

> **rev-11 terminoloji notu:** Bu kayıttaki "fixture" artık **golden referans
> projesi** olarak adlandırılır; dizin `fixtures/` → `golden/`, beklenti dosyası
> `golden.json` → `expected.json`, CLI `--fixtures` → `--golden-set` oldu. Kayıt
> tarihsel olduğu için metni yeniden yazılmadı.

- **Durum:** COMPLETED
- **Tamamlanma:** 2026-09-23
- **Kapsam:** `scripts/golden_report.py` (yeniden yazıldı), yeni
  `scripts/furniture/`, yeni `scripts/columns/`, `scripts/generate_dxf.py`,
  `schema/design.schema.json`, `fixtures/` (rev-11'de `docs/` altından
  proje köküne taşındı).
- **Sonuç — DEV-006:** Golden kontrolü üç katmanlı oldu: ölçüm raporu +
  semantik kurallar + fixture koşucusu. Beş kural eklendi ve hepsi negatif
  testle doğrulandı. `entity_bbox` gerçek extent hesabına geçti; önceki sürüm
  `INSERT` için yalnızca ekleme noktasını döndürdüğü için bloklara geçişte
  rapor sessizce körleşecekti. İki fixture: `minimal`, `tefris_kolon`.
- **Sonuç — DEV-009:** 22 tipli konut tefriş kataloğu; tefriş her zaman DXF
  `BLOCK`. Beş işlevsel grup, her birine kahverengi ailesinden düşük
  kontrastlı layer rengi. Kapı/pencere sahipliği araştırıldı ve
  `openings/`+`walls/`ta kalmasına karar verildi (IFC ve AIA/NCS layer
  standardı).
- **Sonuç — DEV-010:** Taralı kolon; desen/ölçek dinamik, varsayılan
  `ANSI33` + `3.0`. Kesit kataloğu, dairesel/dikdörtgen kesit, dönme.
  İsimlendirme altyapısı hazır ama varsayılan kapalı; `meta.column_label`
  ile kod değişmeden açılıyor. `on_axis_report` kolonu aks kesişimiyle
  eşleyen salt-okunur rapor üretiyor.
- **Doğrulama:** `py_compile`, `validate.py`, `generate_dxf.py`,
  `preview.py`, golden karşılaştırması ve her iki fixture başarılı. Beş
  semantik kural tek tek bozularak yakaladıkları teyit edildi. Tefriş
  bloklarının yeniden kullanımı ölçüldü: 19 tanım → 23 `INSERT`. Hatch
  parametreleri (`ANSI33`, ölçek 3.0) ve grup renkleri DXF'ten okunarak
  doğrulandı.
- **Fixture'ların ilk günde yakaladığı iki gerçek sorun:** (1) Kapak
  paftasının projeye dayattığı asgari yükseklik (1:50'de içeriğin düşey
  açıklığı ≥ 8150 olmalı) — belgelenmemişti; (2) `draw_floor_sheet` içinde
  mahal etiketi `label_style` yerelinin kolon `label_style` parametresini
  gölgelemesi.
- **Golden output etkisi:** Gerçek proje çıktısı DEĞİŞMEDİ — tefriş ve kolon
  verisi `context.json`a eklenmedi (yerleşim proje verisidir ve uydurulmaz).
  Yetenekler `tefris_kolon` fixture'ında doğrulanır.
- **Açık sınır:** Tefriş/kolon için çakışma ve oda-içinde-kalma kontrolü YOK;
  kapı açılım alanı ile tefriş çakışması denetlenmiyor. `counters[]` hâlâ
  `generate_dxf.py` içinde ad-hoc çiziliyor. Katlar arası kolon hizalaması
  kontrol edilmiyor.
- **Sonraki direktif:** `DEV-018` (DXF `BLOCK` yaygınlaştırma — mahal etiketi
  bloğu/`ATTRIB`) veya `DEV-011 elevations` sistem mimarı onayıyla
  başlatılabilir.

## HD-005 — 3 satırlı mahal etiketi ve `typography` modülü

- **Durum:** COMPLETED
- **Tamamlanma:** 2026-09-23
- **Kapsam:** yeni `scripts/typography/`, `scripts/rooms/`,
  `scripts/pafta/` (font kaynağı), `scripts/generate_dxf.py`,
  `scripts/validate.py`, `schema/design.schema.json`, `context.json`.
- **Sonuç:** Mahal etiketi kullanıcı şartnamesine göre **3 satır** oldu
  (mahal adı BLOK / kat kodu-mahal no / alan). Kat kodu `floors[].code`'dan,
  mahal no `rooms[].no`'dan gelir; ikisi de türetilmez. Sığdırma artık hem
  genişliğe hem **yüksekliğe** bakıyor. Proje fontu Arial Narrow'a geçti:
  yeni `typography` modülü fontu `Standard` text style'ına yazarak tek
  noktadan tüm metinlere uyguluyor, `pafta.DEFAULT_FONT` ise ikinci bir sabit
  tutmak yerine bu modülden import ediyor (çizilen font ile ölçülen fontun
  ayrışması engellendi). `meta.fonts.room_label` ile mahal etiketine ayrı
  font seçilebilir.
- **Doğrulama:** `py_compile`, `validate.py`, `generate_dxf.py`,
  `preview.py` ve semantic golden karşılaştırması başarılı. **125/125 mahal
  etiketinin** gerçek font metrikleriyle ölçülen bounding box'ı kendi oda
  poligonunun içinde kaldı. Mahal no ve kat kodu benzersizlik kontrolleri
  `validate.py`ye eklendi ve negatif testle (kasıtlı çakışma) doğrulandı.
  `arialn.ttf` ile `arial.ttf` ölçümlerinin farklı olduğu, `"ArialNarrow"`
  aile adının ise sessizce Arial'e düştüğü ölçülerek teyit edildi.
- **Golden output etkisi:** TEXT 339 → 589 (+250 = 125 oda × 2 ek satır),
  `METIN` layer 177 → 427, toplam entity 1976 → 2226. Geometri (duvar,
  açıklık, aks, çerçeve) değişmedi.
- **Açık sınır:** `RoomLabelStyle` Protocol'ü ve leader'lı yerleşim
  uygulanmadı (kullanıcı fikirlerden birini seçmedi, şartname doğrudan
  uygulandı). Arial Narrow bir TTF'tir; çizimi açan makinede font yoksa
  metin genişlikleri kayar — bu bilinen bir sınırdır.
- **Sonraki direktif:** `DEV-006 Golden fixture kataloğu` (amacı rev-9'da
  genişletildi) veya `DEV-009 tefriş modülü` sistem mimarı onayıyla
  başlatılabilir.

## HD-004 — Tip-A kapak paftası (`CoverBlock`) ve `Sheet` özel-pafta desteği

- **Durum:** COMPLETED
- **Tamamlanma:** 2026-09-23
- **Kapsam:** `scripts/pafta/` (`CoverBlock`, `Sheet.draw` genişletmesi),
  `scripts/generate_dxf.py`, `scripts/preview.py`, `schema/design.schema.json`.
- **Sonuç:** ISO 7200 Tip-A kapak bloğu `CoverBlock` olarak uygulandı; ölçüler
  `to_modelspace(...)` ile projenin ölçeğinden türetilir, böylece kapak ölçekli
  çıktıda her zaman tam A4 (210x297mm) basar. Kapak paftası **özel pafta**
  olarak tanımlandı: dış çerçeve genişliği kapak genişliğine eşittir
  (`padding=0`), blok paftanın sağ-altına sabitlenir, Tip-B şerit anteti
  çizilmez ve kapak çerçevesi her kenardan eşit offsetlidir. `Sheet.draw`
  bunun için `title_box`, `padding` ve `frame_gap` override'ları aldı;
  `CoverBlock.draw` ise `outer_frame` parametresiyle çift çizimi önler.
  `schema`ya `meta.cover` eklendi (`architect_name`, `date`,
  `signature_fields`).
- **Doğrulama:** `py_compile`, `python scripts/validate.py`,
  `python scripts/generate_dxf.py`, `python scripts/preview.py` ve semantic
  golden karşılaştırması başarılı. Ek olarak DXF geometrisi üzerinden 9
  otomatik kontrol (pafta genişliği = kapak genişliği, A4 panel ölçüsü, eşit
  offset, antet yokluğu, pafta bitişikliği, ortak yükseklik, çift çizim
  olmaması) ve 4 farklı ölçekte (1:20/1:50/1:100/1:200) "çıktıda 210x297mm"
  doğrulaması yapıldı. 1:200 ile kapak paftaya sığmadığında üretimin
  `PaftaOverflowError` ile durduğu, sessiz hatalı DXF üretilmediği test edildi.
- **Golden output etkisi:** `output/plan.dxf` yeniden üretildi ve semantic
  golden raporu güncellendi; mevcut kat planı/görünüş geometrisi korunmuştur.
- **Açık sınır:** Kapağın resmi verisi (`architect_name`, `date`, ayrılmış iki
  imza alanının unvanı) kullanıcıdan gelmedi; uydurulmadı, elle doldurulacak
  çizgi olarak bırakıldı (`DEV-007`). Kapak **tasarımı** için kullanıcı ayrı
  bir talep paylaşacak — o talepte geometri (A4, sağ-alt sabitleme, eşit
  offset, antetsiz pafta) değişmemelidir. Çok küçük ölçeklerde kapak bloğu
  için otomatik yeniden yerleşim stratejisi yoktur; yalnızca taşma hatası
  verilir.
- **Sonraki direktif:** `DEV-006 Golden fixture katalogu` görevini sistem
  mimarı onayıyla başlatmak; `DEV-008 RoomLabeler yapısı` PLANNED olarak
  beklemektedir.

## HD-002 — Agentic kontrol ve kabul altyapısı

- **Durum:** COMPLETED
- **Tamamlanma:** 2026-09-23
- **Kapsam:** görev kilidi, rol izinleri, reviewer ayrımı, provenance ve
  semantic golden-output raporu.
- **Sonuç:** `development_control.py` atomik görev kilidi sağlar;
  `AGENT_PERMISSIONS.json` rol alanlarını tanımlar; `PROVENANCE_TEMPLATE.json`
  revizyon izini standartlaştırır; `golden_report.py` entity türleri, layer,
  bounding box ve hash raporu üretir.
- **Doğrulama:** Python derlemesi ve kilit aracının `status` smoke testi
  başarılıdır. Proje validation/generation davranışı değiştirilmemiştir.
- **Golden output etkisi:** Mevcut `output/plan.dxf` için ilk semantic referans
  raporu oluşturulacaktır; byte hash tek kabul ölçütü değildir.
- **Bilinen durum:** OS seviyesinde klasör izinleri değil, proje içi agent
  protokolü ve görev kilidi uygulanır. Sistem dışı yetki mekanizması sonraki
  deployment kararıdır.
- **Sonraki direktif:** Sistem mimarı onayıyla `DEV-001 openings` görevini
  kilit alarak başlatmak.

## HD-003 — Openings, Rooms ve Dimensions modülleri

- **Durum:** COMPLETED
- **Tamamlanma:** 2026-09-23
- **Kapsam:** `scripts/openings/`, `scripts/rooms/`,
  `scripts/dimensions/` ve Axis/Wall/Generator entegrasyonları.
- **Sonuç:** Typed opening görünümü ve schedule, host-wall/açıklık genişliği
  doğrulaması, units-aware room alan/self-intersection doğrulaması,
  `RoomLabeler`, `DimensionChain`, `LinearDim`, `DimensionStyle` ve bounds
  kontrollü `ChainLayout` uygulandı.
- **Doğrulama:** package import, `py_compile`, `python scripts/validate.py`,
  `python scripts/generate_dxf.py` ve semantic golden karşılaştırması başarılı.
- **Golden output etkisi:** `output/plan.dxf` entity/layer/bbox semantic raporuyla
  eşleşti; mevcut örnek geometrisi korunmuştur.
- **Açık sınır:** Swing/variant/host_wall_id gibi yeni schema alanları
  eklenmedi; mevcut `wall_id` sözleşmesi korunmuştur.
- **Sonraki direktif:** `DEV-006 Golden fixture katalogu` görevini sistem
  mimarı onayıyla başlatmak.

## HD-001 — AxisGrid modül izolasyonu

- **Durum:** COMPLETED
- **Tamamlanma:** 2026-09-22
- **Kapsam:** `scripts/axis/` ve `scripts/generate_dxf.py`
- **Sonuç:** `AxisGrid`, `AxisDrawingStandard` ve `ensure_axis_layer`
  generator içinden izole modüle taşındı. Floor/elevation izdüşümü, baloncuk
  teğetliği, sabit AKS layer standardı ve geçici ölçü zincirleri korundu.
- **Doğrulama:** `py_compile` başarılı; `python scripts/validate.py` başarılı;
  `python scripts/generate_dxf.py` başarılı.
- **Golden output etkisi:** `output/plan.dxf` validate edilmiş pipeline ile
  yeniden üretildi. İlk anlamlı entity/geometri golden karşılaştırması sonraki
  kalite çalışmasında ayrıca otomatikleştirilecek.
- **Bilinen durum:** Örnek proje, sistem geliştirmesi öncesinde üretildiği için
  1:100 ölçek mevzuat uyarısı taşır. Bu tarihsel örnek durumudur ve sistem
  mimarisini bloke etmez.
- **Sonraki direktif:** `openings/` sözleşmesini sistem mimarı onayıyla
  uygulama fazına almak.
