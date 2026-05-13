"""
DataCo Supply Chain → Inventory System Loader
===============================================
Transforms the real-world DataCo SMART SUPPLY CHAIN dataset
(180K+ orders, 50 categories, 118 products) from Kaggle/GitHub
into our inventory system's database format.

Source: Constante, Fabian; Silva, Fernando; Pereira, António (2019),
        "DataCo SMART SUPPLY CHAIN FOR BIG DATA ANALYSIS", Mendeley Data

This loader:
  1. Reads the raw 53-column CSV
  2. Selects the top 20 products by order volume
  3. Creates Products with real prices and cost estimates
  4. Creates Inventory with demand-derived reorder points
  5. Creates historical Orders with real lead times
  6. Creates DemandHistory from daily order aggregation
"""

import os
import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from database import engine, SessionLocal, Base
from models import Product, Inventory, DemandHistory, Order, OrderType, OrderStatus

CSV_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "data", "DataCoSupplyChain.csv",
)

# Number of top products to import (keeps the UI manageable)
TOP_N_PRODUCTS = 20


def load_dataco_dataset():
    """Load the DataCo Supply Chain dataset into the inventory database."""

    if not os.path.exists(CSV_PATH):
        print(f"❌ DataCo dataset not found at: {CSV_PATH}")
        print("   Download it first using:")
        print("   python -c \"import urllib.request; urllib.request.urlretrieve("
              "'https://raw.githubusercontent.com/ashishpatel26/DataCo-SMART-"
              "SUPPLY-CHAIN-FOR-BIG-DATA-ANALYSIS/main/DataCoSupplyChainDataset"
              ".csv', 'data/DataCoSupplyChain.csv')\"")
        return False

    print(f"📂 Loading DataCo Supply Chain dataset: {CSV_PATH}")
    df = pd.read_csv(CSV_PATH, encoding="latin-1")
    print(f"   Raw data: {len(df):,} rows, {len(df.columns)} columns")

    # ---------- Parse dates ----------
    df["order_date"] = pd.to_datetime(df["order date (DateOrders)"])

    # ---------- Select top N products by order volume ----------
    top_products = (
        df["Product Name"]
        .value_counts()
        .head(TOP_N_PRODUCTS)
        .index.tolist()
    )
    df_filtered = df[df["Product Name"].isin(top_products)].copy()
    print(f"   Selected top {TOP_N_PRODUCTS} products: {len(df_filtered):,} orders")

    # ---------- Database setup ----------
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Clear existing data
    existing = db.query(Product).count()
    if existing > 0:
        print(f"   ⚠️  Clearing {existing} existing products and related data...")
        db.query(DemandHistory).delete()
        db.query(Order).delete()
        db.query(Inventory).delete()
        db.query(Product).delete()
        db.commit()

    # ---------- Create products ----------
    products_map = {}  # product_name -> product.id
    product_stats = {}  # product_name -> stats dict

    for product_name in top_products:
        prod_df = df_filtered[df_filtered["Product Name"] == product_name]

        # Extract real data from the dataset
        category = prod_df["Category Name"].mode().iloc[0]
        unit_price = round(prod_df["Product Price"].median(), 2)
        avg_lead_time = round(prod_df["Days for shipping (real)"].mean())
        avg_qty_per_order = prod_df["Order Item Quantity"].mean()
        total_orders = len(prod_df)

        # Calculate daily demand statistics
        daily_demand = (
            prod_df.groupby(prod_df["order_date"].dt.date)["Order Item Quantity"]
            .sum()
        )
        avg_daily_demand = daily_demand.mean()
        max_daily_demand = daily_demand.max()

        # Derive cost parameters from real price data
        holding_cost = round(unit_price * 0.02, 2)   # 2% of price per day
        shortage_cost = round(unit_price * 0.10, 2)   # 10% penalty per unit
        ordering_cost = round(10 + unit_price * 0.5, 2)  # Fixed + variable

        # Generate SKU code from category
        cat_code = "".join(w[0] for w in category.split()[:2]).upper()
        item_num = len(products_map) + 1
        sku = f"DC-{cat_code}-{item_num:03d}"

        # Clean product name (truncate if too long)
        clean_name = product_name[:128]

        product = Product(
            sku_code=sku,
            name=clean_name,
            category=category,
            unit_cost=unit_price,
            holding_cost_per_unit=max(0.10, holding_cost),
            shortage_cost_per_unit=max(0.50, shortage_cost),
            ordering_cost=max(10.0, ordering_cost),
        )
        db.add(product)
        db.flush()
        products_map[product_name] = product.id

        # Store stats for inventory calculation
        product_stats[product_name] = {
            "avg_daily_demand": avg_daily_demand,
            "max_daily_demand": max_daily_demand,
            "avg_lead_time": avg_lead_time,
            "total_orders": total_orders,
            "avg_qty": avg_qty_per_order,
        }

        # ---------- Create inventory with demand-derived parameters ----------
        safety_stock = max(5, int(avg_daily_demand * avg_lead_time * 0.5))
        reorder_point = max(10, int(avg_daily_demand * avg_lead_time + safety_stock))
        max_stock = max(50, int(max_daily_demand * avg_lead_time * 3))
        current_stock = random.randint(
            max(1, int(avg_daily_demand * 3)),
            max(10, int(avg_daily_demand * 10))
        )

        inv = Inventory(
            product_id=product.id,
            current_stock=min(current_stock, max_stock),
            reorder_point=reorder_point,
            safety_stock=safety_stock,
            max_stock=max_stock,
        )
        db.add(inv)

    db.commit()
    print(f"   ✅ Created {len(products_map)} products with inventory")

    # ---------- Create historical orders (from real order data) ----------
    print("   📦 Loading real order history...")
    order_count = 0

    for product_name, product_id in products_map.items():
        prod_df = df_filtered[df_filtered["Product Name"] == product_name]

        # Sample up to 20 real orders per product
        sample_size = min(20, len(prod_df))
        sampled = prod_df.sample(n=sample_size, random_state=42)

        for _, row in sampled.iterrows():
            lead_time = int(row.get("Days for shipping (real)", 3))
            ordered_at = row["order_date"]

            # Determine order status from real data
            order_status_raw = str(row.get("Order Status", "")).lower()
            if "complete" in order_status_raw:
                status = OrderStatus.delivered
                delivered_at = ordered_at + timedelta(days=lead_time)
            elif "pending" in order_status_raw:
                status = OrderStatus.pending
                delivered_at = None
            elif "cancel" in order_status_raw or "suspected" in order_status_raw:
                status = OrderStatus.cancelled
                delivered_at = None
            else:
                status = OrderStatus.in_transit
                delivered_at = None

            order = Order(
                product_id=product_id,
                quantity=max(1, int(row.get("Order Item Quantity", 1))),
                order_type=random.choice([OrderType.manual, OrderType.auto]),
                status=status,
                lead_time_days=lead_time,
                ordered_at=ordered_at,
                delivered_at=delivered_at,
            )
            db.add(order)
            order_count += 1

    db.commit()
    print(f"   ✅ Created {order_count} orders from real order data")

    # ---------- Create demand history (daily aggregation) ----------
    print("   📈 Loading daily demand history...")
    demand_count = 0
    batch = []

    for product_name, product_id in products_map.items():
        prod_df = df_filtered[df_filtered["Product Name"] == product_name]

        # Aggregate to daily demand
        daily = (
            prod_df.groupby(prod_df["order_date"].dt.date)["Order Item Quantity"]
            .sum()
            .reset_index()
        )
        daily.columns = ["date", "quantity"]

        for _, row in daily.iterrows():
            record = DemandHistory(
                product_id=product_id,
                date=datetime.combine(row["date"], datetime.min.time()),
                quantity=max(0, int(row["quantity"])),
            )
            batch.append(record)
            demand_count += 1

            if len(batch) >= 500:
                db.bulk_save_objects(batch)
                db.commit()
                batch = []

    if batch:
        db.bulk_save_objects(batch)
        db.commit()

    db.close()

    # ---------- Summary ----------
    print(f"\n🎉 DataCo Supply Chain dataset loaded successfully!")
    print(f"   Source: Kaggle / Mendeley Data (real-world supply chain)")
    print(f"   Products:        {len(products_map)}")
    print(f"   Orders:          {order_count}")
    print(f"   Demand records:  {demand_count:,}")
    print(f"   Categories:      {df_filtered['Category Name'].nunique()}")

    date_range = df_filtered["order_date"]
    print(f"   Date range:      {date_range.min().date()} to {date_range.max().date()}")

    print(f"\n📋 Product Summary:")
    for name, pid in products_map.items():
        stats = product_stats[name]
        cat = df_filtered[df_filtered["Product Name"] == name]["Category Name"].mode().iloc[0]
        print(f"   {name[:45]:45s} | {cat[:20]:20s} | "
              f"avg demand: {stats['avg_daily_demand']:.1f}/day | "
              f"lead time: {stats['avg_lead_time']:.0f}d")

    return True


if __name__ == "__main__":
    load_dataco_dataset()
