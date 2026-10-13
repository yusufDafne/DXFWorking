"""Mahremiyet mercek paketi (DEV-061): BILGI burada yasar; olcum/kural sahibi `architect/` (privacy.py, rules.py).

Yalniz `reasoning.*` import eder (AST ile denetlenir); `register(reg)` import aninda degil YUKLEME aninda cagrilir.
Durum ozeti (kullanici kararlari 2026-10-09):
  * `validate.py`nin GERCEKTEN cagirdigi besi `active` + `legacy` (adaptor ile kayit; davranis DEGISMEZ);
  * DEV-052/DEV-053 kurallari (validate'e bagli DEGIL) yalniz `shadow` - baglamak ayri karar;
  * yeni olcumler `shadow` (kullaniciya gosterilmez); kademelenme / birimler arasi ortak duvar `draft`; misafir yolu `idea`.
Hicbir esik yonetmelik DEGILDIR: saglayici (`provenance`) 'tercih/yaygin' der, kaynak yoksa bunu soyler.
"""
from __future__ import annotations

from dataclasses import replace

from reasoning.model import CheckAdapter, Facet, Lens, Plain, Provenance, Remedy, Smell, Thresholds

LENS_ID = "mahremiyet"
_RULES = "architect.rules"
_PRIV = "architect.privacy"
_ARGS = ("rooms", "walls", "openings")
_NEEDS_DOORS = ("rooms[].unit_id", "rooms[].room_type", "openings[].wall_id")
_PRACTICE = Provenance(kind="mimari_pratik", confidence="yaygin", source="mimari pratik; kaynak yok")
_PREFERENCE = Provenance(kind="mimari_pratik", confidence="tercih", source="v1 pratik varsayilan")


def _legacy(name: str, ref: str, title: str, principle: str, why: str, problem: str, consequence: str,
            applies: str, prov: Provenance = _PRACTICE) -> Facet:
    return Facet(
        id=f"{LENS_ID}.{name}", lens=LENS_ID, title_tr=title, principle_tr=principle, why_tr=why, status="active",
        provenance=prov, adapter=CheckAdapter(f"{_RULES}:{ref}", _ARGS), needs=_NEEDS_DOORS, applies_when=applies,
        plain=Plain(problem=problem, consequence=consequence), legacy=True, subject_kind="unit")


FACETS = (
    # ---- active + legacy: validate.py'nin zaten cagirdigi bes kural --------------------------------------------
    _legacy("gorsel.giris_wc_gorus", "check_entry_sightlines",
            "Girişten WC/banyo kapısı görünür mü?",
            "Daire kapısından girince karşıda WC veya banyo kapısı görünmemeli.",
            "Misafirin ilk gördüğü şey ıslak hacim kapısı olmamalı; kapı açık kalınca içerisi de görünür.",
            "Daireye girince tam karşıda WC/banyo kapısı görünüyor.",
            "Misafir daireye girer girmez ıslak hacim kapısıyla karşılaşır; kapı açıkken içerisi holden görünür.",
            "has_room_type:wc|banyo"),
    _legacy("gorsel.mutfak_wc_karsilikli", "check_kitchen_wet_door_opposite",
            "Mutfak kapısı WC/banyo kapısının tam karşısında mı?",
            "Mutfak kapısından bakınca WC/banyo kapısı görünmemeli.",
            "Yemek hazırlanan alandan ıslak hacim kapısına doğrudan görüş hijyen ve mahremiyet açısından istenmez.",
            "Mutfak kapısı ile WC/banyo kapısı aynı eksende karşı karşıya.",
            "Mutfaktan bakınca WC/banyo kapısı görünür; kapı açıldığında iki alan birbirine açılmış olur.",
            "has_room_type:mutfak"),
    _legacy("gorsel.wc_kapisi_disa_aciliyor", "check_wet_door_swing_inward",
            "WC/banyo kapısı kendi hacmine mi açılıyor?",
            "WC/banyo kapısı varsayılan olarak içeri doğru açılır.",
            "Dışarı açılan kapı, açıkken holden içerisinin görünmesine ve hol trafiğine takılmasına yol açar "
            "(mahremiyetle ilişkisi yaygın gerekçedir; kayıtlı kaynak yok).",
            "WC/banyo kapısı hole doğru açılıyor.",
            "Kapı açıkken içerisi holden görünür ve kanat hol geçişini daraltır.",
            "has_room_type:wc|banyo"),
    _legacy("gecis.yatak_salona_dogrudan", "check_bedroom_via_corridor",
            "Yatak odasının kapısı doğrudan salona mı açılıyor?",
            "Yatak odasına, misafirin bulunduğu salondan değil hol/koridor üzerinden girilmeli.",
            "Misafir salondayken yatak odası kapısı onun görüş ve ses alanında kalır.",
            "Yatak odasının kapısı doğrudan salona açılıyor.",
            "Salondaki misafir yatak odasının kapısını görür; özel alan ile sosyal alan arasında tampon kalmaz.",
            "has_room_type:yatak_odasi"),
    _legacy("gecis.islak_yatak_odasindan", "check_wet_area_reachable_without_bedroom",
            "WC/banyoya yatak odasından geçmeden ulaşılabiliyor mu?",
            "Islak hacme, bir yatak odasının içinden geçmeden hol üzerinden ulaşılabilmeli.",
            "Bir odaya gitmek için başka bir özel odadan geçmek hem yatak odasının hem kullanıcının mahremiyetini bozar.",
            "WC/banyoya ancak bir yatak odasının içinden geçilerek gidiliyor.",
            "Misafir ya da aile bireyi WC'ye gitmek için bir yatak odasından geçmek zorunda kalır.",
            "has_room_type:yatak_odasi"),
    # ---- shadow: DEV-052 / DEV-053 (validate'e BAGLI DEGIL) ----------------------------------------------------
    Facet(id=f"{LENS_ID}.gorsel.giris_wc_kapi_yakin", lens=LENS_ID,
          title_tr="Giriş kapısının önünde/çaprazında ya da bitişiğinde WC/banyo kapısı var mı?",
          principle_tr="Giriş kapısı ile WC/banyo kapısı arasında yeterli temiz aralık olmalı ve WC kapısı giriş karşısına/çaprazına gelmemeli.",
          why_tr="Giriş karşısındaki dar koni `giris_wc_gorus`ta denetlenir; burada çapraz bant ve kapı çerçeveleri arası aralık denetlenir.",
          status="shadow", provenance=_PREFERENCE, adapter=CheckAdapter(f"{_RULES}:check_entry_wet_door_proximity", _ARGS),
          needs=_NEEDS_DOORS, applies_when="has_room_type:wc|banyo", subject_kind="unit",
          thresholds=Thresholds(warn_at=60.0, unit="derece", source="v1 pratik varsayilan (DEV-053; 250 mm aralık da aynı kaynak)")),
    Facet(id=f"{LENS_ID}.gorsel.islak_hacim_komsulugu", lens=LENS_ID,
          title_tr="WC ve banyo yan yana mı, kapıları aynı hatta mı?",
          principle_tr="WC ile banyo ortak duvar paylaşmalı, kapıları aynı hatta yan yana olmalı ve diğer oda kapılarından uzak durmalı.",
          why_tr="Islak hacimlerin kümelenmesi tesisat ekonomisi ve kapı yerleşiminin düzeni içindir; mahremiyetle kısmi ilişkilidir.",
          status="shadow", provenance=_PREFERENCE, adapter=CheckAdapter(f"{_RULES}:check_wet_area_adjacency", _ARGS),
          needs=_NEEDS_DOORS, applies_when="has_room_type:wc|banyo", subject_kind="unit"),
    # ---- shadow: yeni olcumler (architect/privacy.py) ---------------------------------------------------------
    Facet(id=f"{LENS_ID}.gorsel.giristen_yatak_odasi_gorus", lens=LENS_ID,
          title_tr="Girişten yatak odası kapısı görünür mü?",
          principle_tr="Daire kapısından girince aynı dairenin yatak odası kapısı doğrudan görünmemeli.",
          why_tr="Misafirin ilk bakışta yatak odası kapısını görmesi özel alanın kamusal alana açılması demektir.",
          status="shadow", provenance=_PREFERENCE, adapter=CheckAdapter(f"{_PRIV}:check_entry_bedroom_sightline", _ARGS),
          measure_ref=f"{_PRIV}:entry_bedroom_sightline_subjects", needs=_NEEDS_DOORS,
          applies_when="has_room_type:yatak_odasi", subject_kind="unit",
          thresholds=Thresholds(warn_at=45.0, unit="derece", source="v1 pratik varsayilan (check_entry_sightlines koniyle ayni)")),
    Facet(id=f"{LENS_ID}.birimler_arasi.komsu_giris_yakinligi", lens=LENS_ID,
          title_tr="Komşu dairelerin giriş kapıları birbirine çok yakın mı?",
          principle_tr="Farklı dairelerin giriş kapıları (orta noktalar arası) birbirinden yeterince uzak olmalı.",
          why_tr="Yakın girişlerde kapılar aynı anda açıldığında komşuların iç mekânı birbirine görünür ve ses/trafik çakışır.",
          status="shadow", provenance=_PREFERENCE, adapter=CheckAdapter(f"{_PRIV}:check_neighbor_entry_proximity", _ARGS),
          measure_ref=f"{_PRIV}:neighbor_entry_proximity_subjects", needs=_NEEDS_DOORS,
          applies_when="has_room_type:yatak_odasi|salon", subject_kind="unit",
          thresholds=Thresholds(warn_at=3000.0, unit="mm", source="v1 pratik varsayilan; DEFAULT_ENTRY_FRONT_MAX_DISTANCE_MM'den odunc, kaynak yok")),
    Facet(id=f"{LENS_ID}.isitsel.islak_ortak_duvar_ayni_birim", lens=LENS_ID,
          title_tr="Islak hacim, yatak odası veya salonla ortak duvar paylaşıyor mu?",
          principle_tr="Aynı dairede WC/banyo, yatak odası ya da salonla ortak duvar paylaşıyorsa duvar bir ayırıcı olarak düşünülmeli.",
          why_tr="Islak hacimden gelen ses ve koku komşu odaya geçer; duvarın türü ve kütlesi bu etkiyi azaltır ya da artırır.",
          status="shadow", provenance=_PREFERENCE, adapter=CheckAdapter(f"{_PRIV}:check_wet_shared_wall_same_unit", _ARGS),
          measure_ref=f"{_PRIV}:wet_shared_wall_same_unit_subjects", needs=("rooms[].unit_id", "rooms[].room_type"),
          applies_when="has_room_type:wc|banyo", subject_kind="wet_room"),
    Facet(id=f"{LENS_ID}.gecis.islak_iki_bolgeye_kapili", lens=LENS_ID,
          title_tr="Islak hacim hem salona hem yatak odasına mı açılıyor?",
          principle_tr="Aynı WC/banyo hem sosyal alana (salon) hem özel alana (yatak odası) kapılı olmamalı.",
          why_tr="`sandvic_banyo` kokusunun bileşenidir: misafir ile aile aynı hacmi paylaşır, ıslak hacim iki bölge arasında tampon olmaz.",
          status="shadow", provenance=_PREFERENCE, adapter=CheckAdapter(f"{_PRIV}:check_wet_double_zone_doors", _ARGS),
          measure_ref=f"{_PRIV}:wet_double_zone_doors_subjects", needs=_NEEDS_DOORS,
          applies_when="has_room_type:wc|banyo", subject_kind="wet_room"),
    # ---- draft / idea: olcum kodu YOK (cikarilan sonuc: dogru degeri uydurmamak) ---------------------------------
    Facet(id=f"{LENS_ID}.isitsel.islak_ortak_duvar_birimler_arasi", lens=LENS_ID,
          title_tr="Islak hacim, komşu dairenin yatak odası/salonuyla duvar paylaşıyor mu?",
          principle_tr="Birimler arası ortak duvarda ıslak hacim ile komşu dairenin yatak odası/salonu karşı karşıya gelmemeli.",
          why_tr="Aynı ses ve koku gerekçesi, bu kez komşu dairenin mahremiyeti için.",
          status="draft", provenance=_PREFERENCE, needs=("rooms[].unit_id", "rooms[].room_type"),
          applies_when="has_room_type:wc|banyo", subject_kind="wet_room"),
    Facet(id=f"{LENS_ID}.kademelenme.derinlik", lens=LENS_ID,
          title_tr="Giriş → salon → hol → yatak odası sırası korunuyor mu?",
          principle_tr="Kamusaldan özele kademelenme: yatak odasına ulaşan yol kamusal alanlardan daha derinde olmalı.",
          why_tr="Konutta yakınlık gradyanı (kamusal→özel) yaygın bir ilkedir; ölçüm için birim-içi graf derinliği (`_build_unit_adjacency` genişletmesi) gerekir.",
          status="draft", provenance=_PRACTICE, needs=("rooms[].unit_id", "rooms[].room_type"),
          applies_when="has_room_type:yatak_odasi", subject_kind="unit"),
    Facet(id=f"{LENS_ID}.gecis.misafir_yolu", lens=LENS_ID,
          title_tr="Misafir, yatak odası kapıları önünden geçmeden WC'ye ulaşabiliyor mu?",
          principle_tr="Giriş → salon → misafir WC yolu, yatak odası kapılarının önünden geçmemeli.",
          why_tr="Hangi WC'nin misafire açık olduğu bir kullanıcı kararıdır; bu bilgi henüz projede tutulmuyor.",
          status="idea"),
)

# vaka kutuphanesi: scripts/reasoning/cases/<ad>_ihlal + <ad>_temiz (elle yazilmis sentetik mini sahneler)
_CASE_NAMES = {
    "gorsel.giris_wc_gorus": "giris_wc_gorus", "gorsel.mutfak_wc_karsilikli": "mutfak_wc",
    "gorsel.wc_kapisi_disa_aciliyor": "wc_kapi_yonu", "gecis.yatak_salona_dogrudan": "yatak_salon_kapi",
    "gecis.islak_yatak_odasindan": "islak_yatak_zinciri", "gorsel.giris_wc_kapi_yakin": "giris_wc_kapi_yakin",
    "gorsel.islak_hacim_komsulugu": "islak_komsuluk", "gorsel.giristen_yatak_odasi_gorus": "giristen_yatak_gorus",
    "birimler_arasi.komsu_giris_yakinligi": "komsu_giris", "isitsel.islak_ortak_duvar_ayni_birim": "islak_ortak_duvar",
    "gecis.islak_iki_bolgeye_kapili": "sandvic_banyo",
}
# cozum yollari (DEV-064): metinler RAKAMSIZ, bedel nitel (sayi olcumden gelir)
REMEDIES = (
    Remedy("kapiyi_yana_kaydir", "Kapıyı, girişten bakınca görüş ekseninin dışına kaydırmak.",
           "Duvarda kapı için başka bir yer gerekir; o yerdeki mobilya düzeni etkilenebilir."),
    Remedy("hol_bukumu_ekle", "Girişte küçük bir hol ya da duvar dönüşü ekleyerek görüşü kesmek.",
           "Hol biraz büyür, komşu oda biraz küçülür."),
    Remedy("kapiyi_hole_ac", "Kapıyı salon ya da yatak odası yerine doğrudan hole açmak.",
           "Hol sınırı değişir; hol payı biraz artabilir."),
    Remedy("hol_uzat", "Holü, geçilmek zorunda kalınan odanın önüne kadar uzatmak.",
           "Hol büyür, bitişik oda küçülür."),
    Remedy("hol_uzerinden_ac", "Islak hacmi hol üzerinden açmak.",
           "Holün bir kenarı ıslak hacme ayrılır."),
    Remedy("islak_hacmi_tek_bolgeye_bagla", "Islak hacmin kapısını yalnız tek bölgeye (salona ya da özel alana) bağlamak.",
           "Diğer bölgeden bu hacme erişim kalkar; kullanım alışkanlığı değişir."),
)
_FACET_REMEDIES = {
    "gorsel.giris_wc_gorus": ("kapiyi_yana_kaydir", "hol_bukumu_ekle"),
    "gorsel.giristen_yatak_odasi_gorus": ("kapiyi_yana_kaydir", "hol_bukumu_ekle"),
    "gecis.yatak_salona_dogrudan": ("kapiyi_hole_ac",),
    "gecis.islak_yatak_odasindan": ("hol_uzat", "kapiyi_hole_ac"),
    "gecis.islak_iki_bolgeye_kapili": ("islak_hacmi_tek_bolgeye_bagla", "hol_uzerinden_ac"),
}
FACETS = tuple(
    replace(f, cases=(f"{_CASE_NAMES[f.id.split('.', 1)[1]]}_ihlal", f"{_CASE_NAMES[f.id.split('.', 1)[1]]}_temiz")
            if f.id.split(".", 1)[1] in _CASE_NAMES else f.cases,
            remedies=_FACET_REMEDIES.get(f.id.split(".", 1)[1], f.remedies))
    for f in FACETS)

SMELLS = (
    Smell(id="sandvic_banyo", title_tr="Salon ile yatak odası arasına sıkışmış ıslak hacim",
          facet_ids=(f"{LENS_ID}.gecis.islak_iki_bolgeye_kapili", f"{LENS_ID}.isitsel.islak_ortak_duvar_ayni_birim"),
          root_cause_tr="Islak hacim, sosyal ve özel bölge arasında tampon olmadan iki tarafa bağlanmış.",
          remedies=("islak_hacmi_tek_bolgeye_bagla", "hol_uzerinden_ac")),
    Smell(id="gecis_odasi_yatak", title_tr="Yatak odası bir geçiş odasına dönmüş",
          facet_ids=(f"{LENS_ID}.gecis.islak_yatak_odasindan", f"{LENS_ID}.gecis.yatak_salona_dogrudan"),
          root_cause_tr="Hol, odaların tamamına ulaşmıyor; bazı odalara ancak bir yatak odasından geçilerek gidiliyor.",
          remedies=("hol_uzat", "kapiyi_hole_ac")),
    Smell(id="dikizli_giris", title_tr="Girişten özel alan görünüyor",
          facet_ids=(f"{LENS_ID}.gorsel.giris_wc_gorus", f"{LENS_ID}.gorsel.giristen_yatak_odasi_gorus",
                     f"{LENS_ID}.gorsel.giris_wc_kapi_yakin"),
          root_cause_tr="Giriş kapısının karşı hattında özel alan kapıları (WC/banyo, yatak odası) görüş ekseninde kalıyor.",
          remedies=("kapiyi_yana_kaydir", "hol_bukumu_ekle")),
)

LENS = Lens(
    id=LENS_ID, title_tr="Mahremiyet",
    philosophy_tr="Konut kamusaldan özele kademelenir (yakınlık gradyanı; yaygın mimari ilke, resmi kaynak değil). "
                  "Mahremiyetin tek karşılığı yoktur: görsel, işitsel, geçiş, kademelenme ve birimler arası "
                  "veçheler ayrı ölçülür. Meşru istisnalar: stüdyo (1+0), otel odası, bilinçli açık plan tercihi.")


def register(reg) -> None:
    reg.register_lens(LENS)
    for remedy in REMEDIES:
        reg.register_remedy(remedy)
    for facet in FACETS:
        reg.register_facet(facet)
    for smell in SMELLS:
        reg.register_smell(smell)
