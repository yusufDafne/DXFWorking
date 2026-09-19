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

## Çıktı dosyası kilitliyse (ör. AutoCAD'de açık)
- `scripts/generate_dxf.py` ve `scripts/preview.py`, `output/plan.dxf` /
  `output/preview.png` dosyasına yazarken `PermissionError` alırsa (dosya
  başka bir programda açık olduğu için) **akışı durdurmaz**: bunun yerine
  `plan_1.dxf`, `plan_2.dxf` gibi `<isim>_N<uzantı>` şeklinde bir yedek
  dosyaya kaydeder ve bunu kullanıcıya açıkça bildirir.
- Bir sonraki çalıştırmada normal isim (`plan.dxf`/`preview.png`) tekrar
  yazılabilir olduğunda, script önce oraya kaydeder, ardından geçmişte
  oluşmuş `_N` ekli yedek dosyaları otomatik siler — dosya kalabalığı
  oluşmaz.

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

## Duvar çizim standardı (Türkiye standardı)
- Duvarlar AutoCAD'de **"tek merkez çizgisi + width (kalınlık) özniteliği"**
  yöntemiyle çizilmez — bu yöntem sektörde/Türkiye standartlarında
  kullanılmaz.
- Bunun yerine her duvar, kalınlığına karşılık gelen **iki paralel kenar
  çizgisi (rail)** ile temsil edilir; bu kenar çizgileri **LINE veya PLINE**
  (width=0, saf geometri) olarak çizilir.
- Duvar birleşim noktalarında (köşe veya T-kesişimi) bu kenar çizgileri,
  birleşen duvarların ilgili kenar çizgileriyle kesiştirilip (gönye/miter
  birleşim) o kesişim noktasına kadar uzatılır/kısaltılır. Sonuç: her dış
  köşe **dıştan tek bir noktada** temiz şekilde birleşir; çakışma veya boşluk
  oluşmaz.
- Uygulama: `scripts/generate_dxf.py` içinde bu mantık `Wall` ve
  `WallNetwork` sınıflarıyla kapsüllenir. Tüm duvar çizimleri bu sınıflardan
  türetilir/kullanılır — duvar çizen yeni kod tekilleştirilmiş bu sınıflar
  üzerinden yazılır, ayrı ayrı ad-hoc çizim mantığı eklenmez.

## Çok katli bina yapisi (rev-2'den itibaren)
- context.json semasi rev-2'de degisti: artik duz (tek daire) yapi degil,
  `meta.floor_width` / `meta.floor_depth` / `meta.sheet_gap` + `floors[]`
  (her biri kendi rooms/walls/openings/labels/counters/markings listesine
  sahip bir "pafta") + `elevations[]` (basitlestirilmis cephe seviye istifi)
  iceriyor. `schema/design.schema.json` bu yapiyi tanimlar.
- **Pafta duzeni:** `floors[]` sirayla, sonra `elevations[]` sirayla soldan
  saga dizilir; her paftanin X-ofseti kendi genisligi + `sheet_gap` kadar
  ilerler (bkz. `generate_dxf.py::generate`). Her paftanin sag-alt kosesine
  `CERCEVE` katmaninda bir cerceve ve METIN katmaninda kat adi + "PAFTA n/N"
  yazilir (`draw_sheet_frame`).
- **Ortak bina ayak izi:** Tum kat paftalari AYNI `floor_width x floor_depth`
  dikdortgenini kullanir (cikma yok). Derinlik iki banda ayrilir:
  - `y: 0 - 13000` "birim bandi": katin asil islevi (otopark / dukkan+lobi /
    3 daire / cati terasi) burada.
  - `y: 13000 - 17500` "sirkulasyon bandi": HER KATTA AYNI KONUMDA asansor
    (x:0-1000) + merdiven (x:1000-5000), bunlarin guney yuzu `y=14500`'de
    koridora acilir; L-seklinde koridor/rampa odasi tum genisligi kaplar.
    Bu konum tum katlarda sabit tutulmalidir (asansor/merdiven duseyde
    hizali olsun diye).
  - `y=13000` duvari ("band_south"): zemin/normal katlarda VAR (giris
    kapilariyla), bodrum/catida YOK (acik gecis - rampa/teras).
- **Mutfak tezgahi:** `floor.counters[]` icinde basit dikdortgen poligon
  olarak tanimlanir, `MOBILYA` katmaninda kapali polyline ciizilir.
- **Cephe gorunusleri (elevations):** Gercek plan geometrisinden TURETILMEZ;
  kullanicinin acikca izin verdigi sekilde (bkz. rev-2 talebi) semantik/basit
  bir seviye istifi + esit araliklarla yerlestirilmis jenerik pencere
  dikdortgenleri olarak cizilir (`draw_elevation`). `below_ground: true`
  seviyeler zemin cizgisinin (`y=0`) altinda cizilir; DXF'te ayri bir
  kesikli linetype UYGULANMAZ (sadece etiketle ayirt edilir) - bu bilinen
  bir basitlestirmedir.
- **Bilinen basitlestirmeler (rev-2):** Banyo/WC gibi servis odalari,
  "birim bandi"nin tam derinligini paylastigi icin gercekte olmasi
  gerekenden biraz dar-uzun orantili olabilir; otopark cizgileri
  (`markings[]`, `OTOPARK` katmani) salt gorsel/semantik olmayan
  isaretlemedir, validate.py bunlari kontrol etmez; asansor/merdiven kapi
  sembolu cizilmez (sadece etiketli kapali oda olarak gosterilir).

## Git (güncellendi)
1. Git komutları (`add`, `commit`, `log`, `diff`) SADECE bu proje dizini
   içinde çalıştırılır. Her git komutundan önce `git rev-parse
   --show-toplevel` ile bulunulan repo kökünün bu projenin dizini olduğu
   doğrulanır; eşleşmiyorsa işlem durdurulur ve kullanıcıya bildirilir. Bu
   dizin dışında hiçbir repoya dokunulmaz. Remote (`origin`) eklenmez veya
   `git push` yapılmaz — kullanıcı açıkça istemedikçe proje tamamen lokal
   kalır.
2. Bir revizyon işlendikten (context.json güncellenip validate + generate_dxf
   çalıştırıldıktan) SONRA, `git add`/`commit` yapmadan ÖNCE kullanıcıya
   şunlar gösterilip onay istenir:
   - Bu revizyonda context.json'da tam olarak neyin değiştiği (kısa özet)
   - Net bir soru: "Bu değişiklikleri commit'lemem için onaylıyor musun?"
   Kullanıcı açıkça onay vermeden (örn. "onaylıyorum", "evet", "commit'le")
   `git add` veya `git commit` çalıştırılmaz. Onay gelmeden başka bir talebe
   geçilmez.
3. Onay geldiğinde ilgili dosyalar (`context.json`, `output/plan.dxf`,
   `output/preview.png`, `requests.jsonl`) `git add` ile stage edilip
   commit'lenir. **Git config (local/global) hiçbir zaman değiştirilmez** —
   kullanıcı izin verse bile bu kural geçerlidir. Bunun yerine, `git log`'da
   yazar adının "Claude" görünmesi için her `git commit` komutu şu ortam
   değişkenleriyle çalıştırılır (sadece o komuta özel, kalıcı config
   değişikliği yapılmaz):
   `GIT_AUTHOR_NAME="Claude"`, `GIT_AUTHOR_EMAIL="noreply@anthropic.com"`,
   `GIT_COMMITTER_NAME="Claude"`, `GIT_COMMITTER_EMAIL="noreply@anthropic.com"`.
   Commit mesajı formatı sabittir (gelecekte `git log` ile geçmiş taranıp
   belirli bir revizyona hızlıca ulaşılabilsin diye):

   ```
   rev-<N> [<ISO 8601 tarih-saat>]: <tek satır kısa özet>

   Değişiklik: <hangi oda/duvar/kapı/pencere neyin değişti, somut şekilde>
   Kullanıcı talebi: <requests.jsonl'daki ilgili talebin kısa özeti>
   Etkilenen alanlar (context.json): <değişen key/path listesi, örn. rooms[2].area, walls[5]>
   ```

   `<N>` değeri `requests.jsonl`'daki revizyon sayacıyla birebir aynı olmalı.
4. Commit tamamlandığında kullanıcıya sadece commit hash'inin kısa hali ve
   tek satır özeti bildirilir, uzun log çıktısı gösterilmez.
5. **Git kimliği:** Bu proje için push işlemi (yalnızca kullanıcı açıkça
   isterse yapılır) `yusufakcakaya-sketch` hesabıyla yapılmalıdır — SSH host
   alias'ı `github-personal`, anahtar `~/.ssh/id_ed25519`. Bu makinedeki
   global git config şu an farklı bir kimlik kullanıyor (`YusufDafne` /
   `yusufakcakaya@dafneconstruction.com`, `~/.ssh/YusufDafne` anahtarı) —
   bu proje icin varsayilan olarak kullanilmamali. Global git config
   değiştirilmez; bir remote eklenmesi gerektiğinde kullanıcıyla birlikte
   `github-personal` host alias'ı üzerinden yapılandırılır.

## Belirsizlik durumunda
- Eksik/belirsiz bilgi varsa varsayım yapıp üretime devam etmek yerine
  kullanıcıya doğrudan soru sorulur.
