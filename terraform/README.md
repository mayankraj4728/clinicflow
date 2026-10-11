# Terraform — ClinicFlow infrastructure

Provisions the AWS network and the EKS cluster that ClinicFlow runs on.

The module-based approach keeps the focus on Terraform concepts: providers,
variables, modules, state, plan/apply, outputs and the dependency graph.

```text
terraform/
├── versions.tf              # required_version + AWS provider
├── variables.tf             # region, cluster name, VPC CIDR, node sizing
├── main.tf                  # VPC module + EKS module
├── outputs.tf               # cluster name/endpoint, VPC & subnet IDs
└── terraform.tfvars.example # copy → terraform.tfvars for overrides
```

> **Cost warning:** an EKS cluster and a NAT gateway incur AWS charges.
> Always run `terraform destroy` when you are finished.

```bash
cd terraform
terraform init
terraform fmt -recursive
terraform validate
terraform plan
terraform apply

# point kubectl at the new cluster (also available as an output)
aws eks update-kubeconfig --region ap-south-1 --name clinicflow-eks

# tear everything down
terraform destroy
```

No credentials live in this directory. Configure AWS access with
`aws configure` or the `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`
environment variables, and keep any overrides in the git-ignored
`terraform.tfvars`.
