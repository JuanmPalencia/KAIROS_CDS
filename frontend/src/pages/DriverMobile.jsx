import { useState, useEffect, useRef } from "react";
import {
  Truck, Navigation, MapPin, Clock, Fuel, Phone,
  AlertTriangle, CheckCircle2, ArrowRight, RefreshCw,
  User, Radio, Activity, ChevronDown, ChevronUp, Bell,
  LogOut, Sun, Moon, ArrowLeft
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";
import { statusLabel } from "../utils/statusLabels";
import logoKairos from "../assets/logo_kairos.png";
import "../styles/DriverMobile.css";
import { API_BASE } from "../config";

const API = API_BASE;
const hdrs = () => ({ Authorization: `Bearer ${localStorage.getItem("token")}` });

const STATUS_FLOW = [
  { key: "IDLE", label: "Disponible", color: "#22c55e", icon: <CheckCircle2 size={20} /> },
  { key: "EN_ROUTE", label: "En Ruta", color: "#3b82f6", icon: <Navigation size={20} /> },
  { key: "ON_SCENE", label: "En Escena", color: "#f59e0b", icon: <MapPin size={20} /> },
  { key: "RETURNING", label: "Retornando", color: "#8b5cf6", icon: <ArrowRight size={20} /> },
];

export default function DriverMobile() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [vehicle, setVehicle] = useState(null);
  const [allVehicles, setAllVehicles] = useState([]);
  const [incident, setIncident] = useState(null);
  const [loading, setLoading] = useState(true);
  const [updatingStatus, setUpdatingStatus] = useState(false);
  const [expandedIncident, setExpandedIncident] = useState(true);
  const [notifications, setNotifications] = useState([]);
  const [darkMode, setDarkMode] = useState(() => localStorage.getItem("theme") === "dark");
  const [selectedVehicleId, setSelectedVehicleId] = useState(() =>
    localStorage.getItem("driverVehicleId") || ""
  );
  const prevDataRef = useRef(null);

  // Sync theme
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", darkMode ? "dark" : "light");
    localStorage.setItem("theme", darkMode ? "dark" : "light");
  }, [darkMode]);

  const handleLogout = () => {
    logout();
    navigate("/driver-login");
  };

  const handleBackToPanel = () => {
    navigate("/");
  };

  const fetchDriverData = async () => {
    try {
      const vRes = await fetch(`${API}/fleet/vehicles`, { headers: hdrs() });
      if (vRes.ok) {
        const vehicles = await vRes.json();
        // Stable sort so list doesn't jump
        vehicles.sort((a, b) => a.id.localeCompare(b.id));
        // Only update if data actually changed
        const key = JSON.stringify(vehicles.map(v => `${v.id}:${v.status}:${v.lat}:${v.lon}:${v.fuel}`));
        if (key !== prevDataRef.current) {
          prevDataRef.current = key;
          setAllVehicles(vehicles);
        }

        // Use the saved vehicle selection, or fall back to first
        const savedId = selectedVehicleId || localStorage.getItem("driverVehicleId");
        const assigned = savedId
          ? vehicles.find(v => v.id === savedId)
          : vehicles[0];
        setVehicle(assigned || null);

        // If vehicle is en_route or on_scene, fetch its incident
        if (assigned && ["EN_ROUTE", "ON_SCENE"].includes(assigned.status)) {
          const iRes = await fetch(`${API}/events/incidents`, { headers: hdrs() });
          if (iRes.ok) {
            const incidents = await iRes.json();
            const active = incidents.find(i =>
              (i.vehicle_id === assigned.id || i.assigned_vehicle_id === assigned.id) &&
              ["ASSIGNED", "EN_ROUTE", "ON_SCENE"].includes(i.status)
            );
            setIncident(active || null);
          }
        } else {
          setIncident(null);
        }
      }
    } catch (e) {
      console.error("Driver data fetch error:", e);
    } finally {
      setLoading(false);
    }
  };

  const selectVehicle = (vid) => {
    setSelectedVehicleId(vid);
    localStorage.setItem("driverVehicleId", vid);
    const v = allVehicles.find(x => x.id === vid);
    setVehicle(v || null);
    setIncident(null);
  };

  useEffect(() => {
    fetchDriverData();
    const iv = setInterval(fetchDriverData, 8000);
    return () => clearInterval(iv);
  }, [selectedVehicleId]);

  const changeStatus = async (newStatus) => {
    if (!vehicle || updatingStatus) return;
    setUpdatingStatus(true);
    try {
      const res = await fetch(`${API}/fleet/vehicles/${vehicle.id}`, {
        method: "PATCH",
        headers: { ...hdrs(), "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus }),
      });
      if (res.ok) {
        setVehicle(prev => ({ ...prev, status: newStatus }));
        setNotifications(prev => [{
          id: Date.now(),
          text: `Estado cambiado a ${STATUS_FLOW.find(s => s.key === newStatus)?.label || newStatus}`,
          time: new Date().toLocaleTimeString("es-ES", { hour: "2-digit", minute: "2-digit" })
        }, ...prev.slice(0, 4)]);
      }
    } catch (e) { console.error("Status change error:", e); }
    setUpdatingStatus(false);
  };

  const currentStatus = STATUS_FLOW.find(s => s.key === vehicle?.status) || STATUS_FLOW[0];
  const fuelColor = (pct) => pct > 50 ? "#22c55e" : pct > 25 ? "#f59e0b" : "#ef4444";

  if (loading) return (
    <div className="driver-loading">
      <RefreshCw className="spin" size={32} />
      <span>Cargando datos del conductor...</span>
    </div>
  );

  return (
    <div className="driver-page">
      {/* Standalone mobile header */}
      <div className="driver-topbar">
        <div className="driver-brand">
          <img src={logoKairos} alt="KAIROS" className="driver-brand-logo" />
          <span className="driver-brand-name">KAIROS</span>
        </div>
        <div className="driver-live-badge">
          <Radio size={14} className="pulse" /> EN LÍNEA
        </div>
        <div className="driver-topbar-actions">
          <button className="driver-theme-btn" onClick={() => setDarkMode(v => !v)} title={darkMode ? "Modo claro" : "Modo oscuro"}>
            {darkMode ? <Sun size={18} /> : <Moon size={18} />}
          </button>
          <div className="driver-user">
            <User size={16} />
            <span>{user?.username || "Conductor"}</span>
          </div>
          {(user?.role === "ADMIN" || user?.role === "OPERATOR") && (
            <button className="driver-back-btn" onClick={handleBackToPanel} title="Volver al panel">
              <ArrowLeft size={16} /> Panel
            </button>
          )}
          <button className="driver-logout-btn" onClick={handleLogout} title="Cerrar sesión">
            <LogOut size={18} />
          </button>
        </div>
      </div>

      {/* Vehicle Selector */}
      {allVehicles.length > 0 && (
        <div className="driver-vehicle-selector">
          <label><Truck size={16} /> Seleccionar vehículo:</label>
          <select
            value={selectedVehicleId || vehicle?.id || ""}
            onChange={(e) => selectVehicle(e.target.value)}
            className="dvs-select"
          >
            <option value="">— Elegir vehículo —</option>
            {allVehicles.map(v => (
              <option key={v.id} value={v.id}>
                {v.id} ({v.subtype || "SVB"}) — {statusLabel(v.status)}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Vehicle Card */}
      {vehicle ? (
        <div className="driver-vehicle-card">
          <div className="dvc-header">
            <Truck size={24} />
            <div>
              <h2>{vehicle.id}</h2>
              <span className="dvc-subtype">{vehicle.subtype || "SVB"}</span>
            </div>
            <div className="dvc-status" style={{ background: `${currentStatus.color}18`, color: currentStatus.color, borderColor: currentStatus.color }}>
              {currentStatus.icon}
              <span>{currentStatus.label}</span>
            </div>
          </div>

          {/* Fuel */}
          <div className="dvc-fuel">
            <div className="dvc-fuel-header">
              <Fuel size={16} /> Combustible
              <span style={{ color: fuelColor(vehicle.fuel ?? 0) }}>{Math.round(vehicle.fuel ?? 0)}%</span>
            </div>
            <div className="dvc-fuel-bar-bg">
              <div className="dvc-fuel-bar" style={{
                width: `${vehicle.fuel ?? 0}%`,
                background: fuelColor(vehicle.fuel ?? 0)
              }}></div>
            </div>
          </div>

          {/* Location */}
          {vehicle.lat && vehicle.lon && (
            <div className="dvc-location">
              <MapPin size={14} />
              <span>{vehicle.lat.toFixed(4)}, {vehicle.lon.toFixed(4)}</span>
            </div>
          )}
        </div>
      ) : (
        <div className="driver-no-vehicle">
          <Truck size={48} strokeWidth={1} />
          <p>Sin vehículo asignado</p>
        </div>
      )}

      {/* Active Incident */}
      {incident && (
        <div className="driver-incident-card">
          <div className="dic-header" onClick={() => setExpandedIncident(!expandedIncident)}>
            <AlertTriangle size={20} className="dic-alert" />
            <div className="dic-title">
              <h3>Incidente Activo</h3>
              <span className="dic-type">{incident.type}</span>
            </div>
            {expandedIncident ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
          </div>
          {expandedIncident && (
            <div className="dic-body">
              <div className="dic-row">
                <AlertTriangle size={14} />
                <strong>Severidad:</strong>
                <span className={`dic-sev sev-${incident.severity}`}>
                  {"●".repeat(incident.severity || 1)}
                </span>
              </div>
              <div className="dic-row">
                <MapPin size={14} />
                <strong>Ubicación:</strong>
                <span>{incident.lat?.toFixed(4)}, {incident.lon?.toFixed(4)}</span>
              </div>
              {incident.description && (
                <div className="dic-row">
                  <Activity size={14} />
                  <strong>Detalle:</strong>
                  <span>{incident.description}</span>
                </div>
              )}
              {incident.caller_phone && (
                <a href={`tel:${incident.caller_phone}`} className="dic-call-btn">
                  <Phone size={16} /> Llamar: {incident.caller_phone}
                </a>
              )}
            </div>
          )}
        </div>
      )}

      {!incident && vehicle && vehicle.status === "IDLE" && (
        <div className="driver-standby">
          <CheckCircle2 size={32} />
          <h3>En espera</h3>
          <p>No tienes incidentes asignados. Mantente disponible.</p>
        </div>
      )}

      {/* Status quick-change buttons */}
      {vehicle && (
        <div className="driver-status-section">
          <h3><Activity size={18} /> Cambiar Estado</h3>
          <div className="status-buttons">
            {STATUS_FLOW.map(st => (
              <button
                key={st.key}
                className={`status-btn ${vehicle?.status === st.key ? "active" : ""}`}
                style={{
                  "--btn-color": st.color,
                  background: vehicle?.status === st.key ? st.color : "transparent",
                  color: vehicle?.status === st.key ? "#fff" : st.color,
                  borderColor: st.color,
                }}
                disabled={updatingStatus || vehicle?.status === st.key}
                onClick={() => changeStatus(st.key)}
              >
                {st.icon}
                <span>{st.label}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Recent notifications */}
      {notifications.length > 0 && (
        <div className="driver-notif-section">
          <h3><Bell size={18} /> Actividad Reciente</h3>
          <div className="notif-list">
            {notifications.map(n => (
              <div key={n.id} className="notif-item">
                <Clock size={12} />
                <span className="notif-time">{n.time}</span>
                <span>{n.text}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
