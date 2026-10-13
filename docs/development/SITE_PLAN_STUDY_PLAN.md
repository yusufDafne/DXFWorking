# Vaziyet planı girdisi ve yerleşim etüdü — plan (DEV-081 … DEV-085)

Durum: **PLAN** (kod yok). Kaynak: kullanıcı talebi 2026-10-13. Görev durumu ve sıra `DEVELOPMENT_TASKS.md`de TEK kaynaktır;
bu belge tasarımı, veri akışını, dil modeli sınırını ve açık kararları tutar. Hiçbir madde kullanıcı onayı olmadan başlamaz
(`DEV-048` planıyla aynı kural). `DEV-024` (`site/` vaziyet planı) bu planla yeniden kapsamlandı (bkz. §9).

## 1. Kullanıcı talebi (özet, 2026-10-13)

1. **Kuzey oku:** kat planı paftalarında **sağ üst köşede**; **vaziyet planındaki pusula, kullanıcının belirteceği açıda**.
2. **Vaziyet planı dışarıdan DXF olarak alınabilsin:** kullanıcı bir vaziyet planı sağlar; sistem onun üzerine **uygun yerleşim planı
   (etüdü) alternatifleri** üretip sunar.
3. **Dil modeli desteği alınır, çalışma deterministik yürür:** model niyeti/tercihi yapılandırılmış girdiye çevirir ve sonuçları anlatır;
   ölçü, koordinat, alternatif üretimi ve eleme **Python kodudur**. Çalışma, **kullanıcı onayına göre** başlar ve ilerler.

## 2. Çelişki / netleştirme: kuzey sözleşmesi (`DEV-074`) ile bu talep

`DEV-074` (2026-10-12) şunu kurdu: *vaziyet planında kuzey daima yukarı*; proje, kuzeye en yakın cephesi üstte olacak şekilde paftaya konur;
`meta.north_angle ∈ [−45°, +45°]`. Yeni talep vaziyetteki pusulanın **kullanıcının belirttiği açıda** olmasını söylüyor. İkisi birlikte şöyle
okunabilir (ÖNERİ — onay bekler, bkz. Q1):

- **Vaziyet paftasında** pusula açısı = kullanıcının DXF'inde/beyanında verdiği açı (`site.north_angle`, serbest, derece). Kullanıcının vaziyet
  DXF'i zaten bir yöne sahiptir; sistem onu döndürmez.
- **Kat planı paftalarında** ok, *binanın paftadaki yukarısı ile gerçek kuzey arasındaki açıyı* gösterir (`meta.north_angle`) ve **sağ üst köşede**
  durur. Bu açı artık **türetilebilir**: `meta.north_angle = site.north_angle − bina_donusu` (bina vaziyette `bina_donusu` kadar döndürülmüştür).
  Kullanıcı bunu elle de verebilir; ikisi verilirse tutarlılık `validate` denetimidir (HATA değil, UYARI + hangisi kazanır kuralı açıkça seçilir).
- `[−45°, +45°]` kuralı, "kat planı paftası kuzeye en yakın cephe üstte olacak şekilde yerleştirilir" sözleşmesinin sonucuydu. Vaziyet yerleşimi
  binayı serbestçe döndürebiliyorsa bu kural kat planı paftası için **hâlâ geçerli kalır mı** (paftaya yerleştirme kuralı) yoksa **kalkar mı**
  (çünkü kuzey okunun açısı artık vaziyetten gelir)? **Q2.**

## 3. Kavramlar

| Terim | Anlam |
|---|---|
| **Parsel** | Vaziyet DXF'inden çıkarılan kapalı sınır poligonu (+ varsa yol/komşu/ağaç gibi bağlam çizgileri). |
| **Çekme sınırı** | Parsel sınırından içeri bırakılan, yapının aşamayacağı mesafe. **Sayı kullanıcıdan/imar durumundan gelir; sistem uydurmaz.** |
| **Yapılaşma alanı** | Parsel − çekmeler (iç offset poligonu). Bina ayak izi bunun içinde kalmalıdır. |
| **Ayak izi ailesi** | Binanın plan dikdörtgeni(leri): bugün tek `floor_width × floor_depth` (proje verisi); ileride birden çok blok. |
| **Yerleşim alternatifi** | (konum, dönüş, ayak izi) üçlüsü + ölçülmüş niteliklerin listesi. Türevdir; kullanıcı seçene kadar `context.json`a yazılmaz. |
| **Brief (ihtiyaç beyanı)** | Kullanıcının serbest metninin yapılandırılmış hali (izinli alan listesi); dil modeli çıkarır, kullanıcı doğrular. |

## 4. Veri akışı (aşamalar ve kapılar)

```
kullanici DXF (vaziyet)  ──►  [A] iceri aktarma (salt okunur)  ──►  parsel ADAYI + bağlam + güven/provenance
                                         │ kullanici dogrular / duzeltir (onay kapısı 1)
                                         ▼
                              [B] onayli patch  ──►  context.json::site  (yeni, opt-in, semada additif MINOR)
brief (serbest metin) ──► dil modeli ──► yapilandirilmis Brief ──► kullanici dogrular (onay kapısı 2)
                                         ▼
                              [C] deterministik etut motoru: aday uretim → eleme (FORBID) → olcum → siralama
                                         ▼
                              [D] alternatifler (en cok N) + olculmus nitelikler + anlatim (explain.py desenindeki sablon, rakam lint'li)
                                         │ kullanici secer (onay kapısı 3)
                                         ▼
                              [E] secim patch'i  ──► context.json (bina oturumu/donusu, meta.north_angle turetilmisse) + requests.jsonl + rev_history
                                         ▼
                              mevcut hat: validate → generate_dxf → vaziyet paftasi + kat planlari
```

Üç onay kapısı bilinçlidir: (1) **içeri aktarılan geometri** (parsel yanlış okunmuş olabilir — `importer/` desenindeki "aday, asla doğrudan context" kuralı),
(2) **brief** (model yanlış anlamış olabilir), (3) **seçim** (yerleşim kararı kullanıcıya aittir; "sen karar ver" devri kök `CLAUDE.md` muhakeme ilkesi 4'teki
sınırlarla geçerlidir: ciddi bulguda yine sorulur).

## 5. Dil modeli ile deterministik kod arasındaki sınır

Dil modeli **yalnız** şunları yapar: (a) serbest metinden `Brief` alanlarını doldurmayı önermek (izinli şema: öncelikler, "yola cephe dükkân", "salon güneye",
bahçe istekleri…); (b) belirsizlikte kullanıcıya soru sormak; (c) motorun ürettiği alternatifleri **şablonla** anlatmak (rakamlar yalnız ölçülmüş yer-tutucudan,
`reasoning/explain.py` rakam lint'i #13); (d) alternatifler arası takas anlatısı. Dil modeli **asla**: koordinat, mesafe, çekme değeri, TAKS/KAKS gibi sayılar
üretmez; alternatif eklemez/çıkarmaz; elemeyi geçmez; eksik veriyi varsayımla doldurmaz (kök `CLAUDE.md` "Belirsizlik durumunda").

Motor tamamen deterministiktir: aynı parsel + aynı brief + aynı tohum-siz arama → aynı alternatif listesi. Rastgelelik yoktur (ızgara/aday kümesi sıralıdır).

## 6. `site/` modülü (yeni, `DEV-024`ün genişletilmiş hali)

Bağımsız modül kuralı (kök `CLAUDE.md`): kendi `CLAUDE.md`'si, `selftest.py`, gerekçeli `COLLISION_EXEMPT`/ayak izi kararı, `REASONING` katkısı (muaf ya da
sağlayıcı — `doc_check` #10), `CONTRACT_VERSION`. Alt parçalar (öneri; kod yazılırken `site/CLAUDE.md`de kesinleşir):

| Dosya | Görev |
|---|---|
| `parcel.py` | `Parcel` (poligon, kenarlar, alan, yönelim), geçerlilik (kapalı, kendini kesmez, saat yönü normalizasyonu) |
| `setback.py` | iç offset ile yapılaşma alanı; **çekme değerleri girdidir** (kenar başına ya da tek değer); yok ise ETÜT BAŞLAMAZ ve soru döner |
| `dxf_in.py` | vaziyet DXF'inden parsel **adayı** + bağlam çıkarır (`importer/` ile aynı salt-okunur ilke; LWPOLYLINE/LINE zinciri → kapalı poligon, birim/ölçek tespiti raporlanır, tahmin edilmez) |
| `candidates.py` | deterministik aday üretimi (konum ızgarası × izinli dönüşler) |
| `metrics.py` | ölçülen nitelikler (aşağıda §7) |
| `study.py` | eleme + ölçüm + sıralama + `Alternative` listesi |
| `sheet.py` | vaziyet paftası çizimi (`pafta::Sheet` üzerinden), pusula, ölçek 1:200/1:500 kısıtı (`PaperSizePlanner` zaten bilir) |
| `export.py` | vaziyet paftasını/alternatiflerini **bağımsız bir DXF** olarak yazma (bkz. §8) |

## 7. Etüt motoru (deterministik) — ölçümler ve politika

**Eleme (FORBID benzeri, alternatif listesine hiç girmez):** ayak izi yapılaşma alanı dışında; parsel dışı; (varsa) komşu/yol ayak izi ile çakışma.
**Ölçülen nitelikler (hepsi proje geometrisinin ölçüsüdür; her biri ölçüm sahibi fonksiyonla):**
çekme sınırlarına pay (min/ortalama), bina–parsel sınırı mesafeleri, yolu gören cephe, her cephenin gerçek yönü (kuzey açısıyla), bahçe alanının sürekliliği
(tek parça mı bölünmüş mü), parsel doluluğu (ayak izi / parsel — ham oran; **TAKS/KAKS "tavan" olarak yalnız kullanıcı/imar durumu değer verirse** denetlenir),
cephe başına gün ışığı yönelimi (`isik_hava_yonelim` merceğiyle aynı tanım; **kaynaksız eşik uydurulmaz**), giriş cephesinin yola/ortak alana bakışı.
**Sıralama:** kullanıcının brief'inden gelen **ağırlıklar** ile (ağırlıklar kullanıcı onaylı sayılardır, dil modeli önermiş olsa bile kullanıcı doğrular); ağırlık yoksa
sıralama yapılmaz, alternatifler "farklı bir ödünleşimi temsil eden" kümeler olarak sunulur (Pareto sunumu) — **tek "en iyi" iddiası uydurulmaz.**
Tüm sayısal anlatım §5 kuralıyla (ölçülmüş yer-tutucu) üretilir.

## 8. "Dışarıdan DXF" — iki yön (yorum; Q3 ile onay)

Talepteki "vaziyet planı için dışarıda bir DXF alınabilecek şekilde" şöyle okunuyor ve ikisi de planlandı:
- **Girdi:** kullanıcı bir vaziyet planı DXF'i sağlar → `dxf_in.py` (aday, onaylı patch). Kullanıcının DXF'i **kaynak olarak saklanır** (sha256 + yol `site.source`; DXF'in kendisi
  `context.json`a gömülmez, projenin `site/` kaynak dizininde kalır — "çıktı DXF'ler elle düzenlenmez" kuralı girdi için değil üretim için geçerlidir).
- **Çıktı:** vaziyet paftası ana `plan.dxf` içine eklenmeden de **tek başına bir DXF** olarak alınabilir (`export.py`); alternatifler karşılaştırma paftasına ya da ayrı dosyalara yazılır.
  Üretim yolu yine yalnız script'tir (elle düzenleme yasağı geçerli).

## 9. Görev dilimleri (bağımlılık sırası; ayrıntı `DEVELOPMENT_TASKS.md`de)

| Madde | Konu | Önkoşul |
|---|---|---|
| `DEV-081` | Kuzey oku: kat planı sağ üst köşe; vaziyet pusulası kullanıcı açısı (`DEV-074` sözleşme revizyonu) | yok (Q1/Q2 kararı) |
| `DEV-082` | `site/` I: şema (`site`), `Parcel`/`setback`, vaziyet DXF içeri aktarma (aday + onaylı patch) | yok |
| `DEV-083` | `site/` II: deterministik etüt motoru (aday, eleme, ölçüm, alternatif) | `DEV-082` |
| `DEV-084` | `site/` III: vaziyet paftası (pusula dahil) + bağımsız DXF çıktısı + alternatif karşılaştırma | `DEV-081`, `DEV-082` (`DEV-083` alternatif karşılaştırması için) |
| `DEV-085` | Brief + onay diyaloğu: dil modeli rolü, `Brief` şeması, sunum/seçim/onay kaydı, seçim patch'i | `DEV-083` |
| `DEV-024` | (eski) vaziyet planı | **yeniden kapsamlandı:** `DEV-082`/`DEV-084`e bölündü; bu madde yeni uygulamada ayrıca açılmaz |

İkinci faz (bu plana DAHİL DEĞİL, kullanıcı isterse ayrı plan): **birim içi/kat planı yerleşim alternatifleri** — mevcut `architect/study.py`, `templates/`, `testfit/`
ve `DEV-056` (2D yerleşim optimizasyonu) ile birleşir. Talepteki "uygun yerleşim planı (etütleme)" ifadesinin ilk fazı **bina–parsel yerleşimi**dir (Q4).

## 10. Doğrulama stratejisi (her madde için asgari)

- Beklenen değerler ELLE hesaplanabilir mini parsellerle (dikdörtgen, L, eğik kenarlı) kurulur; kasıtlı bozma (çekmeyi yok say, parsel dışı alternatifi geçir, offset hatası,
  rotasyon işaretini ters çevir) testleri; yanlış-pozitif tarafı (sınırda duran alternatif eleme dışı, 1 mm içeri giren elemeli).
- **DXF içeri aktarma:** birim/ölçek tahmini YOK; belirsizse sorar. Kapanmayan zincir, çakışan poligon, birden çok aday → aday listesi + güven, otomatik seçim yok.
- **Golden:** `scripts/site/golden/` (modül referansı) küçük sentetik parsellerle; ana örnek projeye `site` yazılması ayrı bir revizyondur (rev-N).
- **Determinizm testi:** aynı girdi iki koşuda bayt-bayt aynı alternatif listesi.
- Dil modeli katmanı: şablonlara **rakam lint'i** (#13) uygulanır; modelin önerdiği `Brief` alanı şema dışıysa reddedilir; model çıktısı hiçbir koşulda koordinata dönüşmez
  (kasıtlı bozma: modelin "çekme 3 m" önerisini kullanıcı onayı olmadan motora geçirme girişimi reddedilir).

## 11. Riskler

- **Çekme/TAKS/KAKS değerleri uydurulabilir** → motor bu değerler olmadan başlamaz; değer yoksa soru döner (kök `CLAUDE.md` "eksik bilgi varsa sorulur").
- **DXF çeşitliliği** (birim, katman adı, açık polyline, yay) → ilk sürümde desteklenen entity kümesi açıkça sınırlı; desteklenmeyen girdi sessizce yutulmaz, raporlanır.
- **Eğik/serbest yerleşim** kat planı paftası sözleşmesini (kuzeye en yakın cephe üstte, `DEV-074`) zorlar → Q2.
- **Tek ayak izi varsayımı:** bugünkü proje tek dikdörtgen kat; L/çok bloklu binalar bu planın dışındadır (açıkça yazılır).
- **Alternatif patlaması** → üst sınır N kullanıcı parametresidir (varsayılan yok; sorulur).

## 12. Açık kararlar (kullanıcıya sorulacak; cevaplanmadan uygulama başlamaz)

- **Q1.** Vaziyet pusulası açısı ile kat planı kuzey okunun ilişkisi §2'deki öneri mi (kat planı açısı `site.north_angle − bina_donusu`'dan türetilir)?
- **Q2.** `meta.north_angle ∈ [−45°, +45°]` ve "kuzeye en yakın cephe üstte" kuralı kat planı paftası için korunsun mu, vaziyet yerleşimi serbest döndürürse kalksın mı?
- **Q3.** "Dışarıdan DXF" yorumu (§8): hem **girdi** (kullanıcının vaziyet DXF'i) hem **çıktı** (bağımsız vaziyet DXF'i) doğru mu?
- **Q4.** İlk faz yalnız **bina–parsel yerleşimi** mi (kat planı yerleşim alternatifleri ikinci faz)?
- **Q5.** Çekme mesafeleri/TAKS/KAKS nasıl gelecek: kullanıcı kenar kenar mı söyleyecek, imar durumu belgesinden (PDF/metin) mi? (Belge ayrıştırma ayrı bir madde olur.)
- **Q6.** Alternatif sayısı N ve sıralama: ağırlıkları kullanıcı mı verecek, yoksa Pareto sunumu (tek "en iyi" yok) yeterli mi?
