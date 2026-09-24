# sections modülü (bina kesiti) — DEV-021 tamamlandı

Bina kesiti (building section): düşey kat istifini `elevations/`den ödünç
alır, `floors[]`in duvarlarını kesit hattı boyunca tarayıp **kesilen duvar
kalınlığını** ve **kat sınırlarını** çizer, ayrıca plan paftalarına kesit
hattı + bakış yönü işaretini basar. `axis`/`elevations`/`walls` ile aynı
"her çizim konusu kendi modülü" desenidir (bkz. kök `CLAUDE.md`).

## Sorumluluk

| Sınıf/fonksiyon | Görev |
|---|---|
| `SectionCutLine` | Bir kesidin çözülmüş verisi (id/label/axis_source/position/look_direction/levels_from) + `letter`/`width_for` yardımcıları |
| `resolve_sections` | `context['sections']` eksik alanlarını (label, position, levels_from, look_direction) **TEK yerde** doldurur; anahtar hiç yoksa X+Y varsayılan kesit üretir |
| `default_label` / `default_position` | Sırayla A-A/B-B/... ve "1/3 nokta" varsayılan kuralları |
| `crossing_walls` | Bir katın duvarlarından kesit hattını KESENLERİ bulur (elle hesaplanabilir) |
| `SectionFeatureHook` / `DefaultSectionFeatureHook` | Kat sınırı çizim GENİŞLETME NOKTASI (galeri boşluğu / merdiven kırılması) |
| `SectionSheet` | Tam kesit çizimi: aks izdüşümü + kat-kat kesilen duvar dolgusu + sınırlar + etiketler |
| `draw_cut_marker_on_floor` | PLAN paftasına kesit hattı + üçgen bakış-yönü işareti + harf |
| `section_vertical_extent` | Pafta Y-aralığı hesabı (`elevation_vertical_extent` ile aynı rol) |

## Kapsam kararı: kesit hattı HER ZAMAN aks ailesine paraleldir

Kullanıcı kararı (rev-17): *"bu yapılarda hiçbir zaman eğik kesit ya da
atlamalı kesit alınmaz. Bir kesit çizgisi X ve Y eksenindeki akslardan
birine paraleldir."* Bu yüzden `axis_source` alanı **`elevations/`deki
alanla birebir aynı anlamdadır**: `'vertical'` → kesit hattı sabit **Y**'de
(X boyunca uzanır, genişlik=`floor_width`, numerik/düşey akslar kesitte
görünür — `on_cephe` ile aynı izdüşüm). `'horizontal'` → sabit **X**'te
(genişlik=`floor_depth`, `sag_cephe` ile aynı izdüşüm). Bu eşdeğerlik
sayesinde `axis_grid.draw_on_elevation(msp, dx, cut.axis_source, y_bottom,
y_top)` **DOĞRUDAN yeniden kullanılır** — ayrı bir "kesit aksları" kavramı
icat edilmez.

## Varsayılan kesit üretimi (rev-17, kullanıcı kararı)

`context['sections']` **hiç verilmezse** (anahtar yok), sistem **X ve Y
ekseninden birer varsayılan kesit üretir** (`resolve_sections`) — bu
FABRİKASYON değildir, kullanıcının açıkça verdiği bir sistem standardıdır:
*"default ayarlarda X ve Y ekseninden birer kesit çizilir."* Boş dizi
(`[]`) verilirse bu varsayılan **devre dışı** kalır — operatör açıkça
"kesit yok" demiş olur.

**Varsayılan konum yapının TAM ORTASI DEĞİLDİR** (`DEFAULT_POSITION_
FRACTION = 1/3`): kullanıcı *"amacımız default olarak projenin tam
ortasından biraz sağ ya da solundan kesit almaktır"* dedi. Sistem bu
aralıkta **tek, deterministik** bir nokta seçer (1/3), tam merkezden değil
ama yine tek bir sabit kural olarak — "2. ya da 3. çizgi" ifadesindeki
serbestlik burada TEK bir seçime (2.) sabitlenmiştir; 3. (2/3 noktası) eşit
derecede uygun olurdu, gelecekte değişebilir.

## `levels_from`: kesit KENDİ dikey istifini UYDURMAZ

Bina **TEK** bir gerçek düşey kat istifine sahiptir; bu istif zaten
`elevations[].levels[]`de var. `levels_from` (verilmezse `elevations[0]`)
bu istifi **ödünç alır** — kesit için ayrı bir "kat yüksekliği" alanı
YOKTUR. **Kritik invariant:** `floors[]` listesinin uzunluğu, hedef
elevation'ın `levels[]` uzunluğuyla **birebir eşit** olmalı VE her ikisi de
**aynı sırada** (aşağıdan yukarıya) olmalıdır — kat↔seviye eşlemesi
SIRAYLA yapılır, id ile değil (`elevations/`in kendi "seviye sırası ÖNCE
gelmelidir" invariant'ıyla AYNI sınıf risk). Uzunluk uyuşmazlığı
`validate.py::check_sections` tarafından (yalnız kesit AÇIKÇA
bildirildiyse) HATA olarak yakalanır; `SectionSheet.draw` da savunma amaçlı
aynı kontrolü tekrar yapar (`ValueError`).

## `crossing_walls`: hangi duvarlar kesilir

Kesit hattı `axis_source='vertical'` ise (sabit Y), onu kesen duvarlar
**DÜŞEY** duvarlardır (`start.x == end.x`) ve Y-aralığı `cut_position`'ı
İÇERMELİDİR (uçlarda dahil, `EPS` toleransıyla). `axis_source='horizontal'`
simetriktir (YATAY duvarlar, X-aralığı). **Bilinen sınırlama:** kesit
hattına PARALEL duran bir duvar (aynı Y'de yatay bir duvar, `vertical` bir
kesitte) bu fonksiyon tarafından ATLANIR — bu yapıda duvarlar eksene hizalı
(rectilinear) olduğu için köşegen duvar hiç beklenmez, ama paralel-ve-aynı-
hatta-oturan duvar (nadir) da temsil edilemez.

## Genişletme noktası (kullanıcı talebi): galeri boşluğu / merdiven

Kullanıcı açıkça kesit alınırken *"kat yükseklikleri, galeri boşlukları ya
da merdivene denk gelen kısımlar olabilir"* dedi ve bu duyarlılığın
**zamanla güçlendirilebilir** olmasını istedi. Bugün bu senaryolar için
PROJE VERİSİ yoktur (`rooms[]`de "bu bir galeri/merdiven" diyen bir alan
henüz yok) — bu yüzden hiçbir şey UYDURULMAZ. Ama kod, bu genişlemenin TAM
OLARAK nereye gireceğini `SectionFeatureHook` Protocol'üyle (bkz.
`scripts/walls/standard.py::RailDrawingStandard` ile AYNI desen) hazır
tutar: `DefaultSectionFeatureHook.draw_level` bugünkü TEK davranışı (her
seviye altında düz sınır çizgisi) uygular; galeri/merdiven verisi
eklendiğinde YENİ bir `SectionFeatureHook` alt sınıfı yazılıp
`SectionSheet.draw(..., feature_hook=...)`e verilir — **çekirdek
`SectionSheet.draw` değişmez.**

## Plan işareti: kesit hattı + üçgen + harf (`draw_cut_marker_on_floor`)

Kullanıcı talebi: *"kesit çizgilerinin uçlarına ok işaretler (üçgenler)
eklenir ve üçgenlerin sırtına da kesitin harfi yazılır."* Uygulama:

- Kesit hattı bina kenarından **`PRINTED_MARKER_EXTENSION_MM` kadar dışarı
  taşan** bir "stub" ile çizilir (gerçek çizimlerde kesme düzlemi çizgisi
  binayı hafifçe aşar).
- Stub'un **dış ucunda** bir üçgen durur; tepe noktası **bina içine doğru**
  (bakış yönü, `look_direction`) işaret eder.
- Harf (`cut.letter`, `'A-A'` → `'A'`) üçgenin **SIRTINA** (tepe noktasının
  TERSİ yönde, dışarı bakan tarafa) yazılır.
- **HER kat paftasında** (aks ızgarasıyla aynı konumda, tüm katlarda ortak)
  çizilir — kesit tüm bina yüksekliğini kestiği için hangi katın "temsilci"
  olduğuna karar vermek gerekmez.
- **Farklı katman/renk/desen** (kullanıcı talebi): `KESIT` katmanı,
  `KESIT_HATTI` linetype'ı (dash-dot-dash), kırmızımsı RGB — `AKS`
  katmanının gri/kesikli görünümüyle KARIŞTIRILMAZ. `ensure_section_cut_
  layer` idempotent kurulum yapar (`axis`/`elevations`in kendi `DASHED`
  yükleme deseniyle AYNI yöntem, ama BAŞKA bir isim/renk).

## Pafta adı: kesit harfi (kullanıcı talebi)

*"Ayrı bir paftada kesitler gösterilir ve pafta ismine kesitin harfi
verilir (paftanın sağ altına)."* `generate_dxf.py`, her kesit için
`Sheet.draw(..., label=f"{cut.label} KESITI", ...)` çağırır — `"A-A
KESITI"`, `"B-B KESITI"` gibi, standart antedin sağ-alt köşesinde
görünür (bkz. kök `CLAUDE.md` "Pafta başlık kutusu").

## Bağımlılık yönü (tek yönlü, döngü yok)

`sections` → `elevations` (`LevelStack`, `Level`, `DIM_LAYER`,
`LABEL_LAYER`'ı import eder) ve `sections` → `pafta` (`to_modelspace`,
`parse_scale_denominator`). Bu, `rooms` → `pafta` ve `axis` → `dimensions`
ile AYNI, projede zaten kurulu tek-yönlü bağımlılık deseni — `elevations`
ve `pafta`, `sections`i BİLMEZ (döngü yok).

## Public API

```python
from sections import (
    SectionCutLine, SectionSheet, SectionFeatureHook, DefaultSectionFeatureHook,
    resolve_sections, crossing_walls, section_vertical_extent,
    draw_cut_marker_on_floor, ensure_section_cut_layer,
)

sections = resolve_sections(context)                       # context['sections'] eksikse varsayilan uretir
SectionSheet.draw(msp, cut, floors, elevation_lookup, dx, width, label_text_height, axis_grid)
draw_cut_marker_on_floor(msp, cut, dx, floor_width, floor_depth, scale, label_height)
```

`generate_dxf.py` ve `preview.py` (matematik/geometri için aynı fonksiyonlar,
çizim için kendi matplotlib rutini) bu modülü kullanır.

## Doğrulama

`python scripts/sections/selftest.py` — varsayılan konum/etiket kuralları,
`crossing_walls` elle hesaplanabilir + negatif test (ulaşmayan duvar VE
paralel duvar dışlanır), `SectionSheet.draw` varlık sayısı, kat/seviye
uzunluk uyumsuzluğunda `ValueError`, plan işareti varlık sayısı.

`validate.py::check_sections` — sadece AÇIKÇA bildirilmiş kesitler için:
`levels_from` geçerli mi, seviye/kat sayısı eşit mi, `position` bina sınırı
içinde mi. Varsayılan (örtük) kesitler kontrol edilMEZ (kullanıcı verisi
değil, sistemin kendi ürettiği ve doğruluğu garanti edilen veridir).

## Sınır

Bu modül `ezdxf` kullanır ama `context.json`'u değiştirmez; sadece okur ve
çizer. `axis_grid` parametresi `draw_on_elevation(msp, dx, axis_source,
y_bottom, y_top)` sözleşmesine sahip herhangi bir nesneyi kabul eder
(`axis` modülünü import ETMEZ, duck typing — `elevations` ile AYNI sınır).

## Bilinen sınırlamalar

- **Eğik/kademeli kesit YOK** (kullanıcı kararı, bkz. yukarısı) — kesit
  hattı her zaman eksene paraleldir.
- **Kesit hattına paralel duran duvar temsil edilemez** (bkz.
  `crossing_walls`).
- **Galeri boşluğu / merdiven kırılması HENÜZ veri olarak yok** — hazır
  genişletme noktası (`SectionFeatureHook`) var ama hiçbir proje bunu
  KULLANMIYOR (bkz. yukarısı).
- **Çakışma denetimine (`collision/`) girmez** — `COLLISION_EXEMPT`
  listesinde, `elevations` ile AYNI gerekçeyle (motor sadece `floors[]`
  düzleminde çalışır, kesit dikey bir izdüşümdür).
- **Seviye sırası doğrulanmaz** (sadece SAYI eşitliği) — `elevations/`in
  kendi "seviye sırası ÖNCE gelmelidir" bilinen sınırlamasıyla AYNI sınıf.
