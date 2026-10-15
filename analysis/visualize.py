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

orders = pd.read_csv(DATA_DIR / 'orders.csv')
products = pd.read_csv(DATA_DIR / 'products.csv')
orders['discount_pct'] = pd.to_numeric(orders['discount_pct'], errors='coerce')
orders['returned'] = pd.to_numeric(orders['returned'], errors='coerce').fillna(0).astype(int)
orders = orders.merge(products[['product_id', 'price']], on='product_id', how='left')
orders['revenue'] = orders['quantity'] * orders['price'] * (1 - orders['discount_pct'].fillna(0) / 100.0)
orders = orders.drop_duplicates(
    subset=['customer_id', 'product_id', 'order_date', 'quantity', 'discount_pct', 'payment_method', 'rating', 'returned'],
    keep='first',
)

# Payment-method return rate plot.
return_by_payment = (
    orders.groupby('payment_method')
    .agg(total_orders=('order_id', 'count'), returned_orders=('returned', 'sum'))
    .reindex(['COD', 'UPI', 'CARD'], fill_value=0)
    .rename_axis('payment_method')
    .reset_index()
)
return_by_payment['return_rate_pct'] = (return_by_payment['returned_orders'] / return_by_payment['total_orders'] * 100).round(1)

fig, ax = plt.subplots(figsize=(9, 5.5))
bars = ax.bar(return_by_payment['payment_method'], return_by_payment['return_rate_pct'], color=['#d95f59', '#4c9f70', '#5676a9'], width=0.62)
ax.bar_label(bars, labels=[f'{rate:.1f}%  ({count} orders)' for rate, count in zip(return_by_payment['return_rate_pct'], return_by_payment['total_orders'])], padding=5, fontsize=9)
ax.set_title('Return Rate by Payment Method', loc='left', fontsize=15, fontweight='bold', pad=14)
ax.set_xlabel('Payment Method')
ax.set_ylabel('Return rate (%)')
ax.set_ylim(0, max(return_by_payment['return_rate_pct'].max() * 1.25, 1))
ax.set_axisbelow(True)
ax.grid(axis='y', linestyle='--', alpha=0.25)
ax.spines[['top', 'right', 'left']].set_visible(False)
fig.tight_layout()
fig.savefig(OUT_DIR / 'return_rate_by_payment.png', dpi=300, bbox_inches='tight')
plt.close(fig)

# Monthly net revenue after excluding returned orders.
orders['order_date'] = pd.to_datetime(orders['order_date'])
net_orders = orders.loc[orders['returned'] == 0].copy()
monthly = net_orders.groupby(net_orders['order_date'].dt.to_period('M'))['revenue'].sum().reset_index()
monthly['order_date'] = monthly['order_date'].astype(str)

fig, ax = plt.subplots(figsize=(11, 5.5))
ax.plot(monthly['order_date'], monthly['revenue'], marker='o', color='#315f54', linewidth=2.5, markersize=5)
ax.fill_between(range(len(monthly)), monthly['revenue'], color='#4c9f70', alpha=0.12)
ax.set_title('Monthly Net Revenue After Returns', loc='left', fontsize=15, fontweight='bold', pad=14)
ax.set_xlabel('Month')
ax.set_ylabel('Net revenue (₹)')
ax.set_xticks(range(len(monthly)), monthly['order_date'], rotation=35, ha='right')
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda value, _: f'₹{value:,.0f}'))
ax.set_axisbelow(True)
ax.grid(axis='y', linestyle='--', alpha=0.25)
ax.spines[['top', 'right', 'left']].set_visible(False)
fig.tight_layout()
fig.savefig(OUT_DIR / 'monthly_revenue_trend.png', dpi=300, bbox_inches='tight')
plt.close(fig)

print('Saved visualization outputs to', OUT_DIR)
