"""Inventory router – stock level tracking and alerts."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models import Inventory, Product
from schemas import InventoryWithProduct, InventoryUpdate, InventoryOut

router = APIRouter(prefix="/api/inventory", tags=["Inventory"])


@router.get("/", response_model=List[InventoryWithProduct])
def list_inventory(db: Session = Depends(get_db)):
    return db.query(Inventory).options(joinedload(Inventory.product)).all()


@router.get("/alerts", response_model=List[InventoryWithProduct])
def inventory_alerts(db: Session = Depends(get_db)):
    """Return items where current stock is at or below the reorder point."""
    return (
        db.query(Inventory)
        .options(joinedload(Inventory.product))
        .filter(Inventory.current_stock <= Inventory.reorder_point)
        .all()
    )


@router.put("/{product_id}", response_model=InventoryOut)
def update_inventory(product_id: int, payload: InventoryUpdate, db: Session = Depends(get_db)):
    inv = db.query(Inventory).filter(Inventory.product_id == product_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Inventory record not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(inv, field, value)

    db.commit()
    db.refresh(inv)
    return inv
