# TD Description & Prompt for `atx -t`

## TD Name

`ack-resource-adoption-from-iac`

## TD Description (for `atx custom def publish`)

Analyzes CloudFormation, Terraform, and Pulumi code and generates ACK (AWS Controllers for Kubernetes) adoption manifests that bring existing AWS resources under Kubernetes/GitOps management without recreating them - using the ResourceAdoption feature gate with adopt-or-create policy and deletion-policy retain. Translates IaC modules and nested stacks into kro ResourceGraphDefinitions, preserving reusable composition as Kubernetes-native APIs. Produces an ADOPTION_REPORT.md with inventory, discovery items, prerequisites, and dependency-sorted apply order.

## Publish Command

```bash
atx custom def publish -n ack-resource-adoption-from-iac \
    --sd ack-resource-adoption-from-iac \
    --description "Generates ACK adoption manifests and kro ResourceGraphDefinitions from CloudFormation, Terraform, and Pulumi code"
```

## Exec Command

```bash
# Full run
atx custom def exec \
  -n ack-resource-adoption-from-iac \
  -p /path/to/customer-iac-repo \
  -x -t \
  --configuration 'additionalPlanContext=Adopt all resources.'

# Scoped / flat-only variants
#   'additionalPlanContext=Adopt only the networking module.'
#   'additionalPlanContext=Skip kro, flat manifests only.'
#   'additionalPlanContext=Output directory: ack-adoption/'
```

## Prompt to use with `atx -t`

Use this as the initial description when creating the TD interactively:

---

I want to create a Transformation Definition that migrates existing IaC-managed AWS resources (CloudFormation, Terraform, Pulumi) into ACK (AWS Controllers for Kubernetes) management without recreating them.

**What it should do:**

1. **Scan the repository** for CloudFormation templates (.yaml/.json with Resources), Terraform files (.tf, .tfstate, module blocks), and Pulumi programs (@pulumi/aws or pulumi_aws).

2. **Inventory and resolve identifiers** from literals, variable defaults, tfvars, and state files. Mark unresolvable identifiers (computed values, runtime refs) for discovery instead of guessing.

3. **Map each resource to ACK** (apiVersion/Kind) and determine which Kinds need the `services.k8s.aws/adoption-fields` annotation (identifier in status: VPC, SQS, SNS, KMS, CloudFront, etc.).

4. **Generate manifests:**
   - Flat resources: one ACK manifest each, ALWAYS with `adoption-policy: adopt-or-create` and `deletion-policy: retain`
   - Terraform modules / CFN nested stacks / Pulumi components: one kro ResourceGraphDefinition (module inputs as schema fields, internal refs as CEL expressions) plus one instance CR per instantiation
   - Unresolvable identifiers: TODO(discovery) comment with the exact AWS CLI command
   - Unsupported resource types (no GA ACK controller): flag in report, never guess

5. **Validate:** YAML parse on all outputs, annotation audit (100% retain + adopt-or-create), kubectl dry-run when CRDs available.

6. **Report:** ADOPTION_REPORT.md with inventory table, skipped resources with reasons, discovery commands, prerequisite checklist (controllers, feature gate, IRSA/Pod Identity permissions), dependency-sorted apply order (IAM/KMS -> network -> data -> compute), and post-adoption IaC decommission guidance.

**Hard constraints:**
- Never modify the source IaC
- Never touch AWS APIs or any cluster
- Never omit deletion-policy: retain (a missing retain can destroy real infrastructure)
- Never wrap single flat resources in kro (RGDs only for genuine composition units)
