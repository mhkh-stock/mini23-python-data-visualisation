# Mini #23 — findings (Data Visualisation Pack)

**SAMPLE / DEMO data only.** Fictional store Noor Electronics, fictional sales, fictional numbers. Never claimed as real client work. Every number below is recomputed independently from the raw CSVs by `src/checks.py`.

## Headline numbers

| KPI | Value |
|---|---|
| Clean orders / clean lines | 32 / 52 (Jan–Jun 2026) |
| Clean revenue | PKR 346,800 |
| Peak month | 2026-06 — PKR 94,200 (7 orders, 27.16% of total) |
| Lowest month | 2026-03 — PKR 30,500 |
| Jan → Jun growth | +153.91% |
| Top category | Kitchen — PKR 106,000 |
| Smallest category | Stationery — PKR 31,200 |
| Order value: mean / median | PKR 10,837.5 / PKR 10,250.0 |
| Order value: min / max | PKR 2,400 / PKR 20,400 |
| Orders PKR 5,000–15,000 | 20 of 32 (62.50%) |
| Quantity vs revenue correlation | r = -0.151 |
| Hottest heatmap cell | 2026-06 Kitchen — PKR 43,500 |
| June traffic: sessions / visitors / ad spend | 7,649 / 2,382 / PKR 45,600 |
| June orders / conversion | 7 orders, 0.092% of sessions |

## What each chart shows

### 1. Line chart — monthly revenue trend
Revenue climbs from PKR 37,100 (Jan) to PKR 94,200 (Jun), with one dip: March falls to PKR 30,500 (−39.00% month-on-month) on only 4 orders. June is 2.54x January. **Use it when:** the question is direction over time. **Common mistake:** starting the y-axis above zero to exaggerate the slope — this chart starts at zero.

### 2. Bar chart — revenue by category
Kitchen leads at PKR 106,000 (30.57%), then Furniture PKR 105,600 (30.45%) and Electronics PKR 104,000 (29.99%) — the top three are within PKR 2,000 of each other. Stationery trails at PKR 31,200 (9.00%). **Use it when:** comparing totals across a few named groups. **Common mistake:** sorting bars by the order the data arrived in instead of by value — here the bars run largest to smallest.

### 3. Grouped bar — revenue by category × month
No category wins every month: Electronics leads January (PKR 19,500), Kitchen leads February (PKR 25,600), Furniture leads April (PKR 36,000), Kitchen leads June (PKR 43,500). Two cells are genuinely zero — Furniture sold nothing in January, Stationery nothing in February — and the chart shows the gap instead of hiding it. **Use it when:** two dimensions matter at once (here: when × what). **Common mistake:** more than ~4 groups per cluster — the bars turn into noise.

### 4. Histogram — order-value distribution
Order values run PKR 2,400–20,400, mean PKR 10,837.50, median PKR 10,250. The bulk sits in the middle: 20 of 32 orders (62.50%) fall between PKR 5,000 and 15,000, with 5 below PKR 5,000 and 2 above PKR 20,000. **Use it when:** the question is shape — where the bulk is, how long the tail is. **Common mistake:** picking bins after looking at the answer; the PKR 5,000 bins here were fixed before plotting.

### 5. Box plot — line revenue by category
Furniture lines swing widest (median PKR 8,400.0), max PKR 18,000 — one chair is 15x a notebook set). Electronics lines cluster tight (median PKR 5,000.0, IQR PKR 3,500.0–8,500.0). Kitchen's median is PKR 6,400.0; Stationery's is PKR 3,600.0. **Use it when:** comparing distributions side by side, especially spread and outliers. **Common mistake:** reading the box as the whole story — a box hides bimodality; check a histogram too.

### 6. Scatter — quantity vs line revenue, by category
Quantity barely moves revenue: Pearson r = -0.151. A 5-unit Notebook Set line is PKR 6,000 while a 1-unit Office Chair line is PKR 18,000 — price, not volume, decides the line total. 81 units sold across 52 lines. **Use it when:** hunting a relationship between two numbers. **Common mistake:** reading correlation as causation — the scatter shows the two move together (or don't), not why.

### 7. Heatmap — category × month revenue
The hottest cell is 2026-06 Kitchen, PKR 43,500; the coldest non-zero cell is 2026-01 Kitchen, PKR 3,200. Colour makes the pattern visible in one glance: Kitchen heats up late, Furniture peaks in April, Electronics fades after May. **Use it when:** a two-way table is too wide to read as numbers. **Common mistake:** a rainbow palette that lies about magnitude — this one is a single-hue sequential scale.

### 8. Seaborn pairplot — June daily traffic
30 June days: 7,649 website sessions, 2,382 store visitors, PKR 45,600 ad spend, 7 orders (0.092% of sessions). Sessions and visitors track tightly (r = 0.995), and ad spend tracks sessions (r = 0.997). Order days (orange) sit on the higher-traffic side but do not separate cleanly — traffic helps, it does not decide. **Use it when:** scanning several numeric variables for relationships at once. **Common mistake:** pair-plotting 10+ variables — the grid explodes; three is the sweet spot.

### 9. Dual-axis chart — revenue + order count
Bars show revenue (left axis), the line shows order count (right axis), and the peak is annotated: June, PKR 94,200, 7 orders, 27.16% of all six-month revenue. March breaks the pattern — revenue falls to PKR 30,500 while orders only dip to 4, so the fall is a small-basket month, not just a quiet month. **Use it when:** two series share a time axis but not a scale. **Common mistake:** two axes with unrelated scales that make lines cross by accident — both axes here start at zero and are labelled.

### 10. Small multiples — monthly trend per category
One panel per category, same y-scale, same months. Electronics peaks in May (PKR 36,500), Furniture in April (PKR 36,000), Kitchen in June (PKR 43,500), Stationery in January (PKR 14,400) — four different shapes behind one rising total. **Use it when:** the same trend must be compared across groups without overplotting. **Common mistake:** letting each panel have its own y-scale — then equal-looking slopes mean different things.

## What the pack teaches

1. **Pick the chart by the question, not by habit.** Trend → line, comparison → bar, two dimensions → grouped bar or heatmap, shape → histogram, spread → box, relationship → scatter, many variables → pairplot, two scales → dual-axis, same trend across groups → small multiples.
2. **A chart is only as honest as its axis.** Zero-based bars, labelled dual axes, one shared scale across panels, fixed bins chosen before plotting — each technique in this pack names the lie it avoids.
3. **Every chart ships its data.** Each PNG has a matching CSV of the exact plotted values, so anyone can re-plot it and get the same picture. A chart without its data is a claim, not evidence.
4. **Small data still teaches real judgement.** 52 lines cannot prove a trend, but they can show what a trend, a dip, a zero cell and a weak correlation each look like — and how to spot when a chart is dressing one up as the other.
5. **The numbers reconcile.** Monthly revenue sums to PKR 346,800, category revenue sums to PKR 346,800, order values sum to PKR 346,800, and the 7 June order days in the traffic file are the 7 June order dates. If a chart disagrees with the CSV, the chart is wrong.