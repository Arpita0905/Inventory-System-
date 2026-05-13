import { useState, useEffect } from 'react';
import { Brain, Play, CheckCircle, TrendingDown, Target, Loader2 } from 'lucide-react';
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend, Cell, ComposedChart, Area,
} from 'recharts';
import axios from 'axios';

const API = 'http://localhost:8000/api';

export default function RLOptimization() {
  const [results, setResults] = useState(null);
  const [training, setTraining] = useState(false);
  const [status, setStatus] = useState('idle');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadResults();
  }, []);

  const loadResults = async () => {
    try {
      const { data } = await axios.get(`${API}/rl/results`);
      setResults(data);
      setStatus('complete');
    } catch {
      setResults(null);
    }
    setLoading(false);
  };

  const startTraining = async () => {
    setTraining(true);
    setStatus('training');
    try {
      await axios.post(`${API}/rl/train?episodes=200`);
      // Poll for completion
      const poll = setInterval(async () => {
        try {
          const { data } = await axios.get(`${API}/rl/status`);
          if (data.status === 'complete') {
            clearInterval(poll);
            await loadResults();
            setTraining(false);
          }
        } catch { /* keep polling */ }
      }, 2000);
    } catch (e) {
      setTraining(false);
      setStatus('error');
    }
  };

  if (loading) return <div className="loading">Loading RL results…</div>;

  // Prepare chart data
  const learningCurve = results?.learning_curve?.filter((_, i) => i % 2 === 0) || [];
  const costComparison = results ? [
    { name: 'RL Agent', cost: results.rl_avg_cost_last50, fill: '#3b82f6' },
    { name: 'Baseline (s,S)', cost: results.baseline_avg_cost, fill: '#f43f5e' },
  ] : [];
  const episodeSimulation = results?.final_episode || [];

  return (
    <div>
      <div className="page-header">
        <h1>RL Inventory Optimization</h1>
        <p>Deep Q-Network agent for cost-minimized restocking decisions</p>
      </div>

      {/* Training button */}
      <div className="toolbar">
        <button
          id="train-rl-btn"
          className="btn btn-primary"
          onClick={startTraining}
          disabled={training}
          style={{ minWidth: 180 }}
        >
          {training ? <><Loader2 size={16} className="spinning" /> Training…</>
            : <><Play size={16} /> {results ? 'Retrain Agent' : 'Train Agent'}</>}
        </button>
        {results && (
          <span style={{ color: 'var(--accent-emerald)', fontSize: 13, display: 'flex', alignItems: 'center', gap: 6 }}>
            <CheckCircle size={14} /> {results.episodes_trained} episodes trained
          </span>
        )}
      </div>

      {!results ? (
        <div className="card" style={{ padding: 60, textAlign: 'center' }}>
          <Brain size={48} style={{ color: 'var(--text-muted)', marginBottom: 16 }} />
          <h3 style={{ color: 'var(--text-secondary)', marginBottom: 8 }}>No Training Results Yet</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: 14 }}>
            Click "Train Agent" to start the DQN reinforcement learning training.
            The agent will learn optimal restocking policies over 200 episodes.
          </p>
        </div>
      ) : (
        <>
          {/* Performance Summary */}
          <div className="stat-cards">
            <div className="card stat-card blue">
              <div className="stat-icon"><Brain size={22} /></div>
              <div className="stat-value">${results.rl_avg_cost_last50}</div>
              <div className="stat-label">RL Agent Avg. Cost</div>
            </div>
            <div className="card stat-card rose">
              <div className="stat-icon"><Target size={22} /></div>
              <div className="stat-value">${results.baseline_avg_cost}</div>
              <div className="stat-label">Baseline (s,S) Cost</div>
            </div>
            <div className="card stat-card emerald">
              <div className="stat-icon"><TrendingDown size={22} /></div>
              <div className="stat-value">{results.cost_reduction_pct}%</div>
              <div className="stat-label">Cost Reduction</div>
            </div>
            <div className="card stat-card amber">
              <div className="stat-icon"><CheckCircle size={22} /></div>
              <div className="stat-value">{results.service_level}%</div>
              <div className="stat-label">Service Level</div>
            </div>
          </div>

          <div className="grid-2">
            {/* Learning Curve */}
            <div className="card chart-container">
              <h3>Learning Curve (Cost per Episode)</h3>
              <ResponsiveContainer width="100%" height={280}>
                <ComposedChart data={learningCurve}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="episode" tick={{ fill: '#94a3b8', fontSize: 10 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip
                    contentStyle={{ background: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, fontSize: 13 }}
                  />
                  <Area dataKey="total_cost" stroke="none" fill="rgba(59,130,246,0.15)" />
                  <Line dataKey="total_cost" stroke="#3b82f6" strokeWidth={1.5} dot={false} name="Episode Cost" />
                </ComposedChart>
              </ResponsiveContainer>
            </div>

            {/* Cost Comparison */}
            <div className="card chart-container">
              <h3>RL Agent vs. Baseline Cost</h3>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={costComparison} barCategoryGap="40%">
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 12 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} label={{ value: 'Avg Cost ($)', angle: -90, position: 'insideLeft', fill: '#64748b', fontSize: 12 }} />
                  <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8 }} />
                  <Bar dataKey="cost" radius={[6, 6, 0, 0]}>
                    {costComparison.map((entry, i) => (
                      <Cell key={i} fill={entry.fill} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Exploration decay */}
          <div className="card chart-container mt-4">
            <h3>Exploration Decay (ε over Episodes)</h3>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={learningCurve}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="episode" tick={{ fill: '#94a3b8', fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} domain={[0, 1]} />
                <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8 }} />
                <Line dataKey="epsilon" stroke="#f59e0b" strokeWidth={2} dot={false} name="Epsilon" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Episode simulation */}
          {episodeSimulation.length > 0 && (
            <div className="card mt-4" style={{ padding: 24 }}>
              <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Final Episode Breakdown (Trained Agent)</h3>
              <div className="table-container" style={{ maxHeight: 300, overflowY: 'auto' }}>
                <table>
                  <thead>
                    <tr>
                      <th>Step</th>
                      <th>Stock</th>
                      <th>Demand</th>
                      <th>Fulfilled</th>
                      <th>Shortage</th>
                      <th>Ordered</th>
                      <th>Holding $</th>
                      <th>Shortage $</th>
                      <th>Order $</th>
                      <th>Total $</th>
                    </tr>
                  </thead>
                  <tbody>
                    {episodeSimulation.map(h => (
                      <tr key={h.step}>
                        <td>{h.step + 1}</td>
                        <td style={{ fontWeight: 600 }}>{h.stock_after}</td>
                        <td>{h.demand}</td>
                        <td style={{ color: 'var(--accent-emerald)' }}>{h.fulfilled}</td>
                        <td style={{ color: h.shortage > 0 ? 'var(--accent-rose)' : 'var(--text-muted)' }}>{h.shortage}</td>
                        <td style={{ color: h.order_placed > 0 ? 'var(--accent-blue)' : 'var(--text-muted)' }}>{h.order_placed}</td>
                        <td>${h.holding_cost}</td>
                        <td>${h.shortage_cost}</td>
                        <td>${h.ordering_cost}</td>
                        <td style={{ fontWeight: 600 }}>${h.total_cost}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}

      <style>{`
        .spinning { animation: spin 1s linear infinite; }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
}
