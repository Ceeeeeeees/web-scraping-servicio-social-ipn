/**
 * Utilidades para categorizar las carreras del IPN por nivel, escuela y área.
 */

import type { Convocatoria } from "../types/convocatoria";

export interface CarreraInfo {
  nombreOriginal: string;
  nivel: "medio-superior" | "superior";
  escuela: string;
}

/**
 * Categoriza una cadena de texto de carrera del IPN en nivel, escuela y área.
 */
export function categorizarCarrera(carrera: string): CarreraInfo {
  const nombreUpper = carrera.trim().toUpperCase();

  // 1. Detectar Nivel
  let nivel: "medio-superior" | "superior" = "superior";
  const isCecytOrCet = nombreUpper.includes("CECYT") || nombreUpper.includes("CET ");
  const isRvoe = nombreUpper.includes("RVOE");
  const isEnba = nombreUpper.includes("ENBA") || nombreUpper.includes("E.N.B.A.");

  if (isCecytOrCet) {
    nivel = "medio-superior";
  } else if (isRvoe) {
    if (nombreUpper.includes("TÉCNICO") || nombreUpper.includes("TECNICO")) {
      nivel = "medio-superior";
    } else if (nombreUpper.includes("LICENCIATURA")) {
      nivel = "superior";
    } else {
      nivel = "superior";
    }
  } else if (isEnba) {
    if (nombreUpper.includes("PROFESIONAL")) {
      nivel = "medio-superior";
    } else if (nombreUpper.includes("LICENCIATURA")) {
      nivel = "superior";
    } else {
      nivel = "superior";
    }
  } else {
    nivel = "superior";
  }

  // 2. Detectar Escuela
  let escuela = "OTRA";
  const palabras = nombreUpper.split(/\s+/);
  if (palabras.length >= 2) {
    const primerPar = `${palabras[0]} ${palabras[1]}`;
    if (
      primerPar.startsWith("ESIME") ||
      primerPar.startsWith("ESCA") ||
      primerPar.startsWith("ESIA") ||
      primerPar.startsWith("CICS") ||
      primerPar.startsWith("CECYT") ||
      primerPar.startsWith("CET")
    ) {
      escuela = primerPar;
    } else {
      escuela = palabras[0];
    }
  } else if (palabras.length > 0) {
    escuela = palabras[0];
  }

  // Normalizar nombres
  escuela = escuela.trim();

  return {
    nombreOriginal: carrera.trim(),
    nivel,
    escuela
  };
}

/**
 * Elimina emojis y caracteres pictográficos del texto para mantener la interfaz limpia.
 */
export function eliminarEmojis(texto: string | undefined | null): string {
  if (!texto) return "";
  return texto
    .replace(/[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{2600}-\u{27BF}\u{1F1E6}-\u{1F1FF}\u{1F900}-\u{1F9FF}\u{1FA00}-\u{1FAFF}\u{2700}-\u{27BF}\u{1F300}-\u{1F9FF}\u{1F1E0}-\u{1F1FF}]/gu, "")
    .replace(/\s+/g, " ")
    .trim();
}

/**
 * Heurística para detectar la ubicación (Estado de la República) de la institución
 * basándose en el nombre de la institución y la descripción del programa.
 */
export function detectarUbicacion(institucion: string, descripcion?: string): string {
  const texto = `${institucion} ${descripcion || ""}`.toUpperCase();

  if (
    texto.includes("ZACATECAS") ||
    texto.includes("UPIIZ")
  ) {
    return "Zacatecas";
  }
  if (
    texto.includes("HIDALGO") ||
    texto.includes("PACHUCA") ||
    texto.includes("UPIIH")
  ) {
    return "Hidalgo";
  }
  if (
    texto.includes("GUANAJUATO") ||
    texto.includes("SILAO") ||
    texto.includes("UPIIG")
  ) {
    return "Guanajuato";
  }
  if (
    texto.includes("QUERETARO") ||
    texto.includes("QUERÉTARO")
  ) {
    return "Querétaro";
  }
  if (
    texto.includes("CHIHUAHUA")
  ) {
    return "Chihuahua";
  }
  if (
    texto.includes("JALISCO") ||
    texto.includes("GUADALAJARA")
  ) {
    return "Jalisco";
  }
  if (
    texto.includes("NUEVO LEON") ||
    texto.includes("NUEVO LEÓN") ||
    texto.includes("MONTERREY")
  ) {
    return "Nuevo León";
  }
  if (
    texto.includes("ESTADO DE MÉXICO") ||
    texto.includes("ESTADO DE MEXICO") ||
    texto.includes("EDOMEX") ||
    texto.includes("TOLUCA") ||
    texto.includes("TLALNEPANTLA") ||
    texto.includes("ECATEPEC") ||
    texto.includes("NAUCALPAN") ||
    texto.includes("NEZAHUALCOYOTL") ||
    texto.includes("CHIMALHUACAN") ||
    texto.includes("TEXCOCO") ||
    texto.includes("METEPEC") ||
    texto.includes("ATIZAPAN") ||
    texto.includes("CUAUTITLAN") ||
    texto.includes("COACALCO") ||
    texto.includes("TULTITLAN") ||
    texto.includes("CHALCO") ||
    texto.includes("IXTAPALUCA")
  ) {
    return "Estado de México";
  }

  // Por defecto la gran mayoría de prestatarios en el portal del IPN están en CDMX
  return "CDMX";
}

/** Quita acentos, colapsa espacios y pasa a mayúsculas. */
function sinAcentos(texto: string): string {
  return texto
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/\s+/g, " ")
    .trim()
    .toUpperCase();
}

/**
 * Erratas y variantes del portal → nombre canónico (con acentos).
 * Las claves están en la forma ya normalizada (mayúsculas, sin acentos,
 * sin prefijo de alcaldía/municipio).
 */
const ALIAS_UBICACION: Record<string, string> = {
  // CDMX
  "ALVARO OBREGON": "ÁLVARO OBREGÓN",
  "AZCAPTZALCO": "AZCAPOTZALCO",
  "BENITO JUAREZ": "BENITO JUÁREZ",
  "COYOACAN": "COYOACÁN",
  "COYOCAN": "COYOACÁN",
  "CUAHUTEMOC": "CUAUHTÉMOC",
  "CUAUHTEMOC": "CUAUHTÉMOC",
  "CUUHTEMOC": "CUAUHTÉMOC",
  "CUAJIMALPA DE MORELOS": "CUAJIMALPA",
  "G A M": "GUSTAVO A. MADERO",
  "G. A. MADERO": "GUSTAVO A. MADERO",
  "G.A. MADERO": "GUSTAVO A. MADERO",
  "G.A. MDADERO": "GUSTAVO A. MADERO",
  "G.A.M": "GUSTAVO A. MADERO",
  "G.A.M.": "GUSTAVO A. MADERO",
  "GAM": "GUSTAVO A. MADERO",
  "GUSTAVO A MADERO": "GUSTAVO A. MADERO",
  "GUSTAVO A. MADERO.": "GUSTAVO A. MADERO",
  "GUSTAVO A.MADERO": "GUSTAVO A. MADERO",
  "GUSTAVO MADERO": "GUSTAVO A. MADERO",
  "GUSTAVO. A. MADERO": "GUSTAVO A. MADERO",
  "CIUDAD DE MEXICO": "CDMX",
  "MEXICO CITY": "CDMX",
  "MEXICO DF": "CDMX",
  "NARVARTE": "BENITO JUÁREZ", // colonia de la alcaldía Benito Juárez
  "TLAHUAC": "TLÁHUAC",
  // Estado de México
  "ATIZAPAN DE ZARAGOZA": "ATIZAPÁN DE ZARAGOZA",
  "COACALCO DE BERRIOZABAL": "COACALCO",
  "ECATEPEC DE MORELOS": "ECATEPEC",
  "NAUCALPAN DE JUAREZ": "NAUCALPAN",
  "NEZAHUALCOYOTL": "NEZAHUALCÓYOTL",
  "NICOLAS ROMERO": "NICOLÁS ROMERO",
  "TECAMAC": "TECÁMAC",
  "TEPOTZOTLAN": "TEPOTZOTLÁN",
  "TLALNEPANTLA DE BAZ": "TLALNEPANTLA",
  "TULTITLAN DE MARIANO ESCOBEDO": "TULTITLÁN",
  "VALLE DE CHALCO SOLIDARIDAD": "VALLE DE CHALCO",
  // Otros estados
  "CATAZAJA CHIAPAS": "CATAZAJÁ",
  "LEON": "LEÓN",
  "MERIDA": "MÉRIDA",
  "PALENQUE CHIAPAS": "PALENQUE",
  "QUERETARO": "QUERÉTARO",
  "SANTIAGO DE QUERETARO": "QUERÉTARO",
  "SILAO DE LA VICTORIA": "SILAO",
};

/**
 * Normaliza una ubicación para comparar y filtrar: mayúsculas, sin espacios
 * repetidos ni prefijos de demarcación, y con las erratas y variantes del
 * portal ("CUAHUTEMOC", "G.A.M.", "TLALNEPANTLA DE BAZ"...) unificadas en
 * un solo nombre canónico.
 */
export function normalizarUbicacion(texto: string): string {
  const base = sinAcentos(texto).replace(
    /^(?:ALCALDIA|DELEGACION|ALC\.|DEL\.|MUNICIPIO DE)\s+/,
    ""
  );
  return ALIAS_UBICACION[base] ?? base;
}

/** Alcaldías de la CDMX presentes en el portal (sin acentos, para comparar). */
const ALCALDIAS_CDMX = new Set([
  "ALVARO OBREGON",
  "AZCAPOTZALCO",
  "BENITO JUAREZ",
  "COYOACAN",
  "CUAJIMALPA",
  "CUAUHTEMOC",
  "GUSTAVO A. MADERO",
  "IZTACALCO",
  "IZTAPALAPA",
  "MAGDALENA CONTRERAS",
  "MIGUEL HIDALGO",
  "MILPA ALTA",
  "TLAHUAC",
  "TLALPAN",
  "VENUSTIANO CARRANZA",
  "XOCHIMILCO",
]);

/** Municipios del Estado de México presentes en el portal (sin acentos). */
const MUNICIPIOS_EDOMEX = new Set([
  "ATENCO",
  "ATIZAPAN DE ZARAGOZA",
  "CHALCO",
  "COACALCO",
  "CUAUTITLAN",
  "CUAUTITLAN IZCALLI",
  "ECATEPEC",
  "HUIXQUILUCAN",
  "IXTAPALUCA",
  "LA PAZ",
  "METEPEC",
  "NAUCALPAN",
  "NEXTLALPAN",
  "NEZAHUALCOYOTL",
  "NICOLAS ROMERO",
  "SAN MARTIN DE LAS PIRAMIDES",
  "TECAMAC",
  "TEMAMATLA",
  "TEMOAYA",
  "TEOLOYUCAN",
  "TEPOTZOTLAN",
  "TEXCOCO",
  "TLALNEPANTLA",
  "TOLUCA",
  "TULTEPEC",
  "TULTITLAN",
  "VALLE DE CHALCO",
  "ZUMPANGO",
]);

export type Entidad = "CDMX" | "EDOMEX" | "OTRA";

/**
 * Entidad a la que pertenece una ubicación ya normalizada, para agrupar el
 * filtro y permitir el filtrado en cascada ("Toda la CDMX" incluye todas
 * sus alcaldías). Lo que no es CDMX ni Estado de México se agrupa en "OTRA".
 */
export function entidadDeUbicacion(ubicacion: string): Entidad {
  const clave = sinAcentos(ubicacion);
  if (clave === "CDMX" || ALCALDIAS_CDMX.has(clave)) return "CDMX";
  if (clave === "ESTADO DE MEXICO" || MUNICIPIOS_EDOMEX.has(clave)) {
    return "EDOMEX";
  }
  return "OTRA";
}

/**
 * Ubicación canónica (normalizada) de una convocatoria.
 *
 * Usa el dato real extraído por el scraper (`ubicacion`) y, para las
 * convocatorias que aún no lo traen, cae en la heurística por texto.
 * Es la única fuente que deben usar tanto el panel de filtros como las
 * tarjetas, para que los valores coincidan al filtrar.
 */
export function ubicacionDeConvocatoria(convocatoria: Convocatoria): string {
  if (convocatoria.ubicacion) {
    return normalizarUbicacion(convocatoria.ubicacion);
  }
  return normalizarUbicacion(
    detectarUbicacion(convocatoria.institucion, convocatoria.descripcion)
  );
}

/**
 * Versión legible de una ubicación normalizada ("GUSTAVO A. MADERO" →
 * "Gustavo A. Madero"), preservando siglas conocidas.
 */
export function formatearUbicacion(ubicacion: string): string {
  if (ubicacion === "CDMX") return "CDMX";
  return ubicacion
    .toLowerCase()
    .replace(/(^|[\s.])\p{L}/gu, (letra) => letra.toUpperCase());
}

/**
 * Convierte un título en mayúsculas a formato de oración (Sentence Case),
 * preservando las siglas conocidas en mayúsculas.
 */
export function formatearTitulo(titulo: string): string {
  if (!titulo) return "";

  // Si el título no está completamente en mayúsculas, lo dejamos intacto
  if (titulo !== titulo.toUpperCase()) {
    return titulo;
  }

  // Convertir a minúsculas y capitalizar la primera letra
  const minusculas = titulo.toLowerCase();
  let resultado = minusculas.charAt(0).toUpperCase() + minusculas.slice(1);

  // Restaurar siglas conocidas en mayúsculas
  const siglas = [
    "IPN", "YMCA", "CFE", "ADIP", "SCT", "SEMARNAT", "CINVESTAV",
    "ESCOM", "UPIITA", "ESIME", "ESFM", "ENCB", "CICS", "ISSSTE",
    "IMSS", "SAT", "UNAM", "UAM", "CFENERGÍA"
  ];

  siglas.forEach((sigla) => {
    const regex = new RegExp(`\\b${sigla}\\b`, "gi");
    resultado = resultado.replace(regex, sigla);
  });

  return resultado;
}
