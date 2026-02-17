import { createContext, useState, useContext, useEffect, useCallback, useRef } from "react";
import { API_BASE } from "../config";

const API = API_BASE;
const INACTIVITY_LIMIT_MS = 30 * 60 * 1000; // 30 min auto-logout

const AuthContext = createContext(null);

/* ── helpers ── */
function parseJwtPayload(token) {
  try {
    const base64 = token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
    return JSON.parse(atob(base64));
  } catch { return null; }
}

function isTokenExpired(token) {
  const p = parseJwtPayload(token);
  if (!p?.exp) return true;
  return Date.now() / 1000 > p.exp - 30; // 30 s margin
}

/* ── secure fetch wrapper — auto-logout on 401 ── */
function createSecureFetch(tokenRef, doLogout) {
  return async (url, opts = {}) => {
    const headers = { ...(opts.headers || {}) };
    if (tokenRef.current) headers["Authorization"] = `Bearer ${tokenRef.current}`;
    const res = await fetch(url, { ...opts, headers });
    if (res.status === 401) { doLogout(); throw new Error("Session expired"); }
    return res;
  };
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => {
    const t = localStorage.getItem("token");
    if (t && isTokenExpired(t)) { localStorage.removeItem("token"); return null; }
    return t;
  });
  const [loading, setLoading] = useState(true);
  const tokenRef = useRef(token);

  useEffect(() => {
    tokenRef.current = token;
  }, [token]);

  /* ── Forced logout ── */
  const logout = useCallback(() => {
    localStorage.removeItem("token");
    setToken(null);
    setUser(null);
  }, []);

  /* ── Secure fetch exposed to consumers ── */
  const secureFetch = useCallback(
    (url, opts) => createSecureFetch(tokenRef, logout)(url, opts),
    [logout]
  );

  /* ── Validate token on mount / token change ── */
  useEffect(() => {
    if (!token) {
      const id = setTimeout(() => setLoading(false), 0);
      return () => clearTimeout(id);
    }
    if (isTokenExpired(token)) {
      const id = setTimeout(() => {
        logout();
        setLoading(false);
      }, 0);
      return () => clearTimeout(id);
    }

    fetch(`${API}/api/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => {
        if (!res.ok) { logout(); return null; }
        return res.json();
      })
      .then((data) => { if (data) setUser(data); })
      .catch(() => logout())
      .finally(() => setLoading(false));
  }, [token, logout]);

  /* ── Inactivity auto-logout ── */
  useEffect(() => {
    if (!token) return;
    let timer;
    const reset = () => {
      clearTimeout(timer);
      timer = setTimeout(logout, INACTIVITY_LIMIT_MS);
    };
    const events = ["mousedown", "keydown", "scroll", "touchstart"];
    events.forEach((e) => window.addEventListener(e, reset, { passive: true }));
    reset();
    return () => {
      clearTimeout(timer);
      events.forEach((e) => window.removeEventListener(e, reset));
    };
  }, [token, logout]);

  /* ── Token expiry watchdog (check every 60 s) ── */
  useEffect(() => {
    if (!token) return;
    const id = setInterval(() => {
      if (isTokenExpired(token)) logout();
    }, 60_000);
    return () => clearInterval(id);
  }, [token, logout]);

  /* ── Login ── */
  const login = async (username, password) => {
    const formData = new FormData();
    formData.append("username", username);
    formData.append("password", password);

    const res = await fetch(`${API}/api/auth/login`, {
      method: "POST",
      body: formData,
    });

    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail || "Login failed");
    }

    const data = await res.json();
    localStorage.setItem("token", data.access_token);
    setToken(data.access_token);
    setUser(data.user);
    return data;
  };

  return (
    <AuthContext.Provider value={{ user, token, login, logout, loading, secureFetch, API }}>
      {children}
    </AuthContext.Provider>
  );
};

// eslint-disable-next-line react-refresh/only-export-components
export const useAuth = () => useContext(AuthContext);
