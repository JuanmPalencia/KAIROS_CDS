import { memo } from "react";
import { Flame, Route, Fuel, Heart, MapPin, Shield, Activity, Waves, AlertTriangle } from "lucide-react";

function MapControlsToolbar({
  showHeatmap, setShowHeatmap,
  showRoutes, setShowRoutes,
  showGasStations, setShowGasStations,
  showDEA, setShowDEA,
  showGIS, setShowGIS,
  showAgencies, setShowAgencies,
  showSSM, setShowSSM,
  showCoverage, setShowCoverage,
  showRiskZones, setShowRiskZones,
}) {
  const toggle = (setter) => setter(v => !v);

  const buttons = [
    { state: showHeatmap,    setter: setShowHeatmap,    Icon: Flame,         label: "Heatmap",    title: "Mapa de calor" },
    { state: showRoutes,     setter: setShowRoutes,     Icon: Route,         label: "Rutas",      title: "Mostrar rutas" },
    { state: showGasStations,setter: setShowGasStations,Icon: Fuel,          label: "Gasolineras",title: "Mostrar gasolineras" },
    { state: showDEA,        setter: setShowDEA,        Icon: Heart,         label: "DEA",        title: "Desfibriladores (DEA)" },
    { state: showGIS,        setter: setShowGIS,        Icon: MapPin,        label: "GIS",        title: "Capas GIS (colegios, residencias, HAZMAT)" },
    { state: showAgencies,   setter: setShowAgencies,   Icon: Shield,        label: "Agencias",   title: "Recursos multi-agencia" },
    { state: showSSM,        setter: setShowSSM,        Icon: Activity,      label: "SSM",        title: "Zonas SSM cobertura" },
    { state: showCoverage,   setter: setShowCoverage,   Icon: Waves,         label: "Cobertura",  title: "Radio de cobertura ambulancias" },
    { state: showRiskZones,  setter: setShowRiskZones,  Icon: AlertTriangle, label: "Riesgo",     title: "Zonas de riesgo por densidad de incidentes" },
  ];

  return (
    <div className="map-controls">
      {buttons.map((btn) => (
        <button
          key={btn.label}
          className={`map-control-btn ${btn.state ? "active" : ""}`}
          onClick={() => toggle(btn.setter)}
          title={btn.title}
        >
          <btn.Icon size={16} /> {btn.label}
        </button>
      ))}
    </div>
  );
}

export default memo(MapControlsToolbar);
