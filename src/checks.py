"""Independent checks for Mini #23 — Data Visualisation Pack.

Recomputes EVERY headline number from data/raw/*_SAMPLE.csv with the
standard library only (no pandas, no numpy, no matplotlib), then
compares against every output CSV, outputs/summary.json,
outputs/findings.md and README.md, and verifies every chart PNG is a
real, non-trivial image. Also verifies the generator is deterministic
by re-running it to a temp dir and byte-comparing.

Run: python3 src/checks.py
Exit code 0 = all checks pass. Any failure is a build bug — fix the
build, never weaken the check.
"""

import csv
import hashlib
import json
import math
import struct
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "outputs"

MONTHS = ["2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06"]
CATEGORIES = ["Electronics", "Furniture", "Kitchen", "Stationery"]
BIN_EDGES = [0, 5000, 10000, 15000, 20000, 25000]

PASSED = 0
FAILED = []


def check(name, ok, detail=""):
    global PASSED
    if ok:
        PASSED += 1
    else:
        FAILED.append(f"{name} :: {detail}")


def rows(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def quantile(sorted_vals, q):
    """Linear-interpolation quantile, matching pandas default."""
    n = len(sorted_vals)
    pos = (n - 1) * q
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return float(sorted_vals[int(pos)])
    return sorted_vals[lo] + (pos - lo) * (sorted_vals[hi] - sorted_vals[lo])


def pearson(xs, ys):
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    vx = sum((x - mx) ** 2 for x in xs)
    vy = sum((y - my) ** 2 for y in ys)
    return cov / math.sqrt(vx * vy)


def png_size(path):
    """(width, height) from a PNG IHDR chunk, or None if not a PNG."""
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    w, h = struct.unpack(">II", data[16:24])
    return w, h


def main():
    # ================= raw files =================
    orders = rows(RAW / "orders_SAMPLE.csv")
    items = rows(RAW / "order_items_SAMPLE.csv")
    products = rows(RAW / "products_SAMPLE.csv")
    traffic = rows(RAW / "daily_traffic_SAMPLE.csv")

    check("orders: 32 rows", len(orders) == 32, str(len(orders)))
    check("orders: ids 1..32 unique",
          sorted(int(r["order_id"]) for r in orders) == list(range(1, 33)))
    check("orders: all customer ids are plain numbers",
          all(r["customer_id"].isdigit() for r in orders))
    order_date = {int(r["order_id"]): r["order_date"] for r in orders}

    check("items: 52 rows", len(items) == 52, str(len(items)))
    check("items: line ids 1..52 unique",
          sorted(int(r["line_id"]) for r in items) == list(range(1, 53)))
    rev = {int(r["line_id"]): int(r["quantity"]) * int(r["unit_price_pkr"])
           for r in items}
    check("items: total revenue PKR 346,800",
          sum(rev.values()) == 346800, str(sum(rev.values())))
    check("items: total units 81",
          sum(int(r["quantity"]) for r in items) == 81)
    check("items: max quantity 5",
          max(int(r["quantity"]) for r in items) == 5)
    check("items: max line revenue PKR 18,000",
          max(rev.values()) == 18000)

    check("products: 9 rows", len(products) == 9)
    check("products: ids 1..9 unique, no duplicate key",
          sorted(int(r["product_id"]) for r in products)
          == list(range(1, 10)))
    prod_cat = {r["product_id"]: r["category"] for r in products}
    prod_name = {r["product_id"]: r["product_name"] for r in products}

    check("traffic: 30 rows (June days)", len(traffic) == 30)
    check("traffic: dates 2026-06-01..30 in order",
          [r["date"] for r in traffic]
          == [f"2026-06-{d:02d}" for d in range(1, 31)])
    check("traffic: 7 order days",
          sum(int(r["orders"]) for r in traffic) == 7)
    june_order_days = sorted(o for o in order_date.values()
                             if o.startswith("2026-06"))
    check("traffic: order days are the 7 June order dates",
          sorted(r["date"] for r in traffic if r["orders"] == "1")
          == june_order_days, str(june_order_days))
    check("traffic: sessions total 7,649",
          sum(int(r["website_sessions"]) for r in traffic) == 7649)
    check("traffic: visitors total 2,382",
          sum(int(r["store_visitors"]) for r in traffic) == 2382)
    check("traffic: ad spend total PKR 45,600",
          sum(int(r["ad_spend_pkr"]) for r in traffic) == 45600)

    # ================= recomputed aggregates =================
    monthly_rev = defaultdict(int)
    monthly_orders = defaultdict(set)
    cat_rev = defaultdict(int)
    cat_lines = defaultdict(int)
    catmon = defaultdict(int)
    order_val = defaultdict(int)
    for r in items:
        m = order_date[int(r["order_id"])][:7]
        c = prod_cat[r["product_id"]]
        monthly_rev[m] += rev[int(r["line_id"])]
        monthly_orders[m].add(int(r["order_id"]))
        cat_rev[c] += rev[int(r["line_id"])]
        cat_lines[c] += 1
        catmon[(m, c)] += rev[int(r["line_id"])]
        order_val[int(r["order_id"])] += rev[int(r["line_id"])]
    for c in CATEGORIES:
        for m in MONTHS:
            catmon.setdefault((m, c), 0)

    check("monthly revenue sums to PKR 346,800",
          sum(monthly_rev.values()) == 346800)
    check("monthly revenue",
          dict(monthly_rev) == {"2026-01": 37100, "2026-02": 50000,
                                "2026-03": 30500, "2026-04": 62100,
                                "2026-05": 72900, "2026-06": 94200},
          str(dict(monthly_rev)))
    check("orders per month",
          {m: len(monthly_orders[m]) for m in MONTHS}
          == {"2026-01": 5, "2026-02": 6, "2026-03": 4, "2026-04": 5,
              "2026-05": 5, "2026-06": 7})
    check("category revenue",
          dict(cat_rev) == {"Electronics": 104000, "Furniture": 105600,
                            "Kitchen": 106000, "Stationery": 31200},
          str(dict(cat_rev)))
    check("category lines",
          dict(cat_lines) == {"Electronics": 19, "Furniture": 10,
                              "Kitchen": 14, "Stationery": 9})
    check("cat x month: 2 zero cells (Jan Furniture, Feb Stationery)",
          sum(1 for v in catmon.values() if v == 0) == 2
          and catmon[("2026-01", "Furniture")] == 0
          and catmon[("2026-02", "Stationery")] == 0)
    check("cat x month: hottest cell Jun Kitchen PKR 43,500",
          max(catmon.items(), key=lambda kv: kv[1])
          == (("2026-06", "Kitchen"), 43500))
    check("cat x month: coldest nonzero cell Jan Kitchen PKR 3,200",
          min((kv for kv in catmon.items() if kv[1] > 0),
              key=lambda kv: kv[1]) == (("2026-01", "Kitchen"), 3200))

    vals = sorted(order_val.values())
    check("order values: 32 orders", len(vals) == 32)
    check("order values: min 2,400 / max 20,400",
          vals[0] == 2400 and vals[-1] == 20400)
    check("order values: mean PKR 10,837.50",
          abs(sum(vals) / 32 - 10837.5) < 1e-9, str(sum(vals) / 32))
    check("order values: median PKR 10,250",
          (vals[15] + vals[16]) / 2 == 10250)
    bins = [sum(1 for v in vals if BIN_EDGES[i] <= v < BIN_EDGES[i + 1])
            for i in range(5)]
    check("histogram bins [5, 11, 9, 5, 2]", bins == [5, 11, 9, 5, 2],
          str(bins))
    check("orders PKR 5,000-15,000: 20 (62.5%)",
          bins[1] + bins[2] == 20)

    # box stats per category (line revenue)
    cat_line_vals = defaultdict(list)
    for r in items:
        cat_line_vals[prod_cat[r["product_id"]]].append(
            rev[int(r["line_id"])])
    exp_box = {
        "Electronics": (2500, 3500.0, 5000.0, 8500.0, 8500),
        "Furniture": (4200, 4200.0, 8400.0, 18000.0, 18000),
        "Kitchen": (3200, 3200.0, 6400.0, 13275.0, 14500),
        "Stationery": (1200, 2400.0, 3600.0, 4800.0, 6000),
    }
    for c in CATEGORIES:
        s = sorted(cat_line_vals[c])
        got = (s[0], quantile(s, 0.25), quantile(s, 0.5),
               quantile(s, 0.75), s[-1])
        check(f"box {c} (min, q1, median, q3, max)",
              got == exp_box[c], f"got {got} want {exp_box[c]}")

    r_qty = pearson([int(r["quantity"]) for r in items],
                    [rev[int(r["line_id"])] for r in items])
    check("scatter: quantity vs revenue r rounds to -0.151",
          round(r_qty, 3) == -0.151, str(round(r_qty, 3)))
    r_sv = pearson([int(r["website_sessions"]) for r in traffic],
                   [int(r["store_visitors"]) for r in traffic])
    check("traffic: sessions vs visitors r rounds to 0.995",
          round(r_sv, 3) == 0.995, str(round(r_sv, 3)))
    r_sa = pearson([int(r["website_sessions"]) for r in traffic],
                   [int(r["ad_spend_pkr"]) for r in traffic])
    check("traffic: sessions vs ad spend r rounds to 0.997",
          round(r_sa, 3) == 0.997, str(round(r_sa, 3)))
    check("traffic: conversion 7 / 7,649 = 0.092%",
          round(7 / 7649 * 100, 3) == 0.092)

    mom = {}
    prev = None
    for m in MONTHS:
        mom[m] = None if prev is None else round(
            (monthly_rev[m] / prev - 1) * 100, 2)
        prev = monthly_rev[m]
    check("MoM growth",
          mom == {"2026-01": None, "2026-02": 34.77, "2026-03": -39.0,
                  "2026-04": 103.61, "2026-05": 17.39, "2026-06": 29.22},
          str(mom))
    check("Jan to Jun growth +153.91%",
          round((94200 / 37100 - 1) * 100, 2) == 153.91)
    check("June share of total 27.16%",
          round(94200 / 346800 * 100, 2) == 27.16)

    per_cat_peak = {}
    for c in CATEGORIES:
        best_m = max(MONTHS, key=lambda m: catmon[(m, c)])
        per_cat_peak[c] = (best_m, catmon[(best_m, c)])
    check("per-category peak months",
          per_cat_peak == {"Electronics": ("2026-05", 36500),
                           "Furniture": ("2026-04", 36000),
                           "Kitchen": ("2026-06", 43500),
                           "Stationery": ("2026-01", 14400)},
          str(per_cat_peak))

    # ================= summary.json =================
    summary = json.loads((OUT / "summary.json").read_text())
    exp = {
        "clean_orders": 32, "clean_lines": 52, "clean_revenue_pkr": 346800,
        "peak_month": "2026-06", "peak_month_revenue_pkr": 94200,
        "peak_month_orders": 7, "peak_month_share_pct": 27.16,
        "lowest_month": "2026-03", "lowest_month_revenue_pkr": 30500,
        "jan_to_jun_growth_pct": 153.91,
        "top_category": "Kitchen", "top_category_revenue_pkr": 106000,
        "smallest_category": "Stationery",
        "smallest_category_revenue_pkr": 31200,
        "zero_revenue_cells": 2,
        "order_value_min_pkr": 2400, "order_value_max_pkr": 20400,
        "order_value_mean_pkr": 10837.5, "order_value_median_pkr": 10250.0,
        "orders_in_5k_to_15k": 20, "orders_in_5k_to_15k_pct": 62.5,
        "scatter_quantity_revenue_pearson_r": -0.151,
        "total_units_sold": 81, "max_quantity_on_a_line": 5,
        "single_line_max_revenue_pkr": 18000,
        "june_traffic_days": 30, "june_traffic_sessions": 7649,
        "june_traffic_visitors": 2382, "june_traffic_ad_spend_pkr": 45600,
        "june_traffic_orders": 7, "june_traffic_conversion_pct": 0.092,
        "june_traffic_sessions_visitors_pearson_r": 0.995,
        "june_traffic_sessions_adspend_pearson_r": 0.997,
        "march_revenue_pkr": 30500, "march_orders": 4,
    }
    for k, v in exp.items():
        check(f"summary.json {k} == {v}", summary.get(k) == v,
              f"got {summary.get(k)}")
    check("summary.json monthly revenue",
          summary.get("monthly_revenue_pkr")
          == {m: monthly_rev[m] for m in MONTHS})
    check("summary.json orders per month",
          summary.get("orders_per_month")
          == {m: len(monthly_orders[m]) for m in MONTHS})
    check("summary.json category revenue",
          summary.get("revenue_by_category_pkr") == dict(cat_rev))
    check("summary.json category shares",
          summary.get("category_share_pct")
          == {"Kitchen": 30.57, "Furniture": 30.45,
              "Electronics": 29.99, "Stationery": 9.0})
    check("summary.json category lines",
          summary.get("category_lines") == dict(cat_lines))
    check("summary.json category x month",
          summary.get("category_by_month_pkr")
          == {m: {c: catmon[(m, c)] for c in CATEGORIES} for m in MONTHS})
    check("summary.json zero cells list",
          summary.get("zero_revenue_cells_list")
          == ["2026-01 Furniture", "2026-02 Stationery"])
    check("summary.json histogram bins",
          summary.get("histogram_bin_counts") == [5, 11, 9, 5, 2]
          and summary.get("histogram_bin_edges_pkr") == BIN_EDGES)
    for c in CATEGORIES:
        s = sorted(cat_line_vals[c])
        got = summary["boxplot_line_revenue_by_category"][c]
        check(f"summary.json box {c}",
              got == {"min_pkr": s[0], "q1_pkr": quantile(s, 0.25),
                      "median_pkr": quantile(s, 0.5),
                      "q3_pkr": quantile(s, 0.75), "max_pkr": s[-1],
                      "lines": len(s)}, str(got))
    check("summary.json hottest cell",
          summary.get("heatmap_hottest_cell")
          == {"month": "2026-06", "category": "Kitchen",
              "revenue_pkr": 43500})
    check("summary.json coldest nonzero cell",
          summary.get("heatmap_coldest_nonzero_cell")
          == {"month": "2026-01", "category": "Kitchen",
              "revenue_pkr": 3200})
    check("summary.json MoM growth", summary.get("mom_growth_pct") == mom)
    check("summary.json AOV by month",
          summary.get("avg_order_value_by_month_pkr")
          == {m: round(monthly_rev[m] / len(monthly_orders[m]), 2)
              for m in MONTHS})
    check("summary.json per-category peak months",
          summary.get("per_category_peak_month")
          == {c: {"month": per_cat_peak[c][0],
                   "revenue_pkr": per_cat_peak[c][1]}
              for c in CATEGORIES})
    check("summary.json June order days",
          summary.get("june_traffic_order_days") == june_order_days)
    check("summary.json technique row counts",
          summary.get("technique_files")
          == {"t1_rows": 6, "t2_rows": 4, "t3_rows": 24, "t4_rows": 5,
              "t5_rows": 52, "t6_rows": 52, "t7_rows": 6, "t8_rows": 30,
              "t9_rows": 6, "t10_rows": 24})

    # ================= technique CSVs =================
    def check_header(name, got, want):
        check(f"{name} header", got == want, f"got {got}")

    t1 = rows(OUT / "technique_01_monthly_revenue.csv")
    check_header("t1", list(t1[0].keys()),
                 ["month", "revenue_pkr", "orders", "avg_order_value_pkr"])
    check("t1: 6 rows", len(t1) == 6)
    for r in t1:
        m = r["month"]
        check(f"t1 {m} revenue", int(r["revenue_pkr"]) == monthly_rev[m])
        check(f"t1 {m} orders",
              int(r["orders"]) == len(monthly_orders[m]))
        check(f"t1 {m} AOV",
              abs(float(r["avg_order_value_pkr"])
                  - monthly_rev[m] / len(monthly_orders[m])) < 0.01)

    t2 = rows(OUT / "technique_02_revenue_by_category.csv")
    check_header("t2", list(t2[0].keys()),
                 ["category", "revenue_pkr", "lines", "share_pct"])
    check("t2: 4 rows, largest first",
          len(t2) == 4 and [r["category"] for r in t2]
          == ["Kitchen", "Furniture", "Electronics", "Stationery"])
    check("t2: revenues sum to PKR 346,800",
          sum(int(r["revenue_pkr"]) for r in t2) == 346800)
    for r in t2:
        c = r["category"]
        check(f"t2 {c} revenue", int(r["revenue_pkr"]) == cat_rev[c])
        check(f"t2 {c} lines", int(r["lines"]) == cat_lines[c])
        check(f"t2 {c} share",
              abs(float(r["share_pct"]) - cat_rev[c] / 346800 * 100) < 0.01)

    t3 = rows(OUT / "technique_03_category_by_month.csv")
    check_header("t3", list(t3[0].keys()),
                 ["month", "category", "revenue_pkr"])
    check("t3: 24 rows", len(t3) == 24)
    check("t3: every cell matches catmon",
          all(int(r["revenue_pkr"]) == catmon[(r["month"], r["category"])]
              for r in t3))
    check("t3: sums to PKR 346,800",
          sum(int(r["revenue_pkr"]) for r in t3) == 346800)

    t4 = rows(OUT / "technique_04_order_value_histogram.csv")
    check_header("t4", list(t4[0].keys()),
                 ["bin_start_pkr", "bin_end_pkr", "orders", "share_pct"])
    check("t4: 5 rows, counts [5, 11, 9, 5, 2]",
          len(t4) == 5
          and [int(r["orders"]) for r in t4] == [5, 11, 9, 5, 2])
    check("t4: bins are the PKR 5,000 edges",
          [(int(r["bin_start_pkr"]), int(r["bin_end_pkr"])) for r in t4]
          == [(0, 5000), (5000, 10000), (10000, 15000),
              (15000, 20000), (20000, 25000)])
    check("t4: shares sum to 100",
          abs(sum(float(r["share_pct"]) for r in t4) - 100) < 0.01)

    t5 = rows(OUT / "technique_05_line_revenue_by_category.csv")
    check_header("t5", list(t5[0].keys()),
                 ["line_id", "category", "line_revenue_pkr"])
    check("t5: 52 rows", len(t5) == 52)
    check("t5: line revenues match raw",
          all(int(r["line_revenue_pkr"]) == rev[int(r["line_id"])]
              for r in t5))
    check("t5: categories match catalogue",
          all(r["category"] == prod_cat[next(
              x["product_id"] for x in items
              if x["line_id"] == r["line_id"])] for r in t5))

    t6 = rows(OUT / "technique_06_quantity_vs_revenue.csv")
    check_header("t6", list(t6[0].keys()),
                 ["line_id", "product_name", "category", "quantity",
                  "unit_price_pkr", "line_revenue_pkr"])
    check("t6: 52 rows", len(t6) == 52)
    for r in t6:
        src = next(x for x in items if x["line_id"] == r["line_id"])
        check(f"t6 line {r['line_id']} qty x price = revenue",
              int(r["line_revenue_pkr"]) == int(r["quantity"])
              * int(r["unit_price_pkr"])
              and int(r["quantity"]) == int(src["quantity"])
              and int(r["unit_price_pkr"]) == int(src["unit_price_pkr"]))
        check(f"t6 line {r['line_id']} product name",
              r["product_name"] == prod_name[src["product_id"]])

    t7 = rows(OUT / "technique_07_category_month_heatmap.csv")
    check_header("t7", list(t7[0].keys()),
                 ["month"] + CATEGORIES)
    check("t7: 6 rows", len(t7) == 6)
    check("t7: matrix matches catmon",
          all(int(r[c]) == catmon[(r["month"], c)]
              for r in t7 for c in CATEGORIES))

    t8 = rows(OUT / "technique_08_june_daily_traffic.csv")
    check_header("t8", list(t8[0].keys()),
                 ["date", "website_sessions", "store_visitors",
                  "ad_spend_pkr", "orders"])
    check("t8: 30 rows", len(t8) == 30)
    check("t8: rows match the raw traffic file",
          all(r == {k: str(v) for k, v in raw.items()}
              for r, raw in zip(t8, traffic)))
    check("t8: orders sum to 7",
          sum(int(r["orders"]) for r in t8) == 7)

    t9 = rows(OUT / "technique_09_revenue_and_orders.csv")
    check_header("t9", list(t9[0].keys()),
                 ["month", "revenue_pkr", "orders", "revenue_share_pct"])
    check("t9: 6 rows", len(t9) == 6)
    check("t9: revenue and orders match t1",
          all(int(a["revenue_pkr"]) == int(b["revenue_pkr"])
              and int(a["orders"]) == int(b["orders"])
              for a, b in zip(t9, t1)))
    check("t9: shares sum to 100",
          abs(sum(float(r["revenue_share_pct"]) for r in t9) - 100) < 0.01)

    t10 = rows(OUT / "technique_10_monthly_trend_per_category.csv")
    check_header("t10", list(t10[0].keys()),
                 ["month", "category", "revenue_pkr",
                  "share_of_category_pct"])
    check("t10: 24 rows", len(t10) == 24)
    check("t10: every cell matches catmon",
          all(int(r["revenue_pkr"]) == catmon[(r["month"], r["category"])]
              for r in t10))
    check("t10: shares within each category sum to 100",
          all(abs(sum(float(r["share_of_category_pct"]) for r in t10
                      if r["category"] == c) - 100) < 0.02
              for c in CATEGORIES))

    # ================= chart PNGs =================
    for i in range(1, 11):
        pngs = list(OUT.glob(f"technique_{i:02d}_*.png"))
        check(f"chart {i:02d}: exactly one PNG", len(pngs) == 1,
              str([p.name for p in pngs]))
        if len(pngs) == 1:
            p = pngs[0]
            size = png_size(p)
            check(f"chart {i:02d}: valid PNG header", size is not None)
            check(f"chart {i:02d}: non-trivial size (>10 KB)",
                  p.stat().st_size > 10_000,
                  str(p.stat().st_size))
            check(f"chart {i:02d}: at least 800x500 px",
                  size is not None and size[0] >= 800 and size[1] >= 500,
                  str(size))

    # ================= findings.md / README.md =================
    findings = (OUT / "findings.md").read_text()
    readme = (ROOT / "README.md").read_text()
    for label, text in [("findings.md", findings), ("README.md", readme)]:
        for needle in ["SAMPLE", "346,800", "94,200", "106,000", "30,500",
                       "43,500", "7,649", "45,600", "10,250", "10,837.50",
                       "2,400", "20,400", "3,200", "153.91", "62.50",
                       "27.16", "0.092", "-0.151", "81", "32", "52"]:
            check(f"{label} contains {needle!r}", needle in text)
        check(f"{label} never claims real client work",
              "real client" not in text.lower()
              or "never claimed as real client work" in text.lower())

    # ================= generator determinism =================
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        proc = subprocess.run(
            [sys.executable, str(ROOT / "src" / "generate_data.py"),
             "--out-dir", str(td)],
            capture_output=True, text=True)
        check("generator re-runs cleanly", proc.returncode == 0,
              proc.stderr[-300:])
        if proc.returncode == 0:
            for src in sorted(RAW.glob("*.csv")):
                regen = td / src.name
                check(f"generator deterministic: {src.name}",
                      regen.exists()
                      and hashlib.sha256(src.read_bytes()).hexdigest()
                      == hashlib.sha256(regen.read_bytes()).hexdigest())

    # ================= build reproducibility =================
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        proc = subprocess.run(
            [sys.executable, str(ROOT / "src" / "build_charts.py")],
            capture_output=True, text=True, cwd=str(ROOT))
        check("build_charts.py re-runs cleanly", proc.returncode == 0,
              proc.stderr[-300:])
        if proc.returncode == 0:
            summ2 = json.loads((OUT / "summary.json").read_text())
            check("build is reproducible (summary.json stable)",
                  summ2 == summary)

    # ================= repo furniture =================
    req = (ROOT / "requirements.txt").read_text()
    check("requirements.txt pins pandas + matplotlib + seaborn",
          "pandas" in req and "matplotlib" in req and "seaborn" in req)
    check(".gitignore exists", (ROOT / ".gitignore").exists())
    check("data/README.md exists", (ROOT / "data" / "README.md").exists())
    check("run_tests.py exists", (ROOT / "src" / "run_tests.py").exists())

    print(f"{PASSED} checks passed, {len(FAILED)} failed")
    if FAILED:
        print("FAILURES:")
        for f in FAILED:
            print(" -", f)
        sys.exit(1)


if __name__ == "__main__":
    main()
