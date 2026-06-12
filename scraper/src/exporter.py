"""Exportación de convocatorias a JSON.

El archivo generado (`output/convocatorias.json`) es el contrato de
datos con el frontend: debe ser siempre una lista de objetos que
cumplan `shared/schemas/convocatoria.schema.json`.
"""

import json
import logging
from pathlib import Path

import jsonschema

from . import config
from .parser import Convocatoria

logger = logging.getLogger("serviciosocialmx.exporter")


def exportar_json(
    convocatorias: list[Convocatoria],
    ruta: Path = config.ARCHIVO_CONVOCATORIAS,
) -> None:
    """Escribe las convocatorias como JSON en la ruta indicada.

    Args:
        convocatorias: Lista de convocatorias normalizadas.
        ruta: Archivo de destino (por defecto, `output/convocatorias.json`).
    """
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(
        json.dumps(convocatorias, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def cargar_convocatorias(
    ruta: Path = config.ARCHIVO_CONVOCATORIAS,
) -> list[Convocatoria]:
    """Lee las convocatorias de una exportación anterior.

    Args:
        ruta: Archivo a leer (por defecto, `output/convocatorias.json`).

    Returns:
        Lista de convocatorias, o lista vacía si el archivo no existe.
    """
    if not ruta.exists():
        return []
    return json.loads(ruta.read_text(encoding="utf-8"))


def cargar_avance(ruta: Path = config.ARCHIVO_AVANCE) -> dict[str, list[str]]:
    """Lee el avance de una corrida interrumpida.

    Args:
        ruta: Archivo de avance (por defecto, `output/avance.json`).

    Returns:
        Mapeo universidad → identificadores de lotes completados, o
        diccionario vacío si no hay corrida pendiente.
    """
    if not ruta.exists():
        return {}
    return json.loads(ruta.read_text(encoding="utf-8"))


def guardar_avance(
    avance: dict[str, list[str]], ruta: Path = config.ARCHIVO_AVANCE
) -> None:
    """Escribe el avance de la corrida en curso.

    Args:
        avance: Mapeo universidad → identificadores de lotes completados.
        ruta: Archivo de destino (por defecto, `output/avance.json`).
    """
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(
        json.dumps(avance, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def limpiar_avance(ruta: Path = config.ARCHIVO_AVANCE) -> None:
    """Elimina el archivo de avance al terminar una corrida completa."""
    ruta.unlink(missing_ok=True)


def consolidar_convocatorias(
    convocatorias: list[Convocatoria],
) -> list[Convocatoria]:
    """Fusiona convocatorias duplicadas conservando todas sus carreras.

    La misma actividad puede aparecer en varios perfiles (una vacante
    abierta a varias carreras genera el mismo `id`); se conserva la
    primera aparición y se le añaden las carreras de las demás.

    Args:
        convocatorias: Lista de convocatorias, posiblemente con duplicados.

    Returns:
        Lista sin ids repetidos, en el orden de primera aparición.
    """
    por_id: dict[str, Convocatoria] = {}
    for convocatoria in convocatorias:
        existente = por_id.get(convocatoria["id"])
        if existente is None:
            por_id[convocatoria["id"]] = convocatoria
            continue
        for carrera in convocatoria.get("carreras", []):
            if carrera not in existente["carreras"]:
                existente["carreras"].append(carrera)
    return list(por_id.values())


def validar_convocatorias(convocatorias: list[Convocatoria]) -> bool:
    """Valida que cada convocatoria cumpla el esquema compartido.

    Lee `shared/schemas/convocatoria.schema.json` y valida cada elemento;
    los errores se registran en el log con el índice y el id afectados.

    Args:
        convocatorias: Lista de convocatorias a validar.

    Returns:
        True si todas las convocatorias son válidas.
    """
    esquema = json.loads(config.RUTA_ESQUEMA.read_text(encoding="utf-8"))
    validador = jsonschema.Draft202012Validator(esquema)

    valido = True
    for indice, convocatoria in enumerate(convocatorias):
        for error in validador.iter_errors(convocatoria):
            valido = False
            logger.error(
                "Convocatoria %d (id=%s) inválida: %s",
                indice,
                convocatoria.get("id", "?"),
                error.message,
            )
    return valido
