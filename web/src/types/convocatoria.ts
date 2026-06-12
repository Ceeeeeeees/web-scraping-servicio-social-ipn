/**
 * Tipos del dominio de ServicioSocialMX.
 *
 * Este archivo es la versión TypeScript del esquema compartido:
 *   shared/schemas/convocatoria.schema.json
 *
 * Si el esquema cambia, este tipo debe actualizarse a la par: es el
 * contrato oficial entre el scraper (Python) y el frontend (Astro).
 */

/** Modalidad en que se realiza el servicio social. */
export type Modalidad = "presencial" | "remota" | "hibrida" | "no-especificada";

/** Estado actual de una convocatoria. */
export type EstadoConvocatoria = "abierta" | "cerrada" | "proxima";

/** Una convocatoria de servicio social, tal como la genera el scraper. */
export interface Convocatoria {
  /** Identificador único y estable: "<universidadOrigen>-<slug-del-titulo>". */
  id: string;
  /** Nombre del programa tal como aparece en el portal de origen. */
  titulo: string;
  /** Descripción de las actividades a realizar. */
  descripcion?: string;
  /** Dependencia u organismo que ofrece la convocatoria. */
  institucion: string;
  /** Delegación o municipio donde se realiza, o null si no se especifica. */
  ubicacion?: string | null;
  /** Domicilio completo del prestatario (para enlaces a mapas), o null. */
  direccion?: string | null;
  /** Universidad de cuyo portal proviene (ej. "ipn"). */
  universidadOrigen: string;
  /** Carreras a las que aplica; arreglo vacío si aplica a todas. */
  carreras?: string[];
  /** Si ofrece apoyo económico (campo clave del proyecto). */
  apoyoEconomico: boolean;
  /** Monto mensual en MXN, o null si no aplica o no se especifica. */
  monto?: number | null;
  /** Modalidad del servicio social. */
  modalidad?: Modalidad;
  /** Fecha de publicación en formato ISO 8601 (AAAA-MM-DD). */
  fechaPublicacion?: string | null;
  /** Fecha límite de registro en formato ISO 8601 (AAAA-MM-DD). */
  fechaLimite?: string | null;
  /** Enlace a la convocatoria original. */
  url: string;
  /** Estado actual de la convocatoria. */
  estado: EstadoConvocatoria;
}
