#!/usr/bin/env bash
set -euo pipefail

if ! command -v helm >/dev/null 2>&1 || ! command -v kubectl >/dev/null 2>&1; then
  echo "helm and kubectl are required."
  exit 1
fi

if ! kubectl cluster-info >/dev/null 2>&1; then
  echo "The current Kubernetes context is not reachable. Create the kind cluster first."
  exit 1
fi

kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts --force-update
helm repo add grafana https://grafana.github.io/helm-charts --force-update
helm repo update

helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --values - <<'EOF'
prometheus:
  serviceMonitorSelector:
    matchLabels:
      release: kube-prometheus-stack
  serviceMonitorNamespaceSelector: {}
  prometheusSpec:
    retention: 12h
    scrapeInterval: 30s
    evaluationInterval: 30s
    resources:
      requests:
        cpu: 100m
        memory: 256Mi
      limits:
        cpu: 500m
        memory: 512Mi
    storageSpec: {}
alertmanager:
  alertmanagerSpec:
    resources:
      requests:
        cpu: 25m
        memory: 64Mi
      limits:
        cpu: 100m
        memory: 128Mi
grafana:
  adminUser: admin
  adminPassword: pulsepoint-local
  resources:
    requests:
      cpu: 50m
      memory: 128Mi
    limits:
      cpu: 200m
      memory: 256Mi
  sidecar:
    dashboards:
      enabled: true
      searchNamespace: ALL
  additionalDataSources:
    - name: Loki
      type: loki
      access: proxy
      url: http://loki:3100
      isDefault: false
nodeExporter:
  enabled: false
kubeStateMetrics:
  resources:
    requests:
      cpu: 25m
      memory: 64Mi
    limits:
      cpu: 100m
      memory: 128Mi
prometheusOperator:
  resources:
    requests:
      cpu: 25m
      memory: 64Mi
    limits:
      cpu: 100m
      memory: 128Mi
EOF

helm upgrade --install loki grafana/loki-stack \
  --namespace monitoring \
  --set grafana.enabled=false \
  --set prometheus.enabled=false \
  --set loki.persistence.enabled=false \
  --set loki.config.table_manager.retention_deletes_enabled=true \
  --set loki.config.table_manager.retention_period=48h \
  --set loki.resources.requests.cpu=50m \
  --set loki.resources.requests.memory=128Mi \
  --set loki.resources.limits.cpu=200m \
  --set loki.resources.limits.memory=256Mi \
  --set promtail.resources.requests.cpu=25m \
  --set promtail.resources.requests.memory=32Mi \
  --set promtail.resources.limits.cpu=100m \
  --set promtail.resources.limits.memory=128Mi

echo "Monitoring installed in namespace monitoring."
echo "Grafana: kubectl -n monitoring port-forward svc/kube-prometheus-stack-grafana 3000:80"
echo "Prometheus: kubectl -n monitoring port-forward svc/kube-prometheus-stack-prometheus 9090:9090"
