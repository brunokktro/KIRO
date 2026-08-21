# Scoring Model

> Loaded before any severity or tier is assigned.

---

## The portable-construct rule (read before evaluating anything)

Many questions name a construct in their "look for" list that **exists identically on both
platforms**: `HorizontalPodAutoscaler`, `Namespace`, `NetworkPolicy`, `Secret`, `StatefulSet`,
`nodeSelector`, `tolerations`, `Role`/`RoleBinding`, readiness and liveness probes. They are
listed because they carry context, not because their presence is a problem.

**Finding a portable construct is not a gap.** A finding requires one of:

1. an **OpenShift-specific object** (`*.openshift.io`, `k8s.ovn.org`, `k8s.cni.cncf.io`,
   `operators.coreos.com`, `sriovnetwork.openshift.io`), or
2. an **OpenShift-specific attribute** on a portable object (an OpenShift-only
   `storageClassName`, a `node-role.kubernetes.io/infra` selector, an OpenShift
   service-serving-cert annotation), or
3. an **absence** that matters on EKS (no NetworkPolicy on a workload with a network surface,
   no probes on a workload whose rollout behaviour changes), or
4. a **portable object whose semantics change on EKS** (a `StatefulSet` whose EBS volume
   becomes zonal, an RWX PVC that EBS cannot satisfy).

If none of the four applies, the question resolves as an **evaluation**, not a finding.

This rule exists because it was violated in practice, repeatedly and inconsistently: a plain
`autoscaling/v2` HPA in a fully portable workload was reported as an `INF-Q5` finding, and a
plain `Namespace` reference as an `OPS-Q9` finding - both citing the control resource, which is
the file that proves portability. Different runs of the identical fixture resolved these
differently, which is the signature of an ambiguous rubric rather than a model problem.

**Corollary for the control case:** a repository region that is already idiomatic Kubernetes
should produce **zero** findings. If a portable, well-formed workload attracts findings, the
question is over-broad and the rubric is wrong, not the workload.

---

## Severity model

Three unified severities, with RISK split into two sub-tiers. This mirrors the ARA model so
that a portfolio aggregator can consume this lens side-by-side with ARA and MOD.

| Native severity | Meaning | Unified display | Feeds tier arithmetic |
|---|---|---|---|
| `BLOCKER` | The application cannot run on EKS until this is resolved. The construct has no EKS equivalent, or the workload depends on a platform capability EKS does not provide the same way. | High | **yes** (`blocker_count`) |
| `RISK-SAFETY` | The application will start on EKS but a security, availability or data-integrity property is silently lost. | High | **yes** (`risk_safety_count`) |
| `RISK-QUALITY` | Migration is possible; effort, operability or maintainability degrades. | Medium | no |
| `INFO` | Observation worth recording. No action required to migrate. | Low | no |

`safety_impact` is `true` for every `RISK-SAFETY` finding and for any `BLOCKER` that is a
security or data hazard rather than a pure compatibility gap.

---

## The `⚡` scope marker

`⚡` marks a question whose severity depends on the resolved `migration_target`. There are
**7** of them: `INF-Q1`, `INF-Q2`, `INF-Q3`, `INF-Q6`, `DATA-Q1`, and (conditionally on
hybrid) `SEC-Q2`, `OPS-Q3`.

The marker is load-bearing. It tells a downstream check that a downgrade on that question is
a **correct scope resolution**, not an understatement. Do not add, remove or move it casually.

### Target resolution table

| `migration_target` | What it means | Effect on ⚡ questions |
|---|---|---|
| `eks-standard` | Managed node groups or self-managed nodes, full control of the node. | Baseline severity as written in the heading. |
| `eks-auto-mode` | EKS Auto Mode manages nodes; node-level customisation is not available. | Node-level questions (`INF-Q1`, `INF-Q2`, `INF-Q6`) **escalate** one level, because the customisation the workload relies on cannot be reproduced. `INF-Q3` (SR-IOV/Multus) escalates to BLOCKER unconditionally. |
| `eks-hybrid` | EKS Hybrid Nodes, on-premises or edge. | `INF-Q3` and `INF-Q6` **de-escalate** one level (the node is yours, so SR-IOV and CPU pinning remain available). `DATA-Q1` escalates (EBS/EFS are not present on-premises). `SEC-Q2` and `OPS-Q3` are evaluated as written. |

Every ⚡ finding MUST carry `target_resolution`, `migration_target` and
`resolution_reasoning`. A ⚡ question evaluated without those three is an incomplete finding.

---

## Readiness tiers

The tier is a **function of counts**, not of an average. Averages hide a single blocking
construct behind a lot of green.

| Tier | Rule | What it tells the portfolio owner |
|---|---|---|
| **Migration-Ready** | `blocker_count == 0` and `risk_safety_count <= 2` | Move it. Remaining items are handled during the migration. |
| **Migration-Ready (Conditional)** | `blocker_count == 0` and `risk_safety_count >= 3` | Move it, but the safety items are a pre-condition, not a follow-up. |
| **Refactor-Required** | `1 <= blocker_count <= 3` | Application-level work first. Typically DeploymentConfig, Route and SCC. Predictable, bounded. |
| **Re-Platform-Required** | `blocker_count >= 4` | The application is built on OpenShift platform capabilities. Treat as re-platform, not migration, and sequence it late. |

### Count reconciliation (mandatory)

`blocker_count` and `risk_safety_count` are **recomputed from the emitted `findings[]`** at
report time and compared against the summary block. A mismatch fails the analysis and names
the offending `question_id`. No exclusion rule may lower a counter below the number of
enumerated findings carrying that severity.

This invariant exists because the equivalent bug shipped in MOD: a summary authored separately
from `findings[]` drifted, and the header a customer reads disagreed with the findings the
report emitted.

---

## Category display names

| Code | Display name |
|---|---|
| `APP` | Application Shape & Build |
| `INF` | Node Topology & Platform |
| `SEC` | Security Posture & Identity |
| `OPS` | Exposure & Operations |
| `DATA` | Persistence |

---

## Priority mapping

Priority is derived from severity and category, and is what orders the remediation list.

| Native severity | Priority |
|---|---|
| `BLOCKER` | `P0` |
| `RISK-SAFETY` | `P1` |
| `RISK-QUALITY` | `P2` |
| `INFO` | `P3` |

---

## Portability ratio

Recorded in metadata, never scored directly:

```text
portability_ratio = (manifests with no *.openshift.io apiVersion) / (total manifests)
```

It is context for the reader, not a grade. A repository at `0.95` with one
`SecurityContextConstraints` is still `Refactor-Required`, because the blocker is what
decides. Reporting the ratio as a score would be exactly the averaging mistake the tier rules
avoid.
