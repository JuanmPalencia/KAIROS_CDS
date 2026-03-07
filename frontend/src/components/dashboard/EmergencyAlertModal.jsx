import { memo } from "react";
import { Flame, Shield, Phone, X } from "lucide-react";
import toast from "react-hot-toast";

function EmergencyAlertModal({ emergencyAlert, setEmergencyAlert }) {
  if (!emergencyAlert) return null;

  const isFirefighters = emergencyAlert.type === "FIREFIGHTERS";

  const handleCall = () => {
    toast.success(isFirefighters ? "Bomberos notificados" : "Policía notificada", { duration: 4000 });
    setEmergencyAlert(null);
  };

  return (
    <div className="modal-overlay emergency-overlay" onClick={() => setEmergencyAlert(null)}>
      <div
        className={`emergency-alert-modal ${isFirefighters ? "alert-fire" : "alert-police"}`}
        onClick={e => e.stopPropagation()}
      >
        <div className="emergency-alert-header">
          {isFirefighters ? <Flame size={32} color="#f97316" /> : <Shield size={32} color="#3b82f6" />}
          <h2>{isFirefighters ? "¿Alertar a Bomberos?" : "¿Alertar a Policía Nacional?"}</h2>
        </div>
        <div className="emergency-alert-body">
          <p>
            Se ha registrado un incidente de{" "}
            <strong>{isFirefighters ? "Quemadura" : "Violencia"}</strong> (Severidad {emergencyAlert.incident.severity}/5).
          </p>
          <p>
            {isFirefighters
              ? "Se recomienda coordinar con el Servicio de Bomberos para asistencia en el lugar."
              : "Se recomienda coordinar con la Policía Nacional para seguridad en el lugar."}
          </p>
          <div className="emergency-alert-info">
            <div><strong>ID:</strong> {emergencyAlert.incident.id}</div>
            <div>
              <strong>Ubicación:</strong>{" "}
              {emergencyAlert.incident.address || `${emergencyAlert.incident.lat?.toFixed(4)}, ${emergencyAlert.incident.lon?.toFixed(4)}`}
            </div>
          </div>
        </div>
        <div className="emergency-alert-actions">
          <button className="btn-emergency-call" onClick={handleCall}>
            <Phone size={16} /> {isFirefighters ? "Llamar a Bomberos (080)" : "Llamar a Policía (091)"}
          </button>
          <button className="btn-secondary" onClick={() => setEmergencyAlert(null)}>
            <X size={16} /> Descartar
          </button>
        </div>
      </div>
    </div>
  );
}

export default memo(EmergencyAlertModal);
