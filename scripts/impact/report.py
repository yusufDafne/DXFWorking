"""Etki alani raporu: `blast_radius`, `touched_from_diff`, `diff_report`, `coverage`. Salt okunur."""
from __future__ import annotations

from dataclasses import dataclass, field

from .graph import DERIVED_OUTPUTS, EDGE_CLASSES, FLOOR_LIST_KEY, Graph, ImpactError, Node, build_graph


@dataclass(frozen=True)
class Hop:
    node: Node
    via: str          # kenar sinifi
    source: Node      # hangi dugumden gelindi
    depth: int


@dataclass
class ImpactReport:
    touched: list[Node]
    depth: int
    rings: dict[int, list[Hop]] = field(default_factory=dict)      # yayilan kenarlarla ulasilanlar
    related: list[Hop] = field(default_factory=list)                # yayilmayan kenarlar (birim, kat ikizi): yalniz listelenir
    derived: dict[str, tuple[tuple[str, str], ...]] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def affected(self) -> list[Node]:
        return [h.node for d in sorted(self.rings) for h in self.rings[d]]


def _resolve(graph: Graph, touched) -> list[Node]:
    nodes: list[Node] = []
    for t in touched:
        node = t if isinstance(t, Node) else Node(*t)
        if node not in graph.elements:
            raise ImpactError(f"dokunulan eleman bulunamadi: {node} (etki alani uydurulmaz)")
        if node not in nodes:
            nodes.append(node)
    return nodes


def _overlaps(a, b, tol: float) -> bool:
    """a, b: [(lo, hi), ...] araliklar; ikisi de None degil. Herhangi bir cift tolerans payiyla ortusuyor mu."""
    return any(x0 - tol <= y1 and y0 - tol <= x1 for x0, x1 in a for y0, y1 in b)


def _covered(reached, arrival, tol: float) -> bool:
    """`arrival` (None = tamami) zaten `reached` icinde mi."""
    if reached is None:
        return True
    if arrival is None:
        return False
    return all(any(r0 - tol <= lo and hi <= r1 + tol for r0, r1 in reached) for lo, hi in arrival)


def blast_radius(context: dict, dokunulan, depth: int = 2, graph: Graph | None = None) -> ImpactReport:
    """`dokunulan`: [(kat_id, tur, id), ...]. Yayilan kenarlarla en cok `depth` halka; yayilmayan kenarlar `related`da.
    Bir duvara kenarla varildiysa etki o duvarin YALNIZ ilgili parcasindan (span) devam eder (dokunulan duvarin kendisi tamdir).
    `depth` bir SUNUM parametresidir (varsayilan 2: dogrudan + bir komsuluk); bir olcum esigi degildir."""
    from spatial import SHARED_EDGE_TOLERANCE_MM as TOL
    if not isinstance(depth, int) or isinstance(depth, bool) or depth < 1:
        raise ImpactError(f"depth >= 1 tam sayi olmali: {depth!r}")
    g = graph or build_graph(context)
    start = _resolve(g, dokunulan)
    rep = ImpactReport(touched=start, depth=depth, warnings=list(g.warnings))
    seen: set[Node] = set(start)
    reached: dict[Node, list | None] = {n: None for n in start}
    frontier: list[tuple[Node, list | None]] = [(n, None) for n in start]
    related_seen: set[tuple[Node, str]] = set()
    for d in range(1, depth + 1):
        nxt: list[tuple[Node, list | None]] = []
        ring: list[Hop] = []
        for src, arrival in frontier:
            for dst, cls in g.adj[src]:
                if not EDGE_CLASSES[cls][0]:
                    if dst not in seen and (dst, cls) not in related_seen:
                        related_seen.add((dst, cls))
                        rep.related.append(Hop(dst, cls, src, d))
                    continue
                if arrival is not None:                        # duvara bir parcasindan varildi: yalniz ayni parcadan cik
                    out_span = g.span(src, dst, cls)
                    if out_span is not None and not _overlaps(arrival, out_span, TOL):
                        continue
                dst_arrival = g.span(dst, src, cls)
                if dst in reached and _covered(reached[dst], dst_arrival, TOL):
                    continue
                if dst in reached and reached[dst] is not None and dst_arrival is not None:
                    reached[dst] = reached[dst] + dst_arrival
                else:
                    reached[dst] = dst_arrival if dst not in reached else None
                if dst not in seen:
                    seen.add(dst)
                    ring.append(Hop(dst, cls, src, d))
                nxt.append((dst, dst_arrival))
        if ring:
            rep.rings[d] = ring
        frontier = nxt
    kinds = {n.kind for n in start} | {h.node.kind for hops in rep.rings.values() for h in hops}
    rep.derived = {k: DERIVED_OUTPUTS.get(k, ()) for k in sorted(kinds)}
    return rep


def touched_from_diff(before: dict, after: dict) -> dict:
    """Iki context arasindaki fark. Dondurur:
    `added`/`changed` (sonraki context'te var), `removed` (yalniz oncekinde), `floors_added`, `floors_removed`,
    `other` (kat listeleri disinda degisen alanlar: meta, grid, kat etiketi ... - ETKI ALANI HESAPLANMAZ, adiyla soylenir)."""
    out: dict = {"added": [], "changed": [], "removed": [], "floors_added": [], "floors_removed": [], "other": []}
    b_floors = {str(f.get("id")): f for f in before.get("floors", [])}
    a_floors = {str(f.get("id")): f for f in after.get("floors", [])}
    out["floors_added"] = [f for f in a_floors if f not in b_floors]
    out["floors_removed"] = [f for f in b_floors if f not in a_floors]
    for fid, af in a_floors.items():
        bf = b_floors.get(fid, {})
        for kind, key in FLOOR_LIST_KEY.items():
            b_el = {str(e["id"]): e for e in bf.get(key, [])}
            a_el = {str(e["id"]): e for e in af.get(key, [])}
            for i, e in a_el.items():
                if i not in b_el:
                    out["added"].append(Node(fid, kind, i))
                elif b_el[i] != e:
                    out["changed"].append(Node(fid, kind, i))
            for i in b_el:
                if i not in a_el:
                    out["removed"].append(Node(fid, kind, i))
        keys = (set(af) | set(bf)) - set(FLOOR_LIST_KEY.values())
        for k in sorted(keys):
            if af.get(k) != bf.get(k) and fid in b_floors:
                out["other"].append(f"floors[{fid}].{k}")
    for fid, bf in b_floors.items():
        if fid not in a_floors:
            for kind, key in FLOOR_LIST_KEY.items():
                out["removed"].extend(Node(fid, kind, str(e["id"])) for e in bf.get(key, []))
    for k in sorted((set(before) | set(after)) - {"floors", "rev_history"}):
        if before.get(k) != after.get(k):
            out["other"].append(k)
    return out


@dataclass
class DiffReport:
    diff: dict
    after: ImpactReport | None
    before: ImpactReport | None


def diff_report(before: dict, after: dict, depth: int = 2) -> DiffReport:
    """Eklenen/degisen elemanlarin etkisi SONRAKI context'te, silinen/degisenlerin eski komsuluklari ONCEKI context'te hesaplanir
    (silinen elemanin eski komsulari sonrakinde de bulunabilir; iki rapor birlikte okunur)."""
    d = touched_from_diff(before, after)
    after_nodes = d["added"] + d["changed"]
    before_nodes = d["removed"] + d["changed"]
    return DiffReport(
        diff=d,
        after=blast_radius(after, after_nodes, depth) if after_nodes else None,
        before=blast_radius(before, before_nodes, depth) if before_nodes else None,
    )


def coverage(context: dict, graph: Graph | None = None) -> dict:
    """Tamlik/kapsam: tur basina dugum sayisi, YAYILAN hicbir kenari olmayan ('bagsiz') elemanlar, kapsam disi ust seviye alanlar.
    'Etkilenen yok' ile 'bakilamadi' ayni sey degildir: bagsiz eleman, grafin onu hic baglayamadigi elemandir."""
    g = graph or build_graph(context)
    per_kind: dict[str, dict] = {}
    for node in g.elements:
        k = per_kind.setdefault(node.kind, {"count": 0, "isolated": []})
        k["count"] += 1
        if not any(EDGE_CLASSES[cls][0] for _, cls in g.adj[node]):
            k["isolated"].append(str(node))
    return {
        "per_kind": per_kind,
        "out_of_scope": sorted(k for k in context if k not in ("floors", "rev_history")),
        "warnings": list(g.warnings),
    }


def format_report(rep: ImpactReport) -> list[str]:
    lines = [f"Dokunulan ({len(rep.touched)}): " + ", ".join(str(n) for n in rep.touched)]
    for d in sorted(rep.rings):
        lines.append(f"Halka {d} ({len(rep.rings[d])}):")
        for h in rep.rings[d]:
            lines.append(f"  - {h.node}  <- {h.source} [{h.via}]")
    if rep.related:
        lines.append(f"Ilgili, yayilmaz ({len(rep.related)}):")
        groups: dict[tuple[Node, str], list[Node]] = {}
        for h in rep.related:
            groups.setdefault((h.source, h.via), []).append(h.node)
        for (src, via), nodes in groups.items():
            where = ", ".join(n.floor if via == "kat_ikizi" else f"{n.kind}/{n.id}" for n in nodes)
            lines.append(f"  - {src} [{via}] -> {where}")
    if rep.derived:
        lines.append("Yeniden turetilen ciktilar:")
        for kind, outs in rep.derived.items():
            lines.append(f"  - {kind}: " + ("; ".join(f"{m} ({what})" for m, what in outs) or "(yok)"))
    for w in rep.warnings:
        lines.append(f"UYARI: {w}")
    return lines
