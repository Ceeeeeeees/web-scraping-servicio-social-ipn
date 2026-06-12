// @ts-check
import { defineConfig } from "astro/config";
import tailwindcss from "@tailwindcss/vite";

// Configuración de Astro
// Documentación: https://docs.astro.build/es/reference/configuration-reference/
export default defineConfig({
  // Despliegue en GitHub Pages: el sitio queda publicado en
  // https://ceeeeeeees.github.io/web-scraping-servicio-social-ipn/
  // El código ya usa import.meta.env.BASE_URL en los enlaces y en la carga
  // de datos, por lo que no hay que cambiar nada más.
  site: "https://ceeeeeeees.github.io",
  base: "/web-scraping-servicio-social-ipn",

  vite: {
    // Tailwind CSS v4 se integra como plugin de Vite (forma recomendada en Astro 5)
    plugins: [tailwindcss()],
  },
});
