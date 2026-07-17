import os
import math
import time

from fastapi import (
    FastAPI,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile
)

from base_datos import (
    guardar_juego,
    obtener_detalle_juego
)
from bgg_api import obtener_juegos_por_ids
from importador_ludoteca import leer_archivo_ludoteca
from ludoteca import (
    crear_tablas_ludoteca,
    guardar_ludoteca_usuario,
    obtener_ids_juegos_existentes,
    obtener_ids_juegos_inexistentes,
    obtener_ludoteca_usuario,
    obtener_ultima_importacion,
    registrar_importacion
)
from parser_bgg import parsear_juegos

from dotenv import load_dotenv
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from opciones_formulario import (
    obtener_categorias_populares,
    obtener_mecanicas_populares
)

from usuarios import (
    autenticar_usuario,
    crear_tabla_usuarios,
    obtener_usuario_por_id,
    registrar_usuario
)

from recomendador_basico import recomendar_juegos



RUTA_RAIZ = Path(__file__).resolve().parent.parent
load_dotenv(RUTA_RAIZ / ".env")

CLAVE_SESION = os.getenv("SESSION_SECRET")

if not CLAVE_SESION:
    raise RuntimeError(
        "No se ha encontrado SESSION_SECRET en el archivo .env."
    )

RUTA_PLANTILLAS = RUTA_RAIZ / "web" / "templates"
RUTA_STATIC = RUTA_RAIZ / "web" / "static"


app = FastAPI(
    title="Recomendador de juegos de mesa",
    description="Recomendador local basado en datos de BoardGameGeek"
)

app.add_middleware(
        SessionMiddleware,
        secret_key=CLAVE_SESION,
        session_cookie="sesion_recomendador_bgg",
        max_age=60 * 60 * 24 * 30,
        same_site="lax",
        https_only=False
    )

crear_tabla_usuarios()

crear_tablas_ludoteca()

app.mount(
    "/static",
    StaticFiles(directory=str(RUTA_STATIC)),
    name="static"
)

plantillas = Jinja2Templates(
    directory=str(RUTA_PLANTILLAS)
)

@app.get(
    "/mi-ludoteca",
    response_class=HTMLResponse
)
async def mostrar_mi_ludoteca(
    request: Request
):
    usuario = obtener_usuario_actual(request)

    if usuario is None:
        return RedirectResponse(
            url="/iniciar-sesion",
            status_code=303
        )

    juegos = obtener_ludoteca_usuario(
        usuario["id"]
    )

    ultima_importacion = obtener_ultima_importacion(
        usuario["id"]
    )

    mensaje = request.session.pop(
        "mensaje_ludoteca",
        None
    )

    error = request.session.pop(
        "error_ludoteca",
        None
    )

    aviso = request.session.pop(
        "aviso_ludoteca",
        None
    )

    return plantillas.TemplateResponse(
        request=request,
        name="mi_ludoteca.html",
        context={
            "request": request,
            "usuario": usuario,
            "juegos": juegos,
            "total_juegos": len(juegos),
            "ultima_importacion": ultima_importacion,
            "mensaje": mensaje,
            "error": error,
            "aviso": aviso
        }
    )


@app.post("/mi-ludoteca/importar")
async def importar_mi_ludoteca(
    request: Request,
    archivo: UploadFile = File(...),
    reemplazar_ludoteca: bool = Form(False)
):
    usuario = obtener_usuario_actual(request)

    if usuario is None:
        return RedirectResponse(
            url="/iniciar-sesion",
            status_code=303
        )

    try:
        if not archivo.filename:
            raise ValueError(
                "Debes seleccionar un archivo."
            )

        contenido = await archivo.read()

        tamano_maximo = 10 * 1024 * 1024

        if len(contenido) > tamano_maximo:
            raise ValueError(
                "El archivo no puede superar los 10 MB."
            )

        juegos_archivo = leer_archivo_ludoteca(
            contenido=contenido,
            nombre_archivo=archivo.filename
        )

        ids_archivo = [
            juego["id_bgg"]
            for juego in juegos_archivo
        ]

        ids_inexistentes = obtener_ids_juegos_inexistentes(
            ids_archivo
        )

        ids_descargados = set()
        errores_descarga = []

        lotes = [
            ids_inexistentes[indice:indice + 20]
            for indice in range(
                0,
                len(ids_inexistentes),
                20
            )
        ]

        for numero_lote, lote in enumerate(
            lotes,
            start=1
        ):
            try:
                xml_texto = obtener_juegos_por_ids(
                    lote
                )

                juegos_bgg = parsear_juegos(
                    xml_texto
                )

                for juego in juegos_bgg:
                    guardar_juego(juego)
                    ids_descargados.add(
                        juego["id_bgg"]
                    )

            except Exception as error:
                errores_descarga.append(
                    f"Lote {numero_lote}: {error}"
                )

            if numero_lote < len(lotes):
                time.sleep(5)

        ids_existentes_finales = (
            obtener_ids_juegos_existentes(
                ids_archivo
            )
        )

        juegos_validos = [
            juego
            for juego in juegos_archivo
            if juego["id_bgg"]
            in ids_existentes_finales
        ]

        juegos_no_disponibles = (
            len(juegos_archivo)
            - len(juegos_validos)
        )

        guardar_ludoteca_usuario(
            usuario_id=usuario["id"],
            juegos=juegos_validos,
            reemplazar=reemplazar_ludoteca
        )

        registrar_importacion(
            usuario_id=usuario["id"],
            nombre_archivo=archivo.filename,
            juegos_detectados=len(juegos_archivo),
            juegos_asociados=len(juegos_validos),
            juegos_nuevos=len(ids_descargados),
            juegos_no_disponibles=
                juegos_no_disponibles,
            reemplazo_completo=
                reemplazar_ludoteca
        )

        request.session["mensaje_ludoteca"] = (
            f"Importación completada: "
            f"{len(juegos_validos)} juegos añadidos "
            f"a tu ludoteca y "
            f"{len(ids_descargados)} juegos nuevos "
            f"incorporados a la base general."
        )

        if errores_descarga or juegos_no_disponibles:
            request.session["aviso_ludoteca"] = (
                f"No se pudieron importar "
                f"{juegos_no_disponibles} juegos. "
                f"Puede tratarse de expansiones, "
                f"IDs no válidos o errores temporales de BGG."
            )

    except ValueError as error:
        request.session["error_ludoteca"] = str(
            error
        )

    except Exception as error:
        print(
            f"Error importando la ludoteca: {error}"
        )

        request.session["error_ludoteca"] = (
            "Se ha producido un error al importar "
            "la ludoteca. Revisa la consola."
        )

    finally:
        await archivo.close()

    return RedirectResponse(
        url="/mi-ludoteca",
        status_code=303
    )

def obtener_opciones():
    mecanicas = obtener_mecanicas_populares(limite=25)
    categorias = obtener_categorias_populares(limite=25)

    return mecanicas, categorias


def obtener_valores_iniciales():
    return {
        "modo_jugadores": "exacto",
        "num_jugadores": 4,
        "num_jugadores_min": 2,
        "num_jugadores_max": 5,
        "duracion_maxima": 120,
        "complejidad_maxima": 3.5,
        "limite_resultados": 12,
        "solo_rango_recomendado": False,
        "mecanicas_seleccionadas": [],
        "categorias_seleccionadas": []
    }

def obtener_usuario_actual(request):
    usuario_id = request.session.get("usuario_id")

    if usuario_id is None:
        return None

    usuario = obtener_usuario_por_id(usuario_id)

    if usuario is None:
        request.session.clear()
        return None

    return usuario

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
        "usuario": obtener_usuario_actual(request),
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

@app.get("/registro", response_class=HTMLResponse)
async def mostrar_registro(request: Request):
    if obtener_usuario_actual(request):
        return RedirectResponse(
            url="/",
            status_code=303
        )

    return plantillas.TemplateResponse(
        request=request,
        name="registro.html",
        context={
            "request": request,
            "error": None,
            "valores": {
                "nombre": "",
                "email": ""
            }
        }
    )


@app.post("/registro", response_class=HTMLResponse)
async def procesar_registro(request: Request):
    if obtener_usuario_actual(request):
        return RedirectResponse(
            url="/",
            status_code=303
        )

    formulario = await request.form()

    nombre = str(
        formulario.get("nombre", "")
    ).strip()

    email = str(
        formulario.get("email", "")
    ).strip()

    contrasena = str(
        formulario.get("contrasena", "")
    )

    confirmacion_contrasena = str(
        formulario.get("confirmacion_contrasena", "")
    )

    try:
        usuario = registrar_usuario(
            nombre=nombre,
            email=email,
            contrasena=contrasena,
            confirmacion_contrasena=confirmacion_contrasena
        )

        request.session.clear()
        request.session["usuario_id"] = usuario["id"]

        return RedirectResponse(
            url="/",
            status_code=303
        )

    except ValueError as error:
        return plantillas.TemplateResponse(
            request=request,
            name="registro.html",
            context={
                "request": request,
                "error": str(error),
                "valores": {
                    "nombre": nombre,
                    "email": email
                }
            },
            status_code=400
        )


@app.get(
    "/iniciar-sesion",
    response_class=HTMLResponse
)
async def mostrar_inicio_sesion(request: Request):
    if obtener_usuario_actual(request):
        return RedirectResponse(
            url="/",
            status_code=303
        )

    return plantillas.TemplateResponse(
        request=request,
        name="iniciar_sesion.html",
        context={
            "request": request,
            "error": None,
            "email": ""
        }
    )


@app.post(
    "/iniciar-sesion",
    response_class=HTMLResponse
)
async def procesar_inicio_sesion(request: Request):
    if obtener_usuario_actual(request):
        return RedirectResponse(
            url="/",
            status_code=303
        )

    formulario = await request.form()

    email = str(
        formulario.get("email", "")
    ).strip()

    contrasena = str(
        formulario.get("contrasena", "")
    )

    usuario = autenticar_usuario(
        email=email,
        contrasena=contrasena
    )

    if usuario is None:
        return plantillas.TemplateResponse(
            request=request,
            name="iniciar_sesion.html",
            context={
                "request": request,
                "error": (
                    "El correo o la contraseña no son correctos."
                ),
                "email": email
            },
            status_code=401
        )

    request.session.clear()
    request.session["usuario_id"] = usuario["id"]

    return RedirectResponse(
        url="/",
        status_code=303
    )


@app.post("/cerrar-sesion")
async def cerrar_sesion(request: Request):
    request.session.clear()

    return RedirectResponse(
        url="/",
        status_code=303
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
        "modo_jugadores": formulario.get(
            "modo_jugadores",
            "exacto"
        ),
        "num_jugadores": formulario.get(
            "num_jugadores",
            "4"
        ),
        "num_jugadores_min": formulario.get(
            "num_jugadores_min",
            "2"
        ),
        "num_jugadores_max": formulario.get(
            "num_jugadores_max",
            "5"
        ),
        "duracion_maxima": formulario.get(
            "duracion_maxima",
            "120"
        ),
        "complejidad_maxima": formulario.get(
            "complejidad_maxima",
            "3.5"
        ),
        "limite_resultados": formulario.get(
            "limite_resultados",
            "12"
        ),
        "solo_rango_recomendado":
            formulario.get("solo_rango_recomendado") == "on",
        "mecanicas_seleccionadas":
            mecanicas_seleccionadas,
        "categorias_seleccionadas":
            categorias_seleccionadas
    }

    try:
        modo_jugadores = valores["modo_jugadores"]

        if modo_jugadores not in {"exacto", "rango"}:
            raise ValueError(
                "El modo de selección de jugadores no es válido."
            )

        if modo_jugadores == "exacto":
            num_jugadores = convertir_entero(
                valores["num_jugadores"],
                "Número de jugadores",
                minimo=1,
                maximo=20
            )

            num_jugadores_min = num_jugadores
            num_jugadores_max = num_jugadores

        else:
            num_jugadores_min = convertir_entero(
                valores["num_jugadores_min"],
                "Número mínimo de jugadores",
                minimo=1,
                maximo=20
            )

            num_jugadores_max = convertir_entero(
                valores["num_jugadores_max"],
                "Número máximo de jugadores",
                minimo=1,
                maximo=20
            )

        if num_jugadores_min > num_jugadores_max:
            raise ValueError(
                "El número mínimo de jugadores no puede "
                "ser mayor que el máximo."
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

        limite_resultados = convertir_entero(
            valores["limite_resultados"],
            "Cantidad de resultados",
            minimo=1,
            maximo=30
        )

        limites_permitidos = {
            6,
            12,
            18,
            24,
            30
        }

        if limite_resultados not in limites_permitidos:
            raise ValueError(
                "La cantidad de resultados seleccionada "
                "no es válida."
            )
        
        valores["modo_jugadores"] = modo_jugadores
        valores["num_jugadores_min"] = num_jugadores_min
        valores["num_jugadores_max"] = num_jugadores_max

        if modo_jugadores == "exacto":
            valores["num_jugadores"] = num_jugadores

        valores["duracion_maxima"] = (
            duracion_maxima
        )

        valores["complejidad_maxima"] = (
            complejidad_maxima
        )

        valores["limite_resultados"] = (
            limite_resultados
        )

        valores["duracion_maxima"] = duracion_maxima
        valores["complejidad_maxima"] = complejidad_maxima

        juegos = recomendar_juegos(
            num_jugadores_min=num_jugadores_min,
            num_jugadores_max=num_jugadores_max,
            duracion_maxima=duracion_maxima,
            complejidad_maxima=complejidad_maxima,
            mecanicas_preferidas=mecanicas_seleccionadas,
            categorias_preferidas=categorias_seleccionadas,
            solo_rango_recomendado=valores[
                "solo_rango_recomendado"
            ],
            limite=limite_resultados
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