# import modülü — İleri faz

## Sorumluluk

`DxfWallScanner`, PDF/altlık okuma ve mevcut çizimden yapılandırılmış veri çıkarma araştırması.

## Faz planı

1. Kaynak formatlarını ve desteklenen entity/layer kapsamını açıkça listele.
2. `DxfWallScanner` ile güvenilir duvar adaylarını read-only raporla.
3. Belirsiz, eksik veya çakışan geometrileri confidence/uyarı olarak ayır;
   bunları context'e otomatik yazma.
4. İnsan/validator onaylı dönüşümü ayrı bir import patch formatında tanımla.
5. PDF/altlık desteğini DXF duvar okumasından sonra ve bağımsız provenance ile
   ele al.

## Public API adayı

- `DxfWallScanner.scan(source_path)`.
- `ImportReport.entities`, `warnings`, `candidates`, `source_provenance`.
- `ImportPatch.from_approved_report(report)`; yalnızca açık onaydan sonra
  context patch üretir.

## Invariant'lar ve doğrulama

- Kaynak dosya, sürüm ve hash provenance olarak korunur.
- Import sonucu doğrudan nihai DXF veya context değildir.
- Confidence düşükse akış durur ve karar istenir.
- Kaynak geometri ile üretilen aday geometri karşılaştırılabilir olmalıdır.

## Sınır

Import çıktısı otomatik olarak context'e veya nihai DXF'ye yazılmaz. İnsan/validator onayı ve açık dönüşüm sözleşmesi gerekir. Bu modül mevcut context semantiğini belirlemez.

## Kabul

Kaynak dosya provenance'ı korunur, belirsiz geometri raporlanır ve hiçbir tahmin doğrulanmış proje verisi gibi kabul edilmez.
