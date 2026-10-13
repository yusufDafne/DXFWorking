"""Alternatif anlatimi (DEV-083): sablon + olculmus yer-tutucu. Rakam YALNIZ `{olcum:ad}` yer-tutucusundan gelir (sablon metninde rakam yasak)."""
from __future__ import annotations

import re
import unicodedata

PLACEHOLDER = re.compile(r"\{olcum:([a-z_][a-z0-9_]*)\}")
FACE_TR = {"ust": "ust", "sag": "sag", "alt": "alt", "sol": "sol"}
AXIS_PHRASE = {
    "road_proximity": "yola en yakin duran secenek",
    "neighbor_clearance": "yol disindaki komsu sinirlardan en uzak duran secenek",
    "light_south": "uzun cepheleri en cok guneye donuk secenek",
    "zone_fit": "istenen yerlesim bolgesine en iyi oturan secenek",
}

LINES = (
    ("road_distance_mm", "Bina yola {olcum:road_distance_mm} mm uzakliktadir; yola {olcum:road_face} cephesiyle bakar."),
    ("min_other_edge_distance_mm", "Yol disindaki parsel sinirlarina en az {olcum:min_other_edge_distance_mm} mm uzaktadir."),
    ("buildable_margin_mm", "Yapilasma alani sinirina {olcum:buildable_margin_mm} mm payi vardir."),
    ("long_face_south_deviation_deg", "Uzun cepheler guneyden en fazla {olcum:long_face_south_deviation_deg} derece sapmaktadir."),
    ("zone_overlap_ratio", "Istenen yerlesim bolgesiyle ortusme orani {olcum:zone_overlap_ratio}."),
    ("garden_pieces", "Bahce {olcum:garden_pieces} parcadir."),
)


def lint_template(text: str) -> list[str]:
    """Sablon hatalari (bos = temiz): yer-tutucu disinda RAKAM (Unicode Nd/No/Nl) yasak."""
    bare = PLACEHOLDER.sub("", text)
    bad = sorted({ch for ch in bare if unicodedata.category(ch) in ("Nd", "No", "Nl")})
    return [f"sablonda dogrudan rakam var: {bad}"] if bad else []


def _fmt(name: str, value) -> str:
    if isinstance(value, str):
        return value
    if name.endswith("_ratio"):
        return f"{value:.2f}".replace(".", ",")
    if name.endswith("_deg") or name.endswith("_mm"):
        return f"{round(value):d}"
    return f"{round(value):d}" if float(value) == round(value) else f"{value:.2f}"


def render(template: str, values: dict) -> str:
    errs = lint_template(template)
    if errs:
        raise ValueError("; ".join(errs))

    def sub(m):
        if m.group(1) not in values:
            raise KeyError(f"olcum yok: {m.group(1)} (deger uydurulmaz)")
        return _fmt(m.group(1), values[m.group(1)])
    return PLACEHOLDER.sub(sub, template)


def narrate_alternative(alt) -> list[str]:
    """Bir alternatifin anlatimi: baslik (neden secildi) + olculen cumleler. Veri olmayan olcumun cumlesi YAZILMAZ."""
    values = {m.name: m.value for m in alt.measurements}
    if alt.reason.startswith("best:"):
        head = f"{alt.id}: {AXIS_PHRASE[alt.reason[5:]]}."
    elif alt.reason == "diversity":
        head = f"{alt.id}: onceki secenekler arasinda temsil edilmeyen, farkli bir odunlesim sunan secenek."
    else:
        head = f"{alt.id}: istediginiz agirliklara gore bu siradaki secenek."
    lines = [head]
    for key, tpl in LINES:
        if key in values:
            lines.append("  " + render(tpl, values))
    if alt.outside_zone:
        lines.append("  Dikkat: istenen yerlesim bolgesinin disina tasiyor (bolge yaklasik bir istektir).")
    return lines
