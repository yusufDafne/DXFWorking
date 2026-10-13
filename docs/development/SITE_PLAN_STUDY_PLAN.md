# Vaziyet planı girdisi ve yerleşim etüdü — plan (DEV-081 … DEV-085)

Durum: **PLAN** (kod yok). Kaynak: kullanıcı talebi ve **Q1–Q6 cevapları, 2026-10-13** (§12'de kayıtlı). Görev durumu ve sıra `DEVELOPMENT_TASKS.md`de TEK kaynaktır;
bu belge tasarımı, veri akışını, dil modeli sınırını ve açık kararları tutar. Hiçbir madde kullanıcı onayı olmadan başlamaz
(`DEV-048` planıyla aynı kural). `DEV-024` (`vaziyet/` vaziyet planı) bu planla yeniden kapsamlandı (bkz. §9).

## 1. Kullanıcı talebi (özet, 2026-10-13)

1. **Kuzey oku:** kat planı paftalarında **sağ üst köşede**; **vaziyet planındaki pusula, kullanıcının belirteceği açıda**.
2. **Vaziyet planı dışarıdan DXF olarak alınabilsin:** kullanıcı bir vaziyet planı sağlar; sistem onun üzerine **uygun yerleşim planı
   (etüdü) alternatifleri** üretip sunar.
3. **Dil modeli desteği alınır, çalışma deterministik yürür:** model niyeti/tercihi yapılandırılmış girdiye çevirir ve sonuçları anlatır;
   ölçü, koordinat, alternatif üretimi ve eleme **Python kodudur**. Çalışma, **kullanıcı onayına göre** başlar ve ilerler.

## 2. Kuzey ve paftalama sözleşmesi (kullanıcı kararı 2026-10-13; `DEV-074`ü değiştirir)

Önceki çelişki çözüldü (Q1/Q2 cevapları):

1. **Gelen vaziyet planı DAİMA kuzey yukarı kabul edilir.** Girdi bunu göstermiyorsa (kuzey işareti yok / yukarıyı göstermiyor / okunamıyor) sistem **kullanıcıyı UYARIR**; yönü tahmin etmez, açıyı kullanıcıdan ister.
2. **Paftalama:** vaziyetteki bina yerleşimine göre proje paftasına yerleştirilirken **binanın uzun kenarı yatay** olur ve **kuzeye yakın uzun yüzü paftanın üstüne bakar**.
3. **Pusula döner:** pafta pusulası vaziyetteki **gerçek yöne** göre döndürülür. Kullanıcının örneği: vaziyette kuzeye göre 30° duran yapı paftaya yerleştirilince pusulanın kuzeyi paftanın düşeyine göre **−30°** dönmüş görünür.
4. **Kat planı paftalarında aynı mantık** geçerlidir (ok vaziyete göre gerçek yönü gösterir) ve ok **sağ üst köşede** durur.

Tanım (işaret): `bina_donusu` = vaziyette (kuzey yukarı) binanın üst yüzünün dış normalinin kuzeyden **saat yönünde** açısı; `meta.north_angle` (mevcut tanım: paftanın yukarısından kuzeye, saat yönünde) = **−bina_donusu**. Kullanıcı örneği: `bina_donusu = +30° → north_angle = −30°`.

**Çıkarılan sonuç (kullanıcı teyidi gerek, Q2'):** `DEV-074`teki `[−45°, +45°]` aralığı "dört cepheden kuzeye en yakını üstte" varsayımından geliyordu. Yeni kural *uzun kenar yatay* olduğundan paftanın üstüne bakan yüz **iki uzun yüzden kuzeye yakın olandır**; dış normali kuzeyle ≤ 90° yapar. Bu yüzden dikdörtgen (uzun ≠ kısa kenar) binada izinli aralık **`[−90°, +90°]`** olur; **tam kare** binada eski kural (en yakın cephe, `[−45°, +45°]`) kalır. Ayrıca `meta.floor_width ≥ meta.floor_depth` olmalıdır (çizilen plan uzun kenarı yatay tutar); aksi `validate` uyarısı (otomatik döndürme YOK, karar sorulur). Bu, `DEV-081`de koda/`validate`e/belgeye birlikte işlenir.

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

## 6. `vaziyet/` modülü (yeni, `DEV-024`ün genişletilmiş hali; **dizin adı `site` değil `vaziyet`** — `site` Python stdlib modülüyle çakışır; veri anahtarı `context.json::site` kalır)

Bağımsız modül kuralı (kök `CLAUDE.md`): kendi `CLAUDE.md`'si, `selftest.py`, gerekçeli `COLLISION_EXEMPT`/ayak izi kararı, `REASONING` katkısı (muaf ya da
sağlayıcı — `doc_check` #10), `CONTRACT_VERSION`. Alt parçalar (öneri; kod yazılırken `site/CLAUDE.md`de kesinleşir):

| Dosya | Görev |
|---|---|
| `parcel.py` | `Parcel` (poligon, kenarlar, alan, yönelim), geçerlilik (kapalı, kendini kesmez, saat yönü normalizasyonu) |
| `setback.py` | iç offset ile yapılaşma alanı; **çekme değerleri girdidir** (kenar başına ya da tek değer); kullanıcı vermediyse `DEV-086` kataloğundaki **varsayılan** kullanılır ve **adıyla bildirilir** (sessiz varsayım yok) |
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
(tek parça mı bölünmüş mü), parsel doluluğu (ayak izi / parsel — ham oran; **TAKS/KAKS "tavan" olarak kullanıcı değeriyle, yoksa `DEV-086` varsayılanıyla (adıyla bildirilerek)** denetlenir),
cephe başına gün ışığı yönelimi (`isik_hava_yonelim` merceğiyle aynı tanım; **kaynaksız eşik uydurulmaz**), giriş cephesinin yola/ortak alana bakışı.
**Kullanıcının `YERLESIM_ALANI` bölgesi (yaklaşık istek):** eleme DEĞİL, ölçülen nitelik ve sıralama girdisidir (ayak izinin bölgeyle örtüşme oranı, merkez uzaklığı); "yaklaşık" bir istek olduğu için bölge dışına taşan alternatif listeye girebilir ama bu açıkça belirtilir.
**Alternatif sayısı N:** varsayılan **3** (kullanıcı kararı Q6); kullanıcı dil modeline "daha çok/az alternatif" derse yeniden değerlendirilir (N bir kullanıcı parametresidir, sınırı `DEV-083`te yazılır).
**Sıralama/ağırlık (Q6):** ağırlıklar **isteğe bağlıdır**. Kullanıcı vermişse (dil modeli önerir, kullanıcı onaylar) sıralama o ağırlıklarla yapılır; vermemişse alternatifler, farklı bir ödünleşimi (örn. yola yakınlık / bahçe bütünlüğü / ışık) temsil eden **3 aday** olarak seçilir (Pareto'dan çeşitliliği en yüksek 3, seçim kuralı deterministik ve belgelenmiş) — tek bir "en iyi" iddiası yapılmaz.
Tüm sayısal anlatım §5 kuralıyla (ölçülmüş yer-tutucu) üretilir.

## 8. Girdi biçimi ve örnek vaziyet DXF'i (Q3 cevabı)

Kullanıcı **muhtemelen DWG** sunacak ve çizim **olabildiğince basit** olacak: parsel sınırları, dil modelinin yorumlayabileceği kısa metinler ve binanın **yaklaşık yerleşmesini istediği bölgeyi** gösteren bir alan.

- **DWG:** `ezdxf` DWG okumaz. Bu yüzden sistem girdisi **DXF**'tir; DWG için bir dönüştürücü (ODA File Converter, LibreDWG `dwg2dxf` vb.) gerekir. Dönüştürücü bir dış araç ve lisans/kurulum kararıdır → ayrı madde `DEV-087`, kararı kullanıcı verir. Geçici yol: kullanıcı CAD'den "DXF olarak kaydet" yapar. Dönüştürücü yoksa sistem DWG'yi **sessizce okumaz**; "DXF olarak kaydedin" der.
- **Basit vaziyet sözleşmesi** (`DEV-082`de belgelenir; sistemin ürettiği örnek dosya aynı kuralı izler): `PARSEL` katmanında kapalı polyline (parsel sınırı); `YERLESIM_ALANI` katmanında kapalı polyline (binanın yaklaşık oturmasını istediği bölge); `YOL` katmanında çizgiler (yol kenarı); `NOT` katmanında kısa metinler (`KUZEY`, `YOL`, `KOMSU PARSEL`, ada/parsel no, serbest not); `KUZEY` katmanında kuzey işareti. **Katman adları zorunlu DEĞİLDİR:** kullanıcının dosyasında farklı adlar olabilir → sistem kapalı poligonları ve metinleri **aday** olarak listeler, dil modeli metinlere bakarak hangisinin parsel/yerleşim alanı olduğunu **önerir**, kullanıcı onaylar (§5, onay kapısı 1).
- **Örnek dosya:** `scripts/vaziyet/samples/` altında, **script tarafından üretilen** bir `ornek_vaziyet.dxf` (basit dikdörtgen/yamuk parsel + yol + `YERLESIM_ALANI` + notlar + kuzey işareti) ve kullanıcıya verilecek kısa kullanım notu. DXF'i elle yazmak yasaktır; `python scripts/site_sample.py` üretir (`DEV-082`).
- **Çıktı:** vaziyet paftası ve alternatifleri ana `plan.dxf`'ten **bağımsız DXF** olarak da alınabilir (`export.py`, `DEV-084`).
- Kullanıcının DXF'i **kaynak olarak saklanır** (sha256 + yol `site.source`); `context.json`a gömülmez.

## 9. Görev dilimleri (bağımlılık sırası; ayrıntı `DEVELOPMENT_TASKS.md`de)

| Madde | Konu | Önkoşul |
|---|---|---|
| `DEV-081` | Kuzey sözleşmesi: kat planında ok sağ üst köşe; paftalama kuralı (uzun kenar yatay, kuzeye yakın yüz üstte); pusula vaziyetteki gerçek yöne göre döner; `north_angle` aralığı `[−90°, +90°]` (kare: `[−45°, +45°]`) | Q2' teyidi |
| `DEV-082` | `vaziyet/` I: şema `site`, `Parcel`/çekme, vaziyet DXF içeri aktarma, kuzey işareti denetimi, **örnek vaziyet DXF üreteci** | yok |
| `DEV-083` | `vaziyet/` II: deterministik yerleşim etüdü motoru (varsayılan **3** alternatif, isteğe bağlı ağırlık) | `DEV-082`, `DEV-086` |
| `DEV-084` | `vaziyet/` III: vaziyet paftası, bağımsız DXF çıktısı, alternatif karşılaştırma; pafta pusulası döndürülmüş | `DEV-081`, `DEV-082` (`DEV-083` karşılaştırma için) |
| `DEV-085` | `vaziyet/` IV: kullanıcı/dil modeli bilgi akışı, dallanma (parsel sunuyor mu?), onay diyaloğu, seçim patch'i | `DEV-083` |
| `DEV-086` | İmar standart değer kataloğu (çekme, TAKS, KAKS varsayılanları; kullanıcı sonra gerçek yönetmelikle değiştirecek) | yok |
| `DEV-087` | DWG girdisi: dönüştürücü kararı ve entegrasyonu | kullanıcı kararı (araç/lisans) |
| `DEV-024` | (eski) vaziyet planı | **yeniden kapsamlandı:** `DEV-082`/`DEV-084`e bölündü; ayrıca açılmaz |

**Faz dallanması (Q4 cevabı):** operatör akışının ilk sorusu "Parsel/vaziyet planı sunmak ister misiniz?"dır. **Evet** → birinci faz (bina–parsel yerleşimi, bu plan). **Hayır** → doğrudan ikinci faz: **kat planı/birim yerleşim alternatifleri** (mevcut `architect/study.py`, `templates/`, `testfit/`, `DEV-056` ile birleşir; ayrı plan). Soru ve dallanma `DEV-085`te.

## 10. Doğrulama stratejisi (her madde için asgari)

- Beklenen değerler ELLE hesaplanabilir mini parsellerle (dikdörtgen, L, eğik kenarlı) kurulur; kasıtlı bozma (çekmeyi yok say, parsel dışı alternatifi geçir, offset hatası,
  rotasyon işaretini ters çevir) testleri; yanlış-pozitif tarafı (sınırda duran alternatif eleme dışı, 1 mm içeri giren elemeli).
- **DXF içeri aktarma:** birim/ölçek tahmini YOK; belirsizse sorar. Kapanmayan zincir, çakışan poligon, birden çok aday → aday listesi + güven, otomatik seçim yok.
- **Golden:** `scripts/vaziyet/golden/` (modül referansı) küçük sentetik parsellerle; ana örnek projeye `site` yazılması ayrı bir revizyondur (rev-N).
- **Determinizm testi:** aynı girdi iki koşuda bayt-bayt aynı alternatif listesi.
- Dil modeli katmanı: şablonlara **rakam lint'i** (#13) uygulanır; modelin önerdiği `Brief` alanı şema dışıysa reddedilir; model çıktısı hiçbir koşulda koordinata dönüşmez
  (kasıtlı bozma: modelin "çekme 3 m" önerisini kullanıcı onayı olmadan motora geçirme girişimi reddedilir).

## 11. Riskler

- **Çekme/TAKS/KAKS değerleri uydurulabilir** → kullanıcı vermezse yalnız `DEV-086` kataloğundaki kaynaklı varsayılan kullanılır, her kullanımda adıyla bildirilir; kaynak ikincildir ve kullanıcı gerçek yönetmelikle değiştirecektir (§13). Katalogda olmayan değer (örn. başka nizam) için motor SORAR.
- **DXF çeşitliliği** (birim, katman adı, açık polyline, yay) → ilk sürümde desteklenen entity kümesi açıkça sınırlı; desteklenmeyen girdi sessizce yutulmaz, raporlanır.
- **Eğik/serbest yerleşim** kat planı paftası sözleşmesini (kuzeye en yakın cephe üstte, `DEV-074`) zorlar → Q2.
- **Tek ayak izi varsayımı:** bugünkü proje tek dikdörtgen kat; L/çok bloklu binalar bu planın dışındadır (açıkça yazılır).
- **Alternatif patlaması** → üst sınır N kullanıcı parametresidir (varsayılan yok; sorulur).

## 12. Kullanıcı kararları (2026-10-13) ve kalan teyitler

| # | Karar |
|---|---|
| Q1 | Gelen vaziyet kuzey yukarı kabul edilir, değilse UYARI. Paftalama: uzun kenar yatay, kuzeye yakın yüz üstte; pusula vaziyetteki gerçek yöne göre döner (30° → pusula −30°). |
| Q2 | Kat planı paftalarında aynı mantık; ok vaziyete göre gerçek yönü gösterir. |
| Q3 | Girdi muhtemelen **DWG**; basit çizim (parsel sınırı, yorumlanabilir kısa metinler, yaklaşık yerleşim bölgesi alanı). Sistem **basit örnek vaziyet DXF'i** üretip sunar. |
| Q4 | İlk faz, kullanıcının parsel planı sunmak isteyip istemediğine göre: **evet → bina–parsel yerleşimi; hayır → ikinci faz** (kat/birim yerleşim alternatifleri). |
| Q5 | Kullanıcı çekme/TAKS/KAKS bilgisini dil modeline ayrıca sunar; bilinmiyorsa **standart değerler** kullanılır. Bu değerler sistemde henüz yok → `DEV-086` (kısa araştırmayla varsayılanlar; kullanıcı sonra gerçek yönetmelikle belirleyecek). |
| Q6 | Alternatif sayısı varsayılan **3**, kullanıcının dil modeline talebiyle değişebilir; ağırlıklar **isteğe bağlı**. |

**Kalan teyitler (uygulayıcı kullanıcıya sorar):** (Q2') `[−45°,+45°]` yerine dikdörtgen binada `[−90°,+90°]`, kare binada `[−45°,+45°]` sonucu (§2); DWG dönüştürücü seçimi (`DEV-087`); `DEV-086` varsayılan değerlerinin (araştırma ikincil kaynaklıdır) kullanıcı tarafından ilk bakışta onayı.

## 13. İmar standart değerleri — kısa araştırma kaydı (`DEV-086` girdisi)

Kullanıcı gerçek yönetmelik verisiyle sonra değiştirecek; bu değerler **geçici, kaynağı ikincil, doğrulanmamış** varsayılanlardır ve kullanıldığında **adıyla bildirilir** ("varsayılan: …, kaynak: araştırma 2026-10-13"). Plan notu/uygulama imar planı farklı değer veriyorsa o geçer.

| Değer | Varsayılan | Koşul | Kaynak (ikincil) |
|---|---|---|---|
| Ön bahçe / yol kenarı | **5,00 m** (asgari) | uygulama imar planında aksi hüküm yoksa | Planlı Alanlar İmar Yönetmeliği md. 24, [İzmir BB belgesinde alıntı](https://www.izmir.bel.tr:443/YuklenenDosyalar/Dokumanlar/13022024141408.pdf) ve [Alomaliye yönetmelik metni](https://alomaliye.com/2017/07/03/planli-alanlar-imar-yonetmeligi/) |
| Yan bahçe | **3,00 m** (asgari) | aynı | aynı |
| Arka bahçe | **3,00 m** (asgari) | aynı | aynı |
| TAKS (tavan) | **0,40** | uygulama imar planında TAKS belirtilmeyen ayrık/blok nizam | [Bursa Hakimiyet](https://www.bursahakimiyet.com.tr/gundem/imar-yonetmeligi-nde-kapsamli-degisiklik-yapildi-1660706), [Müşavirler Kulübü](https://musavirlerkulubu.com.tr/makale/planli-alanlar-imar-yonetmeligi-degisikligi-ve-emsal-asansor-hukumleri-2026) (1 Temmuz 2026 değişikliği; Resmî Gazete 33297 metni DOĞRULANMADI) |
| KAKS (emsal) | **sayı yok** — KAKS verilmeyen parselde: yapı yaklaşma mesafelerine göre bulunan taban alanı × kat adedi; bu durumda TAKS en çok **0,60** | KAKS belirtilmemişse | aynı ikincil kaynaklar |

Notlar: (1) ön bahçe çoğu zaman planda ayrıca belirtilir; 5 m yalnız aksi yazılmadığında geçerli asgaridir. (2) TAKS 0,40 ile 0,60 farklı koşulların değerleridir, birbirinin yerine geçmez; katalog **koşulu** taşımalıdır. (3) Bölgesel/belediye yönetmelikleri ve nizam (bitişik/ayrık/blok) farklılaştırır — katalog nizam alanı taşır, v1'de yalnız ayrık nizam. (4) Bu tablo `DEV-086`da `scripts/standards/` benzeri bir kütüphane olur (proje verisi DEĞİL, `context.json`a yazılmaz); kullanıcı değeri her zaman ezer.
