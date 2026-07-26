import sys
from pathlib import Path


RUTA_SRC = Path(__file__).resolve().parents[1]

if str(RUTA_SRC) not in sys.path:
    sys.path.insert(0, str(RUTA_SRC))


from app.admin.administracion import (
    convertir_usuario_en_admin,
    preparar_tablas_admin
)
from app.auth.usuarios import crear_tabla_usuarios


def main():
    crear_tabla_usuarios()
    preparar_tablas_admin()

    email = input("Email del usuario que será admin: ").strip()

    if not email:
        print("Debes introducir un email.")
        return

    convertido = convertir_usuario_en_admin(email)

    if convertido:
        print(f"Usuario {email} convertido en administrador.")
    else:
        print(
            "No existe ningún usuario con ese email. "
            "Crea primero la cuenta desde la web y vuelve a ejecutar este script."
        )


if __name__ == "__main__":
    main()