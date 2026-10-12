"""Tipik tefris kumeleri (kutuphane verisi, DEV-063): context'e YAZILMAZ, proje verisi DEGILDIR.

Bir oda tipinin 'tipik tefris kumesi' kapasite merdivenidir: ustten alta, her kume bir oncekinden azini ister. Kume uyeleri
`furniture/` katalogundaki TIP ANAHTARLARIDIR; olculer oradan okunur (ikinci olcu kopyasi yazilmaz). Kume secimi ofis/katalog
pratigidir ('yaygin'; yonetmelik DEGILDIR, kaynak yok). v1 YALNIZ `yatak_odasi` (mutfak `counters[]` cakisma saglayicisi yok;
WC/banyo net olculeri DEV-049/050'de). Gecis payi / rahat sigma (Katman B) degerleri mimar verene dek KODLANMAZ ('draft').
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Cluster:
    id: str
    label_tr: str
    items: tuple[str, ...]   # furniture katalog tip anahtarlari; buyuk parca once (yerlestirme sirasi)


# Kapasite merdiveni (kullanici karari 2026-10-09): K1 > K2 > K3 > K4
BEDROOM_CLUSTERS: tuple[Cluster, ...] = (
    Cluster("K1", "çift kişilik yatak, iki komodin ve gardırop", ("yatak_cift", "gardirop", "komodin", "komodin")),
    Cluster("K2", "çift kişilik yatak ve gardırop", ("yatak_cift", "gardirop")),
    Cluster("K3", "tek kişilik yatak ve gardırop", ("yatak_tek", "gardirop")),
    Cluster("K4", "tek kişilik yatak", ("yatak_tek",)),
)

CLUSTERS_BY_ROOM_TYPE = {"yatak_odasi": BEDROOM_CLUSTERS}
