name: %%WORKFLOW_NAME%%

on:
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: migrate-%%APP%%
  cancel-in-progress: false

jobs:
  migrate:
    runs-on: [self-hosted, Linux, X64]

    steps:
      - name: Verificar ambiente
        working-directory: %%SERVER_PATH%%
        run: |
          .venv/bin/python --version
          .venv/bin/python -m alembic current

      - name: Verificar migrations pendentes
        working-directory: %%SERVER_PATH%%
        run: |
          .venv/bin/python -m alembic heads

      - name: Aplicar migrations
        working-directory: %%SERVER_PATH%%
        run: |
          .venv/bin/python -m alembic upgrade head

      - name: Verificar revisão aplicada
        working-directory: %%SERVER_PATH%%
        run: |
          .venv/bin/python -m alembic current
