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
          node --version
          npm --version
          test -f package.json
          test -d node_modules

      - name: Aplicar migrations
        working-directory: %%SERVER_PATH%%
        run: npm run migrar
