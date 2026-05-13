import { useState, useEffect } from 'react';
import { ShoppingCart, RefreshCw, Truck, CheckCircle, XCircle, Clock } from 'lucide-react';
import { fetchOrders, fetchProducts, createOrder, updateOrderStatus, fetchOrderStats } from '../services/api';

const STATUS_OPTIONS = ['pending', 'in_transit', 'delivered', 'cancelled'];

export default function Orders() {
  const [orders, setOrders] = useState([]);
  const [products, setProducts] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState('');
  const [showReorder, setShowReorder] = useState(false);
  const [reorderForm, setReorderForm] = useState({ product_id: '', quantity: 20 });

  const load = () => {
    setLoading(true);
    Promise.all([
      fetchOrders(filterStatus ? { status: filterStatus } : {}),
      fetchProducts(),
      fetchOrderStats(),
    ]).then(([ords, prods, sts]) => {
      setOrders(ords);
      setProducts(prods);
      setStats(sts);
    }).finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, [filterStatus]);

  const handleReorder = async (e) => {
    e.preventDefault();
    await createOrder({
      product_id: Number(reorderForm.product_id),
      quantity: Number(reorderForm.quantity),
      order_type: 'manual',
    });
    setShowReorder(false);
    setReorderForm({ product_id: '', quantity: 20 });
    load();
  };

  const handleStatusChange = async (orderId, newStatus) => {
    await updateOrderStatus(orderId, newStatus);
    load();
  };

  const statusIcon = (s) => {
    switch(s) {
      case 'pending': return <Clock size={14} />;
      case 'in_transit': return <Truck size={14} />;
      case 'delivered': return <CheckCircle size={14} />;
      case 'cancelled': return <XCircle size={14} />;
      default: return null;
    }
  };

  const fmtDate = (d) => d ? new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : '—';

  return (
    <div>
      <div className="page-header">
        <h1>Orders</h1>
        <p>Track purchase orders and restock shipments</p>
      </div>

      {/* Stats */}
      {stats && (
        <div className="stat-cards">
          <div className="card stat-card blue">
            <div className="stat-icon"><ShoppingCart size={22} /></div>
            <div className="stat-value">{stats.total_orders}</div>
            <div className="stat-label">Total Orders</div>
          </div>
          <div className="card stat-card amber">
            <div className="stat-icon"><Clock size={22} /></div>
            <div className="stat-value">{stats.pending}</div>
            <div className="stat-label">Pending</div>
          </div>
          <div className="card stat-card emerald">
            <div className="stat-icon"><Truck size={22} /></div>
            <div className="stat-value">{stats.in_transit}</div>
            <div className="stat-label">In Transit</div>
          </div>
          <div className="card stat-card rose">
            <div className="stat-icon"><CheckCircle size={22} /></div>
            <div className="stat-value">{stats.delivered}</div>
            <div className="stat-label">Delivered</div>
          </div>
        </div>
      )}

      {/* Toolbar */}
      <div className="toolbar">
        <div className="filter-pills">
          <button className={`pill ${!filterStatus ? 'active' : ''}`} onClick={() => setFilterStatus('')}>All</button>
          {STATUS_OPTIONS.map(s => (
            <button key={s} className={`pill ${filterStatus === s ? 'active' : ''}`} onClick={() => setFilterStatus(s)}>
              {s.replace('_', ' ')}
            </button>
          ))}
        </div>
        <div className="spacer" />
        <button className="btn btn-secondary" onClick={load}><RefreshCw size={14} /> Refresh</button>
        <button id="place-reorder-btn" className="btn btn-primary" onClick={() => setShowReorder(true)}>
          <ShoppingCart size={16} /> Place Reorder
        </button>
      </div>

      {/* Orders table */}
      <div className="card">
        {loading ? (
          <div className="loading">Loading orders…</div>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Order #</th>
                  <th>Product</th>
                  <th>Quantity</th>
                  <th>Type</th>
                  <th>Status</th>
                  <th>Lead Time</th>
                  <th>Ordered</th>
                  <th>Delivered</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {orders.map(o => (
                  <tr key={o.id}>
                    <td style={{ fontFamily: 'monospace', fontWeight: 600 }}>#{String(o.id).padStart(4, '0')}</td>
                    <td style={{ fontWeight: 500 }}>{o.product?.name || `Product #${o.product_id}`}</td>
                    <td>{o.quantity} units</td>
                    <td><span className="badge" style={{ background: 'var(--bg-glass)', color: 'var(--text-secondary)', textTransform: 'capitalize' }}>{o.order_type}</span></td>
                    <td>
                      <span className={`badge ${o.status}`} style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                        {statusIcon(o.status)} {o.status.replace('_', ' ')}
                      </span>
                    </td>
                    <td>{o.lead_time_days} days</td>
                    <td style={{ fontSize: 13 }}>{fmtDate(o.ordered_at)}</td>
                    <td style={{ fontSize: 13 }}>{fmtDate(o.delivered_at)}</td>
                    <td>
                      {o.status !== 'delivered' && o.status !== 'cancelled' && (
                        <select
                          className="input"
                          style={{ width: 120, padding: '4px 8px', fontSize: 12 }}
                          value=""
                          onChange={e => handleStatusChange(o.id, e.target.value)}
                        >
                          <option value="" disabled>Update…</option>
                          {STATUS_OPTIONS.filter(s => s !== o.status).map(s => (
                            <option key={s} value={s}>{s.replace('_', ' ')}</option>
                          ))}
                        </select>
                      )}
                    </td>
                  </tr>
                ))}
                {orders.length === 0 && (
                  <tr><td colSpan={9} className="text-center" style={{ padding: 32, color: 'var(--text-muted)' }}>No orders found</td></tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Reorder Modal */}
      {showReorder && (
        <div className="modal-overlay" onClick={() => setShowReorder(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h2>Place Reorder</h2>
            <form onSubmit={handleReorder}>
              <div className="form-group">
                <label>Product</label>
                <select className="input" value={reorderForm.product_id} onChange={e => setReorderForm({ ...reorderForm, product_id: e.target.value })} required>
                  <option value="" disabled>Select product…</option>
                  {products.map(p => (
                    <option key={p.id} value={p.id}>{p.sku_code} – {p.name}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>Quantity</label>
                <input className="input" type="number" min="1" value={reorderForm.quantity} onChange={e => setReorderForm({ ...reorderForm, quantity: e.target.value })} required />
              </div>
              <div className="modal-actions">
                <button type="button" className="btn btn-secondary" onClick={() => setShowReorder(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Place Order</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
