# Challenge Catalog

Pre-built challenges organized by topic with difficulty levels (Lv200-Lv400). The mentor also sources 2 additional challenges per topic via web search from real community forums.

**Level reference:**
- **Lv200** (Intermediate): Single-component, configuration/debugging
- **Lv300** (Advanced): Multi-component, edge cases, deep dive
- **Lv400** (Expert): Production incidents, complex multi-layer, design trade-offs

---

## Storage (PV/PVC)

### PV/PVC: O Volume que Não Monta (Lv200)
**Contexto:** Um desenvolvedor criou um PVC pedindo 10Gi de storage, mas o Pod fica em Pending.
**Sintomas:** Pod stuck em Pending, evento "no persistent volumes available for this claim"
**Root cause:** PV existe mas com `storageClassName` diferente do PVC, ou capacity insuficiente.
**Conceitos:** StorageClass, PV/PVC binding, access modes (RWO/RWX/ROX)
**Dica L1:** "Compara o PV e o PVC lado a lado — o que precisa bater pra eles se conectarem?"

### ConfigMap: A Variável Fantasma (Lv200)
**Contexto:** Deploy atualizado com novo ConfigMap, mas o Pod ainda mostra o valor antigo.
**Sintomas:** `kubectl exec` mostra variável de ambiente com valor desatualizado.
**Root cause:** Env vars de ConfigMap não atualizam automaticamente — precisa restart do Pod. Volumes sim (com delay).
**Conceitos:** ConfigMap como env vs volume mount, immutability, rollout restart
**Dica L1:** "Como o Pod consome esse ConfigMap — como env var ou como volume?"

### Secret: Decode ou Bust (Lv200)
**Contexto:** Aplicação crashando com "invalid credentials" mas o Secret parece correto.
**Sintomas:** CrashLoopBackOff, logs mostram auth failure.
**Root cause:** Secret foi criado com valor já em base64, resultando em double-encoding.
**Conceitos:** base64 encoding, `stringData` vs `data`, `kubectl create secret`
**Dica L1:** "Decodifica o Secret e vê se o valor faz sentido — `kubectl get secret X -o jsonpath='{.data.password}' | base64 -d`"

---

## Networking

### Service: O ClusterIP Inacessível (Lv200)
**Contexto:** Service criado mas curl de outro Pod retorna "connection refused".
**Sintomas:** `curl service-name:8080` falha, mas o Pod tá Running.
**Root cause:** Selector do Service não bate com labels do Pod, ou targetPort errado.
**Conceitos:** Label selectors, port vs targetPort, endpoints
**Dica L1:** "Verifica se o Service tem endpoints: `kubectl get endpoints service-name`"

### DNS: O Pod que Não Resolve Nomes (Lv300)
**Contexto:** Pod não consegue resolver nomes de outros Services.
**Sintomas:** `nslookup service-name` retorna NXDOMAIN de dentro do Pod.
**Root cause:** CoreDNS não está rodando, ou Pod com `dnsPolicy: None` sem config.
**Conceitos:** CoreDNS, dnsPolicy, /etc/resolv.conf, FQDN patterns
**Dica L1:** "Olha o /etc/resolv.conf dentro do Pod — o nameserver tá apontando pra onde?"

### NetworkPolicy: O Bloqueio Invisível (Lv300)
**Contexto:** Após aplicar NetworkPolicy, um microservice parou de se comunicar com o banco.
**Sintomas:** Timeout em conexões que antes funcionavam.
**Root cause:** NetworkPolicy é deny-by-default quando aplicada. Faltou regra de egress.
**Conceitos:** Ingress vs Egress, podSelector, namespaceSelector, default deny
**Dica L1:** "NetworkPolicy aplicada = tudo que não tá explicitamente permitido é bloqueado. Olha se tem regra de egress."

---

## Scheduling & Resources

### O Pod que Nunca é Agendado (Lv200)
**Contexto:** Pod fica Pending indefinidamente num cluster com nodes disponíveis.
**Sintomas:** Pending, evento "Insufficient cpu" ou "didn't match Pod's node affinity/selector".
**Root cause:** Resource requests maiores que capacity disponível, ou node affinity/taint sem match.
**Conceitos:** requests vs limits, node affinity, taints/tolerations, describe node allocatable
**Dica L1:** "Roda `kubectl describe pod` e olha a seção Events — o scheduler te diz exatamente por que não agendou."

### OOMKilled: O Assassino Silencioso (Lv300)
**Contexto:** Pod reinicia periodicamente sem erro aparente nos logs da aplicação.
**Sintomas:** `kubectl get pod` mostra restarts crescentes, `Last State: OOMKilled`.
**Root cause:** Memory limit muito baixo para o workload, ou memory leak na aplicação.
**Conceitos:** requests vs limits, OOMKilled exit code 137, QoS classes, resource monitoring
**Dica L1:** "Olha o `Last State` do container — `kubectl describe pod X` e procura por OOMKilled."

---

## Security (RBAC)

### RBAC: O ServiceAccount Sem Poder (Lv200)
**Contexto:** Aplicação precisa listar Pods mas recebe "forbidden".
**Sintomas:** Logs mostram `403 Forbidden: pods is forbidden: User "system:serviceaccount:default:app-sa"`
**Root cause:** Falta Role + RoleBinding vinculando o ServiceAccount ao verbo "list" em "pods".
**Conceitos:** ServiceAccount, Role, RoleBinding, verbs, resources, API groups
**Dica L1:** "O erro te diz exatamente quem tá tentando e o que falta. Que tipo de objeto dá permissão pra um ServiceAccount?"

### SecurityContext: O Container Root (Lv300)
**Contexto:** Pod rejeitado pelo admission controller com "must not run as root".
**Sintomas:** Pod falha na criação, evento menciona PodSecurity ou OPA/Kyverno violation.
**Root cause:** Container image roda como root por padrão, precisa de `securityContext.runAsNonRoot: true` + user no Dockerfile.
**Conceitos:** SecurityContext, runAsNonRoot, runAsUser, Pod Security Standards (restricted/baseline/privileged)
**Dica L1:** "Quem é o user que roda dentro do container? Verifica com `kubectl exec -- id`... ah, mas o Pod nem sobe né? Então olha o Dockerfile."

---

## Troubleshooting

### O Pod Terminating Eterno (Lv300)
**Contexto:** Pod stuck em Terminating há 30 minutos após um `kubectl delete`.
**Sintomas:** `kubectl get pod` mostra Terminating, `kubectl delete pod --grace-period=0` não resolve.
**Root cause:** Finalizer custom que não completa, ou node desconectado impedindo kubelet de confirmar deletion.
**Conceitos:** Finalizers, graceful shutdown, preStop hooks, force delete, node NotReady
**Dica L1:** "Tem finalizer nesse Pod? `kubectl get pod X -o jsonpath='{.metadata.finalizers}'`"

### CrashLoopBackOff: O Mistério do Exit Code 137 (Lv400)
**Contexto:** Pod entra em CrashLoopBackOff imediatamente após deploy, mas a imagem funciona localmente.
**Sintomas:** Container inicia, roda por 10-30 segundos, morre com exit code 137.
**Root cause:** Liveness probe falhando porque a aplicação demora pra iniciar (precisa de startupProbe), ou OOMKilled.
**Conceitos:** Probes (liveness vs readiness vs startup), initialDelaySeconds, exit codes, container lifecycle
**Dica L1:** "Exit code 137 = o processo foi killed externamente. Duas possibilidades: OOM ou probe. Investiga qual."

---

## EKS-Specific

### Pod Identity: O Pod que Não Acessa S3 (Lv300)
**Contexto:** Aplicação em EKS precisa ler de um bucket S3 mas recebe AccessDenied.
**Sintomas:** AWS SDK retorna `AccessDeniedException` ou `403 Forbidden`.
**Root cause:** Pod Identity association não configurada, ou IAM policy sem permissão pro bucket.
**Conceitos:** EKS Pod Identity, IRSA (legacy), ServiceAccount annotation, trust policy
**Dica L1:** "O Pod sabe que tem uma identidade AWS? Verifica se o ServiceAccount tá associado a um Pod Identity."

### Karpenter: Nodes que Não Escalam (Lv400)
**Contexto:** Pods Pending mas Karpenter não provisiona novos nodes.
**Sintomas:** Pods em Pending, Karpenter logs sem atividade ou com erros de launch.
**Root cause:** NodePool constraints muito restritivos, ou EC2 capacity insuficiente na AZ/instance type.
**Conceitos:** NodePool, EC2NodeClass, instance types, AZ balancing, consolidation
**Dica L1:** "Olha os logs do Karpenter controller — `kubectl logs -n kube-system -l app.kubernetes.io/name=karpenter`"

---

## Notes for the Mentor

- Challenges can be combined (e.g., "RBAC + NetworkPolicy" for a multi-layer security scenario)
- ALWAYS source 2 additional challenges per topic via web search, in addition to catalog entries
- Adapt difficulty based on how the learner handles each challenge
- If the learner solves without hints, increase complexity in the web-sourced challenges
- If the learner needs L3 hints consistently, simplify the next challenge
