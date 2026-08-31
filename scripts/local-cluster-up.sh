#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

echo "Checking prerequisites..."
command -v kind >/dev/null 2>&1 || { echo "kind not found. Install kind first."; exit 1; }
command -v kubectl >/dev/null 2>&1 || { echo "kubectl not found. Install kubectl first."; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "docker not found. Install docker first."; exit 1; }
command -v helm >/dev/null 2>&1 || { echo "helm not found. Install helm first."; exit 1; }

CLUSTER_NAME=pulsepoint
KIND_CONFIG="$(pwd)/scripts/kind-cluster-config.yaml"

if ! kind get clusters | grep -q "^${CLUSTER_NAME}$"; then
  echo "Creating kind cluster '${CLUSTER_NAME}'..."
  kind create cluster --name "${CLUSTER_NAME}" --config "$KIND_CONFIG"
else
  echo "Kind cluster '${CLUSTER_NAME}' already exists."
fi

echo "Building images..."
docker build -t pulsepoint/backend-api:local -f backend-api/Dockerfile .
docker build -t pulsepoint/prober-worker:local -f prober-worker/Dockerfile .
docker build -t pulsepoint/checks-consumer:local -f checks-consumer/Dockerfile .
docker build -t pulsepoint/frontend:local -f frontend/Dockerfile --build-arg VITE_API_BASE_URL=http://localhost:8000 .

echo "Loading images into kind..."
kind load docker-image pulsepoint/backend-api:local --name ${CLUSTER_NAME}
kind load docker-image pulsepoint/prober-worker:local --name ${CLUSTER_NAME}
kind load docker-image pulsepoint/checks-consumer:local --name ${CLUSTER_NAME}
kind load docker-image pulsepoint/frontend:local --name ${CLUSTER_NAME}

echo "Installing Strimzi operator for Kafka CRDs..."
kubectl create namespace kafka --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f "https://strimzi.io/install/latest?namespace=kafka" -n kafka
kubectl wait deployment/strimzi-cluster-operator -n kafka --for=condition=available --timeout=180s
kubectl get pods -n kafka

echo "Applying Kubernetes manifests with Helm..."
helm upgrade --install pulsepoint ./helm/pulsepoint \
  -f ./helm/pulsepoint/values-dev.yaml \
  -n pulsepoint \
  --create-namespace

echo "Waiting for Kafka and app pods to be ready (this may take a couple minutes)..."
kubectl wait --for=condition=ready pod -l strimzi.io/cluster=pulsepoint-kafka -n pulsepoint --timeout=240s || true
kubectl wait --for=condition=ready pod -l app=postgres -n pulsepoint --timeout=120s || true
kubectl wait --for=condition=ready pod -l app=backend-api -n pulsepoint --timeout=120s || true
kubectl wait --for=condition=ready pod -l app=frontend -n pulsepoint --timeout=120s || true

echo "Port-forwarding backend to localhost:8000 (background)..."
kubectl port-forward svc/backend-api 8000:8000 -n pulsepoint >/dev/null 2>&1 &

echo "Frontend should be reachable at http://localhost:30080"
echo "Backend health endpoint at http://localhost:8000/health"

kubectl get pods -n pulsepoint

echo "Done."
