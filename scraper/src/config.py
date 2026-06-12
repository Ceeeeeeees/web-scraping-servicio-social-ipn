"""Configuración central del scraper.

Aquí se definen rutas, constantes y el registro de universidades
soportadas. Para añadir una nueva universidad basta con agregar una
entrada a `UNIVERSIDADES` y crear su scraper correspondiente en
`scraper.py`.
"""

from pathlib import Path

# --- Rutas del proyecto -------------------------------------------------

# Raíz del paquete scraper (carpeta `scraper/`)
RUTA_SCRAPER = Path(__file__).resolve().parent.parent

# Carpeta donde se escriben los JSON generados
RUTA_SALIDA = RUTA_SCRAPER / "output"

# Archivo principal de salida (contrato con el frontend)
ARCHIVO_CONVOCATORIAS = RUTA_SALIDA / "convocatorias.json"

# Avance de la corrida en curso (lotes/perfiles ya completados). Permite
# reanudar una corrida interrumpida sin repetir lo descargado; se borra
# automáticamente al terminar una corrida completa.
ARCHIVO_AVANCE = RUTA_SALIDA / "avance.json"

# Carpeta de logs de ejecución
RUTA_LOGS = RUTA_SCRAPER / "logs"

# Esquema compartido con el frontend (contrato oficial de datos)
RUTA_ESQUEMA = RUTA_SCRAPER.parent / "shared" / "schemas" / "convocatoria.schema.json"

# --- Parámetros de red ---------------------------------------------------

# User-Agent identificable para hacer scraping responsable
USER_AGENT = "ServicioSocialMX/0.1 (proyecto estudiantil sin fines de lucro)"

# Tiempo máximo de espera por petición, en segundos. El portal del IPN
# se pone lento cuando está cargado; con menos de 15 s aparecen falsos
# timeouts.
TIMEOUT_SEGUNDOS = 15

# Pausa entre peticiones POR HILO, en segundos. El ritmo global contra el
# servidor es aproximadamente HILOS_DESCARGA / (PAUSA_ENTRE_PETICIONES +
# latencia); con 4 hilos y pausa de 1.5 s queda en ~1.3 peticiones/segundo,
# suficiente para no llamar la atención del WAF del portal del IPN.
PAUSA_ENTRE_PETICIONES = 1

# Hilos para descargar páginas de prestatarios en paralelo. Con 1 se
# vuelve al comportamiento secuencial. No subir mucho: con 8 hilos el
# portal empieza a responder con timeouts.
HILOS_DESCARGA = 6

# --- Registro de universidades -------------------------------------------

# Cada universidad soportada se registra aquí. La clave es un
# identificador corto que también se usa en el campo `universidadOrigen`
# del esquema compartido (shared/schemas/convocatoria.schema.json).
UNIVERSIDADES: dict[str, dict[str, str]] = {
    "ipn": {
        "nombre": "Instituto Politécnico Nacional",
        "url_base": "https://serviciosocial.ipn.mx/",
    },
    # Fase 2: añadir más universidades, por ejemplo:
    # "unam": {
    #     "nombre": "Universidad Nacional Autónoma de México",
    #     "url_base": "https://www.dgoserver.unam.mx/",
    # },
}

# --- Portal del IPN -------------------------------------------------------

# El portal del IPN (struts) expone las vacantes por "perfil" (combinación
# de nivel, área y carrera). Las páginas funcionan sin sesión:
#   - Formulario en cascada nivel → área → carrera: InfoServSocListaPerfiles.do
#   - Lista de prestatarios de un perfil: ?cvePerfil=<n>
#   - Programas/actividades de un prestatario: ?cvePerfil=<n>&cvePrsttr=<m>
IPN_URL_PERFILES = (
    "https://serviciosocial.ipn.mx/infoServSoc/InfoServSocListaPerfiles.do"
)
IPN_URL_PRESTATARIOS = (
    "https://serviciosocial.ipn.mx/infoServSoc/InfoServSocListaPrsttrPerf.do"
)
IPN_URL_PROGRAMAS = (
    "https://serviciosocial.ipn.mx/infoServSoc/InfoServSocListaProgsActivi.do"
)

# Perfiles del IPN a scrapear. La clave es el `cvePerfil` del portal y el
# valor, el nombre de la carrera (se usa en el campo `carreras` del esquema).
#
# Si el diccionario se deja VACÍO, el scraper descubre automáticamente
# todos los perfiles del portal recorriendo el formulario en cascada
# (nivel → área → carrera) y rellena este diccionario en tiempo de
# ejecución. Para limitar el scraping a ciertas carreras, registrarlas
# manualmente, por ejemplo:
#
#     PERFILES_IPN = {36: "ESCOM INGENIERÍA EN SISTEMAS COMPUTACIONALES"}
#
PERFILES_IPN: dict[int, str] = {}

# Perfiles a OMITIR en esta corrida (por ejemplo, ya scrapeados en una
# corrida anterior). Sus convocatorias previas en output/convocatorias.json
# se conservan al exportar, de modo que el resultado final queda completo.
# Ejemplo para recorrer todo el portal menos el perfil 36:
#
#     PERFILES_IPN = {}
#     PERFILES_IPN_OMITIR = {36}
#
PERFILES_IPN_OMITIR: set[int] = set()
