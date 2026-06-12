"""Punto de entrada del scraper de ServicioSocialMX.

Orquesta el flujo completo con exportación incremental:

    1. Para cada universidad registrada, descargar sus páginas por
       lotes (scraper.py); en el IPN, un lote = un perfil.
    2. Parsear cada lote a convocatorias normalizadas (parser.py).
    3. Tras cada lote, consolidar, validar y exportar el avance a
       output/convocatorias.json, y registrar el lote en
       output/avance.json.

Si la corrida se interrumpe (Ctrl+C, error de red, etc.), basta con
relanzarla: los lotes registrados en el avance se omiten y sus
convocatorias se conservan del archivo ya exportado. Al terminar una
corrida completa, el avance se borra para que la siguiente parta de cero.

Ejecución (desde la carpeta `scraper/`):

    python -m src.main
"""

import logging

from . import config, exporter, scraper, utils
from .parser import PARSERS, Convocatoria


def _cargar_conservadas(avance: dict[str, list[str]]) -> list[Convocatoria]:
    """Recupera del archivo exportado las convocatorias que no se re-scrapearán.

    Son las de los perfiles omitidos por configuración y las de los lotes
    completados en una corrida anterior interrumpida; se identifican por
    el `cvePerfil` de su URL.

    Args:
        avance: Avance cargado de `output/avance.json`.
    """
    perfiles_conservados = {str(cve) for cve in config.PERFILES_IPN_OMITIR}
    perfiles_conservados.update(avance.get("ipn", []))
    if not perfiles_conservados:
        return []

    marcas = {f"cvePerfil={cve}&" for cve in perfiles_conservados}
    return [
        previa
        for previa in exporter.cargar_convocatorias()
        if any(marca in previa["url"] for marca in marcas)
    ]


def _exportar_avance(
    convocatorias: list[Convocatoria],
    avance: dict[str, list[str]],
    logger: logging.Logger,
) -> None:
    """Consolida, valida y exporta el estado actual, registrando el avance."""
    consolidadas = exporter.consolidar_convocatorias(convocatorias)
    if not exporter.validar_convocatorias(consolidadas):
        logger.error("La validación falló; no se exportó este avance")
        return
    exporter.exportar_json(consolidadas)
    exporter.guardar_avance(avance)
    logger.info("Avance exportado: %d convocatorias", len(consolidadas))


def ejecutar() -> None:
    """Ejecuta el flujo completo del scraper para todas las universidades."""
    logger = utils.configurar_logging()
    logger.info("Iniciando scraper de ServicioSocialMX")

    avance = exporter.cargar_avance()
    conservadas = _cargar_conservadas(avance)
    if conservadas:
        logger.info(
            "Conservadas %d convocatorias de perfiles omitidos o ya completados",
            len(conservadas),
        )

    convocatorias: list[Convocatoria] = []

    for universidad in config.UNIVERSIDADES:
        logger.info("Procesando universidad: %s", universidad)

        completados = set(avance.get(universidad, []))
        if completados:
            logger.info(
                "Reanudando corrida interrumpida: %d lotes ya completados",
                len(completados),
            )

        instancia = scraper.obtener_scraper(universidad)
        parsear = PARSERS[universidad]

        for lote, paginas in instancia.iterar_lotes(completados):
            for html in paginas:
                convocatorias.extend(parsear(html))
            completados.add(lote)
            avance[universidad] = sorted(completados)
            # Las nuevas van primero: en duplicados gana lo recién scrapeado
            _exportar_avance(convocatorias + conservadas, avance, logger)

    # Corrida completa: borrar el avance para que la próxima parta de cero
    exporter.limpiar_avance()
    logger.info("Scraper finalizado")


if __name__ == "__main__":
    ejecutar()
