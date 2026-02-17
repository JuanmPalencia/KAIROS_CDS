import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Heart, Wind, Brain, Zap, Flame, Skull, HeartPulse, Baby, Smile, AlertTriangle, MapPin, Save, Shield, Sparkles, Thermometer, Pill, Waves, PersonStanding } from 'lucide-react';
import "../styles/CreateIncident.css";
import { API_BASE } from "../config";

const INCIDENT_TYPES = [
  { value: "CARDIO", label: "Cardíaco", Icon: Heart },
  { value: "RESPIRATORY", label: "Respiratorio", Icon: Wind },
  { value: "NEUROLOGICAL", label: "Neurológico", Icon: Brain },
  { value: "TRAUMA", label: "Trauma", Icon: Zap },
  { value: "BURN", label: "Quemadura", Icon: Flame },
  { value: "POISONING", label: "Intoxicación", Icon: Skull },
  { value: "OBSTETRIC", label: "Obstétrico", Icon: HeartPulse },
  { value: "PEDIATRIC", label: "Pediátrico", Icon: Baby },
  { value: "PSYCHIATRIC", label: "Psiquiátrico", Icon: Smile },
  { value: "VIOLENCE", label: "Violencia / Agresión", Icon: Shield },
  { value: "ALLERGIC", label: "Reacción Alérgica", Icon: Sparkles },
  { value: "METABOLIC", label: "Metabólico / Endocrino", Icon: Thermometer },
  { value: "INTOXICATION", label: "Intoxicación (drogas/alcohol)", Icon: Pill },
  { value: "DROWNING", label: "Ahogamiento", Icon: Waves },
  { value: "FALL", label: "Caída / Traumatismo leve", Icon: PersonStanding },
];

export default function CreateIncident() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    incident_type: "CARDIO",
    description: "",
    lat: 40.4168,
    lon: -3.7038,
    address: "",
    city: "Madrid",
    province: "Madrid",
    severity: 3,
    affected_count: 1,
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/events/incidents`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });

      if (res.ok) {
        navigate("/incidents");
      } else {
        alert("Error al crear incidente");
      }
    } catch {
      alert("Error de conexión");
    } finally {
      setLoading(false);
    }
  };

  const getLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition((pos) => {
        setFormData({
          ...formData,
          lat: pos.coords.latitude,
          lon: pos.coords.longitude,
        });
      });
    }
  };

  return (
    <div className="create-incident-page">
      <div className="page-header">
        <h1><AlertTriangle size={24} className="icon-3d" /> Nuevo Incidente</h1>
        <p>Registra un nuevo incidente de emergencia</p>
      </div>

      <form onSubmit={handleSubmit} className="incident-form">
        <div className="form-section">
          <label className="section-label">Tipo de Incidente *</label>
          <div className="type-grid">
            {INCIDENT_TYPES.map((type) => (
              <button
                key={type.value}
                type="button"
                className={`type-btn ${
                  formData.incident_type === type.value ? "active" : ""
                }`}
                onClick={() =>
                  setFormData({ ...formData, incident_type: type.value })
                }
              >
                <span className="type-emoji"><type.Icon size={24} /></span>
                <span className="type-name">{type.label}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="form-section">
          <label htmlFor="description">Descripción *</label>
          <textarea
            id="description"
            value={formData.description}
            onChange={(e) =>
              setFormData({ ...formData, description: e.target.value })
            }
            placeholder="Describe la situación de emergencia..."
            required
            rows={4}
            maxLength={500}
          />
          <small>{formData.description.length}/500 caracteres</small>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="lat">Latitud *</label>
            <input
              id="lat"
              type="number"
              step="0.000001"
              value={formData.lat}
              onChange={(e) =>
                setFormData({ ...formData, lat: parseFloat(e.target.value) })
              }
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="lon">Longitud *</label>
            <input
              id="lon"
              type="number"
              step="0.000001"
              value={formData.lon}
              onChange={(e) =>
                setFormData({ ...formData, lon: parseFloat(e.target.value) })
              }
              required
            />
          </div>
          <button
            type="button"
            className="location-btn"
            onClick={getLocation}
            title="Usar mi ubicación"
          >
            <MapPin size={18} />
          </button>
        </div>

        <div className="form-group">
          <label htmlFor="address">Dirección *</label>
          <input
            id="address"
            type="text"
            value={formData.address}
            onChange={(e) =>
              setFormData({ ...formData, address: e.target.value })
            }
            placeholder="Calle, número, piso..."
            required
          />
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="city">Ciudad *</label>
            <select
              id="city"
              value={formData.city}
              onChange={(e) =>
                setFormData({ ...formData, city: e.target.value })
              }
              required
            >
              <option value="Madrid">Madrid</option>
              <option value="Barcelona">Barcelona</option>
              <option value="Valencia">Valencia</option>
              <option value="Sevilla">Sevilla</option>
              <option value="Zaragoza">Zaragoza</option>
              <option value="Málaga">Málaga</option>
              <option value="Murcia">Murcia</option>
              <option value="Palma">Palma</option>
              <option value="Las Palmas">Las Palmas</option>
              <option value="Bilbao">Bilbao</option>
            </select>
          </div>
          <div className="form-group">
            <label htmlFor="province">Provincia *</label>
            <select
              id="province"
              value={formData.province}
              onChange={(e) =>
                setFormData({ ...formData, province: e.target.value })
              }
              required
            >
              <option value="Madrid">Madrid</option>
              <option value="Barcelona">Barcelona</option>
              <option value="Valencia">Valencia</option>
              <option value="Sevilla">Sevilla</option>
              <option value="Zaragoza">Zaragoza</option>
              <option value="Málaga">Málaga</option>
              <option value="Murcia">Murcia</option>
              <option value="Baleares">Baleares</option>
              <option value="Las Palmas">Las Palmas</option>
              <option value="Vizcaya">Vizcaya</option>
            </select>
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="severity">Severidad (1-5)</label>
            <input
              id="severity"
              type="number"
              min="1"
              max="5"
              value={formData.severity}
              onChange={(e) =>
                setFormData({ ...formData, severity: parseInt(e.target.value) })
              }
            />
          </div>
          <div className="form-group">
            <label htmlFor="affected">Afectados</label>
            <input
              id="affected"
              type="number"
              min="1"
              value={formData.affected_count}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  affected_count: parseInt(e.target.value),
                })
              }
            />
          </div>
        </div>

        <div className="form-actions">
          <button
            type="button"
            className="btn-secondary"
            onClick={() => navigate("/incidents")}
          >
            Cancelar
          </button>
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? "Creando..." : <><Save size={16} /> Crear Incidente</>}
          </button>
        </div>
      </form>
    </div>
  );
}
