# BudgetWatchdog

> Automatically detects AWS cost anomalies and enforces spending limits per team — built as a serverless Python tool running on AWS Lambda.

---

## What It Does

BudgetWatchdog is a cloud cost governance tool that:

- **Fetches** real-time AWS spending per team using Cost Explorer API
- **Detects** anomalies — budget overruns and sudden cost spikes
- **Alerts** Uses AWS SNS to send real email alerts for cost anomalies
- **Enforces** limits automatically by restricting IAM access for offending teams
- **Runs automatically** every hour via AWS EventBridge — zero manual effort

---

## Architecture

Architecture

EventBridge
     ↓
AWS Lambda
     ↓
BudgetWatchDog
     ↓
Amazon SNS
     ↓
Email Alert