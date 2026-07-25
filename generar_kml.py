#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import json
import os
import requests
from xml.sax.saxutils import escape

# ------------------------------------------------------------
# CONFIGURACIÓN
# ------------------------------------------------------------

FIRMS_MAP_KEY = os.environ.get("FIRMS_MAP_KEY")

URL_FIRMS = (
    f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/"
    f"{FIRMS_MAP_KEY}/VIIRS_SNPP_NRT/world/1"
)

ARCHIVO_GASODUCTOS = "infraestructuras/gasoductos/gasoductos.json"
ARCHIVO_POSICIONES = "infraestructuras/posiciones/catalogo_posiciones.json"

SALIDA_KML = "incendios_actual.kml"


# ------------------------------------------------------------
# DESCARGAR NASA FIRMS
# ------------------------------------------------------------

def descargar_firms():

    print("Descargando incendios NASA FIRMS...")

    respuesta = requests.get(URL_FIRMS, timeout=60)

    respuesta.raise_for_status()

    lector = csv.DictReader(respuesta.text.splitlines())

    incendios = []

    for fila in lector:

        try:

            incendios.append({
                "lat": float(fila["latitude"]),
                "lon": float(fila["longitude"]),
                "frp": float(fila.get("frp", 0)),
                "confidence": fila.get("confidence", ""),
                "fecha": fila.get("acq_date", ""),
                "hora": fila.get("acq_time", "")
            })

        except Exception:
            continue

    print(f"Incendios descargados: {len(incendios)}")

    return incendios


# ------------------------------------------------------------
# LEER GASODUCTOS
# ------------------------------------------------------------

def cargar_gasoductos():

    print("Leyendo gasoductos...")

    if not os.path.exists(ARCHIVO_GASODUCTOS):

        print("No existe gasoductos.json")

        return []

    with open(ARCHIVO_GASODUCTOS, encoding="utf-8") as f:

        datos = json.load(f)

    print(f"Gasoductos cargados: {len(datos)}")

    return datos


# ------------------------------------------------------------
# LEER POSICIONES
# ------------------------------------------------------------

def cargar_posiciones():

    print("Leyendo posiciones...")

    if not os.path.exists(ARCHIVO_POSICIONES):

        print("No existe catalogo_posiciones.json")

        return []

    with open(ARCHIVO_POSICIONES, encoding="utf-8") as f:

        datos = json.load(f)

    print(f"Posiciones cargadas: {len(datos)}")

    return datos


# ------------------------------------------------------------
# INICIO DEL KML
# ------------------------------------------------------------

def inicio_kml():

    return """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>

<name>Incendios España</name>

<Style id="incendio">

<IconStyle>

<scale>0.8</scale>

<Icon>

<href>http://maps.google.com/mapfiles/kml/shapes/firedept.png</href>

</Icon>

</IconStyle>

</Style>

<Style id="gasoducto">

<LineStyle>

<color>ff0000ff</color>

<width>2</width>

</LineStyle>

</Style>

"""
# ------------------------------------------------------------
# FIN DEL KML
# ------------------------------------------------------------

def fin_kml():
    return """
</Document>
</kml>
"""


# ------------------------------------------------------------
# DIBUJAR GASODUCTOS
# ------------------------------------------------------------

def escribir_gasoductos(f, gasoductos):

    print("Escribiendo gasoductos...")

    for gasoducto in gasoductos:

        nombre = escape(str(gasoducto.get("nombre", "Gasoducto")))
        coordenadas = gasoducto.get("coordenadas", [])

        if len(coordenadas) < 2:
            continue

        f.write(f"""
<Placemark>
    <name>{nombre}</name>
    <styleUrl>#gasoducto</styleUrl>
    <LineString>
        <tessellate>1</tessellate>
        <coordinates>
""")

        for punto in coordenadas:

            try:
                lon = punto["longitud"]
                lat = punto["latitud"]
            except KeyError:
                continue

            f.write(f"{lon},{lat},0 ")

        f.write("""
        </coordinates>
    </LineString>
</Placemark>
""")


# ------------------------------------------------------------
# DIBUJAR INCENDIOS
# ------------------------------------------------------------

def escribir_incendios(f, incendios):

    print("Escribiendo incendios...")

    for incendio in incendios:

        lat = incendio["lat"]
        lon = incendio["lon"]
        frp = incendio["frp"]
        fecha = incendio["fecha"]
        hora = incendio["hora"]

        descripcion = f"""
<![CDATA[
<b>FRP:</b> {frp}<br>
<b>Fecha:</b> {fecha}<br>
<b>Hora:</b> {hora}
]]>
"""

        f.write(f"""
<Placemark>

<name>Incendio</name>

<styleUrl>#incendio</styleUrl>

<description>{descripcion}</description>

<Point>

<coordinates>{lon},{lat},0</coordinates>

</Point>

</Placemark>
""")
# ------------------------------------------------------------
# GENERAR KML
# ------------------------------------------------------------

def generar_kml(incendios, gasoductos, posiciones):

    print("Generando KML...")

    with open(SALIDA_KML, "w", encoding="utf-8") as f:

        f.write(inicio_kml())

        # ----------------------------------------------------
        # GASODUCTOS
        # ----------------------------------------------------

        escribir_gasoductos(f, gasoductos)

        # ----------------------------------------------------
        # INCENDIOS
        # ----------------------------------------------------

        escribir_incendios(f, incendios)

        # ----------------------------------------------------
        # AQUÍ AÑADIREMOS MÁS ADELANTE:
        #
        # - Posiciones
        # - Gasoducto más cercano
        # - Posición más cercana
        #
        # ----------------------------------------------------

        f.write(fin_kml())

    print(f"KML generado correctamente: {SALIDA_KML}")
# ------------------------------------------------------------
# PROGRAMA PRINCIPAL
# ------------------------------------------------------------

def main():

    try:

        incendios = descargar_firms()
        gasoductos = cargar_gasoductos()
        posiciones = cargar_posiciones()

        print()
        print("Resumen")
        print("------------------------------")
        print(f"Incendios : {len(incendios)}")
        print(f"Gasoductos: {len(gasoductos)}")
        print(f"Posiciones: {len(posiciones)}")
        print()

        generar_kml(
            incendios,
            gasoductos,
            posiciones
        )

        print()
        print("Proceso terminado correctamente.")

    except Exception as e:

        print()
        print("ERROR")
        print("--------------------------------")
        print(e)
        raise


if __name__ == "__main__":
    main()
