# Mimari Muhakeme Planı (DEV-048)

> **Durum:** PLAN. Hiçbir kod yazılmadı, `context.json`/şema/DXF değişmedi.
> `DEV-048` `PLANNED` kalır; uygulama `DEV-059`…`DEV-070` ile, kullanıcının
> her adımı AÇIKÇA başlatmasıyla yürür (`DEVELOPMENT_TASKS.md`).
> **Tek kaynak ilkesi:** görev durumu/sırası `DEVELOPMENT_TASKS.md`de, bu belge
> yalnızca *yaklaşımı ve bilgi modelini* tutar. `scripts/reasoning/` kurulunca bu
> belgenin yerini o modülün `CLAUDE.md`si alır (bu dosya "tarihsel gerekçe"ye döner).

**Kimin için:** Operatör ajan → §3, §4, §5 · Bilgi mühendisi (gelecekteki gelişmiş
dil modeli) → §6, §7, §8 · Sistem geliştirici → §7, §9, §10 · Sistem mimarı
(kullanıcı) → §1, §2, §11.

---

## 1. Neden: bugünkü sistem neyi BİLİYOR, neyi bilmiyor

Sistem bugün mimari sağduyuyu **33 ayrı `check_*` fonksiyonu** olarak biliyor (yedi
dosyada: `architect/rules.py` 16, `standards/` 9, `openings/` 5, `shafts/` 2,
`walls/thickness.py` 1; birkaçı toplayıcı). Hepsi doğru çalışıyor ve hepsi aynı
biçimde konuşuyor: bir `list[str]`.
Bu biçim dört şeyi taşıyamıyor:

| Eksik | Somut sonuç |
| --- | --- |
| **Neden önemli?** (kuralın arkasındaki ilke ve kullanıcının yaşayacağı sonuç) | Uyarı bir cümle; kullanıcı "bu ne demek, ne kaybederim?" sorusunu sorunca cevap koda gömülü değil, ajanın o anki hafızasında. |
| **Hangisi hangisine karşı?** (kurallar arası gerilim) | Bir kuralı düzeltirken başkasını bozmak ancak sonradan fark ediliyor (`DEV-041` yan etkisi: kapı kaydırılınca yeni görüş hattı açıldı). |
| **Nasıl anlatılır?** (kullanıcının dilinde, teknik altyapıya girmeden) | Aynı uyarı beş katta beşer kez basılıyor; mimar olmayan kullanıcı için okunmaz. |
| **Yeni bilgi nasıl eklenir?** | Bir ilke ancak o oturumun ajanı fark edip bir `DEV-0XX` açarsa koda girer; `uC` sandviç banyosu gibi keşifler "bir sonraki oturumda yeniden keşfedilmek" zorunda. |

### 1.1 Ölçülmüş boşluklar (2026-10-05, `context.json` rev-28, salt-okunur ölçüm)

Plan spekülasyona değil ölçüme dayanır. Aşağıdakiler mevcut `architect.rules`
yardımcılarıyla (yeni eşik uydurmadan) gerçek projede ölçüldü; ölçüm yöntemi her
satırda yazılıdır ve yeniden üretilebilir.

| # | Ölçüm | Sonuç | Neyi gösteriyor |
| - | ----- | ----- | --------------- |
| 1 | `validate.py` çıktısındaki `UYARI` satırları, kat adı çıkarılıp tekilleştirildi | **15 satır → 3 tekil konu** (K1–K5 özdeş) | Kök-neden kümeleme yok; kullanıcıya konu değil satır sayısı gösteriliyor. |
| 2 | `meta.north_angle` | **yok** | Yönelim değerlendirmesi yapılamaz ve sistem bunu **söylemiyor** (opt-in sessiz geçiş: "temiz" ile "hiç bakılmadı" ayırt edilemiyor). |
| 3 | Pencere alanları | yalnız `width`; **yükseklik/denizlik yok** | Pencere/taban oranı veçhesi mevcut veriyle hesaplanamaz; yükseklik ya katalog varsayılanı + kullanıcı onayı ya da veri ister (uydurulmaz). |
| 4 | Giriş kapısından aynı birimin **yatak odası** kapısına görüş hattı (mevcut `check_entry_sightlines`ın koni+duvar testi, hedef türü yatak odası) | **`uC`: giriş → `uC_d_oda_hol`, sapma 16.1°, mesafe 1978 mm; `uB` de ateşler: 20.2°, 2025 mm** (K1–K5'te aynı; `uB` 2026-10-09 denetiminde bulundu, ilk ölçüm yalnız `uC`yi görmüştü) | Mevcut kural yalnız WC/banyo'ya bakıyor; "girişten yatak odası kapısı görünür" mahremiyet bulgusu hiçbir yerde adlandırılmamış. |
| 5 | Komşu birimlerin giriş kapıları arası mesafe (kapı orta noktaları) | **`uB`–`uC`: 1485 mm** (dX 1050, dY 1050); `uA`–`uB` 6125, `uA`–`uC` 5075 | Hiçbir kural komşu birimlerin giriş kapılarına bakmıyor (yalnız aynı birimin kapıları ölçülüyor). |
| 6 | Islak hacim ↔ yatak odası/salon ortak duvarı (poligon ortak kenarı > 1 mm) | **aynı birimde 5/6 ıslak hacim tetiklenir** (örn. `uA_wc`↔`uA_salon` 2700 mm); hol hedef sayılırsa ya da birimler arası dahil edilirse 6/6 — sayı **tanım seçimine bağlıdır** | Böyle bir veçhe **her birimde ötter**: ayırt edicilik düşük, kalibre edilmeden kullanıcıya gösterilirse alarm yorgunluğu yapar (§8.3). |
| 7 | `floors[].furniture[]` dolu kat sayısı | **0 / 9** | "Yatak odası" etiketi bir yatağın sığdığını kanıtlamıyor; mobilyalanabilirlik hiç sınanmıyor (`uC_oda` AABB 3100×3350 mm). |
| 8 | Yaşam mahalli (salon/yatak/mutfak) penceresiz oda sayısı, 9 kat | **0** (bugün temiz) | İyi haber, ama `rev-22`de `uC_oda` penceresizdi ve **elle** fark edildi; veçhe olsaydı deterministik yakalanırdı (geriye dönük doğrulama, §10.3). |
| 9 | Kapı-ortası / oda-teması / ortak-duvar / nokta-poligon yardımcıları | **en az 5 ayrı yerde** (denetim: `validate.py` ve `architect/layout.py` içinde de kopyalar var) (`collision/geometry`, `architect/rules`, `standards/nuances`, `shafts`, `rooms`) | `rev-13` swing dersinin ("iki yerde ayrı hesaplanan geometri sessizce ayrışır") tekrarı riski; üç yeni mercek bunu 7'ye çıkarırdı → `DEV-059` önkoşul (§10). |

> Ölçüm #4 ve #5 normal katların beşinde (K1–K5) de aynı çıkar — özdeşlik ayrıca
> doğrulandı (giriş kapısı konumları, oda/duvar/açıklık sayıları aynı).

### 1.2 Geçmişten kanıtlı dersler (kayıtlı, uydurma değil)

- **`uC` sandviç banyosu (rev-22/23):** banyo salon ile yatak odası arasına
  sıkışmıştı ve ikisine de kapısı vardı. Hiçbir kural bunu adlandırmıyordu; ajan
  mevcut yardımcıları yeniden birleştirerek **elle** buldu. Bu çıkarım bugün
  koda ve belgeye şu biçimde girmedi: "sandviç banyo diye bir tasarım kokusu
  vardır" (`architect/CLAUDE.md` yalnız olayı anlatıyor). → **Koku kataloğu** (§3).
- **`DEV-041` yan etkisi:** bir kapıyı kaydırmak yeni bir giriş↔WC görüş hattı
  açtı. → **Çoklu mercek regresyon karşılaştırması** (§4, adım 8).
- **`DEV-049`:** AABB, 350 mm'lik hol kolunu gizledi; ölçüm *yerel* yapılınca
  göründü. → Ölçüm doğruluğu bir muhakeme konusudur; mercekler ölçümü
  **sahibi modülden** alır (§7).
- **Sağ-üst ölü bölge (`DEV-045`)** ve **250 mm hol**: kullanıcı gördü, sistem
  görmedi. → "Kullanıcının gözünden kaçanı yakalama" hedefinin kendisi.

---

## 2. Yaklaşım kararı ve anayasa

### 2.1 `DEV-048`in açık kararı çözüldü: (a)+(b), (c)'ye açık — gerekçeyle

Kullanıcı talimatı (2026-10-05): *"bir modül ya da yaklaşım metodu olup tüm
modülleri kapsayabilir, best practices yaklaşımı sen belirleyeceksin."* Karar:

> **Bilgi bildirimseldir, hüküm deterministiktir, anlatım dildir.**

| Katman | Ne | Nerede yaşar | Kim yazar/işletir |
| ------ | -- | ------------ | ----------------- |
| **Bilgi** | Mercek, veçhe, koku, gerilim, profil: *neden önemli, ne zaman geçerli, hangi kaynak, hangi eşik* | **Bildirimsel Python kayıtları** (`scripts/reasoning/lenses/*.py`) + modül-yerel `reasoning.py` | Bilgi mühendisi (insan veya gelecekteki dil modeli) |
| **Hüküm** | Ölçüm ve kural: "bu oda penceresiz mi, bu kapı girişten görünür mü" | **Sahibi modülde** deterministik fonksiyon (`check_*`, `measure_*`) | Modül geliştiricisi |
| **Anlatım** | Bulguyu kullanıcının dilinde, nihai ürün üzerinden açıklamak; seçenek ve bedel sunmak | Dil modeli + **şablon kataloğu** (rakamlar yalnız kanıttan) | Operatör ajan |

**(a) düz doküman** Faz 0'dır ve BU OTURUMDA etkindir (kök `CLAUDE.md` işaretçisi +
bu belge). **(b) script içi veri-odaklı modül** Faz 1'den itibaren aynı bilginin
*çalıştırılabilir* hâlidir. **(c) harici teknoloji** (vektör DB/RAG/skill
dosyası) ŞİMDİ SEÇİLMEDİ, çünkü: (i) bilgi zaten *yapılandırılmış ve git'te
sürümlü* — RAG'ın çözdüğü "yapısız metinde arama" sorunu yok; (ii) deterministik,
denetlenebilir, `git diff`le incelenebilir kalmalı; (iii) kök `CLAUDE.md`nin "agentic
dokümanlar tek bir bağlam sistemidir" ilkesi dosya-tabanlı çözümü ister. (c)'ye
kapı açık kalır: bilgi mühendisi rolünün talimatı (`docs/agents/…`) zaten bir
"skill dosyası"dır (§8).

### 2.2 Yeniden kullanılan mevcut desenler (yeni bir şey icat edilmiyor)

| Desen (emsal) | Muhakemede karşılığı |
| ------------- | -------------------- |
| `collision/` ters bağımlılık + `COLLISION_EXEMPT` + `doc_check` | Çekirdek modülleri import etmez; her modül ya `reasoning.py` sağlar ya da **gerekçeli** `REASONING_EXEMPT`; `doc_check` mekanik denetler. |
| `standards/` `source` + "v1 pratik varsayılan" + güncelleme sözleşmesi | Her eşik/veçhe `Provenance` taşır; değer güncellemesi sürüm artırmaz, alan şekli artırır. |
| `architect/options.py` (hesapla, puanla, **kimlikle seç**) | Çözüm önerileri (remedy) hesaplanmış seçenek kimlikleridir; dil modeli koordinat icat etmez. |
| `topology.register_topology()` | `register_lens()` / `register_facet()` genişletme noktaları. |
| `axis::AxisCoverageReport` (salt-okunur kapsam raporu) | **Muhakeme kapsam raporu:** hangi mercek koştu / koşamadı ve neden. |
| `golden/` + kasıtlı bozma + yanlış-pozitif testi | **Vaka kütüphanesi** (§8.2): her veçhe ≥1 ihlal + ≥1 yanlış-pozitif vakası. |
| `opt-in` (`room_type`, `unit_id`) | Veri yoksa kural koşmaz **ve bu söylenir** (sessiz geçiş kapatılır). |

### 2.3 Anayasa (hiçbir mercek/veçhe/profil bunu aşamaz)

1. **Yalnız UYARI.** Hiçbir mimari muhakeme kuralı `collision/`in `FORBID` sınıfına
   çekilmez; FORBID fiziksel imkânsızlık içindir. Şiddet **bilgidir** (0–1 sayı),
   sınıf değildir. Mimari sağduyu müşterinin bilinçli tercihiyle her zaman
   ezilebilir (`DEV-040` değişmez ilkesi, aynen).
2. **Sayı uydurulmaz.** Kullanıcıya söylenen her sayı ya o projenin bir ölçümü ya da
   `Provenance`lı bir katalog sabitidir. Anlatım şablonları rakam taşıyamaz; rakam
   yalnız `evidence` alanından yer-tutucuyla gelir (§5.3, mekanik lint).
3. **"Yapılamaz" denmez.** "Yapılır, şu bedelle." İtiraz değil bilgi sunulur.
4. **Sessiz geçiş yok.** Koşamayan mercek (veri eksik) **adıyla** söylenir. "Temiz"
   ile "hiç bakılmadı" aynı şey değildir (kök `CLAUDE.md`: *"temiz döndü tek başına
   hiçbir şey kanıtlamaz"*).
5. **Karar kullanıcınındır (ve devredilebilir).** Sistem teşhis + seçenek + bedel + öneri
   sunar; öneri bağlayıcı değildir. Kullanıcı kararı açıkça **devredebilir** ("sen karar
   ver", "alternatif görmek istemiyorum"); o zaman öneri uygulanır ama yapılan seçim ve
   bedeli bildirilir (§5.8). Kabul edilen uyarının gerekçesi kayıt altına alınır (§5.5).
6. **Proje verisi ↔ kütüphane ayrımı.** Bilgi (ilke, eşik, şablon) kütüphanede yaşar;
   `context.json`'a yalnız kullanıcının **kararı** ve (ileride) profil *seçimi* yazılır.
   Çizim/eşik sabiti context'e sızmaz.
7. **Her bilgi kendi epistemik statüsünü taşır** (`kesin` / `yaygin` / `tercih`) ve
   anlatım buna uyar: "yönetmelik gereği" ile "genelde tercih edilmez" ile "zevk
   meselesi" aynı sesle söylenmez. Kaynaksız iddia `kesin` işaretlenemez.
8. **Modül bağımsızlığı.** Veçhe KAYDI lens paketinde (`reasoning/lenses/<mercek>.py`), ÖLÇÜM/KURAL sahibi modülde yaşar (kullanıcı kararı 2026-10-09, `DEV-060`); çekirdek hiçbir
   çizim modülünü import etmez; bir modül yalnız kendi `reasoning.py`si ve
   `CLAUDE.md`si açılarak geliştirilebilir.

---

## 3. Bilgi modeli

| Kavram | Tek cümle | Örnek (mahremiyet) |
| ------ | --------- | ------------------ |
| **Mercek** (lens) | Tasarıma bakılan bir bakış açısı/felsefe; **kural değil, kurallar için bir çerçeve** | `mahremiyet` |
| **Veçhe** (facet, *alt örneklem*) | Merceğin tek bir somut yüzü; ölçülebilir bir soru | `mahremiyet.gorsel.giris_yatak` |
| **Ölçüm** (measurement) | Bir büyüklüğü hesaplayan fonksiyon (sahibi modülde) | giriş kapısı → yatak odası kapısı sapma açısı |
| **Kural** (rule/hüküm) | Ölçümü eşikle karşılaştırıp bulgu üreten fonksiyon | mevcut `check_entry_sightlines` |
| **Bulgu** (finding) | Yapılandırılmış sonuç: veçhe, şiddet 0–1, kanıt, anahtar, çözüm kimlikleri | bkz. §3.2 |
| **Tasarım kokusu** (smell) | Birden çok bulgunun birlikte oluşturduğu **adlı** örüntü + kök neden + standart çıkış | `sandvic_banyo` |
| **Gerilim** (tension) | İki veçhenin birbirine karşı çektiği bilinen ödünleşim | `mahremiyet` ↔ `capraz_havalandirma` |
| **Profil** (profile) | Mercek ağırlıkları ve veçhe açık/kapalı kümesi (bina tipi/yaşam tarzı) | `konut_aile` |
| **Vaka** (case) | Gerçek bir defektten damıtılmış, beklenen bulgu kümesi olan mini sahne | `uC` sandviç banyo |
| **Karar** (decision) | Kullanıcının bir bulguyu bilerek kabul etmesi + gerekçe + kanıt anlık görüntüsü | §5.5 |

**Mercek ≠ kural.** Kullanıcı: *"kural derken asla değişmez şeyler anlama; metodoloji
ya da yaklaşım felsefesi de olabilir."* Bu yüzden mercek bir **soru ailesidir**
("kim kimi görür/duyar/yanından geçer?"); veçheler zamanla artar, mercek sabit kalır.

### 3.1 Veçhe kaydı (bildirim şeması — kodlanacak biçimin taslağı)

> **Taslaktır:** alan adları ve yapıyı gösterir. Kayıttaki **sayılar yer-tutucudur** ve
> `Provenance`lı gerçek değerler ilgili görevde (`DEV-061`…`DEV-066`) belirlenir;
> bu belgeden koda eşik taşınmaz.

```python
Facet(
    id="mahremiyet.gorsel.giris_yatak",         # <mercek>.<kategori>.<ad>, değişmez kimlik
    lens="mahremiyet",
    title_tr="Girişten yatak odası kapısı görünmesin",
    principle_tr="Eve girenin ilk bakışta gördüğü yer sosyal alandır; özel alanın kapısı değil.",
    why_tr="Misafir kapıdan girerken yatak odasının kapısını (açılırsa içini) görür.",
    status="draft",                              # idea | draft | shadow | active
    provenance=Provenance(kind="mimari_pratik",  # kullanici_karari | yonetmelik | mimari_pratik | olcum
                          confidence="yaygin",   # kesin | yaygin | tercih
                          source="v1 pratik varsayılan", reviewed="2026-10-05"),
    measure_ref="architect.rules:door_sightline_angle",   # NOKTALI REFERANS — çekirdek import ETMEZ
    check_ref="architect.rules:check_entry_bedroom_sightline",
    thresholds=Thresholds(warn_at=45.0,          # mevcut check_entry_sightlines konisi (v1)
                          severe_at=15.0,        # YER-TUTUCU — DEV-066 kalibrasyonu belirler
                          unit="derece", source="v1 pratik varsayılan"),
    triggers={"door": ["add", "move"], "room": ["resize"]},
    needs=["rooms[].room_type", "rooms[].unit_id"],      # eksikse KAPSAM RAPORUNA "koşamadı" yazılır
    tensions=["mahremiyet.kademelenme.derinlik", "yasanabilirlik.duvar.kullanilabilir_uzunluk"],
    remedies=["kapi_kaydir", "antre_ekle", "kapi_yonu_cevir"],   # options.py deseninde SEÇENEK kimlikleri
    legit_overrides_tr=["stüdyo (1+0)", "açık plan tercihi", "otel odası"],
    plain=Plain(problem="{unit} biriminde girişten {room} kapısı görünüyor.",
                consequence="Misafir geldiğinde yatak odasının kapısı karşıda durur.",
                numbers=["angle_deg", "distance_mm"]),   # yalnız evidence'tan; şablonda rakam YOK
    cases=["mahremiyet/giris_yatak_ihlal", "mahremiyet/giris_yatak_temiz"],
)
```

Alan zorunlulukları `status`a göre kademelidir (§7.3): `idea` yalnız
`id/lens/title_tr/principle_tr/why_tr` ister; `active` hepsini ister.

### 3.2 Bulgu (finding) sözleşmesi

`Finding(key, facet_id, severity, evidence, message_tr, plain, remedies, floor_id, elements)`

- **`key`** kararlıdır: `<facet_id>|<kat>|<sıralı eleman kimlikleri>`. Aynı sorun
  aynı anahtarı üretir (K1…K5 özdeşliği anahtarla görünür → §4 kümeleme).
- **`severity`** 0–1, **hesaplanır**, uydurulmaz: eşikten sapmanın
  `warn_at`→`severe_at` doğrusal rampası (tavan 1.0). Sınıf adı değil bilgidir;
  anlatım bantları: `bilgi` (<0.25) · `dikkat` (0.25–0.6) · `ciddi` (>0.6).
  (`DEV-040` Fikir 1'in gerçekleşmesi.) Şiddet eğrisi veçhe kaydındadır, çekirdekte değil.
- **`evidence`** sözlüktür (ölçülen sayılar, eleman kimlikleri, eşik). Anlatım rakamı
  yalnız buradan alır.
- Mevcut `check_*` fonksiyonları DEĞİŞMEZ: v1'de bir **adaptör** `list[str]`
  çıktısını `evidence={"mesaj": ...}` ile `Finding`e sarar (strangler deseni). Kuralın
  yapılandırılmış `evidence` üretmesi, ilgili modül geliştiricisinin kendi hızında
  yapacağı bir iyileştirmedir (yeni veçhelerde baştan yapılandırılmıştır).

### 3.3 Epistemik statü → anlatım sesi

| `confidence` | Anlam | Ses (örnek kalıp) |
| ------------ | ----- | ----------------- |
| `kesin` | Fiziksel gerçek ya da **doğrulanmış** yönetmelik maddesi | "Bu, yönetmelik/fizik gereği …" — **yalnız kaynağı kayıtlıysa** |
| `yaygin` | Yazılı olmayan ama geniş kabul gören mimari pratik | "Genellikle … tercih edilir; çünkü …" |
| `tercih` | Yaşam tarzı/zevk; doğru-yanlış değil | "Bu bir tercih meselesi; sizin için … önemliyse …" |

> **Mimari kural iddialarında kaynak disiplini:** Yönetmelik rakamı (ör. pencere/taban
> oranı, merdiven ölçüsü, kaçış mesafesi) **kullanıcı kaynağı getirmeden koda girmez**.
> Bu belgede anılan her yönetmelik-benzeri değer "doğrulanacak aday"dır; `standards/`in
> "v1 pratik varsayılan" disipliniyle işaretlenir (`kesin` statüsü verilmez).

---

## 4. Etüt protokolü (muhakeme döngüsü)

Her talepte ve her etütte aynı döngü işler. **Kim yapar** sütunu sorumluluğu ayırır:
yargı Python'dadır, dil modeli yalnız *yapılandırır ve anlatır*.

| # | Adım | Kim | Çıktı |
| - | ---- | --- | ----- |
| 1 | **Niyeti yapılandır:** ham talebi eleman/işlem türlerine çevir ("yatak odasının kapısı salona açılsın" → `door: move/add`, `room: bedroom,salon`). Ölçü/koordinat dil modelinden gelmez. | LLM | `Intent` (var olan "talep → patch" adımı) |
| 2 | **Yeterlilik:** patchin ihtiyaç duyduğu veri eksik mi? Eksikse **dur ve sor** (kök `CLAUDE.md` "belirsizlikte durma"). | Python+LLM | engelleyici belirsizlik listesi |
| 3 | **Mercek seçimi:** `triggers` ile dokunulan eleman türlerine bağlı mercekler + her zaman açık küresel mercekler. Etütte (sıfırdan tasarım) hepsi. | Python | koşacak veçhe listesi |
| 4 | **Değerlendir:** ölçümleri ve kuralları koştur; **kapsam raporu** yaz (koştu/koşamadı+neden/uygulanmaz). | Python | `Finding[]` + `CoverageReport` |
| 5 | **Kör nokta taraması:** talep öncesi ve sonrası TÜM aktif mercekleri karşılaştır; kullanıcının sormadığı ama bu değişiklikle **yeni çıkan** bulgular ayrı işaretlenir ("yan etki"). | Python | `yeni / çözülen / değişmeyen` |
| 6 | **Teşhis:** bulguları ortak elemanlara/kök nedene göre kümele; eşleşen **koku** varsa adını ver; katlar arası özdeş bulguları tek konuya indir (§1.1 #1). | Python | `Diagnosis[]` |
| 7 | **Gerilim analizi:** düzeltmenin dokunacağı veçheler arasında kayıtlı **gerilim** var mı? Varsa seçenekleri ödünleşimle birlikte sun. | Python | `Option[]` (bedelli) |
| 8 | **Sun ve karar iste:** §5 sözleşmesiyle en fazla 3 konu, sonuç dili, seçenek+bedel+öneri. Karar gelene dek patch uygulanmaz. | LLM | kullanıcı kararı |
| 9 | **Uygula ve yeniden doğrula:** patch → validate → adım 4–5'in tekrarı. Çıktı: "çözüldü / yeni çıktı / değişmedi". **Çözülen bir bulgu başka bir veçheyi bozduysa** kullanıcıya söylenir. | Python+LLM | regresyon farkı |
| 10 | **Kaydet ve öğren:** kabul edilen bulgu → **Karar** kaydı (§5.5). Yeni bir ilke keşfedildiyse → **Vaka→İlke→Veçhe** akışı (§8.1). | LLM+kullanıcı | `Decision`, vaka taslağı |

**Durma koşulları:** engelleyici belirsizlik · kullanıcı kararı bekleniyor · fiziksel
çakışma (`collision` HATA, mimari değil) · şema/MAJOR sürüm kapısı.

### 4.1 Sunum kuyruğu (alarm yorgunluğuna karşı)

Kullanıcıya sıra: `öncelik = şiddet × profil_ağırlığı × yenilik × niyet_ilgisi`
(`yenilik`: karar kaydıyla kabul edilmiş ve kanıtı değişmemiş bulgu = 0; yan etki = ×1.5;
`niyet_ilgisi`: talebin dokunduğu elemana bağlıysa ×1.5). **İlk mesajda en fazla 3 konu**;
gerisi "diğer notlar — ister misiniz?" ile. Ağırlıklar veçhe/profil kaydındaki sabitlerdir,
uydurma değil; kalibrasyonla ayarlanır (§8.3). *(Formül v1 taslaktır; `DEV-066` kalibre eder.)*

### 4.2 Kök-neden kümeleme ve koku kataloğu

Koku = adlı örüntü. v1 kataloğu **yalnız gerçekten yaşanmış** örnekleri kodlar:

| Koku | Bileşen bulgular | Kök neden | Standart çıkış (seçenek kimlikleri) |
| ---- | ---------------- | --------- | ------------------------------------ |
| `sandvic_banyo` | banyo hem salona hem yatak odasına kapılı | ıslak hacim iki bölge arasına sıkışmış | `hol_uzerinden_ac`, `kapiyi_tek_bolgeye_ver` |
| `gecis_odasi_yatak` | `hol→yatak→banyo` zinciri (`DEV-042`) | yatak odası zorunlu geçiş | `hole_dogrudan_kapi` |
| `dikizli_giris` | girişten WC/yatak kapısı görünür | kapı ekseni giriş ekseninde | `kapi_kaydir`, `antre_ekle` |
| `olu_alan` | ortak payı yüksek + kullanılmayan bölge | sirkülasyon fazlası | (kullanıcı kararı; "yerine ne konur" uydurulmaz) |
| `capraz_dar_hol` | hol kolu net < asgari (`DEV-049/050`) | kol dar | `kolu_genislet` |

Yeni koku eklemek bir **kayıt** eklemektir (bileşen veçhe kimlikleri + kök neden + çıkış).

---

## 5. Diyalog sözleşmesi (kullanıcıyla konuşma)

Hedef: *"kullanıcı bazı şeyleri gözünden kaçırabilir; sen onun kapsamlı düşünen
motorusun"* ve *"teknik altyapıya girmeden, nihai ürün üzerinden anlat."*

### 5.1 İki kullanıcı, tek soru

Kullanıcı mimar olabilir ya da hayalini çizdirmek isteyen biri. Oturumun başında
(yalnız bir kez, ve ancak ilk bulgu sunulacağı anda): *"Teknik ayrıntıyı sade tutayım
mı, yoksa mimari terimlerle mi konuşalım?"* Cevap **oturum bilgisidir**, `context.json`'a
yazılmaz. `sade` → ürün dili ("misafir geldiğinde…"), terim ve ölçü azaltılmış;
`mimar` → kısa, terimli, ölçülü. İçerik (teşhis, seçenek) AYNIDIR; yalnız dil değişir.

### 5.2 Anlatım iskeleti (5 parça, bu sırayla)

1. **Ne görüyoruz?** — tek cümle, üründe nasıl göründüğüyle ("`uC` birimde giriş kapısından
   yatak odasının kapısı karşıya düşüyor").
2. **Neden önemli?** — yaşanacak sonuç (veçhenin `why_tr`si); gerekirse epistemik ses (§3.3).
3. **Seçenekler** — en çok 3; her biri **bedeliyle** ("hol {hol_artisi} m² büyür", "salon daralır").
   Bedel sayıları ölçümden gelir (§5.3).
4. **Önerimiz** — tek seçenek + tek cümle gerekçe; "yapılamaz" yok.
5. **Karar sizin** — "olduğu gibi bırakmak da meşru; bunu gerekçesiyle kaydederiz."

### 5.3 Rakam kuralı (mekanik)

> **Uygulandı (DEV-064):** üç yer-tutucu sınıfı — `{ad:..}` (eleman adı), `{olcum:..}` (`Plain.numbers`te bildirilmiş ölçülen sayı), `{sabit:..}` (kaynaklı eşik/şiddet); rakam = Unicode Nd/No/Nl; açık istisna yalnız **satır başı numaralandırma** ("1. seçenek"). Lint şablonu denetler; dil modelinin SERBEST metnini `scripts/reasoning_dialogue.py append/verify` + `dialogue.jsonl` denetler.

Şablon metinleri **rakam içermez**; `{angle_deg}` gibi yer-tutucular yalnız
`Finding.evidence`tan doldurulur. Çekirdeğin `explain` lint'i: (i) şablonda `[0-9]`
yok, (ii) her yer-tutucu `Plain.numbers` içinde ve `evidence`ta var. Dil modelinin
serbest metinde rakam üretmesi anayasanın 2. maddesine aykırıdır; operatör talimatı
bunu açıkça yasaklar (`DEV-064`).

### 5.4 Ton örnekleri

| Yerine | Şöyle |
| ------ | ----- |
| "Bu yapılamaz." | "Yapılır; yalnız şunu bilmenizde fayda var: …" |
| "Standart ihlali!" | "Bu yerleşimde … durumu oluşuyor." |
| "Yönetmeliğe aykırı." (kaynak yok) | "Genelde tercih edilmez; çünkü …" |
| "Hata: oran 2.7." | "Banyo çubuk gibi ince uzun; içinde rahat dönülmez." |

### 5.5 Karar kaydı ("bilinçli göz ardı")

> **Uygulandı (DEV-065, şema 1.4.0):** kayıt `context.json` üst seviye `design_decisions[]`; bir kayıt `covers[]` ile N bulguyu kapsar; ölçülen sayıların anlık görüntüsü de yazılır; v1'de herhangi bir değişim (iyileşme dahil) kabulü düşürür. Ayrıntı: `scripts/reasoning/CLAUDE.md`.

Kullanıcı bir bulguyu bilerek kabul ederse (`DEV-065`, şema değişikliği → mimar onayı):
`design_decisions[]` ekleme-yalnız kaydı: `finding_key`, kullanıcı gerekçesi (zorunlu,
boş olamaz), kanıt anlık görüntüsü (`evidence_hash`), tarih. **Kabul, kanıta bağlıdır:**
aynı bulgunun kanıtı sonradan anlamlı biçimde kötüleşirse (`evidence_hash` değişir) kabul
düşer ve bulgu yeniden sunulur — eski bir "evet", değişen bir sorunu örtmez.

### 5.6 Çalışılmış örnek 1 — mimar olmayan kullanıcı, tek talep

> Kıvrık parantez `{…}` = ölçümden gelen değer (§5.3). Örnekte sayı **yoktur**; çünkü
> bu belge de anayasanın 2. maddesine uyar.

> **Kullanıcı:** "Salonu biraz büyütelim."
>
> *(Adım 1–5: talep `room: salon resize`; salon büyürken bitişik yatak odası küçülüyor.
> Hedef mercekler: yaşanabilirlik, ışık. Kör nokta taraması: yatak odasının penceresi
> etkilenmedi, ama kısa kenarı katalogdaki "çift kişilik yatak + dolap" kümesinin sığdığı
> ölçünün altına iniyor — kullanıcı sormadı.)*
>
> **Ben:** Salon büyür. Yalnız şunu görmenizi isterim: bu değişiklikte bitişik yatak odası
> {küçülme} küçüldüğü için **çift kişilik yatak artık rahat yerleşmiyor** (yatağın iki yanında
> geçiş kalmıyor). Üç yol var:
> 1. Salonu **{daha_az}** büyütmek — yatak odası rahat kalır, salon yine büyür.
> 2. Büyütmeyi aynen yapıp yatak odasını **tek kişilik** düşünmek.
> 3. Aynen bırakmak — bilinçli bir tercihse kaydederim.
>
> Önerim 1. Hangisini istersiniz?

Bu örnekte teknik terim ve kural adı yok. Kullanıcının niyetinden (salon büyüsün) kimse
vazgeçirilmedi: niyet korunur, yan etki görünür kılınır.

### 5.7 Çalışılmış örnek 2 — mimar kullanıcı

> **Kullanıcı:** "uA yatak odası 1 kapısını salona açalım."
>
> **Ben:** Yapılır. Üç etki: (1) `mahremiyet.gecis.yatak_salon` — yatak odası salondan
> geçişli olur (şiddet {severity}); (2) `yasanabilirlik.duvar.kullanilabilir_uzunluk` — salonun
> ortak duvarı kapı kanadıyla {kisalma} kısalır; (3) ışık etkilenmez. Seçenekler: antre/hol
> üzerinden bağlamak (`hol_payi` {once} → {sonra}, eşik {esik}), kapıyı salon köşesine
> çekmek, olduğu gibi bırakmak + karar kaydı.

### 5.8 Delegasyon: "sen karar ver"

Kullanıcı kararı devredebilir; gerçek örnek `rev-23`: *"Zonlama fikri görmek istemiyorum şu
anda, çalışmaya başlayabilirsin."* İki mod:

| Mod | Ne zaman | Davranış |
| --- | -------- | -------- |
| `sor` (varsayılan) | kullanıcı devretmediyse | §5.2 iskeleti; karar gelene dek patch uygulanmaz |
| `devret` | kullanıcı açıkça devrettiyse ("sen karar ver", "alternatif görmek istemiyorum") | önerilen seçenek **uygulanır**; yapılan seçim, bedeli ve reddedilen seçenekler **sonrasında** bildirilir; karar kaydı `devredilmis=true` işaretlenir |

`devret` anayasayı bozmaz: bilgi saklanmaz, yalnız sunum sırası değişir. Devir **o talep
için** geçerlidir ve sessizce kalıcı hâle gelmez; kullanıcı "bundan sonra hep sen karar
ver" derse bu da oturum bilgisi olarak kaydedilir ve `ciddi` bantta (şiddet >0.6) bulgu
çıktığında yine **sorulur** (devir, ciddi bulguyu örtmez).

---

## 6. Bu oturumun üç ana konusu

Seçim ölçütü: (i) **toplumsal / fiziksel-iklimsel / işlevsel** ekseninde birbirinden farklı,
(ii) kullanıcının örneğiyle (mahremiyet) başlayıp (iii) **kullanıcının gözünden en kolay
kaçan**, (iv) mevcut sistemde en az örtülmüş konular. Diğer adaylar §6.4'te.

### 6.1 `mahremiyet` — toplumsal

**Felsefe:** Konut, kamusaldan özele kademelenir ("yakınlık gradyanı"; mimari literatürde
yaygın bir ilke — `yaygin`, resmi kaynak değil). Mahremiyetin tek karşılığı yoktur;
bu yüzden **altı veçhe ailesi** vardır.

| Aile | Veçhe (düz dil sorusu) | Bugünkü durum | Not |
| ---- | ---------------------- | ------------- | --- |
| **Görsel** | Girişten WC kapısı görünür mü? | VAR `check_entry_sightlines`, `check_entry_wet_door_proximity` | adaptörle kaydedilir |
|  | Girişten **yatak odası** kapısı görünür mü? | **YOK** — ölçüm #4: `uC` 16.1°/1978 mm, `uB` 20.2°/2025 mm | yeni veçhe; en değerli ilk ekleme |
|  | Mutfak kapısı ↔ WC kapısı karşılıklı mı? | VAR `check_kitchen_wet_door_opposite` | |
|  | WC/banyo kapısı kendi hacmine mi açılıyor? | VAR `check_wet_door_swing_inward` (#12) | mahremiyetle ilişkisi (kapı açıkken içerisinin holden görünmemesi) yaygın gerekçedir; **kayıtlı kaynak yok** → bilgi mühendisi gerekçeyi doğrulayıp `provenance`a yazar |
| **İşitsel** | Islak hacim yatak odası/salonla ortak duvar paylaşıyor mu? | **YOK** — ölçüm #6: aynı birimde 5/6 tetiklenir | **önce shadow**: ayırt edicilik düşük; duvar türü (`walls.kind`, kütle) ve ıslak hacmin tipi (WC≠banyo) şiddeti ayırmalı |
|  | Yatak odası–salon ortak duvarı | KISMEN (`check_bedroom_via_corridor` salon *kapısına* bakar) | duvar tarafı yok |
|  | Birimler arası ortak duvar | **YOK** | yatak odası komşu daire salonuna mı bakıyor |
| **Geçiş** | Bir odaya gitmek için başka bir özel odadan geçmek gerekiyor mu? | VAR `check_wet_area_reachable_without_bedroom`, `check_bedroom_via_corridor` | |
|  | **Misafir yolu:** giriş→salon→misafir WC, yatak odası kapıları önünden geçmeden | **KISMEN** (WC var, "misafir WC" kavramı yok) | birim içinde hangi WC misafire açık: veri (`rooms[].guest`?) → kullanıcı kararı |
| **Kademelenme** | Giriş→salon→hol→yatak sırası (kamusal→özel) korunuyor mu? | **YOK** | birim-içi graf derinliği (`_build_unit_adjacency` genişletmesi) |
| **Birimler arası** | Komşu birimlerin giriş kapıları birbirine çok yakın mı? | **YOK** — ölçüm #5: `uB`–`uC` 1485 mm | yeni veçhe; kapı genişliği/ortak sahanlık bağlamı ister |
|  | Karşılıklı pencere/balkon bakışı | **YOK** | parsel/komşu verisi → `DEV-024` |
| **Yaşam tarzı** | Açık mutfak/açık plan tercihi, misafir sıklığı, ev ofisi | **YOK** | **profil ağırlığı**; hiçbir zaman sabit kural değil |

**Gerilimler:** `mahremiyet` ↔ kompakt ıslak çekirdek (tesisat ekonomisi ıslak hacimleri
yaklaştırır) · ↔ çapraz havalandırma (karşılıklı açıklık) · ↔ sirkülasyon payı (ayrı geçiş
= daha fazla hol) · ↔ ışık (büyük cam komşuya bakar).
**Meşru istisnalar:** stüdyo (1+0), otel odası, bilinçli açık plan tercihi.
**Koku bağı:** `sandvic_banyo`, `gecis_odasi_yatak`, `dikizli_giris`.
**Veri gereksinimi:** mevcut `room_type`/`unit_id` + (misafir veçhesi için) kullanıcı kararı.

### 6.2 `isik_hava_yonelim` — fiziksel / iklimsel

**Felsefe:** Yaşam mahallinin ışık ve hava almadan yaşanmayacağı fiziksel bir gerçektir;
yönelim ise aynı planı iklimle uyumlu veya uyumsuz kılar. Kullanıcının gözünden
**en kolay kaçan** konudur (plan çiziminde pencere "ikinci iştir") ve `rev-22`de bir
yatak odasının penceresiz kalması **elle** fark edilmiştir.

| Veçhe (düz dil sorusu) | Bugünkü durum | Veri durumu | Not |
| ---------------------- | ------------- | ----------- | --- |
| Her yaşam mahallinin penceresi/dış duvarı var mı? | **YOK** (bugün 0 ihlal, ölçüm #8) | `openings` var ✔ | pencere orta noktası → oda teması (mevcut yöntem); `rev-22` geriye dönük doğrulaması |
| Pencere alanı oda alanına yeter mi? | **YOK** | **pencere yüksekliği yok** (ölçüm #3) | oran eşiği **doğrulanmadan kodlanmaz**; yükseklik: katalog varsayılanı + kullanıcı onayı veya veri alanı (şema kararı) |
| Oda yönelimi uygun mu? (örn. servis kuzeye, salon güneye) | **YOK** | **`meta.north_angle` yok** (ölçüm #2) | kapsam raporu: "yönelim değerlendirilemedi — kuzey yönü verilmedi" → kullanıcıya sorulur; **yön uydurulmaz** |
| Çapraz havalandırma: birimin ≥2 farklı cephede açıklığı var mı? | **YOK** | cephe tayini: duvarın hangi dış kenarda olduğu (aks/`floor_width/depth`) | `mahremiyet` ile gerilim |
| Islak hacim havalandırması: pencere **veya** şaft var mı? | **KISMEN** (`shafts` var; "pencere-ya-da-şaft" kuralı yok) | ✔ | `shafts/` ile ortak; yönetmelik atfı kullanıcıdan |
| Derinlik: pencere duvarından odanın en uzağı pencere yüksekliğine göre makul mü? | **YOK** | yükseklik yok | yükseklik gelince |
| Komşu bina/parsel gölgeleme | **YOK** | `DEV-024` (parsel) | uzak |

**Gerilimler:** ışık ↔ mahremiyet · ışık ↔ ekonomi (derin plan = az cephe) · yönelim ↔ giriş
cephesi seçimi (`options_for_core_placement` ile beraber).
**Yönelim notu:** kuzey yönü olmayan projede tüm yönelim veçheleri `koşamadı` olur ve
kullanıcıya bu açıkça söylenir; "kuzey nerede?" sorusu engelleyici belirsizlik değil,
*kapsamı artıran bir sorudur* (cevap gelmezse mercek atlanır, proje durmaz).
**Güneş yolu** (enlem/boylam gerektirir) ŞİMDİLİK kapsam dışıdır; uydurulmaz.

### 6.3 `yasanabilirlik` — işlevsel / fiziksel

**Felsefe:** Geometrik olarak geçerli ve oransal olarak makul bir oda hâlâ *yaşanamaz*
olabilir: kapı kanadı yatağa çarpar, yatak sığar ama yanından geçilemez, kullanılabilir
duvar kalmaz. Mimar bunu zihninde "mobilya koyarak" dener; sistemde bu deneme yok.
Bu mercek, **tefriş yerleşimi proje verisi olmadan da** "tipik mobilya kümesi sığar mı"
sorusunu **deneme yerleşimiyle** sorar (türetilmiş, `context.json`a yazılmaz).

| Veçhe | Bugünkü durum | Not |
| ----- | ------------- | --- |
| Odanın tipik tefriş kümesi (yatak odası: çift yatak + dolap…) sığar mı? | **YOK** — ölçüm #7: tefriş 0/9 kat | deneme yerleşimi (§10, `DEV-063`); katalog ölçüleri `furniture/`te hazır (`yatak_cift` 1600×2000 …) |
| Kapı kanadı ↔ yerleştirilen mobilya | KISMEN (`collision` kapı sektörü ↔ tefriş, **verilmiş** tefriş için) | deneme yerleşimi için aynı sektör kullanılır |
| Yatak/mobilya çevresinde geçiş payı | **YOK** | pay değerleri `yaygin` — doğrulanmadan kodlanmaz |
| Kapı+pencere sonrası **kullanılabilir duvar uzunluğu** | **YOK** | ölçüm `openings`+`walls` verisinden; mobilya yerleşimi için ham madde |
| Islak hacimde kullanım alanı (klozet/lavabo önü) | KISMEN (`DEV-049` net ölçüm, `DEV-050` dönüş payı) | |
| Mutfak tezgah uzunluğu / çalışma düzeni | **YOK** | `counters[]` verisi var |
| Kapı net geçişi | VAR `check_open_door_net_passage` (`DEV-051`) | adaptörle kaydedilir |

**Gerilimler:** yaşanabilirlik ↔ alan ekonomisi · ↔ ışık (pencere önünü dolap kapatır).
**Önemli:** deneme yerleşimi **çözüm önerisi değil sınavdır**: "sığdı/sığmadı + hangi
kapasitede" döner; hangi mobilyanın nereye konacağı kullanıcı kararıdır.

### 6.4 Aday mercek kataloğu (henüz göreve alınmadı — fikir)

Kullanıcı: *"bunun gibi başka hangi sosyal ya da fiziksel kural olabilir?"* Aşağıdakiler
**aday**dır; her biri ancak kullanıcı seçince göreve girer (`DEVELOPMENT_IDEAS.md`).

| Aday mercek | Tür | Ana soru | Veriyi/ölçümü verecek modüller | Bugün |
| ----------- | --- | -------- | ------------------------------- | ----- |
| `sirkulasyon_akis` | işlevsel | Hol/koridor kullanışlı mı, ölü alan/ölü uç var mı? | `rooms`, `architect`, `templates` | KISMEN (`DEV-045`, `DEV-054`) |
| `tesisat_hijyen` | fiziksel | Islak hacim kümeli mi, **üst katlarda üst üste** mi, koku/hijyen ayrımı? | `shafts`, `architect`, (yeni `vertical`) | KISMEN (yatay var, **düşey yok**) |
| `akustik` | fiziksel | Gürültülü bölge ile sessiz bölge ayrı mı, ortak duvar kütlesi? | `walls` (tür/kalınlık), `rooms` | **YOK** (`mahremiyet.isitsel` ile iç içe) |
| `yapisal_duzen` | fiziksel | Kolon oda ortasına/kapıya düşüyor mu, düşey süreklilik, açıklık? | `columns`, `axis`, `elevations` | KISMEN (kolon çakışması var; düşey hiza `columns` sınırlaması) |
| `guvenlik_kacis` | fiziksel/yasal | Kaçış mesafesi, yangın merdiveni, çıkmaz uç | `stairs`, `rooms`, `openings` | **YOK** (`DEV-027`) |
| `erisilebilirlik` | toplumsal/fiziksel | Eşik/rampa/dönüş çapı/asansör erişimi | `levels`, `stairs`, `openings`, `standards` | KISMEN (`DEV-050` #9) |
| `ekonomi_verim` | ekonomik | Net/brüt oranı, ortak alan payı, tekrarlı düzen | `legend` (`DEV-026`), `architect` | KISMEN (`DEV-045`) |
| `esneklik` | işlevsel | Duvar taşıyıcı mı bölme mi (ileride değişir mi)? | `walls` (`kind`), `columns` | **YOK** |
| `kent_parsel` | toplumsal | Çekme, komşu bakışı, cephe gürültüsü | `site` (`DEV-024`) | **YOK** (modül yok) |
| `enerji_yalitim` | fiziksel | Isı köprüsü, cephe/kapalı alan oranı | `walls` (`DEV-033`), `elevations` | **YOK** |
| `yasam_tarzi` | toplumsal | Aile/tek kişi/misafir sıklığı/ev ofisi/evcil hayvan | **profil** (kullanıcı beyanı) | **YOK** (`DEV-069` brief) |

---

## 7. Genişletilebilirlik mimarisi (kod planı)

### 7.1 Dizin ve bağımlılık yönü

```text
scripts/
  reasoning/                    # ÇEKİRDEK: bilgi içermez, çizim modülü import etmez
    __init__.py                 #   public API + CONTRACT_VERSION
    model.py                    #   Lens, Facet, Provenance, Thresholds, Finding, Smell, Tension, Profile
    registry.py                 #   register_lens/register_facet; noktalı referansı tembel çöz
    findings.py                 #   anahtar, şiddet eğrisi, regresyon farkı, kümeleme
    coverage.py                 #   CoverageReport (koştu / koşamadı+neden / uygulanmaz)
    explain.py                  #   şablon çözümleme + rakam lint'i
    smells.py                   #   koku kataloğu (kayıtlar)
    profiles.py                 #   profil kayıtları
    lenses/                     #   BİLGİ: bildirimsel mercek paketleri
      mahremiyet.py   isik_hava_yonelim.py   yasanabilirlik.py
    cases/                      #   VAKALAR (golden DEĞİL — bkz. §8.2)
    selftest.py     CLAUDE.md
  <modül>/reasoning.py          # saglayici modul: ROL + ÖLÇÜM beyanı (veçhe kaydı lens paketinde); yoksa REASONING_EXEMPT/PENDING
  <modül>/CLAUDE.md             #   standart "## Muhakeme katkısı" bölümü (§8.4)
```

Bağımlılık ters çevrilir (collision deseni): çekirdek `REASONING_PROVIDERS = ["architect.reasoning", …]`
dizgilerini tembel çözer; modüller çekirdeği değil, yalnız kendi `reasoning.py`lerinde
`reasoning.model` tiplerini import eder (veya sade sözlük döner — çekirdek ikisini de kabul eder).
Mercek paketleri (`lenses/*.py`) yalnız **bildirir ve noktalı referans verir**
(`"architect.rules:check_entry_sightlines"`); ölçüm/kural **sahibi modülde** kalır.

### 7.2 Mekanik kapılar (`doc_check.py`'ye eklenecek — `DEV-060`)

| # | Kapı | Emsal |
| - | ---- | ----- |
| 10 | Her çizim/doğrulama modülünün `reasoning.py`si **ya da** `REASONING_EXEMPT[modül]` içinde gerekçesi vardır; ikisi birden olamaz. **Üç durumlu (2026-10-09 denetimi):** üçüncü durum `REASONING_PENDING` ("henüz değerlendirilmedi") yalnız küçülebilir, bilgi kanalıdır ve `DEV-067` bitince kapı bloklayıcı olur — aksi halde kapı 23 pakette ilk gün kırmızıdır | #8 çakışma kapsamı |
| 11 | Her veçhenin `measure_ref`/`check_ref`i AST ile çözülür (`module_symbols` tekniği; modül import edilmez) | #7 |
| 12 | `status ≥ shadow` veçhenin ≥1 ihlal + ≥1 yanlış-pozitif **vakası** vardır ve `cases/`te dosyası bulunur | golden disiplini |
| 13 | Anlatım şablonlarında rakam yok; yer-tutucular `Plain.numbers` ile uyumlu | §5.3 |
| 14 | `kesin` statülü veçhenin `provenance.source`u boş/`"v1 pratik varsayılan"` olamaz | §3.3 |
| 15 | `provenance.reviewed` N aydan eskiyse **bilgi** olarak listelenir (bloklamaz) | bayatlama |

### 7.3 Terfi merdiveni (güvenli büyüme)

`idea` → `draft` → `shadow` → `active`.

| Durum | Anlamı | Kullanıcıya görünür mü | Giriş koşulu |
| ----- | ------ | ---------------------- | ------------ |
| `idea` | yalnız ilke yazılı | hayır | id + ilke + `why_tr` |
| `draft` | kayıt tam, **kod yok** | hayır | + kaynak statüsü + gerekli veri + gerilimler |
| `shadow` | ölçüm/kural koşar, **yalnız muhakeme raporuna** yazar | hayır | + `check_ref` çözülür + ihlal & yanlış-pozitif vakası |
| `active` | kullanıcıya sunulur (UYARI) | evet | + **ayırt edicilik** ölçütü sağlandı (§8.3) + anlatım şablonu + (varsa) kaynak onayı |

`shadow` ölçüm #6'nın dersidir: tetik oranı ~%100 olan bir veçhe bilgi taşımaz; önce
duvar türü gibi ayırıcılarla şiddet bölünür, sonra yükseltilir.

### 7.4 Sürüm ve şema

`reasoning/__init__.py::CONTRACT_VERSION` (`version.CONTRACT_MODULES`e eklenir,
`doc_check` #9). Faz 1–3 **şema değiştirmez**. Şema değişikliği gerektiren iki madde
ayrı kararla açılır: `design_decisions[]` (`DEV-065`) ve (opsiyonel) pencere yüksekliği /
`meta.reasoning_profile`. `validate.py`nin mevcut `UYARI (mimari/sartname)` satırları
**aynen kalır**; muhakeme raporu **ek** bir çıktıdır (geriye dönük uyum, golden
referanslar etkilenmez).

---

## 8. Büyütme protokolü: gelecekteki gelişmiş dil modeli "bilgi mühendisi"

Kullanıcı: *"gelecekte gelişmiş bir dil modeli bu modül bağlamında özel olarak bu
mantıkları geliştirebilmeli; her modül bağımsız geliştirilebilir olmalı."*

### 8.1 Rol ve izin sınırı

`docs/agents/KNOWLEDGE_ENGINEER_AGENT.md` (`DEV-070`): **yazabilir** → `scripts/reasoning/lenses/`,
`scripts/<modül>/reasoning.py`, `scripts/reasoning/cases/`, ilgili `CLAUDE.md`nin
"Muhakeme katkısı" bölümü; **yazamaz** → şema, `validate.py`, kaynaksız eşik/`kesin`
statüsü, `context.json`, başka modülün iç kodu, anayasa. `AGENT_PERMISSIONS.json`a
`knowledge_engineering` girişi eklenir; **final kabulü reviewer + sistem mimarı verir**
(developer kendi çıktısını kabul edemez).

**Vaka → İlke → Veçhe akışı** (`DEV-048` Aşama 3, geri besleme):
1. **Vaka:** gerçek bir defekt (kullanıcı gördü / ajan buldu) → `cases/<ad>/` altına
   mini sahne + beklenen bulgu kümesi (`uC` sandviç banyosu böyle girer).
2. **İlke:** defekt hangi mercek/veçheye ait? Var mı → vakayı ekle, kural genişlet.
   Yok mu → tek cümlelik ilke + `why_tr` yaz (`idea`).
3. **Veçhe:** terfi merdiveni (§7.3).
4. **Kayıt:** `HD` kaydı + ilgili modül `CLAUDE.md` satırı + (kaynak gelince) kalibrasyon.

### 8.2 Vaka kütüphanesi (`scripts/reasoning/cases/`)

`golden/`den **bilinçli ayrı**: golden tam bir proje üretir (DXF + ölçüm raporu);
vaka yalnız **kat parçası** (`rooms/walls/openings[/furniture]`) + `expected_findings.json`
(beklenen `key`ler, **yokluğu beklenenler** dahil) taşır ve saf Python'la saniyeler içinde koşar.
Biçim: her vaka bir ihlal VE aynı geometrinin bozulmamış (yanlış-pozitif) kardeşi.
Başlangıç vakaları gerçek geçmişten: `uC_sandvic_banyo`, `uC_gecis_odasi`, `giris_wc_gorus`,
`dar_hol_kolu`, `penceresiz_yatak`. Geriye dönük vakaların (`penceresiz_yatak`, `uC_*`)
kat parçaları **git geçmişinden** alınır (rev-22 sonrası durum: commit `727405f`; rev-23
düzeltmesi: `7d32a2d`) — böylece vaka uydurma değil, gerçek eski geometridir.

### 8.3 Kalibrasyon ve ayırt edicilik

Bir veçhenin `active`e yükselmesi için **ayırt edicilik** ölçülür: golden seti + gerçek
projedeki tetik oranı. ~%100 (her birimde öter) veya ~%0 (hiç ötmez, vaka dışında) ise
bilgi taşımaz → `shadow`da kalır, ayırıcı eklenir. **Yanlış-pozitif bütçesi:** bir
projede kullanıcıya sunulan "dikkat+ciddi" bulgu sayısı için üst sınır (taslak: tekil
konu başına ≤3, birim başına ≤5; kalibrasyonla ayarlanır). Kullanıcı gerçek yönetmelik/
referans getirdikçe eşikler kalibre edilir (`standards/` "Gelecek güncelleme sözleşmesi" ile
aynı: **değer** değişimi sürüm artırmaz; **alan şekli** değişimi artırır).

### 8.4 Her modülün `CLAUDE.md`sine eklenecek standart bölüm

```markdown
## Muhakeme katkısı (DEV-048)
- **Rol:** ölçüm sağlayıcı | kural sahibi | sunum | muaf (gerekçe: …)
- **Sağladığı ölçümler:** (fonksiyon → ne ölçer → hangi veçheler kullanır)
- **Katıldığı veçheler:** (lens paketindeki veçhe kimlikleri; kayıt lens paketindedir, bu modül yalnız ölçümünü sağlar)
- **Bildiği gerilimler:** (bu modülün kararının dokunduğu diğer veçheler)
- **Bilinen boşluklar / bir sonraki en değerli veçhe:**
- **Bilgi mühendisi için not:** (bu modülde yeni veçhe eklerken dikkat edilecek tuzaklar)
```

### 8.5 Soğuk başlangıç sınavı (Aşama 5'in ölçütü)

Yetenek yalnız bu konuşmada kalmıyor mu? **Sınav:** yeni bir ajan, yalnız kök `CLAUDE.md`
+ bu belgeyi (sonra `scripts/reasoning/CLAUDE.md`) okuyarak, verilen üç vakada (a) doğru
teşhisi koyar, (b) sayı uydurmadan §5 iskeletiyle anlatır, (c) `uC` vakasındaki kokuyu adıyla bulur.
Sınavı **reviewer** (geliştiriciden bağımsız) yürütür; geçmezse bilgi eksiktir, ajan değil.

---

## 9. Her modül için muhakeme rolü

"Her modül için bu mantığı düşün; her modül bağımsız geliştirilebilir olmalı." Tablo,
*bugünkü* `scripts/` modülleri için rolü ve **bir sonraki en değerli veçheyi** verir.
Roller: **ÖS** = ölçüm sağlayıcı, **KS** = kural sahibi, **SU** = sunum/anlatım, **MU** = muaf
adayı (gerekçeli). *Tümü aday; hiçbiri kodlanmadı.*

| Modül | Rol | Muhakemede sahip olduğu/sağladığı | Sonraki en değerli veçhe |
| ----- | --- | --------------------------------- | ------------------------ |
| `architect` | KS+ÖS | mahremiyet/tesisat/sirkülasyon kuralları; ilişkisel ölçümler (görüş hattı, ortak duvar, graf) | `mahremiyet.gorsel.giris_yatak` |
| `standards` | KS+ÖS | oran/net ölçü/kapı-koridor nüansları; `Provenance` emsali | `yasanabilirlik.wc.kullanim_alani` |
| `openings` | KS+ÖS | kapı açılımı (`swing_geometry`), net geçiş, kanat; pencere konumu | `isik.pencere.varlik` (pencere→oda ölçümü) |
| `rooms` | ÖS | poligon, alan, centroid, oda tipi; oda↔oda komşuluk ham verisi | oda komşuluk grafı (ortak sorgu katmanı ile) |
| `walls` | KS+ÖS | duvar türü/kalınlık (`WallCatalog.kind`): **akustik kütle**, taşıyıcı/bölme ayrımı | `mahremiyet.isitsel.ortak_duvar` (tür ayırıcılı) |
| `furniture` | ÖS | katalog ölçüleri (`yatak_cift` …) → **deneme yerleşimi** ham maddesi | `yasanabilirlik.mobilya.sigar_mi` |
| `collision` | ÖS (+sınır) | fiziksel çakışma (FORBID alanı); **mimari muhakemenin sınırını çizer** (anayasa 1) | — (sınır koruyucu) |
| `columns` | KS+ÖS | kolon konumu/kesiti → kolon oda ortasında mı | `yapisal.kolon.oda_ortasi` |
| `axis` | ÖS | aks ızgarası → açıklık/derinlik, cephe tayini | cephe tayini (`isik.capraz_havalandirma`) |
| `dimensions` | SU | hangi ölçü kime gösterilir; **ölçü metni her zaman tam sayı cm** | sade kullanıcıya ölçü gizleme profili |
| `elevations` | ÖS | kat yığını → kat yüksekliği, cephe açıklığı | `isik.derinlik` (yükseklik gelince) |
| `sections` | ÖS | kesit kat yığınını ödünç alır | kesitte baş yüksekliği (merdiven) |
| `stairs` | KS+ÖS | merdiven çıkış noktası/yönü, kol sığması | `erisilebilirlik.merdiven.konfor` (aday) |
| `shafts` | KS+ÖS | şaft konumu/kare kuralı, kat arası aynı konum | `tesisat.islak.duseyyigin` (kat arası) |
| `levels` | ÖS | kot/eşik farkları | `erisilebilirlik.esik` (aday) |
| `ceiling` | ÖS | oda tavan kotu → hacim/havalandırma | `isik.hacim` (aday) |
| `northarrow` | ÖS | `meta.north_angle` — **yönelim mercekinin tek veri kaynağı** | `isik.yonelim.*` (veri gelirse) |
| `templates` | KS | üreteç seçenekleri — mercek puanlarıyla **aday sıralama** | merkezi çekirdek adaylarını mercekle puanla |
| `importer` | SU+ÖS | dışarıdan okunan veri **güven düzeyi**: belirsiz geometri → "kullanıcıya sor" | `veri_guveni` (aday) |
| `pafta` | SU | ölçek/kağıt kısıtı anlatımı ("ölçek küçültülemez" kuralını sade dille açıklama) | mevzuat uyarısı → sonuç dili |
| `legend` | SU | cetvel; alan/malzeme cetveli ileride `ekonomi_verim` | `ekonomi_verim.net_brut` |
| `palette` | MU/SU | katman renk ayrışımı; okunabilirlik (yazdırma kontrastı) | — |
| `typography` | MU/SU | minimum metin yüksekliği (baskı okunabilirliği) | — |
| `version` | MU | sürüm kapısı | — |

**Kural:** bir modül muaf listesine ancak gerekçeyle girer (`COLLISION_EXEMPT` gibi);
muaf olması "düşünülmedi" demek değildir, **"düşünüldü, bu modül muhakemeye ölçüm/kural vermez"**
demektir ve gerekçe yazılıdır.

---

## 10. Uygulama planı

### 10.1 Uygulama sırası (2026-10-09 — kod denetimiyle belirlendi)

**Sıra DOĞRUSALDIR.** Eski taslaktaki "paralel" gösterimler (`{061 ∥ 064 ∥ 070}`, `{062, 063}`) geçersizdir:
görev kuyruğunun kuralı aynı anda **tek** `IN_PROGRESS` görevdir ve `DEV-070` zaten `DEV-061`e
sert bağımlıydı (eski sıra kendi içinde çelişiyordu). Sırayı üç şey belirledi: (i) sert bağımlılıklar
(her biri iki bağımsız ajanca koda karşı doğrulandı), (ii) kullanıcıya görünür değerin ne zaman doğduğu,
(iii) kullanıcı kararlarının ve şema değişikliklerinin gruplanması.

| Sıra | Görev | Efor | Sert önkoşul | Kullanıcıya görünür sonuç | Şema |
| ---- | ----- | ---- | ------------ | ------------------------- | ---- |
| 1 | `DEV-059` ortak mekânsal sorgu katmanı | M | — | yok (temel; bakım riski düşer) | — |
| 2 | `DEV-060` muhakeme çekirdeği | L | — (`059` yumuşak) | yok (altyapı) | — |
| 3 | `DEV-061` mahremiyet paketi | L | 060 | ilk yeni bulgular **gölgede** (rapor); ölçüm #4/#5 raporda | — |
| 4 | `DEV-064` diyalog + açıklama motoru | L | 060 | **ilk görünür kazanç:** 15 uyarı satırı → 3 konu, sade anlatım | — |
| 5 | `DEV-065` karar kaydı | M | 060, 064 | bilinen 3 canlı uyarıyı gerekçeyle **kabul edebilme** | **1.4.0** |
| 6 | `DEV-070` bilgi mühendisi rolü + soğuk başlangıç sınavı | M | 060, 061 | yok (genişletilebilirlik kanıtı) | — |
| 7 | `DEV-062` ışık-hava-yönelim paketi | L | 059, 060 | penceresiz yaşam mahalli / havalandırma / (veri gelirse) yönelim | pencere yüksekliği kararı |
| 8 | `DEV-063` yaşanabilirlik + deneme yerleşimi | L | 059, 060 | "yatak odası sığar mı" cevabı | — |
| 9 | `DEV-066` kalibrasyon ve terfi politikası | L | 059, 060, 061 | shadow→active terfileri (asgari makine 060/061'de) | — |
| 10 | `DEV-069` ihtiyaç beyanı | L | — (`056` tamam) | mimar olmayan kullanıcıdan ihtiyaç toplama (önce v0, şemasız) | v1'de evet |
| 11 | `DEV-068` etki analizi | XL | 059 | "banyoyu büyüt" → etkilenen eleman kümesi (v1: yalnız rapor) | — |
| 12 | `DEV-067` modül yaygınlaştırma (kalan dalgalar) | XL | 059, 060 | kapı #10 bloklayıcı olur | — |

**Neden bu sıra:**
- `059`→`060` **temel**: yeni mercek ölçümleri 6.–7. geometri kopyasını doğurmasın; çekirdek olmadan paket yazılamaz.
- `061` çekirdeğin ilk gerçek sınavıdır ve gerçek geçmiş vakalarla (iki commit) kanıtlanır.
- `064` **`061`den hemen sonra**: kullanıcının fark edeceği ilk iyileşme budur (15 satır → 3 konu); gerçek bulgu ve facet kaydı gerektirir.
- `065` `064`ten sonra: `064` olmadan sunulan bulgu yok, kabul edilecek şey de yok; üstelik bugün zaten görünen 3 uyarı için **hemen** işe yarar. Şema MINOR artışı bir kez yapılır; pencere yüksekliği alanı (varsa) aynı sürüme alınır.
- `070` **iki paketten önce değil, `061`den sonra**: protokol gerçek bir paketten damıtılır; `062`/`063` protokole uyularak yazılır ve **genişletilebilirliğin ilk kanıtı** olur.
- `066` ≥2 paketten sonra: politika/sınırlar tek paketle karşılaştırılamaz. **Ancak asgari terfi makinesi (konu başına ölçüm sözleşmesi, tetik oranı raporu, `legacy` bayrağı, imzalı terfi kaydı) `060`/`061`e çekilir;** aksi halde `061`in kabulü `066`ya, `066` da `061`e bağımlı olurdu (döngü).
- `069`, `068`, `067` çekirdeğe bağımlı ama onu beklemeyen **büyük işlerdir**; değer/efor sırasıyla sona. `067`nin ilk dalgası zaten paketlere gömülür (sürekli "rolling" iş tek-`IN_PROGRESS` kuralıyla uyuşmaz).

**Kritik yol:** `059 → 060 → 061 → 064 → 065`. İlk görünür kazanç 4. adımdadır.

### 10.2 `DEV-040` fikirlerinin bu plana oturması

| `DEV-040` fikri | Bu planda |
| --------------- | --------- |
| 1. Şiddet sayısı | §3.2 `severity` 0–1 + bantlar (`DEV-060`) |
| 2. Bina tipi profilleri | `Profile` kayıtları (§3, `DEV-060`); seçim `meta.reasoning_profile` = ayrı karar |
| 3. Katlar arası ilişkiler | `tesisat_hijyen.düşey` aday merceği + `vertical` bileşeni (`DEV-040`'ta kalır, bu plana **girdidir**) |
| 4. `options_for_*` yaygınlaştırma | `remedies` = seçenek kimlikleri (§3.1) |
| 5. Proje bazlı profil/eşik | yalnız **profil seçimi** şemaya girer, eşik değil (anayasa 6) |
| 6. Bilinçli göz ardı izi | §5.5 / `DEV-065` |

### 10.3 Geriye dönük doğrulama (planın kendi sınavı)

Plan "gerçekten bulur mu" diye gerçek geçmişle sınanır: (i) `rev-22` `uC` penceresiz oda →
`isik.pencere.varlik` yakalamalı (**ölçüldü:** `727405f` durumunda K1 `uC_oda`ya değen pencere
sayısı 0, rev-23 düzeltmesi `7d32a2d`'de 1 — vaka gerçek eski geometridir); (ii) `uC` sandviç banyosu → `sandvic_banyo` kokusu;
(iii) `DEV-041` kapı kaydırma → regresyon karşılaştırması yeni görüş hattını göstermeli;
(iv) bugünkü rev-28 → ölçüm #4/#5 bulgusu. Dördü de yakalanmıyorsa bilgi modeli yetersizdir.

---

### 10.4 Kod denetiminin bulguları (2026-10-09) — plana geri yazılan düzeltmeler

On iki görev, gerçek koda karşı ayrı ajanlarca denetlendi; on biri ikinci bir ajanca çürütülmeye
çalışıldı (`DEV-070` limit nedeniyle yalnız tek denetim aldı). Ortak sonuç: **12 görevin 9'u
olduğu gibi uygulanamıyordu** (kabul ölçütü döngüsel, kör ya da kendi kendiyle çelişiyor). Ayrıntılar
her görevin "Geliştirici yorumu" bölümündedir; planı değiştiren çapraz bulgular:

1. **Kör doğrulama.** `validate.py` çıktısı 11 mekânsal yardımcının 6'sına, `--golden-set` ise
   denenen 9 doğrulama yardımcısının hepsine **kördür** (mutasyon denemesi). "Çıktı bire bir aynı"
   tek başına taşımanın doğruluğunu kanıtlamaz; her taşıma/adaptör için eski↔yeni **diferansiyel
   selftest** şarttır.
2. **Kapı #10 ilk gün kırmızı.** 23 paketin hiçbirinde `reasoning.py` ya da gerekçeli muafiyet yok
   (spatial/reasoning ile 25). Kapı üç durumlu olur (§7.2); bloklayıcılık `DEV-067` sonunda.
3. **Veçhe sahipliği çelişkisi — ÇÖZÜLDÜ (kullanıcı kararı 2026-10-09): veçhe kaydı lens paketinde, ölçüm/kural sahibi modülde.** Eskiden §2.1/§7.1 "lens paketinde", §2.3-8/§8.4/§9 "sahibi modülde" diyordu.
   İki denetim zıt öneri verdi (060: modül-sahipli, 067: lens paketinde + modül yalnız rol/ölçüm).
   **Kullanıcı kararı bekliyor** (görev `DEV-060`, soru 3).
4. **`DEV-060` ↔ `DEV-064` kapsam çakışması.** `explain.py`, rakam lint'i ve kök-neden kümeleme yalnız
   `DEV-064`ündür; `060` yalnız `Finding`/anahtar/kayıt/kapsam raporu taşır.
5. **Mevcut `check_*` → `Finding` adaptörü.** Çağrı imzası 8 çeşit; mesajdan türetilen anahtar
   tekil değil; 33 fonksiyonun 3'ü toplayıcı, bir kısmı `validate.py`nin HATA kanalında, bir kısmı
   **hiç çağrılmıyor**. v1 adaptör anahtarı `legacy.<modül>.<fonksiyon>|<kat>|<sıra>`, şiddet `None`.
6. **Tamamlanmış ama bağlanmamış kurallar.** `check_wet_area_adjacency` (`DEV-052`) ve
   `check_entry_wet_door_proximity` (`DEV-053`) tanımlı ve selftest'li, fakat `validate.py` bunları
   **hiç çağırmıyor** (doğrulandı: `validate.py:97-105` içe aktarımları ve `:624-631` çağrıları). Gerçek
   projede çalışmıyorlar. Bunları bağlamak `validate.py` çıktısını değiştirir → plan §11 #2 ile
   birlikte kullanıcı kararı; `DEV-061` bunları **shadow** kaydeder.
7. **Terfi makinesi döngüsü** (yukarıda 066 notu): asgari makine öne çekilir.
8. **Alt görev kimlikleri sayısal olmalı.** `doc_check.py` `### DEV-\d+` ister; `DEV-063A` gibi
   kimlikler maddeyi görünmez kılar. Bölünen her parça ayrı **numaralı** DEV olur (örn. sınav için
   önerilen `DEV-071`); bölme, ilgili maddenin netleştirme turunda kullanıcıyla kararlaştırılır.
9. **Operatör kaynak erişimi.** Plan başlığı "operatör ajan → §3,4,5" diyor ama operatör talimatı
   `docs/development/`i okuyamıyor; `DEV-064` bu erişimi (ya da kopyasını) çözmek zorunda.

## 11. Açık kararlar (kullanıcı/sistem mimarı)

Aşağıdakiler benim önerimle birlikte listelenmiştir; **onay gelmeden ilgili görev başlamaz**.

| # | Karar | Öneri | Neyi bloklar |
| - | ----- | ----- | ------------ |
| 1 | Çekirdeğin adı/yeri: `scripts/reasoning/` | evet | `DEV-060` |
| 2 | `validate.py` çıktısı **değişmesin**; muhakeme raporu ek | evet | `DEV-060`/`061` |
| 3 | `design_decisions[]` şema alanı (kullanıcı gerekçesi zorunlu, kanıta bağlı) | evet, Faz 4 | `DEV-065` |
| 4 | Pencere yüksekliği: veri alanı mı, katalog varsayılanı + onay mı? | **veri alanı (opsiyonel, opt-in)** — uydurma yok | `DEV-062` pencere/taban oranı |
| 5 | `meta.reasoning_profile` (profil seçimi) | ertele, Faz 4 sonrası | profil ağırlıkları |
| 6 | Hangi yönetmelik maddeleri **önce** getirilsin? (aydınlatma-havalandırma, merdiven, kaçış) | kullanıcı getirir; o zamana kadar `yaygin`/`tercih` | `kesin` statülü veçheler |
| 7 | Mercek önceliği: mahremiyet → ışık → yaşanabilirlik | evet | Faz 2–3 sırası |
| 8 | "Sade / mimar" dil sorusu oturum başında bir kez | evet | `DEV-064` |
| 9 | Misafir WC kavramı (`mahremiyet.gecis.misafir`) hangi veriyle? | kullanıcı kararı (oda alanı mı, birim bildirimi mi) | o veçhe |
| 10 | Komşu giriş kapısı yakınlığı bulgusu (ölçüm #5, 1485 mm) **gerçek projede** ele alınsın mı? | plan değişikliği DEĞİL, bilgi; kullanıcı isterse revizyon | — |

## 12. Riskler ve karşı önlemler

| Risk | Karşı önlem |
| ---- | ----------- |
| **Alarm yorgunluğu** (her şey ötüyor) | sunum kuyruğu ≤3, ayırt edicilik, `shadow` merdiveni, kök-neden kümeleme |
| **Dil modeli rakam uydurur** | şablonda rakam yok + lint + evidence-only + operatör yasağı |
| **Kültürel önyargı** ("doğru plan" dayatması) | `tercih` statüsü, profil ağırlığı, `legit_overrides_tr`, anayasa 1 |
| **Bilgi bayatlar** | `provenance.reviewed` + doc_check #15 (bilgi, bloklamaz) |
| **Çekirdek şişer, her şeyi bilir hâle gelir** | çekirdek bilgi içermez; bilgi sahibi modülde (kapı #10, #11) |
| **Kurallar birbirini bozar** | gerilim kaydı + çoklu mercek regresyon farkı (adım 9) |
| **"Temiz = iyi" yanılgısı** | kapsam raporu: koşamayan mercek adıyla söylenir |
| **Mevcut çıktı bozulur** | `validate` satırları aynen; golden etkisi sıfır (kabul ölçütü) |
| **Yönetmelik rakamı yanlış kodlanır** | kaynaksız `kesin` yasak (kapı #14); kullanıcı kaynağı getirir |
| **Tek geliştirici-ajan yanlış bilgi ekler** | bilgi mühendisi final kabul veremez; reviewer + soğuk başlangıç sınavı |

---

## Ek A — Çalışılmış örnek: `uC` vakası bu çerçevede nasıl işlenirdi

(Gerçek geçmişten; rev-22/23, `architect/CLAUDE.md` "uC yeniden-zonlama".)

1. **Bulgular (bugünkü kurallarla):** `check_wet_area_reachable_without_bedroom` (zincir),
   `check_circulation_area_share`. **Kaçan:** banyonun hem salona hem yatak odasına kapılı olması
   — hiçbir kural adlandırmıyordu.
2. **Teşhis (§4 adım 6):** ortak eleman `uC_banyo` → koku `sandvic_banyo` (kök neden: ıslak hacim iki
   bölge arasında) + `gecis_odasi_yatak` (ikinci kök neden).
3. **Gerilim (adım 7):** çözüm "banyoyu holden aç" ↔ hol payı (`sirkulasyon_akis`, eşik %15) ↔ salon derinliği.
4. **Sunum (§5), sade dil:** "`uC` dairede banyo, salon ile yatak odası arasında ve ikisine de kapısı
   var — yani misafir varken banyo hem salondan hem yatak odasından geçişli. Üç yol: (1) banyoyu holden
   açıp ikisinden kapatmak [hol bir miktar büyür], (2) olduğu gibi bırakmak [kaydederim], (3) yatak
   odasını başka yöne almak." (Gerçekte kullanıcı *"alternatif görmek istemiyorum, çalışmaya
   başla"* dedi — §5.8 `devret` — ve yol 1 uygulandı; hol payı eşiğin altında, %14.13'te kaldı.
   Çerçeve bu delegasyonu bozmaz: seçim sonradan bildirilir ve karar olarak kaydedilir.)
5. **Regresyon (adım 9):** düzeltmenin yeni bir giriş↔WC görüş hattı açıp açmadığı (`DEV-041` dersi) otomatik
   karşılaştırılır.
6. **Kayıt (adım 10):** vaka `cases/uC_sandvic_banyo` + koku kaydı; bir daha elle keşfedilmez.

## Ek B — Ölçüm yöntemi (§1.1'in yeniden üretilebilirliği)

Hepsi `context.json` rev-28 üzerinde, **salt-okunur**, `architect.rules` yardımcılarıyla:
#1 `validate.py` çıktısı, `[kat]` öneki atılıp tekilleştirme · #2/#3 `meta`/`openings` anahtar kümesi ·
#4 `_door_midpoint` + `_rooms_touching_point` ile giriş kapısı bulunur (birim odası ↔ birimsiz oda
teması), `check_entry_sightlines`ın koni+`_clear_line_of_sight` testi hedef = yatak odası kapısı ·
#5 giriş kapısı orta noktaları arası öklid mesafe · #6 `_shared_wall_length > 1 mm`, aynı birim,
ıslak hacim × (yatak odası, salon) · #7 `floors[].furniture` uzunluğu · #8 pencere orta noktası → oda
teması, yaşam mahalli penceresiz · #9 `def _door_mid*`/`_rooms_touching_point`/`point_in_polygon`/
`shared_edge_length` taraması. **Bu ölçümler ürün değildir;** `DEV-060` kurulunca aynı yöntem `cases/`
ve muhakeme raporunda kalıcılaşır.
