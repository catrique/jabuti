# Jabuti

Jabuti é uma CLI opinativa para iniciar projetos organizados e preparados para
evoluir com desenvolvedores e agentes de IA. Gera frontends, APIs, projetos
fullstack e aplicações web com **Lightweight CQRS** e um `AGENTS.md` que orienta
o desenvolvimento.

## Instalação

### CLI

```bash
pip install jabuti
```

Depois:

```bash
jabuti create
```

Requer Python 3.11 ou superior. Para uma CLI isolada, use `pipx install jabuti`.

### Skill para Claude Code e Codex

```bash
npx skills add catrique/jabuti --skill jabuti -a claude-code -a codex -g -y
```

Depois, no Claude Code ou Codex, peça:

> Use o Jabuti para criar um projeto fullstack com React, FastAPI, MySQL e Alembic.

Para instalar somente no **Claude Code**:

```bash
npx skills add catrique/jabuti --skill jabuti -a claude-code -g -y
```

Para instalar somente no **Codex**:

```bash
npx skills add catrique/jabuti --skill jabuti -a codex -g -y
```

O comando usa o [`npx skills`](https://github.com/vercel-labs/skills), que requer
Node.js 22.20+ e npm/npx. A skill é distribuída por este repositório GitHub,
independentemente da CLI Python, que também precisa estar instalada.

A instalação global (`-g`) permite usar a skill para criar vários projetos.
Para instalá-la apenas no projeto atual, execute dentro dele, sem `-g`:

```bash
npx skills add catrique/jabuti --skill jabuti -a codex -y
```

## Exemplo rápido

Na CLI, execute `jabuti create` e escolha nome, tipo, frameworks e, quando
aplicável, banco e migrations usando as setas e Enter. O comando é interativo.
Com a skill instalada, você também pode pedir ao agente:

> Use o Jabuti para criar um projeto fullstack com React e FastAPI.

Após a geração, o agente deve ler o `AGENTS.md` criado antes de escrever código.
Esse arquivo é a fonte principal de arquitetura e convenções do novo projeto.

Outros comandos:

```bash
jabuti doctor     # verifica Python, Node.js, npm e Git, sem alterar nada
jabuti create     # cria um projeto com menus por setas e Enter
jabuti version
jabuti --help
```

## Stacks suportadas

| Tipo | Opções | Estrutura |
| --- | --- | --- |
| Frontend | React (Vite + TypeScript), Angular | aplicação única na raiz |
| API | FastAPI, Express | aplicação única na raiz |
| Fullstack | React ou Angular + FastAPI ou Express | `frontend/` e `backend/` independentes |
| Aplicação web | Flask (Jinja), Express (EJS) | backend renderiza o HTML |

- **Banco:** MySQL opcional onde há backend. O Jabuti gera a configuração por
  variáveis de ambiente e um `.env.example`, mas não instala MySQL, não cria
  banco ou usuário e nunca gera credenciais nem `.env` real.
- **Migrations:** Alembic local para FastAPI e Flask com MySQL
  (`alembic revision --autogenerate`, `alembic upgrade head`). Nada roda
  automaticamente.
- **Express:** sem migrations geradas.
- **Fullstack:** o frontend já aponta para a URL local do backend e o backend
  aceita chamadas do navegador vindas do frontend (`FRONTEND_ORIGINS`).

## Como funciona

O Jabuti apresenta o plano para confirmação, verifica as ferramentas necessárias
e gera o projeto em um novo diretório com o nome escolhido. Destinos existentes
são recusados. Os geradores instalam as dependências do projeto usando as
ferramentas disponíveis; ferramentas do sistema nunca são instaladas.

Cada projeto recebe `README.md`, `AGENTS.md` e `.gitignore`. A
[skill oficial](skills/jabuti/SKILL.md) orienta o agente a operar a CLI; o
`AGENTS.md` gerado orienta a evolução da aplicação.

## Arquitetura gerada

Todo projeto usa **Lightweight CQRS**: um *Command* é uma operação que pode
alterar estado; uma *Query* é uma operação de leitura. Rotas, controllers,
páginas e componentes cuidam apenas do seu papel e delegam o comportamento da
aplicação para Commands e Queries. Não há mediator, bus, repository genérico
nem camadas extras; elas só surgem se o projeto precisar.

O núcleo CQRS não conhece framework, HTTP nem banco. O projeto nasce sem
domínio de exemplo: módulos (`modules/<domínio>/commands`, `queries`) são
criados quando a primeira funcionalidade é pedida, como descrito no `AGENTS.md`
gerado.

## Doctor

`jabuti doctor` diagnostica o ambiente local sem alterar nada e diz quais stacks
podem ser criadas, usando as mesmas regras de versão do `jabuti create`.
Retorna código 1 quando algo está ausente ou incompatível.

| Stack | Precisa de |
| --- | --- |
| React, Express | Node.js 20.19+ ou 22.12+ e npm |
| Angular | Node.js 22.22.3+ ou 24.15+ e npm (CLI oficial via `npm exec`) |
| FastAPI, Flask | Python 3.10+ (cada projeto recebe sua própria `.venv`) |

## Desenvolvimento do Jabuti

```bash
git clone https://github.com/catrique/jabuti.git
cd jabuti
python -m venv .venv
.\.venv\Scripts\Activate.ps1      # PowerShell
source .venv/bin/activate         # Linux ou macOS
python -m pip install -r requirements.txt
python -m pip install -e .
```

Antes de cada commit:

```bash
python -m pytest
python -m ruff check .
python -m pip check
python -m build
```

O mesmo conjunto roda no CI (`.github/workflows/ci.yml`) em pushes e pull
requests para `main`.
