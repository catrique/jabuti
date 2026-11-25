---
name: jabuti
description: Use the Jabuti CLI to scaffold structured software projects and follow the generated AGENTS.md. Use when the user asks to scaffold, bootstrap, start, or create a project with Jabuti.
---

# Jabuti

Use Jabuti to generate the initial project, then use its generated instructions
to guide development. This skill operates the CLI; it does not replace the
generated project's architecture guide.

## Check the CLI

Start by running:

```bash
jabuti version
```

If it works, use the existing installation. If the command is missing, do not
install silently. Tell the user to install the Python CLI with:

```bash
pip install jabuti
```

Prefer `pipx install jabuti` when pipx is available and an isolated CLI is
appropriate. Resume once the CLI is available. Installing this skill does not
install the Python CLI. Never install Python, Node.js, Git, npm, pipx or other
system tools automatically.

Use `jabuti --help` to inspect the installed CLI. `jabuti doctor` diagnoses local
tools without changing them; it exits with code 1 if a tool is missing or
incompatible. Check which stacks are available before proceeding.

## Supported choices

| Project type | Frontend | Backend |
| --- | --- | --- |
| Frontend | React, Angular | None |
| API | None | FastAPI, Express |
| Fullstack | React, Angular | FastAPI, Express |
| Aplicação web | None | Flask, Express |

Database choices are none (`Nenhum`) or MySQL for projects with a backend.
Frontend-only projects have no database prompt. Alembic is optional only with
MySQL and FastAPI or Flask; there are no migrations for Express. The CLI offers
only relevant prompts. Never invent unsupported stacks or combinations. If the
installed version differs, inspect its menus and help instead of assuming options.

## Create a project

Run this from the directory that should contain the new project:

```bash
jabuti create
```

The command is interactive: enter the project name, use arrow keys and Enter
for menus, then review and confirm the displayed plan. Use the user's supplied
choices; ask for missing choices when needed. Do not invent non-interactive
flags or pipe a fabricated command into the menu.

For example, for a request to create `sistema-rh` as a fullstack React + FastAPI
system with MySQL and Alembic, enter these choices in order:

```text
Nome do projeto: sistema-rh
O que você quer criar?: Fullstack
Frontend: React
Backend: FastAPI (Python)
Banco de dados: MySQL
Migrations: Alembic
```

If the agent environment cannot interact with a TTY menu, clearly explain the
limitation and give the user `jabuti create` and the intended selections to run
in their terminal. Continue after generation is confirmed. Do not claim the
project was created when the command did not complete successfully.

Jabuti creates a directory named after the project in the working directory.
Fullstack projects have independent `frontend/` and `backend/` applications;
other types put the application at the project root. Generators install project
dependencies using existing tools. Jabuti refuses an existing destination;
do not delete or regenerate over existing files without an explicit request.

## Read the generated instructions before development

After `jabuti create` succeeds, locate the created project and open and read its
root `AGENTS.md` before writing any new code. Treat that file as the primary
source of truth for the project's architecture and conventions. Use its README
for setup and development commands.

Do not continue development based only on generic framework conventions.
Read and follow the generated AGENTS.md first.

The scaffold uses Lightweight CQRS: Commands change state; Queries read data.
Follow the generated guide for the implementation and growth of that architecture.

## Keep the generated scope

- Do not ignore `AGENTS.md` or immediately restructure the scaffold.
- Do not add deployment, Docker or Redis automatically; Jabuti does not generate
  them.
- Do not introduce repositories, mediators or an event bus without a concrete,
  current need.
- Jabuti never generates credentials or a real `.env`; use the generated
  `.env.example` and project instructions for local configuration.
- Alembic migrations are local and never run automatically. Follow the generated
  instructions and review migrations before applying them.
