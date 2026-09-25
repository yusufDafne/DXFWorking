"""Kolon layer hazirligi, kontur + tarama cizimi ve kat bazinda kolon kumesi."""
from __future__ import annotations

from ezdxf.enums import TextEntityAlignment

from .column import Column
from .section import ColumnSectionCatalog
from .standard import COLUMN_HATCH_RGB, COLUMN_LAYER, COLUMN_RGB, COLUMN_TEXT_RGB
from .style import ColumnHatchStyle, ColumnLabelStyle

def ensure_column_layers(doc, hatch_style: ColumnHatchStyle | None = None,
                         label_style: ColumnLabelStyle | None = None) -> None:
    """Kolon layer'larini hazirlar (`ensure_axis_layer` deseni). Renk koddan
    gelir, context'ten alinmaz. UC layer ARTIK UC FARKLI tondadir (DEV-030,
    scripts/palette) - eskiden ucu de COLUMN_RGB'yi paylasiyordu."""
    hatch_style = hatch_style or ColumnHatchStyle()
    label_style = label_style or ColumnLabelStyle()
    for name, rgb in (
        (COLUMN_LAYER, COLUMN_RGB),
        (hatch_style.layer, COLUMN_HATCH_RGB),
        (label_style.layer, COLUMN_TEXT_RGB),
    ):
        layer = doc.layers.get(name) if name in doc.layers else doc.layers.add(name=name)
        layer.rgb = rgb


class ColumnRenderer:
    """Kolon konturu + taramasi (+ istenirse adi)."""

    @staticmethod
    def draw(msp, column: Column, hatch_style: ColumnHatchStyle | None = None,
             label_style: ColumnLabelStyle | None = None) -> list:
        hatch_style = hatch_style or ColumnHatchStyle()
        label_style = label_style or ColumnLabelStyle()
        entities = []

        if column.section.shape == "circle":
            entities.append(msp.add_circle(
                column.position, column.section.radius,
                dxfattribs={"layer": COLUMN_LAYER}))
        else:
            outline = msp.add_lwpolyline(column.corners(),
                                         dxfattribs={"layer": COLUMN_LAYER})
            outline.closed = True
            entities.append(outline)

        if hatch_style.enabled:
            hatch = msp.add_hatch(dxfattribs={"layer": hatch_style.layer})
            hatch.set_pattern_fill(hatch_style.pattern, scale=hatch_style.scale,
                                   angle=hatch_style.angle)
            if column.section.shape == "circle":
                hatch.paths.add_edge_path().add_arc(
                    center=column.position, radius=column.section.radius)
            else:
                hatch.paths.add_polyline_path(column.corners(), is_closed=True)
            entities.append(hatch)

        # Isimlendirme bugun KAPALI (kullanici aks kesisimiyle ifade ediyor);
        # veri yolu ve stil hazir, acilmasi tek bayrak.
        if label_style.enabled and column.name:
            text = msp.add_text(column.name,
                                dxfattribs={"layer": label_style.layer,
                                            "height": label_style.height})
            text.set_placement(column.position,
                               align=TextEntityAlignment.MIDDLE_CENTER)
            entities.append(text)

        return entities


class ColumnGrid:
    """Bir kattaki kolon kumesi. Aks verisini TUKETIR; aks uretmez."""

    def __init__(self, columns: list[Column],
                 hatch_style: ColumnHatchStyle | None = None,
                 label_style: ColumnLabelStyle | None = None):
        self.columns = list(columns)
        self.hatch_style = hatch_style or ColumnHatchStyle()
        self.label_style = label_style or ColumnLabelStyle()

    @classmethod
    def from_context(cls, data: list[dict], catalog: ColumnSectionCatalog,
                     hatch_style: ColumnHatchStyle | None = None,
                     label_style: ColumnLabelStyle | None = None) -> "ColumnGrid":
        return cls([Column.from_context(item, catalog) for item in data],
                   hatch_style, label_style)

    def draw(self, msp, dx: float = 0.0) -> list:
        entities = []
        for column in self.columns:
            entities += ColumnRenderer.draw(msp, column.translated(dx),
                                            self.hatch_style, self.label_style)
        return entities

    def on_axis_report(self, vertical_axes: list[dict], horizontal_axes: list[dict],
                       tolerance: float = 1.0) -> list[dict]:
        """Hangi kolon hangi aks kesisimine oturuyor - salt-okunur rapor.
        Kolon konumunu DEGISTIRMEZ; yalnizca raporlar."""
        xs = {axis["label"]: float(axis["position"]) for axis in vertical_axes}
        ys = {axis["label"]: float(axis["position"]) for axis in horizontal_axes}
        rows = []
        for column in self.columns:
            vx = next((label for label, value in xs.items()
                       if abs(value - column.position[0]) <= tolerance), None)
            hy = next((label for label, value in ys.items()
                       if abs(value - column.position[1]) <= tolerance), None)
            rows.append({
                "id": column.id,
                "section": column.section.key,
                "axis": f"{hy}{vx}" if vx and hy else None,
                "on_axis": bool(vx and hy),
                "name": column.name,
            })
        return sorted(rows, key=lambda row: row["id"])
