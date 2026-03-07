import { useState, useCallback, useRef } from "react";
import { WMO_MAP, COND_ICON } from "../utils/weatherUtils";

export function useWeather() {
  const [weather, setWeather] = useState(null);
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
      const precip = cur.precipitation ?? 0;
      const rain = cur.rain ?? 0;
      const snow = cur.snowfall ?? 0;
      const cloudCover = cur.cloud_cover ?? 0;

      let [cond, alert, mult, desc] = WMO_MAP[wmo] || ["CLOUD","GREEN",1,"Nublado"];

      // Cross-check WMO code against actual measurements
      if (["RAIN","DRIZZLE","SHOWERS"].includes(cond) && precip < 0.1 && rain < 0.1) {
        cond = cloudCover > 70 ? "CLOUD" : cloudCover > 30 ? "CLOUD" : "CLEAR";
        alert = "GREEN"; mult = 1;
        desc = cloudCover > 70 ? "Nublado" : cloudCover > 30 ? "Parcialmente nublado" : "Despejado";
      }
      if (cond === "SNOW" && snow < 0.01 && precip < 0.1) {
        cond = "CLOUD"; alert = "GREEN"; mult = 1; desc = "Nublado";
      }
      if (temp >= 38 && cond === "CLEAR") {
        cond = "HEAT"; alert = "ORANGE"; mult = 1.1; desc = "Calor extremo";
      }

      const displayDesc = alert !== "GREEN" ? `${desc} — ETAs x${mult.toFixed(1)}` : desc;

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
    } catch (e) {
      console.error("Weather fetch error:", e);
    }
  }, []);

  const onMapMouseMove = useCallback((e) => {
    clearTimeout(weatherTimerRef.current);
    weatherTimerRef.current = setTimeout(() => {
      fetchWeather(e.latlng.lat.toFixed(4), e.latlng.lng.toFixed(4));
    }, 2000);
  }, [fetchWeather]);

  return { weather, fetchWeather, onMapMouseMove };
}
