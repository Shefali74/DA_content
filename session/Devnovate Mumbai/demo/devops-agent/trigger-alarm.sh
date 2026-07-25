#!/bin/bash
set -euo pipefail

FUNCTION_NAME="devnovate-demo-error-generator"
REGION="us-east-1"

echo "=== Triggering DevOps Agent Demo ==="
echo ""
echo "Invoking error Lambda 5 times to trip the CloudWatch Alarm..."
echo ""

for i in $(seq 1 5); do
  echo "  [$i/5] Invoking $FUNCTION_NAME..."
  aws lambda invoke \
    --function-name "$FUNCTION_NAME" \
    --region "$REGION" \
    --invocation-type RequestResponse \
    /tmp/lambda-response.json 2>/dev/null || true
  sleep 1
done

echo ""
echo "Done. Errors generated."
echo ""
echo "What happens next:"
echo "  1. CloudWatch detects >= 3 errors in 1 minute"
echo "  2. Alarm 'devnovate-demo-lambda-errors' transitions to ALARM"
echo "  3. SNS notifies webhook Lambda"
echo "  4. Webhook Lambda calls DevOps Agent API (HMAC signed)"
echo "  5. DevOps Agent starts autonomous investigation"
echo ""
echo "Check:"
echo "  - Alarm state: aws cloudwatch describe-alarms --alarm-names devnovate-demo-lambda-errors --query 'MetricAlarms[0].StateValue' --region $REGION"
echo "  - Lambda logs: aws logs tail /aws/lambda/devnovate-DevOpsAgent-Webhook --follow --region $REGION"
echo "  - DevOps Agent web app: look for new investigation"
echo ""
echo "To reset after demo:"
echo "  aws cloudwatch set-alarm-state --alarm-name devnovate-demo-lambda-errors --state-value OK --state-reason 'Demo reset' --region $REGION"
