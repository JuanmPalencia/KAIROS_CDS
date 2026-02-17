import { Component } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

/**
 * Error Boundary — catches unhandled React errors and shows a fallback UI
 * instead of white-screening the entire app.
 */
export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({ errorInfo });
    console.error("[ErrorBoundary]", error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div style={styles.container}>
          <div style={styles.card}>
            <AlertTriangle size={48} style={{ color: "#ef4444", marginBottom: 16 }} />
            <h2 style={styles.title}>Algo salió mal</h2>
            <p style={styles.text}>
              Se ha producido un error inesperado. Puedes intentar recargar la sección.
            </p>
            {this.state.error && (
              <pre style={styles.pre}>{this.state.error.toString()}</pre>
            )}
            <div style={styles.actions}>
              <button onClick={this.handleReset} style={styles.btnPrimary}>
                <RefreshCw size={16} /> Reintentar
              </button>
              <button onClick={() => window.location.reload()} style={styles.btnSecondary}>
                Recargar página
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

const styles = {
  container: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    minHeight: "60vh",
    padding: 24,
  },
  card: {
    background: "var(--bg-card, #fff)",
    border: "1px solid var(--border-color, #e0e0e0)",
    borderRadius: 16,
    padding: 40,
    maxWidth: 480,
    textAlign: "center",
    boxShadow: "0 4px 24px var(--shadow-color, rgba(0,0,0,0.1))",
  },
  title: {
    margin: "0 0 8px",
    fontSize: 22,
    color: "var(--text-primary, #333)",
  },
  text: {
    color: "var(--text-secondary, #555)",
    margin: "0 0 16px",
    lineHeight: 1.5,
  },
  pre: {
    background: "var(--bg-input, #f5f5f5)",
    padding: 12,
    borderRadius: 8,
    fontSize: 12,
    overflow: "auto",
    maxHeight: 120,
    textAlign: "left",
    color: "#ef4444",
    marginBottom: 16,
  },
  actions: {
    display: "flex",
    gap: 12,
    justifyContent: "center",
    flexWrap: "wrap",
  },
  btnPrimary: {
    display: "inline-flex",
    alignItems: "center",
    gap: 6,
    padding: "10px 20px",
    background: "linear-gradient(135deg, #667eea, #764ba2)",
    color: "#fff",
    border: "none",
    borderRadius: 8,
    cursor: "pointer",
    fontWeight: 600,
    fontSize: 14,
  },
  btnSecondary: {
    padding: "10px 20px",
    background: "transparent",
    color: "var(--text-secondary, #555)",
    border: "1px solid var(--border-color, #e0e0e0)",
    borderRadius: 8,
    cursor: "pointer",
    fontSize: 14,
  },
};
