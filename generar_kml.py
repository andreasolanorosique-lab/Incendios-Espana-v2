import os
import csv
import requests
import xml.etree.ElementTree as ET

MAP_KEY = os.environ["FIRMS_MAP_KEY"]

SOURCE = "VIIRS_SNPP_NRT"
BBOX = "-10,35,5,44"  # España aproximada

URL = (
    f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/"
    f"{MAP_KEY}/{SOURCE}/{BBOX}/1"
)

print("Descargando datos de NASA FIRMS...")

respuesta = requests.get(URL, timeout=120)
respuesta.raise_for_status()

with open("fires.csv", "wb") as f:
    f.write(respuesta.content)

print("CSV descargado correctamente.")

# Mostrar las primeras líneas del CSV
with open("fires.csv", "r", encoding="utf-8") as f:
    lector = csv.reader(f)

    print("Primeras líneas del CSV:")

    for i, fila in enumerate(lector):
        print(fila)

        if i >= 5:
            break

# Crear un KML vacío (todavía sin incendios)
kml = ET.Element(
    "kml",
    xmlns="http://www.opengis.net/kml/2.2"
)

document = ET.SubElement(kml, "Document")
ET.SubElement(document, "name").text = "Incendios activos España"

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

print("KML generado correctamente.")
