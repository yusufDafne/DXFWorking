# testfit modülü (deneme yerleştirme sınavı) — DEV-063

"Bu odaya tipik bir tefriş kümesi **sığar mı?**" sorusunu, tefriş verisi olmayan projede de, katalog ölçüleriyle ve kapı açılım sektörüyle
birlikte sınar. Mimar bunu zihninde mobilya koyarak dener; sistemde bu deneme yoktu (`rev-22`de penceresiz/yatağı sığmayan oda elle fark edildi).
**Sonuç türevdir, `context.json`a YAZILMAZ ve bir çözüm önerisi DEĞİL bir SINAVDIR** ("sığdı / sığmadı, hangi kapasitede"); yerleşim kararı kullanıcınındır.

## Neden ayrı modül (kullanıcı kararı 2026-10-09)
`furniture/` çizim + katalog sorumluluğunu temiz tutar; deneme yerleştirme *muhakemedir* (`collision` ayak izi disipliniyle aynı gerekçe: çizim ≠ muhakeme).
`testfit/` yalnız **tüketir**: `furniture` (tip ölçüleri), `collision` (kapı sektörü + çakışma politikası + son doğrulama), `standards.measure` (net oda),
`openings.collision` (kapı sektörü ayak izi). Hiçbirini DEĞİŞTİRMEZ. (Ad `furnish/` DEĞİL: `furniture/` ile üç harf yazım tuzağı.)

## İçerik
| Dosya | Görev |
|---|---|
| `library.py` | `Cluster`, `BEDROOM_CLUSTERS` — kapasite merdiveni **K1 > K2 > K3 > K4**: K1 çift yatak + 2 komodin + gardırop, K2 çift yatak + gardırop, K3 tek yatak + gardırop, K4 tek yatak. Kütüphane verisi ('yaygın', yönetmelik DEĞİL), context'e yazılmaz. v1 YALNIZ `yatak_odasi` |
| `engine.py` | `try_fit` (deterministik geri izlemeli arama; eksen-hizalı iki yön; aday konumlar net sınır kutusuna / yerleşmiş parçalara / kapı sektörüne hizalı), `best_cluster` (K1→K4 ilk sığan), `net_room_polygon` (merkez çizgisi poligonundan duvar iç yüzleri arası NET), `verify_with_collision` (son doğrulama `collision.CollisionEngine` ile) |
| `measure.py` | `check_bedroom_single_bed_fits` (K4), `check_bedroom_double_bed_wardrobe_fits` (K2) + `*_subjects` ikizleri, `bedroom_capacity` (oda → en büyük sığan küme, yorumsuz rapor) |
| `reasoning.py` | muhakeme sağlayıcısı (rol + ölçüm beyanı); veçhe kayıtları `reasoning/lenses/yasanabilirlik.py` |

## Katmanlar ve değişmezler
- **Katman A (geçiş payı = 0):** yalnız katalog ölçüsü + `collision` kuralı (tefriş↔tefriş, tefriş↔kapı sektörü, oda dışına taşma; temas toleransı
  `CONTACT_TOLERANCE` = 5 mm — yani 5 mm'ye kadar girişim TEMAS sayılır, `collision` ile aynı). Veçheler `shadow`. **Katman B (rahat sığma payları) mimar değer verene
  dek `draft`'tır ve KODLANMAZ** (`yasanabilirlik.mobilya.gecis_payi`).
- **Net ölçü:** oda poligonu duvar MERKEZ çizgisindedir; sınav duvar iç yüzleri arası net poligonla yapılır (uC_oda: 2950×3175 mm).
- **Sınırlı arama:** `MAX_NODES` aşılırsa sonuç `None` = **OLCULEMEDI**, "sığmaz" DENMEZ. Son doğrulama `collision` ile çelişirse "sığdı" denmez.
- **Opt-in/sessizlik:** `room_type='yatak_odasi'` olmayan odaya bakılmaz (kapsam raporu "uygulanmaz"); `unit_id` gerekmez.
- **Sürüm:** `CONTRACT_VERSION` 1.0 — context'ten yalnız eleman sözlüklerini (`rooms[].polygon/room_type`, `walls[]`, `openings[]`) okur, yeni alan YOK.

## Çakışma denetimi: EXEMPT
`collision/scene.py::COLLISION_EXEMPT` içinde: kendi ayak izini ÜRETMEZ; `collision` motorunu çağırarak doğrular.

## Muhakeme katkısı (DEV-048)
- **Rol:** ölçüm sağlayıcı. **Mercek:** `yasanabilirlik`.
- **Sağladığı ölçümler:** `check_bedroom_single_bed_fits` → `yatak_odasi_tek_yatak_sigar`; `check_bedroom_double_bed_wardrobe_fits` → `yatak_odasi_cift_yatak_gardirop_sigar` (ikisi `shadow`).
- **Bildiği gerilimler:** yaşanabilirlik ↔ alan ekonomisi; yaşanabilirlik ↔ ışık (pencere önünü dolap kapatır) — karşı veçhe kayıtlı olmadığı için yazılmadı.
- **Bilinen boşluklar:** mutfak (`counters[]` çakışma sağlayıcısı yok), WC/banyo (net ölçüler DEV-049/050'de), salon kümesi; kullanılabilir duvar uzunluğu (`idea`); Katman B payları; pencere önü.
- **Bilgi mühendisi için not:** yeni oda tipi = `library.py`ye yeni küme merdiveni + `measure.py`ye ölçüm + vaka çifti; kümeyi uydurma, `furniture` kataloğunda olmayan tip ekleme. Sığma sınavı collision toleransını (5 mm) taşır: sınır testlerini ona göre yaz.

## Doğrulama
`python scripts/testfit/selftest.py` — beş kontrol: elle hesaplanan sınırlar (K4 900×2000; K2 2195/2194; K1), kapı sektörü (sürme kapı yanlış-pozitifi dahil), L-şekli oda, bütçe→olculemedi,
gerçek rev-28 + `collision.check_context` ile tutarlılık ve kasıtlı kaydırmanın yakalanması. Muhakeme tarafı `scripts/reasoning/selftest.py`de (`check_yasanabilirlik_pack`).

## Bilinen sınırlamalar
- Yalnız eksen-hizalı yerleşim (eğik duvarlı odada aday konumlar sınırlı olabilir; "sığmaz" muhafazakâr yönde yanılabilir).
- Pencere önü, radyatör, kapı dışı engeller (kolon, niş) modellenmez; kolon `collision` ile ayrıca denetlenir ama burada engel değildir.
- Mobilya yönü/ön yüzü (yatak başı duvara) ve işlevsel kurallar yok: yalnız "ayak izi sığar mı".
