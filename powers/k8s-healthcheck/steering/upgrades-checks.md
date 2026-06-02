# Upgrade Readiness Checks

## Overview

Upgrade readiness validation based on:
- [EKS Best Practices - Cluster Upgrades](https://docs.aws.amazon.com/eks/latest/best-practices/cluster-upgrades.html)
- [Kubernetes Deprecation Policy](https://kubernetes.io/docs/reference/using-api/deprecation-policy/)

---

## Check: EKS Cluster Insights (EKS-Specific)

**Severity:** Varies (from EKS native insights)

**What to check:**
1. Query EKS Insights for UPGRADE_READINESS category
2. Query EKS Insights for MISCONFIGURATION category
3. Review each insight's status and recommendations

**How to check:**
```
get_eks_insights:
  cluster_name: <cluster>
  category: UPGRADE_READINESS
```

**Finding logic:**
- Insight with status FAILING -> HIGH or CRITICAL
- Insight with status WARNING -> MEDIUM
- Insight with status PASSING -> PASS

---

## Check: Deprecated API Usage

**Severity:** CRITICAL (if target version removes the API)

**What to check:**
1. Workloads using APIs removed in target Kubernetes version
2. Helm releases referencing deprecated API versions
3. CRDs using deprecated API versions
4. Webhook configurations using deprecated admission APIs

**Common removals by version:**

| Version | Removed APIs |
|---------|-------------|
| 1.25 | PodSecurityPolicy, batch/v1beta1 CronJob |
| 1.26 | flowcontrol.apiserver.k8s.io/v1beta1 |
| 1.27 | storage.k8s.io/v1beta1 CSIStorageCapacity |
| 1.29 | flowcontrol.apiserver.k8s.io/v1beta2 |
| 1.32 | flowcontrol.apiserver.k8s.io/v1beta3 |

**Tools for detection:**
- `kubectl-convert` plugin
- Pluto (scan for deprecated APIs)
- kube-no-trouble (kubent)

---

## Check: Version Skew Compliance

**Severity:** HIGH

**What to check:**
1. Node kubelet version vs control plane version
2. Allowed skew: kubelet can be up to N-3 (K8s 1.28+) or N-2 (older)
3. All nodes on same minor version (recommended)

**Finding logic:**
- Node version > 3 minor behind control plane (1.28+) -> CRITICAL
- Mixed node versions -> MEDIUM
- All nodes same version as control plane -> PASS

---

## Check: Add-on Compatibility

**Severity:** HIGH

**What to check:**
1. EKS managed add-ons compatible with target version
2. Self-managed add-ons compatibility
3. CSI drivers compatible with target version

**Critical add-ons to verify:**
- VPC CNI (aws-node)
- CoreDNS
- kube-proxy
- EBS/EFS CSI drivers
- cert-manager
- ingress controller
- Karpenter

---

## Check: Upgrade Sequence Planning

**Severity:** MEDIUM

**What to check:**
1. Upgrade plan follows: Control Plane -> Add-ons -> Data Plane
2. Backup strategy in place (Velero)
3. PDBs won't block node drain

**Finding logic:**
- PDB blocking all disruptions -> HIGH (will stall upgrade)
- No backup before upgrade -> MEDIUM

**Recommendation:**
1. Enable control plane logging
2. Take Velero backup
3. Upgrade control plane (one minor version at a time)
4. Update add-ons
5. Upgrade data plane
6. Validate workloads healthy

---

## Check: Webhook Compatibility

**Severity:** HIGH

**What to check:**
1. Webhooks that might break with new API versions
2. Webhook failurePolicy (should be `Ignore` for non-critical)
3. Webhooks pointing to unavailable services

**Finding logic:**
- Webhook with failurePolicy=Fail pointing to unhealthy service -> CRITICAL
- Webhook matching `*` resources -> MEDIUM (broad impact)

---

## Check: Custom Resource Definitions

**Severity:** MEDIUM

**What to check:**
1. CRDs using deprecated API versions
2. CRD stored versions that need migration
3. CRD controllers healthy and compatible

---

## Check: EKS Support Lifecycle

**Severity:** HIGH

**What to check:**
1. Current cluster version vs EKS support calendar
2. Standard support remaining (14 months from release)
3. Extended support pricing implications

**Finding logic:**
- Version entering extended support within 60 days -> HIGH
- Version in extended support (higher cost) -> MEDIUM
- Version at risk of auto-upgrade -> CRITICAL

**Recommendation:**
- Upgrade at least once per year
- Plan upgrades before entering extended support
- Subscribe to EKS release notifications
