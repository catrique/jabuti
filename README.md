# Prumo

Prumo é um CLI que ajuda a criar e padronizar projetos de software. Ele gera
frontends, APIs, projetos fullstack e aplicações web integradas, já com
documentação para agentes e workflows de deploy. O Prumo prepara e padroniza
projetos; ele não administra a máquina do desenvolvedor.

## Requisitos

- Python 3.11 ou superior para executar o Prumo
- Node.js 20.19+ ou 22.12+ e npm, para stacks Node.js
- Python 3.10+ no sistema, para gerar projetos FastAPI e Flask

## Ambiente de desenvolvimento

Crie e ative um ambiente virtual:

```bash
python -m venv .venv
```

No PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

No Linux ou macOS:

```bash
source .venv/bin/activate
```

Instale as dependências e o Prumo em modo editável:

```bash
python -m pip install -r requirements.txt
python -m pip install -e .
```

## Uso

```bash
prumo --help
prumo version
prumo create
```

O comando `prumo create` usa menus navegáveis por setas e Enter e só pergunta
o que é relevante para o tipo escolhido.

| Tipo | Opções | Topologia |
| --- | --- | --- |
| Frontend | React (Vite + TypeScript), Angular | aplicação única |
| API | FastAPI, Express | aplicação única |
| Fullstack | React ou Angular + FastAPI ou Express | `frontend/` e `backend/` separados |
| Aplicação web | Flask (Jinja), Express (EJS) | backend serve o HTML |

- Banco: MySQL opcional onde há backend. O Prumo prepara a aplicação
  (dependências, configuração por variáveis de ambiente e `.env.example`), mas
  não instala MySQL, não cria banco/usuário e nunca gera credenciais.
- Migrations: Alembic para FastAPI e Flask com MySQL. Express ainda não tem
  mecanismo de migrations no scaffold; o workflow `npm run migrar` só é gerado
  quando o projeto realmente possui esse script.
- Deploy: GitHub Actions em runner self-hosted Linux X64, publicando em
  `/srv/apps/<app>`.

Todo projeto criado recebe `AGENTS.md`, `README.md`, `.gitignore` e
`.github/workflows/` gerados a partir da configuração escolhida. Projetos
Python recebem uma `.venv` própria e um `requirements.txt` gerado por
`pip freeze`; projetos Node têm as dependências instaladas localmente.

### Deploy e nomes no servidor

| Projeto | Workflows | APP no servidor |
| --- | --- | --- |
| Aplicação única | `deploy.yml` (+ `migrations.yml`) | `<repo>` |
| Fullstack separado | `deploy-frontend.yml`, `deploy-backend.yml` (+ `migrations-backend.yml`) | frontend `<repo>`, backend `<repo>-api` |

Migrations nunca rodam no push: os workflows de migrations são apenas
manuais (`workflow_dispatch`).

### Ferramentas do sistema

O Prumo verifica, mas não instala: Node.js e npm (React, Angular, Express) e
Python 3.10+ (FastAPI, Flask). Angular é criado com o CLI oficial via
`npm exec`, sem instalação global, e exige Node.js 22.22.3+ ou 24.15+.

## Qualidade

Execute os testes e o lint com:

```bash
pytest
ruff check .
```
