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
| `coverage.py` | `build_coverage`: **kostu / kosamadi (neden) / uygulanmaz**; kayıt boşsa bunu SÖYLER |
| `promotion.py` | `trigger_report`: tetik oranı, dejenere (hep/hiç ötmeyen) uyarısı, ölçülemeyen paydadan çıkar; **kapı değil rapor** |
| `cases.py` | vaka biçimi (`cases/<ad>/case.json` + `expected_findings.json`) ve koşucu; `golden/`den bilinçli ayrı |

## Mekanik kapılar (`doc_check.py`)
**#10** her paket tam BİR yerde (sağlayıcı / gerekçeli muaf / PENDING); PENDING **donuk** (`_PENDING_FROZEN`)
ve yalnız küçülür, `DEV-067` boşaltınca kapı bloklayıcı kalır; **#11** `status ≥ shadow` veçhenin
`adapter/measure/check` başvuruları AST ile çözülür (adapter.inputs parametre adlarıyla örtüşür); **#12**
`status ≥ shadow` veçhe için `ihlal` + `temiz` vaka diskte; **#14** kaynaksız `kesin` yasak; **#15**
bayat `provenance.reviewed` BİLGİ satırı (`run_info`, çıkış kodunu etkilemez; `REVIEW_MAX_AGE_DAYS` bir
politika parametresidir, onay bekler). #13 (rakam lint'i) `DEV-064`tedir. **Üretim kaydı bugün boştur:**
#11/#12/#14 gerçek kayıtta boş koşar ve bu KANIT DEĞİLDİR — kapılar selftest'te enjekte edilen bozuk sahte
kayıtlarla sınanır (her kapı için kasıtlı bozma + yanlış-pozitif).

## Rapor komutu
`python scripts/reasoning_report.py [context.json] [--before onceki.json]`: kapsam + uyarıları kat-bağımsız
tek konuya indirger (rev-28: **15 satır → 3 konu**); `--before` ile yeni/çözülen/değişmeyen. Her zaman
çıkış 0 (tavsiye), `validate.py` BAŞARISIZsa bunu yazar.

## Çakışma denetimi: EXEMPT
`collision/scene.py::COLLISION_EXEMPT` içinde (geometri/ayak izi üretmez).

## Doğrulama
`python scripts/reasoning/selftest.py` — 14 kontrol; elle hesaplanan anahtar/eğri değerleri; üretim koduna
kasıtlı bozma (imzada rakam, kapı #10 çoklu-yer, kapsam durumu karışması) selftest'i GERÇEKTEN kırar.

## Muhakeme katkısı (DEV-048)
**Rol:** çekirdek. Bilinen boşluk: açıklama motoru, rakam lint'i, sunum kuyruğu (`DEV-064`); mercek paketleri
(`DEV-061`+); `legacy.<kategori>` fonksiyon düzeyinde değil (adaptör `CheckAdapter` kaydıyla `DEV-061`de).

## Bilinen sınırlamalar
- `legacy.*` bulgularda siddet `None` (unscored); sunum kuyruğunun bunları nasıl sıralayacağı `DEV-064`/`066`.
- `validate.py` HATA kanalındaki kontroller (örn. `check_room_types`, `check_shafts[0]`) adaptörün kapsamı DIŞINDADIR.
- Kapsam raporu bugün boş kayıtta yalnız "hiçbir mercek kayıtlı değil" der.
