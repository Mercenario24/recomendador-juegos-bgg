from app.database.base_datos import crear_conexion
import unicodedata


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

def normalizar_texto(texto):
    texto = str(texto or "").lower().strip()

    texto = "".join(
        caracter
        for caracter in unicodedata.normalize("NFD", texto)
        if unicodedata.category(caracter) != "Mn"
    )

    return texto


def convertir_a_lista(valor):
    if valor is None:
        return []

    if isinstance(valor, list):
        return valor

    return [
        parte.strip()
        for parte in str(valor).split(",")
        if parte.strip()
    ]


REGLAS_TIPOS_JUEGO = {
    "estrategia": [
        "strategy",
        "economic",
        "civilization",
        "territory building",
        "worker placement",
        "action points",
        "area majority",
        "area control",
        "hand management",
        "variable player powers",
        "network and route building"
    ],
    "tematico": [
        "thematic",
        "adventure",
        "fantasy",
        "science fiction",
        "horror",
        "fighting",
        "exploration",
        "miniatures",
        "scenario",
        "narrative",
        "role playing"
    ],
    "familiar": [
        "family",
        "children",
        "educational",
        "animals",
        "dice",
        "memory",
        "pattern recognition",
        "party"
    ],
    "abstracto": [
        "abstract",
        "abstract strategy",
        "grid movement",
        "pattern building",
        "pattern recognition",
        "tile placement"
    ],
    "party": [
        "party",
        "humor",
        "bluffing",
        "acting",
        "deduction",
        "real-time",
        "word game"
    ],
    "cooperativo": [
        "cooperative",
        "cooperative game",
        "team-based",
        "communication limits",
        "traitor game"
    ],
    "cartas": [
        "card game",
        "deck",
        "hand management",
        "deck bag and pool building",
        "trick-taking",
        "set collection"
    ],
    "eurogame": [
        "economic",
        "farming",
        "industry",
        "worker placement",
        "resource management",
        "auction",
        "tile placement",
        "contracts",
        "network and route building"
    ],
    "wargame": [
        "wargame",
        "war",
        "world war",
        "civil war",
        "napoleonic",
        "hexagon grid",
        "simulation",
        "campaign",
        "combat"
    ]
}


def obtener_texto_clasificacion_juego(juego):
    categorias = convertir_a_lista(
        juego.get("categorias")
    )

    mecanicas = convertir_a_lista(
        juego.get("mecanicas")
    )

    partes = []

    partes.extend(categorias)
    partes.extend(mecanicas)
    partes.append(juego.get("nombre", ""))
    partes.append(juego.get("descripcion", ""))

    return normalizar_texto(
        " ".join(str(parte) for parte in partes)
    )


def juego_coincide_con_tipo(juego, tipo_juego):
    tipo_juego = normalizar_texto(tipo_juego)

    if not tipo_juego:
        return True

    palabras_clave = REGLAS_TIPOS_JUEGO.get(tipo_juego)

    if not palabras_clave:
        return True

    texto_juego = obtener_texto_clasificacion_juego(juego)

    for palabra_clave in palabras_clave:
        if normalizar_texto(palabra_clave) in texto_juego:
            return True

    return False

def recomendar_juegos(
    num_jugadores=None,
    duracion_maxima=120,
    complejidad_maxima=3.5,
    mecanicas_preferidas=None,
    categorias_preferidas=None,
    tipo_juego=None,
    solo_rango_recomendado=False,
    limite=10,
    num_jugadores_min=None,
    num_jugadores_max=None,
    usuario_id=None,
    solo_ludoteca=False
):
    mecanicas_preferidas = mecanicas_preferidas or []
    categorias_preferidas = categorias_preferidas or []

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
            "El número mínimo de jugadores no puede ser mayor que el máximo."
        )

    if solo_ludoteca and usuario_id is None:
        raise ValueError(
            "Para buscar solo en la ludoteca debes iniciar sesión."
        )

    conexion = crear_conexion()
    cursor = conexion.cursor()

    consulta = """
        SELECT
            j.id_bgg,
            j.nombre,
            j.min_jugadores,
            j.max_jugadores,
            j.min_jugadores_recomendados,
            j.max_jugadores_recomendados,
            j.min_mejor_num_jugadores,
            j.max_mejor_num_jugadores,
            j.duracion_minima,
            j.duracion_maxima,
            j.complejidad,
            j.valoracion_media,
            j.imagen_url
        FROM juegos j
    """

    parametros = []

    if solo_ludoteca:
        consulta += """
            JOIN ludoteca_usuario lu
                ON j.id_bgg = lu.juego_id
        """

    consulta += """
        WHERE j.min_jugadores <= ?
          AND j.max_jugadores >= ?
          AND j.duracion_maxima <= ?
          AND j.complejidad <= ?
          AND j.valoracion_media IS NOT NULL
    """

    parametros.extend([
        num_jugadores_min,
        num_jugadores_max,
        duracion_maxima,
        complejidad_maxima
    ])

    if solo_ludoteca:
        consulta += """
          AND lu.usuario_id = ?
        """

        parametros.append(usuario_id)

    consulta += """
        ORDER BY j.valoracion_media DESC
        LIMIT 1000
    """

    cursor.execute(consulta, parametros)

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

        if solo_rango_recomendado and cobertura_recomendada < 1:
            continue

        categorias_juego = obtener_categorias_de_juego(
            cursor,
            id_bgg
        )

        mecanicas_juego = obtener_mecanicas_de_juego(
            cursor,
            id_bgg
        )

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
            "categorias": categorias_juego,
            "mecanicas": mecanicas_juego
        }

        if not juego_coincide_con_tipo(juego, tipo_juego):
            continue

        puntuacion, motivos = calcular_puntuacion(
            juego=juego,
            num_jugadores_min=num_jugadores_min,
            num_jugadores_max=num_jugadores_max,
            duracion_maxima_usuario=duracion_maxima,
            complejidad_maxima_usuario=complejidad_maxima,
            mecanicas_preferidas=mecanicas_preferidas,
            categorias_preferidas=categorias_preferidas
        )

        if solo_ludoteca:
            motivos.insert(
                0,
                "está en tu ludoteca"
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