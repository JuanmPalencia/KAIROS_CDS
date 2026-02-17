import { Loader } from "lucide-react";

/**
 * Suspense fallback — shown while lazy-loaded pages are being fetched.
 */
export default function LoadingFallback() {
  return (
    <div style={styles.container} role="status" aria-label="Cargando página">
      <div style={styles.card}>
        <Loader size={36} style={styles.spinner} className="spin-animation" />
        <p style={styles.text}>Cargando…</p>
      </div>
      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        .spin-animation { animation: spin 1s linear infinite; }
      `}</style>
    </div>
  );
}

const styles = {
  container: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    minHeight: "60vh",
  },
  card: {
    textAlign: "center",
  },
  spinner: {
    color: "var(--accent, #667eea)",
    marginBottom: 12,
  },
  text: {
    color: "var(--text-secondary, #555)",
    fontSize: 16,
    margin: 0,
  },
};
