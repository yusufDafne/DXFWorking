"""Etki grafi: dugumler, acik kenar tablolari, `build_graph`. Salt okunur; context'e yazmaz."""
from __future__ import annotations

from typing import NamedTuple

CONTRACT_VERSION = "1.0"

# kat listesi anahtari -> dugum turu. Tamlik kapisi (`doc_check` #17): semadaki `floor` tanimindaki HER liste burada ya da
# IMPACT_FLOOR_EXEMPT icinde gerekcesiyle olmak zorundadir.
FLOOR_LIST_KEY: dict[str, str] = {
    "room": "rooms", "wall": "walls", "opening": "openings", "shaft": "shafts", "stairs": "stairs",
    "furniture": "furniture", "column": "columns", "counter": "counters", "label": "labels",
    "marking": "markings", "level_mark": "level_marks",
}
KINDS: tuple[str, ...] = tuple(FLOOR_LIST_KEY)
IMPACT_FLOOR_EXEMPT: dict[str, str] = {}   # su an her kat listesi dugumdur

# Sema alan adlariyla bildirilen kimlik basvurulari: (sema tanimi, alan, kaynak tur, hedef tur).
REFERENCE_FIELDS: tuple[tuple[str, str, str, str], ...] = (
    ("opening", "wall_id", "opening", "wall"),
    ("stairs", "room_id", "stairs", "room"),
    ("stairs", "exit_door_id", "stairs", "opening"),
    ("counter", "room_id", "counter", "room"),
)
# Birim (daire) bagi: ayri sinif (yayilmaz), bu yuzden REFERENCE_FIELDS disinda.
UNIT_FIELDS: tuple[tuple[str, str], ...] = (("room", "unit_id"), ("shaft", "unit_id"))
# Kimlik gibi gorunen ama kat icinde kenar OLMAYAN alanlar (gerekce zorunlu).
IMPACT_IGNORED_FIELDS: dict[tuple[str, str], str] = {
    ("section", "levels_from"): "Kesit -> cephe basvurusu; ust seviye `sections[]`/`elevations[]` agaci, kat icinde dugum degil "
                                "(kapsam disi, `coverage` bunu soyler).",
}

# Geometrik/iliskisel kenar siniflari. `propagates`: bu kenardan gecerek ETKI ILERLER mi (False ise yalniz 'ilgili' diye listelenir).
EDGE_CLASSES: dict[str, tuple[bool, str]] = {
    "basvuru": (True, "sema alanindaki kimlik basvurusu (REFERENCE_FIELDS); aciklik-duvar kenari yalniz aciklik BOSLUGU parcasini baglar"),
    "duvar_oda_kenari": (True, "duvar, odanin bir kenariyla esdogrusal ve ortusuyor (spatial.wall_edge_overlap); kenar yalniz ORTUSEN duvar parcasini baglar"),
    "duvar_birlesimi": (True, "duvar ucu baska bir duvarin uzerinde (T/L birlesim; spatial.dist_point_segment <= SHARED_EDGE_TOLERANCE_MM)"),
    "kapi_komsu_oda": (True, "aciklik orta noktasina degen oda (spatial.rooms_touching_point)"),
    "saft_komsu_oda": (True, "saftin odayla ortak kenari var (spatial.shared_edge_length > 0)"),
    "icinde": (True, "tefris/kolon ayak izi ya da etiket/kot/isaret konumu odanin icinde"),
    "kapi_acilim": (True, "kapi acilim sektoru tefris/kolon ayak iziyle kesisiyor (collision ayak izleri)"),
    "birim": (False, "ayni `unit_id` (daire) - gevsek bag, yayilmaz"),
    "kat_ikizi": (False, "baska katta ayni tur+kimlik - kimlik eslesmesi, geometri esitligi iddia edilmez; yayilmaz"),
}

# Eleman turu -> bu elemanin DEGISINCE yeniden turetilen ciktilar (modul adi, ne). Modul adlari `doc_check` #17 ile dizinde aranir.
DERIVED_OUTPUTS: dict[str, tuple[tuple[str, str], ...]] = {
    "room": (("rooms", "mahal etiketi ve alan"), ("dimensions", "olcu zinciri ordinatlari"), ("standards", "oran/olcu uyarilari"),
             ("architect", "iliskisel mimari kurallar"), ("testfit", "deneme yerlestirme sinavi")),
    "wall": (("walls", "rail/gonye cizimi"), ("dimensions", "olcu zinciri"), ("sections", "kesit hatti kesisimi"),
             ("collision", "duvar ayak izi")),
    "opening": (("openings", "sembol, aciklik, cetvel"), ("legend", "kapi/pencere cetveli"), ("collision", "kapi acilim sektoru"),
                ("elevations", "cephe acikliklari")),
    "shaft": (("shafts", "saft kontrolleri"),),
    "stairs": (("stairs", "basamak/riht cizimi ve cikis hizasi"),),
    "furniture": (("furniture", "tefris blogu"), ("collision", "tefris ayak izi"), ("testfit", "deneme yerlestirme")),
    "column": (("columns", "kolon cizimi ve aks hizasi"), ("collision", "kolon ayak izi")),
    "counter": (("collision", "tezgah ayak izi yok; yalniz MOBILYA cizimi"),),
    "label": (),
    "marking": (),
    "level_mark": (("levels", "kot isareti"),),
}


class ImpactError(ValueError):
    """Bilinmeyen kat/tur/kimlik: etki alani UYDURULMAZ."""


class Node(NamedTuple):
    floor: str
    kind: str
    id: str

    def __str__(self) -> str:
        return f"{self.floor}/{self.kind}/{self.id}"


Span = tuple[float, float]   # duvar uzerinde [t0, t1] araligi (duvar baslangicindan mesafe, birim = context birimi)


class Graph:
    """Dugumler + kenarlar. Duvar ucundaki bir kenar, duvarin TAMAMINI degil bir PARCASINI (span) baglar: ayni duvarin
    uzak ucundaki komsular bu yuzden bir degisikligin etki alanina girmez (aksi halde uzun bir dis duvar etkiyi tum kata yayardi)."""

    def __init__(self) -> None:
        self.elements: dict[Node, dict] = {}
        self.adj: dict[Node, list[tuple[Node, str]]] = {}
        self._spans: dict[tuple[Node, Node, str], list[Span] | None] = {}
        self.warnings: list[str] = []
        self.floor_order: list[str] = []

    def add_node(self, node: Node, data: dict) -> None:
        self.elements[node] = data
        self.adj.setdefault(node, [])

    def add_edge(self, a: Node, b: Node, cls: str, span_a: list[Span] | None = None, span_b: list[Span] | None = None) -> None:
        """`span_a`/`span_b`: kenarin a/b ucundaki duvar parcasi (None = elemanin tamami). Ayni kenar tekrar eklenirse parcalar birlesir."""
        if cls not in EDGE_CLASSES:
            raise ImpactError(f"kenar sinifi tanimsiz: {cls}")
        if a == b:
            return
        for x, y, sp in ((a, b, span_a), (b, a, span_b)):
            key = (x, y, cls)
            if key not in self._spans:
                self.adj[x].append((y, cls))
                self._spans[key] = None if sp is None else list(sp)
            elif self._spans[key] is not None:
                self._spans[key] = None if sp is None else self._spans[key] + list(sp)

    def span(self, src: Node, dst: Node, cls: str) -> list[Span] | None:
        """`src` ucunda bu kenarin duvar parcasi; None = tamami."""
        return self._spans[(src, dst, cls)]


def _t(wall: dict, p) -> float:
    """Noktanin duvar dogrusu uzerindeki izdusum parametresi (duvar baslangicindan mesafe)."""
    sx, sy = wall["start"]
    ex, ey = wall["end"]
    L = ((ex - sx) ** 2 + (ey - sy) ** 2) ** 0.5
    if L < 1e-9:
        return 0.0
    return ((p[0] - sx) * (ex - sx) + (p[1] - sy) * (ey - sy)) / L


def _length(wall: dict) -> float:
    return ((wall["end"][0] - wall["start"][0]) ** 2 + (wall["end"][1] - wall["start"][1]) ** 2) ** 0.5


def _shapes(floor: dict, context: dict, graph: Graph):
    """Kata ait cakisma ayak izleri; alinamazsa SESSIZ gecilmez, uyari yazilir."""
    try:
        from collision.scene import Scene
        return Scene.from_floor(floor, context).shapes
    except Exception as exc:  # noqa: BLE001 - ayak izi saglayicisi her turlu veri hatasiyla patlayabilir; uyari olarak yuzeye cikar
        graph.warnings.append(f"{floor.get('id')}: ayak izleri alinamadi ({type(exc).__name__}: {exc}); "
                              "kapi_acilim ve ayak izi tabanli 'icinde' kenarlari bu katta KURULMADI")
        return []


def build_graph(context: dict) -> Graph:
    from collision.geometry import point_in_polygon, polygon_intersection_area
    from collision.shapes import TAG_COLUMN, TAG_DOOR_SWING, TAG_FURNITURE
    from spatial import (SHARED_EDGE_TOLERANCE_MM, dist_point_segment, door_midpoint, rooms_touching_point,
                         shared_edge_length, wall_edge_overlap)

    g = Graph()
    floors = context.get("floors", [])
    by_floor: dict[str, dict] = {}
    for fl in floors:
        fid = str(fl.get("id"))
        by_floor[fid] = fl
        g.floor_order.append(fid)
        for kind, key in FLOOR_LIST_KEY.items():
            for el in fl.get(key, []):
                g.add_node(Node(fid, kind, str(el["id"])), el)

    for fid, fl in by_floor.items():
        walls = fl.get("walls", [])
        rooms = fl.get("rooms", [])
        walls_by_id = {w["id"]: w for w in walls}
        rooms_by_id = {r["id"]: r for r in rooms}
        N = lambda kind, i: Node(fid, kind, str(i))  # noqa: E731

        # 1) kimlik basvurulari (sema alanlari)
        for _defn, field, src, dst in REFERENCE_FIELDS:
            for el in fl.get(FLOOR_LIST_KEY[src], []):
                ref = el.get(field)
                if ref is None:
                    continue
                target = N(dst, ref)
                if target in g.elements:
                    span_src = span_dst = None
                    if field == "wall_id" and ref in walls_by_id:
                        # aciklik: merkez position_from_start, genislik width -> duvar uzerinde bosluk parcasi
                        c, half = float(el.get("position_from_start", 0.0)), float(el.get("width", 0.0)) / 2.0
                        L = _length(walls_by_id[ref])
                        sp = [(max(0.0, c - half), min(L, c + half))]
                        span_dst = sp          # kenarin duvar ucu (hedef)
                    g.add_edge(N(src, el["id"]), target, "basvuru", span_src, span_dst)
                else:
                    g.warnings.append(f"{fid}: {src} '{el['id']}' .{field}='{ref}' olan {dst} yok - kenar kurulamadi")

        # 2) duvar-oda kenari
        for w in walls:
            L = _length(w)
            for r in rooms:
                poly = r["polygon"]
                spans: list[Span] = []
                for k in range(len(poly)):
                    a, b = poly[k], poly[(k + 1) % len(poly)]
                    if wall_edge_overlap(w["start"], w["end"], a, b) > SHARED_EDGE_TOLERANCE_MM:
                        ta, tb = _t(w, a), _t(w, b)
                        lo, hi = max(0.0, min(ta, tb)), min(L, max(ta, tb))
                        spans.append((lo, hi))
                if spans:
                    g.add_edge(N("wall", w["id"]), N("room", r["id"]), "duvar_oda_kenari", spans, None)

        # 3) duvar birlesimi: bir duvarin ucu baska duvarin uzerinde
        for w in walls:
            for t_end, end in ((0.0, w["start"]), (_length(w), w["end"])):
                for o in walls:
                    if o["id"] == w["id"]:
                        continue
                    if dist_point_segment(tuple(end), tuple(o["start"]), tuple(o["end"])) <= SHARED_EDGE_TOLERANCE_MM:
                        t_o = _t(o, end)
                        g.add_edge(N("wall", w["id"]), N("wall", o["id"]), "duvar_birlesimi", [(t_end, t_end)], [(t_o, t_o)])

        # 4) aciklik orta noktasina degen odalar
        for o in fl.get("openings", []):
            mid = door_midpoint(o, walls_by_id)
            if mid is None:
                g.warnings.append(f"{fid}: aciklik '{o['id']}' orta noktasi bulunamadi (duvar yok) - oda kenari kurulamadi")
                continue
            for r in rooms_touching_point(mid, rooms):
                g.add_edge(N("opening", o["id"]), N("room", r["id"]), "kapi_komsu_oda")

        # 5) saft - oda ortak kenari
        for s in fl.get("shafts", []):
            for r in rooms:
                if shared_edge_length(s["polygon"], r["polygon"]) > 0:
                    g.add_edge(N("shaft", s["id"]), N("room", r["id"]), "saft_komsu_oda")

        # 6) ayak izi tabanli: tefris/kolon odanin icinde; kapi acilim sektoru tefris/kolon ile kesisiyor
        shapes = _shapes(fl, context, g)
        sectors = [s for s in shapes if s.tag == TAG_DOOR_SWING]
        solids = [s for s in shapes if s.tag in (TAG_FURNITURE, TAG_COLUMN)]
        kind_of = {TAG_FURNITURE: "furniture", TAG_COLUMN: "column"}
        for s in solids:
            for r in rooms:
                if polygon_intersection_area(r["polygon"], s.polygon) > 0:
                    g.add_edge(N(kind_of[s.tag], s.id), N("room", r["id"]), "icinde")
            for sec in sectors:
                if polygon_intersection_area(s.polygon, sec.polygon) > 0:
                    g.add_edge(N(kind_of[s.tag], s.id), N("opening", sec.id), "kapi_acilim")
        for c in fl.get("counters", []):
            for r in rooms:
                if polygon_intersection_area(r["polygon"], c["polygon"]) > 0:
                    g.add_edge(N("counter", c["id"]), N("room", r["id"]), "icinde")
        # konumu tek nokta olan elemanlar
        for kind, field in (("label", "position"), ("level_mark", "position")):
            for el in fl.get(FLOOR_LIST_KEY[kind], []):
                p = el.get(field)
                if p is None:
                    continue
                for r in rooms:
                    if point_in_polygon(tuple(p), r["polygon"]):
                        g.add_edge(N(kind, el["id"]), N("room", r["id"]), "icinde")
        for m in fl.get("markings", []):
            for r in rooms:
                if point_in_polygon(tuple(m["start"]), r["polygon"]) or point_in_polygon(tuple(m["end"]), r["polygon"]):
                    g.add_edge(N("marking", m["id"]), N("room", r["id"]), "icinde")

        # 7) birim (ayni unit_id) - yayilmayan gevsek bag
        units: dict[str, list[Node]] = {}
        for kind, field in UNIT_FIELDS:
            for el in fl.get(FLOOR_LIST_KEY[kind], []):
                if el.get(field):
                    units.setdefault(str(el[field]), []).append(N(kind, el["id"]))
        for members in units.values():
            for i, a in enumerate(members):
                for b in members[i + 1:]:
                    g.add_edge(a, b, "birim")
        _ = rooms_by_id

    # 8) kat ikizi: baska katta ayni tur+kimlik (yayilmaz)
    seen: dict[tuple[str, str], list[Node]] = {}
    for node in g.elements:
        seen.setdefault((node.kind, node.id), []).append(node)
    for twins in seen.values():
        for i, a in enumerate(twins):
            for b in twins[i + 1:]:
                g.add_edge(a, b, "kat_ikizi")
    return g
