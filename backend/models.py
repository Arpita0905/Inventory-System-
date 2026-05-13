"""SQLAlchemy ORM models for the inventory system."""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, Float, String, DateTime, ForeignKey, Enum as SAEnum
)
from sqlalchemy.orm import relationship
import enum

from database import Base


# ---------- Enums ----------
class OrderType(str, enum.Enum):
    manual = "manual"
    auto = "auto"


class OrderStatus(str, enum.Enum):
    pending = "pending"
    in_transit = "in_transit"
    delivered = "delivered"
    cancelled = "cancelled"


# ---------- Models ----------
class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    sku_code = Column(String(32), unique=True, nullable=False, index=True)
    name = Column(String(128), nullable=False)
    category = Column(String(64), nullable=False)
    unit_cost = Column(Float, nullable=False)
    holding_cost_per_unit = Column(Float, nullable=False, default=0.5)
    shortage_cost_per_unit = Column(Float, nullable=False, default=2.0)
    ordering_cost = Column(Float, nullable=False, default=25.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    inventory = relationship("Inventory", back_populates="product", uselist=False, cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="product", cascade="all, delete-orphan")
    demand_history = relationship("DemandHistory", back_populates="product", cascade="all, delete-orphan")


class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), unique=True, nullable=False)
    current_stock = Column(Integer, nullable=False, default=0)
    reorder_point = Column(Integer, nullable=False, default=20)
    safety_stock = Column(Integer, nullable=False, default=10)
    max_stock = Column(Integer, nullable=False, default=200)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    product = relationship("Product", back_populates="inventory")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Integer, nullable=False)
    order_type = Column(SAEnum(OrderType), nullable=False, default=OrderType.manual)
    status = Column(SAEnum(OrderStatus), nullable=False, default=OrderStatus.pending)
    lead_time_days = Column(Integer, nullable=False, default=3)
    ordered_at = Column(DateTime, default=datetime.utcnow)
    delivered_at = Column(DateTime, nullable=True)

    product = relationship("Product", back_populates="orders")


class DemandHistory(Base):
    __tablename__ = "demand_history"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    date = Column(DateTime, nullable=False)
    quantity = Column(Integer, nullable=False)

    product = relationship("Product", back_populates="demand_history")
