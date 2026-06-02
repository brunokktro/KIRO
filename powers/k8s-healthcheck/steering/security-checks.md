# Security Checks

## Overview

Security validation based on:
- [EKS Best Practices - Security](https://docs.aws.amazon.com/eks/latest/best-practices/security.html)
- [Kubernetes Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)
- [Kubernetes Setup Best Practices - Enforcing PSS](https://kubernetes.io/docs/setup/best-practices/enforcing-pod-security-standards/)
- [Kubernetes Setup Best Practices - PKI Certificates](https://kubernetes.io/docs/setup/best-practices/certificates/)

---

## Check: Pod Security Standards Enforcement

**Severity:** CRITICAL (if no enforcement) / HIGH (if only baseline)

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

## Check: Privileged Containers

**Severity:** CRITICAL

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

---

## Check: RBAC Least Privilege

**Severity:** HIGH

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

---

## Check: Secrets Management

**Severity:** HIGH

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

---

## Check: Network Policies

**Severity:** HIGH

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

## Check: Service Account Token Security

**Severity:** MEDIUM

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

---

## Check: Image Security

**Severity:** HIGH

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

---

## Check: Pod Identity / IRSA (EKS-specific)

**Severity:** HIGH

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

---

## Check: PKI Certificates and Rotation

**Severity:** MEDIUM

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
  labelSelector: "type=kubernetes.io/tls"
```
Also check cert-manager Certificate resources if installed.

**Recommendation:**
- Use cert-manager for automated certificate lifecycle
- Monitor certificate expiry with alerts (< 30 days = warning, < 7 days = critical)
- Enable kubelet certificate rotation (`--rotate-certificates`)

---

## Check: Runtime Security

**Severity:** MEDIUM

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

## Check: Multi-Tenancy Isolation

**Severity:** MEDIUM

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
