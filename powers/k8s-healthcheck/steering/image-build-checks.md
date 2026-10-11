# Image Build Checks

## Overview

Container image build best practices validation based on:
- [AWS Well-Architected Container Build Lens](https://docs.aws.amazon.com/wellarchitected/latest/container-build-lens/container-build-lens.html)
- [EKS Best Practices - Image Security](https://docs.aws.amazon.com/eks/latest/best-practices/security.html)

**Note:** These checks are partially runtime-verifiable and partially guidance-based.

Every check below carries a stable **Check ID**, its evidence commands, the exact FAIL condition and a fixed report line. The catalog of all IDs, the scoring formula and the report format live in `POWER.md`.

---

## Check: IMG-01 Image Tags and Immutability

**Severity:** HIGH

**Check ID:** `IMG-01` | **Scope level:** namespace | **Applies to:** any cluster | **Evaluation:** kubectl

**Evidence:**
```bash
kubectl get deploy,sts,ds -n <ns> -o json | jq -r '.items[] | . as $w | .spec.template.spec.containers[] | select((.image | test("@sha256:") | not) and ((.image | test(":[^/:]+$") | not) or (.image | endswith(":latest")) or .imagePullPolicy != "Always")) | "\($w.kind)/\($w.metadata.name) container=\(.name) pullPolicy=\(.imagePullPolicy)"'
```

**FAIL when:** apply **Finding logic**: `:latest` or no tag (HIGH, every namespace counts as production unless the prompt says dev or test); a tag without digest and `imagePullPolicy` other than `Always` (MEDIUM).

**Why (report line):** A mutable tag means two pods of the same Deployment can run different code.

**Source:** [Images](https://kubernetes.io/docs/concepts/containers/images/)

**What to check:**
1. Containers using `:latest` tag
2. Containers using mutable tags (no SHA digest)
3. Containers with no tag specified (implies `:latest`)
4. Image pull policy not set to `Always` for mutable tags

**Finding logic:**
- Using `:latest` in production -> HIGH
- Using mutable tag without `imagePullPolicy: Always` -> MEDIUM
- Using SHA digest -> PASS

**Recommendation:**
- Use SHA digests for production: `image: myapp@sha256:abc123...`
- At minimum use semantic version tags: `image: myapp:1.2.3`
- Enable tag immutability in ECR

**Fix (YAML):**
```yaml
containers:
- name: <container>
  image: <registry>/<repo>@sha256:<digest>   # or an immutable version tag with ECR tag immutability
  imagePullPolicy: IfNotPresent
```

---

## Check: IMG-02 Base Image Selection

**Severity:** MEDIUM (advisory)

**Check ID:** `IMG-02` | **Scope level:** namespace | **Applies to:** any cluster | **Evaluation:** kubectl

**Evidence:**
```bash
kubectl get deploy,sts,ds -n <ns> -o json | jq -r '.items[] | . as $w | .spec.template.spec.containers[] | (.image | split("@")[0] | split("/") | last | split(":")[0]) as $repo | select($repo | test("^(ubuntu|debian|centos|fedora|amazonlinux|rockylinux|almalinux|oraclelinux|ubi[0-9]*)$")) | "\($w.kind)/\($w.metadata.name) container=\(.name) base=\($repo)"'
```

**FAIL when:** a container runs a full OS image directly (MEDIUM). When nothing matches the check is NOT_EVALUATED, never PASS: the base layer of an application image is not visible to kubectl.

**Why (report line):** Full OS images ship hundreds of packages, each one a CVE you have to patch.

**Source:** [AWS Well-Architected Container Build Lens](https://docs.aws.amazon.com/wellarchitected/latest/container-build-lens/container-build-lens.html)

**What to check:**
1. Containers using full OS base images (ubuntu, centos)
2. Containers using distroless or minimal base images
3. Base image age (old images accumulate CVEs)

**Finding logic:**
- Base image is full OS (ubuntu:22.04) -> MEDIUM
- Base image is minimal (alpine, distroless) -> PASS
- Base image is `scratch` -> PASS

**Recommendation:**
- Use minimal base images (distroless, alpine, or scratch)
- Regularly update base images (monthly)
- Pin base image version with digest
- Consider multi-arch for Graviton

**Fix:** not a manifest change: rebuild the image on a minimal base (distroless, alpine or scratch), see the IMG-03 Dockerfile.

---

## Check: IMG-03 Multi-Stage Build Indicators

**Severity:** LOW (advisory)

**Check ID:** `IMG-03` | **Scope level:** namespace | **Applies to:** any cluster | **Evaluation:** guidance

**Evidence:**
```bash
aws ecr describe-images --region <region> --repository-name <repo> --image-ids imageTag=<tag> --query 'imageDetails[0].imageSizeInBytes'
```

**FAIL when:** guidance only, NOT_EVALUATED unless image size or a Dockerfile is provided; then apply **Finding logic**.

**Why (report line):** Build tools left in the runtime image grow the attack surface and the pull time.

**Source:** [AWS Well-Architected Container Build Lens](https://docs.aws.amazon.com/wellarchitected/latest/container-build-lens/container-build-lens.html)

**What to check:**
1. Image size (large images suggest no multi-stage build)
2. Build tools present in runtime image

**Finding logic:**
- Build tools found in running container -> MEDIUM
- Image > 1GB -> MEDIUM (likely unoptimized)
- Image < 100MB for Go/Rust app -> PASS

**Recommendation:**
```dockerfile
# Build stage
FROM golang:1.22 AS builder
WORKDIR /app
COPY . .
RUN CGO_ENABLED=0 go build -o /app/server

# Runtime stage
FROM gcr.io/distroless/static:nonroot
COPY --from=builder /app/server /server
USER 65534
ENTRYPOINT ["/server"]
```

**Fix:** not a manifest change: use the multi-stage Dockerfile in the Recommendation.

---

## Check: IMG-04 Image Scanning and Vulnerabilities

**Severity:** HIGH

**Check ID:** `IMG-04` | **Scope level:** cluster | **Applies to:** any cluster | **Evaluation:** kubectl

**Evidence:**
```bash
kubectl get validatingwebhookconfigurations,mutatingwebhookconfigurations -o name | grep -Ei 'kyverno|gatekeeper|ratify|policy-controller|connaisseur|trivy|neuvector|kubewarden'
```

**FAIL when:** no admission webhook of a known image policy engine (MEDIUM). When one exists the check PASSes and the enforce versus audit mode is listed under Not checked.

**Why (report line):** Without an admission gate, an image with a known CRITICAL CVE can reach production.

**Source:** [EKS Best Practices - Image security](https://docs.aws.amazon.com/eks/latest/best-practices/image-security.html)

**What to check:**
1. ECR image scanning enabled
2. Admission controller enforcing scan results
3. Scan results freshness (within last 30 days)

**Finding logic:**
- No image scanning admission controller -> MEDIUM
- Admission controller in audit mode -> LOW
- Admission controller in enforce mode -> PASS

**Recommendation:**
- Enable ECR enhanced scanning (Inspector)
- Deploy admission controller to block CRITICAL CVEs
- Integrate scanning into CI/CD (shift-left)

**Fix:** not a single manifest: install an admission policy engine (Kyverno, Gatekeeper, Ratify) in enforce mode and enable ECR enhanced scanning.

---

## Check: IMG-05 Registry Configuration

**Severity:** MEDIUM

**Check ID:** `IMG-05` | **Scope level:** namespace | **Applies to:** any cluster | **Evaluation:** kubectl

**Evidence:**
```bash
kubectl get deploy,sts,ds -n <ns> -o json | jq -r '.items[] | . as $w | .spec.template.spec.containers[] | (.image | split("/")) as $p | select(($p | length) == 1 or (($p[0] | test("[.:]") or . == "localhost") | not) or ($p[0] | IN("docker.io", "index.docker.io"))) | "\($w.kind)/\($w.metadata.name) container=\(.name)"'
kubectl get pods -n <ns> -o json | jq -r '.items[] | select(any(.status.containerStatuses[]?; .state.waiting.reason == "ImagePullBackOff" or .state.waiting.reason == "ErrImagePull")) | "\(.metadata.ownerReferences[0].kind // "Pod")/\(.metadata.ownerReferences[0].name // .metadata.name)"'
```

**FAIL when:** an image comes from `docker.io` (including no registry host) (MEDIUM); a pod is in `ImagePullBackOff` or `ErrImagePull` (HIGH). The pull failure is the observable form of the "missing imagePullSecrets" row.

**Why (report line):** Docker Hub rate limits and missing pull secrets stop pods from starting during a scale-out.

**Source:** [Images](https://kubernetes.io/docs/concepts/containers/images/)

**What to check:**
1. Pulling from public registries (docker.io) in production
2. ECR pull-through cache configured
3. Image pull secrets configured

**Finding logic:**
- Production pods pulling from docker.io -> MEDIUM (rate limits)
- Using private ECR -> PASS
- Missing imagePullSecrets for private registry -> HIGH

**Fix (YAML):**
```yaml
spec:
  template:
    spec:
      imagePullSecrets:
      - name: <registry-secret>   # not needed for ECR, which uses the node or pod role
      containers:
      - name: <container>
        image: <private-registry>/<repo>:<version>   # or an ECR pull-through cache repository
```

---

## Check: IMG-06 Image Signing and Provenance

**Severity:** LOW (advisory)

**Check ID:** `IMG-06` | **Scope level:** cluster | **Applies to:** any cluster | **Evaluation:** guidance

**Evidence:**
```bash
kubectl get validatingwebhookconfigurations,mutatingwebhookconfigurations -o name | grep -Ei 'kyverno|policy-controller|ratify|connaisseur'
```

**FAIL when:** guidance only, always NOT_EVALUATED: a policy engine webhook does not prove that a signature policy exists.

**Why (report line):** Without signature verification the cluster cannot tell your image from a tampered one.

**Source:** [EKS Best Practices - Image security](https://docs.aws.amazon.com/eks/latest/best-practices/image-security.html)

**What to check:**
1. Images signed with Sigstore/cosign
2. SBOM attached to images
3. Admission controller verifying signatures

**Recommendation:**
- Sign images with cosign in CI/CD
- Generate and attach SBOM (syft, trivy)
- Target SLSA Level 2+ for critical workloads

**Fix:** not a manifest change: sign in CI with cosign and verify at admission.

---

## Check: IMG-07 Layer Optimization

**Severity:** LOW (advisory)

**Check ID:** `IMG-07` | **Scope level:** namespace | **Applies to:** any cluster | **Evaluation:** guidance

**Evidence:**
```bash
docker history --no-trunc <image>
```

**FAIL when:** guidance only, always NOT_EVALUATED: layers are not visible to kubectl.

**Why (report line):** Extra layers and caches slow every pull, and secrets in a layer stay readable forever.

**Source:** [AWS Well-Architected Container Build Lens](https://docs.aws.amazon.com/wellarchitected/latest/container-build-lens/container-build-lens.html)

**What to check:**
1. Image layer count (excessive layers)
2. Unnecessary files in image
3. Package manager cache not cleaned
4. Secrets baked into image layers

**Recommendation:**
- Combine related RUN commands
- Clean package manager caches in the same layer
- Use `.dockerignore`
- Never store secrets in Dockerfile

**Fix:** not a manifest change: see the Recommendation.

---

## Check: IMG-08 Non-Root User

**Severity:** HIGH

**Check ID:** `IMG-08` | **Scope level:** namespace | **Applies to:** any cluster | **Evaluation:** kubectl

**Evidence:**
```bash
kubectl get deploy,sts,ds -n <ns> -o json | jq -r '.items[] | .spec.template.spec as $p | . as $w | $p.containers[] | select(((if .securityContext.runAsNonRoot == null then $p.securityContext.runAsNonRoot else .securityContext.runAsNonRoot end) != true) and (((if .securityContext.runAsUser == null then $p.securityContext.runAsUser else .securityContext.runAsUser end) // 0) == 0)) | "\($w.kind)/\($w.metadata.name) container=\(.name)"'
```

**FAIL when:** neither container nor pod sets `runAsNonRoot: true` or a `runAsUser` above 0 (HIGH); a workload the prompt names as an accepted exception (MEDIUM). Spec-based: an image `USER` directive is not visible to kubectl, so set it explicitly.

**Why (report line):** A process running as root inside the container is one kernel bug away from root on the node.

**Source:** [Configure a Security Context for a Pod or Container](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/)

**What to check:**
1. Containers running as root (UID 0)
2. Pod securityContext not setting `runAsNonRoot: true`

**Finding logic:**
- Running as root without override -> HIGH
- Running as root with justification -> MEDIUM
- Running as non-root -> PASS

**Recommendation:**
```dockerfile
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser
```
```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
```
