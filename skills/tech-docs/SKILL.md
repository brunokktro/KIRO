---
name: tech-docs
description: "Generate structured technical documentation for cloud projects following a standardized wiki format. Reads infrastructure code (Terraform, Kubernetes YAMLs, ArgoCD, kro, ACK) from the workspace to auto-populate architecture, infra, and integration sections. Outputs individual Markdown files per solution with a navigable index. Trigger on mentions of 'documentar projeto', 'wiki técnica', 'doc FSI', 'escopo técnico', 'tech-docs', 'documentação técnica', or 'wiki do projeto'."
metadata:
  author: Bruno Lopes
  version: "1.0"
---

# Tech Docs — Technical Documentation Generator

## Purpose
Generate standardized technical documentation for cloud projects (primarily FSI/regulated environments on AWS). Produces a set of interconnected Markdown files ready for Azure DevOps Wikis (repo-based markdown wikis with hyperlinks).

## When to use
- Documenting a new cloud project or solution for a client
- Creating wiki-style technical docs from existing infrastructure code
- Standardizing documentation across multiple solutions in a single project
- User mentions: "documentar projeto", "wiki técnica", "doc FSI", "escopo técnico", "documentação técnica", "wiki do projeto"

## Core Principles
1. **Code-driven documentation** — read Terraform, K8s manifests, ArgoCD apps, kro ResourceGroups, and ACK resources from the workspace to extract real infrastructure context
2. **Standardized structure** — every solution follows the same subsection template (see references/solution-template.md)
3. **Navigable output** — an index file with hyperlinks to all solution docs
4. **Incremental** — can document one solution at a time or batch-generate all
5. **Reusable** — the template works for any project, not just FSI

## Knowledge Sourcing (MCP-first)

Before generating documentation content, ALWAYS consult authoritative sources:
- Use `mcp_knowledge_mcp_server_aws___search_documentation` to verify AWS service details, configurations, and best practices
- Use `mcp_knowledge_mcp_server_aws___read_documentation` to read specific service pages for accurate descriptions
- Ground all technical descriptions in verified, current information
- Fall back to web search only when MCP returns no results

## Output Structure

```
docs/
├── index.md                          # Project index with TOC and hyperlinks
├── 01-introducao.md                  # Introduction
├── 02-visao-geral-{solution-slug}.md # One per solution (e.g., 02-visao-geral-novo-ambiente-pix.md)
├── 03-visao-geral-{solution-slug}.md # Next solution
├── ...
├── parceiros.md                      # Partners
├── contatos.md                       # Support contacts
└── glossario.md                      # Glossary
```

Each solution file follows the standard template from `references/solution-template.md`.

## Workflow

### Phase 1: Discovery
1. User activates skill and provides project context (client, solutions list, repo location)
2. Scan the workspace for infrastructure code:
   - `**/*.tf` — Terraform files (VPCs, EKS clusters, RDS, S3, IAM, etc.)
   - `**/*.yaml`, `**/*.yml` — Kubernetes manifests, ArgoCD Applications, kro ResourceGroups, ACK resources
   - `**/Chart.yaml` — Helm charts
   - `**/kustomization.yaml` — Kustomize overlays
   - `**/Dockerfile` — Container definitions
3. Build an infrastructure map: what services exist, how they connect, what environments are defined
4. Present the discovered infrastructure summary to the user for validation

### Phase 2: Structure
1. Confirm the list of solutions to document (e.g., "Novo Ambiente PIX", "Circuit Breaker", "Monitoramento")
2. Generate the `index.md` with the full TOC and hyperlinks
3. Generate `01-introducao.md` with project-level context

### Phase 3: Solution Documentation
For each solution:
1. Generate the solution markdown using the standard template
2. Auto-populate sections that can be inferred from code:
   - **Arquitetura**: inferred from Terraform modules and K8s resources
   - **Infraestrutura e Ambientes**: from Terraform workspaces/tfvars and K8s namespaces
   - **Repositórios**: from git remotes and ArgoCD source configs
   - **Banco de Dados**: from RDS/DynamoDB Terraform resources or K8s StatefulSets
   - **Integrações e APIs**: from K8s Services, Ingress, API Gateway Terraform resources
   - **Autenticação e Segurança**: from IAM roles, IRSA, NetworkPolicies, SecurityGroups
   - **Observabilidade e Monitoramento**: from CloudWatch, Prometheus, Grafana configs
3. Mark sections that need manual input with `<!-- TODO: preencher manualmente -->`
4. Present each solution doc to the user for review before moving to the next

### Phase 4: Supporting Docs
1. Generate `parceiros.md` using the template from `assets/parceiros-template.md` — includes partner table, per-partner detail sections, SLA and scope fields
2. Generate `contatos.md` using the template from `assets/contatos-template.md` — includes internal team contacts, AWS support channels, escalation flow (Mermaid), and communication channels
3. Generate `glossario.md` using the template from `assets/glossario-template.md` — pre-populated with common AWS/K8s/FSI terms, user adds project-specific terms
4. All three files use `<!-- TODO -->` markers for fields that need manual input
5. User reviews and fills in the specifics

## Infrastructure Code Reading Rules

### Terraform
- Parse `resource`, `module`, and `data` blocks to identify AWS services
- Read `variables.tf` and `terraform.tfvars` for environment-specific configs
- Check `backend` config for state management details
- Look for `locals` blocks for naming conventions and tags

### Kubernetes / ArgoCD / kro / ACK
- Parse `kind` and `apiVersion` to identify resource types
- ArgoCD `Application` resources → map repos, paths, and target clusters
- kro `ResourceGroup` → map composite resources and their dependencies
- ACK resources → map AWS services managed via K8s controllers
- Read `namespace` to infer environment separation
- Check `annotations` and `labels` for metadata (team, app, environment)

### Inference Rules
- If a Terraform resource exists but no K8s manifest references it → document as "infra-only" component
- If a K8s manifest references a service not in Terraform → flag as "externally managed" with a TODO
- Cross-reference ArgoCD apps with Terraform modules to build the full deployment picture

## Formatting Rules
- Language: Portuguese (PT-BR) for all documentation content
- Technical terms in English when they are industry standard (Terraform, Kubernetes, ArgoCD, etc.)
- Use Markdown tables for structured data (RACI, environments, access matrix)
- Use Mermaid diagrams for architecture and flow diagrams (Azure DevOps Wikis support Mermaid)
- Code blocks with syntax highlighting for configs and commands
- Every section that cannot be auto-populated gets a `<!-- TODO: preencher manualmente -->` marker
- Hyperlinks between docs use relative paths (e.g., `[Novo Ambiente PIX](02-visao-geral-novo-ambiente-pix.md)`)

## Quality Checklist
- [ ] index.md has working hyperlinks to all solution docs
- [ ] Every solution doc follows the standard template
- [ ] Auto-populated sections are grounded in actual code from the repo
- [ ] TODO markers are present for sections needing manual input
- [ ] Mermaid diagrams render correctly
- [ ] No fabricated service names or configurations
- [ ] Portuguese language throughout (except technical terms)
- [ ] Relative hyperlinks work for Azure DevOps Wiki navigation

## Reference
See [solution-template.md](references/solution-template.md) for the standard subsection template used for every solution.
