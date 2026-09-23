# Geliştirme Görev Kuyruğu

Bu dosya sistem geliştiricisinin sıradaki kontrollü işini gösterir. Aynı anda
tek bir görev `IN_PROGRESS` olabilir. Sistem mimarı `READY` görevi başlatır;
agent kendi başına sıra değiştirmez.

## READY

### DEV-006 — Golden fixture katalogu

- **Durum:** READY
- **Öncelik:** 1
- **Amaç:** Semantic golden raporlarını modül bazlı fixture ve kritik sembol
  beklentileriyle genişletmek.

## COMPLETED

### DEV-001 — Openings modülünü oluştur

- **Durum:** COMPLETED
- **Sonuç:** Typed `Opening`, `Door`, `Window`, `OpeningSchedule` ve
  enjekte edilebilir `DefaultPlanOpeningStyle` `scripts/openings/` içine alındı;
  generator host-wall ve açıklık genişliği doğrulaması yapıyor.
- **Kayıt:** `DEVELOPMENT_HISTORY.md` içindeki `HD-003`.

### DEV-002 — Room modülü

- **Durum:** COMPLETED
- **Sonuç:** `Room`, `PolygonOps`, `RoomLabeler` ve scanner sınırı
  `scripts/rooms/` içinde; kapanış, alan, self-intersection ve units-aware
  alan doğrulaması aktif.
- **Kayıt:** `DEVELOPMENT_HISTORY.md` içindeki `HD-003`.

### DEV-003 — DimensionChain modülü

- **Durum:** COMPLETED
- **Sonuç:** `DimensionChain`, `LinearDim`, `DimensionStyle` ve `ChainLayout`
  `scripts/dimensions/` içinde; AxisGrid gerçek DXF ölçülerini bu API ile
  üretir ve baseline bounds kontrolünden geçirir.
- **Kayıt:** `DEVELOPMENT_HISTORY.md` içindeki `HD-003`.

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
