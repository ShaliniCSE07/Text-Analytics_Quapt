import json
import os

# Path to the JSON config file (relative to project root when running uvicorn)
_JSON_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "topics_config.json")

# Hardcoded fallback (used if JSON file is missing on first run)
_FALLBACK_TOPICS = {
  "Claims - Settlement Speed": "claim settlement time, claim turnaround time, days taken to settle claim, claim approved quickly, payout speed",
  "Claims - Rejection and Disputes": "claim rejected, claim repudiation, claim denied unfairly, repudiated claim, dispute claim decision",
  "Claims - Documentation": "claim paperwork burden, discharge summary, FIR copy submission, repeated document requests, claim form paperwork",
  "Claims - Intimation and Tracking": "claim intimation number, register claim, claim status tracking, claim reference update, intimation process",
  "Claims - Cashless and Network Providers": "cashless hospitalization, network hospital TPA, cashless garage repair, cashless admission denied, pre-authorization",
  "Claims - Reimbursement": "reimbursement claim settlement, medical bills reimbursement, hospital expense reimbursement, reimbursement payout delay",
  "Claims - Surveyor and Damage Assessment": "surveyor vehicle inspection, damage assessment report, surveyor depreciation deduction, vehicle repair estimate, garage bill",
  "Onboarding - Digital Purchase and KYC": "buying policy online, e-KYC verification, CKYC document upload, policy issuance time, online purchase process",
  "Onboarding - Underwriting and Medical Tests": "pre-policy medical examination, health declaration underwriting checkup, medical checkup test, underwriting decision",
  "Onboarding - Mis-selling and Transparency": "misleading sales pitch, hidden policy exclusions, mis-sold policy by agent, agent promised false terms, fine print",
  "Onboarding - Quotes and Plan Selection": "comparing premium quotes, choosing sum insured, comparing policy plans, add-on plan selection, IDV selection",
  "Premium - Affordability and Value": "expensive policy premium, affordable premium cover, cheaper than competitors, premium too high, premium cost",
  "Premium - Renewal Hike": "premium increased at renewal, renewal price hike, NCB lost on renewal, steep renewal cost jump, renewal loading",
  "Premium - Payment and Auto-debit": "payment gateway failed, UPI payment error, auto-debit NACH mandate, double premium deduction, payment gateway issue",
  "Premium - Refunds and Cancellation": "cancelling policy, policy cancellation refund, free look cancellation, surrender policy charges, cancel policy request",
  "Servicing - Policy Renewal": "renew policy online, renewal reminder process, policy lapsed grace period, renewal continuity benefit",
  "Servicing - Endorsements and Changes": "policy endorsement request, nominee update, change of address, vehicle details endorsement",
  "Servicing - Policy Documents": "download policy document, e-policy certificate, tax certificate, policy copy not received, document download",
  "Service - Agent and Advisor Conduct": "agent behaviour, rude advisor conduct, helpful agent courtesy, relationship manager courtesy",
  "Service - Call Centre and Support": "customer care helpline, kept on hold, call transferred, call centre support response, helpline assistance",
  "Service - Grievance and Escalation": "grievance officer complaint, insurance ombudsman, IRDAI portal complaint, escalation ticket reopened",
  "Service - Branch Experience": "branch office visit, branch staff assistance, counter waiting time, in-person service at branch",
  "Digital - App and Login": "mobile app crash, app login OTP issue, app glitch bug, mobile app interface",
  "Digital - Website and Portal": "customer portal slow, website portal login, portal document upload error, view policy portal",
  "Digital - Notifications and Communication": "promotional spam calls, SMS alerts bombardment, promotional messages, unwanted WhatsApp spam",
  "Coverage - Clarity and Exclusions": "room rent limit, co-payment clause, policy exclusions terms, sub-limits coverage confusion, treatment not covered",
  "Coverage - Waiting Periods and Pre-existing": "pre-existing disease waiting period, initial waiting period clause, waiting period for illness",
  "Coverage - Benefits and Add-ons": "zero depreciation cover, roadside assistance cover, maternity cover rider, critical illness add-on benefit, wellness benefits",
  "Life - Maturity and Surrender": "maturity benefit returns, surrender value payout, life insurance death claim, annuity pension payout",
  "Travel - Trip Disruption and Assistance": "flight delay compensation, trip cancellation claim, baggage loss abroad, travel emergency assistance, overseas medical cover",
  "Home - Property Damage and Repairs": "home insurance property damage, house fire damage repair claim, flood damage residential claim, property theft claim"
}

# Keep TOPICS as module-level constant for any legacy imports
TOPICS = _FALLBACK_TOPICS.copy()


def load_topics() -> dict:
    """Read topics from data/topics_config.json.

    If the file is missing, falls back to the hardcoded dict and
    immediately creates the JSON file from it so future reads succeed.
    """
    path = os.path.normpath(_JSON_PATH)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        # File missing — seed it from the fallback and return fallback
        save_topics(_FALLBACK_TOPICS)
        return _FALLBACK_TOPICS.copy()
    except json.JSONDecodeError:
        # Corrupt file — return fallback without overwriting
        return _FALLBACK_TOPICS.copy()


def save_topics(topics_dict: dict) -> None:
    """Write the given topics dict to data/topics_config.json."""
    path = os.path.normpath(_JSON_PATH)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(topics_dict, f, indent=2, ensure_ascii=False)
