import { useState, useEffect, useCallback } from "react";
import { useAuth } from "../context/AuthContext";
import {
  Key, LogOut as LogOutIcon, AlertTriangle, ClipboardList, CheckCircle,
  UserPlus, Pencil, Trash2, FileEdit, Clock, Link as LinkIcon, Link2,
  HardDrive, ScrollText, FileText, Search, Calendar, Filter,
} from "lucide-react";
import "../styles/AuditLog.css";
import { API_BASE } from "../config";

export default function AuditLog() {
  const { token } = useAuth();
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [filterAction, setFilterAction] = useState("");
  const [filterUser, setFilterUser] = useState("");
  const [filterResource, setFilterResource] = useState("");
  const [filterDateFrom, setFilterDateFrom] = useState("");
  const [filterDateTo, setFilterDateTo] = useState("");
  const [verifyResult, setVerifyResult] = useState(null);
  const [verifyLoading, setVerifyLoading] = useState(false);

  const pageSize = 25;

  const fetchLogs = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        skip: String((page - 1) * pageSize),
        limit: String(pageSize),
      });
      if (filterAction) params.set("action", filterAction);
      if (filterUser) params.set("username", filterUser);

      const res = await fetch(
        `${API_BASE}/api/audit/logs?${params}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      if (res.ok) {
        const data = await res.json();
        setLogs(data.logs || []);
        setTotalPages(Math.max(1, Math.ceil((data.total || 0) / pageSize)));
      }
    } catch (err) {
      console.error("Error fetching audit logs:", err);
    } finally {
      setLoading(false);
    }
  }, [page, filterAction, filterUser, token]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  const exportCSV = async () => {
    try {
      const res = await fetch(
        `${API_BASE}/api/audit/export/csv`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      if (res.ok) {
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `audit_log_${Date.now()}.csv`;
        a.click();
        URL.revokeObjectURL(url);
      }
    } catch (err) {
      console.error("Error exporting audit log:", err);
    }
  };

  const verifyHash = async (hash) => {
    if (!hash) return;
    setVerifyLoading(true);
    setVerifyResult(null);
    try {
      const res = await fetch(
        `${API_BASE}/api/blockchain/verify/${hash}`
      );
      if (res.ok) {
        const data = await res.json();
        setVerifyResult(data);
      }
    } catch (err) {
      console.error("Error verifying hash:", err);
      setVerifyResult({ verified: false, error: "Error de conexión" });
    } finally {
      setVerifyLoading(false);
    }
  };

  const getActionIcon = (action) => {
    const iconMap = {
      LOGIN: <Key size={16} />,
      LOGOUT: <LogOutIcon size={16} />,
      CREATE_INCIDENT: <AlertTriangle size={16} />,
      ASSIGN_INCIDENT: <ClipboardList size={16} />,
      RESOLVE_INCIDENT: <CheckCircle size={16} />,
      CREATE_USER: <UserPlus size={16} />,
      UPDATE_USER: <Pencil size={16} />,
      DELETE_USER: <Trash2 size={16} />,
    };
    return iconMap[action] || <FileEdit size={16} />;
  };

  const getActionColor = (action) => {
    if (action?.includes("CREATE")) return "#10b981";
    if (action?.includes("DELETE")) return "#ef4444";
    if (action?.includes("RESOLVE")) return "#3b82f6";
    if (action?.includes("ASSIGN")) return "#f59e0b";
    if (action?.includes("LOGIN")) return "#667eea";
    return "#6b7280";
  };

  const getExplorerUrl = (txId) => {
    if (!txId || txId.startsWith("local_")) return null;
    return `https://whatsonchain.com/tx/${txId}`;
  };

  const getBlockchainIcon = (log) => {
    if (!log.blockchain_hash) return <Clock size={16} />;
    if (log.blockchain_tx_id && !log.blockchain_tx_id.startsWith("local_")) return <LinkIcon size={16} />;
    if (log.blockchain_tx_id?.startsWith("local_")) return <HardDrive size={16} />;
    return <Link2 size={16} />;
  };

  const getBlockchainTooltip = (log) => {
    if (!log.blockchain_hash) return "Pendiente de hash";
    if (log.blockchain_tx_id && !log.blockchain_tx_id.startsWith("local_")) return "Registrado en BSV blockchain";
    if (log.blockchain_tx_id?.startsWith("local_")) return "Registrado localmente";
    return "Hash calculado, pendiente de próximo batch";
  };

  return (
    <div className="audit-page">
      <div className="audit-header">
        <div>
          <h1><ScrollText size={24} className="icon-3d" style={{marginRight:8,verticalAlign:'middle'}} /> Registro de Auditoría</h1>
          <p>Historial completo de acciones del sistema — notarizado en BSV blockchain</p>
        </div>
        <button className="export-btn" onClick={exportCSV}>
                    <FileText size={16} style={{verticalAlign:'middle',marginRight:4}} /> Exportar CSV
        </button>
      </div>

      <div className="audit-filters">
        <div className="audit-filter-row">
          <div className="audit-filter-group">
            <label><Search size={12} /> Acción</label>
            <input
              type="text"
              placeholder="Filtrar por acción..."
              value={filterAction}
              onChange={(e) => { setFilterAction(e.target.value); setPage(1); }}
              className="filter-input"
            />
          </div>
          <div className="audit-filter-group">
            <label><Search size={12} /> Usuario</label>
            <input
              type="text"
              placeholder="Filtrar por usuario..."
              value={filterUser}
              onChange={(e) => { setFilterUser(e.target.value); setPage(1); }}
              className="filter-input"
            />
          </div>
          <div className="audit-filter-group">
            <label><Filter size={12} /> Recurso</label>
            <input
              type="text"
              placeholder="Entidad (incidente, user...)"
              value={filterResource}
              onChange={(e) => { setFilterResource(e.target.value); setPage(1); }}
              className="filter-input"
            />
          </div>
          <div className="audit-filter-group">
            <label><Calendar size={12} /> Desde</label>
            <input
              type="date"
              value={filterDateFrom}
              onChange={(e) => { setFilterDateFrom(e.target.value); setPage(1); }}
              className="filter-input filter-date"
            />
          </div>
          <div className="audit-filter-group">
            <label><Calendar size={12} /> Hasta</label>
            <input
              type="date"
              value={filterDateTo}
              onChange={(e) => { setFilterDateTo(e.target.value); setPage(1); }}
              className="filter-input filter-date"
            />
          </div>
        </div>
        {(filterAction || filterUser || filterResource || filterDateFrom || filterDateTo) && (
          <button className="audit-clear-btn" onClick={() => { setFilterAction(""); setFilterUser(""); setFilterResource(""); setFilterDateFrom(""); setFilterDateTo(""); setPage(1); }}>
            Limpiar filtros
          </button>
        )}
      </div>

      {/* Verify Result Modal */}
      {verifyResult && (
        <div className="verify-modal-overlay" onClick={() => setVerifyResult(null)}>
          <div className="verify-modal" onClick={(e) => e.stopPropagation()}>
            <div className="verify-modal-header">
              <h3>
                {verifyResult.verified ? "✅ Integridad Verificada" : "❌ Verificación Fallida"}
              </h3>
              <button className="verify-close" onClick={() => setVerifyResult(null)}>✕</button>
            </div>
            <div className="verify-modal-body">
              <div className="verify-row">
                <span className="verify-label">Estado:</span>
                <span className={`verify-value ${verifyResult.verified ? "valid" : "invalid"}`}>
                  {verifyResult.hash_integrity || (verifyResult.verified ? "VALID" : "FAILED")}
                </span>
              </div>
              {verifyResult.audit_entry && (
                <>
                  <div className="verify-row">
                    <span className="verify-label">Audit ID:</span>
                    <span className="verify-value">#{verifyResult.audit_entry.id}</span>
                  </div>
                  <div className="verify-row">
                    <span className="verify-label">Acción:</span>
                    <span className="verify-value">{verifyResult.audit_entry.action}</span>
                  </div>
                  <div className="verify-row">
                    <span className="verify-label">Usuario:</span>
                    <span className="verify-value">{verifyResult.audit_entry.username}</span>
                  </div>
                </>
              )}
              <div className="verify-row">
                <span className="verify-label">Hash:</span>
                <span className="verify-value hash-value">{verifyResult.hash}</span>
              </div>
              {verifyResult.blockchain && (
                <>
                  <div className="verify-row">
                    <span className="verify-label">Blockchain:</span>
                    <span className="verify-value">{verifyResult.blockchain.status}</span>
                  </div>
                  {verifyResult.blockchain.tx_id && (
                    <div className="verify-row">
                      <span className="verify-label">TX ID:</span>
                      <span className="verify-value hash-value">{verifyResult.blockchain.tx_id}</span>
                    </div>
                  )}
                  {verifyResult.blockchain.explorer_url && (
                    <div className="verify-row">
                      <span className="verify-label">Explorer:</span>
                      <a
                        href={verifyResult.blockchain.explorer_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="verify-link"
                      >
                        Ver en WhatsOnChain ↗
                      </a>
                    </div>
                  )}
                  {verifyResult.blockchain.confirmations !== undefined && (
                    <div className="verify-row">
                      <span className="verify-label">Confirmaciones:</span>
                      <span className="verify-value">{verifyResult.blockchain.confirmations}</span>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {loading ? (
        <div className="loading">Cargando registros...</div>
      ) : (
        <>
          <div className="audit-table-container">
            <table className="audit-table">
              <thead>
                <tr>
                  <th>Acción</th>
                  <th>Usuario</th>
                  <th>Detalles</th>
                  <th>Entidad</th>
                  <th>Fecha/Hora</th>
                  <th>Blockchain</th>
                </tr>
              </thead>
              <tbody>
                {logs
                  .filter(log => {
                    if (filterResource && !(log.resource || "").toLowerCase().includes(filterResource.toLowerCase())) return false;
                    if (filterDateFrom && log.timestamp < filterDateFrom) return false;
                    if (filterDateTo && log.timestamp.slice(0, 10) > filterDateTo) return false;
                    return true;
                  })
                  .map((log, idx) => (
                  <tr key={idx}>
                    <td>
                      <span
                        className="action-badge"
                        style={{ background: getActionColor(log.action) }}
                      >
                        {getActionIcon(log.action)} {log.action}
                      </span>
                    </td>
                    <td className="user-cell">{log.username || "sistema"}</td>
                    <td className="detail-cell">
                      {typeof log.details === "object"
                        ? JSON.stringify(log.details)
                        : log.details || "-"}
                    </td>
                    <td>
                      {log.resource || "-"}
                      {log.resource_id ? ` #${log.resource_id}` : ""}
                    </td>
                    <td className="time-cell">
                      {new Date(log.timestamp).toLocaleString("es-ES")}
                    </td>
                    <td className="blockchain-cell">
                      {log.blockchain_hash ? (
                        <div className="blockchain-cell-inner">
                          <button
                            className="blockchain-badge"
                            title={getBlockchainTooltip(log)}
                            onClick={() => verifyHash(log.blockchain_hash)}
                            disabled={verifyLoading}
                          >
                            {getBlockchainIcon(log)} Verificar
                          </button>
                          {getExplorerUrl(log.blockchain_tx_id) && (
                            <a
                              className="blockchain-explorer-link"
                              href={getExplorerUrl(log.blockchain_tx_id)}
                              target="_blank"
                              rel="noopener noreferrer"
                              title={`Ver TX en WhatsOnChain: ${log.blockchain_tx_id}`}
                            >
                              <LinkIcon size={13} /> WoC
                            </a>
                          )}
                        </div>
                      ) : (
                        <span className="blockchain-pending" title="Sin hash"><Clock size={16} /></span>
                      )}
                    </td>
                  </tr>
                ))}
                {logs.length === 0 && (
                  <tr>
                    <td colSpan={6} className="empty-row">
                      No se encontraron registros
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          <div className="pagination">
            <button
              disabled={page <= 1}
              onClick={() => setPage((p) => p - 1)}
            >
              ← Anterior
            </button>
            <span>
              Página {page} de {totalPages}
            </span>
            <button
              disabled={page >= totalPages}
              onClick={() => setPage((p) => p + 1)}
            >
              Siguiente →
            </button>
          </div>
        </>
      )}
    </div>
  );
}
