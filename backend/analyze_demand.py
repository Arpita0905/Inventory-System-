"""Quick script to analyze demand statistics from DataCo data."""
import numpy as np
from database import SessionLocal
from models import Product, Inventory, DemandHistory

db = SessionLocal()
products = db.query(Product).all()
print(f"Products: {len(products)}\n")

all_means = []
all_stds = []

for p in products:
    demands = db.query(DemandHistory).filter(DemandHistory.product_id == p.id).all()
    qtys = [d.quantity for d in demands]
    inv = db.query(Inventory).filter(Inventory.product_id == p.id).first()
    if qtys:
        m = np.mean(qtys)
        s = np.std(qtys)
        all_means.append(m)
        all_stds.append(s)
        print(f"  {p.sku_code}: mean={m:.1f} std={s:.1f} max={max(qtys)} "
              f"records={len(qtys)} hold={p.holding_cost_per_unit} "
              f"short={p.shortage_cost_per_unit} order={p.ordering_cost} "
              f"max_stock={inv.max_stock if inv else 0}")

print(f"\nOverall avg demand: {np.mean(all_means):.1f}")
print(f"Overall avg std: {np.mean(all_stds):.1f}")
print(f"Demand range across products: {min(all_means):.1f} - {max(all_means):.1f}")
db.close()
