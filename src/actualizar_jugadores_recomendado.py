import time

from base_datos import (
    crear_conexion,
    crear_tablas,
    guardar_juego
)
from bgg_api import obtener_juegos_por_ids
from parser_bgg import parsear_juegos


TAMANO_LOTE = 20
SEGUNDOS_ENTRE_LOTES = 5


def obtener_ids_guardados():
    conexion = crear_conexion()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT id_bgg
        FROM juegos
        ORDER BY id_bgg
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


def actualizar_juegos():
    crear_tablas()

    ids_juegos = obtener_ids_guardados()
    total_actualizados = 0
    total_errores = 0

    print(f"Juegos que se van a actualizar: {len(ids_juegos)}")

    for numero_lote, lote in enumerate(
        dividir_en_lotes(ids_juegos, TAMANO_LOTE),
        start=1
    ):
        print(f"\nActualizando lote {numero_lote}: {lote}")

        try:
            xml_texto = obtener_juegos_por_ids(lote)
            juegos = parsear_juegos(xml_texto)

            for juego in juegos:
                guardar_juego(juego)
                total_actualizados += 1

                recomendado_min = juego["min_jugadores_recomendados"]
                recomendado_max = juego["max_jugadores_recomendados"]
                mejor_min = juego["min_mejor_num_jugadores"]
                mejor_max = juego["max_mejor_num_jugadores"]

                print(
                    f"Actualizado: {juego['nombre']} | "
                    f"Recomendado: {recomendado_min}-{recomendado_max} | "
                    f"Mejor: {mejor_min}-{mejor_max}"
                )

        except Exception as error:
            total_errores += len(lote)
            print(f"Error actualizando el lote: {error}")

        time.sleep(SEGUNDOS_ENTRE_LOTES)

    print("\nActualización finalizada")
    print(f"Juegos actualizados: {total_actualizados}")
    print(f"Juegos con error: {total_errores}")


if __name__ == "__main__":
    actualizar_juegos()