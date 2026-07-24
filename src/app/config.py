from pathlib import Path

from dotenv import load_dotenv


RUTA_RAIZ = Path(__file__).resolve().parents[2]

RUTA_ENV = RUTA_RAIZ / ".env"
RUTA_DATOS = RUTA_RAIZ / "datos"
RUTA_BD = RUTA_DATOS / "juegos.db"

RUTA_WEB = RUTA_RAIZ / "web"
RUTA_PLANTILLAS = RUTA_WEB / "templates"
RUTA_STATIC = RUTA_WEB / "static"

load_dotenv(RUTA_ENV)