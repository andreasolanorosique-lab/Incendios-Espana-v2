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

print("Descargando datos de NASA FIRMS...")

respuesta = requests.get(URL, timeout=120)
respuesta.raise_for_status()

with open("fires.csv", "wb") as f:
    f.write(respuesta.content)

print("CSV descargado correctamente.")

kml = ET.Element("kml", xmlns="http://www.opengis.net/kml/2.2")
document = ET.SubElement(kml, "Document")
ET.SubElement(document, "name").text = "Incendios activos España"

contador = 0

with open("fires.csv", "r", encoding="utf-8") as f:
    lector = csv.DictReader(f)

    for fila in lector:
        lat = fila.get("latitude")
        lon = fila.get("longitude")
        if not lat or not lon:
            continue

        placemark = ET.SubElement(document, "Placemark")
        ET.SubElement(placemark, "name").text = f"Incendio {contador + 1}"

        descripcion = (
            f"Fecha: {fila.get('acq_date','')}\n"
            f"Hora: {fila.get('acq_time','')} UTC\n"
            f"FRP: {fila.get('frp','')}\n"
            f"Confianza: {fila.get('confidence','')}\n"
            f"Satélite: {fila.get('satellite','')}\n"
            f"Instrumento: {fila.get('instrument','')}"
        )

        ET.SubElement(placemark, "description").text = descripcion

        punto = ET.SubElement(placemark, "Point")
        ET.SubElement(punto, "coordinates").text = f"{lon},{lat},0"

        contador += 1

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

print(f"Se han añadido {contador} incendios al KML.")
