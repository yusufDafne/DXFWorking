# Geliştirme Görev Kuyruğu

Bu dosya sistem geliştiricisinin sıradaki kontrollü işini gösterir. Aynı anda
tek bir görev `IN_PROGRESS` olabilir. Sistem mimarı `READY` görevi başlatır;
agent kendi başına sıra değiştirmez.

## READY

### DEV-001 — Openings modülünü oluştur

- **Durum:** READY
- **Öncelik:** 1
- **Kaynak:** `scripts/walls/render.py::DefaultPlanOpeningStyle` ve
  `WallNetwork` açıklık boşlukları.
- **Amaç:** `Opening`, `Door`, `Window`, host wall ilişkisi, plan sembol
  stili ve schedule sorumluluğunu izole etmek.
- **Bağımlılıklar:** `walls/` tamamlandı; `axis/` tamamlandı.
- **Önce okunacaklar:** `scripts/openings/CLAUDE.md`, `scripts/walls/CLAUDE.md`,
  `scripts/generate_dxf.py`, mevcut schema ve golden output.
- **Başlamadan önce sistem mimarı kararı:** opening schema alanları,
  `host_wall_id` semantiği, swing/menteşe eksikliği ve plan/cephe stil
  kapsamı.
- **Kabul:** mevcut açıklık rail boşlukları ve sembolleri korunur; focused
  test, validate ve generate başarılı olur; golden farkları raporlanır.

## COMPLETED

### DEV-004 — Golden output anlamsal karşılaştırması

- **Durum:** COMPLETED
- **Sonuç:** `scripts/golden_report.py` entity count/type, layer dağılımı,
  modelspace bbox ve SHA-256 raporu üretir; `--compare` ile semantic kontrol
  yapar.
- **Kayıt:** `DEVELOPMENT_HISTORY.md` içindeki `HD-002`.

### DEV-005 — Agentic kontrol altyapısı

- **Durum:** COMPLETED
- **Sonuç:** `development_control.py` atomik görev kilidi,
  `AGENT_PERMISSIONS.json` rol izinleri ve `PROVENANCE_TEMPLATE.json` eklendi.
- **Kayıt:** `DEVELOPMENT_HISTORY.md` içindeki `HD-002`.

## PLANNED

### DEV-002 — Room modülü

- **Durum:** PLANNED
- **Bağımlılık:** `openings/`
- **Kaynak:** `polygon_centroid`, `draw_room_label`, `RoomPolygonScanner`.
- **Kabul odağı:** kapalı poligon, alan, komşuluk, etiket fit ve oda-duvar
  tutarlılığı.

### DEV-003 — DimensionChain modülü

- **Durum:** PLANNED
- **Bağımlılık:** `axis/`; room/geometry sınırları netleşmiş olmalı.
- **Kaynak:** `AxisGrid._dim_chain_x/_dim_chain_y`.
- **Kabul odağı:** gerçek DXF dimension, tam sayı cm metni, chain layout ve
  pafta taşma kontrolü.

## BACKLOG

Sonraki modül sırası ve ayrıntılı planlar:

`columns/` → `elevations/` → `furniture/` → `legend/` → `import/`

Her görev uygulamaya alınmadan önce ilgili `scripts/<module>/CLAUDE.md` dosyası
ve `docs/phases/NEXT-MODULES-ROADMAP.md` okunur. Buradaki kayıtlar kod
uygulama izni değildir; yalnızca planlama ve devir bağlamıdır.

## Görev tamamlama kuralı

Bir görev için agent şunları yapmadan `COMPLETED` yazamaz:

1. Kabul ölçütlerini karşılayan kod/doküman değişikliğini tamamlamak.
2. Odaklı validation çalıştırmak.
3. Gerekli ise `validate.py` ve `generate_dxf.py` çalıştırmak.
4. Golden output etkisini kaydetmek.
5. Ayrı reviewer/validator çalışmasından kabul raporu almak.
6. `DEVELOPMENT_HISTORY.md`ye kayıt eklemek.
7. `DEVELOPER_NOTES.md`yi bir sonraki direktifle güncellemek.
8. `python scripts/development_control.py release ...` ile görev kilidini bırakmak.
