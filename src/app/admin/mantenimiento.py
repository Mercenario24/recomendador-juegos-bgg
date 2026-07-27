import json
from pathlib import Path

from app.config import RUTA_DATOS


RUTA_ESTADO_MANTENIMIENTO = RUTA_DATOS / "mantenimiento.json"


def obtener_estado_mantenimiento():
    if not RUTA_ESTADO_MANTENIMIENTO.exists():
        return {
            "activo": False,
            "titulo": "Web en mantenimiento",
            "mensaje": "Estamos realizando cambios. Vuelve a intentarlo en unos minutos."
        }

    try:
        with open(RUTA_ESTADO_MANTENIMIENTO, "r", encoding="utf-8") as archivo:
            datos = json.load(archivo)

        return {
            "activo": bool(datos.get("activo", False)),
            "titulo": datos.get("titulo") or "Web en mantenimiento",
            "mensaje": datos.get("mensaje") or "Estamos realizando cambios. Vuelve a intentarlo en unos minutos."
        }

    except Exception:
        return {
            "activo": False,
            "titulo": "Web en mantenimiento",
            "mensaje": "Estamos realizando cambios. Vuelve a intentarlo en unos minutos."
        }


def guardar_estado_mantenimiento(activo, titulo, mensaje):
    RUTA_DATOS.mkdir(parents=True, exist_ok=True)

    datos = {
        "activo": bool(activo),
        "titulo": str(titulo or "Web en mantenimiento").strip(),
        "mensaje": str(
            mensaje or "Estamos realizando cambios. Vuelve a intentarlo en unos minutos."
        ).strip()
    }

    with open(RUTA_ESTADO_MANTENIMIENTO, "w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, ensure_ascii=False, indent=4)

    return datos