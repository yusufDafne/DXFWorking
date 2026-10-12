"""Yasanabilirlik mercek paketi (DEV-063): BILGI burada; olcum sahibi `testfit/` (deneme yerlestirme SINAVI).

Bilgi muhendisi protokolune uyularak yazildi. Yalniz `reasoning.*` import eder. Kullanici kararlari (2026-10-09): motor yeni
`testfit/` modulu (furniture + collision'i tuketir); v1 YALNIZ yatak odasi; tipik kume kapasite merdiveni K1-K4 (kutuphane verisi,
context'e yazilmaz); gecis payi iki katman: A (pay = 0, yalniz katalog olcusu + collision kurali) `shadow`, B (rahat sigma payi)
mimar deger verene dek `draft` ve KODLANMAZ. Sonuc bir cozum onerisi degil SINAVDIR (sigdi/sigmadi + hangi kapasitede).
Hicbiri `shadow` ustune cikmaz: terfi kullanici karari + HD kaydidir.
"""
from __future__ import annotations

from dataclasses import replace

from reasoning.model import CheckAdapter, Facet, Lens, Provenance

LENS_ID = "yasanabilirlik"
_M = "testfit.measure"
_ARGS = ("rooms", "walls", "openings")
_PRACTICE = Provenance(kind="mimari_pratik", confidence="yaygin", source="mimari pratik; kaynak yok")
_PREFERENCE = Provenance(kind="mimari_pratik", confidence="tercih", source="v1 pratik varsayilan")
_NEEDS = ("rooms[].room_type", "openings[].wall_id")

FACETS = (
    Facet(id=f"{LENS_ID}.mobilya.yatak_odasi_tek_yatak_sigar", lens=LENS_ID,
          title_tr="Yatak odasına tek kişilik bir yatak sığıyor mu?",
          principle_tr="Bir yatak odası, kapı kanadı açıkken bile en az bir tek kişilik yatağı alabilmelidir.",
          why_tr="Yatak sığmıyorsa oda yatak odası olarak kullanılamaz; bu, yerleşimin kendisini yeniden düşünmeyi gerektirir.",
          status="shadow", provenance=_PRACTICE, adapter=CheckAdapter(f"{_M}:check_bedroom_single_bed_fits", _ARGS),
          measure_ref=f"{_M}:bedroom_single_bed_fits_subjects", needs=_NEEDS,
          applies_when="has_room_type:yatak_odasi", subject_kind="room"),
    Facet(id=f"{LENS_ID}.mobilya.yatak_odasi_cift_yatak_gardirop_sigar", lens=LENS_ID,
          title_tr="Yatak odasına çift kişilik yatak ve gardırop sığıyor mu?",
          principle_tr="Genel konut pratiğinde bir yatak odası, çift kişilik yatağı ve bir gardırobu kapı kanadıyla çakışmadan alabilmelidir.",
          why_tr="Oda yalnız tek kişilik yatağa yetiyorsa çift kişilik kullanım ya da gardırop için başka bir çözüm gerekir.",
          status="shadow", provenance=_PREFERENCE, adapter=CheckAdapter(f"{_M}:check_bedroom_double_bed_wardrobe_fits", _ARGS),
          measure_ref=f"{_M}:bedroom_double_bed_wardrobe_fits_subjects", needs=_NEEDS,
          applies_when="has_room_type:yatak_odasi", subject_kind="room"),
    Facet(id=f"{LENS_ID}.mobilya.gecis_payi", lens=LENS_ID,
          title_tr="Yatak ve dolap çevresinde rahat geçiş payı kalıyor mu?",
          principle_tr="Mobilya sığmasının ötesinde, yatağın yanından ve dolap önünden rahat geçilebilmelidir.",
          why_tr="Sığan ama geçilemeyen bir yatak odası günlük kullanımda yorucudur. Pay değerleri bir mimar tarafından verilene dek kodlanmaz.",
          status="draft", provenance=_PRACTICE, needs=_NEEDS, applies_when="has_room_type:yatak_odasi", subject_kind="room"),
    Facet(id=f"{LENS_ID}.duvar.kullanilabilir_uzunluk", lens=LENS_ID,
          title_tr="Kapı ve pencereden sonra mobilya için kullanılabilir duvar uzunluğu kalıyor mu?",
          principle_tr="Kapı ve pencere açıklıkları düştükten sonra mobilyanın dayanabileceği düz duvar uzunluğu yeterli olmalıdır.",
          why_tr="Açıklıklarla bölünmüş duvar mobilya yerleşimini kısıtlar; ölçüm duvar ve açıklık verisinden türetilebilir ama henüz yazılmadı.",
          status="idea"),
)

_CASES = {"mobilya.yatak_odasi_tek_yatak_sigar": "yatak_tek", "mobilya.yatak_odasi_cift_yatak_gardirop_sigar": "yatak_cift"}
FACETS = tuple(
    replace(f, cases=(f"{_CASES[f.id.split('.', 1)[1]]}_sigar_ihlal", f"{_CASES[f.id.split('.', 1)[1]]}_sigar_temiz"))
    if f.id.split(".", 1)[1] in _CASES else f for f in FACETS)

LENS = Lens(
    id=LENS_ID, title_tr="Yaşanabilirlik",
    philosophy_tr="Geometrik olarak geçerli ve oransal olarak makul bir oda hâlâ yaşanamaz olabilir: kapı kanadı yatağa çarpar, yatak sığar "
                  "ama yanından geçilemez. Mimar bunu zihninde mobilya koyarak dener; bu mercek aynı denemeyi tefriş verisi olmadan, "
                  "katalog ölçüleriyle yapar. Deneme bir çözüm önerisi değil sınavdır: hangi mobilyanın nereye konacağı kullanıcının kararıdır.")


def register(reg) -> None:
    reg.register_lens(LENS)
    for facet in FACETS:
        reg.register_facet(facet)
