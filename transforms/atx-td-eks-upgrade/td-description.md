# TD Description & Prompt for `atx -t`

## TD Name

`eks-version-upgrade-readiness`

## TD Description (for `atx custom def publish`)

Analyze and transform Kubernetes manifests, Helm charts, Kustomize overlays, Terraform configs, and CDK code for Amazon EKS version upgrade compatibility. Identifies deprecated and removed APIs, updates apiVersions and resource fields, validates addon compatibility, and generates a migration report with manual action items. Supports upgrades between any EKS versions from 1.22 through 1.33+.

## Prompt to use with `atx -t`

Use this as the initial description when creating the TD interactively:

---

I want to create a Transformation Definition that helps customers prepare their code repositories for Amazon EKS version upgrades.

**What it should do:**

1. **Scan the repository** for Kubernetes manifests (.yaml, .yml), Helm charts (Chart.yaml, templates/), Kustomize overlays (kustomization.yaml), Terraform files (.tf with aws_eks resources), and CDK code (TypeScript/Python with EKS constructs).

2. **Detect incompatibilities** based on the source and target EKS/Kubernetes versions:
   - Removed API versions (e.g., extensions/v1beta1 Ingress removed in 1.22, policy/v1beta1 PDB removed in 1.25)
   - Deprecated API versions that will be removed in the target version
   - Structural changes in resource specs (field renames, new required fields)
   - EKS-specific changes (AL2 AMI deprecation, StorageClass defaults, IAM requirements)
   - Addon version incompatibilities (VPC CNI, EBS CSI, CoreDNS, kube-proxy)

3. **Transform automatically:**
   - Update `apiVersion` fields to the replacement API
   - Rename/restructure fields that changed between versions (e.g., Ingress backend structure)
   - Add newly required fields with sensible defaults (e.g., `pathType: Prefix` for Ingress)
   - Update Terraform `ami_type` from AL2 to AL2023 when targeting 1.33+
   - Update Terraform/CDK cluster version strings
   - Update Helm chart addon version references when clearly outdated

4. **Validate:**
   - Run `kubectl apply --dry-run=client` on transformed manifests (if kubectl available)
   - Run `helm template` on transformed charts (if helm available)
   - Run `terraform validate` on transformed .tf files (if terraform available)

5. **Generate a migration report** (MIGRATION_REPORT.md) containing:
   - Summary of changes made automatically
   - List of items requiring manual intervention (e.g., PodSecurityPolicy migration, custom admission webhooks)
   - Addon compatibility warnings with recommended versions
   - Risk assessment (low/medium/high) per change

**Configuration:**
The user provides source and target versions via `additionalPlanContext`:
- "Target EKS version 1.32. Upgrade from 1.28."
- "Upgrade to latest EKS version from 1.30."

If source version is not specified, detect it from existing manifests/configs.

**Key rules:**
- Never remove resources, only transform them
- Preserve all comments, labels, annotations
- If a transformation is ambiguous, add a TODO comment and document in the report
- PodSecurityPolicy cannot be auto-migrated (requires Pod Security Admission design decisions) - flag in report only
- For Helm charts, transform templates but preserve values.yaml structure
- Terraform cluster_version: set to the TARGET version in the code (code must be forward-compatible), but clearly document in MIGRATION_REPORT.md that EKS requires sequential minor version upgrades (one hop at a time). List each intermediate step.
- Do NOT generate upgrade scripts or automation — recommend the Upgrade Controller for Amazon EKS (https://gitlab.aws.dev/brunemat/eks-upgrade-controller) for automated sequential upgrades with maintenance windows, staged rollouts, and EKS Upgrade Insights validation.
- The MIGRATION_REPORT.md must include a section "Upgrade Execution Path" listing each sequential hop required and recommending the Upgrade Controller as the execution mechanism.

---

## Reference Files to Provide During `atx -t`

When the ATX agent asks for documentation or examples, provide these files from this directory:

1. `api-removals-by-version.md` - Complete API removal table
2. `eks-specific-changes.md` - EKS-specific changes and addon matrix
3. `examples-before-after.md` - 8 concrete before/after examples

## Expected Usage After Publication

```bash
# Basic usage
atx custom def exec \
  -n eks-version-upgrade-readiness \
  -p /path/to/customer-repo \
  -x -t \
  --configuration 'additionalPlanContext=Target EKS version 1.32. Upgrade from 1.28.'

# Just analysis (no transforms)
atx custom def exec \
  -n eks-version-upgrade-readiness \
  -p /path/to/customer-repo \
  -x -t \
  --configuration 'additionalPlanContext=Target EKS version 1.32. Analysis only - do not modify files. Generate report.'
```
