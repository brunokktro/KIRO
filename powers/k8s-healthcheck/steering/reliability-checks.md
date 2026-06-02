# Reliability Checks

## Overview

Reliability validation based on:
- [EKS Best Practices - Reliability](https://docs.aws.amazon.com/eks/latest/best-practices/reliability.html)
- [Kubernetes Configuration Good Practices - Managing Workloads](https://kubernetes.io/blog/2025/11/25/configuration-good-practices/)
- [Kubernetes Setup Best Practices - Multiple Zones](https://kubernetes.io/docs/setup/best-practices/multiple-zones/)

---

## Check: Resource Requests and Limits

**Severity:** HIGH

**What to check:**
1. Pods without CPU/memory requests
2. Pods without memory limits
3. Pods with CPU limits set (controversial - can cause throttling)
4. Requests significantly lower than actual usage (under-provisioned)
5. Requests significantly higher than actual usage (over-provisioned)

**How to check:**
```
kubectl_get:
  resourceType: pods
  allNamespaces: true
  output: json
```
Filter: `.spec.containers[].resources.requests` == null

For utilization comparison (EKS with Container Insights):
```
get_cloudwatch_metrics:
  cluster_name: <cluster>
  metric_name: cpu_usage_total
  namespace: ContainerInsights
  dimensions: {ClusterName: <cluster>, Namespace: <ns>, PodName: <pod>}
```

**Finding logic:**
- No requests at all -> HIGH
- No memory limit -> MEDIUM
- CPU limit set -> INFO (consider removing to avoid throttling)
- Request > 2x actual usage -> MEDIUM (over-provisioned)
- Actual usage > request -> HIGH (under-provisioned, at risk of eviction)

**Recommendation:**
- Always set requests (scheduler needs them)
- Always set memory limits (OOM protection)
- Consider not setting CPU limits (avoids throttling)
- Use VPA recommendations for sizing

---

## Check: Liveness and Readiness Probes

**Severity:** HIGH

**What to check:**
1. Containers without readinessProbe
2. Containers without livenessProbe
3. Liveness and readiness probes using the same endpoint (anti-pattern)
4. Probes with overly aggressive settings (timeout < 2s, period < 5s)
5. startupProbe missing for slow-starting applications

**Finding logic:**
- No readinessProbe -> HIGH (traffic sent to unready pods)
- No livenessProbe -> MEDIUM (crashed pods not restarted)
- Same endpoint for both -> MEDIUM (liveness restarts during slow readiness)
- Missing startupProbe with initialDelaySeconds > 30s -> LOW

---

## Check: PodDisruptionBudgets (PDBs)

**Severity:** HIGH

**What to check:**
1. Deployments/StatefulSets with replicas > 1 without a PDB
2. PDBs with `maxUnavailable: 0` or `minAvailable: 100%` (blocks evictions entirely)
3. PDBs not matching any pods (selector mismatch)

**Finding logic:**
- Deployment with replicas > 1 and no PDB -> HIGH
- PDB with maxUnavailable=0 -> HIGH (blocks cluster upgrades)
- PDB selector matches zero pods -> MEDIUM (misconfigured)

---

## Check: Topology Spread and Anti-Affinity

**Severity:** MEDIUM

**What to check:**
1. Deployments with replicas > 1 without topologySpreadConstraints or podAntiAffinity
2. All replicas scheduled on the same node
3. All replicas in the same AZ

**Finding logic:**
- All replicas on same node -> HIGH
- All replicas in same AZ -> MEDIUM
- No topology constraints defined -> MEDIUM
- Proper spread across AZs -> PASS

---

## Check: Naked Pods (No Controller)

**Severity:** HIGH

**What to check:**
1. Pods without ownerReferences (not managed by Deployment, StatefulSet, DaemonSet, Job)
2. Naked pods in production namespaces

**Finding logic:**
- Naked pod in production namespace -> HIGH
- Naked pod in dev/test -> LOW
- System namespace naked pods -> INFO

---

## Check: Replica Count

**Severity:** MEDIUM

**What to check:**
1. Production Deployments with replicas = 1 (single point of failure)
2. Critical system components with insufficient replicas

---

## Check: HPA / VPA / KEDA Configuration

**Severity:** MEDIUM

**What to check:**
1. Deployments without any autoscaler
2. HPA with min = max (effectively disabled)
3. HPA targeting metrics that are not available

---

## Check: Multi-AZ Data Plane (EKS)

**Severity:** HIGH

**What to check:**
1. Nodes spread across at least 2 AZs (preferably 3)
2. PersistentVolumes bound to single AZ without topology awareness

**Finding logic:**
- All nodes in 1 AZ -> CRITICAL
- Nodes in 2 AZs -> MEDIUM (recommend 3)
- Nodes in 3+ AZs -> PASS

---

## Check: Graceful Shutdown

**Severity:** MEDIUM

**What to check:**
1. Pods without `terminationGracePeriodSeconds` customization
2. PreStop hooks for graceful connection draining

**Recommendation:** Add preStop hook for load-balanced services:
```yaml
lifecycle:
  preStop:
    exec:
      command: ["sleep", "5"]
```
