"""Products router – CRUD operations for SKU management."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Product, Inventory
from schemas import ProductCreate, ProductUpdate, ProductOut

router = APIRouter(prefix="/api/products", tags=["Products"])


@router.get("/", response_model=List[ProductOut])
def list_products(skip: int = 0, limit: int = 100, category: str = None, db: Session = Depends(get_db)):
    q = db.query(Product)
    if category:
        q = q.filter(Product.category == category)
    return q.offset(skip).limit(limit).all()


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post("/", response_model=ProductOut, status_code=201)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    existing = db.query(Product).filter(Product.sku_code == payload.sku_code).first()
    if existing:
        raise HTTPException(status_code=409, detail="SKU code already exists")

    product = Product(
        sku_code=payload.sku_code,
        name=payload.name,
        category=payload.category,
        unit_cost=payload.unit_cost,
        holding_cost_per_unit=payload.holding_cost_per_unit,
        shortage_cost_per_unit=payload.shortage_cost_per_unit,
        ordering_cost=payload.ordering_cost,
    )
    db.add(product)
    db.flush()

    inventory = Inventory(
        product_id=product.id,
        current_stock=payload.current_stock,
        reorder_point=payload.reorder_point,
        safety_stock=payload.safety_stock,
        max_stock=payload.max_stock,
    )
    db.add(inventory)
    db.commit()
    db.refresh(product)
    return product


@router.put("/{product_id}", response_model=ProductOut)
def update_product(product_id: int, payload: ProductUpdate, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=204)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
