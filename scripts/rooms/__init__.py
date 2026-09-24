"""Validated room geometry views and deterministic room labels."""
from __future__ import annotations

from dataclasses import dataclass

from ezdxf.enums import TextEntityAlignment
try:
    from ..pafta import fit_text_height
    from ..walls.scan import RoomPolygonScanner
except ImportError:
    from pafta import fit_text_height
    from walls.scan import RoomPolygonScanner


class PolygonOps:
    @staticmethod
    def signed_area(polygon: list[list[float]]) -> float:
        return 0.5 * sum(
            polygon[i][0] * polygon[(i + 1) % len(polygon)][1]
            - polygon[(i + 1) % len(polygon)][0] * polygon[i][1]
            for i in range(len(polygon))
        )

    @staticmethod
    def area(polygon: list[list[float]]) -> float:
        return abs(PolygonOps.signed_area(polygon))

    @staticmethod
    def centroid(polygon: list[list[float]]) -> tuple[float, float]:
        signed_area = PolygonOps.signed_area(polygon)
        if abs(signed_area) < 1e-9:
            xs = [point[0] for point in polygon]
            ys = [point[1] for point in polygon]
            return sum(xs) / len(xs), sum(ys) / len(ys)
        factor = 1.0 / (6.0 * signed_area)
        cx = cy = 0.0
        for i, point in enumerate(polygon):
            next_point = polygon[(i + 1) % len(polygon)]
            cross = point[0] * next_point[1] - next_point[0] * point[1]
            cx += (point[0] + next_point[0]) * cross
            cy += (point[1] + next_point[1]) * cross
        return cx * factor, cy * factor

    @staticmethod
    def is_closed(polygon: list[list[float]]) -> bool:
        # Context polygons are implicitly closed by the renderer.
        return len(polygon) >= 3

    @staticmethod
    def has_self_intersection(polygon: list[list[float]]) -> bool:
        def orientation(a, b, c):
            value = (b[1] - a[1]) * (c[0] - b[0]) - (b[0] - a[0]) * (c[1] - b[1])
            return (value > 0) - (value < 0)

        def intersects(a, b, c, d):
            return orientation(a, b, c) != orientation(a, b, d) and orientation(c, d, a) != orientation(c, d, b)

        edges = list(zip(polygon, polygon[1:] + polygon[:1]))
        for index, (a, b) in enumerate(edges):
            for other_index, (c, d) in enumerate(edges):
                if other_index <= index or other_index in {index - 1, index + 1}:
                    continue
                if index == 0 and other_index == len(edges) - 1:
                    continue
                if intersects(a, b, c, d):
                    return True
        return False


@dataclass(frozen=True)
class Room:
    id: str
    name: str
    area_m2: float
    polygon: list[list[float]]
    layer: str = "METIN"

    @classmethod
    def from_context(cls, data: dict, units: str = "mm") -> "Room":
        room = cls(
            id=data["id"],
            name=data["name"],
            area_m2=float(data["area_m2"]),
            polygon=data["polygon"],
            layer=data.get("layer", "METIN"),
        )
        if not PolygonOps.is_closed(room.polygon) or PolygonOps.area(room.polygon) <= 0:
            raise ValueError(f"Invalid room polygon: {room.id}")
        if PolygonOps.has_self_intersection(room.polygon):
            raise ValueError(f"Self-intersecting room polygon: {room.id}")
        unit_factor = 1_000_000.0 if units == "mm" else 1.0
        calculated_area_m2 = PolygonOps.area(room.polygon) / unit_factor
        if round(calculated_area_m2, 1) != round(room.area_m2, 1):
            raise ValueError(f"Room area mismatch: {room.id}")
        return room

    def centroid(self) -> tuple[float, float]:
        return PolygonOps.centroid(self.polygon)


# --- Mahal etiketi bicim sabitleri (kullanici sartnamesi, bkz. DEV-008) ---
# Etiket 3 satirdir: mahal adi (BLOK) / kat kodu + mahal no / alan.
ROOM_LABEL_NAME_FACTOR = 1.0      # 1. satir: mahal adi - en buyuk
ROOM_LABEL_META_FACTOR = 0.78     # 2. ve 3. satir: kod ve alan
ROOM_LABEL_LINE_GAP = 0.40        # satir arasi bosluk (ana yuksekligin orani)
ROOM_LABEL_MARGIN = 200.0         # oda kenarindan birakilan pay
ROOM_LABEL_MIN_HEIGHT = 55.0      # okunabilirlik tabani

# --- Mahal etiketi BLOK+ATTRIB tanimi (DEV-018, rev-14) ---
# Uc satir da ATTDEF olarak NOMINAL_HEIGHT'a gore konumlanir; INSERT
# scale = fitted_height / NOMINAL_HEIGHT verildiginde, ATTDEF konumlari ve
# yukseklikleri dogrusal olceklenir ve eski duz-TEXT ciziminin URETTIGI
# MUTLAK KONUMLARLA BIREBIR ORTUSUR (bkz. modul CLAUDE.md "blok kanitı").
ROOM_LABEL_BLOCK_NAME = "MAHAL_ETIKET"
ROOM_LABEL_ATTDEF_TAGS = ("MAHAL_ADI", "MAHAL_KOD", "ALAN")
ROOM_LABEL_NOMINAL_HEIGHT = 100.0


def ensure_room_label_block(doc, layer: str = "METIN", style_name: str | None = None):
    """Mahal etiketi blok TANIMINI belgeye bir kere kaydeder (idempotent;
    `FurnitureBlocks.ensure` ile ayni desen). Ikinci cagrida stil/layer
    parametreleri yok sayilir - proje boyunca tek bir sabit stil kullanilir
    (`generate_dxf.py` her katta ayni `room_label_style`i verir)."""
    if ROOM_LABEL_BLOCK_NAME in doc.blocks:
        return doc.blocks.get(ROOM_LABEL_BLOCK_NAME)
    block = doc.blocks.new(name=ROOM_LABEL_BLOCK_NAME)
    factors = (ROOM_LABEL_NAME_FACTOR, ROOM_LABEL_META_FACTOR, ROOM_LABEL_META_FACTOR)
    height = ROOM_LABEL_NOMINAL_HEIGHT
    total = height * (sum(factors) + ROOM_LABEL_LINE_GAP * (len(factors) - 1))
    cursor = total / 2.0
    for tag, factor in zip(ROOM_LABEL_ATTDEF_TAGS, factors):
        line_height = factor * height
        attribs = {"layer": layer, "height": line_height}
        if style_name:
            attribs["style"] = style_name
        attdef = block.add_attdef(tag, dxfattribs=attribs)
        attdef.set_placement((0.0, cursor - line_height / 2.0),
                              align=TextEntityAlignment.MIDDLE_CENTER)
        cursor -= line_height + ROOM_LABEL_LINE_GAP * height
    return block


class RoomLabeler:
    """Mahal etiketi: 3 satirli blok (ad / kat kodu-mahal no / alan).

    Etiket, oda poligonunun centroid'ine ORTALANIR ve oda kutusuna hem
    GENISLIK hem YUKSEKLIK bakimindan sigacak sekilde olceklenir. Onceki
    surum tek satirdi ve yalnizca genislige bakiyordu; 3 satirda yukseklik
    kontrolu olmadan kucuk mahallerde (WC, hol) etiket odadan tasardi.
    """

    @staticmethod
    def room_code(room: "Room | dict", floor_code: str = "") -> str:
        """Kat kodu + mahal no (orn. 'ZK-04'). Biri eksikse var olan
        dondurulur; ikisi de yoksa bos string (satir cizilmez)."""
        data = room if isinstance(room, dict) else room.__dict__
        number = str(data.get("no", "") or "").strip()
        code = str(floor_code or "").strip()
        if code and number:
            return f"{code}-{number}"
        return number or code

    @staticmethod
    def lines(room: "Room | dict", floor_code: str = "") -> list[tuple[str, float]]:
        """(metin, yukseklik_carpani) ciftleri. Bos satirlar cagiran tarafta
        elenir."""
        data = room if isinstance(room, dict) else room.__dict__
        # "Mahal ismi blok olarak islensin" -> BUYUK HARF.
        # context.json ASCII oldugu icin duz .upper() guvenlidir; Turkce
        # karakterli ad eklenirse (i -> I sorunu) bu nokta gozden gecirilmeli.
        name = str(data["name"]).upper()
        area = f"{float(data['area_m2']):.1f} m2"
        return [
            (name, ROOM_LABEL_NAME_FACTOR),
            (RoomLabeler.room_code(data, floor_code), ROOM_LABEL_META_FACTOR),
            (area, ROOM_LABEL_META_FACTOR),
        ]

    @staticmethod
    def content(room: "Room | dict", floor_code: str = "") -> str:
        """Etiketin duz metin karsiligi (rapor/test icin)."""
        return "\n".join(text for text, _ in RoomLabeler.lines(room, floor_code) if text)

    @staticmethod
    def _block_height(lines: list[tuple[str, float]], height: float) -> float:
        if not lines:
            return 0.0
        factors = sum(factor for _, factor in lines)
        return height * (factors + ROOM_LABEL_LINE_GAP * (len(lines) - 1))

    @staticmethod
    def _fit(lines: list[tuple[str, float]], available_width: float,
             available_height: float, max_height: float, font: str | None = None) -> float:
        """Hem genislige hem yukseklige sigan en buyuk ana metin yuksekligi.

        Genislik icin her satir KENDI carpaniyla olculur: carpani 0.78 olan
        bir satir, ana yukseklik h iken 0.78*h yuksekliginde cizilir."""
        candidates = [max_height]
        if available_width > 0:
            for text, factor in lines:
                if not text or factor <= 0:
                    continue
                # max_height cok buyuk, min_height 0 verilerek HAM sigan
                # yukseklik alinir; kirpmayi asagida topluca yapariz.
                fitted = (fit_text_height(text, available_width, 1e9, 0.0, font)
                          if font else fit_text_height(text, available_width, 1e9, 0.0))
                candidates.append(fitted / factor)
        if available_height > 0 and lines:
            denominator = (sum(factor for _, factor in lines)
                           + ROOM_LABEL_LINE_GAP * (len(lines) - 1))
            if denominator > 0:
                candidates.append(available_height / denominator)
        return max(ROOM_LABEL_MIN_HEIGHT, min(candidates))

    @staticmethod
    def draw(msp, room: "Room | dict", max_text_height: float, units: str = "mm",
             floor_code: str = "", style_name: str | None = None,
             font: str | None = None) -> None:
        data = room if isinstance(room, dict) else room.__dict__
        Room.from_context(data, units)
        polygon = data["polygon"]
        center_x, center_y = PolygonOps.centroid(polygon)
        xs = [point[0] for point in polygon]
        ys = [point[1] for point in polygon]
        available_width = max(0.0, max(xs) - min(xs) - 2 * ROOM_LABEL_MARGIN)
        available_height = max(0.0, max(ys) - min(ys) - 2 * ROOM_LABEL_MARGIN)

        lines = [(text, factor) for text, factor in RoomLabeler.lines(data, floor_code) if text]
        if not lines:
            return
        height = RoomLabeler._fit(lines, available_width, available_height,
                                  max_text_height, font)
        layer = data.get("layer", "METIN")
        center = (center_x, center_y)

        if len(lines) == len(ROOM_LABEL_ATTDEF_TAGS):
            # Standart 3 satirlik durum (kat kodu VE mahal no mevcut): tek
            # secilebilir INSERT + duzenlenebilir ATTRIB (DEV-018).
            RoomLabeler._draw_block(msp, lines, center, height, layer, style_name)
        else:
            # Nadir kenar durumu: kat kodu VE mahal no'nun ikisi de eksik ->
            # 2 (veya daha az) satir. Blok 3 ATTDEF icin sabit yerlesimle
            # tanimlandigi icin bu durumda eski duz-TEXT cizimine dusulur;
            # aksi halde bos ortadaki satir gorsel bosluk birakirdi.
            RoomLabeler._draw_raw(msp, lines, center, height, layer, style_name)

    @staticmethod
    def _draw_block(msp, lines: list[tuple[str, float]], center: tuple[float, float],
                     height: float, layer: str, style_name: str | None) -> None:
        doc = msp.doc
        ensure_room_label_block(doc, layer=layer, style_name=style_name)
        scale = height / ROOM_LABEL_NOMINAL_HEIGHT
        insert = msp.add_blockref(
            ROOM_LABEL_BLOCK_NAME, center,
            dxfattribs={"layer": layer, "xscale": scale, "yscale": scale},
        )
        values = {tag: text for tag, (text, _) in zip(ROOM_LABEL_ATTDEF_TAGS, lines)}
        insert.add_auto_attribs(values)
        for attrib in insert.attribs:
            attrib.dxf.layer = layer

    @staticmethod
    def _draw_raw(msp, lines: list[tuple[str, float]], center: tuple[float, float],
                   height: float, layer: str, style_name: str | None) -> None:
        center_x, center_y = center
        cursor = center_y + RoomLabeler._block_height(lines, height) / 2.0
        for text, factor in lines:
            line_height = factor * height
            attribs = {"layer": layer, "height": line_height}
            if style_name:
                attribs["style"] = style_name
            entity = msp.add_text(text, dxfattribs=attribs)
            entity.set_placement((center_x, cursor - line_height / 2.0),
                                 align=TextEntityAlignment.MIDDLE_CENTER)
            cursor -= line_height + ROOM_LABEL_LINE_GAP * height


# Bu modulun CONTEXT SOZLESMESI surumu (DEV-020). KOD surumu DEGILDIR:
# yalnizca bu modulun context.json'dan OKUDUGU alanlar degistiginde artar;
# refactor artirmaz. Bkz. scripts/version.py
CONTRACT_VERSION = "1.0"

__all__ = ["PolygonOps", "Room", "RoomLabeler", "RoomPolygonScanner",
           "ensure_room_label_block", "ROOM_LABEL_BLOCK_NAME",
           "ROOM_LABEL_ATTDEF_TAGS", "ROOM_LABEL_NOMINAL_HEIGHT"]
