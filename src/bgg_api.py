import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv


RUTA_ENV = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=RUTA_ENV)

URL_BASE = "https://boardgamegeek.com/xmlapi2/thing"


def obtener_juegos_por_ids(ids_juegos):
    token = os.getenv("BGG_TOKEN")

    if not token:
        raise ValueError(
            "No se ha encontrado BGG_TOKEN. "
            "Crea un archivo .env con BGG_TOKEN=TU_TOKEN_AQUI"
        )

    ids_como_texto = ",".join(str(id_juego) for id_juego in ids_juegos)

    parametros = {
        "id": ids_como_texto,
        "type": "boardgame",
        "stats": 1
    }

    cabeceras = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "recomendador-juegos-bgg/0.1"
    }

    for intento in range(3):
        respuesta = requests.get(
            URL_BASE,
            params=parametros,
            headers=cabeceras,
            timeout=30
        )

        if respuesta.status_code == 202:
            print("BGG está preparando la respuesta. Reintentando...")
            time.sleep(5)
            continue

        if respuesta.status_code == 401:
            raise PermissionError(
                "BGG ha devuelto 401 Unauthorized. "
                "El token no es válido, no está aprobado o no se está enviando correctamente."
            )

        respuesta.raise_for_status()
        return respuesta.text

    raise TimeoutError("No se pudo obtener respuesta definitiva de BGG.")