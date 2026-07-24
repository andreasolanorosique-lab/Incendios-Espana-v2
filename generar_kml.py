import os
import csv
import requests
import xml.etree.ElementTree as ET

# ==========================
# CONFIGURACIÓN
# ==========================

MAP_KEY = os.environ["FIRMS_MAP_KEY"]

SOURCE = "VIIRS_SNPP_NRT"
BBOX = "-10,35,5,44"      # España aproximada
DAYS = 1

URL = (
    f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/"
    f"{MAP_KEY}/{SOURCE}/{BBOX}/{DAYS}"
)

# ==========================
# DESCARGAR CSV
# ==========================

print("Descargando datos de NASA FIRMS...")

r = requests.get(URL, timeout=120)
r.raise_for_status()

with open("fires.csv", "wb") as f:
    f.write(r.content)

print("CSV descargado correctamente.")

# ==========================
# CREAR KML
# ==========================

kml = ET.Element(
    "kml",
    xmlns="http://www.opengis.net/kml/2.2"
)

document = ET.SubElement(kml, "Document")
ET.SubElement(document, "name").text = "Incendios activos España"

# ---------- Estilos ----------

def crear_estilo(doc, nombre, color):
    style = ET.SubElement(doc, "Style", id=nombre)

    iconstyle = ET.SubElement(style, "IconStyle")
    ET.SubElement(iconstyle, "scale").text = "1.3"
    ET.SubElement(iconstyle, "color").text = color

    icon = ET.SubElement(iconstyle, "Icon")
    ET.SubElement(icon, "href").text = (
        "http://maps.google.com/mapfiles/kml/shapes/firedept.png"
    )

crear_estilo(document, "bajo",     "ff00ff00")  # verde
crear_estilo(document, "medio",    "ff00ffff")  # amarillo
crear_estilo(document, "alto",     "ff0080ff")  # naranja
crear_estilo(document, "extremo",  "ff0000ff")  # rojo

def estilo_por_frp(frp):
    try:
        frp = float(frp)
    except:
        return "#medio"

    if frp < 10:
        return "#bajo"
    elif frp < 30:
        return "#medio"
    elif frp < 60:
        return "#alto"
    else:
        return "#extremo"

# ---------- Incendios ----------

contador = 0

with open("fires.csv", encoding="utf-8") as f:

    lector = csv.DictReader(f)

    for fila in lector:

        lat = fila.get("latitude")
        lon = fila.get("longitude")

        if not lat or not lon:
            continue

        frp = fila.get("frp", "")

        placemark = ET.SubElement(document, "Placemark")

        ET.SubElement(
            placemark,
            "styleUrl"
        ).text = estilo_por_frp(frp)

        ET.SubElement(
            placemark,
            "name"
        ).text = f"🔥 FRP {frp}"

        descripcion = f"""
Fecha: {fila.get('acq_date','')}
Hora UTC: {fila.get('acq_time','')}
FRP: {frp}
Confianza: {fila.get('confidence','')}
Satélite: {fila.get('satellite','')}
Instrumento: {fila.get('instrument','')}
"""

        ET.SubElement(
            placemark,
            "description"
        ).text = descripcion

        punto = ET.SubElement(
            placemark,
            "Point"
        )

        ET.SubElement(
            punto,
            "coordinates"
        ).text = f"{lon},{lat},0"

        contador += 1

# ---------- Guardar ----------

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

print(f"Incendios añadidos: {contador}")
