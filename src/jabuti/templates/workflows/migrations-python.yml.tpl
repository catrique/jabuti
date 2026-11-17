name: %%WORKFLOW_NAME%%

# Migrations nunca rodam automaticamente: este workflow é somente manual.
on:
  workflow_dispatch:

permissions:
  contents: read

env:
  APP: '%%APP%%'
  DEPLOY_ROOT: ${{ vars.DEPLOY_ROOT }}

concurrency:
  group: migrate-%%APP%%
  cancel-in-progress: false

jobs:
  migrate:
    runs-on: [self-hosted, Linux, X64]

    defaults:
      run:
        shell: bash

    steps:
      - name: Validar configuração
        run: |
%%RESOLVE_TARGET%%

          [ -d "$deploy_target" ] || {
            echo "Aplicação $APP ainda não publicada. Execute o deploy antes." >&2
            exit 1
          }

          echo "Destino de deploy validado."

      - name: Verificar ambiente
        run: |
          cd -- "$DEPLOY_TARGET"
          .venv/bin/python --version
          .venv/bin/python -m alembic current

      - name: Verificar migrations pendentes
        run: |
          cd -- "$DEPLOY_TARGET"
          .venv/bin/python -m alembic heads

      - name: Aplicar migrations
        run: |
          cd -- "$DEPLOY_TARGET"
          .venv/bin/python -m alembic upgrade head

      - name: Verificar revisão aplicada
        run: |
          cd -- "$DEPLOY_TARGET"
          .venv/bin/python -m alembic current
