# daire-plani-ai — Proje Kuralları

Bu dosya, bu proje dizininde çalışırken her oturumda otomatik olarak okunacak
kalıcı kurallardır. Aşağıdaki kurallar istisnasız uygulanır.

## Kapsam
- Bu proje dışında hiçbir dizine okuma/yazma yapılmaz. Tüm işlemler
  `daire-plani-ai/` içinde kalır.

## DXF üretim disiplini
- `output/plan.dxf` **asla elle/serbestçe düzenlenmez veya elle yazılmaz**.
  Tek üretim yolu `scripts/generate_dxf.py` script'ini çalıştırmaktır.
- `context.json` içinde veya kullanıcının verdiği bilgide bulunmayan hiçbir
  ölçü, koordinat veya değer **uydurulmaz**. Eksik bilgi varsa varsayım
  yapmak yerine kullanıcıya sorulur.

## Talep işleme akışı (her talep için sırasıyla)
1. Talep, geldiği ham haliyle `requests.jsonl` dosyasına JSON Lines formatında
   satır olarak eklenir: `{"rev": n, "ts": "...", "request": "..."}`.
2. Talep, `context.json` üzerinde yapılandırılmış bir değişiklik (patch)
   olarak uygulanır.
3. Değişiklik uygulandıktan sonra `scripts/validate.py` ile:
   - JSON Schema (`schema/design.schema.json`) doğrulaması,
   - geometrik sağlık kontrolleri (kapalı poligon mu, çakışan oda var mı,
     kapı/pencere genişliği ait olduğu duvardan büyük mü, alanlar toplamı
     mantıklı mı)
   yapılır. **Doğrulama geçmeden DXF üretilmez.**
4. Doğrulama başarılıysa `scripts/generate_dxf.py` çalıştırılıp
   `output/plan.dxf` sıfırdan yeniden üretilir.
5. İsteğe bağlı olarak `scripts/preview.py` ile `output/preview.png` üretilip
   kullanıcıya görsel önizleme sunulabilir.

## Git
- Git işlemleri (`init`, `add`, `commit`, `push` vb.) **sadece kullanıcı
  tarafından yapılır**. Asistan kendi başına hiçbir git komutu çalıştırmaz.
- Her revizyon sonunda kullanıcıya şu formatta bir commit mesajı önerilir:
  `rev-N: <özet>` — ama komut kendisi çalıştırılmaz, sadece önerilir.

## Belirsizlik durumunda
- Eksik/belirsiz bilgi varsa varsayım yapıp üretime devam etmek yerine
  kullanıcıya doğrudan soru sorulur.
