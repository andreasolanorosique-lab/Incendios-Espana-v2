
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

with open("fires.csv", "wb") as f:
    f.write(r.content)

kml = ET.Element("kml", xmlns="http://www.opengis.net/kml/2.2")
doc = ET.SubElement(kml, "Document")
ET.SubElement(doc, "name").text = "Incendios activos España"

BASE = "https://andreasolanorosique-lab.github.io/Incendios-Espana-v2/icons/"


PLANTAS_REGASIFICACION = [
    {"nombre":"Barcelona","lat":41.3447,"lon":2.1568,"operador":"Enagás","almacenamiento":"760.000 m³","regasificacion":"544 GWh/día","tanques":6,"atraques":2,"telefono":"+34 913 709 000","web":"https://www.enagas.es"},
    {"nombre":"Huelva","lat":37.1847,"lon":-6.9448,"operador":"Enagás","almacenamiento":"619.500 m³","regasificacion":"377 GWh/día","tanques":5,"atraques":1,"telefono":"+34 913 709 000","web":"https://www.enagas.es"},
    {"nombre":"Cartagena","lat":37.5756,"lon":-0.9675,"operador":"Enagás","almacenamiento":"587.000 m³","regasificacion":"377 GWh/día","tanques":5,"atraques":2,"telefono":"+34 913 709 000","web":"https://www.enagas.es"},
    {"nombre":"Bilbao","lat":43.3577,"lon":-3.0670,"operador":"Bahía de Bizkaia Gas","almacenamiento":"450.000 m³","regasificacion":"223 GWh/día","tanques":3,"atraques":1,"telefono":"+34 913 709 000","web":"https://www.enagas.es"},
    {"nombre":"Sagunto","lat":39.6442,"lon":-0.2168,"operador":"Saggas","almacenamiento":"600.000 m³","regasificacion":"279 GWh/día","tanques":4,"atraques":1,"telefono":"+34 913 709 000","web":"https://www.enagas.es"},
    {"nombre":"Mugardos","lat":43.4598,"lon":-8.2626,"operador":"Reganosa","almacenamiento":"300.000 m³","regasificacion":"115 GWh/día","tanques":2,"atraques":1,"telefono":"+34 913 709 000","web":"https://www.enagas.es"},
    {"nombre":"El Musel","lat":43.5735,"lon":-5.6955,"operador":"Musel E-Hub","almacenamiento":"130.000 m³","regasificacion":"Logística","tanques":2,"atraques":1,"telefono":"+34 913 709 000","web":"https://www.enagas.es"},
]

styles = {
    "green": ("fire_green.png", 1.0),
    "yellow": ("fire_yellow.png", 1.0),
    "orange": ("fire_orange.png", 1.0),
    "red": ("fire_red.png", 1.0),
}

styles["lng"]=("https://maps.google.com/mapfiles/kml/shapes/harbor.png",1.1)

for sid, (icon, scale) in styles.items():
    st = ET.SubElement(doc, "Style", id=sid)
    iconstyle = ET.SubElement(st, "IconStyle")
    ET.SubElement(iconstyle, "scale").text = str(scale)
    ic = ET.SubElement(iconstyle, "Icon")
    ET.SubElement(ic, "href").text = icon if icon.startswith("http") else BASE + icon
    lbl = ET.SubElement(st, "LabelStyle")
    ET.SubElement(lbl, "scale").text = "0"   # Oculta el texto en el mapa

with open("fires.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        lat = row.get("latitude")
        lon = row.get("longitude")
        if not lat or not lon:
            continue

        try:
            frp = float(row.get("frp") or 0)
        except:
            frp = 0

        if frp < 10:
            style = "#green"
            confianza = "Baja"
        elif frp < 30:
            style = "#yellow"
            confianza = "Media"
        elif frp < 80:
            style = "#orange"
            confianza = "Alta"
        else:
            style = "#red"
            confianza = "Muy alta"

        pm = ET.SubElement(doc, "Placemark")
        ET.SubElement(pm, "styleUrl").text = style
        ET.SubElement(pm, "name").text = ""

        desc = f"""
        <![CDATA[
        <h2>🔥 Incendio activo</h2>
        <table border="0" cellpadding="4">
        <tr><td><b>FRP</b></td><td>{frp:.1f} MW</td></tr>
        <tr><td><b>Confianza</b></td><td>{confianza}</td></tr>
        <tr><td><b>Fecha</b></td><td>{row.get('acq_date','')}</td></tr>
        <tr><td><b>Hora</b></td><td>{row.get('acq_time','')} UTC</td></tr>
        <tr><td><b>Satélite</b></td><td>{row.get('satellite','')}</td></tr>
        <tr><td><b>Instrumento</b></td><td>{row.get('instrument','')}</td></tr>
        <tr><td><b>Latitud</b></td><td>{lat}</td></tr>
        <tr><td><b>Longitud</b></td><td>{lon}</td></tr>
        </table>
        ]]>
        """
        ET.SubElement(pm, "description").text = desc

        pt = ET.SubElement(pm, "Point")
        ET.SubElement(pt, "coordinates").text = f"{lon},{lat},0"


folder = ET.SubElement(doc,"Folder")
ET.SubElement(folder,"name").text="🏭 Plantas de regasificación"
for pl in PLANTAS_REGASIFICACION:
    pm=ET.SubElement(folder,"Placemark")
    ET.SubElement(pm,"styleUrl").text="#lng"
    ET.SubElement(pm,"name").text=pl["nombre"]
    ET.SubElement(pm,"description").text=f"""<![CDATA[
<h2>🏭 {pl['nombre']}</h2>
<b>Operador:</b> {pl['operador']}<br/>
<b>Almacenamiento:</b> {pl['almacenamiento']}<br/>
<b>Regasificación:</b> {pl['regasificacion']}<br/>
<b>Tanques:</b> {pl['tanques']}<br/>
<b>Atraques:</b> {pl['atraques']}<br/>
<b>Teléfono:</b> {pl['telefono']}<br/>
<b>Web:</b> <a href='{pl['web']}'>{pl['web']}</a>
]]>"""
    pt=ET.SubElement(pm,"Point")
    ET.SubElement(pt,"coordinates").text=f"{pl['lon']},{pl['lat']},0"


tree = ET.ElementTree(kml)
try:
    ET.indent(tree, space="  ")
except AttributeError:
    pass
tree.write("incendios_actual.kml", encoding="utf-8", xml_declaration=True)
