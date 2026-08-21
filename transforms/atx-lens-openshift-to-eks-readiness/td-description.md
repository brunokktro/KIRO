# TD Description & Prompt for `atx -t`

## TD Name

`openshift-to-eks-migration-readiness`

## Kind

**Lens (assessment).** Read-only. Scores a repository against a rubric and emits a
report bundle. It never modifies the repository and never touches a cluster.

Paired Custom Definition (separate artifact, built after this one):
`openshift-to-eks` performs the actual transformation per application.

## TD Description (for `atx custom def publish`)

Assess whether an application currently running on Red Hat OpenShift is ready to move to
Amazon EKS. Scores OpenShift-specific constructs found in the repository - DeploymentConfig,
BuildConfig, ImageStream, Route, SecurityContextConstraints, PerformanceProfile,
SriovNetwork, Operators, ClusterResourceQuota - against their EKS equivalents, assigns a
migration readiness tier, and reports what blocks the move per application. Designed for
portfolio assessment of large OpenShift estates where the decision is which applications
can move, in what order, and what must be resolved first.

## Why a Lens and not only a transformation

A customer with a large OpenShift estate does not need a transformer first. They need to
know which applications can move, which are blocked, and what the blocker is. That is a
scored assessment, not a code change. The transformation is the second step and operates on
one application at a time; the Lens operates across the portfolio and produces the
sequencing decision.

## Rubric design decisions (locked)

### Category codes reuse the MOD vocabulary

Categories are `APP`, `DATA`, `INF`, `OPS`, `SEC` - the same five the Modernization
Readiness Analysis (MOD) uses.

This is deliberate. The reference harness parses question ids with a **closed** pattern:

```python
_QID = r"(?:API|AUTH|STATE|HITL|DATA|DISC|OBS|ENG|INF|APP|SEC|OPS)-Q\d+"
```

A new prefix (`OCP-`, `OSHIFT-`) would not parse and would require a code change in the
harness before this Lens could run at all. Reusing the MOD vocabulary means the rubric
parses with **zero harness change**, and the Lens reads as a sibling of MOD rather than a
foreign artifact. The only unavoidable harness change for any new lens is the entry in its
`SKILLS` map.

### Question ids are permanent keys

A `question_id` is a stable join key for findings, baselines and portfolio aggregation.
Never renumber to close a gap. Removals leave a hole.

### Severity lives in the question heading

```text
#### SEC-Q3: SecurityContextConstraints Dependency — BLOCKER
```

Four `#`, and the separator is an **em-dash (U+2014)**, not a hyphen. A hyphen breaks the
parser silently.

### Scope marker

`⚡` marks a question whose severity is conditional on the resolved migration target
(`eks-standard` vs `eks-auto-mode` vs `eks-hybrid`). It is load-bearing, not decoration.

## Prompt to use with `atx -t`

Use this as the initial description when creating the TD interactively:

---

I want to create a Transformation Definition that assesses whether an application running on
Red Hat OpenShift is ready to migrate to Amazon EKS. It is an **analysis only** - it must
never modify the repository and never call a cluster.

**What it should do:**

1. **Scan the repository** for OpenShift-specific artifacts: `DeploymentConfig`,
   `BuildConfig`, `ImageStream`/`ImageStreamTag`, `Route`, `SecurityContextConstraints`,
   `PerformanceProfile`, `Tuned`, `MachineConfig`/`MachineSet`, `SriovNetwork`,
   `NetworkAttachmentDefinition`, `ClusterResourceQuota`, `Template`, `EgressIP`,
   `EgressFirewall`, Operator subscriptions (`Subscription`, `CatalogSource`, OLM),
   Tekton `Pipeline`/`Task`, Knative `Service`, plus `oc`-specific CLI usage in scripts and
   CI definitions. Also detect plain Kubernetes manifests, Helm charts and Kustomize
   overlays, because a repository that is already portable scores differently.

2. **Resolve the migration target** from `additionalPlanContext` (`eks-standard`,
   `eks-auto-mode`, `eks-hybrid`), defaulting to `eks-standard` when absent. The target
   changes the severity of the node-topology and networking questions.

3. **Evaluate against a rubric** of questions across five categories:
   - `APP` - application shape and build: DeploymentConfig, BuildConfig/S2I, ImageStream,
     triggers, Templates
   - `INF` - node topology and platform: PerformanceProfile, Tuned, MachineSet, SriovNetwork,
     Multus, autoscaling
   - `SEC` - posture and identity: SCC, OAuth/identity provider, RBAC, service accounts,
     secret management
   - `OPS` - exposure and operations: Route, ingress, Operators/OLM, monitoring, logging,
     GitOps, pipelines
   - `DATA` - persistence: PVC, StorageClass, internal registry storage, stateful workloads

4. **Assign a readiness tier** for the application, driven by counts of BLOCKER and
   RISK-SAFETY findings, not by an average.

5. **Emit four artifacts**: a Markdown report, a machine-readable JSON with
   `findings[]`/`evaluations[]` (disjoint, covering every question id exactly once), an HTML
   view, and a `metadata.json`.

**Constraints:**

- Read-only. Never modify a file, never create or switch a git branch.
- Never guess an EKS equivalent. When a construct has no equivalent, say so and report it as
  a finding with guidance - never invent a mapping.
- Every finding cites evidence as a file plus line range. When the finding is that something
  is ABSENT, cite where you looked.
- Findings and evaluations are disjoint: a question produces a finding OR an evaluation,
  never both, never neither.
- Severity is read from the question heading, never transcribed or recomputed.
- Summary counts must be derived from the emitted `findings[]`, never from a running tally.

**Out of scope (Non-Goals):**

1. Performing the migration. That is `openshift-to-eks`, a separate Custom Definition.
2. Assessing the OpenShift cluster itself. This reads a repository, not a live cluster.
3. Licensing and commercial analysis of the OpenShift subscription.
4. Cost modelling of the target EKS environment.
