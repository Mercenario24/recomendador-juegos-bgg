import csv
from pathlib import Path

import sys
from pathlib import Path


RUTA_SRC = Path(__file__).resolve().parents[1]

if str(RUTA_SRC) not in sys.path:
    sys.path.insert(0, str(RUTA_SRC))


RUTA_RANKING = Path("datos/bgg_ranking.csv")
RUTA_SALIDA = Path("datos/ids_juegos.csv")
LIMITE_JUEGOS = 1000
MINIMO_VOTOS = 100


def obtener_valor(fila, posibles_nombres):
    for nombre in posibles_nombres:
        if nombre in fila and fila[nombre]:
            return fila[nombre]

    return None


def main():
    juegos = []

    with open(RUTA_RANKING, "r", encoding="utf-8") as archivo:
        lector = csv.DictReader(archivo)

        for fila in lector:
            id_bgg = obtener_valor(fila, ["id", "objectid", "id_bgg"])
            nombre = obtener_valor(fila, ["name", "nombre"])
            num_votos = obtener_valor(fila, ["usersrated", "num_votos"])

            if not id_bgg or not nombre:
                continue

            try:
                votos = int(float(num_votos)) if num_votos else 0
            except ValueError:
                votos = 0

            if votos < MINIMO_VOTOS:
                continue

            juegos.append({
                "id_bgg": int(id_bgg),
                "nombre": nombre
            })

            if len(juegos) >= LIMITE_JUEGOS:
                break

    RUTA_SALIDA.parent.mkdir(parents=True, exist_ok=True)

    with open(RUTA_SALIDA, "w", encoding="utf-8", newline="") as archivo:
        campos = ["id_bgg", "nombre"]
        escritor = csv.DictWriter(archivo, fieldnames=campos)

        escritor.writeheader()
        escritor.writerows(juegos)

    print(f"Archivo generado: {RUTA_SALIDA}")
    print(f"Juegos incluidos: {len(juegos)}")


if __name__ == "__main__":
    main()