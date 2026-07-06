from base_datos import crear_conexion


def obtener_categorias_de_juego(cursor, id_bgg):
    cursor.execute("""
        SELECT c.nombre
        FROM categorias c
        JOIN juego_categoria jc ON c.id = jc.categoria_id
        WHERE jc.juego_id = ?
        ORDER BY c.nombre
    """, (id_bgg,))

    return [fila[0] for fila in cursor.fetchall()]


def obtener_mecanicas_de_juego(cursor, id_bgg):
    cursor.execute("""
        SELECT m.nombre
        FROM mecanicas m
        JOIN juego_mecanica jm ON m.id = jm.mecanica_id
        WHERE jm.juego_id = ?
        ORDER BY m.nombre
    """, (id_bgg,))

    return [fila[0] for fila in cursor.fetchall()]


def recomendar_juegos(
    num_jugadores,
    duracion_maxima,
    complejidad_maxima,
    mecanica_preferida=None,
    categoria_preferida=None,
    limite=10
):
    conexion = crear_conexion()
    cursor = conexion.cursor()

    consulta = """
        SELECT DISTINCT
            j.id_bgg,
            j.nombre,
            j.min_jugadores,
            j.max_jugadores,
            j.duracion_maxima,
            j.complejidad,
            j.valoracion_media
        FROM juegos j
    """

    condiciones = """
        WHERE j.min_jugadores <= ?
          AND j.max_jugadores >= ?
          AND j.duracion_maxima <= ?
          AND j.complejidad <= ?
          AND j.valoracion_media IS NOT NULL
    """

    parametros = [
        num_jugadores,
        num_jugadores,
        duracion_maxima,
        complejidad_maxima
    ]

    if mecanica_preferida:
        consulta += """
            JOIN juego_mecanica jm ON j.id_bgg = jm.juego_id
            JOIN mecanicas m ON jm.mecanica_id = m.id
        """

        condiciones += """
          AND LOWER(m.nombre) LIKE LOWER(?)
        """

        parametros.append(f"%{mecanica_preferida}%")

    if categoria_preferida:
        consulta += """
            JOIN juego_categoria jc ON j.id_bgg = jc.juego_id
            JOIN categorias c ON jc.categoria_id = c.id
        """

        condiciones += """
          AND LOWER(c.nombre) LIKE LOWER(?)
        """

        parametros.append(f"%{categoria_preferida}%")

    consulta += condiciones

    consulta += """
        ORDER BY 
            j.valoracion_media DESC,
            j.complejidad ASC
        LIMIT ?
    """

    parametros.append(limite)

    cursor.execute(consulta, parametros)

    filas = cursor.fetchall()
    juegos = []

    for fila in filas:
        (
            id_bgg,
            nombre,
            min_jugadores,
            max_jugadores,
            duracion_maxima_juego,
            complejidad,
            valoracion_media
        ) = fila

        categorias = obtener_categorias_de_juego(cursor, id_bgg)
        mecanicas = obtener_mecanicas_de_juego(cursor, id_bgg)

        juegos.append({
            "id_bgg": id_bgg,
            "nombre": nombre,
            "min_jugadores": min_jugadores,
            "max_jugadores": max_jugadores,
            "duracion_maxima": duracion_maxima_juego,
            "complejidad": complejidad,
            "valoracion_media": valoracion_media,
            "categorias": categorias,
            "mecanicas": mecanicas
        })

    conexion.close()
    return juegos


def mostrar_recomendaciones(juegos):
    if not juegos:
        print("\nNo se encontraron juegos con esos filtros.")
        print("Prueba aumentando la duración máxima, la complejidad máxima o dejando vacía la mecánica/categoría.")
        return

    print("\nJuegos recomendados:\n")

    for posicion, juego in enumerate(juegos, start=1):
        print(f"{posicion}. {juego['nombre']}")
        print(f"   Jugadores: {juego['min_jugadores']}-{juego['max_jugadores']}")
        print(f"   Duración máxima: {juego['duracion_maxima']} min")
        print(f"   Complejidad: {juego['complejidad']}")
        print(f"   Valoración media: {juego['valoracion_media']}")
        print(f"   Categorías: {', '.join(juego['categorias'])}")
        print(f"   Mecánicas: {', '.join(juego['mecanicas'])}")
        print()


if __name__ == "__main__":
    juegos = recomendar_juegos(
        num_jugadores=4,
        duracion_maxima=180,
        complejidad_maxima=5,
        mecanica_preferida="draft",
        categoria_preferida="science"
    )

    mostrar_recomendaciones(juegos)