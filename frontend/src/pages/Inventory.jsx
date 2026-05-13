import { useState, useEffect } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import { fetchInventory, updateInventory } from '../services/api';

export default function Inventory() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState(null);
  const [editStock, setEditStock] = useState('');

  const load = () => {
    setLoading(true);
    fetchInventory().then(setItems).finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const getStockStatus = (item) => {
    if (item.current_stock <= item.safety_stock) return 'critical';
    if (item.current_stock <= item.reorder_point) return 'low';
    return 'ok';
  };

  const getStockLabel = (s) => {
    if (s === 'critical') return '⚠ Critical';
    if (s === 'low') return '⚡ Low';
    return '✓ OK';
  };

  const handleStockUpdate = async (productId) => {
    await updateInventory(productId, { current_stock: Number(editStock) });
    setEditingId(null);
    load();
  };

  return (
    <div>
      <div className="page-header">
        <h1>Inventory</h1>
        <p>Monitor stock levels across all SKUs</p>
      </div>

      {/* Summary cards */}
      <div className="stat-cards" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
        <div className="card stat-card emerald">
          <div className="stat-icon">✓</div>
          <div className="stat-value">{items.filter(i => getStockStatus(i) === 'ok').length}</div>
          <div className="stat-label">Healthy Stock</div>
        </div>
        <div className="card stat-card amber">
          <div className="stat-icon">⚡</div>
          <div className="stat-value">{items.filter(i => getStockStatus(i) === 'low').length}</div>
          <div className="stat-label">Low Stock</div>
        </div>
        <div className="card stat-card rose">
          <div className="stat-icon">⚠</div>
          <div className="stat-value">{items.filter(i => getStockStatus(i) === 'critical').length}</div>
          <div className="stat-label">Critical Stock</div>
        </div>
      </div>

      <div className="toolbar">
        <button className="btn btn-secondary" onClick={load}><RefreshCw size={14} /> Refresh</button>
      </div>

      <div className="card">
        {loading ? (
          <div className="loading">Loading inventory…</div>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>SKU</th>
                  <th>Product</th>
                  <th>Current Stock</th>
                  <th>Stock Level</th>
                  <th>Reorder Point</th>
                  <th>Safety Stock</th>
                  <th>Max Stock</th>
                  <th>Status</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {items.map(item => {
                  const status = getStockStatus(item);
                  const pct = Math.min((item.current_stock / item.max_stock) * 100, 100);
                  return (
                    <tr key={item.id}>
                      <td style={{ fontFamily: 'monospace', fontSize: 13, color: 'var(--accent-blue)' }}>{item.product?.sku_code}</td>
                      <td style={{ fontWeight: 500 }}>{item.product?.name}</td>
                      <td>
                        {editingId === item.product_id ? (
                          <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                            <input
                              className="input"
                              type="number"
                              value={editStock}
                              onChange={e => setEditStock(e.target.value)}
                              style={{ width: 80, padding: '4px 8px' }}
                              autoFocus
                            />
                            <button className="btn btn-primary btn-sm" onClick={() => handleStockUpdate(item.product_id)}>Save</button>
                            <button className="btn btn-secondary btn-sm" onClick={() => setEditingId(null)}>✕</button>
                          </div>
                        ) : (
                          <span style={{ fontWeight: 600, fontSize: 16 }}>{item.current_stock}</span>
                        )}
                      </td>
                      <td style={{ minWidth: 120 }}>
                        <div className="stock-bar">
                          <div className={`stock-bar-fill ${status}`} style={{ width: `${pct}%` }} />
                        </div>
                        <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{pct.toFixed(0)}% of max</span>
                      </td>
                      <td>{item.reorder_point}</td>
                      <td>{item.safety_stock}</td>
                      <td>{item.max_stock}</td>
                      <td><span className={`badge stock-${status}`}>{getStockLabel(status)}</span></td>
                      <td>
                        <button
                          className="action-btn"
                          title="Adjust stock"
                          onClick={() => { setEditingId(item.product_id); setEditStock(String(item.current_stock)); }}
                        >
                          <RefreshCw size={14} />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
