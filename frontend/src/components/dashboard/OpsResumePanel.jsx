import { memo } from "react";
import { BarChart3, Gauge, Ambulance, TrendingUp, Fuel, Zap, Star, Clock } from "lucide-react";

const SCOLORS = { SVB: "#22c55e", SVA: "#ef4444", VIR: "#3b82f6", VAMM: "#f97316", SAMU: "#a855f7" };
const SLA = { 5: 8, 4: 12, 3: 20, 2: 30, 1: 45 };
const SEV_COLORS = ["", "#22c55e", "#84cc16", "#f59e0b", "#f97316", "#ef4444"];

function fmtMin(m) { return m < 60 ? `${Math.round(m)}m` : `${Math.floor(m / 60)}h${Math.round(m % 60)}m`; }

function OpsResumePanel({ vehicles, openIncidents, assignedIncidents, incidents }) {
  const enabled = vehicles.filter(v => v.enabled);
  const idle = enabled.filter(v => v.status === "IDLE").length;
  const enRoute = enabled.filter(v => v.status === "EN_ROUTE").length;
  const refueling = enabled.filter(v => v.status === "REFUELING").length;
  const total = enabled.length || 1;
  const readiness = Math.round((idle / total) * 100);
  const lowFuel = enabled.filter(v => (v.fuel || 100) < 30).length;
  const avgSpeed = enabled.length ? (enabled.reduce((s, v) => s + (v.speed || 0), 0) / enabled.length).toFixed(0) : 0;
  const avgTrust = enabled.length ? (enabled.reduce((s, v) => s + (v.trust_score || 0), 0) / enabled.length).toFixed(1) : 0;

  const subtypeCounts = {};
  enabled.forEach(v => { const s = v.subtype || "SVB"; subtypeCounts[s] = (subtypeCounts[s] || 0) + 1; });

  // eslint-disable-next-line react-hooks/purity
  const nowMs = Date.now();
  const sevBuckets = { 1: [], 2: [], 3: [], 4: [], 5: [] };
  [...openIncidents, ...assignedIncidents].forEach(inc => {
    const sev = inc.severity || 1;
    const elapsed = (nowMs - (inc.created_at ? new Date(inc.created_at).getTime() : nowMs)) / 60000;
    if (sevBuckets[sev]) sevBuckets[sev].push(elapsed);
  });
  const todayStart = new Date(); todayStart.setHours(0, 0, 0, 0);
  incidents.filter(i => i.status === "RESOLVED" && i.resolved_at && new Date(i.resolved_at) >= todayStart).forEach(inc => {
    const sev = inc.severity || 1;
    const elapsed = (new Date(inc.resolved_at).getTime() - new Date(inc.created_at).getTime()) / 60000;
    if (sevBuckets[sev]) sevBuckets[sev].push(elapsed);
  });

  return (
    <div className="info-section ops-summary">
      <strong><BarChart3 size={16} className="icon-3d" /> Resumen Operativo</strong>
      <div className="ops-grid">
        {/* Fleet readiness */}
        <div className="ops-card ops-readiness">
          <div className="ops-card-header"><Gauge size={14} /> Disponibilidad</div>
          <div className="ops-gauge">
            <div className="ops-gauge-bar">
              <div className="ops-gauge-fill" style={{ width: `${readiness}%`, background: readiness > 60 ? "#22c55e" : readiness > 30 ? "#f59e0b" : "#ef4444" }} />
            </div>
            <span className="ops-gauge-pct">{readiness}%</span>
          </div>
          <div className="ops-status-row">
            <span className="ops-dot" style={{ background: "#22c55e" }} /> {idle} libres
            <span className="ops-dot" style={{ background: "#ef4444" }} /> {enRoute} en ruta
            <span className="ops-dot" style={{ background: "#3b82f6" }} /> {refueling} repostando
          </div>
        </div>

        {/* Subtype breakdown */}
        <div className="ops-card">
          <div className="ops-card-header"><Ambulance size={14} /> Por Subtipo</div>
          <div className="ops-subtype-list">
            {Object.entries(subtypeCounts).sort((a, b) => b[1] - a[1]).map(([sub, count]) => (
              <div key={sub} className="ops-subtype-row">
                <span className="ops-subtype-tag" style={{ background: SCOLORS[sub] || "#6b7280" }}>{sub}</span>
                <div className="ops-subtype-bar-bg">
                  <div className="ops-subtype-bar" style={{ width: `${(count / total) * 100}%`, background: SCOLORS[sub] || "#6b7280" }} />
                </div>
                <span className="ops-subtype-count">{count}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Quick stats */}
        <div className="ops-card">
          <div className="ops-card-header"><TrendingUp size={14} /> Indicadores</div>
          <div className="ops-indicators">
            <div className="ops-indicator"><Fuel size={13} /><span>Bajo combustible</span><strong className={lowFuel > 0 ? "warn" : ""}>{lowFuel}</strong></div>
            <div className="ops-indicator"><Zap size={13} /><span>Vel. media</span><strong>{avgSpeed} km/h</strong></div>
            <div className="ops-indicator"><Star size={13} /><span>Trust medio</span><strong>{avgTrust}</strong></div>
            <div className="ops-indicator"><Clock size={13} /><span>Incidentes / amb.</span><strong>{enabled.length ? (openIncidents.length / enabled.length).toFixed(1) : "0"}</strong></div>
          </div>
        </div>

        {/* Response times by severity */}
        <div className="ops-card">
          <div className="ops-card-header"><Clock size={14} /> Tiempos de Respuesta</div>
          <div className="ops-response-table">
            <div className="ops-rt-header"><span>Sev</span><span>Casos</span><span>Media</span><span>Máx</span></div>
            {[5, 4, 3, 2, 1].map(sev => {
              const arr = sevBuckets[sev] || [];
              const count = arr.length;
              const avg = count ? arr.reduce((a, b) => a + b, 0) / count : 0;
              const max = count ? Math.max(...arr) : 0;
              const overSla = count > 0 && avg > SLA[sev];
              return (
                <div key={sev} className={`ops-rt-row ${overSla ? "ops-rt-over" : ""}`}>
                  <span className="ops-rt-sev" style={{ background: SEV_COLORS[sev] }}>{sev}</span>
                  <span>{count}</span>
                  <span className={overSla ? "warn" : ""}>{count ? fmtMin(avg) : "—"}</span>
                  <span>{count ? fmtMin(max) : "—"}</span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}

export default memo(OpsResumePanel);
