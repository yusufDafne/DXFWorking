"""Mevcut cikti -> Finding adaptoru (DEV-060, 'strangler').

v1 BILINCLI olarak validate.py'nin STDOUT'unu ayristirir: check_* fonksiyonlarinin cagri
yerlerini (arguman secimi, filtreler) yeniden yazmak rev-13 kopya-ayrisma desenini dogururdu;
stdout ayristirmasi validate.py ile PARITE'yi yapi geregi saglar. Sinir: yalniz KATEGORI bilinir
(sartname/mimari/merdiven...), fonksiyon bilinmez -> veche kimligi 'legacy.<kategori>'. Fonksiyon
duzeyinde veche (DEV-061) kayitli CheckAdapter ile gelir.
"""
from __future__ import annotations

import re

from .findings import make_key, quoted_ids
from .model import Finding

_LINE = re.compile(r"^UYARI \((?P<cat>[^)]+)\): (?:\[(?P<floor>[^\]]+)\] )?(?P<msg>.*)$")


def parse_validate_output(text: str) -> list[Finding]:
    """validate.py stdout'undaki 'UYARI (kategori): [kat] mesaj' satirlari -> Finding listesi."""
    findings: list[Finding] = []
    for line in text.splitlines():
        m = _LINE.match(line.rstrip())
        if not m:
            continue
        facet_id = "legacy." + re.sub(r"[^a-z0-9_]", "_", m.group("cat").lower())
        floor, msg = m.group("floor"), m.group("msg")
        elements = quoted_ids(msg)
        findings.append(Finding(key=make_key(facet_id, floor, elements, msg), facet_id=facet_id,
                                floor_id=floor, message=msg, elements=elements))
    return findings


def adapt_warnings(facet_id: str, floor_id: str | None, messages: list[str]) -> list[Finding]:
    """Bir veche icin ham uyari metinlerini Finding'e sarar (yalniz UYARI kanali)."""
    out = []
    for msg in messages:
        elements = quoted_ids(msg)
        out.append(Finding(key=make_key(facet_id, floor_id, elements, msg), facet_id=facet_id,
                           floor_id=floor_id, message=msg, elements=elements))
    return out
