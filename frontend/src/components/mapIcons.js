/**
 * mapIcons.js — Iconos SVG profesionales para Leaflet DivIcon markers.
 *
 * Cada función devuelve un HTML string SVG listo para usar en L.divIcon({ html }).
 * Los iconos tienen sombra, gradientes y se ven bien a cualquier zoom.
 *
 * Subtipos de ambulancias españolas:
 *   SVB  — Soporte Vital Básico (cruz verde)
 *   SVA  — Soporte Vital Avanzado / UCI móvil (cruz roja, borde dorado)
 *   VIR  — Vehículo Intervención Rápida (rayo, fondo azul)
 *   VAMM — Asistencia Médica Múltiple (multicruces, fondo naranja oscuro)
 *   SAMU — Servicio Atención Médica Urgente (corazón, fondo morado)
 */

// ── Colores por subtipo ───────────────────────────────────────────────
const SUBTYPE_COLORS = {
  SVB:  { top: "#22c55e", bot: "#15803d", stroke: "#fff" },      // verde
  SVA:  { top: "#ef4444", bot: "#991b1b", stroke: "#fbbf24" },   // rojo + borde dorado
  VIR:  { top: "#3b82f6", bot: "#1e40af", stroke: "#fff" },      // azul
  VAMM: { top: "#f97316", bot: "#c2410c", stroke: "#fff" },      // naranja
  SAMU: { top: "#a855f7", bot: "#7e22ce", stroke: "#fff" },      // morado
};

const SUBTYPE_LABELS = {
  SVB: "SVB", SVA: "SVA", VIR: "VIR", VAMM: "VAMM", SAMU: "SAMU",
};

// ── Ambulancia genérica por estado + subtipo ──────────────────────────
// status: "EN_ROUTE" | "IDLE" | "REFUELING" | other
export const vehicleIcon = (subtype = "SVB", status = "IDLE", size = 34) => {
  const pal = SUBTYPE_COLORS[subtype] || SUBTYPE_COLORS.SVB;
  const uid = `v-${subtype}-${status}`.toLowerCase();

  // Forma según estado
  const isRouting = status === "EN_ROUTE";
  const isRefueling = status === "REFUELING";

  // En ruta: rectángulo redondeado (más visible). Otros: círculo.
  const shape = isRouting
    ? `<rect x="2" y="2" width="36" height="36" rx="8" fill="url(#g-${uid})" filter="url(#s-${uid})" stroke="${pal.stroke}" stroke-width="1.5"/>`
    : `<circle cx="20" cy="20" r="17" fill="url(#g-${uid})" filter="url(#s-${uid})" stroke="${pal.stroke}" stroke-width="1.5"/>`;

  // Icono interior según subtipo
  let inner;
  if (isRefueling) {
    // Gota de combustible
    inner = `<path d="M20 10 C20 10 12 20 12 25 C12 29.4 15.6 33 20 33 C24.4 33 28 29.4 28 25 C28 20 20 10 20 10Z" fill="white" opacity="0.9"/>`;
  } else if (subtype === "VIR") {
    // Rayo (intervención rápida)
    inner = `<path d="M22 8 L15 21 H20 L18 32 L27 18 H22 Z" fill="white" opacity="0.95"/>`;
  } else if (subtype === "SAMU") {
    // Corazón
    inner = `<path d="M20 30 C14 24 10 20 10 16 C10 12.7 12.7 10 16 10 C18 10 19.5 11 20 12.5 C20.5 11 22 10 24 10 C27.3 10 30 12.7 30 16 C30 20 26 24 20 30Z" fill="white" opacity="0.95"/>`;
  } else if (subtype === "VAMM") {
    // Doble cruz (multicasualty)
    inner = `
      <rect x="13" y="16.5" width="14" height="7" rx="1" fill="white" opacity="0.95"/>
      <rect x="16.5" y="11.5" width="7" height="17" rx="1" fill="white" opacity="0.95"/>`;
  } else {
    // SVB / SVA — cruz médica clásica
    inner = `
      <rect x="17" y="10" width="6" height="20" rx="1.5" fill="white" opacity="0.95"/>
      <rect x="10" y="17" width="20" height="6" rx="1.5" fill="white" opacity="0.95"/>`;
  }

  // Label del subtipo (esquina inferior derecha, solo en ruta)
  const label = isRouting
    ? `<text x="35" y="36" text-anchor="end" font-size="7" font-weight="900" fill="white" font-family="Arial" opacity="0.85">${SUBTYPE_LABELS[subtype] || ""}</text>`
    : "";

  const animClass = isRouting ? "ambulance-en-route" : isRefueling ? "ambulance-refueling-anim" : "";

  return `
<div class="map-icon ${animClass}" style="width:${size}px;height:${size}px;">
  <svg viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <filter id="s-${uid}" x="-20%" y="-20%" width="140%" height="140%">
        <feDropShadow dx="0" dy="2" stdDeviation="2" flood-color="rgba(0,0,0,0.35)"/>
      </filter>
      <linearGradient id="g-${uid}" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="${pal.top}"/>
        <stop offset="100%" stop-color="${pal.bot}"/>
      </linearGradient>
    </defs>
    ${shape}
    ${inner}
    ${label}
  </svg>
</div>`;
};


// ── Helpers de compatibilidad (por si alguien importa las viejas) ─────
export const ambulanceEnRouteIcon = (size = 36) => vehicleIcon("SVB", "EN_ROUTE", size);
export const ambulanceIdleIcon = (size = 32) => vehicleIcon("SVB", "IDLE", size);
export const ambulanceBusyIcon = (size = 32) => vehicleIcon("SVB", "BUSY", size);
export const ambulanceRefuelingIcon = (size = 32) => vehicleIcon("SVB", "REFUELING", size);

// ── HOSPITAL — fondo blanco con cruz roja premium ─────────────────────
export const hospitalIcon = (size = 36) => `
<div class="map-icon hospital-icon" style="width:${size}px;height:${size}px;">
  <svg viewBox="0 0 44 44" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <filter id="shadow-hosp" x="-20%" y="-20%" width="140%" height="140%">
        <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="rgba(0,0,0,0.3)"/>
      </filter>
      <linearGradient id="grad-hosp" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#ffffff"/>
        <stop offset="100%" stop-color="#f1f5f9"/>
      </linearGradient>
    </defs>
    <rect x="2" y="2" width="40" height="40" rx="10" fill="url(#grad-hosp)" filter="url(#shadow-hosp)" stroke="#e2e8f0" stroke-width="1.5"/>
    <rect x="18.5" y="9" width="7" height="26" rx="2" fill="#dc2626"/>
    <rect x="9" y="18.5" width="26" height="7" rx="2" fill="#dc2626"/>
    <text x="22" y="40" text-anchor="middle" font-size="4" fill="#64748b" font-family="Arial" font-weight="bold">H</text>
  </svg>
</div>`;

// ── GASOLINERA — icono de surtidor profesional ────────────────────────
export const gasStationIcon = (size = 34) => `
<div class="map-icon gas-station-icon" style="width:${size}px;height:${size}px;">
  <svg viewBox="0 0 44 44" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <filter id="shadow-gas" x="-20%" y="-20%" width="140%" height="140%">
        <feDropShadow dx="0" dy="2" stdDeviation="2.5" flood-color="rgba(0,0,0,0.3)"/>
      </filter>
      <linearGradient id="grad-gas" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#fbbf24"/>
        <stop offset="100%" stop-color="#d97706"/>
      </linearGradient>
    </defs>
    <rect x="2" y="2" width="40" height="40" rx="10" fill="url(#grad-gas)" filter="url(#shadow-gas)" stroke="#92400e" stroke-width="1"/>
    <!-- Fuel pump body -->
    <rect x="10" y="12" width="16" height="20" rx="2" fill="white"/>
    <rect x="12" y="14" width="12" height="8" rx="1" fill="#1e293b"/>
    <!-- Nozzle -->
    <path d="M26 18 L32 14 L34 16 L30 22 L28 22 L26 18Z" fill="#1e293b"/>
    <circle cx="31" cy="14" r="2" fill="#1e293b"/>
    <!-- Fuel drop -->
    <path d="M18 26 C18 26 15.5 29.5 15.5 31 C15.5 32.4 16.6 33.5 18 33.5 C19.4 33.5 20.5 32.4 20.5 31 C20.5 29.5 18 26 18 26Z" fill="#3b82f6"/>
  </svg>
</div>`;

// ── INCIDENTE (marcador de pulso) ─────────────────────────────────────
export const incidentIcon = (severity = 3, status = "OPEN") => {
  const color = status === "ASSIGNED"
    ? { main: "#f59e0b", dark: "#b45309" }
    : severity >= 4
    ? { main: "#dc2626", dark: "#991b1b" }
    : severity >= 3
    ? { main: "#ef4444", dark: "#b91c1c" }
    : { main: "#f97316", dark: "#c2410c" };

  return `
<div class="map-icon incident-marker ${status === "ASSIGNED" ? "assigned" : ""}">
  <svg viewBox="0 0 40 48" xmlns="http://www.w3.org/2000/svg" style="width:34px;height:41px;">
    <defs>
      <filter id="shadow-inc-${severity}" x="-20%" y="-10%" width="140%" height="130%">
        <feDropShadow dx="0" dy="2" stdDeviation="2" flood-color="rgba(0,0,0,0.35)"/>
      </filter>
      <linearGradient id="grad-inc-${severity}" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="${color.main}"/>
        <stop offset="100%" stop-color="${color.dark}"/>
      </linearGradient>
    </defs>
    <path d="M20 46 C20 46 36 30 36 18 C36 9.2 28.8 2 20 2 C11.2 2 4 9.2 4 18 C4 30 20 46 20 46Z"
          fill="url(#grad-inc-${severity})" filter="url(#shadow-inc-${severity})" stroke="white" stroke-width="1.5"/>
    <circle cx="20" cy="18" r="8" fill="white" opacity="0.95"/>
    <text x="20" y="22" text-anchor="middle" font-size="12" font-weight="bold" fill="${color.main}" font-family="Arial">${severity}</text>
  </svg>
</div>`;
};
