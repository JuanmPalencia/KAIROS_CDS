import { useState, useEffect, useCallback } from "react";
import {
  Building2, Ambulance, Users, Activity, BedDouble,
  AlertTriangle, RefreshCw, Heart, Plus, Database
} from "lucide-react";
import "../styles/HospitalDashboard.css";
import { API_BASE } from "../config";

const API = API_BASE;
const hdrs = () => ({ Authorization: `Bearer ${localStorage.getItem("token")}` });

export default function HospitalDashboard() {
  const [hospitals, setHospitals] = useState([]);
  const [selectedHospital, setSelectedHospital] = useState(null);
  const [details, setDetails] = useState(null);
  const [loading, setLoading] = useState(true);
  const [seeding, setSeeding] = useState(false);

  const seedHospitals = useCallback(async () => {
    setSeeding(true);
    try {
      const res = await fetch(`${API}/api/hospitals/seed`, {
        method: "POST",
        headers: { ...hdrs(), "Content-Type": "application/json" }
      });
      if (res.ok) {
        // Re-fetch after seeding
        const res2 = await fetch(`${API}/api/resources/hospital-dashboard`);
        if (res2.ok) setHospitals(await res2.json());
      }
    } catch (e) { console.error("Seed error:", e); }
    finally { setSeeding(false); }
  }, []);

  const fetchHospitals = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/resources/hospital-dashboard`);
      if (res.ok) {
        const data = await res.json();
        setHospitals(data);
        // Auto-seed if empty on first load
        if (data.length === 0 && loading) {
          await seedHospitals();
        }
      }
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, [loading, seedHospitals]);

  const fetchDetails = useCallback(async (id) => {
    try {
      const res = await fetch(`${API}/api/resources/hospital-dashboard/${id}`);
      if (res.ok) setDetails(await res.json());
    } catch (e) { console.error(e); }
  }, []);

  useEffect(() => {
    fetchHospitals();
    const iv = setInterval(fetchHospitals, 5000);
    return () => clearInterval(iv);
  }, [fetchHospitals]);

  useEffect(() => {
    if (selectedHospital) {
      fetchDetails(selectedHospital);
      const iv = setInterval(() => fetchDetails(selectedHospital), 5000);
      return () => clearInterval(iv);
    }
  }, [selectedHospital, fetchDetails]);

  const occupancyColor = (pct) => pct > 85 ? "#ef4444" : pct > 60 ? "#f59e0b" : "#22c55e";

  if (loading) return <div className="hosp-loading"><RefreshCw className="spin" size={24} /> Cargando hospitales...</div>;

  if (hospitals.length === 0) return (
    <div className="hospital-dash-page">
      <div className="hosp-header">
        <h1><Building2 size={28} /> Dashboard Hospitalario</h1>
      </div>
      <div className="hosp-empty-state">
        <Building2 size={64} strokeWidth={1} />
        <h2>No hay hospitales registrados</h2>
        <p>Carga los hospitales de ejemplo para empezar</p>
        <button className="hosp-seed-btn" onClick={seedHospitals} disabled={seeding}>
          {seeding ? <><RefreshCw className="spin" size={16} /> Cargando...</> : <><Database size={16} /> Cargar hospitales de ejemplo</>}
        </button>
      </div>
    </div>
  );

  return (
    <div className="hospital-dash-page">
      <div className="hosp-header">
        <h1><Building2 size={28} /> Dashboard Hospitalario</h1>
        <p className="hosp-subtitle">Vista en tiempo real para gestión de urgencias hospitalarias</p>
      </div>

      <div className="hosp-layout">
        {/* Hospital list */}
        <div className="hosp-list">
          {hospitals.map(h => (
            <div
              key={h.id}
              className={`hosp-item ${selectedHospital === h.id ? "selected" : ""}`}
              onClick={() => setSelectedHospital(h.id)}
            >
              <div className="hosp-item-header">
                <Building2 size={18} />
                <h3>{h.name}</h3>
              </div>
              <div className="hosp-item-stats">
                <div className="hosp-stat">
                  <BedDouble size={14} />
                  <span>{h.current_load}/{h.capacity}</span>
                </div>
                <div className="hosp-occupancy-mini">
                  <div className="occ-bar-mini" style={{
                    width: `${h.occupancy_pct}%`,
                    background: occupancyColor(h.occupancy_pct)
                  }}></div>
                </div>
                <span style={{ color: occupancyColor(h.occupancy_pct), fontWeight: 700, fontSize: ".85rem" }}>
                  {h.occupancy_pct}%
                </span>
                {h.incoming_ambulances > 0 && (
                  <div className="incoming-badge">
                    <Ambulance size={12} /> {h.incoming_ambulances} en camino
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Detail panel */}
        <div className="hosp-detail">
          {!selectedHospital && (
            <div className="hosp-empty">
              <Building2 size={48} strokeWidth={1} />
              <p>Selecciona un hospital para ver su dashboard</p>
            </div>
          )}
          {details && selectedHospital && (
            <>
              <div className="detail-header">
                <h2><Heart size={22} /> {details.hospital.name}</h2>
                <span className={`emergency-level el-${details.hospital.emergency_level}`}>
                  Nivel {details.hospital.emergency_level}
                </span>
              </div>

              <div className="detail-stats">
                <div className="detail-stat-card">
                  <BedDouble size={20} />
                  <div className="stat-num">{details.hospital.current_load} / {details.hospital.capacity}</div>
                  <div className="stat-label">Ocupación</div>
                  <div className="occ-bar-detail">
                    <div style={{ width: `${details.hospital.occupancy_pct}%`, background: occupancyColor(details.hospital.occupancy_pct) }}></div>
                  </div>
                </div>
                <div className="detail-stat-card">
                  <Ambulance size={20} />
                  <div className="stat-num">{details.incoming_ambulances.length}</div>
                  <div className="stat-label">Ambulancias en camino</div>
                </div>
                <div className="detail-stat-card">
                  <Users size={20} />
                  <div className="stat-num">{details.patients_in_er.length}</div>
                  <div className="stat-label">Pacientes en Urgencias</div>
                </div>
              </div>

              {/* Incoming ambulances */}
              {details.incoming_ambulances.length > 0 && (
                <div className="detail-section">
                  <h3><Ambulance size={18} /> Ambulancias Entrantes</h3>
                  <div className="incoming-list">
                    {details.incoming_ambulances.map((a, idx) => (
                      <div key={idx} className="incoming-card">
                        <div className="inc-header">
                          <span className="inc-vehicle">{a.vehicle_id || "—"}</span>
                          {a.vehicle_subtype && <span className={`subtype-badge st-${a.vehicle_subtype}`}>{a.vehicle_subtype}</span>}
                          <span className={`sev-badge sev-${a.severity}`}>Sev. {a.severity}</span>
                        </div>
                        <div className="inc-type">{a.incident_type} — {a.incident_id}</div>
                        {a.eta_progress != null && (
                          <div className="eta-bar-wrap">
                            <div className="eta-bar" style={{ width: `${Math.round(a.eta_progress * 100)}%` }}></div>
                            <span className="eta-pct">{Math.round(a.eta_progress * 100)}%</span>
                          </div>
                        )}
                        {a.affected_count > 1 && (
                          <div className="multi-victim"><AlertTriangle size={12} /> {a.affected_count} víctimas</div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Patients in ER */}
              {details.patients_in_er.length > 0 && (
                <div className="detail-section">
                  <h3><Users size={18} /> Pacientes en Urgencias</h3>
                  <table className="er-table">
                    <thead>
                      <tr><th>Paciente</th><th>Fase</th><th>Box</th><th>Ingreso</th></tr>
                    </thead>
                    <tbody>
                      {details.patients_in_er.map(pt => (
                        <tr key={pt.id}>
                          <td>{pt.patient_name || `Paciente #${pt.id}`}</td>
                          <td><span className={`phase-badge ph-${pt.phase}`}>{pt.phase}</span></td>
                          <td>{pt.bed || "—"}</td>
                          <td>{pt.admission_time ? new Date(pt.admission_time).toLocaleTimeString("es-ES") : "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
