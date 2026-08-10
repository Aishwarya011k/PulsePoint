# PulsePoint 

**AI-Powered Predictive Uptime Monitoring Platform**

PulsePoint monitors your services and predicts failures *before* they happen — not just alerting when something's already down, but detecting degradation trends early and explaining the likely root cause in plain English.

Built as a full production-style DevOps + AI platform: containerized microservices, event-driven architecture, GitOps deployment, full observability stack, and an AI engine that turns telemetry into predictions.

> PulsePoint also monitors itself — the platform runs on the exact same DevOps stack it offers to monitor other services with.

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

##  Tech Stack

| Layer | Tools |
|---|---|
| **Containerization** | Docker |
| **Orchestration** | Kubernetes, Helm |
| **CI/CD** | Jenkins / GitHub Actions |
| **GitOps / CD** | ArgoCD, dedicated `manifests-repo` |
| **Event Streaming** | Apache Kafka (Strimzi Operator) |
| **Caching / State** | Redis |
| **Database** | PostgreSQL |
| **Observability** | Prometheus, Grafana, Loki + Promtail |
| **Security** | Trivy (image vulnerability scanning) |
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
- [ ] Helm charts for all services
- [ ] CI pipeline (Jenkins/GitHub Actions)
- [ ] GitOps deployment via ArgoCD
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
