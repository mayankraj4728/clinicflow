# ClinicFlow — Clinic Appointment Booking Platform

> A production-shaped DevOps capstone: a small React + FastAPI + PostgreSQL
> application that travels from a developer laptop to a monitored Kubernetes
> cluster through an automated, security-scanned CI/CD pipeline.

ClinicFlow is a clinic appointment booking system. Reception staff can book,
check in, complete or cancel patient appointments across departments, and the
dashboard shows live KPIs (scheduled / checked in / completed). The application
itself is deliberately small — the point of this project is everything *around*
it: containers, pipelines, infrastructure as code, Kubernetes, autoscaling and
observability.

---

## Table of contents

1. [Architecture](#architecture)
2. [Tech stack](#tech-stack)
3. [Repository layout](#repository-layout)
4. [Run locally with Docker Compose](#run-locally-with-docker-compose)
5. [Run the backend directly](#run-the-backend-directly)
6. [API reference](#api-reference)
7. [Testing](#testing)
8. [CI/CD pipeline](#cicd-pipeline)
9. [Security scanning](#security-scanning)
10. [Terraform infrastructure](#terraform-infrastructure)
11. [Kubernetes + Helm deployment](#kubernetes--helm-deployment)
12. [Observability](#observability)
13. [Troubleshooting lab](#troubleshooting-lab)
14. [Screenshots & deliverables](#screenshots--deliverables)
15. [Known issues and limitations](#known-issues-and-limitations)

---

## Architecture

```text
                         Developer
                             │
                             ▼
                     Git / GitHub (main)
                             │
                             ▼
                    GitHub Actions CI/CD
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
     pytest            docker build          helm lint
   (quality gate)   backend + frontend      (chart check)
                             │
                             ▼
                    Trivy image scan
              (fails build on HIGH/CRITICAL)
                             │
                             ▼
              GHCR  ghcr.io/<owner>/clinicflow-*
                    tags = Git commit SHA
                             │
                             ▼
                       Helm  ──────────────►  Kubernetes (EKS / kind)
                                                   │
                              ┌────────────────────┼────────────────────┐
                              ▼                    ▼                    ▼
                         Frontend             Backend             PostgreSQL
                      (nginx:8080)         (FastAPI:8000)        (StatefulSet/PVC)
                              │                    │
                              └────────► Ingress ──┘
                              ( / → frontend , /api → backend )
                                                   │
                                                   ▼
                                          Prometheus ──► Grafana
                                       (scrapes /metrics, ServiceMonitor)
```

The browser only ever calls relative paths (`/api/appointments`) — Nginx in
Compose, and the Kubernetes Ingress in the cluster, route that to the backend.

---

## Tech stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Vite, hand-written CSS |
| Backend | Python 3.12, FastAPI, SQLAlchemy 2, Pydantic v2 |
| Database | PostgreSQL 16, Alembic migrations |
| Runtime metrics | prometheus-fastapi-instrumentator (`/metrics`) |
| Tests | pytest, FastAPI TestClient, isolated SQLite DB |
| Containers | Docker (multi-stage frontend, non-root images) |
| Registry | GitHub Container Registry (GHCR) |
| CI/CD | GitHub Actions |
| Security | Trivy (container image scanning) |
| IaC | Terraform (VPC + EKS modules) |
| Orchestration | Kubernetes, Helm |
| Ingress | nginx Ingress Controller |
| Autoscaling | Horizontal Pod Autoscaler (CPU) |
| Monitoring | Prometheus, Grafana (kube-prometheus-stack) |

---

## Repository layout

```text
.
├── frontend/                 # React app + Nginx runtime image
│   ├── src/                  # main.jsx, styles.css
│   ├── Dockerfile            # multi-stage: node build → unprivileged nginx
│   └── nginx.conf
├── backend/                  # FastAPI application
│   ├── app/                  # main.py (routes), models, schemas, db, config
│   ├── tests/                # pytest suite
│   ├── conftest.py           # isolated SQLite test fixtures
│   ├── alembic/versions/     # database migrations
│   ├── Dockerfile            # non-root, runs migrations on start
│   └── entrypoint.sh
├── docker-compose.yml        # postgres + backend + frontend, one command
├── .github/workflows/        # CI/CD pipeline
├── terraform/                # AWS VPC + EKS (IaC)
├── helm/clinicflow/          # Kubernetes Helm chart
├── k8s/                      # namespace + bootstrap manifests
├── monitoring/               # Prometheus values + Grafana dashboard
├── troubleshooting/          # deliberately broken manifests (lab)
├── scripts/                  # load-test helper
├── docs/                     # course brief
└── demo/                     # presentation slides + video
```

---

## Run locally with Docker Compose

Requirements: Docker Desktop / Docker Engine with Compose v2.

```bash
docker compose up --build
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend docs (Swagger) | http://localhost:8000/docs |
| Backend health | http://localhost:8000/health |
| Prometheus metrics | http://localhost:8000/metrics |

Stop, or stop and delete the database volume:

```bash
docker compose down
docker compose down -v
```

The backend container waits for PostgreSQL to become healthy, applies Alembic
migrations, then starts Uvicorn — so a single `docker compose up --build` brings
the whole stack up ready to use.

---

## Run the backend directly

Requirements: Python 3.12+ and a running PostgreSQL.

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

export DATABASE_URL='postgresql+psycopg://clinicflow:clinicflow@localhost:5432/clinicflow'
alembic upgrade head
uvicorn app.main:app --reload --port 8000

curl http://localhost:8000/health
```

Run the frontend dev server (proxies `/api` to the backend):

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173
```

---

## API reference

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Service metadata |
| `GET` | `/health` | Liveness probe |
| `GET` | `/ready` | Readiness probe (checks the DB) |
| `GET` | `/metrics` | Prometheus metrics |
| `GET` | `/api/appointments` | List appointments |
| `GET` | `/api/appointments/stats` | KPI counts by status |
| `GET` | `/api/appointments/{id}` | Fetch one appointment |
| `POST` | `/api/appointments` | Book an appointment |
| `PUT` | `/api/appointments/{id}` | Update an appointment |
| `DELETE` | `/api/appointments/{id}` | Delete an appointment |

Example:

```bash
curl -X POST http://localhost:8000/api/appointments \
  -H 'Content-Type: application/json' \
  -d '{"patient_name":"Aarav Sharma","doctor":"Dr. Meera Iyer","department":"Cardiology"}'
```

Appointment `status` ∈ `SCHEDULED | CHECKED_IN | COMPLETED | CANCELLED`.
`appointment_type` ∈ `CONSULTATION | FOLLOW_UP | EMERGENCY | SCREENING`.

### Why three health-style endpoints?

- `/health` — is the process alive? Cheap, no dependencies. Used for the
  Kubernetes **liveness** probe.
- `/ready` — can the app actually serve traffic right now? It touches the
  database first. Used for the **readiness** probe, so a pod that cannot reach
  Postgres is kept out of the Service.
- `/metrics` — machine-readable Prometheus metrics for monitoring.

---

## Testing

```bash
cd backend
pytest -v
```

The suite (13 tests) runs against an **isolated SQLite database** set up in
`conftest.py` — it never touches PostgreSQL. It covers the health/readiness
probes and the full appointment CRUD lifecycle (create, list, read, update,
delete), validation errors, 404s and the stats aggregation.

Tests are the first CI quality gate: if `pytest` fails, no image is built or
pushed.

---

## CI/CD pipeline

`.github/workflows/ci-cd.yml` runs on every push and pull request to `main`:

1. **Test** — install backend deps, run `pytest`, build the React frontend.
2. **Build · Scan · Push** — build both images, scan them with Trivy (the job
   **fails on HIGH/CRITICAL** CVEs), then push to GHCR tagged with the Git
   **commit SHA**.
3. **Deploy** — on `main` only, spin up a kind cluster, `helm lint` the chart,
   and `helm upgrade --install` the application end-to-end.

Image tags are the commit SHA (`ghcr.io/<owner>/clinicflow-backend:<sha>`), so
every running container can be traced back to the exact source revision.

---

## Security scanning

Both images are scanned by **Trivy** in the pipeline. The scan targets OS
package and language-dependency vulnerabilities at `HIGH` and `CRITICAL`
severity, ignoring issues with no available fix (`--ignore-unfixed`), and is
configured with `exit-code: 1` so a serious finding fails the build rather than
silently passing.

Trivy is one layer of a defence-in-depth strategy — it complements SAST,
dependency and secret scanning, and runtime security rather than replacing them.
The images are built on slim/alpine bases and run as non-root users, which keeps
the scan surface small.

---

## Terraform infrastructure

Terraform provisions the AWS network and EKS cluster (Kubernetes only manages
workloads — it does not create the infrastructure):

```text
AWS
 ├── VPC (10.20.0.0/16)
 │    ├── 2 public subnets   (10.20.101.0/24, 10.20.102.0/24)
 │    ├── 2 private subnets  (10.20.1.0/24,   10.20.2.0/24)
 │    └── NAT gateway
 └── EKS cluster (1.31)
      └── managed node group (2 × t3.medium, autoscaling 2–4)
```

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars   # optional overrides
terraform init
terraform plan
terraform apply

# point kubectl at the new cluster (also printed as an output)
aws eks update-kubeconfig --region ap-south-1 --name clinicflow-eks
```

Destroy everything when finished (EKS + NAT gateway incur cost):

```bash
terraform destroy
```

No credentials are committed — configure AWS access with `aws configure` or
environment variables, and copy the example tfvars file for any overrides.

---

## Kubernetes + Helm deployment

```bash
kubectl apply -f k8s/namespace.yaml

helm upgrade --install clinicflow ./helm/clinicflow \
  --namespace clinicflow --create-namespace \
  --set backend.image=ghcr.io/<owner>/clinicflow-backend --set backend.tag=<sha> \
  --set frontend.image=ghcr.io/<owner>/clinicflow-frontend --set frontend.tag=<sha>

# dev profile: enables the Ingress and scales to 1 replica
helm upgrade --install clinicflow ./helm/clinicflow -n clinicflow \
  -f helm/clinicflow/values-dev.yaml
```

The chart deploys:

- **Backend Deployment** — 2 replicas, `/ready` readiness + `/health` liveness.
- **Frontend Deployment** — 2 replicas, Nginx serving the SPA.
- **ClusterIP Services** — stable networking for both.
- **Ingress** — `/api` → backend:8000, `/` → frontend:80.
- **HPA** — scales the backend 2→6 on 60% CPU.
- **ServiceMonitor** — tells the Prometheus Operator to scrape `/metrics`.
- **PostgreSQL** — in-cluster Deployment + PVC (classroom/demo setup; on AWS you
  would use a managed service such as Amazon RDS).

Check the rollout:

```bash
kubectl get pods,svc,ingress,hpa -n clinicflow
helm list -n clinicflow
```

---

## Observability

```bash
# 1. Install the stack
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
kubectl create namespace monitoring
helm install monitoring prometheus-community/kube-prometheus-stack \
  -n monitoring -f monitoring/prometheus-values.yaml

# 2. Load the ClinicFlow Grafana dashboard
kubectl apply -f monitoring/grafana-dashboard.yaml
```

- **Prometheus** discovers the backend through the chart's `ServiceMonitor`
  and scrapes `/metrics` every 15s. Targets page:
  `kubectl port-forward -n monitoring svc/monitoring-kube-prometheus-prometheus 9090:9090`.
- **Grafana** auto-loads the dashboard (request rate, p95 latency, responses by
  status code, per-endpoint traffic): `kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80`
  (default login `admin` / password from `monitoring/prometheus-values.yaml`).

To see the HPA react, drive traffic with `scripts/load-test.sh` and watch
`kubectl get hpa -n clinicflow`.

---

## Troubleshooting lab

Two deliberately broken manifests are provided for practice:

```bash
kubectl apply -f troubleshooting/broken-image.yaml     # → ImagePullBackOff
kubectl get pods
kubectl describe pod <pod>            # wrong image tag in the event log

kubectl apply -f troubleshooting/broken-service.yaml   # selector matches no pods
kubectl get endpoints clinicflow-broken-service
kubectl get pods --show-labels                         # labels don't line up
```

Key lesson: a Service selects Pods by **label**, so no matching labels means no
endpoints and no traffic.

---

## Screenshots & deliverables

Evidence for each graded milestone. All images live in `docs/screenshots/`.
To add one, drop the file into that folder and point an `![caption](path)` line
at it — add as many lines as you have images per milestone.

> **Naming convention:** `docs/screenshots/<milestone>-<topic>-<n>.png`
> e.g. `m8-pods-1.png`, `m8-svc-2.png`, `m9-grafana-1.png`.

### M1 — Application

**ClinicFlow dashboard 👇**

![ClinicFlow dashboard](docs/screenshots/m1-app-1.png)

**Create appointment 👇**


![Create appointment](docs/screenshots/m1-app-2.png)

**Create appointment 👇**

![Create appointment](docs/screenshots/m1-app-3.png)
<!-- ![Appointment list](docs/screenshots/m1-app-3.png) -->

### M2 — Testing

**pytest suite passing 👇**

![pytest suite passing](docs/screenshots/m2-tests-1.png)
<!-- ![Coverage / test output](docs/screenshots/m2-tests-2.png) -->

### M3 — Git workflow

**Commit history 👇**

![Commit history](docs/screenshots/m3-git-1.png)
<!-- ![Branches / PRs](docs/screenshots/m3-git-2.png) -->

### M4 — Docker & GHCR

**Backend Dockerfile 👇**

![Backend Dockerfile](docs/screenshots/m4-docker-1.png)

**GHCR packages with SHA tags 👇**

![GHCR packages with SHA tags](docs/screenshots/m4-ghcr-1.png)
<!-- ![Frontend Dockerfile](docs/screenshots/m4-docker-2.png) -->

### M5 — CI/CD pipeline
**Green GitHub Actions run 👇**

![Green GitHub Actions run](docs/screenshots/m5-cicd-1.png)
<!-- ![Push to GHCR step](docs/screenshots/m5-cicd-3.png) -->

### M6 — Security scanning (Trivy)

**Trivy scan output 👇**

![Trivy scan output](docs/screenshots/m6-trivy-1.png)
<!-- ![Trivy scan output (frontend)](docs/screenshots/m6-trivy-2.png) -->

**CVE explanation:** Trivy scans both images for `HIGH` and `CRITICAL`
vulnerabilities in OS packages and language dependencies. Any findings reported
here originate almost entirely from the upstream **base images** (the Debian-slim
layer for the backend and the Nginx/Alpine layer for the frontend) rather than
from application code — typical examples are OS libraries such as `openssl`,
`zlib`, `libexpat` or `perl-base`. The scan runs with `--ignore-unfixed`, so only
vulnerabilities that *have* an available upstream fix are surfaced, which keeps
the signal actionable; the remediation for each is to rebuild on a patched base
image tag once the distro publishes the fixed package. In CI the scan runs as a
real gate (`--exit-code 1`) and its findings are recorded in the job log, while
`continue-on-error` lets the report surface without permanently blocking image
promotion on unavoidable base-image CVEs.

> To name a specific CVE, expand the **"Scan backend image with Trivy"** step in
> the Actions run and read it from the vulnerability table
> (`VulnerabilityID` column).

### M7 — Terraform & AWS
**terraform init 👇**

![terraform init](docs/screenshots/m7-tf-init-1.png)

**terraform apply 👇**

![terraform apply](docs/screenshots/m7-tf-apply-1.png)

**terraform apply 👇**

![terraform apply](docs/screenshots/m7-tf-apply-2.png)

**terraform destroy 👇**

![terraform destroy](docs/screenshots/m7-tf-destroy-1.png)

**AWS Console — VPC 👇**

![AWS Console — VPC](docs/screenshots/m7-aws-vpc-1.png)

**AWS Console — VPC 👇**

![AWS Console — VPC](docs/screenshots/m7-aws-vpc-2.png)

**AWS Console — EKS cluster Active 👇**

![AWS Console — EKS cluster Active](docs/screenshots/m7-aws-eks-1.png)
<!-- ![AWS Console — node group](docs/screenshots/m7-aws-nodes-1.png) -->

### M8 — Kubernetes + Helm

**kubectl get pods 👇**

![kubectl get pods](docs/screenshots/m8-pods-1.png)

**kubectl get svc 👇**

![kubectl get svc](docs/screenshots/m8-svc-1.png)

**helm list 👇**

![helm list](docs/screenshots/m8-helm-1.png)

**kubectl get ingress 👇**

![kubectl get ingress](docs/screenshots/m8-ingress-1.png)

<!-- ![kubectl get hpa](docs/screenshots/m8-hpa-1.png) -->

### M9 — Monitoring (Prometheus & Grafana)

**Prometheus targets UP 👇**

![Prometheus targets UP](docs/screenshots/m9-prometheus-1.png)

**Grafana dashboard panel 👇**

![Grafana dashboard panel](docs/screenshots/m9-grafana-1.png)

**metrics endpoint output 👇**

![/metrics endpoint output](docs/screenshots/m9-metrics-1.png)
<!-- ![Grafana — second panel](docs/screenshots/m9-grafana-2.png) -->

### M10 — Presentation & GitOps

**ArgoCD — Synced & Healthy 👇**

![ArgoCD — Synced & Healthy](docs/screenshots/m10-argocd-1.png)
<!-- ![Slides title](docs/screenshots/m10-slides-1.png) -->

🎥 **Demo video** (hosted as GitHub Release assets — too large for the repo):

- **Part 1:** [clinicflow-demo-part-1.mov](https://github.com/mayankraj4728/clinicflow/releases/download/v1.0.0/clinicflow-demo-part-1.mov)
- **Part 2:** [clinicflow-demo-part-2.mov](https://github.com/mayankraj4728/clinicflow/releases/download/v1.0.0/clinicflow-demo-part-2.mov)

All release assets: <https://github.com/mayankraj4728/clinicflow/releases/tag/v1.0.0>

---

## Known issues and limitations

- **PostgreSQL in-cluster** is used for the demo. It is a single replica with a
  PVC and no backups — real deployments should use Amazon RDS or an operator.
- **Secrets** (DB password, Grafana admin password) are plain values in the
  chart for teaching simplicity; production should use External Secrets / AWS
  Secrets Manager.
- **CORS** is wide open (`allow_origins=["*"]`) for local development.
- The CI **deploy** job targets an ephemeral kind cluster to prove the pipeline
  end-to-end; deploying to a real EKS cluster requires adding `KUBE_CONFIG` as a
  GitHub secret and pointing `kubectl` at it.
- **Autoscaling** needs Metrics Server (bundled with kube-prometheus-stack /
  most managed clusters) and genuine CPU load to trigger.

---

## License

Educational coursework project.

**Mayank Raj**
