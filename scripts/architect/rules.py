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
    from ..collision.geometry import point_on_boundary
except ImportError:
    from collision.geometry import point_on_boundary

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

WC_ROOM_TYPES = frozenset({"wc", "banyo"})
CORE_ROOM_TYPES = frozenset({"asansor", "merdiven"})
CIRCULATION_ROOM_TYPES = frozenset({"koridor"})
BEDROOM_ROOM_TYPES = frozenset({"yatak_odasi"})

# Oda-kapi komsulugu ararken kullanilan tolerans (mm). Bu projede duvar
# kalinligi 200mm ve oda poligonlari cogunlukla duvar MERKEZ cizgisiyle
# ayni koordinatta tanimlanir (bkz. templates::generate_circulation_core);
# 300mm hem merkez-hizali hem ic-yuz-hizali odalari guvenle yakalar.
_TOUCH_TOLERANCE_MM = 300.0


def _door_midpoint(door: dict, walls_by_id: dict) -> tuple[float, float] | None:
    wall = walls_by_id.get(door.get("wall_id"))
    if wall is None:
        return None
    sx, sy = wall["start"]
    ex, ey = wall["end"]
    length = ((ex - sx) ** 2 + (ey - sy) ** 2) ** 0.5
    if length == 0:
        return (sx, sy)
    t = door["position_from_start"] / length
    return (sx + t * (ex - sx), sy + t * (ey - sy))


def _rooms_touching_point(point: tuple[float, float], rooms: list[dict],
                          tolerance: float = _TOUCH_TOLERANCE_MM) -> list[dict]:
    return [r for r in rooms if point_on_boundary(point, r["polygon"], tolerance)]


def _centroid(polygon: list[list[float]]) -> tuple[float, float]:
    xs = [p[0] for p in polygon]
    ys = [p[1] for p in polygon]
    return (sum(xs) / len(xs), sum(ys) / len(ys))


def _segments_intersect(p1, p2, p3, p4) -> bool:
    """Iki dogru parcasi GERCEKTEN (uc noktalarda DEGIL) kesisiyor mu -
    standart yon (cross-product) testi. Uc noktalarda dokunma KASITLI
    olarak KESISIM SAYILMAZ: goru hattinin kendi baslangic/bitis
    noktalari zaten bir duvarin UZERINDEDIR (kapinin oturdugu duvar),
    bu durum bir ENGEL degildir."""
    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    d1 = cross(p3, p4, p1)
    d2 = cross(p3, p4, p2)
    d3 = cross(p1, p2, p3)
    d4 = cross(p1, p2, p4)
    return ((d1 > 0 > d2 or d1 < 0 < d2)
            and (d3 > 0 > d4 or d3 < 0 < d4))


def _clear_line_of_sight(a: tuple[float, float], b: tuple[float, float],
                          walls: list[dict], exclude_wall_ids: set[str]) -> bool:
    """`a`-`b` dogru parcasi, `exclude_wall_ids` DISINDAKI herhangi bir
    duvarin MERKEZ CIZGISINI kesiyor mu? (duvar ayak izi merkez cizgidir -
    `collision/CLAUDE.md`deki AYNI bilinen basitlestirme)."""
    for wall in walls:
        if wall["id"] in exclude_wall_ids:
            continue
        if _segments_intersect(a, b, tuple(wall["start"]), tuple(wall["end"])):
            return False
    return True


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


__all__ = [
    "DEFAULT_CIRCULATION_SHARE_MAX", "DEFAULT_DOOR_CORE_BALANCE_RATIO",
    "DEFAULT_SIGHTLINE_CONE_DEGREES", "DEFAULT_WET_AREA_DOOR_MAX_DISTANCE",
    "WC_ROOM_TYPES", "CORE_ROOM_TYPES", "CIRCULATION_ROOM_TYPES",
    "BEDROOM_ROOM_TYPES", "check_circulation_area_share",
    "check_bedroom_via_corridor", "check_entry_sightlines",
    "check_door_core_balance", "check_wet_area_reachable_without_bedroom",
    "check_wet_area_door_proximity",
]
