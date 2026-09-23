"""Cakisma (clash) denetimi motoru - DEV-019.

**Karar (rev-12):** Cakisma denetimi AYRI BIR MODULDUR, ancak cizim
modullerinin geometrisini BILMEZ. Ayrim aritedir:

- **Arite-1** ("kendi verim gecerli mi": poligon kapali mi, aciklik host
  duvardan genis mi) ILGILI MODULE aittir ve `validate.py::check_*` icinde
  kalir.
- **Arite-2+** ("iki FARKLI eleman ayni yeri mi isgal ediyor") bu motora
  aittir.

Endustri karsiligi: BIM'de modelleme araci kendi disiplinini denetler,
disiplinler arasi clash AYRI bir aractir (Navisworks Clash Detective,
Solibri Model Checker).

**Bagimsizlik nasil korunuyor:** bu paket hicbir cizim modulunu import etmez.
Her modul kendi ayak izini `scripts/<modul>/collision.py::footprints(floor,
context)` ile verir. Boylece **ayak izinin sahibi modul, cakisma kuralinin
sahibi motordur**; sahiplik bolunmez.

Kullanim:

    from collision import check_context
    report = check_context(context)
    if not report.ok:
        for line in report.error_lines():
            print(line)
"""
from __future__ import annotations

from .engine import Clash, CollisionEngine, KIND_CONTAINMENT, KIND_OVERLAP
from .matrix import (
    CONTACT_TOLERANCE,
    CONTAINMENT_TOLERANCE,
    DEFAULT_POLICY,
    CollisionPolicy,
    Policy,
)
from .report import ClashReport
from .scene import COLLISION_EXEMPT, FOOTPRINT_PROVIDERS, Scene, check_context
from .shapes import (
    SECTOR_SEGMENTS,
    TAG_COLUMN,
    TAG_DOOR_SWING,
    TAG_FURNITURE,
    TAG_ROOM,
    TAG_WALL,
    CollisionShape,
    circle_shape,
    polygon_shape,
    rect_shape,
    sector_shape,
    segment_shape,
)

CONTRACT_VERSION = "1.0"

__all__ = [
    "COLLISION_EXEMPT",
    "CONTACT_TOLERANCE",
    "CONTAINMENT_TOLERANCE",
    "CONTRACT_VERSION",
    "DEFAULT_POLICY",
    "FOOTPRINT_PROVIDERS",
    "KIND_CONTAINMENT",
    "KIND_OVERLAP",
    "SECTOR_SEGMENTS",
    "TAG_COLUMN",
    "TAG_DOOR_SWING",
    "TAG_FURNITURE",
    "TAG_ROOM",
    "TAG_WALL",
    "Clash",
    "ClashReport",
    "CollisionEngine",
    "CollisionPolicy",
    "CollisionShape",
    "Policy",
    "Scene",
    "check_context",
    "circle_shape",
    "polygon_shape",
    "rect_shape",
    "sector_shape",
    "segment_shape",
]
