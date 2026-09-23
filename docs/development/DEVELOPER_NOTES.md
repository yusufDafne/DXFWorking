# Geliştirici Notları

Bu dosya bir sonraki geliştiricinin ilk okuyacağı canlı çalışma notudur. Her
çalışma sonunda mevcut durum, ilk ucuz kontrol, açık kararlar ve sonraki
sistem mimarı direktifi güncellenir.

## Mevcut durum

- `pafta/`, `walls/` ve `axis/` tamamlandı.
- `AxisGrid` generator'dan `scripts/axis/` içine taşındı.
- Faz dosyaları kalıcı çalışma kaydı olarak kullanılmaz; tamamlanan işler
  `DEVELOPMENT_HISTORY.md`ye eklenir.
- Proje örneğinin 1:100 mevzuat uyarısı tarihsel bir durumdur; sistem
  geliştirmesini bloke etmez.
- Görev eşzamanlılığına karşı `development_control.py` atomik kilidi eklendi;
  aynı anda iki agent görev alamaz.
- Golden semantic raporu ve provenance şablonu eklendi; byte hash tek başına
  kabul ölçütü değildir.
- `openings/`, `rooms/` ve `dimensions/` modülleri generator akışına entegre
  edildi; pipeline ve semantic golden kontrolü başarılı.

## Sıradaki iş

`DEV-006 — Golden fixture katalogu` görevi hazırdır. Sistem mimarı açıkça
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
