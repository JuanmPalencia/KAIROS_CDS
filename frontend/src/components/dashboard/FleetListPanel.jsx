import { memo } from "react";
import { Ambulance, Fuel, Zap, Star, Heart, Filter, Siren, Droplets } from "lucide-react";

const SCOLORS = { SVB: "#22c55e", SVA: "#ef4444", VIR: "#3b82f6", VAMM: "#f97316", SAMU: "#a855f7" };

function FleetListPanel({ vehicles, focusedVehicleId, focusVehicle, subtypeFilter, setSubtypeFilter, statusFilter, setStatusFilter }) {
  const filteredVehicles = vehicles.filter(v =>
    v.enabled &&
    (subtypeFilter === "ALL" || (v.subtype || "SVB") === subtypeFilter) &&
    (statusFilter === "ALL" || v.status === statusFilter)
  );

  return (
    <div className="incidents-section">
      <h3><Ambulance size={20} className="icon-3d" /> Flota de Ambulancias</h3>

      <div className="subtype-filter-bar">
        <Filter size={14} />
        {["ALL", "SVB", "SVA", "VIR", "VAMM", "SAMU"].map(st => (
          <button
            key={st}
            className={`filter-chip ${subtypeFilter === st ? "active" : ""}`}
            onClick={() => setSubtypeFilter(st)}
            style={subtypeFilter === st && st !== "ALL" ? { background: SCOLORS[st], color: "#fff" } : {}}
          >
            {st === "ALL" ? "Todos" : st}
          </button>
        ))}
      </div>

      <div className="status-filter-bar">
        <Siren size={14} />
        {["ALL", "IDLE", "EN_ROUTE", "REFUELING"].map(st => (
          <button
            key={st}
            className={`filter-chip ${statusFilter === st ? "active" : ""}`}
            onClick={() => setStatusFilter(st)}
            style={statusFilter === st && st !== "ALL" ? { background: { IDLE: "#22c55e", EN_ROUTE: "#ef4444", REFUELING: "#3b82f6" }[st], color: "#fff" } : {}}
          >
            {st === "ALL" ? "Todos" : st === "IDLE" ? "Disponible" : st === "EN_ROUTE" ? "En ruta" : "Repostando"}
          </button>
        ))}
      </div>

      <div className="incidents-list">
        {filteredVehicles.map((v) => {
          const sub = v.subtype || "SVB";
          const sc = SCOLORS[sub] || "#6b7280";
          return (
            <div
              key={v.id}
              className={`incident-item vehicle-item ${focusedVehicleId === v.id ? "focused" : ""} ${v.status === "EN_ROUTE" ? "assigned" : v.status === "REFUELING" ? "refueling" : ""}`}
              onClick={() => focusVehicle(v.id)}
            >
              <div className="incident-header">
                <span className="incident-type">
                  {v.status === "EN_ROUTE" ? <Ambulance size={14} color={sc} />
                    : v.status === "REFUELING" ? <Droplets size={14} color="#3b82f6" />
                    : sub === "VIR" ? <Zap size={14} color={sc} />
                    : sub === "SAMU" ? <Heart size={14} color={sc} />
                    : <Ambulance size={14} color={sc} />} {v.id}
                </span>
                <span className="subtype-tag" style={{ background: sc, color: "#fff" }}>{sub}</span>
                <span className={`status-badge ${v.status === "EN_ROUTE" ? "en-route" : v.status === "IDLE" ? "idle" : v.status === "REFUELING" ? "refueling" : ""}`}>
                  {v.status === "REFUELING" ? "Repostando" : v.status === "EN_ROUTE" ? "En ruta" : v.status === "IDLE" ? "Disponible" : v.status}
                </span>
              </div>
              <div className="vehicle-meta">
                <span><Fuel size={14} /> {v.fuel?.toFixed(0)}% ({((v.fuel / 100) * (v.tank_capacity || 80)).toFixed(0)}L)</span>
                <span><Zap size={14} /> {v.speed} km/h</span>
                <span><Star size={14} /> {v.trust_score}</span>
              </div>
            </div>
          );
        })}
        {filteredVehicles.length === 0 && (
          <div className="empty-state">
            Sin ambulancias {subtypeFilter !== "ALL" ? `tipo ${subtypeFilter}` : ""}{statusFilter !== "ALL" ? ` en estado ${statusFilter}` : "activas"}
          </div>
        )}
      </div>
    </div>
  );
}

export default memo(FleetListPanel);
