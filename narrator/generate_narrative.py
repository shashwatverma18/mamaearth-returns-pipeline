from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FINDINGS_PATH = ROOT / 'narrator' / 'findings.json'
OUT_PATH = ROOT / 'narrator' / 'sample_output.txt'


def build_fallback_narrative(metrics: dict) -> str:
    reconciliation = metrics.get('financial_reconciliation', {})
    savings = metrics.get('cost_savings_scenario', {})
    payment_drivers = sorted(metrics.get('payment_return_drivers', []), key=lambda item: item.get('return_rate_pct', 0), reverse=True)
    city_drivers = sorted(metrics.get('city_return_rate', []), key=lambda item: item.get('return_rate_pct', 0), reverse=True)
    highest_payment = payment_drivers[0] if payment_drivers else {}
    highest_city = city_drivers[0] if city_drivers else {}

    sections = [
        'MAMAEARTH | RETURNS EXECUTIVE BRIEFING',
        'Regional Operations and Finance',
        '',
        'EXECUTIVE READOUT',
        (
            f"The ledger contains {metrics.get('total_orders', 0)} orders, of which "
            f"{reconciliation.get('returned_order_count', 0)} unique orders were returned. "
            f"Net revenue after returns is ₹{reconciliation.get('net_revenue_after_returns', 0):,.2f}."
        ),
        '',
        'RETURN HOTSPOTS',
    ]
    if highest_payment:
        sections.append(
            f"{highest_payment.get('payment_method', 'Unknown')} has the highest payment-method return rate at "
            f"{highest_payment.get('return_rate_pct', 0):.1f}% "
            f"({highest_payment.get('returned_orders', 0)} of {highest_payment.get('total_orders', 0)} orders)."
        )
    if highest_city:
        sections.append(
            f"{highest_city.get('city', 'Unknown')} has the highest city return rate at "
            f"{highest_city.get('return_rate_pct', 0):.1f}% "
            f"({highest_city.get('returned_orders', 0)} of {highest_city.get('total_orders', 0)} orders)."
        )
    sections.extend([
        '',
        'FINANCIAL POSITION',
        (
            f"Raw revenue is ₹{reconciliation.get('raw_revenue_including_duplicates', 0):,.2f}; "
            f"clean revenue after duplicate removal is ₹{reconciliation.get('clean_revenue_after_deduplication', 0):,.2f}. "
            f"The duplicate revenue delta is ₹{reconciliation.get('duplicate_revenue_delta', 0):,.2f}, "
            f"and returned-order revenue is ₹{reconciliation.get('returned_revenue', 0):,.2f}."
        ),
        (
            f"Planning scenario: a {savings.get('return_reduction_target_pct', 0):g}% reduction in returns would avoid an estimated "
            f"{savings.get('estimated_avoided_returns', 0):g} returns and save approximately "
            f"₹{savings.get('estimated_cost_savings', 0):,.2f} in handling costs. "
            f"This uses an assumed cost of ₹{savings.get('assumed_cost_per_avoided_return', 0):,.2f} per avoided return; "
            'it is not a measured or guaranteed saving.'
        ),
        '',
        'RECOMMENDED ACTIONS',
        (
            f"1. Regional Operations: review the {highest_payment.get('payment_method', 'highest-risk payment')} and "
            f"{highest_city.get('city', 'highest-risk city')} return journeys first; test delivery confirmation, address validation, "
            'and clearer pre-purchase product information, then compare return rates with the current baseline.'
        ),
        '2. Finance: validate the assumed handling cost against actual reverse-logistics expenses and quantify contribution margin at risk before booking savings.',
        '3. Operations: reconcile duplicate submissions at order intake and monitor the monthly net-revenue trend alongside returned-order counts.',
        '',
        'The savings figure is directional because actual per-return costs and contribution margins were not supplied.',
    ])
    return '\n'.join(sections)


def generate_with_gemini(metrics: dict) -> str:
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        return build_fallback_narrative(metrics)

    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        request = {
            'model': 'gemini-2.0-flash',
            'contents': [
                {
                    'text': (
                        'You are an executive briefing writer for Mamaearth Regional Operations and Finance leadership. '
                        'Write a concise briefing with these sections: Executive Readout, Return Hotspots, Financial Position, and Recommended Actions. '
                        'Give specific operational actions for the highest-return payment method and city in the supplied findings. '
                        'Explain the cost-savings scenario and state its assumptions; distinguish estimated savings from actual savings. '
                        'Use only figures present in the supplied JSON, do not calculate or invent additional metrics, and do not mention code, scripts, dataframes, or Pandas. '
                        'Do not claim margin impact because contribution-margin data is not supplied. '
                        'Verified findings: ' + json.dumps(metrics, ensure_ascii=False)
                    )
                }
            ],
            'config': {
                'temperature': 0.0,
                'max_output_tokens': 1024,
                'response_mime_type': 'text/plain',
            },
        }
        response = client.models.generate_content(**request)
        return response.text or build_fallback_narrative(metrics)
    except Exception:
        return build_fallback_narrative(metrics)


if __name__ == '__main__':
    findings = json.loads(FINDINGS_PATH.read_text())
    narrative = generate_with_gemini(findings)
    OUT_PATH.write_text(narrative)
    print(narrative)
