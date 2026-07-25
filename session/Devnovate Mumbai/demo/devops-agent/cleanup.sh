#!/bin/bash
set -euo pipefail

echo "=== Cleanup: DevOps Agent Demo (CDK) ==="
echo ""

REGION="us-east-1"

# Reset alarm
echo "[1/2] Resetting CloudWatch Alarm..."
aws cloudwatch set-alarm-state \
  --alarm-name devnovate-demo-lambda-errors \
  --state-value OK \
  --state-reason "Demo cleanup" \
  --region "$REGION" 2>/dev/null || echo "  (alarm may already be deleted)"

# Destroy CDK stack
echo "[2/2] Destroying CDK stack..."
cd "$(dirname "$0")/cdk"
npx cdk destroy DevnovateDevOpsAgentDemo --force

echo ""
echo "=== DevOps Agent demo resources cleaned up ==="
