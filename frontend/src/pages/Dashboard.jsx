import { useEffect, useRef, useState, useCallback, useMemo } from "react";
import { useAuth } from "../context/AuthContext";
import markerIcon2x from "leaflet/dist/images/marker-icon-2x.png";
import markerIcon from "leaflet/dist/images/marker-icon.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";
import L from "leaflet";
import "leaflet.heat";
import "leaflet.markercluster";
import "leaflet.markercluster/dist/MarkerCluster.css";
import "leaflet.markercluster/dist/MarkerCluster.Default.css";
import toast, { Toaster } from "react-hot-toast";
import { LayoutDashboard } from "lucide-react";
import html2canvas from "html2canvas";
import "../styles/Dashboard.css";
import { API_BASE } from "../config";
import { statusLabel as getStatusLabel } from "../utils/statusLabels";
import { getIncidentTypeLabel } from "../utils/incidentUtils";
import { useIncidentNotifications } from "../hooks/useIncidentNotifications";
import { useWeather } from "../hooks/useWeather";
import { useSimulationControls } from "../hooks/useSimulationControls";
import { useDigitalTwin } from "../hooks/useDigitalTwin";

import { vehicleIcon, hospitalIcon as hospitalSvg, gasStationIcon, incidentIcon } from "../components/mapIcons";
import MapLegend from "../components/dashboard/MapLegend";
import WeatherWidget from "../components/dashboard/WeatherWidget";
import MapControlsToolbar from "../components/dashboard/MapControlsToolbar";
import SimulationControls from "../components/dashboard/SimulationControls";
import MetricCards from "../components/dashboard/MetricCards";
import IncidentListPanel from "../components/dashboard/IncidentListPanel";
import ActiveIncidentsPanel from "../components/dashboard/ActiveIncidentsPanel";
import FleetListPanel from "../components/dashboard/FleetListPanel";
import OpsResumePanel from "../components/dashboard/OpsResumePanel";
import DigitalTwinPanel from "../components/dashboard/DigitalTwinPanel";
import EmergencyAlertModal from "../components/dashboard/EmergencyAlertModal";
import AiAutoSuggestionsPanel from "../components/dashboard/AiAutoSuggestionsPanel";
import IncidentDetailModal from "../components/dashboard/IncidentDetailModal";

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({ iconRetinaUrl: markerIcon2x, iconUrl: markerIcon, shadowUrl: markerShadow });

export default function Dashboard() {
  const { user, token } = useAuth();

  // ── Map refs ──────────────────────────────────────────────────────────
  const mapRef = useRef(null);
  const layerRef = useRef(null);
  const markersRef = useRef(new Map());
  const incidentsRef = useRef(new Map());
  const hospitalsRef = useRef(new Map());
  const gasStationsRef = useRef(new Map());
  const routesRef = useRef(new Map());
  const routeDotsRef = useRef(new Map());
  const incidentClusterRef = useRef(null);
  const heatLayerRef = useRef(null);
  const deaMarkersRef = useRef(new Map());
  const gisMarkersRef = useRef(new Map());
  const agencyMarkersRef = useRef(new Map());
  const ssmCirclesRef = useRef(new Map());
  const coverageCirclesRef = useRef(new Map());
  const riskZonesRef = useRef([]);
  const prevIncidentIdsRef = useRef(new Set());
  const lastSecEventIdRef = useRef(null);
  const proximityAlertedRef = useRef(new Set());
  const dashboardRef = useRef(null);

  // ── Live data state ───────────────────────────────────────────────────
  const [fleetMetrics, setFleetMetrics] = useState({ active_vehicles: 0, avg_fuel: 0 });
  const [incidents, setIncidents] = useState([]);
  useIncidentNotifications(incidents);
  const [hospitals, setHospitals] = useState([]);
  const [vehicles, setVehicles] = useState([]);
  const [gasStations, setGasStations] = useState([]);
  const [deaLocations, setDeaLocations] = useState([]);
  const [gisLayers, setGisLayers] = useState([]);
  const [agencyResources, setAgencyResources] = useState([]);
  const [ssmZones, setSsmZones] = useState([]);

  // ── Map layer toggles ─────────────────────────────────────────────────
  const [showHeatmap, setShowHeatmap] = useState(false);
  const [showRoutes, setShowRoutes] = useState(true);
  const [showGasStations, setShowGasStations] = useState(true);
  const [showDEA, setShowDEA] = useState(false);
  const [showGIS, setShowGIS] = useState(false);
  const [showAgencies, setShowAgencies] = useState(false);
  const [showSSM, setShowSSM] = useState(false);
  const [showCoverage, setShowCoverage] = useState(true);
  const [showRiskZones, setShowRiskZones] = useState(false);

  // ── UI state ──────────────────────────────────────────────────────────
  const [focusedVehicleId, setFocusedVehicleId] = useState(null);
  const [subtypeFilter, setSubtypeFilter] = useState(() => localStorage.getItem("subtypeFilter") || "ALL");
  const [statusFilter, setStatusFilter] = useState(() => localStorage.getItem("statusFilter") || "ALL");
  const [emergencyAlert, setEmergencyAlert] = useState(null);
  const [aiAutoSuggestions, setAiAutoSuggestions] = useState([]);
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [incidentTimeline, setIncidentTimeline] = useState(null);
  const [aiSuggestion, setAiSuggestion] = useState(null);
  const [loadingSuggestion, setLoadingSuggestion] = useState(false);
  const [overrideMode, setOverrideMode] = useState(false);
  const [overrideVehicle, setOverrideVehicle] = useState("");
  const [overrideHospital, setOverrideHospital] = useState("");
  const [overrideReason, setOverrideReason] = useState("");
  const [exporting, setExporting] = useState(false);

  // ── Custom hooks ──────────────────────────────────────────────────────
  const { weather, fetchWeather, onMapMouseMove } = useWeather();
  const simControls = useSimulationControls({ setAiAutoSuggestions, setSelectedIncident, setIncidentTimeline, setAiSuggestion, prevIncidentIdsRef });
  const twin = useDigitalTwin(focusedVehicleId);

  // ── Persist filters ───────────────────────────────────────────────────
  useEffect(() => { localStorage.setItem("subtypeFilter", subtypeFilter); }, [subtypeFilter]);
  useEffect(() => { localStorage.setItem("statusFilter", statusFilter); }, [statusFilter]);

  // ── Map focus helpers ─────────────────────────────────────────────────
  const focusVehicle = useCallback((vehicleId) => {
    const marker = markersRef.current.get(vehicleId);
    if (marker && mapRef.current) {
      mapRef.current.flyTo(marker.getLatLng(), 15, { duration: 0.8 });
      marker.openPopup();
      setFocusedVehicleId(prev => prev === vehicleId ? null : vehicleId);
    }
  }, []);

  // Always follows (no toggle) — used by ActiveIncidentsPanel "Seguir" button
  const followVehicle = useCallback((vehicleId) => {
    const marker = markersRef.current.get(vehicleId);
    if (marker && mapRef.current) {
      mapRef.current.flyTo(marker.getLatLng(), 15, { duration: 0.8 });
      marker.openPopup();
    }
    setFocusedVehicleId(vehicleId);
  }, []);

  const focusIncident = useCallback((incidentId) => {
    const circle = incidentsRef.current.get(incidentId);
    if (circle && mapRef.current) {
      mapRef.current.flyTo(circle.getLatLng(), 15, { duration: 0.8 });
      circle.openPopup();
    }
  }, []);

  // ── Export to image ───────────────────────────────────────────────────
  const exportToPDF = useCallback(async () => {
    if (!dashboardRef.current || exporting) return;
    setExporting(true);
    try {
      const canvas = await html2canvas(dashboardRef.current, { scale: 2, useCORS: true, backgroundColor: "#0a0e14", logging: false });
      const link = document.createElement("a");
      link.download = `KAIROS_Dashboard_${new Date().toISOString().slice(0, 19).replace(/[T:]/g, "-")}.png`;
      link.href = canvas.toDataURL("image/png");
      link.click();
      toast.success("Dashboard exportado correctamente", { duration: 3000 });
    } catch (e) {
      toast.error("Error al exportar dashboard");
      console.error("Export error:", e);
    } finally {
      setExporting(false);
    }
  }, [exporting]);

  // ── Fetch static layers (hospitals, DEA, GIS, agencies, SSM) ─────────
  useEffect(() => {
    const headers = { Authorization: `Bearer ${localStorage.getItem("token")}` };
    const fetchAll = async () => {
      try {
        const [deaRes, gisRes, agencyRes, ssmRes] = await Promise.allSettled([
          fetch(`${API_BASE}/api/resources/dea`, { headers }),
          fetch(`${API_BASE}/api/resources/gis`, { headers }),
          fetch(`${API_BASE}/api/resources/agencies`, { headers }),
          fetch(`${API_BASE}/api/resources/ssm/zones`, { headers }),
        ]);
        if (deaRes.status === "fulfilled" && deaRes.value.ok) setDeaLocations(await deaRes.value.json());
        if (gisRes.status === "fulfilled" && gisRes.value.ok) setGisLayers(await gisRes.value.json());
        if (agencyRes.status === "fulfilled" && agencyRes.value.ok) setAgencyResources(await agencyRes.value.json());
        if (ssmRes.status === "fulfilled" && ssmRes.value.ok) setSsmZones(await ssmRes.value.json());
      } catch (e) { console.error("Error fetching resource layers:", e); }
    };
    fetchAll();
  }, []);

  // ── Incident API helpers ──────────────────────────────────────────────
  const getAISuggestion = useCallback(async (incidentId) => {
    setLoadingSuggestion(true);
    try {
      const res = await fetch(`${API_BASE}/api/assignments/suggest/${incidentId}`, {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
      });
      setAiSuggestion(await res.json());
    } catch { alert("Error al obtener sugerencia de IA"); }
    finally { setLoadingSuggestion(false); }
  }, []);

  const confirmAssignment = useCallback(async (incidentId, vehicleId, hospitalId, reason) => {
    try {
      const res = await fetch(`${API_BASE}/api/assignments/confirm`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${localStorage.getItem("token")}` },
        body: JSON.stringify({ incident_id: incidentId, vehicle_id: vehicleId, hospital_id: hospitalId, override_reason: reason }),
      });
      if (res.ok) {
        toast.success("Asignación confirmada");
        setSelectedIncident(null); setAiSuggestion(null);
        setOverrideMode(false); setOverrideVehicle(""); setOverrideHospital(""); setOverrideReason("");
      } else { toast.error("Error al confirmar asignación"); }
    } catch { toast.error("Error de conexión"); }
  }, []);

  const resolveIncident = useCallback(async (incidentId) => {
    if (!confirm("¿Marcar este incidente como resuelto?")) return;
    try {
      const res = await fetch(`${API_BASE}/api/assignments/resolve/${incidentId}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
      });
      if (res.ok) { toast.success("Incidente resuelto"); setSelectedIncident(null); }
      else { toast.error("Error al resolver incidente"); }
    } catch { toast.error("Error de conexión"); }
  }, []);

  const fetchTimeline = useCallback(async (incidentId) => {
    try {
      const res = await fetch(`${API_BASE}/api/events/incidents/${incidentId}/timeline`, {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
      });
      if (res.ok) { const data = await res.json(); setIncidentTimeline(data.timeline || data); }
    } catch (e) { console.error("Error fetching timeline:", e); }
  }, []);

  const dismissAiAutoSuggestion = useCallback((incidentId) => {
    setAiAutoSuggestions(prev => prev.filter(s => s.incidentId !== incidentId));
  }, []);

  // ── Map initialization + polling ──────────────────────────────────────
  useEffect(() => {
    const map = L.map("map").setView([40.4168, -3.7038], 12);
    mapRef.current = map;
    map.invalidateSize(false);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { attribution: "&copy; OpenStreetMap contributors" }).addTo(map);
    layerRef.current = L.layerGroup().addTo(map);

    incidentClusterRef.current = L.markerClusterGroup({
      maxClusterRadius: 45, spiderfyOnMaxZoom: true, showCoverageOnHover: false,
      zoomToBoundsOnClick: true, disableClusteringAtZoom: 16,
      iconCreateFunction: (cluster) => {
        const count = cluster.getChildCount();
        const size = count >= 20 ? "large" : count >= 5 ? "medium" : "small";
        const c = count >= 20 ? "#dc2626" : count >= 5 ? "#f59e0b" : "#3b82f6";
        const dim = size === "large" ? 44 : size === "medium" ? 36 : 30;
        return L.divIcon({ html: `<div style="background:${c};color:#fff;border-radius:50%;width:${dim}px;height:${dim}px;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:${dim > 36 ? 15 : 13}px;box-shadow:0 2px 8px ${c}80;border:2px solid #fff">${count}</div>`, className: "incident-cluster-icon", iconSize: L.point(dim, dim) });
      },
    });
    incidentClusterRef.current.addTo(map);

    map.on("mousemove", onMapMouseMove);
    fetchWeather(40.4168, -3.7038);

    let stopped = false;
    let pollInterval;

    const updateData = async () => {
      if (stopped) return;
      try {
        const cityF = localStorage.getItem("cityFilter") || "";
        const url = cityF ? `${API_BASE}/api/live?city=${encodeURIComponent(cityF)}` : `${API_BASE}/api/live`;
        const res = await fetch(url);
        if (!res.ok) throw new Error("Failed to fetch");
        const data = await res.json();

        if (data.fleet_metrics) setFleetMetrics(data.fleet_metrics);
        if (data.hospitals?.length) setHospitals(data.hospitals);

        const vList = data.vehicles || [];
        setVehicles(vList);
        const vehicleById = {};
        const seen = new Set();
        for (const v of vList) vehicleById[v.id] = v;

        // Update vehicle markers
        for (const v of vList) {
          seen.add(v.id);
          const latlng = [v.lat, v.lon];
          const subtype = v.subtype || "SVB";
          const SUBTYPE_NAMES = { SVB: "Soporte Vital Básico", SVA: "Soporte Vital Avanzado", VIR: "Intervención Rápida", VAMM: "Asistencia Múltiple", SAMU: "SAMU" };
          const tankL = v.tank_capacity || 80;
          const fuelLiters = ((v.fuel / 100) * tankL).toFixed(1);

          const popup = `<div class="map-popup vehicle-popup"><div class="popup-header"><strong>${v.id}</strong><span class="popup-badge subtype-badge">${subtype}</span><span class="popup-badge ${v.status.toLowerCase()}">${getStatusLabel(v.status)}</span></div><div class="popup-subname">${SUBTYPE_NAMES[subtype] || subtype}</div><div class="popup-body"><div class="popup-row"><span class="popup-label">Velocidad</span><span>${v.speed} km/h</span></div><div class="popup-row"><span class="popup-label">Combustible</span><span style="display:flex;align-items:center;gap:8px;width:100%"><span class="fuel-bar-mini"><span class="fuel-fill" style="width:${v.fuel}%;background:${v.fuel < 25 ? "#ef4444" : v.fuel < 50 ? "#f59e0b" : "#22c55e"}"></span></span><span style="white-space:nowrap">${v.fuel.toFixed(0)}% (${fuelLiters}L / ${tankL}L)</span></span></div><div class="popup-row"><span class="popup-label">Confiabilidad</span><span>${v.trust_score}/100</span></div></div></div>`;

          const isFocused = v.id === focusedVehicleId;
          const svgSize = v.status === "EN_ROUTE" ? 36 : 32;
          const statusEmoji = v.status === "EN_ROUTE" ? "🚨" : v.status === "REFUELING" ? "⛽" : v.status === "ON_SCENE" ? "🏥" : "";
          const ambulanceIcon = L.divIcon({
            html: `${statusEmoji ? `<div class="vehicle-status-emoji">${statusEmoji}</div>` : ""}${isFocused ? `<div class="focus-ring"></div>` : ""}${vehicleIcon(subtype, v.status, svgSize)}`,
            className: `ambulance-marker${isFocused ? " focused" : ""}`,
            iconSize: [svgSize, svgSize + (statusEmoji ? 18 : 0)],
            iconAnchor: [svgSize / 2, svgSize / 2 + (statusEmoji ? 18 : 0)],
          });

          let marker = markersRef.current.get(v.id);
          if (!marker) {
            marker = L.marker(latlng, { icon: ambulanceIcon }).addTo(layerRef.current);
            marker.bindPopup(popup);
            markersRef.current.set(v.id, marker);
          } else {
            marker.setLatLng(latlng);
            marker.setPopupContent(popup);
            marker.setIcon(ambulanceIcon);
          }
        }
        for (const [id, marker] of markersRef.current.entries()) {
          if (!seen.has(id)) { layerRef.current.removeLayer(marker); markersRef.current.delete(id); }
        }

        // Coverage circles
        if (showCoverage) {
          const activeIds = new Set();
          for (const v of vList) {
            if (v.status === "IDLE") {
              activeIds.add(v.id);
              const existing = coverageCirclesRef.current.get(v.id);
              if (existing) { existing.setLatLng([v.lat, v.lon]); }
              else {
                const subtypeRadius = { SVA: 3500, SVB: 3000, VIR: 4500, VAMM: 2500, SAMU: 3000 };
                const subtypeColor = { SVA: "#ef4444", SVB: "#22c55e", VIR: "#3b82f6", VAMM: "#f97316", SAMU: "#a855f7" };
                const cCircle = L.circle([v.lat, v.lon], { radius: subtypeRadius[v.subtype] || 3000, color: subtypeColor[v.subtype] || "#22c55e", fillColor: subtypeColor[v.subtype] || "#22c55e", fillOpacity: 0.08, weight: 1.5, opacity: 0.35, dashArray: "6, 4", interactive: false, pane: "shadowPane" }).addTo(layerRef.current);
                coverageCirclesRef.current.set(v.id, cCircle);
              }
            }
          }
          for (const [id, circ] of coverageCirclesRef.current.entries()) {
            if (!activeIds.has(id)) { layerRef.current.removeLayer(circ); coverageCirclesRef.current.delete(id); }
          }
        } else {
          for (const [, circ] of coverageCirclesRef.current.entries()) layerRef.current.removeLayer(circ);
          coverageCirclesRef.current.clear();
        }

        // Update incidents
        const incidentsData = data.incidents || [];
        setIncidents(incidentsData);
        const seenInc = new Set();
        const currentIds = new Set();

        for (const inc of incidentsData) {
          seenInc.add(inc.id);
          currentIds.add(inc.id);
          const latlng = [inc.lat, inc.lon];
          const popup = `<div class="map-popup"><div class="popup-header incident-popup severity-${inc.severity}"><strong>${inc.incident_type || "GENERAL"}</strong><span class="popup-badge ${inc.status.toLowerCase()}">${getStatusLabel(inc.status)}</span></div><div class="popup-body"><div class="popup-row"><span class="popup-label">Severidad</span><span class="severity-dots">${"●".repeat(inc.severity)}${"○".repeat(5 - inc.severity)}</span></div><div class="popup-row"><span class="popup-label">Ambulancia</span><span>${inc.assigned_vehicle_id || "Sin asignar"}</span></div><div class="popup-row"><span class="popup-label">Hospital</span><span>${inc.assigned_hospital_id || "Sin asignar"}</span></div></div><button onclick="window.selectIncidentFromMap('${inc.id}')" class="popup-action-btn">Ver detalles</button></div>`;

          let circle = incidentsRef.current.get(inc.id);
          const icon = L.divIcon({ html: incidentIcon(inc.severity, inc.status), className: "incident-marker-wrap", iconSize: [34, 41], iconAnchor: [17, 41] });
          if (!circle) {
            circle = L.marker(latlng, { icon });
            circle.bindPopup(popup);
            if (incidentClusterRef.current) incidentClusterRef.current.addLayer(circle);
            incidentsRef.current.set(inc.id, circle);
          } else {
            circle.setLatLng(latlng);
            circle.setIcon(icon);
            circle.setPopupContent(popup);
          }

          // Route polylines
          try {
            const isActiveRoute = inc.route_data && inc.status === "ASSIGNED";
            const phase = inc.route_phase || "TO_INCIDENT";
            if (isActiveRoute) {
              const routeObj = typeof inc.route_data === "string" ? JSON.parse(inc.route_data) : inc.route_data;
              const coords = routeObj?.geometry || routeObj;
              const incIdx = routeObj?.incident_waypoint_idx;
              if (Array.isArray(coords) && coords.length > 1) {
                const oldRoute = routesRef.current.get(inc.id);
                if (oldRoute) { (Array.isArray(oldRoute) ? oldRoute : [oldRoute]).forEach(p => layerRef.current.removeLayer(p)); }
                const lines = [];
                const isToHosp = phase === "TO_HOSPITAL", isAtInc = phase === "AT_INCIDENT";
                if (incIdx && incIdx > 0 && incIdx < coords.length) {
                  const abDone = isToHosp || isAtInc;
                  lines.push(L.polyline(coords.slice(0, incIdx + 1), { color: abDone ? "#94a3b8" : "#3b82f6", weight: abDone ? 3 : 5, opacity: abDone ? 0.4 : 0.9, dashArray: abDone ? "6, 8" : null }).addTo(layerRef.current));
                  const legBC = coords.slice(incIdx);
                  if (legBC.length > 1) lines.push(L.polyline(legBC, { color: isToHosp ? "#10b981" : "#6ee7b7", weight: isToHosp ? 5 : 3, opacity: isToHosp ? 0.9 : 0.5, dashArray: isToHosp ? null : "6, 8" }).addTo(layerRef.current));
                } else {
                  lines.push(L.polyline(coords, { color: "#3b82f6", weight: 5, opacity: 0.9 }).addTo(layerRef.current));
                }
                routesRef.current.set(inc.id, lines);

                const av = inc.assigned_vehicle_id ? vehicleById[inc.assigned_vehicle_id] : null;
                const progress = inc.route_progress ?? 0;
                if (av && progress > 0 && progress < 1) {
                  const oldDot = routeDotsRef.current.get(inc.id);
                  if (oldDot) layerRef.current.removeLayer(oldDot);
                  const dot = L.marker([av.lat, av.lon], { icon: L.divIcon({ html: '<div class="route-progress-dot"></div>', className: "route-progress-dot-wrap", iconSize: [16, 16], iconAnchor: [8, 8] }), interactive: false }).addTo(layerRef.current);
                  routeDotsRef.current.set(inc.id, dot);
                }
              }
            } else {
              const oldRoute = routesRef.current.get(inc.id);
              if (oldRoute) { (Array.isArray(oldRoute) ? oldRoute : [oldRoute]).forEach(p => layerRef.current.removeLayer(p)); routesRef.current.delete(inc.id); }
              const oldDot = routeDotsRef.current.get(inc.id);
              if (oldDot) { layerRef.current.removeLayer(oldDot); routeDotsRef.current.delete(inc.id); }
            }
          } catch { /* ignore invalid route_data */ }
        }

        // Cleanup stale markers
        for (const [id, circle] of incidentsRef.current.entries()) {
          if (!seenInc.has(id)) { if (incidentClusterRef.current) incidentClusterRef.current.removeLayer(circle); else layerRef.current.removeLayer(circle); incidentsRef.current.delete(id); }
        }
        for (const [id, polylines] of routesRef.current.entries()) {
          if (!seenInc.has(id)) { (Array.isArray(polylines) ? polylines : [polylines]).forEach(p => layerRef.current.removeLayer(p)); routesRef.current.delete(id); }
        }
        for (const [id, dot] of routeDotsRef.current.entries()) {
          if (!seenInc.has(id)) { layerRef.current.removeLayer(dot); routeDotsRef.current.delete(id); }
        }

        // New incident notifications + AI suggestions
        for (const id of currentIds) {
          if (!prevIncidentIdsRef.current.has(id)) {
            const inc = incidentsData.find(i => i.id === id);
            if (inc?.status === "OPEN") {
              toast.error(`Nuevo incidente: ${inc.incident_type || "GENERAL"} - Severidad ${inc.severity}/5`, { duration: 5000, position: "top-right" });
              if (inc.incident_type === "BURN") setEmergencyAlert({ type: "FIREFIGHTERS", incident: inc });
              else if (inc.incident_type === "VIOLENCE") setEmergencyAlert({ type: "POLICE", incident: inc });
              if (token && (user?.role === "ADMIN" || user?.role === "OPERATOR")) {
                (async () => {
                  try {
                    const r = await fetch(`${API_BASE}/api/assignments/suggest/${inc.id}`, { headers: { Authorization: `Bearer ${token}` } });
                    if (r.ok) { const suggestion = await r.json(); setAiAutoSuggestions(prev => [...prev.filter(s => s.incidentId !== inc.id), { incidentId: inc.id, incident: inc, suggestion }]); }
                  } catch { /* ignore */ }
                })();
              }
            }
          }
        }
        prevIncidentIdsRef.current = currentIds;

        // Heatmap data
        if (heatLayerRef.current) { map.removeLayer(heatLayerRef.current); heatLayerRef.current = null; }
        const heatPoints = incidentsData.filter(i => i.status !== "RESOLVED").map(i => [i.lat, i.lon, i.severity || 3]);
        if (heatPoints.length > 0) {
          heatLayerRef.current = L.heatLayer(heatPoints, { radius: 30, blur: 20, maxZoom: 15, gradient: { 0.2: "blue", 0.4: "lime", 0.6: "yellow", 0.8: "orange", 1: "red" } });
        }

        if (data.gas_stations) setGasStations(data.gas_stations);
      } catch (e) { console.error("Error fetching data:", e); }
    };

    updateData();
    pollInterval = setInterval(updateData, 1500);

    window.selectIncidentFromMap = (incidentId) => {
      const incident = incidents.find(i => i.id === incidentId);
      if (incident) setSelectedIncident(incident);
    };

    return () => {
      stopped = true;
      if (pollInterval) clearInterval(pollInterval);
      try { map.remove(); } catch { /* ignored */ }
    };
  }, [focusedVehicleId, fetchWeather, onMapMouseMove, token, user?.role]);

  // ── Map layer toggle effects ───────────────────────────────────────────
  useEffect(() => {
    if (!mapRef.current || !heatLayerRef.current) return;
    if (showHeatmap) heatLayerRef.current.addTo(mapRef.current);
    else mapRef.current.removeLayer(heatLayerRef.current);
  }, [showHeatmap, incidents]);

  useEffect(() => {
    for (const [, polylines] of routesRef.current.entries()) {
      (Array.isArray(polylines) ? polylines : [polylines]).forEach(p => p.setStyle({ opacity: showRoutes ? 0.8 : 0 }));
    }
  }, [showRoutes, incidents]);

  useEffect(() => {
    if (!layerRef.current) return;
    for (const [, circ] of coverageCirclesRef.current.entries()) layerRef.current.removeLayer(circ);
    coverageCirclesRef.current.clear();
    if (showCoverage && vehicles.length > 0) {
      for (const v of vehicles) {
        if (v.enabled && v.status !== "REFUELING") {
          const subtypeRadius = { SVA: 3500, SVB: 3000, VIR: 4500, VAMM: 2500, SAMU: 3000 };
          const subtypeColor = { SVA: "#ef4444", SVB: "#22c55e", VIR: "#3b82f6", VAMM: "#f97316", SAMU: "#a855f7" };
          const color = subtypeColor[v.subtype] || "#22c55e";
          const cCircle = L.circle([v.lat, v.lon], { radius: subtypeRadius[v.subtype] || 3000, color, fillColor: color, fillOpacity: 0.08, weight: 1.5, opacity: 0.35, dashArray: "6, 4", interactive: false, pane: "shadowPane" }).addTo(layerRef.current);
          coverageCirclesRef.current.set(v.id, cCircle);
        }
      }
    }
  }, [showCoverage, vehicles]);

  useEffect(() => {
    if (!mapRef.current || !layerRef.current) return;
    for (const [, m] of hospitalsRef.current.entries()) layerRef.current.removeLayer(m);
    hospitalsRef.current.clear();
    for (const hospital of hospitals) {
      const occupancyPct = hospital.capacity > 0 ? Math.round((hospital.current_load / hospital.capacity) * 100) : 0;
      const iconColor = occupancyPct >= 85 ? "#ef4444" : occupancyPct >= 60 ? "#f59e0b" : "#22c55e";
      const marker = L.marker([hospital.lat, hospital.lon], { icon: L.divIcon({ html: hospitalSvg(38, iconColor), className: "hospital-marker", iconSize: [38, 38], iconAnchor: [19, 19] }) }).addTo(layerRef.current);
      const availPct = hospital.availability_pct ?? (hospital.capacity > 0 ? Math.round(((hospital.capacity - hospital.current_load) / hospital.capacity) * 100) : 100);
      const barColor = occupancyPct < 60 ? "#22c55e" : occupancyPct < 85 ? "#f59e0b" : "#ef4444";
      marker.bindPopup(`<div class="map-popup"><div class="popup-header hospital-popup"><strong>${hospital.name}</strong></div><div class="popup-body"><div class="popup-row"><span class="popup-label">Ocupación</span><span class="fuel-bar-mini"><span class="fuel-fill" style="width:${occupancyPct}%;background:${barColor}"></span></span><span>${hospital.current_load}/${hospital.capacity} (${occupancyPct}%)</span></div><div class="popup-row"><span class="popup-label">Disponibilidad</span><span style="color:${availPct > 40 ? "#22c55e" : availPct > 15 ? "#f59e0b" : "#ef4444"}">${availPct}%</span></div><div class="popup-row"><span class="popup-label">Especialidades</span><span>${(hospital.specialties || []).join(", ") || "General"}</span></div></div></div>`);
      hospitalsRef.current.set(hospital.id, marker);
    }
  }, [hospitals]);

  useEffect(() => {
    if (!mapRef.current || !layerRef.current) return;
    for (const [, m] of gasStationsRef.current.entries()) layerRef.current.removeLayer(m);
    gasStationsRef.current.clear();
    if (!showGasStations) return;
    for (const gs of gasStations) {
      const marker = L.marker([gs.lat, gs.lon], { icon: L.divIcon({ html: gasStationIcon(34), className: "gas-station-marker", iconSize: [34, 34], iconAnchor: [17, 17] }) }).addTo(layerRef.current);
      marker.bindPopup(`<div class="map-popup"><div class="popup-header gas-popup"><strong>${gs.name}</strong>${gs.open_24h ? '<span class="popup-badge open24">24h</span>' : ""}</div><div class="popup-body"><div class="popup-row"><span class="popup-label">Marca</span><span>${gs.brand || "Genérica"}</span></div><div class="popup-row"><span class="popup-label">Precio</span><span class="price-tag">${gs.price_per_liter.toFixed(2)} €/L</span></div><div class="popup-row"><span class="popup-label">Combustibles</span><span>${(gs.fuel_types || []).join(", ")}</span></div></div></div>`);
      gasStationsRef.current.set(gs.id, marker);
    }
  }, [gasStations, showGasStations]);

  useEffect(() => {
    if (!mapRef.current || !layerRef.current) return;
    for (const [, m] of deaMarkersRef.current) layerRef.current.removeLayer(m);
    deaMarkersRef.current.clear();
    if (!showDEA) return;
    for (const dea of deaLocations) {
      const m = L.marker([dea.lat, dea.lon], { icon: L.divIcon({ html: `<div style="background:#22c55e;border-radius:50%;width:28px;height:28px;display:flex;align-items:center;justify-content:center;border:2px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,.3);font-size:16px;">💚</div>`, className: "dea-marker", iconSize: [28, 28], iconAnchor: [14, 14] }) }).addTo(layerRef.current);
      m.bindPopup(`<div class="map-popup"><div class="popup-header" style="background:#22c55e;color:#fff"><strong>DEA: ${dea.name}</strong></div><div class="popup-body"><div class="popup-row"><span class="popup-label">Tipo</span><span>${dea.location_type || "Público"}</span></div><div class="popup-row"><span class="popup-label">Horario</span><span>${dea.access_hours || "24h"}</span></div></div></div>`);
      deaMarkersRef.current.set(dea.id, m);
    }
  }, [deaLocations, showDEA]);

  useEffect(() => {
    if (!mapRef.current || !layerRef.current) return;
    for (const [, m] of gisMarkersRef.current) layerRef.current.removeLayer(m);
    gisMarkersRef.current.clear();
    if (!showGIS) return;
    const gisIcons = { SCHOOL: "🏫", NURSING_HOME: "🏥", HAZMAT: "☢️", METRO: "🚇", POLICE: "👮", FIRE: "🚒" };
    const gisColors = { SCHOOL: "#3b82f6", NURSING_HOME: "#a855f7", HAZMAT: "#ef4444", METRO: "#06b6d4", POLICE: "#1e40af", FIRE: "#dc2626" };
    for (const poi of gisLayers) {
      const emoji = gisIcons[poi.layer_type] || "📍";
      const color = gisColors[poi.layer_type] || "#6b7280";
      const m = L.marker([poi.lat, poi.lon], { icon: L.divIcon({ html: `<div style="background:${color};border-radius:50%;width:26px;height:26px;display:flex;align-items:center;justify-content:center;border:2px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,.3);font-size:14px;">${emoji}</div>`, className: "gis-marker", iconSize: [26, 26], iconAnchor: [13, 13] }) }).addTo(layerRef.current);
      m.bindPopup(`<div class="map-popup"><div class="popup-header" style="background:${color};color:#fff"><strong>${poi.name}</strong></div><div class="popup-body"><div class="popup-row"><span class="popup-label">Tipo</span><span>${poi.layer_type}</span></div><div class="popup-row"><span class="popup-label">Riesgo</span><span>${poi.risk_level || "NORMAL"}</span></div></div></div>`);
      gisMarkersRef.current.set(poi.id, m);
    }
  }, [gisLayers, showGIS]);

  useEffect(() => {
    if (!mapRef.current || !layerRef.current) return;
    for (const [, m] of agencyMarkersRef.current) layerRef.current.removeLayer(m);
    agencyMarkersRef.current.clear();
    if (!showAgencies) return;
    const agColors = { BOMBEROS: "#ef4444", POLICIA_NACIONAL: "#1e40af", POLICIA_MUNICIPAL: "#3b82f6", PROTECCION_CIVIL: "#f59e0b" };
    const agEmoji = { BOMBEROS: "🚒", POLICIA_NACIONAL: "🚔", POLICIA_MUNICIPAL: "🚓", PROTECCION_CIVIL: "🛡️" };
    for (const ag of agencyResources) {
      if (!ag.lat || !ag.lon) continue;
      const color = agColors[ag.agency] || "#6b7280";
      const emoji = agEmoji[ag.agency] || "🏢";
      const m = L.marker([ag.lat, ag.lon], { icon: L.divIcon({ html: `<div style="background:${color};border-radius:6px;padding:2px 6px;display:flex;align-items:center;gap:4px;border:2px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,.3);font-size:12px;color:#fff;white-space:nowrap;">${emoji} ${ag.unit_name}</div>`, className: "agency-marker", iconSize: [80, 28], iconAnchor: [40, 14] }) }).addTo(layerRef.current);
      m.bindPopup(`<div class="map-popup"><div class="popup-header" style="background:${color};color:#fff"><strong>${ag.unit_name}</strong></div><div class="popup-body"><div class="popup-row"><span class="popup-label">Agencia</span><span>${ag.agency}</span></div><div class="popup-row"><span class="popup-label">Estado</span><span>${ag.status}</span></div></div></div>`);
      agencyMarkersRef.current.set(ag.id, m);
    }
  }, [agencyResources, showAgencies]);

  useEffect(() => {
    if (!mapRef.current || !layerRef.current) return;
    for (const [, c] of ssmCirclesRef.current) layerRef.current.removeLayer(c);
    ssmCirclesRef.current.clear();
    if (!showSSM) return;
    const zones = ssmZones?.zones || ssmZones || [];
    for (const zone of zones) {
      const lat = zone.lat || zone.center_lat, lon = zone.lon || zone.center_lon;
      if (!lat || !lon) continue;
      const coverage = zone.coverage_pct ?? (zone.coverage_status === "OK" ? 100 : 40);
      const color = coverage >= 80 || zone.coverage_status === "OK" ? "#22c55e" : coverage >= 50 ? "#f59e0b" : "#ef4444";
      const circle = L.circle([lat, lon], { radius: 1500, color, fillColor: color, fillOpacity: 0.15, weight: 2 }).addTo(layerRef.current);
      const name = zone.name || zone.zone_name || zone.zone_id;
      circle.bindPopup(`<div class="map-popup"><div class="popup-header" style="background:${color};color:#fff"><strong>${name}</strong></div><div class="popup-body"><div class="popup-row"><span class="popup-label">Estado</span><span>${zone.coverage_status || "N/A"}</span></div><div class="popup-row"><span class="popup-label">Unidades rec.</span><span>${zone.recommended_units}</span></div></div></div>`);
      ssmCirclesRef.current.set(name, circle);
    }
  }, [ssmZones, showSSM]);

  useEffect(() => {
    if (!mapRef.current || !layerRef.current) return;
    for (const r of riskZonesRef.current) layerRef.current.removeLayer(r);
    riskZonesRef.current = [];
    if (!showRiskZones || incidents.length === 0) return;
    for (const inc of incidents.filter(i => i.status !== "RESOLVED" && i.status !== "CLOSED")) {
      const sev = inc.severity || 1;
      const color = sev >= 4 ? "#dc2626" : sev >= 3 ? "#f59e0b" : sev >= 2 ? "#f97316" : "#3b82f6";
      const circle = L.circle([inc.lat, inc.lon], { radius: 300 + sev * 100, color, fillColor: color, fillOpacity: 0.10 + sev * 0.04, weight: 2, opacity: 0.5 + sev * 0.08, dashArray: "6, 4" }).addTo(layerRef.current);
      circle.bindPopup(`<div class="map-popup"><div class="popup-header" style="background:${color};color:#fff"><strong>Zona de Riesgo</strong></div><div class="popup-body"><div class="popup-row"><span class="popup-label">Tipo</span><span>${inc.incident_type || inc.id}</span></div><div class="popup-row"><span class="popup-label">Severidad</span><span>${sev}/5</span></div></div></div>`);
      riskZonesRef.current.push(circle);
    }
  }, [incidents, showRiskZones]);

  // Proximity alerts
  useEffect(() => {
    if (!vehicles.length || !incidents.length) return;
    const openInc = incidents.filter(i => i.status === "OPEN" && !i.assigned_vehicle_id);
    const idleVeh = vehicles.filter(v => v.status === "IDLE");
    if (!openInc.length || !idleVeh.length) return;
    const PROXIMITY_KM = 2.5;
    const toRad = d => d * Math.PI / 180;
    const haversine = (lat1, lon1, lat2, lon2) => {
      const R = 6371, dLat = toRad(lat2 - lat1), dLon = toRad(lon2 - lon1);
      return R * 2 * Math.atan2(Math.sqrt(Math.sin(dLat / 2) ** 2 + Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2), Math.sqrt(1 - (Math.sin(dLat / 2) ** 2 + Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2)));
    };
    for (const inc of openInc) {
      for (const veh of idleVeh) {
        const dist = haversine(inc.lat, inc.lon, veh.lat, veh.lon);
        const key = `${inc.id}_${veh.id}`;
        if (dist <= PROXIMITY_KM && !proximityAlertedRef.current.has(key)) {
          proximityAlertedRef.current.add(key);
          toast(`${veh.id} está a ${dist.toFixed(1)}km del incidente ${inc.incident_type || "GENERAL"} (sev ${inc.severity})`, { icon: "🔔", duration: 6000, position: "top-right", style: { background: "#1e293b", color: "#f1f5f9", border: "1px solid #f59e0b40" } });
        }
      }
    }
    for (const key of proximityAlertedRef.current) {
      const incId = key.split("_")[0];
      if (!incidents.find(i => i.id === incId && i.status === "OPEN")) proximityAlertedRef.current.delete(key);
    }
  }, [vehicles, incidents]);

  // Security events polling
  useEffect(() => {
    const check = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/security/events?limit=5&severity=HIGH`);
        if (!res.ok) return;
        const events = await res.json();
        if (Array.isArray(events) && events.length > 0) {
          const latest = events[0];
          const eventKey = latest.id || latest.timestamp || JSON.stringify(latest).slice(0, 50);
          if (lastSecEventIdRef.current && eventKey !== lastSecEventIdRef.current) {
            const sev = latest.severity || "HIGH";
            toast(`${sev === "CRITICAL" ? "🔴" : sev === "HIGH" ? "🟠" : "🟡"} Security: ${latest.event_type || "Threat"} — ${latest.details || sev}`, { duration: 8000, position: "top-right", style: { background: sev === "CRITICAL" ? "#7f1d1d" : "#78350f", color: "#fff", border: `1px solid ${sev === "CRITICAL" ? "#dc2626" : "#f59e0b"}`, fontWeight: 500 } });
          }
          lastSecEventIdRef.current = eventKey;
        }
      } catch { /* ignore */ }
    };
    check();
    const interval = setInterval(check, 15000);
    return () => clearInterval(interval);
  }, []);

  // ── Derived data ───────────────────────────────────────────────────────
  const openIncidents = useMemo(() => incidents.filter(i => i.status === "OPEN"), [incidents]);
  const assignedIncidents = useMemo(() => incidents.filter(i => ["ASSIGNED", "EN_ROUTE"].includes(i.status)), [incidents]);

  const closeModal = useCallback(() => { setSelectedIncident(null); setIncidentTimeline(null); }, []);

  // ── Render ─────────────────────────────────────────────────────────────
  return (
    <div className="dashboard-container" ref={dashboardRef}>
      <Toaster />

      <div className="map-area">
        <div id="map" className="dashboard-map" />
        <MapControlsToolbar
          showHeatmap={showHeatmap} setShowHeatmap={setShowHeatmap}
          showRoutes={showRoutes} setShowRoutes={setShowRoutes}
          showGasStations={showGasStations} setShowGasStations={setShowGasStations}
          showDEA={showDEA} setShowDEA={setShowDEA}
          showGIS={showGIS} setShowGIS={setShowGIS}
          showAgencies={showAgencies} setShowAgencies={setShowAgencies}
          showSSM={showSSM} setShowSSM={setShowSSM}
          showCoverage={showCoverage} setShowCoverage={setShowCoverage}
          showRiskZones={showRiskZones} setShowRiskZones={setShowRiskZones}
        />
        <WeatherWidget weather={weather} />
        <MapLegend />
      </div>

      <div className="control-panel">
        <div className="panel-header">
          <h2><LayoutDashboard size={24} className="icon-3d" /> Control Central</h2>
          <div className="panel-header-right">
            <div className="user-badge">
              <span className="role-badge">{user?.role || "USER"}</span>
              <span>{user?.username}</span>
            </div>
          </div>
        </div>

        <SimulationControls
          {...simControls}
          exporting={exporting}
          exportToPDF={exportToPDF}
          getIncidentTypeLabel={getIncidentTypeLabel}
        />

        <MetricCards
          fleetMetrics={fleetMetrics}
          openIncidents={openIncidents}
          hospitals={hospitals}
          gasStations={gasStations}
          deaLocations={deaLocations}
        />

        <IncidentListPanel
          openIncidents={openIncidents}
          setSelectedIncident={setSelectedIncident}
          focusIncident={focusIncident}
          getIncidentTypeLabel={getIncidentTypeLabel}
        />

        <ActiveIncidentsPanel
          assignedIncidents={assignedIncidents}
          setSelectedIncident={setSelectedIncident}
          focusIncident={focusIncident}
          followVehicle={followVehicle}
          getIncidentTypeLabel={getIncidentTypeLabel}
        />

        <FleetListPanel
          vehicles={vehicles}
          focusedVehicleId={focusedVehicleId}
          focusVehicle={focusVehicle}
          subtypeFilter={subtypeFilter} setSubtypeFilter={setSubtypeFilter}
          statusFilter={statusFilter} setStatusFilter={setStatusFilter}
        />

        <OpsResumePanel
          vehicles={vehicles}
          openIncidents={openIncidents}
          assignedIncidents={assignedIncidents}
          incidents={incidents}
        />

        <DigitalTwinPanel
          {...twin}
          focusedVehicleId={focusedVehicleId}
        />
      </div>

      <EmergencyAlertModal emergencyAlert={emergencyAlert} setEmergencyAlert={setEmergencyAlert} />

      <AiAutoSuggestionsPanel
        aiAutoSuggestions={aiAutoSuggestions}
        dismissAiAutoSuggestion={dismissAiAutoSuggestion}
        confirmAssignment={confirmAssignment}
        setSelectedIncident={setSelectedIncident}
        setAiSuggestion={setAiSuggestion}
        getIncidentTypeLabel={getIncidentTypeLabel}
      />

      <IncidentDetailModal
        selectedIncident={selectedIncident}
        onClose={closeModal}
        incidentTimeline={incidentTimeline}
        fetchTimeline={fetchTimeline}
        aiSuggestion={aiSuggestion}
        setAiSuggestion={setAiSuggestion}
        loadingSuggestion={loadingSuggestion}
        getAISuggestion={getAISuggestion}
        overrideMode={overrideMode} setOverrideMode={setOverrideMode}
        overrideVehicle={overrideVehicle} setOverrideVehicle={setOverrideVehicle}
        overrideHospital={overrideHospital} setOverrideHospital={setOverrideHospital}
        overrideReason={overrideReason} setOverrideReason={setOverrideReason}
        confirmAssignment={confirmAssignment}
        resolveIncident={resolveIncident}
        vehicles={vehicles}
        hospitals={hospitals}
        user={user}
        getIncidentTypeLabel={getIncidentTypeLabel}
      />
    </div>
  );
}
