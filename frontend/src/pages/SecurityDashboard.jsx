import { useState, useEffect, useCallback } from "react";
import { useAuth } from "../context/AuthContext";
import {
  Shield,
  ShieldAlert,
  ShieldCheck,
  Lock,
  Unlock,
  Activity,
  Users,
  AlertTriangle,
  Ban,
  Eye,
  RefreshCw,
  Search,
  Wifi,
  Server,
  Key,
  Clock,
  Zap,
  CheckCircle2,
  XCircle,
  History,
  Fingerprint,
} from "lucide-react";
import "../styles/SecurityDashboard.css";
import { API_BASE } from "../config";

const API = API_BASE;

const SEVERITY_COLORS = {
  CRITICAL: "#ef4444",
  HIGH: "#f97316",
  MEDIUM: "#eab308",
  LOW: "#22c55e",
  INFO: "#6b7280",
};

const SEVERITY_ICONS = {
  CRITICAL: <ShieldAlert size={14} />,
  HIGH: <AlertTriangle size={14} />,
  MEDIUM: <Eye size={14} />,
  LOW: <CheckCircle2 size={14} />,
  INFO: <Activity size={14} />,
};

const GRADE_COLORS = {
  A: "#22c55e",
  B: "#3b82f6",
  C: "#eab308",
  D: "#f97316",
  F: "#ef4444",
};

export default function SecurityDashboard() {
  const { token } = useAuth();
  const [dashboard, setDashboard] = useState(null);
  const [events, setEvents] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [blockedIps, setBlockedIps] = useState([]);
  const [loginHistory, setLoginHistory] = useState([]);
  const [scanInput, setScanInput] = useState("");
  const [scanResult, setScanResult] = useState(null);
  const [passwordCheck, setPasswordCheck] = useState("");
  const [passwordResult, setPasswordResult] = useState(null);
  const [blockIpInput, setBlockIpInput] = useState("");
  const [sevFilter, setSevFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState("overview");

  const headers = { Authorization: `Bearer ${token}`, "Content-Type": "application/json" };

  const fetchAll = useCallback(async () => {
    try {
      const [dRes, eRes, sRes, bRes, lRes] = await Promise.all([
        fetch(`${API}/api/security/dashboard`, { headers }),
        fetch(`${API}/api/security/events?limit=100${sevFilter ? `&severity=${sevFilter}` : ""}`, { headers }),
        fetch(`${API}/api/security/sessions`, { headers }),
        fetch(`${API}/api/security/blocked-ips`, { headers }),
        fetch(`${API}/api/security/login-history?limit=50`, { headers }),
      ]);
      if (dRes.ok) setDashboard(await dRes.json());
      if (eRes.ok) setEvents((await eRes.json()).events || []);
      if (sRes.ok) setSessions((await sRes.json()).sessions || []);
      if (bRes.ok) setBlockedIps((await bRes.json()).blocked_ips || []);
      if (lRes.ok) setLoginHistory((await lRes.json()).history || []);
    } catch (e) {
      console.error("Security fetch error:", e);
    } finally {
      setLoading(false);
    }
  }, [token, sevFilter]);

  useEffect(() => { fetchAll(); const t = setInterval(fetchAll, 15000); return () => clearInterval(t); }, [fetchAll]);

  /* ── Actions ── */
  const handleScan = async () => {
    if (!scanInput.trim()) return;
    try {
      const r = await fetch(`${API}/api/security/scan-input`, {
        method: "POST", headers, body: JSON.stringify({ value: scanInput }),
      });
      if (r.ok) setScanResult(await r.json());
    } catch { /* ignored */ }
  };

  const handlePasswordCheck = async () => {
    if (!passwordCheck) return;
    try {
      const r = await fetch(`${API}/api/security/check-password`, {
        method: "POST", headers, body: JSON.stringify({ password: passwordCheck }),
      });
      if (r.ok) setPasswordResult(await r.json());
    } catch { /* ignored */ }
  };

  const handleBlockIp = async () => {
    if (!blockIpInput.trim()) return;
    await fetch(`${API}/api/security/block-ip`, {
      method: "POST", headers, body: JSON.stringify({ ip: blockIpInput, reason: "Manual block from dashboard" }),
    });
    setBlockIpInput("");
    fetchAll();
  };

  const handleUnblock = async (ip) => {
    await fetch(`${API}/api/security/block-ip/${ip}`, { method: "DELETE", headers });
    fetchAll();
  };

  if (loading) return <div className="sec-loading"><RefreshCw className="spin" size={32} /> Cargando panel de seguridad...</div>;

  const stats = dashboard?.stats || {};
  const protection = dashboard?.protections || {};
  const score = dashboard?.score || {};

  return (
    <div className="security-dashboard">
      <header className="sec-header">
        <div className="sec-title">
          <Shield size={28} /> Panel de Ciberseguridad
        </div>
        <button className="sec-refresh" onClick={() => { setLoading(true); fetchAll(); }}>
          <RefreshCw size={16} /> Actualizar
        </button>
      </header>

      {/* ── Tabs ── */}
      <div className="sec-tabs">
        {[
          { key: "overview", icon: <ShieldCheck size={16} />, label: "Resumen" },
          { key: "events", icon: <Activity size={16} />, label: "Eventos" },
          { key: "sessions", icon: <Users size={16} />, label: "Sesiones" },
          { key: "anomalies", icon: <Fingerprint size={16} />, label: "Anomalias" },
          { key: "firewall", icon: <Ban size={16} />, label: "Firewall" },
          { key: "tools", icon: <Search size={16} />, label: "Herramientas" },
        ].map((t2) => (
          <button
            key={t2.key}
            className={`sec-tab ${tab === t2.key ? "active" : ""}`}
            onClick={() => setTab(t2.key)}
          >
            {t2.icon} {t2.label}
          </button>
        ))}
      </div>

      {/* ═══════ OVERVIEW ═══════ */}
      {tab === "overview" && (
        <div className="sec-overview">
          {/* Security Score Gauge + KPI cards row */}
          <div className="sec-overview-top">
            <SecurityScoreGauge score={score.score ?? 0} grade={score.grade ?? "?"} breakdown={score.breakdown} />
            <div className="sec-kpi-grid">
              <KpiCard icon={<Activity size={22} />} label="Eventos Totales" value={stats.total_events ?? 0} color="#3b82f6" />
              <KpiCard icon={<ShieldAlert size={22} />} label="Criticos 24h" value={score.breakdown?.incidents?.critical_24h ?? 0} color="#ef4444" />
              <KpiCard icon={<AlertTriangle size={22} />} label="Altos 24h" value={score.breakdown?.incidents?.high_24h ?? 0} color="#f97316" />
              <KpiCard icon={<Users size={22} />} label="Sesiones Activas" value={sessions.length} color="#8b5cf6" />
              <KpiCard icon={<Ban size={22} />} label="IPs Bloqueadas" value={blockedIps.length} color="#ef4444" />
              <KpiCard icon={<Zap size={22} />} label="Rate Limit Hits" value={stats.by_type?.RATE_LIMIT ?? 0} color="#eab308" />
            </div>
          </div>

          {/* Protection Status */}
          <div className="sec-card">
            <h3><ShieldCheck size={18} /> Estado de Proteccion ({Object.values(protection).filter(v => v === true).length} activas)</h3>
            <div className="protection-grid">
              <ProtectionItem label="Headers de Seguridad" active={protection.security_headers} />
              <ProtectionItem label="Rate Limiting" active={protection.rate_limiting} />
              <ProtectionItem label="Rate Limit Headers (RFC)" active={protection.rate_limit_headers} />
              <ProtectionItem label="Deteccion Brute-Force" active={protection.brute_force_detection} />
              <ProtectionItem label="Escaneo de Inputs (Query)" active={protection.input_scanning} />
              <ProtectionItem label="Escaneo de Body (JSON)" active={protection.body_scanning} />
              <ProtectionItem label="Proteccion CSRF" active={protection.csrf_protection} />
              <ProtectionItem label="Gestion de Sesiones" active={protection.session_management} />
              <ProtectionItem label="Bloqueo de IPs" active={protection.ip_blocking} />
              <ProtectionItem label="Politica de Contrasenas" active={protection.password_policy} />
              <ProtectionItem label="JWT Blacklist (Logout)" active={protection.jwt_blacklist} />
              <ProtectionItem label="HIBP Breach Check" active={protection.hibp_breach_check} />
              <ProtectionItem label="Deteccion Anomalias Login" active={protection.login_anomaly_detection} />
              <ProtectionItem label="Extraccion IP Real" active={protection.real_ip_extraction} />
              <ProtectionItem label="Encriptacion de Campos" active={protection.field_encryption} />
              <ProtectionItem label="Auditoria Blockchain" active={protection.audit_blockchain} />
            </div>
          </div>

          {/* Recent events */}
          <div className="sec-card">
            <h3><Activity size={18} /> Eventos Recientes</h3>
            <EventTable events={events.slice(0, 10)} />
          </div>
        </div>
      )}

      {/* ═══════ EVENTS ═══════ */}
      {tab === "events" && (
        <div className="sec-events-tab">
          <div className="sec-events-toolbar">
            <label>Severidad:</label>
            <select value={sevFilter} onChange={(e) => setSevFilter(e.target.value)}>
              <option value="">Todas</option>
              {["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"].map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>
          <EventTable events={events} />
        </div>
      )}

      {/* ═══════ SESSIONS ═══════ */}
      {tab === "sessions" && (
        <div className="sec-card">
          <h3><Users size={18} /> Sesiones Activas ({sessions.length})</h3>
          <div className="sec-table-wrap">
            <table className="sec-table">
              <thead>
                <tr>
                  <th>Usuario</th>
                  <th>IP</th>
                  <th>Creada</th>
                  <th>Ultima Actividad</th>
                  <th>Token (hash)</th>
                </tr>
              </thead>
              <tbody>
                {sessions.length === 0 && (
                  <tr><td colSpan={5} className="sec-empty">Sin sesiones activas</td></tr>
                )}
                {sessions.map((s, i) => (
                  <tr key={i}>
                    <td><Key size={12} /> {s.user}</td>
                    <td><Wifi size={12} /> {s.ip}</td>
                    <td><Clock size={12} /> {new Date(s.created).toLocaleString("es-ES")}</td>
                    <td>{new Date(s.last_seen).toLocaleString("es-ES")}</td>
                    <td className="mono">{s.session_id}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ═══════ ANOMALIES ═══════ */}
      {tab === "anomalies" && (
        <div className="sec-anomalies-tab">
          <div className="sec-card">
            <h3><Fingerprint size={18} /> Deteccion de Anomalias de Login</h3>
            <p className="sec-desc">
              Detecta automaticamente: nuevas IPs, viaje imposible (2 IPs distintas en &lt;1h), y horarios inusuales (02-05 UTC).
            </p>

            {/* Anomaly events from security events */}
            <h4 style={{ margin: "14px 0 8px", fontSize: "0.92rem", fontWeight: 600 }}>
              <AlertTriangle size={15} /> Anomalias Detectadas
            </h4>
            <EventTable
              events={events.filter(e => e.event_type?.startsWith("LOGIN_ANOMALY"))}
            />
          </div>

          <div className="sec-card">
            <h3><History size={18} /> Historial de Login ({loginHistory.length})</h3>
            <div className="sec-table-wrap">
              <table className="sec-table">
                <thead>
                  <tr>
                    <th>Usuario</th>
                    <th>IP</th>
                    <th>Fecha</th>
                  </tr>
                </thead>
                <tbody>
                  {loginHistory.length === 0 && (
                    <tr><td colSpan={3} className="sec-empty">Sin historial de login</td></tr>
                  )}
                  {loginHistory.map((l, i) => (
                    <tr key={i}>
                      <td><Key size={12} /> {l.username}</td>
                      <td><Wifi size={12} /> {l.ip}</td>
                      <td><Clock size={12} /> {new Date(l.timestamp).toLocaleString("es-ES")}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ═══════ FIREWALL ═══════ */}
      {tab === "firewall" && (
        <div className="sec-firewall-tab">
          <div className="sec-card">
            <h3><Ban size={18} /> IPs Bloqueadas ({blockedIps.length})</h3>
            <div className="sec-block-form">
              <input
                placeholder="Ej: 192.168.1.50"
                value={blockIpInput}
                onChange={(e) => setBlockIpInput(e.target.value)}
              />
              <button onClick={handleBlockIp}><Lock size={14} /> Bloquear IP</button>
            </div>
            <div className="sec-table-wrap">
              <table className="sec-table">
                <thead>
                  <tr><th>IP</th><th>Motivo</th><th>Fecha</th><th>Accion</th></tr>
                </thead>
                <tbody>
                  {blockedIps.length === 0 && (
                    <tr><td colSpan={4} className="sec-empty">Sin IPs bloqueadas</td></tr>
                  )}
                  {blockedIps.map((b, i) => (
                    <tr key={i}>
                      <td className="mono">{b.ip}</td>
                      <td>{b.reason || "—"}</td>
                      <td>{b.blocked_at ? new Date(b.blocked_at).toLocaleString("es-ES") : "—"}</td>
                      <td>
                        <button className="sec-unblock-btn" onClick={() => handleUnblock(b.ip)}>
                          <Unlock size={14} /> Desbloquear
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ═══════ TOOLS ═══════ */}
      {tab === "tools" && (
        <div className="sec-tools-tab">
          {/* Input scanner */}
          <div className="sec-card">
            <h3><Search size={18} /> Escaner de Amenazas</h3>
            <p className="sec-desc">Analiza un texto en busca de inyecciones SQL, XSS y path traversal.</p>
            <div className="sec-tool-form">
              <input
                placeholder="Ingresa texto a analizar..."
                value={scanInput}
                onChange={(e) => setScanInput(e.target.value)}
              />
              <button onClick={handleScan}><Search size={14} /> Escanear</button>
            </div>
            {scanResult && (
              <div className={`sec-scan-result ${scanResult.threats_found ? "danger" : "safe"}`}>
                {scanResult.threats_found ? (
                  <>
                    <XCircle size={18} /> <strong>Amenaza detectada:</strong>{" "}
                    {scanResult.threats.map((t2) => t2.type).join(", ")}
                  </>
                ) : (
                  <><CheckCircle2 size={18} /> Texto seguro — sin amenazas detectadas</>
                )}
              </div>
            )}
          </div>

          {/* Password checker + HIBP breach */}
          <div className="sec-card">
            <h3><Key size={18} /> Verificador de Contrasenas + Breach Check</h3>
            <p className="sec-desc">
              Evalua la fortaleza y verifica si la contrasena ha aparecido en filtraciones de datos (HIBP k-anonymity, 100% privado).
            </p>
            <div className="sec-tool-form">
              <input
                type="password"
                placeholder="Ingresa contrasena..."
                value={passwordCheck}
                onChange={(e) => setPasswordCheck(e.target.value)}
              />
              <button onClick={handlePasswordCheck}><Key size={14} /> Verificar</button>
            </div>
            {passwordResult && (
              <div className={`sec-scan-result ${passwordResult.valid && !passwordResult.breached ? "safe" : "danger"}`}>
                <div className="pwd-result-header">
                  {passwordResult.valid && !passwordResult.breached ? <CheckCircle2 size={18} /> : <XCircle size={18} />}
                  <strong>{passwordResult.valid ? "Contrasena valida" : "Contrasena invalida"}</strong>
                </div>
                <div className="pwd-details">
                  <span>Fortaleza: <strong>{passwordResult.strength}</strong></span>
                  <span>Entropia: <strong>{passwordResult.entropy_bits?.toFixed(1)} bits</strong></span>
                </div>
                {passwordResult.breached && (
                  <div className="breach-warning">
                    <ShieldAlert size={16} />
                    <span>
                      Esta contrasena aparece en <strong>{passwordResult.breach_count?.toLocaleString()}</strong> filtraciones de datos conocidas.
                      Cambiala inmediatamente.
                    </span>
                  </div>
                )}
                {!passwordResult.breached && passwordResult.breach_count === 0 && passwordResult.valid && (
                  <div className="breach-safe">
                    <ShieldCheck size={16} />
                    <span>No encontrada en filtraciones de datos conocidas (HIBP).</span>
                  </div>
                )}
                {passwordResult.errors?.length > 0 && (
                  <ul className="pwd-errors">
                    {passwordResult.errors.map((e, i) => <li key={i}>{e}</li>)}
                  </ul>
                )}
              </div>
            )}
          </div>

          {/* Config info */}
          <div className="sec-card">
            <h3><Server size={18} /> Configuracion de Seguridad</h3>
            <div className="sec-config-grid">
              {dashboard?.config && Object.entries(dashboard.config).map(([k, v]) => (
                <div key={k} className="sec-config-item">
                  <span className="config-key">{k.replace(/_/g, " ")}</span>
                  <span className="config-val">
                    {typeof v === "object" ? (
                      <pre className="config-json">{JSON.stringify(v, null, 2)}</pre>
                    ) : String(v)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/* ── Sub-components ── */

function SecurityScoreGauge({ score, grade, breakdown }) {
  const radius = 80;
  const stroke = 12;
  const normalizedRadius = radius - stroke / 2;
  const circumference = normalizedRadius * 2 * Math.PI;
  const strokeDashoffset = circumference - (score / 100) * circumference;
  const color = GRADE_COLORS[grade] || "#6b7280";

  return (
    <div className="score-gauge-container">
      <div className="score-gauge">
        <svg width={radius * 2} height={radius * 2} viewBox={`0 0 ${radius * 2} ${radius * 2}`}>
          {/* Background circle */}
          <circle
            stroke="var(--border-color, #e2e8f0)"
            fill="transparent"
            strokeWidth={stroke}
            r={normalizedRadius}
            cx={radius}
            cy={radius}
          />
          {/* Score arc */}
          <circle
            stroke={color}
            fill="transparent"
            strokeWidth={stroke}
            strokeLinecap="round"
            strokeDasharray={`${circumference} ${circumference}`}
            strokeDashoffset={strokeDashoffset}
            r={normalizedRadius}
            cx={radius}
            cy={radius}
            transform={`rotate(-90 ${radius} ${radius})`}
            style={{ transition: "stroke-dashoffset 0.8s ease-out" }}
          />
          {/* Center text */}
          <text x={radius} y={radius - 10} textAnchor="middle" className="gauge-score" fill={color}>
            {score}
          </text>
          <text x={radius} y={radius + 14} textAnchor="middle" className="gauge-grade" fill={color}>
            {grade}
          </text>
          <text x={radius} y={radius + 32} textAnchor="middle" className="gauge-label" fill="var(--text-secondary, #64748b)">
            Security Score
          </text>
        </svg>
      </div>
      {breakdown && (
        <div className="score-breakdown">
          {Object.entries(breakdown).map(([key, val]) => (
            <div key={key} className="breakdown-item">
              <span className="breakdown-label">{key}</span>
              <div className="breakdown-bar-track">
                <div
                  className="breakdown-bar-fill"
                  style={{
                    width: `${val.score}%`,
                    background: val.score >= 75 ? "#22c55e" : val.score >= 50 ? "#eab308" : "#ef4444",
                  }}
                />
              </div>
              <span className="breakdown-value">{val.score}%</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function KpiCard({ icon, label, value, color }) {
  return (
    <div className="sec-kpi-card" style={{ borderTopColor: color }}>
      <div className="kpi-icon" style={{ color }}>{icon}</div>
      <div className="kpi-body">
        <span className="kpi-value" style={{ color }}>{value}</span>
        <span className="kpi-label">{label}</span>
      </div>
    </div>
  );
}

function ProtectionItem({ label, active }) {
  return (
    <div className={`protection-item ${active ? "on" : "off"}`}>
      {active ? <CheckCircle2 size={16} /> : <XCircle size={16} />}
      <span>{label}</span>
    </div>
  );
}

function EventTable({ events }) {
  if (!events.length) return <div className="sec-empty">Sin eventos</div>;
  return (
    <div className="sec-table-wrap">
      <table className="sec-table">
        <thead>
          <tr>
            <th>Severidad</th>
            <th>Tipo</th>
            <th>IP</th>
            <th>Detalle</th>
            <th>Fecha</th>
          </tr>
        </thead>
        <tbody>
          {events.map((ev, i) => (
            <tr key={i}>
              <td>
                <span className="sev-badge" style={{ background: SEVERITY_COLORS[ev.severity] || "#6b7280" }}>
                  {SEVERITY_ICONS[ev.severity]} {ev.severity}
                </span>
              </td>
              <td>{ev.event_type}</td>
              <td className="mono">{ev.source_ip || "—"}</td>
              <td className="ev-detail">{ev.details}</td>
              <td><Clock size={12} /> {new Date(ev.timestamp).toLocaleString("es-ES")}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
