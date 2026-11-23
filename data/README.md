# Mini #23 — data dictionary (SAMPLE / DEMO only)

Fictional store "Noor Electronics" — the same made-up Pakistani
electronics store as Mini #1 / #3 / #19 / #22, Jan–Jun 2026. The
store, the sales and every number are invented for teaching — the
visualisation techniques are real, the business is not. Regenerate
exactly with `python3 src/generate_data.py` (deterministic, no
randomness). Build the charts with `python3 src/build_charts.py`.

## The clean base (Mini #1 / #3)

- **32 orders, 52 order lines, PKR 346,800 total revenue.**
  10 buying customers, 8 sold products, Jan–Jun 2026.
- The clean totals reconcile exactly with Mini #1, Mini #3 and
  Mini #22's clean base: monthly revenue sums to PKR 346,800,
  category revenue sums to PKR 346,800, and order values sum to
  PKR 346,800.
- Unlike Mini #22, this pack charts the **clean** base only: the
  planted mess (duplicate keys, orphan lines, the bad customer
  key) is not reproduced here — a visualisation pack needs true
  numbers to chart, and the mess already has its own pack.

## data/raw/orders_SAMPLE.csv (32 rows)

| Column | Meaning |
|---|---|
| `order_id` | Order number, 1–32 |
| `customer_id` | Buyer — 1–10 |
| `order_date` | Order date, ISO `yyyy-mm-dd`, 2026-01-08 – 2026-06-28 |

## data/raw/order_items_SAMPLE.csv (52 rows)

| Column | Meaning |
|---|---|
| `line_id` | Order-line number, 1–52 |
| `order_id` | Order the line belongs to |
| `product_id` | Product — 1–8 (product 9 never sold) |
| `quantity` | Units on the line (1–5) |
| `unit_price_pkr` | Price actually charged on the line, PKR |

Line revenue is always `quantity × unit_price_pkr`. The 52 lines
total PKR 346,800; 81 units in total.

## data/raw/products_SAMPLE.csv (9 rows)

| Column | Meaning |
|---|---|
| `product_id` | Product number, 1–9 (each listed once — clean catalogue) |
| `product_name` | Product name |
| `category` | Electronics, Furniture, Stationery, Kitchen |
| `price_pkr` | Current catalogue price, PKR |

Product 9 (Bluetooth Speaker, PKR 6,500) never sold — it is the
product the catalogue carries but no chart can show, because it
has no revenue. Four categories: Electronics (3 products),
Furniture (2), Stationery (1), Kitchen (2).

## data/raw/daily_traffic_SAMPLE.csv (30 rows)

Supplementary file for technique 8 (seaborn pairplot) — the only
file that is not the Noor order book.

| Column | Meaning |
|---|---|
| `date` | Day in June 2026, ISO `yyyy-mm-dd` |
| `website_sessions` | Website sessions that day |
| `store_visitors` | In-store visitors that day |
| `ad_spend_pkr` | Ad spend that day, PKR |
| `orders` | Orders placed that day (0 or 1) |

Totals: 7,649 sessions, 2,382 visitors, PKR 45,600 ad spend,
7 orders — a 0.092% session-to-order conversion. The 7 order days
(2, 5, 12, 18, 20, 25, 28 June) are exactly the 7 June order
dates in `orders_SAMPLE.csv`, so the traffic file reconciles with
the order book instead of floating free.

## Totals (verified)

- 32 clean orders, 52 clean lines, total revenue PKR 346,800.
- Monthly revenue: Jan 37,100 · Feb 50,000 · Mar 30,500 ·
  Apr 62,100 · May 72,900 · Jun 94,200.
- Revenue by category: Electronics PKR 104,000 · Furniture
  PKR 105,600 · Kitchen PKR 106,000 · Stationery PKR 31,200.
- Order values: min PKR 2,400 · median PKR 10,250 · mean
  PKR 10,837.50 · max PKR 20,400.
- Every clean line satisfies `revenue = quantity × unit_price_pkr`
  (checked by `src/checks.py`).

## Known quirks

- **SAMPLE data only.** The store, the sales and the "findings"
  are invented to teach the techniques.
- **One shop, six months, 52 lines.** The patterns scale — the
  row counts do not. A histogram of 32 orders shows the shape of
  the bins, not a law of the market.
- **The traffic file is illustrative, not causal.** Sessions,
  visitors and ad spend move together (r ≈ 0.995–0.997) because
  they were written to move together; the pack uses them to teach
  pairplots, not to prove that ads cause orders.
