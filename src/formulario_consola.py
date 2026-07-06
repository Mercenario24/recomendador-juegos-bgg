from recomendador_basico import recomendar_juegos, mostrar_recomendaciones


def pedir_entero(mensaje, minimo=None, maximo=None):
    while True:
        valor = input(mensaje)

        try:
            numero = int(valor)
        except ValueError:
            print("Introduce un número válido.")
            continue

        if minimo is not None and numero < minimo:
            print(f"El número debe ser mayor o igual que {minimo}.")
            continue

        if maximo is not None and numero > maximo:
            print(f"El número debe ser menor o igual que {maximo}.")
            continue

        return numero


def pedir_float(mensaje, minimo=None, maximo=None):
    while True:
        valor = input(mensaje)

        try:
            numero = float(valor.replace(",", "."))
        except ValueError:
            print("Introduce un número válido.")
            continue

        if minimo is not None and numero < minimo:
            print(f"El número debe ser mayor o igual que {minimo}.")
            continue

        if maximo is not None and numero > maximo:
            print(f"El número debe ser menor o igual que {maximo}.")
            continue

        return numero


def pedir_texto_opcional(mensaje):
    valor = input(mensaje).strip()

    if valor == "":
        return None

    return valor


def explicar_complejidad():
    print("\nComplejidad aproximada:")
    print("1.0 - 1.5  → Muy fácil")
    print("1.5 - 2.5  → Familiar / ligero")
    print("2.5 - 3.5  → Medio")
    print("3.5 - 4.5  → Complejo")
    print("4.5 - 5.0  → Muy complejo")


def main():
    print("======================================")
    print(" Recomendador básico de juegos de mesa ")
    print("======================================")

    num_jugadores = pedir_entero(
        "\n¿Cuántos jugadores sois? ",
        minimo=1,
        maximo=20
    )

    duracion_maxima = pedir_entero(
        "¿Duración máxima en minutos? ",
        minimo=5,
        maximo=600
    )

    explicar_complejidad()

    complejidad_maxima = pedir_float(
        "\n¿Qué complejidad máxima quieres? ",
        minimo=1.0,
        maximo=5.0
    )

    print("\nPuedes escribir parte de una mecánica.")
    print("Ejemplos: deck, draft, worker, dice, tile, hand, cooperative")
    print("Si no quieres filtrar por mecánica, pulsa Enter.")

    mecanica_preferida = pedir_texto_opcional(
        "\n¿Qué mecánica te gustaría? "
    )

    print("\nPuedes escribir parte de una categoría o temática.")
    print("Ejemplos: fantasy, science, economic, civilization, adventure, fighting")
    print("Si no quieres filtrar por categoría, pulsa Enter.")

    categoria_preferida = pedir_texto_opcional(
        "\n¿Qué temática/categoría te gustaría? "
    )

    juegos = recomendar_juegos(
        num_jugadores=num_jugadores,
        duracion_maxima=duracion_maxima,
        complejidad_maxima=complejidad_maxima,
        mecanica_preferida=mecanica_preferida,
        categoria_preferida=categoria_preferida,
        limite=10
    )

    mostrar_recomendaciones(juegos)


if __name__ == "__main__":
    main()