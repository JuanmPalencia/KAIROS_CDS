import { useState, useEffect } from "react";
import {
  Timer, TrendingUp, Activity, Target, Ambulance, Clock,
  BarChart3, AlertTriangle, CheckCircle2, Gauge, Fuel,
  RefreshCw, Zap, Search, Filter
} from "lucide-react";
import "../styles/KPIs.css";
import { statusLabel } from "../utils/statusLabels";
import { API_BASE } from "../config";

const API = API_BASE;
const hdrs = () => ({ Authorization: `Bearer ${localStorage.getItem("token")}` });

export default function KPIs() {
  const [kpis, setKpis] = useState(null);
  const [vehicleKpis, setVehicleKpis] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchVehicle, setSearchVehicle] = useState("");
  const [subtypeFilter, setSubtypeFilter] = useState("ALL");
  const [statusFilter, setStatusFilter] = useState("ALL");

  const fetchKpis = async () => {
    try {
      const city = localStorage.getItem("cityFilter") || "";
      const qs = city ? `?city=${encodeURIComponent(city)}` : "";
      const [rtRes, vRes] = await Promise.all([
        fetch(`${API}/api/kpis/realtime${qs}`, { headers: hdrs() }),
        fetch(`${API}/api/kpis/by-vehicle${qs}`, { headers: hdrs() }),
      ]);
      if (rtRes.ok) setKpis(await rtRes.json());
      if (vRes.ok) {
        const vData = await vRes.json();
        // Stable sort by vehicle_id
        vData.sort((a, b) => (a.vehicle_id || "").localeCompare(b.vehicle_id || ""));
        setVehicleKpis(vData);
      }
    } catch (e) {
      console.error("KPIs fetch error:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchKpis();
    const interval = setInterval(fetchKpis, 5000);
    const onCityChange = () => fetchKpis();
    window.addEventListener("cityFilterChanged", onCityChange);
    return () => { clearInterval(interval); window.removeEventListener("cityFilterChanged", onCityChange); };
  }, []);

  const [snapping, setSnapping] = useState(false);
  const [snapped, setSnapped] = useState(false);
  const takeSnapshot = async () => {
    setSnapping(true);
    try {
      const res = await fetch(`${API}/api/kpis/snapshot`, { method: "POST", headers: hdrs() });
      if (res.ok) { setSnapped(true); setTimeout(() => setSnapped(false), 2000); }
    } catch (e) { console.error("Snapshot error:", e); }
    setSnapping(false);
    fetchKpis();
  };

  if (loading) return <div className="kpi-loading"><Activity className="spin" size={32} /> Cargando KPIs...</div>;
  if (!kpis) return <div className="kpi-error">Error al cargar KPIs</div>;

  const complianceColor = (val, target) => val >= target ? "kpi-good" : val >= target * 0.7 ? "kpi-warn" : "kpi-bad";
  const activeCity = localStorage.getItem("cityFilter") || "";

  return (
    <div className="kpis-page">
      <div className="kpis-header">
        <h1><Gauge size={28} /> KPIs Operativos en Tiempo Real{activeCity ? ` — ${activeCity}` : ""}</h1>
        <button className="snapshot-btn" onClick={takeSnapshot} disabled={snapping}>
          <RefreshCw size={16} className={snapping ? "spin" : ""} /> {snapping ? "Guardando..." : snapped ? "✓ Guardado" : "Guardar Snapshot"}
        </button>
      </div>

      {/* Response Times Section */}
      <section className="kpi-section">
        <h2><Timer size={22} /> Tiempos de Respuesta (24h)</h2>
        <div className="kpi-cards">
          <div className="kpi-card accent-blue">
            <div className="kpi-icon"><Clock size={24} /></div>
            <div className="kpi-value">{kpis.response_times.count > 0 ? Math.round(kpis.response_times.avg_response_sec) + "s" : "—"}</div>
            <div className="kpi-label">Tiempo medio respuesta</div>
          </div>
          <div className="kpi-card accent-green">
            <div className="kpi-icon"><Zap size={24} /></div>
            <div className="kpi-value">{kpis.response_times.fastest_sec > 0 ? Math.round(kpis.response_times.fastest_sec) + "s" : "—"}</div>
            <div className="kpi-label">Más rápido</div>
          </div>
          <div className="kpi-card accent-orange">
            <div className="kpi-icon"><Clock size={24} /></div>
            <div className="kpi-value">{kpis.response_times.slowest_sec > 0 ? Math.round(kpis.response_times.slowest_sec) + "s" : "—"}</div>
            <div className="kpi-label">Más lento</div>
          </div>
          <div className="kpi-card accent-purple">
            <div className="kpi-icon"><BarChart3 size={24} /></div>
            <div className="kpi-value">{kpis.response_times.count}</div>
            <div className="kpi-label">Casos resueltos (24h)</div>
          </div>
        </div>
      </section>

      {/* Compliance Section */}
      <section className="kpi-section">
        <h2><Target size={22} /> Compliance — Estándares SAMUR</h2>
        <div className="kpi-cards">
          <div className={`kpi-card compliance-card ${complianceColor(kpis.compliance.samur_8min, kpis.compliance.target_8min)}`}>
            <div className="compliance-header">
              <span className="compliance-title">Respuesta &lt; 8 min</span>
              <span className="compliance-target">Objetivo: {kpis.compliance.target_8min}%</span>
            </div>
            <div className="compliance-bar-container">
              <div className="compliance-bar" style={{ width: `${Math.min(kpis.compliance.samur_8min, 100)}%` }}></div>
            </div>
            <div className="compliance-value">{kpis.compliance.samur_8min}%</div>
          </div>
          <div className={`kpi-card compliance-card ${complianceColor(kpis.compliance.urban_15min, kpis.compliance.target_15min)}`}>
            <div className="compliance-header">
              <span className="compliance-title">Respuesta &lt; 15 min</span>
              <span className="compliance-target">Objetivo: {kpis.compliance.target_15min}%</span>
            </div>
            <div className="compliance-bar-container">
              <div className="compliance-bar" style={{ width: `${Math.min(kpis.compliance.urban_15min, 100)}%` }}></div>
            </div>
            <div className="compliance-value">{kpis.compliance.urban_15min}%</div>
          </div>
        </div>
      </section>

      {/* Fleet Section */}
      <section className="kpi-section">
        <h2><Ambulance size={22} /> Estado de Flota</h2>
        <div className="kpi-cards">
          <div className="kpi-card accent-blue">
            <div className="kpi-icon"><Ambulance size={24} /></div>
            <div className="kpi-value">{kpis.fleet.total}</div>
            <div className="kpi-label">Total vehículos</div>
          </div>
          <div className="kpi-card accent-green">
            <div className="kpi-icon"><CheckCircle2 size={24} /></div>
            <div className="kpi-value">{kpis.fleet.idle}</div>
            <div className="kpi-label">Disponibles</div>
          </div>
          <div className="kpi-card accent-red">
            <div className="kpi-icon"><Activity size={24} /></div>
            <div className="kpi-value">{kpis.fleet.en_route}</div>
            <div className="kpi-label">En servicio</div>
          </div>
          <div className="kpi-card accent-yellow">
            <div className="kpi-icon"><Fuel size={24} /></div>
            <div className="kpi-value">{kpis.fleet.avg_fuel_pct}%</div>
            <div className="kpi-label">Combustible medio</div>
          </div>
        </div>
        <div className="utilization-section">
          <div className="utilization-header">
            <span>Utilización de flota</span>
            <span className="utilization-value">{kpis.fleet.utilization_pct}%</span>
          </div>
          <div className="utilization-bar-bg">
            <div className="utilization-bar" style={{ width: `${kpis.fleet.utilization_pct}%` }}></div>
          </div>
        </div>
      </section>

      {/* Incidents Section */}
      <section className="kpi-section">
        <h2><AlertTriangle size={22} /> Incidentes</h2>
        <div className="kpi-cards">
          <div className="kpi-card accent-red">
            <div className="kpi-value">{kpis.incidents.open}</div>
            <div className="kpi-label">Abiertos ahora</div>
          </div>
          <div className="kpi-card accent-green">
            <div className="kpi-value">{kpis.incidents.resolved_24h}</div>
            <div className="kpi-label">Resueltos (24h)</div>
          </div>
          <div className="kpi-card accent-blue">
            <div className="kpi-value">{kpis.incidents.total_24h}</div>
            <div className="kpi-label">Total (24h)</div>
          </div>
        </div>
      </section>

      {/* Per-Vehicle KPIs */}
      <section className="kpi-section">
        <h2><TrendingUp size={22} /> KPIs por Vehículo</h2>

        {/* Filters */}
        <div className="vkpi-filters">
          <div className="vkpi-search-wrap">
            <Search size={16} />
            <input
              type="text"
              placeholder="Buscar vehículo..."
              value={searchVehicle}
              onChange={(e) => setSearchVehicle(e.target.value)}
              className="vkpi-search"
            />
            {searchVehicle && <button className="vkpi-search-clear" onClick={() => setSearchVehicle("")}>×</button>}
          </div>
          <div className="vkpi-filter-group">
            <label><Filter size={14} /> Subtipo</label>
            <select value={subtypeFilter} onChange={(e) => setSubtypeFilter(e.target.value)} className="vkpi-select">
              <option value="ALL">Todos</option>
              <option value="SVB">SVB</option>
              <option value="SVA">SVA</option>
              <option value="VIR">VIR</option>
              <option value="VAMM">VAMM</option>
              <option value="SAMU">SAMU</option>
            </select>
          </div>
          <div className="vkpi-filter-group">
            <label><Filter size={14} /> Estado</label>
            <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="vkpi-select">
              <option value="ALL">Todos</option>
              <option value="IDLE">Disponible</option>
              <option value="EN_ROUTE">En Ruta</option>
              <option value="ON_SCENE">En Escena</option>
              <option value="RETURNING">Retornando</option>
              <option value="MAINTENANCE">Mantenimiento</option>
            </select>
          </div>
          {(searchVehicle || subtypeFilter !== "ALL" || statusFilter !== "ALL") && (
            <button className="vkpi-clear-btn" onClick={() => { setSearchVehicle(""); setSubtypeFilter("ALL"); setStatusFilter("ALL"); }}>
              Limpiar filtros
            </button>
          )}
        </div>

        {(() => {
          const filtered = vehicleKpis.filter((vk) => {
            if (searchVehicle && !vk.vehicle_id.toLowerCase().includes(searchVehicle.toLowerCase())) return false;
            if (subtypeFilter !== "ALL" && vk.subtype !== subtypeFilter) return false;
            if (statusFilter !== "ALL" && vk.status !== statusFilter) return false;
            return true;
          });
          return (
            <>
              <div className="vkpi-result-count">{filtered.length} de {vehicleKpis.length} vehículos</div>
              <div className="vehicle-kpi-table">
                <table>
                  <thead>
                    <tr>
                      <th>Vehículo</th>
                      <th>Subtipo</th>
                      <th>Estado</th>
                      <th>Casos</th>
                      <th>Tiempo medio</th>
                      <th>Combustible</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filtered.length === 0 ? (
                      <tr><td colSpan="6" className="no-match">Sin resultados para los filtros seleccionados</td></tr>
                    ) : filtered.map((vk) => (
                      <tr key={vk.vehicle_id}>
                        <td className="vid">{vk.vehicle_id}</td>
                        <td><span className={`subtype-badge st-${vk.subtype}`}>{vk.subtype}</span></td>
                        <td><span className={`status-dot st-${vk.status}`}>{statusLabel(vk.status)}</span></td>
                        <td>{vk.total_incidents}</td>
                        <td>{vk.avg_time_sec > 0 ? `${Math.round(vk.avg_time_sec)}s` : "—"}</td>
                        <td>
                          <div className="fuel-mini">
                            <div className="fuel-mini-bar" style={{ width: `${vk.fuel_pct}%`, backgroundColor: vk.fuel_pct > 50 ? '#22c55e' : vk.fuel_pct > 25 ? '#f59e0b' : '#ef4444' }}></div>
                          </div>
                          {vk.fuel_pct}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          );
        })()}
      </section>
    </div>
  );
}
