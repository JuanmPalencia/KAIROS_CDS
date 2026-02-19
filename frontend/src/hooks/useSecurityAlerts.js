import { useState, useEffect, useRef, useCallback } from "react";
import { API_BASE } from "../config";

const POLL_INTERVAL = 5000; // 5 seconds

/**
 * Hook that polls for HIGH/CRITICAL security alerts.
 * Returns { alerts, hasNew, clearNew, latestId }
 */
export function useSecurityAlerts(token, enabled = true) {
  const [alerts, setAlerts] = useState([]);
  const [hasNew, setHasNew] = useState(false);
  const latestIdRef = useRef(0);

  const clearNew = useCallback(() => setHasNew(false), []);

  useEffect(() => {
    if (!token || !enabled) return;

    let cancelled = false;

    const poll = async () => {
      try {
        const res = await fetch(
          `${API_BASE}/api/security/alerts/recent?since_id=${latestIdRef.current}`,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        if (!res.ok) return;
        const data = await res.json();

        if (data.alerts && data.alerts.length > 0) {
          if (!cancelled) {
            setAlerts((prev) => [...prev, ...data.alerts].slice(-50));
            setHasNew(true);

            // Browser notification
            if (Notification.permission === "granted") {
              const latest = data.alerts[data.alerts.length - 1];
              new Notification("KAIROS Security Alert", {
                body: `[${latest.severity}] ${latest.event_type}: ${latest.details.slice(0, 100)}`,
                icon: "/favicon.ico",
                tag: "kairos-security",
              });
            }
          }
        }

        if (!cancelled) {
          latestIdRef.current = data.latest_id;
        }
      } catch {
        // Silently ignore network errors
      }
    };

    // Request notification permission on first use
    if ("Notification" in window && Notification.permission === "default") {
      Notification.requestPermission();
    }

    poll(); // Initial fetch
    const id = setInterval(poll, POLL_INTERVAL);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [token, enabled]);

  return { alerts, hasNew, clearNew, latestId: latestIdRef.current };
}
