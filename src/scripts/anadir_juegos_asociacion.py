import sys
import time
from pathlib import Path

RUTA_SRC = Path(__file__).resolve().parents[1]

if str(RUTA_SRC) not in sys.path:
    sys.path.insert(0, str(RUTA_SRC))

from app.auth.usuarios import (
    asegurar_columnas_usuarios,
    obtener_usuario_por_email
)
from app.database.base_datos import (
    crear_conexion,
    existe_juego,
    guardar_juego
)
from app.library.ludoteca import (
    anadir_juego_a_ludoteca,
    crear_tablas_ludoteca
)
from app.services.bgg_api import obtener_juegos_por_ids
from app.services.parser_bgg import parsear_juegos


def extraer_ids(argumentos):
    ids = []

    for argumento in argumentos:
        partes = str(argumento).replace(",", " ").split()

        for parte in partes:
            parte = parte.strip()

            if not parte:
                continue

            try:
                id_bgg = int(parte)
            except ValueError:
                print(f"ID ignorado porque no es número: {parte}")
                continue

            if id_bgg > 0 and id_bgg not in ids:
                ids.append(id_bgg)

    return ids


def dividir_en_lotes(lista, tamano_lote):
    for indice in range(0, len(lista), tamano_lote):
        yield lista[indice:indice + tamano_lote]


def obtener_ids_no_existentes(ids_juegos):
    return [
        id_bgg
        for id_bgg in ids_juegos
        if not existe_juego(id_bgg)
    ]


def descargar_juegos_no_existentes(ids_juegos):
    ids_pendientes = obtener_ids_no_existentes(ids_juegos)

    if not ids_pendientes:
        print("Todos los juegos ya existen en la base de datos.")
        return

    print(f"Juegos no existentes que se descargarán: {len(ids_pendientes)}")

    lotes = list(dividir_en_lotes(ids_pendientes, 20))

    for numero_lote, lote in enumerate(lotes, start=1):
        print(f"Descargando lote {numero_lote}/{len(lotes)}: {lote}")

        xml_texto = obtener_juegos_por_ids(lote)
        juegos = parsear_juegos(xml_texto)

        for juego in juegos:
            guardar_juego(juego)
            print(f"Guardado: {juego.get('nombre')} ({juego.get('id_bgg')})")

        if numero_lote < len(lotes):
            time.sleep(5)


def main():
    if len(sys.argv) < 3:
        print("Uso:")
        print("python src/scripts/anadir_juegos_asociacion.py email@ejemplo.com 174430 31260 224517")
        print()
        print("También puedes separar IDs con comas:")
        print("python src/scripts/anadir_juegos_asociacion.py email@ejemplo.com 174430,31260,224517")
        return

    email = sys.argv[1].strip()
    ids_juegos = extraer_ids(sys.argv[2:])

    if not ids_juegos:
        print("No has indicado ningún ID válido.")
        return

    asegurar_columnas_usuarios()
    crear_tablas_ludoteca()

    usuario = obtener_usuario_por_email(email)

    if usuario is None:
        print(f"No existe ningún usuario con email: {email}")
        return

    if usuario.get("tipo_cuenta") != "asociacion":
        print(f"El usuario {email} no es una cuenta de asociación.")
        print("Primero conviértelo con:")
        print(f"python src/scripts/convertir_usuario_en_asociacion.py {email}")
        return

    print(f"Asociación encontrada: {usuario['nombre']} ({usuario['email']})")
    print(f"IDs recibidos: {ids_juegos}")

    descargar_juegos_no_existentes(ids_juegos)

    juegos_anadidos = 0

    for id_bgg in ids_juegos:
        anadir_juego_a_ludoteca(
            usuario_id=usuario["id"],
            juego_id=id_bgg
        )

        juegos_anadidos += 1

    print()
    print("Proceso terminado.")
    print(f"Juegos añadidos a la ludoteca de la asociación: {juegos_anadidos}")


if __name__ == "__main__":
    main()