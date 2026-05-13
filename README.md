# 🧠 Smart Autonomous Inventory Management System

A **Multi-AI-Agent** inventory management system that uses Deep Reinforcement Learning (DQN), Holt-Winters demand forecasting, anomaly detection, and interactive scenario simulation for autonomous single-warehouse optimization — trained and evaluated on **real-world supply chain data** from the DataCo SMART Supply Chain dataset.

## 📊 Key Results

| Metric | Value |
|--------|-------|
| **Service Level** | 99.9% |
| **Cost Reduction vs (s,S)** | 31.7% |
| **Dataset** | DataCo SMART Supply Chain (180K+ real orders) |
| **Products** | 20 SKUs across multiple categories |
| **RL Agent** | DQN with experience replay, trained 200+ episodes |
| **Forecast Model** | Holt-Winters Triple Exponential Smoothing |

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     React Frontend (Vite)                     │
│  Dashboard │ Products │ Inventory │ Orders                    │
│  Forecast  │ RL Agent │ Simulator │ Alerts                    │
├─────────────────────────────────────────────────────────────┤
│                     FastAPI Backend                            │
│  CRUD APIs │ Forecast API │ RL API │ Simulation API           │
│  Agents API │ Scenario Engine                                 │
├─────────────────────────────────────────────────────────────┤
│                      AI Agents                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ Demand       │  │ DQN RL       │  │ Scenario         │   │
│  │ Forecast     │  │ Agent        │  │ Simulator        │   │
│  │ (Holt-       │  │ (Deep Q-     │  │ (What-If         │   │
│  │  Winters)    │  │  Network)    │  │  Analysis)       │   │
│  └──────────────┘  └──────────────┘  └──────────────────┘   │
│  ┌──────────────┐  ┌──────────────┐                          │
│  │ Supplier     │  │ Monitoring   │                          │
│  │ Simulation   │  │ & Alert      │                          │
│  │ Agent        │  │ Agent        │                          │
│  └──────────────┘  └──────────────┘                          │
├─────────────────────────────────────────────────────────────┤
│             SQLite Database (SQLAlchemy ORM)                  │
│  Products │ Inventory │ Orders │ DemandHistory                │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

```bash
# 1. Backend
cd backend
pip install -r requirements.txt

# Load real-world DataCo supply chain data
python load_dataco.py

# Start API server
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# 2. Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 (Frontend) • http://localhost:8000/docs (API Docs)

## 📦 Dataset

The system uses the **DataCo SMART Supply Chain Dataset** (Constante et al., 2019) from Mendeley/Kaggle:
- **180,519 real-world orders** from an actual supply chain company
- **20 product SKUs** across categories (Apparel, Sports, Electronics, etc.)
- Real demand patterns with **mean demand ~46.3 units/day**, **std ~15.4**
- Real lead times averaging **~3.6 days**
- Historical order data spanning 2015-2018

The `load_dataco.py` script processes the raw CSV and maps it to products, demand history, inventory records, and orders in the database.

## 🤖 AI Agents

### 1. Demand Forecasting Agent
- **Model**: Holt-Winters Triple Exponential Smoothing (additive seasonality)
- **Data**: Real DataCo demand history per product
- **Output**: Daily predictions with 95% confidence intervals
- **Horizon**: Configurable from 7 to 90 days
- **API**: `GET /api/forecast/{sku_id}?periods=30`

### 2. RL Inventory Optimization Agent
- **Algorithm**: Deep Q-Network (DQN) with experience replay
- **Architecture**: 3-layer neural network (5→128→64→25), pure NumPy implementation
- **State Space**: 5D normalized vector [stock, pending orders, demand mean, lead time, days of supply]
- **Action Space**: 25 discrete order quantities (0 to 500 units)
- **Training**: Data-driven — pulls real demand statistics from DB for environment calibration
- **Results**: 99.9% service level, 31.7% cost reduction vs (s,S) baseline
- **Reward Shaping**: +15 fulfillment bonus, -8/unit shortage penalty, +3 buffer bonus
- **API**: `POST /api/rl/train` • `GET /api/rl/results`

### 3. Scenario Simulator (NEW)
- **Purpose**: What-if analysis for inventory managers — test the trained RL policy under modified conditions WITHOUT retraining
- **Features**:
  - Configurable simulation days (1-365)
  - Demand multiplier (0.5x to 3x) — simulate demand surges/drops
  - Lead time multiplier (0.5x to 5x) — simulate supplier disruptions
  - Cost multiplier (0.5x to 5x) — simulate cost inflation
- **Metrics**: Total cost, stockout events, service level, avg inventory
- **Charts**: Daily cost breakdown (holding/ordering/shortage), Stock vs Demand timeline
- **AI Recommendation**: Automatic text-based analysis of simulation results
- **API**: `POST /api/simulate-scenario`

### 4. Supplier Simulation Agent
- Simulates stochastic supplier behavior with random lead time variability
- Processes pending orders and tracks delivery reliability
- Models 15% delivery delay probability with 1-3 day additional delays
- **API**: `POST /api/agents/supplier/process` • `GET /api/agents/supplier/metrics`

### 5. Monitoring & Alert Agent
- **Anomaly Types**: Understock, Overstock, Demand Spikes (z-score), Supplier Delays
- Real-time risk assessment with severity levels (critical/warning)
- Smart filtering: Only checks recent orders (last 90 days) to avoid false alerts from historical data
- **API**: `GET /api/agents/alerts`

## 📊 Frontend Pages

| Page | Description |
|------|-------------|
| **Dashboard** | KPI cards (20 SKUs, $1.7M stock value), stock bar chart, order statistics |
| **Products** | CRUD product management with search/filters, real DataCo brands |
| **Inventory** | Stock levels with visual health bars, safety stock, reorder points |
| **Orders** | Order tracking with status management (Pending/In Transit/Delivered) |
| **Forecast** | Holt-Winters demand prediction chart with confidence bands |
| **RL Agent** | Training controls, learning curve, cost comparison vs baseline |
| **Simulator** | ⭐ What-if scenario engine with demand/lead-time/cost multipliers |
| **Alerts** | Severity-coded alerts, supplier reliability metrics, filter pills |

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------:|
| Backend | Python 3.10+, FastAPI, SQLAlchemy, Pydantic |
| AI/ML | NumPy (DQN), statsmodels (Holt-Winters), SciPy |
| Database | SQLite (portable, migrateable to PostgreSQL) |
| Dataset | DataCo SMART Supply Chain (Kaggle/Mendeley) |
| Frontend | React 18, Vite 5, Recharts, Lucide Icons |
| Styling | Custom CSS, Dark Theme, Glassmorphism |

## 📁 Project Structure

```
inventory-ai-system/
├── backend/
│   ├── main.py                  # FastAPI entry point
│   ├── database.py              # SQLAlchemy config
│   ├── models.py                # ORM models (Product, Inventory, Order, DemandHistory)
│   ├── schemas.py               # Pydantic schemas
│   ├── seed.py                  # Database seeder
│   ├── load_dataco.py           # DataCo real-world dataset loader
│   ├── demand_generator.py      # Synthetic demand fallback
│   ├── scenario_engine.py       # What-if simulation engine
│   ├── routers/
│   │   ├── products.py          # Product CRUD
│   │   ├── inventory.py         # Stock management
│   │   ├── orders.py            # Order management
│   │   ├── forecast.py          # Forecast API
│   │   ├── rl.py                # RL training API
│   │   ├── simulation.py        # Scenario simulation API
│   │   └── agents.py            # Multi-agent API
│   └── ai_models/
│       ├── forecasting/
│       │   └── forecast_engine.py   # Holt-Winters implementation
│       ├── rl_agent/
│       │   ├── inventory_env.py     # Gym-style environment
│       │   ├── dqn_agent.py         # DQN neural network (pure NumPy)
│       │   └── trainer.py           # Data-driven training runner
│       ├── agents/
│       │   ├── supplier_agent.py    # Supplier simulation
│       │   └── monitoring_agent.py  # Anomaly detection & alerts
│       └── saved_models/
│           ├── dqn_weights.json     # Trained model weights
│           ├── env_params.json      # Environment parameters
│           └── rl_results.json      # Training results history
└── frontend/
    └── src/
        ├── App.jsx
        ├── index.css                # Dark theme design system
        ├── pages/
        │   ├── Dashboard.jsx
        │   ├── Products.jsx
        │   ├── Inventory.jsx
        │   ├── Orders.jsx
        │   ├── Forecast.jsx
        │   ├── RLOptimization.jsx
        │   ├── Simulator.jsx        # What-if scenario simulator
        │   └── Alerts.jsx
        ├── components/
        │   └── Sidebar.jsx
        └── services/
            └── api.js               # API client

research_paper.md                    # Full academic research paper
```

## 📚 Key References

1. **Oroojlooyjadid et al. (2022)** — "A Deep Q-Network for the Beer Game: Deep Reinforcement Learning for Inventory Optimization," *M&SOM*, 24(1), 285-304. → *DQN architecture design for our RL agent*

2. **Gijsbrechts et al. (2022)** — "Can Deep Reinforcement Learning Improve Inventory Management?," *M&SOM*, 24(3), 1349-1368. → *DRL evaluation methodology and baseline comparison framework*

3. **Boute et al. (2022)** — "Deep Reinforcement Learning for Inventory Control: A Roadmap," *EJOR*, 298(2), 401-412. → *State/action space design and reward function formulation*

4. **De Moor et al. (2022)** — "Reward Shaping to Improve DRL Performance in Perishable Inventory Management," *EJOR*, 301(2), 535-545. → *Reward shaping methodology for our DQN agent*

5. **Mnih et al. (2015)** — "Human-Level Control Through Deep Reinforcement Learning," *Nature*, 518, 529-533. → *Foundational DQN algorithm with experience replay*

## 📄 License

Academic project — Smart Autonomous Inventory Management System.
