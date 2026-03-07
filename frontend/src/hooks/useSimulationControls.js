import { useState, useEffect, useRef, useCallback } from "react";
import { API_BASE } from "../config";
import toast from "react-hot-toast";

export function useSimulationControls({ setAiAutoSuggestions, setSelectedIncident, setIncidentTimeline, setAiSuggestion, prevIncidentIdsRef }) {
  const [autoGenRunning, setAutoGenRunning] = useState(false);
  const [autoGenInterval, setAutoGenInterval] = useState(30);
  const [autoGenCount, setAutoGenCount] = useState(0);
  const [resetting, setResetting] = useState(false);
  const [lastGenIncident, setLastGenIncident] = useState(null);
  const [speedMultiplier, setSpeedMultiplier] = useState(1);
  const prevAutoGenCountRef = useRef(0);

  const toggleAutoGen = useCallback(async () => {
    try {
      if (autoGenRunning) {
        const res = await fetch(`${API_BASE}/simulation/auto-generate/stop`, { method: "POST" });
        if (res.ok) {
          setAutoGenRunning(false);
          setLastGenIncident(null);
          toast.success("Generación automática detenida");
        }
      } else {
        const res = await fetch(`${API_BASE}/simulation/auto-generate/start?interval=${autoGenInterval}`, { method: "POST" });
        if (res.ok) {
          setAutoGenRunning(true);
          setAutoGenCount(0);
          prevAutoGenCountRef.current = 0;
          toast.success(`Generando incidentes cada ~${autoGenInterval}s`);
        }
      }
    } catch {
      toast.error("Error al controlar auto-generación");
    }
  }, [autoGenRunning, autoGenInterval]);

  const resetSystem = useCallback(async () => {
    if (!confirm("¿Reiniciar TODO el sistema? Se borrarán incidentes, auditorías y se reseteará la flota.")) return;
    setResetting(true);
    try {
      const res = await fetch(`${API_BASE}/simulation/reset`, { method: "POST" });
      if (res.ok) {
        const data = await res.json();
        toast.success(`Sistema reiniciado: ${data.deleted_incidents} incidentes borrados`);
        setAutoGenRunning(false);
        setAutoGenCount(0);
        setLastGenIncident(null);
        setAiAutoSuggestions([]);
        setSelectedIncident(null);
        setIncidentTimeline(null);
        setAiSuggestion(null);
        prevIncidentIdsRef.current = new Set();
      }
    } catch {
      toast.error("Error al reiniciar sistema");
    }
    setResetting(false);
  }, [setAiAutoSuggestions, setSelectedIncident, setIncidentTimeline, setAiSuggestion, prevIncidentIdsRef]);

  // Poll auto-gen status + detect new incidents
  useEffect(() => {
    const poll = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/simulation/auto-generate/status`);
        if (!res.ok) return;
        const d = await res.json();
        setAutoGenRunning(d.running);
        if (d.total_generated > prevAutoGenCountRef.current && d.running) {
          try {
            const liveRes = await fetch(`${API_BASE}/api/live`);
            if (liveRes.ok) {
              const live = await liveRes.json();
              const openIncs = (live.incidents || []).filter(i => i.status === "OPEN");
              if (openIncs.length > 0) setLastGenIncident(openIncs[openIncs.length - 1]);
            }
          } catch { /* ignored */ }
        }
        prevAutoGenCountRef.current = d.total_generated;
        setAutoGenCount(d.total_generated);
      } catch { /* ignored */ }
    }, 8000);
    return () => clearInterval(poll);
  }, []);

  return {
    autoGenRunning, autoGenInterval, setAutoGenInterval,
    autoGenCount, resetting, lastGenIncident,
    speedMultiplier, setSpeedMultiplier,
    toggleAutoGen, resetSystem,
  };
}
