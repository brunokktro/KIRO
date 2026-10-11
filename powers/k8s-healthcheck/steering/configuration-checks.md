# Configuration Checks

## Overview

Configuration hygiene validation based on:
- [Kubernetes Configuration Good Practices](https://kubernetes.io/blog/2025/11/25/configuration-good-practices/)
- [Kubernetes Common Labels](https://kubernetes.io/docs/concepts/overview/working-with-objects/common-labels/)
- [Kubernetes Setup Best Practices](https://kubernetes.io/docs/setup/best-practices/)

Every check below carries a stable **Check ID**, its evidence commands, the exact FAIL condition and a fixed report line. The catalog of all IDs, the scoring formula and the report format live in `POWER.md`.

---

## Check: CFG-01 Semantic Labels

**Severity:** MEDIUM

**Check ID:** `CFG-01` | **Scope level:** namespace | **Applies to:** any cluster | **Evaluation:** kubectl

**Evidence:**
```bash
kubectl get deploy,sts,ds -n <ns> -o json | jq -r '.items[] | "\(.kind)/\(.metadata.name) name=\(.metadata.labels // {} | has("app.kubernetes.io/name")) version=\(.metadata.labels // {} | has("app.kubernetes.io/version"))"'
```

**FAIL when:** apply **Finding logic** to the workload `metadata.labels`.

**Why (report line):** Without the common labels, tools and people cannot tell what an object belongs to.

**Source:** [Recommended Labels](https://kubernetes.io/docs/concepts/overview/working-with-objects/common-labels/)

**What to check:**
1. Workloads using recommended Kubernetes labels:
   - `app.kubernetes.io/name`
   - `app.kubernetes.io/instance`
   - `app.kubernetes.io/version`
   - `app.kubernetes.io/component`
   - `app.kubernetes.io/part-of`
   - `app.kubernetes.io/managed-by`
2. Custom labels for operational purposes (team, environment)
3. Consistent labeling scheme across namespaces

**Finding logic:**
- No `app.kubernetes.io/name` label -> MEDIUM
- No version label -> LOW
- Proper semantic labels -> PASS

**Fix (YAML):**
```yaml
metadata:
  labels:
    app.kubernetes.io/name: <app>
    app.kubernetes.io/instance: <app>-<env>
    app.kubernetes.io/version: "<version>"
    app.kubernetes.io/component: <component>
    app.kubernetes.io/part-of: <system>
    app.kubernetes.io/managed-by: <tool>
```

---

## Check: CFG-02 Meaningful Annotations

**Severity:** LOW

**Check ID:** `CFG-02` | **Scope level:** namespace | **Applies to:** any cluster | **Evaluation:** kubectl

**Evidence:**
```bash
kubectl get deploy,sts,ds -n <ns> -o json | jq -r '.items[] | select(.metadata.annotations // {} | has("kubernetes.io/description") | not) | "\(.kind)/\(.metadata.name)"'
```

**FAIL when:** the workload has no `kubernetes.io/description` annotation (LOW).

**Why (report line):** A description annotation tells the on-call engineer what the workload does without reading code.

**Source:** [Well-Known Labels, Annotations and Taints](https://kubernetes.io/docs/reference/labels-annotations-taints/)

**What to check:**
1. Resources with `kubernetes.io/description` annotation
2. Contact/owner annotations for operational clarity
3. Links to runbooks or dashboards

**Fix (YAML):**
```yaml
metadata:
  annotations:
    kubernetes.io/description: "<what this workload does and who owns it>"
```

---

## Check: CFG-03 Latest Stable API Versions

**Severity:** MEDIUM

**Check ID:** `CFG-03` | **Scope level:** namespace | **Applies to:** any cluster | **Evaluation:** kubectl

**Evidence:**
```bash
kubectl get deploy,sts,ds,cronjob,hpa,pdb,ingress -n <ns> -o json --show-managed-fields | jq -r '.items[] | "\(.kind)/\(.metadata.name) writtenWith=\([.metadata.managedFields[]?.apiVersion] | unique | join(","))"'
```

**FAIL when:** an object was written with an `alpha` API version (HIGH) or a `beta` version (MEDIUM), read from `metadata.managedFields[].apiVersion`.

**Why (report line):** Beta and alpha APIs are removed on a schedule, and manifests that use them break on upgrade.

**Source:** [Deprecated API Migration Guide](https://kubernetes.io/docs/reference/using-api/deprecation-guide/)

**What to check:**
1. Resources using beta API versions when stable exists
2. Resources using alpha API versions in production

**Finding logic:**
- Using v1beta1 when v1 is available -> MEDIUM
- Using alpha API in production -> HIGH

**Fix (YAML):**
```yaml
apiVersion: autoscaling/v2   # was autoscaling/v2beta2
kind: HorizontalPodAutoscaler
```

---

## Check: CFG-04 YAML Hygiene

**Severity:** LOW

**Check ID:** `CFG-04` | **Scope level:** cluster | **Applies to:** any cluster | **Evaluation:** kubectl

**Evidence:**
```bash
kubectl get deploy,sts,ds -n default -o name
kubectl get deploy,sts,ds -n kube-system -o name | grep -Ev 'aws-node|kube-proxy|coredns|kube-dns|ebs-csi|efs-csi|fsx-csi|s3-csi|eks-pod-identity-agent|metrics-server|aws-load-balancer-controller|karpenter|cluster-autoscaler|snapshot-controller|cloudwatch-agent|fluent-bit|adot|calico|cilium|tigera|dns-autoscaler|node-local-dns|secrets-store-csi|kube-state-metrics'
```

**FAIL when:** apply **Finding logic**. Non-system = not matched by the allowlist in the second command (extend it with `System workloads:` in the prompt). The boolean row is not scored: the API server normalizes booleans.

**Why (report line):** Workloads in default or kube-system share permissions and quotas with things they should not.

**Source:** [Kubernetes Configuration Good Practices](https://kubernetes.io/blog/2025/11/25/configuration-good-practices/)

**What to check:**
1. Workloads in `default` namespace
2. Non-system pods in `kube-system`
3. Boolean values using non-standard representations

**Finding logic:**
- Workloads in `default` namespace -> MEDIUM
- Non-system pods in `kube-system` -> HIGH

**Fix (YAML):**
```yaml
metadata:
  name: <app>
  namespace: <team-namespace>   # not default, not kube-system
```

---

## Check: CFG-05 Namespace Isolation

**Severity:** MEDIUM

**Check ID:** `CFG-05` | **Scope level:** namespace | **Applies to:** any cluster | **Evaluation:** kubectl

**Evidence:**
```bash
kubectl get resourcequotas,limitranges -n <ns> -o name
```

**FAIL when:** no ResourceQuota (MEDIUM, every cluster is treated as shared unless the prompt says single-tenant); no LimitRange (LOW). The all-workloads-in-one-namespace row (HIGH) is evaluated only in cluster-scope runs.

**Why (report line):** A namespace without quota or limits cannot be isolated from its neighbors.

**Source:** [Resource Quotas](https://kubernetes.io/docs/concepts/policy/resource-quotas/)

**What to check:**
1. Proper namespace separation by environment/team
2. ResourceQuotas per namespace
3. LimitRanges per namespace

**Finding logic:**
- All workloads in one namespace -> HIGH
- Namespace without ResourceQuota in shared cluster -> MEDIUM
- Namespace without LimitRange -> LOW

**Fix:** same manifests as the SEC-11 fix (ResourceQuota and LimitRange).

---

## Check: CFG-06 Version Control and GitOps

**Severity:** MEDIUM

**Check ID:** `CFG-06` | **Scope level:** namespace | **Applies to:** any cluster | **Evaluation:** kubectl

**Evidence:**
```bash
kubectl get deploy,sts,ds,svc -n <ns> -o json | jq -r '.items[] | (.metadata.labels // {}) as $l | (.metadata.annotations // {}) as $a | "\(.kind)/\(.metadata.name) managed=\(($l["app.kubernetes.io/managed-by"] // "") != "" or ($a | has("meta.helm.sh/release-name")) or ($a | has("argocd.argoproj.io/tracking-id")) or ($l | has("argocd.argoproj.io/instance")) or ($l | has("kustomize.toolkit.fluxcd.io/name")) or ($l | has("helm.toolkit.fluxcd.io/name")))"'
kubectl get secrets -n <ns> -l owner=helm,status=failed -o jsonpath='{range .items[*]}{.metadata.labels.name}{"\n"}{end}'
```

**FAIL when:** more than 50% of the listed objects are `managed=false` (MEDIUM, resource `Namespace/<ns>`); a Helm release in `failed` state (HIGH, resource `HelmRelease/<name>`).

**Why (report line):** Objects applied by hand drift from Git and cannot be rebuilt after an incident.

**Source:** [Kubernetes Configuration Good Practices](https://kubernetes.io/blog/2025/11/25/configuration-good-practices/)

**What to check:**
1. Resources with management annotations (Helm, ArgoCD, Flux)
2. Resources without any management annotation (manually applied)
3. Helm releases in failed state

**Finding logic:**
- > 50% resources without management tool -> MEDIUM
- Helm releases in failed state -> HIGH
- All resources managed by GitOps -> PASS

**Fix (YAML):**
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: <app>
  namespace: argocd
spec:
  project: default
  source:
    repoURL: <git-repo-url>
    path: <path>
    targetRevision: main
  destination:
    server: https://kubernetes.default.svc
    namespace: <ns>
  syncPolicy:
    automated: {}
```

---

## Check: CFG-07 ConfigMap and Secret Best Practices

**Severity:** MEDIUM

**Check ID:** `CFG-07` | **Scope level:** namespace | **Applies to:** any cluster | **Evaluation:** kubectl

**Evidence:**
```bash
kubectl get deploy,sts,ds -n <ns> -o json | jq -r '.items[] | select(any(.spec.template.spec.containers[]; any((.env // [])[]; .valueFrom.secretKeyRef != null) or any((.envFrom // [])[]; .secretRef != null))) | "\(.kind)/\(.metadata.name)"'
kubectl get configmaps -n <ns> -o json | jq -r '.items[] | select(((.data // {}) | tostring | length) + ((.binaryData // {}) | tostring | length) > 512000) | "ConfigMap/\(.metadata.name)"'
```

**FAIL when:** apply **Finding logic**. ConfigMap size = length of `data` plus `binaryData` serialized, threshold 500KB (512000).

**Why (report line):** Secrets in env vars leak through process listings, crash dumps and debug logs.

**Source:** [Secrets](https://kubernetes.io/docs/concepts/configuration/secret/)

**What to check:**
1. Secrets referenced as env vars vs volumes
2. ConfigMaps with large data (> 1MB approaching etcd limit)
3. Immutable ConfigMaps/Secrets used where appropriate

**Finding logic:**
- Secrets in env vars -> MEDIUM (log exposure risk)
- ConfigMap > 500KB -> MEDIUM

**Fix (YAML):**
```yaml
spec:
  template:
    spec:
      containers:
      - name: <container>
        volumeMounts:
        - name: app-secret
          mountPath: /etc/app/secret
          readOnly: true
      volumes:
      - name: app-secret
        secret:
          secretName: <secret>
```

---

## Check: CFG-08 Controller Usage (No Naked Pods)

**Severity:** HIGH

**Check ID:** `CFG-08` | **Scope level:** namespace | **Applies to:** any cluster | **Evaluation:** kubectl

**Evidence:**
```bash
kubectl get pods -n <ns> -o json | jq -r '.items[] | select((.metadata.ownerReferences // []) | length == 0) | "Pod/\(.metadata.name)"'
```

**FAIL when:** apply **Finding logic** (same evidence as REL-05).

**Why (report line):** A pod created directly is never rescheduled, scaled or rolled out.

**Source:** [Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)

**What to check:**
1. Pods without ownerReferences (naked pods)
2. Use Deployments for stateless apps
3. Use Jobs/CronJobs for batch tasks

**Finding logic:**
- Naked pod in production -> HIGH
- Appropriate controller usage -> PASS

**Recommendation:** From K8s Configuration Good Practices:
- "A Deployment is almost always preferable to creating Pods directly"
- "A Job is perfect when you need something to run once and then stop"

**Fix:** same Deployment manifest as the REL-05 fix.
