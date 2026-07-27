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

from app.forms.opciones_formulario import (
    obtener_categorias_populares,
    obtener_mecanicas_populares,
    obtener_tipos_juego
)

from app.services.recomendador_basico import recomendar_juegos

from app.database.base_datos import (
    buscar_juegos_por_nombre,
    guardar_juego,
    obtener_detalle_juego
)

from app.auth.usuarios import (
    asegurar_columnas_usuarios,
    autenticar_usuario,
    crear_tabla_usuarios,
    obtener_usuario_por_id,
    registrar_usuario
)

from app.library.ludoteca import (
    crear_tablas_ludoteca,
    guardar_ludoteca_usuario,
    obtener_ids_juegos_existentes,
    obtener_ids_juegos_inexistentes,
    obtener_ludoteca_usuario,
    obtener_ultima_importacion,
    registrar_importacion
)

from app.services.bgg_api import obtener_juegos_por_ids
from app.services.parser_bgg import parsear_juegos
from app.services.importador_ludoteca import leer_archivo_ludoteca
from app.admin.administracion import preparar_tablas_admin
from app.admin.importar_juegos import importar_juegos_admin

from app.admin.administracion import (
    buscar_juegos_admin,
    cambiar_usuario_activo,
    cambiar_usuario_admin,
    eliminar_usuario,
    eliminar_video_tiktok,
    guardar_video_tiktok,
    obtener_estadisticas_admin,
    obtener_usuarios_admin,
    obtener_video_tiktok,
    obtener_videos_tiktok_de_juego,
    obtener_videos_tiktok_publicos,
    preparar_tablas_admin
)

from app.admin.mantenimiento import (
    guardar_estado_mantenimiento,
    obtener_estado_mantenimiento
)

from dotenv import load_dotenv
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


from app.config import (
    RUTA_PLANTILLAS,
    RUTA_STATIC
)

from app.support.soporte import (
    cambiar_estado_mensaje_soporte,
    crear_tabla_mensajes_soporte,
    guardar_mensaje_soporte,
    obtener_mensajes_soporte
)


CLAVE_SESION = os.getenv("SESSION_SECRET")

if not CLAVE_SESION:
    raise RuntimeError(
        "No se ha encontrado SESSION_SECRET en el archivo .env."
    )



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


@app.middleware("http")
async def comprobar_mantenimiento(request: Request, call_next):
    estado_mantenimiento = obtener_estado_mantenimiento()

    if not estado_mantenimiento["activo"]:
        return await call_next(request)

    ruta = request.url.path

    for ruta_permitida in RUTAS_PERMITIDAS_MANTENIMIENTO:
        if ruta.startswith(ruta_permitida):
            return await call_next(request)

    return plantillas.TemplateResponse(
        request=request,
        name="mantenimiento.html",
        context={
            "request": request,
            "titulo": estado_mantenimiento["titulo"],
            "mensaje": estado_mantenimiento["mensaje"]
        },
        status_code=503
    )

RUTAS_PERMITIDAS_MANTENIMIENTO = (
    "/static",
    "/iniciar-sesion",
    "/cerrar-sesion",
    "/admin/mantenimiento"
)

crear_tabla_usuarios()
asegurar_columnas_usuarios()
crear_tablas_ludoteca()
preparar_tablas_admin()
crear_tabla_mensajes_soporte()

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
    mecanicas = obtener_mecanicas_populares(limite=50)
    categorias = obtener_categorias_populares(limite=50)
    tipos_juego = obtener_tipos_juego()

    return mecanicas, categorias, tipos_juego


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
        "solo_ludoteca": False,
        "mecanicas_seleccionadas": [],
        "categorias_seleccionadas": [],
        "tipo_juego": ""
    }

def obtener_usuario_actual(request):
    usuario_id = request.session.get("usuario_id")

    if usuario_id is None:
        return None

    usuario = obtener_usuario_por_id(usuario_id)

    if usuario is None:
        request.session.clear()
        return None

    if not usuario.get("activo", 1):
        request.session.clear()
        return None

    return usuario

def obtener_admin_actual(request):
    usuario = obtener_usuario_actual(request)

    if usuario is None:
        return None

    if not usuario.get("es_admin"):
        raise HTTPException(
            status_code=403,
            detail="No tienes permisos de administrador."
        )

    return usuario

def crear_contexto(
    request,
    valores=None,
    juegos=None,
    error=None,
    formulario_enviado=False
):
    mecanicas, categorias, tipos_juego = obtener_opciones()

    if valores is None:
        valores = obtener_valores_iniciales()

    return {
        "request": request,
        "usuario": obtener_usuario_actual(request),
        "mecanicas": mecanicas,
        "categorias": categorias,
        "tipos_juego": tipos_juego,
        "tipo_juego_seleccionado": valores.get("tipo_juego", ""),
        "valores": valores,
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
    usuario = obtener_usuario_actual(request)
    formulario = await request.form()

    mecanicas_disponibles, categorias_disponibles, tipos_juego = obtener_opciones()

    tipos_validos = {
        tipo["valor"]
        for tipo in tipos_juego
    }

    tipo_juego = str(
        formulario.get("tipo_juego", "")
    ).strip().lower()

    if tipo_juego not in tipos_validos:
        tipo_juego = ""

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
        "solo_ludoteca": 
            formulario.get("solo_ludoteca") == "on",
        "mecanicas_seleccionadas":
            mecanicas_seleccionadas,
        "categorias_seleccionadas":
            categorias_seleccionadas,
        "tipo_juego": tipo_juego,
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
            maximo=60
        )

        limites_permitidos = {
            6,
            12,
            18,
            24,
            30,
            60
        }

        if limite_resultados not in limites_permitidos:
            raise ValueError(
                "La cantidad de resultados seleccionada "
                "no es válida."
            )

        if valores["solo_ludoteca"] and usuario is None:
            raise ValueError(
                "Debes iniciar sesión para recomendar juegos de tu ludoteca."
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
            tipo_juego=valores["tipo_juego"],
            solo_rango_recomendado=valores[
                "solo_rango_recomendado"
            ],
            limite=limite_resultados,
            usuario_id=usuario["id"] if usuario else None,
            solo_ludoteca=valores["solo_ludoteca"]
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

@app.get("/buscar", response_class=HTMLResponse)
async def buscar_juegos(
    request: Request,
    q: str = "",
    solo_ludoteca: bool = False
):
    usuario = obtener_usuario_actual(request)

    texto_busqueda = q.strip()

    error = None
    juegos = []

    if not texto_busqueda:
        error = "Introduce un nombre de juego para buscar."

    elif len(texto_busqueda) < 2:
        error = "La búsqueda debe tener al menos 2 caracteres."

    elif solo_ludoteca and usuario is None:
        error = (
            "Debes iniciar sesión para buscar solo "
            "en tu ludoteca."
        )

    else:
        juegos = buscar_juegos_por_nombre(
            texto_busqueda=texto_busqueda,
            limite=40,
            usuario_id=usuario["id"] if usuario else None,
            solo_ludoteca=solo_ludoteca
        )

    return plantillas.TemplateResponse(
        request=request,
        name="buscar.html",
        context={
            "request": request,
            "usuario": usuario,
            "q": texto_busqueda,
            "solo_ludoteca": solo_ludoteca,
            "juegos": juegos,
            "total_resultados": len(juegos),
            "error": error
        }
    )

@app.get("/admin", response_class=HTMLResponse)
async def panel_admin(request: Request):
    usuario = obtener_admin_actual(request)

    if usuario is None:
        return RedirectResponse(
            url="/iniciar-sesion",
            status_code=303
        )

    estadisticas = obtener_estadisticas_admin()

    return plantillas.TemplateResponse(
        request=request,
        name="admin/dashboard.html",
        context={
            "request": request,
            "usuario": usuario,
            "estadisticas": estadisticas
        }
    )


@app.get("/admin/usuarios", response_class=HTMLResponse)
async def admin_usuarios(request: Request):
    usuario = obtener_admin_actual(request)

    if usuario is None:
        return RedirectResponse(
            url="/iniciar-sesion",
            status_code=303
        )

    mensaje = request.session.pop(
        "mensaje_admin",
        None
    )

    error = request.session.pop(
        "error_admin",
        None
    )

    usuarios = obtener_usuarios_admin()

    return plantillas.TemplateResponse(
        request=request,
        name="admin/usuarios.html",
        context={
            "request": request,
            "usuario": usuario,
            "usuarios": usuarios,
            "mensaje": mensaje,
            "error": error
        }
    )


@app.post("/admin/usuarios/{usuario_id}/admin")
async def cambiar_permiso_admin(
    request: Request,
    usuario_id: int,
    es_admin: bool = Form(False)
):
    usuario = obtener_admin_actual(request)

    if usuario is None:
        return RedirectResponse(
            url="/iniciar-sesion",
            status_code=303
        )

    if usuario_id == usuario["id"] and not es_admin:
        request.session["error_admin"] = (
            "No puedes quitarte permisos de administrador a ti mismo."
        )

        return RedirectResponse(
            url="/admin/usuarios",
            status_code=303
        )

    cambiar_usuario_admin(
        usuario_id=usuario_id,
        es_admin=es_admin
    )

    request.session["mensaje_admin"] = (
        "Permisos actualizados correctamente."
    )

    return RedirectResponse(
        url="/admin/usuarios",
        status_code=303
    )


@app.post("/admin/usuarios/{usuario_id}/activo")
async def cambiar_estado_usuario(
    request: Request,
    usuario_id: int,
    activo: bool = Form(False)
):
    usuario = obtener_admin_actual(request)

    if usuario is None:
        return RedirectResponse(
            url="/iniciar-sesion",
            status_code=303
        )

    if usuario_id == usuario["id"] and not activo:
        request.session["error_admin"] = (
            "No puedes desactivar tu propio usuario."
        )

        return RedirectResponse(
            url="/admin/usuarios",
            status_code=303
        )

    cambiar_usuario_activo(
        usuario_id=usuario_id,
        activo=activo
    )

    request.session["mensaje_admin"] = (
        "Estado del usuario actualizado correctamente."
    )

    return RedirectResponse(
        url="/admin/usuarios",
        status_code=303
    )

@app.post("/admin/usuarios/{usuario_id}/eliminar")
async def eliminar_usuario_admin(
    request: Request,
    usuario_id: int
):
    usuario = obtener_admin_actual(request)

    if usuario is None:
        return RedirectResponse(
            url="/iniciar-sesion",
            status_code=303
        )

    if usuario_id == usuario["id"]:
        request.session["error_admin"] = (
            "No puedes eliminar tu propio usuario."
        )

        return RedirectResponse(
            url="/admin/usuarios",
            status_code=303
        )

    eliminado = eliminar_usuario(usuario_id)

    if eliminado:
        request.session["mensaje_admin"] = (
            "Usuario eliminado correctamente."
        )
    else:
        request.session["error_admin"] = (
            "No se ha encontrado el usuario que quieres eliminar."
        )

    return RedirectResponse(
        url="/admin/usuarios",
        status_code=303
    )

@app.get("/admin/juegos", response_class=HTMLResponse)
async def admin_juegos(
    request: Request,
    q: str = ""
):
    usuario = obtener_admin_actual(request)

    if usuario is None:
        return RedirectResponse(
            url="/iniciar-sesion",
            status_code=303
        )

    texto_busqueda = q.strip()
    juegos = []

    if texto_busqueda:
        juegos = buscar_juegos_admin(
            texto_busqueda=texto_busqueda,
            limite=50
        )

    return plantillas.TemplateResponse(
        request=request,
        name="admin/juegos.html",
        context={
            "request": request,
            "usuario": usuario,
            "q": texto_busqueda,
            "juegos": juegos
        }
    )

@app.get("/admin/juegos/subir", response_class=HTMLResponse)
async def mostrar_subir_juegos_admin(request: Request):
    usuario = obtener_admin_actual(request)

    if usuario is None:
        return RedirectResponse(
            url="/iniciar-sesion",
            status_code=303
        )

    resultado = request.session.pop(
        "resultado_subida_juegos",
        None
    )

    error = request.session.pop(
        "error_subida_juegos",
        None
    )

    valores = request.session.pop(
        "valores_subida_juegos",
        {
            "ids_juegos": ""
        }
    )

    return plantillas.TemplateResponse(
        request=request,
        name="admin/subir_juegos.html",
        context={
            "request": request,
            "usuario": usuario,
            "resultado": resultado,
            "error": error,
            "valores": valores
        }
    )


@app.post("/admin/juegos/subir")
async def subir_juegos_admin(
    request: Request,
    ids_juegos: str = Form(...)
):
    usuario = obtener_admin_actual(request)

    if usuario is None:
        return RedirectResponse(
            url="/iniciar-sesion",
            status_code=303
        )

    try:
        resultado = importar_juegos_admin(ids_juegos)

        request.session["resultado_subida_juegos"] = resultado

    except ValueError as error:
        request.session["error_subida_juegos"] = str(error)
        request.session["valores_subida_juegos"] = {
            "ids_juegos": ids_juegos
        }

    except Exception as error:
        print(f"Error subiendo juegos desde admin: {error}")

        request.session["error_subida_juegos"] = (
            "Se ha producido un error al importar los juegos."
        )

        request.session["valores_subida_juegos"] = {
            "ids_juegos": ids_juegos
        }

    return RedirectResponse(
        url="/admin/juegos/subir",
        status_code=303
    )

@app.get(
    "/admin/juegos/{id_bgg}/videos",
    response_class=HTMLResponse
)
async def admin_videos_juego(
    request: Request,
    id_bgg: int
):
    usuario = obtener_admin_actual(request)

    if usuario is None:
        return RedirectResponse(
            url="/iniciar-sesion",
            status_code=303
        )

    juego = obtener_detalle_juego(id_bgg)

    if juego is None:
        raise HTTPException(
            status_code=404,
            detail="Juego no encontrado."
        )

    videos = obtener_videos_tiktok_de_juego(id_bgg)

    mensaje = request.session.pop(
        "mensaje_admin",
        None
    )

    error = request.session.pop(
        "error_admin",
        None
    )

    return plantillas.TemplateResponse(
        request=request,
        name="admin/videos_juego.html",
        context={
            "request": request,
            "usuario": usuario,
            "juego": juego,
            "videos": videos,
            "mensaje": mensaje,
            "error": error
        }
    )


@app.post("/admin/juegos/{id_bgg}/videos")
async def crear_video_tiktok_juego(
    request: Request,
    id_bgg: int,
    url: str = Form(...),
    titulo: str = Form(""),
    activo: bool = Form(False)
):
    usuario = obtener_admin_actual(request)

    if usuario is None:
        return RedirectResponse(
            url="/iniciar-sesion",
            status_code=303
        )

    juego = obtener_detalle_juego(id_bgg)

    if juego is None:
        raise HTTPException(
            status_code=404,
            detail="Juego no encontrado."
        )

    try:
        guardar_video_tiktok(
            juego_id=id_bgg,
            url=url,
            titulo=titulo,
            activo=activo
        )

        request.session["mensaje_admin"] = (
            "Vídeo de TikTok añadido correctamente."
        )

    except ValueError as error:
        request.session["error_admin"] = str(error)

    return RedirectResponse(
        url=f"/admin/juegos/{id_bgg}/videos",
        status_code=303
    )


@app.post("/admin/videos/{video_id}/eliminar")
async def borrar_video_tiktok(
    request: Request,
    video_id: int
):
    usuario = obtener_admin_actual(request)

    if usuario is None:
        return RedirectResponse(
            url="/iniciar-sesion",
            status_code=303
        )

    video = obtener_video_tiktok(video_id)

    if video is None:
        raise HTTPException(
            status_code=404,
            detail="Vídeo no encontrado."
        )

    juego_id = video["juego_id"]

    eliminar_video_tiktok(video_id)

    request.session["mensaje_admin"] = (
        "Vídeo eliminado correctamente."
    )

    return RedirectResponse(
        url=f"/admin/juegos/{juego_id}/videos",
        status_code=303
    )

@app.get("/admin/mantenimiento", response_class=HTMLResponse)
async def mostrar_mantenimiento_admin(request: Request):
    usuario = obtener_admin_actual(request)

    if usuario is None:
        return RedirectResponse(
            url="/iniciar-sesion",
            status_code=303
        )

    estado_mantenimiento = obtener_estado_mantenimiento()

    return plantillas.TemplateResponse(
        request=request,
        name="admin/mantenimiento.html",
        context={
            "request": request,
            "usuario": usuario,
            "estado_mantenimiento": estado_mantenimiento
        }
    )


@app.post("/admin/mantenimiento")
async def actualizar_mantenimiento_admin(
    request: Request,
    activo: str = Form(None),
    titulo: str = Form(...),
    mensaje: str = Form(...)
):
    usuario = obtener_admin_actual(request)

    if usuario is None:
        return RedirectResponse(
            url="/iniciar-sesion",
            status_code=303
        )

    guardar_estado_mantenimiento(
        activo=activo == "on",
        titulo=titulo,
        mensaje=mensaje
    )

    return RedirectResponse(
        url="/admin/mantenimiento",
        status_code=303
    )

@app.get("/admin/soporte", response_class=HTMLResponse)
async def mostrar_mensajes_soporte_admin(request: Request):
    usuario = obtener_admin_actual(request)

    if usuario is None:
        return RedirectResponse(
            url="/iniciar-sesion",
            status_code=303
        )

    mensajes = obtener_mensajes_soporte()

    return plantillas.TemplateResponse(
        request=request,
        name="admin/soporte.html",
        context={
            "request": request,
            "usuario": usuario,
            "mensajes": mensajes
        }
    )

@app.get("/soporte", response_class=HTMLResponse)
async def mostrar_soporte(request: Request):
    usuario = obtener_usuario_actual(request)

    mensaje_exito = request.session.pop(
        "mensaje_soporte",
        None
    )

    error = request.session.pop(
        "error_soporte",
        None
    )

    valores = request.session.pop(
        "valores_soporte",
        None
    )

    if valores is None:
        valores = {
            "nombre": usuario["nombre"] if usuario else "",
            "email": usuario["email"] if usuario else "",
            "tipo": "mejora",
            "asunto": "",
            "mensaje": ""
        }

    return plantillas.TemplateResponse(
        request=request,
        name="soporte.html",
        context={
            "request": request,
            "usuario": usuario,
            "mensaje_exito": mensaje_exito,
            "error": error,
            "valores": valores
        }
    )

@app.post("/admin/soporte/{mensaje_id}/estado")
async def actualizar_estado_soporte_admin(
    request: Request,
    mensaje_id: int,
    estado: str = Form(...)
):
    usuario = obtener_admin_actual(request)

    if usuario is None:
        return RedirectResponse(
            url="/iniciar-sesion",
            status_code=303
        )

    try:
        cambiar_estado_mensaje_soporte(
            mensaje_id=mensaje_id,
            estado=estado
        )

    except ValueError as error:
        print(f"Error cambiando estado de soporte: {error}")

    except Exception as error:
        print(f"Error inesperado cambiando estado de soporte: {error}")

    return RedirectResponse(
        url="/admin/soporte",
        status_code=303
    )

@app.post("/soporte")
async def enviar_soporte(
    request: Request,
    nombre: str = Form(...),
    email: str = Form(...),
    tipo: str = Form(...),
    asunto: str = Form(...),
    mensaje: str = Form(...)
):
    usuario = obtener_usuario_actual(request)

    try:
        guardar_mensaje_soporte(
            usuario_id=usuario["id"] if usuario else None,
            nombre=nombre,
            email=email,
            tipo=tipo,
            asunto=asunto,
            mensaje=mensaje
        )

        request.session["mensaje_soporte"] = (
            "Mensaje enviado correctamente. Gracias por ayudar a mejorar la web."
        )

    except ValueError as error:
        request.session["error_soporte"] = str(error)

        request.session["valores_soporte"] = {
            "nombre": nombre,
            "email": email,
            "tipo": tipo,
            "asunto": asunto,
            "mensaje": mensaje
        }

    except Exception as error:
        print(f"Error guardando mensaje de soporte: {error}")

        request.session["error_soporte"] = (
            "Se ha producido un error al enviar el mensaje."
        )

        request.session["valores_soporte"] = {
            "nombre": nombre,
            "email": email,
            "tipo": tipo,
            "asunto": asunto,
            "mensaje": mensaje
        }

    return RedirectResponse(
        url="/soporte",
        status_code=303
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

    videos_tiktok = obtener_videos_tiktok_publicos(id_bgg)

    return plantillas.TemplateResponse(
        request=request,
        name="detalle_juego.html",
        context={
            "request": request,
            "juego": juego,
            "videos_tiktok": videos_tiktok
        }
    )