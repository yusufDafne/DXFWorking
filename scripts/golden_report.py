#!/usr/bin/env python3
"""Create or compare a semantic DXF report for golden-output checks."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

import ezdxf


def entity_bbox(entity):
    points = []
    for name in ("start", "end", "insert", "center", "defpoint"):
        if entity.dxf.hasattr(name):
            value = getattr(entity.dxf, name)
            points.append((float(value[0]), float(value[1])))
    if entity.dxftype() in {"LWPOLYLINE", "POLYLINE"}:
        try:
            points.extend((float(point[0]), float(point[1])) for point in entity.get_points())
        except (AttributeError, TypeError):
            pass
    if not points:
        return None
    xs, ys = zip(*points)
    return [min(xs), min(ys), max(xs), max(ys)]


def report(path: Path) -> dict:
    document = ezdxf.readfile(path)
    modelspace = document.modelspace()
    types = Counter(entity.dxftype() for entity in modelspace)
    layers = Counter(entity.dxf.layer for entity in modelspace)
    boxes = [box for entity in modelspace if (box := entity_bbox(entity)) is not None]
    if boxes:
        bbox = [min(box[0] for box in boxes), min(box[1] for box in boxes),
                max(box[2] for box in boxes), max(box[3] for box in boxes)]
    else:
        bbox = None
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return {
        "source": str(path),
        "sha256": digest,
        "entity_count": len(modelspace),
        "entity_types": dict(sorted(types.items())),
        "layers": dict(sorted(layers.items())),
        "modelspace_bbox": bbox,
    }


def compare(actual: dict, expected: dict) -> list[str]:
    differences = []
    for key in ("entity_count", "entity_types", "layers", "modelspace_bbox"):
        if actual.get(key) != expected.get(key):
            differences.append(key)
    return differences


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dxf", type=Path)
    parser.add_argument("--write", type=Path, help="Write a semantic golden report")
    parser.add_argument("--compare", type=Path, help="Compare with an existing report")
    args = parser.parse_args()
    actual = report(args.dxf)
    if args.write:
        args.write.write_text(json.dumps(actual, indent=2) + "\n", encoding="utf-8")
    if args.compare:
        expected = json.loads(args.compare.read_text(encoding="utf-8"))
        differences = compare(actual, expected)
        if differences:
            print("Golden differences: " + ", ".join(differences))
            return 1
        print("Golden semantic report matches.")
        return 0
    print(json.dumps(actual, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
