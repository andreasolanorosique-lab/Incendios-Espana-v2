import os
import csv
import requests
import xml.etree.ElementTree as ET

MAP_KEY = os.environ["FIRMS_MAP_KEY"]
SOURCE = "VIIRS_SNPP_NRT"
BBOX = "-10,35,5,44"

URL = (
    f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/"
    f"{MAP_KEY}/{SOURCE}/{BBOX}/1"
)

r = requests.get(URL, timeout=120)
r.raise_for_status()

with open("fires.csv","wb") as f:
    f.write(r.content)

kml = ET.Element("kml", xmlns="http://www.opengis.net/kml/2.2")
doc = ET.SubElement(kml,"Document")
ET.SubElement(doc,"name").text="Incendios activos España"

BASE="https://andreasolanorosique-lab.github.io/Incendios-Espana-v2/icons/"
for sid,icon in {
    "green":"fire_green.png",
    "yellow":"fire_yellow.png",
    "orange":"fire_orange.png",
    "red":"fire_red.png"
}.items():
    st=ET.SubElement(doc,"Style",id=sid)
    isty=ET.SubElement(st,"IconStyle")
    ET.SubElement(isty,"scale").text="0.8"
    ic=ET.SubElement(isty,"Icon")
    ET.SubElement(ic,"href").text=BASE+icon

with open("fires.csv",encoding="utf-8") as f:
    for row in csv.DictReader(f):
        lat=row.get("latitude"); lon=row.get("longitude")
        if not lat or not lon: continue
        try: frp=float(row.get("frp") or 0)
        except: frp=0
        style="#green" if frp<10 else "#yellow" if frp<30 else "#orange" if frp<80 else "#red"
        pm=ET.SubElement(doc,"Placemark")
        ET.SubElement(pm,"styleUrl").text=style
        ET.SubElement(pm,"name").text=f"FRP {frp:.1f} MW"
        ET.SubElement(pm,"description").text=(
            f"Fecha: {row.get('acq_date','')}<br/>"
            f"Hora: {row.get('acq_time','')} UTC<br/>"
            f"FRP: {frp:.1f} MW")
        pt=ET.SubElement(pm,"Point")
        ET.SubElement(pt,"coordinates").text=f"{lon},{lat},0"

tree=ET.ElementTree(kml)
try: ET.indent(tree,space="  ")
except: pass
tree.write("incendios_actual.kml",encoding="utf-8",xml_declaration=True)
