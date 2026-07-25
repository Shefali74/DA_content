#!/bin/bash
set -euo pipefail

echo "=== Devnovate Mumbai Demo: DevOps Agent Pipeline (CDK) ==="
echo ""

REGION="us-east-1"

cd "$(dirname "$0")/cdk"

# 1. Install dependencies
echo "[1/3] Installing CDK dependencies..."
npm install

# 2. Bootstrap CDK (skip if already done)
echo "[2/3] Bootstrapping CDK environment..."
cdk bootstrap aws://$(aws sts get-caller-identity --query Account --output text)/$REGION 2>/dev/null || true

# 3. Deploy
echo "[3/3] Deploying stack..."
npx cdk deploy DevnovateDevOpsAgentDemo --require-approval never

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "NEXT STEPS:"
echo ""
echo "  1. Create DevOps Agent Space (if not already done):"
echo "     https://console.aws.amazon.com/devopsagent"
echo ""
echo "  2. Generate webhook credentials:"
echo "     Agent Space -> Capabilities tab -> Webhook -> Generate (HMAC)"
echo ""
echo "  3. Update the secret with your credentials:"
echo "     aws secretsmanager put-secret-value \\"
echo "       --secret-id devnovate-demo-webhook-credentials \\"
echo "       --secret-string '{\"webhook_url\": \"YOUR_URL\", \"webhook_secret\": \"YOUR_SECRET\"}' \\"
echo "       --region $REGION"
echo ""
echo "  4. Verify webhook connectivity:"
echo "     echo '{\"Records\":[{\"Sns\":{\"Message\":\"{\\\"AlarmName\\\":\\\"TEST-verify\\\",\\\"AlarmDescription\\\":\\\"Test\\\",\\\"NewStateValue\\\":\\\"ALARM\\\",\\\"NewStateReason\\\":\\\"Manual test\\\",\\\"Region\\\":\\\"us-east-1\\\"}\"}}]}' > /tmp/test-event.json"
echo ""
echo "     aws lambda invoke \\"
echo "       --function-name devnovate-DevOpsAgent-Webhook \\"
echo "       --payload file:///tmp/test-event.json \\"
echo "       --region $REGION \\"
echo "       /tmp/webhook-test.json && cat /tmp/webhook-test.json"
echo ""
echo "  5. Run the demo:"
echo "     ../trigger-alarm.sh"
