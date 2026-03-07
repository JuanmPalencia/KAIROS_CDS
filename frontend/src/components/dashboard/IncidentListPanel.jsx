import { memo } from "react";
import { AlertTriangle, CheckCircle, MapPin } from "lucide-react";

function IncidentListPanel({ openIncidents, setSelectedIncident, focusIncident, getIncidentTypeLabel }) {
  return (
    <div className="incidents-section">
      <h3><AlertTriangle size={20} className="icon-3d" /> Incidentes Pendientes</h3>
      <div className="incidents-list">
        {openIncidents.map((inc) => (
          <div key={inc.id} className="incident-item" onClick={() => setSelectedIncident(inc)}>
            <div className="incident-header">
              <span className="incident-type">{getIncidentTypeLabel(inc.incident_type)}</span>
              <span className={`severity-badge severity-${inc.severity}`}>{inc.severity}/5</span>
            </div>
            <div className="incident-id">{inc.id}</div>
            <div className="incident-location">
              {inc.address || `${(inc.lat || 0).toFixed(4)}, ${(inc.lon || 0).toFixed(4)}`}
            </div>
            <button
              className="focus-btn"
              onClick={(e) => { e.stopPropagation(); focusIncident(inc.id); }}
              title="Focalizar en mapa"
            >
              <MapPin size={14} />
            </button>
          </div>
        ))}
        {openIncidents.length === 0 && (
          <div className="empty-state"><CheckCircle size={14} /> No hay incidentes pendientes</div>
        )}
      </div>
    </div>
  );
}

export default memo(IncidentListPanel);
