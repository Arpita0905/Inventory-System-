"""
Kaggle-Style Dataset Generator
===============================
Generates a realistic supply-chain inventory dataset modeled after
the Kaggle "Store Item Demand Forecasting" competition format.

Output: backend/data/train.csv
Format: date, store, item, sales, category, unit_cost, lead_time_days

Features realistic patterns:
  - Weekly seasonality (weekends spike)
  - Monthly cycles (end-of-month surges)
  - Yearly seasonality (holiday boosts in Nov–Dec)
  - Gradual upward trend
  - Per-item base demand variation
  - Random promotional spikes
  - Gaussian noise
"""

import os
import math
import random
import csv
from datetime import datetime, timedelta

# ---------- CONFIG ----------
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "train.csv")

NUM_STORES = 3       # Multi-warehouse (3 stores)
NUM_ITEMS = 15       # 15 SKUs per store
DAYS = 365           # 1 year of daily data
START_DATE = datetime(2025, 1, 1)

# Item catalog — (item_id, name, category, base_demand, unit_cost, lead_time)
ITEM_CATALOG = [
    (1,  "Wireless Bluetooth Headphones",   "Electronics",    18, 29.99, 4),
    (2,  "USB-C Fast Charger",              "Electronics",    25, 14.99, 3),
    (3,  "Portable Power Bank 10000mAh",    "Electronics",    15, 24.99, 5),
    (4,  "Smart Watch Band",                "Electronics",    12, 19.99, 4),
    (5,  "Organic Green Tea (100 bags)",    "Groceries",      40, 8.99,  2),
    (6,  "Premium Basmati Rice 5kg",        "Groceries",      35, 12.49, 2),
    (7,  "Cold-Pressed Olive Oil 1L",       "Groceries",      28, 9.99,  3),
    (8,  "Whole Wheat Pasta 500g",          "Groceries",      45, 4.99,  2),
    (9,  "Cotton Crew-Neck T-Shirt",        "Apparel",        20, 15.99, 5),
    (10, "Slim-Fit Denim Jeans",            "Apparel",        10, 39.99, 6),
    (11, "Running Sports Shoes",            "Apparel",         8, 54.99, 7),
    (12, "Stainless Steel Water Bottle",    "Home & Living",  22, 11.99, 3),
    (13, "Scented Soy Candle Set",          "Home & Living",  16, 18.99, 4),
    (14, "Bamboo Cutting Board",            "Home & Living",  12, 13.99, 3),
    (15, "Microfiber Cleaning Cloth 5pk",   "Home & Living",  30, 6.99,  2),
]

# Major holiday boost dates (month, day) — simulate real-world demand spikes
HOLIDAYS = [
    (1, 1),    # New Year
    (1, 26),   # Republic Day (India)
    (2, 14),   # Valentine's Day
    (3, 8),    # Holi (approx.)
    (8, 15),   # Independence Day
    (10, 24),  # Diwali (approx.)
    (11, 1),   # Diwali sales
    (11, 24),  # Black Friday (approx.)
    (12, 25),  # Christmas
    (12, 31),  # New Year's Eve
]


def _is_near_holiday(date, window=3):
    """Check if date is within `window` days of any holiday."""
    for m, d in HOLIDAYS:
        try:
            holiday = datetime(date.year, m, d)
            if abs((date - holiday).days) <= window:
                return True
        except ValueError:
            pass
    return False


def _generate_daily_demand(base_demand, date, day_index):
    """
    Produce a realistic daily demand value with multiple seasonal layers.
    """
    # 1. Day-of-week effect: weekends get 20-40% more traffic
    dow = date.weekday()
    if dow == 5:       # Saturday
        dow_factor = 1.30
    elif dow == 6:     # Sunday
        dow_factor = 1.20
    elif dow == 4:     # Friday
        dow_factor = 1.10
    else:
        dow_factor = 1.0

    # 2. Monthly cycle: end-of-month salary bump
    day_of_month = date.day
    monthly_factor = 1.0 + 0.20 * math.sin(2 * math.pi * day_of_month / 30)

    # 3. Yearly seasonality: Q4 festive boost
    day_of_year = date.timetuple().tm_yday
    yearly_factor = 1.0 + 0.15 * math.sin(2 * math.pi * (day_of_year - 60) / 365)

    # 4. Holiday boost
    holiday_factor = 1.6 if _is_near_holiday(date) else 1.0

    # 5. Random promotional spike (5% chance on any day)
    promo_factor = random.choice([1.0] * 19 + [1.5])

    # 6. Gradual upward trend (0.05% daily growth)
    trend = 1.0 + 0.0005 * day_index

    # 7. Gaussian noise
    noise = random.gauss(1.0, 0.12)

    demand = base_demand * dow_factor * monthly_factor * yearly_factor
    demand *= holiday_factor * promo_factor * trend * noise

    return max(0, int(round(demand)))


def generate_dataset():
    """Generate the full dataset and write to CSV."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    rows = []
    for store_id in range(1, NUM_STORES + 1):
        # Each store has a slightly different demand profile
        store_scale = random.uniform(0.85, 1.15)

        for item_id, name, category, base_demand, unit_cost, lead_time in ITEM_CATALOG:
            # Per-store item variation
            item_base = base_demand * store_scale * random.uniform(0.9, 1.1)

            for day_offset in range(DAYS):
                date = START_DATE + timedelta(days=day_offset)
                sales = _generate_daily_demand(item_base, date, day_offset)

                rows.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "store": store_id,
                    "item": item_id,
                    "item_name": name,
                    "category": category,
                    "sales": sales,
                    "unit_cost": unit_cost,
                    "lead_time_days": lead_time,
                })

    # Shuffle rows for realism (not strictly ordered)
    random.shuffle(rows)

    # Write CSV
    fieldnames = ["date", "store", "item", "item_name", "category",
                  "sales", "unit_cost", "lead_time_days"]

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    total = len(rows)
    print(f"✅ Dataset generated: {OUTPUT_FILE}")
    print(f"   {total:,} rows | {NUM_STORES} stores | {NUM_ITEMS} items | {DAYS} days")
    print(f"   Date range: {START_DATE.strftime('%Y-%m-%d')} to "
          f"{(START_DATE + timedelta(days=DAYS-1)).strftime('%Y-%m-%d')}")

    return OUTPUT_FILE


if __name__ == "__main__":
    generate_dataset()
