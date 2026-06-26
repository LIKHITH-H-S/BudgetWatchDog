# detect_anomaly.py
# Takes cost data and figures out WHO is in trouble and HOW BAD it is
from config import SPIKE_THRESHOLD_PERCENT
# ── CONFIGURATION ──────────────────────────────────────────
# If cost spikes by more than this % compared to last month → anomaly
  # 20% sudden increase = suspicious

# Severity levels
SEVERITY_WARNING  = "WARNING"   # close to limit or small spike
SEVERITY_CRITICAL = "CRITICAL"  # over limit or huge spike
# ───────────────────────────────────────────────────────────


# Mock "last month's costs" so we can simulate spikes
# In real life this would also come from Cost Explorer
PREVIOUS_CHECK_COSTS = {
    "team-alpha": 68.00,
    "team-beta":  190.00,
    "team-gamma": 80.00,   # team-gamma doubled! big spike
}


def detect_anomalies(cost_results):
    """
    Goes through each team's cost and checks two things:
    1. Are they over their budget limit?
    2. Did their cost spike suddenly vs last month?
    Returns a list of anomalies found.
    """
    anomalies = []

    for team_data in cost_results:
        team    = team_data["team"]
        cost    = team_data["cost"]
        limit   = team_data["limit"]
        exceeded = team_data["exceeded"]

        previous_cost = PREVIOUS_CHECK_COSTS.get(team, cost)

        # ── CHECK 1: Over budget limit? ──────────────────
        if exceeded:
            overage_pct = ((cost - limit) / limit) * 100
            severity    = SEVERITY_CRITICAL if overage_pct > 20 else SEVERITY_WARNING

            anomalies.append({
                "team":     team,
                "type":     "OVER_BUDGET",
                "severity": severity,
                "message":  f"${cost} spent, limit is ${limit} ({overage_pct:.1f}% over)",
                "cost":     cost,
                "limit":    limit,
            })

        # ── CHECK 2: Sudden spike vs last month? ─────────
        if previous_cost > 0:
            spike_pct = ((cost - previous_cost) / previous_cost) * 100

            if spike_pct > SPIKE_THRESHOLD_PERCENT:
                severity = SEVERITY_CRITICAL if spike_pct > 50 else SEVERITY_WARNING

                anomalies.append({
                    "team":     team,
                    "type":     "SPIKE_DETECTED",
                    "severity": severity,
                    "message":  f"Cost increased {spike_pct:.1f}% since the previous monitoring cycle (${previous_cost} → ${cost})",
                    "cost":     cost,
                    "limit":    limit,
                })

    return anomalies


def print_anomalies(anomalies):
    if not anomalies:
        print("✅ No anomalies detected. All teams within budget!")
        return

    print(f"🔍 Found {len(anomalies)} anomaly(s):\n")
    for a in anomalies:
        icon = "🚨" if a["severity"] == "CRITICAL" else "⚠️ "
        print(f"  {icon} [{a['severity']}] {a['team'].upper()} — {a['type']}")
        print(f"      {a['message']}\n")


if __name__ == "__main__":
    # Import fetch_costs so we can use its data
    from fetch_costs import fetch_costs

    print("🐶 BudgetWatchdog — Detecting anomalies...\n")
    cost_data = fetch_costs()
    print()

    anomalies = detect_anomalies(cost_data)
    print_anomalies(anomalies)