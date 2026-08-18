# ATX Custom TD: EKS Version Upgrade Readiness & Code Migration

## Purpose

Custom Transformation Definition for AWS Transform that analyzes and transforms customer code (K8s manifests, Helm charts, Terraform, CDK, Kustomize) for compatibility with a target Amazon EKS/Kubernetes version.

## Workflow

```text
Input: Customer repo + Target EKS version (via additionalPlanContext)
  |
  +-- 1. Scan: identify all manifests/charts/configs
  +-- 2. Detect: map deprecated/removed APIs for the target version
  +--    + rollback blockers: what the code adopts that does not exist in target-minus-one
  +--    + disruption controls that stall node replacement
  +-- 3. Transform: update apiVersions, fields, and configs automatically
  +-- 4. Validate: dry-run / helm template / terraform validate
  +-- 5. Report: breaking changes + rollback readiness + manual action items
```

## Usage

```bash
atx custom def exec \\
  -n eks-version-upgrade-readiness \\
  -p /path/to/customer-repo \\
  -x -t \\
  --configuration 'additionalPlanContext=Target EKS version 1.32. Upgrade from 1.28.'
```

## Complement to the EKS Upgrade Controller

- **Upgrade Controller** = handles the CLUSTER (control plane + data plane version upgrades)
- **This TD** = handles the CODE (manifests, charts, configs that run ON the cluster)

Together, they provide end-to-end upgrade readiness: code prepared + cluster upgraded automatically.

The Upgrade Controller is also the natural place to implement the **bake period** between the
control plane and data plane rollouts, which is what keeps the EKS rollback window usable (see
below). Today most pipelines advance control plane, add-ons and data plane in one continuous run,
which forfeits the window.

## Rollback Readiness

Amazon EKS Version Rollback reverts the control plane one minor version (N to N-1) within 7 days of
an in-place upgrade. That turns backward compatibility into a **code** requirement: during the
window, what is deployed has to be valid on both versions.

Why this TD is the right place for the check:

- **EKS Rollback Readiness Insights only run after the upgrade, and only for 7 days.** This TD runs
  before, so a blocker can still be designed around instead of discovered during an incident.
- **The insights cover EKS-managed add-ons only** (CoreDNS, VPC CNI, kube-proxy). Karpenter, the LB
  Controller, Istio, ArgoCD and cluster-autoscaler are the customer's problem, and this TD already
  reads their manifests and values.
- **Four of the Auto Mode checks are pure YAML** the TD already parses: NodePool disruption budgets,
  `karpenter.sh/do-not-disrupt` on pods, PDBs with `maxUnavailable: 0`, and node annotations. The
  same controls throttle the data plane upgrade, so the check pays off even with no rollback.

Scope boundary: the TD never calls a cluster API. No `update-cluster-version`, no `list-insights`,
no `cancel-update`. It produces the pre-flight; the operator decides and executes.

Maintenance: the rollback tables are limited to EKS versions in standard or extended support,
because a rollback needs both sides of the hop to be supported. Rows are deleted as versions age
out rather than backfilled.

## Reference Files

- `api-removals-by-version.md` - Complete table of APIs removed per K8s version (1.16 through 1.36), historical on purpose
- `eks-specific-changes.md` - EKS-specific changes per version, disruption controls, addon compatibility matrix
- `examples-before-after.md` - 12 concrete transformation examples (before/after)
- `rollback-readiness.md` - Inverse lookup (what was ADDED per version), Auto Mode blockers with insight severity, add-on cross-compatibility, `rollbackConfig` support per IaC tool
- `td-description.md` - Description and prompt for creating the TD with `atx -t`
