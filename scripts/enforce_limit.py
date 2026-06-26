# enforce_limit.py
# Automatically restricts AWS access for teams that exceed their budget
# Does this by attaching a DENY policy to the team's IAM group
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import boto3
import json
from botocore.exceptions import ClientError
from config import (
    TEAM_IAM_GROUPS,
    USE_MOCK_ENFORCE,
    DENY_POLICY_ARN
)

# Name of the policy we attach to restrict a team
DENY_POLICY_NAME = "BudgetWatchdog-SpendingLimitExceeded"



def build_deny_policy():
    """
    Builds an IAM policy that DENIES creating new
    expensive AWS resources (EC2, RDS, Lambda etc.)
    The team can still READ and VIEW — just can't create more.
    """
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "BudgetWatchdogDeny",
                "Effect": "Deny",
                "Action": [
                    "ec2:RunInstances",
                    "rds:CreateDBInstance",
                    "lambda:CreateFunction",
                    "s3:CreateBucket",
                    "ecs:CreateCluster",
                    "eks:CreateCluster",
                ],
                "Resource": "*",
                "Condition": {
                    "StringEquals": {
                        "aws:RequestedRegion": "us-east-1"
                    }
                }
            }
        ]
    }
    return json.dumps(policy, indent=2)


def manage_team_access(cost_data, anomalies):
    """
    Automatically manages IAM access.

    CRITICAL team  -> Attach deny policy
    Normal team    -> Remove deny policy
    """

    # Build a set of teams that currently have a CRITICAL anomaly
    critical_teams = {
        anomaly["team"]
        for anomaly in anomalies
        if anomaly["severity"] == "CRITICAL"
    }

    print("\n🔒 Managing team access...\n")

    for team_info in cost_data:

        team = team_info["team"]
        iam_group = TEAM_IAM_GROUPS.get(team)

        if not iam_group:
            print(f"⚠️ No IAM group mapped for {team}")
            continue

        # ---------------- MOCK MODE ----------------
        if USE_MOCK_ENFORCE:

            if team in critical_teams:
                print(f"MOCK: Would restrict {iam_group}")
            else:
                print(f"MOCK: Would restore {iam_group}")

            continue

        # ---------------- REAL MODE ----------------
        if team in critical_teams:

            try:
                iam = boto3.client("iam")

                attached = iam.list_attached_group_policies(
                    GroupName=iam_group
                )

                already_attached = any(
                    policy["PolicyArn"] == DENY_POLICY_ARN
                    for policy in attached["AttachedPolicies"]
                )

                if already_attached:
                    print(f"ℹ️ {iam_group} already restricted.")
                else:
                    iam.attach_group_policy(
                        GroupName=iam_group,
                        PolicyArn=DENY_POLICY_ARN,
                    )
                    print(f"🔒 Restricted {iam_group}")

            except ClientError as e:
                print(f"❌ Failed to restrict {team}: {e}")

        else:

            release_limit(team)


def release_limit(team):
    """
    Call this when a team's budget issue is resolved.
    Removes the deny policy — restores full access.
    """
    iam_group = TEAM_IAM_GROUPS.get(team)

    if not iam_group:
        print(f"❌ No IAM group found for {team}")
        return

    try:
        iam       = boto3.client("iam")
        policy_arn = DENY_POLICY_ARN

        attached = iam.list_attached_group_policies(
            GroupName=iam_group
        )

        already_attached = any(
            policy["PolicyArn"] == policy_arn
            for policy in attached["AttachedPolicies"]
        )

        if already_attached:
            iam.detach_group_policy(
                GroupName=iam_group,
                PolicyArn=policy_arn,
            )
            print(f"✅ Released restrictions for {iam_group}")
        else:
            print(f"ℹ️  {iam_group} is already unrestricted.")

    except ClientError as e:
        print(f"❌ Failed to release {team}: {e}")


if __name__ == "__main__":
    from fetch_costs import fetch_costs
    from detect_anomaly import detect_anomalies

    print("🐶 BudgetWatchdog — Enforcing limits...\n")

    cost_data = fetch_costs()
    print()

    anomalies  = detect_anomalies(cost_data)
    print()

    manage_team_access(cost_data, anomalies)