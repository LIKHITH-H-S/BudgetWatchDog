# config.py

# Mock mode switches
USE_MOCK_DATA = True
USE_MOCK_ALERTS = True
USE_MOCK_ENFORCE = True

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

# SNS Topic ARN
SNS_TOPIC_ARN = "arn:aws:sns:us-east-1:114030601216:BudgetWatchdogAlerts"

# IAM Groups
TEAM_IAM_GROUPS = {
    "team-alpha": "TeamAlphaGroup",
    "team-beta": "TeamBetaGroup",
    "team-gamma": "TeamGammaGroup",
}