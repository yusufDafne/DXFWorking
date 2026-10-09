#!/usr/bin/env python3
"""Diyalog koprusu (DEV-064): operatorun kullaniciyla konusmasini SABLONDAN uretir ve KAYDA baglar.

  guide                      diyalog sozlesmesini yazar (operator docs/development'i okuyamaz; sozlesme burada)
  brief --level sade|mimar   ilk mesaj: en cok 3 konu (5 parcali iskelet) + diger notlar + bakilamayan bakis acilari
         [--mode sor|devret] [--before onceki.json] [--intent eleman,eleman] [--context context.json]
  append --level --mode --key <bulgu anahtari>... --text "..."|--stdin [--rev N]
                             <proje>/dialogue.jsonl'e EKLEME-YALNIZ kayit; metindeki KAYNAKSIZ sayi varsa REDDEDER
  verify [--dialogue yol]    reviewer: kayitlardaki her sayi ilgili bulgudan geliyor mu (context_sha256 eslesenler)

`validate.py` DEGISMEZ; bulgular onun stdout'undan (`parse_validate_output`) okunur. Cikis: 0 tamam, 1 hata/kaynaksiz sayi,
2 kullanim hatasi, 3 seviye sorulmamis.
"""
from __future__ import annotations

import argparse
import datetime
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from reasoning import (ExplainError, allowed_numbers_for, append_dialogue, build_coverage,  # noqa: E402
                       coverage_sentence, load_registry, match_smells, narrate, parse_validate_output, read_dialogue,
                       select_topics, validate_record, verify_numbers)
from reasoning import explain  # noqa: E402

DEFAULT_CONTEXT = HERE.parent / "context.json"
GUIDE = """DIYALOG SOZLESMESI (DEV-048 / DEV-064)
1. Seviye: ilk bulgu sunulacagi anda BIR KEZ sor: "%s" Cevap oturum bilgisidir, context.json'a YAZILMAZ.
2. Her konu bes parca, bu sirayla: ne goruyoruz -> neden onemli -> en cok 3 secenek ve bedeli -> onerim -> karar sizin.
3. Ilk mesajda en cok 3 konu; gerisi "diger notlar - ister misiniz?". Ayni kok nedene bagli (ozdes kat) uyarilar TEK konu.
4. SAYI UYDURMA: soyledigin her sayi bulgunun olcumunden gelir. Serbest metinde sayi yazarsan `append` reddeder.
   Yonetmelik rakamini kaynaksiz "kesin" sunma. "Yapilamaz" deme: "yapilir, su bedelle".
5. Bakilamayan bakis acisini (veri eksik) ve henuz olculmeyenleri ADIYLA soyle; "temiz" ile "bakilmadi" ayni sey degildir.
6. Kullanici karari devredebilir ("sen karar ver" -> --mode devret): onerilen uygulanir, secim/bedel/reddedilenler sonradan
   bildirilir. Ciddi (siddet yuksek) bulguda devir olsa bile SOR.
7. Soylediklerini `append` ile <proje>/dialogue.jsonl'e kaydet; reviewer `verify` ile sayilari denetler.
8. Yeni bir ilke kesfedersen merkezi dokumana yazamazsin: kullaniciya bildir (vaka -> ilke -> veche, sistem gelistirme oturumunda).
""" % explain.LEVEL_QUESTION


def run_validate(context: Path) -> str:
    proc = subprocess.run([sys.executable, str(HERE / "validate.py"), str(context)], capture_output=True, text=True, timeout=600)
    return proc.stdout + proc.stderr


def current_findings(context: Path):
    return parse_validate_output(run_validate(context))


def cmd_brief(args) -> int:
    if not args.level:
        print(explain.LEVEL_QUESTION)
        print("(Cevabi --level sade|mimar olarak ver. Bu soru yalniz ilk bulguda bir kez sorulur.)")
        return 3
    context_path = Path(args.context)
    context = json.loads(context_path.read_text(encoding="utf-8"))
    registry, load_errors = load_registry()
    for err in load_errors:
        print("UYARI (kayit):", err)
    findings = current_findings(context_path)
    before = current_findings(Path(args.before)) if args.before else None
    intent = tuple(x for x in (args.intent or "").split(",") if x)
    shown, rest = select_topics(findings, registry.facets, before, intent)
    print(f"[Seviye: {args.level}; mod: {args.mode}]")
    if not shown:
        print("Sunulacak bir konu yok (kayitli uyari bulunmuyor).")
    keys_out = []
    for n, topic in enumerate(shown, 1):
        nar = narrate(topic, registry.facets, registry.remedies, level=args.level, mode=args.mode)
        tag = " [YAN ETKI]" if topic.side_effect else ""
        print(f"\n--- Konu {n}/{len(shown)}{tag} ---\n{nar.text()}")
        keys_out.append(list(nar.finding_keys))
    for smell, parts in match_smells(shown, registry.smells):
        print(f"\n(Kok neden: '{smell.title_tr}' - {smell.root_cause_tr})")
    if rest:
        print(f"\nDiger notlar: {len(rest)} konu daha var - gormek ister misiniz?")
    cov = build_coverage(registry, context)
    blocked = sorted({(registry.facets[e.facet_id].title_tr, e.reason) for e in cov.entries
                      if e.state == "kosamadi" and e.facet_id in registry.facets})
    sentence = coverage_sentence(blocked, [registry.facets[i].title_tr for i in cov.unmeasured if i in registry.facets])
    if sentence:
        print("\n" + sentence)
    print("\nKAYIT ANAHTARLARI (append --key icin):")
    print(json.dumps(keys_out, ensure_ascii=False))
    return 0


def _default_rev(project: Path) -> int | None:
    req = project / "requests.jsonl"
    if not req.exists():
        return None
    lines = [l for l in req.read_text(encoding="utf-8").splitlines() if l.strip()]
    return json.loads(lines[-1]).get("rev") if lines else None


def cmd_append(args) -> int:
    context_path = Path(args.context)
    project = context_path.parent
    dialogue = Path(args.dialogue) if args.dialogue else project / "dialogue.jsonl"
    text = sys.stdin.read() if args.stdin else (args.text or "")
    rev = args.rev if args.rev is not None else _default_rev(project)
    if rev is None:
        print("HATA: rev bilinmiyor (--rev ver ya da requests.jsonl olsun).")
        return 2
    findings = {f.key: f for f in current_findings(context_path)}
    missing = [k for k in args.key if k not in findings]
    if missing:
        print("HATA: guncel bulgular arasinda olmayan anahtar:", missing)
        return 1
    registry, _ = load_registry()
    allowed = allowed_numbers_for([findings[k] for k in args.key], registry.facets)
    rec = {"rev": rev, "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
           "context_sha256": explain.context_sha256(context_path), "finding_keys": list(args.key),
           "text": text, "mode": args.mode, "level": args.level}
    try:
        append_dialogue(dialogue, rec, allowed)
    except ExplainError as exc:
        print("REDDEDILDI:", exc)
        return 1
    print(f"Kaydedildi: {dialogue} (rev-{rev}, {len(args.key)} bulgu)")
    return 0


def cmd_verify(args) -> int:
    context_path = Path(args.context)
    dialogue = Path(args.dialogue) if args.dialogue else context_path.parent / "dialogue.jsonl"
    records = read_dialogue(dialogue)
    if not records:
        print("dialogue.jsonl yok ya da bos - denetlenecek anlati yok.")
        return 0
    sha = explain.context_sha256(context_path)
    findings = {f.key: f for f in current_findings(context_path)}
    registry, _ = load_registry()
    bad = unverifiable = 0
    for i, rec in enumerate(records, 1):
        errs = validate_record(rec)
        if errs:
            print(f"#{i}: bicim hatasi: {errs}")
            bad += 1
            continue
        if rec["context_sha256"] != sha or any(k not in findings for k in rec["finding_keys"]):
            print(f"#{i} (rev-{rec['rev']}): DOGRULANAMADI - baglam sonradan degismis ya da bulgu artik yok")
            unverifiable += 1
            continue
        offending = verify_numbers(rec["text"], allowed_numbers_for([findings[k] for k in rec["finding_keys"]], registry.facets))
        if offending:
            print(f"#{i} (rev-{rec['rev']}): KAYNAKSIZ SAYI {offending}")
            bad += 1
        else:
            print(f"#{i} (rev-{rec['rev']}): tamam")
    print(f"Ozet: {len(records)} kayit, {bad} hatali, {unverifiable} dogrulanamadi.")
    return 1 if bad else 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("guide")
    for name in ("brief", "append", "verify"):
        p = sub.add_parser(name)
        p.add_argument("--context", default=str(DEFAULT_CONTEXT))
        if name != "verify":
            p.add_argument("--level", choices=explain.LEVELS)
            p.add_argument("--mode", choices=explain.MODES, default="sor")
        if name == "brief":
            p.add_argument("--before")
            p.add_argument("--intent")
        if name == "append":
            p.add_argument("--key", action="append", default=[], required=True)
            p.add_argument("--text")
            p.add_argument("--stdin", action="store_true")
            p.add_argument("--rev", type=int)
        if name in ("append", "verify"):
            p.add_argument("--dialogue")
    args = ap.parse_args(argv)
    if args.cmd == "guide":
        print(GUIDE)
        return 0
    if args.cmd == "append" and (not args.level or not (args.text or args.stdin)):
        print("HATA: append icin --level ve --text/--stdin gerekir.")
        return 2
    return {"brief": cmd_brief, "append": cmd_append, "verify": cmd_verify}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
