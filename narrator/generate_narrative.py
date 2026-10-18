from __future__ import annotations

from datetime import datetime
import json
import os
from pathlib import Path
from typing import Any

from google import genai
from google.genai import types

ROOT = Path(__file__).resolve().parents[1]
FINDINGS_PATH = ROOT / 'narrator' / 'findings.json'
OUT_PATH = ROOT / 'narrator' / 'sample_output.txt'
MODEL = 'gemini-2.0-flash'
REQUEST_TIMEOUT_MS = 30_000

SYSTEM_INSTRUCTION = (
    "You are a senior data analyst writing for Mamaearth's regional ops and "
    'finance heads. Return exactly three labeled sections: Situation, '
    'Complication, and Resolution. Every number in the output must come from '
    'the supplied findings and appear with the same value; do not invent, '
    'recalculate, round, or introduce any statistics. Explain the revenue '
    'reconciliation, COD and city-tier risk, and outlier-corrected peak month. '
    'Keep the narrative concise and actionable.'
)


def _result(status: str, narrative: str | None, tokens: Any = None, message: str | None = None) -> dict:
    if status == 'error':
        return {
            'status': 'error',
            'narrative': None,
            'message': message or 'Narrative generation failed.',
        }
    return {'status': status, 'narrative': narrative, 'tokens': tokens}


def generate_scr_narrative_offline(findings: dict) -> dict:
    """Build a deterministic SCR briefing directly from verified findings."""
    payment_rates = findings['return_rate_by_payment']
    highest_risk = findings['highest_risk_segment']
    true_peak = findings['true_peak_month']
    inflated_month = findings['outlier_inflated_month']
    true_peak_month_name = datetime.strptime(true_peak['month'], '%Y-%m').strftime('%B %Y')

    narrative = (
        'Situation\n'
        f"The cleaned order revenue is INR {findings['cleaned_total_revenue_inr']:,.2f}, "
        f"reconciled from raw revenue of INR {findings['raw_total_revenue_inr']:,.2f}. "
        f"After correcting for quantity outliers, {true_peak_month_name} is the peak "
        f"month with order revenue of INR {true_peak['revenue_inr']:,.2f}.\n\n"
        'Complication\n'
        f"Duplicate submissions account for INR "
        f"{findings['duplicate_reconciliation_delta_inr']:,.2f} of the raw-to-clean "
        f"revenue difference. COD has a {payment_rates['COD']:.1f}% return rate "
        f"versus {payment_rates['CARD']:.1f}% for CARD and {payment_rates['UPI']:.1f}% "
        f"for UPI. The highest-risk segment is {highest_risk['payment_method']} in "
        f"Tier-{highest_risk['city_tier']} cities at "
        f"{highest_risk['return_rate_pct']:.1f}%. January's apparent order revenue "
        f"of INR {inflated_month['apparent_revenue_inr']:,.2f} falls to INR "
        f"{inflated_month['corrected_revenue_inr']:,.2f} after removing the two "
        'bulk-order outliers.\n\n'
        'Resolution\n'
        f"Prioritize COD return reduction in Tier-{highest_risk['city_tier']} "
        'cities, and monitor the corrected monthly series rather than the '
        f"outlier-inflated January figure. Use {true_peak_month_name} and its "
        f"INR {true_peak['revenue_inr']:,.2f} order revenue as the corrected "
        'peak-month reference; continue reconciling duplicate orders before '
        'reporting revenue.'
    )
    return _result('success', narrative, tokens=None)


def _generate_scr_narrative_online(findings: dict, api_key: str) -> dict:
    """Return a structured success or error result for one Gemini request."""
    try:
        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=REQUEST_TIMEOUT_MS),
        )
        user_prompt = (
            'Write a business briefing using only these verified findings. '
            'Preserve every numeric value exactly as provided. Findings JSON:\n'
            + json.dumps(findings, ensure_ascii=False, sort_keys=True)
        )
        response = client.models.generate_content(
            model=MODEL,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                # Zero temperature keeps this factual report deterministic.
                temperature=0.0,
                max_output_tokens=1024,
                response_mime_type='text/plain',
            ),
        )
        narrative = response.text
        if not narrative:
            raise ValueError('Gemini returned an empty narrative.')
        usage = getattr(response, 'usage_metadata', None)
        tokens = getattr(usage, 'total_token_count', None)
        return _result('success', narrative, tokens=tokens)
    except Exception as err:
        return _result('error', None, message=str(err))


def generate_scr_narrative(findings: dict) -> dict:
    """Generate SCR via Gemini, falling back to the offline template on error."""
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        return generate_scr_narrative_offline(findings)

    online_result = _generate_scr_narrative_online(findings, api_key)
    if online_result['status'] == 'success':
        online_narrative = online_result['narrative']
        if online_narrative is not None and _has_required_figures(online_narrative):
            return online_result
        print('Gemini narrative omitted required figures; using offline SCR fallback.')
        return generate_scr_narrative_offline(findings)

    print(
        'Gemini narrative request failed; using offline SCR fallback: '
        f"{online_result['message']}"
    )
    return generate_scr_narrative_offline(findings)


def _has_required_figures(narrative: str) -> bool:
    normalized = narrative.replace(',', '')
    return all(
        expected in normalized
        for expected in ('97358.30', '44.4', '54.5', '2501.90')
    ) and 'March' in narrative and '20318.90' in normalized


def check_numeric_accuracy(narrative: str) -> bool:
    """Assert and report every required figure in the saved narrative."""
    normalized = narrative.replace(',', '')
    march_peak_present = 'March' in narrative and '20318.90' in normalized
    checks = [
        ('cleaned revenue', '97358.30'),
        ('COD return rate', '44.4'),
        ('COD Tier-2 return rate', '54.5'),
        ('duplicate reconciliation delta', '2501.90'),
    ]
    all_passed = True
    for label, expected in checks:
        try:
            assert expected in normalized, f'missing {expected}'
            print(f'PASS: {label} ({expected})')
        except AssertionError as err:
            all_passed = False
            print(f'FAIL: {label} ({err})')
    try:
        assert march_peak_present, 'missing March with peak revenue 20318.90'
        print('PASS: true peak month (March, 20318.90)')
    except AssertionError as err:
        all_passed = False
        print(f'FAIL: true peak month ({err})')
    return all_passed


def main() -> int:
    findings = json.loads(FINDINGS_PATH.read_text())
    result = generate_scr_narrative(findings)
    narrative = result['narrative']
    if result['status'] != 'success' or narrative is None:
        print(f"Narrative generation failed: {result.get('message', 'unknown error')}")
        return 1

    OUT_PATH.write_text(narrative.rstrip() + '\n')
    saved_narrative = OUT_PATH.read_text()
    print(saved_narrative)
    print('\nNumeric accuracy checklist:')
    if not check_numeric_accuracy(saved_narrative):
        return 1
    print(f"\nNarrative status: {result['status']}; tokens: {result['tokens']}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
