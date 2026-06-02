import html
import xml.etree.ElementTree as ET


def obtener_valor(elemento, etiqueta, defecto=None):
    nodo = elemento.find(etiqueta)

    if nodo is None:
        return defecto

    return nodo.attrib.get("value", defecto)


def convertir_entero(valor):
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def convertir_float(valor):
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def extraer_links_por_tipo(item, tipo_link):
    valores = []

    for link in item.findall("link"):
        if link.attrib.get("type") == tipo_link:
            valores.append(link.attrib.get("value"))

    return valores


def parsear_juegos(xml_texto):
    raiz = ET.fromstring(xml_texto)
    juegos = []

    for item in raiz.findall("item"):
        id_bgg = convertir_entero(item.attrib.get("id"))

        nombre = None
        for nodo_nombre in item.findall("name"):
            if nodo_nombre.attrib.get("type") == "primary":
                nombre = nodo_nombre.attrib.get("value")
                break

        descripcion_nodo = item.find("description")
        descripcion = ""

        if descripcion_nodo is not None and descripcion_nodo.text:
            descripcion = html.unescape(descripcion_nodo.text)

        estadisticas = item.find("statistics/ratings")

        valoracion_media = None
        complejidad = None

        if estadisticas is not None:
            valoracion_media = convertir_float(
                obtener_valor(estadisticas, "average")
            )
            complejidad = convertir_float(
                obtener_valor(estadisticas, "averageweight")
            )

        juego = {
            "id_bgg": id_bgg,
            "nombre": nombre,
            "descripcion": descripcion,
            "anio_publicacion": convertir_entero(
                obtener_valor(item, "yearpublished")
            ),
            "min_jugadores": convertir_entero(
                obtener_valor(item, "minplayers")
            ),
            "max_jugadores": convertir_entero(
                obtener_valor(item, "maxplayers")
            ),
            "duracion_minima": convertir_entero(
                obtener_valor(item, "minplaytime")
            ),
            "duracion_maxima": convertir_entero(
                obtener_valor(item, "maxplaytime")
            ),
            "edad_minima": convertir_entero(
                obtener_valor(item, "minage")
            ),
            "valoracion_media": valoracion_media,
            "complejidad": complejidad,
            "categorias": extraer_links_por_tipo(item, "boardgamecategory"),
            "mecanicas": extraer_links_por_tipo(item, "boardgamemechanic"),
            "imagen_url": item.findtext("image")
        }

        juegos.append(juego)

    return juegos