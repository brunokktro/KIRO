# Cost Optimization Checks

## Overview

Cost optimization validation based on:
- [EKS Best Practices - Cost Optimization](https://docs.aws.amazon.com/eks/latest/best-practices/cost-opt.html)

Every check below carries a stable **Check ID**, its evidence commands, the exact FAIL condition and a fixed report line. The catalog of all IDs, the scoring formula and the report format live in `POWER.md`.

---

## Check: COST-01 Resource Right-Sizing

**Severity:** MEDIUM

**Check ID:** `COST-01` | **Scope level:** namespace | **Applies to:** EKS only | **Evaluation:** metrics

**Evidence:**
```bash
aws cloudwatch get-metric-statistics --region <region> --namespace ContainerInsights --metric-name pod_cpu_utilization_over_pod_limit --dimensions Name=ClusterName,Value=<cluster> Name=Namespace,Value=<ns> Name=PodName,Value=<pod> --statistics Average --period 3600 --start-time <now-7d> --end-time <now>
```

**FAIL when:** apply **Finding logic** on 7-day averages. Without Container Insights the check is NOT_EVALUATED (reason: no utilization metrics).

**Why (report line):** Requests far above real usage reserve capacity you pay for and never use.

**Source:** [EKS Best Practices - Compute and Autoscaling](https://docs.aws.amazon.com/eks/latest/best-practices/cost-opt-compute.html)

**What to check:**
1. Pods with CPU requests > 2x average usage over 7 days
2. Pods with memory requests > 1.5x peak usage
3. VPA recommendations available but not applied
4. Containers requesting resources but consistently idle

**How to check (EKS with Container Insights):**
```
get_cloudwatch_metrics:
  cluster_name: <cluster>
  metric_name: cpu_usage_total
  namespace: ContainerInsights
  dimensions: {ClusterName: <cluster>, Namespace: <ns>, PodName: <pod>}
  minutes: 10080  # 7 days
  stat: Average
```

Compare with:
```
kubectl_get:
  resourceType: pods
  namespace: <ns>
  output: json
```
Extract `.spec.containers[].resources.requests.cpu`

**Finding logic:**
- Request > 3x actual avg usage → HIGH (significant waste)
- Request > 2x actual avg usage → MEDIUM
- Request within 1.2-2x → PASS (healthy headroom)
- Request < actual usage → HIGH (reliability risk, covered in reliability-checks)

**Recommendation:**
- Use VPA in recommendation mode to get sizing suggestions
- Review resource utilization monthly
- Set requests based on P95 usage + 20% headroom

**Fix (YAML):**
```yaml
# Get sizing recommendations without restarting pods
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: <app>
  namespace: <ns>
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: <app>
  updatePolicy:
    updateMode: "Off"
```

---

## Check: COST-02 Idle and Abandoned Resources

**Severity:** MEDIUM

**Check ID:** `COST-02` | **Scope level:** namespace | **Applies to:** any cluster | **Evaluation:** kubectl

**Evidence:**
```bash
jq -n --argjson pvc "$(kubectl get pvc -n <ns> -o json)" --argjson pods "$(kubectl get pods -n <ns> -o json)" -r '([$pods.items[].spec.volumes[]?.persistentVolumeClaim.claimName] | unique) as $used | $pvc.items[] | select(.metadata.name as $n | $used | index($n) | not) | "PersistentVolumeClaim/\(.metadata.name)"'
kubectl get deploy -n <ns> -o json | jq -r '.items[] | select(.spec.replicas == 0) | "Deployment/\(.metadata.name) lastProgress=\([.status.conditions[]? | select(.type == "Progressing") | .lastUpdateTime][0])"'
kubectl get jobs -n <ns> -o json | jq -r '.items[] | select(.status.completionTime != null and .spec.ttlSecondsAfterFinished == null and ((.metadata.ownerReferences // []) | length == 0) and ((.status.completionTime | fromdateiso8601) < (now - 604800))) | "Job/\(.metadata.name)"'
```

**FAIL when:** apply **Finding logic**. Zero-replica age = last `Progressing` condition update older than 30 days. The zero-endpoint Service row uses the NET-05 evidence.

**Why (report line):** Idle volumes, jobs and deployments keep billing and clutter the cluster.

**Source:** [Automatic Cleanup for Finished Jobs](https://kubernetes.io/docs/concepts/workloads/controllers/ttlafterfinished/)

**What to check:**
1. Deployments scaled to 0 for > 7 days
2. PersistentVolumeClaims not mounted to any pod
3. ConfigMaps/Secrets not referenced by any workload
4. Services with no endpoints and no recent traffic
5. Completed Jobs not cleaned up (TTL not set)
6. Failed pods not automatically cleaned

**How to check:**
```
kubectl_get:
  resourceType: deployments
  allNamespaces: true
  output: json
# Filter: .spec.replicas == 0

kubectl_get:
  resourceType: persistentvolumeclaims
  allNamespaces: true
  output: json
# Cross-reference with pod volume mounts

kubectl_get:
  resourceType: jobs
  allNamespaces: true
  output: json
# Filter: .status.completionTime older than 7 days AND no ttlSecondsAfterFinished
```

**Finding logic:**
- Unattached PVC (especially GP3/io2 volumes) → MEDIUM (paying for unused storage)
- Deployment at 0 replicas > 30 days → LOW
- Completed Jobs without TTL cleanup → LOW
- Services with zero endpoints → MEDIUM

**Recommendation:**
- Set `ttlSecondsAfterFinished` on Jobs
- Use `kubectl get pvc` cross-referenced with pod mounts to find orphans
- Regularly audit zero-replica deployments

**Fix (YAML):**
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: <job>
  namespace: <ns>
spec:
  ttlSecondsAfterFinished: 86400
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: <job>
        image: <image>
```

---

## Check: COST-03 Node Instance Type Optimization

**Severity:** MEDIUM

**Check ID:** `COST-03` | **Scope level:** cluster | **Applies to:** any cluster | **Evaluation:** kubectl

**Evidence:**
```bash
kubectl get nodes -o json | jq -r '.items[] | .metadata.labels | "\(.["kubernetes.io/arch"]) \(.["node.kubernetes.io/instance-type"] // "-")"' | sort | uniq -c
```

**FAIL when:** no `arm64` node (LOW). The CPU utilization rows need Container Insights and the Spot row needs to know which workloads tolerate interruption: without that evidence they are listed under Not checked.

**Why (report line):** Graviton and right-sized instance families cut the compute bill for the same work.

**Source:** [EKS Best Practices - Compute and Autoscaling](https://docs.aws.amazon.com/eks/latest/best-practices/cost-opt-compute.html)

**What to check:**
1. Nodes consistently under 40% CPU utilization
2. Nodes consistently under 50% memory utilization
3. Mix of instance families for cost efficiency
4. Graviton (ARM) instances considered for compatible workloads
5. Spot instances used for fault-tolerant workloads

**How to check (EKS):**
```
get_cloudwatch_metrics:
  cluster_name: <cluster>
  metric_name: node_cpu_utilization
  namespace: ContainerInsights
  dimensions: {ClusterName: <cluster>, InstanceId: <id>}
  minutes: 10080
  stat: Average
```

```
kubectl_get:
  resourceType: nodes
  output: json
```
Check `node.kubernetes.io/instance-type` label.

**Finding logic:**
- Average node CPU < 30% → HIGH (significantly over-provisioned)
- Average node CPU 30-50% → MEDIUM
- No Spot instances and workloads are fault-tolerant → MEDIUM
- No Graviton instances → LOW (cost opportunity)

**Fix (YAML):**
```yaml
apiVersion: karpenter.sh/v1
kind: NodePool
metadata:
  name: default
spec:
  template:
    spec:
      requirements:
      - key: kubernetes.io/arch
        operator: In
        values: ["arm64", "amd64"]
      - key: karpenter.sh/capacity-type
        operator: In
        values: ["spot", "on-demand"]
      nodeClassRef:
        group: karpenter.k8s.aws
        kind: EC2NodeClass
        name: default
```

---

## Check: COST-04 Karpenter / Cluster Autoscaler Configuration

**Severity:** MEDIUM

**Check ID:** `COST-04` | **Scope level:** cluster | **Applies to:** any cluster | **Evaluation:** kubectl

**Evidence:**
```bash
kubectl get deploy -A -o json | jq -r '.items[] | select(.metadata.name | test("karpenter|cluster-autoscaler")) | "\(.metadata.namespace)/Deployment/\(.metadata.name) replicas=\(.spec.replicas) args=\([.spec.template.spec.containers[].args[]?] | map(select(test("scale-down-enabled"))) | join(","))"'
kubectl get nodepools.karpenter.sh -o json 2>/dev/null | jq -r '.items[] | "NodePool/\(.metadata.name) consolidationPolicy=\(.spec.disruption.consolidationPolicy // "unset") consolidateAfter=\(.spec.disruption.consolidateAfter // "unset")"'
kubectl get pods -A --field-selector=status.phase=Pending -o json | jq -r '.items[] | select(any(.status.conditions[]?; .reason == "Unschedulable")) | "\(.metadata.namespace)/Pod/\(.metadata.name)"'
aws eks describe-cluster --name <cluster> --region <region> --query 'cluster.computeConfig.enabled'
```

**FAIL when:** apply **Finding logic**. EKS Auto Mode (`computeConfig.enabled: true`) counts as an autoscaler. Karpenter without consolidation = `consolidationPolicy: WhenEmpty` or `consolidateAfter: Never`.

**Why (report line):** Without an autoscaler that consolidates, empty and half-empty nodes keep running.

**Source:** [EKS Best Practices - Karpenter](https://docs.aws.amazon.com/eks/latest/best-practices/karpenter.html)

**What to check:**
1. Autoscaler installed and healthy
2. Karpenter: consolidation policy enabled
3. Karpenter: NodePool constraints appropriate (instance families, AZs)
4. CAS: scale-down enabled, appropriate thresholds
5. Unschedulable pods due to insufficient capacity

**How to check:**
```
kubectl_get:
  resourceType: pods
  namespace: kube-system
  labelSelector: "app.kubernetes.io/name=karpenter"

kubectl_get:
  resourceType: nodepools.karpenter.sh
  output: json

kubectl_get:
  resourceType: pods
  allNamespaces: true
  fieldSelector: "status.phase=Pending"
```

**Finding logic:**
- No autoscaler installed → MEDIUM
- Karpenter without consolidation → MEDIUM (missing cost savings)
- Pending pods due to capacity → HIGH
- CAS with scale-down disabled → MEDIUM

**Recommendation:**
- Enable Karpenter consolidation (`consolidationPolicy: WhenEmptyOrUnderutilized`)
- Use diverse instance types for better Spot availability
- Set appropriate TTL for empty nodes

**Fix (YAML):**
```yaml
apiVersion: karpenter.sh/v1
kind: NodePool
metadata:
  name: default
spec:
  disruption:
    consolidationPolicy: WhenEmptyOrUnderutilized
    consolidateAfter: 1m
```

---

## Check: COST-05 Namespace-Level Cost Allocation

**Severity:** LOW

**Check ID:** `COST-05` | **Scope level:** namespace | **Applies to:** any cluster | **Evaluation:** kubectl

**Evidence:**
```bash
kubectl get namespace <ns> -o json | jq -r '.metadata.labels | keys[]'
kubectl get resourcequotas -n <ns> -o name
```

**FAIL when:** no ResourceQuota (MEDIUM, every cluster is treated as shared unless the prompt says single-tenant); the namespace has none of the labels `team`, `owner`, `project`, `environment`, `cost-center`, `app.kubernetes.io/part-of` (LOW). The tooling row is INFO.

**Why (report line):** Without allocation labels nobody can tell which team the namespace bill belongs to.

**Source:** [EKS Best Practices - Cost Optimization](https://docs.aws.amazon.com/eks/latest/best-practices/cost-opt.html)

**What to check:**
1. ResourceQuotas defined per namespace
2. Labels for cost allocation (team, project, environment)
3. Namespace mapping to cost centers/teams
4. Kubecost or similar cost visibility tool deployed

**How to check:**
```
kubectl_get:
  resourceType: resourcequotas
  allNamespaces: true

kubectl_get:
  resourceType: namespaces
  output: json
```
Check for cost-related labels/annotations.

**Finding logic:**
- No ResourceQuotas in shared cluster → MEDIUM
- No cost allocation labels → LOW
- No cost visibility tooling → INFO

**Fix (YAML):**
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: <ns>
  labels:
    team: <team>
    environment: <env>
    cost-center: <cost-center>
```

---

## Check: COST-06 Storage Cost Optimization

**Severity:** LOW

**Check ID:** `COST-06` | **Scope level:** namespace | **Applies to:** any cluster | **Evaluation:** kubectl

**Evidence:**
```bash
kubectl get pvc -n <ns> -o json | jq -r '.items[] | "PersistentVolumeClaim/\(.metadata.name) storageClass=\(.spec.storageClassName // "default") size=\(.spec.resources.requests.storage)"'
kubectl get storageclass -o json | jq -r '.items[] | "StorageClass/\(.metadata.name) provisioner=\(.provisioner) type=\(.parameters.type // "unset")"'
```

**FAIL when:** a PVC uses a gp2 StorageClass: `ebs.csi.aws.com` with `type: gp2`, or the in-tree `kubernetes.io/aws-ebs` with `type` gp2 or unset (MEDIUM); a PVC requests more than 100Gi after converting Ti/Mi/G/T to Gi (LOW). The snapshot row is not scored.

**Why (report line):** gp3 gives more baseline performance than gp2 for a lower price per GiB.

**Source:** [EKS Best Practices - Storage](https://docs.aws.amazon.com/eks/latest/best-practices/cost-opt-storage.html)

**What to check:**
1. StorageClass using GP3 instead of GP2 (better price/performance)
2. Oversized PVCs (requested >> actual usage)
3. Snapshot lifecycle policies for EBS volumes
4. EFS vs EBS selection appropriate for access patterns

**How to check:**
```
kubectl_get:
  resourceType: storageclasses
  output: json

kubectl_get:
  resourceType: persistentvolumes
  output: json
```

**Finding logic:**
- Using GP2 StorageClass → MEDIUM (GP3 is cheaper and faster)
- PVC > 100GB without justification → LOW
- No snapshot policy → LOW

**Fix (YAML):**
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: gp3
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
```

---

## Check: COST-07 Data Transfer Costs

**Severity:** MEDIUM

**Check ID:** `COST-07` | **Scope level:** namespace | **Applies to:** any cluster | **Evaluation:** kubectl

**Evidence:**
```bash
kubectl get services -n <ns> -o json | jq -r '.items[] | select(.spec.type == "LoadBalancer" and (.spec.externalTrafficPolicy // "Cluster") == "Cluster" and ((.metadata.annotations // {})["service.beta.kubernetes.io/aws-load-balancer-nlb-target-type"] // "") != "ip") | "Service/\(.metadata.name)"'
```

**FAIL when:** a `LoadBalancer` Service keeps `externalTrafficPolicy: Cluster` and does not use NLB IP targets (LOW). The VPC endpoint, NAT and inter-region rows need VPC flow data and are listed under Not checked.

**Why (report line):** externalTrafficPolicy Cluster adds a node hop that can cross AZs and bill data transfer.

**Source:** [EKS Best Practices - Cost Optimization - Networking](https://docs.aws.amazon.com/eks/latest/best-practices/cost-opt-networking.html)

**What to check:**
1. Cross-AZ traffic patterns (pods communicating across AZs)
2. Services using `externalTrafficPolicy: Cluster` (causes extra hops)
3. NAT Gateway usage for pods needing internet (consider VPC endpoints)
4. Inter-region traffic where not needed

**How to check:**
```
kubectl_get:
  resourceType: services
  allNamespaces: true
  output: json
```
Check `externalTrafficPolicy` field.

For node distribution:
```
kubectl_get:
  resourceType: nodes
  output: json
```
Check AZ labels vs pod placement patterns.

**Recommendation:**
- Use topology-aware routing (`service.kubernetes.io/topology-mode: Auto`)
- Deploy VPC endpoints for ECR, S3, CloudWatch, STS
- Consider `externalTrafficPolicy: Local` where applicable

**Fix (YAML):**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: <svc>
  namespace: <ns>
  annotations:
    service.kubernetes.io/topology-mode: Auto
spec:
  type: LoadBalancer
  externalTrafficPolicy: Local
```

---

## Check: COST-08 EKS Extended Support Pricing Impact

**Severity:** HIGH (if cluster is in Extended Support)

**Check ID:** `COST-08` | **Scope level:** cluster | **Applies to:** EKS only | **Evaluation:** aws

**Evidence:**
```bash
aws eks describe-cluster --name <cluster> --region <region> --query 'cluster.[version, upgradePolicy.supportType]' --output text
aws eks describe-cluster-versions --region <region> --cluster-versions <version> --query 'clusterVersions[0].[versionStatus, endOfStandardSupportDate, endOfExtendedSupportDate]' --output text
```

**FAIL when:** `versionStatus` is `EXTENDED_SUPPORT` (HIGH); `STANDARD_SUPPORT` with `endOfStandardSupportDate` within 90 days of the run (MEDIUM).

**Why (report line):** Extended Support adds a per-hour control plane premium on top of the standard price.

**Source:** [EKS Extended Support](https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions-extended.html)

**What to check:**
1. Whether the cluster is in [Standard Support](https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions-standard.html) or [Extended Support](https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions-extended.html)
2. Per-cluster control-plane premium delta during Extended Support
3. Total monthly impact across the AWS account / org

**How to check:**
- Identify cluster minor: `aws eks describe-cluster --name <c> --query 'cluster.version'`
- Cross-reference with the EKS pricing page and the version matrix in the userguide URLs above
- Confirm via the [AWS Pricing Calculator](https://calculator.aws/) for current rates per region

**Finding logic:**
- Cluster in Extended Support → HIGH (notable per-hour control plane premium - quantify monthly delta and decide between immediate upgrade vs. paying)
- Cluster will enter Extended Support within 90 days → MEDIUM (plan upgrade window now)
- Cluster in Standard Support → PASS

**Recommendation:**
- Plan upgrades to avoid Extended Support unless there is a documented business reason
- If staying on Extended Support, document the business case (compatibility freeze, vendor support, etc.) and the cost delta
- Track Extended Support usage at org level via AWS Cost Explorer (filter on EKS service + cluster tag)
- Cross-reference with `upgrades-checks.md` → "EKS Version Support Lifecycle" for upgrade timing

> **Note:** Extended Support pricing can change. ALWAYS confirm the current control-plane rate via the EKS pricing page or AWS Pricing Calculator at the time of the assessment - do not rely on a static figure embedded in this document.

**Fix:** not a manifest change: upgrade the control plane one minor at a time (`aws eks update-cluster-version`), or document the business case for staying.
