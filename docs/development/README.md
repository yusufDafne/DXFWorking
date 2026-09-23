# Sistem Geliştirme Yönetimi

Bu klasör sistemin generic geliştirme mantığının kalıcı çalışma alanıdır.
Faz dosyaları yerine görev, geçmiş, fikir ve geliştirici notları birlikte
kullanılır. Her yeni agent önce bu dosyayı ve `DEVELOPER_NOTES.md` dosyasını
okur.

## Dosyalar

- `DEVELOPMENT_TASKS.md`: Açık, devam eden, bekleyen ve tamamlanmaya hazır
  geliştirme görevleri.
- `DEVELOPMENT_HISTORY.md`: Tamamlanmış geliştirmelerin aktif geçmişi.
- `DEVELOPMENT_IDEAS.md`: Henüz göreve dönüşmemiş fikirler ve uzun vadeli
  seçenekler.
- `DEVELOPER_NOTES.md`: Bir sonraki geliştiriciye doğrudan çalışma bağlamı,
  açık kararlar, riskler ve önerilen ilk kontrol.
- `AGENT_PERMISSIONS.json`: Roller için izinli ve yasaklı okuma/yazma alanları.
- `PROVENANCE_TEMPLATE.json`: Proje revizyonu ve nihai DXF izlenebilirlik
  şablonu.
- `ACTIVE_TASK.lock`: Aynı anda ikinci agent görev almasını engelleyen geçici
  kilit; elle silinmez, sahibi tarafından serbest bırakılır.

## Görev yaşam döngüsü

`IDEA` → `PLANNED` → `READY` → `IN_PROGRESS` → `VALIDATION` → `COMPLETED`.

- `IDEA`: yalnızca fikir havuzundadır.
- `PLANNED`: kapsamı ve bağımlılığı tanımlanmıştır.
- `READY`: sistem mimarı uygulama direktifi verebilir.
- `IN_PROGRESS`: tek bir agent üzerinde çalışıyordur.
- `VALIDATION`: focused validation ve gerekirse validate/generate bekler.
- `COMPLETED`: kabul ölçütleri sağlanmış, geçmişe aktarılmıştır.

Bir görev tamamlanmadan `DEVELOPMENT_HISTORY.md`ye aktarılmaz. Tamamlanan iş
önce geçmişe eklenir, sonra görev kuyruğundan kaldırılır veya tamamlandı olarak
kısa referans bırakılır.

## 50 kayıt politikası

`DEVELOPMENT_HISTORY.md` en fazla 50 tamamlanmış geliştirme kaydı taşır. 51.
tamamlanmış geliştirme ekleneceği zaman en eski tamamlanmış kayıt silinir.
Silinecek kayıtlar yeniden başka proje dizinine yazılmaz ve aktif görevlere
karıştırılmaz. Git geçmişi teknik değişikliğin tarihsel kaydı olarak kalır ve
kritik belirsizlikte ayrıntılı incelenebilir; bu dosyanın amacı agent'ın güncel
geliştirme bağlamını sınırlı ve okunabilir tutmaktır.

Silme işlemi yalnızca tamamlanmış geçmiş kayıtlarına uygulanır. Açık görevler,
fikirler, geliştirici notları, proje verileri, provenance kayıtları, golden
DXF dosyaları ve kullanıcı talepleri silinmez.

## Yetki sınırı

Bu klasör sistem geliştirme kayıtlarını tutar. Proje context'i, requests,
validation raporu ve nihai DXF proje dizinlerinde tutulur. Project operator bu
klasöre yazamaz; system developer görev tamamlanma kaydını günceller.
Sistem mimarı açıkça sonlandırmadıkça roadmap, fikir ve teknik borç taraması
sürer.

## Eşzamanlı agent koruması

Normal çalışma modeli tek agent'tır; yine de olası eşzamanlı çalışmaya karşı
görev alınmadan önce şu komut çalıştırılır:

```text
python scripts/development_control.py claim DEV-001 --role system-developer --agent-id <benzersiz-id>
```

Kilit varsa ikinci agent çalışmaya başlamaz. İş bitince yalnızca kilit sahibi:

```text
python scripts/development_control.py release DEV-001 --agent-id <benzersiz-id>
```

komutunu çalıştırır. Kilit durumu `status` ile incelenebilir. Kilit dosyası
silinmiş veya bozuksa işlem durur; zorla üzerine yazılmaz.

## Bağımsız review ve kabul

Developer agent kodu ve dokümanı değiştirir; reviewer/validator ayrı bir
çalışma çağrısında yalnızca rapor alanına yazabilir. Reviewer kendi çıktısını
kabul edemez. Final kabulü sistem mimarı veya yetkili kullanıcı verir.

## Golden ve provenance

DXF değişikliklerinden sonra `python scripts/golden_report.py output/plan.dxf`
ile entity sayısı/türleri, layer dağılımı ve modelspace bounding box raporlanır.
Kabul edilen referans rapor `--write` ile saklanır ve sonraki üretim
`--compare` ile kontrol edilir. Her proje revizyonu
`PROVENANCE_TEMPLATE.json` alanlarını doldurur; byte hash'i tek başına kabul
ölçütü değildir.

## Her tamamlanma kaydının zorunlu alanları

- `id`, tarih ve kısa başlık
- değişen dosyalar/modül
- teknik sonuç
- validation/test sonucu
- golden-output etkisi
- açık risk veya bilinen sınırlama
- sonraki direktif
