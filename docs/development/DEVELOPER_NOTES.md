# Geliştirici Notları

Bu dosya bir sonraki geliştiricinin ilk okuyacağı canlı çalışma notudur. Her
çalışma sonunda mevcut durum, ilk ucuz kontrol, açık kararlar ve sonraki
sistem mimarı direktifi güncellenir.

## Mevcut durum

- `pafta/`, `walls/` ve `axis/` tamamlandı.
- `AxisGrid` generator'dan `scripts/axis/` içine taşındı.
- Faz dosyaları kalıcı çalışma kaydı olarak kullanılmaz; tamamlanan işler
  `DEVELOPMENT_HISTORY.md`ye eklenir.
- Proje örneğinin 1:100 mevzuat uyarısı rev-8'de giderildi (ölçek 1:50);
  geçmiş HD kayıtlarındaki 1:100 notları tarihsel bağlamdır.
- Görev eşzamanlılığına karşı `development_control.py` atomik kilidi eklendi;
  aynı anda iki agent görev alamaz.
- Golden semantic raporu ve provenance şablonu eklendi; byte hash tek başına
  kabul ölçütü değildir.
- `openings/`, `rooms/` ve `dimensions/` modülleri generator akışına entegre
  edildi; pipeline ve semantic golden kontrolü başarılı.
- Proje `1:50` mevzuat ölçeğine geçirildi; `classify_violation(...)` artık
  uyarı üretmiyor ve en yüksek pafta (67.0 cm) 90'lık rulonun 88 cm net
  yüksekliğine sığıyor.
- `pafta::CoverBlock` eklendi: kapak paftası ÖZEL paftadır — kapak bloğu
  paftanın iç çizgisinin sağ-alt köşesine sabitlenir (katlandığında üste
  gelsin diye), pafta genişliği kapak genişliğine eşitlenir, bu paftada
  Tip-B antet çizilmez (`Sheet.draw(..., title_box=False)`) ve kapak
  çerçevesi her kenardan eşit offsetlidir. Blok, çıktı hangi ölçekte
  alınırsa alınsın kağıtta tam A4 basar (4 ölçekte doğrulandı).
  `meta.cover` (opsiyonel `architect_name`, `date`, `signature_fields`)
  schema'ya eklendi; verilmeyen resmi alanlar uydurulmaz, doldurma çizgisi
  olarak bırakılır.
- `scripts/preview.py` artık kapak paftasını da (aynı sırada ve aynı A4
  ölçüsünde) çiziyor; önizleme pafta sırası DXF ile birebir.
- Mahal adları ve `area_m2` mevcut `RoomLabeler` ile çizilmeye devam ediyor;
  yapısının geliştirilmesi `DEV-008` olarak planlandı (kullanıcı talebi).

## Sıradaki iş

`DEVELOPMENT_TASKS.md` artık **her modül için ayrı plan maddesi** tutuyor
(`DEV-007` … `DEV-017`) ve her maddede seçilmek üzere **iki fikir** var.

rev-9 durumu:

- `DEV-008` **COMPLETED** — 3 satırlı mahal etiketi + `typography` modülü
  (bkz. `HD-005`).
- `DEV-007` **BLOCKED** — çizim tarafında iş kalmadı; yalnızca kullanıcıdan
  gelecek mimar adı / tarih / unvan bekleniyor.
- `DEV-006` **READY** — amacı rev-9'da genişletildi (bugünkü golden raporunun
  neden zayıf olduğu açıkça yazıldı).
- `DEV-009` (tefriş) kullanıcı talebiyle açıldı, henüz başlatılmadı.

Sıradaki iş için sistem mimarı `DEV-006` veya `DEV-009`u açıkça
başlatmalıdır. Diğer modüller PLANNED olarak bekliyor. Sistem mimarı açıkça
başlatmadan kod değişikliği yapılmaz. Başlangıçta görev kilidi alınmalıdır.

## İlk okuma sırası

1. Bu dosya.
2. `DEVELOPMENT_TASKS.md`.
3. `DEVELOPMENT_HISTORY.md`.
4. `scripts/CLAUDE.md` ve ilgili modül sözleşmesi.
5. `scripts/generate_dxf.py`, schema ve mevcut golden output.
6. `docs/development/AGENT_PERMISSIONS.json` ve
   `PROVENANCE_TEMPLATE.json`.

## İlk ucuz kontrol

Openings değişikliğinden önce mevcut `WallNetwork` açıklık boşlukları ve
`DefaultPlanOpeningStyle` için mevcut DXF entity/layer davranışını çıkar.
Açıklık schema alanları mevcut `additionalProperties: false` sözleşmesiyle
uyumlu değilse uygulamayı durdur ve sistem mimarı kararı iste.

## Açık kararlar

- `host_wall_id` mevcut schema'ya nasıl ve ne zaman eklenecek?
- Opening position duvar başlangıcına göre mi, merkez noktasına göre mi
  tanımlanacak?
- Swing/menteşe bilgisi zorunlu mu, yoksa ayrı bir revizyon mu?
- Cephe açıklıkları plan opening stilini mi tüketir, ayrı bir stil mi kullanır?
- İlk golden-output otomasyonu hangi entity ve geometrik alanları kapsar?
- Reviewer raporu hangi ayrı çalışma çağrısında üretilecek?
- `meta.cover.architect_name` ve `meta.cover.date` değerleri ne olacak?
  (Kapak çizilir durumda; bu iki alan boş doldurma çizgisi olarak çıkıyor.)
- Ayrılmış iki imza alanının unvanı ne olacak?
- Kapakta ruhsat/onay alanları da gerekli mi?
- Kapak TASARIMI için kullanıcıdan ayrı bir talep bekleniyor (geometri
  sabit kalmalı: A4, sağ-alt sabit, eşit offset, antetsiz).
- Tefriş elemanları DXF `BLOCK` olarak mı tanımlanacak (`DEV-009`)?
- "Mahal ismi blok olarak işlensin" büyük harf olarak uygulandı; kullanıcı
  DXF `BLOCK` entity'si kastettiyse bu yeniden ele alınmalı.
- Mahal no bugün kat içinde sıralı (`01`, `02`…). Daire bazlı anlamlı bir
  numaralandırma (örn. A dairesi 01-09, B dairesi 10-19) istenirse yeniden
  numaralandırma gerekir.
- `context.json` programatik yazılırken mevcut biçim korunmalıdır (skaler
  dizi tek satır, nesne dizisi açılmış). Düz `json.dumps(indent=2)` dosyayı
  baştan biçimlendirip ~4000 satırlık sahte diff üretir.

## Çalışma kuralı

Aynı anda yalnızca bir geliştirme görevi `IN_PROGRESS` olabilir. Belirsizlikte
varsayım yapılmaz. Kod editinden hemen sonra focused validation; görev kabulünde
validate/generate ve golden-output raporu zorunludur.

## Sonraki direktif şablonu

Sistem mimarı bir sonraki çalışmada şu bilgileri vermelidir:

- Görev ID'si ve açık kapsam.
- İzin verilen dosya/dizinler.
- Schema/context değişikliğine izin var mı?
- DXF üretimine ve mevcut golden output üzerine yazmaya izin var mı?
- Kabul edilmesi gereken davranış ve beklenen validation.
