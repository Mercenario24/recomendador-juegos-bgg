import sqlite3
from pathlib import Path


RUTA_BD = Path("datos/juegos.db")


def crear_conexion():
    RUTA_BD.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(RUTA_BD)


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
        INSERT OR REPLACE INTO juegos (
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