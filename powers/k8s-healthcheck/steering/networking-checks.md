# Networking Checks

## Overview

Networking validation based on:
- [EKS Best Practices - Networking](https://docs.aws.amazon.com/eks/latest/best-practices/networking.html)
- [Kubernetes Configuration Good Practices - Service Configuration](https://kubernetes.io/blog/2025/11/25/configuration-good-practices/)

---

## Check: VPC CNI Configuration (EKS)

**Severity:** HIGH

**What to check:**
1. VPC CNI add-on version (should be latest compatible)
2. WARM_ENI_TARGET / WARM_IP_TARGET / MINIMUM_IP_TARGET settings
3. Prefix delegation mode enabled for high pod density
4. Custom networking enabled if using secondary CIDRs

**Finding logic:**
- VPC CNI > 2 versions behind -> HIGH
- Default WARM_ENI_TARGET without tuning on large clusters -> MEDIUM
- Prefix mode not enabled with > 100 pods/node -> MEDIUM

---

## Check: IP Address Exhaustion

**Severity:** CRITICAL

**What to check:**
1. Available IPs in each subnet used by nodes
2. Subnet utilization percentage
3. IPv6 cluster consideration for large deployments

**Finding logic:**
- Subnet < 20% available IPs -> CRITICAL
- Subnet < 40% available IPs -> HIGH
- No plan for IP growth -> MEDIUM

---

## Check: DNS Configuration

**Severity:** MEDIUM

**What to check:**
1. CoreDNS replicas (should be >= 2, scale with cluster size)
2. ndots configuration in pods (default 5 causes excessive DNS lookups)
3. DNS policy set appropriately

**Finding logic:**
- CoreDNS replicas < 2 -> HIGH
- CoreDNS without HPA on clusters > 50 nodes -> MEDIUM
- Pods with default ndots=5 causing performance issues -> LOW

---

## Check: Avoid hostPort and hostNetwork

**Severity:** MEDIUM

**What to check:**
1. Pods using `hostPort` (limits scheduling, causes port conflicts)
2. Pods using `hostNetwork: true` (bypasses network isolation)
3. Exceptions: CNI plugins, kube-proxy (legitimate uses)

**Finding logic:**
- Application pod with hostNetwork -> HIGH
- Application pod with hostPort -> MEDIUM
- System pod with hostNetwork -> PASS (expected)

---

## Check: Service Configuration

**Severity:** MEDIUM

**What to check:**
1. Services without selectors (headless or external)
2. LoadBalancer services without annotations for internal/external
3. Services with no matching endpoints

**Finding logic:**
- Service with empty endpoints (not headless) -> HIGH
- LoadBalancer without scheme annotation -> MEDIUM

---

## Check: Ingress Controller Configuration

**Severity:** MEDIUM

**What to check:**
1. Ingress controller deployed and healthy
2. Multiple replicas for HA
3. TLS termination configured
4. Ingress resources without TLS

**Finding logic:**
- Ingress without TLS -> HIGH
- Single replica ingress controller -> MEDIUM

---

## Check: Security Groups for Pods (EKS)

**Severity:** LOW

**What to check:**
1. SecurityGroupPolicy resources defined
2. Pods that need fine-grained network access using SGP

---

## Check: Service Mesh Health

**Severity:** LOW (only if mesh is deployed)

**What to check:**
1. Istio/Linkerd sidecar injection enabled
2. Pods without sidecar in meshed namespaces
3. mTLS mode (strict vs permissive)

**Finding logic:**
- Mesh installed but mTLS in permissive mode -> MEDIUM
- Pods in meshed namespace without sidecar -> MEDIUM
- Mesh control plane unhealthy -> HIGH
