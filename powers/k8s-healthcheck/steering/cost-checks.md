# Cost Optimization Checks

## Overview

Cost optimization validation based on:
- [EKS Best Practices - Cost Optimization](https://docs.aws.amazon.com/eks/latest/best-practices/cost-opt.html)

---

## Check: Resource Right-Sizing

**Severity:** MEDIUM

**What to check:**
1. Pods with CPU requests > 2x average usage over 7 days
2. Pods with memory requests > 1.5x peak usage
3. VPA recommendations available but not applied

**Finding logic:**
- Request > 3x actual avg usage -> HIGH (significant waste)
- Request > 2x actual avg usage -> MEDIUM
- Request within 1.2-2x -> PASS (healthy headroom)

---

## Check: Idle and Abandoned Resources

**Severity:** MEDIUM

**What to check:**
1. Deployments scaled to 0 for > 7 days
2. PersistentVolumeClaims not mounted to any pod
3. Completed Jobs not cleaned up (TTL not set)
4. Services with no endpoints and no recent traffic

**Finding logic:**
- Unattached PVC -> MEDIUM (paying for unused storage)
- Deployment at 0 replicas > 30 days -> LOW
- Completed Jobs without TTL cleanup -> LOW

---

## Check: Node Instance Type Optimization

**Severity:** MEDIUM

**What to check:**
1. Nodes consistently under 40% CPU utilization
2. Mix of instance families for cost efficiency
3. Graviton (ARM) instances considered
4. Spot instances used for fault-tolerant workloads

**Finding logic:**
- Average node CPU < 30% -> HIGH (significantly over-provisioned)
- No Spot instances and workloads are fault-tolerant -> MEDIUM
- No Graviton instances -> LOW (cost opportunity)

---

## Check: Karpenter / Cluster Autoscaler Configuration

**Severity:** MEDIUM

**What to check:**
1. Autoscaler installed and healthy
2. Karpenter: consolidation policy enabled
3. Pending pods due to insufficient capacity

**Finding logic:**
- No autoscaler installed -> MEDIUM
- Karpenter without consolidation -> MEDIUM
- Pending pods due to capacity -> HIGH

---

## Check: Namespace-Level Cost Allocation

**Severity:** LOW

**What to check:**
1. ResourceQuotas defined per namespace
2. Labels for cost allocation (team, project, environment)
3. Kubecost or similar cost visibility tool deployed

---

## Check: Storage Cost Optimization

**Severity:** LOW

**What to check:**
1. StorageClass using GP3 instead of GP2
2. Oversized PVCs
3. Snapshot lifecycle policies for EBS volumes

**Finding logic:**
- Using GP2 StorageClass -> MEDIUM (GP3 is cheaper and faster)
- No snapshot policy -> LOW

---

## Check: Data Transfer Costs

**Severity:** MEDIUM

**What to check:**
1. Cross-AZ traffic patterns
2. Services using `externalTrafficPolicy: Cluster` (causes extra hops)
3. NAT Gateway usage for pods needing internet (consider VPC endpoints)

**Recommendation:**
- Use topology-aware routing
- Deploy VPC endpoints for ECR, S3, CloudWatch, STS
- Consider `externalTrafficPolicy: Local` where applicable
