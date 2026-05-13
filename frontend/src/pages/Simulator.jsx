import { useState } from 'react';
import {
  FlaskConical, Play, Loader2, DollarSign, AlertTriangle,
  Target, Package, Lightbulb, RotateCcw,
} from 'lucide-react';
import {
  AreaChart, Area, LineChart, Line, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  Legend, ComposedChart,
} from 'recharts';
import axios from 'axios';

const API = 'http://localhost:8000/api';

/* ---------- Slider config ---------- */
const SLIDERS = [
  {
    key: 'demand_multiplier',
    label: 'Demand Change',
    icon: '📈',
    min: 0.5, max: 3.0, step: 0.05, default: 1.0,
    format: (v) => `${Math.round(v * 100)}%`,
    color: '#3b82f6',
    description: 'Simulates increase or decrease in customer demand',
  },
  {
    key: 'lead_time_multiplier',
    label: 'Supplier Delay',
    icon: '🚚',
    min: 0.5, max: 3.0, step: 0.05, default: 1.0,
    format: (v) => `${Math.round(v * 100)}%`,
    color: '#f59e0b',
    description: 'Simulates longer or shorter supplier lead times',
  },
  {
    key: 'holding_cost_multiplier',
    label: 'Holding Cost Factor',
    icon: '🏭',
    min: 0.5, max: 3.0, step: 0.05, default: 1.0,
    format: (v) => `${Math.round(v * 100)}%`,
    color: '#8b5cf6',
    description: 'Adjusts the per-unit daily storage expense',
  },
  {
    key: 'stockout_cost_multiplier',
    label: 'Stockout Cost Factor',
    icon: '⚠️',
    min: 0.5, max: 3.0, step: 0.05, default: 1.0,
    format: (v) => `${Math.round(v * 100)}%`,
    color: '#f43f5e',
    description: 'Adjusts the penalty cost for unmet demand',
  },
];

/* ---------- Custom Tooltip ---------- */
const ChartTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="sim-tooltip">
      <div className="sim-tooltip-label">Day {label}</div>
      {payload.map((p, i) => (
        <div key={i} className="sim-tooltip-row">
          <span className="sim-tooltip-dot" style={{ background: p.color }} />
          <span>{p.name}:</span>
          <strong>{typeof p.value === 'number' ? p.value.toFixed(1) : p.value}</strong>
        </div>
      ))}
    </div>
  );
};

/* ========== MAIN COMPONENT ========== */
export default function Simulator() {
  const [params, setParams] = useState(
    Object.fromEntries(SLIDERS.map(s => [s.key, s.default]))
  );
  const [days, setDays] = useState(60);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  /* Update a single slider value */
  const updateParam = (key, value) => {
    setParams(prev => ({ ...prev, [key]: parseFloat(value) }));
  };

  /* Reset all sliders to defaults */
  const resetParams = () => {
    setParams(Object.fromEntries(SLIDERS.map(s => [s.key, s.default])));
    setDays(60);
    setResult(null);
    setError('');
  };

  /* Run the simulation */
  const runSimulation = async () => {
    setLoading(true);
    setError('');
    try {
      const { data } = await axios.post(`${API}/simulate-scenario`, {
        ...params,
        simulation_days: days,
      });
      setResult(data);
    } catch (e) {
      const msg = e.response?.data?.detail || 'Simulation failed. Make sure the RL agent has been trained first.';
      setError(msg);
    }
    setLoading(false);
  };

  /* Compute cumulative cost for chart */
  const dailyWithCumulative = (result?.daily_breakdown || []).map((d, i, arr) => ({
    ...d,
    cumulative_cost: arr.slice(0, i + 1).reduce((s, x) => s + x.total_cost, 0),
  }));

  return (
    <div className="simulator-page">
      <div className="page-header">
        <h1>Scenario Simulator</h1>
        <p>Run what-if simulations using the trained RL agent — modify conditions and see how the policy performs</p>
      </div>

      {/* ===== CONTROL PANEL ===== */}
      <div className="sim-control-panel card">
        <div className="sim-panel-header">
          <div className="sim-panel-title">
            <FlaskConical size={20} />
            <span>Simulation Parameters</span>
          </div>
          <button className="btn btn-secondary btn-sm" onClick={resetParams} id="reset-params-btn">
            <RotateCcw size={14} /> Reset
          </button>
        </div>

        <div className="sim-sliders-grid">
          {SLIDERS.map(s => {
            const val = params[s.key];
            const pct = ((val - s.min) / (s.max - s.min)) * 100;
            const isModified = val !== s.default;
            return (
              <div key={s.key} className={`sim-slider-card ${isModified ? 'modified' : ''}`}>
                <div className="sim-slider-header">
                  <span className="sim-slider-icon">{s.icon}</span>
                  <span className="sim-slider-label">{s.label}</span>
                  <span
                    className="sim-slider-value"
                    style={{ color: isModified ? s.color : 'var(--text-secondary)' }}
                  >
                    {s.format(val)}
                  </span>
                </div>
                <p className="sim-slider-desc">{s.description}</p>
                <div className="sim-slider-track-wrapper">
                  <input
                    type="range"
                    id={`slider-${s.key}`}
                    min={s.min}
                    max={s.max}
                    step={s.step}
                    value={val}
                    onChange={e => updateParam(s.key, e.target.value)}
                    className="sim-slider"
                    style={{
                      '--slider-color': s.color,
                      '--slider-pct': `${pct}%`,
                    }}
                  />
                  <div className="sim-slider-range">
                    <span>{s.format(s.min)}</span>
                    <span>{s.format(s.max)}</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Days input + Run button */}
        <div className="sim-actions-row">
          <div className="sim-days-input">
            <label htmlFor="sim-days">Simulation Days</label>
            <input
              id="sim-days"
              type="number"
              className="input"
              min={10}
              max={120}
              value={days}
              onChange={e => setDays(Math.min(120, Math.max(10, parseInt(e.target.value) || 60)))}
              style={{ width: 100, textAlign: 'center' }}
            />
          </div>
          <button
            id="run-simulation-btn"
            className="btn btn-primary sim-run-btn"
            onClick={runSimulation}
            disabled={loading}
          >
            {loading ? (
              <><Loader2 size={16} className="spinning" /> Running Simulation…</>
            ) : (
              <><Play size={16} /> Run Simulation</>
            )}
          </button>
        </div>

        {error && (
          <div className="sim-error">
            <AlertTriangle size={14} /> {error}
          </div>
        )}
      </div>

      {/* ===== RESULTS ===== */}
      {result && (
        <div className="sim-results fadeIn">
          {/* KPI stat cards */}
          <div className="stat-cards">
            <div className="card stat-card blue">
              <div className="stat-icon"><DollarSign size={22} /></div>
              <div className="stat-value">${result.total_cost.toLocaleString()}</div>
              <div className="stat-label">Total Cost</div>
            </div>
            <div className="card stat-card rose">
              <div className="stat-icon"><AlertTriangle size={22} /></div>
              <div className="stat-value">{result.stockouts}</div>
              <div className="stat-label">Stockout Events</div>
            </div>
            <div className="card stat-card emerald">
              <div className="stat-icon"><Target size={22} /></div>
              <div className="stat-value">{result.service_level}%</div>
              <div className="stat-label">Service Level</div>
            </div>
            <div className="card stat-card amber">
              <div className="stat-icon"><Package size={22} /></div>
              <div className="stat-value">{result.average_inventory}</div>
              <div className="stat-label">Avg. Inventory</div>
            </div>
          </div>

          {/* Charts grid */}
          <div className="grid-2">
            {/* Cost Breakdown Chart */}
            <div className="card chart-container">
              <h3>Daily Cost Breakdown</h3>
              <ResponsiveContainer width="100%" height={280}>
                <AreaChart data={dailyWithCumulative}>
                  <defs>
                    <linearGradient id="gradHolding" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="gradShortage" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#f43f5e" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="gradOrdering" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="day" tick={{ fill: '#94a3b8', fontSize: 10 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip content={<ChartTooltip />} />
                  <Legend wrapperStyle={{ fontSize: 12, color: '#94a3b8' }} />
                  <Area type="monotone" dataKey="holding_cost" name="Holding $" stackId="1" stroke="#8b5cf6" fill="url(#gradHolding)" />
                  <Area type="monotone" dataKey="shortage_cost" name="Shortage $" stackId="1" stroke="#f43f5e" fill="url(#gradShortage)" />
                  <Area type="monotone" dataKey="ordering_cost" name="Ordering $" stackId="1" stroke="#f59e0b" fill="url(#gradOrdering)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            {/* Stock & Demand Chart */}
            <div className="card chart-container">
              <h3>Stock Level vs. Demand</h3>
              <ResponsiveContainer width="100%" height={280}>
                <ComposedChart data={result.daily_breakdown}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="day" tick={{ fill: '#94a3b8', fontSize: 10 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip content={<ChartTooltip />} />
                  <Legend wrapperStyle={{ fontSize: 12, color: '#94a3b8' }} />
                  <Area type="monotone" dataKey="stock" name="Stock" stroke="#3b82f6" fill="rgba(59,130,246,0.1)" strokeWidth={2} />
                  <Line type="monotone" dataKey="demand" name="Demand" stroke="#f59e0b" strokeWidth={1.5} dot={false} strokeDasharray="4 4" />
                  <Bar dataKey="shortage" name="Shortage" fill="rgba(244,63,94,0.5)" radius={[2, 2, 0, 0]} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Cumulative cost curve */}
          <div className="card chart-container mt-4">
            <h3>Cumulative Cost Over Time</h3>
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={dailyWithCumulative}>
                <defs>
                  <linearGradient id="gradCumCost" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#06b6d4" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="day" tick={{ fill: '#94a3b8', fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip content={<ChartTooltip />} />
                <Area type="monotone" dataKey="cumulative_cost" name="Cumulative Cost $" stroke="#06b6d4" fill="url(#gradCumCost)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* AI Recommendation */}
          <div className="sim-recommendation card mt-4">
            <div className="sim-rec-header">
              <div className="sim-rec-icon">
                <Lightbulb size={22} />
              </div>
              <h3>AI Recommendation</h3>
            </div>
            <div className="sim-rec-body">
              {result.recommendation.split('\n\n').map((paragraph, i) => (
                <p key={i}>{paragraph}</p>
              ))}
            </div>
          </div>
        </div>
      )}

      <style>{`
        .spinning { animation: spin 1s linear infinite; }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
}
