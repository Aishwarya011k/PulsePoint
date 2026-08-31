#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

if ! command -v kubectl >/dev/null 2>&1; then
  echo "kubectl is required but not installed or not on PATH."
  exit 1
fi

if ! kubectl config current-context >/dev/null 2>&1; then
  echo "No Kubernetes context is configured. Create a cluster first: ./scripts/local-cluster-up.sh"
  exit 1
fi

CURRENT_CONTEXT=$(kubectl config current-context)
if ! kubectl cluster-info >/dev/null 2>&1; then
  echo "The current Kubernetes context '${CURRENT_CONTEXT}' is not reachable."
  echo "Create or switch to a working cluster first, for example:"
  echo "  kind create cluster --name pulsepoint --config ./scripts/kind-cluster-config.yaml"
  echo "  kubectl config use-context kind-pulsepoint"
  exit 1
fi

echo "Installing ArgoCD into the '${CURRENT_CONTEXT}' cluster..."
kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -

# Clean up existing ArgoCD resources to avoid conflicts
echo "Cleaning up existing ArgoCD resources..."
kubectl delete namespace argocd --ignore-not-found=true
sleep 5
kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -
sleep 2

# Apply ArgoCD manifests with server-side apply and force-conflicts to handle field ownership issues
echo "Applying ArgoCD manifests..."
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml --server-side --force-conflicts

# Wait for deployments to be created
echo "Waiting for ArgoCD deployments to be created..."
for i in {1..30}; do
  if kubectl -n argocd get deployment argocd-server &>/dev/null; then
    echo "ArgoCD deployments found, proceeding with rollout status checks..."
    break
  fi
  echo "Waiting for deployments... ($i/30)"
  sleep 2
done

# Check rollout status with error handling
echo "Checking ArgoCD deployment status..."
kubectl -n argocd rollout status deployment/argocd-server --timeout=180s || echo "Warning: argocd-server rollout timed out, continuing..."
kubectl -n argocd rollout status deployment/argocd-repo-server --timeout=180s || echo "Warning: argocd-repo-server rollout timed out, continuing..."
kubectl -n argocd rollout status deployment/argocd-application-controller --timeout=180s || echo "Warning: argocd-application-controller rollout timed out, continuing..."

# Wait for secret to be created
echo "Waiting for ArgoCD initial admin secret..."
for i in {1..30}; do
  if kubectl -n argocd get secret argocd-initial-admin-secret &>/dev/null; then
    echo "Secret found."
    break
  fi
  echo "Waiting for secret... ($i/30)"
  sleep 2
done

PASSWORD=$(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d)

echo "ArgoCD admin password: ${PASSWORD}"
echo "Port-forward with: kubectl -n argocd port-forward svc/argocd-server 8888:443"
echo "Open: https://localhost:8888"

echo "Apply the application after the server is ready:"
echo "kubectl apply -f argocd/application.yaml"
