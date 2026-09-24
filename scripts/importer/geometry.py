"""2B vektor yardimcilari - importer modulu icinde izole; walls/geometry.py
KASITLI olarak import ETMEZ (o dosya "duvar modulu icinde izole" der,
DEV-013 bu izolasyonu bozmadan kendi kucuk kopyasini tutar).
"""
from __future__ import annotations

import math


def vec_sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def vec_add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def vec_scale(a, s):
    return (a[0] * s, a[1] * s)


def vec_len(a):
    return math.hypot(a[0], a[1])


def vec_norm(a):
    length = vec_len(a)
    if length == 0:
        return (0.0, 0.0)
    return (a[0] / length, a[1] / length)


def vec_perp(a):
    return (-a[1], a[0])


def project_s(point, origin, direction) -> float:
    return (point[0] - origin[0]) * direction[0] + (point[1] - origin[1]) * direction[1]


def angle_between_deg(d1, d2) -> float:
    """Iki (norm ALINMAMIS) yon vektoru arasindaki, YONE duyarsiz aci
    (derece). Ters yonlu (180 derece) ayni RAIL cifti sayilir - iki paralel
    cizgi ayni ekranda ZIT yonde cizilmis olabilir."""
    n1, n2 = vec_norm(d1), vec_norm(d2)
    dot = max(-1.0, min(1.0, n1[0] * n2[0] + n1[1] * n2[1]))
    angle = math.degrees(math.acos(abs(dot)))
    return angle
