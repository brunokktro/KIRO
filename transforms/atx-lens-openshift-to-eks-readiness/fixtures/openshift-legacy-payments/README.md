# Legacy Payments - OpenShift application (test fixture)

Fixture repository for validating `openshift-to-eks-migration-readiness`.

It is **seeded with known OpenShift constructs**, one or more per rubric question, plus
**control resources** that are already portable Kubernetes and MUST NOT be flagged.

This is the same methodology used by the `BENCHMARKS.md` of the other definitions: plant a
known set of incompatibilities, commit as a baseline, run, then assert the run found exactly
what was planted and nothing else.

Not a real application. Do not deploy to production.

## Layout

```text
manifests/
├── openshift-app.yaml           DeploymentConfig, ImageStream, Route, Service
├── openshift-build.yaml         BuildConfig (S2I strategy), Template
├── openshift-platform.yaml      SCC, ClusterResourceQuota, EgressIP, PerformanceProfile
├── openshift-network-telco.yaml SriovNetwork, NetworkAttachmentDefinition, privileged pod
├── openshift-storage.yaml       PVC with ReadWriteMany on an OpenShift StorageClass
├── openshift-operators.yaml     Subscription, CatalogSource, OperatorGroup
└── notifier.yaml        vanilla Deployment/Service/NetworkPolicy - MUST NOT flag
.s2i/assemble, .s2i/run          S2I builder contract
scripts/deploy.sh                oc CLI usage in automation
Dockerfile                       fixed USER, breaks the arbitrary-UID contract
EXPECTED-FINDINGS.md             the assertion spec
```

## How to run

```bash
atx custom def exec -n openshift-to-eks-migration-readiness -p . -x -t \
  --configuration 'additionalPlanContext=migration_target: eks-standard'
```

Then assert the output against `EXPECTED-FINDINGS.md`.

## Target variants worth running

The 7 `⚡` questions change severity with the target, so the fixture is run three times:

| Target | What must change |
|---|---|
| `eks-standard` | baseline, as written in `EXPECTED-FINDINGS.md` |
| `eks-auto-mode` | `INF-Q1`, `INF-Q6` escalate to BLOCKER; `INF-Q3` BLOCKER unconditional; `INF-Q2` escalates to RISK-SAFETY. Tier stays `Re-Platform-Required` but `blocker_count` rises. |
| `eks-hybrid` | `INF-Q3` and `INF-Q6` de-escalate; `DATA-Q1` escalates in scope. A run where nothing moves means the ⚡ resolution is not being applied. |

That third row is the real test of the `⚡` mechanism: if all three runs are identical, the
scope resolution is decorative and the marker is not doing its job.
