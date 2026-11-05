"""`context.json::site` -> etut / gorunum yardimcilari (DEV-083/084). CLI'lar (`site_study.py`, `site_export.py`) AYNI cozumlemeyi kullanir (tek kaynak)."""
from __future__ import annotations

try:
    from .narrate import narrate_alternative
    from .parcel import Parcel, VaziyetError
    from .setback import buildable_area, building_footprint
    from .sheet import SiteView
    from .study import DEFAULT_ALTERNATIVES, run_study
    from .zoning import resolve_zoning, setbacks_for_parcel
except ImportError:
    from narrate import narrate_alternative  # type: ignore
    from parcel import Parcel, VaziyetError  # type: ignore
    from setback import buildable_area, building_footprint  # type: ignore
    from sheet import SiteView  # type: ignore
    from study import DEFAULT_ALTERNATIVES, run_study  # type: ignore
    from zoning import resolve_zoning, setbacks_for_parcel  # type: ignore


def study_from_context(context: dict, *, step_mm, rotations_deg, n=None, weights=None, min_separation_mm=None, taks=None, kaks=None, floors=None, setbacks_user=None):
    """(StudyResult, bildirimler, yapilasma alani). `site.setbacks` yoksa katalog cekmesi KULLANILIR ve bildirimlere ADIYLA yazilir. Veri eksikse `VaziyetError`."""
    site = context.get("site") or {}
    meta = context.get("meta", {})
    if not site.get("parcel"):
        raise VaziyetError("context.json'da site.parcel yok")
    if not meta.get("floor_width") or not meta.get("floor_depth"):
        raise VaziyetError("meta.floor_width/floor_depth yok: bina ayak izi bilinmiyor (uydurulmaz)")
    parcel = Parcel.from_polygon(site["parcel"]["polygon"])
    roads = list(site.get("road_edges", []))
    n_edges = len(parcel.polygon)
    for i in roads:
        if isinstance(i, bool) or not isinstance(i, int) or not 0 <= i < n_edges:
            raise VaziyetError(f"site.road_edges: {i!r} gecersiz kenar indeksi (parselde {n_edges} kenar var)")
    notices: list[str] = []
    user = {k: v for k, v in (("taks", taks), ("kaks", kaks)) if v is not None}
    sb_user = {k: v for k, v in (setbacks_user or {}).items() if v is not None}
    if sb_user and site.get("setbacks"):
        raise VaziyetError("hem site.setbacks hem brief cekmesi var: celiskili olabilir, biri kaldirilmali (sessiz oncelik yok)")
    user.update(sb_user)
    res = resolve_zoning(user)
    if site.get("setbacks"):
        buildable = buildable_area(parcel, site["setbacks"])
    else:
        sb, sres = setbacks_for_parcel(parcel, roads, user)
        buildable = buildable_area(parcel, sb)
        sb_defaults = [z for z in sres.used_defaults if z.key.endswith("setback_mm")]       # TAKS/KAKS varsayilanlari asagida ayri bildirilir
        if sb_defaults:
            notices += ["site.setbacks yok: imar katalogu varsayilani kullanildi."] + [ln for ln in sres.describe() if any(f"[{z.name};" in ln for z in sb_defaults)]
        else:
            notices.append("site.setbacks yok: cekmeler brief'teki kullanici degerlerinden alindi.")
    taks_lim = {"value": res.values["taks"], "source": res.sources["taks"]} if res.values.get("taks") is not None else None
    kaks_lim = {"value": res.values["kaks"], "source": res.sources["kaks"]} if res.values.get("kaks") is not None else None
    for z in res.used_defaults:
        if z.key == "taks":
            notices += [x for x in res.describe() if "TAKS" in x and x not in notices]
    result = run_study(site["parcel"]["polygon"], buildable, float(meta["floor_width"]), float(meta["floor_depth"]), step_mm=step_mm, rotations_deg=rotations_deg,
                       n=n or DEFAULT_ALTERNATIVES, weights=weights, road_edges=roads, zone=(site.get("placement_zone") or {}).get("polygon"),
                       north_confirmed=bool(site.get("north_confirmed")), min_separation_mm=min_separation_mm, taks=taks_lim, kaks=kaks_lim, floor_count=floors)
    return result, notices, buildable


def view_from_building(context: dict) -> SiteView:
    """SECILMIS yerlesim (`site.building`) icin gorunum. Cekme bildirilmediyse yapilasma alani CIZILMEZ (katalog sessizce uygulanmaz) ve bu bilgi satirinda yazar."""
    site = context.get("site") or {}
    meta = context.get("meta", {})
    b = site.get("building")
    if not b:
        raise VaziyetError("context.json'da site.building yok: secilmis yerlesim bilinmiyor (once etut: site_study.py)")
    if not site.get("parcel"):
        raise VaziyetError("context.json'da site.parcel yok")
    if not meta.get("floor_width") or not meta.get("floor_depth"):
        raise VaziyetError("meta.floor_width/floor_depth yok")
    parcel = Parcel.from_polygon(site["parcel"]["polygon"])
    rot = float(b.get("rotation_deg", 0.0))
    fp = building_footprint(float(meta["floor_width"]), float(meta["floor_depth"]), b["position"], rot)
    buildable = buildable_area(parcel, site["setbacks"]) if site.get("setbacks") else None
    lines = [f"BINA DONUSU: {rot:g} DERECE (KUZEYDEN SAAT YONUNDE)"]
    if buildable is None:
        lines.append("CEKME BILDIRILMEDI: YAPILASMA ALANI CIZILMEDI")
    return SiteView(label="VAZIYET PLANI", parcel_polygon=list(parcel.polygon), footprint=fp, rotation_deg=rot, buildable=buildable,
                    road_edges=tuple(site.get("road_edges", [])), zone=(site.get("placement_zone") or {}).get("polygon"), info_lines=lines)


def views_from_study(context: dict, result, buildable) -> list[SiteView]:
    """Her alternatif icin bir gorunum; bilgi satirlari `narrate_alternative` ciktisidir (olculmus sayilar). Bolge disina tasan alternatif bunu satirda soyler."""
    site = context.get("site") or {}
    parcel = Parcel.from_polygon(site["parcel"]["polygon"])
    views = []
    for a in result.alternatives:
        lines = [ln.strip() for ln in narrate_alternative(a)]
        lines.append(f"KAT PLANI KUZEY ACISI: {a.plan_north_angle:g} DERECE")
        views.append(SiteView(label=f"{a.id} ALTERNATIFI", parcel_polygon=list(parcel.polygon), footprint=list(a.footprint), rotation_deg=a.rotation_deg,
                              buildable=buildable, road_edges=tuple(site.get("road_edges", [])), zone=(site.get("placement_zone") or {}).get("polygon"),
                              info_lines=lines))
    return views


def study_from_brief(context: dict, fields: dict):
    """ONAYLI brief alanlariyla etut (`study_from_context`); onay denetimi cagiranin isidir (`brief.require_phase_and_brief`)."""
    for k in ("step_mm", "rotations_deg"):
        if k not in fields:
            raise VaziyetError(f"brief'te '{k}' yok: adim ve donus kumesi varsayilansizdir, kullanicidan istenir")
    return study_from_context(
        context, step_mm=fields["step_mm"], rotations_deg=fields["rotations_deg"], n=fields.get("n"), weights=fields.get("weights"),
        min_separation_mm=fields.get("min_separation_mm"), taks=fields.get("taks"), kaks=fields.get("kaks"), floors=fields.get("floors"),
        setbacks_user={k: fields.get(k) for k in ("front_setback_mm", "side_setback_mm", "rear_setback_mm")})
