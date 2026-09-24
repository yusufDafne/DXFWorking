"""DXF duvar adayi tarayicisi (DEV-013, Fikir 1). Salt-okunur: hicbir dosyaya
YAZMAZ, context.json'u hic gormez. Bkz. modul CLAUDE.md 'Algoritma'.
"""
from __future__ import annotations

import hashlib
import itertools
from dataclasses import dataclass, field
from pathlib import Path

from .geometry import angle_between_deg, project_s, vec_norm, vec_sub

MAX_ANGLE_DEG = 10.0
MIN_THICKNESS = 40.0
MAX_THICKNESS = 400.0
MIN_OVERLAP_RATIO = 0.5


@dataclass(frozen=True)
class WallCandidate:
    """Iki paralel `LINE`den turetilmis TEK bir duvar adayi. Kendisi ASLA
    context semasina uygun bir 'wall' degildir - `as_wall_dict()` cagirilana
    kadar."""

    index: int
    start: tuple[float, float]
    end: tuple[float, float]
    thickness: float
    confidence: float
    layer: str
    source_handles: tuple[str, str]

    def as_wall_dict(self, id_prefix: str = "import") -> dict:
        """`walls[]` semasiyla BIREBIR ayni sekilde bir sozluk uretir
        (`RoomPolygonScanner.suggest_wall_dicts` ile AYNI sekil). Insan/agent
        bunu inceleyip ONAYLARSA normal talep akisiyla context.json'a
        eklenir - burada OTOMATIK bir birlestirme YOKTUR."""
        return {
            "id": f"{id_prefix}_{self.index}",
            "start": [round(self.start[0], 3), round(self.start[1], 3)],
            "end": [round(self.end[0], 3), round(self.end[1], 3)],
            "thickness": round(self.thickness, 1),
            "layer": self.layer,
        }


@dataclass(frozen=True)
class ImportReport:
    source_path: Path
    source_sha256: str
    candidates: list[WallCandidate] = field(default_factory=list)


def _perpendicular_distance(point, origin, axis_dir) -> float:
    rel = vec_sub(point, origin)
    return abs(rel[0] * axis_dir[1] - rel[1] * axis_dir[0])


def _point_on_segment_at(start, end, s_start, s_end, target_s) -> tuple[float, float]:
    if s_end == s_start:
        return start
    t = (target_s - s_start) / (s_end - s_start)
    return (start[0] + t * (end[0] - start[0]), start[1] + t * (end[1] - start[1]))


def _midpoint(a, b) -> tuple[float, float]:
    return ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)


def evaluate_pair(start1, end1, layer1, handle1,
                   start2, end2, layer2, handle2) -> WallCandidate | None:
    """Iki LINE segmentini degerlendirir; adaylik kosullarindan biri
    gecmezse `None` doner (bkz. modul CLAUDE.md 'Algoritma')."""
    if layer1 != layer2:
        return None

    direction1 = vec_sub(end1, start1)
    direction2 = vec_sub(end2, start2)
    len1 = (direction1[0] ** 2 + direction1[1] ** 2) ** 0.5
    len2 = (direction2[0] ** 2 + direction2[1] ** 2) ** 0.5
    if len1 <= 0 or len2 <= 0:
        return None

    angle = angle_between_deg(direction1, direction2)
    if angle > MAX_ANGLE_DEG:
        return None

    axis_dir = vec_norm(direction1)
    dist_a = _perpendicular_distance(start2, start1, axis_dir)
    dist_b = _perpendicular_distance(end2, start1, axis_dir)
    thickness = (dist_a + dist_b) / 2.0
    if not (MIN_THICKNESS <= thickness <= MAX_THICKNESS):
        return None

    s1a, s1b = 0.0, len1
    s2a = project_s(start2, start1, axis_dir)
    s2b = project_s(end2, start1, axis_dir)
    i1 = (min(s1a, s1b), max(s1a, s1b))
    i2 = (min(s2a, s2b), max(s2a, s2b))
    overlap = max(0.0, min(i1[1], i2[1]) - max(i1[0], i2[0]))
    overlap_ratio = overlap / max(len1, len2)
    if overlap_ratio < MIN_OVERLAP_RATIO:
        return None

    ov_start, ov_end = max(i1[0], i2[0]), min(i1[1], i2[1])
    p1a = _point_on_segment_at(start1, end1, s1a, s1b, ov_start)
    p1b = _point_on_segment_at(start1, end1, s1a, s1b, ov_end)
    p2a = _point_on_segment_at(start2, end2, s2a, s2b, ov_start)
    p2b = _point_on_segment_at(start2, end2, s2a, s2b, ov_end)

    parallel_score = 1.0 - angle / MAX_ANGLE_DEG
    confidence = parallel_score * overlap_ratio

    return WallCandidate(
        index=-1,  # scan() tarafindan sonradan atanir (siralamadan sonra)
        start=_midpoint(p1a, p2a),
        end=_midpoint(p1b, p2b),
        thickness=thickness,
        confidence=confidence,
        layer=layer1,
        source_handles=(handle1, handle2),
    )


class DxfWallScanner:
    """Mevcut bir DXF dosyasindan duvar adaylari cikarir. `ezdxf`i SADECE
    OKUMA icin (`readfile`) kullanir; hicbir dosyaya yazmaz."""

    def scan(self, source_path: str | Path, layers: set[str] | None = None) -> ImportReport:
        import ezdxf

        path = Path(source_path)
        doc = ezdxf.readfile(path)
        msp = doc.modelspace()

        lines = []
        for entity in msp.query("LINE"):
            if layers is not None and entity.dxf.layer not in layers:
                continue
            start = (float(entity.dxf.start[0]), float(entity.dxf.start[1]))
            end = (float(entity.dxf.end[0]), float(entity.dxf.end[1]))
            lines.append((start, end, entity.dxf.layer, entity.dxf.handle))

        candidates = []
        for (s1, e1, l1, h1), (s2, e2, l2, h2) in itertools.combinations(lines, 2):
            candidate = evaluate_pair(s1, e1, l1, h1, s2, e2, l2, h2)
            if candidate is not None:
                candidates.append(candidate)

        candidates.sort(key=lambda c: (-c.confidence, c.source_handles))
        candidates = [
            WallCandidate(index=i, start=c.start, end=c.end, thickness=c.thickness,
                         confidence=c.confidence, layer=c.layer,
                         source_handles=c.source_handles)
            for i, c in enumerate(candidates)
        ]

        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        return ImportReport(source_path=path, source_sha256=digest, candidates=candidates)
