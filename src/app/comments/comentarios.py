import sqlite3

from app.database.base_datos import crear_conexion


def crear_tabla_comentarios_juego():
    conexion = crear_conexion()
    cursor = conexion.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS comentarios_juego (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            juego_id INTEGER NOT NULL,
            usuario_id INTEGER NOT NULL,
            comentario TEXT NOT NULL,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            fecha_actualizacion TIMESTAMP,
            FOREIGN KEY (juego_id) REFERENCES juegos(id_bgg),
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
    """)

    conexion.commit()
    conexion.close()


def obtener_comentarios_juego(juego_id, limite=50):
    conexion = crear_conexion()
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT
            cj.id,
            cj.juego_id,
            cj.usuario_id,
            cj.comentario,
            cj.fecha_creacion,
            cj.fecha_actualizacion,
            u.nombre AS nombre_usuario
        FROM comentarios_juego cj
        JOIN usuarios u
            ON cj.usuario_id = u.id
        WHERE cj.juego_id = ?
        ORDER BY cj.fecha_creacion DESC
        LIMIT ?
    """, (
        juego_id,
        limite
    ))

    comentarios = [
        dict(fila)
        for fila in cursor.fetchall()
    ]

    conexion.close()

    return comentarios


def crear_comentario_juego(usuario_id, juego_id, comentario):
    comentario = str(comentario or "").strip()

    if not comentario:
        raise ValueError("El comentario no puede estar vacío.")

    if len(comentario) > 1000:
        raise ValueError("El comentario no puede superar los 1000 caracteres.")

    conexion = crear_conexion()
    cursor = conexion.cursor()

    cursor.execute("""
        INSERT INTO comentarios_juego (
            juego_id,
            usuario_id,
            comentario
        )
        VALUES (?, ?, ?)
    """, (
        juego_id,
        usuario_id,
        comentario
    ))

    conexion.commit()
    conexion.close()


def eliminar_comentario_juego(comentario_id, usuario_id, es_admin=False):
    conexion = crear_conexion()
    cursor = conexion.cursor()

    if es_admin:
        cursor.execute("""
            DELETE FROM comentarios_juego
            WHERE id = ?
        """, (
            comentario_id,
        ))
    else:
        cursor.execute("""
            DELETE FROM comentarios_juego
            WHERE id = ?
              AND usuario_id = ?
        """, (
            comentario_id,
            usuario_id
        ))

    eliminado = cursor.rowcount > 0

    conexion.commit()
    conexion.close()

    return eliminado