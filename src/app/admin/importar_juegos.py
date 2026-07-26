import re
import time

from app.database.base_datos import crear_conexion, guardar_juego
from app.services.bgg_api import obtener_juegos_por_ids
from app.services.parser_bgg import parsear_juegos


def extraer_ids_bgg(texto):
    ids = re.findall(r"\d+", str(texto or ""))

    ids_limpios = []

    for id_texto in ids:
        id_bgg = int(id_texto)

        if id_bgg > 0 and id_bgg not in ids_limpios:
            ids_limpios.append(id_bgg)

    return ids_limpios


def obtener_ids_juegos_existentes(ids_juegos):
    if not ids_juegos:
        return set()

    conexion = crear_conexion()
    cursor = conexion.cursor()

    marcadores = ",".join(["?"] * len(ids_juegos))

    cursor.execute(f"""
        SELECT id_bgg
        FROM juegos
        WHERE id_bgg IN ({marcadores})
    """, ids_juegos)

    existentes = {
        int(fila[0])
        for fila in cursor.fetchall()
    }

    conexion.close()

    return existentes


def dividir_en_lotes(lista, tamano_lote):
    for indice in range(0, len(lista), tamano_lote):
        yield lista[indice:indice + tamano_lote]


def obtener_id_desde_juego(juego):
    return (
        juego.get("id_bgg")
        or juego.get("id")
        or juego.get("id_juego")
    )


def obtener_nombre_desde_juego(juego):
    return (
        juego.get("nombre")
        or juego.get("name")
        or "Sin nombre"
    )


def importar_juegos_admin(texto_ids, tamano_lote=20, pausa_segundos=5):
    ids_recibidos = extraer_ids_bgg(texto_ids)

    if not ids_recibidos:
        raise ValueError("No se ha introducido ningún ID válido de BGG.")

    ids_existentes = obtener_ids_juegos_existentes(ids_recibidos)

    ids_pendientes = [
        id_bgg
        for id_bgg in ids_recibidos
        if id_bgg not in ids_existentes
    ]

    resultado = {
        "ids_recibidos": ids_recibidos,
        "ids_existentes": sorted(ids_existentes),
        "ids_pendientes": ids_pendientes,
        "juegos_guardados": [],
        "ids_no_descargados": [],
        "errores": []
    }

    if not ids_pendientes:
        return resultado

    for lote in dividir_en_lotes(ids_pendientes, tamano_lote):
        try:
            xml = obtener_juegos_por_ids(lote)
            juegos = parsear_juegos(xml)

            ids_descargados_lote = set()

            for juego in juegos:
                id_bgg = obtener_id_desde_juego(juego)

                if id_bgg is None:
                    continue

                id_bgg = int(id_bgg)
                ids_descargados_lote.add(id_bgg)

                guardar_juego(juego)

                resultado["juegos_guardados"].append({
                    "id_bgg": id_bgg,
                    "nombre": obtener_nombre_desde_juego(juego)
                })

            for id_bgg in lote:
                if id_bgg not in ids_descargados_lote:
                    resultado["ids_no_descargados"].append(id_bgg)

        except Exception as error:
            resultado["errores"].append(
                f"Error importando lote {lote}: {error}"
            )

        time.sleep(pausa_segundos)

    return resultado