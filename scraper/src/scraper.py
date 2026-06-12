"""Scrapers por universidad.

Define una clase base `ScraperBase` con la interfaz común y una
implementación por universidad. El diseño permite añadir nuevas
universidades sin tocar el resto del sistema: cada scraper devuelve
HTML/datos crudos que luego `parser.py` convierte en convocatorias
normalizadas.
"""

import logging
import re
import threading
import time
from abc import ABC, abstractmethod
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import parse_qs, urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup

from . import config

logger = logging.getLogger("serviciosocialmx.scraper")


class ScraperBase(ABC):
    """Interfaz común que debe implementar el scraper de cada universidad."""

    #: Identificador corto de la universidad (clave en `config.UNIVERSIDADES`)
    universidad: str

    @abstractmethod
    def iterar_lotes(self, completados: set[str]) -> Iterator[tuple[str, list[str]]]:
        """Descarga las páginas con convocatorias en lotes reanudables.

        Un lote agrupa las páginas que conviene exportar juntas (en el
        IPN, las de un perfil). Tras cada lote, `main` exporta el avance
        y registra su identificador, de modo que una corrida
        interrumpida pueda reanudarse sin repetir lo ya descargado.

        Args:
            completados: Identificadores de lotes completados en una
                corrida anterior interrumpida; deben omitirse.

        Yields:
            Tuplas (identificador del lote, documentos HTML del lote).
        """
        raise NotImplementedError


class ScraperIPN(ScraperBase):
    """Scraper del portal de Servicio Social del IPN.

    Portal objetivo: https://serviciosocial.ipn.mx/

    Flujo general:

        0. Si `config.PERFILES_IPN` está vacío, descubrir todos los
           perfiles (carreras) recorriendo el formulario en cascada
           nivel → área → carrera (InfoServSocListaPerfiles.do).
        1. Descargar la lista de prestatarios de cada perfil
           (InfoServSocListaPrsttrPerf.do?cvePerfil=<n>).
        2. Extraer de los enlaces "Ver" la clave de cada prestatario.
        3. Descargar la página de programas/actividades de cada prestatario
           (InfoServSocListaProgsActivi.do?cvePerfil=<n>&cvePrsttr=<m>).

    Las páginas del paso 3 son las que contienen los datos de cada
    convocatoria y son las que se devuelven para parsear.
    """

    universidad = "ipn"

    def __init__(self) -> None:
        # requests.Session no es thread-safe: cada hilo usa la suya
        self._hilo_local = threading.local()

    @property
    def sesion(self) -> requests.Session:
        """Sesión HTTP propia del hilo actual (se crea bajo demanda)."""
        if not hasattr(self._hilo_local, "sesion"):
            sesion = requests.Session()
            sesion.headers["User-Agent"] = config.USER_AGENT
            # Reintentos con espera creciente para timeouts y errores 5xx
            # transitorios del portal
            reintentos = Retry(
                total=2,
                backoff_factor=2.0,
                status_forcelist=(500, 502, 503, 504),
            )
            sesion.mount("https://", HTTPAdapter(max_retries=reintentos))
            self._hilo_local.sesion = sesion
        return self._hilo_local.sesion

    def _descargar(self, url: str, params: dict[str, int | str]) -> str:
        """Descarga una URL por GET respetando la pausa entre peticiones."""
        respuesta = self.sesion.get(url, params=params, timeout=config.TIMEOUT_SEGUNDOS)
        respuesta.raise_for_status()
        time.sleep(config.PAUSA_ENTRE_PETICIONES)
        return respuesta.text

    def _enviar_formulario_perfiles(self, datos: dict[str, str]) -> str:
        """Envía el formulario en cascada de perfiles y devuelve el HTML."""
        respuesta = self.sesion.post(
            config.IPN_URL_PERFILES, data=datos, timeout=config.TIMEOUT_SEGUNDOS
        )
        respuesta.raise_for_status()
        time.sleep(config.PAUSA_ENTRE_PETICIONES)
        return respuesta.text

    @staticmethod
    def _opciones_select(html: str, nombre: str) -> list[tuple[str, str]]:
        """Extrae las opciones (valor, texto) de un `<select>` por nombre."""
        soup = BeautifulSoup(html, "html.parser")
        select = soup.find("select", attrs={"name": nombre})
        if select is None:
            return []
        return [
            (opcion["value"], opcion.get_text(strip=True))
            for opcion in select.find_all("option")
            if opcion.get("value")
        ]

    def _descubrir_perfiles(self) -> dict[int, str]:
        """Descubre todos los perfiles (carreras) disponibles en el portal.

        Recorre el formulario en cascada de InfoServSocListaPerfiles.do:
        cada combinación nivel → área lista sus carreras (`cveProgEst`) y
        al enviar una carrera el portal responde con la lista de
        prestatarios, de cuyos enlaces se extrae el `cvePerfil` real.

        Returns:
            Mapeo cvePerfil → nombre de la carrera. Si varias carreras
            comparten perfil, los nombres se unen con " / ".
        """
        perfiles: dict[int, str] = {}
        inicio = self._descargar(config.IPN_URL_PERFILES, {})

        for cve_nivel, nivel in self._opciones_select(inicio, "cveNivel"):
            pagina_nivel = self._enviar_formulario_perfiles({"cveNivel": cve_nivel})

            for cve_area, area in self._opciones_select(pagina_nivel, "cveArea"):
                pagina_area = self._enviar_formulario_perfiles(
                    {"cveNivel": cve_nivel, "cveArea": cve_area}
                )
                carreras = self._opciones_select(pagina_area, "cveProgEst")
                logger.info(
                    "Nivel %s / área %s: %d carreras", nivel, area, len(carreras)
                )

                for cve_carrera, carrera in carreras:
                    pagina_carrera = self._enviar_formulario_perfiles(
                        {
                            "cveNivel": cve_nivel,
                            "cveArea": cve_area,
                            "cveProgEst": cve_carrera,
                        }
                    )
                    coincidencia = re.search(r"cvePerfil=(\d+)", pagina_carrera)
                    if coincidencia is None:
                        # Sin enlaces a prestatarios: el perfil no tiene vacantes
                        logger.info("Carrera sin vacantes: %s", carrera)
                        continue
                    cve_perfil = int(coincidencia.group(1))
                    if cve_perfil in perfiles and carrera not in perfiles[cve_perfil]:
                        perfiles[cve_perfil] += f" / {carrera}"
                    else:
                        perfiles[cve_perfil] = carrera

        return perfiles

    def _extraer_claves_prestatarios(self, html: str) -> list[str]:
        """Extrae las claves de prestatario (`cvePrsttr`) de la lista de un perfil.

        Las claves se conservan como texto tal cual aparecen en el enlace:
        el portal tiene claves alfanuméricas (p. ej. "02124X02255") y con
        ceros a la izquierda que una conversión a entero corrompería.
        """
        soup = BeautifulSoup(html, "html.parser")
        claves: list[str] = []
        for enlace in soup.find_all("a", href=True):
            if "InfoServSocListaProgsActivi.do" not in enlace["href"]:
                continue
            parametros = parse_qs(urlparse(enlace["href"]).query)
            if "cvePrsttr" in parametros:
                claves.append(parametros["cvePrsttr"][0])
        return claves

    def iterar_lotes(self, completados: set[str]) -> Iterator[tuple[str, list[str]]]:
        """Descarga las páginas de programas perfil por perfil.

        Usa los perfiles de `config.PERFILES_IPN`; si está vacío, primero
        los descubre todos desde el portal y actualiza ese diccionario
        para que el parser pueda etiquetar el campo `carreras`. Cada
        perfil es un lote: su identificador es el `cvePerfil` como texto.

        Args:
            completados: Perfiles ya completados en una corrida anterior.
        """
        perfiles = dict(config.PERFILES_IPN)
        if not perfiles:
            logger.info("Sin perfiles configurados: descubriendo todos en el portal")
            perfiles = self._descubrir_perfiles()
            logger.info("Perfiles descubiertos: %d", len(perfiles))
            config.PERFILES_IPN.update(perfiles)

        for cve_omitido in config.PERFILES_IPN_OMITIR:
            if perfiles.pop(cve_omitido, None) is not None:
                logger.info("Perfil %d omitido por configuración", cve_omitido)

        for cve_perfil, carrera in perfiles.items():
            if str(cve_perfil) in completados:
                logger.info(
                    "Perfil %d ya completado en una corrida anterior; omitido",
                    cve_perfil,
                )
                continue

            logger.info("Perfil %d (%s): descargando prestatarios", cve_perfil, carrera)
            try:
                lista = self._descargar(
                    config.IPN_URL_PRESTATARIOS, {"cvePerfil": cve_perfil}
                )
            except requests.RequestException as error:
                # Un perfil fallido no debe abortar la corrida completa;
                # al no marcarse como completado, se reintentará al relanzar
                logger.warning(
                    "Perfil %d omitido por error de red: %s", cve_perfil, error
                )
                continue

            claves = self._extraer_claves_prestatarios(lista)
            logger.info(
                "Perfil %d: %d prestatarios encontrados", cve_perfil, len(claves)
            )

            yield str(cve_perfil), self._descargar_programas(cve_perfil, claves)

    def _descargar_programas(self, cve_perfil: int, claves: list[str]) -> list[str]:
        """Descarga en paralelo las páginas de programas de un perfil.

        Usa `config.HILOS_DESCARGA` hilos, cada uno con su propia sesión
        y su propia pausa entre peticiones; el orden de las claves se
        conserva en el resultado.
        """

        def descargar_uno(cve_prsttr: str) -> str | None:
            try:
                return self._descargar(
                    config.IPN_URL_PROGRAMAS,
                    {"cvePerfil": cve_perfil, "cvePrsttr": cve_prsttr},
                )
            except requests.RequestException as error:
                # Un prestatario fallido no debe abortar el perfil completo
                logger.warning(
                    "Prestatario %s omitido por error de red: %s", cve_prsttr, error
                )
                return None

        paginas: list[str] = []
        with ThreadPoolExecutor(max_workers=config.HILOS_DESCARGA) as pool:
            for indice, pagina in enumerate(pool.map(descargar_uno, claves), start=1):
                if pagina is not None:
                    paginas.append(pagina)
                if indice % 50 == 0:
                    logger.info(
                        "Perfil %d: %d/%d prestatarios descargados",
                        cve_perfil,
                        indice,
                        len(claves),
                    )
        return paginas


# Registro de scrapers disponibles. Para añadir una universidad nueva:
# 1. Crear su clase (subclase de ScraperBase) en este módulo.
# 2. Registrarla aquí y en `config.UNIVERSIDADES`.
SCRAPERS: dict[str, type[ScraperBase]] = {
    "ipn": ScraperIPN,
}


def obtener_scraper(universidad: str) -> ScraperBase:
    """Devuelve una instancia del scraper de la universidad indicada.

    Args:
        universidad: Identificador corto (por ejemplo, "ipn").

    Raises:
        KeyError: Si la universidad no está registrada.
    """
    if universidad not in SCRAPERS:
        disponibles = ", ".join(SCRAPERS)
        raise KeyError(
            f"Universidad '{universidad}' no soportada. Disponibles: {disponibles}"
        )
    return SCRAPERS[universidad]()
