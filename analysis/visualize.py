from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / 'data'
OUT_DIR = ROOT / 'visualizations'
OUT_DIR.mkdir(exist_ok=True)

DEDUPLICATION_KEY = [
    'customer_id',
    'product_id',
    'order_date',
    'quantity',
    'discount_pct',
    'payment_method',
    'rating',
    'returned',
]

orders = pd.read_csv(DATA_DIR / 'orders.csv')
products = pd.read_csv(DATA_DIR / 'products.csv')
customers = pd.read_csv(DATA_DIR / 'customers.csv')

orders['payment_method'] = orders['payment_method'].str.strip().str.upper()
orders['discount_pct'] = pd.to_numeric(orders['discount_pct'], errors='coerce').fillna(0)
orders['rating'] = pd.to_numeric(orders['rating'], errors='coerce')
orders['returned'] = pd.to_numeric(orders['returned'], errors='raise').astype(int)
orders = orders.drop_duplicates(subset=DEDUPLICATION_KEY, keep='first').copy()

orders = orders.merge(
    products[['product_id', 'price']],
    on='product_id',
    how='left',
    validate='many_to_one',
)
orders = orders.merge(
    customers[['customer_id', 'city_tier']],
    on='customer_id',
    how='left',
    validate='many_to_one',
)
orders['order_value'] = (
    orders['quantity'] * orders['price'] * (1 - orders['discount_pct'] / 100)
)

quantity_q1 = orders['quantity'].quantile(0.25)
quantity_q3 = orders['quantity'].quantile(0.75)
quantity_iqr = quantity_q3 - quantity_q1
quantity_lower = quantity_q1 - 1.5 * quantity_iqr
quantity_upper = quantity_q3 + 1.5 * quantity_iqr
orders['is_outlier'] = (
    (orders['quantity'] < quantity_lower)
    | (orders['quantity'] > quantity_upper)
)

return_by_payment = (
    orders.groupby('payment_method')
    .agg(total_orders=('order_id', 'count'), returned_orders=('returned', 'sum'))
)
return_by_payment['return_rate_pct'] = (
    return_by_payment['returned_orders'] / return_by_payment['total_orders'] * 100
)
return_by_payment = return_by_payment.sort_values(
    ['return_rate_pct', 'payment_method'],
    ascending=[False, True],
)

cod_rate = float(return_by_payment.loc['COD', 'return_rate_pct'])
card_rate = float(return_by_payment.loc['CARD', 'return_rate_pct'])
cod_to_card_ratio = round(cod_rate / card_rate)

fig, ax = plt.subplots(figsize=(9, 5.5))
bars = ax.bar(
    return_by_payment.index,
    return_by_payment['return_rate_pct'],
    color=['#d95f59', '#4c9f70', '#5676a9'],
    width=0.62,
)
ax.bar_label(
    bars,
    labels=[f'{rate:.1f}%' for rate in return_by_payment['return_rate_pct']],
    padding=5,
    fontsize=10,
)
ax.set_title(
    f'COD Returns at {cod_rate:.1f}% ({cod_to_card_ratio}x Card)',
    loc='left',
    fontsize=15,
    fontweight='bold',
    pad=14,
)
ax.set_xlabel('Payment Method')
ax.set_ylabel('Return rate (%)')
ax.set_ylim(0, return_by_payment['return_rate_pct'].max() * 1.25)
ax.set_axisbelow(True)
ax.grid(axis='y', linestyle='--', alpha=0.25)
ax.spines[['top', 'right', 'left']].set_visible(False)
fig.tight_layout()
fig.savefig(OUT_DIR / 'return_rate_by_payment.png', dpi=300, bbox_inches='tight')
plt.close(fig)

orders['order_date'] = pd.to_datetime(orders['order_date'])
orders['month'] = orders['order_date'].dt.to_period('M').astype(str)
monthly_outlier_corrected = (
    orders.loc[~orders['is_outlier']]
    .groupby('month')['order_value']
    .sum()
    .sort_index()
)
peak_month = str(monthly_outlier_corrected.idxmax())
peak_label = pd.Period(peak_month, freq='M').strftime('%B %Y')

fig, ax = plt.subplots(figsize=(11, 5.5))
ax.plot(
    monthly_outlier_corrected.index,
    monthly_outlier_corrected.values,
    marker='o',
    color='#315f54',
    linewidth=2.5,
    markersize=5,
)
ax.fill_between(
    range(len(monthly_outlier_corrected)),
    monthly_outlier_corrected.values,
    color='#4c9f70',
    alpha=0.12,
)
ax.set_title(
    f'Outlier-Corrected Monthly Revenue - {peak_label} Peak',
    loc='left',
    fontsize=15,
    fontweight='bold',
    pad=14,
)
ax.set_xlabel('Month')
ax.set_ylabel('Order value (₹)')
ax.set_xticks(
    range(len(monthly_outlier_corrected)),
    monthly_outlier_corrected.index,
    rotation=35,
    ha='right',
)
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda value, _: f'₹{value:,.0f}'))
ax.set_axisbelow(True)
ax.grid(axis='y', linestyle='--', alpha=0.25)
ax.spines[['top', 'right', 'left']].set_visible(False)
fig.tight_layout()
fig.savefig(OUT_DIR / 'monthly_revenue_trend.png', dpi=300, bbox_inches='tight')
plt.close(fig)

print('Payment return rates (%), descending:')
print(return_by_payment['return_rate_pct'].round(1).to_string())
print('\nOutlier-corrected monthly order_value:')
print(monthly_outlier_corrected.round(2).to_string())
print(f'\nOutlier-corrected peak month: {peak_month}')
print('Saved visualization outputs to', OUT_DIR)
