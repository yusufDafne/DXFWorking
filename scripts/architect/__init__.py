"""architect modulu (DEV-039): mimarin GERCEK anlamda yaptigi isi yapan
modul - oda/koridor/wc/mutfak vb. yerlesiminin birbirine GORE (arity-2+)
mantikli olup olmadigini denetler VE bir oda programinin verilen alana
nasil YERLESTIRILEBILECEGINE dair yapilandirilmis secenekler sunar.

**Kullanici talebi (2026-09-28):** "bu modul, mimarin gercek anlamda
yaptigi isi yapacak aslinda, planlama ... gercek bir mimar gibi dusunup
oda, koridor, wc, mutfak vs. her seyin planini endustri standardina
uygun bicimde yapacak." Uc somut ornek verdi: bir dairenin kapisi
DOGRUDAN merdivene aciliyorken digerlerinin daha izole bir yere acilmasi
("kapi-cekirdek dengesizligi"), daire kapisindan girince KARSIDA wc
kapisi gorunmesi ("giris-wc goru hatti"), hol'un buyutulup diger odalarin
kucultulmesi ("hol optimum, digerleri oncelikli").

**Arity ayrimi (kok CLAUDE.md/collision'in AYNI ilkesi):** `standards/`
bir odanin KENDI oraninin makul olup olmadigini denetler (arity-1); bu
modul iki/N elemanin BIRBIRINE GORE mantikli olup olmadigini denetler
(arity-2+) - collision'in rooms/'den ayrilmasiyla BIREBIR AYNI gerekce,
sadece konusu fiziksel CAKISMA degil mimari SAGDUYU.

**Ic yapi (DEV-039, kullanici onayli, 2026-09-28 ucuncu tur):** etut ->
mimari iki asamali bir boru hattidir, TEK modulde dort dosya:

  - `rules.py`  - iliskisel WARN kurallari (arity-2+, standards'in WARN
    felsefesiyle AYNI disiplin)
  - `study.py`  - etut asamasi: oda programi sigma kontrolu (DEV-038
    buraya ABSORBE edildi) + kaba (1D) bolge/zone atamasi
  - `options.py`- secenek katalogu: dil modelinin "o anki duruma gore
    hangi secenekler GECERLI" diye SORABILECEGI, ON-PUANLANMIS bir liste
  - `design.py` - mimari asamasi: zonlama planindan kapi KARARI (gercek
    geometriyi KENDISI cizmez)

**v1 kapsami TAMAMI bastan (kademeli DEGIL, kullanici karari):** kapi-
cekirdek dengesizligi, giris-wc goru hatti, hol/sirkulasyon alan payi (+
olculebilir esik alt-kurali), yatak odasinin salon uzerinden degil hol
uzerinden erisilmesi. Merdiven/asansor "efektif" yerlesimi `options.py`
uzerinden cozulur (bir check_* fonksiyonu DEGILDIR, karar-destek
mekanizmasidir).

**Yeni sema alani: `rooms[].unit_id`** - hangi odanin hangi bagimsiz
bolume/daireye ait oldugunu ACIKCA bildirir (eskiden yalnizca `uA_`/`uB_`/
`uC_` id-onek konvansiyonuyla ORTUK idi). Bu modulun TUM iliskisel
kurallari `unit_id` OPT-IN'dir - verilmeyen odalar kontrole HIC GIRMEZ
(`room_type` ile AYNI desen). Kullanicinin kendi gerekcesi: bu alan
DEV-039'un otesinde bir ALTYAPI ihtiyaci - gelecekteki "emsal" (imar alani
orani) hesabi da AYNI guvenilir gruplamaya bagimli olacak.

Detay: `scripts/architect/CLAUDE.md`.
"""
from __future__ import annotations

from .design import place_unit_entry_doors
from .options import CORNERS, PlacementOption, options_for_core_placement
from .rules import (
    BEDROOM_ROOM_TYPES,
    CIRCULATION_ROOM_TYPES,
    CORE_ROOM_TYPES,
    DEFAULT_CIRCULATION_SHARE_MAX,
    DEFAULT_DOOR_CORE_BALANCE_RATIO,
    DEFAULT_SIGHTLINE_CONE_DEGREES,
    DEFAULT_WET_AREA_DOOR_MAX_DISTANCE,
    WC_ROOM_TYPES,
    check_bedroom_via_corridor,
    check_commercial_door_swing,
    check_door_window_nuances,
    check_doors_open_into_rooms,
    check_entry_door_swing_inward,
    check_kitchen_wet_door_opposite,
    check_wet_area_adjacency,
    check_wet_door_swing_inward,
    check_wet_door_window_gap,
    check_circulation_area_share,
    check_common_circulation_share,
    check_door_core_balance,
    check_entry_sightlines,
    check_entry_wet_door_proximity,
    check_wet_area_door_proximity,
    check_wet_area_reachable_without_bedroom,
)
from .core_hall import CentralHallOption, HALL_ALTERNATIVES, options_for_central_hall
from .layout import (
    CURRENT_PROJECT_PROGRAM,
    StudyOption,
    StudyPreference,
    StudySelection,
    StudyWeights,
    UNIT_TYPES,
    UnitType,
    ZonePlan,
    study_floor,
    select_study_option,
    study_and_select,
    suggest_unit_mixes,
)
from .topology import (
    DEFAULT_TOPOLOGIES,
    HallOption,
    TOPOLOGY_BUILDERS,
    options_for_hall_topology,
    register_topology,
)
from .study import (
    FeasibilityReport,
    ZoneAssignment,
    ZoningPlan,
    check_fits,
    resolve_unit_zoning,
)

# Bu modulun CONTEXT SOZLESMESI surumu (DEV-020). Yalnizca bu paketin
# context.json'dan OKUDUGU alan (rooms[].unit_id; rooms[].room_type
# ZATEN standards'in sozlestigi alandir) veya check_*/resolve_*
# fonksiyonlarinin DONUS SEKLI degisirse artar - katalog SABITLERI
# (DEFAULT_CIRCULATION_SHARE_MAX gibi) standards.STANDARDS ile AYNI
# disiplinde SERBESTCE degisir, surum artirmaz.
CONTRACT_VERSION = "1.0"

__all__ = [
    "study_and_select",
    "StudyPreference", "StudySelection", "select_study_option",
    "CURRENT_PROJECT_PROGRAM", "StudyOption", "StudyWeights", "UNIT_TYPES",
    "UnitType", "ZonePlan", "study_floor", "suggest_unit_mixes",
    "CentralHallOption", "HALL_ALTERNATIVES", "options_for_central_hall",
    "DEFAULT_TOPOLOGIES", "HallOption", "TOPOLOGY_BUILDERS",
    "options_for_hall_topology", "register_topology",
    "check_entry_wet_door_proximity",
    "check_wet_area_adjacency",
    "check_commercial_door_swing",
    "check_doors_open_into_rooms",
    "check_door_window_nuances", "check_entry_door_swing_inward",
    "check_kitchen_wet_door_opposite", "check_wet_door_swing_inward",
    "check_wet_door_window_gap",
    "check_circulation_area_share", "check_bedroom_via_corridor",
    "check_entry_sightlines", "check_door_core_balance",
    "check_wet_area_reachable_without_bedroom", "check_wet_area_door_proximity",
    "check_common_circulation_share",
    "DEFAULT_CIRCULATION_SHARE_MAX", "DEFAULT_DOOR_CORE_BALANCE_RATIO",
    "DEFAULT_SIGHTLINE_CONE_DEGREES", "DEFAULT_WET_AREA_DOOR_MAX_DISTANCE",
    "WC_ROOM_TYPES", "CORE_ROOM_TYPES", "CIRCULATION_ROOM_TYPES",
    "BEDROOM_ROOM_TYPES",
    "FeasibilityReport", "check_fits", "ZoneAssignment", "ZoningPlan",
    "resolve_unit_zoning", "PlacementOption", "options_for_core_placement",
    "CORNERS", "place_unit_entry_doors", "CONTRACT_VERSION",
]
