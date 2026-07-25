#!/bin/bash
set -euo pipefail

echo "=== Devnovate Mumbai Demo: K8sGPT Setup ==="
echo ""

CLUSTER_NAME="devnovate-demo"
REGION="us-east-1"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ROLE_NAME="K8sGPTBedrockRole"

# 1. Create EKS cluster
echo "[1/6] Creating EKS cluster..."
eksctl create cluster -f cluster.yaml

# 2. Create IAM Role for K8sGPT Bedrock access
echo "[2/6] Creating IAM Role: $ROLE_NAME..."
cat > /tmp/k8sgpt-bedrock-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": [
        "arn:aws:bedrock:*::foundation-model/*",
        "arn:aws:bedrock:*:*:inference-profile/*"
      ]
    }
  ]
}
EOF

# Create the role (trust policy will be updated by Pod Identity)
aws iam create-role \
  --role-name "$ROLE_NAME" \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": { "Service": "pods.eks.amazonaws.com" },
      "Action": ["sts:AssumeRole", "sts:TagSession"]
    }]
  }' \
  --region "$REGION" 2>/dev/null || echo "  (role may already exist)"

aws iam put-role-policy \
  --role-name "$ROLE_NAME" \
  --policy-name K8sGPTBedrockAccess \
  --policy-document file:///tmp/k8sgpt-bedrock-policy.json

echo "  Role ARN: arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"

# 3. Install K8sGPT Operator
echo "[3/6] Installing K8sGPT Operator..."
helm repo add k8sgpt https://charts.k8sgpt.ai/
helm repo update
helm install k8sgpt-operator k8sgpt/k8sgpt-operator \
  -n k8sgpt-operator-system --create-namespace

# 4. Create Pod Identity association
echo "[4/6] Setting up Pod Identity for Bedrock..."
eksctl create podidentityassociation \
  --cluster "$CLUSTER_NAME" \
  --namespace k8sgpt-operator-system \
  --service-account-name k8sgpt-k8sgpt-operator-system \
  --role-arn "arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}" \
  --region "$REGION"

# 5. Apply K8sGPT config with auto-remediation
echo "[5/6] Applying K8sGPT config..."
kubectl apply -f k8sgpt-config.yaml

# 6. Install Kyverno + policy
echo "[6/6] Installing Kyverno and guardrail policy..."
helm repo add kyverno https://kyverno.github.io/kyverno/
helm install kyverno kyverno/kyverno -n kyverno --create-namespace
echo "  Waiting for Kyverno to be ready..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/instance=kyverno -n kyverno --timeout=120s
kubectl apply -f kyverno-policy.yaml

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Resources created:"
echo "  - EKS cluster: $CLUSTER_NAME"
echo "  - IAM role: $ROLE_NAME (Bedrock access via Pod Identity)"
echo "  - K8sGPT Operator (auto-remediation enabled)"
echo "  - Kyverno (blocks AI in 'critical' namespace)"
echo ""
echo "Ready for demo:"
echo "  kubectl apply -f memory-hog.yaml"
echo "  kubectl get results -n k8sgpt-operator-system -w"
