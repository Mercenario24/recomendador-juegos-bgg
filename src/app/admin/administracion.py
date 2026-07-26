import re

from urllib.parse import urlparse

from app.database.base_datos import crear_conexion


def asegurar_columna(conexion, tabla, columna, definicion):
    cursor = conexion.cursor()

    cursor.execute(f"PRAGMA table_info({tabla})")
    columnas = [
        fila[1]
        for fila in cursor.fetchall()
    ]

    if columna not in columnas:
        cursor.execute(
            f"ALTER TABLE {tabla} ADD COLUMN {columna} {definicion}"
        )


def preparar_tablas_admin():
    conexion = crear_conexion()
    cursor = conexion.cursor()

    asegurar_columna(
        conexion,
        "usuarios",
        "es_admin",
        "INTEGER NOT NULL DEFAULT 0"
    )

    asegurar_columna(
        conexion,
        "usuarios",
        "activo",
        "INTEGER NOT NULL DEFAULT 1"
    )

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS videos_tiktok_juego (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            juego_id INTEGER NOT NULL,
            url TEXT NOT NULL,
            titulo TEXT,
            activo INTEGER NOT NULL DEFAULT 1,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (juego_id)
                REFERENCES juegos(id_bgg)
                ON DELETE CASCADE
        )
    """)

    conexion.commit()
    conexion.close()


def obtener_estadisticas_admin():
    conexion = crear_conexion()
    cursor = conexion.cursor()

    cursor.execute("SELECT COUNT(*) FROM usuarios")
    total_usuarios = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM usuarios
        WHERE activo = 1
    """)
    usuarios_activos = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM juegos")
    total_juegos = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM videos_tiktok_juego")
    total_videos = cursor.fetchone()[0]

    conexion.close()

    return {
        "total_usuarios": total_usuarios,
        "usuarios_activos": usuarios_activos,
        "total_juegos": total_juegos,
        "total_videos": total_videos
    }


def obtener_usuarios_admin():
    conexion = crear_conexion()
    conexion.row_factory = None
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT
            u.id,
            u.nombre,
            u.email,
            u.fecha_registro,
            u.es_admin,
            u.activo,
            COUNT(lu.juego_id) AS total_ludoteca
        FROM usuarios u
        LEFT JOIN ludoteca_usuario lu
            ON lu.usuario_id = u.id
        GROUP BY
            u.id,
            u.nombre,
            u.email,
            u.fecha_registro,
            u.es_admin,
            u.activo
        ORDER BY u.fecha_registro DESC
    """)

    usuarios = []

    for fila in cursor.fetchall():
        usuarios.append({
            "id": fila[0],
            "nombre": fila[1],
            "email": fila[2],
            "fecha_registro": fila[3],
            "es_admin": bool(fila[4]),
            "activo": bool(fila[5]),
            "total_ludoteca": fila[6]
        })

    conexion.close()

    return usuarios


def cambiar_usuario_admin(usuario_id, es_admin):
    conexion = crear_conexion()
    cursor = conexion.cursor()

    cursor.execute("""
        UPDATE usuarios
        SET es_admin = ?
        WHERE id = ?
    """, (
        int(es_admin),
        usuario_id
    ))

    conexion.commit()
    conexion.close()


def cambiar_usuario_activo(usuario_id, activo):
    conexion = crear_conexion()
    cursor = conexion.cursor()

    cursor.execute("""
        UPDATE usuarios
        SET activo = ?
        WHERE id = ?
    """, (
        int(activo),
        usuario_id
    ))

    conexion.commit()
    conexion.close()


def convertir_usuario_en_admin(email):
    conexion = crear_conexion()
    cursor = conexion.cursor()

    cursor.execute("""
        UPDATE usuarios
        SET es_admin = 1,
            activo = 1
        WHERE LOWER(email) = LOWER(?)
    """, (email,))

    filas_afectadas = cursor.rowcount

    conexion.commit()
    conexion.close()

    return filas_afectadas > 0


def buscar_juegos_admin(texto_busqueda, limite=40):
    conexion = crear_conexion()
    cursor = conexion.cursor()

    texto = f"%{texto_busqueda.strip().lower()}%"

    cursor.execute("""
        SELECT
            j.id_bgg,
            j.nombre,
            j.anio_publicacion,
            j.imagen_url,
            j.valoracion_media,
            COUNT(v.id) AS total_videos
        FROM juegos j
        LEFT JOIN videos_tiktok_juego v
            ON v.juego_id = j.id_bgg
        WHERE LOWER(j.nombre) LIKE ?
        GROUP BY
            j.id_bgg,
            j.nombre,
            j.anio_publicacion,
            j.imagen_url,
            j.valoracion_media
        ORDER BY
            CASE
                WHEN LOWER(j.nombre) = LOWER(?) THEN 0
                WHEN LOWER(j.nombre) LIKE LOWER(?) THEN 1
                ELSE 2
            END,
            j.valoracion_media DESC,
            LOWER(j.nombre) ASC
        LIMIT ?
    """, (
        texto,
        texto_busqueda.strip(),
        f"{texto_busqueda.strip()}%",
        limite
    ))

    juegos = []

    for fila in cursor.fetchall():
        juegos.append({
            "id_bgg": fila[0],
            "nombre": fila[1],
            "anio_publicacion": fila[2],
            "imagen_url": fila[3],
            "valoracion_media": fila[4],
            "total_videos": fila[5]
        })

    conexion.close()

    return juegos

def extraer_id_video_tiktok(url):
    texto = str(url or "").strip()

    coincidencia = re.search(
        r"/video/(\d+)",
        texto
    )

    if coincidencia:
        return coincidencia.group(1)

    return None

def validar_url_tiktok(url):
    texto = str(url or "").strip()

    if not texto:
        raise ValueError(
            "Debes introducir un enlace de TikTok."
        )

    url_parseada = urlparse(texto)

    if url_parseada.scheme not in {"http", "https"}:
        raise ValueError(
            "El enlace debe empezar por http:// o https://."
        )

    dominio = url_parseada.netloc.lower()

    dominios_validos = (
        "tiktok.com",
        "www.tiktok.com",
        "vm.tiktok.com",
        "vt.tiktok.com",
        "m.tiktok.com"
    )

    if not any(
        dominio == dominio_valido
        or dominio.endswith("." + dominio_valido)
        for dominio_valido in dominios_validos
    ):
        raise ValueError(
            "El enlace debe ser de TikTok."
        )

    return texto


def obtener_videos_tiktok_de_juego(juego_id):
    conexion = crear_conexion()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT
            id,
            juego_id,
            url,
            titulo,
            activo,
            fecha_creacion
        FROM videos_tiktok_juego
        WHERE juego_id = ?
        ORDER BY fecha_creacion DESC
    """, (juego_id,))

    videos = []

    for fila in cursor.fetchall():
        videos.append({
            "id": fila[0],
            "juego_id": fila[1],
            "url": fila[2],
            "titulo": fila[3],
            "activo": bool(fila[4]),
            "fecha_creacion": fila[5]
        })

    conexion.close()

    return videos


def obtener_videos_tiktok_publicos(juego_id):
    conexion = crear_conexion()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT
            id,
            url,
            titulo
        FROM videos_tiktok_juego
        WHERE juego_id = ?
          AND activo = 1
        ORDER BY fecha_creacion DESC
    """, (juego_id,))

    videos = []

    for fila in cursor.fetchall():
        videos.append({
            "id": fila[0],
            "url": fila[1],
            "titulo": fila[2],
            "video_id": extraer_id_video_tiktok(
                fila[1]
            )
        })

    conexion.close()

    return videos


def guardar_video_tiktok(juego_id, url, titulo=None, activo=True):
    url_validada = validar_url_tiktok(url)

    video_id = extraer_id_video_tiktok(
        url_validada
    )

    if video_id is None:
        raise ValueError(
            "No se ha podido obtener el ID del vídeo. "
            "Usa un enlace completo de TikTok, por ejemplo: "
            "https://www.tiktok.com/@usuario/video/123456789"
        )

    titulo_limpio = str(titulo or "").strip()

    if not titulo_limpio:
        titulo_limpio = None

    conexion = crear_conexion()
    cursor = conexion.cursor()

    cursor.execute("""
        INSERT INTO videos_tiktok_juego (
            juego_id,
            url,
            titulo,
            activo
        )
        VALUES (?, ?, ?, ?)
    """, (
        juego_id,
        url_validada,
        titulo_limpio,
        int(activo)
    ))

    conexion.commit()
    conexion.close()


def obtener_video_tiktok(video_id):
    conexion = crear_conexion()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT
            id,
            juego_id,
            url,
            titulo,
            activo
        FROM videos_tiktok_juego
        WHERE id = ?
    """, (video_id,))

    fila = cursor.fetchone()
    conexion.close()

    if fila is None:
        return None

    return {
        "id": fila[0],
        "juego_id": fila[1],
        "url": fila[2],
        "titulo": fila[3],
        "activo": bool(fila[4])
    }


def eliminar_video_tiktok(video_id):
    conexion = crear_conexion()
    cursor = conexion.cursor()

    cursor.execute("""
        DELETE FROM videos_tiktok_juego
        WHERE id = ?
    """, (video_id,))

    conexion.commit()
    conexion.close()

def eliminar_usuario(usuario_id):
    conexion = crear_conexion()
    cursor = conexion.cursor()

    cursor.execute("""
        DELETE FROM usuarios
        WHERE id = ?
    """, (usuario_id,))

    filas_afectadas = cursor.rowcount

    conexion.commit()
    conexion.close()

    return filas_afectadas > 0