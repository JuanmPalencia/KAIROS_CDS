import { useState, useEffect } from "react";
import {
  Users, UserPlus, Clock, Stethoscope, ShieldCheck,
  Phone, Ambulance, BadgeCheck, CalendarDays, RefreshCw,
  Search, Filter
} from "lucide-react";
import "../styles/CrewManagement.css";
import { API_BASE } from "../config";

const API = API_BASE;
const hdrs = () => ({ Authorization: `Bearer ${localStorage.getItem("token")}` });

const ROLE_LABELS = { MEDICO: "Médico", ENFERMERO: "Enfermero/a", TES: "TES", CONDUCTOR: "Conductor/a" };
const ROLE_COLORS = { MEDICO: "#ef4444", ENFERMERO: "#3b82f6", TES: "#22c55e", CONDUCTOR: "#f59e0b" };
const SHIFT_LABELS = { DIA: "Día (8-20h)", NOCHE: "Noche (20-8h)", GUARDIA_24H: "Guardia 24h" };
const STATUS_LABELS = { ACTIVE: "Activo", COMPLETED: "Finalizado", SCHEDULED: "Programado", CANCELLED: "Cancelado" };

export default function CrewManagement() {
  const [members, setMembers] = useState([]);
  const [shifts, setShifts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState("crew"); // crew | shifts
  const [searchName, setSearchName] = useState("");
  const [roleFilter, setRoleFilter] = useState("ALL");
  const [shiftTypeFilter, setShiftTypeFilter] = useState("ALL");

  const fetchData = async () => {
    try {
      const [mRes, sRes] = await Promise.all([
        fetch(`${API}/api/crews/members`, { headers: hdrs() }),
        fetch(`${API}/api/crews/shifts`, { headers: hdrs() }),
      ]);
      if (mRes.ok) setMembers(await mRes.json());
      if (sRes.ok) setShifts(await sRes.json());
    } catch (e) {
      console.error("Crew fetch error:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const [seeding, setSeeding] = useState(false);
  const [seeded, setSeeded] = useState(false);
  const seedCrew = async () => {
    setSeeding(true);
    try {
      const res = await fetch(`${API}/api/crews/seed`, { method: "POST", headers: hdrs() });
      if (res.ok) { setSeeded(true); setTimeout(() => setSeeded(false), 2500); }
    } catch (e) { console.error("Seed error:", e); }
    setSeeding(false);
    fetchData();
  };

  const endShift = async (shiftId) => {
    try {
      const res = await fetch(`${API}/api/crews/shifts/${shiftId}/end`, { method: "POST", headers: hdrs() });
      if (res.ok) fetchData();
    } catch (e) { console.error("End shift error:", e); }
  };

  const getShiftForMember = (memberId) => shifts.find(s => s.crew_member_id === memberId);

  if (loading) return <div className="crew-loading"><RefreshCw className="spin" size={24} /> Cargando tripulación...</div>;

  return (
    <div className="crew-page">
      <div className="crew-header">
        <h1><Users size={28} /> Gestión de Tripulaciones</h1>
        <div className="crew-actions">
          <button className="seed-btn" onClick={seedCrew} disabled={seeding}>
            <UserPlus size={16} /> {seeding ? "Sembrando..." : seeded ? "✓ Creados" : "Seed Tripulación"}
          </button>
        </div>
      </div>

      <div className="crew-tabs">
        <button className={`tab ${tab === "crew" ? "active" : ""}`} onClick={() => setTab("crew")}>
          <Stethoscope size={16} /> Personal ({members.length})
        </button>
        <button className={`tab ${tab === "shifts" ? "active" : ""}`} onClick={() => setTab("shifts")}>
          <CalendarDays size={16} /> Turnos Activos ({shifts.length})
        </button>
      </div>

      {tab === "crew" && (
        <>
        <div className="crew-filters">
          <div className="crew-search-wrap">
            <Search size={16} />
            <input type="text" placeholder="Buscar por nombre..." value={searchName} onChange={(e) => setSearchName(e.target.value)} className="crew-search" />
            {searchName && <button className="crew-search-clear" onClick={() => setSearchName("")}>×</button>}
          </div>
          <div className="crew-filter-group">
            <label><Filter size={14} /> Rol</label>
            <select value={roleFilter} onChange={(e) => setRoleFilter(e.target.value)} className="crew-select">
              <option value="ALL">Todos</option>
              <option value="MEDICO">Médico</option>
              <option value="ENFERMERO">Enfermero/a</option>
              <option value="TES">TES</option>
              <option value="CONDUCTOR">Conductor/a</option>
            </select>
          </div>
          {(searchName || roleFilter !== "ALL") && (
            <button className="crew-clear-btn" onClick={() => { setSearchName(""); setRoleFilter("ALL"); }}>Limpiar</button>
          )}
        </div>
        <div className="crew-grid">
          {members.length === 0 && (
            <div className="empty-state">
              <Users size={48} strokeWidth={1} />
              <p>No hay personal registrado. Pulsa <strong>Seed Tripulación</strong> para crear datos de ejemplo.</p>
            </div>
          )}
          {members.filter(m => {
            if (searchName && !m.name.toLowerCase().includes(searchName.toLowerCase())) return false;
            if (roleFilter !== "ALL" && m.role !== roleFilter) return false;
            return true;
          }).map(m => {
            const shift = getShiftForMember(m.id);
            return (
              <div key={m.id} className="crew-card">
                <div className="crew-card-header">
                  <div className="crew-avatar" style={{ background: ROLE_COLORS[m.role] || "#64748b" }}>
                    {m.name.split(" ").map(n => n[0]).join("").slice(0, 2).toUpperCase()}
                  </div>
                  <div>
                    <h3>{m.name}</h3>
                    <span className="crew-role" style={{ color: ROLE_COLORS[m.role] }}>
                      {ROLE_LABELS[m.role] || m.role}
                    </span>
                  </div>
                </div>
                <div className="crew-card-body">
                  {m.certification && (
                    <div className="crew-detail">
                      <BadgeCheck size={14} />
                      <span>{m.certification.split(",").join(" · ")}</span>
                    </div>
                  )}
                  {m.phone && (
                    <div className="crew-detail">
                      <Phone size={14} />
                      <span>{m.phone}</span>
                    </div>
                  )}
                  {shift && (
                    <div className="crew-shift-badge">
                      <Ambulance size={14} />
                      <span>{shift.vehicle_id}</span>
                      <span className="shift-type">{SHIFT_LABELS[shift.shift_type] || shift.shift_type}</span>
                    </div>
                  )}
                  {!shift && (
                    <div className="crew-no-shift">Sin turno activo</div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
        </>
      )}

      {tab === "shifts" && (
        <>
        <div className="crew-filters">
          <div className="crew-search-wrap">
            <Search size={16} />
            <input type="text" placeholder="Buscar miembro o vehículo..." value={searchName} onChange={(e) => setSearchName(e.target.value)} className="crew-search" />
            {searchName && <button className="crew-search-clear" onClick={() => setSearchName("")}>×</button>}
          </div>
          <div className="crew-filter-group">
            <label><Filter size={14} /> Turno</label>
            <select value={shiftTypeFilter} onChange={(e) => setShiftTypeFilter(e.target.value)} className="crew-select">
              <option value="ALL">Todos</option>
              <option value="DIA">Día</option>
              <option value="NOCHE">Noche</option>
              <option value="GUARDIA_24H">Guardia 24h</option>
            </select>
          </div>
          {(searchName || shiftTypeFilter !== "ALL") && (
            <button className="crew-clear-btn" onClick={() => { setSearchName(""); setShiftTypeFilter("ALL"); }}>Limpiar</button>
          )}
        </div>
        <div className="shifts-table-wrap">
          <table className="shifts-table">
            <thead>
              <tr>
                <th>Miembro</th>
                <th>Vehículo</th>
                <th>Turno</th>
                <th>Inicio</th>
                <th>Fin</th>
                <th>Estado</th>
                <th>Acción</th>
              </tr>
            </thead>
            <tbody>
              {shifts.filter(s => {
                const member = members.find(m => m.id === s.crew_member_id);
                if (searchName) {
                  const term = searchName.toLowerCase();
                  const nameMatch = member?.name?.toLowerCase().includes(term);
                  const vehicleMatch = s.vehicle_id?.toLowerCase().includes(term);
                  if (!nameMatch && !vehicleMatch) return false;
                }
                if (shiftTypeFilter !== "ALL" && s.shift_type !== shiftTypeFilter) return false;
                return true;
              }).map(s => {
                const member = members.find(m => m.id === s.crew_member_id);
                return (
                  <tr key={s.id}>
                    <td>
                      <div className="shift-member">
                        <strong>{member?.name || s.crew_member_id}</strong>
                        {member && <span className="shift-role" style={{ color: ROLE_COLORS[member.role] }}>{ROLE_LABELS[member.role]}</span>}
                      </div>
                    </td>
                    <td><span className="vehicle-tag">{s.vehicle_id || "—"}</span></td>
                    <td>{SHIFT_LABELS[s.shift_type] || s.shift_type}</td>
                    <td>{s.start_time ? new Date(s.start_time).toLocaleTimeString("es-ES", { hour: "2-digit", minute: "2-digit" }) : "—"}</td>
                    <td>{s.end_time ? new Date(s.end_time).toLocaleTimeString("es-ES", { hour: "2-digit", minute: "2-digit" }) : "—"}</td>
                    <td><span className={`shift-status-badge s-${s.status}`}>{STATUS_LABELS[s.status] || s.status}</span></td>
                    <td>
                      {s.status === "ACTIVE" && (
                        <button className="shift-end-btn" onClick={() => endShift(s.id)}>Finalizar</button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        </>
      )}
    </div>
  );
}
