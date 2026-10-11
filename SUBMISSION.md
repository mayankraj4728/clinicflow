# Submission — DevSecOps Capstone (ClinicFlow)

## Deadline

| | |
|---|---|
| **Date** | Sunday, 19 October 2026 |
| **Time** | 11:59 PM IST |

Late submissions lose **5 points per 24-hour period** after the deadline.

---

## What is submitted

Submit the single GitHub repository link via the submission form
(https://forms.gle/XWAP1vAumDJgAPM1A). The repo contains:

1. **`README.md`** — full technical documentation (setup, architecture, stack,
   CI/CD, Terraform, Kubernetes, observability).
2. **`demo/`** folder with:
   - 🎥 **`demo/clinicflow-demo.mp4`** — presentation video (**MANDATORY**)
   - 📊 **`demo/clinicflow-slides.pptx`** — slide deck (**MANDATORY**)

---

## Video walkthrough plan

1. Present the slides — what ClinicFlow is and the architecture overview.
2. Live walkthrough:
   - **Codebase** — folder structure and the key source files
   - **CI/CD** — trigger a push, show the GitHub Actions pipeline end-to-end
   - **Docker** — the two built images running as non-root
   - **Registry** — images in GHCR with SHA tags
   - **Security** — Trivy scan output
   - **Terraform** — `terraform plan` output + AWS Console (VPC + EKS)
   - **Kubernetes** — `kubectl get pods/svc/ingress` all healthy
   - **Helm** — `helm list -n clinicflow`
   - **Prometheus** — Targets page showing the app as `UP`
   - **Grafana** — live dashboard with application metrics
   - **Troubleshooting** — break the Service/image and fix it live

> **No video = 0 points for M10**, regardless of other artifacts.

---

See [GRADING.md](./GRADING.md) for the full rubric.
