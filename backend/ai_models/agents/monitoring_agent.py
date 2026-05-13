"""Monitoring & Alert Agent – detects anomalies and flags risks."""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
import numpy as np

from models import Inventory, Product, DemandHistory, Order, OrderStatus


class MonitoringAgent:
    """
    Real-time monitoring agent that detects:
    - Overstock warnings
    - Understock/stockout risk
    - Demand spike anomalies
    - Supplier delay alerts (recent orders only)
    """

    def __init__(self, spike_threshold=2.0, critical_stock_ratio=0.3):
        self.spike_threshold = spike_threshold  # std devs above mean = spike
        self.critical_stock_ratio = critical_stock_ratio

    def generate_alerts(self, db: Session):
        """Run all alert checks and return a list of alerts."""
        alerts = []
        alerts.extend(self._check_stock_levels(db))
        alerts.extend(self._check_demand_spikes(db))
        alerts.extend(self._check_supplier_delays(db))
        alerts.extend(self._check_overstock(db))

        # Sort by severity
        severity_order = {"critical": 0, "warning": 1, "info": 2}
        alerts.sort(key=lambda a: severity_order.get(a["severity"], 3))

        return alerts

    def _check_stock_levels(self, db: Session):
        """Check for items below safety stock or reorder point."""
        alerts = []
        items = db.query(Inventory).all()

        for item in items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if not product:
                continue

            if item.current_stock <= item.safety_stock:
                alerts.append({
                    "type": "understock",
                    "severity": "critical",
                    "product_id": item.product_id,
                    "sku_code": product.sku_code,
                    "product_name": product.name,
                    "message": f"CRITICAL: {product.sku_code} stock ({item.current_stock}) is at or below safety stock ({item.safety_stock})",
                    "current_stock": item.current_stock,
                    "threshold": item.safety_stock,
                    "timestamp": datetime.utcnow().isoformat(),
                })
            elif item.current_stock <= item.reorder_point:
                alerts.append({
                    "type": "understock",
                    "severity": "warning",
                    "product_id": item.product_id,
                    "sku_code": product.sku_code,
                    "product_name": product.name,
                    "message": f"LOW STOCK: {product.sku_code} stock ({item.current_stock}) is below reorder point ({item.reorder_point})",
                    "current_stock": item.current_stock,
                    "threshold": item.reorder_point,
                    "timestamp": datetime.utcnow().isoformat(),
                })
        return alerts

    def _check_overstock(self, db: Session):
        """Check for items approaching max stock."""
        alerts = []
        items = db.query(Inventory).all()

        for item in items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if not product:
                continue

            fill_pct = item.current_stock / max(item.max_stock, 1)
            if fill_pct >= 0.9:
                alerts.append({
                    "type": "overstock",
                    "severity": "warning",
                    "product_id": item.product_id,
                    "sku_code": product.sku_code,
                    "product_name": product.name,
                    "message": f"OVERSTOCK: {product.sku_code} is at {int(fill_pct*100)}% capacity ({item.current_stock}/{item.max_stock})",
                    "current_stock": item.current_stock,
                    "max_stock": item.max_stock,
                    "timestamp": datetime.utcnow().isoformat(),
                })
        return alerts

    def _check_demand_spikes(self, db: Session):
        """
        Detect demand anomalies using z-score.
        Uses the most recent demand data available (not hardcoded to 'now'),
        so it works with historical datasets like DataCo.
        """
        alerts = []
        products = db.query(Product).all()

        for product in products:
            # Get ALL demand records ordered by date (most recent first)
            records = (
                db.query(DemandHistory)
                .filter(DemandHistory.product_id == product.id)
                .order_by(DemandHistory.date.desc())
                .limit(60)  # last 60 data points
                .all()
            )

            if len(records) < 10:
                continue

            quantities = [r.quantity for r in records]
            recent = quantities[:5]      # most recent 5 data points
            historical = quantities[5:]  # the rest as baseline

            if not historical:
                continue

            mean = np.mean(historical)
            std = max(np.std(historical), 1)
            recent_avg = np.mean(recent)

            z_score = (recent_avg - mean) / std

            if z_score >= self.spike_threshold:
                latest_date = records[0].date.strftime("%Y-%m-%d") if records else "N/A"
                alerts.append({
                    "type": "demand_spike",
                    "severity": "warning",
                    "product_id": product.id,
                    "sku_code": product.sku_code,
                    "product_name": product.name,
                    "message": f"DEMAND SPIKE: {product.sku_code} recent demand ({recent_avg:.0f}/day) is {z_score:.1f}σ above average ({mean:.0f}/day)",
                    "z_score": round(z_score, 2),
                    "recent_avg": round(recent_avg, 1),
                    "historical_avg": round(mean, 1),
                    "timestamp": datetime.utcnow().isoformat(),
                })
        return alerts

    def _check_supplier_delays(self, db: Session):
        """
        Check for RECENT orders that are overdue.

        Only checks orders placed within the last 90 days to avoid false
        alerts from historical dataset records (e.g. DataCo 2015-2018 data).
        Orders that are already delivered or cancelled are excluded.
        """
        alerts = []
        now = datetime.utcnow()
        cutoff = now - timedelta(days=90)  # Only check recent orders

        overdue_orders = (
            db.query(Order)
            .filter(
                Order.status.in_([OrderStatus.pending, OrderStatus.in_transit]),
                Order.ordered_at >= cutoff,  # Only recent orders
            )
            .all()
        )

        for order in overdue_orders:
            expected = order.ordered_at + timedelta(days=order.lead_time_days)
            if now > expected + timedelta(days=1):
                product = db.query(Product).filter(Product.id == order.product_id).first()
                days_overdue = (now - expected).days
                alerts.append({
                    "type": "supplier_delay",
                    "severity": "warning" if days_overdue <= 3 else "critical",
                    "product_id": order.product_id,
                    "sku_code": product.sku_code if product else "N/A",
                    "product_name": product.name if product else "Unknown",
                    "message": f"DELAY: Order #{order.id} for {product.sku_code if product else 'N/A'} is {days_overdue} days overdue",
                    "order_id": order.id,
                    "days_overdue": days_overdue,
                    "timestamp": datetime.utcnow().isoformat(),
                })
        return alerts
