"""Cakisma denetiminin SAF GEOMETRI cekirdegi.

Bu dosya projedeki poligon matematiginin TEK sahibidir. rev-12'den once ayni
Sutherland-Hodgman kirpmasinin bir KOPYASI `validate.py` icinde duruyordu;
iki kopya zamanla ayrisir ve "oda cakismasi" ile "tefris cakismasi" farkli
cevaplar vermeye baslardi. Artik `validate.py` de buradan tuketir.

Burada ezdxf YOKTUR ve hicbir cizim modulu import EDILMEZ: cakisma denetimi
context seviyesinde, DXF uretilmeden once calisir.
"""
from __future__ import annotations

Point = tuple[float, float]


def as_points(polygon) -> list[Point]:
    """[x, y] listesi veya (x, y) demeti farketmeksizin normalize eder."""
    return [(float(p[0]), float(p[1])) for p in polygon]


def polygon_area(polygon) -> float:
    """Shoelace ile mutlak alan. Sarim yonunden bagimsizdir."""
    points = as_points(polygon)
    if len(points) < 3:
        return 0.0
    total = 0.0
    for i in range(len(points)):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % len(points)]
        total += x1 * y2 - x2 * y1
    return abs(total) / 2.0


def signed_area(polygon) -> float:
    points = as_points(polygon)
    total = 0.0
    for i in range(len(points)):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % len(points)]
        total += x1 * y2 - x2 * y1
    return total / 2.0


def aabb(polygon) -> tuple[float, float, float, float]:
    """Eksen hizali sinir kutusu: (min_x, min_y, max_x, max_y)."""
    points = as_points(polygon)
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return min(xs), min(ys), max(xs), max(ys)


def aabb_overlap(box_a, box_b, tolerance: float = 0.0) -> bool:
    """Kaba faz: iki sinir kutusu birbirine deger mi?

    `tolerance` kadar bir pay birakilir; kutular bu paydan daha uzaksa ince
    faza hic girilmez. Kaba fazin amaci N^2 poligon kirpmasindan kacinmaktir.
    """
    ax0, ay0, ax1, ay1 = box_a
    bx0, by0, bx1, by1 = box_b
    if ax1 + tolerance < bx0 or bx1 + tolerance < ax0:
        return False
    if ay1 + tolerance < by0 or by1 + tolerance < ay0:
        return False
    return True


def min_extent(polygon) -> float:
    """Poligonun sinir kutusunun KISA kenari.

    Bir kesisim poligonunun "ince bir dilim" mi yoksa gercek bir girisim mi
    oldugunu ayirmak icin kullanilir (bkz. `matrix.CONTACT_TOLERANCE`).
    Eksen hizali olcum, egik bir dilimi gercek kalinligindan KALIN gosterir;
    yani hata payi HER ZAMAN "daha cok bildir" yonundedir, sessiz kalma
    yonunde degil.
    """
    min_x, min_y, max_x, max_y = aabb(polygon)
    return min(max_x - min_x, max_y - min_y)


def is_convex(polygon) -> bool:
    """Disbukeylik testi. `polygon_clip` KIRPAN poligonun disbukey olmasini
    gerektirdigi icin gereklidir."""
    points = as_points(polygon)
    if len(points) < 4:
        return True
    sign = 0
    n = len(points)
    for i in range(n):
        ax, ay = points[i]
        bx, by = points[(i + 1) % n]
        cx, cy = points[(i + 2) % n]
        cross = (bx - ax) * (cy - by) - (by - ay) * (cx - bx)
        if abs(cross) < 1e-9:
            continue
        current = 1 if cross > 0 else -1
        if sign == 0:
            sign = current
        elif current != sign:
            return False
    return True


def polygon_clip(subject, clip) -> list[Point]:
    """Sutherland-Hodgman: `subject` poligonunun `clip` icinde kalan parcasi.

    KISIT: `clip` DISBUKEY olmalidir. Varsayilan politika matrisinde alan
    kesisimi hesaplanan her cift (tefris, kolon, duvar dikdortgeni, kapi
    acilim sektoru) disbukeydir. Icbukey olabilen tek sekil ODA poligonudur ve
    o yalnizca ICERME testinde (`point_in_polygon`) kullanilir - orada
    disbukeylik gerekmez.
    """
    output = as_points(subject)
    clip_pts = as_points(clip)
    if signed_area(clip_pts) < 0:
        clip_pts = list(reversed(clip_pts))

    def inside(p, a, b) -> bool:
        return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]) >= 0

    def intersect(p1, p2, a, b) -> Point:
        a1 = (b[0] - a[0]) * (p1[1] - a[1]) - (b[1] - a[1]) * (p1[0] - a[0])
        a2 = (b[0] - a[0]) * (p2[1] - a[1]) - (b[1] - a[1]) * (p2[0] - a[0])
        t = a1 / (a1 - a2)
        return (p1[0] + t * (p2[0] - p1[0]), p1[1] + t * (p2[1] - p1[1]))

    for i in range(len(clip_pts)):
        if not output:
            break
        a = clip_pts[i]
        b = clip_pts[(i + 1) % len(clip_pts)]
        source, output = output, []
        for j in range(len(source)):
            current = source[j]
            previous = source[j - 1]
            current_in = inside(current, a, b)
            previous_in = inside(previous, a, b)
            if current_in:
                if not previous_in:
                    output.append(intersect(previous, current, a, b))
                output.append(current)
            elif previous_in:
                output.append(intersect(previous, current, a, b))
    return output


def polygon_intersection_area(subject, clip) -> float:
    """Kesisim alani. `clip` disbukey olmalidir (bkz. `polygon_clip`)."""
    result = polygon_clip(subject, clip)
    if len(result) < 3:
        return 0.0
    return polygon_area(result)


def point_in_polygon(point, polygon) -> bool:
    """Isin atma (ray casting). ICBUKEY poligonlarda da dogru calisir; oda
    icinde kalma testi bu yuzden bunu kullanir."""
    px, py = float(point[0]), float(point[1])
    points = as_points(polygon)
    inside = False
    n = len(points)
    for i in range(n):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % n]
        if (y1 > py) != (y2 > py):
            x_cross = x1 + (py - y1) * (x2 - x1) / (y2 - y1)
            if x_cross > px:
                inside = not inside
    return inside


def point_on_boundary(point, polygon, tolerance: float) -> bool:
    """Nokta poligon KENARI uzerinde mi (tolerans bandi icinde)?

    Duvara tam dayali bir tefrisin kosesi oda poligonunun kenarina birebir
    oturur; `point_in_polygon` bu durumda kenari 'disarida' sayabilir. Icerme
    testi bu yuzden kenar toleransiyla birlikte kullanilir.
    """
    px, py = float(point[0]), float(point[1])
    points = as_points(polygon)
    n = len(points)
    for i in range(n):
        ax, ay = points[i]
        bx, by = points[(i + 1) % n]
        dx, dy = bx - ax, by - ay
        length_sq = dx * dx + dy * dy
        if length_sq == 0:
            continue
        t = ((px - ax) * dx + (py - ay) * dy) / length_sq
        t = max(0.0, min(1.0, t))
        cx, cy = ax + t * dx, ay + t * dy
        if (px - cx) ** 2 + (py - cy) ** 2 <= tolerance * tolerance:
            return True
    return False


def point_inside_or_on(point, polygon, tolerance: float) -> bool:
    return (point_in_polygon(point, polygon)
            or point_on_boundary(point, polygon, tolerance))


# `validate.py` rev-12'den once kendi kopyasini tasiyordu; ad korunuyor ki
# cagri yerleri degismesin.
shoelace_area = polygon_area
