import { useState, useEffect } from 'react';
import { AlertTriangle, Bell, Shield, Truck, TrendingUp, RefreshCw } from 'lucide-react';
import axios from 'axios';

const API = 'http://localhost:8000/api';

const SEVERITY_CONFIG = {
  critical: { icon: AlertTriangle, color: 'var(--accent-rose)', bg: 'rgba(244,63,94,0.08)', border: 'rgba(244,63,94,0.2)' },
  warning: { icon: Bell, color: 'var(--accent-amber)', bg: 'rgba(245,158,11,0.08)', border: 'rgba(245,158,11,0.2)' },
  info: { icon: Shield, color: 'var(--accent-blue)', bg: 'rgba(59,130,246,0.08)', border: 'rgba(59,130,246,0.2)' },
};

const TYPE_ICON = {
  understock: AlertTriangle,
  overstock: TrendingUp,
  demand_spike: TrendingUp,
  supplier_delay: Truck,
};

export default function Alerts() {
  const [alerts, setAlerts] = useState([]);
  const [supplierMetrics, setSupplierMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState('');

  const load = () => {
    setLoading(true);
    Promise.all([
      axios.get(`${API}/agents/alerts`).then(r => r.data),
      axios.get(`${API}/agents/supplier/metrics`).then(r => r.data),
    ]).then(([alts, metrics]) => {
      setAlerts(alts);
      setSupplierMetrics(metrics);
    }).finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const processSupplier = async () => {
    await axios.post(`${API}/agents/supplier/process`);
    load();
  };

  const types = [...new Set(alerts.map(a => a.type))];
  const filtered = filterType ? alerts.filter(a => a.type === filterType) : alerts;
  const criticalCount = alerts.filter(a => a.severity === 'critical').length;
  const warningCount = alerts.filter(a => a.severity === 'warning').length;

  return (
    <div>
      <div className="page-header">
        <h1>AI Monitoring & Alerts</h1>
        <p>Real-time anomaly detection and risk management</p>
      </div>

      {/* Stats */}
      <div className="stat-cards">
        <div className="card stat-card rose">
          <div className="stat-icon"><AlertTriangle size={22} /></div>
          <div className="stat-value">{criticalCount}</div>
          <div className="stat-label">Critical Alerts</div>
        </div>
        <div className="card stat-card amber">
          <div className="stat-icon"><Bell size={22} /></div>
          <div className="stat-value">{warningCount}</div>
          <div className="stat-label">Warnings</div>
        </div>
        <div className="card stat-card blue">
          <div className="stat-icon"><Truck size={22} /></div>
          <div className="stat-value">{supplierMetrics?.delivery_rate || 0}%</div>
          <div className="stat-label">Supplier Reliability</div>
        </div>
        <div className="card stat-card emerald">
          <div className="stat-icon"><Shield size={22} /></div>
          <div className="stat-value">{supplierMetrics?.avg_lead_time_days || 0}d</div>
          <div className="stat-label">Avg. Lead Time</div>
        </div>
      </div>

      {/* Toolbar */}
      <div className="toolbar">
        <div className="filter-pills">
          <button className={`pill ${!filterType ? 'active' : ''}`} onClick={() => setFilterType('')}>
            All ({alerts.length})
          </button>
          {types.map(t => (
            <button key={t} className={`pill ${filterType === t ? 'active' : ''}`} onClick={() => setFilterType(t)}>
              {t.replace('_', ' ')} ({alerts.filter(a => a.type === t).length})
            </button>
          ))}
        </div>
        <div className="spacer" />
        <button className="btn btn-secondary" onClick={processSupplier}>
          <Truck size={14} /> Process Supplier
        </button>
        <button className="btn btn-secondary" onClick={load}>
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      {/* Alerts list */}
      {loading ? (
        <div className="loading">Scanning for alerts…</div>
      ) : filtered.length === 0 ? (
        <div className="card" style={{ padding: 48, textAlign: 'center' }}>
          <Shield size={48} style={{ color: 'var(--accent-emerald)', marginBottom: 16 }} />
          <h3 style={{ color: 'var(--text-secondary)', marginBottom: 8 }}>All Clear</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: 14 }}>No active alerts detected. All systems operating normally.</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {filtered.map((alert, i) => {
            const config = SEVERITY_CONFIG[alert.severity] || SEVERITY_CONFIG.info;
            const TypeIcon = TYPE_ICON[alert.type] || Bell;
            return (
              <div
                key={i}
                className="card"
                style={{
                  padding: '16px 20px',
                  background: config.bg,
                  borderColor: config.border,
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: 16,
                }}
              >
                <div style={{
                  width: 40, height: 40, borderRadius: 10,
                  background: `${config.color}22`,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  flexShrink: 0,
                }}>
                  <TypeIcon size={20} color={config.color} />
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                    <span className={`badge ${alert.severity === 'critical' ? 'stock-critical' : 'stock-low'}`}>
                      {alert.severity}
                    </span>
                    <span style={{ fontSize: 12, color: 'var(--text-muted)', fontFamily: 'monospace' }}>
                      {alert.sku_code}
                    </span>
                    <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                      {alert.type.replace('_', ' ')}
                    </span>
                  </div>
                  <p style={{ fontSize: 14, color: 'var(--text-primary)', fontWeight: 500 }}>{alert.message}</p>
                  <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>{alert.product_name}</p>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
