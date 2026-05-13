import { useState, useEffect } from 'react';
import { Plus, Pencil, Trash2, Search } from 'lucide-react';
import { fetchProducts, createProduct, updateProduct, deleteProduct } from '../services/api';

const CATEGORIES = ['All', 'Electronics', 'Groceries', 'Apparel', 'Miscellaneous'];

export default function Products() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('All');
  const [modal, setModal] = useState(null); // null | 'add' | product obj

  const load = () => {
    setLoading(true);
    fetchProducts(category === 'All' ? null : category)
      .then(setProducts)
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, [category]);

  const filtered = products.filter(p =>
    p.name.toLowerCase().includes(search.toLowerCase()) ||
    p.sku_code.toLowerCase().includes(search.toLowerCase())
  );

  const handleSave = async (data) => {
    if (modal && modal.id) {
      await updateProduct(modal.id, data);
    } else {
      await createProduct(data);
    }
    setModal(null);
    load();
  };

  const handleDelete = async (id) => {
    if (!confirm('Delete this product?')) return;
    await deleteProduct(id);
    load();
  };

  return (
    <div>
      <div className="page-header">
        <h1>Products</h1>
        <p>Manage your SKU catalog</p>
      </div>

      <div className="toolbar">
        <div style={{ position: 'relative' }}>
          <Search size={16} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
          <input
            id="product-search"
            className="input search-input"
            placeholder="Search products…"
            value={search}
            onChange={e => setSearch(e.target.value)}
            style={{ paddingLeft: 36, width: 280 }}
          />
        </div>
        <div className="filter-pills">
          {CATEGORIES.map(c => (
            <button key={c} className={`pill ${category === c ? 'active' : ''}`} onClick={() => setCategory(c)}>{c}</button>
          ))}
        </div>
        <div className="spacer" />
        <button id="add-product-btn" className="btn btn-primary" onClick={() => setModal('add')}>
          <Plus size={16} /> Add Product
        </button>
      </div>

      <div className="card">
        {loading ? (
          <div className="loading">Loading products…</div>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>SKU Code</th>
                  <th>Name</th>
                  <th>Category</th>
                  <th>Unit Cost</th>
                  <th>Stock</th>
                  <th>Holding Cost</th>
                  <th>Shortage Cost</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {filtered.map(p => (
                  <tr key={p.id}>
                    <td style={{ fontFamily: 'monospace', fontSize: 13, color: 'var(--accent-blue)' }}>{p.sku_code}</td>
                    <td style={{ fontWeight: 500 }}>{p.name}</td>
                    <td><span className="badge" style={{ background: 'var(--bg-glass)', color: 'var(--text-secondary)' }}>{p.category}</span></td>
                    <td>${p.unit_cost.toFixed(2)}</td>
                    <td>{p.inventory?.current_stock ?? '—'}</td>
                    <td>${p.holding_cost_per_unit.toFixed(2)}</td>
                    <td>${p.shortage_cost_per_unit.toFixed(2)}</td>
                    <td>
                      <div className="action-btns">
                        <button className="action-btn" title="Edit" onClick={() => setModal(p)}><Pencil size={14} /></button>
                        <button className="action-btn delete" title="Delete" onClick={() => handleDelete(p.id)}><Trash2 size={14} /></button>
                      </div>
                    </td>
                  </tr>
                ))}
                {filtered.length === 0 && (
                  <tr><td colSpan={8} className="text-center" style={{ padding: 32, color: 'var(--text-muted)' }}>No products found</td></tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Add / Edit Modal */}
      {modal && <ProductModal product={modal === 'add' ? null : modal} onSave={handleSave} onClose={() => setModal(null)} />}
    </div>
  );
}

function ProductModal({ product, onSave, onClose }) {
  const [form, setForm] = useState({
    sku_code: product?.sku_code || '',
    name: product?.name || '',
    category: product?.category || 'Electronics',
    unit_cost: product?.unit_cost || '',
    holding_cost_per_unit: product?.holding_cost_per_unit || 0.5,
    shortage_cost_per_unit: product?.shortage_cost_per_unit || 2.0,
    ordering_cost: product?.ordering_cost || 25.0,
    current_stock: product?.inventory?.current_stock || 0,
    reorder_point: product?.inventory?.reorder_point || 20,
    safety_stock: product?.inventory?.safety_stock || 10,
    max_stock: product?.inventory?.max_stock || 200,
  });

  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value });

  const handleSubmit = (e) => {
    e.preventDefault();
    const data = { ...form, unit_cost: Number(form.unit_cost), holding_cost_per_unit: Number(form.holding_cost_per_unit), shortage_cost_per_unit: Number(form.shortage_cost_per_unit), ordering_cost: Number(form.ordering_cost), current_stock: Number(form.current_stock), reorder_point: Number(form.reorder_point), safety_stock: Number(form.safety_stock), max_stock: Number(form.max_stock) };

    // If editing, only send updatable fields
    if (product) {
      const { sku_code, current_stock, reorder_point, safety_stock, max_stock, ...rest } = data;
      onSave(rest);
    } else {
      onSave(data);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <h2>{product ? 'Edit Product' : 'Add New Product'}</h2>
        <form onSubmit={handleSubmit}>
          {!product && (
            <div className="form-group">
              <label>SKU Code</label>
              <input className="input" value={form.sku_code} onChange={set('sku_code')} required placeholder="e.g. ELEC-004" />
            </div>
          )}
          <div className="form-group">
            <label>Product Name</label>
            <input className="input" value={form.name} onChange={set('name')} required />
          </div>
          <div className="grid-2">
            <div className="form-group">
              <label>Category</label>
              <select className="input" value={form.category} onChange={set('category')}>
                {['Electronics', 'Groceries', 'Apparel', 'Miscellaneous'].map(c => <option key={c}>{c}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label>Unit Cost ($)</label>
              <input className="input" type="number" step="0.01" value={form.unit_cost} onChange={set('unit_cost')} required />
            </div>
          </div>
          <div className="grid-2">
            <div className="form-group">
              <label>Holding Cost / Unit</label>
              <input className="input" type="number" step="0.01" value={form.holding_cost_per_unit} onChange={set('holding_cost_per_unit')} />
            </div>
            <div className="form-group">
              <label>Shortage Cost / Unit</label>
              <input className="input" type="number" step="0.01" value={form.shortage_cost_per_unit} onChange={set('shortage_cost_per_unit')} />
            </div>
          </div>
          {!product && (
            <div className="grid-2">
              <div className="form-group">
                <label>Initial Stock</label>
                <input className="input" type="number" value={form.current_stock} onChange={set('current_stock')} />
              </div>
              <div className="form-group">
                <label>Reorder Point</label>
                <input className="input" type="number" value={form.reorder_point} onChange={set('reorder_point')} />
              </div>
            </div>
          )}
          <div className="modal-actions">
            <button type="button" className="btn btn-secondary" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn btn-primary">{product ? 'Update' : 'Create'}</button>
          </div>
        </form>
      </div>
    </div>
  );
}
