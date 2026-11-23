"""Regenerate the SAMPLE data for Mini #23 — Data Visualisation Pack.

Writes the CLEAN Noor Electronics base (the same 32 orders / 52 lines /
PKR 346,800 as Mini #1 / #3 / #22's clean base — the planted mess from
Mini #22 is deliberately NOT reproduced here; this pack charts clean
numbers) plus a small supplementary daily-traffic file for June 2026,
used by technique 8 (seaborn pairplot).

Everything is hard-coded literals: deterministic, no randomness, no
network. Re-running produces byte-identical files.

Run: python3 src/generate_data.py [--out-dir DIR]
"""

import argparse
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"

ORDERS = [
    # order_id, customer_id, order_date
    (1, 1, "2026-01-08"), (2, 1, "2026-02-14"), (3, 1, "2026-04-02"),
    (4, 2, "2026-01-15"), (5, 2, "2026-03-20"), (6, 2, "2026-05-11"),
    (7, 3, "2026-01-22"), (8, 3, "2026-02-28"), (9, 3, "2026-06-05"),
    (10, 4, "2026-02-05"), (11, 4, "2026-04-18"), (12, 5, "2026-02-12"),
    (13, 5, "2026-05-25"), (14, 6, "2026-03-03"), (15, 6, "2026-03-29"),
    (16, 6, "2026-06-12"), (17, 7, "2026-03-15"), (18, 7, "2026-04-22"),
    (19, 8, "2026-01-30"), (20, 8, "2026-05-08"), (21, 9, "2026-04-10"),
    (22, 9, "2026-06-20"), (23, 10, "2026-04-15"), (24, 10, "2026-05-30"),
    (25, 1, "2026-06-18"), (26, 2, "2026-06-25"), (27, 4, "2026-06-02"),
    (28, 5, "2026-01-19"), (29, 7, "2026-06-28"), (30, 8, "2026-02-21"),
    (31, 9, "2026-02-08"), (32, 3, "2026-05-14"),
]

ITEMS = [
    # line_id, order_id, product_id, quantity, unit_price_pkr
    (1, 1, 1, 2, 2500), (2, 1, 6, 3, 1200), (3, 2, 2, 1, 8500),
    (4, 2, 7, 2, 3200), (5, 3, 4, 1, 18000), (6, 4, 1, 1, 2500),
    (7, 4, 3, 1, 4500), (8, 5, 8, 1, 14500), (9, 6, 2, 1, 8500),
    (10, 6, 5, 2, 4200), (11, 7, 6, 5, 1200), (12, 8, 1, 2, 2500),
    (13, 8, 7, 1, 3200), (14, 9, 3, 1, 4500), (15, 9, 8, 1, 14500),
    (16, 10, 5, 1, 4200), (17, 11, 4, 1, 18000), (18, 11, 6, 2, 1200),
    (19, 12, 7, 3, 3200), (20, 13, 2, 1, 8500), (21, 13, 1, 1, 2500),
    (22, 14, 6, 4, 1200), (23, 15, 1, 1, 2500), (24, 15, 5, 1, 4200),
    (25, 16, 8, 1, 14500), (26, 17, 3, 1, 4500), (27, 18, 2, 1, 8500),
    (28, 18, 7, 2, 3200), (29, 19, 1, 3, 2500), (30, 20, 4, 1, 18000),
    (31, 21, 6, 2, 1200), (32, 22, 8, 1, 14500), (33, 22, 5, 1, 4200),
    (34, 23, 7, 2, 3200), (35, 24, 2, 1, 8500), (36, 25, 5, 2, 4200),
    (37, 25, 6, 3, 1200), (38, 26, 1, 2, 2500), (39, 27, 3, 1, 4500),
    (40, 27, 1, 1, 2500), (41, 28, 6, 4, 1200), (42, 29, 4, 1, 18000),
    (43, 30, 5, 1, 4200), (44, 30, 7, 1, 3200), (45, 31, 1, 1, 2500),
    (46, 32, 2, 1, 8500), (47, 32, 6, 2, 1200), (48, 1, 7, 1, 3200),
    (49, 6, 7, 1, 3200), (50, 10, 7, 1, 3200), (51, 20, 6, 1, 1200),
    (52, 24, 7, 1, 3200),
]

PRODUCTS = [
    # product_id, product_name, category, price_pkr
    (1, "Wireless Mouse", "Electronics", 2500),
    (2, "Mechanical Keyboard", "Electronics", 8500),
    (3, "Laptop Stand", "Electronics", 4500),
    (4, "Office Chair", "Furniture", 18000),
    (5, "Desk Lamp", "Furniture", 4200),
    (6, "Notebook Set", "Stationery", 1200),
    (7, "Ceramic Mug Set", "Kitchen", 3200),
    (8, "Dinner Set 24pc", "Kitchen", 14500),
    (9, "Bluetooth Speaker", "Electronics", 6500),
]

# June 2026 daily traffic. The 7 order days match the 7 June orders in
# orders_SAMPLE.csv exactly (2, 5, 12, 18, 20, 25, 28 Jun).
TRAFFIC = [
    # date, website_sessions, store_visitors, ad_spend_pkr, orders
    ("2026-06-01", 210, 68, 1200, 0), ("2026-06-02", 185, 54, 1000, 1),
    ("2026-06-03", 240, 71, 1400, 0), ("2026-06-04", 196, 60, 1100, 0),
    ("2026-06-05", 268, 84, 1600, 1), ("2026-06-06", 310, 102, 1900, 0),
    ("2026-06-07", 295, 95, 1800, 0), ("2026-06-08", 178, 49, 900, 0),
    ("2026-06-09", 225, 66, 1300, 0), ("2026-06-10", 242, 73, 1450, 0),
    ("2026-06-11", 201, 58, 1150, 0), ("2026-06-12", 287, 89, 1750, 1),
    ("2026-06-13", 331, 110, 2100, 0), ("2026-06-14", 305, 97, 1850, 0),
    ("2026-06-15", 189, 52, 950, 0), ("2026-06-16", 214, 63, 1250, 0),
    ("2026-06-17", 256, 78, 1500, 0), ("2026-06-18", 233, 70, 1400, 1),
    ("2026-06-19", 274, 86, 1650, 0), ("2026-06-20", 342, 118, 2200, 1),
    ("2026-06-21", 318, 104, 2000, 0), ("2026-06-22", 197, 57, 1100, 0),
    ("2026-06-23", 229, 69, 1350, 0), ("2026-06-24", 261, 82, 1550, 0),
    ("2026-06-25", 248, 76, 1500, 1), ("2026-06-26", 289, 91, 1750, 0),
    ("2026-06-27", 356, 121, 2300, 0), ("2026-06-28", 329, 108, 2050, 1),
    ("2026-06-29", 203, 59, 1150, 0), ("2026-06-30", 238, 72, 1400, 0),
]


def write_csv(path, header, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def main(out_dir=None):
    out = Path(out_dir) if out_dir else RAW
    write_csv(out / "orders_SAMPLE.csv",
              ["order_id", "customer_id", "order_date"], ORDERS)
    write_csv(out / "order_items_SAMPLE.csv",
              ["line_id", "order_id", "product_id", "quantity",
               "unit_price_pkr"], ITEMS)
    write_csv(out / "products_SAMPLE.csv",
              ["product_id", "product_name", "category", "price_pkr"],
              PRODUCTS)
    write_csv(out / "daily_traffic_SAMPLE.csv",
              ["date", "website_sessions", "store_visitors",
               "ad_spend_pkr", "orders"], TRAFFIC)
    total = sum(q * p for _, _, _, q, p in ITEMS)
    print(f"wrote 4 files to {out}")
    print(f"orders={len(ORDERS)} lines={len(ITEMS)} revenue=PKR {total:,}"
          f" traffic_days={len(TRAFFIC)}"
          f" traffic_orders={sum(t[4] for t in TRAFFIC)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default=None)
    main(ap.parse_args().out_dir)
