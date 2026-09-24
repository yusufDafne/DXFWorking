#!/usr/bin/env python3
"""Proje <-> sistem surum uyumu ve provenance (DEV-020).

**Karar (rev-12): ikisi de, ama ayni is icin degil.**

| Mekanizma                 | Rolu    | Bloklar mi        |
| ------------------------- | ------- | ----------------- |
| `meta.schema_version`     | KAPI    | MAJOR farkta EVET |
| modul `CONTRACT_VERSION`  | TESHIS  | hayir             |
| `output/provenance.json`  | KAYIT   | hayir             |

**Surumlenen sey KOD DEGIL, SOZLESMEDIR.** rev-11'de `furniture/` tek dosyadan
bes dosyaya bolundu: kod tamamen degisti, etkilenen proje SIFIR. Buna karsilik
`floors[].furniture[].position` alani yeniden adlandirilsa tek satir kod
degisir ve HER proje kirilir. Bu yuzden bir modulun `CONTRACT_VERSION`'u
yalnizca o modulun context'ten OKUDUGU alanlar degistiginde artar; refactor
surumu artirmaz.

**Kapi bagimsiz bir sayi degildir:** `SCHEMA_VERSION`in MAJOR'u, herhangi bir
modul sozlesmesi geriye uyumsuz degistiginde artar - yani modul
sozlesmelerinin turevidir. Boylece tek ve temiz bir karar noktasi ile "hangi
modul sorumlu" cevabi birlikte elde edilir, N x N uyum matrisi maliyeti
odenmeden.

**Migrasyon asla otomatik degildir.** Major kirilimda eski proje sessizce
donusturulmez: proje verisi uydurulmaz ve her degisiklik `requests.jsonl` +
`rev_history` uzerinden gecer (bkz. kok CLAUDE.md). Otomatik migrasyon bu
zinciri kirar ve provenance yalan soylemeye baslar.

**Kademeli giris:** `meta.schema_version` bugun OPSIYONELDIR; yoksa
`DEFAULT_SCHEMA_VERSION` varsayilir ve UYARI verilir. Tum context'ler alani
tasidiktan sonra schema'da `required` yapilacaktir.
"""
from __future__ import annotations

import importlib
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_ROOT = Path(__file__).resolve().parent

# Sistemin BUGUNKU context sozlesmesi. MAJOR yalnizca geriye uyumsuz bir
# schema degisikliginde artar (alan kaldirma/yeniden adlandirma/anlam
# degistirme); alan EKLEMEK minor'dur.
SCHEMA_VERSION = "1.0.0"

# Alani tasimayan eski projeler icin varsayilan. Bugun tum projeler bu
# surumden gelmektedir.
DEFAULT_SCHEMA_VERSION = "1.0.0"

# `CONTRACT_VERSION` tasiyan moduller. Liste ACIKTIR: yeni bir modul buraya
# eklenmezse provenance'a girmez, bu yuzden `doc_check.py` bunu denetler.
CONTRACT_MODULES: tuple[str, ...] = (
    "axis",
    "collision",
    "columns",
    "dimensions",
    "elevations",
    "furniture",
    "importer",
    "legend",
    "openings",
    "pafta",
    "rooms",
    "typography",
    "walls",
)


def parse_semver(value: str) -> tuple[int, int, int]:
    parts = str(value).strip().split(".")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        raise ValueError(f"Gecersiz surum bicimi: '{value}' (beklenen MAJOR.MINOR.PATCH)")
    return int(parts[0]), int(parts[1]), int(parts[2])


def project_schema_version(context: dict) -> tuple[str, bool]:
    """(surum, context'te BILDIRILMIS mi)."""
    declared = context.get("meta", {}).get("schema_version")
    if declared:
        return str(declared), True
    return DEFAULT_SCHEMA_VERSION, False


def check_compatibility(context: dict) -> tuple[list[str], list[str]]:
    """(hatalar, uyarilar).

    MAJOR farki BLOKLAR: proje, sistemin artik anlamadigi (ya da henuz
    anlamadigi) bir sozlesmeyle yazilmistir ve sessizce yanlis bir DXF
    uretmektense durmak dogrudur. MINOR/PATCH farki yalnizca bildirilir.
    """
    errors: list[str] = []
    warnings: list[str] = []

    declared, is_declared = project_schema_version(context)
    if not is_declared:
        warnings.append(
            f"meta.schema_version bildirilmemis; '{DEFAULT_SCHEMA_VERSION}' "
            f"varsayildi. Alan bir revizyonda projeye eklenmelidir (DEV-020)."
        )

    try:
        project = parse_semver(declared)
    except ValueError as exc:
        errors.append(str(exc))
        return errors, warnings

    system = parse_semver(SCHEMA_VERSION)
    if project[0] != system[0]:
        errors.append(
            f"Surum uyumsuzlugu: proje schema_version {declared}, sistem "
            f"{SCHEMA_VERSION}. MAJOR farki geriye uyumsuzdur; proje "
            f"guncellenmeden uretim yapilmaz (otomatik migrasyon YOKTUR)."
        )
    elif project > system:
        warnings.append(
            f"Proje schema_version {declared}, bu sistemden ({SCHEMA_VERSION}) "
            f"YENI. Sistem guncel degil olabilir."
        )
    elif project < system:
        warnings.append(
            f"Proje schema_version {declared}, sistem {SCHEMA_VERSION}. "
            f"Geriye uyumlu fark; uretim surer."
        )
    return errors, warnings


def module_contracts() -> dict[str, str]:
    """Modul -> `CONTRACT_VERSION`. TESHIS bilgisidir, kapi degildir."""
    if str(SCRIPTS_ROOT) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_ROOT))
    contracts: dict[str, str] = {}
    for name in CONTRACT_MODULES:
        try:
            module = importlib.import_module(name)
        except ImportError as exc:  # modul henuz yoksa teshis kesilmez
            contracts[name] = f"<import hatasi: {exc}>"
            continue
        contracts[name] = getattr(module, "CONTRACT_VERSION", "<bildirilmemis>")
    return contracts


def git_commit() -> str:
    """Uretim anindaki commit. Repo yoksa bos doner - uretimi durdurmaz."""
    try:
        result = subprocess.run(
            ["git", "-C", str(PROJECT_ROOT), "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=10, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    return result.stdout.strip() if result.returncode == 0 else ""


def generation_timestamp() -> datetime:
    return datetime.now(timezone.utc).astimezone()


def format_timestamp(moment: datetime) -> str:
    """Kapak ve rapor icin insan okunur damga (yerel saat)."""
    return moment.strftime("%Y-%m-%d %H:%M")


def provenance(context: dict, *, output_path: str = "",
               moment: datetime | None = None) -> dict:
    """Uretim KAYDI. Bloklamaz; "koptu mu, neden" sorusunu yanitlar.

    **Neden `context.json` icinde degil:** provenance bir URETIM CALISTIRMASININ
    kaydidir, proje TASARIM verisi degildir. Context'e yazilsaydi her uretim
    proje dosyasini kirletir ve her `generate` calistirmasi sahte bir diff
    uretirdi. Bu yuzden ciktinin yanina, `output/provenance.json` olarak
    yazilir - `schema/` ve `output/` gibi.
    """
    moment = moment or generation_timestamp()
    declared, is_declared = project_schema_version(context)
    return {
        "generated_at": moment.isoformat(timespec="seconds"),
        "project_name": context.get("meta", {}).get("project_name", ""),
        "project_revision": (context.get("rev_history") or [{}])[-1].get("rev"),
        "schema_version": {
            "project": declared,
            "project_declared": is_declared,
            "system": SCHEMA_VERSION,
        },
        "module_contracts": module_contracts(),
        "git_commit": git_commit(),
        "output": output_path,
    }
