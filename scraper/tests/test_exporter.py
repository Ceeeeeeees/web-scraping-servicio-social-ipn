"""Pruebas del exportador (carga, exportación, consolidación y avance)."""

from pathlib import Path

from src.exporter import (
    cargar_avance,
    cargar_convocatorias,
    exportar_json,
    guardar_avance,
    limpiar_avance,
)


def test_cargar_sin_archivo_devuelve_lista_vacia(tmp_path: Path) -> None:
    """Si nunca se ha exportado, la carga debe devolver una lista vacía."""
    assert cargar_convocatorias(tmp_path / "no-existe.json") == []


def test_exportar_y_cargar_ida_y_vuelta(tmp_path: Path) -> None:
    """Lo exportado debe poder recargarse sin pérdidas."""
    datos = [
        {
            "id": "ipn-1-x",
            "titulo": "Actividad X",
            "url": "https://ejemplo.mx?cvePerfil=36&cvePrsttr=1",
        }
    ]
    ruta = tmp_path / "convocatorias.json"

    exportar_json(datos, ruta)

    assert cargar_convocatorias(ruta) == datos


def test_avance_ciclo_completo(tmp_path: Path) -> None:
    """El avance debe poder guardarse, recargarse y limpiarse."""
    ruta = tmp_path / "avance.json"

    assert cargar_avance(ruta) == {}

    avance = {"ipn": ["36", "46"]}
    guardar_avance(avance, ruta)
    assert cargar_avance(ruta) == avance

    limpiar_avance(ruta)
    assert not ruta.exists()
    # Limpiar sin archivo no debe fallar
    limpiar_avance(ruta)
