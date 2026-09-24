"""Mevcut bir DXF'ten duvar adayi cikaran salt-okunur tarayici (DEV-013).

Adi `import` DEGIL `importer`dir - `import` bir Python anahtar kelimesidir
ve gecerli bir paket adi olamaz (bkz. modul CLAUDE.md 'Isim notu').
"""
from .geometry import angle_between_deg
from .scanner import (
    MAX_ANGLE_DEG,
    MAX_THICKNESS,
    MIN_OVERLAP_RATIO,
    MIN_THICKNESS,
    DxfWallScanner,
    ImportReport,
    WallCandidate,
    evaluate_pair,
)

# Bu modulun CONTEXT SOZLESMESI surumu (DEV-020). Bu modul context.json'u
# HIC OKUMAZ (bkz. CLAUDE.md 'Sinir') - o yuzden bu alan pratikte hicbir
# zaman ARTMAYACAKTIR, ama `doc_check.py::check_contract_versions` TUM
# scripts/ modullerinden bunu ISTISNASIZ ister (collision motoru dahi
# tasir); tutarlilik icin uyulur.
CONTRACT_VERSION = "1.0"

__all__ = [
    "CONTRACT_VERSION",
    "MAX_ANGLE_DEG",
    "MAX_THICKNESS",
    "MIN_OVERLAP_RATIO",
    "MIN_THICKNESS",
    "DxfWallScanner",
    "ImportReport",
    "WallCandidate",
    "angle_between_deg",
    "evaluate_pair",
]
