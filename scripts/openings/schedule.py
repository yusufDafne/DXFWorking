"""Salt-okunur kapi/pencere cetveli."""
from __future__ import annotations

from .opening import Opening


class OpeningSchedule:
    """Deterministic, read-only schedule rows derived from validated openings."""

    @staticmethod
    def from_openings(openings: list[dict | Opening]) -> list[dict]:
        rows = []
        for opening in openings:
            data = opening.as_dict() if isinstance(opening, Opening) else opening
            rows.append({
                "id": data["id"],
                "type": data["type"],
                "wall_id": data["wall_id"],
                "width": data["width"],
                # rev-13: varyant ve acilim yonu cetvele de girer - gercek bir
                # kapi cetvelinde "tek kanat / cift kanat / surme" ayrimi
                # siparis verisidir.
                "variant": data.get("variant", "single"),
                "swing": data.get("swing", "left"),
                "host_side": data.get("host_side", "pos"),
            })
        return sorted(rows, key=lambda row: (row["type"], row["id"]))
