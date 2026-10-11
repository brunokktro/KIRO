---
name: "k8s-healthcheck"
displayName: "Kubernetes Health Check"
description: "Comprehensive health check and best practices validation for Kubernetes clusters, with deep EKS/AWS integration. Covers security, reliability, networking, cost, scalability, upgrades, configuration hygiene, and container image build practices."
keywords: ["kubernetes", "healthcheck", "best-practices", "eks", "well-architected", "security", "reliability", "cost", "networking", "upgrades", "scalability"]
author: "Bruno Lopes"
---

# Kubernetes Health Check Power

## Overview

This Power enables comprehensive health checks and best practices validation for Kubernetes clusters. It combines two MCP servers (Kubernetes + EKS) to programmatically inspect cluster state and produce actionable findings categorized by severity.

**Scope:** Runtime cluster validation, configuration hygiene, and container image build practices.

**Applicable to:** Any Kubernetes cluster (via `kubernetes` MCP), with enhanced checks for AWS EKS clusters (via `awslabs.eks-mcp-server`).

**Power version:** 1.0.0 (printed in every report header and in the JSON companion as `power.version`).

**Based on:**
- [Kubernetes Configuration Good Practices](https://kubernetes.io/blog/2025/11/25/configuration-good-practices/)
- [Kubernetes Setup Best Practices](https://kubernetes.io/docs/setup/best-practices/)
- [Kubernetes Release Notes (CHANGELOG)](https://kubernetes.io/releases/notes/)
- [AWS Well-Architected Container Build Lens](https://docs.aws.amazon.com/wellarchitected/latest/container-build-lens/container-build-lens.html)
- [Amazon EKS Best Practices Guide](https://docs.aws.amazon.com/eks/latest/best-practices/introduction.html)
- [Amazon EKS Kubernetes versions](https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html)
- [EKS Standard Support](https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions-standard.html)
- [EKS Extended Support](https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions-extended.html)
- [EKS Kubernetes release calendar](https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-release-calendar.html)

---

## Available Steering Files

| File | Domain | Description |
|------|--------|-------------|
| `security-checks.md` | Security | Pod Security Standards, RBAC, secrets, network policies, PKI, image security |
| `reliability-checks.md` | Reliability | PDBs, probes, resource requests/limits, topology spread, multi-AZ, controllers |
| `networking-checks.md` | Networking | VPC CNI, IP management, DNS, ingress, service mesh, hostPort avoidance |
| `cost-checks.md` | Cost Optimization | Right-sizing, idle resources, Spot/Savings Plans, Karpenter consolidation |
| `upgrades-checks.md` | Upgrade Readiness | Deprecated APIs, version skew, add-on compatibility, EKS Insights, backup |
| `configuration-checks.md` | Configuration | Labels, annotations, YAML hygiene, namespace isolation, version control |
| `image-build-checks.md` | Container Images | Base images, multi-stage builds, scanning, layer optimization, signing, registry |
| `scalability-checks.md` | Scalability | API server limits, etcd object count, node density, cluster services scaling |

Every check in these files has a stable ID (`SEC-01` ... `SCL-07`), an evidence command, an exact FAIL condition and a fixed report line. The full list is the [Check Catalog](#check-catalog) below.

Maintainers: after changing any severity (catalog, `**Severity:**`, `**FAIL when:**` or `**Finding logic:**`), run `python3 tests/check_severity_consistency.py` (exit 0 = no contradiction) and `--self-test` (paired control).

---

## Available MCP Servers

### Server: `kubernetes`
General-purpose Kubernetes cluster operations via kubectl/Helm.

**Key tools for health checks:**
| Tool | Use Case |
|------|----------|
| `kubectl_get` | List resources across namespaces (pods without limits, services without selectors, etc.) |
| `kubectl_describe` | Deep inspect specific resources for misconfigurations |
| `kubectl_logs` | Check for crash loops, error patterns |
| `list_api_resources` | Discover deprecated API usage |
| `explain_resource` | Validate resource field usage |
| `kubectl_generic` | Run `kubectl top`, custom queries |
| `exec_in_pod` | Validate runtime configuration inside containers |

### Server: `awslabs.eks-mcp-server`
AWS EKS-specific operations and insights.

**Key tools for health checks:**
| Tool | Use Case |
|------|----------|
| `get_eks_insights` | Native EKS cluster insights (misconfigurations + upgrade readiness) |
| `list_k8s_resources` | List resources with EKS-aware context |
| `get_cloudwatch_metrics` | CPU/memory utilization for right-sizing |
| `get_cloudwatch_logs` | Control plane logs for error patterns |
| `get_eks_vpc_config` | VPC/subnet/route table validation |
| `get_pod_logs` | Pod-level log analysis |
| `get_k8s_events` | Event-based issue detection |
| `get_policies_for_role` | IAM role permission audit |

---

## Health Check Workflow

### Run Modes

| Mode | When | Step 0 | Step 1 | Checks run |
|------|------|--------|--------|------------|
| **Interactive** (default) | The prompt has no `Checks:` line | Runs | Asks the user | Every check of the selected pillars, in catalog order |
| **Non-interactive** | The prompt has a `Checks:` line with catalog IDs | Skipped | Skipped | Exactly the listed IDs, in the listed order |

#### Non-interactive prompt contract

Use it when several people must get the same result from the same cluster (workshops, CI, before/after
comparisons). The prompt carries one `Field: value` per line:

```text
Run the k8s-healthcheck Power in non-interactive mode.
Cluster: <cluster name>
Cluster type: EKS | Kubernetes
Region: <aws region>                 # required when Cluster type is EKS, otherwise n/a
Context: <kubectl context>
Namespace: <namespace> | all          # all = cluster scope
Checks: SEC-10, REL-01, REL-02, REL-03, CFG-01, IMG-01
Report: <name>                        # writes report-<name>.md and report-<name>.json
Baseline: report-<previous>.json | none
```

Optional fields: `Target version:` (UPG-02, UPG-04; default current minor + 1), `Environment: production | dev | test`
(default production), `Tenancy: shared | single-tenant` (default shared), `System workloads:` (extra regex for the
CFG-04 allowlist), `Accepted exceptions:` (`Kind/name` list, IMG-08), `Output dir:` (default the current directory),
`Unmask: true` (default false, see [Masking Rules](#masking-rules)).

Rules in this mode, all of them binding:

1. **Validate before touching the cluster.** A missing required field (`Cluster`, `Cluster type`, `Context`,
   `Namespace`, `Checks`, `Report`, plus `Region` for EKS), an ID that is not in the catalog, or a duplicated ID stops
   the run with one line, `HEALTHCHECK INPUT ERROR: <field>: <problem>`. Never ask a question, never guess a value.
2. **Skip Step 0 and Step 1.** The header records `Docs freshness: skipped (non-interactive mode)`.
3. **Pin the context.** Pass `--context <Context>` on every `kubectl` call (or the MCP tool's context parameter);
   never switch the current context. If neither is possible, the current context must equal `<Context>`, otherwise
   stop with an input error.
4. **Run exactly the listed IDs, in the listed order.** Load only the steering files that hold those IDs. No other
   check, no extra observation, no pillar expansion.
5. **Report every listed ID as PASS or FAIL.** NOT_EVALUATED is allowed only when the check cannot run (EKS-only check
   on a non-EKS cluster, `metrics` or `guidance` evaluation without evidence, tool or permission error), always with a
   one-line reason. A tool error never becomes PASS.
6. **Read-only.** No `apply`, no fix, no file other than the two report files.
7. **Delta.** When `Baseline` names a JSON file, compute the [Delta vs Baseline](#delta-vs-baseline) from the two JSON
   files.
8. **Last line of the chat answer**, exactly:
   `HEALTHCHECK DONE report=<name> PASS=<n> FAIL=<n> NOT_EVALUATED=<n> score=<overall>`

Self-check after a run (prints one `ID STATUS` line per check, in run order):

```bash
jq -r '.checks[] | "\(.check_id) \(.status)"' report-<name>.json
```

### Step 0 - Documentation Freshness Check (HARD GATE)

Run BEFORE any cluster validation. This step is mandatory in interactive mode - it ensures the
checks are aligned with the latest authoritative guidance, not the snapshot baked into the
Power at write time. In non-interactive mode it is skipped (see Run Modes) so that every run of the
same prompt takes the same path.

For each URL in the "Based on:" section above:

1. Fetch the page (via `fetch` MCP).
2. Extract the `Last-Modified` HTTP header OR the visible "Last updated" / publication date in the document.
3. Compare against the date this Power was last updated (frontmatter or git log of `POWER.md`).
4. If ANY source is newer than the Power's last update → REPORT to the user before proceeding:
   - Which source(s) changed
   - What changed (summarize the delta if visible)
   - Recommendation to refresh the Power before relying on the findings
5. Record the freshness-check timestamp in the report header (audit trail).

**Doc set to check (cross-references all pillars):**

| Pillar | Authoritative source(s) |
|--------|------------------------|
| Security | EKS Best Practices Guide; Kubernetes Configuration Good Practices |
| Reliability | EKS Best Practices Guide; Kubernetes Configuration Good Practices |
| Networking | EKS Best Practices Guide |
| Cost | EKS Best Practices Guide; EKS Standard/Extended Support pricing pages |
| Upgrades | EKS Kubernetes versions; EKS release calendar; K8s CHANGELOG (target version) |
| Configuration | Kubernetes Configuration Good Practices |
| Image Build | AWS Well-Architected Container Build Lens |
| Scalability | Kubernetes Setup Best Practices; EKS Best Practices Guide |

**Output of Step 0 (shown in the report header of interactive runs):**

```
## Documentation Freshness Check

Performed at: <ISO timestamp>
Power version baseline: <date>

| Source | Last updated | Status |
|--------|-------------|--------|
| EKS Kubernetes versions | 2026-MM-DD | aligned |
| K8s CHANGELOG (target) | 2026-MM-DD | NEWER - review |
| ... | | |
```

If everything is aligned → proceed to Step 1.
If anything changed → ask user: "Proceed with current Power baseline, or pause to refresh?"

---

### Step 1: Determine Cluster Type

Ask the user (interactive mode only; non-interactive mode takes the answers from the prompt fields):
- Is this an EKS cluster? (enables AWS-specific checks)
- Cluster name and region (if EKS)
- Which pillars to check? (all by default)
- Scope: one namespace, or all namespaces (cluster scope)
- Report name, and the previous report JSON to compare against, if any

### Step 2: Execute Checks by Pillar

For each active pillar, load the corresponding steering file and execute the checks programmatically using MCP tools. Each check produces a status (PASS, FAIL or NOT_EVALUATED), and a failing check produces one finding per failing resource.

These rules make two runs on the same unchanged cluster produce the same check IDs, statuses and scores:

- **Evaluate with the check's own block.** Use its **Evidence** commands and its **FAIL when** condition. Do not
  invent conditions, and do not report findings that are not catalog checks (interactive runs may list them under
  "Observations outside the catalog", never scored; non-interactive runs omit them).
- **Scope.** Namespace-scoped run: namespace-level checks evaluate objects in that namespace; cluster-level checks are
  evaluated, reported under "Cluster-level results" and not scored (`scored: false`), because they cannot be fixed
  from the namespace. Rows marked "cluster-scope runs only" are skipped and listed under "Rows not evaluated".
  Cluster-scope run (`Namespace: all`): namespace-level checks run once per non-system namespace and every check is
  scored. System namespaces: `kube-system`, `kube-public`, `kube-node-lease`.
- **Applies to / Evaluation.** An `EKS only` check on a non-EKS cluster, a `metrics` check without the metrics
  backend, and a `guidance` check without the evidence named in its block are NOT_EVALUATED with a reason.
- **Resource key.** Report the top-level owner as `Kind/name`: Pod -> ReplicaSet -> Deployment
  (`kubectl get rs <rs> -n <ns> -o jsonpath='{.metadata.ownerReferences[0].name}'`), Pod -> StatefulSet or DaemonSet,
  Pod -> Job -> CronJob. A pod without owner is `Pod/<name>`. Namespace conditions use `Namespace/<ns>`, cluster
  conditions `Cluster/<cluster>` or the cluster object (`ClusterRole/<name>`). Pod names never appear as resources
  when an owner exists, because they change on every restart.
- **One finding = one check x one resource.** Several failing rows on the same resource make one finding with the
  highest severity; the failing conditions go in its Detail.
- **Status.** A check is FAIL when it has at least one finding (check severity = highest finding severity), PASS when
  it was evaluated and has none, NOT_EVALUATED when it could not run. INFO rows never fail a check.
- **Defaults.** Environment production, tenancy shared, target version current minor + 1, unless the prompt says otherwise.
- **Read-only.** The Power never changes the cluster.
- **Order.** Checks in the order of the `Checks:` list (non-interactive) or catalog order (interactive); resources
  sorted by `Kind/name`.

### Step 3: Generate Report

Write two files next to each other: `report-<name>.md` (below) and `report-<name>.json`
([JSON Companion](#json-companion-schema)). The Markdown is rendered from the same data as the JSON, and both are
masked ([Masking Rules](#masking-rules)). Sections, in this order:

````markdown
# Kubernetes Health Check: <name>

## Run Header
| Field | Value |
|-------|-------|
| Cluster | `<cluster>` (EKS or Kubernetes) |
| Region | `<region>` or n/a |
| Context | `<context>` |
| Scope | namespace `<ns>`, or cluster (N namespaces) |
| Kubernetes version | `1.30` (server `v1.30.x`) |
| Support status | STANDARD_SUPPORT until YYYY-MM-DD, EXTENDED_SUPPORT until YYYY-MM-DD, UNSUPPORTED, or UNKNOWN (reason) |
| Power version | k8s-healthcheck 1.0.0 |
| Run timestamp | YYYY-MM-DDTHH:MM:SSZ (UTC) |
| Mode | interactive or non-interactive |
| Checks | N run: SEC-10, REL-01, ... |
| Baseline | `report-<previous>.json` or none |
| Docs freshness | aligned, N sources newer, or skipped (non-interactive mode) |
| Masking | on (account IDs, ARNs, IPs, hostnames, e-mails) or off (Unmask: true) |

## Delta vs Baseline            <- only when a baseline JSON was named
| Bucket | Count | Check IDs |
|--------|-------|-----------|
| Resolved | 3 | REL-01, REL-02, SEC-10 |
| Still open | 1 | CFG-01 (resources 4 -> 1) |
| Regressed | 0 | - |
| New | 0 | - |
| Still passing | 2 | - |
| Not comparable | 0 | - |
Total: 6 check IDs = sum of the buckets.

| Pillar | Score before | Score after | Change |
|--------|-------------|-------------|--------|
| Security | 0 | 100 | +100 |
| Overall | 31 | 81 | +50 |

## Scorecard
| Pillar | Checks evaluated | PASS | FAIL | CRITICAL | HIGH | MEDIUM | LOW | NOT_EVALUATED | Score |
|--------|------------------|------|------|----------|------|--------|-----|---------------|-------|
| Security | 3 | 1 | 2 | 0 | 0 | 2 | 0 | 0 | 28 |
| ... | | | | | | | | | |
| **Overall** | | | | | | | | | **55** |
PASS, FAIL and NOT_EVALUATED count checks; CRITICAL to LOW count failing findings (one check x one resource).
Only scored checks appear here.

## Findings
### Security
#### SEC-10 Runtime Security: FAIL (MEDIUM)
**Why:** <the check's "Why (report line)", verbatim>
| Resource | Severity | Detail |
|----------|----------|--------|
| Deployment/web | MEDIUM | missing readOnlyRootFilesystem, seccomp RuntimeDefault |
**Evidence:** `<the check's evidence command with <ns>, <cluster>, <region> filled in>`
**Fix:**
```yaml
<the check's Fix (YAML) or Recommendation YAML, with the resource name filled in>
```
(or `**Fix:** <one line>` when the check's fix is not a manifest change)
**Source:** [<title>](<url from the check's Source line>)

## Passed Checks
| ID | Pillar | Title |

## Not Checked / Out of Scope
### Cluster-level results (not scored in a namespace-scoped run)
| ID | Title | Status | Severity | Resource |
### NOT_EVALUATED
| ID | Title | Reason |
### Rows not evaluated
| ID | Row | Reason |       <- e.g. REL-01 utilization rows without Container Insights
### Excluded by scope
<count> catalog checks not run: <IDs>   <- pillars not selected, or IDs not in the Checks list
### Observations outside the catalog     <- interactive mode only, never scored

## Prioritized Actions
````

### Step 4: Prioritized Actions

End with a prioritized action list (failing checks ordered by severity, then by check ID, each line naming the ID):
1. CRITICAL items (fix immediately)
2. HIGH items (fix this sprint)
3. MEDIUM items (plan for next cycle)
4. LOW items (nice-to-have improvements)

---

## Severity Definitions

| Level | Meaning | Action |
|-------|---------|--------|
| **CRITICAL** | Active security vulnerability, data loss risk, or production outage risk | Fix immediately |
| **HIGH** | Significant best practice violation with tangible negative impact | Fix within current sprint |
| **MEDIUM** | Best practice deviation with moderate risk | Plan remediation |
| **LOW** | Minor improvement opportunity | Address when convenient |
| **PASS** | Check passed, no issue found | No action needed |
| **INFO** | Informational observation, no action required | Awareness only |

---

## Check Catalog

68 checks, one stable ID each. The ID is the key used by the scorecard, the JSON companion and the delta, so it never
changes meaning: a check that is retired keeps its ID unused, and a new check takes the next free number of its pillar.
**Default severity** is the check's `**Severity:**` line and is the weight used in the score. **Scope level**:
`namespace` checks look at objects inside a namespace, `cluster` checks at cluster-wide objects or AWS APIs.
**Evaluation**: `kubectl` and `aws` are deterministic from the cluster or the AWS API; `metrics` needs Container
Insights or Prometheus; `guidance` needs evidence kubectl cannot see and is NOT_EVALUATED without it. For a fixed check
list (non-interactive mode) prefer `kubectl` checks, plus `aws` checks when the cluster is EKS and credentials exist.

| ID | Pillar | Title | Default severity | Scope level | Applies to | Evaluation | Evidence (base command, full filter in the steering file) |
|----|--------|-------|------------------|-------------|------------|------------|------------------------------------------------------------|
| SEC-01 | Security | Pod Security Standards Enforcement | CRITICAL | namespace | any | kubectl | `kubectl get namespace <ns> -o json` |
| SEC-02 | Security | Privileged Containers | CRITICAL | namespace | any | kubectl | `kubectl get deploy,sts,ds -n <ns> -o json` |
| SEC-03 | Security | RBAC Least Privilege | HIGH | cluster | any | kubectl | `kubectl get clusterrolebindings -o json` |
| SEC-04 | Security | Secrets Management | HIGH | cluster | EKS | aws | `aws eks describe-cluster --name <cluster> --query cluster.encryptionConfig` |
| SEC-05 | Security | Network Policies | HIGH | namespace | any | kubectl | `kubectl get networkpolicies -n <ns> -o json` |
| SEC-06 | Security | Service Account Token Security | MEDIUM | namespace | any | kubectl | `kubectl get deploy,sts,ds -n <ns> -o json` |
| SEC-07 | Security | Image Security | HIGH | namespace | any | kubectl | `kubectl get deploy,sts,ds -n <ns> -o json` |
| SEC-08 | Security | Pod Identity / IRSA (EKS-specific) | HIGH | namespace | any | kubectl | `kubectl get deploy,sts,ds -n <ns> -o json` |
| SEC-09 | Security | PKI Certificates and Rotation | MEDIUM | namespace | any | kubectl | `kubectl get secrets -n <ns> --field-selector type=kubernetes.io/tls` |
| SEC-10 | Security | Runtime Security | MEDIUM | namespace | any | kubectl | `kubectl get deploy,sts,ds -n <ns> -o json` |
| SEC-11 | Security | Multi-Tenancy Isolation | MEDIUM | namespace | any | kubectl | `kubectl get resourcequotas,limitranges -n <ns> -o name` |
| REL-01 | Reliability | Resource Requests and Limits | HIGH | namespace | any | kubectl | `kubectl get deploy,sts,ds -n <ns> -o json` |
| REL-02 | Reliability | Liveness and Readiness Probes | HIGH | namespace | any | kubectl | `kubectl get deploy,sts,ds -n <ns> -o json` |
| REL-03 | Reliability | PodDisruptionBudgets (PDBs) | HIGH | namespace | any | kubectl | `kubectl get deploy,sts -n <ns> -o json` |
| REL-04 | Reliability | Topology Spread and Anti-Affinity | MEDIUM | namespace | any | kubectl | `kubectl get deploy,sts -n <ns> -o json` |
| REL-05 | Reliability | Naked Pods (No Controller) | HIGH | namespace | any | kubectl | `kubectl get pods -n <ns> -o json` |
| REL-06 | Reliability | Replica Count | MEDIUM | namespace | any | kubectl | `kubectl get deploy,sts -n <ns> -o json` |
| REL-07 | Reliability | HPA / VPA / KEDA Configuration | MEDIUM | namespace | any | kubectl | `kubectl get hpa,scaledobjects,vpa -n <ns> -o json` |
| REL-08 | Reliability | Multi-AZ Data Plane (EKS) | HIGH | cluster | any | kubectl | `kubectl get nodes -o json` |
| REL-09 | Reliability | Graceful Shutdown | MEDIUM | namespace | any | kubectl | `kubectl get deploy,sts -n <ns> -o json` |
| NET-01 | Networking | VPC CNI Configuration (EKS) | HIGH | cluster | EKS | aws | `kubectl get daemonset aws-node -n kube-system -o json` + `aws eks describe-addon-versions` |
| NET-02 | Networking | IP Address Exhaustion | CRITICAL | cluster | EKS | aws | `aws ec2 describe-subnets --subnet-ids <cluster and node subnets>` |
| NET-03 | Networking | DNS Configuration | MEDIUM | cluster | any | kubectl | `kubectl get deploy -n kube-system -l k8s-app=kube-dns` |
| NET-04 | Networking | Avoid hostPort and hostNetwork | MEDIUM | namespace | any | kubectl | `kubectl get deploy,sts,ds -n <ns> -o json` |
| NET-05 | Networking | Service Configuration | MEDIUM | namespace | any | kubectl | `kubectl get services -n <ns> -o json` |
| NET-06 | Networking | Ingress Controller Configuration | MEDIUM | namespace | any | kubectl | `kubectl get ingress -n <ns> -o json` |
| NET-07 | Networking | Security Groups for Pods (EKS) | LOW | cluster | EKS | guidance | `kubectl get securitygrouppolicies -A` |
| NET-08 | Networking | Service Mesh Health | LOW | namespace | any | kubectl | `kubectl get crd -o name` + `kubectl get peerauthentications -A` |
| COST-01 | Cost | Resource Right-Sizing | MEDIUM | namespace | EKS | metrics | `aws cloudwatch get-metric-statistics --namespace ContainerInsights` (7 days) |
| COST-02 | Cost | Idle and Abandoned Resources | MEDIUM | namespace | any | kubectl | `kubectl get pvc,pods -n <ns> -o json` |
| COST-03 | Cost | Node Instance Type Optimization | MEDIUM | cluster | any | kubectl | `kubectl get nodes -o json` |
| COST-04 | Cost | Karpenter / Cluster Autoscaler Configuration | MEDIUM | cluster | any | kubectl | `kubectl get deploy -A -o json` |
| COST-05 | Cost | Namespace-Level Cost Allocation | LOW | namespace | any | kubectl | `kubectl get namespace <ns> -o json` |
| COST-06 | Cost | Storage Cost Optimization | LOW | namespace | any | kubectl | `kubectl get pvc -n <ns> -o json` |
| COST-07 | Cost | Data Transfer Costs | MEDIUM | namespace | any | kubectl | `kubectl get services -n <ns> -o json` |
| COST-08 | Cost | EKS Extended Support Pricing Impact | HIGH | cluster | EKS | aws | `aws eks describe-cluster-versions --cluster-versions <version>` |
| UPG-01 | Upgrades | EKS Cluster Insights (EKS-Specific) | HIGH | cluster | EKS | aws | `aws eks list-insights --cluster-name <cluster>` |
| UPG-02 | Upgrades | Deprecated API Usage | CRITICAL | cluster | any | kubectl | `kubectl get --raw /metrics` |
| UPG-03 | Upgrades | Version Skew Compliance | HIGH | cluster | any | kubectl | `kubectl version -o json` + `kubectl get nodes -o json` |
| UPG-04 | Upgrades | Add-on Compatibility | HIGH | cluster | EKS | aws | `aws eks describe-addon-versions --kubernetes-version <target>` |
| UPG-05 | Upgrades | Upgrade Sequence Planning | MEDIUM | cluster | any | kubectl | `kubectl get pdb -A -o json` |
| UPG-06 | Upgrades | Webhook Compatibility | HIGH | cluster | any | kubectl | `kubectl get validatingwebhookconfigurations,mutatingwebhookconfigurations -o json` |
| UPG-07 | Upgrades | Custom Resource Definitions | MEDIUM | cluster | any | kubectl | `kubectl get crd -o json` |
| UPG-08 | Upgrades | EKS Version Support Lifecycle | HIGH | cluster | EKS | aws | `aws eks describe-cluster-versions --cluster-versions <version>` |
| UPG-09 | Upgrades | Kubernetes Release Notes Review (target version) | HIGH | cluster | any | guidance | `kubent`, `pluto detect-helm` |
| CFG-01 | Configuration | Semantic Labels | MEDIUM | namespace | any | kubectl | `kubectl get deploy,sts,ds -n <ns> -o json` |
| CFG-02 | Configuration | Meaningful Annotations | LOW | namespace | any | kubectl | `kubectl get deploy,sts,ds -n <ns> -o json` |
| CFG-03 | Configuration | Latest Stable API Versions | MEDIUM | namespace | any | kubectl | `kubectl get deploy,sts,ds,cronjob,hpa,pdb,ingress -n <ns> -o json --show-managed-fields` |
| CFG-04 | Configuration | YAML Hygiene | LOW | cluster | any | kubectl | `kubectl get deploy,sts,ds -n default -o name` (and `-n kube-system`) |
| CFG-05 | Configuration | Namespace Isolation | MEDIUM | namespace | any | kubectl | `kubectl get resourcequotas,limitranges -n <ns> -o name` |
| CFG-06 | Configuration | Version Control and GitOps | MEDIUM | namespace | any | kubectl | `kubectl get deploy,sts,ds,svc -n <ns> -o json` |
| CFG-07 | Configuration | ConfigMap and Secret Best Practices | MEDIUM | namespace | any | kubectl | `kubectl get deploy,sts,ds -n <ns> -o json` |
| CFG-08 | Configuration | Controller Usage (No Naked Pods) | HIGH | namespace | any | kubectl | `kubectl get pods -n <ns> -o json` |
| IMG-01 | Image Build | Image Tags and Immutability | HIGH | namespace | any | kubectl | `kubectl get deploy,sts,ds -n <ns> -o json` |
| IMG-02 | Image Build | Base Image Selection | MEDIUM | namespace | any | kubectl | `kubectl get deploy,sts,ds -n <ns> -o json` |
| IMG-03 | Image Build | Multi-Stage Build Indicators | LOW | namespace | any | guidance | `aws ecr describe-images` (image size) |
| IMG-04 | Image Build | Image Scanning and Vulnerabilities | HIGH | cluster | any | kubectl | `kubectl get validatingwebhookconfigurations,mutatingwebhookconfigurations -o name` |
| IMG-05 | Image Build | Registry Configuration | MEDIUM | namespace | any | kubectl | `kubectl get deploy,sts,ds -n <ns> -o json` |
| IMG-06 | Image Build | Image Signing and Provenance | LOW | cluster | any | guidance | `kubectl get validatingwebhookconfigurations,mutatingwebhookconfigurations -o name` |
| IMG-07 | Image Build | Layer Optimization | LOW | namespace | any | guidance | `docker history --no-trunc <image>` |
| IMG-08 | Image Build | Non-Root User | HIGH | namespace | any | kubectl | `kubectl get deploy,sts,ds -n <ns> -o json` |
| SCL-01 | Scalability | API Server Load | HIGH | cluster | any | metrics | `kubectl get --raw /metrics` |
| SCL-02 | Scalability | etcd Object Count | MEDIUM | cluster | any | kubectl | `kubectl get --raw /metrics` |
| SCL-03 | Scalability | Node Density and Pod Limits | MEDIUM | cluster | any | kubectl | `kubectl get nodes -o json` |
| SCL-04 | Scalability | Cluster Services Scaling | HIGH | cluster | any | kubectl | `kubectl get deploy -n kube-system -l k8s-app=kube-dns` |
| SCL-05 | Scalability | Workload Architectural Patterns | MEDIUM | namespace | any | kubectl | `kubectl get endpointslices -n <ns> -o json` |
| SCL-06 | Scalability | Node Group Diversity | MEDIUM | cluster | any | kubectl | `kubectl get nodes -o json` |
| SCL-07 | Scalability | Resource Quotas at Scale | MEDIUM | namespace | any | kubectl | `kubectl get resourcequotas -n <ns> -o name` |

### Overlapping checks

Some conditions sit in more than one pillar on purpose. Each ID is evaluated and scored in its own pillar, so the
overlap is a constant bias that does not change between runs. When you build a fixed check list, pick one ID per
condition.

| Condition | IDs |
|-----------|-----|
| `:latest` or untagged image | SEC-07, IMG-01 |
| Image from `docker.io` | SEC-07, IMG-05 |
| Container may run as root | SEC-10, IMG-08 |
| No ResourceQuota in the namespace | SEC-11, CFG-05, COST-05, SCL-07 |
| Pod without controller | REL-05, CFG-08 |
| PDB that blocks evictions | REL-03, UPG-05 |
| Cluster in Extended Support | COST-08, UPG-08 |
| Service with zero ready endpoints | NET-05, COST-02 |
| CoreDNS replica count | NET-03, SCL-04 |

---

## Scoring

The score is computed only from the check statuses and the catalog weights, so anyone can recompute it from the JSON.

| Default severity | Weight `w` |
|------------------|-----------|
| CRITICAL | 10 |
| HIGH | 5 |
| MEDIUM | 3 |
| LOW | 1 |

- **Scored set `S`:** checks with status PASS or FAIL and `scored: true`. NOT_EVALUATED checks and cluster-level
  checks of a namespace-scoped run are outside `S`.
- **Pillar score:** `score(p) = floor(100 x sum(w of PASS checks of p in S) / sum(w of all checks of p in S) + 0.5)`.
  A pillar with no check in `S` shows `n/a`.
- **Overall score:** the same formula over every check in `S` (weighted by check, not the mean of pillar scores).
- **Why the default severity and not the finding severity:** the denominator then depends only on the check list, so
  before and after scores on the same list are comparable.

Worked example: SEC-01 (CRITICAL, 10) FAIL, SEC-05 (HIGH, 5) PASS, SEC-10 (MEDIUM, 3) FAIL gives
Security = floor(100 x 5 / 18 + 0.5) = 28.

Recompute the scores from a report (prints the same numbers as the `scores` object):

```bash
jq '{"CRITICAL": 10, "HIGH": 5, "MEDIUM": 3, "LOW": 1} as $w
  | def score: (map($w[.default_severity]) | add) as $all
      | if ($all // 0) == 0 then "n/a" else (100 * ((map(select(.status == "PASS") | $w[.default_severity]) | add) // 0) / $all + 0.5 | floor) end;
    [.checks[] | select(.scored and .status != "NOT_EVALUATED")] as $s
  | ($s | group_by(.pillar) | map({key: .[0].pillar, value: score}) | from_entries) + {overall: ($s | score)}' report-<name>.json
```

---

## JSON Companion Schema

`report-<name>.json` is written next to `report-<name>.md`, with the same masking. `schema_version` changes only when
a field is removed or changes meaning.

```json
{
  "schema_version": "1.0",
  "power": {"name": "k8s-healthcheck", "version": "1.0.0"},
  "run": {"report_name": "before", "timestamp": "2026-10-11T15:20:00Z", "mode": "non-interactive",
          "docs_freshness": "skipped", "baseline": null},
  "cluster": {"name": "my-cluster", "type": "EKS", "region": "us-east-1", "context": "my-context",
              "kubernetes_version": "1.30", "server_version": "v1.30.0-eks-0000000",
              "support_status": "EXTENDED_SUPPORT", "support_ends": "2027-01-01"},
  "scope": {"level": "namespace", "namespaces": ["shop"], "check_ids": ["SEC-10", "REL-01", "SEC-04"]},
  "checks": [
    {"check_id": "SEC-10", "pillar": "Security", "title": "Runtime Security", "default_severity": "MEDIUM",
     "scope_level": "namespace", "scored": true, "status": "FAIL", "severity": "MEDIUM",
     "resources": ["Deployment/cart", "Deployment/web"], "reason": null},
    {"check_id": "REL-01", "pillar": "Reliability", "title": "Resource Requests and Limits", "default_severity": "HIGH",
     "scope_level": "namespace", "scored": true, "status": "PASS", "severity": null, "resources": [], "reason": null},
    {"check_id": "SEC-04", "pillar": "Security", "title": "Secrets Management", "default_severity": "HIGH",
     "scope_level": "cluster", "scored": false, "status": "FAIL", "severity": "LOW",
     "resources": ["Cluster/my-cluster"], "reason": null}
  ],
  "findings": [
    {"check_id": "SEC-10", "pillar": "Security", "severity": "MEDIUM", "status": "FAIL",
     "resource": "Deployment/cart", "namespace": "shop", "detail": "missing readOnlyRootFilesystem",
     "evidence": "kubectl get deploy,sts,ds -n shop -o json | jq ..."},
    {"check_id": "SEC-10", "pillar": "Security", "severity": "MEDIUM", "status": "FAIL",
     "resource": "Deployment/web", "namespace": "shop", "detail": "missing runAsNonRoot, drop ALL",
     "evidence": "kubectl get deploy,sts,ds -n shop -o json | jq ..."},
    {"check_id": "SEC-04", "pillar": "Security", "severity": "LOW", "status": "FAIL",
     "resource": "Cluster/my-cluster", "namespace": null,
     "detail": "no customer managed KMS key (default envelope encryption applies)",
     "evidence": "aws eks describe-cluster --name my-cluster --region us-east-1 --query ..."}
  ],
  "scores": {"Security": 0, "Reliability": 100, "overall": 63}
}
```

| Field | Type | Meaning |
|-------|------|---------|
| `run.mode` | `interactive` \| `non-interactive` | Run mode |
| `run.docs_freshness` | `aligned` \| `stale` \| `skipped` | Step 0 outcome |
| `run.baseline` | string \| null | Baseline JSON file name used for the delta |
| `cluster.type` | `EKS` \| `Kubernetes` | Enables EKS-only checks |
| `cluster.support_status` | `STANDARD_SUPPORT` \| `EXTENDED_SUPPORT` \| `UNSUPPORTED` \| `UNKNOWN` | From `aws eks describe-cluster-versions`; `UNKNOWN` for non-EKS clusters without the Step 0 fetch |
| `scope.level` | `namespace` \| `cluster` | Run scope |
| `scope.check_ids` | string[] | Checks run, in run order |
| `checks[].check_id` | string | Catalog ID, unique in the array |
| `checks[].pillar` | string | `Security`, `Reliability`, `Networking`, `Cost`, `Upgrades`, `Configuration`, `Image Build`, `Scalability` |
| `checks[].default_severity` | severity | Catalog weight for the score |
| `checks[].scope_level` | `namespace` \| `cluster` | From the catalog |
| `checks[].scored` | boolean | False for cluster-level checks in a namespace-scoped run |
| `checks[].status` | `PASS` \| `FAIL` \| `NOT_EVALUATED` | Check result |
| `checks[].severity` | severity \| null | Highest finding severity; null unless FAIL |
| `checks[].resources` | string[] | Failing resources as `Kind/name`, sorted |
| `checks[].reason` | string \| null | Why the check is NOT_EVALUATED |
| `findings[]` | object | One per failing check x resource: `check_id`, `pillar`, `severity`, `status` (always `FAIL`), `resource`, `namespace`, `detail`, `evidence` |
| `scores` | object | Pillar name -> 0-100 or `"n/a"`, plus `overall` |

Severity values: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`.

---

## Delta vs Baseline

When the prompt names a baseline (`Baseline: report-before.json`, or a `report-before.md` whose `.json` sits next to
it), the report opens with the delta. It is computed from `checks[]` of the two JSON files, never from the prose. No
baseline JSON = no delta section, and the header says why.

| Bucket | Baseline status | Current status |
|--------|-----------------|----------------|
| Resolved | FAIL | PASS |
| Still open | FAIL | FAIL with the same or a lower severity (show the failing resource count before -> after) |
| Regressed | PASS, or FAIL | FAIL, or FAIL with a higher severity |
| New | absent or NOT_EVALUATED | FAIL |
| Still passing | PASS | PASS (count only) |
| Not comparable | any other combination, for example current NOT_EVALUATED or the ID missing from the current run | |

The bucket counts must add up to the number of distinct check IDs in the two files; the report prints that total.
The per-pillar table shows `scores` from both files; if `scope.check_ids` differ between the runs, say so under the
table, because the scores are then computed on different check sets. Reproducible computation:

```bash
jq -n --slurpfile b report-before.json --slurpfile c report-after.json '
  {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4} as $rank
  | ($b[0].checks | map({key: .check_id, value: .}) | from_entries) as $B
  | ($c[0].checks | map({key: .check_id, value: .}) | from_entries) as $C
  | [($B, $C) | keys[]] | unique
  | map(. as $id | ($B[$id].status // "ABSENT") as $bs | ($C[$id].status // "ABSENT") as $cs
      | {id: $id, bucket: (
          if $bs == "FAIL" and $cs == "PASS" then "Resolved"
          elif $bs == "FAIL" and $cs == "FAIL" then (if $rank[$C[$id].severity] > $rank[$B[$id].severity] then "Regressed" else "Still open" end)
          elif $bs == "PASS" and $cs == "FAIL" then "Regressed"
          elif $cs == "FAIL" then "New"
          elif $bs == "PASS" and $cs == "PASS" then "Still passing"
          else "Not comparable" end)})
  | {total: length, buckets: (group_by(.bucket) | map({bucket: .[0].bucket, count: length, ids: map(.id)}))}'
```

---

## Masking Rules

On by default in the Markdown and the JSON, including any command output quoted in the report. `Unmask: true` in the
prompt turns off rules 1 to 5; rule 6 always applies.

1. AWS account IDs (12 digits) -> `<account-id>`.
2. ARNs keep partition, service, region and resource type; the account becomes `<account-id>` and the resource name
   `<masked>` (`arn:aws:iam::<account-id>:role/<masked>`).
3. IP addresses and CIDR blocks -> `<ip>`. Node names that embed an IP (`ip-10-0-1-23.ec2.internal`) become
   `node-<zone>-<n>`: nodes sorted by name and numbered per zone from 1, so the same cluster gives the same aliases in
   every run.
4. API server endpoints and AWS hostnames -> `<endpoint>`; ECR registry hosts -> `<ecr>`.
5. E-mail addresses -> `<email>`.
6. Secret values, tokens, private keys and kubeconfig content are never read into the report and never printed.

Cluster, namespace, context and workload names are not masked: the reader needs them to act.

---

## Quick Start Examples

### Full Health Check (EKS)
```
"Run a full health check on my EKS cluster 'production' in us-east-1"
```

### Security-Only Check
```
"Check security best practices on my current Kubernetes context"
```

### Upgrade Readiness
```
"Is my EKS cluster 'staging' ready to upgrade from 1.29 to 1.30?"
```

### Cost Optimization Scan
```
"Find idle resources and right-sizing opportunities in namespace 'production'"
```

### Configuration Hygiene
```
"Validate YAML and labeling best practices across all namespaces"
```

### Fixed Check List, Before and After a Fix (non-interactive)
```text
Run the k8s-healthcheck Power in non-interactive mode.
Cluster: my-cluster
Cluster type: EKS
Region: us-east-1
Context: my-context
Namespace: shop
Checks: SEC-10, REL-01, REL-02, REL-03, REL-06, CFG-01, IMG-01, SEC-04
Report: after
Baseline: report-before.json
```
Run it first with `Report: before` and `Baseline: none`, apply the fixes, then run it again as above: the "after"
report opens with the delta computed from the two JSON files.

---

## Best Practices for Using This Power

- Run full health checks monthly or before major changes
- Run upgrade readiness checks before every EKS version upgrade
- Run security checks after any RBAC or network policy change
- Run cost checks quarterly for optimization planning
- Use namespace filters to scope checks to specific workloads
- Compare findings over time to track improvement (name the previous `report-<name>.json` as `Baseline`: the delta is computed by check ID)
- Use the non-interactive mode with a fixed `Checks:` list when several people or pipelines must get the same result

---

## Tools Reference (Cross-Pillar)

These kubectl patterns are used across multiple checks:

```bash
# Pods without resource requests
kubectl_get: pods, allNamespaces=true, output="json"
# Filter: .spec.containers[].resources.requests == null

# Pods without probes
kubectl_get: pods, allNamespaces=true, output="json"
# Filter: .spec.containers[].livenessProbe == null OR readinessProbe == null

# Naked pods (not managed by a controller)
kubectl_get: pods, allNamespaces=true, output="json"
# Filter: .metadata.ownerReferences == null

# Services without selectors
kubectl_get: services, allNamespaces=true, output="json"
# Filter: .spec.selector == null

# PodDisruptionBudgets coverage
kubectl_get: poddisruptionbudgets, allNamespaces=true

# NetworkPolicies per namespace
kubectl_get: networkpolicies, allNamespaces=true

# Deprecated API detection
list_api_resources (cross-reference with workload apiVersion fields)
```

---

## Limitations

- Image build checks are documentation-based guidance (cannot scan images at runtime without additional tooling)
- Cost checks require CloudWatch Container Insights enabled for metric-based analysis
- Some scalability thresholds are approximate and depend on instance types and workload patterns
- Network policy checks verify existence, not correctness of rules
- PKI certificate expiry checks require exec access to nodes or control plane logs
- Checks with Evaluation `metrics` or `guidance` report NOT_EVALUATED when their evidence is unavailable; they never PASS by default
- The evidence commands in the steering files use `jq`; when the MCP tools are used instead, the same filter is applied to their JSON output

---

## Version History

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2026-10-11 | Stable check IDs and catalog, report header with masking, scorecard with a documented 0-100 score, finding format with evidence/fix/source, JSON companion, delta vs baseline, Not checked section, non-interactive mode |
