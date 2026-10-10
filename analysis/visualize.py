# Task 11 — Two visualizations
import pandas as pd
import matplotlib.pyplot as plt
import os

customers = pd.read_csv('customers.csv')
products = pd.read_csv('products.csv')
orders = pd.read_csv('orders.csv')

orders['payment_method'] = orders['payment_method'].str.strip().str.upper()

dup_cols = ['customer_id', 'product_id', 'order_date', 'quantity',
            'discount_pct', 'payment_method', 'rating', 'returned']
is_dup = orders.duplicated(subset=dup_cols, keep='first')
orders_clean = orders[~is_dup].reset_index(drop=True)

orders_clean['discount_pct'] = orders_clean['discount_pct'].fillna(0)
orders_clean['rating'] = orders_clean['rating'].fillna(orders_clean['rating'].median())

merged = orders_clean.merge(products, on='product_id').merge(customers, on='customer_id')
merged['order_value'] = merged['quantity'] * merged['price'] * (1 - merged['discount_pct'] / 100.0)

Q1 = merged['quantity'].quantile(0.25)
Q3 = merged['quantity'].quantile(0.75)
IQR = Q3 - Q1
lower = Q1 - 1.5 * IQR
upper = Q3 + 1.5 * IQR
merged['is_outlier'] = (merged['quantity'] < lower) | (merged['quantity'] > upper)

merged['order_date'] = pd.to_datetime(merged['order_date'])
merged['year_month'] = merged['order_date'].dt.to_period('M')

os.makedirs('visualizations', exist_ok=True)

# Chart 1: Return rate by payment_method
rates = merged.groupby('payment_method')['returned'].mean().mul(100).round(1).sort_values(ascending=False)

plt.figure()
bars = plt.bar(rates.index, rates.values)
for bar, pct in zip(bars, rates.values):
    plt.text(bar.get_x() + bar.get_width()/2, pct + 0.5, f'{pct}%', ha='center')

multiple = round(rates['COD'] / rates['CARD'], 1)
plt.title(f"COD Returns at {rates['COD']}% — {multiple}x Card")
plt.xlabel('Payment Method')
plt.ylabel('Return Rate (%)')
plt.tight_layout()
plt.savefig('visualizations/return_rate_by_payment.png')
plt.close()

# Chart 2: Outlier-corrected monthly revenue trend
monthly = merged[~merged['is_outlier']].groupby('year_month')['order_value'].sum().round(2)
peak_month = monthly.idxmax()

plt.figure()
plt.plot(monthly.index.astype(str), monthly.values, marker='o')
plt.title(f'Monthly Revenue Trend — Peak Month: {peak_month} (Outlier-Corrected)')
plt.xlabel('Month')
plt.ylabel('Total Order Value (₹)')
plt.tight_layout()
plt.savefig('visualizations/monthly_revenue_trend.png')
plt.close()

print("Saved visualizations/return_rate_by_payment.png")
print("Saved visualizations/monthly_revenue_trend.png")
