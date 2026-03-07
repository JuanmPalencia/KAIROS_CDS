import { memo } from "react";
import { Sparkles, Play, Square, RotateCcw, Gauge, Download, Activity, Siren, MapPin } from "lucide-react";
import { API_BASE } from "../../config";

function SimulationControls({
  autoGenRunning, autoGenInterval, setAutoGenInterval, autoGenCount,
  resetting, lastGenIncident,
  speedMultiplier, setSpeedMultiplier,
  exporting,
  toggleAutoGen, resetSystem, exportToPDF,
  getIncidentTypeLabel,
}) {
  return (
    <div className={`sim-controls ${autoGenRunning ? "sim-active" : ""}`}>
      <div className="sim-controls-header">
        <Sparkles size={16} className={autoGenRunning ? "sim-sparkle-spin" : ""} /> Simulación
        {autoGenRunning && <span className="sim-live-badge">EN VIVO</span>}
      </div>

      <div className="sim-controls-row">
        <button
          className={`sim-btn ${autoGenRunning ? "sim-btn-stop" : "sim-btn-start"}`}
          onClick={toggleAutoGen}
          title={autoGenRunning ? "Detener generación" : "Iniciar generación"}
        >
          {autoGenRunning ? <><Square size={14} /> Parar</> : <><Play size={14} /> Auto-generar</>}
        </button>
        <select
          className="sim-interval-select"
          value={autoGenInterval}
          onChange={e => setAutoGenInterval(Number(e.target.value))}
          disabled={autoGenRunning}
        >
          {[10, 20, 30, 45, 60, 120].map(s => (
            <option key={s} value={s}>{s < 60 ? `${s}s` : `${s / 60} min`}</option>
          ))}
        </select>
        <button className="sim-btn sim-btn-reset" onClick={resetSystem} disabled={resetting}>
          <RotateCcw size={14} className={resetting ? "sim-spin" : ""} /> {resetting ? "Limpiando..." : "Reset"}
        </button>
      </div>

      <div className="sim-controls-row sim-speed-row">
        <Gauge size={14} />
        <span className="sim-speed-label">Velocidad:</span>
        <select
          className="sim-interval-select"
          value={speedMultiplier}
          onChange={e => {
            const v = Number(e.target.value);
            setSpeedMultiplier(v);
            fetch(`${API_BASE}/simulation/speed?multiplier=${v}`, { method: "POST" });
          }}
        >
          <option value={1}>1x (Normal)</option>
          <option value={2}>2x Rápido</option>
          <option value={5}>5x Muy rápido</option>
          <option value={10}>10x Turbo</option>
          <option value={20}>20x Ultra</option>
        </select>
        <button className="export-btn" onClick={exportToPDF} disabled={exporting} title="Exportar dashboard a imagen">
          <Download size={15} /> {exporting ? "..." : "Exportar"}
        </button>
      </div>

      {autoGenRunning && (
        <div className="sim-status">
          <Activity size={12} className="sim-pulse" /> Generando... <strong>{autoGenCount}</strong> creados
        </div>
      )}

      {autoGenRunning && lastGenIncident && (
        <div className="sim-last-incident" key={lastGenIncident.id}>
          <div className="sim-last-header"><Siren size={12} /> Último generado</div>
          <div className="sim-last-body">
            <span className="sim-last-id">{lastGenIncident.id}</span>
            <span className="sim-last-type">{getIncidentTypeLabel(lastGenIncident.incident_type)}</span>
            <span className="sim-last-sev">Sev {lastGenIncident.severity}/5</span>
          </div>
          {lastGenIncident.address && (
            <div className="sim-last-addr"><MapPin size={10} /> {lastGenIncident.address}</div>
          )}
        </div>
      )}

      {!autoGenRunning && autoGenCount > 0 && (
        <div className="sim-status sim-status-stopped">
          <Square size={12} /> Detenida — {autoGenCount} incidentes generados
        </div>
      )}
    </div>
  );
}

export default memo(SimulationControls);
