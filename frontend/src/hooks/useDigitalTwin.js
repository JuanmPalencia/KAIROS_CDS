import { useState, useEffect, useCallback } from "react";
import { API_BASE } from "../config";

export function useDigitalTwin(focusedVehicleId) {
  const [twinPanelOpen, setTwinPanelOpen] = useState(false);
  const [twinTelemetry, setTwinTelemetry] = useState(null);
  const [twinLoading, setTwinLoading] = useState(false);
  const [fleetHealth, setFleetHealth] = useState(null);
  const [whatIfResult, setWhatIfResult] = useState(null);
  const [whatIfLoading, setWhatIfLoading] = useState(false);

  const fetchTwinTelemetry = useCallback(async (vehicleId) => {
    setTwinLoading(true);
    try {
      const res = await fetch(`${API_BASE}/digital-twin/telemetry/${vehicleId}`, {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
      });
      if (res.ok) setTwinTelemetry(await res.json());
    } catch (e) {
      console.error("Twin telemetry error:", e);
    } finally {
      setTwinLoading(false);
    }
  }, []);

  const fetchFleetHealth = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/digital-twin/fleet-health`, {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
      });
      if (res.ok) setFleetHealth(await res.json());
    } catch (e) {
      console.error("Fleet health error:", e);
    }
  }, []);

  const runWhatIf = useCallback(async (scenario, vehicleId = null, params = {}) => {
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
    } catch (e) {
      console.error("What-if error:", e);
    } finally {
      setWhatIfLoading(false);
    }
  }, []);

  useEffect(() => {
    if (focusedVehicleId && twinPanelOpen) {
      fetchTwinTelemetry(focusedVehicleId);
      const interval = setInterval(() => fetchTwinTelemetry(focusedVehicleId), 5000);
      return () => clearInterval(interval);
    }
  }, [focusedVehicleId, twinPanelOpen]);

  useEffect(() => {
    if (twinPanelOpen) {
      fetchFleetHealth();
      const interval = setInterval(fetchFleetHealth, 10000);
      return () => clearInterval(interval);
    }
  }, [twinPanelOpen]);

  return {
    twinPanelOpen, setTwinPanelOpen,
    twinTelemetry, twinLoading,
    fleetHealth,
    whatIfResult, setWhatIfResult, whatIfLoading,
    runWhatIf,
  };
}
