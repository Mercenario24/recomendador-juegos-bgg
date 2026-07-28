import sys
from pathlib import Path

RUTA_SRC = Path(__file__).resolve().parents[1]

if str(RUTA_SRC) not in sys.path:
    sys.path.insert(0, str(RUTA_SRC))

from app.auth.usuarios import (
    asegurar_columnas_usuarios,
    convertir_asociacion_en_usuario
)


def main():
    if len(sys.argv) < 2:
        print("Uso:")
        print("python src/scripts/convertir_asociacion_en_usuario.py email@ejemplo.com")
        return

    email = sys.argv[1].strip()

    asegurar_columnas_usuarios()

    actualizado = convertir_asociacion_en_usuario(email)

    if actualizado:
        print(f"Asociación convertida en usuario: {email}")
    else:
        print(f"No se encontró ninguna asociación con email: {email}")


if __name__ == "__main__":
    main()