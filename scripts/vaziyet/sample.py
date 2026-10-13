"""Basit ornek vaziyet DXF'i URETECI (DEV-082): kullaniciya 'boyle bir dosya gonderin' diye verilir. DXF elle yazilmaz, bu fonksiyonla uretilir."""
from __future__ import annotations

from pathlib import Path

import ezdxf

# Ornek parsel (mm, birim: $INSUNITS=4): yola (guney) bakan basit dortgen. Sayilar ORNEKTIR - proje verisi/mevzuat degeri DEGILDIR.
SAMPLE_PARCEL = [(0.0, 0.0), (30000.0, 0.0), (30000.0, 40000.0), (0.0, 40000.0)]
SAMPLE_ZONE = [(6000.0, 8000.0), (24000.0, 8000.0), (24000.0, 30000.0), (6000.0, 30000.0)]
SAMPLE_ROAD = [(-5000.0, -4000.0), (35000.0, -4000.0)]
NORTH_BASE = (36000.0, 36000.0)
NORTH_TIP = (36000.0, 40000.0)


def write_sample(path) -> Path:
    doc = ezdxf.new("R2010", setup=True)
    doc.header["$INSUNITS"] = 4
    for name, color in (("PARSEL", 1), ("YERLESIM_ALANI", 3), ("YOL", 8), ("NOT", 7), ("KUZEY", 5)):
        doc.layers.add(name, color=color)
    msp = doc.modelspace()
    msp.add_lwpolyline(SAMPLE_PARCEL, close=True, dxfattribs={"layer": "PARSEL"})
    msp.add_lwpolyline(SAMPLE_ZONE, close=True, dxfattribs={"layer": "YERLESIM_ALANI"})
    msp.add_line(SAMPLE_ROAD[0], SAMPLE_ROAD[1], dxfattribs={"layer": "YOL"})
    msp.add_line(NORTH_BASE, NORTH_TIP, dxfattribs={"layer": "KUZEY"})
    for text, pos in (("K", (NORTH_TIP[0], NORTH_TIP[1] + 600.0)), ("YOL", (15000.0, -6500.0)), ("PARSEL (ORNEK)", (15000.0, 20000.0)),
                      ("BINA BU BOLGEDE OLSUN (YAKLASIK)", (15000.0, 31500.0)), ("KOMSU PARSEL", (-9000.0, 20000.0))):
        msp.add_text(text, dxfattribs={"layer": "NOT", "height": 800.0, "insert": pos})
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(out)
    return out
