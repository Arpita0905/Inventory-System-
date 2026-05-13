import { useState, useEffect } from 'react';
import { Package, Warehouse, AlertTriangle, ShoppingCart, TrendingUp } from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from 'recharts';
import { fetchProducts, fetchAlerts, fetchOrderStats } from '../services/api';

const BAR_COLORS = ['#3b82f6', '#8b5cf6', '#06b6d4', '#10b981', '#f59e0b', '#f43f5e', '#ec4899', '#14b8a6', '#f97316', '#6366f1'];

export default function Dashboard() {
  const [products, setProducts] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([fetchProducts(), fetchAlerts(), fetchOrderStats()])
      .then(([prods, alts, sts]) => {
        setProducts(prods);
        setAlerts(alts);
        setStats(sts);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading">Loading dashboard…</div>;

  const totalValue = products.reduce((s, p) => s + (p.inventory?.current_stock || 0) * p.unit_cost, 0);
  const stockData = products.map(p => ({
    name: p.sku_code,
    stock: p.inventory?.current_stock || 0,
    max: p.inventory?.max_stock || 100,
  }));

  return (
    <div>
      <div className="page-header">
        <h1>Dashboard</h1>
        <p>Real-time overview of your inventory system</p>
      </div>

      {/* Stat Cards */}
      <div className="stat-cards">
        <div className="card stat-card blue">
          <div className="stat-icon"><Package size={22} /></div>
          <div className="stat-value">{products.length}</div>
          <div className="stat-label">Total SKUs</div>
        </div>
        <div className="card stat-card emerald">
          <div className="stat-icon"><TrendingUp size={22} /></div>
          <div className="stat-value">${totalValue.toLocaleString(undefined, { maximumFractionDigits: 0 })}</div>
          <div className="stat-label">Total Stock Value</div>
        </div>
        <div className="card stat-card amber">
          <div className="stat-icon"><AlertTriangle size={22} /></div>
          <div className="stat-value">{alerts.length}</div>
          <div className="stat-label">Low-Stock Alerts</div>
        </div>
        <div className="card stat-card rose">
          <div className="stat-icon"><ShoppingCart size={22} /></div>
          <div className="stat-value">{stats?.pending || 0}</div>
          <div className="stat-label">Pending Orders</div>
        </div>
      </div>

      {/* Charts row */}
      <div className="grid-2">
        {/* Stock levels chart */}
        <div className="card chart-container">
          <h3>Stock Levels by SKU</h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={stockData} barCategoryGap="20%">
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{
                  background: '#1e293b',
                  border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: 8,
                  fontSize: 13,
                }}
              />
              <Bar dataKey="stock" radius={[4, 4, 0, 0]}>
                {stockData.map((_, i) => (
                  <Cell key={i} fill={BAR_COLORS[i % BAR_COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Order Stats */}
        <div className="card chart-container">
          <h3>Order Statistics</h3>
          {stats && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16, marginTop: 8 }}>
              {[
                { label: 'Total Orders', value: stats.total_orders, color: 'var(--accent-blue)' },
                { label: 'Pending', value: stats.pending, color: 'var(--accent-amber)' },
                { label: 'In Transit', value: stats.in_transit, color: 'var(--accent-cyan)' },
                { label: 'Delivered', value: stats.delivered, color: 'var(--accent-emerald)' },
                { label: 'Total Units Ordered', value: stats.total_units_ordered, color: 'var(--accent-purple)' },
              ].map(({ label, value, color }) => (
                <div key={label} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px', background: 'var(--bg-glass)', borderRadius: 8, border: '1px solid var(--border-glass)' }}>
                  <span style={{ color: 'var(--text-secondary)', fontSize: 14 }}>{label}</span>
                  <span style={{ color, fontSize: 22, fontWeight: 700 }}>{value}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Low Stock Alerts */}
      {alerts.length > 0 && (
        <div className="card mt-4" style={{ padding: 24 }}>
          <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
            <AlertTriangle size={18} color="var(--accent-amber)" /> Low-Stock Alerts
          </h3>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>SKU</th>
                  <th>Product</th>
                  <th>Current Stock</th>
                  <th>Reorder Point</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {alerts.map(a => {
                  const pct = a.current_stock / a.reorder_point;
                  const severity = pct <= 0.5 ? 'critical' : 'low';
                  return (
                    <tr key={a.id}>
                      <td style={{ fontFamily: 'monospace', fontSize: 13 }}>{a.product?.sku_code}</td>
                      <td>{a.product?.name}</td>
                      <td>{a.current_stock}</td>
                      <td>{a.reorder_point}</td>
                      <td><span className={`badge stock-${severity}`}>{severity === 'critical' ? '⚠ Critical' : '⚡ Low'}</span></td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
