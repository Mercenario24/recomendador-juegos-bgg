from app.database.base_datos import crear_conexion

import sys
from pathlib import Path


RUTA_SRC = Path(__file__).resolve().parents[1]

if str(RUTA_SRC) not in sys.path:
    sys.path.insert(0, str(RUTA_SRC))


def mostrar_resumen():
    conexion = crear_conexion()
    cursor = conexion.cursor()

    cursor.execute("SELECT COUNT(*) FROM juegos")
    total_juegos = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM categorias")
    total_categorias = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM mecanicas")
    total_mecanicas = cursor.fetchone()[0]

    print("Resumen de la base de datos")
    print("---------------------------")
    print(f"Juegos guardados: {total_juegos}")
    print(f"Categorías guardadas: {total_categorias}")
    print(f"Mecánicas guardadas: {total_mecanicas}")

    print("\nCategorías:")
    cursor.execute("""
        SELECT nombre
        FROM categorias
        ORDER BY nombre
        LIMIT 30
    """)

    for fila in cursor.fetchall():
        print(f"- {fila[0]}")

    print("\nMecánicas:")
    cursor.execute("""
        SELECT nombre
        FROM mecanicas
        ORDER BY nombre
        LIMIT 30
    """)

    for fila in cursor.fetchall():
        print(f"- {fila[0]}")

    conexion.close()


if __name__ == "__main__":
    mostrar_resumen()