"""Supplier Agent – simulates supplier behavior with stochastic lead times."""
import random
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from models import Order, OrderStatus, Inventory


class SupplierAgent:
    """
    Simulates supplier behavior for the single warehouse:
    - Processes pending orders based on lead time
    - Adds stochastic delays (weather, logistics issues)
    - Tracks delivery reliability metrics
    """

    def __init__(self, reliability=0.85, delay_probability=0.15, max_delay_days=3):
        self.reliability = reliability
        self.delay_probability = delay_probability
        self.max_delay_days = max_delay_days

    def process_orders(self, db: Session):
        """
        Check all in-transit orders and deliver those past their lead time.
        Simulate delays on some orders.
        """
        now = datetime.utcnow()
        results = {"delivered": [], "delayed": [], "total_checked": 0}

        # Get orders that should be delivered by now
        pending_orders = db.query(Order).filter(
            Order.status.in_([OrderStatus.pending, OrderStatus.in_transit])
        ).all()

        results["total_checked"] = len(pending_orders)

        for order in pending_orders:
            expected_delivery = order.ordered_at + timedelta(days=order.lead_time_days)

            # Move pending to in_transit
            if order.status == OrderStatus.pending:
                order.status = OrderStatus.in_transit
                continue

            # Check if delivery is due
            if now >= expected_delivery:
                # Simulate random delay
                if random.random() < self.delay_probability:
                    delay = random.randint(1, self.max_delay_days)
                    order.lead_time_days += delay
                    results["delayed"].append({
                        "order_id": order.id,
                        "product_id": order.product_id,
                        "additional_delay": delay,
                    })
                else:
                    # Deliver the order
                    order.status = OrderStatus.delivered
                    order.delivered_at = now
                    # Update inventory
                    inv = db.query(Inventory).filter(
                        Inventory.product_id == order.product_id
                    ).first()
                    if inv:
                        inv.current_stock += order.quantity
                    results["delivered"].append({
                        "order_id": order.id,
                        "product_id": order.product_id,
                        "quantity": order.quantity,
                    })

        db.commit()
        return results

    def get_metrics(self, db: Session):
        """Calculate supplier reliability metrics."""
        from sqlalchemy import func

        total_orders = db.query(func.count(Order.id)).scalar() or 0
        delivered = db.query(func.count(Order.id)).filter(
            Order.status == OrderStatus.delivered
        ).scalar() or 0

        # Average lead time for delivered orders
        avg_lead = db.query(func.avg(Order.lead_time_days)).filter(
            Order.status == OrderStatus.delivered
        ).scalar() or 0

        return {
            "total_orders": total_orders,
            "delivered": delivered,
            "delivery_rate": round(delivered / max(total_orders, 1) * 100, 1),
            "avg_lead_time_days": round(float(avg_lead), 1),
        }
