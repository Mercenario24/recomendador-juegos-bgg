import re
import sqlite3

from pwdlib import PasswordHash

from app.database.base_datos import crear_conexion


GESTOR_CONTRASENAS = PasswordHash.recommended()

PATRON_EMAIL = re.compile(
    r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
)


def crear_tabla_usuarios():
    conexion = crear_conexion()
    cursor = conexion.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            contrasena_hash TEXT NOT NULL,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            es_admin INTEGER NOT NULL DEFAULT 0,
            activo INTEGER NOT NULL DEFAULT 1
        )
    """)

    conexion.commit()
    conexion.close()

def asegurar_columnas_usuarios():
    conexion = crear_conexion()
    cursor = conexion.cursor()

    cursor.execute("PRAGMA table_info(usuarios)")

    columnas = [
        fila[1]
        for fila in cursor.fetchall()
    ]

    if "es_admin" not in columnas:
        cursor.execute("""
            ALTER TABLE usuarios
            ADD COLUMN es_admin INTEGER NOT NULL DEFAULT 0
        """)

    if "activo" not in columnas:
        cursor.execute("""
            ALTER TABLE usuarios
            ADD COLUMN activo INTEGER NOT NULL DEFAULT 1
        """)

    conexion.commit()
    conexion.close()

def normalizar_email(email):
    return email.strip().lower()


def validar_datos_registro(
    nombre,
    email,
    contrasena,
    confirmacion_contrasena
):
    nombre = nombre.strip()
    email = normalizar_email(email)

    if len(nombre) < 2:
        raise ValueError(
            "El nombre debe tener al menos 2 caracteres."
        )

    if len(nombre) > 80:
        raise ValueError(
            "El nombre no puede superar los 80 caracteres."
        )

    if not PATRON_EMAIL.match(email):
        raise ValueError(
            "Introduce una dirección de correo válida."
        )

    if len(contrasena) < 8:
        raise ValueError(
            "La contraseña debe tener al menos 8 caracteres."
        )

    if len(contrasena) > 128:
        raise ValueError(
            "La contraseña no puede superar los 128 caracteres."
        )

    if contrasena != confirmacion_contrasena:
        raise ValueError(
            "Las contraseñas no coinciden."
        )

    return nombre, email


def registrar_usuario(
    nombre,
    email,
    contrasena,
    confirmacion_contrasena
):
    nombre, email = validar_datos_registro(
        nombre=nombre,
        email=email,
        contrasena=contrasena,
        confirmacion_contrasena=confirmacion_contrasena
    )

    contrasena_hash = GESTOR_CONTRASENAS.hash(
        contrasena
    )

    conexion = crear_conexion()
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    try:
        cursor.execute("""
            INSERT INTO usuarios (
                nombre,
                email,
                contrasena_hash
            )
            VALUES (?, ?, ?)
        """, (
            nombre,
            email,
            contrasena_hash
        ))

        conexion.commit()

        usuario_id = cursor.lastrowid

        cursor.execute("""
            SELECT
                id,
                nombre,
                email,
                fecha_registro,
                es_admin,
                activo
            FROM usuarios
            WHERE id = ?
        """, (usuario_id,))

        usuario = cursor.fetchone()

        return dict(usuario)

    except sqlite3.IntegrityError as error:
        raise ValueError(
            "Ya existe una cuenta registrada con ese correo."
        ) from error

    finally:
        conexion.close()


def obtener_usuario_por_email(email):
    email_normalizado = normalizar_email(email)

    conexion = crear_conexion()
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT
            id,
            nombre,
            email,
            contrasena_hash,
            fecha_registro,
            es_admin,
            activo
        FROM usuarios
        WHERE email = ?
    """, (email_normalizado,))

    usuario = cursor.fetchone()
    conexion.close()

    if usuario is None:
        return None

    return dict(usuario)


def obtener_usuario_por_id(usuario_id):
    conexion = crear_conexion()
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT
            id,
            nombre,
            email,
            fecha_registro,
            es_admin,
            activo
        FROM usuarios
        WHERE id = ?
    """, (usuario_id,))

    usuario = cursor.fetchone()
    conexion.close()

    if usuario is None:
        return None

    return dict(usuario)


def autenticar_usuario(email, contrasena):
    usuario = obtener_usuario_por_email(email)

    if usuario is None:
        return None

    if not usuario["activo"]:
        return None

    try:
        contrasena_correcta = GESTOR_CONTRASENAS.verify(
            contrasena,
            usuario["contrasena_hash"]
        )
    except Exception:
        return None

    if not contrasena_correcta:
        return None

    return {
        "id": usuario["id"],
        "nombre": usuario["nombre"],
        "email": usuario["email"],
        "fecha_registro": usuario["fecha_registro"],
        "es_admin": usuario["es_admin"],
        "activo": usuario["activo"]
    }