import { useState, useEffect, useRef } from "react";
import {
  Stethoscope, Ambulance, MapPin, Clock, Heart, Activity,
  ThermometerSun, Droplets, Brain, FileText, RefreshCw,
  AlertTriangle, Phone, Radio, Search, Filter
} from "lucide-react";
import "../styles/ParamedicView.css";
import { statusLabel, VEHICLE_STATUS_LABELS } from "../utils/statusLabels";
import { API_BASE } from "../config";

const API = API_BASE;
const hdrs = () => ({ Authorization: `Bearer ${localStorage.getItem("token")}` });

export default function ParamedicView() {
  const [vehicles, setVehicles] = useState([]);
  const [selectedVehicle, setSelectedVehicle] = useState(null);
  const [crew, setCrew] = useState(null);
  const [incidents, setIncidents] = useState([]);
  const [preArrival, setPreArrival] = useState(null);
  const [vitals, setVitals] = useState({ hr: "", sys: "", dia: "", spo2: "", temp: "", rr: "", glasgow: "" });
  const [savingVitals, setSavingVitals] = useState(false);
  const [vitalsSaved, setVitalsSaved] = useState(false);
  const [searchVehicle, setSearchVehicle] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const prevVehiclesKey = useRef("");
  const prevIncidentsKey = useRef("");

  const fetchData = async () => {
    try {
      const res = await fetch(`${API}/api/live`, { headers: hdrs() });
      if (res.ok) {
        const data = await res.json();
        // Stable sort by ID to avoid jumps
        const sortedVehicles = (data.vehicles || []).sort((a, b) => a.id.localeCompare(b.id));
        const sortedIncidents = (data.incidents || []).sort((a, b) => (a.id || "").localeCompare(b.id || ""));
        // Only update state if data actually changed
        const vKey = JSON.stringify(sortedVehicles.map(v => `${v.id}:${v.status}:${v.lat}:${v.lon}`));
        const iKey = JSON.stringify(sortedIncidents.map(i => `${i.id}:${i.status}`));
        if (vKey !== prevVehiclesKey.current) {
          prevVehiclesKey.current = vKey;
          setVehicles(sortedVehicles);
        }
        if (iKey !== prevIncidentsKey.current) {
          prevIncidentsKey.current = iKey;
          setIncidents(sortedIncidents);
        }
      }
    } catch (e) { console.error(e); }
  };

  const fetchCrew = async (vid) => {
    try {
      const res = await fetch(`${API}/api/crews/vehicle/${vid}`, { headers: hdrs() });
      if (res.ok) setCrew(await res.json());
    } catch { setCrew(null); }
  };

  const fetchPreArrival = async (type) => {
    try {
      const res = await fetch(`${API}/api/mci/pre-arrival/${type}`, { headers: hdrs() });
      if (res.ok) setPreArrival(await res.json());
    } catch { setPreArrival(null); }
  };

  const saveVitals = async () => {
    if (!assignedIncident) return;
    setSavingVitals(true);
    setVitalsSaved(false);
    try {
      // First ensure ePCR exists for this incident
      const checkRes = await fetch(`${API}/api/epcr/incident/${assignedIncident.id}`, { headers: hdrs() });
      let epcrId = null;
      if (checkRes.ok) {
        const data = await checkRes.json();
        epcrId = data?.epcr?.id;
      }
      if (!epcrId) {
        // Create ePCR
        const createRes = await fetch(`${API}/api/epcr/create`, {
          method: "POST",
          headers: { ...hdrs(), "Content-Type": "application/json" },
          body: JSON.stringify({
            incident_id: assignedIncident.id,
            vehicle_id: selectedVehicle,
            heart_rate: vitals.hr ? parseInt(vitals.hr) : null,
            blood_pressure_sys: vitals.sys ? parseInt(vitals.sys) : null,
            blood_pressure_dia: vitals.dia ? parseInt(vitals.dia) : null,
            spo2: vitals.spo2 ? parseInt(vitals.spo2) : null,
            temperature: vitals.temp ? parseFloat(vitals.temp) : null,
            respiratory_rate: vitals.rr ? parseInt(vitals.rr) : null,
            glasgow_score: vitals.glasgow ? parseInt(vitals.glasgow) : null,
          }),
        });
        if (createRes.ok) {
          const cr = await createRes.json();
          epcrId = cr.epcr_id;
        }
      } else {
        // Update vitals on existing ePCR
        await fetch(`${API}/api/epcr/${epcrId}/vitals`, {
          method: "PUT",
          headers: { ...hdrs(), "Content-Type": "application/json" },
          body: JSON.stringify({
            heart_rate: vitals.hr ? parseInt(vitals.hr) : null,
            blood_pressure_sys: vitals.sys ? parseInt(vitals.sys) : null,
            blood_pressure_dia: vitals.dia ? parseInt(vitals.dia) : null,
            spo2: vitals.spo2 ? parseInt(vitals.spo2) : null,
            temperature: vitals.temp ? parseFloat(vitals.temp) : null,
            respiratory_rate: vitals.rr ? parseInt(vitals.rr) : null,
            glasgow_score: vitals.glasgow ? parseInt(vitals.glasgow) : null,
          }),
        });
      }
      setVitalsSaved(true);
      setTimeout(() => setVitalsSaved(false), 3000);
    } catch (e) {
      console.error("Error saving vitals:", e);
    } finally {
      setSavingVitals(false);
    }
  };

  useEffect(() => {
    fetchData();
    const iv = setInterval(fetchData, 10000);
    return () => clearInterval(iv);
  }, []);

  useEffect(() => {
    if (selectedVehicle) {
      fetchCrew(selectedVehicle);
    }
  }, [selectedVehicle]);

  const selectedV = vehicles.find(v => v.id === selectedVehicle);
  const assignedIncident = selectedV ? incidents.find(i => i.assigned_vehicle_id === selectedVehicle) : null;

  // Filtered vehicles for selector
  const filteredVehicles = vehicles.filter(v => {
    if (statusFilter !== "ALL" && v.status !== statusFilter) return false;
    if (searchVehicle && !v.id.toLowerCase().includes(searchVehicle.toLowerCase())) return false;
    return true;
  });

  useEffect(() => {
    if (assignedIncident?.incident_type) {
      fetchPreArrival(assignedIncident.incident_type);
    } else {
      setPreArrival(null);
    }
  }, [assignedIncident?.incident_type]);

  return (
    <div className="paramedic-page">
      <div className="para-header">
        <h1><Stethoscope size={28} /> Vista Paramédica</h1>
        <p className="para-subtitle">Interfaz para tripulación de ambulancia</p>
      </div>

      {/* Filters */}
      <div className="para-filters">
        <div className="para-search-wrap">
          <Search size={16} />
          <input
            type="text"
            placeholder="Buscar vehículo..."
            value={searchVehicle}
            onChange={e => setSearchVehicle(e.target.value)}
            className="para-search"
          />
          {searchVehicle && <button className="para-search-clear" onClick={() => setSearchVehicle("")}>×</button>}
        </div>
        <div className="para-filter-group">
          <Filter size={14} />
          <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className="para-filter-select">
            <option value="ALL">Todos los estados</option>
            {Object.entries(VEHICLE_STATUS_LABELS).map(([key, label]) => (
              <option key={key} value={key}>{label}</option>
            ))}
          </select>
        </div>
        {(searchVehicle || statusFilter !== "ALL") && (
          <button className="para-clear-btn" onClick={() => { setSearchVehicle(""); setStatusFilter("ALL"); }}>
            Limpiar
          </button>
        )}
      </div>

      {/* Vehicle selector */}
      <div className="vehicle-selector">
        {filteredVehicles.map(v => (
          <button
            key={v.id}
            className={`v-sel-btn ${selectedVehicle === v.id ? "active" : ""} ${v.status === "EN_ROUTE" ? "en-route" : ""}`}
            onClick={() => setSelectedVehicle(v.id)}
          >
            <Ambulance size={16} />
            <span className="v-id">{v.id}</span>
            <span className={`v-status vs-${v.status}`}>{statusLabel(v.status)}</span>
          </button>
        ))}
        {filteredVehicles.length === 0 && vehicles.length > 0 && (
          <p className="para-no-results">Sin resultados para el filtro actual</p>
        )}
      </div>

      {!selectedVehicle && (
        <div className="para-empty">
          <Ambulance size={48} strokeWidth={1} />
          <p>Selecciona tu ambulancia</p>
        </div>
      )}

      {selectedV && (
        <div className="para-content">
          {/* Vehicle info + crew */}
          <div className="para-panel vehicle-panel">
            <h2><Ambulance size={20} /> {selectedV.id} — {selectedV.subtype}</h2>
            <div className="v-info-grid">
              <div className="v-info-item">
                <MapPin size={14} /> {selectedV.lat.toFixed(4)}, {selectedV.lon.toFixed(4)}
              </div>
              <div className="v-info-item">
                <Activity size={14} /> {selectedV.speed.toFixed(1)} km/h
              </div>
              <div className="v-info-item">
                <Droplets size={14} />
                <div className="fuel-bar-sm">
                  <div style={{ width: `${selectedV.fuel}%`, background: selectedV.fuel > 50 ? '#22c55e' : '#f59e0b' }}></div>
                </div>
                {selectedV.fuel.toFixed(0)}%
              </div>
            </div>

            {crew && crew.crew && crew.crew.length > 0 && (
              <div className="crew-section">
                <h3>Tripulación</h3>
                {crew.crew.map(c => (
                  <div key={c.id} className="crew-mini">
                    <span className="crew-mini-role">{c.role}</span>
                    <span>{c.name}</span>
                    {c.phone && <a href={`tel:${c.phone}`} className="crew-phone"><Phone size={12} /></a>}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Active incident */}
          <div className="para-panel incident-panel">
            {assignedIncident ? (
              <>
                <h2 className="active-case">
                  <AlertTriangle size={20} /> Caso Activo: {assignedIncident.id}
                </h2>
                <div className="case-details">
                  <div className="case-row"><strong>Tipo:</strong> {assignedIncident.incident_type}</div>
                  <div className="case-row"><strong>Severidad:</strong>
                    <span className={`sev-dot sev-${assignedIncident.severity}`}>{assignedIncident.severity}/5</span>
                  </div>
                  <div className="case-row"><strong>Ubicación:</strong> {assignedIncident.address || `${assignedIncident.lat.toFixed(4)}, ${assignedIncident.lon.toFixed(4)}`}</div>
                  {assignedIncident.description && (
                    <div className="case-row"><strong>Descripción:</strong> {assignedIncident.description}</div>
                  )}
                  {assignedIncident.affected_count > 1 && (
                    <div className="case-row mci-alert">
                      <AlertTriangle size={14} /> <strong>IMV:</strong> {assignedIncident.affected_count} víctimas
                    </div>
                  )}
                </div>

                {/* Pre-arrival instructions */}
                {preArrival && (
                  <div className="pre-arrival-section">
                    <h3><FileText size={16} /> Instrucciones Pre-Llegada</h3>
                    <div className="pre-arrival-title">{preArrival.title}</div>
                    <ul className="pre-arrival-steps">
                      {preArrival.steps.map((step, i) => (
                        <li key={i}>{step}</li>
                      ))}
                    </ul>
                    {preArrival.critical && (
                      <div className="pre-arrival-critical">
                        <AlertTriangle size={14} /> {preArrival.critical}
                      </div>
                    )}
                  </div>
                )}
              </>
            ) : (
              <div className="no-case">
                <Activity size={32} strokeWidth={1} />
                <p>Sin caso asignado — En espera</p>
              </div>
            )}
          </div>

          {/* Quick vitals entry */}
          <div className="para-panel vitals-panel">
            <h2><Heart size={20} /> Constantes Vitales Rápidas</h2>
            <div className="vitals-grid">
              <div className="vital-input">
                <label><Heart size={14} /> FC</label>
                <input type="number" placeholder="lpm" value={vitals.hr} onChange={e => setVitals(v => ({...v, hr: e.target.value}))} />
              </div>
              <div className="vital-input">
                <label><Activity size={14} /> TA</label>
                <div className="bp-inputs">
                  <input type="number" placeholder="sys" value={vitals.sys} onChange={e => setVitals(v => ({...v, sys: e.target.value}))} />
                  <span>/</span>
                  <input type="number" placeholder="dia" value={vitals.dia} onChange={e => setVitals(v => ({...v, dia: e.target.value}))} />
                </div>
              </div>
              <div className="vital-input">
                <label><Droplets size={14} /> SpO2</label>
                <input type="number" placeholder="%" value={vitals.spo2} onChange={e => setVitals(v => ({...v, spo2: e.target.value}))} />
              </div>
              <div className="vital-input">
                <label><ThermometerSun size={14} /> Temp</label>
                <input type="number" placeholder="°C" step="0.1" value={vitals.temp} onChange={e => setVitals(v => ({...v, temp: e.target.value}))} />
              </div>
              <div className="vital-input">
                <label><Activity size={14} /> FR</label>
                <input type="number" placeholder="rpm" value={vitals.rr} onChange={e => setVitals(v => ({...v, rr: e.target.value}))} />
              </div>
              <div className="vital-input">
                <label><Brain size={14} /> Glasgow</label>
                <input type="number" placeholder="3-15" min="3" max="15" value={vitals.glasgow} onChange={e => setVitals(v => ({...v, glasgow: e.target.value}))} />
              </div>
            </div>
            <button className="save-vitals-btn" disabled={!assignedIncident || savingVitals} onClick={saveVitals}>
              {savingVitals ? "Guardando..." : vitalsSaved ? "✓ Guardadas" : "Guardar Constantes"}
            </button>
          </div>

          {/* Radio / comms panel */}
          <div className="para-panel radio-panel">
            <h2><Radio size={20} /> Comunicaciones</h2>
            <div className="radio-info">
              <div className="radio-channel">
                <Radio size={16} /> Canal TETRA: <strong>SEM-{selectedV.subtype}-01</strong>
              </div>
              <div className="radio-channel">
                <Phone size={16} /> CCUS 112: <strong>+34 112</strong>
              </div>
              <div className="radio-channel">
                <Phone size={16} /> Coordinación: <strong>+34 915 620 420</strong>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
