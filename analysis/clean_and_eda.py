from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / 'data'
NARRATOR_DIR = ROOT / 'narrator'


def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    customers = pd.read_csv(DATA_DIR / 'customers.csv')
    products = pd.read_csv(DATA_DIR / 'products.csv')
    orders = pd.read_csv(DATA_DIR / 'orders.csv')
    orders['discount_pct'] = pd.to_numeric(orders['discount_pct'], errors='coerce')
    orders['rating'] = pd.to_numeric(orders['rating'], errors='coerce')
    return customers, products, orders


def compute_revenue(row: pd.Series) -> float:
    price = row['price']
    discount = row['discount_pct'] if pd.notna(row['discount_pct']) else 0.0
    return float(row['quantity'] * price * (1 - discount / 100.0))


if __name__ == '__main__':
    customers, products, orders = load_data()
    merged = orders.merge(products[['product_id', 'price', 'category']], on='product_id', how='left')
    merged = merged.merge(customers[['customer_id', 'city']], on='customer_id', how='left')
    merged['revenue'] = merged.apply(compute_revenue, axis=1)

    raw_revenue = round(float(merged['revenue'].sum()), 2)
    duplicate_mask = merged.duplicated(subset=['customer_id', 'product_id', 'order_date', 'quantity', 'discount_pct', 'payment_method', 'rating', 'returned'], keep='first')
    duplicate_count = int(duplicate_mask.sum())
    deduped = merged.loc[~duplicate_mask].copy()
    clean_revenue = round(float(deduped['revenue'].sum()), 2)
    duplicate_delta = round(raw_revenue - clean_revenue, 2)
    returned_orders = deduped.loc[deduped['returned'] == 1]
    returned_order_count = int(len(returned_orders))
    returned_revenue = round(float(returned_orders['revenue'].sum()), 2)
    net_revenue = round(clean_revenue - returned_revenue, 2)
    contract_valid = raw_revenue == 99860.20 and clean_revenue == 97358.30 and duplicate_delta == 2501.90

    print('customers:', len(customers))
    print('products:', len(products))
    print('raw_orders:', len(orders))
    print('duplicate_rows:', duplicate_count)
    print('raw_revenue:', raw_revenue)
    print('clean_revenue:', clean_revenue)
    print('duplicate_delta:', duplicate_delta)
    print('returned_orders:', returned_order_count)
    print('returned_revenue:', returned_revenue)
    print('net_revenue_after_returns:', net_revenue)
    print('is_contract_valid:', contract_valid)

    city_return = (
        deduped
        .groupby('city')
        .agg(total_orders=('order_id', 'count'), returned_orders=('returned', 'sum'))
        .reset_index()
    )
    city_return['return_rate_pct'] = (city_return['returned_orders'] / city_return['total_orders'] * 100).round(1)
    print('\nCity return rate:')
    print(city_return.sort_values('return_rate_pct', ascending=False).to_string(index=False))

    payment_summary = orders['payment_method'].value_counts().sort_index()
    print('\nPayment split:')
    print(payment_summary.to_string())

    payment_return = (
        deduped.assign(returned_revenue=deduped['revenue'].where(deduped['returned'] == 1, 0))
        .groupby('payment_method')
        .agg(total_orders=('order_id', 'count'), returned_orders=('returned', 'sum'), returned_revenue=('returned_revenue', 'sum'))
        .reset_index()
    )
    payment_return['return_rate_pct'] = (payment_return['returned_orders'] / payment_return['total_orders'] * 100).round(1)
    payment_return['returned_revenue'] = payment_return['returned_revenue'].round(2)

    monthly_net = deduped.loc[deduped['returned'] == 0].copy()
    monthly_net['month'] = pd.to_datetime(monthly_net['order_date']).dt.to_period('M').astype(str)
    monthly_revenue = (
        monthly_net.groupby('month', as_index=False)['revenue'].sum()
        .rename(columns={'revenue': 'net_revenue'})
    )
    monthly_revenue['net_revenue'] = monthly_revenue['net_revenue'].round(2)

    mitigation_target_pct = 10.0
    assumed_cost_per_return = 150.0
    avoided_returns = round(returned_order_count * mitigation_target_pct / 100, 2)
    estimated_cost_savings = round(avoided_returns * assumed_cost_per_return, 2)
    estimated_revenue_retained = round(returned_revenue * mitigation_target_pct / 100, 2)

    findings = {
        'total_customers': int(len(customers)),
        'total_products': int(len(products)),
        'total_orders': int(len(orders)),
        'unique_orders': int(len(deduped)),
        'clean_revenue': clean_revenue,
        'duplicate_delta': duplicate_delta,
        'raw_revenue': raw_revenue,
        'avg_order_value': round(raw_revenue / len(orders), 2),
        'duplicate_rows': duplicate_count,
        'contract_valid': contract_valid,
        'financial_reconciliation': {
            'raw_revenue_including_duplicates': raw_revenue,
            'clean_revenue_after_deduplication': clean_revenue,
            'duplicate_revenue_delta': duplicate_delta,
            'returned_order_count': returned_order_count,
            'returned_revenue': returned_revenue,
            'net_revenue_after_returns': net_revenue,
        },
        'payment_split': payment_summary.to_dict(),
        'payment_return_drivers': payment_return.to_dict(orient='records'),
        'zero_order_customer': customers.loc[~customers['customer_id'].isin(orders['customer_id']), 'customer_id'].tolist()[0] if not customers['customer_id'].isin(orders['customer_id']).all() else None,
        'city_return_rate': city_return.to_dict(orient='records'),
        'monthly_net_revenue': monthly_revenue.to_dict(orient='records'),
        'cost_savings_scenario': {
            'return_reduction_target_pct': mitigation_target_pct,
            'assumed_cost_per_avoided_return': assumed_cost_per_return,
            'baseline_returned_orders': returned_order_count,
            'estimated_avoided_returns': avoided_returns,
            'estimated_cost_savings': estimated_cost_savings,
            'estimated_revenue_retained': estimated_revenue_retained,
            'assumptions': 'Planning scenario only: 10% fewer returns and an assumed handling cost of ₹150 per avoided return; actual cost data was not provided.',
        },
    }
    NARRATOR_DIR.mkdir(exist_ok=True)
    (NARRATOR_DIR / 'findings.json').write_text(json.dumps(findings, indent=2))

    conn = sqlite3.connect(':memory:')
    customers.to_sql('customers', conn, index=False)
    products.to_sql('products', conn, index=False)
    orders.to_sql('orders', conn, index=False)
    contract_sql = """
    SELECT COUNT(*) AS total_orders,
           ROUND(SUM(quantity * p.price * (1 - COALESCE(o.discount_pct,0)/100.0)), 2) AS total_revenue,
           ROUND(AVG(quantity * p.price * (1 - COALESCE(o.discount_pct,0)/100.0)), 2) AS avg_order_value
    FROM orders o
    JOIN products p ON p.product_id = o.product_id
    """
    sql_result = conn.execute(contract_sql).fetchone()
    print('\nSQL contract check:', sql_result)
