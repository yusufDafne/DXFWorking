"""Tefris YERLESIMI.

Bu, katalogdan farkli olarak PROJE VERISIDIR: hangi tipten, nereye, hangi
donme ile. context.json'daki `floors[].furniture[]` girdilerinden gelir.
"""
from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True)
class FurnitureItem:
    """Bir tefris YERLESIMI - proje verisidir, context.json'dan gelir."""

    id: str
    type: str
    position: tuple[float, float]
    rotation: float = 0.0

    @classmethod
    def from_context(cls, data: dict) -> "FurnitureItem":
        return cls(
            id=data["id"],
            type=data["type"],
            position=(float(data["position"][0]), float(data["position"][1])),
            rotation=float(data.get("rotation", 0.0)),
        )

    def translated(self, dx: float) -> "FurnitureItem":
        return FurnitureItem(self.id, self.type,
                             (self.position[0] + dx, self.position[1]), self.rotation)
