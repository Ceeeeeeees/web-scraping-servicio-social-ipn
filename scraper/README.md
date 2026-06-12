# Scraper — ServicioSocialMX

Extrae convocatorias de servicio social de portales universitarios y las
exporta a `output/convocatorias.json`, el contrato de datos con el frontend
(definido en `../shared/schemas/convocatoria.schema.json`).

## Estructura

```
scraper/
├── src/
│   ├── main.py       # Punto de entrada; orquesta el flujo completo
│   ├── config.py     # Rutas, constantes y registro de universidades
│   ├── scraper.py    # Descarga de páginas (una clase por universidad)
│   ├── parser.py     # HTML crudo → convocatorias normalizadas
│   ├── exporter.py   # Validación y escritura del JSON final
│   └── utils.py      # Logging y helpers
├── output/           # JSON generado (convocatorias.json)
├── logs/             # Logs de ejecución (un archivo por día)
├── tests/            # Pruebas con pytest
└── requirements.txt
```

## Uso

```bash
# Desde la carpeta scraper/
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Ejecutar el scraper
python -m src.main

# Ejecutar las pruebas
pytest
```

## Cómo funciona el scraper del IPN

El portal https://serviciosocial.ipn.mx/ organiza las vacantes por
"perfil" (`cvePerfil`), que corresponde a una combinación de nivel,
área y carrera. El scraper:

1. **Descubre los perfiles**: recorre el formulario en cascada
   nivel → área → carrera de `InfoServSocListaPerfiles.do` y obtiene el
   `cvePerfil` de cada carrera. Si `config.PERFILES_IPN` tiene entradas
   manuales, se usa ese subconjunto y se omite el descubrimiento.
2. **Lista los prestatarios** de cada perfil
   (`InfoServSocListaPrsttrPerf.do?cvePerfil=<n>`).
3. **Descarga las actividades** de cada prestatario
   (`InfoServSocListaProgsActivi.do?cvePerfil=<n>&cvePrsttr=<m>`); cada
   actividad se normaliza como una convocatoria.

La misma actividad puede aparecer en varios perfiles; los duplicados se
fusionan por `id` uniendo sus carreras. El campo `apoyoEconomico` se
deduce del bloque "Apoyos" (presencia de "BECA") y `monto` del texto
"Monto del Apoyo $ …" cuando lo especifica.

Las páginas de prestatarios se descargan en paralelo con
`config.HILOS_DESCARGA` hilos (cada uno con su propia sesión y su pausa
`config.PAUSA_ENTRE_PETICIONES`); el ritmo global queda en ~1–1.5
peticiones/segundo para no presionar al servidor ni a su WAF. Con
`HILOS_DESCARGA = 1` se vuelve al modo secuencial.

### Exportación incremental y reanudación

El avance se exporta a `output/convocatorias.json` **al terminar cada
perfil**, y los perfiles completados se registran en
`output/avance.json`. Si la corrida se interrumpe (Ctrl+C, error de
red), basta con relanzar `python -m src.main`: los perfiles ya
completados se omiten y sus convocatorias se conservan. Al terminar una
corrida completa, `avance.json` se borra para que la siguiente parta de
cero.

> Nota: recorrer **todos** los perfiles implica miles de peticiones
> (puede tardar horas incluso con hilos). Para una ejecución acotada,
> registrar solo los perfiles de interés en `config.PERFILES_IPN`, o
> excluir los ya scrapeados con `config.PERFILES_IPN_OMITIR` (sus
> convocatorias previas se conservan en el JSON exportado).

## Añadir una universidad

1. Registrarla en `config.UNIVERSIDADES`.
2. Crear su clase scraper en `scraper.py` (subclase de `ScraperBase`)
   y registrarla en `SCRAPERS`.
3. Crear su función de parseo en `parser.py` y registrarla en `PARSERS`.
4. Añadir pruebas en `tests/`.

El resultado de todas las universidades se consolida en un único
`output/convocatorias.json`.
