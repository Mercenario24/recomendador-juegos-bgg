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
            valor = link.attrib.get("value")

            if valor:
                valores.append(valor)

    return valores


def convertir_etiqueta_jugadores(etiqueta):
    """
    Convierte etiquetas como '1', '4' o '6+' en un número entero.
    En el caso de '6+', devuelve 6.
    """
    if not etiqueta:
        return None

    texto = etiqueta.strip().replace("+", "")

    try:
        return int(texto)
    except ValueError:
        return None


def calcular_limites_jugadores(etiquetas, max_jugadores_oficial):
    """
    Convierte una lista de etiquetas en un rango mínimo y máximo.

    Ejemplos:
        ['2', '3', '4'] -> (2, 4)
        ['6+'] -> (6, max_jugadores_oficial)
    """
    if not etiquetas:
        return None, None

    numeros = []
    contiene_mas = False

    for etiqueta in etiquetas:
        numero = convertir_etiqueta_jugadores(etiqueta)

        if numero is not None:
            numeros.append(numero)

        if etiqueta.strip().endswith("+"):
            contiene_mas = True

    if not numeros:
        return None, None

    minimo = min(numeros)
    maximo = max(numeros)

    if (
        contiene_mas
        and max_jugadores_oficial is not None
        and max_jugadores_oficial >= maximo
    ):
        maximo = max_jugadores_oficial

    return minimo, maximo


def extraer_recomendacion_jugadores(item, max_jugadores_oficial):
    """
    Lee la encuesta 'suggested_numplayers' de BGG.

    Consideramos recomendado un número de jugadores cuando:

        votos Best + votos Recommended > votos Not Recommended

    El mejor número se obtiene buscando el mayor porcentaje de votos Best.
    """
    encuesta = item.find("./poll[@name='suggested_numplayers']")

    resultado_vacio = {
        "min_jugadores_recomendados": None,
        "max_jugadores_recomendados": None,
        "min_mejor_num_jugadores": None,
        "max_mejor_num_jugadores": None
    }

    if encuesta is None:
        return resultado_vacio

    resultados_jugadores = []

    for grupo_resultados in encuesta.findall("results"):
        etiqueta_jugadores = grupo_resultados.attrib.get("numplayers")

        if not etiqueta_jugadores:
            continue

        votos = {
            "Best": 0,
            "Recommended": 0,
            "Not Recommended": 0
        }

        for resultado in grupo_resultados.findall("result"):
            tipo_voto = resultado.attrib.get("value")
            num_votos = convertir_entero(
                resultado.attrib.get("numvotes")
            ) or 0

            if tipo_voto in votos:
                votos[tipo_voto] = num_votos

        total_votos = sum(votos.values())

        if total_votos == 0:
            continue

        porcentaje_mejor = votos["Best"] / total_votos

        resultados_jugadores.append({
            "etiqueta": etiqueta_jugadores,
            "votos_mejor": votos["Best"],
            "votos_recomendado": votos["Recommended"],
            "votos_no_recomendado": votos["Not Recommended"],
            "porcentaje_mejor": porcentaje_mejor
        })

    if not resultados_jugadores:
        return resultado_vacio

    etiquetas_recomendadas = []

    for resultado in resultados_jugadores:
        votos_positivos = (
            resultado["votos_mejor"]
            + resultado["votos_recomendado"]
        )

        if votos_positivos > resultado["votos_no_recomendado"]:
            etiquetas_recomendadas.append(resultado["etiqueta"])

    resultados_con_votos_mejor = [
        resultado
        for resultado in resultados_jugadores
        if resultado["votos_mejor"] > 0
    ]

    etiquetas_mejor_numero = []

    if resultados_con_votos_mejor:
        porcentaje_maximo = max(
            resultado["porcentaje_mejor"]
            for resultado in resultados_con_votos_mejor
        )

        etiquetas_mejor_numero = [
            resultado["etiqueta"]
            for resultado in resultados_con_votos_mejor
            if abs(
                resultado["porcentaje_mejor"] - porcentaje_maximo
            ) < 0.000001
        ]

    (
        min_jugadores_recomendados,
        max_jugadores_recomendados
    ) = calcular_limites_jugadores(
        etiquetas_recomendadas,
        max_jugadores_oficial
    )

    (
        min_mejor_num_jugadores,
        max_mejor_num_jugadores
    ) = calcular_limites_jugadores(
        etiquetas_mejor_numero,
        max_jugadores_oficial
    )

    return {
        "min_jugadores_recomendados": min_jugadores_recomendados,
        "max_jugadores_recomendados": max_jugadores_recomendados,
        "min_mejor_num_jugadores": min_mejor_num_jugadores,
        "max_mejor_num_jugadores": max_mejor_num_jugadores
    }


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

        max_jugadores = convertir_entero(
            obtener_valor(item, "maxplayers")
        )

        recomendacion_jugadores = extraer_recomendacion_jugadores(
            item,
            max_jugadores
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
            "max_jugadores": max_jugadores,
            "min_jugadores_recomendados":
                recomendacion_jugadores["min_jugadores_recomendados"],
            "max_jugadores_recomendados":
                recomendacion_jugadores["max_jugadores_recomendados"],
            "min_mejor_num_jugadores":
                recomendacion_jugadores["min_mejor_num_jugadores"],
            "max_mejor_num_jugadores":
                recomendacion_jugadores["max_mejor_num_jugadores"],
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
            "categorias": extraer_links_por_tipo(
                item,
                "boardgamecategory"
            ),
            "mecanicas": extraer_links_por_tipo(
                item,
                "boardgamemechanic"
            ),
            "imagen_url": item.findtext("image")
        }

        juegos.append(juego)

    return juegos