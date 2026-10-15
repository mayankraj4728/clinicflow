# Demo assets

This folder holds the presentation material for the ClinicFlow capstone.

| File | Purpose |
|------|---------|
| `clinicflow-slides.pdf` | Slide deck (11 slides) — project overview, stack, architecture, CI/CD, infrastructure, K8s, observability, key learnings. |
| `clinicflow-demo.mp4` | **Presentation video** — full live walkthrough (see below). |

## Video walkthrough script

Follow this order when recording:

1. **Slides** — introduce ClinicFlow and the architecture.
2. **Codebase** — walk the folder structure (`frontend/`, `backend/`, `helm/`, `terraform/`).
3. **CI/CD** — make a small change, `git push`, show GitHub Actions running green end-to-end.
4. **Docker** — show both images built and running as non-root.
5. **Registry** — GHCR package page with SHA-tagged images.
6. **Security** — the Trivy scan step output in the pipeline.
7. **Terraform** — `terraform plan`, then AWS Console showing the VPC + EKS cluster.
8. **Kubernetes** — `kubectl get pods,svc,ingress,hpa -n clinicflow` all healthy.
9. **Helm** — `helm list -n clinicflow`.
10. **Ingress** — open the app in the browser through the Ingress host.
11. **Prometheus** — Targets page showing the ClinicFlow backend as `UP`.
12. **Grafana** — live dashboard with request rate / latency panels populated.
13. **Troubleshooting** — apply `troubleshooting/broken-service.yaml`, show empty endpoints, fix it live.
