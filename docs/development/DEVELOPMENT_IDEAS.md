# Geliştirme Fikirleri

Bu dosya henüz görev kuyruğuna alınmamış fikirleri tutar. Fikirler tasarım
verisi veya uygulama direktifi değildir. Sistem mimarı bir fikri `PLANNED`
veya `READY` göreve dönüştürmeden agent uygulamaya başlayamaz.

## Generic altyapı fikirleri

- ~~**Golden output semantik diff**~~ — göreve alındı ve tamamlandı
  (`DEV-004`, `DEV-006`); bugün `scripts/golden_report.py` üç katmanlı.
- ~~**Provenance manifest**~~ — göreve alındı: `DEV-020`. rev-12'de mimarisi
  karara bağlandı: manifest **teşhis** aracıdır (bloklamaz), bloklayıcı kapı
  ise tek bir `meta.schema_version` alanıdır.
- **Schema karar kayıtları:** `walls[].kind`, opening varyantları ve
  `meta.drawing_standard` gibi önerileri karar geçmişiyle yönetmek.
- **Read-only design scanners:** Room, wall ve import scanner önerilerini
  kullanıcı onayı olmadan context'e yazmayan ortak rapor sözleşmesi.
- ~~**Golden fixture katalogu**~~ — göreve alındı ve tamamlandı (`DEV-006`).
  rev-11'de ad değişti: "fixture" mimaride SABİT TESİSAT anlamına geldiği için
  yanıltıcıydı; bugün `golden/` altında **golden referans projeleri** denir.
- **Faz otomasyonu:** Görev kuyruğu, focused validation, history ve developer
  notes güncellemesini kontrol eden bir geliştirici yardımcı komutu.

## Mimari ve ürün fikirleri

- Pafta bölme + keyplan.
- Uniform sheet template.
- Tip-A kapak paftası ve resmi metadata modeli.
- DXF/PDF import için insan onaylı patch akışı.
- Proje revizyonları arasında görsel ve geometrik fark raporu.
- Modüler uygulama projesi üretimi için disiplinler arası çıktı paketleri.
- ~~Çakışma (clash) denetimi~~ — göreve alındı: `DEV-019`, mimarisi rev-12'de
  karara bağlandı (`scripts/collision/`, ters bağımlılık).

## Fikirden göreve geçiş ölçütü

Bir fikir göreve alınmadan önce şu sorular cevaplanır:

1. Hangi kullanıcı veya sistem riski çözülüyor?
2. Hangi modülün sorumluluğunda?
3. Context/schema değişikliği gerekiyor mu?
4. Deterministik kabul ölçütü nedir?
5. Mevcut golden DXF'lere etkisi nedir?
6. Sistem mimarının hangi kararı gerekiyor?
