# Networking Checks

## Overview

Networking validation based on:
- [EKS Best Practices - Networking](https://docs.aws.amazon.com/eks/latest/best-practices/networking.html)
- [Kubernetes Configuration Good Practices - Service Configuration](https://kubernetes.io/blog/2025/11/25/configuration-good-practices/)

Every check below carries a stable **Check ID**, its evidence commands, the exact FAIL condition and a fixed report line. The catalog of all IDs, the scoring formula and the report format live in `POWER.md`.

---

## Check: NET-01 VPC CNI Configuration (EKS)

**Severity:** HIGH

**Check ID:** `NET-01` | **Scope level:** cluster | **Applies to:** EKS only | **Evaluation:** aws

**Evidence:**
```bash
kubectl get daemonset aws-node -n kube-system -o jsonpath='{.spec.template.spec.containers[0].image}' | sed 's/.*://'
kubectl get daemonset aws-node -n kube-system -o json | jq -r '.spec.template.spec.containers[0].env[] | select(.name | test("^(WARM_ENI_TARGET|WARM_IP_TARGET|MINIMUM_IP_TARGET|ENABLE_PREFIX_DELEGATION)$")) | "\(.name)=\(.value)"'
aws eks describe-addon-versions --addon-name vpc-cni --kubernetes-version <version> --region <region> --query 'addons[0].addonVersions[].addonVersion' --output text
```

**FAIL when:** apply **Finding logic**. Versions behind = position of the running version in the newest-first list (not in the list = more than 2). Large cluster = more than 100 nodes.

**Why (report line):** An old or untuned CNI wastes IPs and misses fixes that affect pod networking.

**Source:** [EKS Best Practices - Amazon VPC CNI](https://docs.aws.amazon.com/eks/latest/best-practices/vpc-cni.html)

**What to check:**
1. VPC CNI add-on version (should be latest compatible)
2. WARM_ENI_TARGET / WARM_IP_TARGET / MINIMUM_IP_TARGET settings
3. Prefix delegation mode enabled for high pod density
4. Custom networking enabled if using secondary CIDRs

**Finding logic:**
- VPC CNI > 2 versions behind -> HIGH
- Default WARM_ENI_TARGET without tuning on large clusters -> MEDIUM
- Prefix mode not enabled with > 100 pods/node -> MEDIUM

**Fix (YAML):**
```yaml
# eksctl ClusterConfig, EKS managed add-on
addons:
- name: vpc-cni
  version: latest
  configurationValues: |-
    env:
      ENABLE_PREFIX_DELEGATION: "true"
      WARM_PREFIX_TARGET: "1"
```

---

## Check: NET-02 IP Address Exhaustion

**Severity:** CRITICAL

**Check ID:** `NET-02` | **Scope level:** cluster | **Applies to:** EKS only | **Evaluation:** aws

**Evidence:**
```bash
aws ec2 describe-subnets --region <region> --subnet-ids $(aws eks describe-cluster --name <cluster> --region <region> --query 'cluster.resourcesVpcConfig.subnetIds' --output text) --query 'Subnets[].[SubnetId,CidrBlock,AvailableIpAddressCount]' --output text
aws ec2 describe-instances --region <region> --filters Name=tag-key,Values=kubernetes.io/cluster/<cluster> --query 'Reservations[].Instances[].SubnetId' --output text
```

**FAIL when:** for every subnet used by the cluster or its nodes, available % = AvailableIpAddressCount / (2^(32 - prefix) - 5) x 100: below 20 (CRITICAL), below 40 (HIGH). The growth-plan row is not scored. The report shows subnet ID, prefix length and %, never the CIDR.

**Why (report line):** When a subnet runs out of IPs, new pods and nodes stay Pending.

**Source:** [EKS Best Practices - Optimizing IP Address Utilization](https://docs.aws.amazon.com/eks/latest/best-practices/ip-opt.html)

**What to check:**
1. Available IPs in each subnet used by nodes
2. Subnet utilization percentage
3. IPv6 cluster consideration for large deployments

**Finding logic:**
- Subnet < 20% available IPs -> CRITICAL
- Subnet < 40% available IPs -> HIGH
- No plan for IP growth -> MEDIUM

**Fix (YAML):**
```yaml
# VPC CNI custom networking: pods take IPs from a secondary CIDR subnet, one ENIConfig per AZ
apiVersion: crd.k8s.amazonaws.com/v1alpha1
kind: ENIConfig
metadata:
  name: <region>a
spec:
  subnet: <secondary-cidr-subnet-id>
  securityGroups:
  - <security-group-id>
```

---

## Check: NET-03 DNS Configuration

**Severity:** MEDIUM

**Check ID:** `NET-03` | **Scope level:** cluster | **Applies to:** any cluster | **Evaluation:** kubectl

**Evidence:**
```bash
kubectl get deploy -n kube-system -l k8s-app=kube-dns -o jsonpath='{range .items[*]}{.metadata.name} replicas={.spec.replicas}{"\n"}{end}'
kubectl get nodes --no-headers | wc -l
kubectl get hpa,deploy -n kube-system -o name | grep -Ei 'coredns|dns-autoscaler'
```

**FAIL when:** CoreDNS replicas < 2 (HIGH); more than 50 nodes and no CoreDNS autoscaling (HPA, cluster-proportional autoscaler or EKS add-on `autoScaling.enabled`) (MEDIUM). The ndots row is not scored.

**Why (report line):** Too few CoreDNS replicas make DNS the first thing to fail under load.

**Source:** [Debugging DNS Resolution](https://kubernetes.io/docs/tasks/administer-cluster/dns-debugging-resolution/)

**What to check:**
1. CoreDNS replicas (should be >= 2, scale with cluster size)
2. ndots configuration in pods (default 5 causes excessive DNS lookups)
3. DNS policy set appropriately

**Finding logic:**
- CoreDNS replicas < 2 -> HIGH
- CoreDNS without HPA on clusters > 50 nodes -> MEDIUM
- Pods with default ndots=5 causing performance issues -> LOW

**Fix (YAML):**
```yaml
# EKS managed CoreDNS add-on (eksctl ClusterConfig); other clusters: scale the coredns Deployment
addons:
- name: coredns
  configurationValues: |-
    replicaCount: 2
    autoScaling:
      enabled: true
      minReplicas: 2
      maxReplicas: 10
```

---

## Check: NET-04 Avoid hostPort and hostNetwork

**Severity:** MEDIUM

**Check ID:** `NET-04` | **Scope level:** namespace | **Applies to:** any cluster | **Evaluation:** kubectl

**Evidence:**
```bash
kubectl get deploy,sts,ds -n <ns> -o json | jq -r '.items[] | select(.spec.template.spec.hostNetwork == true or any(.spec.template.spec.containers[]; any((.ports // [])[]; .hostPort != null))) | "\(.kind)/\(.metadata.name) hostNetwork=\(.spec.template.spec.hostNetwork // false)"'
```

**FAIL when:** apply **Finding logic**. With `hostNetwork: true` the API sets `hostPort` automatically, so report only the hostNetwork row for that workload.

**Why (report line):** hostNetwork bypasses pod network isolation and hostPort limits where pods can schedule.

**Source:** [Service](https://kubernetes.io/docs/concepts/services-networking/service/)

**What to check:**
1. Pods using `hostPort` (limits scheduling, causes port conflicts)
2. Pods using `hostNetwork: true` (bypasses network isolation)
3. Exceptions: CNI plugins, kube-proxy (legitimate uses)

**Finding logic:**
- Application pod with hostNetwork -> HIGH
- Application pod with hostPort -> MEDIUM
- System pod with hostNetwork -> PASS (expected)

**Fix (YAML):**
```yaml
spec:
  template:
    spec:
      hostNetwork: false
      containers:
      - name: <container>
        ports:
        - containerPort: 8080   # no hostPort, expose it through a Service
---
apiVersion: v1
kind: Service
metadata:
  name: <app>
  namespace: <ns>
spec:
  selector:
    app.kubernetes.io/name: <app>
  ports:
  - port: 80
    targetPort: 8080
```

---

## Check: NET-05 Service Configuration

**Severity:** MEDIUM

**Check ID:** `NET-05` | **Scope level:** namespace | **Applies to:** any cluster | **Evaluation:** kubectl

**Evidence:**
```bash
kubectl get services -n <ns> -o json | jq -r '.items[] | "Service/\(.metadata.name) type=\(.spec.type) headless=\(.spec.clusterIP == "None") selector=\(.spec.selector != null) lbScheme=\(.metadata.annotations // {} | has("service.beta.kubernetes.io/aws-load-balancer-scheme") or has("service.beta.kubernetes.io/aws-load-balancer-internal"))"'
kubectl get endpointslices -n <ns> -o json | jq -r '[.items[] | {svc: .metadata.labels["kubernetes.io/service-name"], ready: ([.endpoints[]? | select(.conditions.ready == true)] | length)}] | group_by(.svc) | .[] | "Service/\(.[0].svc) readyEndpoints=\(map(.ready) | add)"'
```

**FAIL when:** a Service with a selector, not headless and not `ExternalName`, has zero ready endpoints (HIGH); on EKS, a `LoadBalancer` Service has no scheme annotation (MEDIUM).

**Why (report line):** A Service with no ready endpoints answers every request with a connection error.

**Source:** [Service](https://kubernetes.io/docs/concepts/services-networking/service/)

**What to check:**
1. Services without selectors (headless or external)
2. LoadBalancer services without annotations for internal/external
3. Services with no matching endpoints

**Finding logic:**
- Service with empty endpoints (not headless) -> HIGH
- LoadBalancer without scheme annotation -> MEDIUM

**Fix (YAML):**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: <svc>
  namespace: <ns>
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-scheme: internal
spec:
  type: LoadBalancer
  selector:
    app.kubernetes.io/name: <app>   # must match the pod template labels
  ports:
  - port: 80
    targetPort: 8080
```

---

## Check: NET-06 Ingress Controller Configuration

**Severity:** MEDIUM

**Check ID:** `NET-06` | **Scope level:** namespace | **Applies to:** any cluster | **Evaluation:** kubectl

**Evidence:**
```bash
kubectl get ingress -n <ns> -o json | jq -r '.items[] | (.metadata.annotations // {}) as $a | "Ingress/\(.metadata.name) tls=\((.spec.tls // []) | length > 0) albCert=\($a | has("alb.ingress.kubernetes.io/certificate-arn")) albHttps=\(($a["alb.ingress.kubernetes.io/listen-ports"] // "") | test("HTTPS"))"'
kubectl get deploy -A -o json | jq -r '.items[] | select(.metadata.name | test("ingress-nginx-controller|aws-load-balancer-controller|traefik|haproxy-ingress")) | "\(.metadata.namespace)/Deployment/\(.metadata.name) replicas=\(.spec.replicas)"'
```

**FAIL when:** an Ingress has none of `spec.tls`, the `alb.ingress.kubernetes.io/certificate-arn` annotation or an HTTPS `listen-ports` annotation (HIGH). The single-replica controller row (MEDIUM) is evaluated only in cluster-scope runs. No Ingress in scope = PASS.

**Why (report line):** An Ingress without TLS sends credentials and session data in clear text.

**Source:** [Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/)

**What to check:**
1. Ingress controller deployed and healthy
2. Multiple replicas for HA
3. TLS termination configured
4. Ingress resources without TLS

**Finding logic:**
- Ingress without TLS -> HIGH
- Single replica ingress controller -> MEDIUM

**Fix (YAML):**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: <ingress>
  namespace: <ns>
  # AWS Load Balancer Controller: use alb.ingress.kubernetes.io/certificate-arn instead of spec.tls
spec:
  tls:
  - hosts: ["<host>"]
    secretName: <tls-secret>
  rules:
  - host: <host>
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: <svc>
            port:
              number: 80
```

---

## Check: NET-07 Security Groups for Pods (EKS)

**Severity:** LOW

**Check ID:** `NET-07` | **Scope level:** cluster | **Applies to:** EKS only | **Evaluation:** guidance

**Evidence:**
```bash
kubectl get securitygrouppolicies.vpcresources.k8s.aws -A -o name 2>/dev/null
```

**FAIL when:** guidance only, always NOT_EVALUATED: which pods need their own security group is a design decision kubectl cannot see. The command lists existing policies as context.

**Why (report line):** Pods that reach RDS or other VPC resources need per-pod security groups to apply least privilege.

**Source:** [Assign security groups to individual Pods](https://docs.aws.amazon.com/eks/latest/userguide/security-groups-for-pods.html)

**What to check:**
1. SecurityGroupPolicy resources defined
2. Pods that need fine-grained network access using SGP

**Fix (YAML):**
```yaml
apiVersion: vpcresources.k8s.aws/v1beta1
kind: SecurityGroupPolicy
metadata:
  name: <app>
  namespace: <ns>
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: <app>
  securityGroups:
    groupIds:
    - <security-group-id>
```

---

## Check: NET-08 Service Mesh Health

**Severity:** LOW (only if mesh is deployed)

**Check ID:** `NET-08` | **Scope level:** namespace | **Applies to:** any cluster | **Evaluation:** kubectl

**Evidence:**
```bash
kubectl get crd -o name | grep -E 'istio.io|linkerd.io'
kubectl get namespace <ns> -o json | jq -r '{labels: .metadata.labels, annotations: .metadata.annotations}'
kubectl get pods -n <ns> -o json | jq -r '.items[] | select(all(.spec.containers[]; .name != "istio-proxy" and .name != "linkerd-proxy") and all((.spec.initContainers // [])[]; .name != "istio-proxy" and .name != "linkerd-proxy")) | "\(.metadata.ownerReferences[0].kind // "Pod")/\(.metadata.ownerReferences[0].name // .metadata.name)"'
kubectl get peerauthentications.security.istio.io -A -o json | jq -r '.items[] | "\(.metadata.namespace)/\(.metadata.name) mode=\(.spec.mtls.mode // "UNSET")"'
```

**FAIL when:** no mesh CRDs = PASS (not applicable). Meshed namespace = label `istio-injection=enabled`, label `istio.io/rev`, or annotation `linkerd.io/inject: enabled`. Then: no STRICT PeerAuthentication in the namespace or in the mesh root namespace (MEDIUM); a pod in a meshed namespace without sidecar (MEDIUM); mesh control plane Deployment not fully available (HIGH, cluster-scope runs only).

**Why (report line):** A mesh in permissive mode or with unmeshed pods gives a false sense of mTLS everywhere.

**Source:** [Istio PeerAuthentication](https://istio.io/latest/docs/reference/config/security/peer_authentication/)

**What to check:**
1. Istio/Linkerd sidecar injection enabled
2. Pods without sidecar in meshed namespaces
3. mTLS mode (strict vs permissive)

**Finding logic:**
- Mesh installed but mTLS in permissive mode -> MEDIUM
- Pods in meshed namespace without sidecar -> MEDIUM
- Mesh control plane unhealthy -> HIGH

**Fix (YAML):**
```yaml
apiVersion: security.istio.io/v1
kind: PeerAuthentication
metadata:
  name: default
  namespace: <ns>
spec:
  mtls:
    mode: STRICT
```
