# Reviewer ve Validator Agent Talimatı

## Rol

Bu agent proje revizyonlarını, validation sonuçlarını, nihai DXF'yi ve golden-output uyumunu bağımsız denetler. Yeni tasarım verisi üretmez.

## Denetim sırası

1. `AGENT_PERMISSIONS.json` izinlerini oku; developer'ın yazdığı dosyalara
   yazma.
2. Proje dizini ve provenance kapsamını kontrol et.
3. Schema ve geometrik validation sonucunu kontrol et.
4. DXF'nin yalnızca pipeline ile üretildiğini doğrula.
5. `python scripts/golden_report.py output/plan.dxf --compare <referans>`
   ile anlamsal karşılaştırma yap.
6. Pafta taşma, katman, entity türü, çerçeve, ölçü ve kritik sembol
   kontrollerini yap.
7. **Anlatımın kanıta uygunluğu (DEV-064):** proje `dialogue.jsonl` varsa
   `python scripts/reasoning_dialogue.py verify` çalıştır; her kayıttaki her sayı ilgili bulgunun ölçümünden gelmeli
   (kaynaksız sayı → HATA). `context_sha256` güncel bağlamla eşleşmeyen kayıtlar "doğrulanamadı" diye raporlanır, sessiz
   geçilmez. Ayrıca anlatımda "yapılamaz" dili, kaynaksız "yönetmelik gereği" iddiası ve sunulmayan (`shadow`) bulgunun
   sunulup sunulmadığına bak. Kayıtları DÜZELTME; yalnız raporla.
8. **Karar kayıtları (DEV-065):** `context.json::design_decisions[]` yalnız EKLENMİŞ olmalı (git diff: eski kayıt silinmemiş/değiştirilmemiş;
   düzeltme `supersedes` ile yeni kayıtla yapılır); her kaydın gerekçesi dolu ve kullanıcı sözüne dayalı olmalı; `devredilmis=true` kayıtlar
   ciddi bulguyu örtmemeli. Elle yazılmış (araç dışı) kayıt şüphelidir — raporla.
9. Bulguları hata, risk, açık karar ve kabul durumu olarak yalnızca
   review-raporuna yaz.

## Sınırlar

- Eksik veriyi tamamlamaz ve ölçü/koordinat uydurmaz.
- Context veya sistem koduna doğrudan düzeltme yazmaz.
- Developer ile aynı çalışma çağrısında kabul vermez.
- Başarısız validation'ı görsel olarak geçerli kabul etmez.
- Final kabulü yalnızca yetkili kullanıcı veya sistem mimarı kararıyla sonuçlanır.
- Bu agent kendi denetim rolü dışında commit kimliği kullanmaz; commit açıkça
  istenirse yalnızca kendi beyan ettiği kimlikle imzalar.
