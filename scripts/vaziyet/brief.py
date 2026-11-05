"""Kullanici / dil modeli bilgi akisi (DEV-085): faz dallanmasi, Brief semasi, onay kapisi, ekleme-yalniz diyalog kaydi, secim patch'i.

Sinir (plan §5): dil modeli `Brief` alanlarini ONERIR, kullanici ONAYLAR; motor yalniz ONAYLI brief ile calisir. Model koordinat/cekme/TAKS-KAKS sayisi URETMEZ:
sayilar kullanicinin verdigi degerler ya da motor olcumudur; kaynaksiz sayi iceren metin REDDEDILIR. Secim patch'i context'e YAZILMAZ (normal revizyon akisi)."""
from __future__ import annotations

import copy
import datetime
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

try:
    from .parcel import VaziyetError
    from .setback import plan_north_angle
    from .study import DEFAULT_ALTERNATIVES, MAX_ALTERNATIVES, OBJECTIVES
    from .checks import check_site
except ImportError:
    from parcel import VaziyetError  # type: ignore
    from setback import plan_north_angle  # type: ignore
    from study import DEFAULT_ALTERNATIVES, MAX_ALTERNATIVES, OBJECTIVES  # type: ignore
    from checks import check_site  # type: ignore

PHASE_QUESTION = "Parsel/vaziyet planı sunmak ister misiniz?"
PHASE_SITE = "faz1_vaziyet"            # evet: bina-parsel yerlesimi (bu plan)
PHASE_UNITS = "faz2_kat_birim"         # hayir: kat/birim yerlesim alternatifleri (ayri plan; bu kod calismaz)
LOG_NAME = "site_dialogue.jsonl"
KINDS = ("phase", "brief_proposed", "brief_approved", "study", "selection")
PROPOSERS = ("dil_modeli", "kullanici")
NUMBER_RE = re.compile(r"(?<![A-Za-z_^])\d+(?:[.,]\d+)?")

# Izinli Brief alanlari (serbest metin YALNIZ `notes`; motora ASLA gecmez).
_NUM = (int, float)
BRIEF_FIELDS = ("n", "weights", "step_mm", "rotations_deg", "min_separation_mm", "front_setback_mm", "side_setback_mm", "rear_setback_mm", "taks", "kaks", "floors",
                "site_scale", "notes")


def _is_num(v) -> bool:
    return isinstance(v, _NUM) and not isinstance(v, bool)


def validate_brief(fields) -> list[str]:
    """Hata listesi (bos = gecerli). Bilinmeyen alan, yanlis tur, aralik disi deger REDDEDILIR; eksik alan hata DEGILDIR (opsiyonel)."""
    if not isinstance(fields, dict):
        return ["brief bir nesne (sozluk) olmali"]
    errs = [f"bilinmeyen brief alani: {k!r} (izinli: {list(BRIEF_FIELDS)})" for k in sorted(set(fields) - set(BRIEF_FIELDS))]
    f = fields
    if "n" in f and (isinstance(f["n"], bool) or not isinstance(f["n"], int) or not 1 <= f["n"] <= MAX_ALTERNATIVES):
        errs.append(f"n: 1..{MAX_ALTERNATIVES} arasi tam sayi olmali (varsayilan {DEFAULT_ALTERNATIVES})")
    if "weights" in f:
        w = f["weights"]
        if not isinstance(w, dict) or not w:
            errs.append("weights: bos olmayan sozluk olmali")
        else:
            errs += [f"weights: bilinmeyen eksen {k!r} (gecerli: {list(OBJECTIVES)})" for k in sorted(set(w) - set(OBJECTIVES))]
            if any(not _is_num(v) or v < 0 for v in w.values()):
                errs.append("weights: degerler negatif olmayan sayi olmali")
            elif not any(v > 0 for v in w.values()):
                errs.append("weights: en az bir agirlik pozitif olmali")
    for k in ("step_mm", "min_separation_mm"):
        if k in f and (not _is_num(f[k]) or f[k] <= 0):
            errs.append(f"{k}: pozitif sayi olmali")
    if "rotations_deg" in f and (not isinstance(f["rotations_deg"], list) or not f["rotations_deg"] or any(not _is_num(r) for r in f["rotations_deg"])):
        errs.append("rotations_deg: bos olmayan sayi listesi olmali")
    for k in ("front_setback_mm", "side_setback_mm", "rear_setback_mm", "taks", "kaks"):
        if k in f and (not _is_num(f[k]) or f[k] < 0):
            errs.append(f"{k}: negatif olmayan sayi olmali")
    if "floors" in f and (isinstance(f["floors"], bool) or not isinstance(f["floors"], int) or f["floors"] < 1):
        errs.append("floors: 1 ya da daha buyuk tam sayi olmali")
    if "site_scale" in f and f["site_scale"] not in ("1/200", "1/500"):
        errs.append("site_scale: '1/200' ya da '1/500' olmali")
    if "notes" in f and not isinstance(f["notes"], str):
        errs.append("notes: metin olmali")
    return errs


def brief_sha(fields: dict) -> str:
    return hashlib.sha256(json.dumps(fields, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def brief_numbers(fields: dict) -> set[str]:
    """Brief'te kullanicinin verdigi sayilarin metin biçimleri (anlatimda kullanilabilir sayilar)."""
    out: set[str] = set()

    def add(v):
        if _is_num(v):
            out.add(f"{v:g}")
            out.add(str(v))
    for k, v in fields.items():
        if k == "notes":
            continue
        if isinstance(v, dict):
            for x in v.values():
                add(x)
        elif isinstance(v, list):
            for x in v:
                add(x)
        else:
            add(v)
    return {t.replace(",", ".") for t in out}


def numbers_in(text: str) -> set[str]:
    return {t.replace(",", ".") for t in NUMBER_RE.findall(text)}


def unsourced_numbers(text: str, allowed) -> list[str]:
    return sorted(numbers_in(text) - {a.replace(",", ".") for a in allowed})


def route_phase(provide_site: bool) -> str:
    """Operator akisinin ilk sorusunun cevabi: evet -> vaziyet fazi; hayir -> kat/birim fazi (bu kod calismaz)."""
    if not isinstance(provide_site, bool):
        raise VaziyetError("faz sorusunun cevabi evet/hayir (bool) olmali")
    return PHASE_SITE if provide_site else PHASE_UNITS


# ------------------------------------------------------------------ ekleme-yalniz diyalog kaydi
def log_path(project_dir) -> Path:
    return Path(project_dir) / LOG_NAME


def read_log(path) -> list[dict]:
    p = Path(path)
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]


def append_record(path, kind: str, data: dict, context_sha256: str | None = None, text: str | None = None, allowed_numbers=None, ts: str | None = None) -> dict:
    """Ekleme-yalniz kayit. Gecersiz tur ya da (allowed verildiyse) KAYNAKSIZ sayi iceren metin REDDEDILIR."""
    if kind not in KINDS:
        raise VaziyetError(f"kayit turu {KINDS} icinden olmali")
    if text is not None and allowed_numbers is not None:
        bad = unsourced_numbers(text, allowed_numbers)
        if bad:
            raise VaziyetError(f"metinde kaynaksiz sayi var: {bad} (sayi yalniz kullanici degerinden ya da olcumden gelir)")
    rec = {"ts": ts or datetime.datetime.now().astimezone().isoformat(timespec="seconds"), "kind": kind, "context_sha256": context_sha256, "data": data}
    if text is not None:
        rec["text"] = text
    with Path(path).open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")
    return rec


def current_phase(records: list[dict]) -> str | None:
    for r in reversed(records):
        if r["kind"] == "phase":
            return r["data"]["phase"]
    return None


def effective_brief(records: list[dict]) -> dict | None:
    """En son brief kaydi (onerilen ya da onayli). ONAYLI degilse `approved=False`: degisiklik yeniden onay ister."""
    for r in reversed(records):
        if r["kind"] in ("brief_proposed", "brief_approved"):
            return {"fields": r["data"]["fields"], "approved": r["kind"] == "brief_approved", "proposed_by": r["data"].get("proposed_by"), "sha": r["data"]["sha"]}
    return None


def require_phase_and_brief(records: list[dict]) -> dict:
    """study/select oncesi kapilar: (1) faz = vaziyet; (2) brief onayli. Aksi halde `VaziyetError` (motor calismaz)."""
    phase = current_phase(records)
    if phase != PHASE_SITE:
        raise VaziyetError("faz sorusu cevaplanmadi" if phase is None else f"faz '{phase}': vaziyet etudu bu fazda calismaz (kat/birim yerlesimi ayri plandir)")
    b = effective_brief(records)
    if b is None:
        raise VaziyetError("brief yok: once brief onerilip kullanici tarafindan ONAYLANMALI")
    if not b["approved"]:
        raise VaziyetError("brief kullanici tarafindan ONAYLANMADI (model onerisi motora gecirilemez)")
    errs = validate_brief(b["fields"])
    if errs:
        raise VaziyetError("brief gecersiz: " + "; ".join(errs))
    return b


# ------------------------------------------------------------------ secim
def selection_patch(alt, existing_north) -> dict:
    """Secilen alternatif -> `site.building` + `meta.north_angle` PATCH taslagi (dosyaya YAZILMAZ). north_angle = -bina_donusu (DEV-081)."""
    return {"site": {"building": {"position": [alt.position[0], alt.position[1]], "rotation_deg": alt.rotation_deg}},
            "meta": {"north_angle": plan_north_angle(alt.rotation_deg)}}


def deep_merge(base: dict, patch: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in patch.items():
        out[k] = deep_merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else copy.deepcopy(v)
    return out


def check_patch(context: dict, patch: dict) -> list[str]:
    """Patch uygulanmis kopyada `check_site` HATALARI (bos = temiz). Uyarilar (tutarlilik vb.) dondurulmez."""
    return check_site(deep_merge(context, patch))[0]


def delegation_decision(result, brief_fields: dict) -> tuple[bool, str]:
    """'sen karar ver' devri: tek bir deterministik ONERI yalniz AGIRLIK verilmisse vardir (A1 = en yuksek skor). Agirliksiz secimde tek 'en iyi' iddiasi YOKTUR ->
    devir reddedilir. Ciddi bulgu (TAKS/KAKS tavani asildi, secenek istenen bolgenin disinda) varsa devir olsa bile SORULUR."""
    if not result.alternatives:
        return False, "alternatif yok"
    if not brief_fields.get("weights"):
        return False, "agirlik verilmedi: motorun tek bir 'en iyi' onerisi yok; agirlik/oncelik verin ya da alternatiflerden birini siz secin"
    first = result.alternatives[0]
    if any(c["ok"] is False for c in result.ceilings):
        return False, "TAKS/KAKS tavani asiliyor (ciddi bulgu): devir olsa bile kullaniciya sorulur"
    if first.outside_zone:
        return False, "onerilen secenek istenen yerlesim bolgesinin disina tasiyor (ciddi bulgu): devir olsa bile kullaniciya sorulur"
    return True, f"{first.id}: istediginiz agirliklara gore en yuksek skorlu secenek"
