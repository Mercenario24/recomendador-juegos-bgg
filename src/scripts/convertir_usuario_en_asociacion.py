import sys
from pathlib import Path

RUTA_SRC = Path(__file__).resolve().parents[1]

if str(RUTA_SRC) not in sys.path:
    sys.path.insert(0, str(RUTA_SRC))

from app.auth.usuarios import (
    asegurar_columnas_usuarios,
    convertir_usuario_en_asociacion
)


def main():
    if len(sys.argv) < 2:
        print("Uso:")
        print("python src/scripts/convertir_usuario_en_asociacion.py email@ejemplo.com")
        return

    email = sys.argv[1].strip()

    asegurar_columnas_usuarios()

    actualizado = convertir_usuario_en_asociacion(email)

    if actualizado:
        print(f"Usuario convertido en asociación: {email}")
    else:
        print(f"No se encontró ningún usuario con email: {email}")


if __name__ == "__main__":
    main()