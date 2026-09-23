# Geliştirme Fikirleri

Bu dosya henüz görev kuyruğuna alınmamış fikirleri tutar. Fikirler tasarım
verisi veya uygulama direktifi değildir. Sistem mimarı bir fikri `PLANNED`
veya `READY` göreve dönüştürmeden agent uygulamaya başlayamaz.

## Generic altyapı fikirleri

- **Golden output semantik diff:** DXF entity/layer/bbox/critical symbol
  karşılaştırmasını otomatikleştirmek.
- **Provenance manifest:** Her nihai DXF için proje, revizyon, schema, kod
  sürümü, validation sonucu ve üretim zamanını eşleyen manifest.
- **Schema karar kayıtları:** `walls[].kind`, opening varyantları ve
  `meta.drawing_standard` gibi önerileri karar geçmişiyle yönetmek.
- **Read-only design scanners:** Room, wall ve import scanner önerilerini
  kullanıcı onayı olmadan context'e yazmayan ortak rapor sözleşmesi.
- **Golden fixture katalogu:** Seçilmiş nihai DXF örneklerini modül bazında
  beklenen entity ve geometri özellikleriyle tanımlamak.
- **Faz otomasyonu:** Görev kuyruğu, focused validation, history ve developer
  notes güncellemesini kontrol eden bir geliştirici yardımcı komutu.

## Mimari ve ürün fikirleri

- Pafta bölme + keyplan.
- Uniform sheet template.
- Tip-A kapak paftası ve resmi metadata modeli.
- DXF/PDF import için insan onaylı patch akışı.
- Proje revizyonları arasında görsel ve geometrik fark raporu.
- Modüler uygulama projesi üretimi için disiplinler arası çıktı paketleri.

## Fikirden göreve geçiş ölçütü

Bir fikir göreve alınmadan önce şu sorular cevaplanır:

1. Hangi kullanıcı veya sistem riski çözülüyor?
2. Hangi modülün sorumluluğunda?
3. Context/schema değişikliği gerekiyor mu?
4. Deterministik kabul ölçütü nedir?
5. Mevcut golden DXF'lere etkisi nedir?
6. Sistem mimarının hangi kararı gerekiyor?
