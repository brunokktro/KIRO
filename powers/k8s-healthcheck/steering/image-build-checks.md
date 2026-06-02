# Image Build Checks

## Overview

Container image build best practices validation based on:
- [AWS Well-Architected Container Build Lens](https://docs.aws.amazon.com/wellarchitected/latest/container-build-lens/container-build-lens.html)
- [EKS Best Practices - Image Security](https://docs.aws.amazon.com/eks/latest/best-practices/security.html)

**Note:** These checks are partially runtime-verifiable and partially guidance-based.

---

## Check: Image Tags and Immutability

**Severity:** HIGH

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

---

## Check: Base Image Selection

**Severity:** MEDIUM (advisory)

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

---

## Check: Multi-Stage Build Indicators

**Severity:** LOW (advisory)

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

---

## Check: Image Scanning and Vulnerabilities

**Severity:** HIGH

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

---

## Check: Registry Configuration

**Severity:** MEDIUM

**What to check:**
1. Pulling from public registries (docker.io) in production
2. ECR pull-through cache configured
3. Image pull secrets configured

**Finding logic:**
- Production pods pulling from docker.io -> MEDIUM (rate limits)
- Using private ECR -> PASS
- Missing imagePullSecrets for private registry -> HIGH

---

## Check: Image Signing and Provenance

**Severity:** LOW (advisory)

**What to check:**
1. Images signed with Sigstore/cosign
2. SBOM attached to images
3. Admission controller verifying signatures

**Recommendation:**
- Sign images with cosign in CI/CD
- Generate and attach SBOM (syft, trivy)
- Target SLSA Level 2+ for critical workloads

---

## Check: Layer Optimization

**Severity:** LOW (advisory)

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

---

## Check: Non-Root User

**Severity:** HIGH

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
