import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { formatDistanceToNow } from "date-fns";
import { es } from "date-fns/locale";
import { ClipboardList, MapPin, AlertTriangle, Ambulance, Search, Filter, X } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { API_BASE } from "../config";
import "../styles/IncidentList.css";

// Helper function to format relative time properly
const formatRelativeTime = (dateStr) => {
  if (!dateStr) return "Hace un momento";

  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return "Ahora mismo";
  if (diffMins < 60) return `hace ${diffMins} minuto${diffMins > 1 ? 's' : ''}`;
  if (diffHours < 24) return `hace ${diffHours} hora${diffHours > 1 ? 's' : ''}`;
  if (diffDays < 7) return `hace ${diffDays} día${diffDays > 1 ? 's' : ''}`;

  return date.toLocaleString("es-ES", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  });
};

const STATUS_COLORS = {
  OPEN: "#f59e0b",
  ASSIGNED: "#3b82f6",
  EN_ROUTE: "#8b5cf6",
  ARRIVED: "#06b6d4",
  RESOLVED: "#10b981",
  CLOSED: "#6b7280",
};

const STATUS_LABELS = {
  OPEN: "Abierto",
  ASSIGNED: "Asignado",
  EN_ROUTE: "En Ruta",
  ARRIVED: "En Escena",
  RESOLVED: "Resuelto",
  CLOSED: "Cerrado",
};

const INCIDENT_TYPES = [
  "CARDIO", "RESPIRATORY", "NEUROLOGICAL", "TRAUMA", "BURN",
  "POISONING", "OBSTETRIC", "PEDIATRIC", "PSYCHIATRIC", "VIOLENCE",
  "ALLERGIC", "METABOLIC", "INTOXICATION", "DROWNING", "GENERAL",
];

export default function IncidentList() {
  const { user } = useAuth();
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("ALL");
  const [searchText, setSearchText] = useState("");
  const [severityFilter, setSeverityFilter] = useState("ALL");
  const [typeFilter, setTypeFilter] = useState("ALL");
  const [sortBy, setSortBy] = useState("newest");
  const [showFilters, setShowFilters] = useState(false);

  useEffect(() => {
    fetchIncidents();
    const interval = setInterval(fetchIncidents, 5000);
    const onCityChange = () => fetchIncidents();
    window.addEventListener("cityFilterChanged", onCityChange);
    return () => { clearInterval(interval); window.removeEventListener("cityFilterChanged", onCityChange); };
  }, []);

  const fetchIncidents = async () => {
    try {
      const city = localStorage.getItem("cityFilter") || "";
      const qs = city ? `?city=${encodeURIComponent(city)}` : "";
      const res = await fetch(`${API_BASE}/events/incidents${qs}`);
      const data = await res.json();
      setIncidents(data);
    } catch (error) {
      console.error("Error fetching incidents:", error);
    } finally {
      setLoading(false);
    }
  };

  const clearFilters = () => {
    setFilter("ALL"); setSearchText(""); setSeverityFilter("ALL"); setTypeFilter("ALL"); setSortBy("newest");
  };

  const activeFilterCount = [filter !== "ALL", searchText, severityFilter !== "ALL", typeFilter !== "ALL"].filter(Boolean).length;

  const filteredIncidents = incidents
    .filter((inc) => {
      if (filter !== "ALL" && inc.status !== filter) return false;
      if (severityFilter !== "ALL" && String(inc.severity) !== severityFilter) return false;
      if (typeFilter !== "ALL" && inc.incident_type !== typeFilter) return false;
      if (searchText) {
        const q = searchText.toLowerCase();
        return (
          (inc.id && inc.id.toLowerCase().includes(q)) ||
          (inc.incident_type && inc.incident_type.toLowerCase().includes(q)) ||
          (inc.address && inc.address.toLowerCase().includes(q)) ||
          (inc.description && inc.description.toLowerCase().includes(q)) ||
          (inc.assigned_vehicle_id && inc.assigned_vehicle_id.toLowerCase().includes(q))
        );
      }
      return true;
    })
    .sort((a, b) => {
      if (sortBy === "newest") return new Date(b.created_at || 0) - new Date(a.created_at || 0);
      if (sortBy === "oldest") return new Date(a.created_at || 0) - new Date(b.created_at || 0);
      if (sortBy === "severity_desc") return (b.severity || 0) - (a.severity || 0);
      if (sortBy === "severity_asc") return (a.severity || 0) - (b.severity || 0);
      return 0;
    });

  if (loading) {
    return <div className="loading">Cargando incidentes...</div>;
  }

  return (
    <div className="incident-list-page">
      <div className="page-header">
        <div>
          <h1><ClipboardList size={24} className="icon-3d" style={{marginRight:8,verticalAlign:'middle'}} /> Lista de Incidentes</h1>
          <p>Total: {incidents.length} incidentes — Mostrando: {filteredIncidents.length}</p>
        </div>
        {user?.role === "ADMIN" && (
          <Link to="/create-incident" className="create-btn">
            + Nuevo Incidente
          </Link>
        )}
      </div>

      {/* Search + toggle filters */}
      <div className="search-bar-row">
        <div className="search-input-wrap">
          <Search size={16} className="search-icon" />
          <input
            type="text"
            placeholder="Buscar por ID, tipo, dirección, vehículo..."
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            className="search-input"
          />
          {searchText && <button className="search-clear" onClick={() => setSearchText("")}><X size={14} /></button>}
        </div>
        <button className={`toggle-filters-btn ${showFilters ? "active" : ""}`} onClick={() => setShowFilters(v => !v)}>
          <Filter size={15} /> Filtros {activeFilterCount > 0 && <span className="filter-count-badge">{activeFilterCount}</span>}
        </button>
        {activeFilterCount > 0 && (
          <button className="clear-all-btn" onClick={clearFilters}>Limpiar filtros</button>
        )}
      </div>

      {/* Collapsible advanced filters */}
      {showFilters && (
        <div className="advanced-filters">
          <div className="filter-group">
            <label>Severidad</label>
            <select value={severityFilter} onChange={(e) => setSeverityFilter(e.target.value)} className="filter-select">
              <option value="ALL">Todas</option>
              {[5,4,3,2,1].map(s => <option key={s} value={String(s)}>Sev {s} {s >= 4 ? "🔴" : s === 3 ? "🟠" : "🟡"}</option>)}
            </select>
          </div>
          <div className="filter-group">
            <label>Tipo</label>
            <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)} className="filter-select">
              <option value="ALL">Todos</option>
              {INCIDENT_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>
          <div className="filter-group">
            <label>Ordenar por</label>
            <select value={sortBy} onChange={(e) => setSortBy(e.target.value)} className="filter-select">
              <option value="newest">Más reciente</option>
              <option value="oldest">Más antiguo</option>
              <option value="severity_desc">Severidad ↓</option>
              <option value="severity_asc">Severidad ↑</option>
            </select>
          </div>
        </div>
      )}

      <div className="filter-bar">
        {Object.keys(STATUS_LABELS).map(st => (
          <button
            key={st}
            className={`filter-btn ${filter === st ? "active" : ""}`}
            onClick={() => setFilter(filter === st ? "ALL" : st)}
          >
            {STATUS_LABELS[st]} ({incidents.filter((i) => i.status === st).length})
          </button>
        ))}
        <button
          className={`filter-btn ${filter === "ALL" ? "active" : ""}`}
          onClick={() => setFilter("ALL")}
        >
          Todos ({incidents.length})
        </button>
      </div>

      <div className="incidents-grid">
        {filteredIncidents.length === 0 ? (
          <div className="empty-state">
            <p>No hay incidentes que coincidan con los filtros</p>
          </div>
        ) : (
          filteredIncidents.map((incident) => (
            <Link
              key={incident.id}
              to={`/incidents/${incident.id}`}
              className="incident-card"
            >
              <div className="card-header">
                <span className="incident-id">{incident.id}</span>
                <span
                  className="status-badge"
                  style={{ background: STATUS_COLORS[incident.status] }}
                >
                  {STATUS_LABELS[incident.status] || incident.status}
                </span>
              </div>

              <div className="card-body">
                <div className="incident-type">
                  <strong>{incident.incident_type || "GENERAL"}</strong>
                  <span className="sev-dots">{"●".repeat(incident.severity)}{"○".repeat(5 - (incident.severity || 0))}</span>
                </div>
                {incident.description && (
                  <p className="incident-desc">{incident.description}</p>
                )}
                <div className="incident-meta">
                  <span><MapPin size={14} style={{verticalAlign:'middle',marginRight:3}} />{incident.address || `${incident.lat?.toFixed(4)}, ${incident.lon?.toFixed(4)}`}</span>
                  <span><AlertTriangle size={14} style={{verticalAlign:'middle',marginRight:3}} />Severidad: {incident.severity}</span>
                  {incident.assigned_vehicle_id && (
                    <span><Ambulance size={14} style={{verticalAlign:'middle',marginRight:3}} />{incident.assigned_vehicle_id}</span>
                  )}
                </div>
              </div>

              <div className="card-footer">
                <small>{formatRelativeTime(incident.created_at)}</small>
              </div>
            </Link>
          ))
        )}
      </div>
    </div>
  );
}
