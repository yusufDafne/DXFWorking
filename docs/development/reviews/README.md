# Reviewer sistem sınavı raporları (ekleme-yalnız)

Bu dizine yalnız reviewer ajanı rapor ekler (`AGENT_PERMISSIONS.json::review_validation.write`). Mevcut rapor DEĞİŞTİRİLMEZ ya da silinmez; düzeltme
yeni bir raporla yapılır. Her rapor şunu taşır: sınav kimliği (`DEV-071`), kullanılan **model kimliği**, sınanan belge **commit**'i, vaka başına 3 koşunun
rubrik sonuçları ve geçti/kaldı kararı. Kaldıysa bilgi eksiktir: belge düzeltilir, ajan suçlanmaz.
