import { memo } from "react";
import { ClipboardList, ScrollText, Bot, Ambulance, Hospital, CheckCircle, Pencil, X } from "lucide-react";

function IncidentDetailModal({
  selectedIncident, onClose,
  incidentTimeline, fetchTimeline,
  aiSuggestion, loadingSuggestion, getAISuggestion,
  overrideMode, setOverrideMode,
  overrideVehicle, setOverrideVehicle,
  overrideHospital, setOverrideHospital,
  overrideReason, setOverrideReason,
  confirmAssignment, resolveIncident,
  vehicles, hospitals, user,
  getIncidentTypeLabel,
}) {
  if (!selectedIncident) return null;

  const canDispatch = user?.role === "ADMIN" || user?.role === "OPERATOR";
  const isOpen = selectedIncident.status === "OPEN";
  const isActive = ["ASSIGNED", "EN_ROUTE"].includes(selectedIncident.status);

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2><ClipboardList size={24} className="icon-3d" /> Detalle del Incidente</h2>
          <button className="close-btn" onClick={onClose}>✕</button>
        </div>

        <div className="modal-body">
          <div className="detail-row"><strong>ID:</strong> {selectedIncident.id}</div>
          <div className="detail-row"><strong>Tipo:</strong> {getIncidentTypeLabel(selectedIncident.incident_type)}</div>
          <div className="detail-row"><strong>Severidad:</strong> {selectedIncident.severity}/5</div>
          <div className="detail-row"><strong>Estado:</strong> {selectedIncident.status}</div>
          <div className="detail-row"><strong>Descripción:</strong> {selectedIncident.description || "Sin descripción"}</div>
          <div className="detail-row"><strong>Dirección:</strong> {selectedIncident.address || "No especificada"}</div>
          <div className="detail-row"><strong>Afectados:</strong> {selectedIncident.affected_count || 1} persona(s)</div>

          <button className="btn-secondary" onClick={() => fetchTimeline(selectedIncident.id)} style={{ marginTop: "0.5rem", marginBottom: "0.5rem" }}>
            <ScrollText size={16} /> Ver Timeline
          </button>

          {incidentTimeline && (
            <div className="incident-timeline">
              <h4><ScrollText size={16} /> Timeline del Incidente</h4>
              <div className="timeline-list">
                {incidentTimeline.map((evt, idx) => (
                  <div key={idx} className="timeline-event">
                    <div className="timeline-dot" style={{ background: evt.color || "#667eea" }}>{evt.icon || "●"}</div>
                    <div className="timeline-content">
                      <div className="timeline-action">{evt.action}</div>
                      <div className="timeline-detail">{evt.detail}</div>
                      <div className="timeline-time">{new Date(evt.timestamp).toLocaleString("es-ES")}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {isOpen && canDispatch && (
            <>
              <button className="btn-primary" onClick={() => getAISuggestion(selectedIncident.id)} disabled={loadingSuggestion}>
                {loadingSuggestion ? <><Bot size={16} /> Analizando...</> : <><Bot size={16} /> Obtener Sugerencia de IA</>}
              </button>

              {aiSuggestion && (
                <div className="ai-suggestion">
                  <h3><Bot size={20} className="icon-3d" /> Recomendación de IA</h3>

                  {aiSuggestion.vehicle_suggestion && (
                    <div className="suggestion-box">
                      <h4><Ambulance size={16} /> Ambulancia Sugerida</h4>
                      <div><strong>ID:</strong> {aiSuggestion.vehicle_suggestion.vehicle_id}</div>
                      <div><strong>ETA:</strong> {aiSuggestion.vehicle_suggestion.eta_minutes} minutos</div>
                      <div><strong>Distancia:</strong> {aiSuggestion.vehicle_suggestion.distance_km} km</div>
                      <div><strong>Confianza:</strong> {(aiSuggestion.vehicle_suggestion.confidence * 100).toFixed(0)}%</div>
                      <div className="reasoning">{aiSuggestion.vehicle_suggestion.reasoning}</div>
                    </div>
                  )}

                  {aiSuggestion.hospital_suggestion && (
                    <div className="suggestion-box">
                      <h4><Hospital size={16} /> Hospital Sugerido</h4>
                      <div><strong>Nombre:</strong> {aiSuggestion.hospital_suggestion.hospital_name}</div>
                      <div><strong>ID:</strong> {aiSuggestion.hospital_suggestion.hospital_id}</div>
                      <div><strong>Confianza:</strong> {(aiSuggestion.hospital_suggestion.confidence * 100).toFixed(0)}%</div>
                      <div className="reasoning">{aiSuggestion.hospital_suggestion.reasoning}</div>
                      {aiSuggestion.hospital_suggestion.alternatives?.length > 0 && (
                        <div className="alternatives">
                          <strong>Alternativas:</strong>
                          {aiSuggestion.hospital_suggestion.alternatives.map(alt => (
                            <div key={alt.hospital_id}>• {alt.hospital_name} ({(alt.confidence * 100).toFixed(0)}%)</div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  <div className="button-group">
                    <button
                      className="btn-success"
                      onClick={() => confirmAssignment(selectedIncident.id, aiSuggestion.vehicle_suggestion?.vehicle_id, aiSuggestion.hospital_suggestion?.hospital_id, null)}
                    >
                      <CheckCircle size={16} /> Aceptar Sugerencia
                    </button>
                    <button
                      className="btn-warning"
                      onClick={() => {
                        setOverrideMode(!overrideMode);
                        setOverrideVehicle(aiSuggestion.vehicle_suggestion?.vehicle_id || "");
                        setOverrideHospital(aiSuggestion.hospital_suggestion?.hospital_id || "");
                        setOverrideReason("");
                      }}
                    >
                      <Pencil size={16} /> {overrideMode ? "Cancelar" : "Modificar y Asignar"}
                    </button>
                  </div>

                  {overrideMode && (
                    <div className="override-form">
                      <div className="override-field">
                        <label>Ambulancia</label>
                        <select value={overrideVehicle} onChange={e => setOverrideVehicle(e.target.value)}>
                          <option value="">— Seleccionar —</option>
                          {vehicles.filter(v => v.status === "IDLE").map(v => (
                            <option key={v.id} value={v.id}>{v.id} ({v.subtype || "SVB"})</option>
                          ))}
                        </select>
                      </div>
                      <div className="override-field">
                        <label>Hospital</label>
                        <select value={overrideHospital} onChange={e => setOverrideHospital(e.target.value)}>
                          <option value="">— Seleccionar —</option>
                          {hospitals.map(h => (
                            <option key={h.id} value={h.id}>{h.name || h.id}</option>
                          ))}
                        </select>
                      </div>
                      <div className="override-field">
                        <label>Motivo del cambio</label>
                        <input
                          type="text"
                          placeholder="Ej: Vehículo más cercano disponible"
                          value={overrideReason}
                          onChange={e => setOverrideReason(e.target.value)}
                        />
                      </div>
                      <button
                        className="btn-success"
                        disabled={!overrideVehicle || !overrideReason}
                        onClick={() => confirmAssignment(selectedIncident.id, overrideVehicle, overrideHospital, overrideReason)}
                      >
                        <CheckCircle size={16} /> Confirmar Asignación Manual
                      </button>
                    </div>
                  )}
                </div>
              )}
            </>
          )}

          {isActive && canDispatch && (
            <button className="btn-success" onClick={() => resolveIncident(selectedIncident.id)}>
              <CheckCircle size={16} /> Marcar como Resuelto
            </button>
          )}

          {selectedIncident.status === "RESOLVED" && (
            <div className="resolved-badge"><CheckCircle size={16} /> Incidente resuelto</div>
          )}
        </div>
      </div>
    </div>
  );
}

export default memo(IncidentDetailModal);
