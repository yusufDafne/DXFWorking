# Geliştirici Notları

Bu dosya bir sonraki geliştiricinin ilk okuyacağı canlı çalışma notudur. Her
çalışma sonunda mevcut durum, ilk ucuz kontrol, açık kararlar ve sonraki
sistem mimarı direktifi güncellenir.

## Mevcut durum

- `pafta/`, `walls/` ve `axis/` tamamlandı.
- `AxisGrid` generator'dan `scripts/axis/` içine taşındı.
- Faz dosyaları kalıcı çalışma kaydı olarak kullanılmaz; tamamlanan işler
  `DEVELOPMENT_HISTORY.md`ye eklenir.
- Proje örneğinin 1:100 mevzuat uyarısı rev-8'de giderildi (ölçek 1:50);
  geçmiş HD kayıtlarındaki 1:100 notları tarihsel bağlamdır.
- Görev eşzamanlılığına karşı `development_control.py` atomik kilidi eklendi;
  aynı anda iki agent görev alamaz.
- Golden semantic raporu ve provenance şablonu eklendi; byte hash tek başına
  kabul ölçütü değildir.
- `openings/`, `rooms/` ve `dimensions/` modülleri generator akışına entegre
  edildi; pipeline ve semantic golden kontrolü başarılı.
- Proje `1:50` mevzuat ölçeğine geçirildi; `classify_violation(...)` artık
  uyarı üretmiyor ve en yüksek pafta (67.0 cm) 90'lık rulonun 88 cm net
  yüksekliğine sığıyor.
- `pafta::CoverBlock` eklendi: kapak paftası ÖZEL paftadır — kapak bloğu
  paftanın iç çizgisinin sağ-alt köşesine sabitlenir (katlandığında üste
  gelsin diye), pafta genişliği kapak genişliğine eşitlenir, bu paftada
  Tip-B antet çizilmez (`Sheet.draw(..., title_box=False)`) ve kapak
  çerçevesi her kenardan eşit offsetlidir. Blok, çıktı hangi ölçekte
  alınırsa alınsın kağıtta tam A4 basar (4 ölçekte doğrulandı).
  `meta.cover` (opsiyonel `architect_name`, `date`, `signature_fields`)
  schema'ya eklendi; verilmeyen resmi alanlar uydurulmaz, doldurma çizgisi
  olarak bırakılır.
- `scripts/preview.py` artık kapak paftasını da (aynı sırada ve aynı A4
  ölçüsünde) çiziyor; önizleme pafta sırası DXF ile birebir.
- Mahal adları ve `area_m2` mevcut `RoomLabeler` ile çizilmeye devam ediyor;
  yapısının geliştirilmesi `DEV-008` olarak planlandı (kullanıcı talebi).
- **`scripts/collision/` eklendi (rev-12):** çakışma denetimi artık
  `validate.py` içinde, üretimden ÖNCE çalışan BLOKLAYICI bir kapıdır. Motor
  hiçbir çizim modülünü import etmez; `rooms`, `walls`, `columns`, `openings`
  ve `furniture` kendi `collision.py` ayak izi sağlayıcılarını taşır.
  `collision/geometry.py` poligon matematiğinin tek sahibi oldu —
  `validate.py` içindeki Sutherland–Hodgman kopyası kaldırıldı.
- **`scripts/version.py` eklendi (rev-12):** `meta.schema_version` bloklayıcı
  KAPI (MAJOR farkta üretim durur), modül `CONTRACT_VERSION` TEŞHİS,
  `output/provenance.json` KAYIT. Alan bugün opsiyonel; yoksa `1.0.0`
  varsayılır ve UYARI basılır.
- **Kapak (rev-12):** imza alanları dörde sabitlendi (MİMAR / BELEDİYE /
  YETKİLİ 1 / YETKİLİ 2, 2×2) ve kapak eteğine üretim damgası eklendi
  (`URETIM: <tarih saat>` / `SISTEM: <schema sürümü>`). `preview.py` aynı
  yerleşimi yansıtır.
- **Ölçü zinciri AÇIK (rev-13):** `meta.dimensions` ile kat paftalarında üç
  kademeli ölçü yığını (`aciklik` / `mahal` / `toplam`) çiziliyor. Ölçü
  sayıları **geometriden türetilir**, context'te yazılı değildir. Aks ölçü
  zinciri yığının dışına taşındı; `pafta::CONTENT_PADDING` 3200 → 4000 oldu
  (taşma korumasının verdiği ölçüyle) ve pafta 67.0 → 70.2 cm'e çıktı.
- **Kısmi/ara aks (rev-13):** `grid.*_axes[].extent` ile bir aks yalnızca
  bildirilen aralıkta uzanabiliyor; ara aks `1'` yazılıyor ve etiket kuralı
  `validate.py` tarafından denetleniyor.
- **Kapı varyantları (rev-13):** `variant` / `swing` / `host_side`. Üçünün de
  varsayılanı rev-12 davranışı olduğu için mevcut proje aynı çizimi üretir.
  Çakışma matrisinde **kapı ↔ kapı artık HATA**.
- **ON modül self-test'i var** ve üretimden sonra hepsi çalıştırılmalıdır:
  `collision`, `dimensions`, `axis`, `openings`, `rooms`, `elevations`,
  `walls`, `importer`, `sections`, `northarrow`.
- **rev-17: `DEV-021` (`sections/`) ve `DEV-025` (`northarrow/` +
  `pafta::ScaleBar`) tamamlandı (`HD-011`).** Kesit hattı her zaman aks
  ailesine paralel (kullanıcı kararı); `sections[]` hiç verilmezse X+Y'den
  birer varsayılan kesit (1/3 nokta, tam merkez DEĞİL) üretilir — bu, ANA
  PROJEYİ de değiştirdi (2 yeni kesit paftası otomatik çıkıyor). `ScaleBar`
  sadece `meta.scale`den türediği için HER paftaya (kat+görünüş+kesit)
  otomatik eklendi. `NorthArrow` `meta.north_angle` yoksa hiç çizilmez —
  ana projede bu alan yok, kuzey oku GÖRÜNMÜYOR (sadece yeni
  `golden/kesit_ornek` referansında sınandı). Kullanıcı ayrıca "kot/datum"
  mantığının proje geneline hakim, çapraz-kesit bir konu olduğunu belirtti;
  bu `DEV-029` olarak PLANNED eklendi, henüz uygulanmadı.
- **rev-18: 3 kullanıcı geri bildirimi işlendi (`HD-012`).** (1) AutoCAD
  "Large, Dense Hatch Patterns" uyarısının kök nedeni bulundu ve düzeltildi
  (`sections`'taki kesit-duvar dolgusu `set_pattern_fill("SOLID")`
  kullanıyordu — GERÇEK bir solid-fill DEĞİLDİ, `set_solid_fill()`e
  çevrildi). (2) Aks ölçü zinciri artık AKS ile AYNI katmanda (`ezdxf`
  1.4.4'ün render-sonrası katman düşürme hatası düzeltildi) VE bir kenarda
  2'den fazla aks varsa ardışık mesafelerin YANINA en-uçtaki-toplam mesafe
  zinciri eklendi. (3) `ScaleBar` (rev-17'de eklenen grafik ölçek çubuğu)
  kullanıcı isteğiyle TAMAMEN KALDIRILDI; `meta.dimensions.enabled` gerçek
  projede `false`ya çekildi (duvar/oda ölçüleri aks ölçüsünün yanında kafa
  karıştırıyordu) — özellik `golden/aciklik_varyantlari`de sınanmaya
  devam ediyor, sadece bu projenin sunum tercihi değişti.

## Sıradaki iş

`DEVELOPMENT_TASKS.md` artık **her modül için ayrı plan maddesi** tutuyor
(`DEV-007` … `DEV-017`) ve her maddede seçilmek üzere **iki fikir** var.

rev-12 durumu:

- `DEV-006` **COMPLETED** — golden artık üç katmanlı (ölçüm + semantik kural +
  golden referans koşucusu), bkz. `HD-006`.
- `DEV-008` **COMPLETED** — 3 satırlı mahal etiketi + `typography` (`HD-005`).
- `DEV-009` **COMPLETED** — tefriş modülü, tefriş = DXF `BLOCK` (`HD-006`).
- `DEV-010` **COMPLETED** — taralı kolon, dinamik hatch (`HD-006`).
- `DEV-007` **BLOCKED** — yalnızca kullanıcıdan gelecek mimar adı / tarih /
  unvan bekleniyor. Kullanıcı rev-12'de "konusunu tekrar açma, plan olarak
  kalsın" dedi; bu madde SORULMAZ, kullanıcı kendisi açacaktır.
- `DEV-019` **COMPLETED (rev-12)** — `scripts/collision/`; arite-1 modülde,
  arite-2+ motorda; motor çizim modüllerini import etmez (`HD-007`).
- `DEV-020` **COMPLETED (rev-12)** — `scripts/version.py`; kapı/teşhis/kayıt
  ayrımı, `output/provenance.json` (`HD-007`).
- `DEV-015` **COMPLETED (rev-13)** — kısmi/ara aks, etiket kuralı, kolon
  rasteri kapsama raporu (`HD-008`).
- `DEV-016` **COMPLETED (rev-13)** — 4 kapı varyantı + açılım yönü; iki gerçek
  hata düzeltildi (270°'lik yay, yarım genişlik kayık sektör) (`HD-008`).
- `DEV-017` **COMPLETED (rev-13)** — türetilen 3 kademeli ölçü yığını +
  kademelendirme (`HD-008`).
- `DEV-018` **COMPLETED (rev-14)** — mahal etiketi `MAHAL_ETIKET` bloğu +
  `ATTRIB` (`MAHAL_ADI`/`MAHAL_KOD`/`ALAN`); `ensure_room_label_block`
  idempotent, `add_auto_attribs` ile doldurulur. `golden_report.py::
  _iter_all` eklendi (ezdxf ATTRIB'i genel iterasyona dahil etmiyor) (`HD-009`).
- `DEV-011` **COMPLETED (rev-14)** — `scripts/elevations/` (yeni modül);
  below-ground `DASHED` linetype gerçekten uygulandı (`HD-009`).
- `DEV-012` **COMPLETED (rev-14)** — `scripts/legend/` (yeni modül); kapı/
  pencere cetveli kapak paftasının boş üst alanında (`HD-009`).
- `DEV-013` **COMPLETED (rev-15)** — `scripts/importer/` (yeni modül,
  `import/`den yeniden adlandırıldı — `import` Python anahtar kelimesi);
  `DxfWallScanner` salt-okunur duvar adayı raporlar (`HD-010`).
- `DEV-014` **COMPLETED (rev-15)** — `scripts/walls/standard.py`;
  `CatalogRailStandard` `tugla_bolme`/`cam_duvar` için gerçek görsel ayrım
  (hatch/linetype); şemaya eksik olan `wall.kind` alanı eklendi (`HD-010`).
- **Planlanan modül kataloğu (`DEV-011`…`DEV-018`) TAMAMLANDI.**

**Önemli işletim notu:** Üretimden sonra artık
`python scripts/golden_report.py output/plan.dxf --rules context.json`,
`python scripts/golden_report.py --golden-set` ve **ON modül self-test'i**
(`collision`, `dimensions`, `axis`, `openings`, `rooms`, `elevations`,
`walls`, `importer`, `sections`, `northarrow`) da çalıştırılmalıdır. Ölçüm
raporunun tek başına yetmediği rev-10'da somut olarak gösterildi; çakışma
motorunun "temiz döndü" çıktısı da tek başına hiçbir şey kanıtlamaz (motor
hiç çalışmasa da temiz dönerdi), bu yüzden self-test kasıtlı bozulmuş bir
kat üzerinde beklenen bulguların TAM OLARAK üretildiğini sınar.

Planlanan modül kataloğunun TAMAMI (`DEV-011`…`DEV-020`) VE rev-17'de
seçilen ilk iki "endüstri standardı boşluk" maddesi (`DEV-021`, `DEV-025`)
tamamlandı. `DEVELOPMENT_TASKS.md::PLANLANAN GÖREVLER` içinde
`DEV-022`…`DEV-024`, `DEV-026`…`DEV-029` (kot/datum mantığı, rev-17'de
kullanıcı tarafından eklendi) hâlâ seçilmeyi bekliyor. Sistem mimarı
açıkça başlatmadan kod değişikliği yapılmaz. Başlangıçta görev kilidi
alınmalıdır.

**2026-09-25 durumu:** Kullanıcı "planlanmış tüm planları uygula" istedi;
kök `CLAUDE.md`nin "PLANLANAN = uygulama izni değildir, tek tek seçilip
yönlendirilir" kuralıyla çelişki agent tarafından açıkça bildirildi ve
kullanıcı **"sırayla, tek tek"** ilerlenmesini onayladı (her görev kendi
Fikir1/Fikir2/açık kararlar analiziyle, tek IN_PROGRESS, validate+golden+
doc_check ile). Ayrıca kullanıcı katman RENK çeşitlendirmesi eksikliğini
fark etti; bu **`DEV-030`** olarak `DEVELOPMENT_TASKS.md`ye eklendi (somut
bulgu: `columns/standard.py::COLUMN_RGB` üç farklı katmana — `KOLON`/
`KOLON-TARAMA`/`KOLON-METIN` — TEK renk atıyor; `furniture/groups.py` ise
zaten iyi bir örnek, 5 farklı kahverengi tonu) — **implementasyon YOK,
yalnızca plan**; hangi Fikrin (merkezi olmayan / merkezi kontrolör modülü)
uygulanacağı kullanıcının ihtiyaca göre vereceği ayrı bir karardır.

**`DEV-022` COMPLETED (aynı oturumda):** kullanıcı Fikir 1'i (yeni bağımsız
`scripts/stairs/` modülü) ve rıht/going/auto_flex varsayılanlarını (170mm/
270mm/açık) seçti; modül, schema, `validate.py::check_stairs`,
`generate_dxf.py` entegrasyonu, `golden/merdiven_ornek` izole referansı ve
10 self-test kontrolü tamamlandı — ayrıntı `HD-013`. Geliştirme sırasında
GERÇEK bir X/Y ekseni takası hatası bulunup düzeltildi (bkz. `HD-013` "Kök
neden" bölümü) ve bunu yakalayacak bir koordinat-doğruluğu testi eklendi —
eski `check_draw_entity_counts` yalnızca SAYI doğruluyordu, koordinat değil.
Gerçek projenin `Merdiven` odası (4000×3000mm) tek düz kollu merdiven için
`StairFitError` ile REDDEDİLDİ (fiziksel olarak yetersiz) — bu yüzden
`context.json`a henüz `stairs[]` verisi eklenmedi, sistem mimarının kararı
bekleniyor (oda büyütülsün mü, çok kollu merdiven desteği mi eklensin).
Bağımsız reviewer/validator geçişi ayrı bir Agent çağrısıyla yapıldı ve
GERÇEK ikinci bir hata buldu: `MIN_GOING_MM` kontrolü yalnızca going'in
otomatik daraltıldığı dalın içindeydi — oda zaten sığıyorsa açıkça verilmiş
güvensiz bir `going_mm` sessizce geçiyordu. Düzeltildi (kontrol artık
koşulsuz, `MAX_GOING_MM` de ilk defa gerçekten kullanılıyor) + 2 yeni
selftest eklendi (10 → 12), bkz. `HD-013`. Reviewer'ın işaret ettiği
"DEV-022'nin DEVELOPMENT_TASKS.md'de COMPLETED bölümünde maddesi yok"
bulgusu paralel doküman düzenlemesinden kaynaklı bir ANLIK yarış durumuydu
(agent DEVELOPMENT_TASKS.md'yi ben hâlâ düzenlerken okumuş) — mevcut
durumda `### DEV-022` maddesi COMPLETED altında gerçekten var ve
`doc_check.py` temiz dönüyor.

**`DEV-030` COMPLETED (aynı oturumun devamı, kullanıcı "29 ve 30. planları
uygula" dedi):** kullanıcı Fikir 2'yi (merkezi `scripts/palette/` modülü)
seçti. `axis`/`columns`/`sections`/`stairs`/`furniture` artık RGB
sabitlerini `palette.color_for(...)`den alıyor; `KOLON`/`KOLON-TARAMA`/
`KOLON-METIN` DEV-030'un kurulma nedeni olan somut bulgu (üçü aynı renkti)
düzeltilerek üç FARKLI tona ayrıldı — ayrıntı `HD-014`. `golden_report.py`
renk değişikliğini YAKALAMADIĞI (yalnızca entity/layer sayısı + bbox
kaydeder) belgelendi, bu bir DEV-030 regresyonu DEĞİL, önceden var olan bir
kör nokta. Sıradaki: `DEV-029` (kot/datum, `scripts/levels/`) — kullanıcı
Fikir 1'i (yeni bağımsız modül) ve kot formatını ("+3.00"/"-0.20"/"±0.00")
onayladı, bu oturumda devam ediliyor.

## İlk okuma sırası

1. Bu dosya.
2. `DEVELOPMENT_TASKS.md`.
3. `DEVELOPMENT_HISTORY.md`.
4. `scripts/CLAUDE.md` ve ilgili modül sözleşmesi.
5. `scripts/generate_dxf.py`, schema ve mevcut golden output.
6. `docs/development/AGENT_PERMISSIONS.json` ve
   `PROVENANCE_TEMPLATE.json`.

## İlk ucuz kontrol

Openings değişikliğinden önce mevcut `WallNetwork` açıklık boşlukları ve
`DefaultPlanOpeningStyle` için mevcut DXF entity/layer davranışını çıkar.
Açıklık schema alanları mevcut `additionalProperties: false` sözleşmesiyle
uyumlu değilse uygulamayı durdur ve sistem mimarı kararı iste.

## Açık kararlar

- `host_wall_id` mevcut schema'ya nasıl ve ne zaman eklenecek?
- Opening position duvar başlangıcına göre mi, merkez noktasına göre mi
  tanımlanacak?
- Swing/menteşe bilgisi zorunlu mu, yoksa ayrı bir revizyon mu?
- Cephe açıklıkları plan opening stilini mi tüketir, ayrı bir stil mi kullanır?
- İlk golden-output otomasyonu hangi entity ve geometrik alanları kapsar?
- Reviewer raporu hangi ayrı çalışma çağrısında üretilecek?
- `meta.cover.architect_name` ve `meta.cover.date` değerleri ne olacak?
  (Kapak çizilir durumda; bu iki alan boş doldurma çizgisi olarak çıkıyor.)
  **Kullanıcı rev-12'de bu konunun AÇILMAMASINI istedi** — agent sormaz,
  kullanıcı kendisi verecektir.
- ~~Ayrılmış iki imza alanının unvanı ne olacak?~~ **rev-12'de çözüldü:**
  dört alan — MİMAR / BELEDİYE / YETKİLİ 1 / YETKİLİ 2.
- Kapakta ruhsat/onay alanları da gerekli mi?
- Kapak TASARIMI için kullanıcıdan ayrı bir talep bekleniyor (geometri
  sabit kalmalı: A4, sağ-alt sabit, eşit offset, antetsiz).
- Mahal etiketi de blok + `ATTRIB` olacak mı (`DEV-018`)?
- `counters[]` (mutfak tezgahı) `furniture/` modülüne devredilecek mi?
  Bugün iki yol da mümkün, bu bir çifte sorumluluktur.
- ~~Çakışma denetimi ayrı modül mü, her modül kendi mi?~~ **rev-12'de
  UYGULANDI** (`HD-007`): arite ile ayrılır — tekil doğrulama modülde, çift
  (çakışma) denetim `scripts/collision/` motorunda; motor çizim modüllerini
  import etmez. Duvar ayak izi merkez çizgi + kalınlık oldu, kapı sektörü 8
  sabit parçayla yaklaşılıyor.
- ~~Kapı açılım yönü schema'da yok.~~ **rev-13'te kapandı** (`DEV-016`);
  kapı ↔ kapı kontrolü artık HATA.
- Ölçü yığını bugün yalnızca **güney ve batı** kenarında çiziliyor. Dört kenar
  istenirse ayrı bir karar (ve yığın yönü) gerekir.
- Eğik duvarlar ölçülendirmeye girmiyor; eksen hizalı olmayan bir yapı
  geldiğinde bu yeniden ele alınmalıdır.
- Katlanır kapı sembolü tek kırılma noktalıdır; gerçek akordeon panel sayısı
  modellenmiyor.
- `PROVENANCE_TEMPLATE.json` ile `output/provenance.json` şu anda İKİ AYRI
  şemadır; şablon `DEV-005`ten kalma kabul/rol alanlarını da taşıyor.
  Birleştirilecek mi, yoksa şablon kabul kaydı olarak ayrı mı kalacak?
- `meta.schema_version` ne zaman `required` yapılacak? (Bugün opsiyonel ve
  eksikse uyarı basılıyor; tüm context'ler alanı taşıyor.)
- Kolonlarda katlar arası düşey hizalama zorunlu tutulacak mı?
- "Mahal ismi blok olarak işlensin" büyük harf olarak uygulandı; kullanıcı
  DXF `BLOCK` entity'si kastettiyse bu yeniden ele alınmalı.
- Mahal no bugün kat içinde sıralı (`01`, `02`…). Daire bazlı anlamlı bir
  numaralandırma (örn. A dairesi 01-09, B dairesi 10-19) istenirse yeniden
  numaralandırma gerekir.
- `context.json` programatik yazılırken mevcut biçim korunmalıdır (skaler
  dizi tek satır, nesne dizisi açılmış). Düz `json.dumps(indent=2)` dosyayı
  baştan biçimlendirip ~4000 satırlık sahte diff üretir.

## Çalışma kuralı

Aynı anda yalnızca bir geliştirme görevi `IN_PROGRESS` olabilir. Belirsizlikte
varsayım yapılmaz. Kod editinden hemen sonra focused validation; görev kabulünde
validate/generate ve golden-output raporu zorunludur.

## Sonraki direktif şablonu

Sistem mimarı bir sonraki çalışmada şu bilgileri vermelidir:

- Görev ID'si ve açık kapsam.
- İzin verilen dosya/dizinler.
- Schema/context değişikliğine izin var mı?
- DXF üretimine ve mevcut golden output üzerine yazmaya izin var mı?
- Kabul edilmesi gereken davranış ve beklenen validation.
