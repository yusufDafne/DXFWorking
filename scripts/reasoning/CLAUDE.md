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
| `coverage.py` | `build_coverage`: **kostu / kosamadi (neden) / uygulanmaz**; kayıt boşsa bunu SÖYLER. `idea`/`draft` veçhe (ölçüm kodu yok) `kostu` SAYILMAZ, ayrıca **"henüz ölçülmeyen"** diye adıyla listelenir ("temiz" ≠ "bakılmadı"); `uygulanmaz` yalnız sayılır, `kosamadi` tek tek yazılır |
| `promotion.py` | `trigger_report`: tetik oranı, dejenere (hep/hiç ötmeyen) uyarısı, ölçülemeyen paydadan çıkar; **kapı değil rapor** |
| `cases.py` | vaka biçimi (`cases/<ad>/case.json` + `expected_findings.json`) ve koşucu; `golden/`den bilinçli ayrı |
| `lenses/mahremiyet.py` | **DEV-061 — ilk mercek paketi** (bilgi burada: 14 veçhe, 3 koku, mercek metni); yalnız `reasoning.*` import eder, `register(reg)` ile yüklenir. Ölçüm/kural sahibi: `architect/rules.py` + `architect/privacy.py`; `architect/reasoning.py` yalnız ROL + ölçüm beyanıdır |
| `cases/` | **22 vaka** (11 veçhe × ihlal+temiz): ELLE yazılmış, uydurulmuş mini sahneler (`origin` alanı bunu söyler; gerçek geçmiş geometri değil — kullanıcı kararı) |

## Mekanik kapılar (`doc_check.py`)
**#10** her paket tam BİR yerde (sağlayıcı / gerekçeli muaf / PENDING); PENDING **donuk** (`_PENDING_FROZEN`)
ve yalnız küçülür, `DEV-067` boşaltınca kapı bloklayıcı kalır; **#11** `status ≥ shadow` veçhenin
`adapter/measure/check` başvuruları AST ile çözülür (adapter.inputs parametre adlarıyla örtüşür); **#12**
`status ≥ shadow` veçhe için `ihlal` + `temiz` vaka diskte (**`legacy` veçhe muaf**: `validate.py`nin zaten çağırdığı kural terfi kapısından geçmez, `model.Facet.legacy` belgesi; vakaları yine de var ve selftest'te koşar); **#14** kaynaksız `kesin` yasak; **#15**
bayat `provenance.reviewed` BİLGİ satırı (`run_info`, çıkış kodunu etkilemez; `REVIEW_MAX_AGE_DAYS` bir
politika parametresidir, onay bekler). #13 (rakam lint'i) `DEV-064`tedir. **Üretim kaydı artık DOLU**
(`mahremiyet`, 14 veçhe): #11/#12/#14 gerçek kayıtta gerçekten koşar; yine de kapılar selftest'te enjekte edilen
bozuk sahte kayıtlarla da sınanır (her kapı için kasıtlı bozma + yanlış-pozitif).

## Rapor komutu
`python scripts/reasoning_report.py [context.json] [--before onceki.json]`: kapsam + uyarıları kat-bağımsız
tek konuya indirger (rev-28: **15 satır → 3 konu**); `--before` ile yeni/çözülen/değişmeyen. Her zaman
çıkış 0 (tavsiye), `validate.py` BAŞARISIZsa bunu yazar. **DEV-061:** ek olarak **"Gölge veçheler"** bölümü
(`status=shadow` veçhelerin bulguları; kullanıcıya SUNULMAZ, `validate.py` çıktısına GİRMEZ) ve **asgari tetik
oranı** (`measure_ref` taşıyan veçheler: özne tekilleştirilir, katlar birleşir; rev-28: giriş→yatak odası 2/3,
komşu giriş 2/3, ıslak ortak duvar 5/6, sandviç banyo 0/6 = dejenere/bilgi taşımıyor). Adaptör→çağrılabilir
köprüsü (`facet_check`) çekirdekte değil bu betiktedir (çekirdek çizim modülü import etmez).

## Çakışma denetimi: EXEMPT
`collision/scene.py::COLLISION_EXEMPT` içinde (geometri/ayak izi üretmez).

## Doğrulama
`python scripts/reasoning/selftest.py` — 19 kontrol (14 çekirdek + 5 mahremiyet paketi: durum dağılımı, `validate.py` bağlama iddiasının koddan sabitlenmesi, 22 vaka + kasıtlı bozma, rev-28 ölçümleri, rapor); elle hesaplanan anahtar/eğri değerleri; üretim koduna
kasıtlı bozma (imzada rakam, kapı #10 çoklu-yer, kapsam durumu karışması) selftest'i GERÇEKTEN kırar.

## Muhakeme katkısı (DEV-048)
**Rol:** çekirdek + ilk mercek paketi (`lenses/mahremiyet.py`, DEV-061). Bilinen boşluk: açıklama motoru, rakam lint'i,
sunum kuyruğu (`DEV-064`); ışık-hava (`DEV-062`) ve yaşanabilirlik (`DEV-063`) paketleri. Rapor, kullanıcıya sunulan
uyarıları hâlâ `validate.py` stdout'undan `legacy.<kategori>` olarak okur; kayıtlı beş `legacy` veçhe kapsamda ve
kayıtta görünür ama sunum yolunu DEĞİŞTİRMEZ (bu `DEV-064`/`066`nın işi).

## Bilinen sınırlamalar
- `legacy.*` bulgularda siddet `None` (unscored); sunum kuyruğunun bunları nasıl sıralayacağı `DEV-064`/`066`.
- `validate.py` HATA kanalındaki kontroller (örn. `check_room_types`, `check_shafts[0]`) adaptörün kapsamı DIŞINDADIR.
- Kapsam raporu boş kayıtta yalnız "hiçbir mercek kayıtlı değil" der.
- Mahremiyet paketinde: çapraz-mercek gerilimleri (`mahremiyet` ↔ kompakt ıslak çekirdek / çapraz havalandırma / ışık)
  KAYDEDİLMEDİ — karşı veçhe başka paketlerde (`DEV-062`/`063`) kayda girince eklenecek (olmayan veçheye gerilim yazılamaz).
- `kademelenme.derinlik` ve `isitsel.islak_ortak_duvar_birimler_arasi` `draft`, `gecis.misafir_yolu` `idea` (plan §11 #9):
  ölçüm kodu yok, `kostu` sayılmaz. Duvar türü ayırıcısı yok (gerçek projede duvar türü verisi yok).
- Vakalar sentetiktir; `sandvic_banyo` bileşen veçhesi gerçek rev-28'de hiç tetiklenmez (0/6), kanıtı yalnız sentetik vakadır.
