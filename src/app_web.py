from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import FastAPI, HTTPException, Request

from opciones_formulario import (
    obtener_categorias_populares,
    obtener_mecanicas_populares
)

from recomendador_basico import recomendar_juegos

from base_datos import obtener_detalle_juego


RUTA_RAIZ = Path(__file__).resolve().parent.parent
RUTA_PLANTILLAS = RUTA_RAIZ / "web" / "templates"
RUTA_STATIC = RUTA_RAIZ / "web" / "static"


app = FastAPI(
    title="Recomendador de juegos de mesa",
    description="Recomendador local basado en datos de BoardGameGeek"
)

app.mount(
    "/static",
    StaticFiles(directory=str(RUTA_STATIC)),
    name="static"
)

plantillas = Jinja2Templates(
    directory=str(RUTA_PLANTILLAS)
)


def obtener_opciones():
    mecanicas = obtener_mecanicas_populares(limite=25)
    categorias = obtener_categorias_populares(limite=25)

    return mecanicas, categorias


def obtener_valores_iniciales():
    return {
        "num_jugadores": 4,
        "duracion_maxima": 120,
        "complejidad_maxima": 3.5,
        "solo_rango_recomendado": False,
        "mecanicas_seleccionadas": [],
        "categorias_seleccionadas": []
    }


def crear_contexto(
    request,
    valores=None,
    juegos=None,
    error=None,
    formulario_enviado=False
):
    mecanicas, categorias = obtener_opciones()

    return {
        "request": request,
        "mecanicas": mecanicas,
        "categorias": categorias,
        "valores": valores or obtener_valores_iniciales(),
        "juegos": juegos or [],
        "error": error,
        "formulario_enviado": formulario_enviado
    }


def convertir_entero(
    valor,
    nombre_campo,
    minimo=None,
    maximo=None
):
    try:
        numero = int(valor)
    except (TypeError, ValueError):
        raise ValueError(
            f"El campo '{nombre_campo}' debe ser un número entero."
        )

    if minimo is not None and numero < minimo:
        raise ValueError(
            f"El campo '{nombre_campo}' debe ser como mínimo {minimo}."
        )

    if maximo is not None and numero > maximo:
        raise ValueError(
            f"El campo '{nombre_campo}' debe ser como máximo {maximo}."
        )

    return numero


def convertir_decimal(
    valor,
    nombre_campo,
    minimo=None,
    maximo=None
):
    try:
        numero = float(str(valor).replace(",", "."))
    except (TypeError, ValueError):
        raise ValueError(
            f"El campo '{nombre_campo}' debe ser un número."
        )

    if minimo is not None and numero < minimo:
        raise ValueError(
            f"El campo '{nombre_campo}' debe ser como mínimo {minimo}."
        )

    if maximo is not None and numero > maximo:
        raise ValueError(
            f"El campo '{nombre_campo}' debe ser como máximo {maximo}."
        )

    return numero


def filtrar_opciones_validas(
    opciones_seleccionadas,
    opciones_disponibles
):
    nombres_validos = {
        nombre.lower()
        for nombre, _ in opciones_disponibles
    }

    return [
        opcion.strip().lower()
        for opcion in opciones_seleccionadas
        if opcion.strip().lower() in nombres_validos
    ]


@app.get("/", response_class=HTMLResponse)
async def mostrar_inicio(request: Request):
    contexto = crear_contexto(request)

    return plantillas.TemplateResponse(
        request=request,
        name="index.html",
        context=contexto
    )


@app.post("/recomendar", response_class=HTMLResponse)
async def procesar_recomendacion(request: Request):
    formulario = await request.form()

    mecanicas_disponibles, categorias_disponibles = obtener_opciones()

    mecanicas_seleccionadas = filtrar_opciones_validas(
        formulario.getlist("mecanicas"),
        mecanicas_disponibles
    )

    categorias_seleccionadas = filtrar_opciones_validas(
        formulario.getlist("categorias"),
        categorias_disponibles
    )

    valores = {
        "num_jugadores": formulario.get("num_jugadores", "4"),
        "duracion_maxima": formulario.get("duracion_maxima", "120"),
        "complejidad_maxima": formulario.get(
            "complejidad_maxima",
            "3.5"
        ),
        "solo_rango_recomendado":
            formulario.get("solo_rango_recomendado") == "on",
        "mecanicas_seleccionadas": mecanicas_seleccionadas,
        "categorias_seleccionadas": categorias_seleccionadas
    }

    try:
        num_jugadores = convertir_entero(
            valores["num_jugadores"],
            "Número de jugadores",
            minimo=1,
            maximo=20
        )

        duracion_maxima = convertir_entero(
            valores["duracion_maxima"],
            "Duración máxima",
            minimo=5,
            maximo=600
        )

        complejidad_maxima = convertir_decimal(
            valores["complejidad_maxima"],
            "Complejidad máxima",
            minimo=1.0,
            maximo=5.0
        )

        valores["num_jugadores"] = num_jugadores
        valores["duracion_maxima"] = duracion_maxima
        valores["complejidad_maxima"] = complejidad_maxima

        juegos = recomendar_juegos(
            num_jugadores=num_jugadores,
            duracion_maxima=duracion_maxima,
            complejidad_maxima=complejidad_maxima,
            mecanicas_preferidas=mecanicas_seleccionadas,
            categorias_preferidas=categorias_seleccionadas,
            solo_rango_recomendado=valores[
                "solo_rango_recomendado"
            ],
            limite=12
        )

        contexto = crear_contexto(
            request=request,
            valores=valores,
            juegos=juegos,
            formulario_enviado=True
        )

    except ValueError as error:
        contexto = crear_contexto(
            request=request,
            valores=valores,
            error=str(error),
            formulario_enviado=True
        )

    except Exception as error:
        print(f"Error interno al recomendar juegos: {error}")

        contexto = crear_contexto(
            request=request,
            valores=valores,
            error=(
                "Se ha producido un error al consultar los juegos. "
                "Revisa la consola del servidor."
            ),
            formulario_enviado=True
        )

    return plantillas.TemplateResponse(
        request=request,
        name="index.html",
        context=contexto
    )

@app.get(
    "/juego/{id_bgg}",
    response_class=HTMLResponse
)
async def mostrar_detalle_juego(
    request: Request,
    id_bgg: int
):
    juego = obtener_detalle_juego(id_bgg)

    if juego is None:
        raise HTTPException(
            status_code=404,
            detail="El juego solicitado no existe."
        )

    return plantillas.TemplateResponse(
        request=request,
        name="detalle_juego.html",
        context={
            "request": request,
            "juego": juego
        }
    )