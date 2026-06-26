# config.py

# Mock mode switches
USE_MOCK_DATA = True
USE_MOCK_ALERTS = False
USE_MOCK_ENFORCE = False
# Team names
TEAMS = {
    "team-alpha": "Team Alpha",
    "team-beta": "Team Beta",
    "team-gamma": "Team Gamma",
}

# Monthly budgets
BUDGET_LIMITS = {
    "team-alpha": 100,
    "team-beta": 200,
    "team-gamma": 150,
}

SPIKE_THRESHOLD_PERCENT = 20 
# SNS Topic ARN
SNS_TOPIC_ARN = "arn:aws:sns:ap-south-1:114030601216:BudgetWatchdogAlertsV2"
# Restrictive IAM policy ARN
DENY_POLICY_ARN = "arn:aws:iam::114030601216:policy/BudgetWatchdog-SpendingLimitExceeded"

# IAM Groups
TEAM_IAM_GROUPS = {
    "team-alpha": "TeamAlphaGroup",
    "team-beta": "TeamBetaGroup",
    "team-gamma": "TeamGammaGroup",
}