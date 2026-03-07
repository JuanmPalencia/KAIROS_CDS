import { useState, memo } from "react";
import { Info, ChevronDown, ChevronUp } from "lucide-react";

function MapLegend() {
  const [open, setOpen] = useState(false);
  return (
    <div className={`map-legend ${open ? "open" : ""}`}>
      <button className="map-legend-toggle" onClick={() => setOpen(v => !v)}>
        <Info size={14} /> Leyenda {open ? <ChevronDown size={13} /> : <ChevronUp size={13} />}
      </button>
      {open && (
        <div className="map-legend-body">
          <div className="legend-section">
            <span className="legend-title">Ambulancias</span>
            <div className="legend-item"><span className="legend-dot" style={{ background: "#22c55e" }} /><span className="legend-cross">✚</span> SVB — Soporte Vital Básico</div>
            <div className="legend-item"><span className="legend-dot" style={{ background: "#ef4444", border: "2px solid #fbbf24" }} /><span className="legend-cross">✚</span> SVA — Soporte Vital Avanzado</div>
            <div className="legend-item"><span className="legend-dot" style={{ background: "#3b82f6" }} /><span className="legend-cross">⚡</span> VIR — Intervención Rápida</div>
            <div className="legend-item"><span className="legend-dot" style={{ background: "#f97316" }} /><span className="legend-cross">✚✚</span> VAMM — Asistencia Múltiple</div>
            <div className="legend-item"><span className="legend-dot" style={{ background: "#a855f7" }} /><span className="legend-cross">♥</span> SAMU — Atención Urgente</div>
          </div>
          <div className="legend-section">
            <span className="legend-title">Estado ambulancia</span>
            <div className="legend-item"><span className="legend-shape circle" /> Disponible / Ocupada</div>
            <div className="legend-item"><span className="legend-shape rect" /> En ruta</div>
          </div>
          <div className="legend-section">
            <span className="legend-title">Puntos de interés</span>
            <div className="legend-item"><span className="legend-poi hospital-poi">✚</span> Hospital</div>
            <div className="legend-item"><span className="legend-poi gas-poi">⛽</span> Gasolinera</div>
            <div className="legend-item"><span className="legend-poi dea-poi">♥</span> DEA (Desfibrilador)</div>
          </div>
          <div className="legend-section">
            <span className="legend-title">Incidentes</span>
            <div className="legend-item"><span className="legend-pin" style={{ background: "#dc2626" }} /> Severidad 4-5 (crítico)</div>
            <div className="legend-item"><span className="legend-pin" style={{ background: "#ef4444" }} /> Severidad 3 (grave)</div>
            <div className="legend-item"><span className="legend-pin" style={{ background: "#f97316" }} /> Severidad 1-2 (moderado)</div>
            <div className="legend-item"><span className="legend-pin" style={{ background: "#f59e0b" }} /> Asignado</div>
          </div>
        </div>
      )}
    </div>
  );
}

export default memo(MapLegend);
