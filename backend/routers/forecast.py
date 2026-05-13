"""Forecast router – demand forecasting API endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from models import Product, DemandHistory
from ai_models.forecasting.forecast_engine import forecast_demand

router = APIRouter(prefix="/api/forecast", tags=["Forecast"])


@router.get("/{sku_id}")
def get_forecast(
    sku_id: int,
    periods: int = Query(default=30, ge=7, le=90, description="Number of days to forecast"),
    db: Session = Depends(get_db),
):
    """Generate demand forecast for a specific product."""
    product = db.query(Product).filter(Product.id == sku_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    result = forecast_demand(db, sku_id, periods=periods)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    result["product_name"] = product.name
    result["sku_code"] = product.sku_code
    return result


@router.get("/")
def list_demand_summary(db: Session = Depends(get_db)):
    """Get demand history summary for all products."""
    products = db.query(Product).all()
    summaries = []
    for p in products:
        records = (
            db.query(DemandHistory)
            .filter(DemandHistory.product_id == p.id)
            .order_by(DemandHistory.date.desc())
            .limit(30)
            .all()
        )
        total_30d = sum(r.quantity for r in records)
        avg_daily = round(total_30d / max(len(records), 1), 1)
        summaries.append({
            "product_id": p.id,
            "sku_code": p.sku_code,
            "name": p.name,
            "total_demand_30d": total_30d,
            "avg_daily_demand": avg_daily,
            "data_points": len(records),
        })
    return summaries
