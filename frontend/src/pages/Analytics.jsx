import { useState, useEffect } from "react";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";
import { BarChart3, TrendingUp, Timer, CheckCircle, Ambulance, FileText, FileDown } from "lucide-react";
import "../styles/Analytics.css";
import { API_BASE } from "../config";

const COLORS = ["#667eea", "#764ba2", "#f59e0b", "#10b981", "#ef4444"];

const exportCSV = (data, period) => {
  if (!data) return;
  const rows = [
    ["KAIROS - Reporte Analytics"],
    [`Período: últimos ${period} días`],
    [`Generado: ${new Date().toLocaleString("es-ES")}`],
    [],
    ["Métrica", "Valor"],
    ["Total Incidentes", data.summary.total_incidents],
    ["Tiempo Respuesta Promedio (min)", data.summary.avg_response_time_min.toFixed(1)],
    ["Tasa de Resolución (%)", data.summary.resolution_rate],
    ["Vehículos Activos", data.summary.active_vehicles],
    ["Utilización de Flota (%)", data.summary.fleet_utilization],
    [],
    ["Incidentes por Severidad"],
    ["Severidad", "Cantidad"],
    ...(data.incidents_by_severity || []).map(s => [s.severity, s.count]),
    [],
    ["Incidentes por Tipo"],
    ["Tipo", "Cantidad"],
    ...(data.incidents_by_type || []).map(t => [t.type, t.count]),
  ];

  const csv = rows.map(r => r.join(",")).join("\n");
  const blob = new Blob(["\uFEFF" + csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `KAIROS_analytics_${period}d_${Date.now()}.csv`;
  a.click();
  URL.revokeObjectURL(url);
};

const exportPDF = (data, period) => {
  if (!data) return;
  const doc = new jsPDF();
  
  // Header
  doc.setFontSize(20);
  doc.setTextColor(102, 126, 234);
  doc.text("KAIROS - Reporte Analytics", 14, 22);
  doc.setFontSize(10);
  doc.setTextColor(100);
  doc.text(`Período: últimos ${period} días | Generado: ${new Date().toLocaleString("es-ES")}`, 14, 30);

  // Summary table
  doc.setFontSize(14);
  doc.setTextColor(0);
  doc.text("Resumen", 14, 42);
  autoTable(doc, {
    startY: 46,
    head: [["Métrica", "Valor"]],
    body: [
      ["Total Incidentes", String(data.summary.total_incidents)],
      ["Tiempo Resp. Promedio", `${data.summary.avg_response_time_min.toFixed(1)} min`],
      ["Tasa de Resolución", `${data.summary.resolution_rate}%`],
      ["Vehículos Activos", String(data.summary.active_vehicles)],
      ["Utilización de Flota", `${data.summary.fleet_utilization}%`],
    ],
    theme: "grid",
    headStyles: { fillColor: [102, 126, 234] },
  });

  // Severity table
  let y = doc.lastAutoTable.finalY + 10;
  doc.text("Incidentes por Severidad", 14, y);
  autoTable(doc, {
    startY: y + 4,
    head: [["Severidad", "Cantidad"]],
    body: (data.incidents_by_severity || []).map(s => [String(s.severity), String(s.count)]),
    theme: "grid",
    headStyles: { fillColor: [118, 75, 162] },
  });

  // Type table
  y = doc.lastAutoTable.finalY + 10;
  doc.text("Incidentes por Tipo", 14, y);
  autoTable(doc, {
    startY: y + 4,
    head: [["Tipo", "Cantidad"]],
    body: (data.incidents_by_type || []).map(t => [t.type, String(t.count)]),
    theme: "grid",
    headStyles: { fillColor: [245, 158, 11] },
  });

  doc.save(`KAIROS_analytics_${period}d_${Date.now()}.pdf`);
};

export default function Analytics() {
  const [data, setData] = useState(null);
  const [responseTimes, setResponseTimes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState(7);

  useEffect(() => {
    fetchAnalytics();
  }, [period]);

  useEffect(() => {
    const onCityChange = () => fetchAnalytics();
    window.addEventListener("cityFilterChanged", onCityChange);
    return () => window.removeEventListener("cityFilterChanged", onCityChange);
  }, [period]);

  const fetchAnalytics = async () => {
    try {
      const cityF = localStorage.getItem("cityFilter") || "";
      const cityParam = cityF ? `&city=${encodeURIComponent(cityF)}` : "";
      const [res, rtRes] = await Promise.all([
        fetch(
          `${API_BASE}/api/analytics/dashboard?days=${period}${cityParam}`,
          { headers: { Authorization: `Bearer ${localStorage.getItem("token")}` } }
        ),
        fetch(
          `${API_BASE}/api/analytics/response-times?days=${period}${cityParam}`,
          { headers: { Authorization: `Bearer ${localStorage.getItem("token")}` } }
        ),
      ]);
      if (res.ok) {
        const json = await res.json();
        setData(json);
      }
      if (rtRes.ok) {
        const rtJson = await rtRes.json();
        // Compute average response time per severity
        const bySev = {};
        for (const d of (rtJson.data || [])) {
          const s = d.severity || 1;
          if (!bySev[s]) bySev[s] = { total: 0, count: 0 };
          bySev[s].total += d.response_time_min;
          bySev[s].count += 1;
        }
        const sevData = Object.entries(bySev)
          .map(([sev, v]) => ({ severity: `Sev ${sev}`, avg_min: +(v.total / v.count).toFixed(1), count: v.count }))
          .sort((a, b) => a.severity.localeCompare(b.severity));
        setResponseTimes(sevData);
      }
    } catch (error) {
      console.error("Error fetching analytics:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !data || !data.summary) {
    return <div className="loading">Cargando analytics...</div>;
  }

  const activeCity = localStorage.getItem("cityFilter") || "";

  return (
    <div className="analytics-page">
      <div className="page-header">
        <div>
          <h1><BarChart3 size={24} className="icon-3d" style={{marginRight:8,verticalAlign:'middle'}} /> Analytics & Reportes</h1>
          <p>Análisis y métricas del sistema{activeCity ? ` — ${activeCity}` : " — Todas las ciudades"}</p>
        </div>
        <div className="header-actions">
          <select
            value={period}
            onChange={(e) => setPeriod(Number(e.target.value))}
            className="period-select"
          >
            <option value={1}>Último día</option>
            <option value={7}>Últimos 7 días</option>
            <option value={30}>Últimos 30 días</option>
            <option value={90}>Últimos 90 días</option>
          </select>
          <button className="export-btn export-csv" onClick={() => exportCSV(data, period)}>
            <FileText size={16} style={{verticalAlign:'middle',marginRight:4}} /> CSV
          </button>
          <button className="export-btn export-pdf" onClick={() => exportPDF(data, period)}>
            <FileDown size={16} style={{verticalAlign:'middle',marginRight:4}} /> PDF
          </button>
        </div>
      </div>

      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-icon icon-3d"><TrendingUp size={28} /></div>
          <div className="metric-value">{data.summary.total_incidents}</div>
          <div className="metric-label">Total Incidentes</div>
        </div>

        <div className="metric-card">
          <div className="metric-icon icon-3d"><Timer size={28} /></div>
          <div className="metric-value">
            {data.summary.avg_response_time_min.toFixed(1)}m
          </div>
          <div className="metric-label">Tiempo Respuesta Promedio</div>
        </div>

        <div className="metric-card">
          <div className="metric-icon icon-3d"><CheckCircle size={28} /></div>
          <div className="metric-value">{data.summary.resolution_rate}%</div>
          <div className="metric-label">Tasa de Resolución</div>
        </div>

        <div className="metric-card">
          <div className="metric-icon icon-3d"><Ambulance size={28} /></div>
          <div className="metric-value">{data.summary.active_vehicles}</div>
          <div className="metric-label">Vehículos Activos</div>
        </div>

        <div className="metric-card">
          <div className="metric-icon icon-3d"><BarChart3 size={28} /></div>
          <div className="metric-value">
            {data.summary.fleet_utilization}%
          </div>
          <div className="metric-label">Utilización de Flota</div>
        </div>
      </div>

      <div className="charts-grid">
        <div className="chart-card">
          <h3>Distribución Horaria (últimas 24h)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={data.hourly_distribution}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="hour" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="count"
                stroke="#667eea"
                strokeWidth={2}
                name="Incidentes"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card">
          <h3>Incidentes por Severidad</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data.incidents_by_severity}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="severity" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="count" fill="#764ba2" name="Cantidad" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card">
          <h3>Incidentes por Tipo</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={data.incidents_by_type}
                dataKey="count"
                nameKey="type"
                cx="50%"
                cy="50%"
                outerRadius={100}
                label
              >
                {data.incidents_by_type.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={COLORS[index % COLORS.length]}
                  />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card">
          <h3>Tiempo de Respuesta por Severidad</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={responseTimes}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="severity" />
              <YAxis unit=" min" />
              <Tooltip formatter={(v, name) => name === "avg_min" ? [`${v} min`, "Tiempo medio"] : [v, "Casos"]} />
              <Legend />
              <Bar dataKey="avg_min" fill="#f59e0b" name="Tiempo medio (min)" />
              <Bar dataKey="count" fill="#667eea" name="Casos resueltos" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
