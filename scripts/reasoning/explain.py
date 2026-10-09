"""Aciklama motoru (DEV-064): bulgu -> kullaniciya anlatim; RAKAM LINT'I; sunum kuyrugu; diyalog kaydi.

Ilke ("bilgi bildirimseldir, hukum deterministiktir, anlatim dildir"): metin SABLONLARI rakam icermez;
rakam yalniz `{olcum:..}` (olculen), `{sabit:..}` (kaynakli esik/siddet) ve `{ad:..}` (eleman adi) yer-tutucusundan
gelir ve bunlar yalniz `Finding`/`Facet` verisinden doldurulur - bulunamazsa HATA verilir, deger uydurulmaz.
Lint SABLONU denetler; dil modelinin SERBEST metnini ise `verify_numbers` + `dialogue.jsonl` denetler (reviewer).

Saf Python; cizim modulu import etmez, dosya sistemine yalniz `append_dialogue/read_dialogue` dokunur.
"""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

from .findings import group_across_floors, severity_band
from .model import Facet, Finding, Remedy, Smell

# ---------------------------------------------------------------- sozlesme sabitleri
LEVELS = ("sade", "mimar")
MODES = ("sor", "devret")
MAX_TOPICS = 3
MAX_OPTIONS = 3
LEVEL_QUESTION = "Teknik ayrıntıyı sade tutayım mı, yoksa mimari terimlerle mi konuşalım?"
LEAVE_OPTION = "Olduğu gibi bırakmak (gerekçesiyle kaydedilir)."
NO_REMEDY_NOTE = "Bu konu için kayıtlı bir çözüm yolu yok; isterseniz birlikte seçenekleri çıkarırız."
DECISION_SOR = "Karar sizin. Olduğu gibi bırakmak da meşru; bunu gerekçesiyle kaydederiz."
DECISION_DEVRET = ("Kararı devrettiğiniz için önerilen seçeneği uyguluyorum; seçimi, bedelini ve reddedilen "
                   "seçenekleri uyguladıktan sonra size bildireceğim.")
SERIOUS_DEVRET_NOTE = "Bu bulgu ciddi olduğu için devir olsa bile önce sizin kararınızı alıyorum."
NOTHING_TO_APPLY_NOTE = "Uygulanabilecek kayıtlı bir çözüm olmadığı için devir geçersiz; kararı size bırakıyorum."
REOPEN_PREFIX = "Daha önce bilinçli olarak kabul etmiştiniz (gerekçeniz: “"
REOPEN_MID = "”); ölçüm değişti: "
REOPEN_SUFFIX = " Bu yüzden yeniden soruyorum."
REOPEN_BEFORE, REOPEN_NOW, REOPEN_GONE = "önce", "şimdi", "ölçülemedi"
UNSCORED_NOTE = "Bu konunun ne kadar ciddi olduğu ölçülemedi; önem sırası belirtilmiyor."
# kategori -> (ne goruyoruz, neden onemli): `legacy.<kategori>` bulgulari icin (bu uyarilar validate.py'de zaten kullaniciya gorunur)
CATEGORY_PLAIN = {
    "sartname": ("Bir mahalin ölçüsü ya da oranı genelde tercih edilen aralığın dışında kalıyor.",
                 "Kullanım rahatlığını etkileyebilir; bu bir yönetmelik hükmü olarak değil, genel tercih olarak sunuluyor."),
    "mimari": ("Daire içi yerleşim ilişkilerinde dikkat edilmesi gereken bir nokta var.",
               "Günlük kullanımda mahremiyeti ya da dolaşımı etkileyebilir; kesin bir hüküm değil, bir tercih notudur."),
    "merdiven": ("Merdivenle ilgili bir ölçü ya da yerleşim notu var.",
                 "Merdivenin kullanım rahatlığını ve güvenliğini etkileyebilir."),
}

PLACEHOLDER = re.compile(r"\{(ad|olcum|sabit):([a-z_][a-z0-9_]*)\}")
ANY_BRACE = re.compile(r"\{[^{}]*\}")
ENUM_RE = re.compile(r"(?m)^[ \t]*\d+\.[ \t]")          # numaralandirma istisnasi: satir basi "1. "
# harfe/alt cizgi/^ bitisik rakam birim ya da ad parcasidir (m2, uC_oda2, m^2), SAYI degildir
NUMBER_RE = re.compile(r"(?<![A-Za-z_^])\d+(?:[.,]\d+)?")


class ExplainError(ValueError):
    """Yer-tutucu verisi yok / gecersiz: deger UYDURULMAZ, anlatim uretilmez."""


# ---------------------------------------------------------------- rakam lint'i
def is_digit_char(ch: str) -> bool:
    """Unicode Nd/No/Nl (ornek: '٣', '²', 'Ⅳ') rakam sayilir; yalniz ASCII 0-9 degil."""
    return unicodedata.category(ch) in ("Nd", "No", "Nl")


def lint_template(text: str, allowed_numbers: tuple[str, ...] | frozenset = ()) -> list[str]:
    """Sablon HATALARI (bos liste = temiz): rakam, gecersiz yer-tutucu, `Plain.numbers` disi olcum yer-tutucusu."""
    errors: list[str] = []
    for m in ANY_BRACE.finditer(text):
        pm = PLACEHOLDER.fullmatch(m.group(0))
        if pm is None:
            errors.append(f"gecersiz yer-tutucu {m.group(0)!r} (siniflar: ad/olcum/sabit)")
        elif pm.group(1) == "olcum" and pm.group(2) not in allowed_numbers:
            errors.append(f"{m.group(0)!r}: olcum yer-tutucusu Plain.numbers icinde bildirilmemis")
    bare = ENUM_RE.sub("", ANY_BRACE.sub("", text))
    bad = sorted({c for c in bare if is_digit_char(c)})
    if bad:
        errors.append(f"sablonda rakam var: {''.join(bad)!r} (rakam yalniz yer-tutucudan gelir)")
    return errors


def _format_number(value) -> str:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ExplainError(f"sayi bekleniyordu: {value!r}")
    return str(int(round(value))) if abs(value - round(value)) < 1e-9 else f"{value:.1f}"


def number_tokens(text: str) -> set[str]:
    """Metindeki sayi belirteclerini normalize eder ('16,1' -> '16.1'); satir basi numaralandirma sayilmaz."""
    return {t.replace(",", ".") for t in NUMBER_RE.findall(ENUM_RE.sub("", text))}


def allowed_numbers_for(findings: list[Finding], facets: dict[str, Facet] | None = None,
                        decisions: list[dict] | None = None) -> set[str]:
    """Bir anlatimda KULLANILABILECEK sayilar: bulgu mesajlari + kanit degerleri + (varsa) veche esikleri."""
    out: set[str] = set()
    if decisions:
        from .decisions import decision_numbers
        out |= decision_numbers(decisions)
    for f in findings:
        out |= number_tokens(f.message)
        for v in f.evidence.values():
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                out.add(_format_number(v))
                out.add(f"{v:.1f}")
        facet = (facets or {}).get(f.facet_id)
        if facet is not None and facet.thresholds is not None:
            for t in (facet.thresholds.warn_at, facet.thresholds.severe_at):
                if t is not None:
                    out.add(_format_number(t))
        if f.severity is not None:
            out.add(_format_number(round(f.severity, 1)))
    return out


def verify_numbers(text: str, allowed: set[str] | frozenset) -> list[str]:
    """Metindeki KAYNAKSIZ sayilar (bos liste = temiz). Dil modelinin serbest anlatimi icin tek mekanik koruma."""
    return sorted(t for t in number_tokens(text) if t not in allowed)


# ---------------------------------------------------------------- sablon doldurma
def render(template: str, finding: Finding, facet: Facet | None = None) -> str:
    """Yer-tutucular yalniz `finding`/`facet` verisinden doldurulur; eksikse `ExplainError` (uydurma yok)."""
    def fill(m: re.Match) -> str:
        cls, key = m.group(1), m.group(2)
        if cls == "ad":
            em = re.fullmatch(r"eleman(\d*)", key)
            if em:
                idx = int(em.group(1) or 1) - 1
                if idx >= len(finding.elements):
                    raise ExplainError(f"{{ad:{key}}}: bulguda {idx + 1}. eleman yok")
                return finding.elements[idx]
            val = finding.evidence.get(key)
            if not isinstance(val, str):
                raise ExplainError(f"{{ad:{key}}}: kanitta ad yok")
            return val
        if cls == "olcum":
            if key not in finding.evidence:
                raise ExplainError(f"{{olcum:{key}}}: kanitta olcum yok")
            return _format_number(finding.evidence[key])
        # sabit: kaynakli esik ya da siddet
        if key == "siddet":
            if finding.severity is None:
                raise ExplainError("{sabit:siddet}: siddet olculmedi")
            return _format_number(round(finding.severity, 1))
        th = facet.thresholds if facet is not None else None
        val = getattr(th, key, None) if th is not None and key in ("warn_at", "severe_at") else None
        if val is None:
            raise ExplainError(f"{{sabit:{key}}}: veche esiginde yok")
        return _format_number(val)

    return PLACEHOLDER.sub(fill, template)


# ---------------------------------------------------------------- konu + sunum kuyrugu
@dataclass(frozen=True)
class Topic:
    key: str                      # kat-bagimsiz kimlik (Finding.group_key)
    findings: tuple[Finding, ...]
    facet_id: str
    severity: float | None
    side_effect: bool = False     # onceki durumda yoktu (yan etki)
    relevant: bool = False        # talebin dokundugu elemana bagli
    reopened: tuple = ()          # kabulu DUSEN kararlar (decisions.Reopened): 'once -> simdi' sayilari

    @property
    def floors(self) -> tuple[str, ...]:
        return tuple(sorted({f.floor_id for f in self.findings if f.floor_id}))

    @property
    def elements(self) -> tuple[str, ...]:
        return tuple(sorted({e for f in self.findings for e in f.elements}))


def is_presentable(finding: Finding, facets: dict[str, Facet]) -> bool:
    """Gorunurluk degismezi: yalniz `active` veche bulgusu ya da zaten validate.py'de kullaniciya gorunen
    `legacy.<kategori>` bulgusu sunulur. `shadow` bulgu ASLA sunulmaz."""
    facet = facets.get(finding.facet_id)
    if facet is not None:
        return facet.status == "active"
    # 'legacy.surum' sistem/proje surum notudur (mimari bir bulgu degil): konu olarak sunulmaz
    return finding.facet_id.startswith("legacy.") and finding.facet_id != "legacy.surum"


def select_topics(findings: list[Finding], facets: dict[str, Facet], before: list[Finding] | None = None,
                  intent_elements: tuple[str, ...] = (), limit: int = MAX_TOPICS,
                  decisions: list[dict] | None = None) -> tuple[list[Topic], list[Topic]]:
    """(ilk mesajdaki en cok `limit` konu, 'diger notlar'). Siralama: yan etki > niyetle ilgili > siddet (olculmeyen EN SONA)
    > ilk gorulme. Carpan/agirlik UYDURULMAZ (plan §4.1 formulu v1 taslaktir, `DEV-066` kalibre eder)."""
    from .decisions import evaluate  # gec iceri aktarim: decisions -> explain dongusunu onler
    before_keys = {f.group_key for f in (before or [])}
    verdict = evaluate(findings, decisions or [])
    topics: list[Topic] = []
    # kanita bagli kabul: kabul EDILMIS ve kaniti degismemis bulgu sunulmaz (yenilik = 0); kabulu dusen sunulur
    pool = [f for f in findings if is_presentable(f, facets) and verdict.get(f.key, ("",))[0] != "kabul"]
    for key, items in group_across_floors(pool):
        reopened, seen_ids = [], set()
        for f in items:
            v = verdict.get(f.key)
            if v and v[0] == "dustu" and v[1].decision_id not in seen_ids:
                seen_ids.add(v[1].decision_id)
                reopened.append(v[1])
        sevs = [f.severity for f in items if f.severity is not None]
        topics.append(Topic(key=key, findings=tuple(items), facet_id=items[0].facet_id,
                            severity=max(sevs) if sevs else None,
                            side_effect=before is not None and key not in before_keys,
                            relevant=any(e in intent_elements for f in items for e in f.elements),
                            reopened=tuple(reopened)))
    order = {t.key: i for i, t in enumerate(topics)}
    topics.sort(key=lambda t: (not (t.side_effect or bool(t.reopened)), not t.relevant, t.severity is None,
                               -(t.severity or 0.0), order[t.key]))
    return topics[:limit], topics[limit:]


def match_smells(topics: list[Topic], smells: dict[str, Smell]) -> list[tuple[Smell, list[Topic]]]:
    """Koku: bilesen vechelerden >=2'si SUNULAN konular arasinda VE bir eleman kimligini paylasiyorsa (tam eslesme)."""
    out = []
    for smell in smells.values():
        parts = [t for t in topics if t.facet_id in smell.facet_ids]
        if len({t.facet_id for t in parts}) >= 2:
            shared = set.intersection(*(set(t.elements) for t in parts)) if parts else set()
            if shared:
                out.append((smell, parts))
    return out


# ---------------------------------------------------------------- anlatim
@dataclass(frozen=True)
class Narrative:
    see: str
    why: str
    options: tuple[str, ...]
    recommendation: str
    decision: str
    mode: str
    level: str
    finding_keys: tuple[str, ...]
    notes: tuple[str, ...] = field(default_factory=tuple)

    def text(self) -> str:
        lines = [self.see, self.why, "", "Seçenekler:"]
        lines += [f"{i}. {o}" for i, o in enumerate(self.options, 1)]
        lines += ["", self.recommendation, self.decision]
        lines += [""] + list(self.notes) if self.notes else []
        return "\n".join(lines)


def effective_mode(requested: str, severity: float | None) -> str:
    """`devret` ciddi (>0.6) bulguda bile olsa SORAR. Siddeti olculmemis bulguda devir engellenmez ama NOT dusulur."""
    if requested not in MODES:
        raise ExplainError(f"mod gecersiz: {requested!r}")
    if requested == "devret" and severity_band(severity) == "ciddi":
        return "sor"
    return requested


def narrate(topic: Topic, facets: dict[str, Facet], remedies: dict[str, Remedy], *, level: str, mode: str = "sor") -> Narrative:
    if level not in LEVELS:
        raise ExplainError(f"seviye gecersiz: {level!r}")
    first = topic.findings[0]
    facet = facets.get(topic.facet_id)
    notes: list[str] = []
    if facet is not None and facet.plain is not None:
        see = render(facet.plain.problem, first, facet)
        why = render(facet.plain.consequence, first, facet)
        remedy_ids = list(facet.remedies)
    else:  # legacy.<kategori>: kategori cumlesi; olcum notu yalniz 'mimar' seviyesinde
        cat = topic.facet_id.split(".", 1)[1]
        see, why = CATEGORY_PLAIN.get(cat, CATEGORY_PLAIN["mimari"])
        if topic.elements:
            see += " İlgili yer: " + ", ".join(topic.elements) + "."
        remedy_ids = []
    if len(topic.floors) > 1:
        see += " Bu durum özdeş katların hepsinde aynı biçimde görülüyor."
    if level == "mimar":
        see += f" ({topic.facet_id}; ölçüm: {first.message})"
    for ro in topic.reopened:
        shown_changes = [f"{REOPEN_BEFORE} {_format_number(b)} → {REOPEN_NOW} "
                         f"{_format_number(a) if a is not None else REOPEN_GONE}" for _k, b, a in ro.changed]
        notes.insert(0, REOPEN_PREFIX + ro.reason + REOPEN_MID + "; ".join(shown_changes) + "." + REOPEN_SUFFIX)
    options = [remedies[r].text_tr for r in remedy_ids if r in remedies][:MAX_OPTIONS - 1]
    if not options:
        notes.append(NO_REMEDY_NOTE)
    options.append(LEAVE_OPTION)
    recommendation = (f"Önerim, ilk seçenek: {options[0]}" if len(options) > 1
                      else "Önerim: bu noktayı birlikte değerlendirmek.")
    eff = effective_mode(mode, topic.severity)
    if mode == "devret" and eff == "sor":
        notes.append(SERIOUS_DEVRET_NOTE)
    if eff == "devret" and len(options) == 1:  # yalniz 'birak' var: uygulanacak bir sey yok
        eff = "sor"
        notes.append(NOTHING_TO_APPLY_NOTE)
    if topic.severity is None:
        notes.append(UNSCORED_NOTE)
    decision = DECISION_DEVRET if eff == "devret" else DECISION_SOR
    return Narrative(see, why, tuple(options), recommendation, decision, eff, level,
                     tuple(f.key for f in topic.findings), tuple(notes))


def coverage_sentence(blocked: list[tuple[str, str]], unmeasured: list[str]) -> str:
    """Bakilamayan bakis acilarini ADIYLA soyler (blocked: [(baslik, neden)], unmeasured: [baslik])."""
    parts = []
    if blocked:
        parts.append("Şu bakış açılarına veri eksikliği yüzünden bakılamadı: "
                     + "; ".join(f"{t} ({why})" for t, why in blocked) + ".")
    if unmeasured:
        parts.append("Şu bakış açıları henüz ölçülmüyor (bu, 'sorun yok' demek değildir): " + "; ".join(unmeasured) + ".")
    return " ".join(parts)


# ---------------------------------------------------------------- diyalog kaydi (dialogue.jsonl, ekleme-yalniz)
RECORD_KEYS = ("rev", "ts", "context_sha256", "finding_keys", "text", "mode", "level")
_SHA_RE = re.compile(r"^[0-9a-f]{64}$")


def context_sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_record(rec: dict) -> list[str]:
    errors = [f"alan eksik: {k}" for k in RECORD_KEYS if k not in rec]
    if errors:
        return errors
    if not isinstance(rec["rev"], int) or isinstance(rec["rev"], bool) or rec["rev"] < 0:
        errors.append("rev negatif olmayan tamsayi olmali")
    if not _SHA_RE.match(str(rec["context_sha256"])):
        errors.append("context_sha256 64 haneli onaltilik olmali")
    if not isinstance(rec["finding_keys"], list) or not all(isinstance(k, str) for k in rec["finding_keys"]):
        errors.append("finding_keys metin listesi olmali")
    if not str(rec["text"]).strip():
        errors.append("text bos olamaz")
    if rec["mode"] not in MODES:
        errors.append(f"mode {MODES} icinde olmali")
    if rec["level"] not in LEVELS:
        errors.append(f"level {LEVELS} icinde olmali")
    return errors


def read_dialogue(path: Path) -> list[dict]:
    p = Path(path)
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]


def append_dialogue(path: Path, rec: dict, allowed: set[str] | frozenset | None = None) -> None:
    """Ekleme-yalniz: gecersiz kayit, geri giden `rev` ya da (allowed verildiyse) KAYNAKSIZ sayi iceren metin REDDEDILIR."""
    errors = validate_record(rec)
    if errors:
        raise ExplainError("; ".join(errors))
    existing = read_dialogue(path)
    if existing and rec["rev"] < existing[-1]["rev"]:
        raise ExplainError(f"rev geri gidemez (son kayit rev-{existing[-1]['rev']}, gelen rev-{rec['rev']})")
    if allowed is not None:
        bad = verify_numbers(rec["text"], allowed)
        if bad:
            raise ExplainError(f"metinde kaynaksiz sayi var: {bad} (sayi yalniz olcumden/kanittan gelir)")
    with Path(path).open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
