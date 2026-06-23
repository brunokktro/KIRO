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

### Step 0 — Documentation Freshness Check (HARD GATE)

Run BEFORE any cluster validation. This step is mandatory and non-skippable - it ensures the
checks are aligned with the latest authoritative guidance, not the snapshot baked into the
Power at write time.

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

**Output of Step 0 (always shown in report header):**

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

Ask the user:
- Is this an EKS cluster? (enables AWS-specific checks)
- Cluster name and region (if EKS)
- Which pillars to check? (all by default)

### Step 2: Execute Checks by Pillar

For each active pillar, load the corresponding steering file and execute the checks programmatically using MCP tools. Each check produces a finding.

### Step 3: Generate Report

Produce a structured report with:

```
## Summary
- Total checks: N
- CRITICAL: X | HIGH: Y | MEDIUM: Z | LOW: W | PASS: P

## Findings by Pillar

### [Pillar Name]

| # | Severity | Check | Finding | Recommendation |
|---|----------|-------|---------|----------------|
| 1 | CRITICAL | ... | ... | ... |
```

### Step 4: Prioritized Actions

End with a prioritized action list:
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

---

## Best Practices for Using This Power

- Run full health checks monthly or before major changes
- Run upgrade readiness checks before every EKS version upgrade
- Run security checks after any RBAC or network policy change
- Run cost checks quarterly for optimization planning
- Use namespace filters to scope checks to specific workloads
- Compare findings over time to track improvement

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
