# PulsePoint — Project Timeline & Phase Plan
**Start Date:** August 11, 2026
**Target Finish:** August 31, 2026
**Total Duration:** 21 days across 8 phases

---

## Timeline Overview

| Phase | Title | Dates | Duration |
|---|---|---|---|
| 1 | Core Application Foundation | Aug 11 – Aug 13 | 3 days |
| 2 | Containerization & Manual K8s Deploy | Aug 14 – Aug 16 | 3 days |
| 3 | Helm Charts + CI Pipeline | Aug 17 – Aug 19 | 3 days |
| 4 | GitOps + ArgoCD | Aug 20 – Aug 22 | 3 days |
| 5 | Kafka Event Pipeline | Aug 23 – Aug 24 | 2 days |
| 6 | Redis Integration | Aug 25 – Aug 26 | 2 days |
| 7 | Observability Stack | Aug 27 – Aug 29 | 3 days |
| 8 | AI Engine + ChatOps + Final Polish | Aug 30 – Aug 31 | 2 days |

```
Aug 11 ───────────────────────────────────────────────► Aug 31
 │P1(3d)│P2(3d)│P3(3d)│P4(3d)│P5(2d)│P6(2d)│P7(3d)│P8(2d)│
 11  13  14  16  17  19  20  22  23 24  25 26  27  29  30 31
```

---

## Phase 1: Core Application Foundation
**Dates:** Aug 11 – Aug 13 (3 days)
**Goal:** Working app logic with no DevOps tooling yet — prove the product idea works.

### Tasks
- [ ] Design Postgres schema (`users`, `targets`, `checks`, `incidents`)
- [ ] Build Backend API (FastAPI/Node): target CRUD, auth, manual "check now" endpoint
- [ ] Build Prober Worker: basic HTTP/TCP check logic, writes results directly to Postgres
- [ ] Build minimal Frontend: register target, view latest status (no styling polish yet)
- [ ] Local `.env`-based setup, no Docker yet — run everything with `npm run dev` / `uvicorn`

### Deliverable
A working local app: register a URL, trigger a check, see status in the UI.

---

## Phase 2: Containerization & Manual K8s Deploy
**Dates:** Aug 14 – Aug 16 (3 days)
**Goal:** Everything runs in containers, deployed manually to a local cluster.

### Tasks
- [ ] Write Dockerfiles (multi-stage) for Frontend, Backend API, Prober Worker
- [ ] Write `docker-compose.yml` for local multi-service testing
- [ ] Set up local Kubernetes cluster (`kind` or `k3d`)
- [ ] Write raw K8s manifests (Deployments, Services, ConfigMaps, Secrets)
- [ ] Deploy manually via `kubectl apply -f` and verify end-to-end via port-forward

### Deliverable
Full app running inside Kubernetes, deployed manually — no automation yet.

---

## Phase 3: Helm Charts + CI Pipeline
**Dates:** Aug 17 – Aug 19 (3 days)
**Goal:** Replace raw manifests with Helm; automate build/test/scan/push.

### Tasks
- [ ] Convert manifests to Helm charts (one chart per service, or umbrella chart)
- [ ] Parameterize environment-specific values (`values-dev.yaml`, `values-prod.yaml`)
- [ ] Set up GitHub Actions (or Jenkins) pipeline: lint → test → build image → Trivy scan → push to registry
- [ ] Pipeline auto-bumps image tag (commits to a `manifests-repo` placeholder for now)

### Deliverable
`helm install` deploys the whole app; every push to `main` triggers a CI build automatically.

---

## Phase 4: GitOps + ArgoCD
**Dates:** Aug 20 – Aug 22 (3 days)
**Goal:** True GitOps deployment — CI never touches the cluster directly.

### Tasks
- [ ] Create separate `manifests-repo` (or `manifests/` folder treated as separate source)
- [ ] Install ArgoCD in the cluster
- [ ] Configure ArgoCD Application(s) pointing at `manifests-repo`
- [ ] Confirm CI pipeline updates `manifests-repo` → ArgoCD auto-syncs → cluster updates
- [ ] Test a manual rollback via ArgoCD UI/CLI

### Deliverable
Push code → CI builds → manifests-repo updates → ArgoCD deploys automatically. No manual `kubectl apply`.

---

## Phase 5: Kafka Event Pipeline
**Dates:** Aug 23 – Aug 24 (2 days)
**Goal:** Decouple probing from processing using Kafka.

### Tasks
- [ ] Deploy Kafka via Strimzi Operator (Helm)
- [ ] Create topics: `checks`, `metrics`, `incidents`
- [ ] Update Prober Worker to publish results to `checks` instead of writing directly to Postgres
- [ ] Build a simple consumer that reads `checks` and persists to Postgres (keeps DB writes async)
- [ ] Verify message flow with `kafka-console-consumer` or a debug endpoint

### Deliverable
Prober Worker and storage layer are fully decoupled via Kafka; message flow verified end-to-end.

---

## Phase 6: Redis Integration
**Dates:** Aug 25 – Aug 26 (2 days)
**Goal:** Add caching and fast state storage.

### Tasks
- [ ] Deploy Redis (Bitnami Helm chart)
- [ ] Cache dashboard "latest status per target" reads in Redis (reduce Postgres load)
- [ ] Set up Redis-backed rolling window structure per target (used by AI Engine in Phase 8)
- [ ] Add basic incident dedup logic scaffold in Redis (prevent duplicate alerts later)

### Deliverable
Dashboard reads are faster via cache; Redis rolling-window structure ready for the AI layer.

---

## Phase 7: Observability Stack
**Dates:** Aug 27 – Aug 29 (3 days)
**Goal:** Full visibility into both monitored targets and PulsePoint's own infrastructure.

### Tasks
- [ ] Deploy Prometheus (Helm) — scrape all PulsePoint services
- [ ] Deploy Grafana — build dashboards: target uptime/latency, infra health, Kafka lag
- [ ] Deploy Loki + Promtail — centralize logs from all services
- [ ] Expose custom Prometheus metrics from Backend API and Prober Worker
- [ ] Confirm Grafana shows both infra metrics and monitoring-product data side by side

### Deliverable
Live Grafana dashboards for the whole platform; logs searchable in Loki.

---

## Phase 8: AI Engine + ChatOps + Final Polish
**Dates:** Aug 30 – Aug 31 (2 days)
**Goal:** Ship the AI differentiator and wrap the project.

### Tasks
- [ ] Build AI Engine: consume `checks`/`metrics` from Kafka, use Redis rolling window
- [ ] Implement trend/anomaly detection (start simple: z-score or EWMA on latency/error rate)
- [ ] On anomaly, publish to `incidents` topic with a generated risk/confidence score
- [ ] Build root-cause summarizer: pull recent Loki logs for the target, call LLM API for plain-English explanation
- [ ] Build ChatOps Bot: consume `incidents`, post Slack/Discord alert with AI summary
- [ ] Register PulsePoint's own services as self-monitored targets
- [ ] Final README polish, architecture doc, and a 2–3 min demo video/GIF

### Deliverable
Fully working PulsePoint: predictive AI alerts with explanations, self-monitoring, all dashboards live, repo fully documented.

---

## Risk Buffer Guidance

- **Phases 1–4 are non-negotiable** — they're the DevOps core and must be solid
- **Phase 5–6 (Kafka/Redis) can be simplified** if time-constrained — e.g., single-broker Kafka, no HA
- **Phase 8 AI complexity is the safest place to cut scope** — a working z-score anomaly detector is a legitimate deliverable even without the LLM summarizer if time runs short; add the LLM piece last
- Given Phase 8 is only 2 days, consider starting the AI Engine's core logic (rolling window + anomaly scoring) a day early if Phase 7 finishes ahead of schedule

---

## Daily Definition of Done (use this checklist mentality each phase)

- [ ] Code compiles/runs without errors
- [ ] Deployed and verified in the local K8s cluster
- [ ] Relevant section of README/architecture doc updated
- [ ] Committed and pushed to GitHub with a clear commit message
- [ ] Quick note added to a `PROGRESS.md` log (helps when writing your final demo narrative)