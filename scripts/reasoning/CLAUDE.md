# reasoning modülü (mimari muhakeme çekirdeği) — DEV-060

Plan ve gerekçe: `docs/development/ARCHITECTURAL_REASONING_PLAN.md` (tek kaynak ilkesi: görev durumu
`DEVELOPMENT_TASKS.md`de). Bu modül **bilgi taşımaz**; bilgi (mercek, veçhe, koku) sonraki maddelerle
(`DEV-061`+) `reasoning/lenses/*.py` ve `<modül>/reasoning.py` dosyalarında yaşar. `collision/` ile AYNI
ters bağımlılık: çekirdek hiçbir çizim modülünü import etmez; sağlayıcı dosyalar DOSYA YOLUYLA yüklenir
ve yalnız `reasoning.*` (+ `__future__`, `dataclasses`, `typing`) import edebilir (AST ile denetlenir).
Import anında doğrulama/yan etki YOKTUR. Politika: yalnız UYARI (FORBID yok).

## Kullanıcı kararları (2026-10-09)
`scripts/reasoning/` adı; `validate.py` çıktısı DEĞİŞMEZ, rapor ek; kapı #10 üç durumlu; **veçhe kaydı lens
paketinde, ölçüm/kural sahibi modülde** (modül `reasoning.py`si yalnız rol + ölçüm beyanı); rapor komutu
`scripts/reasoning_report.py`.

## İçerik
| Dosya | Görev |
|---|---|
| `model.py` | `Provenance`, `Thresholds`, `Plain`, `CheckAdapter`, `Facet`, `Lens`, `Smell`, `Tension`, `Profile`, `Finding`; durum basamağı (`idea→draft→shadow→active`) zorunlu alanları |
| `registry.py` | `REASONING_PROVIDERS` / `REASONING_EXEMPT` / `REASONING_PENDING`, `Registry`, `validate_registry`, `load_registry` (dosya yoluyla, AST import denetimiyle) |
| `findings.py` | kararlı anahtar (`make_key`: rakamsızlaştırılmış mesaj özeti → kısmi çözüm anahtarı bozmaz), `severity_from_curve` (eğri yoksa **None/unscored**, sayı uydurulmaz), `diff_findings` (yeni/çözülen/değişmeyen), `group_across_floors` |
| `adapters.py` | `parse_validate_output`: `validate.py` stdout'u → `Finding` (**parite yapı gereği**; sınır: yalnız kategori bilinir, veçhe kimliği `legacy.<kategori>`) |
| `coverage.py` | `build_coverage` (`Facet.needs_note_tr` ile yol yerine duz dil neden: "yönelim değerlendirilemedi: kuzey yönü verilmedi"; ayni neden tek satırda kat listesiyle toplanır): **kostu / kosamadi (neden) / uygulanmaz**; kayıt boşsa bunu SÖYLER. `idea`/`draft` veçhe (ölçüm kodu yok) `kostu` SAYILMAZ, ayrıca **"henüz ölçülmeyen"** diye adıyla listelenir ("temiz" ≠ "bakılmadı"); `uygulanmaz` yalnız sayılır, `kosamadi` tek tek yazılır |
| `promotion.py` | `trigger_report`: tetik oranı, dejenere (hep/hiç ötmeyen) uyarısı, ölçülemeyen paydadan çıkar; **kapı değil rapor** |
| `cases.py` | vaka biçimi (`cases/<ad>/case.json` + `expected_findings.json`) ve koşucu; `golden/`den bilinçli ayrı |
| `explain.py` | **DEV-064** — açıklama motoru: şablon **rakam lint'i** (`lint_template`; 3 yer-tutucu sınıfı `{ad:..}` eleman adı / `{olcum:..}` ölçülen sayı (`Plain.numbers`te bildirilmiş) / `{sabit:..}` kaynaklı eşik–şiddet; rakam = Unicode Nd/No/Nl; satır başı "1. " numaralandırma istisnası), `render` (veri yoksa `ExplainError`, uydurma yok), `verify_numbers`, **sunum kuyruğu** (`select_topics`: yalnız `active` + zaten kullanıcıya görünen `legacy.*`; `shadow` ASLA; sıra: yan etki > niyetle ilgili > şiddet (ölçülmeyen en sona) > ilk görülme; çarpan UYDURULMAZ), `match_smells` (≥2 bileşen + ortak eleman), `narrate` (5 parça, ≤3 seçenek, `sor`/`devret`; ciddi ya da uygulanacak çözüm yokken devir geçersiz), `coverage_sentence`, `dialogue.jsonl` kaydı (`append_dialogue` ekleme-yalnız, kaynaksız sayıyı reddeder) |
| `decisions.py` | **DEV-065** — tasarım kararı kaydı (saf fonksiyonlar, dosya yazmaz): `evidence_snapshot` (ölçülen sayılar: `Finding.evidence` + mesajdaki sayılar `m1..`), `evidence_hash`, `make_decision` (boş gerekçe REDDEDİLİR), `check_decisions` (validate.py HATASI), `evaluate` (**kabul** / **düştü** + "önce → şimdi"; aynı bulguyu kapsayan SON kayıt geçerli), `decision_numbers`. Yazım yalnız `reasoning_dialogue.py decide` ile |
| `lenses/isik_hava_yonelim.py` | **DEV-062 — ikinci mercek paketi** (bilgi mühendisi protokolüyle yazıldı): 5 veçhe — 4 `shadow` (yaşam mahalli penceresi, çapraz havalandırma, ıslak hacim havalandırması, salon yönelimi [`meta.north_angle` ister]) + 1 `draft` (pencere/taban oranı: `openings[].height` ister). `active` YOK. Ölçüm sahipleri: `openings/daylight.py`, `shafts/ventilation.py` (+ `spatial` cephe sorguları); sağlayıcılar `openings/reasoning.py`, `shafts/reasoning.py` |
| `lenses/mahremiyet.py` | **DEV-061 — ilk mercek paketi** (bilgi burada: 14 veçhe, 3 koku, mercek metni); yalnız `reasoning.*` import eder, `register(reg)` ile yüklenir. Ölçüm/kural sahibi: `architect/rules.py` + `architect/privacy.py`; `architect/reasoning.py` yalnız ROL + ölçüm beyanıdır |
| `cases/` | **30 vaka** (15 veçhe × ihlal+temiz; son 8'i DEV-062): ELLE yazılmış, uydurulmuş mini sahneler (`origin` alanı bunu söyler; gerçek geçmiş geometri değil — kullanıcı kararı) |

## Mekanik kapılar (`doc_check.py`)
**#10** her paket tam BİR yerde (sağlayıcı / gerekçeli muaf / PENDING); PENDING **donuk** (`_PENDING_FROZEN`)
ve yalnız küçülür, `DEV-067` boşaltınca kapı bloklayıcı kalır; **#11** `status ≥ shadow` veçhenin
`adapter/measure/check` başvuruları AST ile çözülür (adapter.inputs parametre adlarıyla örtüşür); **#12**
`status ≥ shadow` veçhe için `ihlal` + `temiz` vaka diskte (**`legacy` veçhe muaf**: `validate.py`nin zaten çağırdığı kural terfi kapısından geçmez, `model.Facet.legacy` belgesi; vakaları yine de var ve selftest'te koşar); **#14** kaynaksız `kesin` yasak; **#15**
bayat `provenance.reviewed` BİLGİ satırı (`run_info`, çıkış kodunu etkilemez; `REVIEW_MAX_AGE_DAYS` bir
politika parametresidir, onay bekler). **#13** (DEV-064) anlatım metinlerinin (veçhe başlık/ilke/neden/plain, çözüm, koku, `explain.py` sabit cümleleri) rakamsızlığı — rakam yalnız yer-tutucudan gelir. **Üretim kaydı artık DOLU**
(`mahremiyet` 14 + `isik_hava_yonelim` 5 veçhe): #11/#12/#14 gerçek kayıtta gerçekten koşar; yine de kapılar selftest'te enjekte edilen
bozuk sahte kayıtlarla da sınanır (her kapı için kasıtlı bozma + yanlış-pozitif).

## Rapor komutu
`python scripts/reasoning_report.py [context.json] [--before onceki.json]`: kapsam + uyarıları kat-bağımsız
tek konuya indirger (rev-28: **15 satır → 3 konu**); `--before` ile yeni/çözülen/değişmeyen. Her zaman
çıkış 0 (tavsiye), `validate.py` BAŞARISIZsa bunu yazar. **DEV-061:** ek olarak **"Gölge veçheler"** bölümü
(`status=shadow` veçhelerin bulguları; kullanıcıya SUNULMAZ, `validate.py` çıktısına GİRMEZ) ve **asgari tetik
oranı** (`measure_ref` taşıyan veçheler: özne tekilleştirilir, katlar birleşir; rev-28: giriş→yatak odası 2/3,
komşu giriş 2/3, ıslak ortak duvar 5/6, sandviç banyo 0/6 = dejenere/bilgi taşımıyor). Adaptör→çağrılabilir
köprüsü (`facet_check`) çekirdekte değil bu betiktedir (çekirdek çizim modülü import etmez).

## Diyalog köprüsü (`scripts/reasoning_dialogue.py`, DEV-064/065)
`guide` (sözleşme metni; operatör `docs/`ı okuyamaz), `decide --key ... --reason` (karar kaydı; `context.json`a EKLEME, mevcut biçim korunur), `brief --level sade|mimar [--mode] [--before] [--intent]` (seviye
verilmezse çıkış 3 + soru), `append` (`<proje>/dialogue.jsonl`, kaynaksız sayıda çıkış 1 ve YAZILMAZ), `verify` (reviewer;
`context_sha256` eşleşmeyen kayıt "doğrulanamadı" diye raporlanır). Bulgular `validate.py` stdout'undan okunur
(`validate.py` değişmez); köprü çekirdek DIŞINDADIR. rev-28: 15 satır → 3 konu → ilk mesajda 3 konu.

## Tasarım kararı kaydı (DEV-065, şema 1.4.0)
`context.json` üst seviye **opt-in** `design_decisions[]`: `id`, `rev`, `ts`, `reason` (zorunlu), `covers[]` (her biri `finding_key` +
`evidence_hash` + `evidence` anlık görüntüsü; özdeş katlar için kat başına bir öge, TEK karar N bulguyu kapsar), `devredilmis`, `supersedes`.
**Kanıta bağlı kabul (v1):** ölçülen sayılar HERHANGİ bir biçimde değişirse (kötüleşme de iyileşme de) kabul düşer, bulgu yeniden
sunulur ve ilk sıraya girer (yan etki gibi); anlatım "önce → şimdi" der. Kaniti aynı kabul sessizdir ama brief "N bulgu gerekçesiyle
kabul edilmiş" diye SAYIYI söyler (sessiz geçme yok). Bulgu anahtarı mesaj TÜRÜ değişince değişir: kabul sessizce değil bulgu yeniden
görünerek düşer (güvenli yön). `validate.py` yalnız `check_decisions` HATALARINI ekler (boş gerekçe, yinelenen kimlik, boş `covers`,
bozuk hash, olmayan `supersedes`); bulgunun kendisi UYARI kalır. Ekleme-yalnızlık KONVANSİYONDUR (denetim: reviewer git diff);
yeni karar eskiyi `supersedes` ile ezer. **Şema MINOR 1.3.0 → 1.4.0:** alanı taşımayan projede `validate` bir `UYARI (surum)` satırı
ekler (15 → 16 satır; konu sayısı etkilenmez: `legacy.surum` sunulmaz). Gerçek projenin `meta.schema_version` değeri henüz 1.3.0
(güncellemek ayrı bir proje revizyonudur, kullanıcı kararı).

## Çakışma denetimi: EXEMPT
`collision/scene.py::COLLISION_EXEMPT` içinde (geometri/ayak izi üretmez).

## Doğrulama
`python scripts/reasoning/selftest.py` — 30 kontrol (DEV-065: karar çekirdeği, şema+validate, düşen kabulün sunumu, `decide` uçtan uca; 14 çekirdek + 5 mahremiyet paketi + 7 DEV-064: lint/render, §5.6 örneği, kuyruk+modlar, koku+kapsam cümlesi, diyalog kaydı, kapı #13, CLI uçtan uca; 6 kasıtlı bozma ilgili testleri kırdı; mahremiyet: durum dağılımı, `validate.py` bağlama iddiasının koddan sabitlenmesi, 22 vaka + kasıtlı bozma, rev-28 ölçümleri, rapor); elle hesaplanan anahtar/eğri değerleri; üretim koduna
kasıtlı bozma (imzada rakam, kapı #10 çoklu-yer, kapsam durumu karışması) selftest'i GERÇEKTEN kırar.

## Işık-hava-yönelim paketi (DEV-062) — notlar
Kullanıcı kararları: yaşam mahalli (salon + yatak odası) ve ıslak hacim (WC + banyo) kümeleri **lens-yerel sabit** ('yaygın'; `standards/` değişmedi, mutfak ayrı kayıt ve değerlendirilmez);
`tesisat`/`havalandirma` şaftı ıslak hacim havalandırması sayılır (≥ 300 mm ortak kenar, `check_shafts` ile aynı tanım; `baca` sayılmaz); cephe = prob noktası, çapraz havalandırma =
≥ 2 farklı dış normal yönünde pencere; pencere yüksekliği opsiyonel `openings[].height` (şema 1.4.0, additif; katalog varsayılanıyla UYDURMA YOK). **Yön uydurulmaz:** `meta.north_angle`
yoksa `salon_kuzeye_bakiyor` KOSAMAZ ve bunu söyler; verilince koşar (`reasoning_report.facet_check` girdiyi katta bulamazsa `meta`da arar). rev-28: penceresiz yaşam mahalli 0/8, çapraz
havalandırma yetersiz birim 0/3, havalandırmasız ıslak hacim 0/6 — hepsi dejenere (bilgi taşımıyor; vaka kanıtı sentetik). Salon yönelimi için eşik (kuzey yarısı = kuzeyden 90°'den az sapma)
'tercih', kaynaksızdır. Çapraz-mercek gerilimi (ışık ↔ mahremiyet) karşı veçhe kayıtlı olmadığı için yazılmadı.

## Bilgi mühendisi
Mercek/veçhe/vaka ekleme kuralları, izin sınırı ve terfi merdiveni: `docs/agents/KNOWLEDGE_ENGINEER_AGENT.md` (DEV-070). Çekirdeği (bu klasördeki `*.py`) bilgi mühendisi DEĞİŞTİRMEZ.

## Muhakeme katkısı (DEV-048)
**Rol:** çekirdek + ilk mercek paketi (`lenses/mahremiyet.py`, DEV-061). Bilinen boşluk: açıklama motoru, rakam lint'i,
sunum kuyruğu (`DEV-064`); ışık-hava (`DEV-062`) ve yaşanabilirlik (`DEV-063`) paketleri. Rapor, kullanıcıya sunulan
uyarıları hâlâ `validate.py` stdout'undan `legacy.<kategori>` olarak okur; kayıtlı beş `legacy` veçhe kapsamda ve
kayıtta görünür ama sunum yolunu DEĞİŞTİRMEZ (bu `DEV-064`/`066`nın işi).

## Bilinen sınırlamalar
- `legacy.*` bulgularda siddet `None` (unscored): kuyruk bunları şiddeti ölçülmüşlerin ARKASINA koyar ve "ne kadar ciddi olduğu ölçülemedi" der; kalibrasyon `DEV-066`. Kategori cümleleri genel (`CATEGORY_PLAIN`): fonksiyon düzeyi anlatım için legacy kuralların `active` `plain`ine geçişi gerekir.
- Anlatım yalnız bulgu mesajından ve veçhe verisinden beslenir; `Finding.evidence` bugün `legacy`/`adapt_warnings` bulgularında BOŞ — `{olcum:..}` yer-tutucusu olan bir veçhe, ölçümü `evidence`a koyan bir ölçümle (DEV-062/063) gelmelidir. `mimar` seviyesi ölçümü ham mesajdan alıntılar.
- `validate.py` HATA kanalındaki kontroller (örn. `check_room_types`, `check_shafts[0]`) adaptörün kapsamı DIŞINDADIR.
- Kapsam raporu boş kayıtta yalnız "hiçbir mercek kayıtlı değil" der.
- Mahremiyet paketinde: çapraz-mercek gerilimleri (`mahremiyet` ↔ kompakt ıslak çekirdek / çapraz havalandırma / ışık)
  KAYDEDİLMEDİ — karşı veçhe başka paketlerde (`DEV-062`/`063`) kayda girince eklenecek (olmayan veçheye gerilim yazılamaz).
- `kademelenme.derinlik` ve `isitsel.islak_ortak_duvar_birimler_arasi` `draft`, `gecis.misafir_yolu` `idea` (plan §11 #9):
  ölçüm kodu yok, `kostu` sayılmaz. Duvar türü ayırıcısı yok (gerçek projede duvar türü verisi yok).
- Vakalar sentetiktir; `sandvic_banyo` bileşen veçhesi gerçek rev-28'de hiç tetiklenmez (0/6), kanıtı yalnız sentetik vakadır.
