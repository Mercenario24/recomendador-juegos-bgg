from base_datos import crear_conexion


def limpiar_lista_texto(texto):
    if not texto:
        return []

    return [
        elemento.strip().lower()
        for elemento in texto.split(",")
        if elemento.strip()
    ]


def esta_en_rango(valor, minimo, maximo):
    if minimo is None or maximo is None:
        return False

    return minimo <= valor <= maximo


def formatear_rango(minimo, maximo):
    if minimo is None or maximo is None:
        return "Sin datos"

    if minimo == maximo:
        return str(minimo)

    return f"{minimo}-{maximo}"


def obtener_categorias_de_juego(cursor, id_bgg):
    cursor.execute("""
        SELECT c.nombre
        FROM categorias c
        JOIN juego_categoria jc
            ON c.id = jc.categoria_id
        WHERE jc.juego_id = ?
        ORDER BY c.nombre
    """, (id_bgg,))

    return [fila[0] for fila in cursor.fetchall()]


def obtener_mecanicas_de_juego(cursor, id_bgg):
    cursor.execute("""
        SELECT m.nombre
        FROM mecanicas m
        JOIN juego_mecanica jm
            ON m.id = jm.mecanica_id
        WHERE jm.juego_id = ?
        ORDER BY m.nombre
    """, (id_bgg,))

    return [fila[0] for fila in cursor.fetchall()]


def calcular_cobertura_rango(
    minimo_usuario,
    maximo_usuario,
    minimo_juego,
    maximo_juego
):
    if minimo_juego is None or maximo_juego is None:
        return 0.0

    inicio_coincidencia = max(
        minimo_usuario,
        minimo_juego
    )

    fin_coincidencia = min(
        maximo_usuario,
        maximo_juego
    )

    if fin_coincidencia < inicio_coincidencia:
        return 0.0

    total_valores_usuario = (
        maximo_usuario - minimo_usuario + 1
    )

    total_valores_coincidentes = (
        fin_coincidencia - inicio_coincidencia + 1
    )

    return total_valores_coincidentes / total_valores_usuario

def calcular_puntuacion(
    juego,
    num_jugadores_min,
    num_jugadores_max,
    duracion_maxima_usuario,
    complejidad_maxima_usuario,
    mecanicas_preferidas,
    categorias_preferidas
):
    puntuacion = 0
    motivos = []

    valoracion = juego["valoracion_media"] or 0
    duracion = (
        juego["duracion_maxima"]
        or duracion_maxima_usuario
    )
    complejidad = (
        juego["complejidad"]
        or complejidad_maxima_usuario
    )

    puntuacion += valoracion * 10

    cobertura_oficial = calcular_cobertura_rango(
        num_jugadores_min,
        num_jugadores_max,
        juego["min_jugadores"],
        juego["max_jugadores"]
    )

    if cobertura_oficial == 1:
        puntuacion += 10
        motivos.append(
            "admite todo el rango de jugadores indicado"
        )

    cobertura_recomendada = calcular_cobertura_rango(
        num_jugadores_min,
        num_jugadores_max,
        juego["min_jugadores_recomendados"],
        juego["max_jugadores_recomendados"]
    )

    puntuacion += 20 * cobertura_recomendada

    if cobertura_recomendada == 1:
        motivos.append(
            "la comunidad lo recomienda para todo el rango"
        )
    elif cobertura_recomendada > 0:
        motivos.append(
            "la comunidad lo recomienda para parte del rango"
        )

    cobertura_mejor_numero = calcular_cobertura_rango(
        num_jugadores_min,
        num_jugadores_max,
        juego["min_mejor_num_jugadores"],
        juego["max_mejor_num_jugadores"]
    )

    puntuacion += 30 * cobertura_mejor_numero

    if cobertura_mejor_numero == 1:
        motivos.append(
            "todo el rango coincide con su mejor número"
        )
    elif cobertura_mejor_numero > 0:
        motivos.append(
            "parte del rango coincide con su mejor número"
        )

    diferencia_duracion = (
        duracion_maxima_usuario - duracion
    )

    if diferencia_duracion >= 0:
        puntos_duracion = max(
            0,
            12 - diferencia_duracion / 15
        )

        puntuacion += puntos_duracion

        if diferencia_duracion <= 30:
            motivos.append("su duración encaja bien")

    diferencia_complejidad = (
        complejidad_maxima_usuario - complejidad
    )

    if diferencia_complejidad >= 0:
        puntos_complejidad = max(
            0,
            12 - diferencia_complejidad * 4
        )

        puntuacion += puntos_complejidad

        if diferencia_complejidad <= 0.5:
            motivos.append("su complejidad encaja bien")

    mecanicas_juego = " ".join(
        juego["mecanicas"]
    ).lower()

    categorias_juego = " ".join(
        juego["categorias"]
    ).lower()

    for mecanica in mecanicas_preferidas:
        if mecanica.lower() in mecanicas_juego:
            puntuacion += 12
            motivos.append(
                f"incluye la mecánica '{mecanica}'"
            )

    for categoria in categorias_preferidas:
        if categoria.lower() in categorias_juego:
            puntuacion += 10
            motivos.append(
                f"incluye la categoría '{categoria}'"
            )

    return round(puntuacion, 2), motivos

def recomendar_juegos(
    num_jugadores=None,
    duracion_maxima=120,
    complejidad_maxima=3.5,
    mecanicas_preferidas=None,
    categorias_preferidas=None,
    solo_rango_recomendado=False,
    limite=10,
    num_jugadores_min=None,
    num_jugadores_max=None
):
    mecanicas_preferidas = mecanicas_preferidas or []
    categorias_preferidas = categorias_preferidas or []

    # Mantiene compatibilidad con el formulario por consola.
    if num_jugadores_min is None:
        num_jugadores_min = num_jugadores

    if num_jugadores_max is None:
        num_jugadores_max = num_jugadores

    if num_jugadores_min is None:
        raise ValueError(
            "Debes indicar el número mínimo de jugadores."
        )

    if num_jugadores_max is None:
        num_jugadores_max = num_jugadores_min

    if num_jugadores_min > num_jugadores_max:
        raise ValueError(
            "El número mínimo de jugadores no puede "
            "ser mayor que el máximo."
        )

    conexion = crear_conexion()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT
            id_bgg,
            nombre,
            min_jugadores,
            max_jugadores,
            min_jugadores_recomendados,
            max_jugadores_recomendados,
            min_mejor_num_jugadores,
            max_mejor_num_jugadores,
            duracion_minima,
            duracion_maxima,
            complejidad,
            valoracion_media,
            imagen_url
        FROM juegos
        WHERE min_jugadores <= ?
          AND max_jugadores >= ?
          AND duracion_maxima <= ?
          AND complejidad <= ?
          AND valoracion_media IS NOT NULL
        ORDER BY valoracion_media DESC
        LIMIT 1000
    """, (
        num_jugadores_min,
        num_jugadores_max,
        duracion_maxima,
        complejidad_maxima
    ))

    filas = cursor.fetchall()
    juegos = []

    for fila in filas:
        (
            id_bgg,
            nombre,
            min_jugadores,
            max_jugadores,
            min_jugadores_recomendados,
            max_jugadores_recomendados,
            min_mejor_num_jugadores,
            max_mejor_num_jugadores,
            duracion_minima,
            duracion_maxima_juego,
            complejidad,
            valoracion_media,
            imagen_url
        ) = fila

        cobertura_recomendada = calcular_cobertura_rango(
            num_jugadores_min,
            num_jugadores_max,
            min_jugadores_recomendados,
            max_jugadores_recomendados
        )

        if (
            solo_rango_recomendado
            and cobertura_recomendada < 1
        ):
            continue

        juego = {
            "id_bgg": id_bgg,
            "nombre": nombre,
            "min_jugadores": min_jugadores,
            "max_jugadores": max_jugadores,
            "min_jugadores_recomendados":
                min_jugadores_recomendados,
            "max_jugadores_recomendados":
                max_jugadores_recomendados,
            "min_mejor_num_jugadores":
                min_mejor_num_jugadores,
            "max_mejor_num_jugadores":
                max_mejor_num_jugadores,
            "duracion_minima": duracion_minima,
            "duracion_maxima": duracion_maxima_juego,
            "complejidad": complejidad,
            "valoracion_media": valoracion_media,
            "imagen_url": imagen_url,
            "categorias": obtener_categorias_de_juego(
                cursor,
                id_bgg
            ),
            "mecanicas": obtener_mecanicas_de_juego(
                cursor,
                id_bgg
            )
        }

        puntuacion, motivos = calcular_puntuacion(
            juego=juego,
            num_jugadores_min=num_jugadores_min,
            num_jugadores_max=num_jugadores_max,
            duracion_maxima_usuario=duracion_maxima,
            complejidad_maxima_usuario=complejidad_maxima,
            mecanicas_preferidas=mecanicas_preferidas,
            categorias_preferidas=categorias_preferidas
        )

        juego["puntuacion"] = puntuacion
        juego["motivos"] = motivos

        juegos.append(juego)

    conexion.close()

    juegos.sort(
        key=lambda juego: juego["puntuacion"],
        reverse=True
    )

    return juegos[:limite]


def mostrar_recomendaciones(juegos):
    if not juegos:
        print("\nNo se encontraron juegos con esos filtros.")
        print(
            "Prueba aumentando la duración, la complejidad "
            "o desactivando el filtro de jugadores recomendados."
        )
        return

    print("\nJuegos recomendados:\n")

    for posicion, juego in enumerate(juegos, start=1):
        rango_oficial = formatear_rango(
            juego["min_jugadores"],
            juego["max_jugadores"]
        )

        rango_recomendado = formatear_rango(
            juego["min_jugadores_recomendados"],
            juego["max_jugadores_recomendados"]
        )

        mejor_numero = formatear_rango(
            juego["min_mejor_num_jugadores"],
            juego["max_mejor_num_jugadores"]
        )

        print(f"{posicion}. {juego['nombre']}")
        print(
            f"   Puntuación del recomendador: "
            f"{juego['puntuacion']}"
        )
        print(f"   Rango oficial: {rango_oficial}")
        print(f"   Rango recomendado: {rango_recomendado}")
        print(f"   Mejor número: {mejor_numero}")
        print(
            f"   Duración: "
            f"{juego['duracion_minima']}-"
            f"{juego['duracion_maxima']} minutos"
        )
        print(f"   Complejidad: {juego['complejidad']}")
        print(
            f"   Valoración media: "
            f"{juego['valoracion_media']}"
        )
        print(
            f"   Categorías: "
            f"{', '.join(juego['categorias'])}"
        )
        print(
            f"   Mecánicas: "
            f"{', '.join(juego['mecanicas'])}"
        )

        if juego["motivos"]:
            print(
                f"   Motivos: "
                f"{'; '.join(juego['motivos'])}"
            )

        print(f"   Imagen: {juego['imagen_url']}")
        print()