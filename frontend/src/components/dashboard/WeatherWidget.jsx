import { memo } from "react";
import { Wind, Droplets } from "lucide-react";

function WeatherWidget({ weather }) {
  if (!weather) return null;
  return (
    <div
      className="weather-widget"
      title={`${weather.detail_desc || weather.condition}\nViento: ${weather.wind_speed_kmh ?? "--"} km/h (ráfagas ${weather.wind_gusts_kmh ?? "--"} km/h)\nHumedad: ${weather.humidity_pct ?? "--"}%\nSensación térmica: ${weather.apparent_temperature_c ?? "--"}°C\nNubosidad: ${weather.cloud_cover_pct ?? "--"}%\nPrecipitación: ${weather.precipitation_mm ?? 0} mm\nWMO: ${weather.wmo_code}`}
    >
      <span className="weather-icon">{weather.icon || "☁️"}</span>
      <span className="weather-temp">{weather.temperature_c ?? "--"}°C</span>
      <span className="weather-details">
        <Wind size={11} /> {weather.wind_speed_kmh ?? "--"} km/h
        <Droplets size={11} style={{ marginLeft: 6 }} /> {weather.humidity_pct ?? "--"}%
      </span>
      <span className="weather-cond">{weather.description || weather.condition}</span>
      {weather.alert_level && weather.alert_level !== "GREEN" && (
        <span className={`weather-alert weather-alert-${weather.alert_level?.toLowerCase()}`}>
          ⚠ {weather.alert_level}
        </span>
      )}
    </div>
  );
}

export default memo(WeatherWidget);
