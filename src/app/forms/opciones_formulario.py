from app.database.base_datos import crear_conexion


def obtener_mecanicas_populares(limite=50):
    conexion = crear_conexion()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT
            nombre,
            total_juegos
        FROM (
            SELECT
                m.nombre AS nombre,
                COUNT(jm.juego_id) AS total_juegos
            FROM mecanicas m
            JOIN juego_mecanica jm
                ON m.id = jm.mecanica_id
            GROUP BY m.id, m.nombre
            ORDER BY total_juegos DESC, m.nombre COLLATE NOCASE ASC
            LIMIT ?
        )
        ORDER BY nombre COLLATE NOCASE ASC
    """, (limite,))

    mecanicas = cursor.fetchall()
    conexion.close()

    return mecanicas


def obtener_categorias_populares(limite=50):
    conexion = crear_conexion()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT
            nombre,
            total_juegos
        FROM (
            SELECT
                c.nombre AS nombre,
                COUNT(jc.juego_id) AS total_juegos
            FROM categorias c
            JOIN juego_categoria jc
                ON c.id = jc.categoria_id
            GROUP BY c.id, c.nombre
            ORDER BY total_juegos DESC, c.nombre COLLATE NOCASE ASC
            LIMIT ?
        )
        ORDER BY nombre COLLATE NOCASE ASC
    """, (limite,))

    categorias = cursor.fetchall()
    conexion.close()

    return categorias


def obtener_tipos_juego():
    return [
        {
            "valor": "",
            "nombre": "Cualquier tipo"
        },
        {
            "valor": "estrategia",
            "nombre": "Estrategia"
        },
        {
            "valor": "tematico",
            "nombre": "Temático"
        },
        {
            "valor": "familiar",
            "nombre": "Familiar"
        },
        {
            "valor": "abstracto",
            "nombre": "Abstracto"
        },
        {
            "valor": "party",
            "nombre": "Party"
        },
        {
            "valor": "cooperativo",
            "nombre": "Cooperativo"
        },
        {
            "valor": "cartas",
            "nombre": "Cartas"
        },
        {
            "valor": "eurogame",
            "nombre": "Eurogame"
        },
        {
            "valor": "wargame",
            "nombre": "Wargame"
        }
    ]


def mostrar_opciones(titulo, opciones):
    print(f"\n{titulo}")
    print("-" * len(titulo))

    for posicion, (nombre, total_juegos) in enumerate(
        opciones,
        start=1
    ):
        print(
            f"{posicion:2}. {nombre} "
            f"({total_juegos} juegos)"
        )

    print(" 0. Ninguna preferencia")


def seleccionar_opciones(titulo, opciones):
    mostrar_opciones(titulo, opciones)

    while True:
        entrada = input(
            "\nSelecciona una o varias opciones "
            "separadas por comas: "
        ).strip()

        if entrada == "" or entrada == "0":
            return []

        try:
            posiciones = [
                int(valor.strip())
                for valor in entrada.split(",")
                if valor.strip()
            ]

        except ValueError:
            print(
                "Introduce números separados por comas. "
                "Ejemplo: 1,4,7"
            )
            continue

        posiciones_invalidas = [
            posicion
            for posicion in posiciones
            if posicion < 1 or posicion > len(opciones)
        ]

        if posiciones_invalidas:
            print(
                "Estas opciones no existen: "
                f"{posiciones_invalidas}"
            )
            continue

        opciones_seleccionadas = []
        posiciones_usadas = set()

        for posicion in posiciones:
            if posicion in posiciones_usadas:
                continue

            posiciones_usadas.add(posicion)

            nombre = opciones[posicion - 1][0]
            opciones_seleccionadas.append(nombre.lower())

        return opciones_seleccionadas