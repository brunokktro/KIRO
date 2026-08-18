# TD Description & Prompt for `atx -t`

## TD Name

`eks-version-upgrade-readiness`

## TD Description (for `atx custom def publish`)

Analyze and transform Kubernetes manifests, Helm charts, Kustomize overlays, Terraform configs, and CDK code for Amazon EKS version upgrade compatibility. Identifies deprecated and removed APIs, updates apiVersions and resource fields, validates addon compatibility, checks rollback readiness (N-1 compatibility and disruption controls), and generates a migration report with manual action items. Supports upgrades between any EKS versions from 1.16 through 1.36+.

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
   - **Rollback blockers**: anything the code adopts that exists in the target version but NOT in
     target-minus-one, which would prevent an EKS Version Rollback during the 7-day window
   - **Disruption controls** that stall node replacement (and therefore both the data plane upgrade
     and an Auto Mode rollback): NodePool disruption budgets of `nodes: "0"` covering `Drifted`,
     `karpenter.sh/do-not-disrupt` annotations, PDBs with `maxUnavailable: 0`

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
   - A "Rollback Readiness" section: which changes are safe on both the target and
     target-minus-one, which ones close the rollback window, and which disruption controls in the
     repo would stall or block a rollback (with the EKS insight severity: ERROR blocks, WARNING
     delays)

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
- Every transformation carries an N-1 verdict: `safe on both` or `target-only (closes the rollback window)`. A target-only change is never suppressed - it is applied and annotated, because the target version is what the customer asked for.
- Rollback checks are scoped to EKS versions currently in standard or extended support. Do not evaluate rollback for a hop where either side is out of support - the API rejects it anyway.
- NEVER call cluster APIs. No `update-cluster-version`, no `list-insights`, no `cancel-update`. The skill reads code and reports; the rollback decision and execution belong to the operator.
- The recommended sequencing to preserve the rollback window is: add-ons cross-compatible with N-1/N/N+1, then control plane, then a bake period (~1 week per environment), then data plane. Document it in the report; do not execute it.

---

## Reference Files to Provide During `atx -t`

When the ATX agent asks for documentation or examples, provide these files from this directory:

1. `api-removals-by-version.md` - Complete API removal table (historical, 1.16+)
2. `eks-specific-changes.md` - EKS-specific changes, disruption controls, and addon matrix
3. `examples-before-after.md` - 12 concrete before/after examples
4. `rollback-readiness.md` - Inverse lookup (what was ADDED per version), Auto Mode disruption
   blockers with insight severity, add-on cross-compatibility strategy, and `rollbackConfig`
   support per IaC tool. Scoped to the supported-version window

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
