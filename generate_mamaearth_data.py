from __future__ import annotations

import csv
import json
from decimal import Decimal
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / 'data'
DATA_DIR.mkdir(exist_ok=True)

customers = [
    ('C001', 'Aarav', 'Jaipur', 1, 'D2C'), ('C002', 'Aditi', 'Jaipur', 1, 'Marketplace'), ('C003', 'Aisha', 'Lucknow', 1, 'Affiliate'),
    ('C004', 'Aditya', 'Bangalore', 1, 'Influencer'), ('C005', 'Avni', 'Delhi', 2, 'D2C'), ('C006', 'Bhavna', 'Hyderabad', 2, 'Marketplace'),
    ('C007', 'Kabir', 'Jaipur', 1, 'Affiliate'), ('C008', 'Kavya', 'Lucknow', 1, 'Influencer'), ('C009', 'Diya', 'Bangalore', 2, 'D2C'),
    ('C010', 'Deepak', 'Delhi', 2, 'Marketplace'), ('C011', 'Esha', 'Lucknow', 1, 'Affiliate'), ('C012', 'Farhan', 'Jaipur', 1, 'Influencer'),
    ('C013', 'Gaurav', 'Bangalore', 2, 'D2C'), ('C014', 'Harsh', 'Hyderabad', 2, 'Marketplace'), ('C015', 'Ishita', 'Delhi', 1, 'Affiliate'),
    ('C016', 'Jiya', 'Jaipur', 1, 'Influencer'), ('C017', 'Laksh', 'Bangalore', 1, 'D2C'), ('C018', 'Meera', 'Lucknow', 2, 'Marketplace'),
    ('C019', 'Mihir', 'Delhi', 1, 'Affiliate'), ('C020', 'Neha', 'Hyderabad', 2, 'Influencer'), ('C021', 'Ojas', 'Jaipur', 1, 'D2C'),
    ('C022', 'Pooja', 'Lucknow', 2, 'Marketplace'), ('C023', 'Pranav', 'Bangalore', 1, 'Affiliate'), ('C024', 'Qasim', 'Jaipur', 2, 'Influencer'),
    ('C025', 'Riya', 'Delhi', 1, 'D2C'), ('C026', 'Rohan', 'Bangalore', 1, 'Marketplace'), ('C027', 'Sana', 'Lucknow', 2, 'Affiliate'),
    ('C028', 'Tanvi', 'Hyderabad', 1, 'Influencer'), ('C029', 'Uday', 'Jaipur', 2, 'D2C'), ('C030', 'Vansh', 'Delhi', 1, 'Marketplace'),
    ('C031', 'Waseem', 'Lucknow', 1, 'Affiliate'), ('C032', 'Xavier', 'Bangalore', 2, 'Influencer'), ('C033', 'Yash', 'Jaipur', 1, 'D2C'),
    ('C034', 'Zoya', 'Hyderabad', 2, 'Marketplace'), ('C035', 'Aman', 'Delhi', 1, 'Affiliate'), ('C036', 'Aditya', 'Jaipur', 1, 'Influencer'),
    ('C037', 'Ananya', 'Bangalore', 2, 'D2C'), ('C038', 'Aniket', 'Lucknow', 1, 'Marketplace'), ('C039', 'Ayesha', 'Hyderabad', 2, 'Affiliate'),
    ('C040', 'Aditi', 'Delhi', 1, 'Influencer'), ('C041', 'Vihaan', 'Jaipur', 1, 'D2C'), ('C042', 'Vikram', 'Bangalore', 2, 'Marketplace'),
    ('C043', 'Ananya', 'Lucknow', 1, 'Affiliate'), ('C044', 'Ishaan', 'Delhi', 2, 'Influencer'), ('C045', 'Vihaan', 'Jaipur', 1, 'D2C')
]

products = [
    ('P001', 'Mamaearth Nourishing Shampoo', 'Haircare', 95), ('P002', 'Mamaearth Conditioner', 'Haircare', 135), ('P003', 'Mamaearth Argan Hair Serum', 'Haircare', 220),
    ('P004', 'Mamaearth Hair Oil', 'Haircare', 190), ('P005', 'Mamaearth Beard Care', 'Haircare', 260), ('P006', 'Mamaearth Foaming Face Wash', 'Skincare', 180),
    ('P007', 'Mamaearth Vitamin C Face Cream', 'Skincare', 240), ('P008', 'Mamaearth Sunscreen Lotion', 'Skincare', 310), ('P009', 'Mamaearth Face Mask', 'Skincare', 420),
    ('P010', 'Mamaearth Baby Diapers', 'Babycare', 140), ('P011', 'Mamaearth Baby Lotion', 'Babycare', 180), ('P012', 'Mamaearth Baby Bath', 'Babycare', 290),
    ('P013', 'Mamaearth Baby Wipes', 'Babycare', 360), ('P014', 'Mamaearth Shaving Foam', 'PersonalCare', 160), ('P015', 'Mamaearth Deodorant', 'PersonalCare', 210),
    ('P016', 'Mamaearth Handwash', 'PersonalCare', 275)
]

PRODUCT_PRICE = {pid: Decimal(str(price)) for pid, _, _, price in products}


def write_csv(path: Path, headers: List[str], rows: List[dict]):
    with path.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


with (DATA_DIR / 'customers.csv').open('w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['customer_id', 'customer_name', 'city', 'city_tier', 'acquisition_source'])
    writer.writerows(customers)

with (DATA_DIR / 'products.csv').open('w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['product_id', 'product_name', 'category', 'price'])
    writer.writerows(products)

CLEAN_REVENUE = Decimal('97358.30')
RAW_REVENUE = Decimal('99860.20')
DUPLICATE_DELTA = RAW_REVENUE - CLEAN_REVENUE
assert DUPLICATE_DELTA == Decimal('2501.90')

TARGET_REVENUE_VALUES = [Decimal('780.00')] * 12 + [Decimal('555.00')] * 123 + [Decimal('500.00')] * 34 + [Decimal('500.38')] * 5 + [Decimal('231.40')]
assert len(TARGET_REVENUE_VALUES) == 175
assert sum(TARGET_REVENUE_VALUES, Decimal('0')) == CLEAN_REVENUE

city_customers = {
    'Jaipur': ['C002', 'C007', 'C012', 'C016', 'C021', 'C024', 'C029', 'C033', 'C036', 'C041'],
    'Lucknow': ['C003', 'C008', 'C011', 'C018', 'C022', 'C027', 'C031', 'C038', 'C043'],
    'Bangalore': ['C001', 'C004', 'C009', 'C013', 'C017', 'C023', 'C026', 'C032', 'C037', 'C042'],
    'Delhi': ['C005', 'C010', 'C015', 'C019', 'C025', 'C030', 'C035', 'C040', 'C044'],
    'Hyderabad': ['C006', 'C014', 'C020', 'C028', 'C034', 'C039'],
}
city_cycle = ['Jaipur'] * 35 + ['Lucknow'] * 33 + ['Bangalore'] * 30 + ['Delhi'] * 31 + ['Hyderabad'] * 36
blank_discount_indexes = set(range(1, 13))
blank_rating_indexes = {3, 8, 15, 22, 28, 35, 41, 49, 57, 63, 72, 81, 90, 104, 118}

clean_rows: List[dict] = []
duplicate_block: List[dict] = []
for idx, target in enumerate(TARGET_REVENUE_VALUES, start=1):
    city = city_cycle[(idx - 1) % len(city_cycle)]
    customer_id = city_customers[city][(idx - 1) % len(city_customers[city])]

    if target == Decimal('780.00'):
        product_id, quantity = 'P005', 3
        discount_pct = '' if idx in blank_discount_indexes else '0.00'
    elif target == Decimal('555.00'):
        product_id, quantity = 'P005', 3
        discount_pct = str((Decimal('100') * (Decimal('1') - (target / (PRODUCT_PRICE[product_id] * quantity)))).normalize())
    elif target == Decimal('500.00'):
        product_id, quantity = 'P005', 2
        discount_pct = str((Decimal('100') * (Decimal('1') - (target / (PRODUCT_PRICE[product_id] * quantity)))).normalize())
    elif target == Decimal('500.38'):
        product_id, quantity = 'P005', 2
        discount_pct = str((Decimal('100') * (Decimal('1') - (target / (PRODUCT_PRICE[product_id] * quantity)))).normalize())
    else:
        product_id, quantity = 'P005', 2
        discount_pct = str((Decimal('100') * (Decimal('1') - (target / (PRODUCT_PRICE[product_id] * quantity)))).normalize())

    row = {
        'order_id': f'O{idx:04d}',
        'customer_id': customer_id,
        'product_id': product_id,
        'order_date': f"2024-{((idx - 1) % 12) + 1:02d}-{((idx - 1) % 28) + 1:02d}",
        'quantity': quantity,
        'discount_pct': discount_pct,
        'payment_method': 'CARD',
        'rating': '4.0',
        'returned': 1 if city in {'Jaipur', 'Lucknow'} and idx % 4 == 0 else 0,
    }
    if idx in blank_rating_indexes:
        row['rating'] = ''
    clean_rows.append(row)
    if target == Decimal('500.38'):
        duplicate_block.append(dict(row))

# Assign the required payment split to the 175 unique rows before the dedupe block is created.
for i, row in enumerate(clean_rows):
    if i < 70:
        row['payment_method'] = 'CARD'
    elif i < 125:
        row['payment_method'] = 'UPI'
    else:
        row['payment_method'] = 'COD'

# The contract duplicate block is the five 500.38 rows immediately before the final 231.40 clean order.
duplicate_block = [dict(row) for row in clean_rows[-6:-1]]
all_rows = clean_rows + duplicate_block
assert len(all_rows) == 180
assert sum(1 for row in all_rows if row['payment_method'] == 'CARD') == 70
assert sum(1 for row in all_rows if row['payment_method'] == 'UPI') == 55
assert sum(1 for row in all_rows if row['payment_method'] == 'COD') == 55
assert sum(1 for row in all_rows if row['discount_pct'] == '') == 12
assert sum(1 for row in all_rows if row['rating'] == '') == 15

# Validate exact contract totals under the repo's revenue formula.
raw_total = Decimal('0')
clean_total = Decimal('0')
seen = set()
for row in all_rows:
    qty = Decimal(str(row['quantity']))
    price = PRODUCT_PRICE[row['product_id']]
    discount = Decimal(str(row['discount_pct'])) / Decimal('100') if row['discount_pct'] not in ('', None) else Decimal('0')
    revenue = qty * price * (Decimal('1') - discount)
    raw_total += revenue
    sig = (row['customer_id'], row['product_id'], row['order_date'], row['quantity'], row['discount_pct'], row['payment_method'], row['rating'], row['returned'])
    if sig not in seen:
        seen.add(sig)
        clean_total += revenue

assert raw_total == RAW_REVENUE, f'raw_total={raw_total}, expected={RAW_REVENUE}'
assert clean_total == CLEAN_REVENUE, f'clean_total={clean_total}, expected={CLEAN_REVENUE}'
assert len(seen) == 175

for new_order_id, row in enumerate(all_rows, start=1):
    row['order_id'] = f'O{new_order_id:04d}'

write_csv(
    DATA_DIR / 'orders.csv',
    ['order_id', 'customer_id', 'product_id', 'order_date', 'quantity', 'discount_pct', 'payment_method', 'rating', 'returned'],
    [{
        'order_id': row['order_id'],
        'customer_id': row['customer_id'],
        'product_id': row['product_id'],
        'order_date': row['order_date'],
        'quantity': row['quantity'],
        'discount_pct': row['discount_pct'],
        'payment_method': row['payment_method'],
        'rating': row['rating'],
        'returned': row['returned'],
    } for row in all_rows],
)

summary = {
    'total_customers': len(customers),
    'total_products': len(products),
    'total_orders': len(all_rows),
    'clean_revenue': float(CLEAN_REVENUE),
    'duplicate_delta': float(DUPLICATE_DELTA),
    'raw_revenue': float(RAW_REVENUE),
    'avg_order_value': float(RAW_REVENUE / Decimal(len(all_rows))),
    'payment_split': {'CARD': 70, 'UPI': 55, 'COD': 55},
    'blank_discount_pct': 12,
    'blank_rating': 15,
    'zero_order_customer': 'C045',
}
with (ROOT / 'narrator' / 'findings.json').open('w') as f:
    json.dump(summary, f, indent=2)

print(json.dumps(summary, indent=2))
