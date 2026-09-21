# Retail Intelligence Project Guide

> Local working guide for a beginner data analyst. This document explains the project using the actual notebooks, analysis summary, and Streamlit dashboard. The branch and commit containing this file are intended to remain local unless you explicitly push them.

## 1. What This Project Does

This project analyzes the **Online Retail** transaction dataset and turns it into:

- A cleaned transaction-level sales dataset.
- Revenue, order, product, customer, country, category, and return analysis.
- RFM customer segmentation.
- A Streamlit dashboard with filters, KPI cards, charts, supporting tables, and customer lookup.

The source data is historical UK online retail transaction data. The project measures commercial activity, not true profit, because product cost and margin fields are not included.

## 2. Project Files

| File | Purpose |
|---|---|
| `app.py` | Streamlit dashboard application and shared analysis pipeline. |
| `RetailDataAnalysis.ipynb` | Main exploratory analysis, cleaning, product, country, category, returns, demand, pricing, and basket analysis. |
| `RFM_Customer_Analysis.ipynb` | Customer RFM calculations, scoring, segmentation, and segment summaries. |
| `Important_Analysis_Summary.md` | Business findings, recommendations, and known limitations. |
| `Online Retail.xlsx` | Required source dataset. |
| `PROJECT_GUIDE_PRIVATE.md` | This beginner and interview preparation guide. |

## 3. Data Pipeline

The project follows this sequence:

1. Load `Online Retail.xlsx` with pandas.
2. Standardize identifier and numeric columns.
3. Parse `InvoiceDate` as a datetime.
4. Remove exact duplicate rows.
5. Flag cancelled invoices and negative-quantity records.
6. Keep exception rows separately in `returns_df` for operational analysis.
7. Remove rows missing required fields, including `CustomerID` for customer analysis.
8. Exclude cancellations, returns, non-positive quantities, non-positive prices, and non-product codes.
9. Calculate line-level revenue:

   `Revenue = Quantity * UnitPrice`

10. Aggregate the cleaned data by month, country, product, category, and customer.
11. Visualize the results in notebooks and the Streamlit dashboard.

### Important data-quality decisions

- Invoice numbers beginning with `C` are treated as cancelled invoices.
- Negative quantities are treated as returned quantities.
- `CustomerID` is required for RFM analysis, so customers with missing IDs are excluded from customer-level results.
- Product categories are estimated from description keywords. They are not official source categories.
- December 2011 is incomplete because the source ends on 9 December.
- A large bulk order can distort product rankings and demand forecasts.

## 4. Dashboard Features

The Streamlit dashboard has two pages.

### Business overview

- Revenue KPI.
- Identifiable customer count.
- Average order value.
- Qualifying order count.
- Return or exception rate.
- Country and category filters.
- Revenue trend by month.
- Revenue by country.
- Top products by revenue.
- Estimated category contribution.
- Supporting market and product rankings.
- Cancellation and exception-value review.

### Customer RFM analysis

- Total revenue represented by scored customers.
- Revenue by RFM segment.
- Search and select a customer ID.
- Segment-specific recommendation.
- Customer revenue, average order value, and order count.
- Customer profile and RFM score.
- Top products purchased.
- Categories purchased.
- Customer purchase history over time.

## 5. Key Business Terms

### Revenue

The sales value calculated from quantity multiplied by unit price. In this project it is cleaned merchandise revenue, not accounting net revenue or profit.

### Order

A distinct `InvoiceNo`. One order can contain many transaction rows and products.

### Average Order Value (AOV)

`AOV = Total Revenue / Number of Distinct Orders`

AOV helps measure the average monetary value of an order.

### Return rate / exception rate

This dashboard uses the absolute value of cancelled or negative-quantity records divided by qualifying revenue plus exception value. It is an operational indicator, not a perfect customer-return rate, because fees and manual adjustments are also present.

### Recency

How many days have passed since a customer's latest purchase, measured from the latest transaction date in the dataset. Lower raw recency is better.

### Frequency

The number of distinct invoices associated with a customer. It measures purchase occasions, not the number of individual items.

### Monetary value

The total cleaned revenue associated with a customer.

### RFM score

A three-part score made from:

- `R`: Recency score.
- `F`: Frequency score.
- `M`: Monetary score.

Each component is ranked into five groups. A higher score is better. Recency is reversed so that more recent customers receive higher scores.

### Customer segments

- **Champions:** Recent, frequent, and high-value customers.
- **Loyal Customers:** Frequent customers with strong recent activity.
- **Big Spenders:** High monetary value but not necessarily high frequency.
- **New Customers:** Recent customers with limited purchase frequency.
- **At Risk:** Older activity with meaningful historical value.
- **Lost Customers:** Older, infrequent, lower-value customers.
- **Developing Customers:** Customers who do not fit the other rules yet.

### Data grain

The source is primarily transaction-line grain: one row represents a product line on an invoice. Always check the grain before counting rows as orders or customers.

### Data leakage

Revenue or information accidentally included from outside the intended time period or prediction point. This project is descriptive, but leakage would matter if these features were used for forecasting or machine learning.

## 6. Useful Commands

Run these commands from the project folder in PowerShell.

### Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use the project interpreter directly or adjust the execution policy according to your organization rules.

### Install project dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install pandas openpyxl matplotlib plotly streamlit jupyter
```

`openpyxl` is needed for reading the Excel workbook.

### Run the dashboard

```powershell
python -m streamlit run app.py
```

To use another port:

```powershell
python -m streamlit run app.py --server.port 8502
```

### Run a notebook

```powershell
jupyter notebook
```

Or:

```powershell
jupyter lab
```

### Validate Python syntax

```powershell
python -m py_compile app.py
```

### Check local Git state

```powershell
git status
git branch --show-current
git log --oneline -5
```

### Create a private local documentation branch

```powershell
git switch -c docs/private-project-guide
git add PROJECT_GUIDE_PRIVATE.md
git commit -m "docs: add retail project guide"
```

A local branch is not visible on a remote until it is pushed. Do not run `git push` if this guide must remain local.

## 7. Beginner Workflow for Investigating a Metric

When a dashboard number looks surprising:

1. Confirm the definition of the metric.
2. Confirm the row grain: line, invoice, customer, or product.
3. Check filters and the date range.
4. Recalculate the number directly in pandas.
5. Compare before-cleaning and after-cleaning totals.
6. Inspect extreme values and duplicate records.
7. Check whether cancelled, returned, fee, or manual rows are included.
8. Document the business interpretation and limitation.

Example:

```python
revenue = clean_df["Quantity"].mul(clean_df["UnitPrice"]).sum()
orders = clean_df["InvoiceNo"].nunique()
aov = revenue / orders
print(f"Revenue: GBP {revenue:,.2f}")
print(f"Orders: {orders:,}")
print(f"AOV: GBP {aov:,.2f}")
```

## 8. MNC-Level Interview Questions and Strong Answer Points

### Data cleaning and SQL

**1. How did you decide which records to exclude?**

Explain that exact duplicates were removed, cancellations and negative quantities were flagged and retained separately, rows missing required analytical fields were removed, and invalid quantities/prices and non-product codes were excluded from qualifying sales. Emphasize that exclusions were documented rather than silently dropped.

**2. Why should you count distinct invoices instead of rows for orders?**

Because one invoice can contain multiple product lines. Counting rows would overstate order volume and understate AOV.

**3. How would you reproduce this analysis in SQL?**

Use a staging CTE for type conversion and flags, a cleaned CTE for business rules, then grouped queries for monthly, country, product, and customer summaries. Use `COUNT(DISTINCT InvoiceNo)` for orders and `COUNT(DISTINCT CustomerID)` for customers.

**4. What checks would you perform before trusting the output?**

Check row counts, nulls, duplicate counts, date range, negative quantities, cancelled invoices, invalid prices, revenue reconciliation, and totals before and after every major filter.

**5. How do you handle missing values?**

Use a business rule for each field. Missing `CustomerID` can be acceptable for sales analysis but not for customer-level RFM. Missing description may prevent category classification. Never use a blanket fill without understanding the field.

### Business and KPI reasoning

**6. What is the difference between revenue, sales, profit, and margin?**

Revenue is money from sales. Profit subtracts costs. Margin is profit divided by revenue. This project calculates revenue only because cost data is absent.

**7. What would you tell a stakeholder about the 82.8% UK revenue share?**

The business is highly UK-concentrated. That supports prioritizing UK operations, but international decisions should also consider order count, repeat behavior, logistics, and margin rather than revenue share alone.

**8. Why is December seasonality difficult to interpret here?**

The dataset ends on 9 December, so December is incomplete. It must not be compared directly with complete months without correcting for the missing period.

**9. Why might the highest-revenue product be misleading?**

A single unusually large bulk transaction can dominate the ranking. Investigate transaction count, quantity per order, customer identity, and whether the order is representative before using it for inventory planning.

**10. What additional data would improve this dashboard?**

Cost of goods, product hierarchy, supplier, inventory, shipping cost, discount, channel, customer acquisition source, and a reliable return reason. These enable margin, profitability, inventory, and marketing analysis.

### RFM and customer analytics

**11. Explain RFM to a non-technical stakeholder.**

It groups customers by how recently they bought, how often they buy, and how much they spend. It helps tailor retention and marketing actions instead of treating every customer identically.

**12. Why is a lower raw Recency value better, but a higher R score better?**

Raw Recency is days since purchase, so fewer days is better. The scoring step reverses the ranking so recent customers receive a higher R score and the combined score is intuitive.

**13. What are the limitations of quantile-based RFM scoring?**

Scores are relative to this dataset, can be sensitive to outliers and ties, and may change when new data arrives. A customer with score 5 is top-ranked relative to the selected population, not necessarily universally excellent.

**14. How would you validate RFM segments?**

Profile each segment by size, revenue share, average value, frequency, recency, retention, and campaign response. Confirm that the recommended action differs meaningfully by segment.

**15. How would you prevent customer leakage in a churn model?**

Choose a historical cutoff date, calculate features using only data before the cutoff, and define the target using a later observation window. Never use future purchases in the feature period.

### Dashboard and stakeholder communication

**16. What makes a dashboard useful rather than decorative?**

Clear metric definitions, visible filters, consistent formatting, appropriate chart choices, fast navigation, actionable context, and a documented data refresh process.

**17. Why use a line chart for monthly revenue and bars for countries?**

A line chart emphasizes time progression and seasonality. Horizontal bars make category or country comparisons and labels easier to read.

**18. How would you design this in Power BI?**

Create a star schema with a sales fact table and date, product, customer, and country dimensions. Add measures for revenue, orders, customers, AOV, returns, and revenue share. Use slicers for date, country, and category, then add drill-through to product and customer detail.

**19. How do you communicate an estimated category result?**

State clearly that categories are keyword-based proxies because the source has no official category field. Label the result as estimated and recommend building a verified product-category mapping.

**20. A stakeholder says the dashboard number is wrong. What do you do?**

Ask for the expected definition and filter state, reproduce both calculations, check grain and exclusions, identify the first point of divergence, and document the agreed definition. Do not change a metric just to match an unexplained expectation.

## 9. Recommended Next Improvements

1. Add automated tests for row counts, revenue, AOV, and RFM score ranges.
2. Move shared cleaning logic into a reusable Python module.
3. Add a `requirements.txt` or `pyproject.toml` with pinned dependencies.
4. Add a verified product-category lookup table.
5. Separate returns, cancellations, fees, and manual adjustments into explicit event types.
6. Add cost and inventory data for margin and stock analysis.
7. Add a data refresh timestamp and source-file validation.
8. Add an export option for filtered dashboard tables.
9. Add a date filter once the data-refresh workflow is established.
10. Add a data dictionary for every source and derived column.

## 10. One-Minute Project Explanation

> I cleaned an online retail transaction dataset by standardizing types, removing exact duplicates, separating cancellations and returns, excluding invalid sales records, and calculating line-level revenue. I analyzed monthly trends, countries, products, categories, returns, and customer value. For customers with usable IDs, I built RFM scores and actionable segments. I then exposed the results in a dark Streamlit dashboard with filters, KPI cards, charts, rankings, and customer-level drill-down. The main limitations are the absence of cost data, estimated product categories, an incomplete December, and possible distortion from bulk transactions.
