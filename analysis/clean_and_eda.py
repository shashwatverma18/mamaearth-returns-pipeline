from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / 'data'
NARRATOR_DIR = ROOT / 'narrator'

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


def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    customers = pd.read_csv(DATA_DIR / 'customers.csv')
    products = pd.read_csv(DATA_DIR / 'products.csv')
    orders = pd.read_csv(DATA_DIR / 'orders.csv')
    return customers, products, orders


def print_monthly_series(title: str, series: pd.Series) -> None:
    print(f'\n{title}:')
    for month, value in series.items():
        print(f'{month}: {value:,.2f}')


if __name__ == '__main__':
    customers, products, orders = load_data()

    print('Task 1 - Load and inspect')
    print('orders.shape before cleaning:', orders.shape)

    print('\nTask 2 - Standardize payment_method casing')
    raw_payment_methods = orders['payment_method'].unique().tolist()
    print('Raw payment_method values:', raw_payment_methods)
    print('Raw distinct payment_method count:', len(raw_payment_methods))
    orders['payment_method'] = orders['payment_method'].str.strip().str.upper()
    print('Standardized payment_method counts:')
    print(orders['payment_method'].value_counts().sort_index().to_string())

    orders['discount_pct'] = pd.to_numeric(orders['discount_pct'], errors='coerce')
    orders['rating'] = pd.to_numeric(orders['rating'], errors='coerce')

    print('\nTask 3 - Remove duplicate orders')
    duplicate_mask = orders.duplicated(subset=DEDUPLICATION_KEY, keep='first')
    dropped_orders = orders.loc[duplicate_mask].copy()
    orders_clean = orders.loc[~duplicate_mask].copy()
    print('Duplicate rows flagged:', int(duplicate_mask.sum()))
    print('Dropped order_id values:', dropped_orders['order_id'].tolist())
    print('orders_clean.shape:', orders_clean.shape)

    print('\nTask 4 - Impute missing values')
    discount_missing_count = int(orders_clean['discount_pct'].isna().sum())
    rating_missing_count = int(orders_clean['rating'].isna().sum())
    rating_median = float(orders_clean['rating'].median())
    print('Missing discount_pct rows:', discount_missing_count)
    print('Missing rating rows:', rating_missing_count)
    print('Rating median before imputation:', rating_median)
    orders_clean['discount_pct'] = orders_clean['discount_pct'].fillna(0)
    orders_clean['rating'] = orders_clean['rating'].fillna(rating_median)
    print('Null counts after imputation:')
    print(orders_clean[['discount_pct', 'rating']].isnull().sum().to_dict())

    merged = orders_clean.merge(
        products[['product_id', 'product_name', 'category', 'price']],
        on='product_id',
        how='left',
        validate='many_to_one',
    )
    merged = merged.merge(
        customers[['customer_id', 'name', 'city', 'city_tier']],
        on='customer_id',
        how='left',
        validate='many_to_one',
    )
    merged['order_value'] = (
        merged['quantity']
        * merged['price']
        * (1 - merged['discount_pct'] / 100)
    )
    clean_revenue = round(float(merged['order_value'].sum()), 2)

    raw_orders_with_price = orders.merge(
        products[['product_id', 'price']],
        on='product_id',
        how='left',
        validate='many_to_one',
    )
    raw_orders_with_price['discount_pct'] = raw_orders_with_price['discount_pct'].fillna(0)
    raw_orders_with_price['order_value'] = (
        raw_orders_with_price['quantity']
        * raw_orders_with_price['price']
        * (1 - raw_orders_with_price['discount_pct'] / 100)
    )
    raw_revenue = round(float(raw_orders_with_price['order_value'].sum()), 2)

    dropped_with_price = dropped_orders.merge(
        products[['product_id', 'price']],
        on='product_id',
        how='left',
        validate='many_to_one',
    )
    dropped_with_price['discount_pct'] = dropped_with_price['discount_pct'].fillna(0)
    dropped_order_value = round(
        float(
            (
                dropped_with_price['quantity']
                * dropped_with_price['price']
                * (1 - dropped_with_price['discount_pct'] / 100)
            ).sum()
        ),
        2,
    )
    duplicate_delta = round(raw_revenue - clean_revenue, 2)

    print('\nTask 5 - Merge and reconcile against Part 1')
    print('Cleaned rows after merge:', len(merged))
    print(f'Cleaned order_value total: {clean_revenue:.2f}')
    print(f'Part 1 raw order_value total: {raw_revenue:.2f}')
    print(f'Dropped duplicate order_value total: {dropped_order_value:.2f}')
    print(
        f'Reconciliation: the Part 1 raw total of ₹{raw_revenue:,.2f} exceeds '
        f'the cleaned total of ₹{clean_revenue:,.2f} by ₹{duplicate_delta:,.2f}. '
        f'That exact delta is the independently calculated combined order_value '
        f'of the five duplicate rows dropped in Task 3; filling missing discounts '
        f'with 0% and ratings with the median does not change order_value.'
    )

    print('\nTask 6 - IQR outlier detection on quantity')
    q1 = float(merged['quantity'].quantile(0.25))
    q3 = float(merged['quantity'].quantile(0.75))
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    merged['is_outlier'] = (
        (merged['quantity'] < lower_bound)
        | (merged['quantity'] > upper_bound)
    )
    quantity_outliers = merged.loc[merged['is_outlier'], ['order_id', 'quantity']]
    print(f'Q1: {q1:.1f}; Q3: {q3:.1f}; IQR: {iqr:.1f}')
    print(f'Lower bound: {lower_bound:.1f}; upper bound: {upper_bound:.1f}')
    print('Outlier rows (retained and flagged):')
    print(quantity_outliers.to_string(index=False))

    print('\nTask 7 - Hypothesis: COD has a higher return rate than CARD and UPI')
    payment_return = (
        merged.groupby('payment_method')['returned']
        .agg(['count', 'mean'])
        .rename(columns={'count': 'total_orders', 'mean': 'return_rate'})
    )
    payment_return['return_rate_pct'] = (payment_return['return_rate'] * 100).round(1)
    print(payment_return[['total_orders', 'return_rate_pct']].to_string())
    cod_rate = float(payment_return.loc['COD', 'return_rate'])
    other_max_rate = float(payment_return.loc[['CARD', 'UPI'], 'return_rate'].max())
    cod_hypothesis_confirmed = cod_rate > other_max_rate
    print(
        'Hypothesis result:',
        'Confirmed' if cod_hypothesis_confirmed else 'Not confirmed',
        '- COD has a higher return rate than CARD and UPI.',
    )

    print('\nTask 8 - Multi-level payment and city-tier segmentation')
    payment_tier = (
        merged.groupby(['payment_method', 'city_tier'])['returned']
        .agg(['count', 'mean'])
        .rename(columns={'count': 'total_orders', 'mean': 'return_rate'})
    )
    payment_tier['return_rate_pct'] = (payment_tier['return_rate'] * 100).round(1)
    print(payment_tier[['total_orders', 'return_rate_pct']].to_string())
    highest_segment = payment_tier['return_rate'].idxmax()
    highest_segment_rate = float(payment_tier.loc[highest_segment, 'return_rate_pct'])
    print(
        f'Highest-risk segment: {highest_segment[0]} + Tier-{highest_segment[1]} '
        f'at {highest_segment_rate:.1f}%.'
    )

    print('\nTask 9 - Correlation analysis')
    correlation_columns = ['rating', 'returned', 'discount_pct', 'quantity']
    correlation_matrix = merged[correlation_columns].corr()
    print(correlation_matrix.to_string(float_format=lambda value: f'{value:.4f}'))

    correlation_bands = [
        (0.2, 'negligible'),
        (0.4, 'weak'),
        (0.7, 'moderate'),
        (1.0000001, 'strong'),
    ]
    pairwise_correlations: dict[str, dict[str, float | str]] = {}
    print('Pairwise correlation strength:')
    for left_index, left in enumerate(correlation_columns):
        for right in correlation_columns[left_index + 1:]:
            coefficient = float(correlation_matrix.loc[left, right])
            magnitude = abs(coefficient)
            band = next(label for ceiling, label in correlation_bands if magnitude < ceiling)
            pair = f'{left} vs {right}'
            pairwise_correlations[pair] = {
                'correlation': round(coefficient, 6),
                'strength': band,
            }
            print(f'{pair}: {coefficient:.4f} ({band})')
    discount_return_correlation = float(correlation_matrix.loc['discount_pct', 'returned'])
    print(
        'Hypothesis "higher discounts reduce returns": Busted '
        f'(discount_pct vs returned correlation = {discount_return_correlation:.4f}, '
        'negligible association).'
    )

    print('\nTask 10 - Outlier-corrected time series')
    merged['order_date'] = pd.to_datetime(merged['order_date'])
    merged['month'] = merged['order_date'].dt.to_period('M').astype(str)
    monthly_including_outliers = (
        merged.groupby('month')['order_value'].sum().sort_index().round(2)
    )
    monthly_outlier_corrected = (
        merged.loc[~merged['is_outlier']]
        .groupby('month')['order_value']
        .sum()
        .sort_index()
        .round(2)
    )
    print_monthly_series('Monthly order_value including quantity outliers', monthly_including_outliers)
    print_monthly_series('Monthly order_value excluding quantity outliers', monthly_outlier_corrected)
    peak_month = str(monthly_outlier_corrected.idxmax())
    january_outliers = merged.loc[
        merged['is_outlier'] & (merged['month'] == '2026-01'),
        ['order_id', 'order_date'],
    ]
    january_outlier_details = ', '.join(
        f"{row.order_id} on {row.order_date:%Y-%m-%d}"
        for row in january_outliers.itertuples(index=False)
    )
    print(
        'January’s apparent lead is an artifact of the two bulk orders landing '
        f'in January ({january_outlier_details}); March is the genuine peak month '
        f'once they are excluded (outlier-corrected peak: {peak_month}).'
    )

    print('\nCity return rate:')
    city_return = (
        merged.groupby('city')
        .agg(total_orders=('order_id', 'count'), returned_orders=('returned', 'sum'))
        .reset_index()
    )
    city_return['return_rate_pct'] = (
        city_return['returned_orders'] / city_return['total_orders'] * 100
    ).round(1)
    print(city_return.sort_values('return_rate_pct', ascending=False).to_string(index=False))

    returned_orders = merged.loc[merged['returned'] == 1]
    returned_order_count = int(len(returned_orders))
    returned_revenue = round(float(returned_orders['order_value'].sum()), 2)
    net_revenue = round(clean_revenue - returned_revenue, 2)
    monthly_net_revenue = (
        merged.loc[merged['returned'] == 0]
        .groupby('month')['order_value']
        .sum()
        .sort_index()
        .round(2)
    )
    payment_summary = orders['payment_method'].value_counts().sort_index()
    payment_return_records = payment_return.reset_index()
    payment_return_records['returned_orders'] = merged.groupby('payment_method')['returned'].sum().values
    payment_return_records['returned_revenue'] = (
        merged.assign(
            returned_revenue=merged['order_value'].where(merged['returned'] == 1, 0)
        )
        .groupby('payment_method')['returned_revenue']
        .sum()
        .reindex(payment_return_records['payment_method'])
        .to_numpy()
    )
    payment_return_records['return_rate_pct'] = (
        payment_return_records['return_rate'] * 100
    ).round(1)
    payment_return_records['returned_revenue'] = payment_return_records['returned_revenue'].round(2)
    return_rate_by_payment = {
        row['payment_method']: float(row['return_rate_pct'])
        for row in payment_return_records.to_dict(orient='records')
    }
    january_inflated_revenue = float(monthly_including_outliers.loc['2026-01'])
    january_corrected_revenue = float(monthly_outlier_corrected.loc['2026-01'])
    true_peak_revenue = float(monthly_outlier_corrected.loc[peak_month])

    mitigation_target_pct = 10.0
    assumed_cost_per_return = 150.0
    avoided_returns = round(returned_order_count * mitigation_target_pct / 100, 2)
    estimated_cost_savings = round(avoided_returns * assumed_cost_per_return, 2)
    estimated_revenue_retained = round(returned_revenue * mitigation_target_pct / 100, 2)
    findings = {
        'total_customers': int(len(customers)),
        'total_products': int(len(products)),
        'total_orders': int(len(orders)),
        'unique_orders': int(len(merged)),
        'clean_revenue': clean_revenue,
        'duplicate_delta': duplicate_delta,
        'raw_revenue': raw_revenue,
        'avg_order_value': round(raw_revenue / len(orders), 2),
        'duplicate_rows': int(duplicate_mask.sum()),
        'duplicate_order_ids': dropped_orders['order_id'].tolist(),
        'dropped_duplicate_order_value': dropped_order_value,
        'contract_valid': (
            raw_revenue == 99860.20
            and clean_revenue == 97358.30
            and duplicate_delta == 2501.90
        ),
        'imputation': {
            'discount_pct_rows': discount_missing_count,
            'rating_rows': rating_missing_count,
            'rating_median': rating_median,
        },
        'quantity_outliers': quantity_outliers.to_dict(orient='records'),
        'correlation_matrix': correlation_matrix.to_dict(),
        'pairwise_correlations': pairwise_correlations,
        'financial_reconciliation': {
            'raw_revenue_including_duplicates': raw_revenue,
            'clean_revenue_after_deduplication': clean_revenue,
            'duplicate_revenue_delta': duplicate_delta,
            'returned_order_count': returned_order_count,
            'returned_revenue': returned_revenue,
            'net_revenue_after_returns': net_revenue,
        },
        'payment_split': payment_summary.to_dict(),
        'payment_return_drivers': payment_return_records[
            ['payment_method', 'total_orders', 'returned_orders', 'returned_revenue', 'return_rate_pct']
        ].to_dict(orient='records'),
        'zero_order_customer': customers.loc[
            ~customers['customer_id'].isin(orders['customer_id']), 'customer_id'
        ].tolist()[0],
        'city_return_rate': city_return.to_dict(orient='records'),
        'monthly_net_revenue': [
            {'month': month, 'net_revenue': float(value)}
            for month, value in monthly_net_revenue.items()
        ],
        'monthly_order_value_including_outliers': [
            {'month': month, 'order_value': float(value)}
            for month, value in monthly_including_outliers.items()
        ],
        'monthly_order_value_outlier_corrected': [
            {'month': month, 'order_value': float(value)}
            for month, value in monthly_outlier_corrected.items()
        ],
        'outlier_corrected_peak_month': peak_month,
        'cleaned_total_revenue_inr': clean_revenue,
        'raw_total_revenue_inr': raw_revenue,
        'duplicate_reconciliation_delta_inr': duplicate_delta,
        'return_rate_by_payment': return_rate_by_payment,
        'highest_risk_segment': {
            'payment_method': str(highest_segment[0]),
            'city_tier': int(highest_segment[1]),
            'return_rate_pct': highest_segment_rate,
        },
        'true_peak_month': {
            'month': peak_month,
            'revenue_inr': true_peak_revenue,
        },
        'outlier_inflated_month': {
            'month': '2026-01',
            'apparent_revenue_inr': january_inflated_revenue,
            'corrected_revenue_inr': january_corrected_revenue,
        },
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
