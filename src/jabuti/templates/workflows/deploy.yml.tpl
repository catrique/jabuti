name: %%WORKFLOW_NAME%%

on:
  push:
    branches: [main]
%%PUSH_FILTER%%
  workflow_dispatch:

permissions:
  contents: read

env:
  APP: '%%APP%%'
  SRC: '%%SRC%%'
  TIPO: '%%TIPO%%'
%%OUT_ENV%%
concurrency:
  group: deploy-${{ github.workflow_ref }}
  cancel-in-progress: false

jobs:
  deploy:
    runs-on: [self-hosted, Linux, X64]

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Preparar publicação
        run: |
          case "$TIPO" in
            python) required=requirements.txt ;;
            node|react|angular|next) required=package.json ;;
            static) required=index.html ;;
            *) echo "TIPO inválido: $TIPO" >&2; exit 1 ;;
          esac

          case "$APP" in
            ''|.|..|.build|*/*|*\\*)
              echo "APP inválido: $APP" >&2
              exit 1
              ;;
          esac

          [ -d "$SRC" ] || {
            echo "SRC não existe: $SRC" >&2
            exit 1
          }

          workspace=$(realpath "$GITHUB_WORKSPACE")
          source=$(realpath "$SRC")

          case "$source" in
            "$workspace"|"$workspace"/*) ;;
            *)
              echo "SRC fora do repositório: $SRC" >&2
              exit 1
              ;;
          esac

          [ -f "$SRC/$required" ] || {
            echo "Arquivo ausente: $SRC/$required" >&2
            exit 1
          }

          if [ "$TIPO" = react ] || [ "$TIPO" = angular ]; then
            [ -f "$SRC/package-lock.json" ] || {
              echo "Arquivo ausente: $SRC/package-lock.json" >&2
              exit 1
            }
          fi

          [ ! -L %%DEPLOY_ROOT%% ] || {
            echo "Raiz de publicação simbólica proibida." >&2
            exit 1
          }

          [ ! -L "%%DEPLOY_ROOT%%/$APP" ] || {
            echo "Destino simbólico proibido: $APP" >&2
            exit 1
          }

          if [ "$TIPO" = angular ] && [ -z "${OUT:-}" ]; then
            echo "Configure OUT com a pasta gerada pelo Angular." >&2
            exit 1
          fi

      - name: Configurar Node.js
        if: env.TIPO == 'angular'
        uses: actions/setup-node@v4
        with:
          node-version: '22.22.3'
          cache: npm
          cache-dependency-path: ${{ env.SRC }}/package-lock.json

      - name: Instalar dependências do frontend
        if: env.TIPO == 'react' || env.TIPO == 'angular'
        working-directory: ./${{ env.SRC }}
        run: npm ci

      - name: Gerar build do frontend
        if: env.TIPO == 'react' || env.TIPO == 'angular'
        working-directory: ./${{ env.SRC }}
        run: npm run build

      - name: Publicar aplicação
        if: env.TIPO != 'next'
        run: |
          source="$SRC"

          if [ "$TIPO" = react ]; then
            source="$SRC/dist"
          fi

          if [ "$TIPO" = angular ]; then
            source="$SRC/$OUT"
          fi

          [ -d "$source" ] || {
            echo "Pasta para publicação não existe: $source" >&2
            exit 1
          }

          if [ "$TIPO" = react ] || [ "$TIPO" = angular ]; then
            [ -f "$source/index.html" ] || {
              echo "Build inválido: falta $source/index.html" >&2
              exit 1
            }
          fi

          workspace=$(realpath "$GITHUB_WORKSPACE")
          published_source=$(realpath "$source")

          case "$published_source" in
            "$workspace"|"$workspace"/*) ;;
            *)
              echo "Origem fora do repositório: $source" >&2
              exit 1
              ;;
          esac

          if [ "$TIPO" = angular ]; then
            project=$(realpath "$SRC")

            case "$published_source" in
              "$project"/*) ;;
              *)
                echo "OUT fora de SRC: $OUT" >&2
                exit 1
                ;;
            esac
          fi

          target="%%DEPLOY_ROOT%%/$APP"

          mkdir -p "$target"

          rsync -a --delete \
            --exclude='.env*' \
            --exclude='.venv/' \
            --exclude='venv/' \
            --exclude='node_modules/' \
            --exclude='uploads/' \
            --exclude='storage/' \
            --exclude='private/' \
            --exclude='data/' \
            --exclude='.npmrc' \
            --exclude='.pypirc' \
            --exclude='.netrc' \
            --exclude='.git/' \
            --exclude='.github/' \
            "$source/" "$target/"

      - name: Instalar dependências Python
        if: env.TIPO == 'python'
        run: |
          cd "%%DEPLOY_ROOT%%/$APP"

          [ -x .venv/bin/python ] || python3 -m venv .venv

          .venv/bin/python -m pip install -r requirements.txt

      - name: Instalar dependências Node
        if: env.TIPO == 'node'
        run: |
          cd "%%DEPLOY_ROOT%%/$APP"

          npm install --no-audit --no-fund

      - name: Gerar build e publicar Next.js
        if: env.TIPO == 'next'
        run: |
          target="%%DEPLOY_ROOT%%/$APP"
          build_root=%%DEPLOY_ROOT%%/.build
          stage="$build_root/$APP"

          [ ! -L "$build_root" ] && [ ! -L "$stage" ] || {
            echo "Área de build simbólica proibida." >&2
            exit 1
          }

          umask 077
          mkdir -p "$stage"
          chmod 700 "$stage"

          rsync -a --no-perms --delete \
            --exclude='.env*' \
            --exclude='node_modules/' \
            --exclude='.next/' \
            --exclude='.npmrc' \
            --exclude='.pypirc' \
            --exclude='.netrc' \
            --exclude='.git/' \
            --exclude='.github/' \
            "$SRC/" "$stage/"

          find "$stage" -maxdepth 1 -name '.env*' -delete

          if [ -d "$target" ]; then
            rsync -a --no-perms \
              --include='/.env*' \
              --exclude='*' \
              "$target/" "$stage/"
          fi

          cd "$stage"

          npm install --no-audit --no-fund
          npm run build

          mkdir -p "$target"

          rsync -a --delete \
            --exclude='.env*' \
            --exclude='.venv/' \
            --exclude='venv/' \
            --exclude='uploads/' \
            --exclude='storage/' \
            --exclude='private/' \
            --exclude='data/' \
            --exclude='.npmrc' \
            --exclude='.pypirc' \
            --exclude='.netrc' \
            --exclude='.git/' \
            --exclude='.github/' \
            "$stage/" "$target/"

      - name: Reiniciar PM2
        if: env.TIPO == 'python' || env.TIPO == 'node' || env.TIPO == 'next'
        run: |
          if [ "$(id -un)" = deploy ]; then
            pm2_command=(pm2)
          else
            pm2_command=(sudo -n -H -u deploy pm2)
          fi

          if ! processes=$("${pm2_command[@]}" jlist); then
            echo "Falha ao consultar PM2 do usuário deploy." >&2
            exit 1
          fi

          status=$(
            printf '%s' "$processes" |
            python3 -c '
          import json
          import os
          import sys

          processes = json.load(sys.stdin)
          assert isinstance(processes, list)

          print(
              "found"
              if any(
                  process.get("name") == os.environ["APP"]
                  for process in processes
              )
              else "missing"
          )
          '
          ) || {
            echo "Resposta inválida do PM2 do usuário deploy." >&2
            exit 1
          }

          if [ "$status" = missing ]; then
            echo "Processo PM2 ainda não configurado. Primeira publicação concluída."
          else
            echo "Processo PM2 encontrado: $APP. Reiniciando aplicação..."

            "${pm2_command[@]}" restart "$APP"

            echo "Aplicação reiniciada com sucesso."
          fi
