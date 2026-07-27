import sys
import time
from pathlib import Path

RUTA_SRC = Path(__file__).resolve().parents[1]

if str(RUTA_SRC) not in sys.path:
    sys.path.insert(0, str(RUTA_SRC))

from app.database.base_datos import (
    asegurar_columnas_rankings_bgg,
    crear_conexion,
    guardar_juego
)
from app.services.bgg_api import obtener_juegos_por_ids
from app.services.parser_bgg import parsear_juegos


def obtener_ids_juegos():
    conexion = crear_conexion()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT id_bgg
        FROM juegos
        ORDER BY id_bgg ASC
    """)

    ids_juegos = [
        fila[0]
        for fila in cursor.fetchall()
    ]

    conexion.close()

    return ids_juegos


def dividir_en_lotes(lista, tamano_lote):
    for indice in range(0, len(lista), tamano_lote):
        yield lista[indice:indice + tamano_lote]


def main():
    asegurar_columnas_rankings_bgg()

    ids_juegos = obtener_ids_juegos()
    lotes = list(dividir_en_lotes(ids_juegos, 20))

    total = len(ids_juegos)
    actualizados = 0
    errores = []

    print(f"Juegos encontrados: {total}")
    print(f"Lotes a procesar: {len(lotes)}")

    for numero_lote, lote in enumerate(lotes, start=1):
        print()
        print(f"Actualizando lote {numero_lote}/{len(lotes)}")
        print(lote)

        try:
            xml_texto = obtener_juegos_por_ids(lote)
            juegos = parsear_juegos(xml_texto)

            for juego in juegos:
                guardar_juego(juego)
                actualizados += 1

            print(f"Actualizados: {actualizados}/{total}")

        except Exception as error:
            mensaje_error = f"Lote {numero_lote} {lote}: {error}"
            errores.append(mensaje_error)
            print(mensaje_error)

        if numero_lote < len(lotes):
            time.sleep(5)

    print()
    print("Proceso terminado.")
    print(f"Actualizados: {actualizados}/{total}")

    if errores:
        print()
        print("Errores encontrados:")
        for error in errores:
            print(error)


if __name__ == "__main__":
    main()