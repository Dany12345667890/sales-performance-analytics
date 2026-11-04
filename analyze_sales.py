from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
INPUT = ROOT / "data" / "raw_sales.csv"
OUT = ROOT / "output"
OUT.mkdir(exist_ok=True)
REQUIRED = {"order_id", "order_date", "sales_channel", "product_category", "product", "quantity", "unit_price_ngn", "unit_cost_ngn", "discount_pct", "order_status", "payment_status"}


def main():
    if not INPUT.exists():
        raise FileNotFoundError(f"Input file missing: {INPUT}")
    df = pd.read_csv(INPUT)
    missing = REQUIRED - set(df.columns)
    if missing:
        raise ValueError(f"Required columns missing: {sorted(missing)}")
    rows_loaded = len(df)
    duplicate_rows_removed = int(df.duplicated().sum())
    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    for col in ["quantity", "unit_price_ngn", "unit_cost_ngn", "discount_pct"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.drop_duplicates()
    before_required_fields = len(df)
    df = df.dropna(subset=["order_id", "order_date", "product", "quantity", "unit_price_ngn", "unit_cost_ngn"])
    rows_missing_required_fields_removed = before_required_fields - len(df)
    before_valid_values = len(df)
    df = df[(df["quantity"] > 0) & (df["unit_price_ngn"] >= 0) & (df["unit_cost_ngn"] >= 0)]
    rows_invalid_values_removed = before_valid_values - len(df)
    df["discount_pct"] = df["discount_pct"].fillna(0).clip(0, 1)
    df["net_sales_ngn"] = (df["quantity"] * df["unit_price_ngn"] * (1 - df["discount_pct"])).round(2)
    df["estimated_cost_ngn"] = (df["quantity"] * df["unit_cost_ngn"]).round(2)
    df["estimated_gross_profit_ngn"] = (df["net_sales_ngn"] - df["estimated_cost_ngn"]).round(2)
    df["month"] = df["order_date"].dt.to_period("M").astype(str)
    paid = df[(df["order_status"].str.lower() == "completed") & (df["payment_status"].str.lower() == "paid")].copy()
    if paid.empty:
        raise ValueError("No completed, paid order lines found; check status values.")
    monthly = paid.groupby("month", as_index=False).agg(revenue_ngn=("net_sales_ngn", "sum"), estimated_gross_profit_ngn=("estimated_gross_profit_ngn", "sum"), unique_orders=("order_id", "nunique"), units_sold=("quantity", "sum"))
    monthly["average_order_value_ngn"] = monthly["revenue_ngn"] / monthly["unique_orders"].clip(lower=1)
    monthly.to_csv(OUT / "monthly_performance.csv", index=False)
    products = paid.groupby(["product_category", "product"], as_index=False).agg(revenue_ngn=("net_sales_ngn", "sum"), estimated_gross_profit_ngn=("estimated_gross_profit_ngn", "sum"), units_sold=("quantity", "sum"), unique_orders=("order_id", "nunique")).sort_values("revenue_ngn", ascending=False)
    products.to_csv(OUT / "product_performance.csv", index=False)
    channels = paid.groupby("sales_channel", as_index=False).agg(revenue_ngn=("net_sales_ngn", "sum"), unique_orders=("order_id", "nunique"), units_sold=("quantity", "sum")).sort_values("revenue_ngn", ascending=False)
    channels.to_csv(OUT / "channel_performance.csv", index=False)
    paid.to_csv(OUT / "cleaned_paid_order_lines.csv", index=False)
    total_revenue = float(paid["net_sales_ngn"].sum())
    gross_profit = float(paid["estimated_gross_profit_ngn"].sum())
    orders = int(paid["order_id"].nunique())
    units = float(paid["quantity"].sum())
    aov = total_revenue / max(orders, 1)
    margin = gross_profit / total_revenue if total_revenue else 0
    best_product = products.iloc[0]
    best_channel = channels.iloc[0]
    best_month = monthly.sort_values("revenue_ngn", ascending=False).iloc[0]
    money = lambda n: f"₦{n:,.0f}"

    plt.figure(figsize=(9, 5))
    plt.bar(monthly["month"], monthly["revenue_ngn"])
    plt.title("Paid Sales Revenue by Month")
    plt.xlabel("Month"); plt.ylabel("Revenue (NGN)"); plt.xticks(rotation=30, ha="right")
    plt.tight_layout(); plt.savefig(OUT / "monthly_revenue.png", dpi=160); plt.close()
    top = products.head(8).sort_values("revenue_ngn")
    plt.figure(figsize=(9, 5)); plt.barh(top["product"], top["revenue_ngn"])
    plt.title("Top Products by Paid Revenue"); plt.xlabel("Revenue (NGN)")
    plt.tight_layout(); plt.savefig(OUT / "top_products.png", dpi=160); plt.close()

    # Local, standalone HTML: only data values are interpolated; no server required.
    css = """body{font:16px/1.5 Arial,sans-serif;max-width:1100px;margin:32px auto;padding:0 18px;color:#172033;background:#f7f8fa}h1,h2{line-height:1.2}.note{background:#fff4d6;padding:12px 16px;border-radius:8px}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px}.card{background:white;padding:18px;border-radius:12px;box-shadow:0 2px 10px #10182810}.number{font-size:25px;font-weight:700}section{background:white;margin:18px 0;padding:18px;border-radius:12px;overflow-x:auto}img{max-width:100%;height:auto}table{border-collapse:collapse;width:100%;font-size:14px}th,td{padding:8px;border-bottom:1px solid #e5e7eb;text-align:left}th{background:#eef2f7}small{color:#5b6474}"""
    mhtml = monthly.to_html(index=False, border=0, classes="data", float_format=lambda x: f"{x:,.2f}")
    phtml = products.head(10).to_html(index=False, border=0, classes="data", float_format=lambda x: f"{x:,.2f}")
    chhtml = channels.to_html(index=False, border=0, classes="data", float_format=lambda x: f"{x:,.2f}")
    observations = (f"<li>Highest-revenue product in this sample: <b>{best_product['product']}</b> ({money(float(best_product['revenue_ngn']))}).</li>"
                    f"<li>Highest-revenue channel in this sample: <b>{best_channel['sales_channel']}</b> ({money(float(best_channel['revenue_ngn']))}).</li>"
                    f"<li>Highest-revenue month in this sample: <b>{best_month['month']}</b> ({money(float(best_month['revenue_ngn']))}).</li>"
                    "<li>Estimated gross profit excludes overhead, delivery, tax, payment fees and other unrecorded costs.</li>")
    html = f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Sales Clarity Demo</title><style>{css}</style></head><body>
<h1>Sales Clarity: Sales Performance Report</h1><p class="note"><b>Demo disclaimer:</b> this report uses synthetic sample data for portfolio demonstration. Figures are not results from a real client.</p>
<div class="cards"><div class="card"><small>Paid revenue</small><div class="number">{money(total_revenue)}</div></div><div class="card"><small>Completed, paid orders</small><div class="number">{orders:,}</div></div><div class="card"><small>Average order value</small><div class="number">{money(aov)}</div></div><div class="card"><small>Estimated gross margin</small><div class="number">{margin:.1%}</div></div></div>
<section><h2>Monthly trend</h2><img src="monthly_revenue.png" alt="Paid sales revenue by month"><h3>Monthly details</h3>{mhtml}</section>
<section><h2>Top products</h2><img src="top_products.png" alt="Top products by paid revenue"><h3>Top 10 product table</h3>{phtml}</section>
<section><h2>Sales channel performance</h2>{chhtml}</section><section><h2>Management observations</h2><ul>{observations}</ul></section>
<p><small>Raw rows: {rows_loaded:,}. Duplicate rows removed: {duplicate_rows_removed:,}. Rows removed for missing/invalid required fields: {rows_missing_required_fields_removed:,}. Rows removed for invalid numeric values: {rows_invalid_values_removed:,}. Cleaned rows: {len(df):,}. Paid order lines included in headline KPIs: {len(paid):,}. Currency: NGN. Built with Python and pandas.</small></p></body></html>'''
    (OUT / "sales_report.html").write_text(html, encoding="utf-8")
    summary = f"""# Sales Clarity — Demo Results\n\n> All data is synthetic and for portfolio demonstration only. Do not present these figures as client results.\n\n- **Raw input rows:** {rows_loaded:,}\n- **Exact duplicate rows removed:** {duplicate_rows_removed:,}\n- **Rows removed for missing/invalid required fields:** {rows_missing_required_fields_removed:,}\n- **Rows removed for invalid numeric values:** {rows_invalid_values_removed:,}\n- **Valid cleaned rows:** {len(df):,}\n- **Paid order-line rows used for KPIs:** {len(paid):,}\n- **Completed, paid orders:** {orders:,}\n- **Paid revenue:** {money(total_revenue)}\n- **Estimated gross profit:** {money(gross_profit)}\n- **Estimated gross margin:** {margin:.1%}\n- **Average order value:** {money(aov)}\n- **Units sold:** {units:,.0f}\n- **Top product:** {best_product['product']}\n- **Top sales channel:** {best_channel['sales_channel']}\n- **Best month by revenue:** {best_month['month']}\n\n## Output files\n\n- `sales_report.html` — open locally in a browser\n- `monthly_performance.csv` — monthly KPI table\n- `product_performance.csv` — product-level results\n- `channel_performance.csv` — channel-level results\n- `cleaned_paid_order_lines.csv` — cleaned data used for paid-sales metrics\n- `monthly_revenue.png` and `top_products.png` — chart images\n\n## Method and limitations\n\nRevenue = quantity × unit price × (1 − discount). Only completed orders marked paid are included in headline sales KPIs. Estimated gross profit subtracts unit cost × quantity. This demo does not account for overhead, shipping, tax, payment fees or unrecorded return costs. Results depend on input quality and correct status labels.\n"""
    (OUT / "summary.md").write_text(summary, encoding="utf-8")
    print(summary)

if __name__ == "__main__":
    main()
