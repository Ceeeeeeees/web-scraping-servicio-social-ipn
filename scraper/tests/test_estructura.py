"""Pruebas básicas de la estructura del scraper.

Verifican que los módulos se importan correctamente y que el registro
de universidades es consistente. Sirven como punto de partida para las
pruebas reales cuando se implemente el scraping.
"""

from src import config, scraper
from src.parser import PARSERS


def test_universidades_tienen_scraper_y_parser() -> None:
    """Cada universidad registrada debe tener scraper y parser asociados."""
    for universidad in config.UNIVERSIDADES:
        assert universidad in scraper.SCRAPERS
        assert universidad in PARSERS


def test_obtener_scraper_desconocido_falla() -> None:
    """Pedir un scraper no registrado debe lanzar KeyError."""
    try:
        scraper.obtener_scraper("universidad-inexistente")
    except KeyError:
        pass
    else:
        raise AssertionError("Se esperaba KeyError")
