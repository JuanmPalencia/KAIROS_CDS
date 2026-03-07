import { memo } from "react";
import { Bot, Ambulance, Hospital, CheckCircle, X } from "lucide-react";

function AiAutoSuggestionsPanel({ aiAutoSuggestions, dismissAiAutoSuggestion, confirmAssignment, setSelectedIncident, setAiSuggestion, getIncidentTypeLabel }) {
  if (aiAutoSuggestions.length === 0) return null;

  return (
    <div className="ai-auto-panel">
      <div className="ai-auto-panel-header">
        <Bot size={18} /> Recomendaciones IA ({aiAutoSuggestions.length})
      </div>
      {aiAutoSuggestions.map(({ incidentId, incident, suggestion }) => (
        <div key={incidentId} className="ai-auto-card">
          <div className="ai-auto-card-header">
            <span>{getIncidentTypeLabel(incident?.incident_type)} — {incidentId}</span>
            <button className="ai-auto-close" onClick={() => dismissAiAutoSuggestion(incidentId)}>
              <X size={14} />
            </button>
          </div>
          {suggestion.vehicle_suggestion && (
            <div className="ai-auto-row">
              <Ambulance size={14} /> <strong>{suggestion.vehicle_suggestion.vehicle_id}</strong> — ETA {suggestion.vehicle_suggestion.eta_minutes} min ({suggestion.vehicle_suggestion.distance_km} km)
            </div>
          )}
          {suggestion.hospital_suggestion && (
            <div className="ai-auto-row">
              <Hospital size={14} /> <strong>{suggestion.hospital_suggestion.hospital_name}</strong>
            </div>
          )}
          <div className="ai-auto-actions">
            <button
              className="btn-sm-success"
              onClick={() => {
                confirmAssignment(incidentId, suggestion.vehicle_suggestion?.vehicle_id, suggestion.hospital_suggestion?.hospital_id, null);
                dismissAiAutoSuggestion(incidentId);
              }}
            >
              <CheckCircle size={12} /> Aceptar
            </button>
            <button
              className="btn-sm-secondary"
              onClick={() => {
                setSelectedIncident(incident);
                setAiSuggestion(suggestion);
                dismissAiAutoSuggestion(incidentId);
              }}
            >
              <Bot size={12} /> Ver detalle
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}

export default memo(AiAutoSuggestionsPanel);
