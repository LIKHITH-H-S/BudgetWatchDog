# enforce_limit.py
# Automatically restricts AWS access for teams that exceed their budget
# Does this by attaching a DENY policy to the team's IAM group
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import boto3
import json
from botocore.exceptions import ClientError
from config import TEAM_IAM_GROUPS, USE_MOCK_ENFORCE

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


def enforce_limit(anomalies):
    """
    For every CRITICAL anomaly, attaches the deny policy
    to that team's IAM group — blocking new resource creation.
    """
    # Only enforce on CRITICAL anomalies, not warnings
    critical = [a for a in anomalies if a["severity"] == "CRITICAL"]

    if not critical:
        print("✅ No critical anomalies — no enforcement needed.")
        return

    print(f"🔒 Enforcing limits for {len(critical)} critical team(s)...\n")

    for anomaly in critical:
        team      = anomaly["team"]
        iam_group = TEAM_IAM_GROUPS.get(team)

        if not iam_group:
            print(f"  ⚠️  No IAM group mapped for {team} — skipping")
            continue

        if USE_MOCK_ENFORCE:
            print(f"  ⚠️  MOCK MODE — would restrict: {iam_group}")
            print(f"      Reason: {anomaly['message']}")
            print(f"      Action: Attach '{DENY_POLICY_NAME}' policy to {iam_group}")
            print(f"      Effect: Team cannot create new EC2, RDS, Lambda, S3\n")
            continue

        # Real IAM enforcement
        try:
            iam = boto3.client("iam")

            # Step 1: Create the deny policy (or get existing)
            try:
                policy_response = iam.create_policy(
                    PolicyName=DENY_POLICY_NAME,
                    PolicyDocument=build_deny_policy(),
                    Description="BudgetWatchdog auto-enforcement policy",
                )
                policy_arn = policy_response["Policy"]["Arn"]
                print(f"  ✅ Created policy: {policy_arn}")

            except ClientError as e:
                if e.response["Error"]["Code"] == "EntityAlreadyExists":
                    # Policy already exists — get its ARN
                    account_id = boto3.client("sts").get_caller_identity()["Account"]
                    policy_arn = f"arn:aws:iam::{account_id}:policy/{DENY_POLICY_NAME}"
                    print(f"  ℹ️  Policy already exists: {policy_arn}")
                else:
                    raise

            # Step 2: Attach the policy to the team's IAM group
            iam.attach_group_policy(
                GroupName=iam_group,
                PolicyArn=policy_arn,
            )
            print(f"  🔒 ENFORCED: {iam_group} is now restricted")
            print(f"      Reason: {anomaly['message']}\n")

        except ClientError as e:
            print(f"  ❌ Failed to enforce {team}: {e}\n")


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
        account_id = boto3.client("sts").get_caller_identity()["Account"]
        policy_arn = f"arn:aws:iam::{account_id}:policy/{DENY_POLICY_NAME}"

        iam.detach_group_policy(
            GroupName=iam_group,
            PolicyArn=policy_arn,
        )
        print(f"✅ Released restrictions for {iam_group}")

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

    enforce_limit(anomalies)