from base_datos import crear_conexion


def recomendar_juegos(num_jugadores, duracion_maxima, complejidad_maxima, limite=10):
    conexion = crear_conexion()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT 
            nombre,
            min_jugadores,
            max_jugadores,
            duracion_maxima,
            complejidad,
            valoracion_media,
            categorias,
            mecanicas
        FROM juegos
        WHERE min_jugadores <= ?
          AND max_jugadores >= ?
          AND duracion_maxima <= ?
          AND complejidad <= ?
        ORDER BY valoracion_media DESC
        LIMIT ?
    """, (
        num_jugadores,
        num_jugadores,
        duracion_maxima,
        complejidad_maxima,
        limite
    ))

    juegos = cursor.fetchall()
    conexion.close()

    return juegos


def mostrar_recomendaciones(juegos):
    if not juegos:
        print("No se encontraron juegos con esos filtros.")
        return

    print("\nJuegos recomendados:\n")

    for posicion, juego in enumerate(juegos, start=1):
        (
            nombre,
            min_jugadores,
            max_jugadores,
            duracion_maxima,
            complejidad,
            valoracion_media,
            categorias,
            mecanicas
        ) = juego

        print(f"{posicion}. {nombre}")
        print(f"   Jugadores: {min_jugadores}-{max_jugadores}")
        print(f"   Duración máxima: {duracion_maxima} min")
        print(f"   Complejidad: {complejidad}")
        print(f"   Valoración media: {valoracion_media}")
        print(f"   Categorías: {categorias}")
        print(f"   Mecánicas: {mecanicas}")
        print()


if __name__ == "__main__":
    juegos = recomendar_juegos(
        num_jugadores=4,
        duracion_maxima=120,
        complejidad_maxima=4.0
    )

    mostrar_recomendaciones(juegos)