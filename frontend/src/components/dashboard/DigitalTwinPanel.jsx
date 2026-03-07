import { memo } from "react";
import { Cpu, Activity, Wifi, Radio, Ambulance, Gauge, Fuel, Star, Route, Wrench, AlertCircle, AlertTriangle, TrendingUp, ChevronDown, ChevronUp, Eye, Sparkles, X } from "lucide-react";

const SCOLORS = { SVB: "#22c55e", SVA: "#ef4444", VIR: "#3b82f6", VAMM: "#f97316", SAMU: "#a855f7" };

function DigitalTwinPanel({
  twinPanelOpen, setTwinPanelOpen,
  fleetHealth,
  twinTelemetry, twinLoading,
  focusedVehicleId,
  whatIfResult, setWhatIfResult, whatIfLoading,
  runWhatIf,
}) {
  return (
    <div className="info-section twin-section">
      <div className="twin-header" onClick={() => setTwinPanelOpen(v => !v)}>
        <strong><Cpu size={16} className="icon-3d" /> Digital Twin</strong>
        <span className="twin-toggle-icon">{twinPanelOpen ? <ChevronUp size={14} /> : <ChevronDown size={14} />}</span>
      </div>

      {twinPanelOpen && (
        <div className="twin-body">
          {fleetHealth && (
            <div className="twin-fleet-health">
              <div className="twin-fleet-header">
                <Activity size={14} /> Salud de Flota
                <span className={`twin-health-badge ${fleetHealth.avg_health_score > 80 ? "good" : fleetHealth.avg_health_score > 50 ? "warn" : "crit"}`}>
                  {fleetHealth.avg_health_score}%
                </span>
              </div>
              <div className="twin-fleet-stats">
                <div className="twin-stat"><span>Vehículos</span><strong>{fleetHealth.fleet_size}</strong></div>
                <div className="twin-stat"><span>Anomalías</span><strong className={fleetHealth.total_anomalies > 0 ? "warn" : ""}>{fleetHealth.total_anomalies}</strong></div>
                <div className="twin-stat"><span>Links Inter-Twin</span><strong>{fleetHealth.inter_twin_links?.length || 0}</strong></div>
              </div>
              {fleetHealth.inter_twin_links?.length > 0 && (
                <div className="twin-links">
                  <div className="twin-links-title"><Wifi size={12} /> Comunicación Inter-Twin</div>
                  {fleetHealth.inter_twin_links.slice(0, 3).map((link, i) => (
                    <div key={i} className="twin-link-row">
                      <Radio size={11} />
                      <span>{link.from}</span>
                      <span className="twin-link-arrow">⟷</span>
                      <span>{link.to}</span>
                      <span className="twin-link-dist">{link.distance_m}m</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {focusedVehicleId ? (
            twinLoading && !twinTelemetry ? (
              <div className="twin-loading"><Activity size={14} className="sim-pulse" /> Cargando telemetría...</div>
            ) : twinTelemetry ? (
              <div className="twin-telemetry">
                <div className="twin-vehicle-header">
                  <Ambulance size={14} />
                  <strong>{twinTelemetry.vehicle_id}</strong>
                  <span className="subtype-tag" style={{ background: SCOLORS[twinTelemetry.subtype] || "#6b7280" }}>{twinTelemetry.subtype}</span>
                  <span className="twin-model-tag">{twinTelemetry.twin_metadata?.model}</span>
                </div>
                <div className="twin-health-gauge">
                  <div className="twin-gauge-label">Salud del Gemelo</div>
                  <div className="twin-gauge-bar">
                    <div className="twin-gauge-fill" style={{
                      width: `${twinTelemetry.maintenance?.health_score || 0}%`,
                      background: (twinTelemetry.maintenance?.health_score || 0) > 80 ? "#22c55e" : (twinTelemetry.maintenance?.health_score || 0) > 50 ? "#f59e0b" : "#ef4444",
                    }} />
                  </div>
                  <span className="twin-gauge-pct">{twinTelemetry.maintenance?.health_score || 0}%</span>
                </div>
                <div className="twin-kpi-grid">
                  <div className="twin-kpi"><Gauge size={13} /><span>{twinTelemetry.speed?.toFixed(0) || 0} km/h</span></div>
                  <div className="twin-kpi"><Fuel size={13} /><span>{twinTelemetry.fuel_pct?.toFixed(1)}% ({twinTelemetry.fuel_liters?.toFixed(0)}L)</span></div>
                  <div className="twin-kpi"><Star size={13} /><span>Trust: {twinTelemetry.trust_score}</span></div>
                  <div className="twin-kpi"><Route size={13} /><span>Autonomía: {twinTelemetry.maintenance?.estimated_range_km?.toFixed(0)} km</span></div>
                </div>
                <div className={`twin-maintenance ${twinTelemetry.maintenance?.maintenance_urgency === "HIGH" ? "urgent" : twinTelemetry.maintenance?.maintenance_urgency === "MEDIUM" ? "preventive" : "ok"}`}>
                  <Wrench size={13} /><span>{twinTelemetry.maintenance?.next_maintenance}</span>
                </div>
                <div className="twin-efficiency">
                  <span>Eficiencia: {twinTelemetry.maintenance?.efficiency_pct}%</span>
                  <span>Consumo: {twinTelemetry.maintenance?.consumption_rate_L100km} L/100km (esp: {twinTelemetry.maintenance?.expected_consumption})</span>
                </div>
                {twinTelemetry.anomalies?.length > 0 && (
                  <div className="twin-anomalies">
                    <div className="twin-anomalies-title"><AlertCircle size={13} /> Anomalías ({twinTelemetry.anomalies.length})</div>
                    {twinTelemetry.anomalies.map((a, i) => (
                      <div key={i} className={`twin-anomaly-row sev-${a.severity?.toLowerCase()}`}>
                        <AlertTriangle size={12} /><span>{a.message}</span>
                      </div>
                    ))}
                  </div>
                )}
                {twinTelemetry.telemetry_sparkline?.speeds?.length > 5 && (
                  <div className="twin-sparkline">
                    <div className="twin-spark-title"><TrendingUp size={12} /> Velocidad (últimos {twinTelemetry.telemetry_sparkline.speeds.length} ticks)</div>
                    <div className="twin-spark-bars">
                      {twinTelemetry.telemetry_sparkline.speeds.slice(-30).map((s, i) => {
                        const maxS = twinTelemetry.twin_metadata?.max_speed_kmh || 100;
                        return <div key={i} className="twin-spark-bar" style={{ height: `${Math.min(100, (s / maxS) * 100)}%` }} title={`${s?.toFixed(0)} km/h`} />;
                      })}
                    </div>
                  </div>
                )}
                <div className="twin-meta">
                  <Cpu size={11} /> <span>Tick: {twinTelemetry.twin_metadata?.tick_rate_ms}ms</span>
                  <span>·</span><span>Buffer: {twinTelemetry.twin_metadata?.history_depth} pts</span>
                  <span>·</span><span>×{twinTelemetry.speed_multiplier}</span>
                </div>
              </div>
            ) : null
          ) : (
            <div className="twin-empty"><Eye size={14} /> Selecciona un vehículo para ver su gemelo digital</div>
          )}

          <div className="twin-whatif">
            <div className="twin-whatif-title"><Sparkles size={13} /> Simulador "What-If"</div>
            <div className="twin-whatif-btns">
              <button className="twin-whatif-btn" onClick={() => runWhatIf("vehicle_breakdown", focusedVehicleId)} disabled={whatIfLoading}><Wrench size={12} /> Avería</button>
              <button className="twin-whatif-btn" onClick={() => runWhatIf("fuel_shortage")} disabled={whatIfLoading}><Fuel size={12} /> Combustible</button>
              <button className="twin-whatif-btn" onClick={() => runWhatIf("mass_casualty", null, { extra_incidents: 8 })} disabled={whatIfLoading}>🚨 Masivo</button>
              <button className="twin-whatif-btn" onClick={() => runWhatIf("road_closure", null, { lat: 40.42, lon: -3.70, radius_m: 1000 })} disabled={whatIfLoading}><AlertTriangle size={12} /> Corte vial</button>
            </div>
            {whatIfLoading && <div className="twin-loading"><Activity size={12} className="sim-pulse" /> Simulando escenario...</div>}
            {whatIfResult && !whatIfLoading && (
              <div className={`twin-whatif-result risk-${whatIfResult.risk_level?.toLowerCase()}`}>
                <div className="twin-whatif-result-header">
                  <strong>{whatIfResult.description}</strong>
                  <span className={`twin-risk-badge risk-${whatIfResult.risk_level?.toLowerCase()}`}>{whatIfResult.risk_level}</span>
                </div>
                <div className="twin-whatif-impact">
                  {Object.entries(whatIfResult.impact || {}).map(([k, v]) => (
                    <div key={k} className="twin-impact-row">
                      <span>{k.replace(/_/g, " ")}</span>
                      <strong>{typeof v === "boolean" ? (v ? "Sí" : "No") : v}</strong>
                    </div>
                  ))}
                </div>
                <div className="twin-whatif-recs">
                  {whatIfResult.recommendations?.map((r, i) => <div key={i} className="twin-rec-row">💡 {r}</div>)}
                </div>
                <button className="twin-whatif-close" onClick={() => setWhatIfResult(null)}><X size={12} /> Cerrar</button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default memo(DigitalTwinPanel);
