# Security Checks

## Overview

Security validation based on:
- [EKS Best Practices - Security](https://docs.aws.amazon.com/eks/latest/best-practices/security.html)
- [Kubernetes Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)
- [Kubernetes Setup Best Practices - Enforcing PSS](https://kubernetes.io/docs/setup/best-practices/enforcing-pod-security-standards/)
- [Kubernetes Setup Best Practices - PKI Certificates](https://kubernetes.io/docs/setup/best-practices/certificates/)

Every check below carries a stable **Check ID**, its evidence commands, the exact FAIL condition and a fixed report line. The catalog of all IDs, the scoring formula and the report format live in `POWER.md`.

---

## Check: SEC-01 Pod Security Standards Enforcement

**Severity:** CRITICAL (if no enforcement) / MEDIUM (if only baseline)

**Check ID:** `SEC-01` | **Scope level:** namespace | **Applies to:** any cluster | **Evaluation:** kubectl

**Evidence:**
```bash
kubectl get namespace <ns> -o json | jq -r '.metadata.labels | with_entries(select(.key | startswith("pod-security.kubernetes.io/")))'
```

**FAIL when:** no `pod-security.kubernetes.io/enforce` label, or `enforce: privileged` (CRITICAL); `enforce: baseline` (MEDIUM). PASS only with `enforce: restricted`.

**Why (report line):** Without an enforced Pod Security level, any pod spec (privileged, hostPath, root) is admitted.

**Source:** [Pod Security Admission](https://kubernetes.io/docs/concepts/security/pod-security-admission/)

**What to check:**
1. List all namespaces and check for PSS labels:
   - `pod-security.kubernetes.io/enforce`
   - `pod-security.kubernetes.io/warn`
   - `pod-security.kubernetes.io/audit`
2. Identify namespaces with no PSS labels at all
3. Check if any namespace uses `privileged` level in enforce mode

**How to check (kubernetes MCP):**
```
kubectl_get:
  resourceType: namespaces
  output: json
```

**Finding logic:**
- No PSS labels on namespace -> CRITICAL
- Only `baseline` enforce -> MEDIUM (recommend `restricted` for production)
- `restricted` enforce -> PASS

**Recommendation:**
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/warn: restricted
    pod-security.kubernetes.io/audit: restricted
```

---

## Check: SEC-02 Privileged Containers

**Severity:** CRITICAL

**Check ID:** `SEC-02` | **Scope level:** namespace | **Applies to:** any cluster | **Evaluation:** kubectl

**Evidence:**
```bash
kubectl get deploy,sts,ds -n <ns> -o json | jq -r '.items[] | select(any(.spec.template.spec.containers[]; .securityContext.privileged == true or .securityContext.allowPrivilegeEscalation == true or ((.securityContext.capabilities.add // []) | any(. == "SYS_ADMIN" or . == "NET_ADMIN" or . == "ALL")))) | "\(.kind)/\(.metadata.name)"'
```

**FAIL when:** any container sets `privileged: true`, `allowPrivilegeEscalation: true`, or adds `SYS_ADMIN`, `NET_ADMIN` or `ALL` (CRITICAL).

**Why (report line):** A privileged or escalating container can take over the node and every pod on it.

**Source:** [EKS Best Practices - Pod Security](https://docs.aws.amazon.com/eks/latest/best-practices/pod-security.html)

**What to check:**
1. Scan all pods for containers running with:
   - `securityContext.privileged: true`
   - `securityContext.allowPrivilegeEscalation: true`
   - `securityContext.capabilities.add` containing `SYS_ADMIN`, `NET_ADMIN`, `ALL`

**How to check:**
```
kubectl_get:
  resourceType: pods
  allNamespaces: true
  output: json
```
Filter for `.spec.containers[].securityContext.privileged == true`

**Recommendation:** Remove privileged mode. Use specific capabilities instead of broad grants.

**Fix (YAML):**
```yaml
spec:
  template:
    spec:
      containers:
      - name: <container>
        securityContext:
          privileged: false
          allowPrivilegeEscalation: false
          capabilities:
            drop: ["ALL"]
```

---

## Check: SEC-03 RBAC Least Privilege

**Severity:** HIGH

**Check ID:** `SEC-03` | **Scope level:** cluster | **Applies to:** any cluster | **Evaluation:** kubectl

**Evidence:**
```bash
kubectl get clusterrolebindings -o json | jq -r '.items[] | select(.roleRef.name == "cluster-admin" and (.metadata.name | test("^(system:|eks:)") | not)) | "ClusterRoleBinding/\(.metadata.name)"'
kubectl get clusterroles -o json | jq -r '.items[] | select((.metadata.name | test("^(system:|eks:|cluster-admin$)") | not) and any(.rules[]?; ((.resources // []) | index("*")) and ((.verbs // []) | index("*")))) | "ClusterRole/\(.metadata.name)"'
```

**FAIL when:** the first two **Finding logic** rows (HIGH). The ServiceAccount row is scored under SEC-06, not here.

**Why (report line):** A broad binding turns one leaked token into full control of the cluster.

**Source:** [RBAC Good Practices](https://kubernetes.io/docs/concepts/security/rbac-good-practices/)

**What to check:**
1. ClusterRoleBindings with `cluster-admin` role
2. ClusterRoles with wildcard (`*`) permissions on resources/verbs
3. RoleBindings granting write access to secrets
4. ServiceAccounts with token auto-mount enabled

**How to check:**
```
kubectl_get:
  resourceType: clusterrolebindings
  output: json

kubectl_get:
  resourceType: clusterroles
  output: json
```

**Finding logic:**
- Non-system ClusterRoleBinding to `cluster-admin` -> HIGH
- ClusterRole with `resources: ["*"]` and `verbs: ["*"]` -> HIGH
- ServiceAccount with `automountServiceAccountToken: true` (non-system) -> MEDIUM

**Recommendation:** Follow least-privilege principle. Create specific roles per workload.

**Fix (YAML):**
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: <app>-reader
  namespace: <ns>
rules:
- apiGroups: [""]
  resources: ["configmaps"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: <app>-reader
  namespace: <ns>
subjects:
- kind: ServiceAccount
  name: <app>
  namespace: <ns>
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: <app>-reader
```

---

## Check: SEC-04 Secrets Management

**Severity:** HIGH

**Check ID:** `SEC-04` | **Scope level:** cluster | **Applies to:** EKS only | **Evaluation:** aws

**Evidence:**
```bash
aws eks describe-cluster --name <cluster> --region <region> --query '{version: cluster.version, encryption: cluster.encryptionConfig}'
```

**FAIL when:** `encryptionConfig` is empty on Kubernetes < 1.28 (HIGH: no envelope encryption of Secrets); empty on 1.28 or later (LOW: EKS applies default envelope encryption with an AWS owned key, a customer managed KMS key adds key control and audit). PASS when a KMS key is configured.

**Why (report line):** Secrets in etcd are only base64; envelope encryption with your own KMS key controls who can decrypt them.

**Source:** [EKS default envelope encryption](https://docs.aws.amazon.com/eks/latest/userguide/envelope-encryption.html)

**What to check:**
1. Secrets stored as `Opaque` type without external secrets operator
2. EKS: Envelope encryption enabled for etcd secrets (KMS key)
3. Secrets referenced in environment variables vs volume mounts (env vars appear in logs)
4. External Secrets Operator or AWS Secrets Manager integration present

**How to check (EKS):**
```
get_eks_insights:
  cluster_name: <cluster>
  category: MISCONFIGURATION
```
Also check cluster describe for `encryptionConfig`.

**Recommendation:**
- Enable envelope encryption with KMS
- Use External Secrets Operator or CSI Secrets Store
- Mount secrets as volumes, not env vars

**Fix (YAML):**
```yaml
# eksctl ClusterConfig, applied with: eksctl utils enable-secrets-encryption -f cluster.yaml
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig
metadata:
  name: <cluster>
  region: <region>
secretsEncryption:
  keyARN: arn:aws:kms:<region>:<account-id>:key/<key-id>
```

---

## Check: SEC-05 Network Policies

**Severity:** HIGH

**Check ID:** `SEC-05` | **Scope level:** namespace | **Applies to:** any cluster | **Evaluation:** kubectl

**Evidence:**
```bash
kubectl get networkpolicies -n <ns> -o json | jq -r '.items[] | "NetworkPolicy/\(.metadata.name) podSelector=\(.spec.podSelector | tojson) types=\(.spec.policyTypes // [] | join(",")) ingressRules=\(.spec.ingress // [] | length)"'
```

**FAIL when:** apply **Finding logic**. Default-deny means a policy with `podSelector: {}`, `Ingress` in `policyTypes` and no `ingress` rules. Resource = `Namespace/<ns>`.

**Why (report line):** Without NetworkPolicies every pod can reach every other pod, so one compromised pod can move laterally.

**Source:** [Network Policies](https://kubernetes.io/docs/concepts/services-networking/network-policies/)

**What to check:**
1. Namespaces without ANY NetworkPolicy
2. Default-deny ingress policy existence
3. Default-deny egress policy existence
4. Pods with no NetworkPolicy selecting them

**How to check:**
```
kubectl_get:
  resourceType: networkpolicies
  allNamespaces: true
  output: json
```

**Finding logic:**
- Namespace with workloads but zero NetworkPolicies -> HIGH
- No default-deny policy -> MEDIUM
- Namespace has policies but not covering all pods -> LOW

**Recommendation:**
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
spec:
  podSelector: {}
  policyTypes:
  - Ingress
```

---

## Check: SEC-06 Service Account Token Security

**Severity:** MEDIUM

**Check ID:** `SEC-06` | **Scope level:** namespace | **Applies to:** any cluster | **Evaluation:** kubectl

**Evidence:**
```bash
kubectl get deploy,sts,ds -n <ns> -o json | jq -r '.items[] | "\(.kind)/\(.metadata.name) sa=\(.spec.template.spec.serviceAccountName // "default") automount=\(.spec.template.spec.automountServiceAccountToken | tostring)"'
kubectl get serviceaccounts -n <ns> -o json | jq -r '.items[] | "ServiceAccount/\(.metadata.name) automount=\(.automountServiceAccountToken | tostring)"'
```

**FAIL when:** the workload uses the `default` ServiceAccount (MEDIUM), or neither the pod template nor its ServiceAccount sets `automountServiceAccountToken: false` (MEDIUM).

**Why (report line):** An auto-mounted token gives every process in the pod an API credential it usually does not need.

**Source:** [Configure Service Accounts for Pods](https://kubernetes.io/docs/tasks/configure-pod-container/configure-service-account/)

**What to check:**
1. Pods using the `default` ServiceAccount
2. ServiceAccounts with `automountServiceAccountToken: true` (default)
3. Pods not explicitly setting `automountServiceAccountToken: false`

**How to check:**
```
kubectl_get:
  resourceType: pods
  allNamespaces: true
  output: json
```
Filter: `.spec.serviceAccountName == "default"` OR `.spec.automountServiceAccountToken != false`

**Recommendation:** Create dedicated ServiceAccounts per workload. Disable token auto-mount unless needed.

**Fix (YAML):**
```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: <app>
  namespace: <ns>
automountServiceAccountToken: false
---
# in the workload
spec:
  template:
    spec:
      serviceAccountName: <app>
      automountServiceAccountToken: false
```

---

## Check: SEC-07 Image Security

**Severity:** HIGH

**Check ID:** `SEC-07` | **Scope level:** namespace | **Applies to:** any cluster | **Evaluation:** kubectl

**Evidence:**
```bash
kubectl get deploy,sts,ds -n <ns> -o json | jq -r '.items[] | . as $w | .spec.template.spec.containers[] | (.image | split("/")) as $p | (if ($p | length) > 1 and ($p[0] | test("[.:]") or . == "localhost") then $p[0] else "docker.io" end) as $host | select(((.image | test("@sha256:") | not) and ((.image | test(":[^/:]+$") | not) or (.image | endswith(":latest")))) or ($host | IN("docker.io", "index.docker.io", "quay.io"))) | "\($w.kind)/\($w.metadata.name) container=\(.name) registry=\($host)"'
```

**FAIL when:** image uses `:latest` or no tag and no digest (HIGH); image is pulled from a public registry: `docker.io` (including images with no registry host), `index.docker.io` or `quay.io` (MEDIUM).

**Why (report line):** Mutable or public images can change or disappear under a running workload and bypass your scanning.

**Source:** [EKS Best Practices - Image security](https://docs.aws.amazon.com/eks/latest/best-practices/image-security.html)

**What to check:**
1. Containers using `latest` tag or no tag at all
2. Containers pulling from public registries (docker.io, quay.io) in production
3. No image pull policy set (defaults to `IfNotPresent` which can use stale images)
4. ImagePullSecrets not configured for private registries

**How to check:**
```
kubectl_get:
  resourceType: pods
  allNamespaces: true
  output: json
```
Filter: `.spec.containers[].image` without SHA digest or using `:latest`

**Recommendation:**
- Use immutable image tags or SHA digests
- Pull from private ECR/registry
- Set `imagePullPolicy: Always` for mutable tags

**Fix (YAML):**
```yaml
spec:
  template:
    spec:
      containers:
      - name: <container>
        image: <private-registry>/<repo>@sha256:<digest>
```

---

## Check: SEC-08 Pod Identity / IRSA (EKS-specific)

**Severity:** HIGH

**Check ID:** `SEC-08` | **Scope level:** namespace | **Applies to:** any cluster | **Evaluation:** kubectl

**Evidence:**
```bash
kubectl get deploy,sts,ds -n <ns> -o json | jq -r '.items[] | select(any(.spec.template.spec.containers[]; (.env // []) | any(.name == "AWS_ACCESS_KEY_ID" or .name == "AWS_SECRET_ACCESS_KEY"))) | "\(.kind)/\(.metadata.name)"'
kubectl get serviceaccounts -n <ns> -o json | jq -r '.items[] | "ServiceAccount/\(.metadata.name) irsa=\(.metadata.annotations // {} | has("eks.amazonaws.com/role-arn"))"'
aws eks list-pod-identity-associations --cluster-name <cluster> --region <region> --namespace <ns> --query 'associations[].serviceAccount'
```

**FAIL when:** a container defines `AWS_ACCESS_KEY_ID` or `AWS_SECRET_ACCESS_KEY` as an env var (HIGH). The node IAM role row is evaluated only in cluster-scope EKS runs: node role with `AdministratorAccess` or `*:*` (HIGH). The ServiceAccount and Pod Identity commands are context for the fix; they never print an ARN.

**Why (report line):** Static AWS keys in a pod never rotate and leak through env dumps and logs.

**Source:** [EKS Pod Identity](https://docs.aws.amazon.com/eks/latest/userguide/pod-identities.html)

**What to check:**
1. Pods accessing AWS services without IRSA or Pod Identity
2. Node IAM role with overly broad permissions
3. Pod Identity associations vs IRSA annotations consistency

**How to check (EKS):**
```
get_policies_for_role:
  role_name: <node-role-name>

list_k8s_resources:
  cluster_name: <cluster>
  kind: ServiceAccount
  api_version: v1
```
Check for `eks.amazonaws.com/role-arn` annotation.

**Recommendation:** Use Pod Identity (preferred) or IRSA. Never put AWS credentials in env vars or ConfigMaps.

**Fix (YAML):**
```yaml
# Remove AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY from the pod and use a dedicated ServiceAccount.
# Pod Identity (preferred): no annotation, create an association for <ns>/<app>.
# IRSA: annotate the ServiceAccount.
apiVersion: v1
kind: ServiceAccount
metadata:
  name: <app>
  namespace: <ns>
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::<account-id>:role/<app-role>
```

---

## Check: SEC-09 PKI Certificates and Rotation

**Severity:** MEDIUM

**Check ID:** `SEC-09` | **Scope level:** namespace | **Applies to:** any cluster | **Evaluation:** kubectl

**Evidence:**
```bash
kubectl get secrets -n <ns> --field-selector type=kubernetes.io/tls -o jsonpath='{range .items[*]}{.metadata.name}{"\n"}{end}'
kubectl get secret <name> -n <ns> -o jsonpath='{.data.tls\.crt}' | base64 -d | openssl x509 -noout -enddate
```

**FAIL when:** a TLS Secret certificate is expired (CRITICAL), expires in less than 7 days (HIGH) or in less than 30 days (MEDIUM). No TLS Secrets in scope = PASS. Never read or print `tls.key`.

**Why (report line):** An expired certificate breaks TLS for every client at once, usually without warning.

**Source:** [Manage TLS Certificates in a Cluster](https://kubernetes.io/docs/tasks/tls/managing-tls-in-a-cluster/)

**What to check:**
1. EKS: Certificate authority expiry (EKS auto-rotates, but verify)
2. Self-managed: kubelet serving certificates rotation enabled
3. Custom certificates (webhook, admission controllers) approaching expiry
4. mTLS certificates for service mesh (Istio/Linkerd) rotation policy

**How to check:**
```
kubectl_get:
  resourceType: secrets
  allNamespaces: true
  fieldSelector: "type=kubernetes.io/tls"
```
Also check cert-manager Certificate resources if installed.

**Recommendation:**
- Use cert-manager for automated certificate lifecycle
- Monitor certificate expiry with alerts (< 30 days = warning, < 7 days = critical)
- Enable kubelet certificate rotation (`--rotate-certificates`)

**Fix (YAML):**
```yaml
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: <name>
  namespace: <ns>
spec:
  secretName: <tls-secret>
  dnsNames: ["<host>"]
  duration: 2160h
  renewBefore: 720h
  issuerRef:
    kind: ClusterIssuer
    name: <issuer>
```

---

## Check: SEC-10 Runtime Security

**Severity:** MEDIUM

**Check ID:** `SEC-10` | **Scope level:** namespace | **Applies to:** any cluster | **Evaluation:** kubectl

**Evidence:**
```bash
kubectl get deploy,sts,ds -n <ns> -o json | jq -r '.items[] | .spec.template.spec as $p | . as $w | $p.containers[] | select(((if .securityContext.runAsNonRoot == null then $p.securityContext.runAsNonRoot else .securityContext.runAsNonRoot end) != true) or (.securityContext.readOnlyRootFilesystem != true) or (((if .securityContext.seccompProfile.type == null then $p.securityContext.seccompProfile.type else .securityContext.seccompProfile.type end) // "") | IN("RuntimeDefault", "Localhost") | not) or ((.securityContext.capabilities.drop // []) | index("ALL") == null)) | "\($w.kind)/\($w.metadata.name) container=\(.name)"'
```

**FAIL when:** any container misses one of: `runAsNonRoot: true` (container or pod level), `readOnlyRootFilesystem: true`, seccomp `RuntimeDefault` or `Localhost` (container or pod level), `capabilities.drop: ["ALL"]` (MEDIUM). The finding names the missing fields.

**Why (report line):** Root, a writable filesystem and full capabilities turn an application bug into a container escape path.

**Source:** [Configure a Security Context for a Pod or Container](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/)

**What to check:**
1. Pods running as root (`runAsUser: 0` or no `runAsNonRoot: true`)
2. Containers with writable root filesystem (`readOnlyRootFilesystem: false`)
3. No seccomp profile set
4. Pods not dropping ALL capabilities

**How to check:**
```
kubectl_get:
  resourceType: pods
  allNamespaces: true
  output: json
```
Filter security context fields.

**Recommendation:**
```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false
  capabilities:
    drop: ["ALL"]
  seccompProfile:
    type: RuntimeDefault
```

---

## Check: SEC-11 Multi-Tenancy Isolation

**Severity:** MEDIUM

**Check ID:** `SEC-11` | **Scope level:** namespace | **Applies to:** any cluster | **Evaluation:** kubectl

**Evidence:**
```bash
kubectl get resourcequotas,limitranges -n <ns> -o name
```

**FAIL when:** the namespace has no ResourceQuota (MEDIUM) or no LimitRange (MEDIUM). Resource = `Namespace/<ns>`.

**Why (report line):** Without quotas and default limits one tenant can starve every other workload on the cluster.

**Source:** [Resource Quotas](https://kubernetes.io/docs/concepts/policy/resource-quotas/)

**What to check:**
1. Shared namespaces between different teams/tenants without ResourceQuotas
2. Missing LimitRange in shared namespaces
3. No namespace-level RBAC separation
4. Cross-namespace service access without NetworkPolicy restriction

**How to check:**
```
kubectl_get:
  resourceType: resourcequotas
  allNamespaces: true

kubectl_get:
  resourceType: limitranges
  allNamespaces: true
```

**Recommendation:** Each tenant gets own namespace with ResourceQuota, LimitRange, NetworkPolicy, and dedicated ServiceAccounts.

**Fix (YAML):**
```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: compute-quota
  namespace: <ns>
spec:
  hard:
    requests.cpu: "4"
    requests.memory: 8Gi
    limits.memory: 16Gi
    pods: "50"
---
apiVersion: v1
kind: LimitRange
metadata:
  name: default-limits
  namespace: <ns>
spec:
  limits:
  - type: Container
    defaultRequest:
      cpu: 100m
      memory: 128Mi
    default:
      memory: 256Mi
```
