# Deployment & Demo Guide

## When AI Becomes Your On-Call Engineer - Devnovate Mumbai

This guide covers end-to-end deployment, testing, and stage execution for both demos.

---

## Prerequisites

| Tool | Version | Install | Verify |
| --- | --- | --- | --- |
| AWS CLI | 2.x | `brew install awscli` | `aws --version` |
| eksctl | 0.227+ | `brew install eksctl` | `eksctl version` |
| kubectl | 1.32+ | `brew install kubectl` | `kubectl version --client` |
| helm | 4.0+ | `brew install helm` | `helm version` |
| Node.js | 18+ | `brew install node` | `node --version` |
| AWS CDK | 2.160+ | `npm install -g aws-cdk` | `cdk --version` |

### AWS Account Requirements

- An AWS account with admin access
- Bedrock model access enabled for `us.anthropic.claude-sonnet-4-20250514-v1:0` in `us-east-1`
- A DevOps Agent Space created in the AWS DevOps Agent console (us-east-1)

---

## Part 1: K8sGPT Demo

### 1.1 Deploy (run the night before - takes ~15-20 min)

```bash
cd ~/Desktop/DA_content/session/Devnovate\ Mumbai/demo/k8sgpt/
chmod +x setup.sh cleanup.sh
./setup.sh

```

This creates:

- EKS cluster `devnovate-demo` (2x m5.large nodes)
- IAM role `K8sGPTBedrockRole` with `bedrock:InvokeModel` permission
- Pod Identity association (zero API keys in cluster)
- K8sGPT Operator with auto-remediation enabled (Bedrock backend)
- Kyverno with `block-ai-remediation-critical` ClusterPolicy

### 1.2 Verify Deployment

```bash
# K8sGPT pods running
kubectl get pods -n k8sgpt-operator-system
# Expected: k8sgpt-operator-controller-manager-xxx  Running

# K8sGPT config applied
kubectl get k8sgpt -n k8sgpt-operator-system
# Expected: k8sgpt   30s

# Kyverno policy active
kubectl get clusterpolicy
# Expected: block-ai-remediation-critical   Enforce

```

### 1.3 Test: Auto-remediation works

```bash
# Deploy broken pod (demo namespace - AI allowed)
kubectl apply -f memory-hog.yaml

# Show that the pod is OOMKilling (wait ~10 seconds)
kubectl get pods -n demo -w
# Expected: memory-hog-xxx   OOMKilled / CrashLoopBackOff

# Show WHY it failed - memory limit too low
kubectl describe pod -n demo -l app=memory-hog | grep -A 5 "Last State"
# Expected: Reason: OOMKilled, Exit Code: 137

# Watch K8sGPT detect and fix it
kubectl get results -n k8sgpt-operator-system -w
# Wait 30-60 seconds. You should see a Result appear, then a Mutation.

# Read the AI-generated explanation (plain English root cause)
kubectl get results -n k8sgpt-operator-system -o yaml | grep -A 10 "details:"
# Expected: "The pod is OOMKilled because the memory limit (64Mi) is insufficient..."

# Check mutations - confirms auto-fix was generated and applied
kubectl get mutations -n k8sgpt-operator-system
# Expected: demomemoryhog  Successful  46%

# Verify the fix was applied
kubectl get deployment memory-hog -n demo -o jsonpath='{.spec.template.spec.containers[0].resources.limits.memory}'
# Expected: something > 64Mi (e.g., 256Mi)

# Verify pod is now running
kubectl get pods -n demo
# Expected: memory-hog-xxx   Running

```

### 1.4 Test: Kyverno blocks AI in critical namespace

```bash
# Deploy same broken pod in critical namespace
kubectl apply -f memory-hog-critical.yaml

# Wait 60-90 seconds for K8sGPT to detect and attempt auto-fix

# Show Kyverno blocked the AI mutation (check admission controller logs)
kubectl logs -n kyverno -l app.kubernetes.io/component=admission-controller --tail=5 | grep "blocking admission"
# Expected: blocking admission request ... policy=block-ai-remediation-critical resource=critical/Deployment/memory-hog

# Show mutations - critical ones stuck "In Progress" vs demo ones "Successful"
kubectl get mutations -n k8sgpt-operator-system
# Expected: criticalmemoryhog  In Progress  vs  demomemoryhog  Successful

# Pod keeps crashing because AI cannot fix it
kubectl get pods -n critical
# Expected: memory-hog-xxx   CrashLoopBackOff

```

### 1.5 Reset between rehearsals

```bash
kubectl delete namespace demo --ignore-not-found
kubectl delete namespace critical --ignore-not-found

```

---

## Part 2: DevOps Agent Demo (CDK)

### 2.1 Deploy (takes ~2 min)

```bash
cd ~/Desktop/DA_content/session/Devnovate\ Mumbai/demo/devops-agent/
chmod +x setup.sh cleanup.sh trigger-alarm.sh
./setup.sh

```

This creates:

- `devnovate-demo-error-generator` - Lambda that always throws errors
- `devnovate-demo-lambda-errors` - CloudWatch Alarm (>= 3 errors in 1 min)
- `devnovate-demo-alarms` - SNS Topic
- `devnovate-DevOpsAgent-Webhook` - Lambda that forwards alarm to DevOps Agent
- `devnovate-demo-webhook-credentials` - Secrets Manager secret (placeholder)

### 2.2 Configure Webhook Credentials (one-time)

1. Go to [AWS DevOps Agent Console](https://console.aws.amazon.com/devopsagent)
2. Open your Agent Space - **Capabilities** tab
3. Under **Webhook** - click **Generate webhook**
4. Choose **HMAC** authentication
5. Download the CSV (contains URL + secret)
6. Update the secret:

```bash
aws secretsmanager put-secret-value \
  --secret-id devnovate-demo-webhook-credentials \
  --secret-string '{"webhook_url": "https://YOUR_ACTUAL_URL", "webhook_secret": "YOUR_ACTUAL_SECRET"}' \
  --region us-east-1

```

### 2.3 Verify: Webhook connectivity

```bash
# Test the webhook Lambda directly with a fake alarm event
echo '{"Records":[{"Sns":{"Message":"{\"AlarmName\":\"TEST-verify\",\"AlarmDescription\":\"Webhook test\",\"NewStateValue\":\"ALARM\",\"NewStateReason\":\"Manual test\",\"Region\":\"us-east-1\"}"}}]}' > /tmp/test-event.json

aws lambda invoke \
  --function-name devnovate-DevOpsAgent-Webhook \
  --payload file:///tmp/test-event.json \
  --region us-east-1 \
  /tmp/webhook-test.json

cat /tmp/webhook-test.json
# Expected: {"statusCode": 200, "body": "...investigation triggered...webhookStatus: 200..."}

```

Then go to DevOps Agent web app - you should see a test investigation named `CloudWatch Alarm: TEST-verify` under the Incident tab.

### 2.4 Test: Full pipeline (error Lambda - alarm - webhook - investigation)

```bash
./trigger-alarm.sh

```

This invokes the error Lambda 5 times. Then:

1. Wait ~1-2 minutes for CloudWatch to evaluate the alarm
2. Check alarm state:```bash aws cloudwatch describe-alarms --alarm-names devnovate-demo-lambda-errors --query 'MetricAlarms[0].StateValue' --output text --region us-east-1

# Expected: ALARM

```
3. Check webhook Lambda logs:```bash
aws logs tail /aws/lambda/devnovate-DevOpsAgent-Webhook --follow --region us-east-1
# Expected: "DevOps Agent webhook response: 200"

```

1. Open DevOps Agent web app - new investigation should appear

### 2.5 Reset between rehearsals

```bash
aws cloudwatch set-alarm-state \
  --alarm-name devnovate-demo-lambda-errors \
  --state-value OK \
  --state-reason "Demo reset" \
  --region us-east-1

```

---

## Stage Demo Script (Day of Talk)

### Before going on stage

```bash
# Verify K8sGPT is still healthy
kubectl get pods -n k8sgpt-operator-system
kubectl get clusterpolicy

# Verify DevOps Agent alarm is in OK state
aws cloudwatch describe-alarms \
  --alarm-names devnovate-demo-lambda-errors \
  --query 'MetricAlarms[0].StateValue' --output text --region us-east-1

# Clean any leftover namespaces from rehearsals
kubectl delete namespace demo --ignore-not-found
kubectl delete namespace critical --ignore-not-found

```

### During the talk - Part 1 (K8sGPT)

```bash
# Step 1: Deploy broken pod
kubectl apply -f memory-hog.yaml

# Step 1b: Show OOMKill (narrate: "64Mi limit but app needs 128Mi")
kubectl get pods -n demo -w
kubectl describe pod -n demo -l app=memory-hog | grep -A 5 "Last State"

# Step 2: Watch K8sGPT detect + fix (narrate while waiting)
kubectl get results -n k8sgpt-operator-system -w

# Step 2b: Show the AI explanation (what K8sGPT told Bedrock and got back)
kubectl get results -n k8sgpt-operator-system -o yaml | grep -A 10 "details:"
# Narrate: "K8sGPT is explaining in plain English why this pod failed"

# Step 3: Show auto-fix proof
kubectl get mutations -n k8sgpt-operator-system
kubectl get deployment memory-hog -n demo -o jsonpath='{.spec.template.spec.containers[0].resources.limits.memory}'

# Step 4: Now deploy in critical namespace
kubectl apply -f memory-hog-critical.yaml

# Step 5: Wait 60-90s, then show Kyverno blocking it
kubectl get mutations -n k8sgpt-operator-system
# Point out: demo = Successful, critical = In Progress (blocked!)

# Step 6: Show the actual block
kubectl logs -n kyverno -l app.kubernetes.io/component=admission-controller --tail=5 | grep "blocking admission"

```

### During the talk - Part 2 (DevOps Agent)

```bash
# Step 1: Trigger errors
./trigger-alarm.sh

# Step 2: Switch to browser - DevOps Agent web app
# Wait for investigation to appear (~1-2 min)
# Narrate: "The agent is now correlating Lambda error logs,
#           checking for recent deployments, and building root cause..."

# Step 3: Show the investigation result
# - Root cause identified
# - Mitigation plan generated

```

---

## Cleanup (After the event)

```bash
# Part 1: K8sGPT (takes ~10 min)
cd ~/Desktop/DA_content/session/Devnovate\ Mumbai/demo/k8sgpt/
./cleanup.sh

# Part 2: DevOps Agent (takes ~2 min)
cd ~/Desktop/DA_content/session/Devnovate\ Mumbai/demo/devops-agent/
./cleanup.sh

```

---

## Troubleshooting

### K8sGPT not detecting issues

```bash
# Check operator logs
kubectl logs -n k8sgpt-operator-system -l app.kubernetes.io/name=k8sgpt-operator -f

# Verify Bedrock connectivity
kubectl logs -n k8sgpt-operator-system -l app=k8sgpt -f
# Look for "backend" errors or "access denied"

# Verify Pod Identity is working
kubectl describe sa k8sgpt-sa -n k8sgpt-operator-system

```

### Alarm not firing

```bash
# Check if errors are being recorded
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value=devnovate-demo-error-generator \
  --start-time $(date -u -v-5M +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 --statistics Sum --region us-east-1

```

### Webhook Lambda failing

```bash
# Check logs
aws logs tail /aws/lambda/devnovate-DevOpsAgent-Webhook --since 5m --region us-east-1

# Common issues:
# - "AccessDeniedException" -> secret name mismatch, check WEBHOOK_SECRET_NAME env var
# - "HTTP 401/403" -> webhook credentials wrong, re-run put-secret-value
# - "HTTP 404" -> webhook URL wrong or webhook was deleted in console

```

### DevOps Agent not starting investigation

- Confirm webhook is configured in Agent Space (Capabilities tab)
- Confirm the Agent Space has your AWS account associated
- Check that the investigation wasn't auto-skipped (Skills tab - skip criteria)

---

## Timeline Recommendation

| When | Action |
| --- | --- |
| Night before | Deploy K8sGPT (`./setup.sh`) - EKS takes 15-20 min |
| Night before | Deploy DevOps Agent CDK (`./setup.sh`) - 2 min |
| Night before | Configure webhook credentials |
| Night before | Run full test of both demos |
| 30 min before talk | Verify everything is healthy |
| 10 min before talk | Reset namespaces + alarm state |
| On stage | Execute demo script above |
| After event | Run both cleanup scripts |

