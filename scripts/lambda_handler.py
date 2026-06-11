# lambda_handler.py
# This is the entry point for AWS Lambda.
# Lambda calls the handler() function every hour via EventBridge.
# It ties all 4 scripts together in the correct order.

import json
from datetime import datetime

from fetch_costs    import fetch_costs
from detect_anomaly import detect_anomalies, print_anomalies
from send_alert     import send_alert
from enforce_limit  import enforce_limit


def handler(event, context):
    """
    AWS Lambda calls this function automatically.
    'event'   → data passed in by EventBridge (we don't use it here)
    'context' → Lambda runtime info (memory, timeout etc.)
    Both are required by Lambda even if unused — don't remove them.
    """

    print("=" * 50)
    print(f"🐶 BudgetWatchdog started at {datetime.now()}")
    print("=" * 50)

    # ── STEP 1: Fetch costs ──────────────────────────
    print("\n📊 STEP 1: Fetching AWS costs...\n")
    try:
        cost_data = fetch_costs()
    except Exception as e:
        print(f"❌ Failed to fetch costs: {e}")
        return build_response(500, "Failed at cost fetching")

    # ── STEP 2: Detect anomalies ─────────────────────
    print("\n🔍 STEP 2: Detecting anomalies...\n")
    try:
        anomalies = detect_anomalies(cost_data)
        print_anomalies(anomalies)
    except Exception as e:
        print(f"❌ Failed to detect anomalies: {e}")
        return build_response(500, "Failed at anomaly detection")

    # ── STEP 3: Send alerts ──────────────────────────
    print("\n📧 STEP 3: Sending alerts...\n")
    try:
        send_alert(anomalies)
    except Exception as e:
        print(f"❌ Failed to send alerts: {e}")
        return build_response(500, "Failed at alert sending")

    # ── STEP 4: Enforce limits ───────────────────────
    print("\n🔒 STEP 4: Enforcing limits...\n")
    try:
        enforce_limit(anomalies)
    except Exception as e:
        print(f"❌ Failed to enforce limits: {e}")
        return build_response(500, "Failed at enforcement")

    # ── DONE ─────────────────────────────────────────
    summary = {
        "teams_checked":    len(cost_data),
        "anomalies_found":  len(anomalies),
        "critical_count":   len([a for a in anomalies if a["severity"] == "CRITICAL"]),
        "warning_count":    len([a for a in anomalies if a["severity"] == "WARNING"]),
        "timestamp":        str(datetime.now()),
    }

    print("\n" + "=" * 50)
    print("✅ BudgetWatchdog run complete!")
    print(f"   Teams checked  : {summary['teams_checked']}")
    print(f"   Anomalies found: {summary['anomalies_found']}")
    print(f"   Critical       : {summary['critical_count']}")
    print(f"   Warnings       : {summary['warning_count']}")
    print("=" * 50)

    return build_response(200, "BudgetWatchdog completed successfully", summary)


def build_response(status_code, message, data=None):
    """
    Builds a standard response object.
    Lambda functions always return a response like this.
    """
    body = {"message": message}
    if data:
        body["summary"] = data

    return {
        "statusCode": status_code,
        "body": json.dumps(body, indent=2),
    }


# ── LOCAL TESTING ─────────────────────────────────
# When running locally (not on Lambda), simulate a Lambda call
if __name__ == "__main__":
    # Simulate what EventBridge sends to Lambda
    mock_event   = {"source": "aws.events", "detail-type": "Scheduled Event"}
    mock_context = {}   # empty — we don't use context locally

    result = handler(mock_event, mock_context)

    print("\n📦 Lambda response:")
    print(result["body"])