# Web — ServicioSocialMX

Frontend estático construido con **Astro 5**, **TypeScript** y
**Tailwind CSS 4**. Consume los datos generados por el scraper desde
`public/data/convocatorias.json` (sin backend ni base de datos).

## Desarrollo

```bash
npm install
npm run dev       # http://localhost:4321
```

Otros comandos:

```bash
npm run build     # Genera el sitio estático en dist/
npm run preview   # Sirve dist/ localmente para revisarlo
```

## Estructura

```
web/
├── public/data/convocatorias.json  # Datos (copiados por scripts/sync_data.py)
├── src/
│   ├── components/   # Componentes reutilizables (Header, tarjetas, etc.)
│   ├── layouts/      # BaseLayout: head, tema claro/oscuro, header y footer
│   ├── pages/        # Rutas del sitio (index, convocatorias, acerca-de, 404)
│   ├── styles/       # global.css: Tailwind, tema y modo oscuro
│   ├── types/        # Tipos TS espejo del esquema compartido
│   └── utils/        # Carga de datos en tiempo de build
├── astro.config.mjs
└── tailwind.config.mjs
```

## Notas de diseño

- **Modo oscuro**: por clase `dark` en `<html>`; se alterna desde el botón
  del header y se persiste en `localStorage`.
- **Datos**: se leen en tiempo de build (`src/utils/data.ts`). Cuando el
  scraper publica datos nuevos, el sitio se reconstruye vía GitHub Actions.
- **Contrato de datos**: `src/types/convocatoria.ts` debe mantenerse
  sincronizado con `../shared/schemas/convocatoria.schema.json`.
- **GitHub Pages**: al desplegar bajo subruta, descomentar `site` y `base`
  en `astro.config.mjs`; los enlaces ya usan `import.meta.env.BASE_URL`.
