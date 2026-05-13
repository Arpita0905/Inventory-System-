"""Seed script – populates the database with 10 sample SKUs and historical orders."""
import random
from datetime import datetime, timedelta
from database import engine, SessionLocal, Base
from models import Product, Inventory, Order, OrderType, OrderStatus

PRODUCTS = [
    # (sku, name, category, unit_cost, holding, shortage, ordering)
    ("ELEC-001", "Wireless Bluetooth Headphones", "Electronics", 29.99, 0.60, 3.50, 30.0),
    ("ELEC-002", "USB-C Fast Charger", "Electronics", 14.99, 0.30, 2.00, 20.0),
    ("ELEC-003", "Portable Power Bank 10000mAh", "Electronics", 24.99, 0.50, 3.00, 25.0),
    ("GROC-001", "Organic Green Tea (100 bags)", "Groceries", 8.99, 0.20, 1.50, 15.0),
    ("GROC-002", "Premium Basmati Rice 5kg", "Groceries", 12.49, 0.25, 1.80, 18.0),
    ("GROC-003", "Cold-Pressed Olive Oil 1L", "Groceries", 9.99, 0.22, 1.60, 16.0),
    ("APRL-001", "Cotton Crew-Neck T-Shirt", "Apparel", 15.99, 0.35, 2.50, 22.0),
    ("APRL-002", "Slim-Fit Denim Jeans", "Apparel", 39.99, 0.80, 4.00, 35.0),
    ("APRL-003", "Running Sports Shoes", "Apparel", 54.99, 1.00, 5.00, 40.0),
    ("MISC-001", "Stainless Steel Water Bottle", "Miscellaneous", 11.99, 0.28, 1.70, 17.0),
]


def seed():
    """Create tables and insert sample data."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Skip if already seeded
    if db.query(Product).count() > 0:
        print("Database already seeded. Skipping.")
        db.close()
        return

    now = datetime.utcnow()

    for sku, name, cat, cost, hold, short, order_cost in PRODUCTS:
        stock = random.randint(15, 120)
        reorder_pt = random.randint(15, 35)
        safety = random.randint(5, 15)
        max_stk = random.randint(150, 300)

        product = Product(
            sku_code=sku,
            name=name,
            category=cat,
            unit_cost=cost,
            holding_cost_per_unit=hold,
            shortage_cost_per_unit=short,
            ordering_cost=order_cost,
        )
        db.add(product)
        db.flush()

        inv = Inventory(
            product_id=product.id,
            current_stock=stock,
            reorder_point=reorder_pt,
            safety_stock=safety,
            max_stock=max_stk,
        )
        db.add(inv)

        # Generate 3-8 historical orders per product over the last 30 days
        num_orders = random.randint(3, 8)
        statuses = [OrderStatus.delivered, OrderStatus.delivered, OrderStatus.delivered,
                    OrderStatus.in_transit, OrderStatus.pending]
        for _ in range(num_orders):
            days_ago = random.randint(1, 30)
            ordered_at = now - timedelta(days=days_ago)
            status = random.choice(statuses)
            lead = random.randint(2, 7)
            delivered_at = ordered_at + timedelta(days=lead) if status == OrderStatus.delivered else None

            order = Order(
                product_id=product.id,
                quantity=random.randint(10, 80),
                order_type=random.choice([OrderType.manual, OrderType.auto]),
                status=status,
                lead_time_days=lead,
                ordered_at=ordered_at,
                delivered_at=delivered_at,
            )
            db.add(order)

    db.commit()
    db.close()
    print(f"✅ Seeded {len(PRODUCTS)} products with inventory and historical orders.")


if __name__ == "__main__":
    seed()
