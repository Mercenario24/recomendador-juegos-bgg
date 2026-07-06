from base_datos import crear_conexion


def main():
    conexion = crear_conexion()
    cursor = conexion.cursor()

    cursor.execute("SELECT COUNT(*) FROM juegos")
    total_juegos = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM categorias")
    total_categorias = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM mecanicas")
    total_mecanicas = cursor.fetchone()[0]

    print("Resumen actual")
    print("--------------")
    print(f"Juegos en BD: {total_juegos}")
    print(f"Categorías en BD: {total_categorias}")
    print(f"Mecánicas en BD: {total_mecanicas}")

    conexion.close()


if __name__ == "__main__":
    main()