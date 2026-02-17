/**
 * NotificationManager — Browser notifications + sound alerts for critical incidents.
 *
 * Features:
 * - Requests browser Notification permission on mount
 * - Plays audio alert on severity 4-5 incidents
 * - Shows native browser notifications when tab is not focused
 * - Debounced to avoid notification spam
 */
import { useEffect, useRef, useCallback } from "react";

const ALERT_SOUND_URL = "data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgkKutl2xBMkN0nK2ug1g0OGmRqq2SYzk0YIykrZlnRjg+Xoifqptkdll1b3luaF1VYm1paWFaV2FqaWdiW1lia2tnYlxbYmtqZ2JdXGJra2diXVxia2tn";

// Severity labels for notifications
const sevLabels = { 5: "CRÍTICO", 4: "GRAVE", 3: "MODERADO", 2: "LEVE", 1: "MENOR" };

export function useIncidentNotifications(incidents) {
  const knownIds = useRef(new Set());
  const audioRef = useRef(null);

  // Request notification permission on first call
  useEffect(() => {
    if ("Notification" in window && Notification.permission === "default") {
      Notification.requestPermission();
    }
  }, []);

  const notify = useCallback((incident) => {
    const title = `🚨 ${sevLabels[incident.severity] || "NUEVO"} — ${incident.type}`;
    const body = `${incident.description || "Incidente nuevo"}\nSeveridad: ${incident.severity}/5`;

    // Browser notification (when tab not focused)
    if ("Notification" in window && Notification.permission === "granted" && document.hidden) {
      try {
        const n = new Notification(title, {
          body,
          icon: "/favicon.ico",
          tag: incident.id, // Prevents duplicate notifications
          requireInteraction: incident.severity >= 4,
        });
        // Auto-close after 8 seconds for non-critical
        if (incident.severity < 4) {
          setTimeout(() => n.close(), 8000);
        }
      } catch {
        // Notification API not available in some contexts
      }
    }

    // Audio alert for severity 4-5
    if (incident.severity >= 4) {
      try {
        if (!audioRef.current) {
          audioRef.current = new Audio(ALERT_SOUND_URL);
          audioRef.current.volume = 0.5;
        }
        audioRef.current.play().catch(() => {});
      } catch {
        // Audio not available
      }
    }
  }, []);

  // Watch for new incidents
  useEffect(() => {
    if (!incidents || !Array.isArray(incidents)) return;

    for (const inc of incidents) {
      if (inc.status === "OPEN" && !knownIds.current.has(inc.id)) {
        knownIds.current.add(inc.id);
        notify(inc);
      }
    }

    // Keep the set clean — remove resolved/closed incidents
    const activeIds = new Set(incidents.map((i) => i.id));
    for (const id of knownIds.current) {
      if (!activeIds.has(id)) knownIds.current.delete(id);
    }
  }, [incidents, notify]);
}

export default useIncidentNotifications;
