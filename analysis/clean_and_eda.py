import pandas as pd

# Task 1 — Load and inspect
customers = pd.read_csv('customers.csv')
products = pd.read_csv('products.csv')
orders = pd.read_csv('orders.csv')

print("orders shape (raw):", orders.shape)

# Task 2 — Standardize payment_method casing
print("payment_method raw unique values:", orders['payment_method'].unique())
orders['payment_method'] = orders['payment_method'].str.strip().str.upper()
print("payment_method cleaned unique values:", orders['payment_method'].unique())
print("payment_method counts:\n", orders['payment_method'].value_counts())


# Task 3 — Remove duplicate orders
dup_cols = ['customer_id', 'product_id', 'order_date', 'quantity',
            'discount_pct', 'payment_method', 'rating', 'returned']

is_dup = orders.duplicated(subset=dup_cols, keep='first')

print("Number of duplicate rows flagged:", is_dup.sum())
print("Dropped order_id values:", orders.loc[is_dup, 'order_id'].tolist())

orders_clean = orders[~is_dup].reset_index(drop=True)
print("orders_clean shape:", orders_clean.shape)

# Task 4 — Impute missing values
print("Missing before imputing:\n", orders_clean[['discount_pct', 'rating']].isnull().sum())

orders_clean['discount_pct'] = orders_clean['discount_pct'].fillna(0)


rating_median = orders_clean['rating'].median()
print("Median rating (before imputing):", rating_median)

orders_clean['rating'] = orders_clean['rating'].fillna(rating_median)

print("Missing after imputing:\n", orders_clean[['discount_pct', 'rating']].isnull().sum())

# Task 5 — Merge and reconcile against Part 1 raw total
merged = orders_clean.merge(products, on='product_id', how='left') \
                     .merge(customers, on='customer_id', how='left')

# Calculate order_value for each order
merged['order_value'] = (
    merged['quantity'] * merged['price'] *
    (1 - merged['discount_pct'] / 100.0)
)

# Calculate cleaned total revenue
total_clean = round(merged['order_value'].sum(), 2)

print("Total order_value (cleaned, 175 rows):", total_clean)


dropped_rows = orders[is_dup].merge(
    products, on='product_id', how='left'
)

dropped_rows['order_value'] = (
    dropped_rows['quantity'] * dropped_rows['price'] *
    (1 - dropped_rows['discount_pct'].fillna(0) / 100.0)
)

dropped_total = round(dropped_rows['order_value'].sum(), 2)

print("Sum of order_value for the 5 dropped duplicate rows:", dropped_total)

raw_total = 99860.20
delta = round(raw_total - total_clean, 2)

print("Delta (raw total - cleaned total):", delta)

# Explain the difference
print(f"""
Reconciliation note: The cleaned dataset's total order_value of ₹{total_clean}
is ₹{delta} lower than Part 1 Report (a)'s raw total of ₹{raw_total}.
This difference should match the combined order_value of the 5 duplicate
rows removed in Task 3 (O0176-O0180), independently calculated as
₹{dropped_total}.

Filling missing discount_pct values with 0 does not change the order value
when the original missing discount is treated as 0% off. Filling missing
rating values with the median does not affect order_value because rating
is not part of the formula.
""")

# Task 6 — IQR outlier detection on quantity
Q1 = merged['quantity'].quantile(0.25)
Q3 = merged['quantity'].quantile(0.75)
IQR = Q3 - Q1
lower = Q1 - 1.5 * IQR
upper = Q3 + 1.5 * IQR

print(f"Q1 = {Q1}, Q3 = {Q3}, IQR = {IQR}, lower = {lower}, upper = {upper}")

merged['is_outlier'] = (merged['quantity'] < lower) | (merged['quantity'] > upper)

outliers = merged[merged['is_outlier']]
print("Outlier rows:\n", outliers[['order_id', 'quantity']])
print("Number of outliers:", merged['is_outlier'].sum())

# Task 7 — Hypothesis:
print("Hypothesis: COD (Cash on Delivery) orders have a higher return rate "
      "than CARD or UPI orders, because COD customers pay nothing upfront, "
      "making it easier to refuse/return an order than one already paid for online.")

return_rates = merged.groupby('payment_method')['returned'].agg(['count', 'mean'])
return_rates['return_rate_pct'] = (return_rates['mean'] * 100).round(1)

print(return_rates)

cod_rate = return_rates.loc['COD', 'return_rate_pct']
other_rates = return_rates.drop('COD')['return_rate_pct']

if cod_rate > other_rates.max():
    print(f"Hypothesis Confirmed: COD has the highest return rate at {cod_rate}%, "
          f"compared to {dict(other_rates)} for the other methods.")
else:
    print("Hypothesis Not Confirmed.")

# Task 8 — Multi-level segmentation
segment_rates = merged.groupby(['payment_method', 'city_tier'])['returned'].agg(['count', 'mean'])
segment_rates['return_rate_pct'] = (segment_rates['mean'] * 100).round(1)

print("Return rate by payment_method x city_tier:\n", segment_rates)

highest_risk = segment_rates['return_rate_pct'].idxmax()
highest_rate = segment_rates['return_rate_pct'].max()

print(f"\nHighest-risk segment: payment_method={highest_risk[0]}, "
      f"city_tier={highest_risk[1]}, return_rate={highest_rate}%")

cod_t1 = segment_rates.loc[('COD', 1)]
cod_t2 = segment_rates.loc[('COD', 2)]
print(f"\nCOD risk is not uniform across tiers: Tier-1 COD has "
      f"{int(cod_t1['count'])} orders at {cod_t1['return_rate_pct']}%, "
      f"while Tier-2 COD has {int(cod_t2['count'])} orders at "
      f"{cod_t2['return_rate_pct']}% — nearly {round(cod_t2['return_rate_pct']/cod_t1['return_rate_pct'], 1)}x higher, "
      f"a gap the blended 44.4% overall COD rate (from Task 7) completely hides.")

# Task 9 — Correlation Analysis

corr_cols = ['rating', 'returned', 'discount_pct', 'quantity']

corr_matrix = merged[corr_cols].corr()

print("Correlation Matrix:")
print(corr_matrix.round(2).to_string())


def band(r):
    if pd.isna(r):
        return "undefined"

    r = abs(r)

    if r < 0.2:
        return "negligible"
    elif r < 0.4:
        return "weak"
    elif r < 0.7:
        return "moderate"
    else:
        return "strong"

print("\nPairwise Correlation Strength:")

for i in range(len(corr_cols)):
    for j in range(i + 1, len(corr_cols)):
        col1 = corr_cols[i]
        col2 = corr_cols[j]

        r = corr_matrix.loc[col1, col2]

        if pd.isna(r):
            print(f"{col1} vs {col2}: r = undefined -> undefined")
        else:
            print(
                f"{col1} vs {col2}: "
                f"r = {r:.2f} -> {band(r)}"
            )

discount_returned_r = corr_matrix.loc['discount_pct', 'returned']

print("\nHypothesis: Higher discounts reduce returns.")

if pd.isna(discount_returned_r):
    print("Conclusion: Inconclusive — correlation is undefined.")
elif abs(discount_returned_r) < 0.2:
    print(
        f"Conclusion: Busted. The correlation is "
        f"{discount_returned_r:.2f}, which is negligible "
        f"(|r| < 0.2). No meaningful linear relationship "
        f"was found between discount percentage and returns."
    )
elif discount_returned_r < 0:
    print(
        f"Conclusion: The correlation is negative "
        f"(r = {discount_returned_r:.2f}), consistent with "
        f"the hypothesis, but correlation alone does not "
        f"establish causation."
    )
else:
    print(
        f"Conclusion: The correlation is positive "
        f"(r = {discount_returned_r:.2f}), which does not "
        f"support the hypothesis that higher discounts "
        f"are associated with fewer returns."
    )
# Task 10 — Outlier-corrected time series
merged['order_date'] = pd.to_datetime(merged['order_date'])
merged['year_month'] = merged['order_date'].dt.to_period('M')

monthly_with_outliers = merged.groupby('year_month')['order_value'].sum().round(2)
print("Monthly order_value (including outliers):")
print(monthly_with_outliers.to_string(float_format=lambda x: f"{x:.2f}"))


monthly_no_outliers = merged[~merged['is_outlier']].groupby('year_month')['order_value'].sum().round(2)
print("\nMonthly order_value (outlier-corrected, excluding O0011 and O0098):")
print(monthly_no_outliers.to_string(float_format=lambda x: f"{x:.2f}"))

highest_with = monthly_with_outliers.idxmax()
highest_without = monthly_no_outliers.idxmax()

print(f"""January's apparent lead ({monthly_with_outliers.loc['2026-01']}) in the
uncorrected series is an artifact of two bulk orders landing in January:
O0011 (quantity 25, dated 2026-01-28) and O0098 (quantity 30, dated
2026-01-10) — both flagged as outliers in Task 6. Once these two orders
are excluded, January drops to {monthly_no_outliers.loc['2026-01']}, and
{highest_without} emerges as the genuine peak month at
{monthly_no_outliers.loc[highest_without]} — this is precisely why outlier
detection (Task 6) needed to happen before this time-series analysis
(Task 10), not after: analyzing trends on uncorrected data would have led
to the wrong conclusion about which month actually performs best.
""")




