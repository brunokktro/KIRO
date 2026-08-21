---
name: openshift-to-eks-migration-readiness
description: Evaluates whether an application running on Red Hat OpenShift is ready to migrate to Amazon EKS - covering application shape, node topology, security posture, exposure and operations, and persistence
type: lens
version: 0.1.0
---

## Name

OpenShift to Amazon EKS Migration Readiness

## Objective

Evaluate whether an application currently running on Red Hat OpenShift can move to Amazon
EKS, what blocks the move, and in what order a portfolio of such applications should be
sequenced. The analysis targets the **repository** - manifests, charts, build definitions,
CI pipelines and scripts - not a live cluster.

It answers one question per application: **can this move, and if not, what has to change
first?**

This is a design-time review. It evaluates whether portability exists in code and
configuration; it does not verify runtime behaviour, performance parity, or licensing.

## Summary

This lens scans a repository to discover OpenShift-specific constructs and evaluates them
against their Amazon EKS equivalents across **38 questions in 5 sections**:

- **APP** - Application Shape and Build (9 questions)
- **INF** - Node Topology and Platform (7 questions)
- **SEC** - Security Posture and Identity (8 questions)
- **OPS** - Exposure and Operations (9 questions)
- **DATA** - Persistence (5 questions)

The output is a readiness tier plus a per-question finding set, structured so that a
portfolio aggregator can roll many applications into a sequencing decision.

## Reference Files

Load each file at the point in the flow where the step directs you to. Do not skip any.

- **`references/01-scoring-model.md`** - readiness tiers, the severity model, the
  target-resolution table that drives conditional (⚡) severities, and the display-name
  mapping. Load before assigning any severity or tier.
- **`references/02-question-bank.md`** - the authoritative catalog of all 38 questions
  (Steps 2-6), each with what to look for, its EKS equivalent, and its calibration. Load
  after Discovery.
- **`references/03-report-template.md`** - the Markdown report structure.
- **`references/04-output-contract.md`** - the machine-readable four-artifact contract.

## Entry Criteria

- The repository is accessible and readable at the specified path.
- The repository contains files relevant to analysis: Kubernetes or OpenShift manifests,
  Helm charts, Kustomize overlays, build definitions, CI/CD definitions, or scripts.
- Write permission exists to create the output artifact bundle (MD, JSON, HTML,
  `metadata.json`).
- The analysis operates in **read-only mode**. It will not modify any source file.
- Stay on the current branch. Do not create, switch or checkout any git branch.

## Implementation Steps

### Step 0: Read additionalPlanContext

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `migration_target` | enum | No | `eks-standard` | `eks-standard`, `eks-auto-mode`, `eks-hybrid`. Drives the severity of ⚡ questions. |
| `app_criticality` | enum | No | - | `P0`, `P1`, `P2`. Recorded in metadata; does not change severity. |
| `openshift_version` | string | No | auto-detected | e.g. `4.14`. Some constructs are already deprecated upstream and that changes the recommendation. |
| `context` | string | No | - | Free text describing the application. Used to frame findings. |
| `tags` | string[] | No | - | Recorded in metadata. |

### Step 1: Discovery

Scan the whole repository. Build an inventory of:

1. **OpenShift API groups** - any manifest whose `apiVersion` matches
   `*.openshift.io`, `apps.openshift.io`, `build.openshift.io`, `image.openshift.io`,
   `route.openshift.io`, `security.openshift.io`, `machineconfiguration.openshift.io`,
   `operator.openshift.io`, `quota.openshift.io`, `template.openshift.io`,
   `k8s.cni.cncf.io`, `performance.openshift.io`, `tuned.openshift.io`.
2. **Vanilla Kubernetes manifests** - Deployment, Service, Ingress, ConfigMap, Secret, PVC,
   StatefulSet, HPA, NetworkPolicy, ServiceAccount, Role/RoleBinding.
3. **Packaging** - Helm charts (`Chart.yaml`, `templates/`), Kustomize (`kustomization.yaml`),
   OpenShift `Template` objects.
4. **Automation** - CI definitions (`.gitlab-ci.yml`, `.github/workflows/`, `Jenkinsfile`,
   Tekton `Pipeline`/`Task`), and any script invoking `oc `.
5. **Container build inputs** - `Dockerfile`, `Containerfile`, S2I assemble/run scripts,
   `.s2i/` directory.
6. **Notable absences** - no NetworkPolicy, no probes, no resource requests. Absence is
   evidence and must cite where you looked.

Record a `portability_ratio`: OpenShift-specific manifests over total manifests. A repository
that is already mostly vanilla Kubernetes scores differently from one built on
DeploymentConfig and BuildConfig.

### Step 1.5: Resolve the migration target

Load `references/01-scoring-model.md` and resolve `migration_target`. Record the resolution
and the reasoning; every ⚡ question echoes it.

### Step 2: Evaluate APP questions

Load `references/02-question-bank.md`. Evaluate APP-Q1 through APP-Q9.

### Step 3: Evaluate INF questions

Evaluate INF-Q1 through INF-Q7.

### Step 4: Evaluate SEC questions

Evaluate SEC-Q1 through SEC-Q8.

### Step 5: Evaluate OPS questions

Evaluate OPS-Q1 through OPS-Q9.

### Step 6: Evaluate DATA questions

Evaluate DATA-Q1 through DATA-Q5.

### Step 7: Assign the readiness tier

Per `references/01-scoring-model.md`. The tier is driven by BLOCKER and RISK-SAFETY **counts
derived from the emitted findings**, never from a running tally and never from an average.

### Step 8: Emit the report bundle

Per `references/03-report-template.md` and `references/04-output-contract.md`.

## Constraints

### Read-only

Never modify a file in the repository. Never call a Kubernetes or AWS API.

**On git:** the analysis itself must not create, switch or delete a branch, and must not commit.
It writes only the four output artifacts. Note that the **AWS Transform platform** stages
results on its own branch (`atx-result-staging-<timestamp>`) and commits the artifacts there -
that is platform behaviour, not the analysis, and it is expected. The read-only contract is
verified by `git diff <baseline> HEAD -- <source paths>` returning empty: the diff must contain
**only** the four artifacts and no source file.

### Never guess a mapping

When an OpenShift construct has no EKS equivalent, report it as a finding with guidance.
Never invent an equivalent. A gap degrades to explicit guidance, never to a wrong mapping.

### Evidence is mandatory

Every finding cites `{file, lines}`. When the finding is that something is absent, cite the
file where you looked (`package.json`, `README.md`, the manifest directory).

### Coverage is exact

Every one of the 38 question ids appears in **either** `findings[]` **or** `evaluations[]`.
Never both. Never neither.

### Severity comes from the rubric

Read the severity from the question heading in `references/02-question-bank.md`. Do not
recompute it, do not transcribe it into a second place.

## Exit Criteria

1. All 38 questions evaluated; `findings[] ∪ evaluations[]` covers every id exactly once.
2. Every finding carries evidence with a file path.
3. Every ⚡ question carries its target resolution and reasoning.
4. Summary counts recomputed from `findings[]` and reconciled; a mismatch fails the analysis.
5. Readiness tier assigned per the count rules, with the driving counts stated.
6. Four artifacts written: MD, JSON, HTML, `metadata.json`.
7. Zero files in the repository modified; `git status` clean apart from the output bundle.

## Non-Goals

1. **Performing the migration.** That is the `openshift-to-eks` Custom Definition.
2. **Assessing the OpenShift cluster.** This reads a repository, not a live cluster. Cluster
   posture, operator health and node state are out of scope.
3. **Licensing or commercial analysis** of the OpenShift subscription.
4. **Cost modelling** of the target EKS environment.
5. **Runtime or performance parity.** Design-time only.
