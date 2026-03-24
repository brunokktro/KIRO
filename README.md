# Kiro — Skills, Powers & Steering

Uma coleção de customizações para o [Kiro](https://kiro.dev) — a IDE com assistente de IA integrado. Este repositório contém Skills (capacidades especializadas), Powers (integrações MCP) e templates de Steering (personalização do assistente) prontos para uso.

## O que é o Kiro?

[Kiro](https://kiro.dev) é uma IDE com assistente de IA que ajuda desenvolvedores a escrever, testar e manter código. O Kiro oferece diversas formas de personalização e extensão — para conhecer todas, veja a [documentação oficial](https://kiro.dev/docs/). Neste repositório, focamos em três delas:

- [**Steering**](#steering--personalizando-seu-assistente) — documentos markdown que personalizam o comportamento do assistente
- [**Skills**](#skills--capacidades-especializadas) — instruções especializadas que dão ao agente capacidades específicas
- [**Powers**](#powers--integrações-mcp) — integrações com serviços externos via Model Context Protocol (MCP)

> 📥 [Download do Kiro](https://kiro.dev/downloads/)

> 📂 **Pasta de configuração do Kiro:** os arquivos de personalização ficam na pasta `.kiro/` dentro do seu diretório home. No macOS/Linux é `~/.kiro/`, no Windows é `%USERPROFILE%\.kiro\`. Neste README, usamos `<KIRO_HOME>` para representar esse caminho.

### Pricing

O Kiro tem um **nível gratuito** usando o [AWS Builder ID](https://profile.aws.amazon.com/) — sem cartão de crédito, sem compromisso. Nos **primeiros 30 dias**, você ainda ganha **500 créditos de bônus** pra testar tudo.

**O que é 1 crédito?** Pense em créditos como tokens com peso variável. Prompts simples gastam menos de 1 crédito; tarefas complexas (como executar uma spec task) gastam mais. Modelos mais caros consomem mais créditos por prompt — por exemplo, Sonnet 4 custa ~1.3x mais que o modo Auto para a mesma tarefa. O menor consumo possível é 0.01 créditos.

Para detalhes completos, veja a [página de pricing do Kiro](https://kiro.dev/pricing/).

---

## Steering — Personalizando seu Assistente

Steering files são documentos markdown em `.kiro/steering/` que configuram como o assistente se comporta. Pense neles como **prompts permanentes** — em vez de repetir instruções a cada conversa, você documenta uma vez e o agente segue sempre.

### Tipos de inclusão

| Tipo | Quando carrega | Uso |
|------|---------------|-----|
| `auto` | Toda interação | Regras gerais, estilo de comunicação, protocolos |
| `manual` | Quando você chama `#nome` no chat | Contexto sob demanda (memória, referências) |
| `fileMatch` | Quando um arquivo específico é aberto | Regras por tipo de arquivo |

### Templates incluídos

Este repo inclui dois templates para você começar:

**[r2d2-template.md](steering/r2d2-template.md)** — Template do steering principal (`auto`)

> 🤖 Por que "R2D2"? Dar um nome ao steering torna o conceito tangível: é o *seu* assistente. Alfred, Jarvis, Minions... aqui é R2D2 — o droid de Star Wars que combina processamento, inteligência, conhecimento e personalidade. Resolve problemas complexos, antecipa necessidades e nunca precisa de muita explicação. Escolha o que fizer sentido pra você.
- Seção "Sobre Você" — perfil, cargo, domínios
- Estilo de comunicação — tabela do que fazer vs. evitar
- Estrutura de respostas — padrão conclusão → detalhes → trade-offs → ação
- Modo de operação — protocolos de segurança, fluxo git, ambiente
- Critérios de qualidade — o que é uma resposta excelente vs. anti-padrões

**[memory-template.md](steering/memory-template.md)** — Template de memória acumulativa (`manual`)
- Correções e ajustes — erros corrigidos que não devem se repetir
- Preferências observadas — padrões do seu estilo de trabalho
- Padrões reutilizáveis — abordagens que funcionaram bem
- Decisões e justificativas — registro de decisões com raciocínio

### Como instalar

1. Copie os templates `steering/r2d2-template.md` e `steering/memory-template.md` para `<KIRO_HOME>/steering/`
2. Renomeie e edite com suas informações
3. O steering principal (`auto`) carrega em toda interação
4. O memory (`manual`) você ativa com `#memory` no chat

> 💡 Pode fazer isso direto pelo Kiro: cole no chat algo como *"copie o template r2d2-template.md para a pasta de steering do Kiro e renomeie para meu-steering.md"* — o agente cuida do resto, independente do seu OS.

---

## Skills — Capacidades Especializadas

Skills são pacotes de instruções em markdown que dão ao agente do Kiro capacidades específicas. Uma skill pode ensinar o agente a seguir padrões de frontend, gerar documentação, preparar você pra uma certificação, ou qualquer outra tarefa que você repete com frequência. Seguem a especificação aberta [Agent Skills](https://agentskills.io/home).

Alguns exemplos do que skills podem fazer:

- [**frontend-design**](https://github.com/anthropics/skills/blob/main/skills/frontend-design/SKILL.md) (Anthropic) — define padrões de UI/UX, componentes e design system pro agente seguir ao gerar código frontend
- [**pptx**](https://github.com/anthropics/skills/blob/main/skills/pptx/SKILL.md) (Anthropic) — cria e edita apresentações PowerPoint programaticamente
- [**spanish-mentor**](skills/spanish-mentor/) (este repo) — mentor de gramática espanhola baseado nas regras da Real Academia Española (RAE)
- [**bookmark-curator**](skills/bookmark-curator/) (este repo) — transforma exports de bookmarks do Firefox em feeds visuais categorizados

Explore mais exemplos no [repositório de skills da Anthropic](https://github.com/anthropics/skills/tree/main/skills).

### Estrutura de uma Skill

```
skill-name/
├── SKILL.md              # Obrigatório — instruções principais + frontmatter
├── references/            # Opcional — docs detalhados carregados sob demanda
├── scripts/               # Opcional — scripts executáveis
└── assets/                # Opcional — templates, dados
```

O `SKILL.md` contém um frontmatter YAML (`name`, `description`) e o corpo com instruções. Arquivos em `references/` só são carregados quando necessário — isso é chamado de **progressive disclosure** e mantém o contexto leve.

### Skills neste repositório

| Skill | Descrição | Ative com |
|-------|-----------|-----------|
| [english-mentor](skills/english-mentor/) | Tutor de inglês americano baseado em padrões IELTS/TOEIC. Revisa gramática, sugere correções. | `#english-mentor` ou "review english" |
| [spanish-mentor](skills/spanish-mentor/) | Mentor de gramática espanhola baseado nas regras da Real Academia Española (RAE). | `#spanish-mentor` ou "corregir español" |
| [kubestronaut-coach](skills/kubestronaut-coach/) | Coach para certificações Kubernetes (CKA, CKAD, CKS, KCNA, KCSA). Foco em velocidade e atalhos para provas. | `#kubestronaut-coach` ou "desafio CKA" |
| [tech-mentor](skills/tech-mentor/) | Mentor técnico para labs hands-on de Kubernetes/EKS. Gera cenários progressivos de troubleshooting. | `#tech-mentor` ou "treino k8s" |
| [training-mentor](skills/training-mentor/) | Gera portais HTML de estudo a partir de uma lista de tópicos. Inclui referências oficiais e vídeos. | `#training-mentor` ou "training content" |
| [bookmark-curator](skills/bookmark-curator/) | Processa exports de bookmarks do Firefox, categoriza, resume e gera um feed visual HTML. | `#bookmark-curator` ou "organizar bookmarks" |
| [tech-docs](skills/tech-docs/) | Gera documentação técnica estruturada a partir de código de infraestrutura (Terraform, K8s, ArgoCD). | `#tech-docs` ou "documentar projeto" |
| [skill-factory](skills/skill-factory/) | Guia a criação de novas skills seguindo a especificação Agent Skills. | `#skill-factory` ou "criar skill" |

### Como instalar

1. Copie a pasta da skill desejada (ex: `skills/kubestronaut-coach/`) para `<KIRO_HOME>/skills/`
2. Para instalar todas, copie todo o conteúdo de `skills/` para `<KIRO_HOME>/skills/`

> 💡 Pode fazer isso direto pelo Kiro: cole no chat *"instalar a skill kubestronaut-coach"* ou *"instalar todas as skills deste repo"* — o agente copia os arquivos pra você.

Skills são ativadas no chat do Kiro usando `#nome-da-skill` ou mencionando as keywords definidas na `description` do frontmatter.

### Referências

- [Agent Skills Spec](https://agentskills.io/home) — especificação aberta para skills de agentes IA
- [Anthropic Skills Examples](https://github.com/anthropics/skills/tree/main/skills) — exemplos oficiais da Anthropic

---

## Powers — Integrações MCP

Powers dão ao agente acesso a conhecimento especializado com **carregamento dinâmico** — diferente de conectar MCP servers diretamente (onde 5 servers = 180+ tools = 40%+ da janela de contexto consumida antes do primeiro prompt), Powers ativam só quando o contexto da conversa pede e desativam quando não são mais relevantes.

Um Power é mais do que um MCP server — é um pacote que une **POWER.md** (steering pro agente), **configuração MCP** (tools e conexão) e opcionalmente **steering/hooks** (workflows automatizados). Para saber mais, veja a [documentação de Powers](https://kiro.dev/docs/powers/).

> 💡 Por que converti meus MCP servers em Powers? Economia de contexto. Empacotando como Power, o Kiro só carrega as tools quando precisa — respostas mais rápidas e com mais qualidade.

### Estrutura de um Power

```
power-name/
├── POWER.md              # Instruções e documentação
├── mcp.json              # Configuração do servidor MCP
└── steering/             # Opcional — guias de workflow
```

### Powers neste repositório

| Power | Descrição | MCP Server |
|-------|-----------|------------|
| [github-power](powers/github-power/) | Integração completa com GitHub — repos, issues, PRs, code search | `@modelcontextprotocol/server-github` |
| [eks-power](powers/eks-power/) | Gerenciamento de clusters AWS EKS — clusters, node groups, add-ons, pod identity | `awslabs.eks-mcp-server` |
| [kubernetes-power](powers/kubernetes-power/) | Operações Kubernetes — kubectl, Helm, pods, troubleshooting | `kubernetes MCP` |
| [markitdown](powers/markitdown/) | Converte arquivos e URLs para Markdown (PDF, DOCX, PPTX, imagens, áudio) | `markitdown-mcp` |
| [aws-diagram](powers/aws-diagram/) | Gera diagramas de arquitetura AWS usando Python diagrams DSL | `awslabs/diagram-mcp-server` |
| [research-assistant](powers/research-assistant/) | Pesquisa profunda com loops iterativos plan-search-evaluate, verificação de fontes e prevenção de alucinações | `tavily` + `fetch` + `context7` + `deepwiki` |

### Como instalar

1. Copie a pasta do Power desejado (ex: `powers/github-power/`) para `<KIRO_HOME>/powers/installed/`
2. Abra o `mcp.json` dentro do Power e substitua os placeholders (ex: `<YOUR_GITHUB_PAT>`) pelas suas chaves
3. Reinicie o Kiro para reconectar os MCP servers

> 💡 Pode fazer isso direto pelo Kiro: cole no chat *"instalar o power github-power"* — o agente copia os arquivos e te orienta sobre as chaves necessárias.

> 💡 Explore mais Powers no [Kiro Powers Hub](https://kiro.dev/powers/)

### Pré-requisitos comuns

| Power | Requer |
|-------|--------|
| github-power | GitHub Personal Access Token |
| eks-power | AWS credentials configuradas (`aws configure`) |
| kubernetes-power | `kubeconfig` configurado |
| markitdown | Python + `uvx` instalado |
| aws-diagram | Python + `uvx` instalado |
| research-assistant | Tavily API key (gratuita em [tavily.com](https://tavily.com)) |

---

## Estrutura do Repositório

```
KIRO/
├── README.md
├── steering/
│   ├── r2d2-template.md          # Template do steering principal
│   └── memory-template.md        # Template de memória acumulativa
├── skills/
│   ├── english-mentor/           # Tutor de inglês
│   ├── spanish-mentor/           # Mentor de espanhol
│   ├── kubestronaut-coach/       # Coach de certificações K8s
│   ├── tech-mentor/              # Labs hands-on K8s
│   ├── training-mentor/          # Portais de estudo HTML
│   ├── bookmark-curator/         # Curadoria de bookmarks
│   ├── tech-docs/                # Gerador de documentação técnica
│   └── skill-factory/            # Meta-skill para criar novas skills
└── powers/
    ├── github-power/             # GitHub integration
    ├── eks-power/                # AWS EKS management
    ├── kubernetes-power/         # Kubernetes operations
    ├── markitdown/               # File-to-Markdown converter
    ├── aws-diagram/              # AWS architecture diagrams
    └── research-assistant/       # Deep research with source verification
```

---

## Como Criar sua Própria Skill

Use a skill `skill-factory` incluída neste repo para criar novas skills:

1. Copie a pasta `skills/skill-factory/` para `<KIRO_HOME>/skills/`
2. No chat do Kiro, diga: "criar skill para [descreva o que quer]"
3. O skill-factory guia você pela estrutura, frontmatter e instruções
4. Resultado: uma skill pronta em `<KIRO_HOME>/skills/`

> 💡 Pode pedir direto no chat: *"instalar a skill skill-factory e criar uma skill para [seu caso de uso]"*

Ou crie manualmente seguindo a [especificação Agent Skills](https://agentskills.io/home).

---

## Contribuindo

1. Fork este repo
2. Crie sua skill/power seguindo a estrutura acima
3. Garanta que não há chaves, tokens ou dados pessoais nos arquivos
4. Abra um Pull Request

---

## Licença

MIT
