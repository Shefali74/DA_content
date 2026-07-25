#!/bin/bash
set -euo pipefail

echo "=== Cleanup: K8sGPT Demo Infrastructure ==="
echo ""

CLUSTER_NAME="devnovate-demo"
REGION="us-east-1"
ROLE_NAME="K8sGPTBedrockRole"

# Delete demo workloads
echo "[1/5] Deleting demo namespaces..."
kubectl delete namespace demo --ignore-not-found
kubectl delete namespace critical --ignore-not-found

# Uninstall Kyverno
echo "[2/5] Uninstalling Kyverno..."
kubectl delete clusterpolicy block-ai-remediation-critical --ignore-not-found
helm uninstall kyverno -n kyverno 2>/dev/null || true
kubectl delete namespace kyverno --ignore-not-found

# Uninstall K8sGPT
echo "[3/5] Uninstalling K8sGPT Operator..."
kubectl delete k8sgpt k8sgpt -n k8sgpt-operator-system --ignore-not-found
helm uninstall k8sgpt-operator -n k8sgpt-operator-system 2>/dev/null || true
kubectl delete namespace k8sgpt-operator-system --ignore-not-found

# Delete IAM Role
echo "[4/5] Deleting IAM Role: $ROLE_NAME..."
aws iam delete-role-policy --role-name "$ROLE_NAME" --policy-name K8sGPTBedrockAccess 2>/dev/null || true
aws iam delete-role --role-name "$ROLE_NAME" 2>/dev/null || true

# Delete EKS cluster
echo "[5/5] Deleting EKS cluster: $CLUSTER_NAME..."
eksctl delete cluster --name "$CLUSTER_NAME" --region "$REGION" --wait

echo ""
echo "=== All K8sGPT demo resources cleaned up ==="
