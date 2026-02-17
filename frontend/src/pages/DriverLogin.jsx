import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";
import { LogIn } from "lucide-react";
import logoKairos from "../assets/logo_kairos.png";
import logoGtp from "../assets/logo_gtp.jpeg";
import "../styles/DriverMobile.css";

export default function DriverLogin() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login, user } = useAuth();
  const navigate = useNavigate();

  // If already logged in, redirect to driver app
  if (user) {
    navigate("/driver", { replace: true });
    return null;
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(username, password);
      navigate("/driver");
    } catch {
      setError("Credenciales incorrectas");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="driver-page driver-login-page">
      <div className="driver-login-container">
        <div className="driver-login-logo">
          <img src={logoKairos} alt="KAIROS" className="driver-login-logo-img" />
          <h1>KAIROS</h1>
          <p>App Conductor</p>
          <img src={logoGtp} alt="GTP" className="driver-login-gtp" />
        </div>

        <form onSubmit={handleSubmit} className="driver-login-form">
          {error && <div className="driver-login-error">{error}</div>}

          <div className="driver-login-field">
            <label htmlFor="drv-user">Usuario</label>
            <input
              id="drv-user"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Ej: conductor01"
              required
              autoFocus
              autoComplete="username"
            />
          </div>

          <div className="driver-login-field">
            <label htmlFor="drv-pass">Contraseña</label>
            <input
              id="drv-pass"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              autoComplete="current-password"
            />
          </div>

          <button type="submit" className="driver-login-btn" disabled={loading}>
            <LogIn size={18} />
            {loading ? "Ingresando..." : "Iniciar Sesión"}
          </button>

          <div className="driver-login-hint">
            <small>Default: <strong>admin</strong> / <strong>admin123</strong></small>
          </div>
        </form>
      </div>
    </div>
  );
}
