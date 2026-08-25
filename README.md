# PulsePoint 

[![CI](https://github.com/aishwarya011k/pulsepoint/actions/workflows/ci.yml/badge.svg)](https://github.com/aishwarya011k/pulsepoint/actions/workflows/ci.yml)

**AI-Powered Predictive Uptime Monitoring Platform**

PulsePoint monitors your services and predicts failures *before* they happen — not just alerting when something's already down, but detecting degradation trends early and explaining the likely root cause in plain English.

Built as a full production-style DevOps + AI platform: containerized microservices, event-driven architecture, GitOps deployment, full observability stack, and an AI engine that turns telemetry into predictions.

PulsePoint also monitors itself — the platform runs on the exact same DevOps stack it offers to monitor other services with.

---

##  Features

-  **Continuous monitoring** — register any URL/API/service for scheduled health checks
-  **Predictive detection** — AI flags degrading trends before full outage, not just downtime
-  **AI root-cause summaries** — plain-English explanations generated from logs at incident time
-  **Incident correlation** — links related degradations across multiple monitored services
-  **ChatOps alerting** — Slack/Discord notifications with AI-generated context
-  **Full observability dashboards** — uptime, latency, infra health, and AI model accuracy in Grafana
-  **GitOps-driven deployment** — every change to PulsePoint itself is deployed via ArgoCD, auditable via Git
-  **(Stretch) Auto-remediation** — trigger rollback via ArgoCD for connected user services

---

##  Architecture

```
Developer → CI (Jenkins/GitHub Actions) → manifests-repo → ArgoCD → Kubernetes
                                                                        │
                        ┌───────────────────────────────────────────────┤
                        │                                                │
              Frontend ── Backend API ── Postgres                 Prober Worker
                             │                                          │
                          Redis (cache)                          Kafka (checks)
                                                                          │
                                                                    AI Engine
                                                              (Redis rolling state,
                                                               anomaly/trend model)
                                                                          │
                                                                 Kafka (incidents)
                                                                    │        │
                                                            ChatOps Bot   Auto-Remediation
                                                            (Slack alert)   (ArgoCD rollback)

Prometheus + Loki scrape/aggregate everything → Grafana dashboards
```

Full architecture write-up with diagrams: [`docs/architecture.md`](docs/architecture.md)

---

##  Quick Start (Local Development)

### Three Independent Services

1. **backend-api/** — FastAPI REST API (Python)
2. **prober-worker/** — Background health check scheduler (Python)
3. **frontend/** — React + Vite dashboard (TypeScript)

### Prerequisites

- **PostgreSQL 15+** (local install or `docker run postgres`)
- **Python 3.11+**
- **Node.js 18+**

### Run Locally in 3 Terminals

**Terminal 1: Backend API**
```bash
cd backend-api
cp .env.example .env
pip install -r requirements.txt
python main.py
# API runs at http://localhost:8000, docs at http://localhost:8000/docs
```

**Terminal 2: Prober Worker**
```bash
cd prober-worker
cp .env.example .env
pip install -r requirements.txt
python worker.py
# Checks targets every 60 seconds
```

### Running with Docker (single-machine via Docker Compose)

Prerequisites: Docker and Docker Compose installed locally.

1. Copy or verify service `.env` files (already included for local development):

```bash
# Optional: inspect defaults
cat backend-api/.env
cat prober-worker/.env
cat frontend/.env
```

2. Build and start the stack:

```bash
docker-compose up --build
```

3. Verify services:

 - Backend API: http://localhost:8000/health
 - Frontend: http://localhost:3000

4. Tear down and remove volumes when finished:

```bash
docker-compose down -v
```

Notes:
- The frontend image is built with `VITE_API_BASE_URL` set at build time (default points to the `backend-api` service). If you need to change the API host without rebuilding the image, see the project notes — runtime reconfiguration requires a small client-side change.
- Postgres data is persisted in a named volume `pgdata` created by Compose.

The following section shows how to run the same stack on a local Kubernetes cluster using `kind`.

### Running with Kubernetes locally (kind)

Prerequisites: `docker`, `kind`, and `kubectl` installed.

1. Build images and bring up a local `kind` cluster, load images, and deploy manifests:

```bash
./scripts/local-cluster-up.sh
```

2. Confirm the stack is running:

```bash
kubectl get pods -n pulsepoint
kubectl get svc -n pulsepoint
```

3. Access services:

- Frontend (NodePort): http://localhost:30080
- Backend (port-forwarded by the script): http://localhost:8000/health

4. Tear down when finished:

```bash
./scripts/local-cluster-down.sh
```

---

### Kafka Event Pipeline

PulsePoint now uses Kafka as the event backbone between the Prober Worker and Postgres. The flow is:

```text
Prober Worker -> Kafka checks topic -> checks-consumer -> Postgres checks/incidents tables
```

This keeps the probe loop focused on network checks and timing, while the consumer owns the database writes and incident transition logic. The `metrics` and `incidents` topics are created up front for Phase 8, but they are not consumed by the app yet.

For local debugging, you can inspect Kafka from the Strimzi-managed broker pod:

```bash
kubectl -n pulsepoint get pods | grep kafka
kubectl -n pulsepoint exec -it <kafka-pod-name> -- /bin/bash

# Inside the pod
/bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic checks --from-beginning
```

If the Strimzi CLI or UI is easier in your local setup, use that instead; the important part is that the raw `checks` messages remain visible for troubleshooting.

> Phase 6 will eventually add Redis for the checks-consumer's recent-window state, but this phase intentionally leaves that out to keep the worker and consumer focused on the Kafka pipeline.

### Deploying with Helm

The PulsePoint stack is packaged as a Helm chart for easy, repeatable deployments across different environments (local, dev, production).

#### Prerequisites
- Kubernetes cluster running (e.g., `kind`, `k3d`, or a managed cluster like EKS/GKE)
- `kubectl` and `helm` (v3+) installed
- Local Docker images pre-built and loaded into the cluster (or available in a registry)

#### Chart Structure

```
helm/pulsepoint/
├── Chart.yaml              # Chart metadata
├── values.yaml             # Default values (local/dev-like)
├── values-dev.yaml         # Dev environment overrides
├── values-prod.yaml        # Production environment overrides (placeholder)
└── templates/
    ├── namespace.yaml
    ├── postgres/           # Database deployment, service, PVC, secret
    ├── backend-api/        # Backend API deployment, service, secret, configmap
    ├── prober-worker/      # Prober worker deployment, secret, configmap
    └── frontend/           # Frontend deployment, service
```

#### Installation

**Option 1: Local Development (recommended for quick iteration)**
```bash
# Full clean reinstall of the namespace + chart
kubectl delete namespace pulsepoint
helm upgrade --install pulsepoint ./helm/pulsepoint \
  -f ./helm/pulsepoint/values-dev.yaml \
  -n pulsepoint \
  --create-namespace

# Verify the installation
kubectl get pods -n pulsepoint
kubectl get svc -n pulsepoint
```

**Option 2: Production-like (using prod overrides)**
```bash
helm upgrade --install pulsepoint ./helm/pulsepoint \
  -f ./helm/pulsepoint/values-prod.yaml \
  -n pulsepoint \
  --create-namespace
```

#### Customizing Values

All deployment parameters are exposed in `values.yaml`. To override specific settings without modifying the files:

```bash
# Override image tag for backend-api
helm upgrade --install pulsepoint ./helm/pulsepoint \
  -f ./helm/pulsepoint/values-dev.yaml \
  --set backendApi.image.tag=v1.2.3 \
  -n pulsepoint

# Override replica counts, resource limits, CORS origins, etc.
helm upgrade --install pulsepoint ./helm/pulsepoint \
  -f ./helm/pulsepoint/values-dev.yaml \
  --set backendApi.replicas=3 \
  --set backendApi.corsAllowedOrigins="{http://localhost:3000,https://api.example.com}" \
  -n pulsepoint
```

#### Secrets Management

By default, `values.yaml` includes plaintext passwords as placeholders (`aishu` for Postgres, hardcoded JWT secrets). **In production, do not commit plaintext secrets to Git.**

Instead, use one of these approaches:
1. **Helm secrets plugin:** `helm secrets` to encrypt/decrypt values files
2. **External secret store:** Use `ExternalSecrets` Operator or similar to fetch secrets from HashiCorp Vault, AWS Secrets Manager, etc.
3. **Override at deploy time:** 

```bash
helm upgrade --install pulsepoint ./helm/pulsepoint \
  -f ./helm/pulsepoint/values-prod.yaml \
  --set postgres.password="$(aws secretsmanager get-secret-value --secret-id postgres-password --query SecretString --output text)" \
  -n pulsepoint
```

#### Important Notes

- The `k8s/` directory (raw K8s manifests) is now superseded by `helm/pulsepoint/` and will be removed in a future cleanup phase.
- Frontend's `VITE_API_BASE_URL` is baked in at **Docker image build time**, not at deploy time. To change the API endpoint, rebuild the frontend image with a different `--build-arg VITE_API_BASE_URL=<new-url>`.
- Backend-api's `CORS_ALLOWED_ORIGINS` is templated via the `corsAllowedOrigins` array in `values.yaml`. Ensure your frontend's origin (e.g., `http://localhost:30080`) is included to avoid cross-origin errors.

### GitOps Deployment Flow

PulsePoint now uses a GitOps delivery loop instead of direct `helm upgrade --install` commands for normal deployments.

```text
git push (app code) → GitHub Actions CI (lint/test/build/scan/push image)
   → CI updates the dedicated manifests repo with the new image tag
   → ArgoCD detects the Git change → auto-syncs the cluster
   → New version is running, with zero manual kubectl/helm commands
```

#### How the manifests repo is updated

The CI workflow in `.github/workflows/ci.yml` performs the final GitOps step after the image pushes succeed:

1. Check out the separate `pulsepoint-manifests` repo using a `MANIFESTS_REPO_PAT` GitHub secret.
2. Update `dev/values.yaml` with the current short SHA for:
   - `backendApi.image.tag`
   - `proberWorker.image.tag`
   - `frontend.image.tag`
3. Commit the change and push it back to the manifests repo.

> The PAT should be a fine-grained or repository-scoped token with write access only to the `pulsepoint-manifests` repo, and should not be a broad personal access token with full account scope.

#### ArgoCD setup and local access

Install ArgoCD in the local cluster:

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

Get the initial admin password:

```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

Then port-forward the ArgoCD API server locally:

```bash
kubectl -n argocd port-forward svc/argocd-server 8080:443
```

Open `https://localhost:8080` in a browser, log in as `admin`, and change the password when prompted.

#### Manual sync and verification

The ArgoCD application is defined in `argocd/application.yaml` and points to the `pulsepoint-manifests` repo's `dev/` path.

To trigger a sync manually:

```bash
argocd app sync pulsepoint
```

Or use the ArgoCD UI and select the application, then click `Sync`.

To verify the GitOps loop end-to-end:

1. Make a small code change in the PulsePoint app repo.
2. Push to `main`.
3. Watch GitHub Actions build, scan, push the image, then update the manifests repo.
4. ArgoCD detects the Git change and syncs the cluster automatically.
5. Confirm the running cluster reflects the new image without any direct `kubectl` or `helm` deploy commands.

> For a local `kind` cluster, the simplest migration path from the Phase 3 Helm install is to delete and recreate the `pulsepoint` namespace before applying the ArgoCD application, so ArgoCD owns the resources from the first sync cleanly.

---

4. Tear down when finished:

```bash
./scripts/local-cluster-down.sh
```

Notes:
- The `scripts/kind-cluster-config.yaml` configures port mappings so NodePort 30080 and backend port 8000 are accessible on `localhost` while testing with `kind`.
- Browser-to-backend communication requires an address reachable from your browser (the script port-forwards the backend to `localhost:8000`).


**Terminal 3: Frontend**
```bash
cd frontend
cp .env.example .env
npm install
npm run dev
# Dashboard at http://localhost:3000
```

### First Steps

1. **Register & Login** at http://localhost:3000
2. **Add a Target** (e.g., `https://httpbin.org/status/200`)
3. **Wait** for the Prober Worker to pick it up (~60s)
4. **View Results** in the dashboard
5. **Check Now** to trigger an immediate health check

### Test It

```bash
cd backend-api
pytest test_main.py -v
```

Full Phase 1 guide: [`docs/phase1.md`](phase1-setup.md) *(coming soon)*

---

##  Tech Stack

| Layer | Tools |
|---|---|
| **Containerization** | Docker |
| **Orchestration** | Kubernetes, Helm |
| **CI/CD** | GitHub Actions |
| **Container Registry** | GitHub Container Registry (ghcr.io) |
| **Security Scanning** | Trivy |
| **GitOps / CD** | ArgoCD, dedicated `manifests-repo` (Phase 4) |
| **Event Streaming** | Apache Kafka (Strimzi Operator) |
| **Caching / State** | Redis |
| **Database** | PostgreSQL |
| **Observability** | Prometheus, Grafana, Loki + Promtail |
| **AI/ML** | scikit-learn / statsmodels (anomaly & trend detection), LLM API (root-cause summarization) |
| **Backend** | FastAPI (Python) / Node.js |
| **Frontend** | React / Next.js |

---

##  Microservices

| Service | Responsibility |
|---|---|
| `frontend/` | Dashboard — manage targets, view status, incident timeline |
| `backend-api/` | Target CRUD, auth, serves dashboard data |
| `prober-worker/` | Runs scheduled health checks, publishes results to Kafka |
| `ai-engine/` | Consumes metrics, predicts degradation, generates root-cause summaries |
| `chatops-bot/` | Sends AI-annotated incident alerts to Slack/Discord |
| `auto-remediation/` *(stretch)* | Triggers ArgoCD rollback for connected user services |

---

##  Repository Structure

```
pulsepoint/
├── services/
│   ├── frontend/
│   ├── backend-api/
│   ├── prober-worker/
│   ├── ai-engine/
│   ├── chatops-bot/
│   └── auto-remediation/
├── helm-charts/
│   ├── backend-api/
│   ├── frontend/
│   ├── prober-worker/
│   ├── ai-engine/
│   ├── kafka/
│   └── redis/
├── manifests-repo/          # separate repo in production — ArgoCD's source of truth
│   ├── dev/
│   ├── staging/
│   └── prod/
├── ci/
│   ├── Jenkinsfile
│   └── .github/workflows/
├── observability/
│   ├── prometheus/
│   ├── grafana/dashboards/
│   └── loki/
├── argocd/
│   └── application-sets.yaml
└── docs/
    └── architecture.md
```

---

## Getting Started (Local Development)

### Prerequisites
- Docker & Docker Compose
- `kind` or `k3d` (lightweight local Kubernetes)
- `kubectl`
- `helm`
- `argocd` CLI (optional, for GitOps workflow)

### 1. Clone the repo
```bash
git clone https://github.com/<your-username>/pulsepoint.git
cd pulsepoint
```

### 2. Spin up a local cluster
```bash
kind create cluster --name pulsepoint
kubectl cluster-info --context kind-pulsepoint
```

### 3. Install core infra (Kafka, Redis, Postgres)
```bash
helm install kafka helm-charts/kafka -n pulsepoint --create-namespace
helm install redis helm-charts/redis -n pulsepoint
helm install postgres helm-charts/postgres -n pulsepoint
```

### 4. Deploy application services
```bash
helm install backend-api helm-charts/backend-api -n pulsepoint
helm install frontend helm-charts/frontend -n pulsepoint
helm install prober-worker helm-charts/prober-worker -n pulsepoint
helm install ai-engine helm-charts/ai-engine -n pulsepoint
```

### 5. (Optional) Set up ArgoCD for GitOps deployment
```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl apply -f argocd/application-sets.yaml
```

### 6. Access the dashboard
```bash
kubectl port-forward svc/frontend 3000:3000 -n pulsepoint
```
Visit `http://localhost:3000`

Full setup guide: [`docs/setup.md`](docs/setup.md)

---

## 🗺️ Roadmap

- [x] Core app: target registration, manual health checks
- [x] Dockerized services deployed to Kubernetes
- [x] Helm charts for all services (Phase 3)
- [x] CI pipeline (GitHub Actions) with linting, testing, build, Trivy scan, push (Phase 3)
- [ ] GitOps deployment via ArgoCD (Phase 4)
- [ ] Dedicated manifests repo for ArgoCD (Phase 4)
- [ ] Kafka-based event pipeline for checks
- [ ] Redis caching + AI rolling-window state
- [ ] Prometheus + Grafana + Loki observability
- [ ] AI trend/anomaly detection engine
- [ ] LLM-based root-cause summarization
- [ ] ChatOps alerting (Slack/Discord)
- [ ] Self-monitoring (PulsePoint monitors itself)
- [ ] Auto-remediation via ArgoCD rollback (stretch)

---

## Why PulsePoint

Most uptime tools alert *after* a service is already down. PulsePoint's AI engine watches trends in latency and error rates to flag likely incidents **before** full failure, and explains the probable cause using log correlation — instead of just "service is down, good luck."

---

## License

MIT License — see [`LICENSE`](LICENSE) for details.

---

## Contributing

Contributions welcome. Please open an issue to discuss significant changes before submitting a PR.
