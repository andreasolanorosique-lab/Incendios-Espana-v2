import xml.etree.ElementTree as ET

kml = ET.Element(
    "kml",
    xmlns="http://www.opengis.net/kml/2.2"
)

document = ET.SubElement(kml, "Document")

ET.SubElement(document, "name").text = "Prueba"

placemark = ET.SubElement(document, "Placemark")

ET.SubElement(placemark, "name").text = "Punto de prueba"

point = ET.SubElement(placemark, "Point")

ET.SubElement(
    point,
    "coordinates"
).text = "-3.7038,40.4168,0"

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

print("KML generado correctamente")
