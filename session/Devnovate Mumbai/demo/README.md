# Demo: When AI Becomes Your On-Call Engineer

Devnovate AWS Mumbai Meetup

## Structure

```
demo/
├── k8sgpt/                    # Part 1: K8sGPT Self-Healing on EKS
│   ├── cluster.yaml                 eksctl cluster config
│   ├── k8sgpt-config.yaml           K8sGPT operator + Bedrock + auto-remediation
│   ├── memory-hog.yaml              Broken pod (demo ns - AI fixes it)
│   ├── memory-hog-critical.yaml     Broken pod (critical ns - Kyverno blocks)
│   ├── kyverno-policy.yaml          ClusterPolicy blocking AI in critical
│   ├── setup.sh                     One-command setup
│   └── cleanup.sh                   Tear everything down
│
├── devops-agent/              # Part 2: AWS DevOps Agent (CDK)
│   ├── cdk/                         CDK TypeScript project
│   │   ├── bin/app.ts
│   │   ├── lib/devops-agent-demo-stack.ts
│   │   ├── lambda/index.py          Lambda: alarm -> webhook (HMAC)
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   └── cdk.json
│   ├── trigger-alarm.sh             Manually fire alarm for stage demo
│   ├── setup.sh                     npm install + cdk deploy
│   └── cleanup.sh                   cdk destroy + cleanup
│
└── README.md                  # This file
```

## Prerequisites

| Tool       | Version | Install                    |
|------------|---------|----------------------------|
| eksctl     | 0.227+  | `brew install eksctl`      |
| kubectl    | 1.32+   | `brew install kubectl`     |
| helm       | 4.0+    | `brew install helm`        |
| AWS CLI    | 2.x     | `brew install awscli`      |
| Node.js    | 18+     | `brew install node`        |
| AWS CDK    | 2.160+  | `npm install -g aws-cdk`   |

## Demo Flow (45 min talk)

### Part 1: K8sGPT (~15 min demo)

```bash
cd k8sgpt/
./setup.sh                                # EKS cluster + K8sGPT + Kyverno

# Demo Step 1: Deploy broken pod
kubectl apply -f memory-hog.yaml
kubectl get results -n k8sgpt-operator-system -w   # Watch K8sGPT detect + auto-fix

# Demo Step 2: Same pod in critical namespace
kubectl apply -f memory-hog-critical.yaml
kubectl get events -n critical --field-selector reason=PolicyViolation

# Cleanup after talk
./cleanup.sh
```

### Part 2: AWS DevOps Agent (~10 min demo)

```bash
cd devops-agent/
./setup.sh                                # CDK deploy

# One-time: update secret with your webhook credentials
aws secretsmanager put-secret-value \
  --secret-id devnovate-demo-webhook-credentials \
  --secret-string '{"webhook_url": "YOUR_URL", "webhook_secret": "YOUR_SECRET"}' \
  --region us-east-1

# Demo: trigger the alarm
./trigger-alarm.sh
# Open DevOps Agent web app -> watch investigation appear

# Cleanup after talk
./cleanup.sh
```

## Architecture

### Part 1: K8sGPT

```
EKS Cluster (us-east-1)
├── K8sGPT Operator -> Amazon Bedrock (Claude) -> auto-fix
├── Kyverno -> blocks AI mutations in critical namespaces
├── demo namespace -> AI can fix
└── critical namespace -> AI blocked
```

### Part 2: DevOps Agent

```
CloudWatch Alarm -> SNS Topic -> Lambda -> DevOps Agent Webhook (HMAC)
                                              |
                                              v
                                 Autonomous Investigation
                                 Root Cause Analysis
                                 Mitigation Plan
```

## References

- [AWS DevOps Agent webhook docs](https://docs.aws.amazon.com/devopsagent/latest/userguide/configuring-integrations-and-knowledge-invoking-devops-agent-through-webhook.html)
- [Automated network incident response (aws-samples)](https://github.com/aws-samples/sample-automated-aws-devops-agent-network-incident-response)
- [CDK onboarding guide](https://docs.aws.amazon.com/devopsagent/latest/userguide/getting-started-with-aws-devops-agent-getting-started-with-aws-devops-agent-using-aws-cdk.html)
- [CDK sample repo](https://github.com/aws-samples/sample-aws-devops-agent-cdk)
- [K8sGPT auto-remediation docs](https://github.com/k8sgpt-ai/k8sgpt-operator/blob/main/AUTO_REMEDIATION.md)