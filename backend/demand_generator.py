"""Demand data generator – creates 90 days of synthetic demand with seasonal patterns."""
import math
import random
from datetime import datetime, timedelta
from database import SessionLocal
from models import Product, DemandHistory


# Base demand ranges per category (daily units)
CATEGORY_DEMAND = {
    "Electronics": (8, 25),
    "Groceries": (15, 45),
    "Apparel": (5, 20),
    "Miscellaneous": (10, 30),
}


def generate_demand(days: int = 90):
    """Generate synthetic daily demand data for all products."""
    db = SessionLocal()

    # Skip if already generated
    if db.query(DemandHistory).count() > 0:
        print("Demand data already exists. Skipping generation.")
        db.close()
        return

    products = db.query(Product).all()
    now = datetime.utcnow()
    start_date = now - timedelta(days=days)

    for product in products:
        low, high = CATEGORY_DEMAND.get(product.category, (10, 30))
        base_demand = random.uniform(low, high)

        for day_offset in range(days):
            date = start_date + timedelta(days=day_offset)
            day_of_week = date.weekday()

            # Weekly seasonality: weekends have higher demand
            weekend_boost = 1.3 if day_of_week >= 5 else 1.0

            # Monthly seasonality: end-of-month spike
            day_of_month = date.day
            month_factor = 1.0 + 0.25 * math.sin(2 * math.pi * day_of_month / 30)

            # Slight upward trend over time
            trend = 1.0 + 0.002 * day_offset

            # Random noise
            noise = random.gauss(1.0, 0.15)

            demand = max(0, int(base_demand * weekend_boost * month_factor * trend * noise))

            record = DemandHistory(
                product_id=product.id,
                date=date,
                quantity=demand,
            )
            db.add(record)

    db.commit()
    db.close()
    print(f"✅ Generated {days} days of demand data for {len(products)} products.")


if __name__ == "__main__":
    generate_demand()
