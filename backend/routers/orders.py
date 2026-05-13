"""Orders router – order management and statistics."""
import random
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from database import get_db
from models import Order, OrderType, OrderStatus, Product, Inventory
from schemas import OrderCreate, OrderStatusUpdate, OrderWithProduct, OrderOut, OrderStats

router = APIRouter(prefix="/api/orders", tags=["Orders"])


@router.get("/", response_model=List[OrderWithProduct])
def list_orders(
    status: Optional[str] = None,
    product_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    q = db.query(Order).options(joinedload(Order.product))
    if status:
        q = q.filter(Order.status == status)
    if product_id:
        q = q.filter(Order.product_id == product_id)
    return q.order_by(Order.ordered_at.desc()).offset(skip).limit(limit).all()


@router.get("/stats", response_model=OrderStats)
def order_stats(db: Session = Depends(get_db)):
    total = db.query(func.count(Order.id)).scalar() or 0
    pending = db.query(func.count(Order.id)).filter(Order.status == OrderStatus.pending).scalar() or 0
    in_transit = db.query(func.count(Order.id)).filter(Order.status == OrderStatus.in_transit).scalar() or 0
    delivered = db.query(func.count(Order.id)).filter(Order.status == OrderStatus.delivered).scalar() or 0
    cancelled = db.query(func.count(Order.id)).filter(Order.status == OrderStatus.cancelled).scalar() or 0
    total_units = db.query(func.sum(Order.quantity)).scalar() or 0
    return OrderStats(
        total_orders=total,
        pending=pending,
        in_transit=in_transit,
        delivered=delivered,
        cancelled=cancelled,
        total_units_ordered=total_units,
    )


@router.post("/", response_model=OrderOut, status_code=201)
def create_order(payload: OrderCreate, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == payload.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Simulate stochastic lead time (2-7 days)
    lead_time = random.randint(2, 7)

    order = Order(
        product_id=payload.product_id,
        quantity=payload.quantity,
        order_type=OrderType(payload.order_type),
        status=OrderStatus.pending,
        lead_time_days=lead_time,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


@router.put("/{order_id}/status", response_model=OrderOut)
def update_order_status(order_id: int, payload: OrderStatusUpdate, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    new_status = OrderStatus(payload.status)
    order.status = new_status

    # When delivered, update inventory stock and set delivery timestamp
    if new_status == OrderStatus.delivered:
        order.delivered_at = datetime.utcnow()
        inv = db.query(Inventory).filter(Inventory.product_id == order.product_id).first()
        if inv:
            inv.current_stock += order.quantity

    db.commit()
    db.refresh(order)
    return order
