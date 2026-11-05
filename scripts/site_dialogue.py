#!/usr/bin/env python3
"""Vaziyet yerlesim etudu - kullanici/dil modeli diyalog koprusu (DEV-085). Context'e YAZMAZ; secim PATCH TASLAGI basar (normal revizyon akisiyla uygulanir).

  guide                                  sozlesme metni (operator docs/'u okuyamaz)
  phase    CONTEXT --provide-site evet|hayir     ilk soru: "Parsel/vaziyet plani sunmak ister misiniz?"  (hayir -> kat/birim fazi; bu komutlar calismaz)
  brief propose CONTEXT --by dil_modeli|kullanici --json '{...}'   izinli alanlardan brief ONERISI (onaylanmadan motora gecmez)
  brief approve CONTEXT                  EN SON oneriyi kullanici ONAYLADI olarak kaydet (yalniz kullanici acikca onayladiktan sonra)
  brief show    CONTEXT
  study    CONTEXT                       ONAYLI brief ile etut (alternatifler + olculmus anlatim)
  select   CONTEXT --alternative A2 | --delegate    secim patch'i (site.building + meta.north_angle); --delegate yalniz agirlik verildiyse ve ciddi bulgu yoksa

Kayit: <context dizini>/site_dialogue.jsonl (ekleme-yalniz).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from vaziyet import (BRIEF_FIELDS, OBJECTIVE_LABEL, PHASE_QUESTION, PHASE_SITE, VaziyetError, append_record, brief_numbers, brief_sha, check_patch,  # noqa: E402
                     current_phase, delegation_decision, effective_brief, log_path, narrate_alternative, read_log, require_phase_and_brief, route_phase,
                     selection_patch, study_from_brief, unsourced_numbers, validate_brief)
from vaziyet.brief import numbers_in  # noqa: E402

GUIDE = f"""VAZIYET ETUDU DIYALOG SOZLESMESI (DEV-085)
1. Ilk soru: "{PHASE_QUESTION}" Evet -> bina-parsel yerlesimi (bu arac). Hayir -> kat/birim yerlesim alternatifleri (ayri plan); bu arac calismaz.
2. Dil modeli YALNIZ onerir: brief alanlari ({', '.join(BRIEF_FIELDS)}); serbest metin yalniz `notes` (motora gecmez). Model koordinat, cekme, TAKS/KAKS gibi sayi URETMEZ -
   sayilar kullanicidan gelir. Brief kullanici tarafindan ONAYLANMADAN etut calismaz (onay: `brief approve`, yalniz kullanici acikca onayladiktan sonra).
3. Adim (`step_mm`) ve donus kumesi (`rotations_deg`) varsayilansizdir: kullaniciya sorulur. Alternatif sayisi varsayilan 3; agirlik isteğe baglidir.
   Cekme/TAKS/KAKS bilinmiyorsa imar katalogu varsayilani KULLANILIR ve ADIYLA, 'DOGRULANMADI' ibaresiyle bildirilir.
4. Motor deterministiktir; tek 'en iyi' iddiasi yoktur; alternatifleri sade dille ve OLCULMUS sayilarla anlat (kaynaksiz sayi yok). Bolge disina tasan secenegi ve
   tavan asimini SOYLE.
5. Secim kullanicinindir (`select --alternative`). 'Sen karar ver' devri yalniz agirlik verilmisse ve ciddi bulgu yoksa gecerlidir; secim ve bedeli SONRADAN bildirilir.
6. Secim patch'i context'e otomatik yazilmaz: normal revizyon akisi (requests.jsonl, validate, kullanici onayi, commit onayi) uygulanir.
"""


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(args):
    ctx_path = Path(args.context)
    return ctx_path, json.loads(ctx_path.read_text(encoding="utf-8")), log_path(ctx_path.parent)


def cmd_phase(args) -> int:
    ctx_path, _, log = _load(args)
    phase = route_phase(args.provide_site == "evet")
    append_record(log, "phase", {"phase": phase, "question": PHASE_QUESTION}, _sha(ctx_path))
    if phase == PHASE_SITE:
        print("Birinci faz: bina-parsel yerlesimi. Siradaki: brief onerisi (`brief propose`).")
    else:
        print("Ikinci faz: kat/birim yerlesim alternatifleri (vaziyet etudu bu fazda calismaz; ayri plan).")
    return 0


def cmd_brief_propose(args) -> int:
    ctx_path, _, log = _load(args)
    try:
        fields = json.loads(args.json)
    except json.JSONDecodeError as exc:
        print("HATA: --json gecerli JSON degil:", exc)
        return 2
    errs = validate_brief(fields)
    if errs:
        print("BRIEF REDDEDILDI:")
        for e in errs:
            print("  -", e)
        return 1
    if current_phase(read_log(log)) != PHASE_SITE:
        print("HATA: once `phase --provide-site evet` (faz sorusu cevaplanmali).")
        return 1
    sha = brief_sha(fields)
    append_record(log, "brief_proposed", {"fields": fields, "sha": sha, "proposed_by": args.by}, _sha(ctx_path))
    print(f"Brief onerildi ({args.by}); kullanici onayi BEKLENIYOR. Su degerlerle calisilacak:")
    for k in BRIEF_FIELDS:
        if k in fields:
            print(f"  {k}: {fields[k]}")
    print("Dogruysa kullanici acikca onayladiktan sonra: brief approve. Degisiklik icin yeni oneri yazin (onay yeniden gerekir).")
    return 0


def cmd_brief_approve(args) -> int:
    ctx_path, _, log = _load(args)
    b = effective_brief(read_log(log))
    if b is None:
        print("HATA: onaylanacak brief yok.")
        return 1
    if b["approved"]:
        print("Bu brief zaten onayli.")
        return 0
    append_record(log, "brief_approved", {"fields": b["fields"], "sha": b["sha"], "proposed_by": b["proposed_by"], "approved_by": "kullanici"}, _sha(ctx_path))
    print("Brief ONAYLANDI (kullanici). Siradaki: study.")
    return 0


def cmd_brief_show(args) -> int:
    _, _, log = _load(args)
    b = effective_brief(read_log(log))
    print("brief yok" if b is None else json.dumps({"fields": b["fields"], "onayli": b["approved"], "oneren": b["proposed_by"]}, ensure_ascii=False, indent=2))
    return 0


def _run(args):
    ctx_path, ctx, log = _load(args)
    records = read_log(log)
    b = require_phase_and_brief(records)
    result, notices, buildable = study_from_brief(ctx, b["fields"])
    return ctx_path, ctx, log, b, result, notices


def cmd_study(args) -> int:
    try:
        ctx_path, ctx, log, b, result, notices = _run(args)
    except (VaziyetError, ValueError, KeyError) as exc:
        print("ETUT YAPILAMADI:", exc)
        return 1
    print(f"Aday: {result.generated}, elenen: {sum(result.eliminated.values())} {dict(sorted(result.eliminated.items()))}, kalan: {result.survivors}")
    print("Takas eksenleri:", ", ".join(OBJECTIVE_LABEL[a] for a in result.parameters["axes"]) or "-")
    for line in notices:
        print("BILGI:", line)
    texts = []
    for a in result.alternatives:
        print(f"\n{a.id} - konum {a.position[0]:.0f}, {a.position[1]:.0f} mm; donus {a.rotation_deg:g} derece; kat plani kuzey acisi {a.plan_north_angle:g} derece")
        for line in narrate_alternative(a):
            print(line)
            texts.append(line)
    for c in result.ceilings:
        val = "olculemedi" if c["value"] is None else f"{c['value']:.3f}"
        print(f"\n{c['name']}: {val} (tavan {c['limit']:g}, kaynak {c['limit_source']}) -> {'TAMAM' if c['ok'] else ('ASILIYOR' if c['ok'] is False else 'olculemedi')}")
    for note in result.notes:
        print("NOT:", note)
    append_record(log, "study", {"brief_sha": b["sha"], "alternatives": [{"id": a.id, "position": list(a.position), "rotation_deg": a.rotation_deg} for a in result.alternatives]},
                  _sha(ctx_path))
    return 0


def cmd_select(args) -> int:
    try:
        ctx_path, ctx, log, b, result, notices = _run(args)
    except (VaziyetError, ValueError, KeyError) as exc:
        print("SECIM YAPILAMADI:", exc)
        return 1
    delegated = bool(args.delegate)
    if delegated and args.alternative:
        print("HATA: --delegate ile --alternative birlikte verilmez.")
        return 2
    if not delegated and not args.alternative:
        print("HATA: --alternative <id> ya da --delegate gerekir.")
        return 2
    if delegated:
        ok, why = delegation_decision(result, b["fields"])
        if not ok:
            print("DEVIR GECERSIZ:", why)
            return 1
        chosen = result.alternatives[0]
    else:
        match = [a for a in result.alternatives if a.id == args.alternative]
        if not match:
            print(f"HATA: '{args.alternative}' alternatifi yok (mevcut: {[a.id for a in result.alternatives]})")
            return 1
        chosen = match[0]
    patch = selection_patch(chosen, ctx.get("meta", {}).get("north_angle"))
    errs = check_patch(ctx, patch)
    if errs:
        print("PATCH GECERSIZ (check_site):")
        for e in errs:
            print("  -", e)
        return 1
    lines = narrate_alternative(chosen)
    prev = ctx.get("meta", {}).get("north_angle")
    text = f"{chosen.id} secildi" + (" (devredildi: secim ve bedeli bildiriliyor)" if delegated else "") + "\n" + "\n".join(lines)
    text += f"\nKat plani kuzey acisi: {chosen.plan_north_angle:g} derece" + ("" if prev is None else f" (mevcut: {prev:g})")
    allowed = brief_numbers(b["fields"]) | numbers_in("\n".join(lines)) | {f"{chosen.plan_north_angle:g}", f"{chosen.rotation_deg:g}"} | ({f"{prev:g}"} if prev is not None else set())
    bad = unsourced_numbers(text, allowed | numbers_in(chosen.id))
    if bad:
        print("ANLATIM REDDEDILDI (kaynaksiz sayi):", bad)
        return 1
    print(text)
    print("\nPATCH TASLAGI (context.json'a YAZILMADI; normal revizyon akisiyla uygulanir):")
    print(json.dumps(patch, ensure_ascii=False, indent=2))
    append_record(log, "selection", {"alternative": chosen.id, "delegated": delegated, "patch": patch, "brief_sha": b["sha"]}, _sha(ctx_path), text=text, allowed_numbers=allowed | numbers_in(chosen.id))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("guide")
    p = sub.add_parser("phase")
    p.add_argument("context")
    p.add_argument("--provide-site", choices=("evet", "hayir"), required=True)
    pb = sub.add_parser("brief")
    pb.add_argument("action", choices=("propose", "approve", "show"))
    pb.add_argument("context")
    pb.add_argument("--by", choices=("dil_modeli", "kullanici"))
    pb.add_argument("--json")
    for name in ("study", "select"):
        q = sub.add_parser(name)
        q.add_argument("context")
        if name == "select":
            q.add_argument("--alternative")
            q.add_argument("--delegate", action="store_true")
    args = ap.parse_args(argv)
    if args.cmd == "guide":
        print(GUIDE)
        return 0
    if args.cmd == "phase":
        return cmd_phase(args)
    if args.cmd == "brief":
        if args.action == "propose":
            if not args.by or not args.json:
                print("HATA: propose icin --by ve --json gerekir.")
                return 2
            return cmd_brief_propose(args)
        return {"approve": cmd_brief_approve, "show": cmd_brief_show}[args.action](args)
    return {"study": cmd_study, "select": cmd_select}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
