import { Link, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useState, useEffect, useRef, memo } from "react";
import logoKairos from "../assets/logo_kairos.png";
import logoGtp from "../assets/logo_gtp.jpeg";
import {
  LayoutDashboard,
  ClipboardList,
  AlertTriangle,
  BarChart3,
  BrainCircuit,
  ScrollText,
  Sun,
  Moon,
  LogOut,
  User,
  Shield,
  ShieldCheck,
  Gauge,
  Users,
  Building2,
  Stethoscope,
  UserCheck,
  MapPin,
  ChevronDown,
  Radio,
  Activity,
  HeartPulse,
  Clock,
  Truck,
} from "lucide-react";
import "../styles/Layout.css";
import { API_BASE } from "../config";
import ChatWidget from "./ChatWidget";

/* ── Isolated clock component — only this rerenders every second ── */
const NavClock = memo(function NavClock() {
  const [now, setNow] = useState(new Date());

  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  const getShiftLabel = (d) => {
    const h = d.getHours();
    if (h >= 7 && h < 14) return { label: "Mañana", color: "#f59e0b" };
    if (h >= 14 && h < 22) return { label: "Tarde", color: "#3b82f6" };
    return { label: "Noche", color: "#8b5cf6" };
  };
  const shift = getShiftLabel(now);

  return (
    <div className="nav-clock" title={`Turno: ${shift.label} (07-15 / 15-23 / 23-07)`}>
      <Clock size={14} />
      <span className="clock-time">{now.toLocaleTimeString("es-ES", { hour: "2-digit", minute: "2-digit", second: "2-digit" })}</span>
      <span className="clock-shift" style={{ background: shift.color }}>{shift.label}</span>
    </div>
  );
});

function DropdownMenu({
  name,
  icon,
  label,
  items,
  openDropdown,
  openMenu,
  closeMenu,
  isInGroup,
  isActive,
  setOpenDropdown,
}) {
  if (items.length === 0) return null;
  const paths = items.map((i) => i.to);
  const active = isInGroup(paths);
  return (
    <div
      className={`nav-dropdown ${openDropdown === name ? "open" : ""}`}
      onMouseEnter={() => openMenu(name)}
      onMouseLeave={closeMenu}
    >
      <button
        className={`nav-link nav-dropdown-trigger ${active ? "active" : ""}`}
        onMouseEnter={() => openMenu(name)}
        aria-expanded={openDropdown === name}
        aria-haspopup="true"
      >
        <span className="icon-3d" aria-hidden="true">{icon}</span> {label} <ChevronDown size={13} className="chevron" aria-hidden="true" />
      </button>
      {openDropdown === name && (
        <div className="nav-dropdown-menu">
          {items.map((item) => (
            <Link
              key={item.to}
              to={item.to}
              className={`dropdown-item ${isActive(item.to) ? "active" : ""}`}
              onClick={() => setOpenDropdown(null)}
            >
              {item.icon} {item.label}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

export default function Layout({ children }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [darkMode, setDarkMode] = useState(() => {
    return localStorage.getItem("theme") === "dark";
  });
  const [cityFilter, setCityFilter] = useState(() => localStorage.getItem("cityFilter") || "");
  const [cities, setCities] = useState([]);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", darkMode ? "dark" : "light");
    localStorage.setItem("theme", darkMode ? "dark" : "light");
  }, [darkMode]);

  useEffect(() => {
    fetch(`${API_BASE}/api/cities`)
      .then(r => r.ok ? r.json() : { cities: [] })
      .then(d => setCities(d.cities || []))
      .catch(() => {});
  }, []);

  useEffect(() => {
    localStorage.setItem("cityFilter", cityFilter);
    window.dispatchEvent(new Event("cityFilterChanged"));
  }, [cityFilter]);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const isActive = (path) => location.pathname === path;
  const isInGroup = (paths) => paths.some(p => location.pathname === p);

  // Dropdown state
  const [openDropdown, setOpenDropdown] = useState(null);
  const dropdownTimeout = useRef(null);

  const openMenu = (name) => {
    clearTimeout(dropdownTimeout.current);
    setOpenDropdown(name);
  };
  const closeMenu = () => {
    dropdownTimeout.current = setTimeout(() => setOpenDropdown(null), 300);
  };

  // Role-based navigation access
  const role = user?.role;
  const canAccess = {
    createIncident: role === "ADMIN",
    aiInsights:     ["ADMIN", "OPERATOR"].includes(role),
    audit:          role === "ADMIN",
    crews:          ["ADMIN", "OPERATOR"].includes(role),
    hospitals:      ["ADMIN", "OPERATOR"].includes(role),
    paramedic:      ["ADMIN", "OPERATOR", "DOCTOR"].includes(role),
    patients:       ["ADMIN", "OPERATOR", "DOCTOR"].includes(role),
  };

  // Build dropdown groups — only include items the user can see
  const operacionesItems = [
    canAccess.createIncident && { to: "/create-incident", icon: <AlertTriangle size={16} />, label: "Crear Incidente" },
    canAccess.crews          && { to: "/crew",            icon: <Users size={16} />,          label: "Tripulaciones" },
    canAccess.hospitals      && { to: "/hospital-dashboard", icon: <Building2 size={16} />,   label: "Hospitales" },
    { to: "/driver", icon: <Truck size={16} />, label: "App Conductor" },
  ].filter(Boolean);

  const analisisItems = [
    { to: "/analytics",  icon: <BarChart3 size={16} />,    label: "Analytics" },
    { to: "/kpis",       icon: <Gauge size={16} />,        label: "KPIs" },
    canAccess.aiInsights && { to: "/ai-insights", icon: <BrainCircuit size={16} />, label: "AI Insights" },
  ].filter(Boolean);

  const clinicoItems = [
    canAccess.paramedic && { to: "/paramedic",        icon: <Stethoscope size={16} />, label: "Paramédico" },
    canAccess.patients  && { to: "/patient-tracking",  icon: <UserCheck size={16} />,   label: "Pacientes" },
  ].filter(Boolean);

  return (
    <div className="layout">
      {/* Skip to content link for keyboard users */}
      <a href="#main-content" className="skip-link">Saltar al contenido</a>
      <nav className="navbar" role="navigation" aria-label="Navegación principal">
        <div className="nav-brand">
          <img src={logoKairos} alt="KAIROS" className="brand-logo" />
          <span className="brand-name">KAIROS</span>
          <span className="brand-separator">|</span>
          <img src={logoGtp} alt="GTP" className="brand-logo-gtp" />
        </div>

        <div className="nav-links">
          <Link
            to="/"
            className={`nav-link ${isActive("/") ? "active" : ""}`}
          >
            <span className="icon-3d"><LayoutDashboard size={18} /></span> Dashboard
          </Link>
          <Link
            to="/incidents"
            className={`nav-link ${isActive("/incidents") ? "active" : ""}`}
          >
            <span className="icon-3d"><ClipboardList size={18} /></span> Incidentes
          </Link>

          {operacionesItems.length > 0 && (
            <DropdownMenu
              name="ops"
              icon={<Radio size={18} />}
              label="Operaciones"
              items={operacionesItems}
              openDropdown={openDropdown}
              openMenu={openMenu}
              closeMenu={closeMenu}
              isInGroup={isInGroup}
              isActive={isActive}
              setOpenDropdown={setOpenDropdown}
            />
          )}

          <DropdownMenu
            name="analytics"
            icon={<Activity size={18} />}
            label="Análisis"
            items={analisisItems}
            openDropdown={openDropdown}
            openMenu={openMenu}
            closeMenu={closeMenu}
            isInGroup={isInGroup}
            isActive={isActive}
            setOpenDropdown={setOpenDropdown}
          />

          {clinicoItems.length > 0 && (
            <DropdownMenu
              name="clinico"
              icon={<HeartPulse size={18} />}
              label="Clínico"
              items={clinicoItems}
              openDropdown={openDropdown}
              openMenu={openMenu}
              closeMenu={closeMenu}
              isInGroup={isInGroup}
              isActive={isActive}
              setOpenDropdown={setOpenDropdown}
            />
          )}

          {canAccess.audit && (
            <Link
              to="/audit-log"
              className={`nav-link ${isActive("/audit-log") ? "active" : ""}`}
            >
              <span className="icon-3d"><ScrollText size={18} /></span> Auditoría
            </Link>
          )}

          {role === "ADMIN" && (
            <Link
              to="/security"
              className={`nav-link ${isActive("/security") ? "active" : ""}`}
            >
              <span className="icon-3d"><ShieldCheck size={18} /></span> Seguridad
            </Link>
          )}
        </div>

        <div className="nav-user">
          <NavClock />
          <div className="city-filter-wrap">
            <MapPin size={14} />
            <select
              className="city-filter-select"
              value={cityFilter}
              onChange={e => setCityFilter(e.target.value)}
              title="Filtro por ciudad"
            >
              <option value="">Todas las ciudades</option>
              {cities.map(c => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>
          <button
            className="theme-toggle-btn"
            onClick={() => setDarkMode((v) => !v)}
            title={darkMode ? "Modo claro" : "Modo oscuro"}
            aria-label={darkMode ? "Cambiar a modo claro" : "Cambiar a modo oscuro"}
          >
            {darkMode ? <Sun size={20} aria-hidden="true" /> : <Moon size={20} aria-hidden="true" />}
          </button>
          <div className="user-info">
            <span className="user-name">
              <User size={14} style={{ marginRight: 4, verticalAlign: 'middle' }} />
              {user?.full_name || user?.username}
            </span>
            <span className="user-role">
              <Shield size={10} style={{ marginRight: 3, verticalAlign: 'middle' }} />
              {user?.role}
            </span>
          </div>
          <button onClick={handleLogout} className="logout-btn" aria-label="Cerrar sesión">
            <LogOut size={16} style={{ marginRight: 4, verticalAlign: 'middle' }} aria-hidden="true" />
            Salir
          </button>
        </div>
      </nav>

      <main id="main-content" className="main-content" role="main" aria-label="Contenido principal">{children}</main>
      <ChatWidget />
    </div>
  );
}
