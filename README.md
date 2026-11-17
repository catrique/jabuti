# Jabuti

Jabuti é um CLI que cria e padroniza projetos de software: frontends, APIs,
projetos fullstack e aplicações web integradas, já com `AGENTS.md`, `README.md`,
`.gitignore` e workflows de deploy do GitHub Actions.

O Jabuti prepara e padroniza projetos; ele não administra a máquina do
desenvolvedor. Ferramentas do sistema são verificadas, nunca instaladas.

## Instalação

Requer Python 3.11 ou superior.

```bash
git clone https://github.com/catrique/jabuti.git
cd jabuti
pip install .
```

Instalação diretamente do GitHub:

```bash
pip install git+https://github.com/catrique/jabuti.git
```

Após a publicação no PyPI:

```bash
pip install jabuti
pipx install jabuti
```

## Uso

```bash
jabuti --help
jabuti version
jabuti doctor
jabuti create
```

### `jabuti doctor`

Diagnostica o ambiente local sem alterar nada: mostra as versões de Python,
Node.js, npm e Git e quais stacks podem ser criadas, usando as mesmas regras
de versão do `jabuti create`. Retorna código 1 quando algo está ausente ou
incompatível.

| Stack | Precisa de |
| --- | --- |
| React, Express | Node.js 20.19+ ou 22.12+ e npm |
| Angular | Node.js 22.22.3+ ou 24.15+ e npm (CLI oficial via `npm exec`) |
| FastAPI, Flask | Python 3.10+ (cada projeto recebe sua própria `.venv`) |

### `jabuti create`

Menus navegáveis por setas e Enter, perguntando só o que é relevante:

| Tipo | Opções | Estrutura |
| --- | --- | --- |
| Frontend | React (Vite + TypeScript), Angular | aplicação única na raiz |
| API | FastAPI, Express | aplicação única na raiz |
| Fullstack | React ou Angular + FastAPI ou Express | `frontend/` e `backend/` independentes |
| Aplicação web | Flask (Jinja), Express (EJS) | backend serve o HTML e os estáticos |

- **Banco:** MySQL opcional onde há backend. O Jabuti gera a configuração por
  variáveis de ambiente e um `.env.example`, mas não instala MySQL, não cria
  banco ou usuário e nunca gera credenciais nem `.env` real.
- **Migrations:** Alembic, para FastAPI e Flask com MySQL. Express ainda não
  tem mecanismo de migrations no scaffold.

- **Deploy:** ao final, o `jabuti create` pergunta se deve gerar os workflows
  de deploy. Respondendo "Não", o projeto é criado normalmente, sem
  `.github/workflows/` (nem workflows de migrations).

## Deploy gerado

Os workflows publicam em um runner self-hosted Linux X64. Eles conhecem apenas
o que pertence ao projeto (`APP`, `SRC`, `TIPO` e, no Angular, `OUT`). O que
pertence ao servidor nunca é gravado nos arquivos gerados: vem de GitHub
Actions Variables, configuradas em cada repositório em **Settings → Secrets and
variables → Actions → Variables**.

| Variável | Uso |
| --- | --- |
| `DEPLOY_ROOT` | Obrigatória. Diretório base, absoluto e já existente, onde as aplicações são publicadas. Sem ela o workflow falha antes de alterar qualquer coisa. |
| `DEPLOY_USER` | Opcional. Usuário dono dos processos PM2. Vazia, o PM2 roda como o próprio usuário do runner; preenchida com outro usuário, é usado `sudo -n -u`. |

Cada aplicação é publicada em `$DEPLOY_ROOT/<APP>`:

| Projeto | Workflows | APP no servidor |
| --- | --- | --- |
| Aplicação única | `deploy.yml` (+ `migrations.yml`) | `<repo>` |
| Fullstack | `deploy-frontend.yml`, `deploy-backend.yml` (+ `migrations-backend.yml`) | frontend `<repo>`, backend `<repo>-api` |

Antes de publicar, o workflow valida `DEPLOY_ROOT` (absoluto, existente, sem
`.`/`..`, sem link simbólico, diferente de `/` e do home), `APP` (um único nome
seguro) e confirma que o destino fica dentro de `DEPLOY_ROOT`. O `.env` do
servidor é preservado e arquivos `.env` do repositório nunca são publicados.

No fullstack, cada lado tem seu próprio deploy, disparado só por mudanças na
sua pasta. Migrations nunca rodam no push: seus workflows são manuais
(`workflow_dispatch`).

## Desenvolvimento

```bash
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
