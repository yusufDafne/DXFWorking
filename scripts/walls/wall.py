"""Tek duvar segmenti: merkez cizgisi + kalinlik -> cift rail (bkz. kok CLAUDE.md)."""
from __future__ import annotations

from .catalog import WallCatalog
from .geometry import vec_add, vec_len, vec_norm, vec_perp, vec_scale, vec_sub


class Wall:
    def __init__(
        self,
        wall_id: str,
        start,
        end,
        thickness: float,
        layer: str,
        *,
        kind: str | None = None,
        catalog: WallCatalog | None = None,
    ):
        self.id = wall_id
        self.start = tuple(start)
        self.end = tuple(end)
        self.layer = layer
        self.kind = kind
        self.thickness = thickness
        if catalog and kind:
            spec = catalog.get(kind)
            if spec:
                self.kind_label = spec.label
                self.structural = spec.structural
            else:
                self.kind_label = kind
                self.structural = False
        else:
            self.kind_label = kind
            self.structural = False

        self.length = vec_len(vec_sub(self.end, self.start))
        self.direction = vec_norm(vec_sub(self.end, self.start))
        self.normal = vec_perp(self.direction)
        self.rail_trim = {"pos": [0.0, self.length], "neg": [0.0, self.length]}

    @classmethod
    def from_context(cls, wall_dict: dict, catalog: WallCatalog | None = None) -> "Wall":
        cat = catalog or WallCatalog()
        thickness, layer, kind = cat.resolve(wall_dict)
        return cls(
            wall_dict["id"],
            wall_dict["start"],
            wall_dict["end"],
            thickness,
            layer,
            kind=kind,
            catalog=cat,
        )

    def rail_origin(self, side: str) -> tuple[float, float]:
        sign = 1.0 if side == "pos" else -1.0
        return vec_add(self.start, vec_scale(self.normal, sign * self.thickness / 2.0))

    def rail_point(self, side: str, s: float) -> tuple[float, float]:
        return vec_add(self.rail_origin(side), vec_scale(self.direction, s))

    def rail_line(self, side: str):
        return self.rail_origin(side), self.direction

    def endpoint_s(self, which: str) -> float:
        return 0.0 if which == "start" else self.length

    def set_trim(self, side: str, which: str, s: float) -> None:
        idx = 0 if which == "start" else 1
        self.rail_trim[side][idx] = s

    def centerline_point(self, s: float) -> tuple[float, float]:
        return vec_add(self.start, vec_scale(self.direction, s))
