# Expected Findings - `openshift-legacy-payments`

Assertion spec for this fixture at `migration_target: eks-standard`.

A run is only correct if it satisfies **all three** buckets below. Bucket B matters as much as
bucket A: a rubric that flags everything is as useless as one that flags nothing, and the
control resources exist to catch exactly that.

---

## Expected tier

```text
blocker_count      = 9   (every BLOCKER question in the rubric is planted)
tier               = Re-Platform-Required   (rule: blocker_count >= 4)
```

If the tier comes back `Refactor-Required`, the run either missed blockers or averaged them
away. Averaging is the failure mode the tier rules exist to prevent, so a wrong tier here is a
scoring-model bug, not a detection miss.

---

## Bucket A - MUST produce a finding

Nine BLOCKERs, planted one per BLOCKER question:

| Question | Severity | Planted construct | File |
|---|---|---|---|
| APP-Q1 | BLOCKER | `DeploymentConfig` with `pre`/`post` lifecycle hooks | `openshift-app.yaml`, `openshift-network-telco.yaml` |
| APP-Q2 | BLOCKER | `BuildConfig` **sourceStrategy (S2I)** + `.s2i/assemble` and `.s2i/run` | `openshift-build.yaml`, `.s2i/` |
| APP-Q3 | BLOCKER | `image: payments-api:latest` resolving via `ImageStreamTag`, no registry host | `openshift-app.yaml` |
| INF-Q3 | BLOCKER ⚡ | `SriovNetwork`, `SriovNetworkNodePolicy`, `NetworkAttachmentDefinition` | `openshift-network-telco.yaml` |
| SEC-Q1 | BLOCKER | `SecurityContextConstraints` + RoleBinding to a service account | `openshift-platform.yaml` |
| SEC-Q2 | BLOCKER ⚡ | `privileged: true`, `hostNetwork`, `hostPID`, `hostPath`, `SYS_ADMIN` | `openshift-network-telco.yaml` |
| OPS-Q1 | BLOCKER | `Route` with `haproxy.router.openshift.io/*` annotations | `openshift-app.yaml` |
| OPS-Q3 | BLOCKER ⚡ | `Subscription` x3, `CatalogSource`, `OperatorGroup`, plus a `KafkaTopic` CR | `openshift-operators.yaml` |
| DATA-Q1 | BLOCKER ⚡ | `storageClassName: ocs-storagecluster-cephfs` and `thin` | `openshift-storage.yaml` |

Thirteen RISK-SAFETY, planted:

| Question | Planted construct | File |
|---|---|---|
| APP-Q5 | `image-registry.openshift-image-registry.svc:5000` and `registry.access.redhat.com` base | `openshift-app.yaml`, `Dockerfile` |
| APP-Q7 | `USER 1001` + `chown -R 1001:0` - breaks the arbitrary-UID contract | `Dockerfile` |
| INF-Q1 | `PerformanceProfile` with isolated CPUs, hugepages, single-numa-node | `openshift-platform.yaml` |
| INF-Q6 | guaranteed QoS with integer CPU limit + `hugepages-2Mi` request | `openshift-app.yaml` |
| INF-Q7 | `hostNetwork: true` pod reaching cluster services | `openshift-network-telco.yaml` |
| SEC-Q6 | `QUEUE_PASSWORD` from `generate: expression` passed as a plain env value | `openshift-build.yaml` |
| SEC-Q7 | **NetworkPolicy ABSENT** for `payments-api` and `payments-hsm-bridge` | absence - cite `manifests/` |
| SEC-Q8 | `EgressIP` (partner allow-lists it) and `EgressFirewall` | `openshift-platform.yaml` |
| OPS-Q2 | `termination: reencrypt` + `service.beta.openshift.io/serving-cert-secret-name` | `openshift-app.yaml` |
| OPS-Q8 | `ClusterResourceQuota` with a label selector across namespaces | `openshift-platform.yaml` |
| DATA-Q2 | `accessModes: [ReadWriteMany]` | `openshift-storage.yaml` |
| DATA-Q3 | `StatefulSet` + `volumeClaimTemplates`, zonal-volume assumption | `openshift-storage.yaml` |
| SEC-Q5 | RBAC referencing SCC `use`, plus `oc adm policy add-scc-to-user` | `openshift-platform.yaml`, `scripts/deploy.sh` |

Plus RISK-QUALITY and INFO: `APP-Q4` (Template with `generate: expression`), `APP-Q6`
(`ImageChange` trigger), `INF-Q2` (`MachineConfig` writing sysctl to the host), `INF-Q4`
(`node-role.kubernetes.io/infra`), `OPS-Q6` (`oc` verbs), `OPS-Q7` (OpenShift Pipelines /
Tekton), `DATA-Q4` (internal registry `Config`), `APP-Q8` (**probes absent** on
`payments-api`), `APP-Q9` (portability ratio reported, not scored).

---

## Bucket B - MUST NOT produce a finding

**Every resource in `manifests/notifier.yaml`.** It is vanilla Kubernetes with
`runAsNonRoot`, dropped capabilities, `readOnlyRootFilesystem`, both probes, resource
requests, a NetworkPolicy covering ingress and egress, and an `autoscaling/v2` HPA.

A finding against anything in that file is a **false positive and a hard fail**, regardless of
how correct the rest of the run is.

These questions must land in `evaluations[]`, not `findings[]`, because the construct is
genuinely absent from the fixture:

| Question | Why it must be an evaluation |
|---|---|
| SEC-Q4 | No `OAuth`, `OAuthClient` or `oauth-proxy` sidecar anywhere |
| OPS-Q4 | No `ServiceMonitor`, `PrometheusRule` or monitoring config |
| OPS-Q5 | No `ClusterLogForwarder` or `ClusterLogging` |
| OPS-Q9 | No `Project` or `ProjectRequest` object |
| DATA-Q5 | No `Backup`, `Schedule` or `VolumeSnapshot` |
| INF-Q5 | Only a portable `autoscaling/v2` HPA; no `ClusterAutoscaler` or `MachineAutoscaler` |

Emitting a finding for any of those means the rubric is inventing a gap - the
over-escalation failure mode already filed as a bug against ARA and MOD in the reference repo.

---

## Bucket C - judgment calls

One question is deliberately ambiguous, to test that reasoning is stated rather than guessed:

**SEC-Q3 (Service Account Token and Cloud Identity).** The fixture defines service accounts
but no cloud identity mechanism and no static AWS credential. A finding ("no IRSA or Pod
Identity path defined, and the workload will need one") and an evaluation ("no cloud identity
is used, nothing to migrate") are **both defensible**. What is not acceptable is a finding
asserting a static credential that is not in the repository. Fabricating evidence fails this
question regardless of the severity chosen.

---

## Coverage invariant

```text
|findings[] ∪ evaluations[]| == 38     and     findings[] ∩ evaluations[] == ∅
```

Every question id appears exactly once. A fabricated id (`SEC-Q9`, `APP-Q10-ext`) that carries
BLOCKER or RISK-SAFETY is a hard fail, because it would feed `blocker_count` and move the tier.

## Count reconciliation

Recompute `blocker_count` and `risk_safety_count` from the emitted `findings[]` and compare
against the summary block. They must agree. This is the invariant that MOD shipped without,
where the header a customer reads disagreed with the findings the report emitted.
