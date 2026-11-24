# Jabuti

Jabuti é um CLI que cria projetos de software prontos para crescer: frontends,
APIs, projetos fullstack e aplicações web, já com estrutura consistente,
**Lightweight CQRS**, camada de API organizada, `README.md`, `AGENTS.md` e
`.gitignore`. Quando há backend, MySQL e migrations com Alembic são opcionais.

O valor não está em chamar `npm create vite` ou `ng new`, e sim no que vem
junto: uma arquitetura simples e explícita, documentada para que pessoas e
agentes de IA continuem o projeto do mesmo jeito.

Ferramentas do sistema são verificadas, nunca instaladas.

## Instalação

Requer Python 3.11 ou superior.

```bash
pip install jabuti
# ou
pipx install jabuti
```

## Uso

```bash
jabuti doctor     # verifica Python, Node.js, npm e Git, sem alterar nada
jabuti create     # cria um projeto com menus por setas e Enter
jabuti version
jabuti --help
```

### `jabuti create`

Pergunta só o que é relevante para o tipo escolhido:

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
- **Fullstack:** o frontend já aponta para a URL local do backend e o backend
  aceita chamadas do navegador vindas do frontend (`FRONTEND_ORIGINS`).

### `jabuti doctor`

Diagnostica o ambiente local sem alterar nada e diz quais stacks podem ser
criadas, usando as mesmas regras de versão do `jabuti create`. Retorna código 1
quando algo está ausente ou incompatível.

| Stack | Precisa de |
| --- | --- |
| React, Express | Node.js 20.19+ ou 22.12+ e npm |
| Angular | Node.js 22.22.3+ ou 24.15+ e npm (CLI oficial via `npm exec`) |
| FastAPI, Flask | Python 3.10+ (cada projeto recebe sua própria `.venv`) |

## Arquitetura gerada

Todo projeto usa **Lightweight CQRS**: um *Command* é uma operação que pode
alterar estado; uma *Query* é uma operação de leitura. Rotas, controllers,
páginas e componentes cuidam apenas do seu papel e delegam o comportamento da
aplicação para Commands e Queries. Não há mediator, bus, repository genérico
nem camadas extras; elas só surgem se o projeto precisar.

| Stack | O que é gerado |
| --- | --- |
| FastAPI, Flask | `app/application/cqrs/` (Command, Query, handlers sync/async, results, `ErrorCode`), `app/http.py` (mapeia `ErrorCode` para HTTP), `app/infrastructure/database.py` com MySQL |
| Express | `src/application/cqrs/` (mesmos conceitos, com `async/await`), `src/http.js`, `src/infrastructure/database.js` com MySQL |
| React | `src/application/cqrs.ts`, `src/infrastructure/api/` (`ApiClient` sobre `fetch`, URL via `VITE_API_BASE_URL`) |
| Angular | `src/app/application/cqrs.ts`, `src/app/infrastructure/api/` (`ApiClient` sobre `HttpClient`/`Observable`), `src/environments/` |

O núcleo CQRS não conhece framework, HTTP nem banco. O projeto nasce sem
domínio de exemplo: módulos (`modules/<domínio>/commands`, `queries`) são
criados quando a primeira funcionalidade é pedida, como descrito no `AGENTS.md`
gerado.

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
ruff check .
pytest
python -m pip check
python -m build
```

O mesmo conjunto roda no CI (`.github/workflows/ci.yml`) em pushes e pull
requests para `main`.
