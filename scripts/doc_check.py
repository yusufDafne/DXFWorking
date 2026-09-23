#!/usr/bin/env python3
"""Gelistirme dokumanlarinin KENDI ICINDE tutarli olup olmadigini denetler.

**Neden var:** "Calisma sonunda dokumanlari guncelle" kurali uzun sure yalnizca
DUZYAZI olarak duruyordu ve gercekten kacti: rev-10'da `DEV-006` maddesinin
`Durum:` alani COMPLETED yapildi ama madde hala `## READY` basliginin altinda
kaldi; ayni sekilde COMPLETED ve BLOCKED maddeler "PLANNED" basligi altinda
birikti. Kullanici bunu fark etti. Duzyazi bir hatirlatma bu hata sinifini
engellemiyor - bu yuzden kural MEKANIK bir kontrole cevrildi.

Kontroller:

1. `## READY` bolumunde COMPLETED/BLOCKED bir madde bulunamaz.
2. `## COMPLETED` bolumundeki her madde gercekten COMPLETED olmalidir.
3. "Durum ozeti" tablosu her maddenin gercek `Durum:` degeriyle ortusmelidir.
4. Her DEV kimligi tam bir kez tanimlanir ve tabloda tam bir kez gecer.
5. COMPLETED bir madde `HD-xxx` kaydina atif yapiyorsa o kayit
   `DEVELOPMENT_HISTORY.md` icinde GERCEKTEN bulunmalidir.
6. Atif yapilan `golden/<ad>/` diskte var olmalidir; diskteki her modulun
   kendi `CLAUDE.md`'si bulunmali ve `scripts/CLAUDE.md` icinde anilmalidir.
7. `scripts/CLAUDE.md` modul tablosunda UYGULANDI isaretli bir satirda anilan
   her sinif adi o modulde GERCEKTEN tanimli olmali; bir modul tabloda birden
   fazla kez listelenmemelidir.
8. CAKISMA KAPSAMI (DEV-019): geometri ureten her modulun ya kendi
   `collision.py` ayak izi saglayicisi olmali, ya da `collision/scene.py`
   icindeki `COLLISION_EXEMPT` sozlugunde GEREKCESIYLE listelenmis olmalidir.
   Bu, "yeni bir modul eklendiginde 'bu modul hangi modulle cakisabilir?'
   sorusu acikca yanitlanir" kuralini duzyazi olmaktan cikarip MEKANIK hale
   getirir - tipki 6. maddenin yaptigi gibi.
9. SOZLESME SURUMU (DEV-020): her modul `CONTRACT_VERSION` tasimali ve
   `version.py::CONTRACT_MODULES` listesiyle BIREBIR ortusmelidir; aksi halde
   provenance kaydi eksik/bayat cikar.

Kullanim:
    python scripts/doc_check.py
Cikis kodu: tutarliysa 0, degilse 1.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEVELOPMENT_DIR = ROOT / "docs" / "development"
TASKS_PATH = DEVELOPMENT_DIR / "DEVELOPMENT_TASKS.md"
HISTORY_PATH = DEVELOPMENT_DIR / "DEVELOPMENT_HISTORY.md"

STATUS_WORDS = ("COMPLETED", "BLOCKED", "PLANNED", "READY", "IN_PROGRESS", "VALIDATION")


def _read(path: Path) -> str:
    return path.read_bytes().decode("utf-8")


def parse_items(text: str) -> list[dict]:
    """Her `### DEV-xxx` maddesini bolumu ve durumuyla birlikte cikarir."""
    items: list[dict] = []
    section = ""
    current: dict | None = None
    for line in text.splitlines():
        if line.startswith("## "):
            section = line[3:].strip()
            continue
        heading = re.match(r"### (DEV-\d+)\s*(?:—|-)\s*(.*)", line)
        if heading:
            current = {"id": heading.group(1), "title": heading.group(2).strip(),
                       "section": section, "status": None, "body": []}
            items.append(current)
            continue
        if current is None:
            continue
        current["body"].append(line)
        status = re.match(r"- \*\*Durum:\*\*\s*(\S+)", line)
        if status and current["status"] is None:
            current["status"] = status.group(1).strip("*")
    return items


def parse_summary_table(text: str) -> dict[str, str]:
    """'Durum ozeti' tablosundaki DEV -> durum eslesmesi."""
    table: dict[str, str] = {}
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 3 or not cells[0].startswith("DEV-"):
            continue
        status = next((w for w in STATUS_WORDS if w in cells[2]), None)
        if status:
            table[cells[0]] = status
    return table


def check_tasks() -> list[str]:
    errors: list[str] = []
    text = _read(TASKS_PATH)
    items = parse_items(text)
    table = parse_summary_table(text)

    seen: dict[str, int] = {}
    for item in items:
        seen[item["id"]] = seen.get(item["id"], 0) + 1
        if item["status"] is None:
            errors.append(f"{item['id']}: 'Durum:' satiri yok.")
            continue

        # 1-2) bolum ile durum tutarliligi
        if item["section"].startswith("READY") and item["status"] != "READY":
            errors.append(
                f"{item['id']}: durumu {item['status']} ama hala '## READY' "
                f"basligi altinda. Tamamlanan madde dogru bolume tasinmalidir."
            )
        if item["section"].startswith("COMPLETED") and item["status"] != "COMPLETED":
            errors.append(
                f"{item['id']}: '## COMPLETED' altinda ama durumu {item['status']}."
            )

        # 3) ozet tablo ile tutarlilik
        if item["id"] not in table:
            errors.append(f"{item['id']}: 'Durum ozeti' tablosunda yok.")
        elif table[item["id"]] != item["status"]:
            errors.append(
                f"{item['id']}: tabloda {table[item['id']]}, maddede "
                f"{item['status']} yaziyor."
            )

        # 5) COMPLETED madde atif yaptigi HD kaydi gercekten var mi
        body = "\n".join(item["body"])
        for record in set(re.findall(r"HD-\d+", body)):
            if not re.search(rf"^## {record}\b", _read(HISTORY_PATH), re.M):
                errors.append(
                    f"{item['id']}: '{record}' kaydina atif yapiyor ama bu kayit "
                    f"DEVELOPMENT_HISTORY.md icinde yok."
                )

    # 4) yinelenen / fazladan kimlik
    for task_id, count in sorted(seen.items()):
        if count > 1:
            errors.append(f"{task_id}: {count} kez tanimlanmis.")
    for task_id in sorted(set(table) - set(seen)):
        errors.append(f"{task_id}: tabloda var ama maddesi yok.")
    return errors


def check_paths() -> list[str]:
    """Modul/golden yapisi ile dokumanlarin ortusmesi.

    NOT: "dokumanda gecen her yol diskte olmali" kurali YANLIS POZITIF uretir -
    plan maddeleri bilerek HENUZ OLMAYAN modullerden soz eder (orn. DEV-018'in
    onerdigi `scripts/blocks/`). Bu yuzden yon TERSINE cevrildi: diskte VAR olan
    bir bilesenin dokumante edilmis olmasi aranir. Bayat kalan sey budur.
    """
    errors: list[str] = []

    # 6a) Dokumanlarda ATIF YAPILAN golden referansi gercekten var mi (somut
    #     veridir, tasinirsa atif bayatlar - nitekim docs/ altindan tasindi).
    golden_pattern = re.compile(r"`(golden/[A-Za-z0-9_]+)/?`")
    for doc in sorted(DEVELOPMENT_DIR.glob("*.md")) + [ROOT / "CLAUDE.md",
                                                       ROOT / "scripts" / "CLAUDE.md"]:
        if not doc.exists():
            continue
        for match in sorted(set(golden_pattern.findall(_read(doc)))):
            if not (ROOT / match).exists():
                errors.append(
                    f"{doc.relative_to(ROOT).as_posix()}: '{match}' golden "
                    f"referansina atif yapiyor ama bu dizin yok."
                )

    # 6b) Her modulun KENDI CLAUDE.md'si olmali (projenin mottosu).
    # 6c) Her modul scripts/CLAUDE.md'de anilmali (mimari dosyasi bayatlamasin).
    architecture = _read(ROOT / "scripts" / "CLAUDE.md")
    for module in sorted((ROOT / "scripts").iterdir()):
        if not module.is_dir() or module.name.startswith(("_", ".")):
            continue
        if not (module / "__init__.py").exists():
            continue
        if not (module / "CLAUDE.md").exists():
            errors.append(
                f"scripts/{module.name}/: modulun kendi CLAUDE.md dosyasi yok "
                f"(her cizim konusu kendi modulu + kendi izole CLAUDE.md'si)."
            )
        if f"scripts/{module.name}/" not in architecture:
            errors.append(
                f"scripts/{module.name}/: scripts/CLAUDE.md icinde anilmiyor "
                f"(yeni modul mimari dosyasina islenmemis)."
            )
    return errors


def module_symbols(module: Path) -> set[str]:
    """Bir modulun tanimladigi adlar (`__all__` + modul seviyesindeki sinif/
    fonksiyon adlari). `ast` ile okunur; modulu import etmez, boylece bu
    kontrol ezdxf gibi calisma zamani bagimliliklari gerektirmez."""
    import ast

    source = module / "__init__.py"
    if not source.exists():
        return set()
    tree = ast.parse(source.read_bytes().decode("utf-8"))
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
            if any(getattr(t, "id", None) == "__all__" for t in node.targets):
                names |= {e.value for e in getattr(node.value, "elts", [])
                          if isinstance(e, ast.Constant) and isinstance(e.value, str)}
    return names


def check_architecture_table() -> list[str]:
    """scripts/CLAUDE.md modul tablosu gercek API ile ortusuyor mu.

    UYGULANDI isaretli bir satirda anilan her ad modulde TANIMLI olmalidir.
    Bu kontrol, tablonun bayatlamasini engeller: rev-11'den once `furniture/`
    satiri hic var olmayan `Counter`/`Fixture` siniflarini anlatiyordu ve
    modul iki kez listelenmisti - kimse fark etmedi."""
    errors: list[str] = []
    architecture = _read(ROOT / "scripts" / "CLAUDE.md")
    seen: dict[str, int] = {}
    for line in architecture.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 3:
            continue
        module_match = re.fullmatch(r"`(scripts/)?([a-z_]+)/`", cells[0])
        if not module_match:
            continue
        name = module_match.group(2)
        seen[name] = seen.get(name, 0) + 1
        if "PLANLANAN" in cells[2]:
            continue
        symbols = module_symbols(ROOT / "scripts" / name)
        if not symbols:
            errors.append(
                f"scripts/CLAUDE.md: '{name}/' UYGULANDI olarak isaretli ama "
                f"scripts/{name}/__init__.py bulunamadi."
            )
            continue
        for symbol in re.findall(r"`([A-Za-z_][A-Za-z0-9_]*)`", cells[1]):
            if symbol not in symbols:
                errors.append(
                    f"scripts/CLAUDE.md: '{name}/' satiri `{symbol}` sinifini "
                    f"anlatiyor ama modulde boyle bir ad YOK."
                )
    for name, count in sorted(seen.items()):
        if count > 1:
            errors.append(
                f"scripts/CLAUDE.md: '{name}/' modul tablosunda {count} kez "
                f"listelenmis."
            )
    return errors


def _drawing_modules() -> list[Path]:
    """`scripts/` altindaki gercek moduller (paket olanlar)."""
    modules = []
    for module in sorted((ROOT / "scripts").iterdir()):
        if not module.is_dir() or module.name.startswith(("_", ".")):
            continue
        if (module / "__init__.py").exists():
            modules.append(module)
    return modules


def check_collision_coverage() -> list[str]:
    """Her modul cakisma denetimine ya KATILIR ya da GEREKCEYLE muaftir.

    `collision` ve `version` saf Python'dur (ezdxf/jsonschema gerektirmez),
    bu yuzden buradan import edilebilirler; cizim modulleri hala import
    EDILMEZ (bkz. `module_symbols`, ast ile okur).
    """
    errors: list[str] = []
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        from collision import COLLISION_EXEMPT, FOOTPRINT_PROVIDERS
    except ImportError as exc:
        return [f"collision modulu import edilemedi: {exc}"]

    provider_modules = {path.split(".")[0] for path in FOOTPRINT_PROVIDERS}

    for module in _drawing_modules():
        name = module.name
        has_provider = (module / "collision.py").exists()
        is_exempt = name in COLLISION_EXEMPT
        if has_provider and is_exempt:
            errors.append(
                f"scripts/{name}/: hem collision.py var hem COLLISION_EXEMPT "
                f"icinde listelenmis - biri kaldirilmalidir."
            )
        elif not has_provider and not is_exempt:
            errors.append(
                f"scripts/{name}/: ne collision.py ayak izi saglayicisi var ne "
                f"de COLLISION_EXEMPT icinde gerekcesi yazili. 'Bu modul hangi "
                f"modulle cakisabilir?' sorusu yanitlanmamis (DEV-019)."
            )
        if has_provider and name not in provider_modules:
            errors.append(
                f"scripts/{name}/collision.py var ama collision/scene.py "
                f"FOOTPRINT_PROVIDERS listesinde YOK - saglayici hic cagrilmiyor."
            )

    existing = {m.name for m in _drawing_modules()}
    for name, reason in sorted(COLLISION_EXEMPT.items()):
        if name not in existing:
            errors.append(
                f"COLLISION_EXEMPT: '{name}' diye bir modul YOK (bayat kayit)."
            )
        if not str(reason).strip():
            errors.append(f"COLLISION_EXEMPT['{name}']: gerekce bos.")

    for path in FOOTPRINT_PROVIDERS:
        module_name, _, leaf = path.partition(".")
        if not (ROOT / "scripts" / module_name / f"{leaf}.py").exists():
            errors.append(
                f"collision/scene.py: '{path}' saglayicisi listelenmis ama "
                f"scripts/{module_name}/{leaf}.py bulunamadi."
            )
    return errors


def check_contract_versions() -> list[str]:
    """Modul sozlesme surumleri ile `version.CONTRACT_MODULES` ortusuyor mu."""
    errors: list[str] = []
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        from version import CONTRACT_MODULES
    except ImportError as exc:
        return [f"version modulu import edilemedi: {exc}"]

    declared = set(CONTRACT_MODULES)
    for module in _drawing_modules():
        has_version = "CONTRACT_VERSION" in module_symbols(module)
        if has_version and module.name not in declared:
            errors.append(
                f"scripts/{module.name}/: CONTRACT_VERSION tasiyor ama "
                f"version.py::CONTRACT_MODULES icinde YOK - provenance kaydina "
                f"girmiyor (DEV-020)."
            )
        if not has_version:
            errors.append(
                f"scripts/{module.name}/__init__.py: CONTRACT_VERSION "
                f"bildirmemis (DEV-020)."
            )
    for name in sorted(declared - {m.name for m in _drawing_modules()}):
        errors.append(
            f"version.py::CONTRACT_MODULES: '{name}' diye bir modul YOK "
            f"(bayat kayit)."
        )
    return errors


def run() -> list[str]:
    return (check_tasks() + check_paths() + check_architecture_table()
            + check_collision_coverage() + check_contract_versions())


def main() -> int:
    errors = run()
    if errors:
        print("DOKUMAN TUTARLILIGI BASARISIZ:")
        for error in errors:
            print(f"  - {error}")
        return 1
    print("Dokuman tutarliligi TAMAM: gorev durumlari, ozet tablo, HD atiflari, "
          "modul/golden yollari, cakisma kapsami ve sozlesme surumleri ortusuyor.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
