# Jabuti

Jabuti é um CLI que cria e padroniza projetos de software: frontends, APIs,
projetos fullstack e aplicações web integradas. Cada projeto nasce com uma
organização consistente, `AGENTS.md`, `README.md` e `.gitignore` próprios e,
quando há backend, configuração opcional de MySQL e migrations com Alembic.

O Jabuti não gera arquivos de deploy nem configura infraestrutura: publicação
fica a cargo de cada equipe.

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
- **Arquitetura fullstack:** `frontend/` e `backend/` são aplicações
  independentes no mesmo repositório; só o backend acessa o banco.
- **Documentação:** cada projeto recebe `README.md` (stack, estrutura,
  comandos, banco e migrations locais) e `AGENTS.md` (regras de arquitetura,
  segurança, ambiente e testes para agentes de código).

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
