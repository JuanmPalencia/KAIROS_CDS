import { memo } from "react";
import { Ambulance, Fuel, Flame, Hospital, HeartPulse } from "lucide-react";

function MetricCards({ fleetMetrics, openIncidents, hospitals, gasStations, deaLocations }) {
  const cards = [
    { Icon: Ambulance,  value: fleetMetrics.active_vehicles,        label: "Ambulancias Activas" },
    { Icon: Fuel,       value: `${fleetMetrics.avg_fuel.toFixed(1)}%`, label: "Combustible Promedio" },
    { Icon: Flame,      value: openIncidents.length,                 label: "Incidentes Abiertos" },
    { Icon: Hospital,   value: hospitals.length,                     label: "Hospitales Disponibles" },
    { Icon: Fuel,       value: gasStations.length,                   label: "Gasolineras" },
    { Icon: HeartPulse, value: deaLocations.length,                  label: "DEA Disponibles" },
  ];

  return (
    <div className="metrics-cards">
      {cards.map((card) => (
        <div key={card.label} className="metric-card">
          <div className="metric-icon"><card.Icon size={24} className="icon-3d" /></div>
          <div className="metric-value">{card.value}</div>
          <div className="metric-label">{card.label}</div>
        </div>
      ))}
    </div>
  );
}

export default memo(MetricCards);
