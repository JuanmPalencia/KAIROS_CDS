import { memo } from "react";
import { RefreshCw, Ambulance, Hospital, MapPin } from "lucide-react";

function ActiveIncidentsPanel({ assignedIncidents, setSelectedIncident, focusIncident, followVehicle, getIncidentTypeLabel }) {
  return (
    <div className="incidents-section">
      <h3><RefreshCw size={20} className="icon-3d" /> En Progreso</h3>
      <div className="incidents-list">
        {assignedIncidents.map((inc) => (
          <div key={inc.id} className="incident-item assigned" onClick={() => setSelectedIncident(inc)}>
            <div className="incident-header">
              <span className="incident-type">{getIncidentTypeLabel(inc.incident_type)}</span>
              <span className="status-badge">{inc.status}</span>
            </div>
            <div className="incident-id">{inc.id}</div>
            <div className="incident-assignment">
              <Ambulance size={14} /> {inc.assigned_vehicle_id} → <Hospital size={14} /> {inc.assigned_hospital_id}
            </div>
            <div className="route-progress-section">
              <span className="route-phase-label">
                {inc.route_phase === "TO_HOSPITAL" ? "🏥 Traslado a hospital"
                  : inc.route_phase === "COMPLETED" ? "✅ Completado"
                  : "🚑 Camino al incidente"}
              </span>
              <div className="route-progress-bar">
                <div
                  className={`route-progress-fill ${inc.route_phase === "TO_HOSPITAL" ? "phase-hospital" : "phase-incident"}`}
                  style={{ width: `${Math.min((inc.route_progress || 0) * 100, 100)}%` }}
                />
              </div>
              <span className="route-progress-pct">{Math.round((inc.route_progress || 0) * 100)}%</span>
            </div>
            <div className="incident-focus-btns">
              <button className="focus-btn" onClick={(e) => { e.stopPropagation(); focusIncident(inc.id); }} title="Focalizar incidente">
                <MapPin size={14} />
              </button>
              {inc.assigned_vehicle_id && (
                <button className="focus-btn follow-btn" onClick={(e) => { e.stopPropagation(); followVehicle(inc.assigned_vehicle_id); }} title="Seguir ambulancia en el mapa">
                  <Ambulance size={14} /> Seguir
                </button>
              )}
            </div>
          </div>
        ))}
        {assignedIncidents.length === 0 && (
          <div className="empty-state">Sin incidentes en progreso</div>
        )}
      </div>
    </div>
  );
}

export default memo(ActiveIncidentsPanel);
