import sqlite3

from app.database.base_datos import crear_conexion


TIPOS_MENSAJE_VALIDOS = {
    "soporte",
    "mejora",
    "error",
    "otro"
}

ESTADOS_SOPORTE_VALIDOS = {
    "pendiente",
    "en_revision",
    "resuelto",
    "descartado"
}

def crear_tabla_mensajes_soporte():
    conexion = crear_conexion()
    cursor = conexion.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mensajes_soporte (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            nombre TEXT NOT NULL,
            email TEXT NOT NULL,
            tipo TEXT NOT NULL,
            asunto TEXT NOT NULL,
            mensaje TEXT NOT NULL,
            estado TEXT NOT NULL DEFAULT 'pendiente',
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (usuario_id)
                REFERENCES usuarios(id)
                ON DELETE SET NULL
        )
    """)

    conexion.commit()
    conexion.close()


def validar_mensaje_soporte(
    nombre,
    email,
    tipo,
    asunto,
    mensaje
):
    nombre = str(nombre or "").strip()
    email = str(email or "").strip().lower()
    tipo = str(tipo or "").strip().lower()
    asunto = str(asunto or "").strip()
    mensaje = str(mensaje or "").strip()

    if len(nombre) < 2:
        raise ValueError(
            "El nombre debe tener al menos 2 caracteres."
        )

    if "@" not in email or "." not in email:
        raise ValueError(
            "Introduce un correo válido."
        )

    if tipo not in TIPOS_MENSAJE_VALIDOS:
        raise ValueError(
            "El tipo de mensaje no es válido."
        )

    if len(asunto) < 4:
        raise ValueError(
            "El asunto debe tener al menos 4 caracteres."
        )

    if len(asunto) > 120:
        raise ValueError(
            "El asunto no puede superar los 120 caracteres."
        )

    if len(mensaje) < 10:
        raise ValueError(
            "El mensaje debe tener al menos 10 caracteres."
        )

    if len(mensaje) > 3000:
        raise ValueError(
            "El mensaje no puede superar los 3000 caracteres."
        )

    return {
        "nombre": nombre,
        "email": email,
        "tipo": tipo,
        "asunto": asunto,
        "mensaje": mensaje
    }


def guardar_mensaje_soporte(
    usuario_id,
    nombre,
    email,
    tipo,
    asunto,
    mensaje
):
    datos = validar_mensaje_soporte(
        nombre=nombre,
        email=email,
        tipo=tipo,
        asunto=asunto,
        mensaje=mensaje
    )

    conexion = crear_conexion()
    cursor = conexion.cursor()

    cursor.execute("""
        INSERT INTO mensajes_soporte (
            usuario_id,
            nombre,
            email,
            tipo,
            asunto,
            mensaje
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        usuario_id,
        datos["nombre"],
        datos["email"],
        datos["tipo"],
        datos["asunto"],
        datos["mensaje"]
    ))

    conexion.commit()
    conexion.close()


def obtener_mensajes_soporte():
    conexion = crear_conexion()
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT
            ms.id,
            ms.usuario_id,
            ms.nombre,
            ms.email,
            ms.tipo,
            ms.asunto,
            ms.mensaje,
            ms.estado,
            ms.fecha_creacion,
            u.nombre AS nombre_usuario
        FROM mensajes_soporte ms
        LEFT JOIN usuarios u
            ON u.id = ms.usuario_id
        ORDER BY ms.fecha_creacion DESC
    """)

    mensajes = [
        dict(fila)
        for fila in cursor.fetchall()
    ]

    conexion.close()

    return mensajes

def cambiar_estado_mensaje_soporte(mensaje_id, estado):
    estado = str(estado or "").strip().lower()

    if estado not in ESTADOS_SOPORTE_VALIDOS:
        raise ValueError("El estado seleccionado no es válido.")

    conexion = crear_conexion()
    cursor = conexion.cursor()

    cursor.execute("""
        UPDATE mensajes_soporte
        SET estado = ?
        WHERE id = ?
    """, (
        estado,
        mensaje_id
    ))

    filas_afectadas = cursor.rowcount

    conexion.commit()
    conexion.close()

    return filas_afectadas > 0