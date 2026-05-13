"""
Kaggle Dataset Loader
======================
Loads the generated (or downloaded) CSV dataset into the inventory
system's database, replacing the synthetic seed data with rich,
realistic demand patterns.

Supports both:
  - The generated Kaggle-style dataset (generate_kaggle_dataset.py)
  - Real Kaggle "Store Item Demand Forecasting" CSVs (date, store, item, sales)

Usage:
  python data_loader.py                    # Load default data/train.csv
  python data_loader.py path/to/file.csv   # Load custom CSV
"""

import os
import sys
import random
import pandas as pd
from datetime import datetime

from database import engine, SessionLocal, Base
from models import Product, Inventory, DemandHistory, Order, OrderType, OrderStatus


# ---------- CONFIG ----------
DEFAULT_CSV = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "data", "train.csv"
)

# Cost defaults for datasets that don't include cost columns
DEFAULT_COSTS = {
    "Electronics":   {"unit_cost": 24.99, "holding": 0.55, "shortage": 3.00, "ordering": 28.0},
    "Groceries":     {"unit_cost": 9.99,  "holding": 0.22, "shortage": 1.60, "ordering": 16.0},
    "Apparel":       {"unit_cost": 36.99, "holding": 0.70, "shortage": 3.50, "ordering": 30.0},
    "Home & Living": {"unit_cost": 12.99, "holding": 0.30, "shortage": 2.00, "ordering": 20.0},
    "default":       {"unit_cost": 15.00, "holding": 0.40, "shortage": 2.00, "ordering": 22.0},
}


def load_kaggle_dataset(csv_path: str = None, store_filter: int = None):
    """
    Load a Kaggle-style CSV into the inventory database.

    Parameters
    ----------
    csv_path : str
        Path to the CSV file. Defaults to data/train.csv
    store_filter : int or None
        If set, only load data for this store ID (useful for single-
        warehouse setups). None = load all stores merged.
    """
    csv_path = csv_path or DEFAULT_CSV

    if not os.path.exists(csv_path):
        print(f"❌ CSV not found: {csv_path}")
        print("   Run 'python generate_kaggle_dataset.py' first, or download from Kaggle.")
        return False

    print(f"📂 Loading dataset: {csv_path}")
    df = pd.read_csv(csv_path, parse_dates=["date"])

    # Filter to single store if requested
    if store_filter and "store" in df.columns:
        df = df[df["store"] == store_filter]
        print(f"   Filtered to store {store_filter}: {len(df)} rows")

    # ---------- Database setup ----------
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Clear existing data for a fresh load
    existing_count = db.query(Product).count()
    if existing_count > 0:
        print(f"   ⚠️  Clearing {existing_count} existing products and related data...")
        db.query(DemandHistory).delete()
        db.query(Order).delete()
        db.query(Inventory).delete()
        db.query(Product).delete()
        db.commit()

    # ---------- Detect CSV format ----------
    has_name = "item_name" in df.columns
    has_category = "category" in df.columns
    has_cost = "unit_cost" in df.columns
    has_lead_time = "lead_time_days" in df.columns

    print(f"   Format: {'extended' if has_name else 'basic'} "
          f"({'with' if has_cost else 'without'} costs)")

    # ---------- Process unique items ----------
    if has_name:
        items_df = df.groupby("item").agg({
            "item_name": "first",
            "category": "first",
            **({"unit_cost": "first"} if has_cost else {}),
            **({"lead_time_days": "first"} if has_lead_time else {}),
            "sales": ["mean", "std", "max"],
        }).reset_index()
        items_df.columns = ["_".join(c).strip("_") for c in items_df.columns]
    else:
        items_df = df.groupby("item").agg(
            sales_mean=("sales", "mean"),
            sales_std=("sales", "std"),
            sales_max=("sales", "max"),
        ).reset_index()

    products_map = {}  # item_id -> product.id

    for _, row in items_df.iterrows():
        item_id = int(row["item"])

        # Get item metadata
        name = row.get("item_name_first", f"Item {item_id}")
        category = row.get("category_first", "Miscellaneous")
        costs = DEFAULT_COSTS.get(category, DEFAULT_COSTS["default"])
        unit_cost = row.get("unit_cost_first", costs["unit_cost"])
        lead_time = int(row.get("lead_time_days_first", 3))

        avg_demand = float(row.get("sales_mean", 20))
        max_demand = float(row.get("sales_max", 50))

        # SKU code
        cat_prefix = category[:4].upper().replace(" ", "")
        sku = f"KGL-{cat_prefix}-{item_id:03d}"

        # Create product
        product = Product(
            sku_code=sku,
            name=name if isinstance(name, str) else f"Item {item_id}",
            category=category if isinstance(category, str) else "Miscellaneous",
            unit_cost=float(unit_cost),
            holding_cost_per_unit=costs["holding"],
            shortage_cost_per_unit=costs["shortage"],
            ordering_cost=costs["ordering"],
        )
        db.add(product)
        db.flush()

        # Create inventory with demand-derived parameters
        safety_stock = max(5, int(avg_demand * 1.5))
        reorder_point = max(10, int(avg_demand * 3))
        max_stock = max(50, int(max_demand * 5))
        current_stock = random.randint(
            int(avg_demand * 2), int(avg_demand * 6)
        )

        inv = Inventory(
            product_id=product.id,
            current_stock=min(current_stock, max_stock),
            reorder_point=reorder_point,
            safety_stock=safety_stock,
            max_stock=max_stock,
        )
        db.add(inv)

        # Generate realistic historical orders
        num_orders = random.randint(5, 12)
        now = datetime.utcnow()
        statuses = [OrderStatus.delivered] * 4 + [OrderStatus.in_transit, OrderStatus.pending]
        for _ in range(num_orders):
            from datetime import timedelta
            days_ago = random.randint(1, 60)
            ordered_at = now - timedelta(days=days_ago)
            status = random.choice(statuses)
            lt = random.randint(max(1, lead_time - 2), lead_time + 3)
            delivered_at = (ordered_at + timedelta(days=lt)
                           if status == OrderStatus.delivered else None)

            order = Order(
                product_id=product.id,
                quantity=random.randint(
                    int(avg_demand * 2), int(avg_demand * 5)
                ),
                order_type=random.choice([OrderType.manual, OrderType.auto]),
                status=status,
                lead_time_days=lt,
                ordered_at=ordered_at,
                delivered_at=delivered_at,
            )
            db.add(order)

        products_map[item_id] = product.id

    db.commit()
    print(f"   ✅ Created {len(products_map)} products with inventory & orders")

    # ---------- Load demand history ----------
    print("   📈 Loading demand history...")

    # Aggregate by (date, item) — merge across stores if multi-store
    if store_filter is None and "store" in df.columns:
        demand_df = df.groupby(["date", "item"]).agg(
            sales=("sales", "sum")
        ).reset_index()
    else:
        demand_df = df[["date", "item", "sales"]].copy()

    batch = []
    batch_size = 500
    total_records = 0

    for _, row in demand_df.iterrows():
        item_id = int(row["item"])
        if item_id not in products_map:
            continue

        record = DemandHistory(
            product_id=products_map[item_id],
            date=row["date"],
            quantity=max(0, int(row["sales"])),
        )
        batch.append(record)
        total_records += 1

        if len(batch) >= batch_size:
            db.bulk_save_objects(batch)
            db.commit()
            batch = []

    # Flush remaining
    if batch:
        db.bulk_save_objects(batch)
        db.commit()

    db.close()

    print(f"   ✅ Loaded {total_records:,} demand history records")
    print(f"\n🎉 Dataset loaded successfully!")
    print(f"   Products: {len(products_map)}")
    print(f"   Demand records: {total_records:,}")
    print(f"   Date range: {demand_df['date'].min()} to {demand_df['date'].max()}")
    return True


def get_dataset_stats(csv_path: str = None):
    """Print dataset statistics without loading into DB."""
    csv_path = csv_path or DEFAULT_CSV
    if not os.path.exists(csv_path):
        print(f"❌ File not found: {csv_path}")
        return

    df = pd.read_csv(csv_path, parse_dates=["date"])
    print(f"\n📊 Dataset Statistics: {csv_path}")
    print(f"   Total rows:  {len(df):,}")
    print(f"   Stores:      {df['store'].nunique() if 'store' in df.columns else 'N/A'}")
    print(f"   Items:       {df['item'].nunique()}")
    if "category" in df.columns:
        print(f"   Categories:  {list(df['category'].unique())}")
    print(f"   Date range:  {df['date'].min()} to {df['date'].max()}")
    print(f"\n   Sales distribution:")
    print(f"     Mean:   {df['sales'].mean():.1f}")
    print(f"     Std:    {df['sales'].std():.1f}")
    print(f"     Min:    {df['sales'].min()}")
    print(f"     Max:    {df['sales'].max()}")
    print(f"     Median: {df['sales'].median():.0f}")


if __name__ == "__main__":
    csv = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CSV

    if "--stats" in sys.argv:
        get_dataset_stats(csv)
    else:
        load_kaggle_dataset(csv)
