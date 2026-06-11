import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import boto3
from datetime import datetime
from config import TEAMS, BUDGET_LIMITS, USE_MOCK_DATA


def get_date_range():
    today = datetime.today()
    start = today.replace(day=1).strftime("%Y-%m-%d")
    end   = today.strftime("%Y-%m-%d")
    return start, end


def get_mock_costs():
    """
    Fake cost data that simulates real AWS spending.
    team-beta and team-gamma are over their limits on purpose
    so we can test the alert system later.
    """
    return [
        {"team": "team-alpha", "cost": 72.40,  "currency": "USD", "limit": 100, "exceeded": False},
        {"team": "team-beta",  "cost": 243.10, "currency": "USD", "limit": 200, "exceeded": True},
        {"team": "team-gamma", "cost": 167.80, "currency": "USD", "limit": 150, "exceeded": True},
    ]


def fetch_costs():
    if USE_MOCK_DATA:
        print("Running in MOCK mode (no real AWS data)\n")
        results = get_mock_costs()
    else:
        client = boto3.client("ce", region_name="us-east-1")
        start, end = get_date_range()

        response = client.get_cost_and_usage(
            TimePeriod={"Start": start, "End": end},
            Granularity="MONTHLY",
            Metrics=["UnblendedCost"],
            GroupBy=[{"Type": "TAG", "Key": "Team"}],
        )

        results = []
        for group in response["ResultsByTime"][0]["Groups"]:
            tag_value = group["Keys"][0].replace("Team$", "")
            cost      = float(group["Metrics"]["UnblendedCost"]["Amount"])
            currency  = group["Metrics"]["UnblendedCost"]["Unit"]
            limit     = BUDGET_LIMITS.get(tag_value, 999)
            exceeded  = cost > limit

            results.append({
                "team":     tag_value,
                "cost":     round(cost, 2),
                "currency": currency,
                "limit":    limit,
                "exceeded": exceeded,
            })

    # Print results
    for r in results:
        status = "🚨 EXCEEDED" if r["exceeded"] else "✅ OK"
        print(f"{TEAMS.get(r['team'], r['team'])}: ${r['cost']} / ${r['limit']} {status}")

    return results


if __name__ == "__main__":
    print("🐶 BudgetWatchdog — Fetching AWS costs...\n")
    fetch_costs()