# Scalability Checks

## Overview

Scalability validation based on:
- [EKS Best Practices - Scalability](https://docs.aws.amazon.com/eks/latest/best-practices/scalability.html)
- [Kubernetes Setup Best Practices - Large Clusters](https://kubernetes.io/docs/setup/best-practices/cluster-large/)

Every check below carries a stable **Check ID**, its evidence commands, the exact FAIL condition and a fixed report line. The catalog of all IDs, the scoring formula and the report format live in `POWER.md`.

---

## Check: SCL-01 API Server Load

**Severity:** HIGH (at scale)

**Check ID:** `SCL-01` | **Scope level:** cluster | **Applies to:** any cluster | **Evaluation:** metrics

**Evidence:**
```bash
kubectl get --raw /metrics | grep '^apiserver_request_duration_seconds_bucket'
```

**FAIL when:** apply **Finding logic** when a P99 is available from Prometheus or CloudWatch; the raw histogram has no time window, so without a metrics backend the check is NOT_EVALUATED.

**Why (report line):** A saturated API server slows every controller, deploy and autoscaling decision.

**Source:** [EKS Best Practices - Kubernetes Control Plane](https://docs.aws.amazon.com/eks/latest/best-practices/scale-control-plane.html)

**What to check:**
1. API server request latency (P99 > 1s indicates stress)
2. Number of watchers on high-cardinality resources
3. LIST calls without pagination
4. Custom controllers with aggressive reconciliation loops

**Finding logic:**
- API server P99 latency > 5s -> CRITICAL
- API server P99 latency > 1s -> HIGH
- > 1000 active watchers on single resource type -> MEDIUM
- Custom controller reconciling every < 10s -> MEDIUM

**Recommendation:**
- Use informer/watch instead of polling
- Paginate LIST calls (limit=500)
- Increase informer resync periods (5-10 min)
- Use server-side apply to reduce conflict retries

**Fix:** not a manifest change: see the Recommendation.

---

## Check: SCL-02 etcd Object Count

**Severity:** MEDIUM

**Check ID:** `SCL-02` | **Scope level:** cluster | **Applies to:** any cluster | **Evaluation:** kubectl

**Evidence:**
```bash
kubectl get --raw /metrics | grep -E '^apiserver_(resource|storage)_objects\{' | sort
kubectl get jobs -A -o json | jq '[.items[] | select(.status.completionTime != null)] | length'
```

**FAIL when:** total objects above 100K (HIGH): sum one metric family, `apiserver_resource_objects` when present, otherwise `apiserver_storage_objects`; more than 1000 completed Jobs (MEDIUM). The per-namespace row is not scored.

**Why (report line):** A large object count makes every LIST slower and grows control plane memory.

**Source:** [EKS Best Practices - Kubernetes Control Plane](https://docs.aws.amazon.com/eks/latest/best-practices/scale-control-plane.html)

**What to check:**
1. Total number of objects in etcd
2. Namespaces with excessive ConfigMaps/Secrets (> 1000)
3. Completed Jobs not cleaned up
4. Excessive Events

**Finding logic:**
- Total objects > 100K -> HIGH
- Single namespace > 5000 objects -> MEDIUM
- Uncleaned Jobs > 1000 -> MEDIUM

**Recommendation:**
- Set `ttlSecondsAfterFinished` on Jobs
- Use event expiry settings
- For EKS: AWS manages etcd but high object count still impacts performance

**Fix:** not a manifest change: add `ttlSecondsAfterFinished` to Jobs (COST-02 fix) and clean up stale objects.

---

## Check: SCL-03 Node Density and Pod Limits

**Severity:** MEDIUM

**Check ID:** `SCL-03` | **Scope level:** cluster | **Applies to:** any cluster | **Evaluation:** kubectl

**Evidence:**
```bash
kubectl get nodes -o json | jq -r '.items[] | "\(.metadata.name) allocatablePods=\(.status.allocatable.pods)"'
kubectl get pods -A --field-selector=status.phase=Running -o json | jq -r '[.items[].spec.nodeName] | group_by(.) | map("\(.[0]) runningPods=\(length)")[]'
```

**FAIL when:** apply **Finding logic** per node (node names masked). The prefix delegation row uses the NET-01 evidence and is EKS only.

**Why (report line):** A node at its pod limit cannot take the replicas that a scale-out or a drain needs.

**Source:** [EKS Best Practices - Kubernetes Data Plane](https://docs.aws.amazon.com/eks/latest/best-practices/scale-data-plane.html)

**What to check:**
1. Pods per node approaching instance limit
2. ENI/IP address limits for instance type
3. Prefix delegation enabled for high density

**Finding logic:**
- Pod count > 80% of node allocatable -> HIGH
- Pod count > 60% of node allocatable -> MEDIUM
- Prefix delegation not enabled with > 50 pods/node -> MEDIUM

**Recommendation (EKS):**
- Enable prefix delegation: `ENABLE_PREFIX_DELEGATION=true`
- Max pods formula (secondary IP mode): `(ENIs * (IPs per ENI - 1)) + 2`
- Max pods with prefix delegation: `(ENIs * ((IPs per ENI - 1) * 16)) + 2`

**Fix:** not a manifest change: enable prefix delegation (NET-01 fix) or use larger instance types.

---

## Check: SCL-04 Cluster Services Scaling

**Severity:** HIGH (at scale)

**Check ID:** `SCL-04` | **Scope level:** cluster | **Applies to:** any cluster | **Evaluation:** kubectl

**Evidence:**
```bash
kubectl get deploy -n kube-system -l k8s-app=kube-dns -o jsonpath='{range .items[*]}{.metadata.name} replicas={.spec.replicas}{"\n"}{end}'
kubectl get pods -n kube-system -l k8s-app=metrics-server -o json | jq '[.items[].status.containerStatuses[]?.lastState.terminated.reason] | map(select(. == "OOMKilled")) | length'
kubectl get deploy -A -o json | jq -r '.items[] | select(.metadata.name == "karpenter") | "\(.metadata.namespace)/Deployment/karpenter replicas=\(.spec.replicas)"'
```

**FAIL when:** apply **Finding logic** with the node count from `kubectl get nodes --no-headers | wc -l`.

**Why (report line):** Cluster services sized for a small cluster become the bottleneck as it grows.

**Source:** [EKS Best Practices - Cluster Services](https://docs.aws.amazon.com/eks/latest/best-practices/scale-cluster-services.html)

**What to check:**
1. CoreDNS scaled appropriately for cluster size
2. Metrics server resource allocation
3. Karpenter/CAS controller resources
4. Ingress controller scaled for traffic

**Scaling guidelines:**
| Component | Guideline |
|-----------|----------|
| CoreDNS | 1 replica per 50 nodes OR NodeLocal DNSCache |
| Metrics Server | Increase memory for > 100 nodes |
| Karpenter | 2 replicas (HA), increase memory for > 1000 pods |
| Ingress Controller | Scale with traffic, not node count |

**Finding logic:**
- CoreDNS with 2 replicas on > 100 node cluster -> HIGH
- Metrics server OOMKilled events -> HIGH
- Karpenter single replica -> MEDIUM

**Fix:** see the NET-03 fix for CoreDNS; run Karpenter with 2 replicas (Helm value `replicas: 2`).

---

## Check: SCL-05 Workload Architectural Patterns

**Severity:** MEDIUM

**Check ID:** `SCL-05` | **Scope level:** namespace | **Applies to:** any cluster | **Evaluation:** kubectl

**Evidence:**
```bash
kubectl get endpointslices -n <ns> -o json | jq -r '[.items[] | {svc: .metadata.labels["kubernetes.io/service-name"], n: (.endpoints // [] | length)}] | group_by(.svc) | .[] | "Service/\(.[0].svc) endpoints=\(map(.n) | add)"'
```

**FAIL when:** a Service has more than 1000 endpoints (MEDIUM). EndpointSlices are always in use on Kubernetes 1.21 or later, so that row PASSes there.

**Why (report line):** Very large Services make every endpoint update expensive for kube-proxy on every node.

**Source:** [EKS Best Practices - Workloads](https://docs.aws.amazon.com/eks/latest/best-practices/scale-workloads.html)

**What to check:**
1. Services with > 5000 endpoints
2. Single Deployment with > 1000 replicas
3. EndpointSlices enabled

**Finding logic:**
- Service with > 1000 endpoints -> MEDIUM
- EndpointSlices not in use -> MEDIUM

**Fix:** not a manifest change: split the Service or the workload.

---

## Check: SCL-06 Node Group Diversity

**Severity:** MEDIUM

**Check ID:** `SCL-06` | **Scope level:** cluster | **Applies to:** any cluster | **Evaluation:** kubectl

**Evidence:**
```bash
kubectl get nodes -o json | jq -r '.items[] | .metadata.labels | "\(.["node.kubernetes.io/instance-type"] // "-") capacity=\(.["karpenter.sh/capacity-type"] // .["eks.amazonaws.com/capacityType"] // "-") zone=\(.["topology.kubernetes.io/zone"] // "-")"' | sort | uniq -c
```

**FAIL when:** one instance type across all nodes (MEDIUM); Spot nodes present with fewer than 3 distinct instance types among them (HIGH); anything else PASSes.

**Why (report line):** Few instance types make Spot interruptions and capacity shortages hit all nodes at once.

**Source:** [EKS Best Practices - Kubernetes Data Plane](https://docs.aws.amazon.com/eks/latest/best-practices/scale-data-plane.html)

**What to check:**
1. Single instance type across all nodes
2. Insufficient instance type diversity for Spot
3. Mix of compute types (On-Demand + Spot)

**Finding logic:**
- Single instance type -> MEDIUM
- < 3 instance types with Spot -> HIGH (interruption risk)
- Good diversity (5+ types, 3 AZs) -> PASS

**Recommendation:**
- Use 5+ instance types for Spot
- Mix instance families (m5, m6i, m6g, c5, c6i)
- Spread across 3 AZs
- Use Karpenter with broad NodePool constraints

**Fix:** see the COST-03 fix: widen the NodePool requirements to 5 or more instance types.

---

## Check: SCL-07 Resource Quotas at Scale

**Severity:** MEDIUM

**Check ID:** `SCL-07` | **Scope level:** namespace | **Applies to:** any cluster | **Evaluation:** kubectl

**Evidence:**
```bash
kubectl get resourcequotas -n <ns> -o name
```

**FAIL when:** no ResourceQuota in the namespace (MEDIUM, every cluster is treated as multi-tenant unless the prompt says single-tenant). The FlowSchema row never fails.

**Why (report line):** Without quotas a runaway HPA or CronJob can consume the whole cluster.

**Source:** [Resource Quotas](https://kubernetes.io/docs/concepts/policy/resource-quotas/)

**What to check:**
1. Namespace-level ResourceQuotas prevent runaway scaling
2. API priority and fairness configuration

**Finding logic:**
- No ResourceQuotas in multi-tenant cluster -> MEDIUM
- Custom FlowSchemas for critical controllers -> PASS

**Recommendation:**
- Set ResourceQuotas per namespace
- For > 300 nodes: review APF settings
- Ensure critical controllers have dedicated FlowSchema

**Fix:** same ResourceQuota manifest as the SEC-11 fix.
