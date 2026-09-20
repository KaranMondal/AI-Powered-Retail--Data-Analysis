# RetailDataAnalysis Notebook Summary and Reference Notes

## 1. File reviewed

- Notebook: `RetailDataAnalysis.ipynb`
- Workspace: `AI-Powered--Data-Analysis`
- Input file expected by the notebook: `Online Retail.xlsx`
- Analysis type currently present: exploratory data analysis (EDA) and data-quality profiling
- Total notebook cells: 5 code cells
- Markdown cells: none

## 2. Overall purpose

The notebook begins an exploratory analysis of the Online Retail transaction dataset. Its current purpose is to load the data, inspect the basic structure, document known data-quality risks, and calculate a compact profile of missing values, duplicates, cancellations, prices, quantities, dates, customers, invoices, and country concentration.

The notebook is currently an initial profiling stage. It does not yet include a cleaned dataset, charts, customer segmentation, RFM metrics, predictive modeling, or a final business recommendation section.

## 3. Steps completed in the notebook

### Step 1: Start the EDA section

The first cell contains the label `#EDA`. This marks the beginning of the exploratory data analysis workflow.

### Step 2: Import pandas and load the Excel data

The notebook imports pandas and reads the workbook with:

```python
import pandas as pd
df = pd.read_excel("Online Retail.xlsx")
df.head()
```

What this does:

- Imports pandas as `pd`.
- Loads the worksheet data from `Online Retail.xlsx` into a DataFrame named `df`.
- Displays the first five rows with `df.head()`.

Expected requirement:

- `Online Retail.xlsx` must be available in the notebook's working directory, or the path must be changed to the correct location.

### Step 3: Inspect the DataFrame structure

The notebook runs:

```python
df.info()
```

This displays the DataFrame's index range, column names, non-null counts, data types, and memory usage. Based on the documented observations, the dataset contains 541,909 transaction line items and includes fields such as invoice number, stock code, description, quantity, invoice date, unit price, customer ID, and country.

### Step 4: Record immediate data-quality observations

The notebook documents the following findings.

#### Dataset coverage

- Time period: 1 December 2010 through 9 December 2011.
- Transaction line items: 541,909.
- Invoices: 25,900.
- Customers with non-null customer IDs: 4,372.
- Countries: 38.

#### Missing customer IDs

- Missing `CustomerID` rows: 135,080.
- Approximate share: 24.9% of all rows.
- Interpretation: these are likely guest or unregistered purchases.
- Important financial point: these rows still represent approximately GBP 1.45 million of signed line value, so they should not automatically be discarded for overall revenue reporting.
- Customer-analysis point: they cannot be reliably assigned to a customer and should be excluded from customer-level RFM calculations or handled as a separate guest segment.
- Data-type note: `CustomerID` is stored as a float because missing values are present, although non-null IDs are whole numbers.

#### Missing descriptions

- Missing `Description` rows: 1,454.
- Approximate share: 0.27%.
- Every row with a missing description also has a missing customer ID and a unit price of zero.
- Approximately 862 of these rows have negative quantities.
- Interpretation: these rows appear more consistent with stock adjustments or operational records than ordinary product sales.

#### Exact duplicate rows

- Exact duplicates: 5,268 rows.
- Approximate share: 0.97%.
- The duplicates match on invoice, product, quantity, price, and timestamp.
- Interpretation: they may be double-logged transaction lines.
- Recommended treatment: assess and normally remove exact duplicates before aggregation, while preserving an audit count of how many rows were removed.

#### Negative quantities and cancellations

- Negative-quantity rows: 10,624.
- Cancellation invoices identified by an invoice number beginning with `C`: 9,288.
- Negative-quantity rows that are not cancellation invoices: 1,336.
- Interpretation: most negative quantities are product cancellations or returns, but the remaining negative lines may represent inventory write-offs or other adjustments.
- Recommended treatment: distinguish returns/cancellations from operational adjustments rather than treating every negative quantity as the same business event.

#### Zero and negative unit prices

- Zero-unit-price rows: 2,515.
- These are almost all missing a customer ID.
- Example operational descriptions include `check`, `?`, `damages`, `found`, and `thrown away`.
- Negative-unit-price rows: 2.
- The negative-price records are described as `Adjust bad debt`, use stock code `B`, and have a unit price of approximately GBP -11,062 each.
- Recommended treatment: exclude non-sales adjustments from product-sales metrics, and separately report them as adjustments.

#### Extreme quantity outliers

- Extreme quantities include approximately +74,215, -74,215, +80,995, and -80,995.
- The documented pattern is a sale followed immediately by a full cancellation.
- Risk: summing raw quantities can make sales volume and return volume appear much larger than normal.
- Recommended treatment: inspect these records individually, retain them for a transparent audit trail, and decide whether netting or exclusion is appropriate for each business metric.

#### Geographic concentration

- United Kingdom rows represent approximately 91.4% of the dataset.
- 446 rows have country listed as `Unspecified`.
- Any geographic comparison should account for the very large UK concentration and should avoid interpreting raw row counts as balanced country performance.

#### Non-product stock codes

The `StockCode` field contains operational or fee records mixed with product records. Documented examples include:

- `POST`: 1,256 rows.
- `DOT`: 710 rows.
- `M` and `Manual`: 571 rows combined as documented.
- `D` and `Discount`: 77 rows combined as documented.
- Other codes: `AMAZONFEE`, `BANK CHARGES`, `CRUK`, and `S`.

These codes should be classified separately from ordinary merchandise before product-level analysis.

#### Description formatting

Most product descriptions are uppercase. Mixed-case descriptions are often operational notes rather than catalog product names. Description casing can therefore be a useful signal during product/adjustment classification, but it should not be used as the only classification rule.

#### Signed financial value

- Positive signed line value: approximately GBP 10.67 million.
- Negative signed line value from returns and adjustments: approximately GBP 0.92 million.
- Net signed line value: approximately GBP 9.75 million.

The net value must not be described simply as total sales. Gross sales, returns, adjustments, and net sales should be reported separately.

### Step 5: Build a reusable data-quality profile

The final cell creates a missing-value table and a `profile` dictionary:

```python
miss = df.isna().sum().to_frame("missing")
miss["pct"] = (miss["missing"] / len(df) * 100).round(2)
```

This calculates, for every column:

- The number of missing values in `missing`.
- The percentage of missing values in `pct`.

The notebook then standardizes invoice numbers for cancellation detection:

```python
inv = df["InvoiceNo"].astype(str)
```

The profile dictionary records:

- Total row count.
- Exact duplicate count.
- Missing customer ID count.
- Missing description count.
- Negative quantity count.
- Number of invoice numbers beginning with `C`.
- Negative quantities that are not cancellation invoices.
- Zero unit-price count.
- Negative unit-price count.
- Minimum and maximum quantity.
- Minimum and maximum invoice date.
- Number of unique non-null customers.
- Number of unique invoices.
- Percentage of rows from the United Kingdom.

Finally:

```python
display(miss)
profile
```

The missing-value table is displayed, and the profile dictionary is returned as the final cell result.

## 4. Current analytical conclusions

1. The data is large enough for meaningful transaction, product, country, and customer analysis.
2. Customer-level analysis must account for the 24.9% of rows with no customer ID.
3. Revenue analysis must separate positive sales from cancellations, returns, zero-price records, and other adjustments.
4. Exact duplicates should be investigated before calculating totals or customer metrics.
5. Negative quantity alone is not sufficient to identify a standard return because some negative rows are operational adjustments.
6. Non-product stock codes need a separate classification.
7. The United Kingdom dominates the dataset, so country-level comparisons are highly imbalanced.
8. Net signed value is useful for reconciliation, but it is not equivalent to gross sales.

## 5. Recommended next steps for future analysis

These steps are recommendations for extending the notebook; they are not yet implemented in the current file.

### A. Validate the source and schema

- Confirm the workbook path and worksheet.
- Check that all expected columns exist.
- Convert `InvoiceDate` to datetime if it is not already typed correctly.
- Confirm numeric types for `Quantity` and `UnitPrice`.
- Convert non-null customer IDs to a nullable integer representation after checking for invalid values.

### B. Create explicit transaction flags

Add separate boolean or categorical fields such as:

- `is_cancelled_invoice`: invoice number starts with `C`.
- `is_negative_quantity`: quantity is below zero.
- `is_zero_price`: unit price equals zero.
- `is_negative_price`: unit price is below zero.
- `is_missing_customer`: customer ID is null.
- `is_missing_description`: description is null.
- `is_exact_duplicate`: row is duplicated.
- `is_non_product_code`: stock code is classified as an operational code.

### C. Create line-value fields

Calculate:

```python
df["LineValue"] = df["Quantity"] * df["UnitPrice"]
```

Then report positive sales, returns, adjustments, and net value separately. Do not silently overwrite the original transaction values.

### D. Handle duplicates transparently

- Count exact duplicate rows.
- Save the count before removal.
- Drop exact duplicates for the analytical copy of the data.
- Keep the original DataFrame or an audit table for reconciliation.

### E. Separate sales, returns, and adjustments

Use invoice status, quantity sign, price, description, and stock-code classification together. Keep at least these analytical categories:

- Normal merchandise sales.
- Cancellations or returns.
- Zero-price operational lines.
- Fees and charges.
- Bad-debt or accounting adjustments.
- Other inventory or warehouse adjustments.

### F. Produce descriptive statistics and visualizations

Useful next outputs include:

- Daily and monthly revenue trends.
- Order counts over time.
- Return and cancellation rates.
- Top products by revenue and quantity.
- Top customers by revenue.
- Country-level sales and customer counts.
- Distribution of order value and customer spend.
- Missing-value and adjustment summaries.

### G. Build customer-level RFM analysis

For customer IDs that are present:

- Recency: days since the customer's last qualifying purchase.
- Frequency: number of distinct qualifying invoices.
- Monetary value: qualifying net or gross spend, with the definition clearly stated.

Guest rows should either be excluded from RFM or reported separately as a guest segment.

### H. Document metric definitions

Before interpreting results, define whether each metric includes or excludes:

- Cancellations.
- Returns.
- Zero-price lines.
- Fees.
- Manual adjustments.
- Duplicate rows.
- Missing-customer transactions.

This prevents gross sales, net sales, revenue, and order value from being used interchangeably.

## 6. Important limitations of the current notebook

- No cleaning code is currently implemented.
- No charts are currently implemented.
- No output files are currently exported.
- No model or forecasting method is currently implemented.
- The documented numeric findings depend on the source workbook and should be rechecked if the workbook changes.
- The notebook assumes `Online Retail.xlsx` is available at the expected relative path.
- The current notebook stores observations as comments rather than structured markdown documentation.

## 7. Reference checklist for future sessions

- [ ] Confirm `Online Retail.xlsx` is present.
- [ ] Run the data-loading cell.
- [ ] Run `df.info()` and verify the schema.
- [ ] Run the missing-value and quality profile.
- [ ] Reconcile the documented counts against the current source file.
- [ ] Create transaction classification flags.
- [ ] Create line-value calculations.
- [ ] Decide how duplicates and operational adjustments will be treated.
- [ ] Build clean analytical datasets for sales and customer analysis.
- [ ] Add visual EDA.
- [ ] Add RFM analysis only for identifiable customers.
- [ ] Define and document all financial metrics.
- [ ] Export cleaned data and analytical results if needed.

## 8. Final reference note

This notepad records the work currently present in `RetailDataAnalysis.ipynb`, distinguishes completed steps from recommended future work, and preserves the key data-quality findings for later analysis.

Prepared by: GitHub Copilot
