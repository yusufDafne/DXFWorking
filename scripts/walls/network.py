"""Duvar agi: kose ve T-kesisimlerinde rail miter/trim cozumu."""
from __future__ import annotations

from .geometry import (
    line_intersection,
    point_on_segment,
    project_s,
    round_point,
    vec_len,
    vec_sub,
)
from .wall import Wall

GAP_EPSILON = 1e-6


class WallNetwork:
    def __init__(self, walls: list[Wall], units: str):
        self.walls = walls
        self.units = units
        self.tol = 1.0 if units == "mm" else 0.001
        self._resolve_joints()

    @classmethod
    def from_context(cls, wall_dicts: list[dict], units: str, catalog=None) -> "WallNetwork":
        from .catalog import WallCatalog

        cat = catalog or WallCatalog()
        walls = [Wall.from_context(w, cat) for w in wall_dicts]
        return cls(walls, units)

    def _resolve_joints(self) -> None:
        endpoint_groups: dict[tuple[float, float], list[tuple[Wall, str]]] = {}
        for w in self.walls:
            for which, pt in (("start", w.start), ("end", w.end)):
                key = round_point(pt, self.units)
                endpoint_groups.setdefault(key, []).append((w, which))

        handled: set[tuple[str, str]] = set()

        for entries in endpoint_groups.values():
            if len(entries) < 2:
                continue
            for i in range(len(entries)):
                for j in range(i + 1, len(entries)):
                    wA, whichA = entries[i]
                    wB, whichB = entries[j]
                    self._miter_corner(wA, whichA, wB, whichB)
            for w, which in entries:
                handled.add((w.id, which))

        for w in self.walls:
            for which, pt in (("start", w.start), ("end", w.end)):
                if (w.id, which) in handled:
                    continue
                for other in self.walls:
                    if other.id == w.id:
                        continue
                    if point_on_segment(pt, other.start, other.end, self.tol):
                        self._trim_stub_at_through(w, which, other)
                        break

    def _miter_corner(self, wA: Wall, whichA: str, wB: Wall, whichB: str) -> None:
        for side in ("pos", "neg"):
            originA, dirA = wA.rail_line(side)
            originB, dirB = wB.rail_line(side)
            inter = line_intersection(originA, dirA, originB, dirB)
            if inter is None:
                continue
            wA.set_trim(side, whichA, project_s(inter, originA, dirA))
            wB.set_trim(side, whichB, project_s(inter, originB, dirB))

    def _trim_stub_at_through(self, stub: Wall, which: str, through: Wall) -> None:
        far_s = stub.endpoint_s("end" if which == "start" else "start")
        far_point = stub.centerline_point(far_s)
        for side in ("pos", "neg"):
            origin, direction = stub.rail_line(side)
            candidates = []
            for t_side in ("pos", "neg"):
                t_origin, t_dir = through.rail_line(t_side)
                inter = line_intersection(origin, direction, t_origin, t_dir)
                if inter is not None:
                    candidates.append(inter)
            if not candidates:
                continue
            best = min(candidates, key=lambda p: vec_len(vec_sub(p, far_point)))
            stub.set_trim(side, which, project_s(best, origin, direction))

    def drawable_rail_segments(self, wall: Wall, side: str, openings: list[dict]):
        s0, s1 = wall.rail_trim[side]
        if s0 > s1:
            s0, s1 = s1, s0

        gaps = []
        for op in openings:
            if op["wall_id"] != wall.id:
                continue
            half = op["width"] / 2.0
            g_start = max(s0, op["position_from_start"] - half)
            g_end = min(s1, op["position_from_start"] + half)
            if g_end > g_start:
                gaps.append((g_start, g_end))
        gaps.sort()

        cursor = s0
        segments = []
        for g_start, g_end in gaps:
            if g_start - cursor > GAP_EPSILON:
                segments.append((cursor, g_start))
            cursor = max(cursor, g_end)
        if s1 - cursor > GAP_EPSILON:
            segments.append((cursor, s1))
        if not gaps:
            segments = [(s0, s1)]

        return [
            (wall.rail_point(side, a), wall.rail_point(side, b))
            for a, b in segments
            if b - a > GAP_EPSILON
        ]


def gaps_for_wall(wall: Wall, openings: list[dict]):
    gaps = []
    for op in openings:
        if op["wall_id"] != wall.id:
            continue
        half = op["width"] / 2.0
        g_start = max(0.0, op["position_from_start"] - half)
        g_end = min(wall.length, op["position_from_start"] + half)
        if g_end > g_start:
            gaps.append((g_start, g_end, op))
    gaps.sort(key=lambda g: g[0])
    return gaps
