"""Agents router – supplier processing and monitoring alerts."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from ai_models.agents.supplier_agent import SupplierAgent
from ai_models.agents.monitoring_agent import MonitoringAgent

router = APIRouter(prefix="/api/agents", tags=["Multi-Agent"])

supplier = SupplierAgent()
monitor = MonitoringAgent()


@router.post("/supplier/process")
def process_supplier(db: Session = Depends(get_db)):
    """Run supplier agent to process pending orders."""
    return supplier.process_orders(db)


@router.get("/supplier/metrics")
def supplier_metrics(db: Session = Depends(get_db)):
    """Get supplier reliability metrics."""
    return supplier.get_metrics(db)


@router.get("/alerts")
def get_alerts(db: Session = Depends(get_db)):
    """Get all active alerts from the monitoring agent."""
    return monitor.generate_alerts(db)
