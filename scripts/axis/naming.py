"""Aks etiketleme kurali (DEV-015'in acik karari).

**Karar (rev-13): ara aks `1'` yazilir, `1A` YAZILMAZ.**

Gerekce tercih degil, CATISMA'dir: yatay aks ailesi zaten `A`, `B`, `C` ile
etiketlenir. `1A` etiketi "1 ve A akslarinin kesisimi" gibi okunur ve
`columns.ColumnGrid.on_axis_report` bir kolonu tam olarak bu bicimde (`B2`)
adlandirir. Iki gosterim ayni dizede carpisirdi.

Kural bu yuzden MEKANIK olarak denetlenir: dusey (numerik) aile rakam,
yatay (alfabetik) aile harf kullanir; her ikisi de tek bir kesme isaretiyle
ara aks olabilir.
"""
from __future__ import annotations

import re

from .axis import INTERMEDIATE_SUFFIX

VERTICAL_PATTERN = re.compile(r"^[0-9]+'?$")
HORIZONTAL_PATTERN = re.compile(r"^[A-Z]+'?$")

VERTICAL_FAMILY = "vertical"
HORIZONTAL_FAMILY = "horizontal"


def check_labels(vertical: list[dict], horizontal: list[dict]) -> list[str]:
    """Etiket kurali ihlallerini dondurur (bos liste = temiz)."""
    errors: list[str] = []

    for entry in vertical:
        label = str(entry.get("label", ""))
        if not VERTICAL_PATTERN.match(label):
            errors.append(
                f"Dusey aks etiketi '{label}' kurala uymuyor: dusey akslar "
                f"NUMERIK olmalidir (1, 2, 3...), ara aks icin kesme isareti "
                f"eklenir (2{INTERMEDIATE_SUFFIX}). '1A' gibi bir etiket, "
                f"yatay aks ailesiyle (A, B, C) karisir."
            )

    for entry in horizontal:
        label = str(entry.get("label", ""))
        if not HORIZONTAL_PATTERN.match(label):
            errors.append(
                f"Yatay aks etiketi '{label}' kurala uymuyor: yatay akslar "
                f"ALFABETIK olmalidir (A, B, C...), ara aks icin kesme "
                f"isareti eklenir (B{INTERMEDIATE_SUFFIX})."
            )

    for family, entries in ((VERTICAL_FAMILY, vertical),
                            (HORIZONTAL_FAMILY, horizontal)):
        seen: dict[str, float] = {}
        for entry in entries:
            label = str(entry.get("label", ""))
            if label in seen:
                errors.append(
                    f"Aks etiketi '{label}' {family} ailesinde iki kez "
                    f"kullanilmis ({seen[label]} ve {entry.get('position')})."
                )
            else:
                seen[label] = entry.get("position")

    return errors
