"""Sincroniza los datos del scraper con el frontend.

Copia el archivo generado por el scraper:

    scraper/output/convocatorias.json

hacia la carpeta pública del frontend, donde Astro lo sirve como
archivo estático:

    web/public/data/convocatorias.json

Uso (desde la raíz del repositorio):

    python scripts/sync_data.py

Este script también lo ejecuta GitHub Actions (.github/workflows/scrape.yml)
después de cada corrida del scraper.
"""

import shutil
import sys
from pathlib import Path

# Raíz del repositorio (carpeta padre de scripts/)
RAIZ = Path(__file__).resolve().parent.parent

ORIGEN = RAIZ / "scraper" / "output" / "convocatorias.json"
DESTINO = RAIZ / "web" / "public" / "data" / "convocatorias.json"


def sincronizar() -> None:
    """Copia el JSON del scraper a la carpeta pública del frontend."""
    if not ORIGEN.exists():
        print(f"Error: no existe el archivo de origen: {ORIGEN}")
        sys.exit(1)

    # Asegura que la carpeta de destino exista antes de copiar
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ORIGEN, DESTINO)

    print(f"Sincronizado: {ORIGEN} -> {DESTINO}")


if __name__ == "__main__":
    sincronizar()
