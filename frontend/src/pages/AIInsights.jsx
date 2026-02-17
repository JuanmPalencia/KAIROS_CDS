// frontend/src/pages/AIInsights.jsx
import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Brain, BarChart3, Flame, MapPin, AlertTriangle, Wrench, MessageCircle, Ambulance, User, Bot, TrendingUp, Sparkles, CheckCircle, Hospital, Pencil } from 'lucide-react';
import { API_BASE as API_BASE_URL } from '../config';
import './AIInsights.css';

const AIInsights = () => {
  const { token } = useAuth();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [loading, setLoading] = useState(false);
  
  // Dashboard data
  const [dashboardData, setDashboardData] = useState(null);
  const [hotspots, setHotspots] = useState([]);
  const [anomalies, setAnomalies] = useState([]);
  const [systemHealth, setSystemHealth] = useState(null);
  const [maintenance, setMaintenance] = useState(null);
  
  // Chat
  const [messages, setMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  
  // User profile
  const [userProfile, setUserProfile] = useState(null);
  
  const API_BASE = API_BASE_URL + '/api';
  
  useEffect(() => {
    if (activeTab === 'dashboard') {
      loadDashboard();
    } else if (activeTab === 'chat') {
      // Chat ya se carga cuando se envía mensaje
    } else if (activeTab === 'profile') {
      loadProfile();
    }
  }, [activeTab, token]);
  
  const loadDashboard = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/ai/insights/dashboard`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setDashboardData(data);
        setHotspots(data.hotspots || []);
        setSystemHealth(data.system_health);
      }
    } catch (error) {
      console.error('Error loading AI dashboard:', error);
    }
    setLoading(false);
  };
  
  const loadAnomalies = async () => {
    try {
      const [vehicleRes, systemRes] = await Promise.all([
        fetch(`${API_BASE}/ai/anomalies/vehicles`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${API_BASE}/ai/anomalies/system-health`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
      ]);
      
      if (vehicleRes.ok) {
        const data = await vehicleRes.json();
        setAnomalies(data.anomalies || []);
      }
      
      if (systemRes.ok) {
        const health = await systemRes.json();
        setSystemHealth(health);
      }
    } catch (error) {
      console.error('Error loading anomalies:', error);
    }
  };
  
  const loadMaintenance = async () => {
    try {
      const response = await fetch(`${API_BASE}/ai/maintenance/fleet-schedule`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setMaintenance(data);
      }
    } catch (error) {
      console.error('Error loading maintenance:', error);
    }
  };
  
  const sendMessage = async () => {
    if (!chatInput.trim()) return;
    
    const userMessage = { role: 'user', content: chatInput };
    setMessages(prev => [...prev, userMessage]);
    setChatInput('');
    setLoading(true);
    
    try {
      const response = await fetch(`${API_BASE}/ai/chat`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message: chatInput })
      });
      
      if (response.ok) {
        const data = await response.json();
        const assistantMessage = { role: 'assistant', content: data.response };
        setMessages(prev => [...prev, assistantMessage]);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = { role: 'assistant', content: 'Error al procesar tu mensaje' };
      setMessages(prev => [...prev, errorMessage]);
    }
    setLoading(false);
  };
  
  const loadProfile = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/ai/recommendations/profile`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setUserProfile(data);
      }
    } catch (error) {
      console.error('Error loading profile:', error);
    }
    setLoading(false);
  };
  
  const renderDashboard = () => (
    <div className="ai-dashboard">
      <h2><Brain size={24} className="icon-3d" /> AI Dashboard</h2>
      
      {loading ? (
        <div className="loading">Cargando...</div>
      ) : dashboardData ? (
        <>
          {/* System Health */}
          {systemHealth && (
            <div className="health-card">
              <h3><BarChart3 size={20} className="icon-3d" /> Salud del Sistema</h3>
              <div className={`health-score health-${systemHealth.status.toLowerCase()}`}>
                <div className="score-value">{systemHealth.overall_score}</div>
                <div className="score-label">{systemHealth.status}</div>
              </div>
              <div className="health-metrics">
                <div>Salud Vehículos: {systemHealth.vehicle_health}%</div>
                <div>Salud Incidentes: {systemHealth.incident_health}%</div>
                <div>Anomalías: {systemHealth.anomaly_count}</div>
              </div>
            </div>
          )}
          
          {/* Hotspots */}
          {hotspots.length > 0 && (
            <div className="hotspots-card">
              <h3><Flame size={20} className="icon-3d" /> Hotspots de Demanda</h3>
              <div className="hotspots-list">
                {hotspots.map((spot, idx) => (
                  <div key={idx} className="hotspot-item">
                    <div className="hotspot-location">
                      <MapPin size={14} /> {spot.lat.toFixed(4)}, {spot.lon.toFixed(4)}
                    </div>
                    <div className="hotspot-severity">
                      Severidad: {spot.severity} ({(spot.probability * 100).toFixed(0)}%)
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {/* Quick Actions */}
          <div className="quick-actions">
            <button onClick={loadAnomalies} className="action-btn">
              <AlertTriangle size={16} /> Ver Anomalías
            </button>
            <button onClick={loadMaintenance} className="action-btn">
              <Wrench size={16} /> Ver Mantenimiento
            </button>
            <button onClick={() => setActiveTab('chat')} className="action-btn primary">
              <MessageCircle size={16} /> Hablar con IA
            </button>
          </div>

          {/* Anomalies Section */}
          {anomalies.length > 0 && (
            <div className="hotspots-card">
              <h3><AlertTriangle size={20} className="icon-3d" /> Anomalías Detectadas</h3>
              <div className="hotspots-list">
                {anomalies.map((a, idx) => (
                  <div key={idx} className="hotspot-item" style={{
                    borderLeft: `4px solid ${a.severity === 'HIGH' ? '#ef4444' : a.severity === 'MEDIUM' ? '#f59e0b' : '#3b82f6'}`
                  }}>
                    <div className="hotspot-location">
                      <strong>{a.vehicle_id || a.type || 'Anomalía'}</strong>
                    </div>
                    <div className="hotspot-severity">
                      {a.description || a.message || JSON.stringify(a)}
                    </div>
                    <div style={{fontSize: '0.8em', color: 'var(--text-muted, #888)', marginTop: '4px'}}>
                      Severidad: {a.severity || 'N/A'} | Score: {a.anomaly_score != null ? a.anomaly_score.toFixed(2) : 'N/A'}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Maintenance Section */}
          {maintenance && (
            <div className="hotspots-card">
              <h3><Wrench size={20} className="icon-3d" /> Plan de Mantenimiento</h3>
              <div className="hotspots-list">
                {(maintenance.schedule || maintenance.predictions || []).map((m, idx) => (
                  <div key={idx} className="hotspot-item" style={{
                    borderLeft: `4px solid ${m.urgency === 'HIGH' || m.priority === 'HIGH' ? '#ef4444' : m.urgency === 'MEDIUM' || m.priority === 'MEDIUM' ? '#f59e0b' : '#10b981'}`
                  }}>
                    <div className="hotspot-location">
                      <strong><Ambulance size={14} /> {m.vehicle_id}</strong>
                    </div>
                    <div className="hotspot-severity">
                      {m.recommendation || m.action || m.type || 'Mantenimiento programado'}
                    </div>
                    <div style={{fontSize: '0.8em', color: 'var(--text-muted, #888)', marginTop: '4px'}}>
                      {m.urgency || m.priority || 'NORMAL'} {m.next_maintenance ? `| Próximo: ${m.next_maintenance}` : ''}
                      {m.estimated_days != null ? ` | En ${m.estimated_days} días` : ''}
                    </div>
                  </div>
                ))}
                {(!maintenance.schedule && !maintenance.predictions) && (
                  <div className="hotspot-item">
                    <pre style={{fontSize: '0.85em', margin: 0, whiteSpace: 'pre-wrap'}}>{JSON.stringify(maintenance, null, 2)}</pre>
                  </div>
                )}
              </div>
            </div>
          )}
        </>
      ) : (
        <div className="empty">No hay datos disponibles</div>
      )}
    </div>
  );
  
  const renderChat = () => (
    <div className="ai-chat">
      <h2><MessageCircle size={24} className="icon-3d" /> Asistente IA KAIROS</h2>
      
      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="chat-welcome">
            <h3>¡Hola! Soy tu asistente IA</h3>
            <p>Puedo ayudarte con:</p>
            <ul>
              <li><BarChart3 size={14} /> Consultar estado de la flota</li>
              <li><AlertTriangle size={14} /> Crear y gestionar incidentes</li>
              <li><Hospital size={14} /> Información de hospitales</li>
              <li><TrendingUp size={14} /> Análisis y métricas</li>
              <li><Sparkles size={14} /> Predicciones de demanda</li>
            </ul>
          </div>
        )}
        
        {messages.map((msg, idx) => (
          <div key={idx} className={`message message-${msg.role}`}>
            <div className="message-icon">
              {msg.role === 'user' ? <User size={18} /> : <Bot size={18} />}
            </div>
            <div className="message-content">{msg.content}</div>
          </div>
        ))}
        
        {loading && (
          <div className="message message-assistant">
            <div className="message-icon"><Bot size={18} /></div>
            <div className="message-content typing">Escribiendo...</div>
          </div>
        )}
      </div>
      
      <div className="chat-input-container">
        <input
          type="text"
          className="chat-input"
          placeholder="Escribe tu mensaje..."
          value={chatInput}
          onChange={(e) => setChatInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
          disabled={loading}
        />
        <button 
          onClick={sendMessage} 
          className="chat-send-btn"
          disabled={loading || !chatInput.trim()}
        >
          Enviar
        </button>
      </div>
    </div>
  );
  
  const renderProfile = () => (
    <div className="ai-profile">
      <h2><User size={24} className="icon-3d" /> Perfil de Operador</h2>
      
      {loading ? (
        <div className="loading">Cargando perfil...</div>
      ) : userProfile ? (
        <>
          {/* Profile Stats */}
          <div className="profile-stats">
            <div className="stat-card">
              <div className="stat-value">{userProfile.profile.experience_level}</div>
              <div className="stat-label">Nivel de Experiencia</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{userProfile.profile.total_decisions}</div>
              <div className="stat-label">Casos Gestionados</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">
                {(userProfile.profile.ai_acceptance_rate * 100).toFixed(0)}%
              </div>
              <div className="stat-label">Concordancia con IA</div>
            </div>
          </div>
          
          {/* Performance Insights */}
          {userProfile.learning && (
            <div className="learning-section">
              <h3><BarChart3 size={20} className="icon-3d" /> Análisis de Desempeño</h3>
              
              {/* Strengths */}
              {userProfile.learning.strengths.length > 0 && (
                <div className="strengths">
                  <h4><CheckCircle size={16} /> Puntos Fuertes</h4>
                  <ul>
                    {userProfile.learning.strengths.map((s, idx) => (
                      <li key={idx}>{s}</li>
                    ))}
                  </ul>
                </div>
              )}
              
              {/* Preferred Hospitals */}
              {userProfile.profile.preferred_hospitals && userProfile.profile.preferred_hospitals.length > 0 && (
                <div className="strengths">
                  <h4><Hospital size={16} /> Hospitales Frecuentes</h4>
                  <ul>
                    {userProfile.profile.preferred_hospitals.slice(0, 3).map((h, idx) => (
                      <li key={idx}>{h}</li>
                    ))}
                  </ul>
                </div>
              )}
              
              {/* Override Reasons */}
              {userProfile.profile.common_override_reasons && userProfile.profile.common_override_reasons.length > 0 && (
                <div className="strengths">
                  <h4><Pencil size={16} /> Razones de Override Comunes</h4>
                  <ul>
                    {userProfile.profile.common_override_reasons.slice(0, 3).map((r, idx) => (
                      <li key={idx}>{r}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </>
      ) : (
        <div className="empty">No hay datos de perfil disponibles</div>
      )}
    </div>
  );
  
  return (
    <div className="ai-insights-container">
      <div className="ai-header">
        <h1><Bot size={28} className="icon-3d" /> AI Insights & Assistant</h1>
        <p>Inteligencia Artificial integrada en KAIROS</p>
      </div>
      
      <div className="ai-tabs">
        <button 
          className={activeTab === 'dashboard' ? 'tab active' : 'tab'}
          onClick={() => setActiveTab('dashboard')}
        >
          <BarChart3 size={16} /> Dashboard
        </button>
        <button 
          className={activeTab === 'chat' ? 'tab active' : 'tab'}
          onClick={() => setActiveTab('chat')}
        >
          <MessageCircle size={16} /> Chat IA
        </button>
        <button 
          className={activeTab === 'profile' ? 'tab active' : 'tab'}
          onClick={() => setActiveTab('profile')}
        >
          <User size={16} /> Mi Perfil
        </button>
      </div>
      
      <div className="ai-content">
        {activeTab === 'dashboard' && renderDashboard()}
        {activeTab === 'chat' && renderChat()}
        {activeTab === 'profile' && renderProfile()}
      </div>
    </div>
  );
};

export default AIInsights;
