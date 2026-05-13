import { useState } from 'react';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import Products from './pages/Products';
import Inventory from './pages/Inventory';
import Orders from './pages/Orders';
import Forecast from './pages/Forecast';
import RLOptimization from './pages/RLOptimization';
import Alerts from './pages/Alerts';
import Simulator from './pages/Simulator';
import './index.css';

const PAGES = {
  dashboard: Dashboard,
  products: Products,
  inventory: Inventory,
  orders: Orders,
  forecast: Forecast,
  rl: RLOptimization,
  alerts: Alerts,
  simulator: Simulator,
};

function App() {
  const [page, setPage] = useState('dashboard');
  const Page = PAGES[page];

  return (
    <div className="app-layout">
      <Sidebar activePage={page} onNavigate={setPage} />
      <main className="main-content">
        <Page />
      </main>
    </div>
  );
}

export default App;
