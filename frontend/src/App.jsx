import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { lazy, Suspense } from "react";
import { AuthProvider, useAuth } from "./context/AuthContext";
import ErrorBoundary from "./components/ErrorBoundary";
import LoadingFallback from "./components/LoadingFallback";
import Layout from "./components/Layout";
import "./App.css";

/* ── Lazy-loaded pages (code-splitting) ── */
const Login = lazy(() => import("./pages/Login"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const IncidentList = lazy(() => import("./pages/IncidentList"));
const CreateIncident = lazy(() => import("./pages/CreateIncident"));
const Analytics = lazy(() => import("./pages/Analytics"));
const AIInsights = lazy(() => import("./pages/AIInsights"));
const AuditLog = lazy(() => import("./pages/AuditLog"));
const KPIs = lazy(() => import("./pages/KPIs"));
const CrewManagement = lazy(() => import("./pages/CrewManagement"));
const HospitalDashboard = lazy(() => import("./pages/HospitalDashboard"));
const ParamedicView = lazy(() => import("./pages/ParamedicView"));
const PatientTracking = lazy(() => import("./pages/PatientTracking"));
const DriverMobile = lazy(() => import("./pages/DriverMobile"));
const DriverLogin = lazy(() => import("./pages/DriverLogin"));
const SecurityDashboard = lazy(() => import("./pages/SecurityDashboard"));

function PrivateRoute({ children }) {
  const { user, loading } = useAuth();

  if (loading) {
    return <div className="loading-screen">Cargando...</div>;
  }

  return user ? children : <Navigate to="/login" />;
}

function RoleRoute({ children, roles }) {
  const { user } = useAuth();

  if (!roles || roles.includes(user?.role)) return children;

  return <Navigate to="/" replace />;
}

function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <BrowserRouter>
          <Suspense fallback={<LoadingFallback />}>
            <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/"
            element={
              <PrivateRoute>
                <Layout>
                  <Dashboard />
                </Layout>
              </PrivateRoute>
            }
          />
          <Route
            path="/incidents"
            element={
              <PrivateRoute>
                <Layout>
                  <IncidentList />
                </Layout>
              </PrivateRoute>
            }
          />
          <Route
            path="/create-incident"
            element={
              <PrivateRoute>
                <RoleRoute roles={["ADMIN"]}>
                  <Layout>
                    <CreateIncident />
                  </Layout>
                </RoleRoute>
              </PrivateRoute>
            }
          />
          <Route
            path="/analytics"
            element={
              <PrivateRoute>
                <Layout>
                  <Analytics />
                </Layout>
              </PrivateRoute>
            }
          />
          <Route
            path="/ai-insights"
            element={
              <PrivateRoute>
                <RoleRoute roles={["ADMIN", "OPERATOR"]}>
                  <Layout>
                    <AIInsights />
                  </Layout>
                </RoleRoute>
              </PrivateRoute>
            }
          />
          <Route
            path="/audit-log"
            element={
              <PrivateRoute>
                <RoleRoute roles={["ADMIN"]}>
                  <Layout>
                    <AuditLog />
                  </Layout>
                </RoleRoute>
              </PrivateRoute>
            }
          />
          <Route
            path="/kpis"
            element={
              <PrivateRoute>
                <Layout>
                  <KPIs />
                </Layout>
              </PrivateRoute>
            }
          />
          <Route
            path="/crew"
            element={
              <PrivateRoute>
                <RoleRoute roles={["ADMIN", "OPERATOR"]}>
                  <Layout>
                    <CrewManagement />
                  </Layout>
                </RoleRoute>
              </PrivateRoute>
            }
          />
          <Route
            path="/hospital-dashboard"
            element={
              <PrivateRoute>
                <RoleRoute roles={["ADMIN", "OPERATOR"]}>
                  <Layout>
                    <HospitalDashboard />
                  </Layout>
                </RoleRoute>
              </PrivateRoute>
            }
          />
          <Route
            path="/paramedic"
            element={
              <PrivateRoute>
                <RoleRoute roles={["ADMIN", "OPERATOR", "DOCTOR"]}>
                  <Layout>
                    <ParamedicView />
                  </Layout>
                </RoleRoute>
              </PrivateRoute>
            }
          />
          <Route
            path="/patient-tracking"
            element={
              <PrivateRoute>
                <RoleRoute roles={["ADMIN", "OPERATOR", "DOCTOR"]}>
                  <Layout>
                    <PatientTracking />
                  </Layout>
                </RoleRoute>
              </PrivateRoute>
            }
          />
          <Route
            path="/driver"
            element={
              <PrivateRoute>
                <DriverMobile />
              </PrivateRoute>
            }
          />
          <Route path="/driver-login" element={<DriverLogin />} />
          <Route
            path="/security"
            element={
              <PrivateRoute>
                <RoleRoute roles={["ADMIN"]}>
                  <Layout>
                    <SecurityDashboard />
                  </Layout>
                </RoleRoute>
              </PrivateRoute>
            }
          />
            </Routes>
          </Suspense>
        </BrowserRouter>
      </AuthProvider>
    </ErrorBoundary>
  );
}

export default App;
