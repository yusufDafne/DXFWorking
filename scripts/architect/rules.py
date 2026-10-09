"""Iliskisel (arity-2+) kural kontrolu - DEV-039.

`standards/`dan farki ARITEDIR: `standards::check_room_proportions` bir
odanin KENDI oraninin makul olup olmadigina bakar (tek oda, arity-1). Bu
dosyadaki fonksiyonlar iki/N FARKLI elemanin BIRBIRINE GORE mantikli olup
olmadigina bakar (arity-2+) - `collision/`in `rooms/`den ayrilmasiyla
BIREBIR AYNI gerekce, sadece konusu fiziksel CAKISMA degil mimari SAGDUYU.

**Politika: `standards/` ile AYNI - HER ZAMAN UYARI, asla HATA**
(kullanici karari, 2026-09-28 ucuncu tur: "hayir" - mahremiyet kurallari
dahil hicbiri daha ciddi bir sinifa CEKILMEDI). Esikler context.json'a
YAZILMAZ (kok CLAUDE.md: "cizim sabiti context'e sizmamali") - katalog
sabiti olarak burada tanimlanir VE her fonksiyon bir OVERRIDE parametresi
tasir (kullanici: "default bir oran olsun ama ihtiyaca gore
esnetilebilsin").

**Tum kurallar `unit_id` OPT-IN'dir** (`room_type` ile AYNI desen): bir oda
`unit_id` tasimiyorsa ilgisiz kontrole HIC GIRMEZ. Gercek projenin bugunku
`context.json`'inda `unit_id` HENUZ YOK (bu ayri, sonraki bir revizyondur -
bkz. DEVELOPMENT_TASKS.md DEV-039 "Uygulama sirasi" adim 14), bu yuzden bu
kurallar bugun gercek projede SESSIZCE hicbir uyari URETMEZ - tipki
`room_type` rev-19'a kadar bos oldugu icin `standards/` hicbir uyari
uretmemesi gibi.

**Oda-kapi komsulugu NASIL bulunur:** bir kapinin duvar-merkez-cizgisi
uzerindeki orta noktasi hesaplanir (`_door_midpoint`), sonra
`collision.geometry.point_on_boundary` ile HANGI oda(lar)in poligon
KENARININ bu noktaya deger oldugu bulunur (`_rooms_touching_point`). Bu,
projedeki poligon matematiginin TEK sahibini (`collision/geometry.py`)
YENIDEN kullanir, ikinci bir kopya YAZILMAZ.
"""
from __future__ import annotations

import math

try:
    from ..collision.geometry import point_in_polygon, point_on_boundary
    from ..spatial import (
        TOUCH_TOLERANCE_MM,
        clear_line_of_sight as _clear_line_of_sight,
        door_midpoint as _door_midpoint,
        rooms_touching_point as _rooms_touching_point,
        segments_intersect as _segments_intersect,
        shared_edge_length as _shared_wall_length,
        vertex_mean as _centroid,
    )
except ImportError:
    from collision.geometry import point_in_polygon, point_on_boundary
    from spatial import (
        TOUCH_TOLERANCE_MM,
        clear_line_of_sight as _clear_line_of_sight,
        door_midpoint as _door_midpoint,
        rooms_touching_point as _rooms_touching_point,
        segments_intersect as _segments_intersect,
        shared_edge_length as _shared_wall_length,
        vertex_mean as _centroid,
    )
# DEV-059: mekansal sorgular `spatial/` modulune tasindi (ayni ozel adlarla takma ad).

# v1 pratik varsayilanlar (standards.STANDARDS ile AYNI disiplin - katalog
# SABITI, proje verisi DEGIL). Her check_* fonksiyonu bunu bir parametre
# olarak da kabul eder (kullanicinin "esnetilebilsin" istegi).
DEFAULT_CIRCULATION_SHARE_MAX = 0.15
DEFAULT_DOOR_CORE_BALANCE_RATIO = 1.6
DEFAULT_SIGHTLINE_CONE_DEGREES = 45.0
# DEV-043: gercek projenin KENDI uA/uB banyo-wc kapi mesafesi (4016mm,
# rev-22) bu sinirin ALTINDA kalacak sekilde secildi - "ayni kanat"
# sayilacak kaba bir ust sinir, metre hassasiyetinde bir olcum DEGIL.
DEFAULT_WET_AREA_DOOR_MAX_DISTANCE = 5000.0

# DEV-050 (madde 4/12/13/14) varsayilanlari - v1 pratik varsayilan.
DEFAULT_WET_DOOR_WINDOW_MIN_GAP_MM = 600.0
DEFAULT_DOOR_AXIS_ALIGN_TOLERANCE_MM = 450.0
_SWING_PROBE_MM = 400.0
KITCHEN_ROOM_TYPES = frozenset({"mutfak"})
# DEV-051 ek karar (2026-10-05): dukkanlar konut KABUL EDILMEZ; kapi yonu kurali
# ayridir (konutta odaya, ticari birimde kacis yonunde = ortak alana).
COMMERCIAL_ROOM_TYPES = frozenset({"dukkan"})
# DEV-053 (kullanici karari 2026-10-05): kapi arasi asgari TEMIZ aralik = 100mm
# kapi cerceve oturumu + 150mm priz/tesisat payi = 250mm.
DEFAULT_DOOR_GAP_MIN_MM = 250.0
# "daire kapisi acilinca hemen onunde / capraziunda WC kapisi olmasin":
# capraz = giris yonune gore 60 dereceye kadar; mesafe ust siniri agent
# varsayilani (hol derinligi), esnetilebilir.
DEFAULT_ENTRY_FRONT_CONE_DEGREES = 60.0
DEFAULT_ENTRY_FRONT_MAX_DISTANCE_MM = 3000.0
DEFAULT_COMMERCIAL_SWING_POLICY = "outward"

WC_ROOM_TYPES = frozenset({"wc", "banyo"})
CORE_ROOM_TYPES = frozenset({"asansor", "merdiven"})
CIRCULATION_ROOM_TYPES = frozenset({"koridor"})
BEDROOM_ROOM_TYPES = frozenset({"yatak_odasi"})

# Oda-kapi komsulugu ararken kullanilan tolerans (mm). Bu projede duvar
# kalinligi 200mm ve oda poligonlari cogunlukla duvar MERKEZ cizgisiyle
# ayni koordinatta tanimlanir (bkz. templates::generate_circulation_core);
# 300mm hem merkez-hizali hem ic-yuz-hizali odalari guvenle yakalar.
_TOUCH_TOLERANCE_MM = TOUCH_TOLERANCE_MM



def check_circulation_area_share(
    rooms: list[dict], *, max_share: float = DEFAULT_CIRCULATION_SHARE_MAX,
) -> list[str]:
    """[madde 3+6] Hol/sirkulasyon alani, ayni `unit_id`deki TOPLAM net
    alanin `max_share` oranini asarsa UYARI - "hol buyutulup diger odalar
    kucultulmez" ilkesini OLCULEBILIR hale getirir. `unit_id` tasimayan
    odalar hesaba KATILMAZ (opt-in)."""
    warnings: list[str] = []
    by_unit: dict[str, list[dict]] = {}
    for room in rooms:
        unit_id = room.get("unit_id")
        if not unit_id:
            continue
        by_unit.setdefault(unit_id, []).append(room)

    for unit_id, unit_rooms in sorted(by_unit.items()):
        total = sum(r["area_m2"] for r in unit_rooms)
        circulation = sum(
            r["area_m2"] for r in unit_rooms if r.get("room_type") == "koridor"
        )
        if total <= 0 or circulation <= 0:
            continue
        share = circulation / total
        if share > max_share:
            warnings.append(
                f"Birim '{unit_id}': hol/sirkulasyon alani toplam net alanin "
                f"%{share * 100:.1f}'i, izin verilen ust sinir "
                f"%{max_share * 100:.1f} asildi (hol={circulation:.1f} m2, "
                f"toplam={total:.1f} m2)."
            )
    return warnings


def check_bedroom_via_corridor(rooms: list[dict], walls: list[dict],
                                openings: list[dict]) -> list[str]:
    """[madde 5] Bir yatak odasinin kapisi, AYNI birimdeki bir salona
    DOGRUDAN aciliyorsa UYARI - mahremiyet gerekcesi madde 2 ile AYNI
    aileden (misafirin gorecegi bir sirkulasyondan yatak odasina dogrudan
    gecis olmamali, hol/koridor uzerinden erisim tercih edilir)."""
    warnings: list[str] = []
    walls_by_id = {w["id"]: w for w in walls}

    for room in rooms:
        if room.get("room_type") != "yatak_odasi" or not room.get("unit_id"):
            continue
        for door in openings:
            if door.get("type") != "door":
                continue
            point = _door_midpoint(door, walls_by_id)
            if point is None:
                continue
            touching = _rooms_touching_point(point, rooms)
            touching_ids = {r["id"] for r in touching}
            if room["id"] not in touching_ids:
                continue
            for other in touching:
                if other["id"] == room["id"]:
                    continue
                if other.get("unit_id") != room.get("unit_id"):
                    continue
                if other.get("room_type") == "salon":
                    warnings.append(
                        f"Yatak odasi '{room['id']}' kapisi ('{door['id']}') "
                        f"dogrudan salona ('{other['id']}') aciliyor - "
                        f"hol/koridor uzerinden erisim tercih edilir."
                    )
    return warnings


def check_entry_sightlines(
    rooms: list[dict], walls: list[dict], openings: list[dict], *,
    cone_degrees: float = DEFAULT_SIGHTLINE_CONE_DEGREES,
) -> list[str]:
    """[madde 2] Bir birimin GIRIS kapisi (ortak alandan `unit_id`li bir
    odaya gecen kapi) ile AYNI birimdeki bir WC/banyo kapisi ayni goru
    hattindaysa (giris yonunden `cone_degrees` koni ICINDE VE arada
    engelleyen bir duvar YOKSA) UYARI.

    **v1 basitlestirmesi (bilerek, standards'in AABB basitlestirmesiyle
    AYNI kategoride):** goru hatti, iki kapi ORTA NOKTASI arasindaki DUZ
    CIZGI + bu cizginin baska bir duvarin merkez cizgisini KESIP kesmedigi
    testiyle yaklasik olarak modellenir - gercek bir mimarin gozuyle
    yapilan tam bir gorunurluk analizi (odanin ic mobilyasi, kapi acilim
    yayi vb.) DEGILDIR."""
    warnings: list[str] = []
    walls_by_id = {w["id"]: w for w in walls}
    cos_threshold = math.cos(math.radians(cone_degrees))
    doors = [o for o in openings if o.get("type") == "door"]

    for entry in doors:
        wall = walls_by_id.get(entry.get("wall_id"))
        entry_point = _door_midpoint(entry, walls_by_id)
        if wall is None or entry_point is None:
            continue
        touching = _rooms_touching_point(entry_point, rooms)
        unit_side = [r for r in touching if r.get("unit_id")]
        common_side = [r for r in touching if not r.get("unit_id")]
        if not unit_side or not common_side:
            continue  # giris kapisi tanimi: ortak alan <-> birim gecisi

        unit_id = unit_side[0].get("unit_id")
        sx, sy = wall["start"]
        ex, ey = wall["end"]
        dx, dy = ex - sx, ey - sy
        length = (dx * dx + dy * dy) ** 0.5
        if length == 0:
            continue
        normal = (-dy / length, dx / length)
        unit_centroid = _centroid(unit_side[0]["polygon"])
        to_unit = (unit_centroid[0] - entry_point[0], unit_centroid[1] - entry_point[1])
        if normal[0] * to_unit[0] + normal[1] * to_unit[1] < 0:
            normal = (-normal[0], -normal[1])

        for other in doors:
            if other["id"] == entry["id"]:
                continue
            other_point = _door_midpoint(other, walls_by_id)
            if other_point is None:
                continue
            other_touching = _rooms_touching_point(other_point, rooms)
            wc_rooms = [
                r for r in other_touching
                if r.get("room_type") in WC_ROOM_TYPES and r.get("unit_id") == unit_id
            ]
            if not wc_rooms:
                continue

            direction = (other_point[0] - entry_point[0], other_point[1] - entry_point[1])
            dist = (direction[0] ** 2 + direction[1] ** 2) ** 0.5
            if dist == 0:
                continue
            direction_n = (direction[0] / dist, direction[1] / dist)
            cos_angle = normal[0] * direction_n[0] + normal[1] * direction_n[1]
            if cos_angle < cos_threshold:
                continue
            if not _clear_line_of_sight(
                entry_point, other_point, walls, {entry["wall_id"], other["wall_id"]}
            ):
                continue

            angle = math.degrees(math.acos(max(-1.0, min(1.0, cos_angle))))
            warnings.append(
                f"Giris kapisi '{entry['id']}' ile WC/banyo kapisi "
                f"'{other['id']}' ayni goru hattinda (sapma {angle:.0f} "
                f"derece, sinir {cone_degrees:.0f}) - giristen girildiginde "
                f"WC/banyo kapisi dogrudan gorunur."
            )
    return warnings


def check_entry_wet_door_proximity(
    rooms: list[dict], walls: list[dict], openings: list[dict], *,
    min_gap: float = DEFAULT_DOOR_GAP_MIN_MM,
    cone_degrees: float = DEFAULT_ENTRY_FRONT_CONE_DEGREES,
    max_distance: float = DEFAULT_ENTRY_FRONT_MAX_DISTANCE_MM,
) -> list[str]:
    """[DEV-053 + DEV-050 #15 birlesti] Giris kapisi (birim <-> ortak alan) ile
    AYNI birimdeki WC/banyo kapisi icin iki kontrol, mesafe DUZ CIZGI:
      1) kapi kenarlari arasi TEMIZ aralik `min_gap`ten (250mm = 100 cerceve
         + 150 priz payi) azsa UYARI;
      2) giris kapisi acilinca ONUNDE / CAPRAZINDA (giris yonune gore
         `cone_degrees`e kadar, `max_distance` icinde, arada duvar yok) bir
         WC/banyo kapisi varsa UYARI. `check_entry_sightlines`in kapsadigi dar
         koni (<=45 derece) burada TEKRARLANMAZ (capraz bandi: 45-60).
    Mutfak vb. diger oda kapilari bu kurala girmez (yerlesim plani konusu)."""
    warnings: list[str] = []
    walls_by_id = {w["id"]: w for w in walls}
    cos_cone = math.cos(math.radians(cone_degrees))
    cos_inner = math.cos(math.radians(DEFAULT_SIGHTLINE_CONE_DEGREES))
    doors = [o for o in openings if o.get("type") == "door"]
    for entry in doors:
        wall = walls_by_id.get(entry.get("wall_id"))
        entry_point = _door_midpoint(entry, walls_by_id)
        normal = _wall_unit_normal(wall) if wall else None
        if entry_point is None or normal is None:
            continue
        touching = _rooms_touching_point(entry_point, rooms)
        unit_side = [r for r in touching if r.get("unit_id")]
        if not unit_side or not any(not r.get("unit_id") for r in touching):
            continue
        unit_id = unit_side[0]["unit_id"]
        centroid = _centroid(unit_side[0]["polygon"])
        if normal[0] * (centroid[0] - entry_point[0]) + normal[1] * (centroid[1] - entry_point[1]) < 0:
            normal = (-normal[0], -normal[1])
        for other in doors:
            if other["id"] == entry["id"]:
                continue
            other_point = _door_midpoint(other, walls_by_id)
            if other_point is None:
                continue
            if not any(r.get("room_type") in WC_ROOM_TYPES and r.get("unit_id") == unit_id
                       for r in _rooms_touching_point(other_point, rooms)):
                continue
            vx, vy = other_point[0] - entry_point[0], other_point[1] - entry_point[1]
            dist = (vx * vx + vy * vy) ** 0.5
            gap = dist - (entry["width"] + other["width"]) / 2.0
            if gap < min_gap - 1e-6:
                warnings.append(
                    f"Giris kapisi '{entry['id']}' ile WC/banyo kapisi '{other['id']}' "
                    f"arasi temiz aralik {max(gap, 0.0):.0f}mm, asgari {min_gap:.0f}mm "
                    f"(100 cerceve + 150 priz payi)."
                )
            if dist == 0 or dist > max_distance:
                continue
            cos_angle = (normal[0] * vx + normal[1] * vy) / dist
            if cos_angle < cos_cone or cos_angle >= cos_inner:
                continue  # onde-capraz bandinin disinda ya da dar koni (sightlines)
            if not _clear_line_of_sight(entry_point, other_point, walls,
                                        {entry["wall_id"], other["wall_id"]}):
                continue
            angle = math.degrees(math.acos(max(-1.0, min(1.0, cos_angle))))
            warnings.append(
                f"Giris kapisi '{entry['id']}' acilinca capraz onunde "
                f"(sapma {angle:.0f} derece, {dist:.0f}mm) WC/banyo kapisi "
                f"'{other['id']}' var - WC kapisi giris karsisina/capraz "
                f"onune konmamali."
            )
    return warnings


def check_door_core_balance(
    rooms: list[dict], walls: list[dict], openings: list[dict], *,
    max_ratio: float = DEFAULT_DOOR_CORE_BALANCE_RATIO,
) -> list[str]:
    """[madde 1] Ayni kattaki birimlerin GIRIS kapilarinin cekirdege
    (asansor+merdiven merkez noktasi) olan EN YAKIN mesafesi birbirine
    gore COK dengesizse (en uzak/en yakin orani `max_ratio`yi asarsa)
    UYARI - "bir dairenin kapisi dogrudan merdivene aciliyorken digerleri
    daha izole" ornegi."""
    warnings: list[str] = []
    walls_by_id = {w["id"]: w for w in walls}
    core_rooms = [r for r in rooms if r.get("room_type") in CORE_ROOM_TYPES]
    if not core_rooms:
        return warnings
    core_points = [_centroid(r["polygon"]) for r in core_rooms]
    core_x = sum(p[0] for p in core_points) / len(core_points)
    core_y = sum(p[1] for p in core_points) / len(core_points)

    distances: dict[str, float] = {}
    for door in openings:
        if door.get("type") != "door":
            continue
        if walls_by_id.get(door.get("wall_id")) is None:
            continue
        point = _door_midpoint(door, walls_by_id)
        if point is None:
            continue
        touching = _rooms_touching_point(point, rooms)
        unit_side = [r for r in touching if r.get("unit_id")]
        common_side = [r for r in touching if not r.get("unit_id")]
        if not unit_side or not common_side:
            continue
        unit_id = unit_side[0].get("unit_id")
        dist = ((point[0] - core_x) ** 2 + (point[1] - core_y) ** 2) ** 0.5
        if unit_id not in distances or dist < distances[unit_id]:
            distances[unit_id] = dist

    if len(distances) < 2:
        return warnings
    max_dist = max(distances.values())
    min_dist = min(distances.values())
    if min_dist <= 0:
        return warnings
    ratio = max_dist / min_dist
    if ratio > max_ratio:
        nearest = min(distances, key=distances.get)
        farthest = max(distances, key=distances.get)
        warnings.append(
            f"Daire girisleri cekirdege (asansor/merdiven) gore DENGESIZ "
            f"dagilmis: '{nearest}' {min_dist:.0f}mm, '{farthest}' "
            f"{max_dist:.0f}mm (oran {ratio:.2f}, izin verilen ust sinir "
            f"{max_ratio:.2f})."
        )
    return warnings


def _build_unit_adjacency(rooms: list[dict], walls: list[dict],
                           openings: list[dict], unit_id: str) -> dict[str, set[str]]:
    """`unit_id`li odalar arasinda, bir kapi ile DOGRUDAN baglantili
    olanlarin komsuluk grafini kurar. Graf BILEREK yalnizca BU birimin
    kendi odalariyla sinirlidir (ortak/sirkulasyon alani veya baska bir
    birim DAHIL EDILMEZ) - DEV-042'nin sorusu "bu birimin KENDI holunden
    islak hacime yatak odasina UGRAMADAN gidilebilir mi", bina genelindeki
    erisim DEGIL. Kenarlar `rules._door_midpoint`/`_rooms_touching_point`i
    (bu modulun TEK oda-kapi komsuluk kaynagi) YENIDEN kullanir."""
    unit_rooms = [r for r in rooms if r.get("unit_id") == unit_id]
    walls_by_id = {w["id"]: w for w in walls}
    adjacency: dict[str, set[str]] = {r["id"]: set() for r in unit_rooms}
    for door in openings:
        if door.get("type") != "door":
            continue
        point = _door_midpoint(door, walls_by_id)
        if point is None:
            continue
        touching_ids = [r["id"] for r in _rooms_touching_point(point, unit_rooms)]
        for i in range(len(touching_ids)):
            for j in range(i + 1, len(touching_ids)):
                a, b = touching_ids[i], touching_ids[j]
                adjacency[a].add(b)
                adjacency[b].add(a)
    return adjacency


def _reachable_avoiding(adjacency: dict[str, set[str]], start_ids: set[str],
                         target_id: str, blocked_ids: set[str]) -> bool:
    """`blocked_ids`deki dugumlerden GECMEDEN, `start_ids`den herhangi
    birinden `target_id`e bir yol var mi (genis-oncelikli arama)."""
    visited: set[str] = set()
    queue: list[str] = [s for s in start_ids if s not in blocked_ids]
    visited.update(queue)
    while queue:
        current = queue.pop()
        if current == target_id:
            return True
        for neighbor in adjacency.get(current, ()):
            if neighbor in blocked_ids or neighbor in visited:
                continue
            visited.add(neighbor)
            queue.append(neighbor)
    return target_id in visited


def check_wet_area_reachable_without_bedroom(
    rooms: list[dict], walls: list[dict], openings: list[dict],
) -> list[str]:
    """[DEV-042] Ayni birimdeki bir ıslak hacme (banyo/wc), birimin KENDI
    hol/koridor odasindan bir yatak odasindan GECMEDEN ulasilan EN AZ bir
    yol yoksa UYARI - kullanicinin somut ornegi: *"koridor -> hol -> oda
    -> banyo ... bu asla kabul edilebilir bir yaklasim degildir."*

    `check_bedroom_via_corridor` (DEV-039) bunu KACIRDI cunku SADECE
    "yatak odasi SALONA dogrudan aciliyor mu" diye bakiyor; "yatak odasi,
    BASKA bir odaya ulasmak icin ZORUNLU bir GECIS odasi mi" sorusunu HIC
    SORMUYOR. Bu kontrol bir graf gezinmesidir (bugune kadarki dort
    kuralin "iki komsu oda" tek-adim testinden FARKLI bir karmasiklik
    seviyesi) - TEK yolun yatak odasindan gecmesi DEGIL, HICBIR yolun
    gecmeMEmesi arandigi icin (otel gibi coklu-erisimli birimlerde YANLIS-
    POZITIF uretmemek icin BILEREK boyle), bir yatak odasi "engelli dugum"
    sayilarak BFS ile test edilir (`_reachable_avoiding`).

    `unit_id` VE `room_type` OPT-IN'dir (diger uc kuralla AYNI desen):
    hicbiri yoksa kontrol SESSIZCE atlanir."""
    warnings: list[str] = []
    by_unit: dict[str, list[dict]] = {}
    for room in rooms:
        unit_id = room.get("unit_id")
        if unit_id:
            by_unit.setdefault(unit_id, []).append(room)

    for unit_id, unit_rooms in sorted(by_unit.items()):
        wet_rooms = [r for r in unit_rooms if r.get("room_type") in WC_ROOM_TYPES]
        corridor_ids = {r["id"] for r in unit_rooms
                         if r.get("room_type") in CIRCULATION_ROOM_TYPES}
        if not wet_rooms or not corridor_ids:
            continue
        bedroom_ids = {r["id"] for r in unit_rooms
                       if r.get("room_type") in BEDROOM_ROOM_TYPES}
        adjacency = _build_unit_adjacency(rooms, walls, openings, unit_id)

        for wet_room in wet_rooms:
            if _reachable_avoiding(adjacency, corridor_ids, wet_room["id"], bedroom_ids):
                continue
            warnings.append(
                f"Birim '{unit_id}': ıslak hacim '{wet_room['id']}' odasına "
                f"hol/koridordan yatak odasından GEÇMEDEN ulaşan bir yol "
                f"yok - tüm erişim yolları en az bir yatak odasından geçiyor."
            )
    return warnings



def _same_line(wall_a: dict, wall_b: dict, tol: float = 1.0) -> bool:
    """Iki duvar AYNI dogru uzerinde mi (paralel + aralarinda <= tol)."""
    (ax, ay), (bx, by) = wall_a["start"], wall_a["end"]
    dx, dy = bx - ax, by - ay
    length = (dx * dx + dy * dy) ** 0.5
    if length == 0:
        return False
    return all(
        abs(dx * (p[1] - ay) - dy * (p[0] - ax)) / length <= tol
        for p in (wall_b["start"], wall_b["end"])
    )


def check_wet_area_adjacency(
    rooms: list[dict], walls: list[dict], openings: list[dict], *,
    require_shared_wall: bool = True,
) -> list[str]:
    """[DEV-052] Ayni birimdeki WC ve banyo icin GERCEK komsuluk (DEV-043'un
    kapi-orta-nokta mesafesi yaklasiminin eksigini kapatir). Kullanici
    kararlari (2026-10-05, varsayilan ayarlar):
      a) WC ve banyo ORTAK DUVAR paylasmali (`require_shared_wall=False`
         kapatir; ortak uzunluk asgarisi YOK, kose temasi sayilmaz).
      b) Kapilari AYNI HATTA ve yan yana olmali - sirt sirta/karsilikli
         (farkli hatlarda) OLMAZ: her iki oda kapisinin en yakin cifti ayni
         dogru uzerindeki duvarlarda degilse UYARI.
      c) Kapilar, ayni birimdeki DIGER oda kapilarindan (salon, yatak, mutfak;
         giris ve hol kapilari haric) mumkun oldugunca UZAK olmali: bir islak
         hacim kapisinin en yakin diger-oda kapisi, kendi islak-cift kapisina
         olan uzakligindan YAKINSA UYARI (goreli kural - sayi uydurulmaz).
    Yakinlik ust siniri `check_wet_area_door_proximity`de kalir; sah/baca
    bosluklari ayri bir modul olarak incelenecek (DEV-057, fikirler)."""
    warnings: list[str] = []
    walls_by_id = {w["id"]: w for w in walls}
    by_unit: dict[str, list[dict]] = {}
    for room in rooms:
        if room.get("unit_id") and room.get("room_type") in WC_ROOM_TYPES:
            by_unit.setdefault(room["unit_id"], []).append(room)
    doors = [o for o in openings if o.get("type") == "door"]

    def doors_of(room):
        out = []
        for door in doors:
            mid = _door_midpoint(door, walls_by_id)
            if mid is not None and room["id"] in {r["id"] for r in _rooms_touching_point(mid, [room])}:
                out.append((door, mid))
        return out

    for unit_id, wet in sorted(by_unit.items()):
        for i in range(len(wet)):
            for j in range(i + 1, len(wet)):
                ra, rb = wet[i], wet[j]
                if require_shared_wall and _shared_wall_length(ra["polygon"], rb["polygon"]) <= 0.0:
                    warnings.append(
                        f"Birim '{unit_id}': '{ra['id']}' ve '{rb['id']}' ortak duvar "
                        f"paylasmiyor - WC ve banyo varsayilan olarak bitisik olmali."
                    )
                da, db = doors_of(ra), doors_of(rb)
                if not da or not db:
                    continue
                dist = lambda p, q: ((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2) ** 0.5
                (door_a, mid_a), (door_b, mid_b) = min(
                    ((x, y) for x in da for y in db), key=lambda xy: dist(xy[0][1], xy[1][1]))
                if not _same_line(walls_by_id[door_a["wall_id"]], walls_by_id[door_b["wall_id"]]):
                    warnings.append(
                        f"Birim '{unit_id}': '{door_a['id']}' ve '{door_b['id']}' ayni "
                        f"hatta degil (sirt sirta/karsilikli) - WC ve banyo kapilari "
                        f"ayni hatta yan yana olmali."
                    )
                pair = dist(mid_a, mid_b)
                wet_ids = {door_a["id"], door_b["id"]}
                other = []
                for door in doors:
                    if door["id"] in wet_ids:
                        continue
                    mid = _door_midpoint(door, walls_by_id)
                    if mid is None:
                        continue
                    touching = _rooms_touching_point(mid, rooms)
                    if any(r.get("room_type") in WC_ROOM_TYPES for r in touching):
                        continue
                    plain = [r for r in touching if r.get("unit_id") == unit_id
                             and r.get("room_type") not in CIRCULATION_ROOM_TYPES
                             and r.get("room_type") not in CORE_ROOM_TYPES]
                    if plain and all(r.get("unit_id") for r in touching if r.get("room_type") not in CIRCULATION_ROOM_TYPES):
                        other.append((door, mid))
                for wet_door, wet_mid in ((door_a, mid_a), (door_b, mid_b)):
                    near = min(((dist(wet_mid, m), d) for d, m in other), default=None, key=lambda t: t[0])
                    if near is not None and near[0] < pair - 1e-6:
                        warnings.append(
                            f"Birim '{unit_id}': islak hacim kapisi '{wet_door['id']}' "
                            f"diger oda kapisina ('{near[1]['id']}') {near[0]:.0f}mm, "
                            f"kendi WC/banyo cifti ise {pair:.0f}mm - oda kapilarindan "
                            f"mumkun oldugunca uzak olmali."
                        )
    return warnings


def check_wet_area_door_proximity(
    rooms: list[dict], walls: list[dict], openings: list[dict], *,
    max_distance: float = DEFAULT_WET_AREA_DOOR_MAX_DISTANCE,
) -> list[str]:
    """[DEV-043] Ayni birimdeki ıslak hacim (banyo/wc) kapilari
    birbirinden `max_distance`den uzaksa UYARI - kullanicinin somut
    ornegi: *"banyo wc kapıları genelde yan yana olur, kapıları
    birbirinden çok uzak yapma mümkünse."* Bu ayni zamanda yaygin kabul
    goren bir tesisat ekonomisi pratigidir (islak hacimler AYNI duvar
    hatti/sahft'i paylasirsa daha ucuzdur).

    **v1 basitlestirmesi (bilerek, `check_entry_sightlines`in gorus-hatti
    basitlestirmesiyle AYNI kategoride):** yalnizca kapi-ORTA-NOKTASI
    mesafesi olculur, iki oda arasinda GERCEK bir ortak duvar (adjacency)
    olup olmadigi KONTROL EDILMEZ - bu, mesafece yakin ama araya baska bir
    oda/duvar giren bir YANLIS-POZITIF uretebilir (bkz. `DEVELOPMENT_
    TASKS.md` DEV-043 "Acik kararlar"). Esik, `standards/`in kataloguyla
    AYNI disiplinde bir "pratik varsayilan"dir, metre hassasiyetinde bir
    olcum DEGIL."""
    warnings: list[str] = []
    walls_by_id = {w["id"]: w for w in walls}
    wet_rooms_by_unit: dict[str, list[dict]] = {}
    for room in rooms:
        unit_id = room.get("unit_id")
        if unit_id and room.get("room_type") in WC_ROOM_TYPES:
            wet_rooms_by_unit.setdefault(unit_id, []).append(room)

    doors = [o for o in openings if o.get("type") == "door"]
    for unit_id, wet_rooms in sorted(wet_rooms_by_unit.items()):
        wet_ids = {r["id"] for r in wet_rooms}
        wet_doors: list[tuple[str, tuple[float, float]]] = []
        for door in doors:
            point = _door_midpoint(door, walls_by_id)
            if point is None:
                continue
            touching_ids = {r["id"] for r in _rooms_touching_point(point, wet_rooms)}
            if touching_ids & wet_ids:
                wet_doors.append((door["id"], point))

        for i in range(len(wet_doors)):
            for j in range(i + 1, len(wet_doors)):
                door_a, point_a = wet_doors[i]
                door_b, point_b = wet_doors[j]
                dist = ((point_a[0] - point_b[0]) ** 2
                        + (point_a[1] - point_b[1]) ** 2) ** 0.5
                if dist > max_distance:
                    warnings.append(
                        f"Birim '{unit_id}': ıslak hacim kapıları '{door_a}' "
                        f"ve '{door_b}' birbirinden {dist:.0f}mm uzakta "
                        f"(izin verilen üst sınır {max_distance:.0f}mm) - "
                        f"tesisat ekonomisi için yakın olmaları tercih edilir."
                    )
    return warnings


def check_common_circulation_share(
    rooms: list[dict], *, max_share: float = DEFAULT_CIRCULATION_SHARE_MAX,
) -> list[str]:
    """[DEV-045] `check_circulation_area_share`in BİNA/KAT SEVİYESİNE
    genellenmesi: ORTAK sirkülasyon alanı (hiçbir `unit_id` TAŞIMAYAN,
    `room_type='koridor'` odalar - örn. ortak kat koridoru/`band`),
    kattaki TÜM birimlerin (`unit_id`li odalar) TOPLAM net alanının
    `max_share` oranını aşarsa UYARI.

    Kullanıcının somut örneği: *"şu anda örnek planımızda kat planında
    sağ üstteki alan tamamıyla ölü bir alan."* Bu kural o alanı DOĞRUDAN
    ÖLÇMEZ (hangi bölgenin "ölü" olduğunu bilmez - yalnızca GEOMETRİ
    okur) ama AYNI sonucu dolaylı yakalar: gereksiz yere büyütülmüş bir
    ortak koridor, TOPLAM payını şişirir. `templates::generate_
    circulation_core`nin DEV-045 düzeltmesi (`scripts/templates/
    CLAUDE.md` "DEV-045 düzeltmesi") bu payı GERÇEKTEN küçültür - Fikir 1
    (bu fonksiyon) DENETLER, Fikir 2 (template düzeltmesi) DÜZELTİR,
    `standards`+`templates` ikilisinin DEV-036/037'deki ilişkisiyle AYNI
    desen.

    **`check_circulation_area_share`dan FARKI:** o fonksiyon HER birimin
    KENDİ hol'ünü (`unit_id`li bir koridor odası) birimin KENDİ net
    alanına göre ölçer (birim-içi); bu fonksiyon `unit_id`SİZ (ortak)
    koridor odalarını TÜM birimlerin TOPLAM alanına göre ölçer (bina-
    seviyesi) - ikisi AYNI ANDA, farklı payları test eder, biri diğerinin
    yerini TUTMAZ."""
    warnings: list[str] = []
    total_unit_area = sum(r["area_m2"] for r in rooms if r.get("unit_id"))
    common_circulation = sum(
        r["area_m2"] for r in rooms
        if not r.get("unit_id") and r.get("room_type") == "koridor"
    )
    if total_unit_area <= 0 or common_circulation <= 0:
        return warnings
    share = common_circulation / total_unit_area
    if share > max_share:
        warnings.append(
            f"Ortak sirkülasyon alanı, kattaki birimlerin toplam net "
            f"alanının %{share * 100:.1f}'i, izin verilen üst sınır "
            f"%{max_share * 100:.1f} aşıldı (ortak koridor="
            f"{common_circulation:.1f} m2, birimler toplamı="
            f"{total_unit_area:.1f} m2)."
        )
    return warnings


__all__ = [
    "DEFAULT_CIRCULATION_SHARE_MAX", "DEFAULT_DOOR_CORE_BALANCE_RATIO",
    "DEFAULT_SIGHTLINE_CONE_DEGREES", "DEFAULT_WET_AREA_DOOR_MAX_DISTANCE",
    "WC_ROOM_TYPES", "CORE_ROOM_TYPES", "CIRCULATION_ROOM_TYPES",
    "BEDROOM_ROOM_TYPES", "check_circulation_area_share",
    "check_bedroom_via_corridor", "check_entry_sightlines",
    "check_door_core_balance", "check_wet_area_reachable_without_bedroom",
    "check_wet_area_door_proximity", "check_common_circulation_share",
]


# --- DEV-050: kapi/pencere iliskisel nuanslar (madde 4, 12, 13, 14) --------
# HEPSI UYARI; unit_id/room_type OPT-IN (alan yoksa kontrole girmez).

def _wall_unit_normal(wall: dict) -> tuple[float, float] | None:
    dx, dy = wall["end"][0] - wall["start"][0], wall["end"][1] - wall["start"][1]
    length = (dx * dx + dy * dy) ** 0.5
    return None if length == 0 else (-dy / length, dx / length)


def _door_swing_target(door: dict, walls_by_id: dict, rooms: list[dict]) -> dict | None:
    """Kapi kanadinin ACILDIGI oda (host_side: 'pos' = duvar normali +).
    Surme/katlanir kapi icin `None` (kanat odaya donmez)."""
    if door.get("variant", "single") in ("sliding", "folding"):
        return None
    wall = walls_by_id.get(door.get("wall_id"))
    mid = _door_midpoint(door, walls_by_id)
    normal = _wall_unit_normal(wall) if wall else None
    if mid is None or normal is None:
        return None
    sign = 1.0 if door.get("host_side", "pos") == "pos" else -1.0
    probe = (mid[0] + normal[0] * sign * _SWING_PROBE_MM, mid[1] + normal[1] * sign * _SWING_PROBE_MM)
    for room in rooms:
        if point_in_polygon(probe, room["polygon"]):
            return room
    return None


def check_wet_door_swing_inward(rooms: list[dict], walls: list[dict],
                                openings: list[dict]) -> list[str]:
    """[madde 12] WC/Banyo kapisi VARSAYILAN olarak kendi hacmine acilir;
    hole/baska odaya dogru aciliyorsa UYARI."""
    warnings: list[str] = []
    walls_by_id = {w["id"]: w for w in walls}
    for door in (o for o in openings if o.get("type") == "door"):
        mid = _door_midpoint(door, walls_by_id)
        if mid is None:
            continue
        wet = [r for r in _rooms_touching_point(mid, rooms) if r.get("room_type") in WC_ROOM_TYPES]
        if not wet:
            continue
        target = _door_swing_target(door, walls_by_id, rooms)
        if target is not None and target["id"] not in {r["id"] for r in wet}:
            warnings.append(
                f"'{wet[0]['id']}' kapisi ('{door['id']}') kendi hacmine degil "
                f"'{target['id']}' alanina aciliyor - varsayilan olarak WC/Banyo "
                f"kapisi icine acilir."
            )
    return warnings


def check_entry_door_swing_inward(rooms: list[dict], walls: list[dict],
                                  openings: list[dict]) -> list[str]:
    """[madde 13] Daire giris kapisi kendi birimine ICE acilmali; ortak
    hole (unit_id'siz oda) aciliyorsa UYARI."""
    warnings: list[str] = []
    walls_by_id = {w["id"]: w for w in walls}
    for door in (o for o in openings if o.get("type") == "door"):
        mid = _door_midpoint(door, walls_by_id)
        if mid is None:
            continue
        touching = _rooms_touching_point(mid, rooms)
        if not any(r.get("unit_id") for r in touching) or not any(not r.get("unit_id") for r in touching):
            continue  # giris kapisi: birim <-> ortak alan
        target = _door_swing_target(door, walls_by_id, rooms)
        if target is not None and not target.get("unit_id"):
            warnings.append(
                f"Giris kapisi '{door['id']}' ortak alana ('{target['id']}') "
                f"aciliyor - daire giris kapisi kendi birimine ice acilmali."
            )
    return warnings


def check_kitchen_wet_door_opposite(
    rooms: list[dict], walls: list[dict], openings: list[dict], *,
    tolerance: float = DEFAULT_DOOR_AXIS_ALIGN_TOLERANCE_MM,
) -> list[str]:
    """[madde 14] Ayni birimdeki mutfak kapisi ile WC/Banyo kapisi, ayni
    holde PARALEL duvarlarda ve duvar normali boyunca (tolerans icinde)
    KARSI KARSIYA ise (arada engel yoksa) UYARI. Kullanicinin ornegi:
    mutfak kapisinin onunde wc olmamali."""
    warnings: list[str] = []
    walls_by_id = {w["id"]: w for w in walls}
    entries = []  # (door, mid, wall, normal, kind, unit_id, touching_ids)
    for door in (o for o in openings if o.get("type") == "door"):
        mid = _door_midpoint(door, walls_by_id)
        wall = walls_by_id.get(door.get("wall_id"))
        if mid is None or wall is None:
            continue
        touching = _rooms_touching_point(mid, rooms)
        for room in touching:
            kind = ("mutfak" if room.get("room_type") in KITCHEN_ROOM_TYPES
                    else "wet" if room.get("room_type") in WC_ROOM_TYPES else None)
            if kind and room.get("unit_id"):
                entries.append((door, mid, wall, kind, room["unit_id"],
                                {r["id"] for r in touching if r["id"] != room["id"]}))
    for i, (da, ma, wa, ka, ua, ta) in enumerate(entries):
        if ka != "mutfak":
            continue
        for (db, mb, wb, kb, ub, tb) in entries:
            if kb != "wet" or ub != ua or da["id"] == db["id"] or not (ta & tb):
                continue
            na, nb = _wall_unit_normal(wa), _wall_unit_normal(wb)
            if na is None or nb is None or abs(na[0] * nb[1] - na[1] * nb[0]) > 1e-3:
                continue  # paralel duvar degil
            v = (mb[0] - ma[0], mb[1] - ma[1])
            across = abs(v[0] * na[0] + v[1] * na[1])
            along = abs(-v[0] * na[1] + v[1] * na[0])
            if across < 1.0 or along > tolerance:
                continue
            if _clear_line_of_sight(ma, mb, walls, {wa["id"], wb["id"]}):
                warnings.append(
                    f"Mutfak kapisi ('{da['id']}') ile WC/Banyo kapisi ('{db['id']}') "
                    f"ayni eksende karsi karsiya ({along:.0f}mm kayik) - "
                    f"mutfak kapisindan wc'ye gorus olmamali."
                )
    return warnings


def check_wet_door_window_gap(
    rooms: list[dict], walls: list[dict], openings: list[dict], *,
    min_gap: float = DEFAULT_WET_DOOR_WINDOW_MIN_GAP_MM,
) -> list[str]:
    """[madde 4] Islak hacim kapisi ile AYNI duvardaki pencere arasindaki
    duz duvar boslugu `min_gap`ten azsa UYARI."""
    warnings: list[str] = []
    walls_by_id = {w["id"]: w for w in walls}
    for door in (o for o in openings if o.get("type") == "door"):
        mid = _door_midpoint(door, walls_by_id)
        if mid is None or not any(r.get("room_type") in WC_ROOM_TYPES for r in _rooms_touching_point(mid, rooms)):
            continue
        for win in (o for o in openings if o.get("type") == "window" and o.get("wall_id") == door["wall_id"]):
            gap = abs(win["position_from_start"] - door["position_from_start"]) - (win["width"] + door["width"]) / 2.0
            if gap < min_gap:
                warnings.append(
                    f"Islak hacim kapisi '{door['id']}' ile pencere '{win['id']}' arasi "
                    f"{max(gap, 0.0):.0f}mm, asgari {min_gap:.0f}mm."
                )
    return warnings


DEFAULT_SWING_POLICY = "into_room"


def check_doors_open_into_rooms(
    rooms: list[dict], walls: list[dict], openings: list[dict], *,
    swing_policy: str = DEFAULT_SWING_POLICY,
) -> list[str]:
    """[DEV-051] Kullanici karari (2026-10-05): KONUT icin varsayilan, kapilarin
    ODALARA dogru acilmasidir (hole/koridora degil). Hastane/otel gibi kacis
    planli yapilar ileride `swing_policy` ile ayri incelenecek; `"any"` bu
    kontrolu kapatir. Kapsam: tam olarak BIR sirkulasyon (koridor) ve BIR
    normal oda arasindaki kapi. Islak hacim (madde 12) ve giris kapisi
    (madde 13, birim<->ortak alan) o kurallarda ZATEN denetlendiginden burada
    TEKRARLANMAZ; cekirdek (asansor/merdiven) kapilari atlanir."""
    if swing_policy != DEFAULT_SWING_POLICY:
        return []
    warnings: list[str] = []
    walls_by_id = {w["id"]: w for w in walls}
    for door in (o for o in openings if o.get("type") == "door"):
        mid = _door_midpoint(door, walls_by_id)
        if mid is None:
            continue
        touching = _rooms_touching_point(mid, rooms)
        circ = [r for r in touching if r.get("room_type") in CIRCULATION_ROOM_TYPES]
        plain = [r for r in touching if r.get("room_type") not in CIRCULATION_ROOM_TYPES
                 and r.get("room_type") not in CORE_ROOM_TYPES and r.get("room_type") not in WC_ROOM_TYPES]
        if len(circ) != 1 or len(plain) != 1 or len(touching) != 2:
            continue
        if plain[0].get("room_type") in COMMERCIAL_ROOM_TYPES:
            continue  # ticari birim: check_commercial_door_swing
        if plain[0].get("unit_id") and not circ[0].get("unit_id"):
            continue  # giris kapisi: madde 13
        target = _door_swing_target(door, walls_by_id, rooms)
        if target is not None and target["id"] == circ[0]["id"]:
            warnings.append(
                f"Kapi '{door['id']}' odaya ('{plain[0]['id']}') degil "
                f"'{circ[0]['id']}' sirkulasyon alanina aciliyor - konutta "
                f"kapilar odalara dogru acilmali."
            )
    return warnings


def check_commercial_door_swing(
    rooms: list[dict], walls: list[dict], openings: list[dict], *,
    shop_swing_policy: str = DEFAULT_COMMERCIAL_SWING_POLICY,
) -> list[str]:
    """[DEV-051 ek karar] Dukkan (`room_type='dukkan'`) konut sayilmaz ve AYRI
    islenir. Varsayilan: dukkan <-> ortak alan kapisi kacis yonunde, yani
    DISARI (ortak alana) acilir; ice acilirsa UYARI. Hastane/otel gibi diger
    ticari/kamusal yapilarin kacis planlari ileride ayri incelenecek;
    `shop_swing_policy="any"` kapatir. `unit_id` aranmaz (dukkan birim
    degildir); yalnizca `room_type` opt-in'dir."""
    if shop_swing_policy != DEFAULT_COMMERCIAL_SWING_POLICY:
        return []
    warnings: list[str] = []
    walls_by_id = {w["id"]: w for w in walls}
    for door in (o for o in openings if o.get("type") == "door"):
        mid = _door_midpoint(door, walls_by_id)
        if mid is None:
            continue
        touching = _rooms_touching_point(mid, rooms)
        shops = [r for r in touching if r.get("room_type") in COMMERCIAL_ROOM_TYPES]
        others = [r for r in touching if r.get("room_type") not in COMMERCIAL_ROOM_TYPES]
        if len(shops) != 1 or len(others) != 1:
            continue
        target = _door_swing_target(door, walls_by_id, rooms)
        if target is not None and target["id"] == shops[0]["id"]:
            warnings.append(
                f"Dukkan kapisi '{door['id']}' dukkana ('{shops[0]['id']}') ice "
                f"aciliyor - ticari birimde kapi kacis yonunde, ortak alana "
                f"('{others[0]['id']}') acilmali."
            )
    return warnings


def check_door_window_nuances(rooms: list[dict], walls: list[dict],
                              openings: list[dict]) -> list[str]:
    return (
        check_doors_open_into_rooms(rooms, walls, openings)
        + check_commercial_door_swing(rooms, walls, openings)
        + check_wet_door_window_gap(rooms, walls, openings)
        + check_wet_door_swing_inward(rooms, walls, openings)
        + check_entry_door_swing_inward(rooms, walls, openings)
        + check_kitchen_wet_door_opposite(rooms, walls, openings)
    )
