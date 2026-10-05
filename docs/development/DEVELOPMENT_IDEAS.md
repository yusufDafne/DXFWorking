# Geliştirme Fikirleri

Bu dosya henüz görev kuyruğuna alınmamış fikirleri tutar. Fikirler tasarım
verisi veya uygulama direktifi değildir. Sistem mimarı bir fikri `PLANNED`
veya `READY` göreve dönüştürmeden agent uygulamaya başlayamaz.

## Kat planı efektifliği ve endüstri standardı nüans fikirleri (kullanıcı talebi, 2026-10-05)

~~Kat planı efektifliği + 15 maddelik kapı/duvar/koridor endüstri
standardı nüans kataloğu (standart gözden geçirme, net geçiş genişliği,
ıslak hacim kapı kuralları, hol topolojisi kütüphanesi, sirkülasyon
çekirdeğinin merkeze taşınması + asansör kapısı, etüt modülünün 2D
yerleşim optimizasyonuna genişletilmesi)~~ — kullanıcı kararıyla
(2026-10-05) sekiz maddeye bölünüp göreve alındı: `DEV-049`…`DEV-056`
(`DEVELOPMENT_TASKS.md`). Uygulama sırası kullanıcı tarafından belirlendi:
`DEV-049 → DEV-050 → DEV-051 → DEV-052 → DEV-053 → DEV-054 → DEV-055 →
DEV-056` (gerekçe ve her maddenin ayrıntısı `DEVELOPMENT_TASKS.md`de TEK
kaynak olarak tutulur, burada TEKRARLANMAZ — `DEV-040`'ın `scripts/
architect/CLAUDE.md`ye yaptığı atıfla AYNI disiplin). Hiçbiri `READY`
değildir: her madde yalnızca kullanıcının mini-detay talimatıyla açılır.
Sekiz maddenin seansında çıkan mini düzeltmeler `DEV-057`de (en sonda,
kümülatif) toplanır.

## Şaft / havalandırma / baca boşlukları modülü (kullanıcı fikri, 2026-10-05)

`DEV-052` sırasında: WC ve banyo arasındaki duvardan kare (karesel) bir şaft
boşluğu planlanacak; sistemde şaft, havalandırma boşluğu ve belki baca boşluğu
olacağı için bunlar AYRI bir modülde (kendi `CLAUDE.md`'si, `collision`
ayak izi veya gerekçeli muafiyet) incelenebilir. Henüz göreve ALINMADI;
BAĞIMSIZ yeni geliştirme fikridir (kullanıcı kararı 2026-10-05: DEV-057'den
çıkarıldı); tamamlanınca şaft genişliği, ıslak hacim kapı mesafesi eşiğini
(`check_wet_area_door_proximity`, 5000 mm) belirler. Veri proje bazlıdır (`context.json`), kütüphane
(şaft tipleri/asgari ölçüler) modül altında yaşar.

## Etüt: daire içi oda bölüntüsü (kullanıcı fikri, 2026-10-05)

`DEV-056` yalnız ZONLAMA (daire sınırları) yapar. Her dairenin içindeki oda
bölüntüsü (salon/yatak/mutfak/banyo/WC yerleşimi, hol topolojisi seçimi,
kapılar) AYRI bir geliştirme fikridir: kullanıcı detaylı bir etüt çalışması
görmek isterse o çıktı üretilecek. Girdi `DEV-056` bölgeleri +
`DEV-054` hol topolojisi + `DEV-049…053` kuralları; çıktı yine "hesapla, puanla,
seç" deseninde aday listesidir. Henüz göreve ALINMADI.

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
