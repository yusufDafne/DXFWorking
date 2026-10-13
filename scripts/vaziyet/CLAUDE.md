# vaziyet modülü (vaziyet/parsel girdisi) — DEV-082 v1

Kullanıcının **vaziyet/parsel planı** girdisini içeri alır, parsel ve çekme geometrisini doğrular ve yapılaşma alanını hesaplar. Plan: `docs/development/SITE_PLAN_STUDY_PLAN.md`
(`DEV-081`…`DEV-087`). Bu madde **yalnız girdi katmanıdır**: yerleşim etüdü motoru `DEV-083`, vaziyet paftası/DXF çıktısı `DEV-084`, brief/onay diyaloğu `DEV-085`, imar varsayılan
kataloğu `DEV-086`, DWG `DEV-087`. **Context'e YAZMAZ, DXF ÇİZMEZ, çekme değeri UYDURMAZ.**

## İsim notu
Plan `site/` adını kullanıyordu; `site` bir **Python stdlib modülüdür** (yorumlayıcı başlarken otomatik yüklenir) — `import site` paketimizi DEĞİL stdlib'i verirdi (`import` → `importer`, `fixture` → `golden`
ile aynı sınıf bir ad düzeltmesi). Dizin/paket: `vaziyet/`. **Veri anahtarı `context.json::site` KALDI** (JSON anahtarı, import değil). Kod: `from vaziyet import ...`.

## Veri: `context.json::site` (şema 1.8.0, OPT-IN)
`source{path, sha256, units}` (kayıt; DXF context'e gömülmez), `north_confirmed` (kullanıcı vaziyetin KUZEY YUKARI olduğunu onayladı), `parcel.polygon` ([x,y] mm, kapalı kabul, son nokta ilkini TEKRARLAMAZ; kenar `i` = köşe `i`→`i+1`
**CCW normalizasyonundan sonra**), `placement_zone.polygon` (kullanıcının binanın YAKLAŞIK oturmasını istediği bölge; eleme değil), `road_edges[]` (yola bakan kenar indeksleri), `setbacks{uniform_mm | edges_mm[]}`
(**kullanıcı girdisi**; yoksa yapılaşma alanı hesaplanmaz — varsayılan katalog `DEV-086`), `building{position, rotation_deg}` (SEÇİLEN yerleşim; ayak izi `meta.floor_width × meta.floor_depth`, `position` MERKEZ).
**Dönme sözleşmesi (DEV-081):** `rotation_deg = B` = kuzey-yukarı vaziyette binanın üst yüzünün dış normalinin kuzeyden **saat yönünde** açısı; kat planı `meta.north_angle = −B` (`plan_north_angle`; 30 → −30).

## Public API
| Ad | Görev |
|---|---|
| `validate_polygon`, `normalize_ccw`, `Parcel` | çokgen geçerliliği (≥3 farklı köşe, kendini kesmez/değmez, komşu kenar geri dönüşü yok), CCW normalizasyonu, alan/kenar |
| `inward_offset`, `buildable_area`, `resolve_setbacks` | kenar başına içeri offset (komşu offset doğrularının kesişimi = gönye) — sonuç DOĞRULANIR (basit çokgen, kenar yönleri korunmuş, her köşenin her orijinal kenara mesafesi ≥ o kenarın çekmesi); doğrulanamazsa `VaziyetError`. Çekme: kullanıcı değeri > varsayılan katalog (`defaults`, DEV-086 biçimi) > hata |
| `building_footprint`, `plan_north_angle` | bina dikdörtgeni (merkez + saat yönünde dönme) ve `north_angle = −B` |
| `scan_site_dxf`, `SiteScan`, `Candidate`, `build_site_patch`, `layer_hint` | vaziyet DXF'i SALT OKUNUR tarama + ONAYLI aday seçiminden `site` patch taslağı (dosyaya YAZMAZ) |
| `check_site` | `validate.py` kancası (opt-in): HATA geçersiz parsel/yerleşim alanı, `road_edges` aralığı, çekme alanı yok ediyor, bina parsel DIŞINDA; UYARI kuzey onaysız, yerleşim alanı parsel dışı, çekme yok, bina yapılaşma alanı dışında |
| `ZONING_DEFAULTS`, `ZoningValue`, `ZoningResolution`, `resolve_zoning`, `edge_roles`, `setbacks_for_parcel` | **DEV-086** imar standart değer kataloğu (aşağıda) |
| `write_sample` | basit ÖRNEK vaziyet DXF'i (kullanıcıya verilir); CLI `python scripts/site_sample.py`; tarama CLI `python scripts/site_scan.py dosya.dxf [--patch c0,c1]` |

## Vaziyet DXF sözleşmesi (kullanıcıya verilen basit düzen)
`PARSEL` (kapalı polyline), `YERLESIM_ALANI` (kapalı polyline), `YOL` (çizgi), `NOT` (kısa metinler), `KUZEY` (yukarı bakan ok çizgisi + "K"), birim `$INSUNITS`. **Katman adı zorunlu DEĞİL:** adlar yalnız `layer_hint` İPUCUDUR
(ASCII-katlamalı: "Yerleşim Alanı" → `yerlesim_alani`); asıl karar kullanıcıdadır (dil modeli yalnız ÖNERİR, `DEV-085`). Aday kaynakları: kapalı `LWPOLYLINE`/2B `POLYLINE` ve **her düğümü derece 2 olan kapanan LINE zinciri**
(uç payı `JOIN_TOLERANCE_MM = 1`: ÇİZİM HASSASİYETİ, tasarım eşiği değil). Yay (bulge), ARC/CIRCLE/SPLINE, açık polyline, 3B POLYLINE **aday sayılmaz ama `unsupported` olarak RAPORLANIR** (sessiz yutulmaz).
**Tahmin yok:** `$INSUNITS` = 0 ise mm'ye ÇEVRİLMEZ (`to_mm=None`, uyarı) ve `build_site_patch` reddeder; **DWG okunmaz** (AC10xx başlığı → "DXF olarak kaydedin", dönüştürücü `DEV-087`).
**Kuzey denetimi:** `KUZEY`/`north` katmanındaki ilk çizgi/polyline'ın yönü (başlangıç→uç, +Y'den saat yönünde) `NORTH_UP_TOLERANCE_DEG = 1` içindeyse `yukari`; sapıyorsa `yukari_degil`; yalnız "K/N/KUZEY/NORTH" metni varsa `belirsiz`; hiçbiri yoksa `yok`.
`yukari` dışındakilerde kullanıcıya UYARI (DEV-081: gelen vaziyet kuzey yukarıdır; yön tahmin edilmez).

## İmar standart değer kataloğu (DEV-086, `zoning.py`)
Kullanıcı kararı (2026-10-13): çekme/TAKS/KAKS kullanıcıdan (dil modeline ayrıca) istenir; **bilinmiyorsa standart değerler kullanılır** — bunlar kısa bir araştırmayla kaydedilmiş, **kaynağı İKİNCİL ve DOĞRULANMAMIŞ** (`verified=False`)
geçici değerlerdir; kullanıcı gerçek yönetmelik verisiyle değiştirecektir. Değerler (ayrık nizam): ön 5000 / yan 3000 / arka 3000 mm (asgari; uygulama imar planında aksi hüküm yoksa), TAKS 0,40 (planda TAKS belirtilmeyen ayrık/blok nizam),
KAKS **sayı yok** (belirtilmediyse yapı yaklaşma mesafelerinden çıkan taban alanı × kat adedi; bu durumda TAKS en çok 0,60). Kaynak bağlantıları ve kayıt `scripts/vaziyet/zoning.py` + `python scripts/defaults_report.py --catalog`.
**Sözleşme:** her kayıt koşul + nizam + kaynak + tarih + `verified` taşır; **kullanıcı değeri HER ZAMAN ezer** (0 da geçerli); **koşul eşleşmezse varsayılan UYGULANMAZ** (`plan_states` ile planın TAKS/KAKS belirttiği bildirilirse, ya da nizam `ayrik` değilse soru döner — varsayım yok);
kullanılan her varsayılan ADIYLA bildirilir (`ZoningResolution.describe`, `defaults_report.py`: `site.setbacks` yoksa hangi varsayılanların uygulanacağını SÖYLER, UYGULAMAZ). `edge_roles`: yola bakan kenar = ön; kalanlardan ilk yol kenarına en antiparalel (eşitlikte en uzun) = arka; diğerleri yan —
yola bakan kenar bilinmiyorsa rol UYDURULMAZ. `setbacks_for_parcel` → `site.setbacks` biçimi (`edges_mm`). Güncelleme sözleşmesi (`standards/` ile aynı): değer DEĞİŞİMİ sürüm artırmaz (`researched_on`/`verified`/`source` güncellenir, HD kaydı), alan ŞEKLİ değişimi `CONTRACT_VERSION`ı artırır. Katalog değerleri BAĞIMSIZ literal sayılardır.

## Çakışma denetimi: EXEMPT
`collision/scene.py::COLLISION_EXEMPT` içinde: vaziyet düzlemi kat sahnesinden ayrı bir koordinat dünyasıdır; parsel/yapılaşma alanı/ayak izi içerme denetimi `checks.py::check_site`te (tekil arite).

## Muhakeme katkısı (DEV-048)
**Rol:** gerekçeli muaf (`reasoning/registry.py::REASONING_EXEMPT`). **Gerekçe (düşünüldü, ölçüm/kural vermez):** kullanıcının verdiği parseli doğrular; bugün veçhe/kural yok. Plan §9 adayı `kent_parsel` (kullanıcı seçmedi).
**Sağlayıcıya geçiş:** bu modül için bir veçhe doğarsa modül `REASONING_EXEMPT`ten çıkar, `scripts/vaziyet/reasoning.py` (rol + ölçüm beyanı; veçhe kaydı lens paketinde) yazılır ve `REASONING_PROVIDERS`a girer — kural ve izinler: `docs/agents/KNOWLEDGE_ENGINEER_AGENT.md`.

## Doğrulama
`python scripts/vaziyet/selftest.py` — 5 grup: çokgen geçerliliği (kelebek/yinelenen/kolinear + L yanlış-pozitif yok), **ELLE hesaplanan** offset (dikdörtgen, kenar başına, L konkav reflex genişlemesi, çökme, eşdoğrusal, kısmen çöken), çekme çözümleme +
ayak izi (90° saat yönü elle) + `plan_north_angle`, `check_site` kancası, DXF içeri aktarma (üretilen örnek, salt-okunurluk/sha256, birim/cm×10, LINE zinciri [açık/dallı/8-şekli/0,5 mm–5 mm boşluk], kuzey 4 durum + 1° sınırı, desteklenmeyenler, DWG, bozuk dosya).
DEV-086 testi `check_zoning_catalog_dev086` (elle okunan değerler, kullanıcı üstünlüğü, koşul/nizam, rol seçimi, defaults_report CLI; 17 kasıtlı bozmadan 16'sı yakalandı, 1'i ölü savunma satırı). Kasıtlı bozma (DEV-082: 31 mutasyon): 29'u yakalandı; 2'si **eşdeğer savunma satırı** (offset'te `signed_area<=0` kenar-yönü kontrolüyle örtüşür; LINE zincirinde derece≠2 dışlaması dolaşma başarısızlığıyla örtüşür — rastgele 4000+20000 çokgen aramasıyla ayrıştıran girdi bulunamadı).
Golden: `scripts/vaziyet/golden/parsel_ornek` (şema 1.8.0 + `site` + `north_angle=−30`; bina 6000×9000 olduğundan `floor_width < floor_depth` UYARISI bilinçli olarak görünür).

## Bilinen sınırlamalar
- **Konveks ve hafif konkav parsel:** offset gönye (miter) ile yapılır ve doğrulanır; çok girintili/dar boyunlu parsel için `VaziyetError` verir (sessizce yanlış çokgen YOK). Gerçek `straight skeleton` offset'i bu sürümde yok.
- LINE zinciri: bir LINE'ın ucu başka bir LINE'ın **ortasına** değiyorsa (T) bu düğüm sayılmaz; kapanma yalnız uç-uç eşleşmesiyle aranır.
- Parsel kenar indeksi CCW normalizasyonuna göredir (CW girdide ilk köşe değişebilir); `road_edges` bu indekslerle yazılır — içeri aktarma patch'i `Parcel` sırasını değil DXF sırasını verir, kullanıcı onayında kenar numaraları gösterilmelidir (`DEV-085`).
- Tek parsel, tek bina dikdörtgeni; çok parselli/çok bloklu/L biçimli bina kapsam dışı.
- Bina ayak izi parsel DIŞINDA ise HATA, yalnız çekmeye giriyorsa UYARI; `placement_zone` eleme değildir.
- Yerleşim etüdü, vaziyet paftası/pusulası, brief ve DWG sonraki maddelerdir. İmar varsayılanları ikincil kaynaklıdır ve doğrulanmamıştır; yalnız ayrık nizam; TAKS 0,40 / 0,60 farklı koşulların değeridir (birbirinin yerine geçmez); kat adedi/taban alanı hesabı (KAKS) etüt motorunda (DEV-083).
