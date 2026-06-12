"""Parseo de HTML crudo a convocatorias normalizadas.

Cada universidad tiene su propia función de parseo porque la estructura
de su portal es distinta, pero todas deben producir diccionarios que
cumplan el esquema compartido definido en:

    shared/schemas/convocatoria.schema.json
"""

import logging
import re
from datetime import date
from typing import Any

from bs4 import BeautifulSoup, Tag

from . import config, utils

logger = logging.getLogger("serviciosocialmx.parser")

# Alias de tipo: una convocatoria normalizada según el esquema compartido.
Convocatoria = dict[str, Any]

# Fechas del portal del IPN: día/mes/año sin ceros a la izquierda (16/5/2025)
_RE_FECHA = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})")

# Clave del prestatario en el subtítulo: "Prestatario : YMCA (401019432)".
# Puede ser alfanumérica (p. ej. "02124X02255"), no solo dígitos.
_RE_CVE_PRSTTR = re.compile(r"\(([0-9A-Za-z]+)\)\s*$")

# Monto dentro del bloque de apoyos: "Monto del Apoyo $ 1,500.00"
_RE_MONTO = re.compile(r"Monto del Apoyo\s*\$\s*([\d][\d,]*(?:\.\d+)?)")

# Clave del programa: "Nombre del programa: APOYO INTEGRAL (B000000074)"
_RE_CVE_PROGRAMA = re.compile(r"\(([0-9A-Za-z]+)\)\s*$")

# Demarcación dentro del domicilio: "..., Delegación o Municipio: MIGUEL HIDALGO"
_RE_UBICACION = re.compile(r"Delegaci[oó]n o Municipio:\s*([^,]+)")

# Prefijos redundantes en la demarcación ("ALCALDÍA GUSTAVO A. MADERO",
# "ALC. BENITO JUÁREZ", "MUNICIPIO DE ECATEPEC"); se quitan para que el
# filtro por ubicación no tenga categorías duplicadas
_RE_PREFIJO_UBICACION = re.compile(
    r"^(?:ALCALD[IÍ]A|DELEGACI[OÓ]N|ALC\.|DEL\.|MUNICIPIO DE)\s+", re.IGNORECASE
)


def _texto(elemento: Tag) -> str:
    """Texto plano de un elemento, con espacios normalizados."""
    return re.sub(r"\s+", " ", elemento.get_text(" ", strip=True)).strip()


def _parsear_fecha(texto: str) -> str | None:
    """Convierte una fecha 'd/m/aaaa' del portal a ISO 8601, o None."""
    coincidencia = _RE_FECHA.search(texto)
    if not coincidencia:
        return None
    dia, mes, anio = (int(grupo) for grupo in coincidencia.groups())
    try:
        return date(anio, mes, dia).isoformat()
    except ValueError:
        return None


def _calcular_estado(fecha_inicio: str | None, fecha_termino: str | None) -> str:
    """Deriva el estado de la convocatoria a partir de sus fechas de vigencia."""
    hoy = date.today().isoformat()
    if fecha_inicio and hoy < fecha_inicio:
        return "proxima"
    if fecha_termino and hoy > fecha_termino:
        return "cerrada"
    return "abierta"


def _parsear_actividad(
    bloque: list[Tag], cve_perfil: int | None
) -> Convocatoria | None:
    """Convierte un bloque de actividad del portal del IPN en una convocatoria.

    Args:
        bloque: Elementos del bloque, empezando por el `div.subtitulo`
            con el nombre de la actividad.
        cve_perfil: Clave del perfil de origen (para `carreras` y `url`).
    """
    titulo = _texto(bloque[0]).removeprefix("Actividad:").strip()
    if not titulo:
        return None

    # Recolectar los campos etiquetados ("Nombre largo:", "Objetivo:", ...)
    campos: dict[str, str] = {}
    cve_prsttr: str | None = None
    for elemento in bloque[1:]:
        texto = _texto(elemento)
        if "subtitulo2" in (elemento.get("class") or []):
            coincidencia = _RE_CVE_PRSTTR.search(texto)
            if coincidencia:
                cve_prsttr = coincidencia.group(1)
            continue
        etiqueta = elemento.find("b")
        if etiqueta is not None:
            nombre = _texto(etiqueta).rstrip(":")
            campos[nombre] = texto.removeprefix(_texto(etiqueta)).strip()

    if cve_prsttr is None:
        logger.warning("Actividad '%s' sin clave de prestatario; omitida", titulo)
        return None

    # Fechas de vigencia (vienen juntas en la misma fila)
    fila_fechas = campos.get("Fecha inicio", "")
    partes = fila_fechas.split("Fecha término:")
    fecha_inicio = _parsear_fecha(partes[0])
    fecha_termino = _parsear_fecha(partes[1]) if len(partes) > 1 else None

    # Apoyos: el campo clave del proyecto es la beca económica
    apoyos = campos.get("Apoyos", "")
    apoyo_economico = "BECA" in apoyos.upper()
    coincidencia_monto = _RE_MONTO.search(apoyos)
    monto = (
        float(coincidencia_monto.group(1).replace(",", ""))
        if coincidencia_monto
        else None
    )

    # Varias carreras pueden compartir perfil; van unidas con " / "
    carrera = config.PERFILES_IPN.get(cve_perfil) if cve_perfil else None

    # La clave del programa distingue actividades del mismo prestatario
    # con títulos casi idénticos (difieren solo en puntuación)
    coincidencia_programa = _RE_CVE_PROGRAMA.search(
        campos.get("Nombre del programa", "")
    )
    cve_programa = coincidencia_programa.group(1) if coincidencia_programa else ""

    # Domicilio del prestatario: texto completo para el enlace a mapas y
    # la delegación/municipio como dato limpio para filtrar por ubicación
    direccion = campos.get("Domicilio", "").strip(" ,") or None
    coincidencia_ubicacion = _RE_UBICACION.search(direccion or "")
    ubicacion = (
        coincidencia_ubicacion.group(1).strip() if coincidencia_ubicacion else None
    )
    if ubicacion:
        ubicacion = _RE_PREFIJO_UBICACION.sub("", ubicacion).strip() or None

    return {
        "id": utils.generar_id("ipn", f"{cve_prsttr} {cve_programa} {titulo}"),
        "titulo": titulo,
        "descripcion": campos.get("Objetivo", ""),
        "institucion": campos.get("Nombre largo", ""),
        "ubicacion": ubicacion,
        "direccion": direccion,
        "universidadOrigen": "ipn",
        "carreras": carrera.split(" / ") if carrera else [],
        "apoyoEconomico": apoyo_economico,
        "monto": monto,
        "modalidad": "no-especificada",
        "fechaPublicacion": fecha_inicio,
        "fechaLimite": fecha_termino,
        "url": (
            f"{config.IPN_URL_PROGRAMAS}?cvePerfil={cve_perfil}"
            f"&cvePrsttr={cve_prsttr}"
        ),
        "estado": _calcular_estado(fecha_inicio, fecha_termino),
    }


def parsear_ipn(html: str) -> list[Convocatoria]:
    """Extrae convocatorias de una página de programas del portal del IPN.

    La página (InfoServSocListaProgsActivi.do) lista una o más
    "actividades" de un prestatario; cada actividad se normaliza como
    una convocatoria independiente.

    Args:
        html: Documento HTML crudo descargado por `ScraperIPN`.

    Returns:
        Lista de convocatorias normalizadas (puede estar vacía).
    """
    soup = BeautifulSoup(html, "html.parser")

    # El perfil de origen viene en el enlace "Regresar" de la página
    cve_perfil: int | None = None
    enlace_regresar = soup.find(
        "a", href=lambda h: h and "InfoServSocListaPrsttrPerf.do" in h
    )
    if enlace_regresar is not None:
        coincidencia = re.search(r"cvePerfil=(\d+)", enlace_regresar["href"])
        if coincidencia:
            cve_perfil = int(coincidencia.group(1))

    # Las actividades viven en el div.tabla del contenido (el menú lateral
    # también usa la clase "tabla", pero no contiene div.subtitulo).
    convocatorias: list[Convocatoria] = []
    for tabla in soup.find_all("div", class_="tabla"):
        bloque: list[Tag] = []
        for elemento in tabla.find_all("div", recursive=False):
            clases = elemento.get("class") or []
            if "subtitulo" in clases:
                if bloque:
                    convocatoria = _parsear_actividad(bloque, cve_perfil)
                    if convocatoria:
                        convocatorias.append(convocatoria)
                bloque = [elemento]
            elif bloque:
                bloque.append(elemento)
        if bloque:
            convocatoria = _parsear_actividad(bloque, cve_perfil)
            if convocatoria:
                convocatorias.append(convocatoria)

    return convocatorias


# Registro de parsers por universidad, paralelo a `scraper.SCRAPERS`.
PARSERS = {
    "ipn": parsear_ipn,
}
