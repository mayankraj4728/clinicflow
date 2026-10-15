# ClinicFlow — Presentation Video Script

A spoken walkthrough script for the mandatory M10 video. For each part: **SHOW**
= what to have on screen, **SAY** = narration (paraphrase in your own words,
don't read robotically). Target length ~8–12 minutes. Record with your face-cam
optional but your voice required.

> Tip: do a 1-minute dry run of the first two parts before the real take.
> If DNS drops mid-recording, pause, run the flush command, and resume.

---

## 0. Intro (15 sec)
**SHOW:** Your first PPT slide (title).
**SAY:** "Hi, I'm Mayank. This is my DevSecOps capstone — ClinicFlow, a clinic
appointment-booking app. I'll walk through the architecture on slides, then do a
full live demo from code commit all the way to a monitored Kubernetes cluster on AWS."

## 1. Slides — overview & architecture (1–1.5 min)
**SHOW:** Click through your slides: overview, tech stack, architecture diagram,
CI/CD flow, infrastructure, Kubernetes, observability.
**SAY:** "ClinicFlow is a React frontend, a FastAPI backend, and PostgreSQL.
The whole thing is containerized and ships through a GitHub Actions pipeline that
tests, builds, scans with Trivy, and pushes images to GHCR. Infrastructure is
Terraform — a VPC and an EKS cluster on AWS. The app is packaged as a Helm chart,
deployed via ArgoCD using GitOps, and monitored with Prometheus and Grafana."

## 2. Codebase (1 min)
**SHOW:** The repo in your editor. Expand `frontend/`, `backend/app/`,
`backend/tests/`, `helm/clinicflow/`, `terraform/`, `monitoring/`.
**SAY:** "The backend exposes REST endpoints for appointments plus health, ready,
and metrics endpoints. `backend/tests` has the pytest suite. The Helm chart in
`helm/clinicflow` templates the deployments, services, ingress, HPA, and a
ServiceMonitor. `terraform/` provisions the VPC and EKS, and `monitoring/` holds
the Prometheus and Grafana values."

## 3. CI/CD pipeline (1.5 min)
**SHOW:** GitHub → **Actions** tab → your latest **green** run → expand the three
jobs (Test, Build/Scan/Push, Deploy).
**SAY:** "Every push to main runs this pipeline. First it runs pytest — that's the
first quality gate; if tests fail, nothing gets built. Then it builds the backend
and frontend Docker images, scans both with Trivy, and pushes them to GitHub
Container Registry tagged with the commit SHA for traceability. The last job
deploys to a throwaway Kubernetes cluster to verify the chart end-to-end."
**(Optional live):** make a tiny change, commit, push, and show the run starting.

## 4. Docker & Registry (45 sec)
**SHOW:** `backend/Dockerfile` and `frontend/Dockerfile` (point out multi-stage +
the non-root user). Then GitHub → **Packages** → both images with SHA tags.
**SAY:** "The backend image runs as a non-root user. The frontend uses a
multi-stage build — Node builds the React bundle, then it's served by an
unprivileged Nginx. Here are both images published in GHCR, tagged by commit SHA."

## 5. Security — Trivy (30 sec)
**SHOW:** In the green Actions run, open the "Scan backend/frontend image with
Trivy" step logs showing the vulnerability table.
**SAY:** "Trivy scans both images for HIGH and CRITICAL vulnerabilities. It's
configured to flag them as a security gate. A scanner isn't a guarantee of
security — it's one automated control in the pipeline, alongside dependency and
secret scanning."

## 6. Terraform — infrastructure (1.5 min)
**SHOW:** `terraform/main.tf` (point out the VPC and EKS modules). Then your
`terraform plan` output, then the **AWS Console**: VPC with subnets, and the EKS
cluster showing **Active** with its node group.
**SAY:** "Instead of clicking around the AWS console, the infrastructure is code.
Terraform creates a VPC with public and private subnets across two availability
zones, a NAT gateway, and an EKS cluster with a managed node group. Here's the
plan, and here in the console is the running VPC and the Active EKS cluster with
two worker nodes."

## 7. Kubernetes + Helm (1.5 min)
**SHOW:** A terminal:
```
kubectl get nodes
kubectl get pods -n clinicflow
kubectl get svc -n clinicflow
kubectl get ingress -n clinicflow
kubectl get hpa -n clinicflow
helm list -n clinicflow
```
**SAY:** "The cluster has two worker nodes. In the clinicflow namespace the
backend and frontend each run two replicas, with PostgreSQL in-cluster. Services
give stable networking, the Ingress routes slash to the frontend and slash-api to
the backend, and an HPA can autoscale the backend on CPU. The whole app is managed
as one Helm release."

## 8. The app itself (45 sec)
**SHOW:** The ClinicFlow UI in the browser. Create an appointment live; show it
appear in the list.
**SAY:** "Here's the running app. I'll create an appointment — it hits the FastAPI
backend, which writes to PostgreSQL, and it shows up immediately. That's the full
stack working front to back."

## 9. Prometheus & Grafana (1 min)
**SHOW:** Prometheus **Targets** page — the clinicflow backend **UP**. Then the
Grafana **ClinicFlow dashboard** with a populated panel.
**SAY:** "The backend exposes a /metrics endpoint. Prometheus scrapes it via a
ServiceMonitor — here it is, UP. And Grafana visualizes those metrics — request
rate, latency, and errors — so I can see the app's health at a glance."

## 10. ArgoCD — GitOps (1 min)
**SHOW:** ArgoCD UI — the clinicflow Application **Healthy + Synced**. Point at the
repo URL and path.
**SAY:** "Deployment is GitOps with ArgoCD. It watches my Git repo and continuously
reconciles the cluster to match the Helm chart on main. When I push a change,
ArgoCD automatically syncs it — this is the continuous-delivery half of the
pipeline. The app is Synced and Healthy."

## 11. Troubleshooting lab (1 min)
**SHOW:**
```
kubectl apply -f troubleshooting/broken-service.yaml
kubectl get endpoints -n clinicflow
kubectl get pods --show-labels -n clinicflow
```
**SAY:** "Finally, a troubleshooting scenario. I'll apply a broken Service whose
selector labels don't match any pods. Look — the Service has no endpoints, so no
traffic reaches the pods. The lesson is that a Service finds pods by labels; no
matching labels means no endpoints means no traffic. I'd fix it by correcting the
selector." (Then delete it: `kubectl delete -f troubleshooting/broken-service.yaml`.)

## 12. Close (15 sec)
**SHOW:** Back to the app or the architecture slide.
**SAY:** "That's ClinicFlow — from a commit, through CI/CD, security scanning, and
a container registry, onto Terraform-provisioned EKS, deployed by Helm and ArgoCD,
and monitored with Prometheus and Grafana. Thanks for watching."

---

## Minimum must-show checklist (from the rubric)
- [ ] PPT slides presented
- [ ] CI/CD — a green GitHub Actions run
- [ ] Codebase overview
- [ ] Terraform plan/apply + AWS Console (VPC + EKS)
- [ ] ArgoCD — synced/healthy
- [ ] Kubernetes — pods/services/ingress running
- [ ] Prometheus — target UP
- [ ] Grafana — live panel

## Recording notes
- QuickTime → File → New Screen Recording. Enable the microphone.
- Have all tabs/terminals pre-opened so you don't fumble live.
- Save as `demo/clinicflow-demo.mp4`. If over ~100 MB, upload as a GitHub Release
  asset and link it in README.md.
- Record **before** running `terraform destroy` — the live cluster parts need it.
