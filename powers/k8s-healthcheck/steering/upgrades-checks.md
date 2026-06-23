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

get_eks_insights:
  cluster_name: <cluster>
  category: MISCONFIGURATION
```

**Finding logic:**
- Insight with status FAILING → map to HIGH or CRITICAL based on description
- Insight with status WARNING → map to MEDIUM
- Insight with status PASSING → PASS

**Recommendation:** Follow EKS Insight recommendations directly. They are version-specific and authoritative.

---

## Check: Deprecated API Usage

**Severity:** CRITICAL (if target version removes the API)

**What to check:**
1. Workloads using APIs removed in target Kubernetes version
2. Helm releases referencing deprecated API versions
3. CRDs using deprecated API versions
4. Webhook configurations using deprecated admission APIs

**How to check:**
```
kubectl_get:
  resourceType: deployments
  allNamespaces: true
  output: json
# Check apiVersion field

list_api_resources (kubernetes MCP)
# Cross-reference available APIs with workload manifests
```

For EKS, also check control plane audit logs:
```
get_cloudwatch_logs:
  cluster_name: <cluster>
  resource_type: cluster
  log_type: control-plane
  filter_pattern: "deprecated"
  minutes: 10080
```

**Common removals by version:**

| Version | Removed APIs |
|---------|-------------|
| 1.25 | PodSecurityPolicy, batch/v1beta1 CronJob |
| 1.26 | flowcontrol.apiserver.k8s.io/v1beta1 |
| 1.27 | storage.k8s.io/v1beta1 CSIStorageCapacity |
| 1.29 | flowcontrol.apiserver.k8s.io/v1beta2 |
| 1.32 | flowcontrol.apiserver.k8s.io/v1beta3 |

**Tools for detection:**
- `kubectl-convert` plugin (convert manifests to new API versions)
- Pluto (scan for deprecated APIs in manifests and Helm releases)
- kube-no-trouble (kubent) - scan for deprecated/removed APIs

**Recommendation:**
- Run `kubent` before every upgrade
- Update manifests to use current stable APIs
- Use `kubectl convert` to migrate YAML files

---

## Check: Version Skew Compliance

**Severity:** HIGH

**What to check:**
1. Node kubelet version vs control plane version
2. kubectl version vs cluster version
3. Allowed skew: kubelet can be up to N-3 (K8s 1.28+) or N-2 (older)
4. All nodes on same minor version (recommended)

**How to check:**
```
kubectl_get:
  resourceType: nodes
  output: json
```
Check `.status.nodeInfo.kubeletVersion` vs cluster version.

**Finding logic:**
- Node version > 2 minor behind control plane (pre-1.28) → CRITICAL
- Node version > 3 minor behind control plane (1.28+) → CRITICAL
- Mixed node versions (e.g., some 1.29, some 1.30) → MEDIUM
- All nodes same version as control plane → PASS

**Recommendation:**
- Upgrade data plane within days of control plane upgrade
- Use managed node groups or Karpenter drift for automated node updates
- Never skip more than 1 minor version per upgrade cycle

---

## Check: Add-on Compatibility

**Severity:** HIGH

**What to check:**
1. EKS managed add-ons compatible with target version
2. Self-managed add-ons (cert-manager, ingress, monitoring) compatibility
3. Helm chart versions compatible with target K8s version
4. CSI drivers compatible with target version

**How to check (EKS):**
```
list_k8s_resources:
  cluster_name: <cluster>
  kind: Pod
  api_version: v1
  namespace: kube-system
```
List all system pods and their versions.

**Critical add-ons to verify:**
- VPC CNI (aws-node)
- CoreDNS
- kube-proxy
- EBS CSI driver
- EFS CSI driver
- cert-manager
- ingress controller
- monitoring stack (Prometheus, Grafana)
- Karpenter
- Cluster Autoscaler

**Finding logic:**
- Add-on with known incompatibility → CRITICAL
- Add-on version > 2 releases behind → MEDIUM
- No compatibility check performed → HIGH

---

## Check: Upgrade Sequence Planning

**Severity:** MEDIUM

**What to check:**
1. Upgrade plan follows correct sequence: Control Plane → Add-ons → Data Plane
2. Blue/green cluster strategy evaluated for multi-version jumps
3. Backup strategy in place (Velero or equivalent)
4. PodDisruptionBudgets won't block node drain
5. Drain testing performed

**How to check:**
```
kubectl_get:
  resourceType: poddisruptionbudgets
  allNamespaces: true
  output: json
```
Check for PDBs with `maxUnavailable: 0` (will block upgrades).

**Finding logic:**
- PDB blocking all disruptions → HIGH (will stall upgrade)
- No backup before upgrade → MEDIUM
- Multi-version jump planned without blue/green → MEDIUM
- Proper sequence documented → PASS

**Recommendation:**
1. Enable control plane logging before upgrade
2. Take Velero backup
3. Upgrade control plane (one minor version at a time)
4. Update add-ons to compatible versions
5. Upgrade data plane (node groups, Karpenter nodes)
6. Validate workloads healthy after each step

---

## Check: Webhook Compatibility

**Severity:** HIGH

**What to check:**
1. Validating/Mutating webhooks that might break with new API versions
2. Webhook timeout settings (too aggressive can block API calls)
3. Webhook failurePolicy (should be `Ignore` for non-critical webhooks)
4. Webhooks pointing to unavailable services

**How to check:**
```
kubectl_get:
  resourceType: validatingwebhookconfigurations
  output: json

kubectl_get:
  resourceType: mutatingwebhookconfigurations
  output: json
```

**Finding logic:**
- Webhook with failurePolicy=Fail pointing to unhealthy service → CRITICAL
- Webhook with timeout > 10s → MEDIUM
- Webhook matching `*` resources → MEDIUM (broad impact)

---

## Check: Custom Resource Definitions

**Severity:** MEDIUM

**What to check:**
1. CRDs using deprecated API versions (apiextensions.k8s.io/v1beta1)
2. CRD stored versions that need migration
3. CRD controllers healthy and compatible

**How to check:**
```
kubectl_get:
  resourceType: customresourcedefinitions
  output: json
```
Check `.spec.versions` and `.status.storedVersions`.

**Finding logic:**
- CRD with only v1beta1 → CRITICAL (removed in 1.22+)
- CRD with stale storedVersions → MEDIUM
- CRD controller not running → HIGH

---

## Check: EKS Version Support Lifecycle

**Severity:** HIGH

**What to check:**
1. Current cluster version against the [EKS Kubernetes versions](https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html) matrix
2. Days remaining in [Standard Support](https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions-standard.html) (~14 months from EKS release of that minor)
3. Whether the cluster is already in [Extended Support](https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions-extended.html) (cost premium - see `cost-checks.md`)
4. Auto-upgrade deadline (forced upgrade once Extended Support expires)
5. EKS-specific changes between minors via [release calendar](https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-release-calendar.html) (e.g., AL2023 default, IPv6 support, control plane changes that don't exist upstream)

**How to check (EKS):**
- Identify cluster version: `aws eks describe-cluster --name <c> --query 'cluster.version'`
- Cross-reference with the support matrix tables in the userguide URLs above (these are updated by AWS - always re-fetch, never rely on a snapshot)

**Finding logic:**
- Version unsupported (past Extended Support expiry) → CRITICAL (forced upgrade imminent)
- Version in Extended Support → HIGH (cost impact + EOL approaching)
- Version exiting Standard Support within 90 days → HIGH (plan upgrade now)
- Version in Standard Support with >6 months remaining → PASS

**Recommendation:**
- Maintain at most N-1 minor version behind the latest Standard Support release
- Schedule upgrade BEFORE Standard Support ends to avoid Extended Support premium
- Subscribe to AWS Health Dashboard EKS notifications for version-specific events

---

## Check: Kubernetes Release Notes Review (target version)

**Severity:** HIGH (when planning an upgrade)

**What to check:**
Before any upgrade, review the official [Kubernetes release notes](https://kubernetes.io/releases/notes/) for the target minor version to identify:
1. Removed APIs (must migrate manifests + Helm charts before upgrade)
2. Deprecated APIs (warn, but still work)
3. Behavior changes (default values, scheduler changes, kubelet changes)
4. Feature gate promotions (alpha → beta → GA, or removals)
5. Security fixes that justify accelerating the upgrade

**How to check:**
- Fetch the index at `https://kubernetes.io/releases/notes/` and follow the link for the target version
- Cross-reference with EKS-specific changes via the [release calendar](https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-release-calendar.html)
- Run `kubent` (kube-no-trouble) and `pluto` against current cluster manifests + Helm releases

**Finding logic:**
- Removed API used by any workload → CRITICAL (will fail post-upgrade)
- Deprecated API used → HIGH (must migrate within 1-2 minors)
- Default behavior change affects current setup → MEDIUM
- Feature gate change affects enabled features → MEDIUM

**Recommendation:**
- ALWAYS read the target version's CHANGELOG before scheduling the upgrade
- Maintain a per-version delta document for the team
- Run `kubent` and `pluto` in CI against staging clusters
