# impact modülü (revizyon etki alanı raporu) — DEV-068 v1

Bir değişikliğin dokunduğu elemanlardan **etkilenen eleman kümesini** deterministik olarak çıkarır: *"banyoyu büyüttüm — hangi duvar, kapı,
şaft, komşu oda, mahal etiketi, ölçü zinciri etkilendi?"* **Salt okunur ve türevdir:** `context.json`a yazmaz, DXF çizmez, hüküm vermez.
**Minimal patch planı bu modülde YOK** (sistemde patch dili yok; ayrı madde, patch grameri tanımlanınca). Kullanıcı kararları (2026-10-09):
v1 yalnız etki alanı raporu; bağımlılık bilgisi küçük **açık tablo** + mevcut collision ayak izleri (modül-yerel `impact.py` yok);
girdi `blast_radius(context, dokunulan)` + `touched_from_diff(önceki, sonraki)`; düğüm ayrıntısı duvar-kenar **parçası (span)**, yeni tolerans YOK.

## Model
- **Düğüm** `Node(kat_id, tür, id)` — kimlikler katlar arası tekrar eder (rev-28'de 160 kimliğin 123'ü), kat zorunludur. Türler: oda, duvar, açıklık, şaft,
  merdiven, tefriş, kolon, tezgah, etiket, işaret, kot (`FLOOR_LIST_KEY`, 626 düğüm).
- **Kenar sınıfları** (`EDGE_CLASSES`, her biri `yayılır mı` + açıklama taşır): `basvuru` (şema alanındaki kimlik başvurusu), `duvar_oda_kenari`,
  `duvar_birlesimi` (T/L), `kapi_komsu_oda`, `saft_komsu_oda`, `icinde` (tefriş/kolon ayak izi, etiket/kot/işaret/tezgah konumu oda içinde),
  `kapi_acilim` (açılım sektörü ↔ tefriş/kolon ayak izi), ve **yayılmayan** `birim` (aynı `unit_id`) ile `kat_ikizi` (başka katta aynı tür+kimlik) — bunlar
  yalnız "ilgili" olarak listelenir; birim/kat ikizi yayılsaydı tek bir odanın değişimi tüm binayı kapsardı.
- **Span (duvar parçası):** duvara bir kenarla varılırsa etki duvarın **yalnız ilgili parçasından** ilerler. Parça: oda kenarıyla örtüşen aralık, açıklık boşluğu
  (`position_from_start ± width/2`, merkez-konumu kuralı kök CLAUDE.md), birleşim noktası. Dokunulan duvarın kendisi TAMDIR. Span olmadan 40 m'lik bir dış duvar etkiyi
  tüm kata yayardı (başlangıç denemesinde ring 2: 25 düğüm → span ile 4). Karşılaştırma toleransı `spatial.SHARED_EDGE_TOLERANCE_MM`; **yeni sayı yok**.
- **`depth`** bir SUNUM parametresidir (varsayılan 2: doğrudan + bir komşuluk), ölçüm eşiği değildir.
- **Türetilen çıktılar** (`DERIVED_OUTPUTS`): hangi tür değişince hangi modülün çıktısı yeniden türetilir (örn. oda → mahal etiketi, ölçü zinciri, testfit); modül adları
  dizinde aranır.

## Public API
`build_graph(context)`, `blast_radius(context, dokunulan, depth=2)` → `ImpactReport` (halkalar, `related`, `derived`, `warnings`), `touched_from_diff(önceki, sonraki)`
(eklenen/değişen/silinen düğümler; kat listesi dışındaki değişiklikler `other`te ADIYLA söylenir, etki alanı hesaplanmaz), `diff_report`, `coverage(context)`, `format_report`.
Bilinmeyen kat/tür/kimlik `ImpactError` verir — etki alanı uydurulmaz. CLI: `python scripts/impact_report.py [context.json] --touch kat:tür:id | --before önceki.json | --coverage [--depth N]`.

## Tamlık (sessiz geçiş yasağı)
`doc_check` **#17**: `REFERENCE_FIELDS`/`UNIT_FIELDS` alanları şemada var; şemadaki her `*_id` alanı bir başvuru, birim alanı ya da gerekçeli `IMPACT_IGNORED_FIELDS`te;
`floor` tanımındaki her liste bir düğüm türü ya da gerekçeli `IMPACT_FLOOR_EXEMPT`te; `DERIVED_OUTPUTS` modülleri var. Yeni bir şema başvurusu etki grafına eklenmezse kapı kırılır.
`coverage` rapor: tür başına eleman sayısı, **bağsız** (yayılan hiçbir kenarı olmayan) elemanlar, kapsam dışı üst seviye alanlar (`meta`, `grid`, `elevations`, `layers`).
Ayak izleri alınamazsa (`Scene` hatası) ve kopuk başvurularda UYARI yazılır, sessiz geçilmez.

## Ölçülen (rev-28)
626 düğüm, tüm oda/duvar/açıklık/şaft/merdiven/tezgah düğümleri bağlı (bağsız 0). `uC_banyo` dokunulunca halka-1: 8 duvar parçası, kapı, şaft; halka-2: 4 komşu oda
(`uA_oda2`, `uC_oda`, `uC_wc`, `uC_hol`); uzak pencereler (`uA_win_oda2_g`, `uC_win_salon`) etkiye GİRMEZ; kat ikizleri ve aynı birim "ilgili, yayılmaz" olarak listelenir.

## Bilinen sınırlamalar
- **Düşey (katlar arası) bağ yalnız kimlik eşleşmesidir** (`kat_ikizi`); şaft/merdiven hizası geometrik olarak karşılaştırılmaz (`DEV-040` Fikir 3 ile kesişir).
- Kolon ↔ aks, ölçü zinciri ↔ aks baloncuğu, kesit hattı ↔ duvar gibi **pafta düzeyi** bağlar yoktur; yalnız `DERIVED_OUTPUTS` bunları ADIYLA söyler.
- `duvar_birlesimi` yalnız duvar UCU başka duvarın üzerinde ise kurulur (merkez çizgisi); iki duvarın ortada kesişmesi (artı) birleşim sayılmaz.
- Açıklık ↔ oda bağı `spatial` 300 mm temas toleransıyla kurulur; bu toleransın sahibi `spatial`dir.
- Kapı sektörü yalnız tefriş/kolon ile kesişimi sayar; duvar/başka sektör bu kenarı kurmaz (çakışma kararı `collision` motorunundur).
- Tefrişi olmayan gerçek projede (`furniture` 0/9 kat) `icinde`/`kapi_acilim` kenarları yalnız sentetik sahnede sınanır.
- `labels`/`level_marks`/`markings` gerçek projede kullanılmıyor veya az; kenarları sentetik sahnede sınanır.

## Çakışma denetimi: EXEMPT
`collision/scene.py::COLLISION_EXEMPT` içinde: kendi ayak izi üretmez, collision ayak izlerini yalnız OKUR.

## Muhakeme katkısı (DEV-048)
**Rol:** muaf (`REASONING_EXEMPT`): ölçüm/veçhe sağlamaz. Plan §4 adım 3'ün (mercek seçimi: "bu talep hangi bakış açılarını etkiliyor") ve adım 5'in (kör nokta taraması)
deterministik kaynağıdır; tüketimi bir mercek paketinin değil operatör akışının işidir (bugün bağlı değil). Bilinen boşluk: operatör talimatına bağlama yapılmadı.

## Doğrulama
`python scripts/impact/selftest.py` — 10 kontrol: mini sahne (iki oda, orta duvar, kapı, pencere, 3 tefriş, kolon, şaft, merdiven, tezgah, etiket, kot, işaret; ELLE çıkarılan kenarlar
ve halkalar, kapı sektörü bağımsız olarak `collision` motorundan), span yayılımı ve yanlış-pozitifleri, yayılmayan sınıflar, hata/salt-okunurluk/determinizm, fark, kapsam,
gerçek proje, kapı #17 (sahte tablolarla 8 bozma), ve **kasıtlı bozmalar** (span kontrolü, `birim`/`kat_ikizi` yayılımı, izdüşüm, kapsama yardımcıları; ayrıca elle 10 üretim kodu bozması).
