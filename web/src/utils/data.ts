/**
 * Carga de datos de convocatorias.
 *
 * El sitio es 100 % estático: los datos se leen del archivo
 * `public/data/convocatorias.json` en tiempo de construcción (build),
 * no en el navegador. Cuando el scraper publica datos nuevos, el sitio
 * se reconstruye y los incorpora.
 */

import type { Convocatoria } from "../types/convocatoria";
// Importación estática: Vite incrusta el JSON al construir, de modo que la
// ruta se resuelve desde el código fuente y no desde el paquete generado
import datos from "../../public/data/convocatorias.json";

/** Lee y devuelve todas las convocatorias del archivo estático. */
export function obtenerConvocatorias(): Convocatoria[] {
  return datos as Convocatoria[];
}

/** Devuelve solo las convocatorias que ofrecen apoyo económico. */
export function obtenerConApoyo(): Convocatoria[] {
  return obtenerConvocatorias().filter((c) => c.apoyoEconomico);
}

/** Estadísticas básicas para la sección de números de la portada. */
export function obtenerEstadisticas(): {
  total: number;
  conApoyo: number;
  universidades: number;
} {
  const convocatorias = obtenerConvocatorias();
  const universidades = new Set(convocatorias.map((c) => c.universidadOrigen));
  return {
    total: convocatorias.length,
    conApoyo: convocatorias.filter((c) => c.apoyoEconomico).length,
    universidades: universidades.size,
  };
}
