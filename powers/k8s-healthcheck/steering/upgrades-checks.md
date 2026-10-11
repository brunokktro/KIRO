# Upgrade Readiness Checks

## Overview

Upgrade readiness validation based on:
- [EKS Best Practices - Cluster Upgrades](https://docs.aws.amazon.com/eks/latest/best-practices/cluster-upgrades.html)
- [Kubernetes Deprecation Policy](https://kubernetes.io/docs/reference/using-api/deprecation-policy/)

Every check below carries a stable **Check ID**, its evidence commands, the exact FAIL condition and a fixed report line. The catalog of all IDs, the scoring formula and the report format live in `POWER.md`.

---

## Check: UPG-01 EKS Cluster Insights (EKS-Specific)

**Severity:** Varies (from EKS native insights)

**Check ID:** `UPG-01` | **Scope level:** cluster | **Applies to:** EKS only | **Evaluation:** aws

**Evidence:**
```bash
aws eks list-insights --cluster-name <cluster> --region <region> --query 'insights[].[name, category, insightStatus.status]' --output text
```

**FAIL when:** an insight with status `ERROR` (HIGH) or `WARNING` (MEDIUM). `UNKNOWN` insights go to Not checked. Resource = `Insight/<name>`.

**Why (report line):** EKS Insights are version-specific blockers that AWS has already detected on this cluster.

**Source:** [EKS cluster insights](https://docs.aws.amazon.com/eks/latest/userguide/cluster-insights.html)

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
- Insight with status ERROR → HIGH (the API statuses are PASSING, WARNING, ERROR, UNKNOWN)
- Insight with status WARNING → map to MEDIUM
- Insight with status PASSING → PASS

**Recommendation:** Follow EKS Insight recommendations directly. They are version-specific and authoritative.

**Fix:** not a manifest change: follow the recommendation of each insight (`aws eks describe-insight --cluster-name <cluster> --id <insight-id>`).

---

## Check: UPG-02 Deprecated API Usage

**Severity:** CRITICAL (if target version removes the API)

**Check ID:** `UPG-02` | **Scope level:** cluster | **Applies to:** any cluster | **Evaluation:** kubectl

**Evidence:**
```bash
kubectl get --raw /metrics | grep '^apiserver_requested_deprecated_apis'
```

**FAIL when:** a series with `removed_release` lower than or equal to the target minor (CRITICAL). Target = current minor + 1 unless the prompt names `Target version`. Resource = `API/<group>/<version>/<resource>`.

**Why (report line):** A request to an API removed in the target version fails the moment the control plane is upgraded.

**Source:** [Deprecated API Migration Guide](https://kubernetes.io/docs/reference/using-api/deprecation-guide/)

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

**Fix (YAML):**
```yaml
# Move the manifest to the stable API named in the removal, for example:
apiVersion: batch/v1   # was batch/v1beta1
kind: CronJob
```

---

## Check: UPG-03 Version Skew Compliance

**Severity:** HIGH

**Check ID:** `UPG-03` | **Scope level:** cluster | **Applies to:** any cluster | **Evaluation:** kubectl

**Evidence:**
```bash
kubectl version -o json | jq -r '.serverVersion.gitVersion'
kubectl get nodes -o json | jq -r '[.items[].status.nodeInfo.kubeletVersion] | group_by(.) | map("\(.[0]) nodes=\(length)")[]'
```

**FAIL when:** apply **Finding logic** (the LOW row covers nodes one minor behind, inside the allowed skew).

**Why (report line):** Kubelets outside the supported skew stop working after the next control plane upgrade.

**Source:** [Version Skew Policy](https://kubernetes.io/releases/version-skew-policy/)

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
- All nodes one minor behind the control plane, inside the allowed skew → LOW
- All nodes same version as control plane → PASS

**Recommendation:**
- Upgrade data plane within days of control plane upgrade
- Use managed node groups or Karpenter drift for automated node updates
- Never skip more than 1 minor version per upgrade cycle

**Fix:** not a manifest change: upgrade the data plane (managed node group update, Karpenter drift, or replace self-managed nodes).

---

## Check: UPG-04 Add-on Compatibility

**Severity:** HIGH

**Check ID:** `UPG-04` | **Scope level:** cluster | **Applies to:** EKS only | **Evaluation:** aws

**Evidence:**
```bash
aws eks list-addons --cluster-name <cluster> --region <region> --output text
aws eks describe-addon --cluster-name <cluster> --region <region> --addon-name <addon> --query 'addon.addonVersion' --output text
aws eks describe-addon-versions --region <region> --addon-name <addon> --kubernetes-version <target> --query 'addons[0].addonVersions[].addonVersion' --output text
```

**FAIL when:** an EKS managed add-on version is not in the list for the target version (CRITICAL); more than 2 releases behind the newest version for the current Kubernetes version (MEDIUM). Self-managed add-ons (Helm) are listed under Not checked instead of the "No compatibility check performed" row.

**Why (report line):** An incompatible add-on (CNI, CoreDNS, kube-proxy, CSI) breaks networking or storage right after the upgrade.

**Source:** [Amazon EKS add-ons](https://docs.aws.amazon.com/eks/latest/userguide/eks-add-ons.html)

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

**Fix (YAML):**
```yaml
# eksctl ClusterConfig
addons:
- name: <addon>
  version: <version listed for the target Kubernetes version>
```

---

## Check: UPG-05 Upgrade Sequence Planning

**Severity:** MEDIUM

**Check ID:** `UPG-05` | **Scope level:** cluster | **Applies to:** any cluster | **Evaluation:** kubectl

**Evidence:**
```bash
kubectl get pdb -A -o json | jq -r '.items[] | select(.spec.maxUnavailable == 0 or .spec.maxUnavailable == "0%" or .spec.minAvailable == "100%" or ((.spec.minAvailable | type) == "number" and (.status.expectedPods // 0) > 0 and .spec.minAvailable >= .status.expectedPods)) | "\(.metadata.namespace)/PodDisruptionBudget/\(.metadata.name)"'
kubectl get crd backups.velero.io -o name 2>/dev/null
```

**FAIL when:** a PDB allows zero disruptions by spec (HIGH); no Velero CRD and no other backup tool named in the prompt (MEDIUM). The blue/green and sequence rows are not scored.

**Why (report line):** A PDB that allows zero evictions stalls every node drain of the upgrade.

**Source:** [EKS Best Practices - Cluster Upgrades](https://docs.aws.amazon.com/eks/latest/best-practices/cluster-upgrades.html)

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

**Fix (YAML):**
```yaml
spec:
  maxUnavailable: 1   # never maxUnavailable: 0 or minAvailable: 100%
```

---

## Check: UPG-06 Webhook Compatibility

**Severity:** HIGH

**Check ID:** `UPG-06` | **Scope level:** cluster | **Applies to:** any cluster | **Evaluation:** kubectl

**Evidence:**
```bash
kubectl get validatingwebhookconfigurations,mutatingwebhookconfigurations -o json | jq -r '.items[] | .kind as $k | .metadata.name as $n | .webhooks[] | "\($k)/\($n) webhook=\(.name) failurePolicy=\(.failurePolicy) timeout=\(.timeoutSeconds) service=\(.clientConfig.service.namespace // "-")/\(.clientConfig.service.name // "-") wildcard=\(any(.rules[]?; (.resources // []) | any(. == "*" or . == "*/*")))"'
```

**FAIL when:** apply **Finding logic**. Unhealthy service = zero ready endpoints in `kubectl get endpointslices -n <svc-ns> -l kubernetes.io/service-name=<svc>`.

**Why (report line):** A failing webhook with failurePolicy Fail blocks API writes cluster-wide, including the upgrade itself.

**Source:** [Dynamic Admission Control](https://kubernetes.io/docs/reference/access-authn-authz/extensible-admission-controllers/)

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

**Fix (YAML):**
```yaml
# Patch of the existing configuration (other fields unchanged)
webhooks:
- name: <webhook>
  failurePolicy: Ignore   # keep Fail only for webhooks that must block
  timeoutSeconds: 5
  rules:
  - apiGroups: ["apps"]
    apiVersions: ["v1"]
    operations: ["CREATE", "UPDATE"]
    resources: ["deployments"]   # no "*"
```

---

## Check: UPG-07 Custom Resource Definitions

**Severity:** MEDIUM

**Check ID:** `UPG-07` | **Scope level:** cluster | **Applies to:** any cluster | **Evaluation:** kubectl

**Evidence:**
```bash
kubectl get crd -o json | jq -r '.items[] | select((.status.storedVersions | length) > 1) | "CustomResourceDefinition/\(.metadata.name) storedVersions=\(.status.storedVersions | join(","))"'
```

**FAIL when:** a CRD keeps more than one entry in `status.storedVersions` (MEDIUM). The v1beta1 row cannot occur on 1.22 or later. The controller row is not scored.

**Why (report line):** Stale stored versions block removing an old CRD version and break the next operator upgrade.

**Source:** [Versions in CustomResourceDefinitions](https://kubernetes.io/docs/tasks/extend-kubernetes/custom-resources/custom-resource-definition-versioning/)

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

**Fix:** not a manifest change: migrate stored objects to the storage version, then remove the old entry from `status.storedVersions`.

---

## Check: UPG-08 EKS Version Support Lifecycle

**Severity:** HIGH

**Check ID:** `UPG-08` | **Scope level:** cluster | **Applies to:** EKS only | **Evaluation:** aws

**Evidence:**
```bash
aws eks describe-cluster-versions --region <region> --cluster-versions <version> --query 'clusterVersions[0].[versionStatus, endOfStandardSupportDate, endOfExtendedSupportDate]' --output text
```

**FAIL when:** apply **Finding logic** with `versionStatus`: `UNSUPPORTED` (CRITICAL), `EXTENDED_SUPPORT` (HIGH), standard support ending within 90 days (HIGH), between 90 days and 6 months (MEDIUM), more than 6 months (PASS).

**Why (report line):** An unsupported or Extended Support version costs more and ends in a forced upgrade.

**Source:** [Understand the Kubernetes version lifecycle on EKS](https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html)

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
- Version exiting Standard Support in 90 days to 6 months → MEDIUM
- Version in Standard Support with >6 months remaining → PASS

**Recommendation:**
- Maintain at most N-1 minor version behind the latest Standard Support release
- Schedule upgrade BEFORE Standard Support ends to avoid Extended Support premium
- Subscribe to AWS Health Dashboard EKS notifications for version-specific events

**Fix:** not a manifest change: plan the next minor upgrade before `endOfStandardSupportDate`.

---

## Check: UPG-09 Kubernetes Release Notes Review (target version)

**Severity:** HIGH (when planning an upgrade)

**Check ID:** `UPG-09` | **Scope level:** cluster | **Applies to:** any cluster | **Evaluation:** guidance

**Evidence:**
```bash
kubent; pluto detect-helm -o wide
```

**FAIL when:** guidance only, NOT_EVALUATED unless the prompt provides `kubent` or `pluto` output; it needs the release notes fetch that non-interactive mode skips. When that output is provided, apply **Finding logic**.

**Why (report line):** Release notes list the behavior changes that no scanner detects.

**Source:** [Kubernetes Release Notes](https://kubernetes.io/releases/notes/)

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

**Fix:** not a manifest change: read the target CHANGELOG and migrate every removed API before scheduling the upgrade.
