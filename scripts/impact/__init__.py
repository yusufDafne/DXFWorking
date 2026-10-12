"""Revizyon ETKI ALANI raporu (DEV-068, v1): bir degisikligin dokundugu elemanlardan, etkilenen eleman kumesi.

SALT OKUNUR ve TURETILMISTIR: context.json'a hicbir sey yazmaz, DXF cizmez, patch uretmez ("minimal patch plani" kapsam
disidir: sistemde patch dili yok). Cevap "bu eleman degisirse HANGI elemanlara bakmaliyiz" sorusudur; hukum vermez.

Dugum = (kat kimligi, tur, id) - kimlikler katlar arasi tekrar eder (160 kimligin 123'u), bu yuzden kat zorunludur.
Kenarlar iki kaynaktan gelir ve ikisi de ACIK listedir (sessiz kayit yok):
  * REFERENCE_FIELDS - sema alan adlariyla bildirilen kimlik basvurulari (openings[].wall_id ...); `doc_check` #17 sema ile ortusmesini denetler.
  * EDGE_CLASSES - geometrik/iliskisel siniflar; her sinifin yayilip yayilmadigi (`propagates`) bildirilir.
Yeni esik/tolerans SAYISI YOKTUR: yalniz `spatial` ve `collision` sabitleri kullanilir; `depth` bir SUNUM parametresidir.
Kapsam raporu (`coverage`) kapsam disini ve bagsiz elemanlari adiyla soyler: "etkilenen yok" ile "bakilamadi" ayni sey degildir.
"""
from __future__ import annotations

from .graph import (CONTRACT_VERSION, DERIVED_OUTPUTS, EDGE_CLASSES, FLOOR_LIST_KEY, IMPACT_FLOOR_EXEMPT, IMPACT_IGNORED_FIELDS,
                    KINDS, REFERENCE_FIELDS, UNIT_FIELDS, Graph, ImpactError, Node, build_graph)
from .report import DiffReport, ImpactReport, blast_radius, coverage, diff_report, format_report, touched_from_diff

__all__ = [
    "CONTRACT_VERSION", "Node", "Graph", "ImpactError", "ImpactReport", "KINDS", "FLOOR_LIST_KEY", "REFERENCE_FIELDS",
    "UNIT_FIELDS", "EDGE_CLASSES", "DERIVED_OUTPUTS", "IMPACT_IGNORED_FIELDS", "IMPACT_FLOOR_EXEMPT",
    "DiffReport", "format_report", "build_graph", "blast_radius", "touched_from_diff", "diff_report", "coverage",
]
