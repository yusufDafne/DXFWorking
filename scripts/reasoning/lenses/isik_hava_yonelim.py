"""Isik-hava-yonelim mercek paketi (DEV-062): BILGI burada; olcum sahibi `openings/daylight.py` ve `shafts/ventilation.py`.

Bilgi muhendisi protokolune (docs/agents/KNOWLEDGE_ENGINEER_AGENT.md) uyularak yazildi. Yalniz `reasoning.*` import eder.
Kullanici kararlari (2026-10-09): yasam mahalli (salon + yatak odasi, pencere sart) ve islak hacim (WC + banyo) kumeleri lens-yerel
sabitlerdir ('yaygin'); `tesisat`/`havalandirma` saftleri islak hacim havalandirmasi sayilir (>=300 mm ortak kenar, `check_shafts`
ile ayni tanim); cephe = prob noktasi; capraz havalandirma = en az iki farkli dis normal yonunde pencere; pencere yuksekligi
opsiyonel opt-in alan (katalog varsayilaniyla UYDURMA YOK) -> pencere/taban orani `draft`.
Hicbiri `shadow` ustune cikmaz: terfi kullanici karari + HD kaydidir. `meta.north_angle` yoksa yonelim veçhesi KOSAMAZ ve bunu soyler.
"""
from __future__ import annotations

from dataclasses import replace

from reasoning.model import CheckAdapter, Facet, Lens, Provenance, Thresholds

LENS_ID = "isik_hava_yonelim"
_OPEN = "openings.daylight"
_VENT = "shafts.ventilation"
_ARGS = ("rooms", "walls", "openings", "shafts")
_PRACTICE = Provenance(kind="mimari_pratik", confidence="yaygin", source="mimari pratik; kaynak yok")
_PREFERENCE = Provenance(kind="mimari_pratik", confidence="tercih", source="v1 pratik varsayilan")
_NEEDS = ("rooms[].room_type", "openings[].wall_id")
_NORTH_NOTE = (("meta.north_angle", "yönelim değerlendirilemedi: kuzey yönü verilmedi (meta.north_angle)"),)

FACETS = (
    Facet(id=f"{LENS_ID}.isik.yasam_mahalli_penceresi", lens=LENS_ID,
          title_tr="Her yaşam mahallinin dış cepheye açılan penceresi var mı?",
          principle_tr="Salon ve yatak odası gibi yaşam mahallerinin en az bir dış pencereye ihtiyacı vardır.",
          why_tr="Pencere gün ışığı ve doğal havalandırma demektir; penceresiz bir yatak odası ya da salon yaşanması zor bir mekândır.",
          status="shadow", provenance=_PRACTICE, adapter=CheckAdapter(f"{_OPEN}:check_living_room_window", _ARGS),
          measure_ref=f"{_OPEN}:living_room_window_subjects", needs=_NEEDS,
          applies_when="has_room_type:salon|yatak_odasi", subject_kind="room"),
    Facet(id=f"{LENS_ID}.hava.capraz_havalandirma", lens=LENS_ID,
          title_tr="Daire birbirinden farklı iki cepheye açılıyor mu (çapraz havalandırma)?",
          principle_tr="Dairenin pencereleri en az iki farklı dış cephede olmalı; böylece hava bir yönden girip diğerinden çıkabilir.",
          why_tr="Tek cepheye açılan dairede hava akımı oluşmaz; pencereler açık olsa bile havalandırma zayıf kalır.",
          status="shadow", provenance=_PREFERENCE, adapter=CheckAdapter(f"{_OPEN}:check_cross_ventilation", _ARGS),
          measure_ref=f"{_OPEN}:cross_ventilation_subjects", needs=_NEEDS + ("rooms[].unit_id",),
          applies_when="has_room_type:salon|yatak_odasi", subject_kind="unit"),
    Facet(id=f"{LENS_ID}.hava.islak_hacim_havalandirma", lens=LENS_ID,
          title_tr="WC ve banyonun havalandırması (pencere ya da şaft) var mı?",
          principle_tr="Islak hacmin ya dış cepheye açılan penceresi ya da havalandırma/tesisat şaftına bitişik duvarı olmalı.",
          why_tr="Nem ve koku dışarı atılamazsa ıslak hacimde küf ve koku kalıcı olur. Şaft tanımı şaft kurallarıyla aynıdır.",
          status="shadow", provenance=_PRACTICE, adapter=CheckAdapter(f"{_VENT}:check_wet_ventilation", _ARGS),
          measure_ref=f"{_VENT}:wet_ventilation_subjects", needs=("rooms[].room_type",),
          applies_when="has_room_type:wc|banyo", subject_kind="wet_room"),
    Facet(id=f"{LENS_ID}.yonelim.salon_kuzeye_bakiyor", lens=LENS_ID,
          title_tr="Salonun pencereleri güney yarısına bakıyor mu?",
          principle_tr="Salonun pencerelerinden en az biri kuzey yarısının dışına, yani güneş alan yöne bakmalı.",
          why_tr="Yalnız kuzeye bakan salon gün boyu doğrudan güneş almaz; kış aylarında serin ve loş kalır.",
          status="shadow", provenance=_PREFERENCE,
          adapter=CheckAdapter(f"{_OPEN}:check_salon_orientation", _ARGS + ("north_angle",)),
          measure_ref=f"{_OPEN}:salon_orientation_subjects", needs=_NEEDS + ("meta.north_angle",),
          needs_note_tr=_NORTH_NOTE, applies_when="has_room_type:salon", subject_kind="room",
          thresholds=Thresholds(warn_at=90.0, unit="derece", source="v1 pratik varsayilan: kuzey yarisi = kuzeyden 90 dereceden az sapma; kaynak yok")),
    Facet(id=f"{LENS_ID}.isik.pencere_alani_orani", lens=LENS_ID,
          title_tr="Pencere alanı oda alanına yetiyor mu?",
          principle_tr="Pencere alanının oda alanına oranı yeterli olmalı; oran eşiği doğrulanmış bir kaynak gelmeden kodlanmaz.",
          why_tr="Küçük pencere büyük odayı aydınlatamaz. Ölçüm için pencere yüksekliği gerekir; bu bilgi henüz projede tutulmuyor.",
          status="draft", provenance=_PRACTICE, needs=("openings[].height", "rooms[].room_type"),
          needs_note_tr=(("openings[].height", "pencere yüksekliği verilmedi (openings[].height)"),),
          applies_when="has_room_type:salon|yatak_odasi", subject_kind="room"),
)

_CASES = {"isik.yasam_mahalli_penceresi": "pencere_yasam", "hava.capraz_havalandirma": "capraz_hava",
          "hava.islak_hacim_havalandirma": "islak_hava", "yonelim.salon_kuzeye_bakiyor": "salon_yonelim"}
FACETS = tuple(
    replace(f, cases=(f"{_CASES[f.id.split('.', 1)[1]]}_ihlal", f"{_CASES[f.id.split('.', 1)[1]]}_temiz"))
    if f.id.split(".", 1)[1] in _CASES else f for f in FACETS)

LENS = Lens(
    id=LENS_ID, title_tr="Işık, hava ve yönelim",
    philosophy_tr="Yaşam mahallinin ışık ve hava almadan yaşanmayacağı fiziksel bir gerçektir; yönelim ise aynı planı iklimle uyumlu "
                  "ya da uyumsuz kılar. Kuzey yönü olmayan projede yönelim değerlendirilemez ve bu açıkça söylenir; yön uydurulmaz. "
                  "Güneş yolu (enlem/boylam) şimdilik kapsam dışıdır.")


def register(reg) -> None:
    reg.register_lens(LENS)
    for facet in FACETS:
        reg.register_facet(facet)
