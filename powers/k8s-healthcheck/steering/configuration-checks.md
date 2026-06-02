# Configuration Checks

## Overview

Configuration hygiene validation based on:
- [Kubernetes Configuration Good Practices](https://kubernetes.io/blog/2025/11/25/configuration-good-practices/)
- [Kubernetes Common Labels](https://kubernetes.io/docs/concepts/overview/working-with-objects/common-labels/)
- [Kubernetes Setup Best Practices](https://kubernetes.io/docs/setup/best-practices/)

---

## Check: Semantic Labels

**Severity:** MEDIUM

**What to check:**
1. Workloads using recommended Kubernetes labels:
   - `app.kubernetes.io/name`
   - `app.kubernetes.io/instance`
   - `app.kubernetes.io/version`
   - `app.kubernetes.io/component`
   - `app.kubernetes.io/part-of`
   - `app.kubernetes.io/managed-by`
2. Custom labels for operational purposes (team, environment)
3. Consistent labeling scheme across namespaces

**Finding logic:**
- No `app.kubernetes.io/name` label -> MEDIUM
- No version label -> LOW
- Proper semantic labels -> PASS

---

## Check: Meaningful Annotations

**Severity:** LOW

**What to check:**
1. Resources with `kubernetes.io/description` annotation
2. Contact/owner annotations for operational clarity
3. Links to runbooks or dashboards

---

## Check: Latest Stable API Versions

**Severity:** MEDIUM

**What to check:**
1. Resources using beta API versions when stable exists
2. Resources using alpha API versions in production

**Finding logic:**
- Using v1beta1 when v1 is available -> MEDIUM
- Using alpha API in production -> HIGH

---

## Check: YAML Hygiene

**Severity:** LOW

**What to check:**
1. Workloads in `default` namespace
2. Non-system pods in `kube-system`
3. Boolean values using non-standard representations

**Finding logic:**
- Workloads in `default` namespace -> MEDIUM
- Non-system pods in `kube-system` -> HIGH

---

## Check: Namespace Isolation

**Severity:** MEDIUM

**What to check:**
1. Proper namespace separation by environment/team
2. ResourceQuotas per namespace
3. LimitRanges per namespace

**Finding logic:**
- All workloads in one namespace -> HIGH
- Namespace without ResourceQuota in shared cluster -> MEDIUM
- Namespace without LimitRange -> LOW

---

## Check: Version Control and GitOps

**Severity:** MEDIUM

**What to check:**
1. Resources with management annotations (Helm, ArgoCD, Flux)
2. Resources without any management annotation (manually applied)
3. Helm releases in failed state

**Finding logic:**
- > 50% resources without management tool -> MEDIUM
- Helm releases in failed state -> HIGH
- All resources managed by GitOps -> PASS

---

## Check: ConfigMap and Secret Best Practices

**Severity:** MEDIUM

**What to check:**
1. Secrets referenced as env vars vs volumes
2. ConfigMaps with large data (> 1MB approaching etcd limit)
3. Immutable ConfigMaps/Secrets used where appropriate

**Finding logic:**
- Secrets in env vars -> MEDIUM (log exposure risk)
- ConfigMap > 500KB -> MEDIUM

---

## Check: Controller Usage (No Naked Pods)

**Severity:** HIGH

**What to check:**
1. Pods without ownerReferences (naked pods)
2. Use Deployments for stateless apps
3. Use Jobs/CronJobs for batch tasks

**Finding logic:**
- Naked pod in production -> HIGH
- Appropriate controller usage -> PASS

**Recommendation:** From K8s Configuration Good Practices:
- "A Deployment is almost always preferable to creating Pods directly"
- "A Job is perfect when you need something to run once and then stop"
