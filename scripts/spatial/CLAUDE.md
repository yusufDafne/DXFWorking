# spatial modülü (ortak mekânsal sorgu katmanı) — DEV-059

Eleman-farkındalıklı mekânsal sorguların (kapı → orta nokta, bir noktaya değen odalar, iki poligonun
ortak kenarı, doğru parçası kesişimi / görüş hattı) **TEK sahibidir**. Eskiden `architect/rules.py`,
`standards/nuances.py`, `shafts/__init__.py` içinde ayrı ayrı yazılmıştı; rev-13 dersi ("iki yerde ayrı
hesaplanan geometri sessizce ayrışır") tekrar etmesin diye toplandı. Yeni mercek ölçümleri (`DEV-048`
planı) bu katmanı kullanır, yeni kopya doğurmaz.

## Bağımlılık yönü
`spatial → collision.geometry` (TEK yönlü). Ham poligon matematiği (`point_in_polygon`,
`point_on_boundary`) `collision/geometry.py`de KALIR; burada yeniden dışa aktarılır. `collision` bu
modülü ASLA import etmez. Saf Python: `ezdxf` yok, çizim yok, context'e yazmaz, `context.json`'dan alan
okumaz (`CONTRACT_VERSION = "1.0"`).

## Public API
`door_midpoint`, `door_frame`, `rooms_touching_point`, `dist_point_segment`, `touches_within`,
`vertex_mean`, `segments_intersect`, `clear_line_of_sight`, `shared_edge_length`, `point_in_polygon`,
`point_on_boundary`; sabitler `TOUCH_TOLERANCE_MM` (300), `SHARED_EDGE_TOLERANCE_MM` (1.0).

## Davranış korunarak taşındı — BİLİNÇLİ ayrılıklar (kullanıcı kararları 2026-10-09)
- **Sıfır uzunluklu duvar:** `door_midpoint` duvar başlangıç noktasını verir (eski architect),
  `door_frame` `(None, None)` verir (eski standards). Birleştirmek ayrı, açık bir değişikliktir.
- **`shared_edge_length` tek anlam = mimari sürüm** (her yönde, `tol` dahil dik uzaklık, yalnız `tol`dan
  büyük örtüşme). Eski `shafts` sürümünden dört sınır farkı ölçüldü ve selftest'te sabitlendi:
  0,5 mm örtüşme (eski 0,5 → yeni 0), tam 1,0 mm boşluk (eski 0 → yeni 1000), tam 1,0 mm örtüşme
  (eski 1,0 → yeni 0), 45° kenar (eski 0 → yeni 1414,2). Şaft eşiği (≥300 mm) gerçek context'teki tüm
  oda çiftlerinde aynı karar verir. `shafts.shared_edge_length` genel API olarak yeniden dışa aktarılır.
- **`touches_within`** (sqrt karşılaştırma, eski standards) ile **`rooms_touching_point`**
  (`point_on_boundary`, kare karşılaştırma) tam tolerans sınırında float düzeyinde ayrışabilir;
  birleştirilmedi.
- **`vertex_mean`** köşe ortalamasıdır; `rooms.PolygonOps.centroid` ALAN ağırlıklıdır (144 odanın
  37'sinde fark). Adı bilerek `centroid` DEĞİL.
- `rooms.PolygonOps._point_in_polygon` ince bir takma addır (selftest'e dokunulmaz).

## Doğrulama
`python scripts/spatial/selftest.py` — **neden diferansiyel:** `validate.py` çıktısı 11 mekânsal
yardımcının 6'sına, `--golden-set` ise denenen 9'una KÖRDÜR (DEV-059 mutasyon denemesi); bu yüzden
taşımanın doğruluğu burada kanıtlanır: eski kodun commit `9f97553`ten BİREBİR donmuş kopyaları oracle
olarak gömülüdür ve gerçek `context.json` (tüm katlar: açıklık × oda, oda çiftleri, görüş hatları) ile
deterministik tohumlu sentetik girdiler üzerinde yeni sürümle karşılaştırılır; elle hesaplanan değerler;
yanlış-pozitif kontrolleri; kasıtlı bozulmuş `door_midpoint`in karşılaştırmayı gerçekten kırdığı.

## Çakışma denetimi: EXEMPT
`collision/scene.py::COLLISION_EXEMPT` içinde: salt sorgu kütüphanesi, ayak izi üretmez.

## Muhakeme katkısı (DEV-048)
**Rol:** ölçüm sağlayıcı. Mercek ölçümlerinin (görüş açısı, ortak duvar, pencere→oda, dış duvar) ortak
zemini; bilgi mühendisi yeni ölçümü burada (kopya olarak değil) tanımlar. Bilinen boşluk: dış duvar/cephe
tayini ve pencere→oda sorgusu `DEV-062`de, duvar/oda-kenarı çakışma ailesi (`walls/thickness._on_edge`,
`standards/measure.edge_wall_thicknesses`, `architect/layout._collinear_overlap`) `DEV-068` için eklenecek.

## Bilinen sınırlamalar
- Kapsam yalnız `architect`, `standards`, `shafts`, `rooms` kopyalarıdır. `validate.py` içindeki
  `point_on_segment`/`point_position_on_segment` (`walls/geometry` kopyası) ve `architect/layout.py`
  `_edge_overlap`/`_collinear_overlap` henüz taşınmadı (DEV-059 denetiminde "en az 5 kopya" bulgusu).
