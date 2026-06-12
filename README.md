# ServicioSocialMX

Plataforma abierta que **centraliza convocatorias de servicio social** de
universidades mexicanas, destacando las que ofrecen **apoyo económico**.

## El problema

Las convocatorias de servicio social están dispersas en portales
universitarios poco amigables. Para un estudiante, saber qué programas
ofrecen apoyo económico implica revisar manualmente cientos de vacantes,
una por una. Esa información debería poder consultarse en segundos.

## Objetivo

Recolectar automáticamente las convocatorias de los portales oficiales,
normalizarlas en un formato común y publicarlas en un sitio web gratuito,
rápido y fácil de filtrar.

## Público objetivo

Estudiantes universitarios de México que deben realizar su servicio
social, empezando por la comunidad del **Instituto Politécnico Nacional
(IPN)**.

## Arquitectura

Filosofía: **coste cero**. Sin backend propio, sin bases de datos, sin
servicios de pago. Los datos viven en archivos JSON dentro del propio
repositorio y el sitio es 100 % estático.

```
┌─────────────────┐     ┌──────────────────────┐     ┌─────────────────────┐
│  GitHub Actions │ ──▶ │  scraper (Python)    │ ──▶ │ scraper/output/     │
│  (programado)   │     │  extrae y normaliza  │     │ convocatorias.json  │
└─────────────────┘     └──────────────────────┘     └──────────┬──────────┘
                                                                │
                                                    scripts/sync_data.py
                                                                │
┌─────────────────┐     ┌──────────────────────┐     ┌──────────▼──────────┐
│  GitHub Pages   │ ◀── │  web (Astro)         │ ◀── │ web/public/data/    │
│  (sitio público)│     │  build estático      │     │ convocatorias.json  │
└─────────────────┘     └──────────────────────┘     └─────────────────────┘
```

El contrato de datos entre ambos mundos es el esquema JSON de
`shared/schemas/convocatoria.schema.json`.

## Estructura del repositorio

| Carpeta    | Contenido                                                          |
| ---------- | ------------------------------------------------------------------ |
| `scraper/` | Scraper en Python (src layout). Extrae y exporta convocatorias.    |
| `web/`     | Frontend estático con Astro + TypeScript + Tailwind CSS.           |
| `shared/`  | Esquema JSON oficial: contrato entre scraper y frontend.           |
| `scripts/` | Utilidades del monorepo (sincronización de datos).                 |
| `.github/` | Workflows de scraping automático y despliegue en GitHub Pages.     |

## Tecnologías

- **Scraper**: Python 3.12, requests, BeautifulSoup, lxml (Playwright si
  hace falta JavaScript), pytest.
- **Frontend**: Astro 5, TypeScript, Tailwind CSS 4, modo claro/oscuro,
  diseño responsive.
- **Automatización**: GitHub Actions + GitHub Pages.

## Flujo de datos

1. GitHub Actions ejecuta el scraper de forma programada.
2. El scraper genera `scraper/output/convocatorias.json` (válido contra
   el esquema compartido).
3. `scripts/sync_data.py` copia ese archivo a
   `web/public/data/convocatorias.json`.
4. Si hay cambios, el workflow hace commit; ese push dispara el
   despliegue, que reconstruye el sitio con los datos nuevos.

## Cómo ejecutar el scraper

```bash
cd scraper
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m src.main
```

## Cómo iniciar el frontend

```bash
cd web
npm install
npm run dev      # http://localhost:4321
```

## Cómo sincronizar datos

```bash
# Desde la raíz del repositorio
python scripts/sync_data.py
```

## Cómo desplegar en GitHub Pages

1. En GitHub: **Settings → Pages → Source: GitHub Actions**.
2. En `web/astro.config.mjs`, descomentar y ajustar `site` y `base` con
   tu usuario y el nombre del repositorio.
3. Hacer push a `main`: el workflow `deploy.yml` construye y publica el
   sitio automáticamente.

## Roadmap

- **Fase 1 — IPN**: implementar el scraper del portal
  [serviciosocial.ipn.mx](https://serviciosocial.ipn.mx/) y publicar las
  primeras convocatorias reales.
- **Fase 2 — Más universidades**: integrar nuevas instituciones (UNAM,
  UAM, …) reutilizando la arquitectura modular del scraper.
- **Fase 3 — Alertas**: notificar a los estudiantes cuando aparezcan
  convocatorias nuevas que coincidan con su carrera.
- **Fase 4 — Crecimiento nacional**: recomendaciones personalizadas y
  cobertura de universidades de todo el país.

## Licencia

Publicado bajo la [licencia MIT](LICENSE).
