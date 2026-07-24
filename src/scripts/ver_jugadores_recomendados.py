from app.database.base_datos import crear_conexion

import sys
from pathlib import Path


RUTA_SRC = Path(__file__).resolve().parents[1]

if str(RUTA_SRC) not in sys.path:
    sys.path.insert(0, str(RUTA_SRC))


def formatear_rango(minimo, maximo):
    if minimo is None or maximo is None:
        return "Sin suficientes votos"

    if minimo == maximo:
        return str(minimo)

    return f"{minimo}-{maximo}"


def main():
    conexion = crear_conexion()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT
            nombre,
            min_jugadores,
            max_jugadores,
            min_jugadores_recomendados,
            max_jugadores_recomendados,
            min_mejor_num_jugadores,
            max_mejor_num_jugadores
        FROM juegos
        ORDER BY valoracion_media DESC
        LIMIT 30
    """)

    for fila in cursor.fetchall():
        (
            nombre,
            min_oficial,
            max_oficial,
            min_recomendado,
            max_recomendado,
            min_mejor,
            max_mejor
        ) = fila

        print(f"\n{nombre}")
        print(f"  Rango oficial: {min_oficial}-{max_oficial}")
        print(
            "  Rango recomendado: "
            f"{formatear_rango(min_recomendado, max_recomendado)}"
        )
        print(
            "  Mejor número: "
            f"{formatear_rango(min_mejor, max_mejor)}"
        )

    conexion.close()


if __name__ == "__main__":
    main()