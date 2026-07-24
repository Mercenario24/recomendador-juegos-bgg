from app.database.base_datos import crear_conexion


def mostrar_juegos():
    conexion = crear_conexion()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT 
            nombre,
            min_jugadores,
            max_jugadores,
            duracion_maxima,
            complejidad,
            valoracion_media
        FROM juegos
        ORDER BY valoracion_media DESC
    """)

    juegos = cursor.fetchall()

    conexion.close()

    for juego in juegos:
        nombre, min_jugadores, max_jugadores, duracion_maxima, complejidad, valoracion_media = juego

        print("--------------------------------")
        print(f"Nombre: {nombre}")
        print(f"Jugadores: {min_jugadores}-{max_jugadores}")
        print(f"Duración máxima: {duracion_maxima} min")
        print(f"Complejidad: {complejidad}")
        print(f"Valoración media: {valoracion_media}")


if __name__ == "__main__":
    mostrar_juegos()