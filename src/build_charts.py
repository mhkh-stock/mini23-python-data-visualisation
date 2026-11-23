"""Build Mini #23 — Python Data Visualisation Pack (matplotlib + seaborn).

Reads the clean Noor Electronics SAMPLE data (32 orders / 52 lines /
PKR 346,800, Jan-Jun 2026) plus the June daily-traffic file, and builds
ten charts — one PNG + one CSV of the plotted values per technique —
plus outputs/summary.json and outputs/findings.md.

Run: python3 src/build_charts.py
"""

import json
import math
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import seaborn as sns

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "outputs"

SOURCE = "Source: SAMPLE data \u2014 Noor Electronics (fictional store), Jan\u2013Jun 2026"
MONTHS = ["2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06"]
MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
CATEGORIES = ["Electronics", "Furniture", "Kitchen", "Stationery"]
CAT_COLORS = {"Electronics": "#1f77b4", "Furniture": "#ff7f0e",
              "Kitchen": "#2ca02c", "Stationery": "#9467bd"}
BIN_EDGES = [0, 5000, 10000, 15000, 20000, 25000]

plt.rcParams.update({
    "font.size": 11, "axes.titlesize": 14, "axes.titleweight": "bold",
    "axes.labelsize": 11, "xtick.labelsize": 10, "ytick.labelsize": 10,
    "figure.dpi": 150,
})


def pkr(x):
    """PKR axis formatter: 94,200 -> '94k' style is avoided; use commas."""
    return f"{int(x):,}"


def style_ax(ax, title, xlabel, ylabel):
    ax.set_title(title, loc="left", pad=12)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", alpha=0.3)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def save(fig, name):
    fig.text(0.01, 0.005, SOURCE, fontsize=8, color="#666666")
    fig.savefig(OUT / name, bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {name}")


def load():
    orders = pd.read_csv(RAW / "orders_SAMPLE.csv", parse_dates=["order_date"])
    items = pd.read_csv(RAW / "order_items_SAMPLE.csv")
    products = pd.read_csv(RAW / "products_SAMPLE.csv")
    traffic = pd.read_csv(RAW / "daily_traffic_SAMPLE.csv", parse_dates=["date"])
    items["line_revenue_pkr"] = items["quantity"] * items["unit_price_pkr"]
    df = (items.merge(products, on="product_id")
               .merge(orders[["order_id", "order_date"]], on="order_id"))
    df["month"] = df["order_date"].dt.strftime("%Y-%m")
    return df, traffic


def monthly_table(df):
    m = (df.groupby("month")
           .agg(revenue_pkr=("line_revenue_pkr", "sum"),
                orders=("order_id", "nunique"))
           .reindex(MONTHS))
    m["avg_order_value_pkr"] = (m["revenue_pkr"] / m["orders"]).round(2)
    m = m.reset_index()
    m["revenue_share_pct"] = (m["revenue_pkr"] / m["revenue_pkr"].sum()
                              * 100).round(2)
    m["mom_growth_pct"] = m["revenue_pkr"].pct_change().mul(100).round(2)
    return m


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    df, traffic = load()
    total_rev = int(df["line_revenue_pkr"].sum())
    assert total_rev == 346800 and len(df) == 52, "clean base must reconcile"
    monthly = monthly_table(df)
    cat = (df.groupby("category")["line_revenue_pkr"].sum()
             .reindex(CATEGORIES).reset_index()
             .rename(columns={"line_revenue_pkr": "revenue_pkr"}))
    cat["lines"] = df.groupby("category").size().reindex(CATEGORIES).values
    cat["share_pct"] = (cat["revenue_pkr"] / total_rev * 100).round(2)
    # T2 bars run largest to smallest; other techniques keep CATEGORIES order
    cat = cat.sort_values("revenue_pkr", ascending=False).reset_index(drop=True)
    catmon = (df.pivot_table(index="month", columns="category",
                             values="line_revenue_pkr", aggfunc="sum",
                             fill_value=0).reindex(MONTHS)[CATEGORIES])
    order_values = (df.groupby("order_id")["line_revenue_pkr"].sum()
                      .reset_index().rename(
                          columns={"line_revenue_pkr": "order_value_pkr"}))
    order_values = order_values.merge(
        df[["order_id", "month"]].drop_duplicates(), on="order_id")
    summary = {"dataset": "Noor Electronics \u2014 SAMPLE / DEMO data only "
                          "(fictional store, Jan\u2013Jun 2026; same shop as "
                          "Mini #1 / #3 / #19 / #22)",
               "clean_orders": 32, "clean_lines": 52,
               "clean_revenue_pkr": total_rev}

    # ---------- T1: line chart — monthly revenue trend ----------
    t1 = monthly[["month", "revenue_pkr", "orders", "avg_order_value_pkr"]]
    t1.to_csv(OUT / "technique_01_monthly_revenue.csv", index=False)
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(MONTH_LABELS, monthly["revenue_pkr"], marker="o", linewidth=2.5,
            color="#1f77b4")
    for x, y in zip(MONTH_LABELS, monthly["revenue_pkr"]):
        ax.annotate(f"{int(y):,}", (x, y), textcoords="offset points",
                    xytext=(0, 10), ha="center", fontsize=10,
                    fontweight="bold")
    ax.set_ylim(0, monthly["revenue_pkr"].max() * 1.15)
    style_ax(ax, "Monthly revenue is climbing \u2014 June is 2.5x January",
             "Month (2026)", "Revenue (PKR)")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: pkr(v)))
    save(fig, "technique_01_monthly_revenue.png")
    peak = monthly.loc[monthly["revenue_pkr"].idxmax()]
    low = monthly.loc[monthly["revenue_pkr"].idxmin()]
    summary["monthly_revenue_pkr"] = dict(
        zip(monthly["month"], monthly["revenue_pkr"].astype(int)))
    summary["orders_per_month"] = dict(
        zip(monthly["month"], monthly["orders"].astype(int)))
    summary["peak_month"] = peak["month"]
    summary["peak_month_revenue_pkr"] = int(peak["revenue_pkr"])
    summary["peak_month_orders"] = int(peak["orders"])
    summary["peak_month_share_pct"] = round(
        peak["revenue_pkr"] / total_rev * 100, 2)
    summary["lowest_month"] = low["month"]
    summary["lowest_month_revenue_pkr"] = int(low["revenue_pkr"])
    summary["mom_growth_pct"] = {
        r["month"]: (None if pd.isna(r["mom_growth_pct"])
                     else float(r["mom_growth_pct"]))
        for _, r in monthly.iterrows()}
    summary["jan_to_jun_growth_pct"] = round(
        (monthly["revenue_pkr"].iloc[-1] / monthly["revenue_pkr"].iloc[0]
         - 1) * 100, 2)
    summary["avg_order_value_by_month_pkr"] = {
        r["month"]: float(r["avg_order_value_pkr"])
        for _, r in monthly.iterrows()}

    # ---------- T2: bar chart — revenue by category ----------
    cat.to_csv(OUT / "technique_02_revenue_by_category.csv", index=False)
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(cat["category"], cat["revenue_pkr"],
                  color=[CAT_COLORS[c] for c in cat["category"]])
    for b, v, s in zip(bars, cat["revenue_pkr"], cat["share_pct"]):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 2500,
                f"PKR {int(v):,}\n({s:.1f}%)", ha="center", fontsize=10,
                fontweight="bold")
    ax.set_ylim(0, cat["revenue_pkr"].max() * 1.22)
    style_ax(ax, "Three categories carry the store almost equally",
             "Category", "Revenue (PKR)")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: pkr(v)))
    save(fig, "technique_02_revenue_by_category.png")
    summary["revenue_by_category_pkr"] = dict(
        zip(cat["category"], cat["revenue_pkr"].astype(int)))
    summary["category_share_pct"] = dict(
        zip(cat["category"], cat["share_pct"]))
    summary["category_lines"] = dict(zip(cat["category"], cat["lines"].astype(int)))
    summary["top_category"] = cat.loc[cat["revenue_pkr"].idxmax(), "category"]
    summary["top_category_revenue_pkr"] = int(cat["revenue_pkr"].max())
    summary["smallest_category"] = cat.loc[cat["revenue_pkr"].idxmin(), "category"]
    summary["smallest_category_revenue_pkr"] = int(cat["revenue_pkr"].min())

    # ---------- T3: grouped bar — category x month ----------
    t3 = catmon.reset_index().melt(id_vars="month", value_vars=CATEGORIES,
                                   var_name="category",
                                   value_name="revenue_pkr")
    t3 = t3.sort_values(["month", "category"]).reset_index(drop=True)
    t3.to_csv(OUT / "technique_03_category_by_month.csv", index=False)
    fig, ax = plt.subplots(figsize=(11, 6))
    x = np.arange(len(MONTHS))
    w = 0.19
    for i, c in enumerate(CATEGORIES):
        ax.bar(x + (i - 1.5) * w, catmon[c], width=w, label=c,
               color=CAT_COLORS[c])
    ax.set_xticks(x)
    ax.set_xticklabels(MONTH_LABELS)
    ax.legend(title="Category", frameon=False)
    style_ax(ax, "No single category wins every month \u2014 the lead rotates",
             "Month (2026)", "Revenue (PKR)")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: pkr(v)))
    save(fig, "technique_03_category_by_month.png")
    summary["category_by_month_pkr"] = {
        m: {c: int(catmon.loc[m, c]) for c in CATEGORIES} for m in MONTHS}
    summary["zero_revenue_cells"] = int((catmon == 0).sum().sum())
    summary["zero_revenue_cells_list"] = [
        f"{m} {c}" for m in MONTHS for c in CATEGORIES if catmon.loc[m, c] == 0]

    # ---------- T4: histogram — order-value distribution ----------
    counts, edges = np.histogram(order_values["order_value_pkr"],
                                 bins=BIN_EDGES)
    t4 = pd.DataFrame({"bin_start_pkr": edges[:-1].astype(int),
                       "bin_end_pkr": edges[1:].astype(int),
                       "orders": counts})
    t4["share_pct"] = (t4["orders"] / t4["orders"].sum() * 100).round(2)
    t4.to_csv(OUT / "technique_04_order_value_histogram.csv", index=False)
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar([f"{a:,} \u2013 {b:,}" for a, b in zip(edges[:-1], edges[1:])],
                  counts, color="#1f77b4", width=0.7)
    for b, v in zip(bars, counts):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.3,
                str(int(v)), ha="center", fontsize=11, fontweight="bold")
    ax.set_ylim(0, counts.max() * 1.2)
    style_ax(ax, "Most orders land between PKR 5,000 and 15,000",
             "Order value (PKR)", "Orders")
    save(fig, "technique_04_order_value_histogram.png")
    vals = order_values["order_value_pkr"]
    summary["order_value_min_pkr"] = int(vals.min())
    summary["order_value_max_pkr"] = int(vals.max())
    summary["order_value_mean_pkr"] = round(float(vals.mean()), 2)
    summary["order_value_median_pkr"] = float(vals.median())
    summary["histogram_bin_counts"] = counts.astype(int).tolist()
    summary["histogram_bin_edges_pkr"] = BIN_EDGES
    summary["orders_in_5k_to_15k"] = int(counts[1] + counts[2])
    summary["orders_in_5k_to_15k_pct"] = round(
        (counts[1] + counts[2]) / counts.sum() * 100, 2)

    # ---------- T5: box plot — line revenue by category ----------
    t5 = df[["line_id", "category", "line_revenue_pkr"]].sort_values(
        ["category", "line_revenue_pkr"]).reset_index(drop=True)
    t5.to_csv(OUT / "technique_05_line_revenue_by_category.csv", index=False)
    fig, ax = plt.subplots(figsize=(10, 6))
    data = [df.loc[df["category"] == c, "line_revenue_pkr"] for c in CATEGORIES]
    bp = ax.boxplot(data, labels=CATEGORIES, patch_artist=True,
                    showfliers=True)
    for patch, c in zip(bp["boxes"], CATEGORIES):
        patch.set_facecolor(CAT_COLORS[c])
        patch.set_alpha(0.55)
    style_ax(ax, "Furniture lines swing widest \u2014 one chair is 15x a notebook",
             "Category", "Line revenue (PKR)")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: pkr(v)))
    save(fig, "technique_05_line_revenue_by_category.png")
    box = {}
    for c in CATEGORIES:
        s = df.loc[df["category"] == c, "line_revenue_pkr"]
        box[c] = {"min_pkr": int(s.min()), "q1_pkr": float(s.quantile(0.25)),
                  "median_pkr": float(s.median()),
                  "q3_pkr": float(s.quantile(0.75)),
                  "max_pkr": int(s.max()), "lines": int(len(s))}
    summary["boxplot_line_revenue_by_category"] = box

    # ---------- T6: scatter — quantity vs line revenue, hue category ----------
    t6 = df[["line_id", "product_name", "category", "quantity",
             "unit_price_pkr", "line_revenue_pkr"]].sort_values("line_id")
    t6.to_csv(OUT / "technique_06_quantity_vs_revenue.csv", index=False)
    fig, ax = plt.subplots(figsize=(10, 6))
    for c in CATEGORIES:
        sub = df[df["category"] == c]
        ax.scatter(sub["quantity"], sub["line_revenue_pkr"],
                   label=c, color=CAT_COLORS[c], s=70, alpha=0.85,
                   edgecolors="white")
    ax.legend(title="Category", frameon=False)
    style_ax(ax, "Quantity barely moves revenue \u2014 price does",
             "Quantity (units on the line)", "Line revenue (PKR)")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: pkr(v)))
    ax.set_xticks(range(1, 6))
    save(fig, "technique_06_quantity_vs_revenue.png")
    r = float(np.corrcoef(df["quantity"], df["line_revenue_pkr"])[0, 1])
    summary["scatter_quantity_revenue_pearson_r"] = round(r, 3)
    summary["total_units_sold"] = int(df["quantity"].sum())
    summary["max_quantity_on_a_line"] = int(df["quantity"].max())
    summary["single_line_max_revenue_pkr"] = int(df["line_revenue_pkr"].max())

    # ---------- T7: heatmap — category x month revenue ----------
    t7 = catmon.reset_index().rename(columns={"month": "month"})
    t7.to_csv(OUT / "technique_07_category_month_heatmap.csv", index=False)
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.heatmap(catmon.T, annot=True, fmt=",d", cmap="YlGnBu", ax=ax,
                linewidths=0.5, cbar_kws={"label": "Revenue (PKR)"})
    ax.set_title("Revenue heatmap: June Kitchen is the hottest cell",
                 loc="left", pad=12, fontsize=14, fontweight="bold")
    ax.set_xlabel("Month (2026)")
    ax.set_ylabel("Category")
    ax.set_xticklabels(MONTH_LABELS)
    save(fig, "technique_07_category_month_heatmap.png")
    hottest = catmon.stack().idxmax()
    summary["heatmap_hottest_cell"] = {"month": hottest[0],
                                       "category": hottest[1],
                                       "revenue_pkr": int(catmon.loc[hottest])}
    nonzero = catmon.stack()
    nonzero = nonzero[nonzero > 0]
    coldest = nonzero.idxmin()
    summary["heatmap_coldest_nonzero_cell"] = {
        "month": coldest[0], "category": coldest[1],
        "revenue_pkr": int(nonzero.loc[coldest])}

    # ---------- T8: seaborn pairplot — June daily traffic ----------
    traffic["orders_label"] = traffic["orders"].map(
        {0: "no order", 1: "order day"})
    t8 = traffic[["date", "website_sessions", "store_visitors",
                  "ad_spend_pkr", "orders"]].copy()
    t8["date"] = t8["date"].dt.strftime("%Y-%m-%d")
    t8.to_csv(OUT / "technique_08_june_daily_traffic.csv", index=False)
    g = sns.pairplot(traffic,
                     vars=["website_sessions", "store_visitors",
                           "ad_spend_pkr"],
                     hue="orders_label", diag_kind="kde",
                     palette={"no order": "#8c8c8c", "order day": "#ff7f0e"},
                     plot_kws={"s": 55, "alpha": 0.8})
    g.figure.suptitle("June traffic: sessions, visitors and ad spend move "
                      "together", y=1.02, fontsize=14, fontweight="bold")
    if g._legend is not None:
        g._legend.set_title("June day")
    g.figure.text(0.01, -0.01, SOURCE, fontsize=8, color="#666666")
    g.figure.savefig(OUT / "technique_08_june_daily_traffic.png",
                     bbox_inches="tight")
    plt.close("all")
    print("  wrote technique_08_june_daily_traffic.png")
    summary["june_traffic_days"] = int(len(traffic))
    summary["june_traffic_sessions"] = int(traffic["website_sessions"].sum())
    summary["june_traffic_visitors"] = int(traffic["store_visitors"].sum())
    summary["june_traffic_ad_spend_pkr"] = int(traffic["ad_spend_pkr"].sum())
    summary["june_traffic_orders"] = int(traffic["orders"].sum())
    summary["june_traffic_conversion_pct"] = round(
        traffic["orders"].sum() / traffic["website_sessions"].sum() * 100, 3)
    summary["june_traffic_sessions_visitors_pearson_r"] = round(
        float(np.corrcoef(traffic["website_sessions"],
                          traffic["store_visitors"])[0, 1]), 3)
    summary["june_traffic_sessions_adspend_pearson_r"] = round(
        float(np.corrcoef(traffic["website_sessions"],
                          traffic["ad_spend_pkr"])[0, 1]), 3)
    summary["june_traffic_order_days"] = sorted(
        traffic.loc[traffic["orders"] == 1, "date"].dt.strftime(
            "%Y-%m-%d").tolist())

    # ---------- T9: dual-axis — revenue bars + order-count line ----------
    t9 = monthly[["month", "revenue_pkr", "orders"]].copy()
    t9["revenue_share_pct"] = (t9["revenue_pkr"] / total_rev * 100).round(2)
    t9.to_csv(OUT / "technique_09_revenue_and_orders.csv", index=False)
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(MONTH_LABELS, monthly["revenue_pkr"], color="#1f77b4",
                  alpha=0.85, label="Revenue (PKR)")
    ax.set_ylabel("Revenue (PKR)")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: pkr(v)))
    ax.set_ylim(0, monthly["revenue_pkr"].max() * 1.18)
    ax2 = ax.twinx()
    ax2.plot(MONTH_LABELS, monthly["orders"], color="#ff7f0e", marker="o",
             linewidth=2.5, label="Orders")
    ax2.set_ylabel("Orders")
    ax2.set_ylim(0, monthly["orders"].max() * 1.6)
    ax2.spines["top"].set_visible(False)
    peak_i = int(monthly["revenue_pkr"].idxmax())
    ax.annotate("Peak: Jun \u2014 PKR 94,200 \u00b7 7 orders",
                xy=(peak_i, monthly["revenue_pkr"].iloc[peak_i]),
                xytext=(peak_i - 2.2,
                        monthly["revenue_pkr"].iloc[peak_i] * 1.02),
                arrowprops=dict(arrowstyle="->", color="#333333"),
                fontsize=11, fontweight="bold")
    style_ax(ax, "Revenue and order count rise together \u2014 except March",
             "Month (2026)", "Revenue (PKR)")
    ax2.grid(False)
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, frameon=False, loc="upper left")
    save(fig, "technique_09_revenue_and_orders.png")
    summary["peak_month_share_of_total_pct"] = summary["peak_month_share_pct"]
    summary["march_revenue_pkr"] = int(
        monthly.loc[monthly["month"] == "2026-03", "revenue_pkr"].iloc[0])
    summary["march_orders"] = int(
        monthly.loc[monthly["month"] == "2026-03", "orders"].iloc[0])

    # ---------- T10: small multiples — monthly trend per category ----------
    t10 = t3.copy()
    t10["share_of_category_pct"] = t10.groupby("category")["revenue_pkr"].transform(
        lambda s: (s / s.sum() * 100).round(2))
    t10 = t10.sort_values(["category", "month"]).reset_index(drop=True)
    t10.to_csv(OUT / "technique_10_monthly_trend_per_category.csv",
               index=False)
    fig, axes = plt.subplots(2, 2, figsize=(10, 7), sharey=True)
    for ax, c in zip(axes.flat, CATEGORIES):
        s = catmon[c]
        peak_pos = int(np.argmax(s.values))
        ax.plot(MONTH_LABELS, s, marker="o", linewidth=2,
                color=CAT_COLORS[c])
        ax.fill_between(MONTH_LABELS, s, alpha=0.12, color=CAT_COLORS[c])
        ax.set_title(f"{c} \u2014 PKR {int(s.sum()):,} total",
                     loc="left", fontsize=12)
        ax.grid(axis="y", alpha=0.3)
        ax.set_axisbelow(True)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
        ax.yaxis.set_major_formatter(
            mticker.FuncFormatter(lambda v, _: pkr(v)))
        label_ha = "right" if peak_pos == len(MONTHS) - 1 else "left"
        label_x = -4 if peak_pos == len(MONTHS) - 1 else 0
        ax.annotate(f"peak {MONTH_LABELS[peak_pos]}: "
                    f"{int(s.max()):,}",
                    xy=(peak_pos, s.max()),
                    xytext=(label_x, 8), textcoords="offset points",
                    ha=label_ha, fontsize=9, fontweight="bold")
    fig.suptitle("Same upward story, four different shapes",
                 x=0.02, ha="left", fontsize=14, fontweight="bold")
    fig.supylabel("Revenue (PKR)")
    fig.tight_layout()
    save(fig, "technique_10_monthly_trend_per_category.png")
    per_cat_peak = {}
    for c in CATEGORIES:
        s = catmon[c]
        per_cat_peak[c] = {"month": MONTHS[int(np.argmax(s.values))],
                           "revenue_pkr": int(s.max())}
    summary["per_category_peak_month"] = per_cat_peak
    summary["technique_files"] = {
        "t1_rows": int(len(t1)), "t2_rows": int(len(cat)),
        "t3_rows": int(len(t3)), "t4_rows": int(len(t4)),
        "t5_rows": int(len(t5)), "t6_rows": int(len(t6)),
        "t7_rows": int(len(t7)), "t8_rows": int(len(t8)),
        "t9_rows": int(len(t9)), "t10_rows": int(len(t10))}

    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print("wrote summary.json")
    return summary, monthly, cat, catmon, order_values, traffic


def fmt(n):
    return f"{n:,}"


def write_findings(summary, monthly, cat, catmon, order_values, traffic):
    box = summary["boxplot_line_revenue_by_category"]
    s = summary
    lines = []
    lines.append("# Mini #23 \u2014 findings (Data Visualisation Pack)\n")
    lines.append("**SAMPLE / DEMO data only.** Fictional store Noor "
                 "Electronics, fictional sales, fictional numbers. Never "
                 "claimed as real client work. Every number below is "
                 "recomputed independently from the raw CSVs by "
                 "`src/checks.py`.\n")
    lines.append("## Headline numbers\n")
    lines.append("| KPI | Value |")
    lines.append("|---|---|")
    lines.append(f"| Clean orders / clean lines | 32 / 52 (Jan\u2013Jun 2026) |")
    lines.append(f"| Clean revenue | PKR {fmt(s['clean_revenue_pkr'])} |")
    lines.append(f"| Peak month | {s['peak_month']} \u2014 PKR "
                 f"{fmt(s['peak_month_revenue_pkr'])} "
                 f"({s['peak_month_orders']} orders, "
                 f"{s['peak_month_share_pct']:.2f}% of total) |")
    lines.append(f"| Lowest month | {s['lowest_month']} \u2014 PKR "
                 f"{fmt(s['lowest_month_revenue_pkr'])} |")
    lines.append(f"| Jan \u2192 Jun growth | +{s['jan_to_jun_growth_pct']:.2f}% |")
    lines.append(f"| Top category | {s['top_category']} \u2014 PKR "
                 f"{fmt(s['top_category_revenue_pkr'])} |")
    lines.append(f"| Smallest category | {s['smallest_category']} \u2014 PKR "
                 f"{fmt(s['smallest_category_revenue_pkr'])} |")
    lines.append(f"| Order value: mean / median | PKR "
                 f"{fmt(s['order_value_mean_pkr'])} / PKR "
                 f"{fmt(s['order_value_median_pkr'])} |")
    lines.append(f"| Order value: min / max | PKR "
                 f"{fmt(s['order_value_min_pkr'])} / PKR "
                 f"{fmt(s['order_value_max_pkr'])} |")
    lines.append(f"| Orders PKR 5,000\u201315,000 | "
                 f"{s['orders_in_5k_to_15k']} of 32 "
                 f"({s['orders_in_5k_to_15k_pct']:.2f}%) |")
    lines.append(f"| Quantity vs revenue correlation | "
                 f"r = {s['scatter_quantity_revenue_pearson_r']} |")
    lines.append(f"| Hottest heatmap cell | "
                 f"{s['heatmap_hottest_cell']['month']} "
                 f"{s['heatmap_hottest_cell']['category']} \u2014 PKR "
                 f"{fmt(s['heatmap_hottest_cell']['revenue_pkr'])} |")
    lines.append(f"| June traffic: sessions / visitors / ad spend | "
                 f"{fmt(s['june_traffic_sessions'])} / "
                 f"{fmt(s['june_traffic_visitors'])} / PKR "
                 f"{fmt(s['june_traffic_ad_spend_pkr'])} |")
    lines.append(f"| June orders / conversion | "
                 f"{s['june_traffic_orders']} orders, "
                 f"{s['june_traffic_conversion_pct']:.3f}% of sessions |")
    lines.append("")
    lines.append("## What each chart shows\n")
    lines.append("### 1. Line chart \u2014 monthly revenue trend")
    lines.append("Revenue climbs from PKR 37,100 (Jan) to PKR 94,200 (Jun), "
                 "with one dip: March falls to PKR 30,500 (\u221239.00% "
                 "month-on-month) on only 4 orders. June is 2.54x January. "
                 "**Use it when:** the question is direction over time. "
                 "**Common mistake:** starting the y-axis above zero to "
                 "exaggerate the slope \u2014 this chart starts at zero.\n")
    lines.append("### 2. Bar chart \u2014 revenue by category")
    lines.append("Kitchen leads at PKR 106,000 (30.57%), then Furniture "
                 "PKR 105,600 (30.45%) and Electronics PKR 104,000 "
                 "(29.99%) \u2014 the top three are within PKR 2,000 of "
                 "each other. Stationery trails at PKR 31,200 (9.00%). "
                 "**Use it when:** comparing totals across a few named "
                 "groups. **Common mistake:** sorting bars by the order "
                 "the data arrived in instead of by value \u2014 here the "
                 "bars run largest to smallest.\n")
    lines.append("### 3. Grouped bar \u2014 revenue by category \u00d7 month")
    lines.append("No category wins every month: Electronics leads January "
                 "(PKR 19,500), Kitchen leads February (PKR 25,600), "
                 "Furniture leads April (PKR 36,000), Kitchen leads June "
                 "(PKR 43,500). Two cells are genuinely zero \u2014 "
                 "Furniture sold nothing in January, Stationery nothing "
                 "in February \u2014 and the chart shows the gap instead "
                 "of hiding it. **Use it when:** two dimensions matter at "
                 "once (here: when \u00d7 what). **Common mistake:** more "
                 "than ~4 groups per cluster \u2014 the bars turn into "
                 "noise.\n")
    lines.append("### 4. Histogram \u2014 order-value distribution")
    lines.append("Order values run PKR 2,400\u201320,400, mean PKR "
                 "10,837.50, median PKR 10,250. The bulk sits in the "
                 "middle: 20 of 32 orders (62.50%) fall between PKR 5,000 "
                 "and 15,000, with 5 below PKR 5,000 and 2 above PKR "
                 "20,000. **Use it when:** the question is shape \u2014 "
                 "where the bulk is, how long the tail is. **Common "
                 "mistake:** picking bins after looking at the answer; "
                 "the PKR 5,000 bins here were fixed before plotting.\n")
    lines.append("### 5. Box plot \u2014 line revenue by category")
    lines.append(f"Furniture lines swing widest (median PKR "
                 f"{fmt(box['Furniture']['median_pkr'])}), max "
                 f"PKR {fmt(box['Furniture']['max_pkr'])} \u2014 one chair "
                 f"is 15x a notebook set). Electronics lines cluster "
                 f"tight (median PKR "
                 f"{fmt(box['Electronics']['median_pkr'])}, IQR PKR "
                 f"{fmt(box['Electronics']['q1_pkr'])}\u2013"
                 f"{fmt(box['Electronics']['q3_pkr'])}). Kitchen's median "
                 f"is PKR {fmt(box['Kitchen']['median_pkr'])}; "
                 f"Stationery's is PKR "
                 f"{fmt(box['Stationery']['median_pkr'])}. **Use it when:** "
                 "comparing distributions side by side, especially spread "
                 "and outliers. **Common mistake:** reading the box as "
                 "the whole story \u2014 a box hides bimodality; check a "
                 "histogram too.\n")
    lines.append("### 6. Scatter \u2014 quantity vs line revenue, by category")
    lines.append("Quantity barely moves revenue: Pearson r = "
                 f"{s['scatter_quantity_revenue_pearson_r']}. A "
                 "5-unit Notebook Set line is PKR 6,000 while a 1-unit "
                 "Office Chair line is PKR 18,000 \u2014 price, not "
                 "volume, decides the line total. 81 units sold across "
                 "52 lines. **Use it when:** hunting a relationship "
                 "between two numbers. **Common mistake:** reading "
                 "correlation as causation \u2014 the scatter shows the "
                 "two move together (or don't), not why.\n")
    lines.append("### 7. Heatmap \u2014 category \u00d7 month revenue")
    lines.append(f"The hottest cell is "
                 f"{s['heatmap_hottest_cell']['month']} "
                 f"{s['heatmap_hottest_cell']['category']}, PKR "
                 f"{fmt(s['heatmap_hottest_cell']['revenue_pkr'])}; the "
                 f"coldest non-zero cell is "
                 f"{s['heatmap_coldest_nonzero_cell']['month']} "
                 f"{s['heatmap_coldest_nonzero_cell']['category']}, PKR "
                 f"{fmt(s['heatmap_coldest_nonzero_cell']['revenue_pkr'])}. "
                 "Colour makes the pattern visible in one glance: Kitchen "
                 "heats up late, Furniture peaks in April, Electronics "
                 "fades after May. **Use it when:** a two-way table is "
                 "too wide to read as numbers. **Common mistake:** a "
                 "rainbow palette that lies about magnitude \u2014 this "
                 "one is a single-hue sequential scale.\n")
    lines.append("### 8. Seaborn pairplot \u2014 June daily traffic")
    lines.append("30 June days: 7,649 website sessions, 2,382 store "
                 "visitors, PKR 45,600 ad spend, 7 orders (0.092% of "
                 "sessions). Sessions and visitors track tightly "
                 f"(r = {s['june_traffic_sessions_visitors_pearson_r']}), "
                 "and ad spend tracks sessions "
                 f"(r = {s['june_traffic_sessions_adspend_pearson_r']}). "
                 "Order days (orange) sit on the higher-traffic side but "
                 "do not separate cleanly \u2014 traffic helps, it does "
                 "not decide. **Use it when:** scanning several numeric "
                 "variables for relationships at once. **Common mistake:** "
                 "pair-plotting 10+ variables \u2014 the grid explodes; "
                 "three is the sweet spot.\n")
    lines.append("### 9. Dual-axis chart \u2014 revenue + order count")
    lines.append("Bars show revenue (left axis), the line shows order "
                 "count (right axis), and the peak is annotated: June, "
                 "PKR 94,200, 7 orders, 27.16% of all six-month revenue. "
                 "March breaks the pattern \u2014 revenue falls to PKR "
                 "30,500 while orders only dip to 4, so the fall is a "
                 "small-basket month, not just a quiet month. **Use it "
                 "when:** two series share a time axis but not a scale. "
                 "**Common mistake:** two axes with unrelated scales "
                 "that make lines cross by accident \u2014 both axes here "
                 "start at zero and are labelled.\n")
    lines.append("### 10. Small multiples \u2014 monthly trend per category")
    lines.append("One panel per category, same y-scale, same months. "
                 "Electronics peaks in May (PKR 36,500), Furniture in "
                 "April (PKR 36,000), Kitchen in June (PKR 43,500), "
                 "Stationery in January (PKR 14,400) \u2014 four different "
                 "shapes behind one rising total. **Use it when:** the "
                 "same trend must be compared across groups without "
                 "overplotting. **Common mistake:** letting each panel "
                 "have its own y-scale \u2014 then equal-looking slopes "
                 "mean different things.\n")
    lines.append("## What the pack teaches\n")
    lines.append("1. **Pick the chart by the question, not by habit.** "
                 "Trend \u2192 line, comparison \u2192 bar, two dimensions "
                 "\u2192 grouped bar or heatmap, shape \u2192 histogram, "
                 "spread \u2192 box, relationship \u2192 scatter, many "
                 "variables \u2192 pairplot, two scales \u2192 dual-axis, "
                 "same trend across groups \u2192 small multiples.")
    lines.append("2. **A chart is only as honest as its axis.** Zero-based "
                 "bars, labelled dual axes, one shared scale across "
                 "panels, fixed bins chosen before plotting \u2014 each "
                 "technique in this pack names the lie it avoids.")
    lines.append("3. **Every chart ships its data.** Each PNG has a "
                 "matching CSV of the exact plotted values, so anyone can "
                 "re-plot it and get the same picture. A chart without "
                 "its data is a claim, not evidence.")
    lines.append("4. **Small data still teaches real judgement.** 52 lines "
                 "cannot prove a trend, but they can show what a trend, "
                 "a dip, a zero cell and a weak correlation each look "
                 "like \u2014 and how to spot when a chart is dressing "
                 "one up as the other.")
    lines.append("5. **The numbers reconcile.** Monthly revenue sums to "
                 "PKR 346,800, category revenue sums to PKR 346,800, "
                 "order values sum to PKR 346,800, and the 7 June order "
                 "days in the traffic file are the 7 June order dates. "
                 "If a chart disagrees with the CSV, the chart is wrong.")
    (OUT / "findings.md").write_text("\n".join(lines))
    print("wrote findings.md")


if __name__ == "__main__":
    summary, monthly, cat, catmon, order_values, traffic = main()
    write_findings(summary, monthly, cat, catmon, order_values, traffic)
