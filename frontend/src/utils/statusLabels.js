/**
 * Centralized Spanish labels for all status codes across the app.
 */

// Vehicle statuses
export const VEHICLE_STATUS_LABELS = {
  IDLE: "Disponible",
  EN_ROUTE: "En Ruta",
  ON_SCENE: "En Escena",
  RETURNING: "Retornando",
  MAINTENANCE: "Mantenimiento",
  REFUELING: "Repostando",
  ASSIGNED: "Asignado",
  OFFLINE: "Fuera de servicio",
};

// Incident statuses
export const INCIDENT_STATUS_LABELS = {
  OPEN: "Abierto",
  ASSIGNED: "Asignado",
  EN_ROUTE: "En Ruta",
  ON_SCENE: "En Escena",
  RESOLVED: "Resuelto",
  CLOSED: "Cerrado",
  CANCELLED: "Cancelado",
};

// Combined fallback — works for any status code
export const STATUS_LABELS = {
  ...VEHICLE_STATUS_LABELS,
  ...INCIDENT_STATUS_LABELS,
};

/**
 * Get a Spanish label for any status code. Falls back to the raw code.
 */
export function statusLabel(code) {
  if (!code) return "—";
  return STATUS_LABELS[code.toUpperCase()] || code;
}

// Vehicle status colors
export const VEHICLE_STATUS_COLORS = {
  IDLE: "#22c55e",
  EN_ROUTE: "#3b82f6",
  ON_SCENE: "#f59e0b",
  RETURNING: "#8b5cf6",
  MAINTENANCE: "#6b7280",
  REFUELING: "#06b6d4",
  ASSIGNED: "#3b82f6",
  OFFLINE: "#ef4444",
};

// Incident status colors
export const INCIDENT_STATUS_COLORS = {
  OPEN: "#f59e0b",
  ASSIGNED: "#3b82f6",
  EN_ROUTE: "#0ea5e9",
  ON_SCENE: "#f59e0b",
  RESOLVED: "#10b981",
  CLOSED: "#6b7280",
  CANCELLED: "#ef4444",
};
