# typography modülü — DEV-008 ile kuruldu

Projedeki **yazı tipi** kararlarının tek sahibi. `pafta` modülü gibi kendi
klasöründe yaşar; `generate_dxf.py` yalnızca public API'yi import eder.

## Sorumluluk

| Bileşen | Görev |
|---------|-------|
| `TextStyles` | Rol → font eşlemesi, DXF text style kaydı |
| `DEFAULT_FONT_FILE` | Proje varsayılan fontu (`arialn.ttf` — Arial Narrow) |
| `style_name_for(font_file)` | Font dosya adından geçerli DXF stil adı |

## Nasıl çalışır — tek noktadan proje fontu

Proje geneli font, **`Standard` text style'ının fontu değiştirilerek**
uygulanır:

```python
doc.styles.get("Standard").dxf.font = "arialn.ttf"
```

Bu tek satır yeterlidir çünkü projedeki TÜM metinler (`pafta` anteti ve kapak
bloğu, `axis` baloncukları, cephe kat etiketleri, `generate_dxf` etiketleri)
`msp.add_text(...)`'i açıkça `style` vermeden çağırır ve `Standard`a düşer.
Ölçü metinleri de `dimstyle="Standard"` üzerinden aynı text style'ı kullanır
(doğrulandı). Yani yeni bir metin ekleyen kodun font için ekstra bir şey
yapmasına gerek yoktur.

Yalnızca **farklı** font isteyen bir rol için ayrı bir text style kaydedilir
ve o entity'ye `style` açıkça verilir (bugün: `room_label`).

## Roller

- `default` — proje geneli.
- `room_label` — mahal etiketi. Kullanıcı bu rolün ayrı seçilebilmesini
  açıkça istedi; `meta.fonts.room_label` verilmezse `default` ile aynıdır.

`context.json`:

```json
"meta": {
  "fonts": { "default": "arialn.ttf", "room_label": "arialn.ttf" }
}
```

`meta.fonts` opsiyoneldir; hiç verilmezse her iki rol de Arial Narrow olur.

## Public API

- `TextStyles.from_context(meta)` — `meta.fonts`'tan kurar.
- `TextStyles.ensure(doc)` — `ezdxf.new(...)` sonrası, **herhangi bir metin
  çizilmeden önce** çağrılmalıdır.
- `TextStyles.style_of(role)` — o rolün DXF text style adı (varsayılanla
  aynıysa `"Standard"`).
- `TextStyles.font_of(role)` — o rolün font dosyası; **metin sığdırma
  ölçümlerine bu verilmelidir.**

## Invariant'lar ve doğrulama

- **Font DOSYA adı verilir, aile adı değil.** ezdxf'te `"ArialNarrow"` sessizce
  Arial'e düşer ve ölçüm yanlış çıkar (`SALON` için `arialn.ttf` 388.3,
  `arial.ttf` 473.6 birim — ölçüldü). Bu sessiz bir hatadır, exception
  fırlatmaz.
- **Çizilen font ile ölçülen font aynı olmalıdır.** `pafta.fit_text_height`'e
  geçirilen font, entity'nin text style'ındaki fontla aynı değilse metin
  pafta dışına taşar veya gereksiz küçülür. `pafta.DEFAULT_FONT` bu yüzden bu
  modüldeki `DEFAULT_FONT_FILE`'dan import edilir — iki ayrı sabit tutulmaz.
- `ensure(doc)` metin çizilmeden önce çağrılmazsa stil kaydı eksik kalır.

## Sınır

Bu modül metin **çizmez**, yerleşim yapmaz ve yükseklik hesaplamaz. Metin
sığdırma `pafta.fit_text_height`'te, mahal etiketi düzeni `rooms`'ta kalır.
Burada yalnızca "hangi font, hangi stil adı" sorusu yanıtlanır.

## Bilinen sınırlamalar

- **Font alıcı bilgisayarda bulunmalıdır.** Arial Narrow bir TTF'tir; çizimi
  açan makinede `ARIALN.TTF` yoksa CAD programı başka bir fonta düşer ve
  metin genişlikleri kayar — bu durumda pafta taşma kontrolü üretim anında
  geçmiş olsa bile görsel taşma oluşabilir. SHX'e geri dönmek veya fontu
  proje ile birlikte dağıtmak ayrı bir karardır.
- Kalın/italik varyantlar (`ARIALNB.TTF` vb.) rol olarak tanımlanmadı; "blok"
  gösterim bugün **büyük harf** ile sağlanıyor, kalın font ile değil.
- Rol listesi (`ROLES`) kod seviyesindedir; yeni bir rol eklemek kod
  değişikliği gerektirir.
