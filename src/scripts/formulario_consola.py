from app.services.recomendador_basico import (
    recomendar_juegos,
    mostrar_recomendaciones,
    limpiar_lista_texto
)

import sys
from pathlib import Path


RUTA_SRC = Path(__file__).resolve().parents[1]

if str(RUTA_SRC) not in sys.path:
    sys.path.insert(0, str(RUTA_SRC))


def pedir_entero(mensaje, minimo=None, maximo=None):
    while True:
        valor = input(mensaje).strip()

        try:
            numero = int(valor)
        except ValueError:
            print("Introduce un número entero válido.")
            continue

        if minimo is not None and numero < minimo:
            print(
                f"El número debe ser mayor o igual que {minimo}."
            )
            continue

        if maximo is not None and numero > maximo:
            print(
                f"El número debe ser menor o igual que {maximo}."
            )
            continue

        return numero


def pedir_float(mensaje, minimo=None, maximo=None):
    while True:
        valor = input(mensaje).strip()

        try:
            numero = float(valor.replace(",", "."))
        except ValueError:
            print("Introduce un número válido.")
            continue

        if minimo is not None and numero < minimo:
            print(
                f"El número debe ser mayor o igual que {minimo}."
            )
            continue

        if maximo is not None and numero > maximo:
            print(
                f"El número debe ser menor o igual que {maximo}."
            )
            continue

        return numero


def pedir_si_no(mensaje, valor_defecto=False):
    while True:
        respuesta = input(mensaje).strip().lower()

        if respuesta == "":
            return valor_defecto

        if respuesta in ["s", "si", "sí"]:
            return True

        if respuesta in ["n", "no"]:
            return False

        print("Responde con 's' o 'n'.")


def explicar_complejidad():
    print("\nComplejidad aproximada:")
    print("1.0 - 1.5 → Muy fácil")
    print("1.5 - 2.5 → Familiar o ligero")
    print("2.5 - 3.5 → Dificultad media")
    print("3.5 - 4.5 → Complejo")
    print("4.5 - 5.0 → Muy complejo")


def mostrar_preferencias(
    num_jugadores,
    duracion_maxima,
    complejidad_maxima,
    mecanicas_preferidas,
    categorias_preferidas,
    solo_rango_recomendado
):
    print("\n========================================")
    print(" Preferencias seleccionadas")
    print("========================================")
    print(f"Jugadores: {num_jugadores}")
    print(f"Duración máxima: {duracion_maxima} minutos")
    print(f"Complejidad máxima: {complejidad_maxima}")

    if solo_rango_recomendado:
        print("Número de jugadores: debe estar recomendado")
    else:
        print("Número de jugadores: basta con estar admitido")

    if mecanicas_preferidas:
        print(
            "Mecánicas: "
            f"{', '.join(mecanicas_preferidas)}"
        )
    else:
        print("Mecánicas: sin preferencia")

    if categorias_preferidas:
        print(
            "Categorías: "
            f"{', '.join(categorias_preferidas)}"
        )
    else:
        print("Categorías: sin preferencia")


def main():
    print("========================================")
    print("  Recomendador de juegos de mesa")
    print("========================================")

    num_jugadores = pedir_entero(
        "\n¿Cuántos jugadores sois? ",
        minimo=1,
        maximo=20
    )

    solo_rango_recomendado = pedir_si_no(
        "¿Quieres mostrar solo juegos recomendados "
        "para ese número de jugadores? [s/N]: ",
        valor_defecto=False
    )

    duracion_maxima = pedir_entero(
        "\n¿Cuántos minutos puede durar como máximo? ",
        minimo=5,
        maximo=600
    )

    explicar_complejidad()

    complejidad_maxima = pedir_float(
        "\n¿Qué complejidad máxima quieres? ",
        minimo=1.0,
        maximo=5.0
    )

    mecanicas_disponibles = obtener_mecanicas_populares(
        limite=25
    )

    mecanicas_preferidas = seleccionar_opciones(
        "Mecánicas más frecuentes",
        mecanicas_disponibles
    )

    categorias_disponibles = obtener_categorias_populares(
        limite=25
    )

    categorias_preferidas = seleccionar_opciones(
        "Categorías más frecuentes",
        categorias_disponibles
    )

    mostrar_preferencias(
        num_jugadores=num_jugadores,
        duracion_maxima=duracion_maxima,
        complejidad_maxima=complejidad_maxima,
        mecanicas_preferidas=mecanicas_preferidas,
        categorias_preferidas=categorias_preferidas,
        solo_rango_recomendado=solo_rango_recomendado
    )

    juegos = recomendar_juegos(
        num_jugadores=num_jugadores,
        duracion_maxima=duracion_maxima,
        complejidad_maxima=complejidad_maxima,
        mecanicas_preferidas=mecanicas_preferidas,
        categorias_preferidas=categorias_preferidas,
        solo_rango_recomendado=solo_rango_recomendado,
        limite=10
    )

    mostrar_recomendaciones(juegos)


if __name__ == "__main__":
    main()