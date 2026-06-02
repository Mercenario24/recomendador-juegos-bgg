import sqlite3
from pathlib import Path


RUTA_BD = Path("datos/juegos.db")


def crear_conexion():
    RUTA_BD.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(RUTA_BD)


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
            duracion_minima INTEGER,
            duracion_maxima INTEGER,
            edad_minima INTEGER,
            valoracion_media REAL,
            complejidad REAL,
            categorias TEXT,
            mecanicas TEXT,
            imagen_url TEXT
        )
    """)

    conexion.commit()
    conexion.close()


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
            duracion_minima,
            duracion_maxima,
            edad_minima,
            valoracion_media,
            complejidad,
            categorias,
            mecanicas,
            imagen_url
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        juego["id_bgg"],
        juego["nombre"],
        juego["descripcion"],
        juego["anio_publicacion"],
        juego["min_jugadores"],
        juego["max_jugadores"],
        juego["duracion_minima"],
        juego["duracion_maxima"],
        juego["edad_minima"],
        juego["valoracion_media"],
        juego["complejidad"],
        ", ".join(juego["categorias"]),
        ", ".join(juego["mecanicas"]),
        juego["imagen_url"]
    ))

    conexion.commit()
    conexion.close()


def obtener_juegos():
    conexion = crear_conexion()
    cursor = conexion.cursor()

    cursor.execute("SELECT * FROM juegos")
    juegos = cursor.fetchall()

    conexion.close()
    return juegos