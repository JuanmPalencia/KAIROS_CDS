import { useState, useEffect, useCallback } from "react";
import {
  Users, UserCheck, Building2, BedDouble, Ambulance,
  ArrowRight, Clock, RefreshCw, Home, AlertTriangle,
  Search, Filter, Database, ChevronRight, Eye, EyeOff
} from "lucide-react";
import "../styles/PatientTracking.css";
import { API_BASE } from "../config";

const API = API_BASE;
const _hdrs = () => ({ Authorization: `Bearer ${localStorage.getItem("token")}` });

const PHASES = [
  { key: "ON_SCENE", label: "En Escena", icon: <AlertTriangle size={16} />, color: "#ef4444" },
  { key: "IN_AMBULANCE", label: "En Ambulancia", icon: <Ambulance size={16} />, color: "#3b82f6" },
  { key: "AT_HOSPITAL_ER", label: "Urgencias", icon: <Building2 size={16} />, color: "#f59e0b" },
  { key: "ADMITTED", label: "Hospitalizado", icon: <BedDouble size={16} />, color: "#8b5cf6" },
  { key: "DISCHARGED", label: "Alta", icon: <Home size={16} />, color: "#22c55e" },
];

const NEXT_PHASE = {
  ON_SCENE: "IN_AMBULANCE",
  IN_AMBULANCE: "AT_HOSPITAL_ER",
  AT_HOSPITAL_ER: "ADMITTED",
  ADMITTED: "DISCHARGED",
};

export default function PatientTracking() {
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchPt, setSearchPt] = useState("");
  const [phaseFilter, setPhaseFilter] = useState("ALL");
  const [seeding, setSeeding] = useState(false);
  const [showAll, setShowAll] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const url = showAll ? `${API}/api/epcr/all-tracking-full` : `${API}/api/epcr/all-tracking`;
      const res = await fetch(url);
      if (res.ok) setPatients(await res.json());
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, [showAll]);

  const seedPatients = useCallback(async () => {
    setSeeding(true);
    try {
      const res = await fetch(`${API}/api/epcr/seed-demo-patients`, { method: "POST" });
      if (res.ok) await fetchData();
    } catch (e) { console.error(e); }
    finally { setSeeding(false); }
  }, [fetchData]);

  const advancePhase = useCallback(async (trackingId, nextPhase) => {
    try {
      const res = await fetch(`${API}/api/epcr/tracking/${trackingId}/phase`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phase: nextPhase }),
      });
      if (res.ok) await fetchData();
    } catch (e) { console.error(e); }
  }, [fetchData]);

  useEffect(() => {
    fetchData();
    const iv = setInterval(fetchData, 5000);
    return () => clearInterval(iv);
  }, [fetchData]);

  const phaseBadge = (phase) => {
    const p = PHASES.find(x => x.key === phase) || PHASES[0];
    return (
      <span className="phase-tag" style={{ background: `${p.color}18`, color: p.color, borderColor: p.color }}>
        {p.icon} {p.label}
      </span>
    );
  };

  if (loading) return <div className="pt-loading"><RefreshCw className="spin" size={24} /> Cargando tracking...</div>;

  // Group by phase
  const grouped = {};
  PHASES.forEach(p => { grouped[p.key] = []; });
  patients.forEach(pt => {
    if (grouped[pt.current_phase]) grouped[pt.current_phase].push(pt);
  });

  const totalActive = patients.length;

  return (
    <div className="pt-page">
      <div className="pt-header">
        <h1><Users size={28} /> Seguimiento de Pacientes</h1>
        <div className="pt-total">
          <UserCheck size={18} /> {totalActive} pacientes activos
        </div>
      </div>

      <div className="pt-filters">
        <div className="pt-search-wrap">
          <Search size={16} />
          <input type="text" placeholder="Buscar paciente, incidente o vehículo..." value={searchPt} onChange={(e) => setSearchPt(e.target.value)} className="pt-search" />
          {searchPt && <button className="pt-search-clear" onClick={() => setSearchPt("")}>×</button>}
        </div>
        <div className="pt-filter-group">
          <label><Filter size={14} /> Fase</label>
          <select value={phaseFilter} onChange={(e) => setPhaseFilter(e.target.value)} className="pt-select">
            <option value="ALL">Todas</option>
            {PHASES.map(p => <option key={p.key} value={p.key}>{p.label}</option>)}
          </select>
        </div>
        <button className="pt-toggle-btn" onClick={() => setShowAll(!showAll)} title={showAll ? "Solo activos" : "Mostrar todos"}>
          {showAll ? <><EyeOff size={14} /> Solo activos</> : <><Eye size={14} /> Incluir altas</>}
        </button>
        {(searchPt || phaseFilter !== "ALL") && (
          <button className="pt-clear-btn" onClick={() => { setSearchPt(""); setPhaseFilter("ALL"); }}>Limpiar</button>
        )}
      </div>

      {/* Phase pipeline */}
      <div className="phase-pipeline">
        {PHASES.filter(p => p.key !== "DISCHARGED").map((p, idx) => (
          <div key={p.key} className="pipeline-stage">
            <div className="pipeline-icon" style={{ background: p.color }}>{p.icon}</div>
            <div className="pipeline-label">{p.label}</div>
            <div className="pipeline-count">{grouped[p.key]?.length || 0}</div>
            {idx < 3 && <ArrowRight size={18} className="pipeline-arrow" />}
          </div>
        ))}
      </div>

      {/* Patient cards by phase */}
      {PHASES.filter(p => showAll || p.key !== "DISCHARGED").filter(p => phaseFilter === "ALL" || p.key === phaseFilter).map(phase => {
        const phasePatients = (grouped[phase.key] || []).filter(pt => {
          if (!searchPt) return true;
          const term = searchPt.toLowerCase();
          return (pt.patient_name || "").toLowerCase().includes(term)
            || (pt.incident_id || "").toLowerCase().includes(term)
            || (pt.vehicle_id || "").toLowerCase().includes(term)
            || (pt.hospital_id || "").toLowerCase().includes(term);
        });
        return phasePatients.length > 0 && (
          <div key={phase.key} className="phase-section">
            <h2 style={{ color: phase.color }}>
              {phase.icon} {phase.label} ({phasePatients.length})
            </h2>
            <div className="patients-grid">
              {phasePatients.map(pt => (
                <div key={pt.id} className="patient-card" style={{ borderLeftColor: phase.color }}>
                  <div className="pt-card-header">
                    <span className="pt-name">{pt.patient_name || `Paciente #${pt.id}`}</span>
                    {phaseBadge(pt.current_phase)}
                  </div>
                  <div className="pt-card-details">
                    <div className="pt-detail"><AlertTriangle size={12} /> {pt.incident_id}</div>
                    {pt.vehicle_id && <div className="pt-detail"><Ambulance size={12} /> {pt.vehicle_id}</div>}
                    {pt.hospital_id && <div className="pt-detail"><Building2 size={12} /> {pt.hospital_id}</div>}
                    {pt.hospital_bed && <div className="pt-detail"><BedDouble size={12} /> Box: {pt.hospital_bed}</div>}
                    <div className="pt-detail"><Clock size={12} /> {pt.created_at ? new Date(pt.created_at).toLocaleTimeString("es-ES") : "—"}</div>
                  </div>
                  {NEXT_PHASE[pt.current_phase] && (
                    <button
                      className="pt-advance-btn"
                      style={{ borderColor: PHASES.find(p => p.key === NEXT_PHASE[pt.current_phase])?.color || "#6366f1" }}
                      onClick={() => advancePhase(pt.id, NEXT_PHASE[pt.current_phase])}
                    >
                      <ChevronRight size={14} /> Avanzar a {PHASES.find(p => p.key === NEXT_PHASE[pt.current_phase])?.label}
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        );
      })}

      {totalActive === 0 && (
        <div className="pt-empty">
          <Users size={48} strokeWidth={1} />
          <p>No hay pacientes en seguimiento activo</p>
          <p className="pt-hint">Los pacientes aparecerán cuando se creen ePCR desde los incidentes</p>
          <button className="pt-seed-btn" onClick={seedPatients} disabled={seeding}>
            {seeding ? <><RefreshCw className="spin" size={16} /> Cargando...</> : <><Database size={16} /> Cargar pacientes de demo</>}
          </button>
        </div>
      )}
    </div>
  );
}
