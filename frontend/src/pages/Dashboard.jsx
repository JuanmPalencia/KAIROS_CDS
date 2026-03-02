import { useEffect, useRef, useState, useCallback } from "react";
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
import { Ambulance, Fuel, Flame, Hospital, AlertTriangle, MapPin, CheckCircle, RefreshCw, LayoutDashboard, Map as MapIcon, Route, ClipboardList, ScrollText, Bot, Pencil, Star, Zap, Heart, Wind, Brain, Skull, HeartPulse, Baby, Smile, Droplets, Shield, Filter, Siren, Phone, X, Play, Square, RotateCcw, Sparkles, Thermometer, Pill, Waves, PersonStanding, Activity, Info, ChevronDown, ChevronUp, Clock, TrendingUp, BarChart3, Gauge, Download, Cpu, Wifi, AlertCircle, Wrench, Radio, Eye, EyeOff } from 'lucide-react';
import { vehicleIcon, hospitalIcon as hospitalSvg, gasStationIcon, incidentIcon } from '../components/mapIcons';
import html2canvas from 'html2canvas';
import "../styles/Dashboard.css";
import { API_BASE } from "../config";
import { statusLabel as getStatusLabel } from "../utils/statusLabels";
import { useIncidentNotifications } from "../hooks/useIncidentNotifications";

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
});

/* ── Map Legend (collapsible) ───────────────────────────────────────── */
function MapLegend() {
  const [open, setOpen] = useState(false);
  return (
    <div className={`map-legend ${open ? "open" : ""}`}>
      <button className="map-legend-toggle" onClick={() => setOpen(v => !v)}>
        <Info size={14} /> Leyenda {open ? <ChevronDown size={13} /> : <ChevronUp size={13} />}
      </button>
      {open && (
        <div className="map-legend-body">
          <div className="legend-section">
            <span className="legend-title">Ambulancias</span>
            <div className="legend-item"><span className="legend-dot" style={{ background: "#22c55e" }} /><span className="legend-cross">✚</span> SVB — Soporte Vital Básico</div>
            <div className="legend-item"><span className="legend-dot" style={{ background: "#ef4444", border: "2px solid #fbbf24" }} /><span className="legend-cross">✚</span> SVA — Soporte Vital Avanzado</div>
            <div className="legend-item"><span className="legend-dot" style={{ background: "#3b82f6" }} /><span className="legend-cross">⚡</span> VIR — Intervención Rápida</div>
            <div className="legend-item"><span className="legend-dot" style={{ background: "#f97316" }} /><span className="legend-cross">✚✚</span> VAMM — Asistencia Múltiple</div>
            <div className="legend-item"><span className="legend-dot" style={{ background: "#a855f7" }} /><span className="legend-cross">♥</span> SAMU — Atención Urgente</div>
          </div>
          <div className="legend-section">
            <span className="legend-title">Estado ambulancia</span>
            <div className="legend-item"><span className="legend-shape circle" /> Disponible / Ocupada</div>
            <div className="legend-item"><span className="legend-shape rect" /> En ruta</div>
          </div>
          <div className="legend-section">
            <span className="legend-title">Puntos de interés</span>
            <div className="legend-item"><span className="legend-poi hospital-poi">✚</span> Hospital</div>
            <div className="legend-item"><span className="legend-poi gas-poi">⛽</span> Gasolinera</div>
            <div className="legend-item"><span className="legend-poi dea-poi">♥</span> DEA (Desfibrilador)</div>
          </div>
          <div className="legend-section">
            <span className="legend-title">Incidentes</span>
            <div className="legend-item"><span className="legend-pin" style={{ background: "#dc2626" }} /> Severidad 4-5 (crítico)</div>
            <div className="legend-item"><span className="legend-pin" style={{ background: "#ef4444" }} /> Severidad 3 (grave)</div>
            <div className="legend-item"><span className="legend-pin" style={{ background: "#f97316" }} /> Severidad 1-2 (moderado)</div>
            <div className="legend-item"><span className="legend-pin" style={{ background: "#f59e0b" }} /> Asignado</div>
          </div>
        </div>
      )}
    </div>
  );
}

// WMO weather code mapping (condition, alert, eta_multiplier)
const WMO_MAP = {
  0:["CLEAR","GREEN",1,"Despejado"],1:["CLEAR","GREEN",1,"Mayormente despejado"],
  2:["CLOUD","GREEN",1,"Parcialmente nublado"],3:["CLOUD","GREEN",1,"Nublado"],
  45:["FOG","YELLOW",1.3,"Niebla"],48:["FOG","YELLOW",1.3,"Niebla engelante"],
  51:["DRIZZLE","GREEN",1.05,"Llovizna ligera"],53:["DRIZZLE","YELLOW",1.1,"Llovizna moderada"],55:["DRIZZLE","YELLOW",1.15,"Llovizna intensa"],
  56:["DRIZZLE","YELLOW",1.2,"Llovizna engelante"],57:["DRIZZLE","ORANGE",1.3,"Llovizna engelante intensa"],
  61:["RAIN","YELLOW",1.2,"Lluvia ligera"],63:["RAIN","ORANGE",1.3,"Lluvia moderada"],65:["RAIN","RED",1.5,"Lluvia intensa"],
  66:["RAIN","ORANGE",1.3,"Lluvia engelante"],67:["RAIN","RED",1.5,"Lluvia engelante intensa"],
  71:["SNOW","ORANGE",1.5,"Nevada ligera"],73:["SNOW","RED",1.7,"Nevada moderada"],75:["SNOW","RED",2.0,"Nevada intensa"],
  77:["SNOW","ORANGE",1.4,"Granizo fino"],
  80:["SHOWERS","YELLOW",1.2,"Chubascos ligeros"],81:["SHOWERS","ORANGE",1.4,"Chubascos moderados"],82:["SHOWERS","RED",1.6,"Chubascos fuertes"],
  85:["SNOW","ORANGE",1.5,"Chubascos de nieve"],86:["SNOW","RED",1.8,"Chubascos de nieve fuertes"],
  95:["STORM","RED",1.8,"Tormenta"],96:["STORM","RED",2.0,"Tormenta con granizo"],99:["STORM","RED",2.2,"Tormenta severa con granizo"],
};
const COND_ICON = {
  CLEAR:"☀️",CLOUD:"☁️",FOG:"🌫️",DRIZZLE:"🌦️",RAIN:"🌧️",SHOWERS:"🌦️",SNOW:"❄️",STORM:"⛈️",HEAT:"🔥",
};

export default function Dashboard() {
  const { user, token } = useAuth();
  const mapRef = useRef(null);
  const layerRef = useRef(null);
  const markersRef = useRef(new Map());
  const incidentsRef = useRef(new Map());
  const hospitalsRef = useRef(new Map());
  const gasStationsRef = useRef(new Map());
  const routesRef = useRef(new Map());
  const incidentClusterRef = useRef(null);
  const heatLayerRef = useRef(null);
  const prevIncidentIdsRef = useRef(new Set());

  const [fleetMetrics, setFleetMetrics] = useState({
    active_vehicles: 0,
    avg_fuel: 0,
  });
  const [incidents, setIncidents] = useState([]);
  useIncidentNotifications(incidents);
  const [hospitals, setHospitals] = useState([]);
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [aiSuggestion, setAiSuggestion] = useState(null);
  const [loadingSuggestion, setLoadingSuggestion] = useState(false);
  const [showHeatmap, setShowHeatmap] = useState(false);
  const [showRoutes, setShowRoutes] = useState(true);
  const [showGasStations, setShowGasStations] = useState(true);
  const [gasStations, setGasStations] = useState([]);
  const [incidentTimeline, setIncidentTimeline] = useState(null);
  const [vehicles, setVehicles] = useState([]);
  const [focusedVehicleId, setFocusedVehicleId] = useState(null);
  // Restore filters from localStorage on mount
  const [subtypeFilter, setSubtypeFilter] = useState(() => localStorage.getItem("subtypeFilter") || "ALL");
  const [statusFilter, setStatusFilter] = useState(() => localStorage.getItem("statusFilter") || "ALL");
  const [emergencyAlert, setEmergencyAlert] = useState(null); // {type:'FIREFIGHTERS'|'POLICE', incident}
  const lastSecEventIdRef = useRef(null); // Track last seen security event
  const [aiAutoSuggestions, setAiAutoSuggestions] = useState([]); // [{incidentId, suggestion}]
  const [overrideMode, setOverrideMode] = useState(false);
  const [overrideVehicle, setOverrideVehicle] = useState("");
  const [overrideHospital, setOverrideHospital] = useState("");
  const [overrideReason, setOverrideReason] = useState("");
  const [autoGenRunning, setAutoGenRunning] = useState(false);
  const [autoGenInterval, setAutoGenInterval] = useState(30);
  const [autoGenCount, setAutoGenCount] = useState(0);
  const [resetting, setResetting] = useState(false);
  const [lastGenIncident, setLastGenIncident] = useState(null); // last auto-generated incident
  const prevAutoGenCountRef = useRef(0);

  // NEW: DEA, GIS, Weather, SSM, Agencies
  const [showDEA, setShowDEA] = useState(false);
  const [showGIS, setShowGIS] = useState(false);
  const [showAgencies, setShowAgencies] = useState(false);
  const [deaLocations, setDeaLocations] = useState([]);
  const [gisLayers, setGisLayers] = useState([]);
  const [agencyResources, setAgencyResources] = useState([]);
  const [weather, setWeather] = useState(null);
  const [ssmZones, setSsmZones] = useState([]);
  const [showSSM, setShowSSM] = useState(false);
  const deaMarkersRef = useRef(new Map());
  const gisMarkersRef = useRef(new Map());
  const agencyMarkersRef = useRef(new Map());
  const ssmCirclesRef = useRef(new Map());
  const coverageCirclesRef = useRef(new Map());
  const riskZonesRef = useRef([]);
  const routeDotsRef = useRef(new Map());
  const [showCoverage, setShowCoverage] = useState(true);
  const [showRiskZones, setShowRiskZones] = useState(false);

  /** Fly to a vehicle and highlight it */
  const focusVehicle = (vehicleId) => {
    const marker = markersRef.current.get(vehicleId);
    if (marker && mapRef.current) {
      const ll = marker.getLatLng();
      mapRef.current.flyTo(ll, 15, { duration: 0.8 });
      marker.openPopup();
      setFocusedVehicleId((prev) => (prev === vehicleId ? null : vehicleId));
    }
  };

  /** Fly to an incident on the map */
  const focusIncident = (incidentId) => {
    const circle = incidentsRef.current.get(incidentId);
    if (circle && mapRef.current) {
      const ll = circle.getLatLng();
      mapRef.current.flyTo(ll, 15, { duration: 0.8 });
      circle.openPopup();
    }
  };

  // Fetch hospitals + new resource layers on mount
  useEffect(() => {
    fetchHospitals();
    fetchResourceLayers();
  }, []);

  // Save filters to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem("subtypeFilter", subtypeFilter);
  }, [subtypeFilter]);

  useEffect(() => {
    localStorage.setItem("statusFilter", statusFilter);
  }, [statusFilter]);

  const fetchResourceLayers = async () => {
    const headers = { Authorization: `Bearer ${localStorage.getItem("token")}` };
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

  // Real-time weather directly from Open-Meteo (no backend round-trip)
  // Includes precipitation mm to cross-check WMO code accuracy
  const weatherTimerRef = useRef(null);
  const fetchWeather = useCallback(async (lat, lon) => {
    try {
      const url = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m,wind_gusts_10m,precipitation,rain,snowfall,cloud_cover&timezone=auto`;
      const res = await fetch(url);
      if (!res.ok) return;
      const data = await res.json();
      const cur = data.current || {};
      const wmo = cur.weather_code ?? 0;
      const temp = cur.temperature_2m ?? 0;
      const precip = cur.precipitation ?? 0;   // mm in last interval
      const rain = cur.rain ?? 0;              // mm liquid rain
      const snow = cur.snowfall ?? 0;          // cm snowfall
      const cloudCover = cur.cloud_cover ?? 0;

      let entry = WMO_MAP[wmo] || ["CLOUD","GREEN",1,"Nublado"];
      let [cond, alert, mult, desc] = entry;

      // Cross-check: if WMO says rain/drizzle/showers but precipitation is 0, downgrade
      if (["RAIN","DRIZZLE","SHOWERS"].includes(cond) && precip < 0.1 && rain < 0.1) {
        cond = cloudCover > 70 ? "CLOUD" : cloudCover > 30 ? "CLOUD" : "CLEAR";
        alert = "GREEN";
        mult = 1;
        desc = cloudCover > 70 ? "Nublado" : cloudCover > 30 ? "Parcialmente nublado" : "Despejado";
      }
      // Cross-check: if WMO says snow but no snowfall measured, downgrade
      if (cond === "SNOW" && snow < 0.01 && precip < 0.1) {
        cond = "CLOUD";
        alert = "GREEN";
        mult = 1;
        desc = "Nublado";
      }
      // Heat override
      if (temp >= 38 && cond === "CLEAR") { cond = "HEAT"; alert = "ORANGE"; mult = 1.1; desc = "Calor extremo"; }

      let displayDesc = desc;
      if (alert !== "GREEN") displayDesc += ` — ETAs x${mult.toFixed(1)}`;

      setWeather({
        condition: cond,
        temperature_c: Math.round(temp * 10) / 10,
        apparent_temperature_c: Math.round((cur.apparent_temperature ?? temp) * 10) / 10,
        humidity_pct: cur.relative_humidity_2m ?? 0,
        wind_speed_kmh: Math.round((cur.wind_speed_10m ?? 0) * 10) / 10,
        wind_gusts_kmh: Math.round((cur.wind_gusts_10m ?? 0) * 10) / 10,
        precipitation_mm: Math.round(precip * 10) / 10,
        cloud_cover_pct: cloudCover,
        eta_multiplier: mult,
        alert_level: alert,
        description: displayDesc,
        detail_desc: desc,
        wmo_code: wmo,
        icon: COND_ICON[cond] || "☁️",
      });
    } catch (e) { console.error("Weather fetch error:", e); }
  }, []);

  // Debounced weather fetch following mouse position (2s debounce — reduced API calls)
  const onMapMouseMove = useCallback((e) => {
    clearTimeout(weatherTimerRef.current);
    weatherTimerRef.current = setTimeout(() => {
      fetchWeather(e.latlng.lat.toFixed(4), e.latlng.lng.toFixed(4));
    }, 2000);
  }, [fetchWeather]);

  const fetchHospitals = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/hospitals/`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });
      if (!res.ok) {
        console.error("Failed to fetch hospitals:", res.status);
        return;
      }
      const data = await res.json();
      if (Array.isArray(data)) {
        setHospitals(data);
      }
    } catch (error) {
      console.error("Error fetching hospitals:", error);
    }
  };

  const getAISuggestion = async (incidentId) => {
    setLoadingSuggestion(true);
    try {
      const res = await fetch(
        `${API_BASE}/api/assignments/suggest/${incidentId}`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
        }
      );
      const data = await res.json();
      setAiSuggestion(data);
    } catch (error) {
      console.error("Error getting AI suggestion:", error);
      alert("Error al obtener sugerencia de IA");
    } finally {
      setLoadingSuggestion(false);
    }
  };

  const confirmAssignment = async (incidentId, vehicleId, hospitalId, reason) => {
    try {
      const res = await fetch(
        `${API_BASE}/api/assignments/confirm`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
          body: JSON.stringify({
            incident_id: incidentId,
            vehicle_id: vehicleId,
            hospital_id: hospitalId,
            override_reason: reason,
          }),
        }
      );

      if (res.ok) {
        toast.success("✅ Asignación confirmada");
        setSelectedIncident(null);
        setAiSuggestion(null);
        setOverrideMode(false);
        setOverrideVehicle("");
        setOverrideHospital("");
        setOverrideReason("");
      } else {
        toast.error("Error al confirmar asignación");
      }
    } catch (error) {
      console.error("Error confirming assignment:", error);
      toast.error("Error de conexión");
    }
  };

  const resolveIncident = async (incidentId) => {
    if (!confirm("¿Marcar este incidente como resuelto?")) return;

    try {
      const res = await fetch(
        `${API_BASE}/api/assignments/resolve/${incidentId}`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
        }
      );

      if (res.ok) {
        toast.success("✅ Incidente resuelto");
        setSelectedIncident(null);
      } else {
        toast.error("Error al resolver incidente");
      }
    } catch (error) {
      console.error("Error resolving incident:", error);
      toast.error("Error de conexión");
    }
  };

  useEffect(() => {
    // Create map
    const map = L.map("map").setView([40.4168, -3.7038], 12);
    mapRef.current = map;

    // Ensure map renders correctly (optimized, without flicker)
    map.invalidateSize(false);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "&copy; OpenStreetMap contributors",
    }).addTo(map);

    layerRef.current = L.layerGroup().addTo(map);

    // Cluster group for incident markers
    incidentClusterRef.current = L.markerClusterGroup({
      maxClusterRadius: 45,
      spiderfyOnMaxZoom: true,
      showCoverageOnHover: false,
      zoomToBoundsOnClick: true,
      disableClusteringAtZoom: 16,
      iconCreateFunction: (cluster) => {
        const count = cluster.getChildCount();
        let size = 'small';
        let c = '#3b82f6';
        if (count >= 20) { size = 'large'; c = '#dc2626'; }
        else if (count >= 5) { size = 'medium'; c = '#f59e0b'; }
        const dim = size === 'large' ? 44 : size === 'medium' ? 36 : 30;
        return L.divIcon({
          html: `<div style="background:${c};color:#fff;border-radius:50%;width:${dim}px;height:${dim}px;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:${dim > 36 ? 15 : 13}px;box-shadow:0 2px 8px ${c}80;border:2px solid #fff">${count}</div>`,
          className: 'incident-cluster-icon',
          iconSize: L.point(dim, dim),
        });
      },
    });
    incidentClusterRef.current.addTo(map);

    // Weather: fetch on mouse position + initial center
    map.on("mousemove", onMapMouseMove);
    fetchWeather(40.4168, -3.7038);

    // Polling instead of WebSocket for stable updates every 3 seconds
    let stopped = false;
    let pollInterval;

    const updateData = async () => {
      if (stopped) return;
      
      try {
        // Fetch live data
        const cityF = localStorage.getItem("cityFilter") || "";
        const liveUrl = cityF ? `${API_BASE}/api/live?city=${encodeURIComponent(cityF)}` : `${API_BASE}/api/live`;
        const res = await fetch(liveUrl);
        if (!res.ok) throw new Error("Failed to fetch");
        
        const data = await res.json();

        if (data.fleet_metrics) setFleetMetrics(data.fleet_metrics);

        // Update hospitals from live data
        if (data.hospitals && Array.isArray(data.hospitals)) {
          setHospitals(data.hospitals);
        }

        // Update vehicles
        const vehicles = data.vehicles || [];
        setVehicles(vehicles);
        const seen = new Set();

        for (const v of vehicles) {
          seen.add(v.id);

          let marker = markersRef.current.get(v.id);
          const latlng = [v.lat, v.lon];

          // Vehicle icon based on status
          const subtype = v.subtype || "SVB";
          const SUBTYPE_NAMES = { SVB: "Soporte Vital Básico", SVA: "Soporte Vital Avanzado", VIR: "Intervención Rápida", VAMM: "Asistencia Múltiple", SAMU: "SAMU" };
          const subtypeName = SUBTYPE_NAMES[subtype] || subtype;
          const statusLabel = getStatusLabel(v.status);
          const tankL = v.tank_capacity || 80;
          const fuelLiters = ((v.fuel / 100) * tankL).toFixed(1);

          const popup = `
            <div class="map-popup vehicle-popup">
              <div class="popup-header">
                <strong>${v.id}</strong>
                <span class="popup-badge subtype-badge">${subtype}</span>
                <span class="popup-badge ${v.status.toLowerCase()}">${statusLabel}</span>
              </div>
              <div class="popup-subname">${subtypeName}</div>
              <div class="popup-body">
                <div class="popup-row"><span class="popup-label">Velocidad</span><span>${v.speed} km/h</span></div>
                <div class="popup-row"><span class="popup-label">Combustible</span>
                  <span style="display:flex;align-items:center;gap:8px;width:100%">
                    <span class="fuel-bar-mini"><span class="fuel-fill" style="width:${v.fuel}%;background:${v.fuel < 25 ? '#ef4444' : v.fuel < 50 ? '#f59e0b' : '#22c55e'}"></span></span>
                    <span style="white-space:nowrap">${v.fuel.toFixed(0)}% (${fuelLiters}L / ${tankL}L)</span>
                  </span>
                </div>
                <div class="popup-row"><span class="popup-label">Confiabilidad</span><span>${v.trust_score}/100</span></div>
              </div>
            </div>
          `;

          const isFocused = v.id === focusedVehicleId;
          const focusRing = isFocused
            ? `<div class="focus-ring"></div>`
            : "";

          const svgSize = v.status === "EN_ROUTE" ? 36 : 32;
          const svgHtml = vehicleIcon(subtype, v.status, svgSize);

          const ambulanceIcon = L.divIcon({
            html: `${focusRing}${svgHtml}`,
            className: `ambulance-marker${isFocused ? " focused" : ""}`,
            iconSize: [svgSize, svgSize],
            iconAnchor: [svgSize / 2, svgSize / 2],
          });

          if (!marker) {
            marker = L.marker(latlng, { icon: ambulanceIcon }).addTo(
              layerRef.current
            );
            marker.bindPopup(popup);
            markersRef.current.set(v.id, marker);
          } else {
            marker.setLatLng(latlng);
            marker.setPopupContent(popup);
            marker.setIcon(ambulanceIcon);
          }
        }

        // Remove old vehicle markers
        for (const [id, marker] of markersRef.current.entries()) {
          if (!seen.has(id)) {
            layerRef.current.removeLayer(marker);
            markersRef.current.delete(id);
          }
        }

        // Coverage radius — update in place instead of recreating
        if (showCoverage) {
          const activeIds = new Set();
          for (const v of vehicles) {
            if (v.status === 'IDLE') {
              activeIds.add(v.id);
              const existing = coverageCirclesRef.current.get(v.id);
              if (existing) {
                existing.setLatLng([v.lat, v.lon]);
              } else {
                const subtypeRadius = { SVA: 3500, SVB: 3000, VIR: 4500, VAMM: 2500, SAMU: 3000 };
                const subtypeColor = { SVA: '#ef4444', SVB: '#22c55e', VIR: '#3b82f6', VAMM: '#f97316', SAMU: '#a855f7' };
                const cCircle = L.circle([v.lat, v.lon], {
                  radius: subtypeRadius[v.subtype] || 3000,
                  color: subtypeColor[v.subtype] || '#22c55e',
                  fillColor: subtypeColor[v.subtype] || '#22c55e',
                  fillOpacity: 0.08, weight: 1.5, opacity: 0.35,
                  dashArray: '6, 4', interactive: false, pane: 'shadowPane',
                }).addTo(layerRef.current);
                coverageCirclesRef.current.set(v.id, cCircle);
              }
            }
          }
          // Remove circles for vehicles no longer IDLE
          for (const [id, circ] of coverageCirclesRef.current.entries()) {
            if (!activeIds.has(id)) {
              layerRef.current.removeLayer(circ);
              coverageCirclesRef.current.delete(id);
            }
          }
        } else {
          // Coverage disabled — remove all
          for (const [, circ] of coverageCirclesRef.current.entries()) {
            layerRef.current.removeLayer(circ);
          }
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

          let circle = incidentsRef.current.get(inc.id);
          const latlng = [inc.lat, inc.lon];

          const colorMap = {
            OPEN: "#ef4444",
            ASSIGNED: "#f59e0b",
            EN_ROUTE: "#3b82f6",
            RESOLVED: "#10b981",
          };
          const _color = colorMap[inc.status] || "#6b7280";

          const popup = `
            <div class="map-popup">
              <div class="popup-header incident-popup severity-${inc.severity}">
                <strong>${inc.incident_type || "GENERAL"}</strong>
                <span class="popup-badge ${inc.status.toLowerCase()}">${getStatusLabel(inc.status)}</span>
              </div>
              <div class="popup-body">
                <div class="popup-row"><span class="popup-label">Severidad</span><span class="severity-dots">${'●'.repeat(inc.severity)}${'○'.repeat(5 - inc.severity)}</span></div>
                <div class="popup-row"><span class="popup-label">Ambulancia</span><span>${inc.assigned_vehicle_id || "Sin asignar"}</span></div>
                <div class="popup-row"><span class="popup-label">Hospital</span><span>${inc.assigned_hospital_id || "Sin asignar"}</span></div>
              </div>
              <button onclick="window.selectIncidentFromMap('${inc.id}')" class="popup-action-btn">
                Ver detalles
              </button>
            </div>
          `;

          if (!circle) {
            const icon = L.divIcon({
              html: incidentIcon(inc.severity, inc.status),
              className: "incident-marker-wrap",
              iconSize: [34, 41],
              iconAnchor: [17, 41],
            });
            circle = L.marker(latlng, { icon });
            circle.bindPopup(popup);
            if (incidentClusterRef.current) incidentClusterRef.current.addLayer(circle);
            incidentsRef.current.set(inc.id, circle);
          } else {
            circle.setLatLng(latlng);
            const icon = L.divIcon({
              html: incidentIcon(inc.severity, inc.status),
              className: "incident-marker-wrap",
              iconSize: [34, 41],
              iconAnchor: [17, 41],
            });
            circle.setIcon(icon);
            circle.setPopupContent(popup);
          }

          // Draw route polylines (A→B blue, B→C green) — visible during all active phases
          try {
            const routeRaw = inc.route_data;
            const isActiveRoute = routeRaw && inc.status === "ASSIGNED";
            const phase = inc.route_phase || "TO_INCIDENT";

            if (isActiveRoute) {
              const routeObj = typeof routeRaw === "string" ? JSON.parse(routeRaw) : routeRaw;
              const coords = routeObj?.geometry || routeObj;
              const incIdx = routeObj?.incident_waypoint_idx;

              if (Array.isArray(coords) && coords.length > 1) {
                // Remove old polylines for this incident
                const oldRoute = routesRef.current.get(inc.id);
                if (oldRoute) {
                  if (Array.isArray(oldRoute)) {
                    oldRoute.forEach(p => layerRef.current.removeLayer(p));
                  } else {
                    layerRef.current.removeLayer(oldRoute);
                  }
                }

                const lines = [];
                const isToHospital = phase === "TO_HOSPITAL";
                const isAtIncident = phase === "AT_INCIDENT";

                if (incIdx && incIdx > 0 && incIdx < coords.length) {
                  // Tramo A→B: ambulancia → incidente (azul, dimmed if past)
                  const legAB = coords.slice(0, incIdx + 1);
                  const abDone = isToHospital || isAtIncident;
                  const polyAB = L.polyline(legAB, {
                    color: abDone ? "#94a3b8" : "#3b82f6",
                    weight: abDone ? 3 : 5,
                    opacity: abDone ? 0.4 : 0.9,
                    dashArray: abDone ? "6, 8" : null,
                  }).addTo(layerRef.current);
                  lines.push(polyAB);

                  // Tramo B→C: incidente → hospital (verde)
                  const legBC = coords.slice(incIdx);
                  if (legBC.length > 1) {
                    const polyBC = L.polyline(legBC, {
                      color: isToHospital ? "#10b981" : "#6ee7b7",
                      weight: isToHospital ? 5 : 3,
                      opacity: isToHospital ? 0.9 : 0.5,
                      dashArray: isToHospital ? null : "6, 8",
                    }).addTo(layerRef.current);
                    lines.push(polyBC);
                  }
                } else {
                  // Sin separación, dibujar todo en azul
                  const poly = L.polyline(coords, {
                    color: "#3b82f6",
                    weight: 5,
                    opacity: 0.9,
                  }).addTo(layerRef.current);
                  lines.push(poly);
                }

                routesRef.current.set(inc.id, lines);

                // Animated progress dot along route
                const progress = inc.route_progress ?? 0;
                if (progress > 0 && progress < 1 && coords.length > 1) {
                  const oldDot = routeDotsRef.current.get(inc.id);
                  if (oldDot) layerRef.current.removeLayer(oldDot);

                  let totalDist = 0;
                  const segDists = [];
                  for (let i = 1; i < coords.length; i++) {
                    const d = mapRef.current.distance(coords[i - 1], coords[i]);
                    segDists.push(d);
                    totalDist += d;
                  }
                  let targetDist = progress * totalDist;
                  let dotLat = coords[0][0], dotLon = coords[0][1];
                  for (let i = 0; i < segDists.length; i++) {
                    if (targetDist <= segDists[i]) {
                      const frac = segDists[i] > 0 ? targetDist / segDists[i] : 0;
                      dotLat = coords[i][0] + frac * (coords[i + 1][0] - coords[i][0]);
                      dotLon = coords[i][1] + frac * (coords[i + 1][1] - coords[i][1]);
                      break;
                    }
                    targetDist -= segDists[i];
                  }
                  const dotIcon = L.divIcon({
                    html: '<div class="route-progress-dot"></div>',
                    className: 'route-progress-dot-wrap',
                    iconSize: [16, 16],
                    iconAnchor: [8, 8],
                  });
                  const dot = L.marker([dotLat, dotLon], { icon: dotIcon, interactive: false }).addTo(layerRef.current);
                  routeDotsRef.current.set(inc.id, dot);
                }
              }
            } else if (!isActiveRoute) {
              // Remove route if incident no longer active
              const oldRoute = routesRef.current.get(inc.id);
              if (oldRoute) {
                if (Array.isArray(oldRoute)) {
                  oldRoute.forEach(p => layerRef.current.removeLayer(p));
                } else {
                  layerRef.current.removeLayer(oldRoute);
                }
                routesRef.current.delete(inc.id);
              }
              const oldDot = routeDotsRef.current.get(inc.id);
              if (oldDot) {
                layerRef.current.removeLayer(oldDot);
                routeDotsRef.current.delete(inc.id);
              }
            }
          } catch {
            // ignore invalid route_data
          }
        }

        // Remove old incident markers and routes
        for (const [id, circle] of incidentsRef.current.entries()) {
          if (!seenInc.has(id)) {
            if (incidentClusterRef.current) incidentClusterRef.current.removeLayer(circle);
            else layerRef.current.removeLayer(circle);
            incidentsRef.current.delete(id);
          }
        }
        for (const [id, polylines] of routesRef.current.entries()) {
          if (!seenInc.has(id)) {
            if (Array.isArray(polylines)) {
              polylines.forEach(p => layerRef.current.removeLayer(p));
            } else {
              layerRef.current.removeLayer(polylines);
            }
            routesRef.current.delete(id);
          }
        }
        // Clean up stale route progress dots
        for (const [id, dot] of routeDotsRef.current.entries()) {
          if (!seenInc.has(id)) {
            layerRef.current.removeLayer(dot);
            routeDotsRef.current.delete(id);
          }
        }

        // Toast notifications + emergency alerts + AI suggestions for new incidents
        for (const id of currentIds) {
          if (!prevIncidentIdsRef.current.has(id)) {
            const inc = incidentsData.find(i => i.id === id);
            if (inc && inc.status === "OPEN") {
              toast.error(
                `🚨 Nuevo incidente: ${inc.incident_type || "GENERAL"} - Severidad ${inc.severity}/5`,
                { duration: 5000, position: "top-right" }
              );

              // Emergency service alerts
              if (inc.incident_type === "BURN") {
                setEmergencyAlert({ type: "FIREFIGHTERS", incident: inc });
              } else if (inc.incident_type === "VIOLENCE") {
                setEmergencyAlert({ type: "POLICE", incident: inc });
              }

              // Auto-fetch AI suggestion for new OPEN incidents
              if (token && (user?.role === "ADMIN" || user?.role === "OPERATOR")) {
                (async () => {
                  try {
                    const res = await fetch(`${API_BASE}/api/assignments/suggest/${inc.id}`, {
                      headers: { Authorization: `Bearer ${token}` },
                    });
                    if (res.ok) {
                      const suggestion = await res.json();
                      setAiAutoSuggestions(prev => [...prev.filter(s => s.incidentId !== inc.id), { incidentId: inc.id, incident: inc, suggestion }]);
                    }
                  } catch { /* ignore */ }
                })();
              }
            }
          }
        }
        prevIncidentIdsRef.current = currentIds;

        // Update heatmap layer
        if (heatLayerRef.current) {
          map.removeLayer(heatLayerRef.current);
          heatLayerRef.current = null;
        }
        const heatPoints = incidentsData
          .filter(i => i.status !== "RESOLVED")
          .map(i => [i.lat, i.lon, i.severity || 3]);
        if (heatPoints.length > 0) {
          heatLayerRef.current = L.heatLayer(heatPoints, {
            radius: 30,
            blur: 20,
            maxZoom: 15,
            gradient: { 0.2: "blue", 0.4: "lime", 0.6: "yellow", 0.8: "orange", 1: "red" },
          });
          // Only add to map if toggle is on — we'll handle this via state
        }

        // Update gas stations
        if (data.gas_stations) {
          setGasStations(data.gas_stations);
        }
      } catch (error) {
        console.error("Error fetching data:", error);
      }
    };

    // Initial fetch
    updateData();

    // Poll every 15 seconds for stable updates (prevents flickering and excessive reloading)
    pollInterval = setInterval(updateData, 15000);

    // Make function available globally for popup buttons
    window.selectIncidentFromMap = (incidentId) => {
      const incident = incidents.find((i) => i.id === incidentId);
      if (incident) {
        setSelectedIncident(incident);
      }
    };

    return () => {
      stopped = true;
      if (pollInterval) clearInterval(pollInterval);
      try {
        map.remove();
      } catch { /* ignored */ }
    };
  }, [focusedVehicleId, fetchWeather, onMapMouseMove, token, user?.role]);

  // Toggle heatmap on/off
  useEffect(() => {
    if (!mapRef.current || !heatLayerRef.current) return;
    if (showHeatmap) {
      heatLayerRef.current.addTo(mapRef.current);
    } else {
      mapRef.current.removeLayer(heatLayerRef.current);
    }
  }, [showHeatmap, incidents]);

  // Toggle route visibility
  useEffect(() => {
    for (const [, polylines] of routesRef.current.entries()) {
      const items = Array.isArray(polylines) ? polylines : [polylines];
      items.forEach(p => {
        if (showRoutes) {
          p.setStyle({ opacity: 0.8 });
        } else {
          p.setStyle({ opacity: 0 });
        }
      });
    }
  }, [showRoutes, incidents]);

  // Toggle coverage visibility - remove old circles and update
  useEffect(() => {
    if (!layerRef.current) return;

    // Remove all old coverage circles
    for (const [, circ] of coverageCirclesRef.current.entries()) {
      layerRef.current.removeLayer(circ);
    }
    coverageCirclesRef.current.clear();

    // If coverage is enabled, recreate circles for active vehicles (exclude REFUELING/disabled)
    if (showCoverage && vehicles.length > 0) {
      for (const v of vehicles) {
        if (v.enabled && v.status !== 'REFUELING') {
          const subtypeRadius = { SVA: 3500, SVB: 3000, VIR: 4500, VAMM: 2500, SAMU: 3000 };
          const radius = subtypeRadius[v.subtype] || 3000;
          const subtypeColor = { SVA: '#ef4444', SVB: '#22c55e', VIR: '#3b82f6', VAMM: '#f97316', SAMU: '#a855f7' };
          const color = subtypeColor[v.subtype] || '#22c55e';
          const cCircle = L.circle([v.lat, v.lon], {
            radius,
            color,
            fillColor: color,
            fillOpacity: 0.08,
            weight: 1.5,
            opacity: 0.35,
            dashArray: '6, 4',
            interactive: false,
            pane: 'shadowPane',
          }).addTo(layerRef.current);
          coverageCirclesRef.current.set(v.id, cCircle);
        }
      }
    }
  }, [showCoverage, vehicles]);

  // Fetch incident timeline
  const fetchTimeline = async (incidentId) => {
    try {
      const res = await fetch(
        `${API_BASE}/api/events/incidents/${incidentId}/timeline`,
        { headers: { Authorization: `Bearer ${localStorage.getItem("token")}` } }
      );
      if (res.ok) {
        const data = await res.json();
        setIncidentTimeline(data.timeline || data);
      }
    } catch (e) {
      console.error("Error fetching timeline:", e);
    }
  };

  // Render hospitals on map
  useEffect(() => {
    if (!mapRef.current || !layerRef.current) return;

    // Clear old hospital markers
    for (const [_id, marker] of hospitalsRef.current.entries()) {
      layerRef.current.removeLayer(marker);
    }
    hospitalsRef.current.clear();

    // Add hospital markers
    for (const hospital of hospitals) {
      // Determine icon color based on occupancy
      const occupancyPct = hospital.capacity > 0 ? Math.round((hospital.current_load / hospital.capacity) * 100) : 0;
      let iconColor = "#22c55e"; // green < 60%
      if (occupancyPct >= 85) iconColor = "#ef4444"; // red >= 85%
      else if (occupancyPct >= 60) iconColor = "#f59e0b"; // orange >= 60%

      const hospIcon = L.divIcon({
        html: hospitalSvg(38, iconColor),
        className: "hospital-marker",
        iconSize: [38, 38],
        iconAnchor: [19, 19],
      });

      const marker = L.marker([hospital.lat, hospital.lon], {
        icon: hospIcon,
      }).addTo(layerRef.current);

      const availabilityPct = hospital.availability_pct ?? (hospital.capacity > 0 ? Math.round(((hospital.capacity - hospital.current_load) / hospital.capacity) * 100) : 100);
      const occupancyColorBar = occupancyPct < 60 ? '#22c55e' : occupancyPct < 85 ? '#f59e0b' : '#ef4444';

      const popup = `
        <div class="map-popup">
          <div class="popup-header hospital-popup">
            <strong>${hospital.name}</strong>
          </div>
          <div class="popup-body">
            <div class="popup-row"><span class="popup-label">Dirección</span><span>${hospital.address || "N/A"}</span></div>
            <div class="popup-row"><span class="popup-label">Ocupación</span>
              <span class="fuel-bar-mini"><span class="fuel-fill" style="width:${occupancyPct}%;background:${occupancyColorBar}"></span></span>
              <span>${hospital.current_load}/${hospital.capacity} (${occupancyPct}%)</span>
            </div>
            <div class="popup-row"><span class="popup-label">Disponibilidad</span><span style="color:${availabilityPct > 40 ? '#22c55e' : availabilityPct > 15 ? '#f59e0b' : '#ef4444'}">${availabilityPct}%</span></div>
            <div class="popup-row"><span class="popup-label">Nivel UCE</span><span>${'★'.repeat(hospital.emergency_level || 1)}${'☆'.repeat(3 - (hospital.emergency_level || 1))}</span></div>
            <div class="popup-row"><span class="popup-label">Especialidades</span><span>${(hospital.specialties || []).join(", ") || "General"}</span></div>
          </div>
        </div>
      `;

      marker.bindPopup(popup);
      hospitalsRef.current.set(hospital.id, marker);
    }
  }, [hospitals]);

  // Render gas stations on map
  useEffect(() => {
    if (!mapRef.current || !layerRef.current) return;

    // Clear old gas station markers
    for (const [_id, marker] of gasStationsRef.current.entries()) {
      layerRef.current.removeLayer(marker);
    }
    gasStationsRef.current.clear();

    if (!showGasStations) return;

    for (const gs of gasStations) {
      const gsIcon = L.divIcon({
        html: gasStationIcon(34),
        className: "gas-station-marker",
        iconSize: [34, 34],
        iconAnchor: [17, 17],
      });

      const marker = L.marker([gs.lat, gs.lon], { icon: gsIcon }).addTo(layerRef.current);

      const popup = `
        <div class="map-popup">
          <div class="popup-header gas-popup">
            <strong>${gs.name}</strong>
            ${gs.open_24h ? '<span class="popup-badge open24">24h</span>' : ''}
          </div>
          <div class="popup-body">
            <div class="popup-row"><span class="popup-label">Marca</span><span>${gs.brand || "Genérica"}</span></div>
            <div class="popup-row"><span class="popup-label">Precio</span><span class="price-tag">${gs.price_per_liter.toFixed(2)} €/L</span></div>
            <div class="popup-row"><span class="popup-label">Combustibles</span><span>${(gs.fuel_types || []).join(", ")}</span></div>
          </div>
        </div>
      `;

      marker.bindPopup(popup);
      gasStationsRef.current.set(gs.id, marker);
    }
  }, [gasStations, showGasStations]);

  // Render DEA/AED locations on map
  useEffect(() => {
    if (!mapRef.current || !layerRef.current) return;
    for (const [, m] of deaMarkersRef.current) layerRef.current.removeLayer(m);
    deaMarkersRef.current.clear();
    if (!showDEA) return;
    for (const dea of deaLocations) {
      const icon = L.divIcon({
        html: `<div style="background:#22c55e;border-radius:50%;width:28px;height:28px;display:flex;align-items:center;justify-content:center;border:2px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,.3);font-size:16px;">💚</div>`,
        className: "dea-marker", iconSize: [28, 28], iconAnchor: [14, 14],
      });
      const m = L.marker([dea.lat, dea.lon], { icon }).addTo(layerRef.current);
      m.bindPopup(`<div class="map-popup"><div class="popup-header" style="background:#22c55e;color:#fff"><strong>DEA: ${dea.name}</strong></div><div class="popup-body"><div class="popup-row"><span class="popup-label">Tipo</span><span>${dea.location_type || "Público"}</span></div><div class="popup-row"><span class="popup-label">Horario</span><span>${dea.access_hours || "24h"}</span></div></div></div>`);
      deaMarkersRef.current.set(dea.id, m);
    }
  }, [deaLocations, showDEA]);

  // Render GIS layers on map
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
      const icon = L.divIcon({
        html: `<div style="background:${color};border-radius:50%;width:26px;height:26px;display:flex;align-items:center;justify-content:center;border:2px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,.3);font-size:14px;">${emoji}</div>`,
        className: "gis-marker", iconSize: [26, 26], iconAnchor: [13, 13],
      });
      const m = L.marker([poi.lat, poi.lon], { icon }).addTo(layerRef.current);
      m.bindPopup(`<div class="map-popup"><div class="popup-header" style="background:${color};color:#fff"><strong>${poi.name}</strong></div><div class="popup-body"><div class="popup-row"><span class="popup-label">Tipo</span><span>${poi.layer_type}</span></div><div class="popup-row"><span class="popup-label">Riesgo</span><span>${poi.risk_level || "NORMAL"}</span></div></div></div>`);
      gisMarkersRef.current.set(poi.id, m);
    }
  }, [gisLayers, showGIS]);

  // Render agency resources on map
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
      const icon = L.divIcon({
        html: `<div style="background:${color};border-radius:6px;padding:2px 6px;display:flex;align-items:center;gap:4px;border:2px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,.3);font-size:12px;color:#fff;white-space:nowrap;">${emoji} ${ag.unit_name}</div>`,
        className: "agency-marker", iconSize: [80, 28], iconAnchor: [40, 14],
      });
      const m = L.marker([ag.lat, ag.lon], { icon }).addTo(layerRef.current);
      m.bindPopup(`<div class="map-popup"><div class="popup-header" style="background:${color};color:#fff"><strong>${ag.unit_name}</strong></div><div class="popup-body"><div class="popup-row"><span class="popup-label">Agencia</span><span>${ag.agency}</span></div><div class="popup-row"><span class="popup-label">Tipo</span><span>${ag.unit_type}</span></div><div class="popup-row"><span class="popup-label">Estado</span><span>${ag.status}</span></div><div class="popup-row"><span class="popup-label">Radio</span><span>${ag.contact_radio || "N/A"}</span></div></div></div>`);
      agencyMarkersRef.current.set(ag.id, m);
    }
  }, [agencyResources, showAgencies]);

  // Render SSM coverage zones on map
  useEffect(() => {
    if (!mapRef.current || !layerRef.current) return;
    for (const [, c] of ssmCirclesRef.current) layerRef.current.removeLayer(c);
    ssmCirclesRef.current.clear();
    if (!showSSM) return;
    const zones = ssmZones?.zones || ssmZones || [];
    for (const zone of zones) {
      const lat = zone.lat || zone.center_lat;
      const lon = zone.lon || zone.center_lon;
      if (!lat || !lon) continue;
      const coverage = zone.coverage_pct ?? (zone.coverage_status === "OK" ? 100 : 40);
      const color = coverage >= 80 || zone.coverage_status === "OK" ? "#22c55e" : coverage >= 50 ? "#f59e0b" : "#ef4444";
      const circle = L.circle([lat, lon], {
        radius: 1500, color, fillColor: color, fillOpacity: 0.15, weight: 2,
      }).addTo(layerRef.current);
      const name = zone.name || zone.zone_name || zone.zone_id;
      circle.bindPopup(`<div class="map-popup"><div class="popup-header" style="background:${color};color:#fff"><strong>${name}</strong></div><div class="popup-body"><div class="popup-row"><span class="popup-label">Estado</span><span>${zone.coverage_status || "N/A"}</span></div><div class="popup-row"><span class="popup-label">Demanda</span><span>${zone.demand_weight}</span></div><div class="popup-row"><span class="popup-label">Unidades rec.</span><span>${zone.recommended_units}</span></div><div class="popup-row"><span class="popup-label">Desplegadas</span><span>${zone.current_units ?? 0}</span></div></div></div>`);
      ssmCirclesRef.current.set(name, circle);
    }
  }, [ssmZones, showSSM]);

  // Risk zones — each active incident gets a risk radius circle
  useEffect(() => {
    if (!mapRef.current || !layerRef.current) return;
    for (const r of riskZonesRef.current) layerRef.current.removeLayer(r);
    riskZonesRef.current = [];
    if (!showRiskZones || incidents.length === 0) return;

    const activeInc = incidents.filter(i => i.status !== 'RESOLVED' && i.status !== 'CLOSED');
    if (activeInc.length === 0) return;

    for (const inc of activeInc) {
      const sev = inc.severity || 1;
      // Radius: higher severity = larger zone (300m to 800m)
      const radius = 300 + sev * 100;
      const color = sev >= 4 ? '#dc2626' : sev >= 3 ? '#f59e0b' : sev >= 2 ? '#f97316' : '#3b82f6';
      const circle = L.circle([inc.lat, inc.lon], {
        radius,
        color,
        fillColor: color,
        fillOpacity: 0.10 + sev * 0.04,
        weight: 2,
        opacity: 0.5 + sev * 0.08,
        dashArray: '6, 4',
      }).addTo(layerRef.current);
      circle.bindPopup(`<div class="map-popup"><div class="popup-header" style="background:${color};color:#fff"><strong>Zona de Riesgo</strong></div><div class="popup-body"><div class="popup-row"><span class="popup-label">Incidente</span><span>${inc.incident_type || inc.id}</span></div><div class="popup-row"><span class="popup-label">Severidad</span><span>${sev}/5</span></div><div class="popup-row"><span class="popup-label">Radio afectado</span><span>${radius}m</span></div></div></div>`);
      riskZonesRef.current.push(circle);
    }
  }, [incidents, showRiskZones]);

  // Proximity alerts — detect IDLE vehicles near unassigned incidents
  const proximityAlertedRef = useRef(new Set());
  useEffect(() => {
    if (vehicles.length === 0 || incidents.length === 0) return;
    const openInc = incidents.filter(i => i.status === 'OPEN' && !i.assigned_vehicle_id);
    const idleVeh = vehicles.filter(v => v.status === 'IDLE');
    if (openInc.length === 0 || idleVeh.length === 0) return;

    const PROXIMITY_KM = 2.5;
    const toRad = (d) => d * Math.PI / 180;
    const haversine = (lat1, lon1, lat2, lon2) => {
      const R = 6371;
      const dLat = toRad(lat2 - lat1);
      const dLon = toRad(lon2 - lon1);
      const a = Math.sin(dLat / 2) ** 2 + Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2;
      return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    };

    for (const inc of openInc) {
      for (const veh of idleVeh) {
        const dist = haversine(inc.lat, inc.lon, veh.lat, veh.lon);
        if (dist <= PROXIMITY_KM) {
          const key = `${inc.id}_${veh.id}`;
          if (!proximityAlertedRef.current.has(key)) {
            proximityAlertedRef.current.add(key);
            toast(
              `📍 ${veh.id} está a ${dist.toFixed(1)}km del incidente ${inc.incident_type || "GENERAL"} (sev ${inc.severity})`,
              { icon: "🔔", duration: 6000, position: "top-right", style: { background: "#1e293b", color: "#f1f5f9", border: "1px solid #f59e0b40" } }
            );
          }
        }
      }
    }
    // Clean alerts for resolved incidents
    for (const key of proximityAlertedRef.current) {
      const incId = key.split("_")[0];
      if (!incidents.find(i => i.id === incId && i.status === 'OPEN')) {
        proximityAlertedRef.current.delete(key);
      }
    }
  }, [vehicles, incidents]);

  // Security events polling — show toast for HIGH/CRITICAL threats
  useEffect(() => {
    const checkSecurityEvents = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/security/events?limit=5&severity=HIGH`);
        if (!res.ok) return;
        const events = await res.json();
        if (Array.isArray(events) && events.length > 0) {
          const latest = events[0];
          const eventKey = latest.id || latest.timestamp || JSON.stringify(latest).slice(0, 50);
          if (lastSecEventIdRef.current && eventKey !== lastSecEventIdRef.current) {
            const sev = latest.severity || "HIGH";
            const icon = sev === "CRITICAL" ? "🔴" : sev === "HIGH" ? "🟠" : "🟡";
            toast(
              `${icon} Security: ${latest.event_type || latest.type || "Threat detected"} — ${latest.details || latest.description || sev}`,
              {
                duration: 8000,
                position: "top-right",
                style: {
                  background: sev === "CRITICAL" ? "#7f1d1d" : "#78350f",
                  color: "#fff",
                  border: `1px solid ${sev === "CRITICAL" ? "#dc2626" : "#f59e0b"}`,
                  fontWeight: 500,
                },
              }
            );
          }
          lastSecEventIdRef.current = eventKey;
        }
      } catch { /* ignore */ }
    };
    checkSecurityEvents();
    const interval = setInterval(checkSecurityEvents, 15000);
    return () => clearInterval(interval);
  }, []);

  const getIncidentTypeLabel = (type) => {
    const labels = {
      CARDIO: { icon: Heart, text: "Cardíaco" },
      RESPIRATORY: { icon: Wind, text: "Respiratorio" },
      NEUROLOGICAL: { icon: Brain, text: "Neurológico" },
      TRAUMA: { icon: Zap, text: "Trauma" },
      BURN: { icon: Flame, text: "Quemadura" },
      POISONING: { icon: Skull, text: "Intoxicación" },
      OBSTETRIC: { icon: HeartPulse, text: "Obstétrico" },
      PEDIATRIC: { icon: Baby, text: "Pediátrico" },
      PSYCHIATRIC: { icon: Smile, text: "Psiquiátrico" },
      VIOLENCE: { icon: Shield, text: "Violencia" },
      ALLERGIC: { icon: Sparkles, text: "Alérgico" },
      METABOLIC: { icon: Thermometer, text: "Metabólico" },
      INTOXICATION: { icon: Pill, text: "Intoxicación (drogas)" },
      DROWNING: { icon: Waves, text: "Ahogamiento" },
      FALL: { icon: PersonStanding, text: "Caída" },
      GENERAL: { icon: AlertTriangle, text: "General" },
    };
    const entry = labels[type];
    if (!entry) return type;
    const Icon = entry.icon;
    return <><Icon size={14} /> {entry.text}</>;
  };

  /** Dismiss an AI auto-suggestion */
  const dismissAiAutoSuggestion = (incidentId) => {
    setAiAutoSuggestions(prev => prev.filter(s => s.incidentId !== incidentId));
  };

  /** Auto-generate control */
  const toggleAutoGen = async () => {
    try {
      if (autoGenRunning) {
        const res = await fetch(`${API_BASE}/simulation/auto-generate/stop`, { method: "POST" });
        if (res.ok) { setAutoGenRunning(false); setLastGenIncident(null); toast.success("⏹ Generación automática detenida"); }
      } else {
        const res = await fetch(`${API_BASE}/simulation/auto-generate/start?interval=${autoGenInterval}`, { method: "POST" });
        if (res.ok) { setAutoGenRunning(true); setAutoGenCount(0); prevAutoGenCountRef.current = 0; toast.success(`▶ Generando incidentes cada ~${autoGenInterval}s`); }
      }
    } catch { toast.error("Error al controlar auto-generación"); }
  };

  /** Reset system */
  const resetSystem = async () => {
    if (!confirm("¿Reiniciar TODO el sistema? Se borrarán incidentes, auditorías y se reseteará la flota.")) return;
    setResetting(true);
    try {
      const res = await fetch(`${API_BASE}/simulation/reset`, { method: "POST" });
      if (res.ok) {
        const data = await res.json();
        toast.success(`🔄 Sistema reiniciado: ${data.deleted_incidents} incidentes borrados`);
        setAutoGenRunning(false);
        setAutoGenCount(0);
        setLastGenIncident(null);
        setAiAutoSuggestions([]);
        setSelectedIncident(null);
        setIncidentTimeline(null);
        setAiSuggestion(null);
        prevIncidentIdsRef.current = new Set();
      }
    } catch { toast.error("Error al reiniciar sistema"); }
    setResetting(false);
  };

  /** Poll auto-gen status + detect new auto-generated incidents */
  useEffect(() => {
    const poll = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/simulation/auto-generate/status`);
        if (res.ok) {
          const d = await res.json();
          setAutoGenRunning(d.running);
          // Detect count increase → a new incident was just generated
          if (d.total_generated > prevAutoGenCountRef.current && d.running) {
            // Fetch latest open incident to show in the ticker
            try {
              const liveRes = await fetch(`${API_BASE}/api/live`);
              if (liveRes.ok) {
                const live = await liveRes.json();
                const openIncs = (live.incidents || []).filter(i => i.status === "OPEN");
                if (openIncs.length > 0) {
                  const newest = openIncs[openIncs.length - 1];
                  setLastGenIncident(newest);
                }
              }
            } catch { /* ignored */ }
          }
          prevAutoGenCountRef.current = d.total_generated;
          setAutoGenCount(d.total_generated);
        }
      } catch { /* ignored */ }
    }, 8000);  // OPTIMIZED: increased from 3000ms to reduce polling
    return () => clearInterval(poll);
  }, []);

  const openIncidents = incidents.filter((i) => i.status === "OPEN");
  const assignedIncidents = incidents.filter((i) =>
    ["ASSIGNED", "EN_ROUTE"].includes(i.status)
  );

  const dashboardRef = useRef(null);
  const [exporting, setExporting] = useState(false);
  const [speedMultiplier, setSpeedMultiplier] = useState(1);

  // ── Digital Twin telemetry state ──
  const [twinPanelOpen, setTwinPanelOpen] = useState(false);
  const [twinTelemetry, setTwinTelemetry] = useState(null);
  const [twinLoading, setTwinLoading] = useState(false);
  const [fleetHealth, setFleetHealth] = useState(null);
  const [whatIfResult, setWhatIfResult] = useState(null);
  const [whatIfLoading, setWhatIfLoading] = useState(false);
  const exportToPDF = async () => {
    if (!dashboardRef.current || exporting) return;
    setExporting(true);
    try {
      const canvas = await html2canvas(dashboardRef.current, {
        scale: 2,
        useCORS: true,
        backgroundColor: "#0a0e14",
        logging: false,
      });
      const link = document.createElement("a");
      const ts = new Date().toISOString().slice(0, 19).replace(/[T:]/g, "-");
      link.download = `KAIROS_Dashboard_${ts}.png`;
      link.href = canvas.toDataURL("image/png");
      link.click();
      toast.success("📸 Dashboard exportado correctamente", { duration: 3000 });
    } catch (e) {
      toast.error("Error al exportar dashboard");
      console.error("Export error:", e);
    } finally {
      setExporting(false);
    }
  };

  // ── Digital Twin API calls ──
  const fetchTwinTelemetry = async (vehicleId) => {
    setTwinLoading(true);
    try {
      const res = await fetch(`${API_BASE}/digital-twin/telemetry/${vehicleId}`, {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
      });
      if (res.ok) setTwinTelemetry(await res.json());
    } catch (e) { console.error("Twin telemetry error:", e); }
    finally { setTwinLoading(false); }
  };

  const fetchFleetHealth = async () => {
    try {
      const res = await fetch(`${API_BASE}/digital-twin/fleet-health`, {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
      });
      if (res.ok) setFleetHealth(await res.json());
    } catch (e) { console.error("Fleet health error:", e); }
  };

  const runWhatIf = async (scenario, vehicleId = null, params = {}) => {
    setWhatIfLoading(true);
    try {
      const res = await fetch(`${API_BASE}/digital-twin/what-if`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify({ scenario, vehicle_id: vehicleId, parameters: params }),
      });
      if (res.ok) setWhatIfResult(await res.json());
    } catch (e) { console.error("What-if error:", e); }
    finally { setWhatIfLoading(false); }
  };

  // Fetch twin telemetry when a vehicle is focused
  useEffect(() => {
    if (focusedVehicleId && twinPanelOpen) {
      fetchTwinTelemetry(focusedVehicleId);
      const interval = setInterval(() => fetchTwinTelemetry(focusedVehicleId), 5000);  // OPTIMIZED: from 2000ms
      return () => clearInterval(interval);
    }
  }, [focusedVehicleId, twinPanelOpen]);

  // Fetch fleet health when twin panel opens
  useEffect(() => {
    if (twinPanelOpen) {
      fetchFleetHealth();
      const interval = setInterval(fetchFleetHealth, 10000);  // OPTIMIZED: from 5s
      return () => clearInterval(interval);
    }
  }, [twinPanelOpen]);

  return (
    <div className="dashboard-container" ref={dashboardRef}>
      <Toaster />
      <div className="map-area">
        <div id="map" className="dashboard-map" />
      
        {/* Map overlay controls */}
        <div className="map-controls">
          <button
            className={`map-control-btn ${showHeatmap ? "active" : ""}`}
            onClick={() => setShowHeatmap((v) => !v)}
            title="Mapa de calor"
          >
            <Flame size={16} /> Heatmap
          </button>
          <button
            className={`map-control-btn ${showRoutes ? "active" : ""}`}
            onClick={() => setShowRoutes((v) => !v)}
            title="Mostrar rutas"
          >
            <Route size={16} /> Rutas
          </button>
          <button
            className={`map-control-btn ${showGasStations ? "active" : ""}`}
            onClick={() => setShowGasStations((v) => !v)}
            title="Mostrar gasolineras"
          >
            <Fuel size={16} /> Gasolineras
          </button>
          <button
            className={`map-control-btn ${showDEA ? "active" : ""}`}
            onClick={() => setShowDEA((v) => !v)}
            title="Desfibriladores (DEA)"
          >
            <Heart size={16} /> DEA
          </button>
          <button
            className={`map-control-btn ${showGIS ? "active" : ""}`}
            onClick={() => setShowGIS((v) => !v)}
            title="Capas GIS (colegios, residencias, HAZMAT)"
          >
            <MapPin size={16} /> GIS
          </button>
          <button
            className={`map-control-btn ${showAgencies ? "active" : ""}`}
            onClick={() => setShowAgencies((v) => !v)}
            title="Recursos multi-agencia"
          >
            <Shield size={16} /> Agencias
          </button>
          <button
            className={`map-control-btn ${showSSM ? "active" : ""}`}
            onClick={() => setShowSSM((v) => !v)}
            title="Zonas SSM cobertura"
          >
            <Activity size={16} /> SSM
          </button>
          <button
            className={`map-control-btn ${showCoverage ? "active" : ""}`}
            onClick={() => setShowCoverage((v) => !v)}
            title="Radio de cobertura ambulancias"
          >
            <Waves size={16} /> Cobertura
          </button>
          <button
            className={`map-control-btn ${showRiskZones ? "active" : ""}`}
            onClick={() => setShowRiskZones((v) => !v)}
            title="Zonas de riesgo por densidad de incidentes"
          >
            <AlertTriangle size={16} /> Riesgo
          </button>
        </div>

        {/* Weather widget — bottom-right of map */}
        {weather && (
          <div className="weather-widget" title={`${weather.detail_desc || weather.condition}\nViento: ${weather.wind_speed_kmh ?? "--"} km/h (ráfagas ${weather.wind_gusts_kmh ?? "--"} km/h)\nHumedad: ${weather.humidity_pct ?? "--"}%\nSensación térmica: ${weather.apparent_temperature_c ?? "--"}°C\nNubosidad: ${weather.cloud_cover_pct ?? "--"}%\nPrecipitación: ${weather.precipitation_mm ?? 0} mm\nWMO: ${weather.wmo_code}`}>
            <span className="weather-icon">{weather.icon || "☁️"}</span>
            <span className="weather-temp">{weather.temperature_c ?? "--"}°C</span>
            <span className="weather-details">
              <Wind size={11} /> {weather.wind_speed_kmh ?? "--"} km/h
              <Droplets size={11} style={{marginLeft: 6}} /> {weather.humidity_pct ?? "--"}%
            </span>
            <span className="weather-cond">{weather.description || weather.condition}</span>
            {weather.alert_level && weather.alert_level !== "GREEN" && (
              <span className={`weather-alert weather-alert-${weather.alert_level?.toLowerCase()}`}>⚠ {weather.alert_level}</span>
            )}
          </div>
        )}

        {/* Map Legend — top-right of map */}
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

        {/* Simulation controls */}
        <div className={`sim-controls ${autoGenRunning ? "sim-active" : ""}`}>
          <div className="sim-controls-header">
            <Sparkles size={16} className={autoGenRunning ? "sim-sparkle-spin" : ""} /> Simulación
            {autoGenRunning && <span className="sim-live-badge">EN VIVO</span>}
          </div>
          <div className="sim-controls-row">
            <button
              className={`sim-btn ${autoGenRunning ? "sim-btn-stop" : "sim-btn-start"}`}
              onClick={toggleAutoGen}
              title={autoGenRunning ? "Detener generación" : "Iniciar generación"}
            >
              {autoGenRunning ? <><Square size={14} /> Parar</> : <><Play size={14} /> Auto-generar</>}
            </button>
            <select
              className="sim-interval-select"
              value={autoGenInterval}
              onChange={e => setAutoGenInterval(Number(e.target.value))}
              disabled={autoGenRunning}
            >
              <option value={10}>10s</option>
              <option value={20}>20s</option>
              <option value={30}>30s</option>
              <option value={45}>45s</option>
              <option value={60}>1 min</option>
              <option value={120}>2 min</option>
            </select>
            <button
              className="sim-btn sim-btn-reset"
              onClick={resetSystem}
              disabled={resetting}
            >
              <RotateCcw size={14} className={resetting ? "sim-spin" : ""} /> {resetting ? "Limpiando..." : "Reset"}
            </button>
          </div>
          <div className="sim-controls-row sim-speed-row">
            <Gauge size={14} />
            <span className="sim-speed-label">Velocidad:</span>
            <select
              className="sim-interval-select"
              value={speedMultiplier}
              onChange={e => {
                const v = Number(e.target.value);
                setSpeedMultiplier(v);
                fetch(`${API_BASE}/simulation/speed?multiplier=${v}`, { method: "POST" });
              }}
            >
              <option value={1}>1x (Normal)</option>
              <option value={2}>2x Rápido</option>
              <option value={5}>5x Muy rápido</option>
              <option value={10}>10x Turbo</option>
              <option value={20}>20x Ultra</option>
            </select>
            <button className="export-btn" onClick={exportToPDF} disabled={exporting} title="Exportar dashboard a imagen">
              <Download size={15} /> {exporting ? "..." : "Exportar"}
            </button>
          </div>
          {autoGenRunning && (
            <div className="sim-status">
              <Activity size={12} className="sim-pulse" /> Generando... <strong>{autoGenCount}</strong> creados
            </div>
          )}
          {autoGenRunning && lastGenIncident && (
            <div className="sim-last-incident" key={lastGenIncident.id}>
              <div className="sim-last-header">
                <Siren size={12} /> Último generado
              </div>
              <div className="sim-last-body">
                <span className="sim-last-id">{lastGenIncident.id}</span>
                <span className="sim-last-type">{getIncidentTypeLabel(lastGenIncident.incident_type)}</span>
                <span className="sim-last-sev">Sev {lastGenIncident.severity}/5</span>
              </div>
              {lastGenIncident.address && <div className="sim-last-addr"><MapPin size={10} /> {lastGenIncident.address}</div>}
            </div>
          )}
          {!autoGenRunning && autoGenCount > 0 && (
            <div className="sim-status sim-status-stopped">
              <Square size={12} /> Detenida — {autoGenCount} incidentes generados
            </div>
          )}
        </div>

        <div className="metrics-cards">
          <div className="metric-card">
            <div className="metric-icon"><Ambulance size={24} className="icon-3d" /></div>
            <div className="metric-value">{fleetMetrics.active_vehicles}</div>
            <div className="metric-label">Ambulancias Activas</div>
          </div>
          <div className="metric-card">
            <div className="metric-icon"><Fuel size={24} className="icon-3d" /></div>
            <div className="metric-value">{fleetMetrics.avg_fuel.toFixed(1)}%</div>
            <div className="metric-label">Combustible Promedio</div>
          </div>
          <div className="metric-card">
            <div className="metric-icon"><Flame size={24} className="icon-3d" /></div>
            <div className="metric-value">{openIncidents.length}</div>
            <div className="metric-label">Incidentes Abiertos</div>
          </div>
          <div className="metric-card">
            <div className="metric-icon"><Hospital size={24} className="icon-3d" /></div>
            <div className="metric-value">{hospitals.length}</div>
            <div className="metric-label">Hospitales Disponibles</div>
          </div>
          <div className="metric-card">
            <div className="metric-icon"><Fuel size={24} className="icon-3d" /></div>
            <div className="metric-value">{gasStations.length}</div>
            <div className="metric-label">Gasolineras</div>
          </div>
          <div className="metric-card">
            <div className="metric-icon"><HeartPulse size={24} className="icon-3d" /></div>
            <div className="metric-value">{deaLocations.length}</div>
            <div className="metric-label">DEA Disponibles</div>
          </div>
        </div>

        <div className="incidents-section">
          <h3><AlertTriangle size={20} className="icon-3d" /> Incidentes Pendientes</h3>
          <div className="incidents-list">
            {openIncidents.map((inc) => (
              <div
                key={inc.id}
                className="incident-item"
                onClick={() => setSelectedIncident(inc)}
              >
                <div className="incident-header">
                  <span className="incident-type">{getIncidentTypeLabel(inc.incident_type)}</span>
                  <span className={`severity-badge severity-${inc.severity}`}>
                    {inc.severity}/5
                  </span>
                </div>
                <div className="incident-id">{inc.id}</div>
                <div className="incident-location">{inc.address || `${(inc.lat || 0).toFixed(4)}, ${(inc.lon || 0).toFixed(4)}`}</div>
                <button className="focus-btn" onClick={(e) => { e.stopPropagation(); focusIncident(inc.id); }} title="Focalizar en mapa"><MapPin size={14} /></button>
              </div>
            ))}
            {openIncidents.length === 0 && (
              <div className="empty-state"><CheckCircle size={14} /> No hay incidentes pendientes</div>
            )}
          </div>
        </div>

        <div className="incidents-section">
          <h3><RefreshCw size={20} className="icon-3d" /> En Progreso</h3>
          <div className="incidents-list">
            {assignedIncidents.map((inc) => (
              <div
                key={inc.id}
                className="incident-item assigned"
                onClick={() => setSelectedIncident(inc)}
              >
                <div className="incident-header">
                  <span className="incident-type">{getIncidentTypeLabel(inc.incident_type)}</span>
                  <span className="status-badge">{inc.status}</span>
                </div>
                <div className="incident-id">{inc.id}</div>
                <div className="incident-assignment">
                  <Ambulance size={14} /> {inc.assigned_vehicle_id} → <Hospital size={14} /> {inc.assigned_hospital_id}
                </div>
                {/* Route progress */}
                <div className="route-progress-section">
                  <span className="route-phase-label">
                    {inc.route_phase === "TO_HOSPITAL" ? "🏥 Traslado a hospital"
                      : inc.route_phase === "COMPLETED" ? "✅ Completado"
                      : "🚑 Camino al incidente"}
                  </span>
                  <div className="route-progress-bar">
                    <div
                      className={`route-progress-fill ${inc.route_phase === "TO_HOSPITAL" ? "phase-hospital" : "phase-incident"}`}
                      style={{ width: `${Math.min((inc.route_progress || 0) * 100, 100)}%` }}
                    />
                  </div>
                  <span className="route-progress-pct">{Math.round((inc.route_progress || 0) * 100)}%</span>
                </div>
                <div className="incident-focus-btns">
                  <button className="focus-btn" onClick={(e) => { e.stopPropagation(); focusIncident(inc.id); }} title="Focalizar incidente"><MapPin size={14} /></button>
                  {inc.assigned_vehicle_id && <button className="focus-btn" onClick={(e) => { e.stopPropagation(); focusVehicle(inc.assigned_vehicle_id); }} title="Seguir ambulancia"><Ambulance size={14} /></button>}
                </div>
              </div>
            ))}
            {assignedIncidents.length === 0 && (
              <div className="empty-state">Sin incidentes en progreso</div>
            )}
          </div>
        </div>

        {/* Vehicle fleet list */}
        <div className="incidents-section">
          <h3><Ambulance size={20} className="icon-3d" /> Flota de Ambulancias</h3>
          {/* Subtype filter chips */}
          <div className="subtype-filter-bar">
            <Filter size={14} />
            {["ALL", "SVB", "SVA", "VIR", "VAMM", "SAMU"].map(st => (
              <button
                key={st}
                className={`filter-chip ${subtypeFilter === st ? "active" : ""}`}
                onClick={() => setSubtypeFilter(st)}
                style={subtypeFilter === st && st !== "ALL" ? {background: {SVB:"#22c55e",SVA:"#ef4444",VIR:"#3b82f6",VAMM:"#f97316",SAMU:"#a855f7"}[st], color:"#fff"} : {}}
              >
                {st === "ALL" ? "Todos" : st}
              </button>
            ))}
          </div>
          {/* Status filter chips */}
          <div className="status-filter-bar">
            <Siren size={14} />
            {["ALL", "IDLE", "EN_ROUTE", "REFUELING"].map(st => (
              <button
                key={st}
                className={`filter-chip ${statusFilter === st ? "active" : ""}`}
                onClick={() => setStatusFilter(st)}
                style={statusFilter === st && st !== "ALL" ? {background: {IDLE:"#22c55e",EN_ROUTE:"#ef4444",REFUELING:"#3b82f6"}[st], color:"#fff"} : {}}
              >
                {st === "ALL" ? "Todos" : st === "IDLE" ? "Disponible" : st === "EN_ROUTE" ? "En ruta" : "Repostando"}
              </button>
            ))}
          </div>
          <div className="incidents-list">
            {vehicles.filter(v => v.enabled && (subtypeFilter === "ALL" || (v.subtype || "SVB") === subtypeFilter) && (statusFilter === "ALL" || v.status === statusFilter)).map((v) => {
              const sub = v.subtype || "SVB";
              const SCOLORS = { SVB: "#22c55e", SVA: "#ef4444", VIR: "#3b82f6", VAMM: "#f97316", SAMU: "#a855f7" };
              const sc = SCOLORS[sub] || "#6b7280";
              return (
              <div
                key={v.id}
                className={`incident-item vehicle-item ${focusedVehicleId === v.id ? "focused" : ""} ${v.status === "EN_ROUTE" ? "assigned" : v.status === "REFUELING" ? "refueling" : ""}`}
                onClick={() => focusVehicle(v.id)}
              >
                <div className="incident-header">
                  <span className="incident-type">
                    {v.status === "EN_ROUTE" ? <Ambulance size={14} color={sc} /> : v.status === "REFUELING" ? <Droplets size={14} color="#3b82f6" /> : sub === "VIR" ? <Zap size={14} color={sc} /> : sub === "SAMU" ? <Heart size={14} color={sc} /> : <Ambulance size={14} color={sc} />} {v.id}
                  </span>
                  <span className="subtype-tag" style={{background: sc, color: '#fff'}}>{sub}</span>
                  <span className={`status-badge ${v.status === "EN_ROUTE" ? "en-route" : v.status === "IDLE" ? "idle" : v.status === "REFUELING" ? "refueling" : ""}`}>
                    {v.status === "REFUELING" ? "Repostando" : v.status === "EN_ROUTE" ? "En ruta" : v.status === "IDLE" ? "Disponible" : v.status}
                  </span>
                </div>
                <div className="vehicle-meta">
                  <span><Fuel size={14} /> {v.fuel?.toFixed(0)}% ({((v.fuel / 100) * (v.tank_capacity || 80)).toFixed(0)}L)</span>
                  <span><Zap size={14} /> {v.speed} km/h</span>
                  <span><Star size={14} /> {v.trust_score}</span>
                </div>
              </div>
              );
            })}
            {vehicles.filter(v => v.enabled && (subtypeFilter === "ALL" || (v.subtype || "SVB") === subtypeFilter) && (statusFilter === "ALL" || v.status === statusFilter)).length === 0 && (
              <div className="empty-state">Sin ambulancias {subtypeFilter !== "ALL" ? `tipo ${subtypeFilter}` : ""}{statusFilter !== "ALL" ? ` en estado ${statusFilter}` : "activas"}</div>
            )}
          </div>
        </div>

        {/* Resumen Operativo */}
        <div className="info-section ops-summary">
          <strong><BarChart3 size={16} className="icon-3d" /> Resumen Operativo</strong>
          <div className="ops-grid">
            {(() => {
              const enabled = vehicles.filter(v => v.enabled);
              const idle = enabled.filter(v => v.status === "IDLE").length;
              const enRoute = enabled.filter(v => v.status === "EN_ROUTE").length;
              const refueling = enabled.filter(v => v.status === "REFUELING").length;
              const total = enabled.length || 1;
              const readiness = Math.round((idle / total) * 100);
              const subtypeCounts = {};
              enabled.forEach(v => { const s = v.subtype || "SVB"; subtypeCounts[s] = (subtypeCounts[s] || 0) + 1; });
              const lowFuel = enabled.filter(v => (v.fuel || 100) < 30).length;
              const avgSpeed = enabled.length ? (enabled.reduce((s, v) => s + (v.speed || 0), 0) / enabled.length).toFixed(0) : 0;
              const avgTrust = enabled.length ? (enabled.reduce((s, v) => s + (v.trust_score || 0), 0) / enabled.length).toFixed(1) : 0;
              const SCOLORS = { SVB: "#22c55e", SVA: "#ef4444", VIR: "#3b82f6", VAMM: "#f97316", SAMU: "#a855f7" };

              // Response time stats by severity
              const nowMs = Date.now();
              const allActive = [...openIncidents, ...assignedIncidents];
              const sevBuckets = { 1: [], 2: [], 3: [], 4: [], 5: [] };
              allActive.forEach(inc => {
                const sev = inc.severity || 1;
                const created = inc.created_at ? new Date(inc.created_at).getTime() : nowMs;
                const elapsed = (nowMs - created) / 60000; // minutes
                if (sevBuckets[sev]) sevBuckets[sev].push(elapsed);
              });
              // Also include resolved ones (today)
              const todayStart = new Date(); todayStart.setHours(0,0,0,0);
              incidents.filter(i => i.status === "RESOLVED" && i.resolved_at && new Date(i.resolved_at) >= todayStart).forEach(inc => {
                const sev = inc.severity || 1;
                const created = new Date(inc.created_at).getTime();
                const resolved = new Date(inc.resolved_at).getTime();
                const elapsed = (resolved - created) / 60000;
                if (sevBuckets[sev]) sevBuckets[sev].push(elapsed);
              });

              return (
                <>
                  {/* Fleet readiness gauge */}
                  <div className="ops-card ops-readiness">
                    <div className="ops-card-header"><Gauge size={14} /> Disponibilidad</div>
                    <div className="ops-gauge">
                      <div className="ops-gauge-bar">
                        <div className="ops-gauge-fill" style={{ width: `${readiness}%`, background: readiness > 60 ? '#22c55e' : readiness > 30 ? '#f59e0b' : '#ef4444' }} />
                      </div>
                      <span className="ops-gauge-pct">{readiness}%</span>
                    </div>
                    <div className="ops-status-row">
                      <span className="ops-dot" style={{background:'#22c55e'}} /> {idle} libres
                      <span className="ops-dot" style={{background:'#ef4444'}} /> {enRoute} en ruta
                      <span className="ops-dot" style={{background:'#3b82f6'}} /> {refueling} repostando
                    </div>
                  </div>

                  {/* Subtype breakdown */}
                  <div className="ops-card">
                    <div className="ops-card-header"><Ambulance size={14} /> Por Subtipo</div>
                    <div className="ops-subtype-list">
                      {Object.entries(subtypeCounts).sort((a, b) => b[1] - a[1]).map(([sub, count]) => (
                        <div key={sub} className="ops-subtype-row">
                          <span className="ops-subtype-tag" style={{ background: SCOLORS[sub] || '#6b7280' }}>{sub}</span>
                          <div className="ops-subtype-bar-bg">
                            <div className="ops-subtype-bar" style={{ width: `${(count / total) * 100}%`, background: SCOLORS[sub] || '#6b7280' }} />
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
                      <div className="ops-indicator">
                        <Fuel size={13} />
                        <span>Bajo combustible</span>
                        <strong className={lowFuel > 0 ? "warn" : ""}>{lowFuel}</strong>
                      </div>
                      <div className="ops-indicator">
                        <Zap size={13} />
                        <span>Vel. media</span>
                        <strong>{avgSpeed} km/h</strong>
                      </div>
                      <div className="ops-indicator">
                        <Star size={13} />
                        <span>Trust medio</span>
                        <strong>{avgTrust}</strong>
                      </div>
                      <div className="ops-indicator">
                        <Clock size={13} />
                        <span>Incidentes / amb.</span>
                        <strong>{enabled.length ? (openIncidents.length / enabled.length).toFixed(1) : '0'}</strong>
                      </div>
                    </div>
                  </div>

                  {/* Response times by severity */}
                  <div className="ops-card">
                    <div className="ops-card-header"><Clock size={14} /> Tiempos de Respuesta</div>
                    <div className="ops-response-table">
                      <div className="ops-rt-header">
                        <span>Sev</span><span>Casos</span><span>Media</span><span>Máx</span>
                      </div>
                      {[5,4,3,2,1].map(sev => {
                        const arr = sevBuckets[sev] || [];
                        const count = arr.length;
                        const avg = count ? (arr.reduce((a,b)=>a+b,0)/count) : 0;
                        const max = count ? Math.max(...arr) : 0;
                        const fmtMin = (m) => m < 60 ? `${Math.round(m)}m` : `${Math.floor(m/60)}h${Math.round(m%60)}m`;
                        const SEV_COLORS = ['','#22c55e','#84cc16','#f59e0b','#f97316','#ef4444'];
                        const SLA = { 5: 8, 4: 12, 3: 20, 2: 30, 1: 45 }; // SLA target minutes
                        const overSla = count > 0 && avg > SLA[sev];
                        return (
                          <div key={sev} className={`ops-rt-row ${overSla ? 'ops-rt-over' : ''}`}>
                            <span className="ops-rt-sev" style={{background: SEV_COLORS[sev]}}>{sev}</span>
                            <span>{count}</span>
                            <span className={overSla ? 'warn' : ''}>{count ? fmtMin(avg) : '—'}</span>
                            <span>{count ? fmtMin(max) : '—'}</span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </>
              );
            })()}
          </div>
        </div>

        {/* ── DIGITAL TWIN Panel ── */}
        <div className="info-section twin-section">
          <div className="twin-header" onClick={() => setTwinPanelOpen(v => !v)}>
            <strong><Cpu size={16} className="icon-3d" /> Digital Twin</strong>
            <span className="twin-toggle-icon">{twinPanelOpen ? <ChevronUp size={14} /> : <ChevronDown size={14} />}</span>
          </div>

          {twinPanelOpen && (
            <div className="twin-body">
              {/* Fleet health overview */}
              {fleetHealth && (
                <div className="twin-fleet-health">
                  <div className="twin-fleet-header">
                    <Activity size={14} /> Salud de Flota
                    <span className={`twin-health-badge ${fleetHealth.avg_health_score > 80 ? 'good' : fleetHealth.avg_health_score > 50 ? 'warn' : 'crit'}`}>
                      {fleetHealth.avg_health_score}%
                    </span>
                  </div>
                  <div className="twin-fleet-stats">
                    <div className="twin-stat">
                      <span>Vehículos</span>
                      <strong>{fleetHealth.fleet_size}</strong>
                    </div>
                    <div className="twin-stat">
                      <span>Anomalías</span>
                      <strong className={fleetHealth.total_anomalies > 0 ? 'warn' : ''}>{fleetHealth.total_anomalies}</strong>
                    </div>
                    <div className="twin-stat">
                      <span>Links Inter-Twin</span>
                      <strong>{fleetHealth.inter_twin_links?.length || 0}</strong>
                    </div>
                  </div>

                  {/* Inter-twin communication links */}
                  {fleetHealth.inter_twin_links?.length > 0 && (
                    <div className="twin-links">
                      <div className="twin-links-title"><Wifi size={12} /> Comunicación Inter-Twin</div>
                      {fleetHealth.inter_twin_links.slice(0, 3).map((link, i) => (
                        <div key={i} className="twin-link-row">
                          <Radio size={11} />
                          <span>{link.from}</span>
                          <span className="twin-link-arrow">⟷</span>
                          <span>{link.to}</span>
                          <span className="twin-link-dist">{link.distance_m}m</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Vehicle telemetry (when focused) */}
              {focusedVehicleId ? (
                twinLoading && !twinTelemetry ? (
                  <div className="twin-loading"><Activity size={14} className="sim-pulse" /> Cargando telemetría...</div>
                ) : twinTelemetry ? (
                  <div className="twin-telemetry">
                    <div className="twin-vehicle-header">
                      <Ambulance size={14} />
                      <strong>{twinTelemetry.vehicle_id}</strong>
                      <span className="subtype-tag" style={{background: {SVB:"#22c55e",SVA:"#ef4444",VIR:"#3b82f6",VAMM:"#f97316",SAMU:"#a855f7"}[twinTelemetry.subtype] || '#6b7280'}}>{twinTelemetry.subtype}</span>
                      <span className="twin-model-tag">{twinTelemetry.twin_metadata?.model}</span>
                    </div>

                    {/* Health gauge */}
                    <div className="twin-health-gauge">
                      <div className="twin-gauge-label">Salud del Gemelo</div>
                      <div className="twin-gauge-bar">
                        <div className="twin-gauge-fill" style={{
                          width: `${twinTelemetry.maintenance?.health_score || 0}%`,
                          background: (twinTelemetry.maintenance?.health_score || 0) > 80 ? '#22c55e' : (twinTelemetry.maintenance?.health_score || 0) > 50 ? '#f59e0b' : '#ef4444'
                        }} />
                      </div>
                      <span className="twin-gauge-pct">{twinTelemetry.maintenance?.health_score || 0}%</span>
                    </div>

                    {/* Key telemetry data */}
                    <div className="twin-kpi-grid">
                      <div className="twin-kpi">
                        <Gauge size={13} />
                        <span>{twinTelemetry.speed?.toFixed(0) || 0} km/h</span>
                      </div>
                      <div className="twin-kpi">
                        <Fuel size={13} />
                        <span>{twinTelemetry.fuel_pct?.toFixed(1)}% ({twinTelemetry.fuel_liters?.toFixed(0)}L)</span>
                      </div>
                      <div className="twin-kpi">
                        <Star size={13} />
                        <span>Trust: {twinTelemetry.trust_score}</span>
                      </div>
                      <div className="twin-kpi">
                        <Route size={13} />
                        <span>Autonomía: {twinTelemetry.maintenance?.estimated_range_km?.toFixed(0)} km</span>
                      </div>
                    </div>

                    {/* Maintenance status */}
                    <div className={`twin-maintenance ${twinTelemetry.maintenance?.maintenance_urgency === 'HIGH' ? 'urgent' : twinTelemetry.maintenance?.maintenance_urgency === 'MEDIUM' ? 'preventive' : 'ok'}`}>
                      <Wrench size={13} />
                      <span>{twinTelemetry.maintenance?.next_maintenance}</span>
                    </div>

                    {/* Efficiency */}
                    <div className="twin-efficiency">
                      <span>Eficiencia: {twinTelemetry.maintenance?.efficiency_pct}%</span>
                      <span>Consumo: {twinTelemetry.maintenance?.consumption_rate_L100km} L/100km (esp: {twinTelemetry.maintenance?.expected_consumption})</span>
                    </div>

                    {/* Anomalies */}
                    {twinTelemetry.anomalies?.length > 0 && (
                      <div className="twin-anomalies">
                        <div className="twin-anomalies-title"><AlertCircle size={13} /> Anomalías ({twinTelemetry.anomalies.length})</div>
                        {twinTelemetry.anomalies.map((a, i) => (
                          <div key={i} className={`twin-anomaly-row sev-${a.severity?.toLowerCase()}`}>
                            <AlertTriangle size={12} />
                            <span>{a.message}</span>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Sparkline (mini text chart) */}
                    {twinTelemetry.telemetry_sparkline?.speeds?.length > 5 && (
                      <div className="twin-sparkline">
                        <div className="twin-spark-title"><TrendingUp size={12} /> Velocidad (últimos {twinTelemetry.telemetry_sparkline.speeds.length} ticks)</div>
                        <div className="twin-spark-bars">
                          {twinTelemetry.telemetry_sparkline.speeds.slice(-30).map((s, i) => {
                            const maxS = twinTelemetry.twin_metadata?.max_speed_kmh || 100;
                            return <div key={i} className="twin-spark-bar" style={{ height: `${Math.min(100, (s / maxS) * 100)}%` }} title={`${s?.toFixed(0)} km/h`} />;
                          })}
                        </div>
                      </div>
                    )}

                    {/* Metadata */}
                    <div className="twin-meta">
                      <Cpu size={11} /> <span>Tick: {twinTelemetry.twin_metadata?.tick_rate_ms}ms</span>
                      <span>·</span>
                      <span>Buffer: {twinTelemetry.twin_metadata?.history_depth} pts</span>
                      <span>·</span>
                      <span>×{twinTelemetry.speed_multiplier}</span>
                    </div>
                  </div>
                ) : null
              ) : (
                <div className="twin-empty">
                  <Eye size={14} /> Selecciona un vehículo para ver su gemelo digital
                </div>
              )}

              {/* What-If Simulator */}
              <div className="twin-whatif">
                <div className="twin-whatif-title"><Sparkles size={13} /> Simulador "What-If"</div>
                <div className="twin-whatif-btns">
                  <button className="twin-whatif-btn" onClick={() => runWhatIf("vehicle_breakdown", focusedVehicleId)} disabled={whatIfLoading}>
                    <Wrench size={12} /> Avería
                  </button>
                  <button className="twin-whatif-btn" onClick={() => runWhatIf("fuel_shortage")} disabled={whatIfLoading}>
                    <Fuel size={12} /> Combustible
                  </button>
                  <button className="twin-whatif-btn" onClick={() => runWhatIf("mass_casualty", null, { extra_incidents: 8 })} disabled={whatIfLoading}>
                    <Siren size={12} /> Masivo
                  </button>
                  <button className="twin-whatif-btn" onClick={() => runWhatIf("road_closure", null, { lat: 40.42, lon: -3.70, radius_m: 1000 })} disabled={whatIfLoading}>
                    <AlertTriangle size={12} /> Corte vial
                  </button>
                </div>
                {whatIfLoading && <div className="twin-loading"><Activity size={12} className="sim-pulse" /> Simulando escenario...</div>}
                {whatIfResult && !whatIfLoading && (
                  <div className={`twin-whatif-result risk-${whatIfResult.risk_level?.toLowerCase()}`}>
                    <div className="twin-whatif-result-header">
                      <strong>{whatIfResult.description}</strong>
                      <span className={`twin-risk-badge risk-${whatIfResult.risk_level?.toLowerCase()}`}>{whatIfResult.risk_level}</span>
                    </div>
                    <div className="twin-whatif-impact">
                      {Object.entries(whatIfResult.impact || {}).map(([k, v]) => (
                        <div key={k} className="twin-impact-row">
                          <span>{k.replace(/_/g, ' ')}</span>
                          <strong>{typeof v === 'boolean' ? (v ? 'Sí' : 'No') : v}</strong>
                        </div>
                      ))}
                    </div>
                    <div className="twin-whatif-recs">
                      {whatIfResult.recommendations?.map((r, i) => (
                        <div key={i} className="twin-rec-row">💡 {r}</div>
                      ))}
                    </div>
                    <button className="twin-whatif-close" onClick={() => setWhatIfResult(null)}><X size={12} /> Cerrar</button>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Emergency service alert modal */}
      {emergencyAlert && (
        <div className="modal-overlay emergency-overlay" onClick={() => setEmergencyAlert(null)}>
          <div className={`emergency-alert-modal ${emergencyAlert.type === "FIREFIGHTERS" ? "alert-fire" : "alert-police"}`} onClick={e => e.stopPropagation()}>
            <div className="emergency-alert-header">
              {emergencyAlert.type === "FIREFIGHTERS" ? <Flame size={32} color="#f97316" /> : <Shield size={32} color="#3b82f6" />}
              <h2>{emergencyAlert.type === "FIREFIGHTERS" ? "¿Alertar a Bomberos?" : "¿Alertar a Policía Nacional?"}</h2>
            </div>
            <div className="emergency-alert-body">
              <p>
                Se ha registrado un incidente de <strong>{emergencyAlert.type === "FIREFIGHTERS" ? "Quemadura" : "Violencia"}</strong> (Severidad {emergencyAlert.incident.severity}/5).
              </p>
              <p>
                {emergencyAlert.type === "FIREFIGHTERS"
                  ? "Se recomienda coordinar con el Servicio de Bomberos para asistencia en el lugar."
                  : "Se recomienda coordinar con la Policía Nacional para seguridad en el lugar."}
              </p>
              <div className="emergency-alert-info">
                <div><strong>ID:</strong> {emergencyAlert.incident.id}</div>
                <div><strong>Ubicación:</strong> {emergencyAlert.incident.address || `${emergencyAlert.incident.lat?.toFixed(4)}, ${emergencyAlert.incident.lon?.toFixed(4)}`}</div>
              </div>
            </div>
            <div className="emergency-alert-actions">
              <button className="btn-emergency-call" onClick={() => { toast.success(emergencyAlert.type === "FIREFIGHTERS" ? "📞 Bomberos notificados" : "📞 Policía notificada", { duration: 4000 }); setEmergencyAlert(null); }}>
                <Phone size={16} /> {emergencyAlert.type === "FIREFIGHTERS" ? "Llamar a Bomberos (080)" : "Llamar a Policía (091)"}
              </button>
              <button className="btn-secondary" onClick={() => setEmergencyAlert(null)}>
                <X size={16} /> Descartar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* AI auto-suggestion floating panel */}
      {aiAutoSuggestions.length > 0 && (
        <div className="ai-auto-panel">
          <div className="ai-auto-panel-header">
            <Bot size={18} /> Recomendaciones IA ({aiAutoSuggestions.length})
          </div>
          {aiAutoSuggestions.map(({ incidentId, incident, suggestion }) => (
            <div key={incidentId} className="ai-auto-card">
              <div className="ai-auto-card-header">
                <span>{getIncidentTypeLabel(incident?.incident_type)} — {incidentId}</span>
                <button className="ai-auto-close" onClick={() => dismissAiAutoSuggestion(incidentId)}><X size={14} /></button>
              </div>
              {suggestion.vehicle_suggestion && (
                <div className="ai-auto-row">
                  <Ambulance size={14} /> <strong>{suggestion.vehicle_suggestion.vehicle_id}</strong> — ETA {suggestion.vehicle_suggestion.eta_minutes} min ({suggestion.vehicle_suggestion.distance_km} km)
                </div>
              )}
              {suggestion.hospital_suggestion && (
                <div className="ai-auto-row">
                  <Hospital size={14} /> <strong>{suggestion.hospital_suggestion.hospital_name}</strong>
                </div>
              )}
              <div className="ai-auto-actions">
                <button className="btn-sm-success" onClick={() => {
                  confirmAssignment(
                    incidentId,
                    suggestion.vehicle_suggestion?.vehicle_id,
                    suggestion.hospital_suggestion?.hospital_id,
                    null
                  );
                  dismissAiAutoSuggestion(incidentId);
                }}>
                  <CheckCircle size={12} /> Aceptar
                </button>
                <button className="btn-sm-secondary" onClick={() => {
                  setSelectedIncident(incident);
                  setAiSuggestion(suggestion);
                  dismissAiAutoSuggestion(incidentId);
                }}>
                  <Bot size={12} /> Ver detalle
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal for incident details and AI suggestion */}
      {selectedIncident && (
        <div className="modal-overlay" onClick={() => { setSelectedIncident(null); setIncidentTimeline(null); }}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2><ClipboardList size={24} className="icon-3d" /> Detalle del Incidente</h2>
              <button
                className="close-btn"
                onClick={() => { setSelectedIncident(null); setIncidentTimeline(null); }}
              >
                ✕
              </button>
            </div>

            <div className="modal-body">
              <div className="detail-row">
                <strong>ID:</strong> {selectedIncident.id}
              </div>
              <div className="detail-row">
                <strong>Tipo:</strong> {getIncidentTypeLabel(selectedIncident.incident_type)}
              </div>
              <div className="detail-row">
                <strong>Severidad:</strong> {selectedIncident.severity}/5
              </div>
              <div className="detail-row">
                <strong>Estado:</strong> {selectedIncident.status}
              </div>
              <div className="detail-row">
                <strong>Descripción:</strong> {selectedIncident.description || "Sin descripción"}
              </div>
              <div className="detail-row">
                <strong>Dirección:</strong> {selectedIncident.address || "No especificada"}
              </div>
              <div className="detail-row">
                <strong>Afectados:</strong> {selectedIncident.affected_count || 1} persona(s)
              </div>

              {/* Timeline button */}
              <button
                className="btn-secondary"
                onClick={() => fetchTimeline(selectedIncident.id)}
                style={{ marginTop: "0.5rem", marginBottom: "0.5rem" }}
              >
                <ScrollText size={16} /> Ver Timeline
              </button>

              {incidentTimeline && (
                <div className="incident-timeline">
                  <h4><ScrollText size={16} /> Timeline del Incidente</h4>
                  <div className="timeline-list">
                    {incidentTimeline.map((evt, idx) => (
                      <div key={idx} className="timeline-event">
                        <div className="timeline-dot" style={{ background: evt.color || "#667eea" }}>
                          {evt.icon || "●"}
                        </div>
                        <div className="timeline-content">
                          <div className="timeline-action">{evt.action}</div>
                          <div className="timeline-detail">{evt.detail}</div>
                          <div className="timeline-time">{new Date(evt.timestamp).toLocaleString("es-ES")}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {selectedIncident.status === "OPEN" && (user?.role === "ADMIN" || user?.role === "OPERATOR") && (
                <>
                  <button
                    className="btn-primary"
                    onClick={() => getAISuggestion(selectedIncident.id)}
                    disabled={loadingSuggestion}
                  >
                    {loadingSuggestion ? <><Bot size={16} /> Analizando...</> : <><Bot size={16} /> Obtener Sugerencia de IA</>}
                  </button>

                  {aiSuggestion && (
                    <div className="ai-suggestion">
                      <h3><Bot size={20} className="icon-3d" /> Recomendación de IA</h3>
                      
                      {aiSuggestion.vehicle_suggestion && (
                        <div className="suggestion-box">
                          <h4><Ambulance size={16} /> Ambulancia Sugerida</h4>
                          <div><strong>ID:</strong> {aiSuggestion.vehicle_suggestion.vehicle_id}</div>
                          <div><strong>ETA:</strong> {aiSuggestion.vehicle_suggestion.eta_minutes} minutos</div>
                          <div><strong>Distancia:</strong> {aiSuggestion.vehicle_suggestion.distance_km} km</div>
                          <div><strong>Confianza:</strong> {(aiSuggestion.vehicle_suggestion.confidence * 100).toFixed(0)}%</div>
                          <div className="reasoning">{aiSuggestion.vehicle_suggestion.reasoning}</div>
                        </div>
                      )}
                      
                      {aiSuggestion.hospital_suggestion && (
                        <div className="suggestion-box">
                          <h4><Hospital size={16} /> Hospital Sugerido</h4>
                          <div><strong>Nombre:</strong> {aiSuggestion.hospital_suggestion.hospital_name}</div>
                          <div><strong>ID:</strong> {aiSuggestion.hospital_suggestion.hospital_id}</div>
                          <div><strong>Confianza:</strong> {(aiSuggestion.hospital_suggestion.confidence * 100).toFixed(0)}%</div>
                          <div className="reasoning">{aiSuggestion.hospital_suggestion.reasoning}</div>
                          
                          {aiSuggestion.hospital_suggestion.alternatives?.length > 0 && (
                            <div className="alternatives">
                              <strong>Alternativas:</strong>
                              {aiSuggestion.hospital_suggestion.alternatives.map((alt) => (
                                <div key={alt.hospital_id}>
                                  • {alt.hospital_name} ({(alt.confidence * 100).toFixed(0)}%)
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )}

                      <div className="button-group">
                        <button
                          className="btn-success"
                          onClick={() =>
                            confirmAssignment(
                              selectedIncident.id,
                              aiSuggestion.vehicle_suggestion?.vehicle_id,
                              aiSuggestion.hospital_suggestion?.hospital_id,
                              null
                            )
                          }
                        >
                          <CheckCircle size={16} /> Aceptar Sugerencia
                        </button>
                        <button
                          className="btn-warning"
                          onClick={() => {
                            setOverrideMode(!overrideMode);
                            setOverrideVehicle(aiSuggestion.vehicle_suggestion?.vehicle_id || "");
                            setOverrideHospital(aiSuggestion.hospital_suggestion?.hospital_id || "");
                            setOverrideReason("");
                          }}
                        >
                          <Pencil size={16} /> {overrideMode ? "Cancelar" : "Modificar y Asignar"}
                        </button>
                      </div>

                      {overrideMode && (
                        <div className="override-form">
                          <div className="override-field">
                            <label>Ambulancia</label>
                            <select value={overrideVehicle} onChange={e => setOverrideVehicle(e.target.value)}>
                              <option value="">— Seleccionar —</option>
                              {vehicles.filter(v => v.status === "IDLE").map(v => (
                                <option key={v.id} value={v.id}>{v.id} ({v.subtype || "SVB"})</option>
                              ))}
                            </select>
                          </div>
                          <div className="override-field">
                            <label>Hospital</label>
                            <select value={overrideHospital} onChange={e => setOverrideHospital(e.target.value)}>
                              <option value="">— Seleccionar —</option>
                              {hospitals.map(h => (
                                <option key={h.id} value={h.id}>{h.name || h.id}</option>
                              ))}
                            </select>
                          </div>
                          <div className="override-field">
                            <label>Motivo del cambio</label>
                            <input type="text" placeholder="Ej: Vehículo más cercano disponible" value={overrideReason} onChange={e => setOverrideReason(e.target.value)} />
                          </div>
                          <button
                            className="btn-success"
                            disabled={!overrideVehicle || !overrideReason}
                            onClick={() => confirmAssignment(selectedIncident.id, overrideVehicle, overrideHospital, overrideReason)}
                          >
                            <CheckCircle size={16} /> Confirmar Asignación Manual
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </>
              )}

              {(selectedIncident.status === "ASSIGNED" || selectedIncident.status === "EN_ROUTE") && 
               (user?.role === "ADMIN" || user?.role === "OPERATOR") && (
                <button
                  className="btn-success"
                  onClick={() => resolveIncident(selectedIncident.id)}
                >
                  <CheckCircle size={16} /> Marcar como Resuelto
                </button>
              )}

              {selectedIncident.status === "RESOLVED" && (
                <div className="resolved-badge">
                  <CheckCircle size={16} /> Incidente resuelto
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
