# Reliability Checks

## Overview

Reliability validation based on:
- [EKS Best Practices - Reliability](https://docs.aws.amazon.com/eks/latest/best-practices/reliability.html)
- [Kubernetes Configuration Good Practices - Managing Workloads](https://kubernetes.io/blog/2025/11/25/configuration-good-practices/)
- [Kubernetes Setup Best Practices - Multiple Zones](https://kubernetes.io/docs/setup/best-practices/multiple-zones/)

Every check below carries a stable **Check ID**, its evidence commands, the exact FAIL condition and a fixed report line. The catalog of all IDs, the scoring formula and the report format live in `POWER.md`.

---

## Check: REL-01 Resource Requests and Limits

**Severity:** HIGH

**Check ID:** `REL-01` | **Scope level:** namespace | **Applies to:** any cluster | **Evaluation:** kubectl

**Evidence:**
```bash
kubectl get deploy,sts,ds -n <ns> -o json | jq -r '.items[] | . as $w | .spec.template.spec.containers[] | select(.resources.requests == null or .resources.limits.memory == null) | "\($w.kind)/\($w.metadata.name) container=\(.name) requests=\(.resources.requests // {} | tojson) memoryLimit=\(.resources.limits.memory // "none")"'
```

**FAIL when:** the first two **Finding logic** rows (no requests = HIGH, no memory limit = MEDIUM). A CPU limit is INFO and never fails the check. The utilization rows need Container Insights; without it they are listed under Not checked.

**Why (report line):** Without requests the scheduler packs pods blindly and the kubelet evicts them first under pressure.

**Source:** [Resource Management for Pods and Containers](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/)

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

**Fix (YAML):**
```yaml
resources:
  requests:
    cpu: 250m
    memory: 256Mi
  limits:
    memory: 512Mi
```

---

## Check: REL-02 Liveness and Readiness Probes

**Severity:** HIGH

**Check ID:** `REL-02` | **Scope level:** namespace | **Applies to:** any cluster | **Evaluation:** kubectl

**Evidence:**
```bash
kubectl get deploy,sts,ds -n <ns> -o json | jq -r '.items[] | . as $w | .spec.template.spec.containers[] | "\($w.kind)/\($w.metadata.name) container=\(.name) readiness=\(.readinessProbe != null) liveness=\(.livenessProbe != null) startup=\(.startupProbe != null) sameEndpoint=\(.readinessProbe.httpGet != null and .readinessProbe.httpGet == .livenessProbe.httpGet)"'
```

**FAIL when:** apply **Finding logic**. Same endpoint = identical `httpGet` (path and port) on readiness and liveness.

**Why (report line):** Without a readiness probe the Service sends traffic to pods that cannot answer yet.

**Source:** [Configure Liveness, Readiness and Startup Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)

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

**Fix (YAML):**
```yaml
readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  periodSeconds: 10
  timeoutSeconds: 2
livenessProbe:
  httpGet:
    path: /healthz
    port: 8080
  periodSeconds: 10
  timeoutSeconds: 2
startupProbe:
  httpGet:
    path: /healthz
    port: 8080
  periodSeconds: 5
  failureThreshold: 30
```

---

## Check: REL-03 PodDisruptionBudgets (PDBs)

**Severity:** HIGH

**Check ID:** `REL-03` | **Scope level:** namespace | **Applies to:** any cluster | **Evaluation:** kubectl

**Evidence:**
```bash
kubectl get deploy,sts -n <ns> -o json | jq -r '.items[] | select(.spec.replicas > 1) | "\(.kind)/\(.metadata.name) podLabels=\(.spec.template.metadata.labels | tojson)"'
kubectl get pdb -n <ns> -o json | jq -r '.items[] | "PodDisruptionBudget/\(.metadata.name) selector=\(.spec.selector.matchLabels | tojson) minAvailable=\(.spec.minAvailable // "-") maxUnavailable=\(.spec.maxUnavailable // "-") expectedPods=\(.status.expectedPods)"'
```

**FAIL when:** apply **Finding logic**. A PDB covers a workload when every key/value of its `matchLabels` is in the workload pod template labels. A workload with replicas = 1 passes this check (REL-06 scores it).

**Why (report line):** Without a PDB a node drain or upgrade can evict every replica at the same time.

**Source:** [Specifying a Disruption Budget for your Application](https://kubernetes.io/docs/tasks/run-application/configure-pdb/)

**What to check:**
1. Deployments/StatefulSets with replicas > 1 without a PDB
2. PDBs with `maxUnavailable: 0` or `minAvailable: 100%` (blocks evictions entirely)
3. PDBs not matching any pods (selector mismatch)

**Finding logic:**
- Deployment with replicas > 1 and no PDB -> HIGH
- PDB with maxUnavailable=0 -> HIGH (blocks cluster upgrades)
- PDB selector matches zero pods -> MEDIUM (misconfigured)

**Fix (YAML):**
```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: <app>
  namespace: <ns>
spec:
  maxUnavailable: 1
  selector:
    matchLabels:
      app.kubernetes.io/name: <app>
```

---

## Check: REL-04 Topology Spread and Anti-Affinity

**Severity:** MEDIUM

**Check ID:** `REL-04` | **Scope level:** namespace | **Applies to:** any cluster | **Evaluation:** kubectl

**Evidence:**
```bash
kubectl get deploy,sts -n <ns> -o json | jq -r '.items[] | select(.spec.replicas > 1) | "\(.kind)/\(.metadata.name) spread=\(.spec.template.spec.topologySpreadConstraints != null) antiAffinity=\(.spec.template.spec.affinity.podAntiAffinity != null)"'
kubectl get pods -n <ns> -o json | jq -r '.items[] | "\(.metadata.ownerReferences[0].name // .metadata.name) node=\(.spec.nodeName)"'
kubectl get nodes -o json | jq -r '.items[] | "\(.metadata.name) zone=\(.metadata.labels["topology.kubernetes.io/zone"] // "none")"'
```

**FAIL when:** apply **Finding logic** to workloads with replicas > 1. Node names are masked in the report.

**Why (report line):** Replicas packed on one node or one AZ fail together.

**Source:** [Pod Topology Spread Constraints](https://kubernetes.io/docs/concepts/scheduling-eviction/topology-spread-constraints/)

**What to check:**
1. Deployments with replicas > 1 without topologySpreadConstraints or podAntiAffinity
2. All replicas scheduled on the same node
3. All replicas in the same AZ

**Finding logic:**
- All replicas on same node -> HIGH
- All replicas in same AZ -> MEDIUM
- No topology constraints defined -> MEDIUM
- Proper spread across AZs -> PASS

**Fix (YAML):**
```yaml
spec:
  template:
    spec:
      topologySpreadConstraints:
      - maxSkew: 1
        topologyKey: topology.kubernetes.io/zone
        whenUnsatisfiable: ScheduleAnyway
        labelSelector:
          matchLabels:
            app.kubernetes.io/name: <app>
      - maxSkew: 1
        topologyKey: kubernetes.io/hostname
        whenUnsatisfiable: ScheduleAnyway
        labelSelector:
          matchLabels:
            app.kubernetes.io/name: <app>
```

---

## Check: REL-05 Naked Pods (No Controller)

**Severity:** HIGH

**Check ID:** `REL-05` | **Scope level:** namespace | **Applies to:** any cluster | **Evaluation:** kubectl

**Evidence:**
```bash
kubectl get pods -n <ns> -o json | jq -r '.items[] | select((.metadata.ownerReferences // []) | length == 0) | "Pod/\(.metadata.name)"'
```

**FAIL when:** apply **Finding logic**. A namespace is production unless the prompt names it as dev or test.

**Why (report line):** A pod without a controller is not recreated when its node fails.

**Source:** [Pods - Working with Pods](https://kubernetes.io/docs/concepts/workloads/pods/)

**What to check:**
1. Pods without ownerReferences (not managed by Deployment, StatefulSet, DaemonSet, Job)
2. Naked pods in production namespaces

**Finding logic:**
- Naked pod in production namespace -> HIGH
- Naked pod in dev/test -> LOW
- System namespace naked pods -> INFO

**Fix (YAML):**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: <app>
  namespace: <ns>
spec:
  replicas: 2
  selector:
    matchLabels:
      app.kubernetes.io/name: <app>
  template:
    metadata:
      labels:
        app.kubernetes.io/name: <app>
    spec:
      containers:
      - name: <app>
        image: <image>
```

---

## Check: REL-06 Replica Count

**Severity:** MEDIUM

**Check ID:** `REL-06` | **Scope level:** namespace | **Applies to:** any cluster | **Evaluation:** kubectl

**Evidence:**
```bash
kubectl get deploy,sts -n <ns> -o json | jq -r '.items[] | select(.spec.replicas == 1) | "\(.kind)/\(.metadata.name)"'
kubectl get hpa -n <ns> -o json | jq -r '.items[] | "\(.spec.scaleTargetRef.kind)/\(.spec.scaleTargetRef.name) minReplicas=\(.spec.minReplicas // 1)"'
```

**FAIL when:** a Deployment or StatefulSet runs `replicas: 1` and no HPA targeting it has `minReplicas` >= 2 (MEDIUM).

**Why (report line):** A single replica is a single point of failure for every restart, drain or crash.

**Source:** [EKS Best Practices - Running highly-available applications](https://docs.aws.amazon.com/eks/latest/best-practices/application.html)

**What to check:**
1. Production Deployments with replicas = 1 (single point of failure)
2. Critical system components with insufficient replicas

**Fix (YAML):**
```yaml
spec:
  replicas: 2   # pair it with a PodDisruptionBudget (REL-03)
```

---

## Check: REL-07 HPA / VPA / KEDA Configuration

**Severity:** MEDIUM

**Check ID:** `REL-07` | **Scope level:** namespace | **Applies to:** any cluster | **Evaluation:** kubectl

**Evidence:**
```bash
kubectl get hpa -n <ns> -o json | jq -r '.items[] | "\(.spec.scaleTargetRef.kind)/\(.spec.scaleTargetRef.name) min=\(.spec.minReplicas // 1) max=\(.spec.maxReplicas) scalingActive=\([.status.conditions[]? | select(.type == "ScalingActive") | .status][0] // "unknown")"'
kubectl get scaledobjects.keda.sh,verticalpodautoscalers.autoscaling.k8s.io -n <ns> -o name 2>/dev/null
```

**FAIL when:** a Deployment or StatefulSet with replicas > 0 has no HPA, KEDA ScaledObject or VPA targeting it (MEDIUM); an HPA has `minReplicas` = `maxReplicas` (MEDIUM); an HPA reports `ScalingActive=False` (MEDIUM). Missing KEDA or VPA CRDs count as no object.

**Why (report line):** Without an autoscaler the workload cannot follow load, so it is either over-provisioned or saturated.

**Source:** [Horizontal Pod Autoscaling](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)

**What to check:**
1. Deployments without any autoscaler
2. HPA with min = max (effectively disabled)
3. HPA targeting metrics that are not available

**Fix (YAML):**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: <app>
  namespace: <ns>
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: <app>
  minReplicas: 2
  maxReplicas: 6
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

---

## Check: REL-08 Multi-AZ Data Plane (EKS)

**Severity:** HIGH

**Check ID:** `REL-08` | **Scope level:** cluster | **Applies to:** any cluster | **Evaluation:** kubectl

**Evidence:**
```bash
kubectl get nodes -o json | jq -r '.items[].metadata.labels["topology.kubernetes.io/zone"] // "none"' | sort | uniq -c
```

**FAIL when:** apply **Finding logic** to the number of distinct zones. The PersistentVolume row is not scored.

**Why (report line):** Nodes in a single AZ turn one AZ event into a full outage.

**Source:** [EKS Best Practices - Reliability](https://docs.aws.amazon.com/eks/latest/best-practices/reliability.html)

**What to check:**
1. Nodes spread across at least 2 AZs (preferably 3)
2. PersistentVolumes bound to single AZ without topology awareness

**Finding logic:**
- All nodes in 1 AZ -> CRITICAL
- Nodes in 2 AZs -> MEDIUM (recommend 3)
- Nodes in 3+ AZs -> PASS

**Fix (YAML):**
```yaml
# eksctl ClusterConfig (Karpenter: list three zones in the NodePool topology.kubernetes.io/zone requirement)
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig
metadata:
  name: <cluster>
  region: <region>
managedNodeGroups:
- name: <nodegroup>
  availabilityZones: ["<region>a", "<region>b", "<region>c"]
```

---

## Check: REL-09 Graceful Shutdown

**Severity:** MEDIUM

**Check ID:** `REL-09` | **Scope level:** namespace | **Applies to:** any cluster | **Evaluation:** kubectl

**Evidence:**
```bash
kubectl get deploy,sts -n <ns> -o json | jq -r '.items[] | select(all(.spec.template.spec.containers[]; .lifecycle.preStop == null)) | "\(.kind)/\(.metadata.name)"'
```

**FAIL when:** no container of a Deployment or StatefulSet defines `lifecycle.preStop` (MEDIUM). A custom `terminationGracePeriodSeconds` alone does not fail.

**Why (report line):** Without a preStop pause, pods are killed while the load balancer still sends them requests.

**Source:** [Container Lifecycle Hooks](https://kubernetes.io/docs/concepts/containers/container-lifecycle-hooks/)

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
