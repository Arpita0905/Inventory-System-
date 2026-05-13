import { useState, useEffect } from 'react';
import { TrendingUp, BarChart3, Calendar, Zap } from 'lucide-react';
import {
  AreaChart, Area, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend, ComposedChart, Bar,
} from 'recharts';
import { fetchProducts } from '../services/api';
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

export default function Forecast() {
  const [products, setProducts] = useState([]);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [forecastData, setForecastData] = useState(null);
  const [demandSummary, setDemandSummary] = useState([]);
  const [periods, setPeriods] = useState(30);
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetchProducts(),
      axios.get(`${API_BASE}/forecast/`).then(r => r.data),
    ]).then(([prods, summary]) => {
      setProducts(prods);
      setDemandSummary(summary);
      if (prods.length > 0) {
        setSelectedProduct(prods[0]);
        loadForecast(prods[0].id, periods);
      }
    }).finally(() => setInitialLoading(false));
  }, []);

  const loadForecast = async (productId, numPeriods) => {
    setLoading(true);
    try {
      const { data } = await axios.get(`${API_BASE}/forecast/${productId}?periods=${numPeriods}`);
      setForecastData(data);
    } catch (e) {
      console.error('Forecast error:', e);
      setForecastData(null);
    }
    setLoading(false);
  };

  const handleProductChange = (e) => {
    const prod = products.find(p => p.id === Number(e.target.value));
    setSelectedProduct(prod);
    loadForecast(prod.id, periods);
  };

  const handlePeriodsChange = (e) => {
    const newPeriods = Number(e.target.value);
    setPeriods(newPeriods);
    if (selectedProduct) loadForecast(selectedProduct.id, newPeriods);
  };

  if (initialLoading) return <div className="loading">Loading forecast data…</div>;

  // Merge history and forecast into one chart dataset
  const chartData = forecastData ? [
    ...forecastData.history.map(h => ({
      date: h.date,
      actual: h.actual,
      predicted: null,
      lower: null,
      upper: null,
    })),
    // Bridge point: last history point connects to first forecast point
    ...(forecastData.forecast.length > 0 ? [{
      date: forecastData.history[forecastData.history.length - 1]?.date,
      actual: forecastData.history[forecastData.history.length - 1]?.actual,
      predicted: forecastData.forecast[0]?.predicted,
      lower: forecastData.forecast[0]?.lower,
      upper: forecastData.forecast[0]?.upper,
    }] : []),
    ...forecastData.forecast.map(f => ({
      date: f.date,
      actual: null,
      predicted: f.predicted,
      lower: f.lower,
      upper: f.upper,
    })),
  ] : [];

  // Confidence band data for area chart
  const bandData = forecastData?.forecast.map(f => ({
    date: f.date,
    band: [f.lower, f.upper],
    predicted: f.predicted,
  })) || [];

  return (
    <div>
      <div className="page-header">
        <h1>Demand Forecasting</h1>
        <p>AI-powered demand predictions with confidence intervals</p>
      </div>

      {/* Controls */}
      <div className="toolbar">
        <div className="form-group" style={{ marginBottom: 0, minWidth: 220 }}>
          <label>Select Product</label>
          <select
            id="forecast-product-select"
            className="input"
            value={selectedProduct?.id || ''}
            onChange={handleProductChange}
          >
            {products.map(p => (
              <option key={p.id} value={p.id}>{p.sku_code} – {p.name}</option>
            ))}
          </select>
        </div>
        <div className="form-group" style={{ marginBottom: 0, minWidth: 160 }}>
          <label>Forecast Horizon</label>
          <select className="input" value={periods} onChange={handlePeriodsChange}>
            <option value={7}>7 days</option>
            <option value={14}>14 days</option>
            <option value={30}>30 days</option>
            <option value={60}>60 days</option>
            <option value={90}>90 days</option>
          </select>
        </div>
      </div>

      {/* Summary Stats */}
      {forecastData?.summary && (
        <div className="stat-cards">
          <div className="card stat-card blue">
            <div className="stat-icon"><TrendingUp size={22} /></div>
            <div className="stat-value">{forecastData.summary.avg_daily_demand}</div>
            <div className="stat-label">Avg. Daily Demand</div>
          </div>
          <div className="card stat-card emerald">
            <div className="stat-icon"><BarChart3 size={22} /></div>
            <div className="stat-value">{forecastData.summary.total_forecasted?.toLocaleString()}</div>
            <div className="stat-label">Total Forecasted ({periods}d)</div>
          </div>
          <div className="card stat-card amber">
            <div className="stat-icon"><Calendar size={22} /></div>
            <div className="stat-value">{forecastData.summary.peak_date}</div>
            <div className="stat-label">Peak Demand Date</div>
          </div>
          <div className="card stat-card rose">
            <div className="stat-icon"><Zap size={22} /></div>
            <div className="stat-value">{forecastData.summary.peak_value}</div>
            <div className="stat-label">Peak Daily Demand</div>
          </div>
        </div>
      )}

      {/* Main forecast chart */}
      <div className="card chart-container" style={{ minHeight: 420 }}>
        <h3>
          Historical Demand & Forecast
          {selectedProduct && <span style={{ color: 'var(--text-muted)', fontWeight: 400, fontSize: 14, marginLeft: 8 }}>
            – {selectedProduct.sku_code}
          </span>}
        </h3>
        {loading ? (
          <div className="loading">Generating forecast…</div>
        ) : chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={360}>
            <ComposedChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="gradientBlue" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="gradientPurple" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.25} />
                  <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis
                dataKey="date"
                tick={{ fill: '#94a3b8', fontSize: 10 }}
                axisLine={false}
                tickLine={false}
                interval={Math.floor(chartData.length / 10)}
                tickFormatter={d => {
                  const dt = new Date(d);
                  return `${dt.getMonth() + 1}/${dt.getDate()}`;
                }}
              />
              <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{
                  background: '#1e293b',
                  border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: 8,
                  fontSize: 13,
                }}
                labelFormatter={d => new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
              />
              <Legend />
              {/* Confidence band */}
              <Area
                dataKey="upper"
                stroke="none"
                fill="url(#gradientPurple)"
                name="Upper Bound"
                dot={false}
                activeDot={false}
              />
              <Area
                dataKey="lower"
                stroke="none"
                fill="var(--bg-primary)"
                name="Lower Bound"
                dot={false}
                activeDot={false}
              />
              {/* Actual demand */}
              <Line
                dataKey="actual"
                stroke="#3b82f6"
                strokeWidth={2}
                dot={false}
                name="Actual Demand"
                connectNulls={false}
              />
              {/* Predicted demand */}
              <Line
                dataKey="predicted"
                stroke="#8b5cf6"
                strokeWidth={2}
                strokeDasharray="6 3"
                dot={false}
                name="Forecasted"
                connectNulls={false}
              />
            </ComposedChart>
          </ResponsiveContainer>
        ) : (
          <div className="text-center" style={{ padding: 40, color: 'var(--text-muted)' }}>
            No forecast data available
          </div>
        )}
      </div>

      {/* Demand Summary Table */}
      <div className="card mt-4" style={{ padding: 24 }}>
        <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>
          30-Day Demand Summary (All Products)
        </h3>
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>SKU</th>
                <th>Product</th>
                <th>Total Demand (30d)</th>
                <th>Avg. Daily</th>
                <th>Data Points</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {demandSummary.map(s => (
                <tr key={s.product_id}>
                  <td style={{ fontFamily: 'monospace', fontSize: 13, color: 'var(--accent-blue)' }}>{s.sku_code}</td>
                  <td style={{ fontWeight: 500 }}>{s.name}</td>
                  <td style={{ fontWeight: 600 }}>{s.total_demand_30d}</td>
                  <td>{s.avg_daily_demand}</td>
                  <td>{s.data_points}</td>
                  <td>
                    <button
                      className="btn btn-sm btn-secondary"
                      onClick={() => {
                        const prod = products.find(p => p.id === s.product_id);
                        setSelectedProduct(prod);
                        loadForecast(s.product_id, periods);
                        window.scrollTo({ top: 0, behavior: 'smooth' });
                      }}
                    >
                      View Forecast
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
