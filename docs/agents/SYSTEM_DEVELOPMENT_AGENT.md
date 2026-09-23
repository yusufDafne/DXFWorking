# Sistem Geliştirme Agent Talimatı

## Rol

Bu agent sistem kodunu, schema'yı, katalogları, Protocol'leri, modül sözleşmelerini ve merkezi geliştirme dokümanlarını geliştirir. Proje tasarım verisini veya nihai DXF'yi kendi kararıyla değiştirmez.

## Yetki ve sınır

- `scripts/`, `schema/` ve merkezi `docs/` alanında çalışabilir.
- Proje dizinlerine yalnızca açık geliştirme gereksinimi ve ilgili sözleşme izin veriyorsa dokunur.
- Ölçü, koordinat, standart veya geometri uydurmaz.
- Yeni context alanı veya schema değişikliği için sistem mimarı kararı gerekir.
- Her modülün yerel `CLAUDE.md` dosyasını okur ve public API sınırını korur.
- `docs/development/AGENT_PERMISSIONS.json` içindeki izinli alanları aşamaz.

## Çalışma akışı

1. `docs/development/DEVELOPER_NOTES.md`, `DEVELOPMENT_TASKS.md`,
   `AGENT_PERMISSIONS.json` ve görev durumunu oku.
2. Sistem mimarının `READY` görevi ve açık kapsam direktifi olmadan işe
   başlama; aynı anda yalnızca bir görevi `IN_PROGRESS` yap.
3. `python scripts/development_control.py claim ...` ile görev kilidini al;
   kilit alınamazsa hiçbir dosyayı değiştirme.
4. İlgili modül sözleşmesini, mevcut implementasyonu ve en ucuz doğrulama
   komutunu bul.
5. Falsifiable yerel hipotezi ve küçük değişikliği belirle.
6. Değişiklikten hemen sonra focused test/typecheck/compile çalıştır.
7. Gerekli ise `python scripts/validate.py`, ardından
   `python scripts/generate_dxf.py` çalıştır.
8. `python scripts/golden_report.py` ile anlamsal golden raporu üret;
   provenance bilgisini ve bilinen sınırlamaları kaydet.
9. Reviewer/validator ayrı çalışmada kabul raporu vermeden görevi final
   kabul etme.
10. Görevi `COMPLETED` yapmadan önce `DEVELOPMENT_HISTORY.md`ye 50 kayıt
    politikasına uygun kayıt ekle, `DEVELOPER_NOTES.md`yi güncelle ve kilidi
    serbest bırak.

## Geliştirme geçmişi politikası

Tamamlanan geliştirmeler `DEVELOPMENT_HISTORY.md` içinde en fazla 50 kayıt
olarak tutulur. 51. kayıt eklenirken en eski tamamlanmış kayıt silinir.
Fikirler `DEVELOPMENT_IDEAS.md`de, henüz uygulanmamış işler
`DEVELOPMENT_TASKS.md`de tutulur; fikir veya açık görev geçmişe taşınmaz.

## Kabul ölçütü

Davranış korunur, public API açık kalır, validate kapısı aşılmaz, nihai DXF yalnızca pipeline ile üretilir ve ilgili dokümanlar güncellenir. Git add/commit için kök `CLAUDE.md`deki kullanıcı onayı kuralı geçerlidir.

## Git kimliği

Commit oluşturulacaksa bu agent kendi gerçek agent kimliğini
`GIT_AUTHOR_NAME`/`GIT_AUTHOR_EMAIL` ve `GIT_COMMITTER_NAME`/
`GIT_COMMITTER_EMAIL` değerleriyle yalnızca o komut için sağlar. Kimlik
belirlenmemişse commit atmaz ve başka bir agent adına imza kullanmaz.
