# ATX Custom TD: EKS Version Upgrade Readiness & Code Migration

## Purpose

Custom Transformation Definition for AWS Transform that analyzes and transforms customer code (K8s manifests, Helm charts, Terraform, CDK, Kustomize) for compatibility with a target Amazon EKS/Kubernetes version.

## Workflow

```text
Input: Customer repo + Target EKS version (via additionalPlanContext)
  |
  +-- 1. Scan: identify all manifests/charts/configs
  +-- 2. Detect: map deprecated/removed APIs for the target version
  +-- 3. Transform: update apiVersions, fields, and configs automatically
  +-- 4. Validate: dry-run / helm template / terraform validate
  +-- 5. Report: generate breaking changes report + manual action items
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

## Reference Files

- `api-removals-by-version.md` - Complete table of APIs removed per K8s version (1.16 through 1.36)
- `eks-specific-changes.md` - EKS-specific changes per version + addon compatibility matrix
- `examples-before-after.md` - 8 concrete transformation examples (before/after)
- `td-description.md` - Description and prompt for creating the TD with `atx -t`
