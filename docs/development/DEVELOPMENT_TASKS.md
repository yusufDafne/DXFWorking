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

### DEV-007 — Resmi Tip-A kapak verisinin tamamlanması

- **Durum:** PLANNED
- **Bağımlılık:** Kullanıcıdan gelecek müellif (mimar) adı, proje/onay tarihi,
  ruhsat ve resmi onay bilgileri.
- **Mevcut durum:** Tip-A kapak **çizimi ve yerleşimi** rev-8'de tamamlandı
  (`scripts/pafta::CoverBlock`): kapak paftasının iç çizgisinin sağ-alt
  köşesine sabitlenmiş, çıktıda tam A4 (210x297mm) basan, her kenardan eşit
  offsetli çerçeveli bir blok; proje adı, proje tipi, ölçek, mimar/tarih
  alanları ve `meta.cover.signature_fields` ile sürülen imza kutuları.
  Verilmeyen alanlar UYDURULMAZ, elle doldurulacak çizgi olarak bırakılır.
- **Kalan iş:** `meta.cover.architect_name` ve `meta.cover.date` değerlerinin
  kullanıcıdan alınması; ayrılmış iki imza alanının unvanının belirlenmesi;
  ruhsat/onay alanlarının gerekip gerekmediğine karar verilmesi.
- **Beklenen ayrı talep:** Kullanıcı kapak **tasarımı** için ayrı ve özel bir
  prompt paylaşacağını bildirdi; içerik/tipografi düzeni o talep geldiğinde
  ele alınacak. Geometri (A4 ölçüsü, sağ-alt sabitleme, eşit offset çerçeve,
  antetsiz pafta) bu talepte değişmemelidir.
- **Kabul odağı:** Resmi alanlar schema ile tanımlı, eksik veri uydurulmamış ve
  kapak golden output ile doğrulanmış olmalıdır.

### DEV-008 — RoomLabeler yapısının geliştirilmesi

- **Durum:** PLANNED
- **Öncelik:** 2
- **Talep kaynağı:** rev-8 kullanıcı talebi ("mevcut room labeların yapısını
  geliştirmemiz gerekiyor").
- **Mevcut durum:** `scripts/rooms::RoomLabeler.draw` tek satırlık, sabit
  biçimli bir metin üretir: `"{ad} ({alan} m2)"`. Metin oda poligonunun
  centroid'ine `MIDDLE_CENTER` yerleştirilir ve yalnızca oda **genişliğine**
  göre `fit_text_height` ile küçültülür.
- **Bilinen sınırlamalar (ele alınacaklar):**
  - Tek satır zorunlu: uzun mahal adları (örn. "Salon (Amerikan Mutfak)")
    dar odalarda `min_height=60` tabanına kadar küçülüyor, okunaksızlaşıyor.
    Çok satırlı (ad / alan ayrı satır) bir düzen yok.
  - Sığdırma yalnızca yatay: oda **yüksekliği** hiç hesaba katılmıyor.
  - Konum sabit centroid: içbükey (L şeklinde) poligonlarda etiket oda
    dışına düşebilir; alternatif yerleşim veya leader çizgisi yok.
  - Biçim sabit: mahal no, mahal tipi, kaplama vb. alanlar eklenemiyor;
    etiket içeriği enjekte edilebilir bir stil/Protocol değil (karşılaştır:
    `openings::OpeningSymbolStyle`).
  - Alan metni her zaman `m2`; kök CLAUDE.md'deki "ölçü metni tam sayı cm"
    kuralıyla ilişkisi tanımlı değil.
- **Başlatma öncesi kararlar:** Etiket bloğu kaç satır olacak ve hangi alanları
  taşıyacak? Mahal no şeması (deterministik türetme mi, context verisi mi)?
  Poligon-içi yerleşim garantisi nasıl sağlanacak? `RoomLabelStyle` Protocol'ü
  eklenecek mi?
- **Kabul odağı:** Etiketler oda poligonu İÇİNDE kalır, pafta taşma kontrolünden
  geçer, mevcut oda çıktısındaki değişiklikler golden output ile raporlanır ve
  yeni mahal verisi uydurulmaz.

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
