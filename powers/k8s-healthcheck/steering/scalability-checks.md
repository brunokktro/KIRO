# Scalability Checks

## Overview

Scalability validation based on:
- [EKS Best Practices - Scalability](https://docs.aws.amazon.com/eks/latest/best-practices/scalability.html)
- [Kubernetes Setup Best Practices - Large Clusters](https://kubernetes.io/docs/setup/best-practices/cluster-large/)

---

## Check: API Server Load

**Severity:** HIGH (at scale)

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

---

## Check: etcd Object Count

**Severity:** MEDIUM

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

---

## Check: Node Density and Pod Limits

**Severity:** MEDIUM

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

---

## Check: Cluster Services Scaling

**Severity:** HIGH (at scale)

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

---

## Check: Workload Architectural Patterns

**Severity:** MEDIUM

**What to check:**
1. Services with > 5000 endpoints
2. Single Deployment with > 1000 replicas
3. EndpointSlices enabled

**Finding logic:**
- Service with > 1000 endpoints -> MEDIUM
- EndpointSlices not in use -> MEDIUM

---

## Check: Node Group Diversity

**Severity:** MEDIUM

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

---

## Check: Resource Quotas at Scale

**Severity:** MEDIUM

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
