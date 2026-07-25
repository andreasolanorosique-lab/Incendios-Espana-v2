import os
import csv
import json
import requests
import xml.etree.ElementTree as ET

from math import radians, sin, cos, sqrt, atan2

MAP_KEY = os.environ["FIRMS_MAP_KEY"]
SOURCE = "VIIRS_SNPP_NRT"
BBOX = "-10,35,5,44"

DISTANCIA_AGRUPACION = 300  # metros

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

styles = {
    "green": ("fire_green.png", 1.0),
    "yellow": ("fire_yellow.png", 1.0),
    "orange": ("fire_orange.png", 1.0),
    "red": ("fire_red.png", 1.0),
}

for sid, (icon, scale) in styles.items():
    st = ET.SubElement(doc, "Style", id=sid)

    iconstyle = ET.SubElement(st, "IconStyle")
    ET.SubElement(iconstyle, "scale").text = str(scale)

    icono = ET.SubElement(iconstyle, "Icon")
    ET.SubElement(icono, "href").text = BASE + icon

    label = ET.SubElement(st, "LabelStyle")
    ET.SubElement(label, "scale").text = "0"


# =====================================================
# FUNCIONES DE AGRUPACIÓN
# =====================================================

def distancia_metros(lat1, lon1, lat2, lon2):

    R = 6371000

    lat1 = radians(lat1)
    lon1 = radians(lon1)
    lat2 = radians(lat2)
    lon2 = radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        sin(dlat / 2) ** 2
        + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    )

    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c
def agrupar_focos(focos):

    grupos = []

    for foco in focos:

        añadido = False

        for grupo in grupos:

            for referencia in grupo:

                if distancia_metros(
                    foco["lat"],
                    foco["lon"],
                    referencia["lat"],
                    referencia["lon"]
                ) <= DISTANCIA_AGRUPACION:

                    grupo.append(foco)
                    añadido = True
                    break

            if añadido:
                break

        if not añadido:
            grupos.append([foco])

    return grupos# =====================================================
# LEER TODOS LOS FOCOS NASA
# =====================================================

focos = []

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

        focos.append({
            "lat": float(lat),
            "lon": float(lon),
            "frp": frp,
            "row": row
        })


# =====================================================
# AGRUPAR FOCOS
# =====================================================

grupos = agrupar_focos(focos)

grupos = [grupo for grupo in grupos if len(grupo) > 1]

# =====================================================
# CREAR PLACEMARKS
# (EN ESTA FASE SIGUE SIENDO UNO POR FOCO)
# =====================================================

for grupo in grupos:

    for foco in grupo:

        row = foco["row"]

        lat = foco["lat"]
        lon = foco["lon"]
        frp = foco["frp"]

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
# =====================================================
# CARGAR RED DE GASODUCTOS
# =====================================================

with open(
    "infraestructuras/gasoductos/gasoductos.json",
    encoding="utf-8"
) as f:
    gasoductos = json.load(f)

# =====================================================
# DIBUJAR RED DE GASODUCTOS
# =====================================================

carpeta_gas = ET.SubElement(doc, "Folder")
ET.SubElement(carpeta_gas, "name").text = "Gasoductos"

for tramo in gasoductos:

    coords = tramo.get("coordenadas", [])

    if len(coords) < 2:
        continue

    pm = ET.SubElement(carpeta_gas, "Placemark")
    ET.SubElement(pm, "name").text = tramo.get("nombre", "Gasoducto")

    estilo = ET.SubElement(pm, "Style")
    linea = ET.SubElement(estilo, "LineStyle")

    ET.SubElement(linea, "color").text = "ff0000ff"
    ET.SubElement(linea, "width").text = "4"

    ls = ET.SubElement(pm, "LineString")

    ET.SubElement(ls, "tessellate").text = "1"
    ET.SubElement(ls, "altitudeMode").text = "clampToGround"

    ET.SubElement(ls, "coordinates").text = "\n".join(
        f"{lon},{lat}"
        for lon, lat in coords
    )

tree = ET.ElementTree(kml)

try:
    ET.indent(tree, space="  ")
except AttributeError:
    pass
tree.write(
    "incendios_actual.kml",
    encoding="utf-8",
    xml_declaration=True
)
