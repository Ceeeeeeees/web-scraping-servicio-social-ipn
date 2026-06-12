"""Utilidades compartidas del scraper (logging, helpers genéricos)."""

import logging
import re
import unicodedata
from datetime import datetime

from . import config


def configurar_logging(nombre: str = "serviciosocialmx") -> logging.Logger:
    """Configura y devuelve el logger del proyecto.

    Escribe simultáneamente a consola y a un archivo con fecha dentro
    de `scraper/logs/`.

    Args:
        nombre: Nombre del logger raíz del proyecto.
    """
    config.RUTA_LOGS.mkdir(parents=True, exist_ok=True)
    archivo_log = config.RUTA_LOGS / f"{datetime.now():%Y-%m-%d}.log"

    logger = logging.getLogger(nombre)
    logger.setLevel(logging.INFO)

    # Evita duplicar handlers si se llama más de una vez
    if not logger.handlers:
        formato = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

        consola = logging.StreamHandler()
        consola.setFormatter(formato)
        logger.addHandler(consola)

        archivo = logging.FileHandler(archivo_log, encoding="utf-8")
        archivo.setFormatter(formato)
        logger.addHandler(archivo)

    return logger


def generar_id(universidad: str, titulo: str) -> str:
    """Genera un identificador estable para una convocatoria.

    Combina la universidad y un slug del título para que el mismo
    programa conserve su id entre ejecuciones del scraper.

    Args:
        universidad: Identificador corto de la universidad (ej. "ipn").
        titulo: Título de la convocatoria.
    """
    # Slug URL-safe: sin acentos ni signos, solo [a-z0-9] separados por guiones
    sin_acentos = (
        unicodedata.normalize("NFKD", titulo).encode("ascii", "ignore").decode()
    )
    slug = re.sub(r"[^a-z0-9]+", "-", sin_acentos.lower())[:60].strip("-")
    return f"{universidad}-{slug}"
