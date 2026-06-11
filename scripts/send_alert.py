# send_alert.py
# Sends email/SMS alerts via AWS SNS when anomalies are detected
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import boto3
from botocore.exceptions import ClientError
from config import SNS_TOPIC_ARN, USE_MOCK_ALERTS


def build_alert_message(anomalies):
    """
    Takes the list of anomalies and builds a clean
    email message from them.
    """
    if not anomalies:
        return None

    lines = []
    lines.append("🐶 BudgetWatchdog Alert Report")
    lines.append("=" * 40)
    lines.append(f"Total anomalies found: {len(anomalies)}\n")

    for a in anomalies:
        icon = "🚨 CRITICAL" if a["severity"] == "CRITICAL" else "⚠️  WARNING"
        lines.append(f"{icon} | {a['team'].upper()} | {a['type']}")
        lines.append(f"  → {a['message']}")
        lines.append("")

    lines.append("=" * 40)
    lines.append("Action required: Review AWS Cost Explorer immediately.")
    lines.append("https://console.aws.amazon.com/cost-management/home")

    return "\n".join(lines)


def send_alert(anomalies):
    """
    Sends the alert message to the SNS topic.
    SNS then forwards it to all subscribed emails/phones.
    """
    if not anomalies:
        print("✅ No anomalies — no alert needed.")
        return

    message = build_alert_message(anomalies)

    if USE_MOCK_ALERTS:
        print("⚠️  Running in MOCK mode — not sending real SNS alert\n")
        print("📧 Alert message that WOULD be sent:\n")
        print("-" * 40)
        print(message)
        print("-" * 40)
        return

    # Real SNS send
    try:
        client = boto3.client("sns", region_name="us-east-1")

        response = client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject="🚨 BudgetWatchdog Alert — AWS Cost Anomaly Detected",
            Message=message,
        )

        print(f"✅ Alert sent! Message ID: {response['MessageId']}")

    except ClientError as e:
        print(f"❌ Failed to send alert: {e}")


if __name__ == "__main__":
    from fetch_costs import fetch_costs
    from detect_anomaly import detect_anomalies

    print("🐶 BudgetWatchdog — Sending alerts...\n")

    cost_data = fetch_costs()
    print()

    anomalies = detect_anomalies(cost_data)
    send_alert(anomalies)