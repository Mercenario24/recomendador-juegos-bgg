from bgg_api import obtener_juegos_por_ids
from parser_bgg import parsear_juegos
from base_datos import crear_tablas, guardar_juego, obtener_juegos


def main():
    crear_tablas()

    ids_juegos = [
        174430,  # Gloomhaven
        224517,  # Brass: Birmingham
        167791,  # Terraforming Mars
        68448,   # 7 Wonders
        30549    # Pandemic
    ]

    xml_texto = obtener_juegos_por_ids(ids_juegos)
    juegos = parsear_juegos(xml_texto)

    for juego in juegos:
        guardar_juego(juego)
        print(f"Guardado: {juego['nombre']}")

    print("\nJuegos en la base de datos:")
    for fila in obtener_juegos():
        print(fila)


if __name__ == "__main__":
    main()