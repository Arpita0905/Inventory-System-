"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base
from routers import products, inventory, orders, forecast, rl, agents, simulation
from seed import seed
from demand_generator import generate_demand

# Create all tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Smart Inventory AI System",
    description="Multi-agent autonomous inventory management API",
    version="1.0.0",
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(products.router)
app.include_router(inventory.router)
app.include_router(orders.router)
app.include_router(forecast.router)
app.include_router(rl.router)
app.include_router(agents.router)
app.include_router(simulation.router)


@app.on_event("startup")
def on_startup():
    """Seed database and generate demand data on first run."""
    seed()
    generate_demand()


@app.get("/")
def root():
    return {"message": "Smart Inventory AI System API", "docs": "/docs"}
