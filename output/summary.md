# Sales Clarity — Demo Results

> All data is synthetic and for portfolio demonstration only. Do not present these figures as client results.

- **Raw input rows:** 230
- **Exact duplicate rows removed:** 1
- **Rows removed for missing/invalid required fields:** 1
- **Rows removed for invalid numeric values:** 1
- **Valid cleaned rows:** 227
- **Paid order-line rows used for KPIs:** 162
- **Completed, paid orders:** 113
- **Paid revenue:** ₦2,195,440
- **Estimated gross profit:** ₦878,440
- **Estimated gross margin:** 40.0%
- **Average order value:** ₦19,429
- **Units sold:** 235
- **Top product:** Electric Trimmer
- **Top sales channel:** WhatsApp
- **Best month by revenue:** 2026-10

## Output files

- `sales_report.html` — open locally in a browser
- `monthly_performance.csv` — monthly KPI table
- `product_performance.csv` — product-level results
- `channel_performance.csv` — channel-level results
- `cleaned_paid_order_lines.csv` — cleaned data used for paid-sales metrics
- `monthly_revenue.png` and `top_products.png` — chart images

## Method and limitations

Revenue = quantity × unit price × (1 − discount). Only completed orders marked paid are included in headline sales KPIs. Estimated gross profit subtracts unit cost × quantity. This demo does not account for overhead, shipping, tax, payment fees or unrecorded return costs. Results depend on input quality and correct status labels.
