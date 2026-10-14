# ClinicFlow — AWS Deployment Runbook (no-skip)

End-to-end: AWS auth → Terraform (VPC + EKS) → images → Helm → Ingress →
monitoring → ArgoCD → HPA → troubleshooting → **destroy**. Every command is
copy-paste ready for this repo (`mayankraj4728/clinicflow`, region `ap-south-1`).

> 💰 **Cost warning.** EKS + NAT gateway + 2× t3.medium bill by the hour.
> Do the whole demo in **one sitting**, capture screenshots, then run
> **Phase 10 (destroy)** the same day. Expect roughly a few USD if torn down promptly.

Screenshot targets are called out inline as **📸 SHOT (Mx)** and summarised in the
final checklist. `Mx` = grading module in `GRADING.md`.

---

## Phase 0 — Install tools & authenticate (laptop)

### 0.1 Install the CLIs (macOS / Homebrew)
```bash
brew install awscli terraform kubectl helm
# verify
aws --version && terraform version && kubectl version --client && helm version
```

### 0.2 Create an AWS IAM user with programmatic access
1. AWS Console → **IAM → Users → Create user** (e.g. `clinicflow-admin`).
2. Attach **AdministratorAccess** (fine for a short-lived capstone demo).
3. **Create access key** → *Command Line Interface (CLI)* → copy the Access key
   ID and Secret.

### 0.3 Configure credentials locally
```bash
aws configure
#   AWS Access Key ID     : <paste>
#   AWS Secret Access Key : <paste>
#   Default region name   : ap-south-1
#   Default output format  : json

# confirm you are authenticated
aws sts get-caller-identity
```
> ⚠️ Never put these keys in any file in the repo. `aws configure` stores them in
> `~/.aws/`, which is outside the project.

---

## Phase 1 — Terraform: provision VPC + EKS (M7, 15 pts)

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars    # git-ignored; adjust if you like

terraform init
```
**📸 SHOT (M7):** `terraform init` success ("Terraform has been successfully initialized!").

```bash
terraform plan -out tfplan
```
**📸 SHOT (M7):** the end of `terraform plan` — the "Plan: N to add, 0 to change,
0 to destroy" line (should be non-empty).

```bash
terraform apply tfplan      # takes ~15–20 minutes (EKS control plane is slow)
```
**📸 SHOT (M7):** `Apply complete! Resources: N added` plus the **Outputs** block
(cluster_name, cluster_endpoint, vpc_id, etc.).

Now prove it in the console:
- **📸 SHOT (M7):** AWS Console → **VPC** → your `clinicflow-eks-vpc` with its subnets.
- **📸 SHOT (M7):** AWS Console → **EKS → Clusters → clinicflow-eks** showing
  *Active*, and its **Compute → Node group** with 2 nodes Ready.

---

## Phase 2 — Point kubectl at the new cluster

Terraform prints the exact command as the `configure_kubectl_command` output:
```bash
aws eks update-kubeconfig --region ap-south-1 --name clinicflow-eks

kubectl get nodes
```
**📸 SHOT (M8):** `kubectl get nodes` → 2 nodes in `Ready` state.

---

## Phase 3 — Make the images pullable

The CI already pushed `ghcr.io/mayankraj4728/clinicflow-backend` and
`-frontend`, tagged with the Git commit SHA.

### 3.1 (Simplest) make the two GHCR packages public
github.com/users/mayankraj4728/packages → open each package → **Package settings**
→ **Danger Zone → Change visibility → Public**. Do this for **both** images.

### 3.2 (Alternative) keep them private + use a pull secret
```bash
# classic PAT with read:packages scope
kubectl create namespace clinicflow
kubectl create secret docker-registry ghcr-secret \
  --namespace clinicflow \
  --docker-server=ghcr.io \
  --docker-username=mayankraj4728 \
  --docker-password=<YOUR_GHCR_PAT>
# then add  --set imagePullSecrets[0].name=ghcr-secret  to the helm command below
```

Capture the image tag you'll deploy (the full SHA that CI pushed):
```bash
export IMAGE_TAG=$(git rev-parse origin/main)
echo "$IMAGE_TAG"
```

---

## Phase 4 — Monitoring stack FIRST (so the ServiceMonitor CRD exists)

Install kube-prometheus-stack before ClinicFlow, because the chart ships a
`ServiceMonitor` (`monitoring.coreos.com/v1`) that needs the Prometheus Operator CRDs.

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
kubectl create namespace monitoring

helm install monitoring prometheus-community/kube-prometheus-stack \
  -n monitoring -f monitoring/prometheus-values.yaml

# load the ClinicFlow Grafana dashboard
kubectl apply -f monitoring/grafana-dashboard.yaml

kubectl get pods -n monitoring      # wait until all are Running (~2–3 min)
```

---

## Phase 5 — Deploy ClinicFlow with Helm (M8, 15 pts)

```bash
helm upgrade --install clinicflow ./helm/clinicflow \
  --namespace clinicflow --create-namespace \
  --set backend.image=ghcr.io/mayankraj4728/clinicflow-backend \
  --set backend.tag=$IMAGE_TAG \
  --set frontend.image=ghcr.io/mayankraj4728/clinicflow-frontend \
  --set frontend.tag=$IMAGE_TAG \
  --set postgres.enabled=true
# (add --set imagePullSecrets[0].name=ghcr-secret here if you used Phase 3.2)

kubectl get pods -n clinicflow -w     # Ctrl-C once backend/frontend/postgres are Running
```
**📸 SHOT (M8):** `kubectl get pods -n clinicflow` — all pods `Running`.
**📸 SHOT (M8):** `kubectl get svc -n clinicflow` — backend + frontend ClusterIP services.
**📸 SHOT (M8):** `helm list -n clinicflow` — the `clinicflow` release `deployed`.

> If a pod is `ImagePullBackOff`, you skipped Phase 3 — make the images public
> or attach the pull secret, then `helm upgrade ...` again.

---

## Phase 6 — Ingress: reach the app in a browser (M8)

### 6.1 Install an ingress controller (creates an AWS load balancer)
```bash
helm upgrade --install ingress-nginx ingress-nginx \
  --repo https://kubernetes.github.io/ingress-nginx \
  --namespace ingress-nginx --create-namespace

kubectl get svc -n ingress-nginx    # wait for EXTERNAL-IP (an *.elb.amazonaws.com name)
```

### 6.2 Re-deploy ClinicFlow with the dev values (enables the Ingress resource)
```bash
helm upgrade --install clinicflow ./helm/clinicflow \
  --namespace clinicflow \
  -f helm/clinicflow/values-dev.yaml \
  --set backend.image=ghcr.io/mayankraj4728/clinicflow-backend \
  --set backend.tag=$IMAGE_TAG \
  --set frontend.image=ghcr.io/mayankraj4728/clinicflow-frontend \
  --set frontend.tag=$IMAGE_TAG \
  --set postgres.enabled=true

kubectl get ingress -n clinicflow
```
**📸 SHOT (M8):** `kubectl get ingress -n clinicflow` — host `clinicflow.local`,
routes `/` and `/api`.

### 6.3 Open it in a browser
The ingress host is the fake name `clinicflow.local`, so map it to the load balancer:
```bash
# resolve the ELB hostname to an IP
ELB=$(kubectl get svc -n ingress-nginx ingress-nginx-controller \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
echo "$ELB"
nslookup "$ELB"          # grab one of the returned IPs
# add to /etc/hosts  (replace 1.2.3.4 with that IP)
echo "1.2.3.4  clinicflow.local" | sudo tee -a /etc/hosts
```
Open **http://clinicflow.local** in the browser.
**📸 SHOT (M8):** the ClinicFlow UI loaded via the Ingress host.
**📸 SHOT (M1):** create an appointment in the UI to show the app working.

> **Fallback if the ELB/DNS is slow:** `kubectl port-forward -n clinicflow
> svc/clinicflow-frontend 8080:80` then open http://localhost:8080 — still a valid
> "app running in the cluster" shot, though prefer the Ingress one for M8.

---

## Phase 7 — Observability screenshots (M9, 10 pts)

### 7.1 Prometheus targets
```bash
kubectl port-forward -n monitoring svc/monitoring-kube-prometheus-prometheus 9090:9090
```
Open **http://localhost:9090** → **Status → Targets**.
**📸 SHOT (M9):** the ClinicFlow backend target showing **UP**.

### 7.2 Backend /metrics (raw)
```bash
kubectl port-forward -n clinicflow svc/clinicflow-backend 8000:8000
curl http://localhost:8000/metrics | head -30
```
**📸 SHOT (M9):** Prometheus-formatted `/metrics` output.

### 7.3 Grafana dashboard
```bash
kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80
```
Open **http://localhost:3000** → login `admin` / `clinicflow-admin` →
open the **ClinicFlow** dashboard. Generate a little traffic first (refresh the app
or `curl` the API a few times) so panels populate.
**📸 SHOT (M9):** a Grafana panel with live request-rate / latency data.

---

## Phase 8 — ArgoCD / GitOps (required in the M10 video)

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f \
  https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl wait --for=condition=available --timeout=300s \
  deployment/argocd-server -n argocd

# point the Application manifest at your repo (replace the <owner> placeholder)
sed -i '' 's/<owner>/mayankraj4728/g' argocd/application.yaml
kubectl apply -f argocd/application.yaml

# login to the UI
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath='{.data.password}' | base64 -d; echo
kubectl port-forward -n argocd svc/argocd-server 8081:443
```
Open **https://localhost:8081** → login `admin` / (password printed above).
**📸 SHOT (M10 video):** the `clinicflow` Application **Synced / Healthy**.

---

## Phase 9 — HPA + troubleshooting (demo / video)

### 9.1 HPA (uses the default values; needs metrics-server — EKS has it)
```bash
kubectl get hpa -n clinicflow
# generate load, then watch it scale
bash scripts/*load* 2>/dev/null || kubectl run load --image=busybox -n clinicflow \
  --restart=Never -- /bin/sh -c "while true; do wget -q -O- http://clinicflow-backend:8000/ ; done"
kubectl get hpa -n clinicflow -w
```
**📸 SHOT (demo):** HPA replica count climbing under load.

### 9.2 Troubleshooting lab
```bash
kubectl apply -f troubleshooting/broken-service.yaml
kubectl get endpoints            # show empty endpoints (label mismatch)
kubectl get pods --show-labels
# ...then fix it live and show endpoints populate
```
**📸 SHOT (demo):** broken Service with no endpoints, then fixed.

---

## Phase 10 — DESTROY everything (M7, stops the bill)

```bash
# delete in-cluster add-ons first so their load balancers are removed
helm uninstall clinicflow -n clinicflow
helm uninstall ingress-nginx -n ingress-nginx
helm uninstall monitoring -n monitoring

# then tear down the infrastructure
cd terraform
terraform destroy
```
**📸 SHOT (M7):** `Destroy complete! Resources: N destroyed.`

> Double-check in the console that the **EKS cluster, NAT gateway, and any
> leftover ELB** are gone, so AWS stops charging you.

---

## Screenshot checklist (maps to GRADING.md)

| # | Screenshot | Module |
|---|------------|--------|
| 1 | `terraform init` success | M7 |
| 2 | `terraform plan` — non-empty plan | M7 |
| 3 | `terraform apply` complete + Outputs | M7 |
| 4 | AWS Console — VPC + subnets | M7 |
| 5 | AWS Console — EKS cluster Active + node group | M7 |
| 6 | `terraform destroy` complete | M7 |
| 7 | `kubectl get nodes` Ready | M8 |
| 8 | `kubectl get pods -n clinicflow` all Running | M8 |
| 9 | `kubectl get svc -n clinicflow` | M8 |
| 10 | `helm list -n clinicflow` | M8 |
| 11 | `kubectl get ingress -n clinicflow` | M8 |
| 12 | App open in browser via Ingress | M8 |
| 13 | App — create an appointment | M1 |
| 14 | Prometheus Targets — backend UP | M9 |
| 15 | `/metrics` raw output | M9 |
| 16 | Grafana panel with live data | M9 |
| 17 | GitHub Actions — green pipeline run | M5 |
| 18 | GHCR packages with SHA tags | M5 |
| 19 | Trivy scan output in the pipeline | M6 |
| 20 | ArgoCD Application Synced/Healthy | M10 video |

**Already done / separate from AWS:** the green CI run (#17), GHCR images (#18),
and Trivy output (#19) come from your GitHub Actions run — screenshot those from the
browser; you don't need the cluster for them.
