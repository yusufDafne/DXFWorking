"""Kolon modulu: parametrik kesit, TARAMA (hatch) ve aks kesisimine oturma.

Tasarim kararlari (kullanici talebi, DEV-010):

- **Kolonlar TARALIDIR.** Tarama deseni ve olcegi DINAMIKTIR
  (`ColumnHatchStyle`), ancak makul bir varsayilani vardir: `ANSI33`,
  olcek `3.0`. Farkli bir desen/olcek istendiginde alt sinif gerekmez,
  farkli bir stil nesnesi verilir.
- **Kolon isimlendirme SIMDILIK KAPALI ama desteklenir.** Kullanici kolonlari
  aks birlesim noktalariyla ifade etmeyi tercih ediyor; bu yuzden
  `ColumnLabelStyle.enabled` varsayilan olarak `False`. Ileride ad istendiginde
  `Column.name` doldurulur ve stil acilir - cizim kodu degismez.
- **Konum uydurulmaz.** Kolon konumu ve kesiti context.json'dan gelir. Bu
  modul aks verisini TUKETIR, aks/duvar/oda sorumlulugunu ustlenmez.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

from ezdxf.enums import TextEntityAlignment

COLUMN_LAYER = "KOLON"
COLUMN_HATCH_LAYER = "KOLON-TARAMA"
COLUMN_TEXT_LAYER = "KOLON-METIN"
COLUMN_RGB = (90, 90, 96)

DEFAULT_HATCH_PATTERN = "ANSI33"
DEFAULT_HATCH_SCALE = 3.0


@dataclass(frozen=True)
class ColumnHatchStyle:
    """Kolon taramasi. Desen ve olcek dinamiktir; asagidakiler varsayilandir."""

    pattern: str = DEFAULT_HATCH_PATTERN
    scale: float = DEFAULT_HATCH_SCALE
    angle: float = 0.0
    layer: str = COLUMN_HATCH_LAYER
    enabled: bool = True

    @classmethod
    def from_context(cls, data: dict | None) -> "ColumnHatchStyle":
        """`meta.column_hatch` verilirse ondan, verilmezse varsayilandan."""
        if not data:
            return cls()
        return cls(
            pattern=str(data.get("pattern", DEFAULT_HATCH_PATTERN)),
            scale=float(data.get("scale", DEFAULT_HATCH_SCALE)),
            angle=float(data.get("angle", 0.0)),
            enabled=bool(data.get("enabled", True)),
        )


@dataclass(frozen=True)
class ColumnLabelStyle:
    """Kolon adi gosterimi. Kullanici su an istemedigi icin varsayilan KAPALI;
    altyapi hazir birakildi (ileriye donuk tasarim)."""

    enabled: bool = False
    height: float = 180.0
    layer: str = COLUMN_TEXT_LAYER

    @classmethod
    def from_context(cls, data: dict | None) -> "ColumnLabelStyle":
        if not data:
            return cls()
        return cls(
            enabled=bool(data.get("enabled", False)),
            height=float(data.get("height", 180.0)),
        )


@dataclass(frozen=True)
class ColumnSection:
    """Kolon kesiti. `shape`: 'rect' veya 'circle'."""

    key: str
    width: float
    depth: float
    shape: str = "rect"

    @property
    def radius(self) -> float:
        return min(self.width, self.depth) / 2.0


DEFAULT_COLUMN_CATALOG: dict[str, ColumnSection] = {
    section.key: section for section in (
        ColumnSection("S30x60", 300.0, 600.0),
        ColumnSection("S40x40", 400.0, 400.0),
        ColumnSection("S40x80", 400.0, 800.0),
        ColumnSection("S50x50", 500.0, 500.0),
        ColumnSection("S60x60", 600.0, 600.0),
        ColumnSection("D40", 400.0, 400.0, "circle"),
        ColumnSection("D50", 500.0, 500.0, "circle"),
    )
}


class ColumnSectionCatalog:
    """Kesit adi -> `ColumnSection`. Veri odakli; alt sinif gerekmez."""

    def __init__(self, sections: dict[str, ColumnSection] | None = None):
        self.sections = dict(sections if sections is not None else DEFAULT_COLUMN_CATALOG)

    def __contains__(self, key: str) -> bool:
        return key in self.sections

    def get(self, key: str) -> ColumnSection:
        if key not in self.sections:
            raise KeyError(
                f"Bilinmeyen kolon kesiti: '{key}'. Katalogdaki kesitler: "
                f"{', '.join(sorted(self.sections))}"
            )
        return self.sections[key]

    def keys(self) -> list[str]:
        return sorted(self.sections)


@dataclass(frozen=True)
class Column:
    """Bir kolon yerlesimi. `position` kolonun MERKEZIDIR.

    `name` opsiyoneldir ve bugun cizilmez (bkz. `ColumnLabelStyle`); kullanici
    kolonlari aks kesisimiyle ifade ediyor. Alan yine de tasinir ki
    isimlendirme istendiginde veri yolu hazir olsun."""

    id: str
    position: tuple[float, float]
    section: ColumnSection
    rotation: float = 0.0
    name: str = ""

    @classmethod
    def from_context(cls, data: dict, catalog: ColumnSectionCatalog) -> "Column":
        if "section" in data:
            section = catalog.get(data["section"])
        else:
            section = ColumnSection(
                key=f"{data['id']}_custom",
                width=float(data["width"]),
                depth=float(data["depth"]),
                shape=str(data.get("shape", "rect")),
            )
        column = cls(
            id=data["id"],
            position=(float(data["position"][0]), float(data["position"][1])),
            section=section,
            rotation=float(data.get("rotation", 0.0)),
            name=str(data.get("name", "") or ""),
        )
        if section.width <= 0 or section.depth <= 0:
            raise ValueError(f"Kolon '{column.id}' kesit olcusu pozitif olmali.")
        return column

    def translated(self, dx: float) -> "Column":
        return replace(self, position=(self.position[0] + dx, self.position[1]))

    def corners(self) -> list[tuple[float, float]]:
        """Donme uygulanmis kose noktalari (dikdortgen kesit icin)."""
        import math

        half_w, half_d = self.section.width / 2.0, self.section.depth / 2.0
        angle = math.radians(self.rotation)
        cos_a, sin_a = math.cos(angle), math.sin(angle)
        cx, cy = self.position
        points = []
        for dx, dy in ((-half_w, -half_d), (half_w, -half_d),
                       (half_w, half_d), (-half_w, half_d)):
            points.append((cx + dx * cos_a - dy * sin_a,
                           cy + dx * sin_a + dy * cos_a))
        return points


def ensure_column_layers(doc, hatch_style: ColumnHatchStyle | None = None,
                         label_style: ColumnLabelStyle | None = None) -> None:
    """Kolon layer'larini hazirlar (`ensure_axis_layer` deseni). Renk koddan
    gelir, context'ten alinmaz."""
    hatch_style = hatch_style or ColumnHatchStyle()
    label_style = label_style or ColumnLabelStyle()
    for name in (COLUMN_LAYER, hatch_style.layer, label_style.layer):
        layer = doc.layers.get(name) if name in doc.layers else doc.layers.add(name=name)
        layer.rgb = COLUMN_RGB


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


__all__ = [
    "COLUMN_HATCH_LAYER",
    "COLUMN_LAYER",
    "COLUMN_TEXT_LAYER",
    "DEFAULT_COLUMN_CATALOG",
    "DEFAULT_HATCH_PATTERN",
    "DEFAULT_HATCH_SCALE",
    "Column",
    "ColumnGrid",
    "ColumnHatchStyle",
    "ColumnLabelStyle",
    "ColumnRenderer",
    "ColumnSection",
    "ColumnSectionCatalog",
    "ensure_column_layers",
]
