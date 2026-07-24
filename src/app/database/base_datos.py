import sqlite3

from app.config import RUTA_BD


def crear_conexion():
    RUTA_BD.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    conexion = sqlite3.connect(RUTA_BD)
    conexion.execute("PRAGMA foreign_keys = ON")

    return conexion


def existe_juego(id_bgg):
    conexion = crear_conexion()
    cursor = conexion.cursor()

    cursor.execute(
        "SELECT 1 FROM juegos WHERE id_bgg = ?",
        (id_bgg,)
    )

    existe = cursor.fetchone() is not None

    conexion.close()
    return existe

def asegurar_columna(cursor, tabla, columna, tipo):
    cursor.execute(f"PRAGMA table_info({tabla})")

    columnas_existentes = {
        fila[1]
        for fila in cursor.fetchall()
    }

    if columna not in columnas_existentes:
        cursor.execute(
            f"ALTER TABLE {tabla} ADD COLUMN {columna} {tipo}"
        )

def crear_tablas():
    conexion = crear_conexion()
    cursor = conexion.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS juegos (
            id_bgg INTEGER PRIMARY KEY,
            nombre TEXT NOT NULL,
            descripcion TEXT,
            anio_publicacion INTEGER,
            min_jugadores INTEGER,
            max_jugadores INTEGER,
            min_jugadores_recomendados INTEGER,
            max_jugadores_recomendados INTEGER,
            min_mejor_num_jugadores INTEGER,
            max_mejor_num_jugadores INTEGER,
            duracion_minima INTEGER,
            duracion_maxima INTEGER,
            edad_minima INTEGER,
            valoracion_media REAL,
            complejidad REAL,
            imagen_url TEXT
        )
    """)

    asegurar_columna(
        cursor,
        "juegos",
        "min_jugadores_recomendados",
        "INTEGER"
    )

    asegurar_columna(
        cursor,
        "juegos",
        "max_jugadores_recomendados",
        "INTEGER"
    )

    asegurar_columna(
        cursor,
        "juegos",
        "min_mejor_num_jugadores",
        "INTEGER"
    )

    asegurar_columna(
        cursor,
        "juegos",
        "max_mejor_num_jugadores",
        "INTEGER"
    )

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mecanicas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS juego_categoria (
            juego_id INTEGER NOT NULL,
            categoria_id INTEGER NOT NULL,
            PRIMARY KEY (juego_id, categoria_id),
            FOREIGN KEY (juego_id) REFERENCES juegos(id_bgg),
            FOREIGN KEY (categoria_id) REFERENCES categorias(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS juego_mecanica (
            juego_id INTEGER NOT NULL,
            mecanica_id INTEGER NOT NULL,
            PRIMARY KEY (juego_id, mecanica_id),
            FOREIGN KEY (juego_id) REFERENCES juegos(id_bgg),
            FOREIGN KEY (mecanica_id) REFERENCES mecanicas(id)
        )
    """)

    conexion.commit()
    conexion.close()


def obtener_o_crear_id(cursor, tabla, nombre):
    cursor.execute(f"SELECT id FROM {tabla} WHERE nombre = ?", (nombre,))
    fila = cursor.fetchone()

    if fila:
        return fila[0]

    cursor.execute(f"INSERT INTO {tabla} (nombre) VALUES (?)", (nombre,))
    return cursor.lastrowid


def guardar_juego(juego):
    conexion = crear_conexion()
    cursor = conexion.cursor()

    cursor.execute("""
        INSERT INTO juegos (
            id_bgg,
            nombre,
            descripcion,
            anio_publicacion,
            min_jugadores,
            max_jugadores,
            min_jugadores_recomendados,
            max_jugadores_recomendados,
            min_mejor_num_jugadores,
            max_mejor_num_jugadores,
            duracion_minima,
            duracion_maxima,
            edad_minima,
            valoracion_media,
            complejidad,
            imagen_url
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

        ON CONFLICT(id_bgg) DO UPDATE SET
            nombre = excluded.nombre,
            descripcion = excluded.descripcion,
            anio_publicacion = excluded.anio_publicacion,
            min_jugadores = excluded.min_jugadores,
            max_jugadores = excluded.max_jugadores,
            min_jugadores_recomendados =
                excluded.min_jugadores_recomendados,
            max_jugadores_recomendados =
                excluded.max_jugadores_recomendados,
            min_mejor_num_jugadores =
                excluded.min_mejor_num_jugadores,
            max_mejor_num_jugadores =
                excluded.max_mejor_num_jugadores,
            duracion_minima = excluded.duracion_minima,
            duracion_maxima = excluded.duracion_maxima,
            edad_minima = excluded.edad_minima,
            valoracion_media = excluded.valoracion_media,
            complejidad = excluded.complejidad,
            imagen_url = excluded.imagen_url
    """, (
        juego["id_bgg"],
        juego["nombre"],
        juego["descripcion"],
        juego["anio_publicacion"],
        juego["min_jugadores"],
        juego["max_jugadores"],
        juego["min_jugadores_recomendados"],
        juego["max_jugadores_recomendados"],
        juego["min_mejor_num_jugadores"],
        juego["max_mejor_num_jugadores"],
        juego["duracion_minima"],
        juego["duracion_maxima"],
        juego["edad_minima"],
        juego["valoracion_media"],
        juego["complejidad"],
        juego["imagen_url"]
    ))

    cursor.execute(
        "DELETE FROM juego_categoria WHERE juego_id = ?",
        (juego["id_bgg"],)
    )

    cursor.execute(
        "DELETE FROM juego_mecanica WHERE juego_id = ?",
        (juego["id_bgg"],)
    )

    for categoria in juego["categorias"]:
        categoria_id = obtener_o_crear_id(cursor, "categorias", categoria)

        cursor.execute("""
            INSERT OR IGNORE INTO juego_categoria (juego_id, categoria_id)
            VALUES (?, ?)
        """, (
            juego["id_bgg"],
            categoria_id
        ))

    for mecanica in juego["mecanicas"]:
        mecanica_id = obtener_o_crear_id(cursor, "mecanicas", mecanica)

        cursor.execute("""
            INSERT OR IGNORE INTO juego_mecanica (juego_id, mecanica_id)
            VALUES (?, ?)
        """, (
            juego["id_bgg"],
            mecanica_id
        ))

    conexion.commit()
    conexion.close()


def obtener_juegos():
    conexion = crear_conexion()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT 
            id_bgg,
            nombre,
            anio_publicacion,
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

    return juegos

def obtener_detalle_juego(id_bgg):
    conexion = crear_conexion()
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT
            id_bgg,
            nombre,
            descripcion,
            anio_publicacion,
            min_jugadores,
            max_jugadores,
            min_jugadores_recomendados,
            max_jugadores_recomendados,
            min_mejor_num_jugadores,
            max_mejor_num_jugadores,
            duracion_minima,
            duracion_maxima,
            edad_minima,
            valoracion_media,
            complejidad,
            imagen_url
        FROM juegos
        WHERE id_bgg = ?
    """, (id_bgg,))

    fila = cursor.fetchone()

    if fila is None:
        conexion.close()
        return None

    juego = dict(fila)

    cursor.execute("""
        SELECT c.nombre
        FROM categorias c
        JOIN juego_categoria jc
            ON c.id = jc.categoria_id
        WHERE jc.juego_id = ?
        ORDER BY c.nombre
    """, (id_bgg,))

    juego["categorias"] = [
        resultado[0]
        for resultado in cursor.fetchall()
    ]

    cursor.execute("""
        SELECT m.nombre
        FROM mecanicas m
        JOIN juego_mecanica jm
            ON m.id = jm.mecanica_id
        WHERE jm.juego_id = ?
        ORDER BY m.nombre
    """, (id_bgg,))

    juego["mecanicas"] = [
        resultado[0]
        for resultado in cursor.fetchall()
    ]

    conexion.close()

    return juego

def buscar_juegos_por_nombre(
    texto_busqueda,
    limite=30,
    usuario_id=None,
    solo_ludoteca=False
):
    conexion = crear_conexion()
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    texto = f"%{texto_busqueda.strip().lower()}%"

    consulta = """
        SELECT
            j.id_bgg,
            j.nombre,
            j.anio_publicacion,
            j.min_jugadores,
            j.max_jugadores,
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
        WHERE LOWER(j.nombre) LIKE ?
    """

    parametros.append(texto)

    if solo_ludoteca:
        consulta += """
          AND lu.usuario_id = ?
        """

        parametros.append(usuario_id)

    consulta += """
        ORDER BY
            CASE
                WHEN LOWER(j.nombre) = LOWER(?) THEN 0
                WHEN LOWER(j.nombre) LIKE LOWER(?) THEN 1
                ELSE 2
            END,
            j.valoracion_media DESC,
            LOWER(j.nombre) ASC
        LIMIT ?
    """

    parametros.extend([
        texto_busqueda.strip(),
        f"{texto_busqueda.strip()}%",
        limite
    ])

    cursor.execute(consulta, parametros)

    juegos = [
        dict(fila)
        for fila in cursor.fetchall()
    ]

    conexion.close()

    return juegos