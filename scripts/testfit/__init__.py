"""testfit modulu (DEV-063): deneme yerlestirme SINAVI - 'tipik tefris kumesi bu odaya sigar mi?'

`furniture/` (katalog olculeri) ve `collision/` (kapi sektoru + cakisma politikasi) modullerini TUKETIR, ikisini de DEGISTIRMEZ.
Cizim yapmaz, context'e YAZMAZ; cikti turevdir ve bir cozum onerisi degil SINAV sonucudur (yerlesim karari kullanicinindir).
Ayrim: `furniture/` cizim + katalog, `testfit/` muhakeme (`collision` ayak izi disipliniyle ayni gerekce). Ayrinti: CLAUDE.md.
"""
from __future__ import annotations

from .engine import FitResult, MAX_NODES, Placement, best_cluster, net_room_polygon, try_fit, verify_with_collision
from .library import BEDROOM_CLUSTERS, CLUSTERS_BY_ROOM_TYPE, Cluster
from .measure import (bedroom_capacity, bedroom_double_bed_wardrobe_fits_subjects, bedroom_single_bed_fits_subjects,
                      check_bedroom_double_bed_wardrobe_fits, check_bedroom_single_bed_fits)

# Context sozlesmesi: yalniz eleman sozlukleri (rooms[].polygon/room_type, walls[], openings[]) okur; yeni alan YOK.
CONTRACT_VERSION = "1.0"

__all__ = [
    "CONTRACT_VERSION", "BEDROOM_CLUSTERS", "CLUSTERS_BY_ROOM_TYPE", "Cluster", "FitResult", "Placement", "MAX_NODES",
    "best_cluster", "net_room_polygon", "try_fit", "verify_with_collision", "bedroom_capacity",
    "bedroom_double_bed_wardrobe_fits_subjects", "bedroom_single_bed_fits_subjects",
    "check_bedroom_double_bed_wardrobe_fits", "check_bedroom_single_bed_fits",
]
