import sqlite3

from base_datos import crear_conexion


def crear_tablas_ludoteca():
    conexion = crear_conexion()
    cursor = conexion.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ludoteca_usuario (
            usuario_id INTEGER NOT NULL,
            juego_id INTEGER NOT NULL,
            valoracion_usuario REAL,
            num_partidas INTEGER NOT NULL DEFAULT 0,
            fecha_importacion TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP,

            PRIMARY KEY (usuario_id, juego_id),

            FOREIGN KEY (usuario_id)
                REFERENCES usuarios(id)
                ON DELETE CASCADE,

            FOREIGN KEY (juego_id)
                REFERENCES juegos(id_bgg)
                ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS importaciones_ludoteca (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            nombre_archivo TEXT,
            juegos_detectados INTEGER DEFAULT 0,
            juegos_asociados INTEGER DEFAULT 0,
            juegos_nuevos INTEGER DEFAULT 0,
            juegos_no_disponibles INTEGER DEFAULT 0,
            reemplazo_completo INTEGER DEFAULT 0,
            fecha_importacion TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (usuario_id)
                REFERENCES usuarios(id)
                ON DELETE CASCADE
        )
    """)

    conexion.commit()
    conexion.close()


def dividir_en_lotes(lista, tamano=500):
    for indice in range(0, len(lista), tamano):
        yield lista[indice:indice + tamano]


def obtener_ids_juegos_existentes(ids_juegos):
    ids_unicos = sorted({
        int(id_juego)
        for id_juego in ids_juegos
    })

    if not ids_unicos:
        return set()

    conexion = crear_conexion()
    cursor = conexion.cursor()

    ids_existentes = set()

    for lote in dividir_en_lotes(
        ids_unicos,
        tamano=500
    ):
        marcadores = ",".join(
            "?"
            for _ in lote
        )

        cursor.execute(
            f"""
                SELECT id_bgg
                FROM juegos
                WHERE id_bgg IN ({marcadores})
            """,
            lote
        )

        ids_existentes.update(
            fila[0]
            for fila in cursor.fetchall()
        )

    conexion.close()

    return ids_existentes


def obtener_ids_juegos_inexistentes(ids_juegos):
    ids_solicitados = {
        int(id_juego)
        for id_juego in ids_juegos
    }

    ids_existentes = obtener_ids_juegos_existentes(
        ids_solicitados
    )

    return sorted(
        ids_solicitados - ids_existentes
    )


def guardar_ludoteca_usuario(
    usuario_id,
    juegos,
    reemplazar=False
):
    conexion = crear_conexion()
    cursor = conexion.cursor()

    try:
        if reemplazar:
            cursor.execute("""
                DELETE FROM ludoteca_usuario
                WHERE usuario_id = ?
            """, (usuario_id,))

        for juego in juegos:
            cursor.execute("""
                INSERT INTO ludoteca_usuario (
                    usuario_id,
                    juego_id,
                    valoracion_usuario,
                    num_partidas,
                    fecha_importacion
                )
                VALUES (
                    ?, ?, ?, ?, CURRENT_TIMESTAMP
                )

                ON CONFLICT(
                    usuario_id,
                    juego_id
                ) DO UPDATE SET
                    valoracion_usuario =
                        excluded.valoracion_usuario,
                    num_partidas =
                        excluded.num_partidas,
                    fecha_importacion =
                        CURRENT_TIMESTAMP
            """, (
                usuario_id,
                juego["id_bgg"],
                juego["valoracion_usuario"],
                juego["num_partidas"]
            ))

        conexion.commit()

    except Exception:
        conexion.rollback()
        raise

    finally:
        conexion.close()


def registrar_importacion(
    usuario_id,
    nombre_archivo,
    juegos_detectados,
    juegos_asociados,
    juegos_nuevos,
    juegos_no_disponibles,
    reemplazo_completo
):
    conexion = crear_conexion()
    cursor = conexion.cursor()

    cursor.execute("""
        INSERT INTO importaciones_ludoteca (
            usuario_id,
            nombre_archivo,
            juegos_detectados,
            juegos_asociados,
            juegos_nuevos,
            juegos_no_disponibles,
            reemplazo_completo
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        usuario_id,
        nombre_archivo,
        juegos_detectados,
        juegos_asociados,
        juegos_nuevos,
        juegos_no_disponibles,
        int(reemplazo_completo)
    ))

    conexion.commit()
    conexion.close()


def obtener_ludoteca_usuario(usuario_id):
    conexion = crear_conexion()
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    cursor.execute("""
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
            j.imagen_url,
            lu.valoracion_usuario,
            lu.num_partidas,
            lu.fecha_importacion
        FROM ludoteca_usuario lu
        JOIN juegos j
            ON j.id_bgg = lu.juego_id
        WHERE lu.usuario_id = ?
        ORDER BY LOWER(j.nombre)
    """, (usuario_id,))

    juegos = [
        dict(fila)
        for fila in cursor.fetchall()
    ]

    conexion.close()

    return juegos


def obtener_ultima_importacion(usuario_id):
    conexion = crear_conexion()
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT
            nombre_archivo,
            juegos_detectados,
            juegos_asociados,
            juegos_nuevos,
            juegos_no_disponibles,
            reemplazo_completo,
            fecha_importacion
        FROM importaciones_ludoteca
        WHERE usuario_id = ?
        ORDER BY id DESC
        LIMIT 1
    """, (usuario_id,))

    importacion = cursor.fetchone()
    conexion.close()

    if importacion is None:
        return None

    return dict(importacion)