import csv
import time
from pathlib import Path

import sys
from pathlib import Path


RUTA_SRC = Path(__file__).resolve().parents[1]

if str(RUTA_SRC) not in sys.path:
    sys.path.insert(0, str(RUTA_SRC))

from app.services.bgg_api import obtener_juegos_por_ids
from app.services.parser_bgg import parsear_juegos
from app.database.base_datos import (
    crear_tablas,
    guardar_juego,
    existe_juego
)

RUTA_CSV = Path("datos/ids_juegos.csv")
TAMANO_LOTE = 20
SEGUNDOS_ENTRE_LOTES = 8


def leer_ids_desde_csv(ruta_csv):
    ids_juegos = []

    with open(ruta_csv, "r", encoding="utf-8") as archivo:
        lector = csv.DictReader(archivo)

        for fila in lector:
            try:
                id_bgg = int(fila["id_bgg"])
                ids_juegos.append(id_bgg)
            except (ValueError, KeyError):
                print(f"Fila ignorada: {fila}")

    return ids_juegos


def dividir_en_lotes(lista, tamano_lote):
    for indice in range(0, len(lista), tamano_lote):
        yield lista[indice:indice + tamano_lote]


def filtrar_juegos_no_guardados(ids_juegos):
    ids_pendientes = []

    for id_juego in ids_juegos:
        if not existe_juego(id_juego):
            ids_pendientes.append(id_juego)

    return ids_pendientes


def cargar_juegos(ids_juegos):
    crear_tablas()

    ids_pendientes = filtrar_juegos_no_guardados(ids_juegos)

    print(f"IDs recibidos: {len(ids_juegos)}")
    print(f"IDs ya guardados: {len(ids_juegos) - len(ids_pendientes)}")
    print(f"IDs pendientes: {len(ids_pendientes)}")

    total_guardados = 0

    for numero_lote, lote in enumerate(dividir_en_lotes(ids_pendientes, TAMANO_LOTE), start=1):
        print(f"\nLote {numero_lote}: {lote}")

        try:
            xml_texto = obtener_juegos_por_ids(lote)
            juegos = parsear_juegos(xml_texto)

            for juego in juegos:
                guardar_juego(juego)
                total_guardados += 1
                print(f"Guardado: {juego['nombre']}")

        except Exception as error:
            print(f"Error cargando lote {lote}: {error}")

        print(f"Esperando {SEGUNDOS_ENTRE_LOTES} segundos...")
        time.sleep(SEGUNDOS_ENTRE_LOTES)

    print(f"\nCarga finalizada. Juegos nuevos guardados: {total_guardados}")


if __name__ == "__main__":
    ids_juegos = leer_ids_desde_csv(RUTA_CSV)
    cargar_juegos(ids_juegos)