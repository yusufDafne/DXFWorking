"""Vaziyet paftasi ve bagimsiz DXF cikti (DEV-084). `pafta::Sheet` + `northarrow::NorthArrow` TUKETIR; context'e YAZMAZ.

Sozlesme (DEV-081): vaziyette kuzey DAIMA yukaridir. Her pafta iki pusula tasir: sag-ustte vaziyet pusulasi (yukari, 'K'), sol-ustte KAT PLANI pusulasi
(`plan_north_angle` kadar dondurulmus: kat plani paftasinda ok boyle gorunecek). Olcek `SITE_SCALES`tan SECILIR (varsayilan yok)."""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import ezdxf
from ezdxf.enums import TextEntityAlignment
from ezdxf.fonts import fonts

try:
    from ..pafta import CONTENT_PADDING, DEFAULT_FONT, FRAME_GAP, Sheet, add_text, parse_scale_denominator, to_modelspace
    from ..northarrow import NorthArrow
    from ..palette import color_for
    from ..typography import TextStyles
except ImportError:
    from pafta import CONTENT_PADDING, DEFAULT_FONT, FRAME_GAP, Sheet, add_text, parse_scale_denominator, to_modelspace
    from northarrow import NorthArrow
    from palette import color_for
    from typography import TextStyles

try:
    from .parcel import Parcel, VaziyetError
    from .setback import plan_north_angle
except ImportError:
    from parcel import Parcel, VaziyetError  # type: ignore
    from setback import plan_north_angle  # type: ignore

SITE_SCALES = ("1/200", "1/500")          # kok CLAUDE.md: VAZIYET_PLANI -> 1:200 veya 1:500
PRINTED_TEXT_MM = 2.5                     # kagit uzerinde metin yuksekligi (olcege gore modelspace'e cevrilir)
PRINTED_COMPASS_MARGIN_MM = 10.0          # kat plani ok marjiyla ayni (sheet_margin)
LAYERS = ("VAZ-PARSEL", "VAZ-CEKME", "VAZ-YOL", "VAZ-BINA", "VAZ-ALAN")
DASHED_LAYERS = ("VAZ-CEKME", "VAZ-ALAN")
CAPTION_PLAN_COMPASS = "KAT PLANI PUSULASI"


@dataclass
class SiteView:
    label: str                       # pafta adi (antet)
    parcel_polygon: list
    footprint: list                  # bina ayak izi (mm)
    rotation_deg: float
    buildable: list | None = None
    road_edges: tuple = ()
    zone: list | None = None
    info_lines: list = field(default_factory=list)


def ensure_site_layers(doc) -> None:
    if "DASHED" not in doc.linetypes:
        doc.linetypes.add("DASHED", pattern=[750.0, 500.0, -250.0], description="kesikli")
    for name in ("CERCEVE", "METIN"):
        if name not in doc.layers:
            doc.layers.add(name=name, dxfattribs={"color": 7})
    for name in LAYERS:
        layer = doc.layers.get(name) if name in doc.layers else doc.layers.add(name=name)
        layer.rgb = color_for(name)
        if name in DASHED_LAYERS:
            layer.dxf.linetype = "DASHED"


def _bbox(poly):
    xs, ys = [p[0] for p in poly], [p[1] for p in poly]
    return min(xs), min(ys), max(xs), max(ys)


def _closed(msp, pts, layer, shift):
    e = msp.add_lwpolyline([(x + shift[0], y + shift[1]) for x, y in pts], dxfattribs={"layer": layer})
    e.closed = True
    return e


def _outward_normal(a, b):
    ux, uy = b[0] - a[0], b[1] - a[1]
    l = math.hypot(ux, uy)
    return (uy / l, -ux / l)            # CCW parselde sag = dis


def _plan(view: SiteView, scale: str):
    """Pafta icerik olculeri: (genislik, y_alt, y_ust, h, shift). Parsel bbox sol-alti (dx, 0)a oturur; altta bilgi satirlari, ustte pusula bandi."""
    denom = parse_scale_denominator(scale)
    h = to_modelspace(PRINTED_TEXT_MM, denom)
    arrow = NorthArrow(scale)
    x0, y0, x1, y1 = _bbox(view.parcel_polygon)
    text_w = max((fonts.make_font(DEFAULT_FONT, h).text_width(t) for t in view.info_lines), default=0.0)       # bilgi satirlari GERCEK font olcusuyle sigmali
    width = max(x1 - x0, 4 * arrow.extent + 2 * to_modelspace(PRINTED_COMPASS_MARGIN_MM, denom), text_w)
    info_h = (len(view.info_lines) + 1) * 1.8 * h if view.info_lines else 0.0
    margin = to_modelspace(PRINTED_COMPASS_MARGIN_MM, denom)
    need_top = max(0.0, margin + 2 * arrow.extent - CONTENT_PADDING)       # pusula parselin ustune binmesin
    # yol kenari: parsel disinda 4h ofsetli cizgi + etiket -> bbox disina tasabilir
    pad = 6 * h if view.road_edges else 2 * h
    return width, -(info_h) - pad, (y1 - y0) + need_top + pad, h, (-x0, -y0)


def draw_site_view(msp, sheet: Sheet, dx: float, view: SiteView, scale: str):
    """Bir vaziyet paftasini cizer; (pafta genisligi, entity listesi) doner. Tasma `Sheet.draw` icinde denetlenir."""
    parcel = Parcel.from_polygon(view.parcel_polygon)
    ppoly = list(parcel.polygon)
    width, y_bottom, y_top, h, (sx, sy) = _plan(view, scale)
    ox = dx + (width - (_bbox(ppoly)[2] - _bbox(ppoly)[0])) / 2.0          # parsel bbox'i pafta icinde yatay ortala
    shift = (ox + sx, sy)                                                   # sx = -parsel_min_x
    start = len(msp)
    _closed(msp, ppoly, "VAZ-PARSEL", shift)
    if view.buildable:
        _closed(msp, view.buildable, "VAZ-CEKME", shift)
    if view.zone:
        _closed(msp, view.zone, "VAZ-ALAN", shift)
    n = len(ppoly)
    for i, (a, b) in enumerate(parcel.edges()):                             # kenar uzunluklari: tam sayi cm (olcu metni standardi)
        nx, ny = _outward_normal(a, b)
        mid = ((a[0] + b[0]) / 2 + nx * 1.2 * h + shift[0], (a[1] + b[1]) / 2 + ny * 1.2 * h + shift[1])
        add_text(msp, f"{round(math.dist(a, b) / 10):d}", mid, h, "METIN", align=TextEntityAlignment.MIDDLE_CENTER)
    for i in view.road_edges:
        a, b = parcel.edges()[i]
        nx, ny = _outward_normal(a, b)
        off = 4 * h
        pa, pb = (a[0] + nx * off + shift[0], a[1] + ny * off + shift[1]), (b[0] + nx * off + shift[0], b[1] + ny * off + shift[1])
        msp.add_line(pa, pb, dxfattribs={"layer": "VAZ-YOL"})
        add_text(msp, "YOL", ((pa[0] + pb[0]) / 2 + nx * 1.2 * h, (pa[1] + pb[1]) / 2 + ny * 1.2 * h), h, "METIN",
                 align=TextEntityAlignment.MIDDLE_CENTER)
    _closed(msp, view.footprint, "VAZ-BINA", shift)
    # binanin UST yuzunu gosteren kisa ok (yerel +Y yonu = donus kadar saat yonunde)
    fp = view.footprint
    top_mid = ((fp[2][0] + fp[3][0]) / 2, (fp[2][1] + fp[3][1]) / 2)
    th = math.radians(view.rotation_deg)
    tip = (top_mid[0] + 4 * h * math.sin(th), top_mid[1] + 4 * h * math.cos(th))
    msp.add_line((top_mid[0] + shift[0], top_mid[1] + shift[1]), (tip[0] + shift[0], tip[1] + shift[1]), dxfattribs={"layer": "VAZ-BINA"})
    add_text(msp, "UST", (tip[0] + shift[0], tip[1] + shift[1] + 0.8 * h), h, "METIN", align=TextEntityAlignment.MIDDLE_CENTER)
    clear = 6 * h if view.road_edges else 2 * h
    for k, line in enumerate(view.info_lines):                              # bilgi satirlari parselin ALTINDA, soldan hizali
        add_text(msp, line, (dx, -clear - (k + 1) * 1.8 * h), h, "METIN", align=TextEntityAlignment.LEFT)
    arrow = NorthArrow(scale)
    ix0, iy0, ix1, iy1 = sheet.inner_bounds(dx, width, y_bottom, y_top)
    margin = to_modelspace(PRINTED_COMPASS_MARGIN_MM, parse_scale_denominator(scale))
    right = arrow.corner_center(ix1, iy1, margin)
    arrow.draw(msp, right, 0.0)                                                # vaziyet pusulasi: DAIMA yukari
    left = (ix0 + margin + arrow.extent, right[1])
    arrow.draw(msp, left, plan_north_angle(view.rotation_deg))                  # kat plani pusulasi: -B kadar donuk
    add_text(msp, CAPTION_PLAN_COMPASS, (left[0], left[1] - arrow.extent - 0.8 * h), h * 0.8, "METIN", align=TextEntityAlignment.TOP_CENTER)
    entities = list(msp)[start:]
    return width, y_bottom, y_top, entities


def render_site_views(views: list[SiteView], scale: str, meta: dict | None = None):
    """Birden cok vaziyet paftasi (yan yana, dis cizgilerinden bitisik) iceren yeni DXF belgesi doner. `scale` `SITE_SCALES`ten OLMALI."""
    if scale not in SITE_SCALES:
        raise VaziyetError(f"vaziyet olcegi {SITE_SCALES} icinden secilmeli (verilen: {scale!r}); varsayilan yok")
    if not views:
        raise VaziyetError("cizilecek vaziyet gorunumu yok")
    doc = ezdxf.new(dxfversion="R2010")
    doc.header["$INSUNITS"] = ezdxf.units.MM
    TextStyles.from_context(meta or {}).ensure(doc)
    ensure_site_layers(doc)
    msp = doc.modelspace()
    denom = parse_scale_denominator(scale)
    h = to_modelspace(PRINTED_TEXT_MM, denom)
    plans = [_plan(v, scale) for v in views]
    sheet = Sheet(scale, h, [v.label for v in views], [(p[1], p[2]) for p in plans])
    cursor = 0.0
    out = []
    for v, p in zip(views, plans):
        width, y_bottom, y_top, entities = draw_site_view(msp, sheet, cursor, v, scale)
        sheet.draw(msp, cursor, width, y_bottom, y_top, v.label, content_entities=entities)
        out.append({"label": v.label, "dx": cursor, "width": width, "y_bottom": y_bottom, "y_top": y_top})
        cursor += width + 2 * (CONTENT_PADDING + FRAME_GAP)
    return doc, out
