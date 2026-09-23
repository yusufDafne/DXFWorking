"""Tefris plan sembollerinin cizim fonksiyonlari.

Her fonksiyon bir BLOK TANIMI icine, yerel koordinatta cizer. Yerel orijin
(0,0) elemanin SOL-ALT kosesidir; `INSERT` noktasi ve rotasyon merkezi budur.
Yeni bir tefris tipi eklemek icin buraya bir cizim fonksiyonu, `catalog.py`ye
bir katalog satiri eklenir.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - yalnizca tip ipucu
    from .catalog import FurnitureSpec

def _rect(block, x0: float, y0: float, x1: float, y1: float) -> None:
    polyline = block.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
    polyline.closed = True


def _line(block, p1, p2) -> None:
    block.add_line(p1, p2)


def _draw_sofa(block, spec: "FurnitureSpec") -> None:
    width, depth = spec.width, spec.depth
    arm, back = 150.0, 180.0
    _rect(block, 0, 0, width, depth)
    _line(block, (arm, 0), (arm, depth))
    _line(block, (width - arm, 0), (width - arm, depth))
    _line(block, (arm, depth - back), (width - arm, depth - back))
    seats = max(1, spec.options.get("seats", 1))
    seat_width = (width - 2 * arm) / seats
    for index in range(1, seats):
        x = arm + index * seat_width
        _line(block, (x, 0), (x, depth - back))


def _draw_chair(block, spec: "FurnitureSpec") -> None:
    width, depth = spec.width, spec.depth
    _rect(block, 0, 0, width, depth)
    _line(block, (0, depth - 70), (width, depth - 70))


def _draw_table(block, spec: "FurnitureSpec") -> None:
    _rect(block, 0, 0, spec.width, spec.depth)
    inset = 60.0
    if spec.width > 2 * inset and spec.depth > 2 * inset:
        _rect(block, inset, inset, spec.width - inset, spec.depth - inset)


def _draw_bed(block, spec: "FurnitureSpec") -> None:
    width, depth = spec.width, spec.depth
    _rect(block, 0, 0, width, depth)
    pillows = max(1, spec.options.get("pillows", 1))
    margin = 90.0
    pillow_width = (width - margin * (pillows + 1)) / pillows
    for index in range(pillows):
        x0 = margin + index * (pillow_width + margin)
        _rect(block, x0, depth - 520, x0 + pillow_width, depth - 160)
    _line(block, (0, depth - 700), (width, depth - 700))


def _draw_cabinet(block, spec: "FurnitureSpec") -> None:
    """Gardirop / tezgah / dolap: govde + on hat + kapak bolumleri."""
    width, depth = spec.width, spec.depth
    _rect(block, 0, 0, width, depth)
    _line(block, (0, depth * 0.22), (width, depth * 0.22))
    doors = max(1, int(round(width / spec.options.get("door_width", 600.0))))
    for index in range(1, doors):
        x = width * index / doors
        _line(block, (x, depth * 0.22), (x, depth))


def _draw_cooker(block, spec: "FurnitureSpec") -> None:
    width, depth = spec.width, spec.depth
    _rect(block, 0, 0, width, depth)
    radius = min(width, depth) * 0.16
    for fx in (0.28, 0.72):
        for fy in (0.28, 0.72):
            block.add_circle((width * fx, depth * fy), radius)


def _draw_sink(block, spec: "FurnitureSpec") -> None:
    width, depth = spec.width, spec.depth
    _rect(block, 0, 0, width, depth)
    _rect(block, width * 0.08, depth * 0.15, width * 0.62, depth * 0.85)
    block.add_circle((width * 0.35, depth * 0.5), min(width, depth) * 0.06)


def _draw_fridge(block, spec: "FurnitureSpec") -> None:
    width, depth = spec.width, spec.depth
    _rect(block, 0, 0, width, depth)
    _line(block, (0, depth * 0.62), (width, depth * 0.62))
    _line(block, (width * 0.5, 0), (width * 0.5, depth * 0.62))


def _draw_washbasin(block, spec: "FurnitureSpec") -> None:
    width, depth = spec.width, spec.depth
    _rect(block, 0, 0, width, depth)
    block.add_ellipse((width * 0.5, depth * 0.52),
                      major_axis=(width * 0.36, 0), ratio=0.72)
    block.add_circle((width * 0.5, depth * 0.52), min(width, depth) * 0.05)


def _draw_toilet(block, spec: "FurnitureSpec") -> None:
    width, depth = spec.width, spec.depth
    _rect(block, 0, 0, width, depth * 0.28)          # rezervuar
    block.add_ellipse((width * 0.5, depth * 0.62),
                      major_axis=(0, depth * 0.34), ratio=0.62)


def _draw_shower(block, spec: "FurnitureSpec") -> None:
    width, depth = spec.width, spec.depth
    _rect(block, 0, 0, width, depth)
    _line(block, (0, 0), (width, depth))
    _line(block, (0, depth), (width, 0))
    block.add_circle((width * 0.5, depth * 0.5), min(width, depth) * 0.07)


def _draw_bathtub(block, spec: "FurnitureSpec") -> None:
    width, depth = spec.width, spec.depth
    _rect(block, 0, 0, width, depth)
    inset = min(width, depth) * 0.10
    _rect(block, inset, inset, width - inset, depth - inset)
    block.add_circle((width - inset * 3.0, depth * 0.5), min(width, depth) * 0.06)


def _draw_appliance(block, spec: "FurnitureSpec") -> None:
    """Camasir/bulasik makinesi: govde + tambur dairesi."""
    width, depth = spec.width, spec.depth
    _rect(block, 0, 0, width, depth)
    block.add_circle((width * 0.5, depth * 0.5), min(width, depth) * 0.30)


def _draw_simple(block, spec: "FurnitureSpec") -> None:
    _rect(block, 0, 0, spec.width, spec.depth)
