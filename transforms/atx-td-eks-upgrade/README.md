# ATX Custom TD: EKS Version Upgrade Readiness & Code Migration

## Objetivo

Custom Transformation Definition para o AWS Transform que analisa e transforma código de clientes (manifests K8s, Helm charts, Terraform, CDK, Kustomize) para compatibilidade com uma versão target do Amazon EKS/Kubernetes.

## Fluxo da TD

```text
Input: Repo do cliente + Target EKS version (via additionalPlanContext)
  |
  +-- 1. Scan: identifica todos os manifests/charts/configs
  +-- 2. Detect: mapeia APIs deprecadas/removidas na versao target
  +-- 3. Transform: atualiza apiVersions, campos, e configs automaticamente
  +-- 4. Validate: dry-run / helm template / terraform validate
  +-- 5. Report: gera relatorio de breaking changes + acoes manuais
```

## Uso

```bash
atx custom def exec \
  -n eks-version-upgrade-readiness \
  -p /path/to/customer-repo \
  -x -t \
  --configuration 'additionalPlanContext=Target EKS version 1.32. Upgrade from 1.28.'
```

## Complemento ao EKS Upgrade Controller

- **Upgrade Controller** = cuida do CLUSTER (control plane + data plane version)
- **Esta TD** = cuida do CODIGO (manifests, charts, configs que rodam NO cluster)

Juntos, oferecem upgrade end-to-end: codigo preparado + cluster atualizado automaticamente.

## Arquivos de Referencia

- `api-removals-by-version.md` - Tabela completa de APIs removidas por versao K8s
- `eks-specific-changes.md` - Mudancas especificas do EKS por versao
- `examples-before-after.md` - Exemplos de transformacao (antes/depois)
- `td-description.md` - Descricao e prompt para criacao da TD com `atx -t`
