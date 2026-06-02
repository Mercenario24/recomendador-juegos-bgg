import os
import time
import requests


URL_BASE = "https://boardgamegeek.com/xmlapi2/thing"


def obtener_juegos_por_ids(ids_juegos):
    token = os.getenv("BGG_TOKEN")

    if not token:
        raise ValueError(
            "No se ha encontrado el token de BGG. "
            "Crea la variable de entorno BGG_TOKEN."
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
            time.sleep(5)
            continue

        if respuesta.status_code == 401:
            raise PermissionError(
                "BGG ha devuelto 401 Unauthorized. "
                "Revisa que el token sea correcto, que tenga el formato Bearer TOKEN "
                "y que estés usando https://boardgamegeek.com sin www."
            )

        respuesta.raise_for_status()
        return respuesta.text

    raise TimeoutError("BGG sigue devolviendo 202 después de varios intentos.")