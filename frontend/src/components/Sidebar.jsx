import { useState } from 'react';
import {
  LayoutDashboard,
  Package,
  Warehouse,
  ShoppingCart,
  TrendingUp,
  Brain,
  AlertTriangle,
  FlaskConical,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import './Sidebar.css';

const NAV_ITEMS = [
  { key: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { key: 'products', label: 'Products', icon: Package },
  { key: 'inventory', label: 'Inventory', icon: Warehouse },
  { key: 'orders', label: 'Orders', icon: ShoppingCart },
  { key: '_divider1', divider: true, label: 'AI Agents' },
  { key: 'forecast', label: 'Forecast', icon: TrendingUp },
  { key: 'rl', label: 'RL Agent', icon: Brain },
  { key: 'simulator', label: 'Simulator', icon: FlaskConical },
  { key: 'alerts', label: 'Alerts', icon: AlertTriangle },
];

export default function Sidebar({ activePage, onNavigate }) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
      {/* Brand */}
      <div className="sidebar-brand">
        <div className="brand-icon">
          <Brain size={22} />
        </div>
        {!collapsed && (
          <div className="brand-text">
            <span className="brand-name">InventoryAI</span>
            <span className="brand-sub">Smart System</span>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav">
        {NAV_ITEMS.map(({ key, label, icon: Icon, divider }) => {
          if (divider) {
            return !collapsed ? (
              <div key={key} className="nav-divider">{label}</div>
            ) : <div key={key} className="nav-divider-line" />;
          }
          return (
            <button
              key={key}
              id={`nav-${key}`}
              className={`nav-item ${activePage === key ? 'active' : ''}`}
              onClick={() => onNavigate(key)}
              title={label}
            >
              <Icon size={20} />
              {!collapsed && <span>{label}</span>}
              {activePage === key && <div className="active-indicator" />}
            </button>
          );
        })}
      </nav>

      {/* Collapse toggle */}
      <button
        className="collapse-btn"
        onClick={() => setCollapsed(!collapsed)}
        title={collapsed ? 'Expand' : 'Collapse'}
      >
        {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
      </button>
    </aside>
  );
}
