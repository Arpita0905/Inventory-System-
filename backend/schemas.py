"""Pydantic schemas for request/response validation."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


# ---- Product ----
class ProductBase(BaseModel):
    sku_code: str
    name: str
    category: str
    unit_cost: float
    holding_cost_per_unit: float = 0.5
    shortage_cost_per_unit: float = 2.0
    ordering_cost: float = 25.0


class ProductCreate(ProductBase):
    current_stock: int = 0
    reorder_point: int = 20
    safety_stock: int = 10
    max_stock: int = 200


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    unit_cost: Optional[float] = None
    holding_cost_per_unit: Optional[float] = None
    shortage_cost_per_unit: Optional[float] = None
    ordering_cost: Optional[float] = None


class InventoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    product_id: int
    current_stock: int
    reorder_point: int
    safety_stock: int
    max_stock: int
    updated_at: Optional[datetime] = None


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sku_code: str
    name: str
    category: str
    unit_cost: float
    holding_cost_per_unit: float
    shortage_cost_per_unit: float
    ordering_cost: float
    created_at: Optional[datetime] = None
    inventory: Optional[InventoryOut] = None


# ---- Inventory ----
class InventoryUpdate(BaseModel):
    current_stock: Optional[int] = None
    reorder_point: Optional[int] = None
    safety_stock: Optional[int] = None
    max_stock: Optional[int] = None


class InventoryWithProduct(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    product_id: int
    current_stock: int
    reorder_point: int
    safety_stock: int
    max_stock: int
    updated_at: Optional[datetime] = None
    product: Optional[ProductBase] = None


# ---- Orders ----
class OrderCreate(BaseModel):
    product_id: int
    quantity: int
    order_type: str = "manual"


class OrderStatusUpdate(BaseModel):
    status: str


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    product_id: int
    quantity: int
    order_type: str
    status: str
    lead_time_days: int
    ordered_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None


class OrderWithProduct(OrderOut):
    model_config = ConfigDict(from_attributes=True)
    product: Optional[ProductBase] = None


class OrderStats(BaseModel):
    total_orders: int
    pending: int
    in_transit: int
    delivered: int
    cancelled: int
    total_units_ordered: int


# ---- Scenario Simulation ----
class ScenarioRequest(BaseModel):
    """Input parameters for what-if scenario simulation."""
    demand_multiplier: float = 1.0        # 0.5 – 3.0 (1.0 = no change)
    lead_time_multiplier: float = 1.0     # 0.5 – 3.0
    holding_cost_multiplier: float = 1.0  # 0.5 – 3.0
    stockout_cost_multiplier: float = 1.0 # 0.5 – 3.0
    simulation_days: int = 60             # 10 – 120


class ScenarioResponse(BaseModel):
    """Aggregated results from a scenario simulation run."""
    total_cost: float
    stockouts: int
    service_level: float
    average_inventory: float
    recommendation: str
    daily_breakdown: List[dict]
