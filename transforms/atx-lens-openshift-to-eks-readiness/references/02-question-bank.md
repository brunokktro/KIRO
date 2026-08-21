# Question Bank

> Loaded after Discovery. The authoritative catalog of all 38 questions.
>
> **Heading format is load-bearing:** four `#`, then `<ID>: <title>`, then an
> **em-dash (U+2014)** before the severity. A hyphen breaks the parser silently.
> `⚡` marks a question whose severity depends on the resolved `migration_target`.

---

## Section APP - Application Shape & Build (Step 2)

#### APP-Q1: DeploymentConfig Usage — BLOCKER

**Look for:** `apiVersion: apps.openshift.io/v1`, `kind: DeploymentConfig`; `oc rollout`
against a `dc/`; `triggers` blocks with `ImageChange` or `ConfigChange`.

**EKS equivalent:** `apps/v1 Deployment`. There is none for `DeploymentConfig` itself.

**Why BLOCKER:** the object does not exist outside OpenShift, so nothing deploys until it is
converted. Conversion is mechanical for the pod template but **not** for the parts that have
no counterpart: `ImageChange` triggers (see APP-Q6), and `pre`/`mid`/`post` lifecycle hooks,
which have to become init containers, Jobs or a pipeline step.

**Calibration:** deprecated upstream since OpenShift 4.14 in favour of `Deployment`. If
`openshift_version >= 4.14` and the repository still uses it, say so - the customer is
already on a deprecated path and the migration removes debt rather than adding it.

#### APP-Q2: BuildConfig and Source-to-Image Pipeline — BLOCKER

**Look for:** `kind: BuildConfig`, `strategy.sourceStrategy`/`dockerStrategy`, `.s2i/`,
`assemble`/`run` scripts, `oc start-build`.

**EKS equivalent:** none in-cluster by default. The build moves out to CodeBuild, GitHub
Actions or GitLab CI, or stays in-cluster with Kaniko, BuildKit or Cloud Native Buildpacks.

**Why BLOCKER:** the application cannot produce an image on EKS until a build path exists.
This is the single most under-estimated item in an OpenShift migration, because on OpenShift
the build is part of the platform and invisible in the application repo.

**Calibration:** S2I is materially harder than `dockerStrategy`. A `dockerStrategy` build is a
`Dockerfile` and ports directly. An S2I build depends on a builder image contract
(`assemble`/`run`) that has to be reproduced explicitly, usually as a multi-stage
`Dockerfile`. Report which strategy is in use; do not collapse them.

#### APP-Q3: ImageStream and ImageStreamTag References — BLOCKER

**Look for:** `kind: ImageStream`, `kind: ImageStreamTag`, `from.kind: ImageStreamTag`,
image references shaped `<namespace>/<name>:<tag>` with no registry host.

**EKS equivalent:** Amazon ECR with explicit image URIs. There is no equivalent for the
indirection layer.

**Why BLOCKER:** ImageStream is an indirection between a symbolic tag and a concrete digest.
Manifests that reference an `ImageStreamTag` carry no resolvable registry host, so they cannot
pull on EKS. Every reference has to become a fully qualified URI.

**Calibration:** loss of the indirection also removes the automatic re-deploy on tag change.
Where that behaviour is relied on, pair this finding with APP-Q6.

#### APP-Q4: OpenShift Template Usage — RISK-QUALITY

**Look for:** `kind: Template`, `objects:` with `parameters:`, `oc process`.

**EKS equivalent:** Helm chart or Kustomize overlay.

**Why RISK-QUALITY:** parameterisation is a solved problem with a direct target, so migration
is possible. What degrades is effort: the parameter substitution model differs (Template
substitutes strings before apply; Helm templates at render time), so defaults, required
parameters and generated values (`generate: expression`) need explicit re-modelling.

#### APP-Q5: Image Registry Reference Portability — RISK-SAFETY

**Look for:** `image-registry.openshift-image-registry.svc`, `docker-registry.default.svc`,
`registry.redhat.io`, `registry.access.redhat.com`, any hard-coded cluster-internal registry
host.

**EKS equivalent:** ECR, or a mirrored upstream registry.

**Why RISK-SAFETY:** two distinct hazards, not just effort. An internal registry host does not
resolve on EKS, so the pod fails to pull at runtime rather than at apply time. And
`registry.redhat.io` images require a pull secret tied to the Red Hat subscription, which may
not survive the migration - that is an availability and a licensing surprise discovered in
production.

#### APP-Q6: Deployment Trigger Semantics — RISK-QUALITY

**Look for:** `triggers` with `type: ImageChange` or `type: ConfigChange` on a
`DeploymentConfig`; reliance on automatic rollout when a tag moves.

**EKS equivalent:** none built in. The behaviour is reproduced by a GitOps controller
(ArgoCD image updater, Flux image automation) or by a CI step that patches the digest.

**Why RISK-QUALITY:** the workload still runs after conversion; what is lost is the automatic
rollout. If it is not replaced, deployments silently stop happening on image push, which is a
process regression rather than an outage.

#### APP-Q7: Container Image UID and Non-Root Assumptions — RISK-SAFETY

**Look for:** `USER` directives in the Dockerfile, `runAsUser` in the pod spec, images that
write to paths owned by a fixed UID, `fsGroup` usage, assumptions of an arbitrary assigned UID.

**EKS equivalent:** the pod spec's `securityContext`, plus Pod Security Admission.

**Why RISK-SAFETY:** OpenShift assigns an **arbitrary UID per namespace** via SCC, so
compliant images are built to run as any UID with group-writable paths. On EKS nothing assigns
a UID, so an image that relied on that behaviour may run as root without anyone noticing -
posture silently weakens. The reverse also bites: an image hardened for the arbitrary-UID
contract may fail to write its own data directory when it suddenly runs as a fixed UID.

#### APP-Q8: Health Probe Definition — INFO

**Look for:** `readinessProbe`, `livenessProbe`, `startupProbe` in the pod template.

**EKS equivalent:** identical. Fully portable.

**Why INFO:** probes are the same API on both platforms. Recorded because their absence
matters during a migration, when rollout behaviour changes and an unprobed workload hides a
failed start.

#### APP-Q9: Portable Manifest Coverage — INFO

**Look for:** the ratio of manifests with no `*.openshift.io` `apiVersion` to total manifests
(the `portability_ratio` from Discovery).

**EKS equivalent:** not applicable.

**Why INFO:** context for the reader, never a grade. A repository at `0.95` with a single
`SecurityContextConstraints` is still `Refactor-Required`, because the blocker decides the
tier. Report the number and the constructs behind it; do not let it soften a blocker.

---

## Section INF - Node Topology & Platform (Step 3)

#### INF-Q1: PerformanceProfile and Tuned Dependency — RISK-SAFETY ⚡

**Look for:** `kind: PerformanceProfile`, `kind: Tuned`, `apiVersion: performance.openshift.io`
or `tuned.openshift.io`, references to reserved/isolated CPU sets, kernel argument tuning.

**EKS equivalent:** Karpenter `NodePool` plus `NodeClass` with node bootstrap
(`userData`/Bottlerocket settings) for kernel and sysctl parameters. There is no single object
that carries the whole profile.

**Why RISK-SAFETY:** the workload starts on a default node and appears healthy while the
latency or throughput guarantee it was tuned for is gone. That failure is invisible until
production load.

**⚡ Resolution:** `eks-standard` as written. `eks-auto-mode` **escalates to BLOCKER** - node
customisation is not available, so the guarantee cannot be reproduced at all.
`eks-hybrid` as written.

#### INF-Q2: MachineSet and Machine API Coupling — RISK-QUALITY ⚡

**Look for:** `kind: MachineSet`, `kind: MachineConfig`, `apiVersion:
machineconfiguration.openshift.io`, MachineConfigPool selectors, automation that scales a
MachineSet.

**EKS equivalent:** Karpenter `NodePool` or an EKS managed node group.

**Why RISK-QUALITY:** the target exists and is arguably better, so this is effort rather than
risk. `MachineConfig` that writes files or units onto the host is the part that needs care -
it becomes node bootstrap data.

**⚡ Resolution:** `eks-auto-mode` **escalates to RISK-SAFETY** (host-level config cannot be
applied). Others as written.

#### INF-Q3: SR-IOV and Multus Secondary Networks — BLOCKER ⚡

**Look for:** `kind: SriovNetwork`, `kind: SriovNetworkNodePolicy`, `kind:
NetworkAttachmentDefinition`, `k8s.v1.cni.cncf.io/networks` annotations, `apiVersion:
k8s.cni.cncf.io`.

**EKS equivalent:** Multus is supported on EKS with self-managed nodes; SR-IOV requires
instance types exposing the hardware and is not available in every configuration.

**Why BLOCKER:** a workload attached to a secondary network does not start without it. This is
the classic telco and NFV pattern and it is the item most likely to make an application
non-migratable outright.

**⚡ Resolution:** `eks-auto-mode` **BLOCKER, unconditional** (no Multus). `eks-hybrid`
**de-escalates to RISK-SAFETY** (the node is yours, so SR-IOV can be provided).
`eks-standard` as written.

#### INF-Q4: Node Selector and Taint Topology — RISK-QUALITY

**Look for:** `nodeSelector`, `tolerations`, `affinity`, `topologySpreadConstraints`, and
labels that only exist on OpenShift (`node-role.kubernetes.io/infra`,
`node-role.kubernetes.io/worker`).

**EKS equivalent:** the same API, but the label vocabulary differs. `node-role.kubernetes.io/infra`
has no EKS counterpart and must become a deliberate NodePool with matching labels and taints.

**Why RISK-QUALITY:** the manifests apply cleanly; pods then sit `Pending` because the
selector matches nothing, or schedule anywhere because the taint is gone. Both are visible
immediately, which is why this is not RISK-SAFETY.

#### INF-Q5: Autoscaling Model — RISK-QUALITY

**Look for:** `kind: ClusterAutoscaler`, `kind: MachineAutoscaler`,
`kind: VerticalPodAutoscalerController` (all `*.openshift.io`), and OpenShift-specific
autoscaling configuration.

**Do NOT treat a plain `autoscaling/v2` HorizontalPodAutoscaler as a gap.** The HPA API is
identical on EKS and is already the target state, so an HPA is **evidence of portability, not
of a problem**. Read it only as context for whether node-level autoscaling has to keep up with
pod-level scaling.

**Resolution rule, explicit because this question was ambiguous and produced inconsistent
results across runs:**

| What the repository contains | Outcome |
|---|---|
| An OpenShift autoscaler object (`ClusterAutoscaler`, `MachineAutoscaler`, `VerticalPodAutoscalerController`) | **finding**, RISK-QUALITY |
| Only a portable `autoscaling/v2` HPA, no OpenShift autoscaler | **evaluation**, `resolution: not-present`. Not a finding. |
| Neither | **evaluation**, `resolution: not-present` |

**EKS equivalent:** Karpenter for nodes; HPA unchanged for pods; VPA installed separately.

**Why RISK-QUALITY when it does fire:** node autoscaling changes model - Karpenter provisions
per-pod rather than scaling a fixed group. That is an improvement, but it changes capacity
behaviour enough to need validation. The pod-level HPA needs no work at all.

#### INF-Q6: CPU Manager, Topology Manager and HugePages — RISK-SAFETY ⚡

**Look for:** `resources.limits.hugepages-*`, guaranteed QoS pods with integer CPU limits
relying on exclusive pinning, `cpu-manager-policy: static`, `topologyManagerPolicy`.

**EKS equivalent:** kubelet configuration via node bootstrap on self-managed or managed nodes
with custom launch templates.

**Why RISK-SAFETY:** the pod schedules and runs. Without static CPU management it shares cores
and the latency guarantee is gone, silently. HugePages requests, by contrast, fail to schedule
if unavailable, which is the loud half of the same question.

**⚡ Resolution:** `eks-auto-mode` **escalates to BLOCKER**. `eks-hybrid` **de-escalates to
RISK-QUALITY**. `eks-standard` as written.

#### INF-Q7: Cluster Network Plugin Assumptions — RISK-SAFETY

**Look for:** assumptions about OVN-Kubernetes or OpenShift SDN behaviour: pod CIDR
assumptions, hard-coded pod IP ranges, reliance on the cluster network for east-west policy,
`EgressRouter`, host-network pods used to reach cluster services.

**EKS equivalent:** Amazon VPC CNI, where **pods receive routable VPC IPs**.

**Why RISK-SAFETY:** the addressing model genuinely differs. On EKS a pod IP is a VPC IP, so
anything that assumed pod addresses were private to the cluster now has a wider blast radius,
and IP exhaustion becomes a real capacity constraint rather than a theoretical one. Both are
silent until they bite.

---

## Section SEC - Security Posture & Identity (Step 4)

#### SEC-Q1: SecurityContextConstraints Dependency — BLOCKER

**Look for:** `kind: SecurityContextConstraints`, `apiVersion: security.openshift.io/v1`,
RoleBindings granting `use` on an SCC, references to `anyuid`, `privileged`, `hostaccess`,
`nonroot`.

**EKS equivalent:** **Pod Security Admission first**, for anything expressible as the
`privileged`/`baseline`/`restricted` profiles. Kyverno or OPA Gatekeeper **only** for the
custom logic PSA cannot express (per-field allow-lists, conditional rules, mutation).

**Why BLOCKER:** the object does not exist on EKS, and workloads bound to a permissive SCC
will be rejected or silently under-constrained. The migration must decide, per workload,
whether the permission was genuinely required or inherited.

**Calibration:** mapping every SCC straight to Kyverno imports a policy engine the customer
may not need. Report which SCC capabilities are actually used and split them: the PSA-covered
part, and the residue that genuinely needs an admission controller. A repository using only
`anyuid` needs PSA and nothing else.

#### SEC-Q2: Privileged and Host Namespace Requirements — BLOCKER ⚡

**Look for:** `privileged: true`, `hostNetwork`, `hostPID`, `hostIPC`, `hostPath` volumes,
`allowedCapabilities`, `SYS_ADMIN` and similar capability grants.

**EKS equivalent:** technically the same pod spec fields, but they collide with PSA and with
managed node assumptions.

**Why BLOCKER:** a privileged workload is a design decision that must be re-authorised on the
target, not carried over silently. On EKS it also constrains which node type can host it.

**⚡ Resolution:** `eks-hybrid` as written - the node is customer-managed, so the requirement
may remain legitimate; state that in the resolution. Others as written.

#### SEC-Q3: Service Account Token and Cloud Identity — RISK-SAFETY

**Look for:** `ServiceAccount` definitions, mounted token paths, long-lived AWS credentials in
Secrets or env vars, `automountServiceAccountToken`, use of the OpenShift-injected CA bundle.

**EKS equivalent:** EKS Pod Identity (preferred) or IRSA, both of which vend short-lived
credentials via OIDC.

**Why RISK-SAFETY:** the workload keeps running with whatever static credential it has, so
nothing breaks and nothing signals that the migration was the moment to remove it. A static
key that survives the move is a posture regression with no symptom.

#### SEC-Q4: OAuth and Identity Provider Integration — RISK-QUALITY

**Look for:** `kind: OAuth`, `kind: OAuthClient`, `apiVersion: config.openshift.io`,
applications relying on the OpenShift OAuth proxy sidecar (`oauth-proxy` images).

**EKS equivalent:** none built in. EKS has no integrated OAuth server. Application-level auth
moves to Cognito, an external IdP, or an equivalent proxy deployed explicitly.

**Why RISK-QUALITY:** it fails visibly and immediately at first login, so it is effort and
design rather than a silent hazard. Note that the `oauth-proxy` sidecar pattern is common and
often invisible to the application team.

#### SEC-Q5: RBAC Portability — RISK-QUALITY

**Look for:** `Role`, `ClusterRole`, `RoleBinding`, `ClusterRoleBinding`; rules referencing
OpenShift API groups; bindings to OpenShift built-in roles (`system:image-puller`,
`admin`, `edit`, `view` as OpenShift defines them).

**Also look for these, which grant authorization WITHOUT a RoleBinding object** and are the
most commonly missed form on OpenShift:

- the `users:` and `groups:` lists on a `SecurityContextConstraints` - that field **is** the
  binding; an SCC naming a service account has granted it access with no RBAC object present
- `oc adm policy add-scc-to-user` / `add-scc-to-group` / `add-role-to-user` /
  `add-cluster-role-to-user` in scripts, Makefiles, CI definitions and runbooks
- `oc policy add-role-to-user` in the same places

A repository can therefore have **zero** `RoleBinding` objects and still depend heavily on
OpenShift-specific authorization. Concluding `not-present` from the absence of RBAC objects
alone is wrong, and is the failure this list exists to prevent.

**EKS equivalent:** the same RBAC API. Rules over `*.openshift.io` groups become dead, and
OpenShift's built-in role names are not all present. Imperative `oc adm policy` grants have to
become declarative RBAC plus, where the grant was an SCC, a Pod Security Admission label or an
admission policy (see SEC-Q1).

**Why RISK-QUALITY:** dead rules are inert rather than dangerous, and missing built-ins fail
loudly on apply. The real work is mapping cluster access to IAM plus the EKS access entry
model, and re-expressing every imperative grant declaratively.

#### SEC-Q6: Secret Management — RISK-SAFETY

**Look for:** `kind: Secret` with literal values committed, `stringData` in version control,
sealed-secrets or external-secrets usage, references to a vault.

**EKS equivalent:** AWS Secrets Manager or SSM Parameter Store via the Secrets Store CSI
driver or External Secrets Operator.

**Why RISK-SAFETY:** a committed secret is already an exposure; migrating it forward preserves
the exposure while everything appears to work. The migration is the natural point to break
that, and if it is not flagged the secret is copied verbatim.

#### SEC-Q7: Network Policy Coverage — RISK-SAFETY

**Look for:** `kind: NetworkPolicy` and, importantly, its **absence** when the workload has a
network surface.

**EKS equivalent:** identical API, enforced by VPC CNI network policy or Cilium/Calico.

**Why RISK-SAFETY:** compounded by INF-Q7. On OpenShift a project often relies on the SDN plus
default-deny conventions; on EKS pods hold routable VPC IPs, so the same absence of policy is
a wider exposure than it was. Cite where you looked when reporting absence.

#### SEC-Q8: EgressIP and EgressFirewall Dependency — RISK-SAFETY

**Look for:** `kind: EgressIP`, `kind: EgressFirewall`, `kind: EgressNetworkPolicy`,
`kind: EgressRouter`.

**EKS equivalent:** deterministic egress addressing via NAT Gateway per subnet; egress
filtering via security groups, NetworkPolicy egress rules, or a firewall appliance. There is
no single object equivalent.

**Why RISK-SAFETY:** downstream systems frequently allow-list the egress IP. If the source
address changes without anyone mapping it, the application starts and then fails against a
third party - and the failure surfaces at the partner, not in the cluster.

---

## Section OPS - Exposure & Operations (Step 5)

#### OPS-Q1: Route Dependency and Exposure Model — BLOCKER

**Look for:** `kind: Route`, `apiVersion: route.openshift.io/v1`, `spec.host`,
`spec.tls.termination`, wildcard routes, `haproxy.router.openshift.io/*` annotations.

**EKS equivalent:** Gateway API (`HTTPRoute` plus a Gateway) is the modern target; an
`Ingress` with the AWS Load Balancer Controller is the direct one.

**Why BLOCKER:** nothing is reachable until the exposure is rebuilt. `Route` is the single
most common OpenShift-specific object in an application repository.

**Calibration:** the mapping is not one-to-one. Route features to check individually:
edge/passthrough/reencrypt termination (see OPS-Q2), per-route timeouts and balancing
algorithm expressed as `haproxy.*` annotations, and wildcard hosts. Report which of these are
used rather than asserting a clean conversion.

#### OPS-Q2: TLS Termination and Certificate Source — RISK-SAFETY

**Look for:** `spec.tls.termination` values, inline certificates in a Route, the
service-serving-cert annotation (`service.beta.openshift.io/serving-cert-secret-name`),
reliance on the OpenShift-managed internal CA.

**EKS equivalent:** ACM with an ALB/NLB for edge TLS, cert-manager for in-cluster
certificates. The automatic service-serving certificate has no equivalent.

**Why RISK-SAFETY:** `reencrypt` and `passthrough` preserve encryption to the pod. A careless
conversion to `edge` termination silently drops in-cluster encryption while the endpoint keeps
answering on HTTPS. Nothing fails; the property is just gone.

#### OPS-Q3: Operator and OLM Dependency — BLOCKER ⚡

**Look for:** `kind: Subscription` (`operators.coreos.com`), `kind: CatalogSource`,
`kind: OperatorGroup`, `kind: ClusterServiceVersion`, and CRs of operator-provided CRDs.

**EKS equivalent:** the Helm chart for the same operator where one exists, an EKS add-on where
AWS provides one, or OLM installed explicitly on EKS. Red Hat certified operators from
`redhat-operators` may have no non-OpenShift distribution at all.

**Why BLOCKER:** if the application's CRs depend on an operator that is not available, the
application cannot function. Availability has to be checked **per operator**, not assumed.

**Calibration:** split the inventory into three buckets and **emit one finding per bucket that
is present**, never one collapsed finding. The bucket, not the target, sets the severity, and
the severity per bucket is **fixed, not a judgement call**:

| Bucket | How to identify it | Severity | Why |
|---|---|---|---|
| `community` | community or upstream operator with a published Helm chart or an EKS add-on (Strimzi, cert-manager, Prometheus) | **RISK-QUALITY** | A supported install path exists. This is effort, not a blocker. Grading it BLOCKER is over-escalation. |
| `certified-with-upstream` | Red Hat certified operator that has a non-OpenShift upstream (`rhbk-operator` → Keycloak, `rhsso` → Keycloak) | **RISK-SAFETY** | An equivalent exists but is not the same build; feature and support parity must be validated before committing. |
| `openshift-only` | no non-OpenShift distribution exists (`openshift-pipelines-operator-rh`, `openshift-gitops-operator`, anything under `operator.openshift.io`) | **BLOCKER** | Genuinely blocking. **This is the bucket that decides the tier**, so a run that fails to emit it has under-reported the migration. |

Assign the bucket from the `Subscription`'s `name` and `source` (`community-operators` vs
`redhat-operators` vs a private `CatalogSource`), and confirm against whether a CR of that
operator's CRDs actually exists in the repository - an installed operator with no CR is a
weaker dependency than one the application consumes.

**A run that emits fewer findings than there are buckets present has failed this question.**
Emitting only `community` and `certified-with-upstream` while an `openshift-only` operator sits
in the manifests is the exact failure mode: it drops the one item that makes the application
non-migratable.

**⚡ Resolution:** all targets as written; the bucket, not the target, drives severity.

#### OPS-Q4: Monitoring Stack Coupling — RISK-QUALITY

**Look for:** `ServiceMonitor`, `PodMonitor`, `PrometheusRule`, `kind: GrafanaDashboard`,
queries against `openshift-monitoring`, `user-workload-monitoring` config.

**EKS equivalent:** Amazon Managed Service for Prometheus with ADOT, or a self-managed
Prometheus Operator, which keeps `ServiceMonitor` working unchanged.

**Why RISK-QUALITY:** the CRDs are portable if the Prometheus Operator is installed. What
degrades is the assumption that the platform provides monitoring for free - on EKS that is an
explicit component someone has to own.

#### OPS-Q5: Logging Pipeline Coupling — RISK-QUALITY

**Look for:** `kind: ClusterLogForwarder`, `kind: ClusterLogging`, assumptions about an
in-cluster Elasticsearch, Loki or Kibana provided by the platform.

**EKS equivalent:** Fluent Bit to CloudWatch Logs, OpenSearch, or a third-party sink.

**Why RISK-QUALITY:** log delivery is rebuildable and its absence is obvious. Note that
`ClusterLogForwarder` frequently encodes routing and filtering rules that are the real
content, not the transport.

#### OPS-Q6: `oc` CLI Usage in Automation — RISK-QUALITY

**Look for:** `oc ` invocations in scripts, Makefiles, CI definitions, runbooks; `oc new-app`,
`oc process`, `oc start-build`, `oc rollout`, `oc get route`, `oc login`.

**EKS equivalent:** `kubectl` for the subset that is plain Kubernetes; the OpenShift-specific
verbs have no equivalent and their intent must be re-expressed.

**Why RISK-QUALITY:** automation fails loudly and is fixed mechanically. Worth measuring
because a high count signals how deeply the delivery process is tied to the platform, which
predicts effort better than the manifest count does.

#### OPS-Q7: CI/CD Pipeline Portability — RISK-QUALITY

**Look for:** Tekton `Pipeline`/`Task`/`PipelineRun` (`tekton.dev`), OpenShift Pipelines
operator usage, `kind: Application` from an OpenShift GitOps ArgoCD, Jenkins running in-cluster
via the Jenkins template.

**EKS equivalent:** Tekton runs on EKS; ArgoCD installs by Helm; Jenkins moves out or is
re-hosted. CodePipeline and CodeBuild are the managed alternative.

**Why RISK-QUALITY:** every option exists, so this is planning and effort. Flag where the
pipeline uses OpenShift-specific steps (`buildconfig` triggers, `oc` tasks from the Tekton
catalog) since those carry APP-Q2's problem into the pipeline layer.

#### OPS-Q8: ClusterResourceQuota Dependency — RISK-SAFETY

**Look for:** `kind: ClusterResourceQuota` (`quota.openshift.io`), quota applied by project
selector or annotation across multiple namespaces.

**EKS equivalent:** **no single native object.** Kubernetes `ResourceQuota` is namespaced
only. There are four candidate approaches and they are **not interchangeable** - rank them by
whether they preserve the actual CRQ semantics, which is a *shared aggregate ceiling across a
set of namespaces selected by label*:

| Approach | Preserves a shared aggregate ceiling? | Notes |
|---|---|---|
| **vCluster** (virtual clusters) | **yes** - closest equivalent | A hard tenant boundary; the vcluster's host-side footprint is what gets capped. Heaviest change to the operating model. |
| **Policy engine** (Kyverno, OPA Gatekeeper) | **yes, if the policy computes the aggregate** | The pattern most customers land on. The engine must sum current usage across the selected namespaces at admission, which is real work and has a race window under concurrent creates. |
| **Per-namespace `ResourceQuota` kept in sync by tooling** | **no** | The pragmatic default and usually what ships. Produces a *sum of per-namespace maximums*, not a shared pool: every namespace can reach its own limit simultaneously and exceed what the CRQ allowed. **State this gap explicitly** rather than presenting it as equivalent. |
| **AAQ** (`kubevirt/application-aware-quota`) | **no - does not apply** | Verified against its `v1alpha1` API: it defines only `ApplicationAwareResourceQuota`, which is **namespaced**; there is no cluster-scoped type. AAQ solves a different problem - making quota *accounting* extensible for pods an operator creates as an implementation detail, using scheduling gates instead of admission. Name it only to rule it out. |

**Why RISK-SAFETY:** the manifests apply and every namespace works, but the aggregate ceiling
that protected the cluster is gone. Nothing reports it, and the first symptom is one tenant
consuming the capacity of all of them. The per-namespace workaround is especially dangerous
here precisely *because* it looks like a faithful conversion.

**Calibration:** report which approach the target environment already has available (is there
a policy engine installed? is vCluster in play?) before recommending one. Recommending a
policy engine to a customer who has none imports a new platform component, which is a
different decision from writing quotas.

#### OPS-Q9: Project versus Namespace Provisioning — INFO

**Look for:** `kind: Project`, `kind: ProjectRequest`, project templates, self-service project
creation assumptions.

**EKS equivalent:** `Namespace`, provisioned by whatever platform tooling the customer adopts.

**A plain `Namespace`, or a `namespace:` field on any resource, is NOT a finding.** Namespaces
are identical on both platforms. Only the OpenShift `Project`/`ProjectRequest` objects and the
self-service project-creation machinery count. See the portable-construct rule in
`01-scoring-model.md`.

| What the repository contains | Outcome |
|---|---|
| `kind: Project`, `kind: ProjectRequest`, or a project template | **finding**, INFO |
| Only plain `Namespace` objects or `namespace:` fields | **evaluation**, `not-present` |
| Neither | **evaluation**, `not-present` |

**Why INFO when it does fire:** a Project is a Namespace with defaults attached. The conversion
is trivial; the defaults (quota, limit range, network policy, role bindings) are the substance,
and they are already covered by OPS-Q8, SEC-Q5 and SEC-Q7. Recorded so the self-service
expectation is not lost silently.

---

## Section DATA - Persistence (Step 6)

#### DATA-Q1: PersistentVolumeClaim and StorageClass Portability — BLOCKER ⚡

**Look for:** `kind: PersistentVolumeClaim`, `storageClassName` values, OpenShift default
class names (`gp2-csi`, `gp3-csi`, `thin`, `ocs-storagecluster-*`, `managed-nfs-storage`),
`kind: StorageClass`.

**EKS equivalent:** the EBS CSI driver (`gp3`) or the EFS CSI driver, installed as EKS add-ons.
The class **name** almost never matches.

**Why BLOCKER:** a PVC referencing a non-existent StorageClass stays `Pending` and the
workload never starts. It is loud, but it is absolutely blocking, and it is trivially missed
because the manifest looks portable.

**⚡ Resolution:** `eks-hybrid` **escalates** in scope - EBS and EFS are not available
on-premises, so the storage backend itself has to be chosen, not just the class renamed.
Others as written.

#### DATA-Q2: ReadWriteMany Access Mode — RISK-SAFETY

**Look for:** `accessModes: [ReadWriteMany]`, shared volumes mounted by multiple pods, NFS
provisioners, OpenShift Data Foundation CephFS.

**EKS equivalent:** EFS. EBS is `ReadWriteOnce` only.

**Why RISK-SAFETY:** if RWX is converted to a `gp3` PVC, the first pod mounts fine and the
second is unschedulable, or worse the workload appears healthy at one replica and the sharing
assumption breaks only under scale-out. Also a cost and latency change that should be a
deliberate decision.

#### DATA-Q3: Stateful Workload Topology — RISK-SAFETY

**Look for:** `kind: StatefulSet`, `volumeClaimTemplates`, pod anti-affinity for data
placement, headless Services, single-AZ assumptions.

**EKS equivalent:** the same API, but **EBS volumes are zonal**, so a pod cannot move across
Availability Zones and reattach.

**Why RISK-SAFETY:** the StatefulSet applies and runs. The zonal constraint only appears during
an AZ event or a node replacement, when the pod cannot reschedule. This is the failure mode
most likely to be discovered during an incident rather than during the migration.

#### DATA-Q4: Internal Registry Storage — RISK-QUALITY

**Look for:** `kind: Config` (`imageregistry.operator.openshift.io`), registry storage
configuration, PVC backing the internal registry.

**EKS equivalent:** ECR, which is managed and needs no storage decision.

**Why RISK-QUALITY:** the target is strictly simpler. Worth reporting because the migration
removes a component the customer was operating, which is a saving to name explicitly rather
than a risk to manage.

#### DATA-Q5: Backup and Snapshot Dependency — INFO

**Look for:** `kind: Backup`/`Restore`/`Schedule` (OADP or Velero), `VolumeSnapshot`,
`VolumeSnapshotClass`.

**EKS equivalent:** Velero runs on EKS; EBS snapshots via the CSI snapshotter; AWS Backup.

**Why INFO:** the capability exists on both sides and the conversion is a platform task rather
than an application change. Recorded so the data-protection posture is carried over
deliberately instead of being rebuilt from memory after the move.
